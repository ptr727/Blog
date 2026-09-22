#!/usr/bin/env python3
"""Fail if a carried media file holds location, device, or authorship metadata.

Every image under static/ is copied byte for byte into the built site, so whatever a camera
or an editor wrote into a file is served with it. An archive imported from another platform
arrived carrying GPS coordinates that resolved one residential address to about a metre, and
nothing in the pipeline noticed, because a build gate reads pages and a linter reads prose.

Three decisions shape what this reads, and each one came from something that was missed.

Inside archives. A .zip in the media tree is opened and its members read. A loose-file walk
cannot see them, and the imported archive held a photograph and a video that were invisible
to every scan run before this one.

Values rather than key names. A metadata tool can unlink a value from its index and leave
the bytes in the file, reporting the file clean while the coordinate is still there. So a
QuickTime file is searched for a coordinate that parses, never for the name of the atom that
used to hold one.

Compressed text blocks. A PNG can carry a whole EXIF segment hex-encoded inside a zlib
compressed text chunk, where a scan of the ordinary chunks never looks. Those are decoded and
read like any other segment, because a tag hidden two layers down is still served.

Stdlib only, to match the rest of checks/. Read-only. Exit 1 on any finding.
"""

from __future__ import annotations

import binascii
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TREES = ("static/media", "static/external")

# A member larger than this is reported rather than decompressed.
# Reading an archive to clear it must not become a way to exhaust the runner.
MEMBER_LIMIT = 256 * 1024 * 1024

# A TIFF tag whose presence in a carried file is a finding on its own.
TAGS = {
    0x8825: "GPS",
    0x010F: "Make",
    0x0110: "Model",
    0x013B: "Artist",
    0x013C: "HostComputer",
    0x8298: "Copyright",
    0x9286: "UserComment",
    0xA430: "CameraOwnerName",
    0xA431: "BodySerialNumber",
    0xA432: "LensSerialNumber",
    0x0201: "EmbeddedThumbnail",
}

# A pointer to a sub-IFD.
# GPS, and most of the identity tags, live behind one rather than in IFD0.
SUB_IFD = {0x8769, 0x8825, 0xA005}

# An ISO6709 coordinate, which is what a QuickTime location actually looks like on disk.
COORDINATE = re.compile(rb"[+-]\d{2}\.\d{2,}[+-]\d{3}\.\d{2,}")


def tiff_tags(raw: bytes) -> set[str]:
    """Walk the IFD chain of a TIFF or EXIF segment and name the tags that matter."""
    found: set[str] = set()
    start = raw.find(b"Exif\x00\x00")
    if start >= 0:
        raw = raw[start + 6 :]
    if raw[:2] not in (b"II", b"MM"):
        return found
    fmt = "<" if raw[:2] == b"II" else ">"
    try:
        pending = [struct.unpack_from(fmt + "I", raw, 4)[0]]
    except struct.error:
        return found
    seen: set[int] = set()
    # Bounded and cycle-guarded, because a malformed chain can point at itself.
    while pending and len(seen) < 16:
        offset = pending.pop()
        if not 0 < offset < len(raw) or offset in seen:
            continue
        seen.add(offset)
        try:
            count = struct.unpack_from(fmt + "H", raw, offset)[0]
        except struct.error:
            continue
        for i in range(count):
            entry = offset + 2 + i * 12
            if entry + 12 > len(raw):
                break
            tag = struct.unpack_from(fmt + "H", raw, entry)[0]
            if tag in TAGS:
                found.add(TAGS[tag])
            if tag in SUB_IFD:
                sub = struct.unpack_from(fmt + "I", raw, entry + 8)[0]
                if 0 < sub < len(raw) and sub not in seen:
                    pending.append(sub)
        try:
            nxt = struct.unpack_from(fmt + "I", raw, offset + 2 + count * 12)[0]
        except struct.error:
            nxt = 0
        if 0 < nxt < len(raw) and nxt not in seen:
            pending.append(nxt)
    return found


def scan_jpeg(data: bytes) -> set[str]:
    found: set[str] = set()
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            break
        marker = data[i + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker == 0xDA:  # start of scan, metadata is all behind us
            break
        try:
            length = struct.unpack_from(">H", data, i + 2)[0]
        except struct.error:
            break
        segment = data[i + 4 : i + 2 + length]
        if marker == 0xE1:
            found |= tiff_tags(segment)
            if b"exif:GPS" in segment:
                found.add("XMP GPS")
        elif marker == 0xFE:
            found.add("JPEG comment")
        i += 2 + length
    return found


def png_text(chunk_type: bytes, body: bytes) -> bytes:
    """Return the payload of a PNG text chunk, decompressing zTXt."""
    if chunk_type == b"zTXt":
        return zlib.decompress(body.split(b"\x00", 1)[1][1:])
    if chunk_type == b"iTXt":
        return body.split(b"\x00", 5)[-1]
    return body.split(b"\x00", 1)[1]


def scan_png(data: bytes) -> set[str]:
    found: set[str] = set()
    i = 8
    while i + 8 <= len(data):
        try:
            length = struct.unpack_from(">I", data, i)[0]
        except struct.error:
            break
        chunk_type = data[i + 4 : i + 8]
        body = data[i + 8 : i + 8 + length]
        if chunk_type == b"eXIf":
            found |= tiff_tags(body)
        elif chunk_type in (b"tEXt", b"zTXt", b"iTXt"):
            try:
                text = png_text(chunk_type, body)
            except (zlib.error, IndexError):
                i += 12 + length
                continue
            if body.startswith(b"Raw profile type"):
                # A hex-encoded segment.
                # Decode it and read the tags rather than the label.
                hexed = b"".join(line.strip() for line in text.split(b"\n")[2:])
                try:
                    found |= tiff_tags(binascii.unhexlify(hexed))
                except binascii.Error:
                    pass
            elif b"GPS" in text:
                found.add("XMP GPS")
        i += 12 + length
    return found


def scan_quicktime(data: bytes) -> set[str]:
    # The value, not the atom name, because a tool can remove one and leave the other.
    return {"QuickTime location"} if COORDINATE.search(data) else set()


def scan(data: bytes) -> set[str]:
    if data[:2] == b"\xff\xd8":
        return scan_jpeg(data)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return scan_png(data)
    if data[4:8] == b"ftyp" or b"moov" in data[:4096]:
        return scan_quicktime(data)
    return set()


def findings() -> list[tuple[str, set[str]]]:
    out = []
    for tree in TREES:
        root = REPO / tree
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            name = str(path.relative_to(REPO))
            data = path.read_bytes()
            if path.suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(path) as archive:
                        for info in archive.infolist():
                            if info.file_size > MEMBER_LIMIT:
                                out.append(
                                    (
                                        f"{name}!{info.filename}",
                                        {"member too large to read"},
                                    )
                                )
                                continue
                            hit = scan(archive.read(info))
                            if hit:
                                out.append((f"{name}!{info.filename}", hit))
                except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
                    # An encrypted or corrupt archive cannot be read, so it cannot be cleared.
                    out.append((name, {f"unreadable archive: {type(exc).__name__}"}))
                continue
            hit = scan(data)
            if hit:
                out.append((name, hit))
    return out


def main() -> int:
    found = findings()
    scanned = sum(1 for tree in TREES for p in (REPO / tree).rglob("*") if p.is_file())
    if found:
        for name, tags in found:
            print(f"{name}: {', '.join(sorted(tags))}")
        print(
            f"\n{len(found)} file(s) carry metadata. Strip before committing, see CONTENT.md."
        )
        return 1
    print(
        f"media   : {scanned} carried file(s), none carry location, device, or authorship metadata"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
