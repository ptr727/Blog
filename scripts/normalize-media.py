#!/usr/bin/env python3
"""Bring carried media into a form `checks/check-media-metadata.py` can vouch for.

Run on demand rather than in CI, because it rewrites files.

The gate names what a file holds that is not on its allowlist. This removes exactly
that, and the order of preference is what makes it safe to run on an archive of
originals that cannot be retaken.

**Dropping beats re-encoding, and almost everything here drops.** A PNG text chunk, a
JPEG APP segment, a GIF comment and a WebP metadata chunk are all ancillary: the picture
does not depend on them, so removing them leaves the compressed pixel payload untouched
and the result is bit-identical where it matters. That is not a weaker form of
normalizing, it is a stronger one, because a re-encode of a JPEG loses generation quality
in exchange for removing something a delete already removed.

Re-encoding is the fallback for the case dropping cannot reach, a structure the picture
does depend on that is still not recognized. Nothing in this repository needs it, and the
script says so rather than doing it silently.

The inversion the gate is built on holds here too. This never parses the thing it
removes. It does not need to know what a vendor MakerNote says to know it is not on the
list, and "not on the list" is the whole of the reason it goes.
"""

import argparse
import importlib.util
import pathlib
import shutil
import struct
import subprocess
import sys
import zipfile
import zlib

REPO = pathlib.Path(__file__).resolve().parent.parent

# The gate's filename carries a hyphen, so it loads by path rather than by import.
_spec = importlib.util.spec_from_file_location(
    "gate", REPO / "checks" / "check-media-metadata.py"
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def normalize_png(data: bytes) -> bytes | None:
    """Drop every ancillary chunk that is not on the allowlist."""
    out = bytearray(data[:8])
    i = 8
    while i + 8 <= len(data):
        length = struct.unpack_from(">I", data, i)[0]
        chunk = data[i + 4 : i + 8]
        if i + 12 + length > len(data):
            return None
        critical = not (chunk[0] & 0x20)
        if chunk in gate.PNG_ALLOWED or critical:
            if chunk not in gate.PNG_ALLOWED and critical:
                # A critical chunk cannot be dropped, so this file needs a re-encode.
                return None
            out += data[i : i + 12 + length]
        i += 12 + length
        if chunk == b"IEND":
            return bytes(out)
    # No IEND means the stream was truncated, so there is nothing safe to write.
    return None


def exif_orientation(segment: bytes) -> int:
    """The Orientation value in an Exif segment, or 1 where it says nothing."""
    raw = segment[segment.find(b"Exif\x00\x00") + 6 :]
    if raw[:2] not in (b"II", b"MM"):
        return 1
    fmt = "<" if raw[:2] == b"II" else ">"
    try:
        if struct.unpack_from(fmt + "H", raw, 2)[0] != 42:
            return 1
        offset = struct.unpack_from(fmt + "I", raw, 4)[0]
        count = struct.unpack_from(fmt + "H", raw, offset)[0]
        for index in range(count):
            entry = offset + 2 + index * 12
            if entry + 12 > len(raw):
                break
            if struct.unpack_from(fmt + "H", raw, entry)[0] == 0x0112:
                return struct.unpack_from(fmt + "H", raw, entry + 8)[0]
    except struct.error:
        return 1
    return 1


def orientation_segment(value: int) -> bytes:
    """A minimal Exif segment carrying nothing but Orientation."""
    entry = struct.pack("<HHI", 0x0112, 3, 1) + struct.pack("<HH", value, 0)
    tiff = b"II" + struct.pack("<HI", 42, 8) + struct.pack("<H", 1) + entry
    body = b"Exif\x00\x00" + tiff + struct.pack("<I", 0)
    return b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body


def normalize_jpeg(data: bytes) -> bytes | None:
    """Drop every APP and comment segment that is not on the allowlist."""
    out = bytearray(data[:2])
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        if marker in (0x01, 0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack_from(">H", data, i + 2)[0]
        if length < 2 or i + 2 + length > len(data):
            return None
        segment = data[i + 4 : i + 2 + length]
        keep = True
        if any(marker == m and segment.startswith(p) for m, p in gate.JPEG_APP_ALLOWED):
            keep = True
        elif marker == 0xE1 and segment.startswith(b"Exif\x00\x00"):
            # An Exif segment with an unrecognized tag goes whole.
            # Rewriting an IFD in place means re-computing every offset in it.
            # Orientation decides which way the picture displays, so it is re-emitted alone.
            keep = not gate.exif_unrecognized(segment)
            if not keep:
                turned = exif_orientation(segment)
                if turned not in (0, 1):
                    out += orientation_segment(turned)
        elif 0xE0 <= marker <= 0xEF or marker == 0xFE:
            keep = False
        if marker == 0xDA:
            # The first end marker after the scan is the real one.
            # A later one is appended, so searching backwards would keep what it hides.
            end = data.find(b"\xff\xd9", i)
            if end < 0:
                return None
            out += data[i : end + 2]
            return bytes(out)
        if keep:
            out += data[i : i + 2 + length]
        i += 2 + length
    # The loop ended without reaching the scan, so the picture was never found.
    return None


def normalize_gif(data: bytes) -> bytes | None:
    """Drop every extension block that is not on the allowlist."""
    head = 13
    if len(data) > 10 and data[10] & 0x80:
        head += 3 * (2 << (data[10] & 7))
    out = bytearray(data[:head])
    i = head

    def block_end(j: int) -> int:
        while j < len(data) and data[j]:
            j += data[j] + 1
        return j + 1

    while i < len(data):
        marker = data[i]
        if marker == 0x3B:
            return bytes(out) + b"\x3b"
        if marker == 0x21:
            if i + 2 > len(data) - 1:
                return None
            label = data[i + 1]
            end = block_end(i + 2)
            netscape = label == 0xFF and data[i + 3 : i + 14] == b"NETSCAPE2.0"
            if label == 0xF9 or netscape:
                out += data[i:end]
            i = end
        elif marker == 0x2C:
            if i + 10 > len(data):
                return None
            flags = data[i + 9]
            j = i + 10
            if flags & 0x80:
                j += 3 * (2 << (flags & 7))
            end = block_end(j + 1)
            out += data[i:end]
            i = end
        else:
            return None
    # No trailer means the stream was truncated.
    return None


def normalize_webp(data: bytes) -> bytes | None:
    """Drop every chunk that is not on the allowlist, and restate the RIFF size."""
    body = bytearray()
    i = 12
    while i + 8 <= len(data):
        chunk = data[i : i + 4]
        length = struct.unpack_from("<I", data, i + 4)[0]
        span = 8 + length + (length & 1)
        if i + span > len(data):
            return None
        if chunk in gate.WEBP_ALLOWED:
            body += data[i : i + span]
        i += span
    if not body:
        return None
    return b"RIFF" + struct.pack("<I", len(body) + 4) + b"WEBP" + bytes(body)


def normalize_iso(path: pathlib.Path, destination: pathlib.Path) -> bool:
    """Rewrite a video without its metadata, copying the streams rather than encoding."""
    if not shutil.which("ffmpeg"):
        return False
    result = subprocess.run(
        # The bitexact flags stop ffmpeg stamping its own version into the file it cleaned.
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-map_metadata",
            "-1",
            "-map",
            "0",
            "-c",
            "copy",
            "-fflags",
            "+bitexact",
            "-flags",
            "+bitexact",
            str(destination),
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr.decode("utf-8", "replace"))
        return False
    return True


def normalize_bytes(data: bytes) -> bytes | None:
    """Dispatch one file's bytes to the normalizer for its container."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return normalize_png(data)
    if data[:2] == b"\xff\xd8":
        return normalize_jpeg(data)
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return normalize_gif(data)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return normalize_webp(data)
    return None


def member_suffix(info: zipfile.ZipInfo) -> str:
    """The member's own extension, which ffmpeg needs to pick an output container."""
    return pathlib.PurePosixPath(info.filename).suffix


def normalize_member(
    data: bytes, scratch_dir: pathlib.Path, apply: bool, suffix: str = ""
) -> bytes | None:
    """Normalize one archive member, using a scratch file only for a video.

    The scratch file keeps the member's extension, because ffmpeg picks the output
    container from it and writes nothing when given a name it cannot infer one from.
    """
    if data[4:8] in (b"ftyp", b"moov", b"wide", b"mdat", b"free", b"skip"):
        if not shutil.which("ffmpeg"):
            return None
        if not apply:
            # A report stands in for the rewrite rather than paying for one.
            return b""
        source = scratch_dir / f".normalize-member-in{suffix}"
        cleaned = scratch_dir / f".normalize-member-out{suffix}"
        source.write_bytes(data)
        result = cleaned.read_bytes() if normalize_iso(source, cleaned) else None
        source.unlink(missing_ok=True)
        cleaned.unlink(missing_ok=True)
        return result
    return normalize_bytes(data)


def normalize_archive(path: pathlib.Path, apply: bool) -> list[str]:
    """Normalize the media inside an archive, repacking it under the same entry names.

    Each member is read, decided on, and released before the next one, so peak memory is
    one member rather than the whole archive twice over. A member that needs normalizing
    and cannot be normalized is named rather than passed over in silence.
    """
    removed: list[str] = []
    stuck: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if info.file_size > gate.SIZE_LIMIT:
                stuck.append(f"{info.filename}: too large to read")
                continue
            try:
                data = archive.read(info)
            except (RuntimeError, zipfile.BadZipFile, zlib.error) as exc:
                # An encrypted or corrupt member is left as it is, and said so.
                print(f"{path}!{info.filename}: unreadable, {type(exc).__name__}")
                continue
            holds = gate.scan(data)
            named_media = (
                pathlib.PurePosixPath(info.filename).suffix.lower()
                in gate.MEDIA_SUFFIXES
            )
            unvouched = holds and (named_media or holds != {"unrecognized container"})
            if unvouched:
                if (
                    normalize_member(data, path.parent, False, member_suffix(info))
                    is not None
                ):
                    removed.append(f"{info.filename}: {', '.join(sorted(holds))}")
                else:
                    # Named rather than skipped, since the member stays as it is.
                    stuck.append(f"{info.filename}: {', '.join(sorted(holds))}")
            del data
    for line in stuck:
        print(f"{path}!{line} -> needs a re-encode, which this does not do for you")
    if not (apply and removed):
        return removed
    scratch = path.with_name(f".normalize-{path.name}")
    with (
        zipfile.ZipFile(path) as source,
        zipfile.ZipFile(scratch, "w", zipfile.ZIP_DEFLATED) as target,
    ):
        for info in source.infolist():
            if info.file_size > gate.SIZE_LIMIT:
                # Copied across without being read whole, since nothing here will rewrite it.
                with source.open(info) as fsrc, target.open(info, "w") as fdst:
                    shutil.copyfileobj(fsrc, fdst)
                continue
            try:
                data = source.read(info)
            except (RuntimeError, zipfile.BadZipFile, zlib.error):
                # A member that cannot be read cannot be repacked, so the rewrite stops.
                scratch.unlink(missing_ok=True)
                raise
            new = (
                None
                if info.is_dir()
                else normalize_member(data, path.parent, True, member_suffix(info))
            )
            if new is None and not info.is_dir():
                # Carried over rather than dropped, and never in silence.
                print(f"{path}!{info.filename}: not normalized, carried over as it was")
            target.writestr(info, new if new else data)
            del data
    scratch.replace(path)
    return removed


def pixel_payload(data: bytes) -> bytes | None:
    """Return the compressed picture bytes, so a rewrite can be proven lossless.

    None means this cannot isolate them for that format, so the caller asserts nothing
    rather than comparing whole files and calling every rewrite lossy.
    """
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        out, i = bytearray(), 8
        while i + 8 <= len(data):
            length = struct.unpack_from(">I", data, i)[0]
            if data[i + 4 : i + 8] == b"IDAT":
                out += data[i + 8 : i + 8 + length]
            i += 12 + length
        return bytes(out)
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 4 <= len(data):
            if data[i] != 0xFF:
                break
            marker = data[i + 1]
            if marker in (0x01, 0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            if marker == 0xDA:
                # To the first end marker after the scan.
                # A later one is appended, and reading to it counts a payload as picture.
                end = data.find(b"\xff\xd9", i)
                return data[i : end + 2] if end >= 0 else data[i:]
            i += 2 + struct.unpack_from(">H", data, i + 2)[0]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "paths", nargs="*", help="files or directories, default the carried trees"
    )
    parser.add_argument(
        "--apply", action="store_true", help="write the files, rather than reporting"
    )
    args = parser.parse_args()

    roots = [pathlib.Path(p) for p in args.paths] or [REPO / t for t in gate.TREES]
    targets: list[pathlib.Path] = []
    for root in roots:
        if root.is_dir():
            # A symlink is never followed, since an apply would rewrite its target.
            targets.extend(
                sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink())
            )
        elif root.is_symlink():
            print(f"{root}: symlink, not followed")
        else:
            targets.append(root)

    changed, reencode, saved = [], [], 0
    for path in targets:
        if path.suffix.lower() == ".zip":
            inner = normalize_archive(path, args.apply)
            for line in inner:
                verb = "removed" if args.apply else "would remove"
                print(f"{path}!{line} ({verb})")
            if inner:
                changed.append((str(path), ["archive members"], 0))
            continue
        data = path.read_bytes()
        holds = gate.scan(data)
        if not holds:
            continue
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            new = normalize_png(data)
        elif data[:2] == b"\xff\xd8":
            new = normalize_jpeg(data)
        elif data[:6] in (b"GIF87a", b"GIF89a"):
            new = normalize_gif(data)
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            new = normalize_webp(data)
        elif data[4:8] in (b"ftyp", b"moov", b"wide", b"mdat", b"free", b"skip"):
            if not shutil.which("ffmpeg"):
                # Reported as needing a re-encode, since nothing here can perform one.
                new = None
            elif not args.apply:
                # A report does not run ffmpeg, so it stands in for the rewrite.
                new = b""
            else:
                scratch = path.with_name(f".normalize-{path.name}")
                new = scratch.read_bytes() if normalize_iso(path, scratch) else None
                scratch.unlink(missing_ok=True)
        else:
            new = None

        name = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
        if new is None:
            reencode.append((name, sorted(holds)))
            continue
        before, after = pixel_payload(data), pixel_payload(new) if new else None
        if before is not None and after != before:
            reencode.append((name, [*sorted(holds), "rewrite would not be lossless"]))
            continue
        changed.append((name, sorted(holds), len(data) - len(new) if new else 0))
        saved += len(data) - len(new) if new else 0
        if args.apply and new:
            path.write_bytes(new)

    for name, holds, delta in changed:
        verb = "removed" if args.apply else "would remove"
        print(f"{name}: {verb} {', '.join(holds)} ({delta} bytes)")
    for name, holds in reencode:
        print(f"{name}: needs a re-encode, dropping cannot reach {', '.join(holds)}")

    print()
    print(
        f"{len(changed)} file(s) {'normalized' if args.apply else 'to normalize'}, {saved} bytes"
    )
    if reencode:
        print(
            f"{len(reencode)} file(s) need a re-encode, which this does not do for you"
        )
    if not args.apply and changed:
        print("this was a report, pass --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
