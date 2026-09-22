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

# A file or archive member larger than this is reported rather than read.
SIZE_LIMIT = 256 * 1024 * 1024

# JPEG markers that carry picture data or coding tables rather than description.
# TEM and the restart markers stand alone, so they are skipped before a length is read.
JPEG_STRUCTURAL = (
    {0xD8, 0xD9, 0xDA, 0xDB, 0xC4, 0xCC, 0xDD, 0x01}
    | set(range(0xD0, 0xD8))
    | {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)

# JPEG APP segments that carry rendering data rather than description.
JPEG_APP_ALLOWED = ((0xE0, b"JFIF\x00"), (0xE2, b"ICC_PROFILE\x00"), (0xEE, b"Adobe"))

# TIFF tags that exist so a decoder renders the picture correctly.
# A tag outside this set is not judged, it is simply not vouched for.
EXIF_ALLOWED = {
    0x0001,  # InteropIndex
    0x0002,  # InteropVersion
    0x0100,  # ImageWidth
    0x0101,  # ImageLength
    0x0102,  # BitsPerSample
    0x0103,  # Compression
    0x0106,  # PhotometricInterpretation
    0x0112,  # Orientation
    0x0115,  # SamplesPerPixel
    0x011A,  # XResolution
    0x011B,  # YResolution
    0x011C,  # PlanarConfiguration
    0x0128,  # ResolutionUnit
    0x0132,  # DateTime
    0x0213,  # YCbCrPositioning
    0x8769,  # ExifIFDPointer
    0x9000,  # ExifVersion
    0x9003,  # DateTimeOriginal
    0x9101,  # ComponentsConfiguration
    0xA000,  # FlashpixVersion
    0xA001,  # ColorSpace
    0xA002,  # PixelXDimension
    0xA003,  # PixelYDimension
    0xA005,  # InteropIFDPointer
}

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


def exif_unrecognized(raw: bytes) -> set[str]:
    """Name every TIFF tag in a segment that is not on the display-correctness list."""
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
    seen: set[int] = set()
    while pending and len(seen) < 16:
        offset = pending.pop()
        if offset in seen or offset <= 0 or offset + 2 > len(raw):
            continue
        seen.add(offset)
        try:
            count = struct.unpack_from(fmt + "H", raw, offset)[0]
        except struct.error:
            continue
        for index in range(count):
            entry = offset + 2 + index * 12
            if entry + 12 > len(raw):
                break
            tag = struct.unpack_from(fmt + "H", raw, entry)[0]
            if tag not in EXIF_ALLOWED:
                out.add(f"Exif tag 0x{tag:04X}")
            if tag in (0x8769, 0x8825, 0xA005):
                try:
                    pending.append(struct.unpack_from(fmt + "I", raw, entry + 8)[0])
                except struct.error:
                    pass
    return out


def scan_jpeg(data: bytes) -> set[str]:
    out: set[str] = set()
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            out.add("JPEG segment structure not understood")
            break
        marker = data[i + 1]
        if marker in (0x01, 0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack_from(">H", data, i + 2)[0]
        if length < 2 or i + 2 + length > len(data):
            out.add("JPEG segment runs past the end of the file")
            break
        segment = data[i + 4 : i + 2 + length]
        if any(marker == m and segment.startswith(p) for m, p in JPEG_APP_ALLOWED):
            pass
        elif marker == 0xE1 and segment.startswith(b"Exif\x00\x00"):
            out |= exif_unrecognized(segment)
        elif 0xE0 <= marker <= 0xEF:
            out.add(f"JPEG APP{marker - 0xE0} segment")
        elif marker == 0xFE:
            out.add("JPEG comment")
        elif marker not in JPEG_STRUCTURAL:
            out.add(f"JPEG marker 0x{marker:02X}")
        if marker == 0xDA:
            end = data.find(b"\xff\xd9", i)
            if end < 0:
                out.add("JPEG has no end marker")
            elif end + 2 != len(data):
                out.add("JPEG trailing bytes after the end marker")
            return out
        i += 2 + length
    # The markers ran out before the picture began.
    out.add("JPEG has no scan")
    return out


def scan_png(data: bytes) -> set[str]:
    out: set[str] = set()
    i = 8
    while i + 8 <= len(data):
        try:
            length = struct.unpack_from(">I", data, i)[0]
        except struct.error:
            out.add("PNG chunk structure not understood")
            break
        chunk = data[i + 4 : i + 8]
        if i + 12 + length > len(data):
            out.add("PNG chunk runs past the end of the file")
            break
        if chunk not in PNG_ALLOWED:
            out.add(f"PNG {chunk.decode('ascii', 'replace')} chunk")
        i += 12 + length
        if chunk == b"IEND":
            if i != len(data):
                out.add("PNG trailing bytes after IEND")
            break
    return out


def scan_gif(data: bytes) -> set[str]:
    out: set[str] = set()
    i = 13
    if len(data) > 10 and data[10] & 0x80:
        i += 3 * (2 << (data[10] & 7))

    def skip_blocks(j: int) -> int:
        while j < len(data) and data[j]:
            j += data[j] + 1
        return j + 1

    seen_trailer = False
    while i < len(data):
        marker = data[i]
        if marker == 0x3B:
            seen_trailer = True
            if i + 1 != len(data):
                out.add("GIF trailing bytes after the trailer")
            break
        if marker == 0x21:
            if i + 2 > len(data) - 1:
                out.add("GIF extension runs past the end of the file")
                break
            label = data[i + 1]
            if label == 0xFF:
                if data[i + 3 : i + 14] != b"NETSCAPE2.0":
                    out.add("GIF application extension")
            elif label != 0xF9:
                out.add(f"GIF extension 0x{label:02X}")
            i = skip_blocks(i + 2)
        elif marker == 0x2C:
            if i + 10 > len(data):
                out.add("GIF image descriptor runs past the end of the file")
                break
            flags = data[i + 9]
            i += 10
            if flags & 0x80:
                i += 3 * (2 << (flags & 7))
            i = skip_blocks(i + 1)
        else:
            out.add("GIF block structure not understood")
            break
    if not seen_trailer:
        out.add("GIF ends without a trailer")
    return out


def scan_webp(data: bytes) -> set[str]:
    out: set[str] = set()
    i = 12
    while i + 8 <= len(data):
        chunk = data[i : i + 4]
        length = struct.unpack_from("<I", data, i + 4)[0]
        span = 8 + length + (length & 1)
        if i + span > len(data):
            out.add("WebP chunk runs past the end of the file")
            break
        if chunk not in WEBP_ALLOWED:
            out.add(f"WebP {chunk.decode('ascii', 'replace')} chunk")
        i += span
    return out


def scan_iso(data: bytes, start: int = 0, end: int | None = None) -> set[str]:
    out: set[str] = set()
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
            out |= scan_iso(data, i + 8, i + length)
        i += length
    if i != end:
        out.add("ISO trailing bytes outside any atom")
    if start == 0 and COORDINATE.search(data):
        out.add("ISO6709 coordinate")
    return out


def scan(data: bytes) -> set[str]:
    """Name what a file holds that this cannot vouch for."""
    if data[:2] == b"\xff\xd8":
        return scan_jpeg(data)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return scan_png(data)
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return scan_gif(data)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return scan_webp(data)
    if data[4:8] in (b"ftyp", b"moov", b"wide", b"mdat", b"free", b"skip"):
        return scan_iso(data)
    return {"unrecognized container"}


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
                except (RuntimeError, zipfile.BadZipFile, zlib.error) as exc:
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
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
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
