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


def png_chunk(name: bytes, body: bytes) -> bytes:
    crc = zlib.crc32(name + body) & 0xFFFFFFFF
    return struct.pack(">I", len(body)) + name + body + struct.pack(">I", crc)


def normalize_png(data: bytes) -> bytes | None:
    """Drop every ancillary chunk that is not on the allowlist.

    A known profile in a body that is not pinned is re-emitted in the one canonical body.
    An sBIT or bKGD out of its one value, out of place, or repeated, is dropped, since no browser draws by either.
    So is a PLTE in a truecolor image, which only suggests a palette.
    A file is refused where it holds an APNG frame, since dropping one would leave the default image alone, or where `exif_orientation` refuses its Exif Orientation, or where that Orientation turns the picture.
    """
    parts, problems = gate.png_parts(data)
    if problems - gate.TRAILING:
        return None
    header = gate.png_header(data, parts)
    palette = sum(e - s - 12 for c, s, e in parts if c == b"PLTE") // 3
    out = bytearray(data[:8])
    kept: set[bytes] = set()
    misplaced = gate.png_misplaced([bytes(c) for c, _, _ in parts])
    for at, (chunk, start, end) in enumerate(parts):
        body = data[start + 8 : end - 4]
        if chunk == b"eXIf" and exif_orientation(body) != 1:
            return None
        if chunk in gate.PNG_ANIMATION:
            return None
        if chunk not in gate.PNG_ALLOWED:
            if not chunk[0] & 0x20:
                # A critical chunk cannot be dropped, so this file needs a re-encode.
                return None
            continue
        repeated = chunk in gate.PNG_ONCE and chunk in kept
        known = gate.png_field_known(chunk, body, header, palette)
        if repeated or at in misplaced or not known:
            # Which copy a decoder reads, and how it reads a value out of range, is its own choice.
            if gate.png_undrawn(chunk, header):
                continue
            return None
        kept.add(chunk)
        if chunk == b"iCCP" and gate.png_icc_problems(body):
            profile = gate.png_icc_profile(body)
            if profile is None or not gate.icc_known(profile):
                return None
            out += png_chunk(chunk, gate.png_icc_body(profile))
        else:
            out += data[start:end]
    return bytes(out)


def exif_orientation(segment: bytes) -> int | None:
    """The Orientation value in an Exif segment or chunk, or 1 where it says nothing.

    A browser reads it only as one SHORT, where other decoders read a LONG too.
    Any other shape is None, so the file is refused rather than guessed at.
    Two entries that disagree are None too, in IFD0 or in an IFD reached from it, since decoders take either one.
    An IFD0 holding none counts as 1 against a value held elsewhere, since a browser reads IFD0.
    Decoders differ on whether they read an IFD whose entries run past the segment, or an IFD0 inside
    the TIFF header. An Orientation in or reached from such an IFD0 is None, and one held past IFD0 is
    None where reading it changes the answer. An Orientation entry the segment cuts off is None wherever it sits.
    """
    raw = segment.removeprefix(b"Exif\x00\x00")
    if raw[:2] not in (b"II", b"MM"):
        return 1
    fmt = "<" if raw[:2] == b"II" else ">"
    try:
        if struct.unpack_from(fmt + "H", raw, 2)[0] != 42:
            return 1
        ifd0 = struct.unpack_from(fmt + "I", raw, 4)[0]
    except struct.error:
        return 1
    # Each pending IFD carries what malformed IFD led to it: none, one past IFD0, or IFD0 itself.
    pending = [(ifd0, 0)]
    seen: set[int] = set()
    behind: set[int] = set()
    values: set[int] = set()
    maybe: set[int] = set()
    placed = False
    while pending:
        offset, taint = pending.pop()
        # An offset the gate skips costs it none of its 16 IFDs, so it costs none here.
        # The gate never walks what a malformed IFD leads to, so that has a budget of its own.
        walked = behind if taint else seen
        outside = offset + 2 > len(raw) or (offset < 8 and offset != ifd0)
        # A clean path walks an IFD again though a malformed one reached it first, as the gate does.
        if (
            outside
            or offset in seen
            or (taint and offset in behind)
            or len(walked) >= 16
        ):
            continue
        walked.add(offset)
        count = struct.unpack_from(fmt + "H", raw, offset)[0]
        if offset < 8 or offset + 2 + count * 12 > len(raw):
            taint = taint or (2 if offset == ifd0 else 1)
        for index in range(count):
            entry = offset + 2 + index * 12
            if entry + 2 > len(raw):
                break
            tag = struct.unpack_from(fmt + "H", raw, entry)[0]
            # A browser reads a malformed IFD0 or it does not, so an Orientation there or behind it is disputed.
            if tag == 0x0112 and (taint == 2 or entry + 12 > len(raw)):
                return None
            if entry + 12 > len(raw):
                break
            if tag == 0x0112:
                if struct.unpack_from(fmt + "HI", raw, entry + 2) != (3, 1):
                    return None
                value = struct.unpack_from(fmt + "H", raw, entry + 8)[0]
                (maybe if taint else values).add(value)
                placed = placed or offset == ifd0
            elif tag in gate.EXIF_POINTERS:
                pointer = struct.unpack_from(fmt + "I", raw, entry + 8)[0]
                pending.append((pointer, taint))
    held = settled(values, placed)
    # A decoder may read an Orientation held in a malformed IFD or skip it, so both readings must agree.
    return held if settled(values | maybe, placed) == held else None


def settled(values: set[int], placed: bool) -> int | None:
    """The one Orientation a set of values read from an Exif segment settles on, or None where they disagree.

    An IFD0 holding none counts as 1 against a value held elsewhere, since a browser reads IFD0.
    """
    if values and not placed:
        values = values | {1}
    if len(values) > 1:
        return None
    value = next(iter(values)) if values else 1
    return value if 1 <= value <= 8 else 1


def app_segment(marker: int, body: bytes) -> bytes:
    return bytes((0xFF, marker)) + struct.pack(">H", len(body) + 2) + body


def orientation_segment(value: int) -> bytes:
    """A minimal Exif segment carrying nothing but Orientation."""
    entry = struct.pack("<HHI", 0x0112, 3, 1) + struct.pack("<HH", value, 0)
    tiff = b"II" + struct.pack("<HI", 42, 8) + struct.pack("<H", 1) + entry
    return app_segment(0xE1, b"Exif\x00\x00" + tiff + struct.pack("<I", 0))


def normalize_jpeg(data: bytes) -> bytes | None:
    """Drop every APP and comment segment that is not on the allowlist.

    A JFIF segment is kept once, and a JFIF or Adobe segment is cut to its fixed fields.
    A known profile is re-emitted in its canonical chunks where the first of its own chunks stood.
    """
    parts, problems = gate.jpeg_parts(data)
    if problems - gate.TRAILING:
        return None
    names = [
        gate.jpeg_app_name(m, data[s + 4 : e]) if 0xE0 <= m <= 0xEF else None
        for m, s, e in parts
    ]
    profile = [
        data[s + 4 : e] for (_, s, e), n in zip(parts, names) if n == b"ICC_PROFILE\x00"
    ]
    adobe = [
        n for (_, s, e), n in zip(parts, names) if n == b"Adobe" and e - s - 4 >= 12
    ]
    # With a broken profile, or a second Adobe or Exif, what draws is the decoder's choice.
    trouble = gate.icc_problems(profile) - {
        "JPEG ICC profile not in its canonical chunks"
    }
    # Moving a chunk a decoder never read to where it reads one redraws the picture.
    late = gate.jpeg_late_icc(data, parts)
    if trouble or late or len(adobe) > 1 or names.count(b"Exif\x00\x00") > 1:
        return None
    out = bytearray(data[:2])
    kept: set[bytes] = set()
    for (marker, start, end), name in zip(parts, names):
        segment = data[start + 4 : end]
        if name == b"ICC_PROFILE\x00":
            if name not in kept:
                kept.add(name)
                chunks = gate.icc_chunks(gate.icc_profile(profile))
                out += b"".join(app_segment(marker, chunk) for chunk in chunks)
        elif name in gate.JPEG_APP_FIXED:
            fixed = gate.JPEG_APP_FIXED[name]
            # A decoder ignores one shorter than its fields, so dropping it changes nothing.
            if name not in kept and len(segment) >= fixed:
                kept.add(name)
                body = segment[:fixed]
                if name == b"JFIF\x00":
                    body = body[:12] + b"\x00\x00"
                if gate.jpeg_app_fields(name, body):
                    out += app_segment(marker, body)
                elif name == b"JFIF\x00":
                    out += app_segment(marker, gate.JFIF_FIELDS)
                elif body[11] <= 2:
                    # The transform decides how the picture decodes, so only it is kept.
                    out += app_segment(marker, gate.ADOBE_FIELDS + body[11:])
                else:
                    return None
        elif name:
            # An Exif segment the gate flags is dropped, since rewriting it means re-computing every offset.
            # Orientation decides which way the picture displays, so a turn is re-emitted alone.
            # A file whose Orientation is not one SHORT, or holds two different values, is refused.
            if not gate.exif_unrecognized(segment):
                out += data[start:end]
            elif (turned := exif_orientation(segment)) is None:
                return None
            elif turned != 1:
                out += orientation_segment(turned)
        elif 0xE0 <= marker <= 0xEF or marker == 0xFE:
            continue
        elif marker in gate.JPEG_STRUCTURAL:
            out += data[start:end]
        else:
            # An unknown marker may be one a decoder needs, so dropping it is not safe.
            return None
    return bytes(out)


def normalize_gif(data: bytes) -> bytes | None:
    """Drop every extension block that is not on the allowlist.

    A graphic control block's reserved bits and unused transparent index are written as zero.
    So are the screen and image descriptor fields no browser draws by, and a global table no image reads is dropped.
    """
    parts, problems = gate.gif_parts(data)
    if problems - gate.TRAILING:
        return None
    out = bytearray()
    for kind, start, end in parts:
        block = data[start:end]
        if kind == "extension 0xF9" and gate.gif_extension_allowed(block):
            control = gate.gif_control(block)
            if control is None:
                return None
            out += control
        elif kind == "header":
            out += gate.gif_screen(block, gate.gif_table_read(data, parts))
        elif kind == "image":
            out += gate.gif_descriptor(block)
        elif not str(kind).startswith("extension") or gate.gif_extension_allowed(block):
            out += block
        elif block[1] == 0xF9:
            # A graphic control extension sets transparency and timing, so it is not dropped.
            return None
    # Every field gif_fields names is written above, so this guards only against the two drifting apart.
    return None if gate.gif_fields(bytes(out)) else bytes(out)


def riff_chunk(data: bytes, start: int) -> bytes:
    """The chunk at start with a zero pad byte, whatever its own pad held."""
    length = struct.unpack_from("<I", data, start + 4)[0]
    return data[start : start + 8 + length] + bytes(length & 1)


def normalize_webp(data: bytes) -> bytes | None:
    """Drop every chunk that is not on the allowlist, and restate the RIFF size.

    The VP8X reserved bits, the ANIM background color and each pad byte are written as zero.
    A file is refused where `exif_orientation` refuses its Exif Orientation, or where that Orientation turns the picture.
    """
    parts, problems = gate.webp_parts(data)
    if problems - gate.TRAILING:
        return None
    names = {bytes(c) for c, _, _ in parts if c in gate.WEBP_ALLOWED}
    body = bytearray()
    for chunk, start, _ in parts:
        length = struct.unpack_from("<I", data, start + 4)[0]
        if (
            chunk == b"EXIF"
            and exif_orientation(data[start + 8 : start + 8 + length]) != 1
        ):
            return None
        if chunk not in gate.WEBP_ALLOWED:
            continue
        if gate.WEBP_FIXED.get(chunk, length) != length:
            # A decoder refuses a fixed chunk of another size, so this is not a drop.
            return None
        if chunk == b"VP8X":
            flags = data[start + 8]
            # A decoder reads a profile or frames only where a flag announces them, so a flip redraws.
            if not gate.vp8x_agrees(flags, names):
                return None
            body += (
                data[start : start + 8]
                + bytes((flags & ~gate.VP8X_RESERVED,))
                + bytes(3)
            )
            body += data[start + 12 : start + 18]
            continue
        if chunk == b"ANIM":
            # No browser draws the background color, so it is written as zero.
            body += data[start : start + 8] + bytes(4) + data[start + 12 : start + 14]
            continue
        if chunk != b"ANMF":
            body += riff_chunk(data, start)
            continue
        inner, trouble = gate.anmf_parts(data, start)
        if trouble - gate.TRAILING:
            return None
        frame = data[start + 8 : start + 8 + gate.WEBP_FRAME_HEADER]
        frame += b"".join(
            riff_chunk(data, s) for c, s, _ in inner if c in gate.WEBP_FRAME_ALLOWED
        )
        body += b"ANMF" + struct.pack("<I", len(frame)) + frame + bytes(len(frame) & 1)
    result = b"RIFF" + struct.pack("<I", len(body) + 4) + b"WEBP" + body
    # Which of two images a decoder draws is its own choice, so that needs a person.
    # An unknown profile or a frame header out of its values is not something a drop resolves.
    refused = gate.webp_layout(result) or gate.webp_fields(result)
    return None if not body or refused else result


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


NORMALIZERS = {
    "png": normalize_png,
    "jpeg": normalize_jpeg,
    "gif": normalize_gif,
    "webp": normalize_webp,
}


def normalize_bytes(data: bytes) -> bytes | None:
    """Dispatch one file's bytes to the normalizer for its container."""
    normalizer = NORMALIZERS.get(gate.container(data))
    return normalizer(data) if normalizer else None


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
    if gate.container(data) == "iso":
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
    try:
        archive = zipfile.ZipFile(path)
    except gate.ZIP_ERRORS as exc:
        print(f"{path}: unreadable archive, {type(exc).__name__}")
        return removed
    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if info.file_size > gate.SIZE_LIMIT:
                stuck.append(f"{info.filename}: too large to read")
                continue
            try:
                data = archive.read(info)
            except gate.ZIP_ERRORS as exc:
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
            except gate.ZIP_ERRORS:
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


def unpadded(data: bytes, start: int) -> bytes:
    """The chunk at start without its pad byte, which no decoder reads."""
    return data[start : start + 8 + struct.unpack_from("<I", data, start + 4)[0]]


def pixel_payload(data: bytes) -> bytes | None:
    """Return the bytes a decoder draws the picture from, so a rewrite can be proven lossless.

    None means this cannot isolate them for that format, so the caller asserts nothing
    rather than comparing whole files and calling every rewrite lossy.
    """
    kind = gate.container(data)
    if kind == "png":
        parts, _ = gate.png_parts(data)
        return b"".join(data[s + 8 : e - 4] for c, s, e in parts if c == b"IDAT")
    if kind == "jpeg":
        parts, _ = gate.jpeg_parts(data)
        return b"".join(data[s:e] for m, s, e in parts if m in gate.JPEG_STRUCTURAL)
    if kind == "gif":
        # The descriptor fields the normalizer zeroes are not drawn, so they are compared as it writes them.
        parts, _ = gate.gif_parts(data)
        read = gate.gif_table_read(data, parts)
        drawn = {
            "header": lambda b: gate.gif_screen(b, read),
            "image": gate.gif_descriptor,
        }
        return b"".join(drawn[k](data[s:e]) for k, s, e in parts if k in drawn)
    if kind == "webp":
        parts, _ = gate.webp_parts(data)
        drawn = bytearray()
        for chunk, start, _ in parts:
            if chunk == b"ANMF":
                inner, _ = gate.anmf_parts(data, start)
                drawn += data[start + 8 : start + 8 + gate.WEBP_FRAME_HEADER]
                drawn += b"".join(
                    unpadded(data, s)
                    for c, s, _ in inner
                    if c in gate.WEBP_FRAME_ALLOWED
                )
            elif chunk in gate.WEBP_FRAME_ALLOWED:
                drawn += unpadded(data, start)
        return bytes(drawn)
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
        if gate.container(data) != "iso":
            new = normalize_bytes(data)
        elif not shutil.which("ffmpeg"):
            # Reported as needing a re-encode, since nothing here can perform one.
            new = None
        elif not args.apply:
            # A report does not run ffmpeg, so it stands in for the rewrite.
            new = b""
        else:
            scratch = path.with_name(f".normalize-{path.name}")
            new = scratch.read_bytes() if normalize_iso(path, scratch) else None
            scratch.unlink(missing_ok=True)

        name = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
        if new is None:
            reencode.append((name, sorted(holds)))
            continue
        before, after = pixel_payload(data), pixel_payload(new) if new else None
        if before is not None and after != before:
            reencode.append((name, [*sorted(holds), "rewrite would not be lossless"]))
            continue
        if new and gate.scan(new):
            reencode.append((name, [*sorted(holds), "rewrite would still not pass"]))
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
