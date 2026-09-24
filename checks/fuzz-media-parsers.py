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
5. The archive walk never raises on a damaged archive.
6. The normalizer refuses a picture its Exif turns, or returns one turned the same way.

Seeds are constructed fixtures plus a sample of the carried media, read in memory and
never written anywhere. The run is deterministic for a given seed and file list, and
bounded by both a case count and a time budget, so it can run in CI.
"""

import argparse
import contextlib
import importlib.util
import io
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
from collections.abc import Callable

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


ICC = b"ICC_PROFILE\x00\x01\x01"
SOF = jpeg_segment(0xC0, b"\x08\x00\x08\x00\x08\x01\x01\x11\x00")
SOS = jpeg_segment(0xDA, b"\x01\x01\x00\x00\x3f\x00")

# APP segments each already allowed alone, planted so that their shape or repetition carries bytes.
JPEG_APP_BENT = (
    ([jpeg_segment(0xE0, JFIF + PLANT_TEXT)], "JFIF with bytes past its fields"),
    (
        [jpeg_segment(0xE0, JFIF[:12] + b"\x03\x01" + PLANT_TEXT + b"\x00\x00")],
        "JFIF thumbnail",
    ),
    ([jpeg_segment(0xEE, ADOBE + PLANT_TEXT)], "Adobe with bytes past its fields"),
    ([jpeg_segment(0xE0, JFIF)] * 2, "repeated JFIF"),
    ([jpeg_segment(0xEE, ADOBE)] * 2, "repeated Adobe"),
    ([exif_segment()] * 8, "repeated Exif"),
    (
        [jpeg_segment(0xE2, ICC + bytes(8)), jpeg_segment(0xE2, ICC + PLANT_TEXT)],
        "repeated ICC chunk",
    ),
    (
        [jpeg_segment(0xE2, ICC[:12] + b"\x01\x03" + PLANT_TEXT)],
        "incomplete ICC profile",
    ),
    ([jpeg_segment(0xE2, ICC + PLANT_TEXT)], "ICC profile not a known profile"),
    ([jpeg_segment(0xE0, bend(JFIF, 5, b"pl"))], "JFIF version not a known version"),
    ([jpeg_segment(0xE0, bend(JFIF, 7, b"p"))], "JFIF units not a known unit"),
    ([jpeg_segment(0xE0, bend(JFIF, 8, b"plan"))], "JFIF density not square"),
    ([jpeg_segment(0xEE, bend(ADOBE, 5, b"pl"))], "Adobe version not 100"),
    ([jpeg_segment(0xEE, bend(ADOBE, 7, b"plan"))], "Adobe flags not zero"),
    ([jpeg_segment(0xEE, bend(ADOBE, 11, b"p"))], "Adobe transform not a known one"),
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


def plants(kind: str, data: bytes) -> list[tuple[bytes, str]]:
    """Variants holding metadata a decoder reads, which the scanner has to report.

    A seed's own elements are where a decoder looks for the next one, so a piece planted
    before any of them, between two scans included, is one the decoder reads.
    """
    out: list[tuple[bytes, str]] = []
    if kind == "jpeg":
        parts, _ = gate.jpeg_parts(data)
        comment = jpeg_segment(0xFE, PLANT_TEXT)
        out += at_boundaries(data, parts, comment, "comment")
        out.append(
            (data[:2] + exif_gap_segment() + data[2:], "bytes between Exif IFDs")
        )
        # A shape plant goes into a seed with no APP segments, so that repetition cannot report it.
        bare = data[:2] + b"".join(
            data[s:e] for m, s, e in parts if not 0xE0 <= m <= 0xEF
        )
        for entries, what in EXIF_BENT:
            bent = exif_ifd_segment(entries)
            out.append((bare[:2] + bent + bare[2:], f"Exif {what}"))
        for segments, what in JPEG_APP_BENT:
            out.append((bare[:2] + b"".join(segments) + bare[2:], what))
        padded = exif_ifd_segment([ORIENTATION, (0x0132, 2, 20, DATE)], b"p")
        out.append((bare[:2] + padded + bare[2:], "Exif pad byte not zero"))
        tailed = exif_segment(b"p")
        out.append((bare[:2] + tailed + bare[2:], "Exif trailing pad byte not zero"))
        eoi = [s for m, s, _ in parts if m == 0xD9]
        if eoi:
            second = b"\xff\xd8" + SOF + SOS + PLANT_TEXT
            out.append((data[: eoi[-1]] + second + data[eoi[-1] :], "second stream"))
            out.append((data[: eoi[-1]] + SOF + data[eoi[-1] :], "second frame header"))
        for marker, start, end in parts:
            if marker != 0xE1 or data[start + 4 : start + 10] != b"Exif\x00\x00":
                continue
            length = struct.unpack_from(">H", data, start + 2)[0]
            tail = b"\xff\xd8" + PLANT_TEXT + b"\xff\xd9"
            grown = struct.pack(">H", length + len(tail))
            variant = data[: start + 2] + grown + data[start + 4 : end] + tail
            out.append((variant + data[end:], "bytes past the Exif IFDs"))
    elif kind == "png":
        parts, _ = gate.png_parts(data)
        text = png_chunk(b"tEXt", b"Comment\x00" + PLANT_TEXT)
        out += at_boundaries(data, parts[1:], text, "tEXt")
        profile = png_chunk(b"iCCP", b"icc\x00\x00" + zlib.compress(PLANT_TEXT))
        out.append((data[:33] + profile + data[33:], "iCCP not a known profile"))
    elif kind == "gif":
        parts, _ = gate.gif_parts(data)
        comment = b"\x21\xfe" + bytes((len(PLANT_TEXT),)) + PLANT_TEXT + b"\x00"
        out += at_boundaries(data, parts[1:], comment, "comment")
        block = bytes((len(PLANT_TEXT),)) + PLANT_TEXT
        for name, _, end in parts:
            if str(name).startswith("extension"):
                variant = data[: end - 1] + block + data[end - 1 :]
                out.append((variant, f"sub-block inside {name}"))
    elif kind == "webp":
        parts, _ = gate.webp_parts(data)
        chunk = riff_chunk(b"EXIF", PLANT_TEXT)
        out += [
            (with_riff_size(variant), what)
            for variant, what in at_boundaries(data, parts, chunk, "EXIF")
        ]
        out.append((data + PLANT_TEXT[:7], "bytes appended"))
        frame = riff_chunk(b"VP8L", PLANT_TEXT)
        out.append((data + frame, "frame past the RIFF size"))
        lossless = riff_chunk(b"VP8L", b"\x2f" + PLANT_TEXT)
        for name, start, end in parts:
            payload = start + 8 + struct.unpack_from("<I", data, start + 4)[0]
            if name == b"ANMF":
                held_at = start + 8 + gate.WEBP_FRAME_HEADER
                header = data[start + 8 : held_at]
                for held, what in (
                    (data[held_at:payload] + chunk, "EXIF inside ANMF"),
                    (data[held_at:payload] + lossless, "second image inside ANMF"),
                    (b"", "ANMF with no image"),
                ):
                    grown = riff_chunk(b"ANMF", header + held)
                    variant = with_riff_size(data[:start] + grown + data[end:])
                    out.append((variant, what))
            if name in (b"VP8 ", b"VP8L"):
                variant = with_riff_size(data[:end] + lossless + data[end:])
                out.append((variant, "second image"))
                alpha = riff_chunk(b"ALPH", PLANT_TEXT)
                variant = with_riff_size(data[:start] + alpha + data[start:])
                out.append((variant, "ALPH not before a lossy image"))
            if name == b"ANMF":
                header = data[start + 8 : start + 8 + gate.WEBP_FRAME_HEADER]
                for field, value, what in (
                    (15, b"p", "ANMF reserved bits not zero"),
                    (0, b"pla", "ANMF frame outside the canvas"),
                ):
                    moved = bend(header, field, value)
                    variant = data[: start + 8] + moved
                    variant += data[start + 8 + gate.WEBP_FRAME_HEADER :]
                    out.append((variant, what))
            if name == b"VP8X":
                flags = data[start + 8]
                for value, what in (
                    (bytes((flags | 0x01,)) + b"pla", "VP8X reserved bits not zero"),
                    (bytes((flags | 0x0C,)), "VP8X flags a chunk never admitted"),
                    (bytes((flags ^ 0x20,)), "VP8X ICC flag without its chunk"),
                    (bytes((flags ^ 0x02,)), "VP8X animation flag without its chunks"),
                ):
                    variant = data[: start + 8] + value + data[start + 8 + len(value) :]
                    out.append((variant, what))
                profile = riff_chunk(b"ICCP", PLANT_TEXT)
                flagged = bytes((flags | 0x20,))
                variant = data[: start + 8] + flagged + data[start + 9 : end]
                variant = with_riff_size(variant + profile + data[end:])
                out.append((variant, "ICCP not a known profile"))
            length = struct.unpack_from("<I", data, start + 4)[0]
            if length & 1 and name in gate.WEBP_ALLOWED:
                variant = data[: end - 1] + b"p" + data[end:]
                out.append((variant, f"{name.decode()} pad byte not zero"))
            if name in (b"VP8X", b"ANIM"):
                grown = riff_chunk(name, data[start + 8 : payload] + PLANT_TEXT)
                variant = with_riff_size(data[:start] + grown + data[end:])
                out.append((variant, f"{name.decode()} with bytes past its fields"))
                again = riff_chunk(
                    name, (PLANT_TEXT + bytes(10))[: payload - start - 8]
                )
                variant = with_riff_size(data[:end] + again + data[end:])
                out.append((variant, f"repeated {name.decode()}"))
        if any(name == b"ANMF" for name, _, _ in parts):
            variant = with_riff_size(data + lossless)
            out.append((variant, "image beside the frames"))
    elif kind == "iso":
        out.append((data + atom(b"udta", PLANT_TEXT), "udta atom appended"))
        deep = atom(b"udta", PLANT_TEXT)
        for _ in range(3000):
            deep = atom(b"moov", deep)
        out.append((data + deep, "deeply nested moov"))
    return out if len(out) <= 64 else out[:32] + out[-32:]


def orientation_tiff(order: bytes, kind: int) -> bytes:
    """A TIFF header and one IFD holding Orientation 6 as the given type."""
    fmt = "<" if order == b"II" else ">"
    value = struct.pack(fmt + "HH", 6, 0) if kind == 3 else struct.pack(fmt + "I", 6)
    entry = struct.pack(fmt + "HHI", 0x0112, kind, 1) + value
    head = order + struct.pack(fmt + "HIH", 42, 8, 1)
    return head + entry + struct.pack(fmt + "I", 0)


def turned(kind: str, data: bytes) -> list[tuple[bytes, str]]:
    """Variants whose Exif turns the picture a quarter turn, as Orientation 6 does."""
    out: list[tuple[bytes, str]] = []
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
            out.append((bare[:2] + segment + bare[2:], what))
    elif kind == "png":
        chunk = png_chunk(b"eXIf", orientation_tiff(b"II", 3))
        out.append((data[:33] + chunk + data[33:], "eXIf with Orientation"))
    elif kind == "webp":
        chunk = riff_chunk(b"EXIF", orientation_tiff(b"II", 3))
        out.append((with_riff_size(data + chunk), "EXIF with Orientation"))
    return out


def orientation(kind: str, data: bytes) -> int:
    """The Orientation the first Exif in a file holds, or 1 where it holds none."""
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


def check_plant(report: Report, kind: str, data: bytes, where: str) -> None:
    report.cases += 1
    found, raised = attempt(lambda: gate.scan(data))
    if raised:
        report.fail("1 scanner raised", kind, raised, where)
        return
    what = re.sub(r" at \d+$", "", where.split(": ", 1)[-1])
    if not found:
        report.fail("4 planted metadata passed", kind, what, where)
    new, raised = attempt(lambda: normalizer.normalize_bytes(data))
    if raised:
        report.fail("2 normalizer raised", kind, raised, where)
    elif isinstance(new, bytes) and PLANT_TEXT in new:
        report.fail("4 normalizer kept planted metadata", kind, what, where)
    elif isinstance(new, bytes) and new:
        again, raised = attempt(lambda: gate.scan(new))
        if raised:
            report.fail("1 scanner raised on normalized output", kind, raised, where)
        elif again:
            detail = ", ".join(sorted(again))
            report.fail("2 normalizer output rejected", kind, detail, where)


def check_turn(report: Report, kind: str, data: bytes, where: str) -> None:
    report.cases += 1
    new, raised = attempt(lambda: normalizer.normalize_bytes(data))
    if raised:
        report.fail("2 normalizer raised", kind, raised, where)
        return
    if isinstance(new, bytes) and new:
        kept, raised = attempt(lambda: orientation(kind, new))
        if raised or kept != 6:
            what = where.split(": ", 1)[-1]
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
        if label.startswith("fixture:") and gate.scan(data):
            report.fail("0 fixture not clean", kind, ", ".join(gate.scan(data)), label)
        for variant, what in plants(kind, data):
            check_plant(report, kind, variant, f"{label}: {what}")
        for variant, what in turned(kind, data):
            check_turn(report, kind, variant, f"{label}: {what}")
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
