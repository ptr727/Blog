#!/usr/bin/env python3
"""Feed the media gate and its normalizer malformed input, and fail on what breaks them.

The gate and the normalizer are only checked by the carried tree, and every file in it is
well formed. Review kept finding malformed-input cases one at a time, each one a case
somebody thought of. This generates them instead: truncated, extended, bit-flipped and
spliced variants of every container the gate recognizes, plus planted metadata that the
gate must notice wherever a decoder would read it.

The properties, each checked on every variant:

1. The scanner never raises. A malformed file is a finding, never a traceback.
2. The normalizer never raises, and never returns a file its own scanner rejects.
3. The normalizer returns nothing, or a file whose picture payload is unchanged.
4. Planted metadata is always reported.
   A plant that declares a refusal is refused, and one that declares a rewrite is rewritten.
5. The archive walk never raises on a damaged archive.
6. The normalizer refuses a picture its Exif turns, or returns one turned the same way.
   Where decoders disagree on the turn, it refuses.
7. A clean plant, holding only values the gate admits, is reported by nothing and left unchanged.

Seeds are constructed fixtures plus a sample of the carried media, read in memory and
never written anywhere. The run is deterministic for a given seed and file list, and
bounded by both a case count and a time budget, so it can run in CI.
"""

import argparse
import contextlib
import functools
import importlib.util
import io
import itertools
import pathlib
import random
import re
import struct
import sys
import tempfile
import time
import warnings
import zipfile
import zlib
from collections.abc import Callable, Iterable, Iterator

REPO = pathlib.Path(__file__).resolve().parent.parent


def load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load("gate", REPO / "checks" / "check-media-metadata.py")
normalizer = load("normalizer", REPO / "scripts" / "normalize-media.py")

# A comment segment, chunk, block or atom holding nothing, so no allowlist can admit it.
PLANT_TEXT = b"planted"

# What a plant may declare the normalizer does with it, or the exact bytes of its rewrite.
# A plant that declares nothing passes whether the normalizer refuses or rewrites it.
REFUSED = "refused"
REWRITTEN = "rewritten"


def jpeg_segment(marker: int, body: bytes) -> bytes:
    return bytes((0xFF, marker)) + struct.pack(">H", len(body) + 2) + body


def exif_segment(tail: bytes = b"") -> bytes:
    """An Exif APP1 carrying only Orientation, with optional bytes after its one IFD."""
    entry = struct.pack("<HHIHH", 0x0112, 3, 1, 6, 0)
    tiff = b"II" + struct.pack("<HI", 42, 8) + struct.pack("<H", 1) + entry
    return jpeg_segment(0xE1, b"Exif\x00\x00" + tiff + struct.pack("<I", 0) + tail)


def exif_gap_segment() -> bytes:
    """An Exif APP1 whose Exif IFD sits past bytes nothing references, as a thumbnail would."""
    gap = b"\xff\xd8" + PLANT_TEXT + b"\xff\xd9"
    ifd0 = struct.pack("<H", 1) + struct.pack("<HHII", 0x8769, 4, 1, 26 + len(gap))
    exif_ifd = struct.pack("<H", 1) + struct.pack("<HHIHH", 0xA001, 3, 1, 1, 0)
    tiff = b"II" + struct.pack("<HI", 42, 8) + ifd0 + struct.pack("<I", 0) + gap
    tiff += exif_ifd + struct.pack("<I", 0)
    return jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)


def exif_ifd_segment(
    entries: list[tuple[int, int, int, bytes]], pad: bytes = b""
) -> bytes:
    """An Exif APP1 with one IFD holding the given tag, type, count and value entries.

    A pad goes between the IFD and the values it points to, as a writer aligning them leaves one.
    """
    table, values = b"", b""
    start = 8 + 2 + 12 * len(entries) + 4 + len(pad)
    for tag, kind, count, value in entries:
        if len(value) > 4:
            field = struct.pack("<I", start + len(values))
            values += value
        else:
            field = value.ljust(4, b"\x00")
        table += struct.pack("<HHI", tag, kind, count) + field
    ifd = struct.pack("<H", len(entries)) + table + struct.pack("<I", 0)
    tiff = b"II" + struct.pack("<HI", 42, 8) + ifd + pad + values
    return jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)


DATE = b"2001:01:01 00:00:00\x00"
ORIENTATION = (0x0112, 3, 1, struct.pack("<H", 6))

# Allowed tags bent out of their one shape, each able to carry bytes a decoder never needs.
EXIF_BENT = (
    ([ORIENTATION, (0x0132, 2, len(DATE) + 7, DATE + PLANT_TEXT)], "long DateTime"),
    ([ORIENTATION, (0x0132, 12, 20, DATE * 8)], "DateTime as doubles"),
    ([ORIENTATION, (0x0102, 12, 4, PLANT_TEXT * 5)], "BitsPerSample as doubles"),
    ([ORIENTATION, (0x0132, 2, 20, DATE), (0x0132, 2, 20, DATE)], "repeated DateTime"),
    ([ORIENTATION, ORIENTATION], "repeated Orientation"),
    (
        [ORIENTATION, (0x0132, 2, 20, b"+37.7749-122.4194\x00\x00\x00")],
        "DateTime not a date",
    ),
    ([ORIENTATION, (0x0132, 2, 4, b"abc\x00")], "short DateTime"),
    ([ORIENTATION, (0x9000, 7, 2, b"02\x00\x00")], "ExifVersion with fewer values"),
    ([ORIENTATION, (0x0102, 3, 2, struct.pack("<HH", 8, 8))], "BitsPerSample of 2"),
    (
        [
            ORIENTATION,
            (0x0115, 3, 1, struct.pack("<H", 1)),
            (0x0102, 3, 3, struct.pack("<HHH", 8, 8, 8)),
        ],
        "BitsPerSample of 3 for 1 sample",
    ),
    ([(0x0112, 3, 1, struct.pack("<H", 6) + b"pl")], "Orientation padding"),
    ([(0x0112, 3, 1, b"pl")], "Orientation out of its range"),
    ([ORIENTATION, (0x9000, 7, 4, b"plnt")], "ExifVersion not a known version"),
    ([ORIENTATION, (0xA000, 7, 4, b"plnt")], "FlashpixVersion not a known version"),
    ([ORIENTATION, (0x0002, 7, 4, b"plnt")], "InteropVersion not a known version"),
    ([ORIENTATION, (0x0001, 2, 4, b"pln\x00")], "InteropIndex not a known index"),
    (
        [ORIENTATION, (0x9101, 7, 4, b"plnt")],
        "ComponentsConfiguration not a known order",
    ),
    ([ORIENTATION, (0x0102, 3, 3, PLANT_TEXT[:6])], "BitsPerSample of 3 not 8 bits"),
    ([ORIENTATION, (0x0102, 3, 1, b"pl")], "BitsPerSample of 1 not 8 bits"),
    *(
        ([ORIENTATION, (tag, 3, 1, b"pl")], f"SHORT 0x{tag:04X} out of its range")
        for tag in (0x0103, 0x0106, 0x0115, 0x011C, 0x0128, 0x0213, 0xA001)
    ),
)

JFIF = b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
ADOBE = b"Adobe\x00\x64\x00\x00\x00\x00\x01"


def bend(fields: bytes, at: int, value: bytes) -> bytes:
    """A fixed-shape segment's fields with the bytes at one offset replaced."""
    return fields[:at] + value + fields[at + len(value) :]


# A restart marker, which a fill run inside a scan precedes.
RESTART = re.compile(rb"\xff[\xd0-\xd7]")

# The values sBIT and bKGD hold for each PNG color type, stated here rather than taken from the gate.
PNG_SIGNIFICANT = {0: 1, 2: 3, 3: 3, 4: 2, 6: 4}
PNG_BACKGROUND = {0: 2, 2: 6, 3: 1, 4: 2, 6: 6}
SRGB_GAMMA = struct.pack(">I", 45455)
SQUARE = struct.pack(">IIB", 3779, 3779, 1)


def png_field_plants(data: bytes, parts: list) -> list[tuple[bytes, str, str | bytes]]:
    """Ancillary PNG chunks each admitted alone, planted out of their values or more than once.

    A plant goes into a seed with no ancillary chunks, so that repetition cannot report it.
    """
    if len(data) < 33:
        return []
    bare = data[:8] + b"".join(
        data[s:e] for c, s, e in parts if c in (b"IHDR", b"PLTE", b"IDAT", b"IEND")
    )
    depth, color = data[24], data[25]
    significant = PNG_SIGNIFICANT.get(color, 1)
    background = PNG_BACKGROUND.get(color, 2)
    palette = sum(e - s - 12 for c, s, e in parts if c == b"PLTE") // 3
    alpha = {0: b"pla", 2: PLANT_TEXT, 3: bytes(palette + 1)}.get(color, b"pl")
    # A palette no browser draws by goes, and one in a grayscale image is refused.
    suggestion = REWRITTEN if color in (2, 6) else REFUSED
    planted = [
        (b"gAMA", b"plnt", "gAMA not the sRGB gamma", REFUSED),
        (b"gAMA", SRGB_GAMMA + PLANT_TEXT, "gAMA with bytes past its fields", REFUSED),
        (b"cHRM", (PLANT_TEXT * 5)[:32], "cHRM not the sRGB primaries", REFUSED),
        (b"sRGB", b"p", "sRGB intent not a known intent", REFUSED),
        (b"pHYs", SQUARE[:4] + b"plnt\x01", "pHYs density not square", REFUSED),
        (b"pHYs", SQUARE[:8] + b"p", "pHYs unit not a known unit", REFUSED),
        (b"pHYs", SQUARE + PLANT_TEXT, "pHYs with bytes past its fields", REFUSED),
        (b"sBIT", b"p" * significant, "sBIT not the full depth", REWRITTEN),
        (b"bKGD", b"p" * background, "bKGD not zero", REWRITTEN),
        (b"hIST", b"pl", "hIST chunk", REWRITTEN),
        (b"tRNS", alpha, "tRNS not in its shape", REFUSED),
    ]
    if color == 0 and depth < 16:
        planted.append((b"tRNS", b"\xff\xff", "tRNS gray past its depth", REFUSED))
    out = [
        (bare[:33] + png_chunk(chunk, body) + bare[33:], what, expect)
        for chunk, body, what, expect in planted
    ]
    full = bytes((8 if color == 3 else depth,)) * significant
    for chunk, body, expect in (
        (b"gAMA", SRGB_GAMMA, REFUSED),
        (b"sRGB", b"\x00", REFUSED),
        (b"pHYs", SQUARE, REFUSED),
        (b"sBIT", full, REWRITTEN),
        (b"bKGD", bytes(background), REWRITTEN),
    ):
        twice = png_chunk(chunk, body) * 2
        variant = bare[:33] + twice + bare[33:]
        out.append((variant, f"repeated {chunk.decode()}", expect))
    # A decoder passes over a chunk out of its place, so its bytes are free there.
    late = png_chunk(b"gAMA", SRGB_GAMMA)
    out.append((bare[:-12] + late + bare[-12:], "gAMA after IDAT", REFUSED))
    if palette:
        early = png_chunk(b"tRNS", bytes(1))
        out.append((bare[:33] + early + bare[33:], "tRNS before PLTE", REFUSED))
    # A palette entry no pixel can address, and a palette no browser draws by, each hold free bytes.
    if color == 3 and depth <= 8:
        entries = (1 << depth) + 1
        long = png_chunk(b"PLTE", (PLANT_TEXT * entries)[: 3 * entries])
        head = bare[:8] + b"".join(
            long if c == b"PLTE" else data[s:e]
            for c, s, e in parts
            if c in (b"IHDR", b"PLTE", b"IDAT", b"IEND")
        )
        out.append((head, "PLTE longer than the bit depth addresses", REFUSED))
    elif color != 3:
        suggested = png_chunk(b"PLTE", PLANT_TEXT * 3)
        variant = bare[:33] + suggested + bare[33:]
        out.append((variant, "PLTE in a color type that draws none", suggestion))
        # A second palette fails the picture in libpng, so dropping both would draw one it did not.
        out.append((bare[:33] + suggested * 2 + bare[33:], "two PLTE", REFUSED))
    if color == 2:
        # A truecolor color key may precede a suggested palette, so only the palette goes.
        key = png_chunk(b"tRNS", bytes(6))
        variant = bare[:33] + key + suggested + bare[33:]
        out.append(
            (variant, "tRNS before a suggested PLTE", bare[:33] + key + bare[33:])
        )
    # A palette after the picture data is one a decoder does not read.
    palettes = [data[s:e] for c, s, e in parts if c == b"PLTE"][:1] or [
        png_chunk(b"PLTE", PLANT_TEXT * 3)
    ]
    moved = bare[:8] + b"".join(
        data[s:e] for c, s, e in parts if c in (b"IHDR", b"IDAT")
    )
    after = REFUSED if color == 3 else suggestion
    out.append((moved + palettes[0] + bare[-12:], "PLTE after IDAT", after))
    # An APNG frame is refused, so a still decoder never reads a default image the gate alone passed.
    control = png_chunk(b"acTL", struct.pack(">II", 1, 0))
    frame = png_chunk(b"fdAT", struct.pack(">I", 0) + PLANT_TEXT)
    out.append((bare[:33] + control + bare[33:], "acTL chunk", REFUSED))
    out.append((bare[:-12] + frame + bare[-12:], "fdAT with no acTL", REFUSED))
    return out


def png_clean_plants(data: bytes, parts: list) -> list[tuple[bytes, str]]:
    """Ancillary PNG chunks each holding a value writers use, which the gate passes and the normalizer keeps."""
    if len(data) < 33:
        return []
    bare = data[:8] + b"".join(
        data[s:e] for c, s, e in parts if c in (b"IHDR", b"PLTE", b"IDAT", b"IEND")
    )
    depth, color = data[24], data[25]
    palette = sum(e - s - 12 for c, s, e in parts if c == b"PLTE") // 3
    full = bytes((8 if color == 3 else depth,)) * PNG_SIGNIFICANT.get(color, 1)
    kept = [
        *((b"sRGB", bytes((intent,))) for intent in range(4)),
        *((b"cHRM", primaries) for primaries in sorted(gate.PNG_PRIMARIES)),
        (b"gAMA", SRGB_GAMMA),
        (b"pHYs", SQUARE),
        (b"pHYs", struct.pack(">IIB", 72, 72, 0)),
        (b"sBIT", full),
        (b"bKGD", bytes(PNG_BACKGROUND.get(color, 2))),
    ]
    if color in (0, 2):
        kept.append((b"tRNS", bytes(2 if color == 0 else 6)))
    elif color == 3 and palette:
        kept.append((b"tRNS", bytes(palette)))
    at = 33 + sum(e - s for c, s, e in parts if c == b"PLTE") if color == 3 else 33
    out = []
    for chunk, body in kept:
        # Transparency and background follow a palette, and every other chunk goes first.
        place = at if chunk in (b"tRNS", b"bKGD") else 33
        variant = bare[:place] + png_chunk(chunk, body) + bare[place:]
        out.append((variant, f"{chunk.decode()} {body.hex()}"))
    # Rows of filter type zero and sample zero, laid out in the Adam7 passes an interlaced header needs.
    interlaced = data[16:28] + b"\x01"
    size = gate.png_picture_size(interlaced)
    piece = gate.PNG_INFLATE_PIECE
    rows = deflated(bytes(min(piece, size - at)) for at in range(0, size, piece))
    idat = [(s, e) for c, s, e in parts if c == b"IDAT"]
    if idat:
        head = data[:8] + png_chunk(b"IHDR", interlaced) + data[33 : idat[0][0]]
        variant = head + png_chunk(b"IDAT", rows) + data[idat[-1][1] :]
        out.append((variant, "interlaced IHDR over its Adam7 passes"))
    return out


def png_structure_plants(data: bytes, parts: list) -> list[tuple[bytes, str, str]]:
    """PNGs missing or bending a critical chunk a decoder needs, so no browser draws them and every byte is free."""
    if len(data) < 33:
        return []
    signature, ihdr, iend = data[:8], data[8:33], data[-12:]
    header = ihdr[8:21]
    # The seed's own picture data, so each plant bends only the rule it names.
    idat = b"".join(data[s:e] for c, s, e in parts if c == b"IDAT")
    plte = [data[s:e] for c, s, e in parts if c == b"PLTE"]
    body = b"".join(data[s:e] for c, s, e in parts if c in (b"PLTE", b"IDAT"))
    ended = png_chunk(b"IEND", PLANT_TEXT)
    padded = png_chunk(b"IHDR", header + PLANT_TEXT)
    out = [
        (signature + idat + iend, "no IHDR", REFUSED),
        (signature + idat + ihdr + iend, "IHDR not first", REFUSED),
        (signature + ihdr + b"".join(plte) + iend, "no IDAT", REFUSED),
        (signature + ihdr + body + ended, "IEND with a body", REWRITTEN),
        (signature + padded + body + iend, "IHDR with bytes past its fields", REFUSED),
    ]
    for at, value, what in (
        (0, bytes(4), "IHDR width zero"),
        (4, b"\x80\x00\x00\x00", "IHDR height past the range"),
        (
            0,
            struct.pack(">I", gate.PNG_SIDE_LIMIT + 1),
            "IHDR width past libpng's limit",
        ),
        (
            4,
            struct.pack(">I", gate.PNG_SIDE_LIMIT + 1),
            "IHDR height past libpng's limit",
        ),
        (8, b"\x03", "IHDR depth not one its color type pairs with"),
        (9, b"\x05", "IHDR color type not a defined one"),
        (10, b"\x01", "IHDR compression not zero"),
        (11, b"\x01", "IHDR filter not zero"),
        (12, b"\x02", "IHDR interlace not a defined one"),
    ):
        bent = header[:at] + value + header[at + len(value) :]
        out.append((signature + png_chunk(b"IHDR", bent) + body + iend, what, REFUSED))
    deep = header[:8] + b"\x10\x03" + header[10:]
    wide = png_chunk(b"PLTE", (PLANT_TEXT * 3)[:9] * 3)
    out.append(
        (
            signature + png_chunk(b"IHDR", deep) + wide + idat + iend,
            "palette with a 16-bit depth",
            REFUSED,
        )
    )
    if header[9] == 3:
        variant = signature + ihdr + idat + iend
        out.append((variant, "palette image with no PLTE", REFUSED))
    for at, name, expect in ((8, "IHDR", REFUSED), (len(data) - 12, "IEND", REWRITTEN)):
        bent = data[: at + 8 + (13 if name == "IHDR" else 0)] + b"plnt"
        out.append((bent + data[len(bent) :], f"{name} CRC not its own", expect))
    gamma = png_chunk(b"gAMA", SRGB_GAMMA)[:-4] + b"plnt"
    out.append((data[:33] + gamma + data[33:], "gAMA CRC not its own", REWRITTEN))
    return out


def inflated(stream: bytes) -> Iterator[bytes]:
    """A seed's picture data inflated in bounded pieces, so a plant built from it never holds the whole picture."""
    inflate = zlib.decompressobj()
    while piece := inflate.decompress(stream, gate.PNG_INFLATE_PIECE):
        yield piece
        stream = inflate.unconsumed_tail


def all_but_last(pieces: Iterator[bytes]) -> Iterator[bytes]:
    """The pieces with their final byte left off."""
    held = b""
    for piece in pieces:
        yield held
        held = piece
    yield held[:-1]


def deflated(pieces: Iterable[bytes]) -> bytes:
    deflate = zlib.compressobj()
    return b"".join(deflate.compress(piece) for piece in pieces) + deflate.flush()


def png_stream_plants(data: bytes, parts: list) -> list[tuple[bytes, str, str]]:
    """PNGs whose picture data is not one whole zlib stream of the length IHDR needs, so a decoder fails the picture or passes over bytes."""
    idat = [(s, e) for c, s, e in parts if c == b"IDAT"]
    if len(data) < 33 or not idat:
        return []
    head, tail = data[: idat[0][0]], data[idat[-1][1] :]
    stream = b"".join(data[s + 8 : e - 4] for s, e in idat)
    past = deflated(itertools.chain(inflated(stream), (PLANT_TEXT,)))
    short = deflated(all_but_last(inflated(stream)))
    pieces = inflated(stream)
    first = next(pieces)
    bent = deflated(itertools.chain((b"\x05" + first[1:],), pieces))
    out = [
        (png_chunk(b"IDAT", b""), "IDAT empty"),
        (png_chunk(b"IDAT", PLANT_TEXT), "IDAT not a zlib stream"),
        (png_chunk(b"IDAT", stream + PLANT_TEXT), "bytes after the IDAT stream"),
        (
            png_chunk(b"IDAT", stream) + png_chunk(b"IDAT", PLANT_TEXT),
            "IDAT after the stream's end",
        ),
        (png_chunk(b"IDAT", stream[:-4]), "IDAT stream cut off"),
        (png_chunk(b"IDAT", past), "IDAT past its rows"),
        (png_chunk(b"IDAT", short), "IDAT short of its rows"),
        (png_chunk(b"IDAT", bent), "IDAT row filter 5"),
    ]
    variants = [(head + body + tail, what, REFUSED) for body, what in out]
    header = data[16:29]
    side = struct.pack(">I", gate.PNG_SIDE_LIMIT // 10)
    vast = data[:8] + png_chunk(b"IHDR", side * 2 + header[8:]) + data[33:]
    variants.append((vast, "IHDR picture past the size limit", REFUSED))
    interlaced = header[:12] + b"\x01"
    if gate.png_picture_size(interlaced) != gate.png_picture_size(header):
        whole = data[:8] + png_chunk(b"IHDR", interlaced) + data[33:]
        variants.append((whole, "interlaced IHDR over rows laid out whole", REFUSED))
    return variants


def gif_field_plants(data: bytes, parts: list) -> list[tuple[bytes, str, str | bytes]]:
    """GIF blocks each admitted alone, planted with a reserved or unused field not zero.

    A field the normalizer writes as zero comes back as the seed, which a clean seed holds zero there.
    """
    if len(data) < 13:
        return []
    out = [
        (data[:12] + b"p" + data[13:], "aspect ratio byte not zero", data),
        (data[:11] + b"p" + data[12:], "background index not zero", data),
        (
            data[:10] + bytes((data[10] | 0x70,)) + data[11:],
            "color resolution not zero",
            data,
        ),
        (
            data[:10] + bytes((data[10] | 0x08,)) + data[11:],
            "screen sort flag not zero",
            data,
        ),
    ]
    if data[10] & 0x80:
        table = 3 * (2 << (data[10] & 7))
        flags = b"\x07"
        variant = data[:10] + flags + data[11:13] + data[13 + table :]
        out.append((variant, "table size with no color table", REWRITTEN))
        # A local table on every image leaves the global one read by nothing.
        local = bytearray(data)
        for name, start, _ in reversed(parts):
            if name == "image" and not data[start + 9] & 0x80:
                local[start + 9] = data[start + 9] & 0x40 | 0x80
                local[start + 10 : start + 10] = bytes(6)
        out.append((bytes(local), "global color table no image reads", REWRITTEN))
    out.append((b"GIF87a" + data[6:], "version not 89a", data))
    for name, start, end in parts:
        if name == "extension 0xF9" and end - start == 8:
            packed, index = data[start + 3], data[start + 6]
            # Decoders differ on a disposal method the format does not define, so it is not rewritten.
            for value, held, what, expect in (
                (packed | 0xE0, index, "graphic control reserved bits not zero", data),
                (
                    packed | 0x1C,
                    index,
                    "graphic control disposal not a known method",
                    REFUSED,
                ),
                (
                    packed & 0xFE,
                    0x70,
                    "graphic control unused transparent index",
                    REWRITTEN,
                ),
            ):
                fields = bytes((value,)) + data[start + 4 : start + 6] + bytes((held,))
                variant = data[: start + 3] + fields + data[start + 7 :]
                out.append((variant, what, expect))
        elif name == "image":
            held = data[start + 9]
            for value, what in (
                (held | 0x18, "image descriptor reserved bits not zero"),
                (held | 0x20, "image descriptor sort flag not zero"),
            ):
                variant = data[: start + 9] + bytes((value,)) + data[start + 10 :]
                out.append((variant, what, data))
            if not held & 0x80:
                variant = data[: start + 9] + bytes((held | 0x07,)) + data[start + 10 :]
                out.append((variant, "image table size with no local table", data))
    return out


ICC = b"ICC_PROFILE\x00\x01\x01"
SOF = jpeg_segment(0xC0, b"\x08\x00\x08\x00\x08\x01\x01\x11\x00")
SOS = jpeg_segment(0xDA, b"\x01\x01\x00\x00\x3f\x00")

# APP segments each already allowed alone, planted so that their shape or repetition carries bytes.
JPEG_APP_BENT = (
    (
        [jpeg_segment(0xE0, JFIF + PLANT_TEXT)],
        "JFIF with bytes past its fields",
        REWRITTEN,
    ),
    (
        [jpeg_segment(0xE0, JFIF[:12] + b"\x03\x01" + PLANT_TEXT + b"\x00\x00")],
        "JFIF thumbnail",
        REWRITTEN,
    ),
    (
        [jpeg_segment(0xEE, ADOBE + PLANT_TEXT)],
        "Adobe with bytes past its fields",
        REWRITTEN,
    ),
    ([jpeg_segment(0xE0, JFIF)] * 2, "repeated JFIF", REWRITTEN),
    ([jpeg_segment(0xEE, ADOBE)] * 2, "repeated Adobe", REFUSED),
    ([exif_segment()] * 8, "repeated Exif", REFUSED),
    (
        [jpeg_segment(0xE2, ICC + bytes(8)), jpeg_segment(0xE2, ICC + PLANT_TEXT)],
        "repeated ICC chunk",
        REFUSED,
    ),
    (
        [jpeg_segment(0xE2, ICC[:12] + b"\x01\x03" + PLANT_TEXT)],
        "incomplete ICC profile",
        REFUSED,
    ),
    (
        [jpeg_segment(0xE2, ICC + PLANT_TEXT)],
        "ICC profile not a known profile",
        REFUSED,
    ),
    (
        [jpeg_segment(0xE0, bend(JFIF, 5, b"pl"))],
        "JFIF version not a known version",
        REWRITTEN,
    ),
    (
        [jpeg_segment(0xE0, bend(JFIF, 7, b"p"))],
        "JFIF units not a known unit",
        REWRITTEN,
    ),
    (
        [jpeg_segment(0xE0, bend(JFIF, 8, b"plan"))],
        "JFIF density not square",
        REWRITTEN,
    ),
    ([jpeg_segment(0xEE, bend(ADOBE, 5, b"pl"))], "Adobe version not 100", REWRITTEN),
    ([jpeg_segment(0xEE, bend(ADOBE, 7, b"plan"))], "Adobe flags not zero", REWRITTEN),
    (
        [jpeg_segment(0xEE, bend(ADOBE, 11, b"p"))],
        "Adobe transform not a known one",
        REFUSED,
    ),
)


def with_riff_size(data: bytes) -> bytes:
    """Restate a WebP's RIFF size to cover the whole file, as a decoder then reads it all."""
    return data[:4] + struct.pack("<I", len(data) - 8) + data[8:]


def jpeg_fixture(progressive: bool) -> bytes:
    """A structurally complete JPEG, with stuffed bytes and a restart marker in its scans."""
    sof = 0xC2 if progressive else 0xC0
    out = b"\xff\xd8" + jpeg_segment(
        0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    )
    out += exif_segment()
    out += jpeg_segment(0xDB, b"\x00" + bytes(range(64)))
    out += jpeg_segment(sof, b"\x08\x00\x08\x00\x08\x01\x01\x11\x00")
    out += jpeg_segment(0xC4, b"\x00" + bytes(16) + b"")
    out += jpeg_segment(0xDA, b"\x01\x01\x00\x00\x3f\x00")
    out += b"\x12\x34\xff\x00\x56\xff\xd0\x78\x9a"
    if progressive:
        out += jpeg_segment(0xC4, b"\x10" + bytes(16))
        out += jpeg_segment(0xDA, b"\x01\x01\x00\x01\x3f\x00")
        out += b"\xab\xff\x00\xcd\xff\xd1\xef"
    return out + b"\xff\xd9"


def dated_jpeg_fixture() -> bytes:
    """A JPEG whose Exif holds every out-of-line allowed tag in its one shape."""
    rational = struct.pack("<II", 72, 1)
    exif = exif_ifd_segment(
        [
            ORIENTATION,
            (0x0102, 3, 3, struct.pack("<HHH", 8, 8, 8)),
            (0x011A, 5, 1, rational),
            (0x0132, 2, 20, DATE),
        ]
    )
    return jpeg_fixture(False).replace(exif_segment(), exif)


def png_chunk(name: bytes, body: bytes) -> bytes:
    crc = zlib.crc32(name + body) & 0xFFFFFFFF
    return struct.pack(">I", len(body)) + name + body + struct.pack(">I", crc)


def png_fixture() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
    idat = zlib.compress(b"\x00\x7f")
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"gAMA", struct.pack(">I", 45455))
        + png_chunk(b"IDAT", idat)
        + png_chunk(b"IEND", b"")
    )


def truecolor_png_fixture() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(4))
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", idat)
        + png_chunk(b"IEND", b"")
    )


def small_png_fixture() -> bytes:
    """A 5x3 grayscale PNG at two bits a sample, so rows hold a partial byte and interlacing spans several passes."""
    ihdr = struct.pack(">IIBBBBB", 5, 3, 2, 0, 0, 0, 0)
    idat = zlib.compress(b"\x00\x1b\xc0" * 3)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", idat[:5])
        + png_chunk(b"IDAT", idat[5:])
        + png_chunk(b"IEND", b"")
    )


def palette_png_fixture() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 1, 3, 0, 0, 0)
    idat = zlib.compress(b"\x00\x00")
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"PLTE", bytes(6))
        + png_chunk(b"IDAT", idat)
        + png_chunk(b"IEND", b"")
    )


def gif_fixture() -> bytes:
    head = b"GIF89a" + struct.pack("<HH", 1, 1) + b"\x80\x00\x00" + bytes(6)
    netscape = b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"
    control = b"\x21\xf9\x04\x00\x00\x00\x00\x00"
    image = b"\x2c" + struct.pack("<HHHH", 0, 0, 1, 1) + b"\x00"
    return head + netscape + control + image + b"\x02\x02\x44\x01\x00" + b"\x3b"


def riff_chunk(name: bytes, body: bytes) -> bytes:
    return (
        name + struct.pack("<I", len(body)) + body + (b"\x00" if len(body) & 1 else b"")
    )


def webp_fixture() -> bytes:
    body = riff_chunk(b"VP8X", bytes(10)) + riff_chunk(b"VP8L", b"\x2f\x00\x00\x00\x00")
    return b"RIFF" + struct.pack("<I", len(body) + 4) + b"WEBP" + body


def animated_webp_fixture() -> bytes:
    """An animated WebP of one frame, which holds its own chunks inside an ANMF."""
    frame = bytes(12) + b"\x64\x00\x00\x00"
    frame += riff_chunk(b"VP8L", b"\x2f\x00\x00\x00\x00")
    body = riff_chunk(b"VP8X", b"\x02" + bytes(9)) + riff_chunk(b"ANIM", bytes(6))
    body += riff_chunk(b"ANMF", frame)
    return b"RIFF" + struct.pack("<I", len(body) + 4) + b"WEBP" + body


def atom(name: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body) + 8) + name + body


def iso_fixture() -> bytes:
    moov = atom(
        b"moov", atom(b"mvhd", bytes(100)) + atom(b"trak", atom(b"tkhd", bytes(84)))
    )
    return atom(b"ftyp", b"isom\x00\x00\x02\x00isom") + moov + atom(b"mdat", bytes(32))


def zip_fixture() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("picture.png", png_fixture())
        archive.writestr("picture.jpg", jpeg_fixture(False))
        archive.writestr("notes.txt", b"not media")
        for method in (zipfile.ZIP_LZMA, zipfile.ZIP_BZIP2):
            picture = jpeg_fixture(True) * 8
            archive.writestr(f"picture-{method}.jpg", picture, compress_type=method)
    return buffer.getvalue()


def container(data: bytes) -> str:
    if data[:2] == b"\xff\xd8":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[4:8] in (b"ftyp", b"moov", b"wide", b"mdat", b"free", b"skip"):
        return "iso"
    return "other"


# Each mutator returns the variant and a short description of what it did.
Mutator = Callable[[random.Random, bytes], tuple[bytes, str]]


def truncate(rng: random.Random, data: bytes) -> tuple[bytes, str]:
    cut = rng.randrange(0, len(data))
    return data[:cut], f"truncate at {cut}"


def extend(rng: random.Random, data: bytes) -> tuple[bytes, str]:
    tail = bytes(rng.randrange(256) for _ in range(rng.choice((1, 3, 7, 8, 64))))
    return data + tail, f"append {len(tail)} bytes"


def bit_flip(rng: random.Random, data: bytes) -> tuple[bytes, str]:
    out = bytearray(data)
    flips = rng.randrange(1, 9)
    for _ in range(flips):
        position = rng.randrange(len(out))
        out[position] ^= 1 << rng.randrange(8)
    return bytes(out), f"{flips} bit flips"


def smash(rng: random.Random, data: bytes) -> tuple[bytes, str]:
    """Overwrite a 2- or 4-byte field with a boundary value, where a length would sit."""
    width = rng.choice((2, 4))
    position = rng.randrange(max(1, len(data) - width))
    value = rng.choice((0, 1, 2, 7, 8, 0xFF, 0x7FFF, 0xFFFF, 0x7FFFFFFF, 0xFFFFFFFF))
    value &= (1 << (8 * width)) - 1
    fmt = rng.choice((">", "<")) + ("H" if width == 2 else "I")
    field = struct.pack(fmt, value)
    return data[:position] + field + data[
        position + width :
    ], f"smash {width} at {position}"


def splice(rng: random.Random, data: bytes) -> tuple[bytes, str]:
    position = rng.randrange(len(data) + 1)
    piece = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 17)))
    return data[:position] + piece + data[
        position:
    ], f"splice {len(piece)} at {position}"


def duplicate(rng: random.Random, data: bytes) -> tuple[bytes, str]:
    start = rng.randrange(len(data))
    end = min(len(data), start + rng.randrange(1, 257))
    return data[:end] + data[start:end] + data[end:], f"duplicate {start}:{end}"


MUTATORS: tuple[Mutator, ...] = (truncate, extend, bit_flip, smash, splice, duplicate)


def at_boundaries(
    data: bytes, parts: list, piece: bytes, what: str
) -> list[tuple[bytes, str]]:
    """Insert a piece before every parsed element, and once after the last."""
    offsets = sorted({start for _, start, _ in parts} | {len(data)})
    return [(data[:o] + piece + data[o:], f"{what} at {o}") for o in offsets]


def jpeg_clean_plants(data: bytes, parts: list) -> list[tuple[bytes, str]]:
    """JFIF and Adobe segments each holding values writers use, planted into a seed with no APP segments."""
    bare = data[:2] + b"".join(data[s:e] for m, s, e in parts if not 0xE0 <= m <= 0xEF)
    kept = [
        *(jpeg_segment(0xE0, bend(JFIF, 5, bytes((1, minor)))) for minor in range(3)),
        *(
            jpeg_segment(0xE0, bend(JFIF, 7, struct.pack(">BHH", units, dots, dots)))
            for units, dots in ((1, 72), (1, 96), (1, 300), (2, 28), (2, 118))
        ),
        *(jpeg_segment(0xEE, ADOBE[:11] + bytes((move,))) for move in range(3)),
    ]
    return [(bare[:2] + app + bare[2:], f"APP {app[4:].hex()}") for app in kept]


def gif_clean_plants(data: bytes, parts: list) -> list[tuple[bytes, str]]:
    """Looping and graphic control blocks each holding values writers use, before the first image of a seed with no extensions."""
    images = [s for k, s, _ in parts if k == "image"]
    if not images:
        return []
    bare = b"".join(
        data[s:e] for k, s, e in parts if not str(k).startswith("extension")
    )
    at = images[0] - sum(
        e - s for k, s, e in parts if str(k).startswith("extension") and s < images[0]
    )
    kept = [
        *(
            b"\x21\xff\x0bNETSCAPE2.0\x03\x01" + struct.pack("<H", loops) + b"\x00"
            for loops in (0, 1, 3, 65535)
        ),
        *(
            b"\x21\xf9\x04"
            + bytes((dispose << 2 | clear,))
            + struct.pack("<HB", delay, index)
            + b"\x00"
            for dispose, clear, delay, index in (
                (0, 0, 0, 0),
                (1, 0, 10, 0),
                (2, 1, 10, 1),
                (3, 1, 100, 1),
            )
        ),
    ]
    return [
        (bare[:at] + block + bare[at:], f"extension {block.hex()}") for block in kept
    ]


def webp_clean_plants(data: bytes, parts: list) -> list[tuple[bytes, str]]:
    """VP8X, ANIM and ANMF fields each holding values writers use, set in a seed that already carries the chunk."""
    out = []
    for name, start, _ in parts:
        body = start + 8
        if name == b"VP8X":
            flags = data[body] | 0x10
            variant = data[:body] + bytes((flags,)) + data[body + 1 :]
            out.append((variant, "VP8X alpha flag"))
        elif name == b"ANIM":
            for loops in (1, 3, 65535):
                variant = data[: body + 4] + struct.pack("<H", loops) + data[body + 6 :]
                out.append((variant, f"ANIM loop count {loops}"))
        elif name == b"ANMF":
            for duration, flags in ((0, 0), (40, 1), (100, 2), (0xFFFFFF, 3)):
                fields = duration.to_bytes(3, "little") + bytes((flags,))
                variant = data[: body + 12] + fields + data[body + 16 :]
                out.append((variant, f"ANMF duration {duration} flags {flags}"))
    return out


def clean_plants(kind: str, data: bytes) -> list[tuple[bytes, str]]:
    """Variants holding only values the gate admits, which it has to pass and the normalizer keep."""
    if kind == "png":
        return png_clean_plants(data, gate.png_parts(data)[0])
    if kind == "jpeg":
        return jpeg_clean_plants(data, gate.jpeg_parts(data)[0])
    if kind == "gif":
        return gif_clean_plants(data, gate.gif_parts(data)[0])
    if kind == "webp":
        return webp_clean_plants(data, gate.webp_parts(data)[0])
    return []


def plants(kind: str, data: bytes) -> list[tuple]:
    """Variants holding metadata a decoder reads, which the scanner has to report.

    A seed's own elements are where a decoder looks for the next one, so a piece planted
    before any of them, between two scans included, is one the decoder reads.
    """
    out: list[tuple] = []
    if kind == "jpeg":
        parts, _ = gate.jpeg_parts(data)
        comment = jpeg_segment(0xFE, PLANT_TEXT)
        out += [
            (variant, what, data)
            for variant, what in at_boundaries(data, parts, comment, "comment")
        ]
        # A shape plant goes into a seed with no APP segments, so that repetition cannot report it.
        bare = data[:2] + b"".join(
            data[s:e] for m, s, e in parts if not 0xE0 <= m <= 0xEF
        )
        # The planted Exif holds no Orientation, so dropping it leaves nothing to re-emit.
        gap = bare[:2] + exif_gap_segment() + bare[2:]
        out.append((gap, "bytes between Exif IFDs", bare))
        for entries, what in EXIF_BENT:
            bent = exif_ifd_segment(entries)
            out.append((bare[:2] + bent + bare[2:], f"Exif {what}", REWRITTEN))
        for segments, what, expect in JPEG_APP_BENT:
            out.append((bare[:2] + b"".join(segments) + bare[2:], what, expect))
        padded = exif_ifd_segment([ORIENTATION, (0x0132, 2, 20, DATE)], b"p")
        out.append((bare[:2] + padded + bare[2:], "Exif pad byte not zero", REWRITTEN))
        tailed = exif_segment(b"p")
        out.append(
            (bare[:2] + tailed + bare[2:], "Exif trailing pad byte not zero", REWRITTEN)
        )
        eoi = [s for m, s, _ in parts if m == 0xD9]
        if eoi:
            second = b"\xff\xd8" + SOF + SOS + PLANT_TEXT
            variant = data[: eoi[-1]] + second + data[eoi[-1] :]
            out.append((variant, "second stream", REFUSED))
            variant = data[: eoi[-1]] + SOF + data[eoi[-1] :]
            out.append((variant, "second frame header", REFUSED))
        for marker, start, end in parts:
            if marker != 0xE1 or data[start + 4 : start + 10] != b"Exif\x00\x00":
                continue
            length = struct.unpack_from(">H", data, start + 2)[0]
            tail = b"\xff\xd8" + PLANT_TEXT + b"\xff\xd9"
            grown = struct.pack(">H", length + len(tail))
            variant = data[: start + 2] + grown + data[start + 4 : end] + tail
            out.append((variant + data[end:], "bytes past the Exif IFDs", REWRITTEN))
        # A run of fill bytes has a length nothing reads, before a segment or after a scan alike.
        for at in (parts[1][1], *eoi) if len(parts) > 1 else ():
            variant = data[:at] + b"\xff" * 5 + data[at:]
            out.append((variant, "fill bytes before a marker", data))
        scans = [(s, e) for m, s, e in parts if m == 0xDA]
        restart = next(
            (hit.start() for s, e in scans for hit in RESTART.finditer(data, s, e)),
            None,
        )
        if restart is not None:
            variant = data[:restart] + b"\xff\xff" + data[restart:]
            out.append((variant, "fill bytes inside a scan", REFUSED))
    elif kind == "png":
        parts, _ = gate.png_parts(data)
        text = png_chunk(b"tEXt", b"Comment\x00" + PLANT_TEXT)
        texts = at_boundaries(data, parts[1:], text, "tEXt")
        # One between two IDAT chunks splits the picture data, which no decoder draws past.
        split = {
            f"tEXt at {start}"
            for (c, _, _), (d, start, _) in itertools.pairwise(parts)
            if c == d == b"IDAT"
        }
        out += [
            (variant, what, REFUSED if what in split else REWRITTEN)
            for variant, what in texts
        ]
        profile = png_chunk(b"iCCP", b"icc\x00\x00" + zlib.compress(PLANT_TEXT))
        variant = data[:33] + profile + data[33:]
        out.append((variant, "iCCP not a known profile", REFUSED))
        out += png_field_plants(data, parts)
        out += png_structure_plants(data, parts)
        out += png_stream_plants(data, parts)
    elif kind == "gif":
        parts, _ = gate.gif_parts(data)
        comment = b"\x21\xfe" + bytes((len(PLANT_TEXT),)) + PLANT_TEXT + b"\x00"
        out += [
            (variant, what, data)
            for variant, what in at_boundaries(data, parts[1:], comment, "comment")
        ]
        block = bytes((len(PLANT_TEXT),)) + PLANT_TEXT
        for name, _, end in parts:
            if str(name).startswith("extension"):
                variant = data[: end - 1] + block + data[end - 1 :]
                # A graphic control block sets transparency and timing, so it is refused rather than dropped.
                expect = REFUSED if name == "extension 0xF9" else REWRITTEN
                out.append((variant, f"sub-block inside {name}", expect))
        out += gif_field_plants(data, parts)
    elif kind == "webp":
        parts, _ = gate.webp_parts(data)
        chunk = riff_chunk(b"EXIF", PLANT_TEXT)
        out += [
            (with_riff_size(variant), what, data)
            for variant, what in at_boundaries(data, parts, chunk, "EXIF")
        ]
        out.append((data + PLANT_TEXT[:7], "bytes appended", data))
        frame = riff_chunk(b"VP8L", PLANT_TEXT)
        out.append((data + frame, "frame past the RIFF size", data))
        lossless = riff_chunk(b"VP8L", b"\x2f" + PLANT_TEXT)
        for name, start, end in parts:
            payload = start + 8 + struct.unpack_from("<I", data, start + 4)[0]
            if name == b"ANMF":
                held_at = start + 8 + gate.WEBP_FRAME_HEADER
                header = data[start + 8 : held_at]
                for held, what, expect in (
                    (data[held_at:payload] + chunk, "EXIF inside ANMF", data),
                    (
                        data[held_at:payload] + lossless,
                        "second image inside ANMF",
                        REFUSED,
                    ),
                    (b"", "ANMF with no image", REFUSED),
                ):
                    grown = riff_chunk(b"ANMF", header + held)
                    variant = with_riff_size(data[:start] + grown + data[end:])
                    out.append((variant, what, expect))
            if name in (b"VP8 ", b"VP8L"):
                variant = with_riff_size(data[:end] + lossless + data[end:])
                out.append((variant, "second image", REFUSED))
            # An ALPH draws only before a lossy image in a file with a VP8X, so that image takes no plant.
            extended = any(c == b"VP8X" for c, _, _ in parts)
            if name == b"VP8L" or (name == b"VP8 " and not extended):
                alpha = riff_chunk(b"ALPH", PLANT_TEXT)
                variant = with_riff_size(data[:start] + alpha + data[start:])
                what = (
                    "ALPH not before a lossy image" if extended else "ALPH with no VP8X"
                )
                out.append((variant, what, REFUSED))
            if name == b"ANIM" and payload - start - 8 == gate.WEBP_FIXED[name]:
                variant = data[: start + 8] + b"plnt" + data[start + 12 :]
                out.append((variant, "ANIM background not zero", data))
            if name == b"ANMF":
                header = data[start + 8 : start + 8 + gate.WEBP_FRAME_HEADER]
                # The normalizer keeps a frame header as it is, so one out of its values is refused.
                for field, value, what in (
                    (15, b"p", "ANMF reserved bits not zero"),
                    (0, b"pla", "ANMF frame outside the canvas"),
                ):
                    moved = bend(header, field, value)
                    variant = data[: start + 8] + moved
                    variant += data[start + 8 + gate.WEBP_FRAME_HEADER :]
                    out.append((variant, what, REFUSED))
            if name == b"VP8X":
                flags = data[start + 8]
                for value, what, expect in (
                    (
                        bytes((flags | 0x01,)) + b"pla",
                        "VP8X reserved bits not zero",
                        data,
                    ),
                    (bytes((flags | 0x0C,)), "VP8X flags a chunk never admitted", data),
                    (
                        bytes((flags ^ 0x20,)),
                        "VP8X ICC flag without its chunk",
                        REFUSED,
                    ),
                    (
                        bytes((flags ^ 0x02,)),
                        "VP8X animation flag without its chunks",
                        REFUSED,
                    ),
                ):
                    variant = data[: start + 8] + value + data[start + 8 + len(value) :]
                    out.append((variant, what, expect))
                profile = riff_chunk(b"ICCP", PLANT_TEXT)
                flagged = bytes((flags | 0x20,))
                variant = data[: start + 8] + flagged + data[start + 9 : end]
                variant = with_riff_size(variant + profile + data[end:])
                out.append((variant, "ICCP not a known profile", REFUSED))
            length = struct.unpack_from("<I", data, start + 4)[0]
            if length & 1 and name in gate.WEBP_ALLOWED:
                variant = data[: end - 1] + b"p" + data[end:]
                out.append((variant, f"{name.decode()} pad byte not zero", data))
            if name in (b"VP8X", b"ANIM"):
                grown = riff_chunk(name, data[start + 8 : payload] + PLANT_TEXT)
                variant = with_riff_size(data[:start] + grown + data[end:])
                what = f"{name.decode()} with bytes past its fields"
                out.append((variant, what, REFUSED))
                again = riff_chunk(
                    name, (PLANT_TEXT + bytes(10))[: payload - start - 8]
                )
                variant = with_riff_size(data[:end] + again + data[end:])
                out.append((variant, f"repeated {name.decode()}", REFUSED))
        if any(name == b"ANMF" for name, _, _ in parts):
            variant = with_riff_size(data + lossless)
            out.append((variant, "image beside the frames", REFUSED))
    elif kind == "iso":
        out.append((data + atom(b"udta", PLANT_TEXT), "udta atom appended"))
        deep = atom(b"udta", PLANT_TEXT)
        for _ in range(3000):
            deep = atom(b"moov", deep)
        out.append((data + deep, "deeply nested moov"))
    return out if len(out) <= 64 else out[:32] + out[-32:]


def orientation_tiff(
    order: bytes, kind: int, first: int = 6, then: int = 0, sub: bool = False
) -> bytes:
    """A TIFF header and one IFD holding Orientation `first` as the given type, or none where it is 0.

    A nonzero `then` adds a second Orientation SHORT holding that value,
    in the Exif sub-IFD where `sub` is set and in the same IFD otherwise.
    """
    fmt = "<" if order == b"II" else ">"
    if kind == 3:
        value = struct.pack(fmt + "HH", first, 0)
    else:
        value = struct.pack(fmt + "I", first)
    entries = [struct.pack(fmt + "HHI", 0x0112, kind, 1) + value] if first else []
    second = struct.pack(fmt + "HHIHH", 0x0112, 3, 1, then, 0) if then else b""
    tail = b""
    if sub:
        at = 8 + 2 + 12 * (len(entries) + 1) + 4
        entries.append(struct.pack(fmt + "HHII", 0x8769, 4, 1, at))
        tail = struct.pack(fmt + "H", len(second) // 12) + second
        tail += struct.pack(fmt + "I", 0)
    elif second:
        entries.append(second)
    head = order + struct.pack(fmt + "HIH", 42, 8, len(entries))
    return head + b"".join(entries) + struct.pack(fmt + "I", 0) + tail


# Each pair disagrees, and each order changed what a decoder taking the last entry reads.
DISPUTED = ((6, 8), (1, 6))
# Where the second value sits in the Exif sub-IFD, each order changed what a flattening decoder reads.
PLACES = ((False, "then"), (True, "then in the sub-IFD"))


def turned(kind: str, data: bytes) -> list[tuple[bytes, str, int | None]]:
    """Variants whose Exif turns the picture a quarter turn, as Orientation 6 does.

    Each carries the Orientation the normalized file must hold, or None for a turn decoders
    disagree on, which only a refusal keeps.
    """
    out: list[tuple[bytes, str, int | None]] = []
    if kind == "jpeg":
        parts, _ = gate.jpeg_parts(data)
        bare = data[:2] + b"".join(
            data[s:e] for m, s, e in parts if not 0xE0 <= m <= 0xEF
        )
        for order, size, what in (
            (b"MM", 4, "Orientation as a big-endian LONG"),
            (b"II", 4, "Orientation as a little-endian LONG"),
            (b"MM", 3, "Orientation as a big-endian SHORT"),
        ):
            segment = jpeg_segment(
                0xE1, b"Exif\x00\x00" + orientation_tiff(order, size)
            )
            out.append((bare[:2] + segment + bare[2:], what, None if size == 4 else 6))
        for (first, then), (sub, place) in itertools.product(
            (*DISPUTED, (6, 6)), PLACES
        ):
            tiff = orientation_tiff(b"II", 3, first, then, sub)
            segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
            what = f"Orientation {first} {place} {then}"
            out.append(
                (bare[:2] + segment + bare[2:], what, None if first != then else 6)
            )
        # An IFD0 saying nothing reads as upright in a browser, so a turn held only elsewhere is disputed.
        tiff = orientation_tiff(b"II", 3, 0, 6, sub=True)
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        out.append(
            (bare[:2] + segment + bare[2:], "Orientation 6 in the sub-IFD alone", None)
        )
        # A zeroed pointer points at the header, whose bytes read as an IFD of thousands of entries.
        ifd0 = struct.pack("<HHIHH", 0x0112, 3, 1, 6, 0)
        ifd0 += struct.pack("<HHII", 0x8825, 4, 1, 0)
        tiff = b"II" + struct.pack("<HIH", 42, 8, 2) + ifd0 + struct.pack("<I", 0)
        tiff += struct.pack("<H", 0x0112) + bytes(10)
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        out.append(
            (bare[:2] + segment + bare[2:], "Orientation 6 by a zeroed pointer", 6)
        )
        # The gate reads at most 16 IFDs, so pointers it skips must not use up the reader's 16 first.
        bad = (*range(1, 8), *range(0xFFFF0000, 0xFFFF0008))
        at = 8 + 2 + 12 * (2 + len(bad)) + 4
        ifd0 = struct.pack("<HHIHH", 0x0112, 3, 1, 6, 0)
        ifd0 += struct.pack("<HHII", 0x8769, 4, 1, at)
        ifd0 += b"".join(struct.pack("<HHII", 0x8769, 4, 1, off) for off in bad)
        tiff = b"II" + struct.pack("<HIH", 42, 8, 2 + len(bad)) + ifd0
        tiff += struct.pack("<I", 0) + struct.pack("<H", 1)
        tiff += struct.pack("<HHIHHI", 0x0112, 3, 1, 8, 0, 0)
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 then in the sub-IFD 8 behind skipped pointers"
        out.append((bare[:2] + segment + bare[2:], what, None))
        # An IFD0 inside the TIFF header is no IFD to one decoder and a long one to another.
        tiff = b"II" + struct.pack("<HI", 42, 0) + bytes(6)
        tiff += struct.pack("<HHIHHI", 0x0112, 3, 1, 6, 0, 0)
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 spelled by an IFD0 inside the header"
        out.append((bare[:2] + segment + bare[2:], what, None))
        # An IFD0 cut short by the segment is read in part by some decoders and not at all by others.
        tiff = b"II" + struct.pack("<HIH", 42, 8, 2)
        tiff += struct.pack("<HHIHH", 0x0112, 3, 1, 6, 0)
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 in an IFD0 cut short"
        out.append((bare[:2] + segment + bare[2:], what, None))
        # An IFD0 missing only its next-IFD pointer still holds every entry whole.
        tiff = b"II" + struct.pack("<HIH", 42, 8, 1)
        tiff += struct.pack("<HHIHH", 0x0112, 3, 1, 6, 0)
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 in an IFD0 missing its next pointer"
        out.append((bare[:2] + segment + bare[2:], what, 6))
        # A pointer that fits in an IFD0 cut short reaches a turn only some decoders read.
        tiff = b"II" + struct.pack("<HI", 42, 26) + struct.pack("<H", 1)
        tiff += struct.pack("<HHIHHI", 0x0112, 3, 1, 6, 0, 0)
        tiff += struct.pack("<H", 5) + struct.pack("<HHII", 0x8769, 4, 1, 8)
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 behind a pointer in an IFD0 cut short"
        out.append((bare[:2] + segment + bare[2:], what, None))
        # A last entry cut off after its value still spells a turn to a decoder reading what it can.
        tiff = b"II" + struct.pack("<HIH", 42, 8, 1)
        tiff += struct.pack("<HHIH", 0x0112, 3, 1, 6)
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 in an IFD0 entry cut off"
        out.append((bare[:2] + segment + bare[2:], what, None))
        # A sub-IFD cut short by the segment is read in part by some decoders and not at all by others.
        tiff = b"II" + struct.pack("<HIH", 42, 8, 1)
        tiff += struct.pack("<HHII", 0x8769, 4, 1, 26) + struct.pack("<I", 0)
        tiff += struct.pack("<H", 2) + struct.pack("<HHIHH", 0x0112, 3, 1, 6, 0)
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 in a sub-IFD cut short"
        out.append((bare[:2] + segment + bare[2:], what, None))
        # A sub-IFD missing only its next-IFD pointer still holds every entry whole.
        for first, shown in ((0, None), (6, 6)):
            tiff = orientation_tiff(b"II", 3, first, 6, sub=True)[:-4]
            segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
            where = "alone" if not first else "in IFD0 and"
            what = f"Orientation 6 {where} in a sub-IFD missing its next pointer"
            out.append((bare[:2] + segment + bare[2:], what, shown))
        # A sub-IFD cut short that agrees with IFD0 reads the same whether a decoder reads it or not.
        tiff = orientation_tiff(b"II", 3, 6, 6, sub=True)[:-4]
        tiff = tiff[:-14] + struct.pack("<H", 3) + tiff[-12:]
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 in IFD0 and in a sub-IFD cut short"
        out.append((bare[:2] + segment + bare[2:], what, 6))
        # What a sub-IFD cut short leads to is walked apart from the 16 IFDs the gate reads.
        ifd0 = struct.pack("<HHIHH", 0x0112, 3, 1, 6, 0)
        ifd0 += struct.pack("<HHII", 0x8825, 4, 1, 50)
        ifd0 += struct.pack("<HHII", 0x8769, 4, 1, 68)
        tiff = b"II" + struct.pack("<HIH", 42, 8, 3) + ifd0 + struct.pack("<I", 0)
        tiff += struct.pack("<H", 1) + struct.pack("<HHIHHI", 0x0112, 3, 1, 8, 0, 0)
        empty = 68 + 2 + 14 * 12
        tiff += struct.pack("<H", 40) + b"".join(
            struct.pack("<HHII", 0x8769, 4, 1, empty + 6 * n) for n in range(14)
        )
        tiff += struct.pack("<HI", 0, 0) * 14
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 then in the GPS IFD 8 behind a sub-IFD cut short"
        out.append((bare[:2] + segment + bare[2:], what, None))
        # An IFD a sub-IFD cut short reaches first is walked again when a clean path reaches it.
        link = 50 + 18
        empty = link + 18
        cut = empty + 6 * 15
        ifd0 = struct.pack("<HHIHH", 0x0112, 3, 1, 6, 0)
        ifd0 += struct.pack("<HHII", 0x8825, 4, 1, 50)
        ifd0 += struct.pack("<HHII", 0x8769, 4, 1, cut)
        tiff = b"II" + struct.pack("<HIH", 42, 8, 3) + ifd0 + struct.pack("<I", 0)
        tiff += struct.pack("<H", 1) + struct.pack("<HHIII", 0xA005, 4, 1, link, 0)
        tiff += struct.pack("<H", 1) + struct.pack("<HHIHHI", 0x0112, 3, 1, 8, 0, 0)
        tiff += struct.pack("<HI", 0, 0) * 15
        tiff += struct.pack("<H", 60) + struct.pack("<HHII", 0x8769, 4, 1, 50)
        tiff += b"".join(
            struct.pack("<HHII", 0xA005, 4, 1, empty + 6 * n) for n in range(15)
        )
        segment = jpeg_segment(0xE1, b"Exif\x00\x00" + tiff)
        what = "Orientation 6 then 8 behind an IFD a sub-IFD cut short reaches first"
        out.append((bare[:2] + segment + bare[2:], what, None))
    elif kind == "png":
        out.append(
            (
                data[:33] + png_chunk(b"eXIf", orientation_tiff(b"II", 3)) + data[33:],
                "eXIf with Orientation",
                6,
            )
        )
        for (first, then), (sub, place) in itertools.product(DISPUTED, PLACES):
            chunk = png_chunk(b"eXIf", orientation_tiff(b"II", 3, first, then, sub))
            what = f"eXIf Orientation {first} {place} {then}"
            out.append((data[:33] + chunk + data[33:], what, None))
    elif kind == "webp":
        out.append(
            (
                with_riff_size(data + riff_chunk(b"EXIF", orientation_tiff(b"II", 3))),
                "EXIF with Orientation",
                6,
            )
        )
        for (first, then), (sub, place) in itertools.product(DISPUTED, PLACES):
            chunk = riff_chunk(b"EXIF", orientation_tiff(b"II", 3, first, then, sub))
            what = f"EXIF Orientation {first} {place} {then}"
            out.append((with_riff_size(data + chunk), what, None))
    return out


def orientation(kind: str, data: bytes) -> int | None:
    """The Orientation the first Exif in a file holds, 1 where it holds none, or None where disputed."""
    held = []
    if kind == "jpeg":
        parts, _ = gate.jpeg_parts(data)
        held = [data[s + 4 : e] for m, s, e in parts if m == 0xE1]
        held = [h for h in held if h.startswith(b"Exif\x00\x00")]
    elif kind == "png":
        parts, _ = gate.png_parts(data)
        held = [data[s + 8 : e - 4] for c, s, e in parts if c == b"eXIf"]
    elif kind == "webp":
        parts, _ = gate.webp_parts(data)
        held = [data[s + 8 : e] for c, s, e in parts if c == b"EXIF"]
    return normalizer.exif_orientation(held[0]) if held else 1


class Report:
    def __init__(self) -> None:
        self.cases = 0
        self.failures: dict[tuple[str, str, str], tuple[int, str]] = {}

    def fail(self, prop: str, kind: str, detail: str, where: str) -> None:
        key = (prop, kind, re.sub(r"0x[0-9A-F]+", "0x..", detail))
        count, first = self.failures.get(key, (0, where))
        self.failures[key] = (count + 1, first)


def attempt(call: Callable[[], object]) -> tuple[object, str | None]:
    """Run one parser call, returning its result or the name of what it raised."""
    try:
        return call(), None
    except Exception as exc:  # noqa: BLE001
        return None, type(exc).__name__


def check_variant(report: Report, kind: str, data: bytes, where: str) -> None:
    report.cases += 1
    _, raised = attempt(lambda: gate.scan(data))
    if raised:
        report.fail("1 scanner raised", kind, raised, where)
    new, raised = attempt(lambda: normalizer.normalize_bytes(data))
    if raised:
        report.fail("2 normalizer raised", kind, raised, where)
    if not isinstance(new, bytes) or not new:
        return
    again, raised = attempt(lambda: gate.scan(new))
    if raised:
        report.fail("1 scanner raised on normalized output", kind, raised, where)
    elif again:
        detail = ", ".join(sorted(again))
        report.fail("2 normalizer output rejected", kind, detail, where)
    payloads, raised = attempt(
        lambda: (normalizer.pixel_payload(data), normalizer.pixel_payload(new))
    )
    if raised:
        report.fail("3 payload extraction raised", kind, raised, where)
    elif payloads[0] is not None and payloads[0] != payloads[1]:
        report.fail("3 normalizer changed the payload", kind, "", where)


def check_plant(
    report: Report,
    kind: str,
    data: bytes,
    where: str,
    expect: str | bytes | None = None,
) -> None:
    report.cases += 1
    found, raised = attempt(lambda: gate.scan(data))
    what = re.sub(r" at \d+$", "", where.split(": ", 1)[-1])
    if raised:
        report.fail("1 scanner raised", kind, raised, where)
    elif not found:
        report.fail("4 planted metadata passed", kind, what, where)
    new, raised = attempt(lambda: normalizer.normalize_bytes(data))
    if raised:
        report.fail("2 normalizer raised", kind, raised, where)
        return
    rewritten = isinstance(new, bytes) and bool(new)
    if expect == REFUSED and rewritten:
        report.fail("4 normalizer rewrote a plant it should refuse", kind, what, where)
    elif expect not in (None, REFUSED) and not rewritten:
        report.fail("4 normalizer refused a plant it should rewrite", kind, what, where)
    elif isinstance(expect, bytes) and rewritten and new != expect:
        report.fail(
            "4 normalizer rewrote a plant other than declared", kind, what, where
        )
    if isinstance(new, bytes) and PLANT_TEXT in new:
        report.fail("4 normalizer kept planted metadata", kind, what, where)
    elif rewritten:
        again, raised = attempt(lambda: gate.scan(new))
        if raised:
            report.fail("1 scanner raised on normalized output", kind, raised, where)
        elif again:
            detail = ", ".join(sorted(again))
            report.fail("2 normalizer output rejected", kind, detail, where)
        payloads, raised = attempt(
            lambda: (normalizer.pixel_payload(data), normalizer.pixel_payload(new))
        )
        if raised:
            report.fail("3 payload extraction raised", kind, raised, where)
        elif payloads[0] is not None and payloads[0] != payloads[1]:
            report.fail("3 normalizer changed the payload", kind, what, where)


def check_clean(report: Report, kind: str, data: bytes, where: str) -> None:
    report.cases += 1
    what = where.split(": ", 1)[-1]
    found, raised = attempt(lambda: gate.scan(data))
    if raised:
        report.fail("1 scanner raised", kind, raised, where)
    elif found:
        report.fail("7 clean plant reported", kind, ", ".join(sorted(found)), where)
    new, raised = attempt(lambda: normalizer.normalize_bytes(data))
    if raised:
        report.fail("2 normalizer raised", kind, raised, where)
    elif not isinstance(new, bytes) or not new:
        report.fail("7 normalizer refused a clean plant", kind, what, where)
    elif new != data:
        report.fail("7 normalizer changed a clean plant", kind, what, where)


def check_turn(
    report: Report, kind: str, data: bytes, where: str, shown: int | None
) -> None:
    report.cases += 1
    disputed = shown is None
    what = where.split(": ", 1)[-1]
    found, raised = attempt(lambda: gate.scan(data))
    if raised:
        report.fail("1 scanner raised", kind, raised, where)
    elif disputed and not found:
        report.fail("4 gate admitted a disputed orientation", kind, what, where)
    new, raised = attempt(lambda: normalizer.normalize_bytes(data))
    if raised:
        report.fail("2 normalizer raised", kind, raised, where)
        return
    if isinstance(new, bytes) and new:
        again, raised = attempt(lambda: gate.scan(new))
        if raised:
            report.fail("1 scanner raised on normalized output", kind, raised, where)
        elif again:
            detail = ", ".join(sorted(again))
            report.fail("2 normalizer output rejected", kind, detail, where)
    if disputed and isinstance(new, bytes) and new:
        report.fail("6 normalizer settled a disputed orientation", kind, what, where)
    elif kind == "jpeg" and not disputed and not new:
        # Only PNG and WebP refuse a turn, since a JPEG can carry one without its other Exif.
        report.fail("6 normalizer refused an undisputed orientation", kind, what, where)
    elif kind in ("png", "webp") and shown != 1 and new:
        # A PNG or WebP keeps no Exif, so only a refusal keeps its turn.
        report.fail("6 normalizer settled a PNG or WebP turn", kind, what, where)
    elif isinstance(new, bytes) and new:
        kept, raised = attempt(lambda: orientation(kind, new))
        if raised or kept != shown:
            report.fail("6 normalizer lost the orientation", kind, what, where)


def check_archive(
    report: Report, data: bytes, where: str, scratch: pathlib.Path
) -> None:
    report.cases += 1
    path = scratch / "fuzz.zip"
    path.write_bytes(data)
    _, raised = attempt(lambda: gate.walk_archive(path, "fuzz.zip"))
    if raised:
        report.fail("5 archive walk raised", "zip", raised, where)
    with contextlib.redirect_stdout(io.StringIO()):
        _, raised = attempt(lambda: normalizer.normalize_archive(path, False))
    if raised:
        report.fail("5 archive normalize raised", "zip", raised, where)


def carried_seeds(
    rng: random.Random, per_kind: int, max_size: int
) -> list[tuple[str, bytes]]:
    """A deterministic sample of the carried media, capped in size so the run stays fast."""
    by_kind: dict[str, list[pathlib.Path]] = {}
    for tree in gate.TREES:
        root = REPO / tree
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*"), key=pathlib.Path.as_posix):
            if path.is_symlink() or not path.is_file() or path.suffix.lower() == ".zip":
                continue
            if path.stat().st_size > max_size:
                continue
            with path.open("rb") as handle:
                kind = container(handle.read(12))
            by_kind.setdefault(kind, []).append(path)
    seeds = []
    for kind in sorted(by_kind):
        paths = by_kind[kind]
        for path in rng.sample(paths, min(per_kind, len(paths))):
            seeds.append((str(path.relative_to(REPO)), path.read_bytes()))
    return seeds


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=173, help="random seed")
    parser.add_argument("--cases", type=int, default=400, help="variants per seed file")
    parser.add_argument(
        "--per-kind", type=int, default=6, help="carried files per container"
    )
    parser.add_argument(
        "--max-size", type=int, default=512 * 1024, help="largest carried seed"
    )
    parser.add_argument(
        "--budget", type=float, default=90.0, help="seconds before stopping"
    )
    parser.add_argument(
        "--min-cases",
        type=int,
        default=4000,
        help="fewest cases a run the time budget cut short may pass with",
    )
    parser.add_argument(
        "--no-carried", action="store_true", help="constructed fixtures only"
    )
    args = parser.parse_args()

    warnings.simplefilter("ignore")
    rng = random.Random(args.seed)
    seeds = [
        ("fixture:jpeg", jpeg_fixture(False)),
        ("fixture:jpeg-progressive", jpeg_fixture(True)),
        ("fixture:jpeg-dated", dated_jpeg_fixture()),
        ("fixture:png", png_fixture()),
        ("fixture:png-palette", palette_png_fixture()),
        ("fixture:png-truecolor", truecolor_png_fixture()),
        ("fixture:png-small", small_png_fixture()),
        ("fixture:gif", gif_fixture()),
        ("fixture:webp", webp_fixture()),
        ("fixture:webp-animated", animated_webp_fixture()),
        ("fixture:iso", iso_fixture()),
    ]
    if not args.no_carried:
        seeds += carried_seeds(rng, args.per_kind, args.max_size)

    report = Report()
    deadline = time.monotonic() + args.budget
    archive = zip_fixture()
    with tempfile.TemporaryDirectory() as scratch:
        for _ in range(args.cases):
            if time.monotonic() > deadline:
                break
            variant, what = rng.choice(MUTATORS)(rng, archive)
            check_archive(
                report, variant, f"fixture:zip: {what}", pathlib.Path(scratch)
            )
    for label, data in seeds:
        kind = container(data)
        check_variant(report, kind, data, f"{label}: unmodified")
        if label.startswith("fixture:"):
            found, raised = attempt(functools.partial(gate.scan, data))
            if not raised and found:
                detail = ", ".join(sorted(found))
                report.fail("0 fixture not clean", kind, detail, label)
        # Planting and turning split the seed with the gate's parsers and this file's own code.
        planted, raised = attempt(functools.partial(plants, kind, data))
        if raised:
            report.fail("0 variants not built", kind, f"plants {raised}", label)
        turns, raised = attempt(functools.partial(turned, kind, data))
        if raised:
            report.fail("0 variants not built", kind, f"turned {raised}", label)
        for variant, what, *expect in planted or []:
            check_plant(report, kind, variant, f"{label}: {what}", *expect)
        kept, raised = attempt(functools.partial(clean_plants, kind, data))
        if raised:
            report.fail("0 variants not built", kind, f"clean {raised}", label)
        for variant, what in kept or []:
            check_clean(report, kind, variant, f"{label}: {what}")
        for variant, what, shown in turns or []:
            check_turn(report, kind, variant, f"{label}: {what}", shown)
        for _ in range(args.cases):
            if time.monotonic() > deadline:
                break
            mutate = rng.choice(MUTATORS)
            variant, what = mutate(rng, data)
            check_variant(report, kind, variant, f"{label}: {what}")
    stopped = time.monotonic() > deadline

    for (prop, kind, detail), (count, first) in sorted(report.failures.items()):
        suffix = f" ({detail})" if detail else ""
        print(f"{prop}: {kind}{suffix}, {count} case(s), first {first}")
    budget = ", stopped at the time budget" if stopped else ""
    print(f"\nfuzz    : {report.cases} case(s) over {len(seeds)} seed(s){budget}")
    short = stopped and report.cases < args.min_cases
    if short:
        print(f"the time budget stopped the run below {args.min_cases} case(s)")
    if report.failures:
        print(f"{len(report.failures)} distinct failure(s)")
    return 1 if report.failures or short else 0


if __name__ == "__main__":
    sys.exit(main())
