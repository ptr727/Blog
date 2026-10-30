"""Constructed media the media gate tests build their cases from."""

import struct
import zlib


def jpeg_segment(marker: int, body: bytes) -> bytes:
    return bytes((0xFF, marker)) + struct.pack(">H", len(body) + 2) + body


def exif_segment() -> bytes:
    """An Exif APP1 carrying only Orientation."""
    entry = struct.pack("<HHIHH", 0x0112, 3, 1, 6, 0)
    tiff = b"II" + struct.pack("<HI", 42, 8) + struct.pack("<H", 1) + entry
    return jpeg_segment(0xE1, b"Exif\x00\x00" + tiff + struct.pack("<I", 0))


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

JFIF = b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
ADOBE = b"Adobe\x00\x64\x00\x00\x00\x00\x01"


def bend(fields: bytes, at: int, value: bytes) -> bytes:
    """A fixed-shape segment's fields with the bytes at one offset replaced."""
    return fields[:at] + value + fields[at + len(value) :]


SQUARE = struct.pack(">IIB", 3779, 3779, 1)
ICC = b"ICC_PROFILE\x00\x01\x01"


def jpeg_fixture() -> bytes:
    """A structurally complete JPEG, with stuffed bytes and a restart marker in its scan."""
    out = b"\xff\xd8" + jpeg_segment(
        0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    )
    out += exif_segment()
    out += jpeg_segment(0xDB, b"\x00" + bytes(range(64)))
    out += jpeg_segment(0xC0, b"\x08\x00\x08\x00\x08\x01\x01\x11\x00")
    out += jpeg_segment(0xC4, b"\x00" + bytes(16) + b"")
    out += jpeg_segment(0xDA, b"\x01\x01\x00\x00\x3f\x00")
    out += b"\x12\x34\xff\x00\x56\xff\xd0\x78\x9a"
    return out + b"\xff\xd9"


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
