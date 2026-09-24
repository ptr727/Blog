#!/usr/bin/env python3
"""Fail the build on carried media that is not in a form this can vouch for.

This is an allowlist, and that is the whole design. An earlier version of this file
enumerated the places metadata is known to hide and failed on those, and review found a
new hole in it in eleven of twelve rounds: a sub-IFD never followed, a text chunk never
decompressed, a container never recognized, a length never bounded. Each fix was correct
and each widened a surface with no edge, because "where can metadata hide" has no closed
answer and no version of that file was ever finished.

The question is inverted here. Every structural element a carried file may hold is named
below, and anything outside those names is reported as something to convert rather than
something to parse. Nobody needs to know what a vendor MakerNote contains to decide it
should not ship. That turns an unbounded question into a short list that can be read in
one sitting and argued with.

What survives an allowlist is only what exists for display correctness: the dimensions,
the color profile, and the orientation, plus the capture timestamp on the formats whose
tags carry one, which is JPEG here and not PNG. Identity, location, device and authorship
are not enumerated here at all, because they do not need to be. They are not on the list,
so they fail.

A file this reports is not accused of carrying anything. It is a file whose form cannot
be vouched for, and `scripts/normalize-media.py` is what resolves that, by decoding to
pixels and writing a fresh file that is clean by construction.
"""

import lzma
import pathlib
import re
import struct
import sys
import zipfile
import zlib

REPO = pathlib.Path(__file__).resolve().parent.parent
TREES = ("static/media", "static/external")

# Extensions that name a picture or a video, read only inside an archive.
# A member is judged by its bytes wherever they are recognized.
# An unrecognized container is a finding only where the name says the member is media.
# An archive here also carries source files and binaries, which are not in scope.
MEDIA_SUFFIXES = frozenset(
    (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
        ".heic",
        ".heif",
        ".avif",
        ".jxl",
        ".mov",
        ".mp4",
        ".m4v",
        ".avi",
        ".mkv",
        ".webm",
        ".mpg",
        ".mpeg",
        ".3gp",
        ".raw",
        ".dng",
        ".cr2",
        ".nef",
    )
)

# What a damaged archive raises while being opened or read.
ZIP_ERRORS = (
    zipfile.BadZipFile,
    RuntimeError,
    NotImplementedError,
    OSError,
    EOFError,
    ValueError,
    zlib.error,
    lzma.LZMAError,
)

# A file or archive member larger than this is reported rather than read.
SIZE_LIMIT = 256 * 1024 * 1024

# JPEG markers that carry picture data or coding tables rather than description.
# TEM and the restart markers stand alone, so they are skipped before a length is read.
JPEG_FRAME = frozenset(
    (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF)
)
JPEG_STRUCTURAL = (
    {0xD8, 0xD9, 0xDA, 0xDB, 0xC4, 0xCC, 0xDD, 0x01}
    | set(range(0xD0, 0xD8))
    | JPEG_FRAME
)

# JPEG APP segments that carry rendering data rather than description.
JPEG_APP_ALLOWED = ((0xE0, b"JFIF\x00"), (0xE2, b"ICC_PROFILE\x00"), (0xEE, b"Adobe"))

# The one length of each admitted APP segment whose fields are fixed, so it has no room for more.
# JFIF is its fields plus a thumbnail sized by its last two, which have to be zero.
JPEG_APP_FIXED = {b"JFIF\x00": 14, b"Adobe": 12}

# TIFF tags that exist so a decoder renders the picture correctly, each in its one shape.
# A shape is the tag's field types and exactly how many values it holds, so it has no room for more.
# BitsPerSample holds one value per sample, so its count is the SamplesPerPixel value.
# A tag outside this set is not judged, it is simply not vouched for.
SHORT_OR_LONG = frozenset((3, 4))
EXIF_SHAPE = {
    0x0001: (frozenset((2,)), 4),  # InteropIndex
    0x0002: (frozenset((7,)), 4),  # InteropVersion
    0x0100: (SHORT_OR_LONG, 1),  # ImageWidth
    0x0101: (SHORT_OR_LONG, 1),  # ImageLength
    0x0102: (frozenset((3,)), 4),  # BitsPerSample
    0x0103: (frozenset((3,)), 1),  # Compression
    0x0106: (frozenset((3,)), 1),  # PhotometricInterpretation
    0x0112: (frozenset((3,)), 1),  # Orientation
    0x0115: (frozenset((3,)), 1),  # SamplesPerPixel
    0x011A: (frozenset((5,)), 1),  # XResolution
    0x011B: (frozenset((5,)), 1),  # YResolution
    0x011C: (frozenset((3,)), 1),  # PlanarConfiguration
    0x0128: (frozenset((3,)), 1),  # ResolutionUnit
    0x0132: (frozenset((2,)), 20),  # DateTime
    0x0213: (frozenset((3,)), 1),  # YCbCrPositioning
    0x8769: (frozenset((4,)), 1),  # ExifIFDPointer
    0x9000: (frozenset((7,)), 4),  # ExifVersion
    0x9003: (frozenset((2,)), 20),  # DateTimeOriginal
    0x9101: (frozenset((7,)), 4),  # ComponentsConfiguration
    0xA000: (frozenset((7,)), 4),  # FlashpixVersion
    0xA001: (frozenset((3,)), 1),  # ColorSpace
    0xA002: (SHORT_OR_LONG, 1),  # PixelXDimension
    0xA003: (SHORT_OR_LONG, 1),  # PixelYDimension
    0xA005: (frozenset((4,)), 1),  # InteropIFDPointer
}
EXIF_ALLOWED = frozenset(EXIF_SHAPE)

PNG_ALLOWED = {
    b"IHDR",
    b"PLTE",
    b"IDAT",
    b"IEND",
    b"tRNS",
    b"gAMA",
    b"cHRM",
    b"sRGB",
    b"iCCP",
    b"sBIT",
    b"bKGD",
    b"pHYs",
    b"hIST",
    b"acTL",
    b"fcTL",
    b"fdAT",
}

WEBP_ALLOWED = {b"VP8 ", b"VP8L", b"VP8X", b"ALPH", b"ANIM", b"ANMF", b"ICCP"}
WEBP_FRAME_ALLOWED = {b"VP8 ", b"VP8L", b"ALPH"}
WEBP_FIXED = {b"VP8X": 10, b"ANIM": 6}

# The chunk runs one picture is drawn from, a lossy image with its alpha or a single image.
WEBP_IMAGES = ([b"VP8 "], [b"VP8L"], [b"ALPH", b"VP8 "])

# An animation frame's position, size, duration and flags, which precede its own chunks.
WEBP_FRAME_HEADER = 16

# ISO base media atoms that hold the picture, the timing, or nothing at all.
ISO_ALLOWED = {
    b"ftyp",
    b"moov",
    b"mdat",
    b"free",
    b"skip",
    b"wide",
    b"mvhd",
    b"trak",
    b"tkhd",
    b"edts",
    b"elst",
    b"mdia",
    b"mdhd",
    b"hdlr",
    b"minf",
    b"vmhd",
    b"smhd",
    b"dinf",
    b"dref",
    b"stbl",
    b"stsd",
    b"stts",
    b"stss",
    b"stsc",
    b"stsz",
    b"stco",
    b"co64",
    b"ctts",
    b"sdtp",
    b"avcC",
    b"pasp",
    b"colr",
    b"btrt",
    b"sgpd",
    b"sbgp",
}
ISO_CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf"}

# An ISO6709 coordinate, checked by value rather than by the name of the atom holding it.
# A tool can unlink the value and leave the bytes, which is how a video here read clean while located.
COORDINATE = re.compile(rb"[+-]\d{2}\.\d{2,}[+-]\d{3}\.\d{2,}")


# A timestamp tag holds a date or the blanks that mean unknown, never free text.
EXIF_DATES = (0x0132, 0x9003)
EXIF_DATE = re.compile(rb"(\d{4}:\d\d:\d\d \d\d:\d\d:\d\d| {19})\x00")


# Bytes per value for each TIFF field type, so a value's extent can be bounded.
EXIF_TYPE_SIZE = {
    1: 1,
    2: 1,
    3: 2,
    4: 4,
    5: 8,
    6: 1,
    7: 1,
    8: 2,
    9: 4,
    10: 8,
    11: 4,
    12: 8,
}

# Problems a normalizer resolves by rewriting the container rather than by refusing it.
TRAILING = frozenset(
    (
        "JPEG trailing bytes after the end marker",
        "PNG trailing bytes after IEND",
        "GIF trailing bytes after the trailer",
        "WebP trailing bytes outside any chunk",
        "WebP RIFF size does not match the file",
    )
)

# How far ISO atoms may nest, well past any real file and well short of the stack.
ISO_DEPTH = 16

# A parsed element: its type, where it starts, and where it ends.
Part = tuple[object, int, int]


def exif_unrecognized(raw: bytes) -> set[str]:
    """Name every TIFF tag in a segment that is not on the display-correctness list.

    Every byte of the segment has to be something its IFDs reference. A thumbnail left
    behind after its pointer was zeroed is referenced by nothing, so it is reported.
    """
    out: set[str] = set()
    start = raw.find(b"Exif\x00\x00")
    if start >= 0:
        raw = raw[start + 6 :]
    if raw[:2] not in (b"II", b"MM"):
        return {"APP1/Exif with no TIFF header"}
    fmt = "<" if raw[:2] == b"II" else ">"
    try:
        if struct.unpack_from(fmt + "H", raw, 2)[0] != 42:
            return {"APP1/Exif with a bad TIFF magic"}
        pending = [struct.unpack_from(fmt + "I", raw, 4)[0]]
    except struct.error:
        return {"APP1/Exif truncated"}
    covered = [(0, 8)]
    seen: set[int] = set()
    while pending and len(seen) < 16:
        offset = pending.pop()
        if offset in seen:
            continue
        if offset < 8 or offset + 2 > len(raw):
            out.add("Exif IFD pointer outside the segment")
            continue
        seen.add(offset)
        count = struct.unpack_from(fmt + "H", raw, offset)[0]
        end = offset + 2 + count * 12 + 4
        if end > len(raw):
            out.add("Exif IFD runs past the segment")
            continue
        covered.append((offset, end))
        tags: dict[int, tuple[int, int]] = {}
        for index in range(count):
            entry = offset + 2 + index * 12
            tag, kind, number = struct.unpack_from(fmt + "HHI", raw, entry)
            types, exact = EXIF_SHAPE.get(tag, (frozenset(), 0))
            counts = (1, 3) if tag == 0x0102 else (exact,)
            if tag not in EXIF_ALLOWED:
                out.add(f"Exif tag 0x{tag:04X}")
            elif tag in tags or kind not in types or number not in counts:
                out.add(f"Exif tag 0x{tag:04X} not in its one shape")
            tags[tag] = (number, struct.unpack_from(fmt + "H", raw, entry + 8)[0])
            if tag in (0x8769, 0x8825, 0xA005):
                pending.append(struct.unpack_from(fmt + "I", raw, entry + 8)[0])
            if kind not in EXIF_TYPE_SIZE:
                out.add("Exif value of unknown type")
                continue
            size = EXIF_TYPE_SIZE[kind] * number
            if size <= 4 and any(raw[entry + 8 + size : entry + 12]):
                out.add("Exif inline value padding not zero")
            if size > 4:
                value = struct.unpack_from(fmt + "I", raw, entry + 8)[0]
                if value + size > len(raw):
                    out.add("Exif value runs past the segment")
                    continue
                covered.append((value, value + size))
                date = raw[value : value + size]
                if tag in EXIF_DATES and not EXIF_DATE.fullmatch(date):
                    out.add(f"Exif tag 0x{tag:04X} is not a date")
        bits, samples = tags.get(0x0102), tags.get(0x0115)
        if bits and samples and bits[0] != samples[1]:
            out.add("Exif tag 0x0102 not in its one shape")
        # A chained IFD is a second image, usually a thumbnail of the frame before any edit.
        if struct.unpack_from(fmt + "I", raw, end - 4)[0]:
            out.add("Exif chained IFD")
    if pending:
        out.add("Exif holds more IFDs than this reads")
    # A value starts on a word boundary, so a single pad byte is the only gap a writer leaves.
    reach = 0
    for low, high in sorted(covered):
        if low - reach > 1:
            out.add("Exif bytes no IFD references")
        reach = max(reach, high)
    if len(raw) - reach > 1:
        out.add("Exif bytes no IFD references")
    return out


def jpeg_parts(data: bytes) -> tuple[list[Part], set[str]]:
    """Split a JPEG into its segments, and name what stopped the split.

    A scan segment runs through its entropy data, which ends at the first marker that is
    neither a stuffed byte nor a restart. So a segment between two scans, or between the
    last scan and the end marker, is a segment like any other rather than picture data.
    """
    parts: list[Part] = []
    problems: set[str] = set()
    i = 2
    while True:
        if i + 2 > len(data):
            problems.add("JPEG has no end marker")
            break
        if data[i] != 0xFF:
            problems.add("JPEG segment structure not understood")
            break
        marker = data[i + 1]
        if marker == 0xFF:
            # A fill byte may precede any marker.
            i += 1
            continue
        if marker == 0xD9:
            parts.append((marker, i, i + 2))
            if i + 2 != len(data):
                problems.add("JPEG trailing bytes after the end marker")
            break
        if marker in (0x01, 0xD8) or 0xD0 <= marker <= 0xD7:
            parts.append((marker, i, i + 2))
            i += 2
            continue
        if i + 4 > len(data):
            problems.add("JPEG segment runs past the end of the file")
            break
        length = struct.unpack_from(">H", data, i + 2)[0]
        if length < 2 or i + 2 + length > len(data):
            problems.add("JPEG segment runs past the end of the file")
            break
        end = i + 2 + length
        if marker == 0xDA:
            end = entropy_end(data, end)
            if end < 0:
                problems.add("JPEG has no end marker")
                break
        parts.append((marker, i, end))
        i = end
    if not any(marker == 0xDA for marker, _, _ in parts):
        problems.add("JPEG has no scan")
    # A second stream is picture data no decoder draws, so it is not dropped as if it were a tag.
    if any(marker == 0xD8 for marker, _, _ in parts):
        problems.add("JPEG second start of image")
    if sum(marker in JPEG_FRAME for marker, _, _ in parts) > 1:
        problems.add("JPEG second frame header")
    return parts, problems


def entropy_end(data: bytes, i: int) -> int:
    """The offset of the marker that ends a scan's entropy data, or -1 where none does."""
    while True:
        i = data.find(b"\xff", i)
        if i < 0 or i + 1 >= len(data):
            return -1
        following = data[i + 1]
        if following == 0x00 or 0xD0 <= following <= 0xD7:
            i += 2
        elif following == 0xFF:
            i += 1
        else:
            return i


def jpeg_app_name(marker: int, segment: bytes) -> bytes | None:
    """The name an APP segment is admitted by, or None where it is not admitted."""
    if marker == 0xE1 and segment.startswith(b"Exif\x00\x00"):
        return b"Exif\x00\x00"
    return next(
        (p for m, p in JPEG_APP_ALLOWED if m == marker and segment.startswith(p)), None
    )


def jpeg_app_fixed(name: bytes, segment: bytes) -> bool:
    """Whether a JFIF or Adobe segment is exactly its fields, with no thumbnail."""
    return len(segment) == JPEG_APP_FIXED[name] and (
        name != b"JFIF\x00" or segment[12:14] == b"\x00\x00"
    )


def icc_numbering(segment: bytes) -> tuple[int, int] | None:
    """An ICC chunk's sequence number and chunk count, or None where they do not make sense."""
    if len(segment) < 14 or not 1 <= segment[12] <= segment[13]:
        return None
    return segment[12], segment[13]


def icc_problems(segments: list[bytes]) -> set[str]:
    """What keeps a JPEG's ICC chunks from being one complete profile holding each chunk once."""
    numbers = [icc_numbering(segment) for segment in segments]
    known = [n for n in numbers if n is not None]
    out = {"JPEG ICC chunk not numbered"} if len(known) < len(numbers) else set()
    sequence = [n[0] for n in known]
    if len(set(sequence)) < len(sequence):
        out.add("JPEG repeated ICC chunk")
    totals = {n[1] for n in known}
    if len(totals) > 1:
        out.add("JPEG ICC chunks disagree on their count")
    elif totals and set(sequence) != set(range(1, max(totals) + 1)):
        # No decoder reads an incomplete profile, so its chunks are bytes nothing draws.
        out.add("JPEG ICC profile incomplete")
    return out


def scan_jpeg(data: bytes) -> set[str]:
    parts, out = jpeg_parts(data)
    names: set[bytes] = set()
    profile: list[bytes] = []
    for marker, start, end in parts:
        segment = data[start + 4 : end]
        if marker in (0x01, 0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        name = jpeg_app_name(marker, segment)
        label = name.rstrip(b"\x00").decode("ascii") if name else ""
        # A segment that passes alone still carries bytes once per repeat, so each admits one.
        if name == b"ICC_PROFILE\x00":
            profile.append(segment)
        elif name:
            if name in names:
                out.add(f"JPEG repeated {label} segment")
            names.add(name)
        if name in JPEG_APP_FIXED and not jpeg_app_fixed(name, segment):
            out.add(f"JPEG {label} segment not in its fixed shape")
        if name == b"Exif\x00\x00":
            out |= exif_unrecognized(segment)
        elif name:
            continue
        elif 0xE0 <= marker <= 0xEF:
            out.add(f"JPEG APP{marker - 0xE0} segment")
        elif marker == 0xFE:
            out.add("JPEG comment")
        elif marker not in JPEG_STRUCTURAL:
            out.add(f"JPEG marker 0x{marker:02X}")
    return out | icc_problems(profile)


def png_parts(data: bytes) -> tuple[list[Part], set[str]]:
    """Split a PNG into its chunks, through IEND, and name what stopped the split."""
    parts: list[Part] = []
    problems: set[str] = set()
    i = 8
    while i + 8 <= len(data):
        length = struct.unpack_from(">I", data, i)[0]
        chunk = data[i + 4 : i + 8]
        if i + 12 + length > len(data):
            problems.add("PNG chunk runs past the end of the file")
            return parts, problems
        parts.append((chunk, i, i + 12 + length))
        i += 12 + length
        if chunk == b"IEND":
            if i != len(data):
                problems.add("PNG trailing bytes after IEND")
            return parts, problems
    problems.add("PNG ends without IEND")
    return parts, problems


def scan_png(data: bytes) -> set[str]:
    parts, out = png_parts(data)
    for chunk, _, _ in parts:
        if chunk not in PNG_ALLOWED:
            out.add(f"PNG {chunk.decode('ascii', 'replace')} chunk")
    return out


def gif_blocks_end(data: bytes, j: int) -> int:
    """The offset after a run of data sub-blocks, or -1 where it runs past the file."""
    while j < len(data) and data[j]:
        j += data[j] + 1
    return j + 1 if j < len(data) else -1


def gif_parts(data: bytes) -> tuple[list[Part], set[str]]:
    """Split a GIF into its header, extensions, images and trailer."""
    parts: list[Part] = []
    problems: set[str] = set()
    head = 13
    if len(data) > 10 and data[10] & 0x80:
        head += 3 * (2 << (data[10] & 7))
    if head > len(data):
        problems.add("GIF ends without a trailer")
        return parts, problems
    parts.append(("header", 0, head))
    i = head
    while i < len(data):
        marker = data[i]
        if marker == 0x3B:
            parts.append(("trailer", i, i + 1))
            if i + 1 != len(data):
                problems.add("GIF trailing bytes after the trailer")
            return parts, problems
        if marker == 0x21:
            end = gif_blocks_end(data, i + 2) if i + 2 < len(data) else -1
            if end < 0:
                problems.add("GIF extension runs past the end of the file")
                return parts, problems
            parts.append((f"extension 0x{data[i + 1]:02X}", i, end))
        elif marker == 0x2C:
            if i + 10 > len(data):
                problems.add("GIF image descriptor runs past the end of the file")
                return parts, problems
            flags = data[i + 9]
            j = i + 10
            if flags & 0x80:
                j += 3 * (2 << (flags & 7))
            end = gif_blocks_end(data, j + 1) if j + 1 < len(data) else -1
            if end < 0:
                problems.add("GIF image runs past the end of the file")
                return parts, problems
            parts.append(("image", i, end))
        else:
            problems.add("GIF block structure not understood")
            return parts, problems
        i = end
    problems.add("GIF ends without a trailer")
    return parts, problems


def gif_extension_allowed(block: bytes) -> bool:
    """A graphic control or looping extension in its one fixed shape, with no room for more."""
    if block[1] == 0xF9:
        return len(block) == 8 and block[2] == 4
    netscape = block[2:14] == b"\x0bNETSCAPE2.0"
    return netscape and len(block) == 19 and block[14:16] == b"\x03\x01"


def scan_gif(data: bytes) -> set[str]:
    parts, out = gif_parts(data)
    for kind, start, end in parts:
        if not str(kind).startswith("extension"):
            continue
        block = data[start:end]
        if gif_extension_allowed(block):
            continue
        if block[1] == 0xFF:
            out.add("GIF application extension")
        elif block[1] == 0xF9:
            out.add("GIF graphic control extension not in its fixed shape")
        else:
            out.add(f"GIF extension 0x{block[1]:02X}")
    return out


def webp_parts(data: bytes) -> tuple[list[Part], set[str]]:
    """Split a WebP into its chunks, reading no further than the RIFF size says a decoder does."""
    riff = struct.unpack_from("<I", data, 4)[0] + 8
    parts, problems = riff_chunks(data, 12, min(riff, len(data)))
    if riff != len(data):
        problems.add("WebP RIFF size does not match the file")
    return parts, problems


def anmf_parts(data: bytes, start: int) -> tuple[list[Part], set[str]]:
    """Split the ANMF frame at start into the chunks it holds after its header."""
    length = struct.unpack_from("<I", data, start + 4)[0]
    if length < WEBP_FRAME_HEADER:
        return [], {"WebP ANMF frame shorter than its header"}
    return riff_chunks(data, start + 8 + WEBP_FRAME_HEADER, start + 8 + length)


def riff_chunks(data: bytes, i: int, stop: int) -> tuple[list[Part], set[str]]:
    """Split the bytes from i to stop into RIFF chunks."""
    parts: list[Part] = []
    problems: set[str] = set()
    while i + 8 <= stop:
        length = struct.unpack_from("<I", data, i + 4)[0]
        span = 8 + length + (length & 1)
        if i + span > stop:
            problems.add("WebP chunk runs past the end of the file")
            return parts, problems
        parts.append((data[i : i + 4], i, i + span))
        i += span
    if i < stop:
        problems.add("WebP trailing bytes outside any chunk")
    return parts, problems


def scan_webp(data: bytes) -> set[str]:
    parts, out = webp_parts(data)
    for chunk, start, _ in parts:
        name = bytes(chunk).decode("ascii", "replace")
        length = struct.unpack_from("<I", data, start + 4)[0]
        if chunk not in WEBP_ALLOWED:
            out.add(f"WebP {name} chunk")
        elif WEBP_FIXED.get(chunk, length) != length:
            out.add(f"WebP {name} chunk not in its fixed shape")
        elif chunk == b"ANMF":
            inner, problems = anmf_parts(data, start)
            out |= problems
            for held, _, _ in inner:
                if held not in WEBP_FRAME_ALLOWED:
                    label = bytes(held).decode("ascii", "replace")
                    out.add(f"WebP {label} chunk inside a frame")
    return out | webp_layout(data)


def webp_layout(data: bytes) -> set[str]:
    """Name where a WebP's allowlisted chunks hold other than one picture per frame.

    A decoder draws one image and passes over any other, so a second one is bytes nothing draws.
    """
    parts, _ = webp_parts(data)
    names = [bytes(chunk) for chunk, _, _ in parts if chunk in WEBP_ALLOWED]
    out = {
        f"WebP repeated {once.decode()} chunk"
        for once in (b"VP8X", b"ICCP", b"ANIM")
        if names.count(once) > 1
    }
    if b"VP8X" not in names and names not in WEBP_IMAGES[:2]:
        out.add("WebP extended chunks with no VP8X")
    drawn = [name for name in names if name in WEBP_FRAME_ALLOWED]
    frames = [start for chunk, start, _ in parts if chunk == b"ANMF"]
    if not frames and drawn not in WEBP_IMAGES:
        out.add("WebP not one image")
    if frames and drawn:
        out.add("WebP image beside its frames")
    for start in frames:
        inner, _ = anmf_parts(data, start)
        held = [bytes(c) for c, _, _ in inner if c in WEBP_FRAME_ALLOWED]
        if held not in WEBP_IMAGES:
            out.add("WebP frame not one image")
    return out


def scan_iso(
    data: bytes, start: int = 0, end: int | None = None, depth: int = 0
) -> set[str]:
    out: set[str] = set()
    if depth > ISO_DEPTH:
        return {"ISO atoms nested too deeply"}
    i = start
    end = len(data) if end is None else end
    while i + 8 <= end:
        length = struct.unpack_from(">I", data, i)[0]
        atom = data[i + 4 : i + 8]
        if length == 0:
            length = end - i
        if length < 8 or i + length > end:
            out.add("ISO atom structure not understood")
            break
        if atom not in ISO_ALLOWED:
            out.add(f"ISO {atom.decode('ascii', 'replace')} atom")
        elif atom in ISO_CONTAINERS:
            out |= scan_iso(data, i + 8, i + length, depth + 1)
        i += length
    if i != end:
        out.add("ISO trailing bytes outside any atom")
    if start == 0 and COORDINATE.search(data):
        out.add("ISO6709 coordinate")
    return out


def container(data: bytes) -> str:
    """Name the container a file's leading bytes declare, or "other"."""
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


SCANNERS = {
    "jpeg": scan_jpeg,
    "png": scan_png,
    "gif": scan_gif,
    "webp": scan_webp,
    "iso": scan_iso,
}


def scan(data: bytes) -> set[str]:
    """Name what a file holds that this cannot vouch for."""
    scanner = SCANNERS.get(container(data))
    return scanner(data) if scanner else {"unrecognized container"}


def findings() -> list[tuple[str, set[str]]]:
    out = []
    for tree in TREES:
        root = REPO / tree
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                # Never followed, since a target can sit outside the tree.
                out.append((str(path.relative_to(REPO)), {"symlink, not read"}))
                continue
            if not path.is_file():
                continue
            name = str(path.relative_to(REPO))
            if path.stat().st_size > SIZE_LIMIT:
                out.append((name, {"too large to read"}))
                continue
            if path.suffix.lower() == ".zip":
                out.extend(walk_archive(path, name))
                continue
            hit = scan(path.read_bytes())
            if hit:
                out.append((name, hit))
    return out


def walk_archive(path: pathlib.Path, name: str) -> list[tuple[str, set[str]]]:
    """Check the media inside an archive, which a walk of loose files cannot see."""
    out = []
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                if info.file_size > SIZE_LIMIT:
                    out.append((f"{name}!{info.filename}", {"too large to read"}))
                    continue
                try:
                    member = archive.read(info)
                except ZIP_ERRORS as exc:
                    out.append(
                        (
                            f"{name}!{info.filename}",
                            {f"unreadable member: {type(exc).__name__}"},
                        )
                    )
                    continue
                # Only media is in scope, so a source file or a binary is left alone.
                # A member named as media counts even where its bytes are unrecognized.
                # Otherwise the same file fails loose and passes inside a zip.
                hit = scan(member)
                named_media = (
                    pathlib.PurePosixPath(info.filename).suffix.lower()
                    in MEDIA_SUFFIXES
                )
                if hit and (named_media or hit != {"unrecognized container"}):
                    out.append((f"{name}!{info.filename}", hit))
    except ZIP_ERRORS as exc:
        out.append((name, {f"unreadable archive: {type(exc).__name__}"}))
    return out


def main() -> int:
    found = findings()
    scanned = sum(
        1
        for tree in TREES
        for p in (REPO / tree).rglob("*")
        if p.is_file() and not p.is_symlink()
    )
    if found:
        for name, tags in found:
            print(f"{name}: {', '.join(sorted(tags))}")
        print(
            f"\n{len(found)} file(s) hold something this cannot vouch for."
            " Run scripts/normalize-media.py, see CONTENT.md."
        )
        return 1
    print(f"media   : {scanned} carried file(s), every one in a form this recognizes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
