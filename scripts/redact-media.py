#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow==11.3.0"]
# ///
"""Apply the redactions declared in `checks/media-redactions.json` to carried media.

Run on demand with `uv run scripts/redact-media.py`, rather than in CI, because it
rewrites files. `checks/check-media-redactions.py` is the gate that proves the result.

**The manifest is the whole of the decision.** Each entry names a file, the flat
opaque fills and the crop it takes, and why, so a redaction is reviewed as data and
reproduced by running this rather than placed by hand. Nothing here looks for anything.

**Deterministic and idempotent.** An entry records the hash of the file it expects,
the normalized original, and the hash of the file it produces. A file already at its
result is left alone, a file at its source is redacted and must land on its result,
and a file at neither is an error rather than a guess. An entry also records a digest
of its fills and crop, so an edit to them that was never rerun fails the gate. The
pinned Pillow version, with the codecs its wheel bundles for the platform, is what
makes the output reproducible byte for byte.

**A redacted file no longer holds its source, so changing one starts from history.**
Restore the file's original with `git checkout <revision> -- <file>`, normalize it
with `scripts/normalize-media.py --apply`, edit its entry, and run with `--record`.
The same restore, run without `--record`, is how a Pillow upgrade is checked, since a
changed output is then reported against the recorded result.

A JPEG is written with its own quantization tables and chroma subsampling, which keeps
the generation loss outside a fill to a level or two, and a crop off the block grid
costs more. Its color profile is carried across and its Exif is not, since an Exif
block can hold a thumbnail of the frame before the fill. A PNG is written at 8 bits and
keeps its gamma, chromaticity, and sRGB chunks and its alpha channel, the fills opaque.
One whose transparency is a tRNS color key is refused, since the key carries across and
a fill in the key's color would come out transparent. An animated PNG is refused, since
a fill would reach only its first frame.
The output then goes through the same lossless drop as `scripts/normalize-media.py`.
"""

import argparse
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import struct
import sys

from PIL import Image, ImageDraw, JpegImagePlugin

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "checks" / "media-redactions.json"
FILL = (0, 0, 0)
PNG_COLOR_CHUNKS = (b"gAMA", b"cHRM", b"sRGB")

# The normalizer's filename carries a hyphen, so it loads by path rather than by import.
_spec = importlib.util.spec_from_file_location(
    "normalize", REPO / "scripts" / "normalize-media.py"
)
normalize = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(normalize)
_spec = importlib.util.spec_from_file_location(
    "check", REPO / "checks" / "check-media-redactions.py"
)
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)
_spec = importlib.util.spec_from_file_location(
    "gate", REPO / "checks" / "check-media-metadata.py"
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    """Each chunk's type and its whole bytes, length and CRC included."""
    chunks, i = [], 8
    while i + 8 <= len(data):
        length = struct.unpack_from(">I", data, i)[0]
        chunks.append((data[i + 4 : i + 8], data[i : i + 12 + length]))
        i += 12 + length
    return chunks


def carry_png_color(source: bytes, result: bytes) -> bytes:
    """Put the source's color chunks back after IHDR, which Pillow does not write."""
    have = {kind for kind, _ in png_chunks(result)}
    extra = b"".join(
        raw
        for kind, raw in png_chunks(source)
        if kind in PNG_COLOR_CHUNKS and kind not in have
    )
    ihdr_end = 8 + 12 + struct.unpack_from(">I", result, 8)[0]
    return result[:ihdr_end] + extra + result[ihdr_end:]


def boxes(entry: dict) -> list[list[int]]:
    """The entry's fills, then its crop, each checked to be four integers."""
    fill, crop = entry.get("fill", []), entry.get("crop")
    if not isinstance(fill, list):
        raise TypeError(f"fill {fill!r} is not a list of boxes")
    out = fill + ([crop] if crop is not None else [])
    for box in out:
        if not (
            isinstance(box, list)
            and len(box) == 4
            and all(type(value) is int for value in box)
        ):
            raise ValueError(f"box {box!r} is not four integers")
    return out


def redact(data: bytes, entry: dict) -> bytes:
    """Return the file's bytes with the entry's fills and crop applied."""
    source = Image.open(io.BytesIO(data))
    if source.format not in ("JPEG", "PNG") or source.mode not in ("RGB", "RGBA"):
        raise ValueError(f"unsupported {source.format} {source.mode}")
    if source.getexif().get(0x0112, 1) != 1:
        raise ValueError("rotated by Exif, so the manifest's coordinates are ambiguous")
    if "transparency" in source.info:
        raise ValueError("carries a tRNS color key, which a fill could match")
    if getattr(source, "n_frames", 1) != 1:
        raise ValueError("animated, and a fill would reach only its first frame")
    sampling = JpegImagePlugin.get_sampling(source) if source.format == "JPEG" else 0
    if sampling == -1:
        raise ValueError("chroma subsampling the JPEG writer cannot reproduce")
    width, height = source.size
    for x0, y0, x1, y1 in boxes(entry):
        if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            raise ValueError(f"box {[x0, y0, x1, y1]} is outside {width}x{height}")
    image = source.copy()
    draw = ImageDraw.Draw(image)
    for x0, y0, x1, y1 in entry.get("fill", []):
        fill = FILL + (255,) if image.mode == "RGBA" else FILL
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=fill)
    if entry.get("crop") is not None:
        image = image.crop(tuple(entry["crop"]))

    out = io.BytesIO()
    options = {}
    if source.info.get("icc_profile"):
        options["icc_profile"] = source.info["icc_profile"]
    if source.format == "JPEG":
        image.save(
            out,
            "JPEG",
            qtables=source.quantization,
            subsampling=sampling,
            progressive=bool(source.info.get("progressive")),
            **options,
        )
    else:
        if source.info.get("dpi"):
            options["dpi"] = source.info["dpi"]
        image.save(out, "PNG", compress_level=9, **options)
    result = out.getvalue()
    if source.format == "PNG":
        result = carry_png_color(data, result)
    return normalize.normalize_bytes(result) or result


def replace(path: pathlib.Path, data: bytes) -> None:
    """Write through a scratch file, so the path holds either its old bytes or the new ones."""
    scratch = path.with_name(f".redact-{path.name}")
    try:
        scratch.write_bytes(data)
        os.replace(scratch, path)
    finally:
        scratch.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply", action="store_true", help="write the files, rather than reporting"
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="for each entry whose fills or crop changed, take the file as its source and record the result",
    )
    args = parser.parse_args()
    apply = args.apply or args.record

    manifest = json.loads(MANIFEST.read_text())
    done, errors = 0, []
    writes: list[tuple[pathlib.Path, str, bytes]] = []
    for name, entry in manifest["files"].items():
        path = REPO / name
        if not isinstance(entry, dict):
            errors.append(f"{name}: entry is not an object")
            continue
        try:
            data = path.read_bytes()
        except OSError as error:
            errors.append(f"{name}: {error.strerror or error}")
            continue
        current = sha256(data)
        spec = check.declared(entry)
        changed = spec != entry.get("declared")
        if changed and current == entry.get("result"):
            errors.append(f"{name}: fills or crop changed, restore its original first")
            continue
        if changed and not args.record:
            errors.append(f"{name}: fills or crop changed, rerun with --record")
            continue
        if current == entry.get("result"):
            done += 1
            continue
        if changed and (unclean := gate.scan(data)):
            errors.append(
                f"{name}: not normalized ({', '.join(sorted(unclean))}), run scripts/normalize-media.py --apply"
            )
            continue
        if not changed and current != entry.get("source"):
            errors.append(f"{name}: matches neither its source nor its result hash")
            continue
        try:
            new = redact(data, entry)
        except (OSError, TypeError, ValueError) as error:
            errors.append(f"{name}: {error}")
            continue
        if changed:
            entry["source"], entry["declared"] = current, spec
            entry["result"] = sha256(new)
        elif sha256(new) != entry.get("result"):
            errors.append(f"{name}: redacted output does not match its result hash")
            continue
        writes.append((path, current, new))
        print(f"{name}: to redact")

    moved = set()
    for path, current, _ in writes if apply else []:
        try:
            same = sha256(path.read_bytes()) == current
        except OSError:
            same = False
        if not same:
            moved.add(path)
            errors.append(
                f"{path.relative_to(REPO).as_posix()}: changed during the run"
            )
    # Under --record the manifest and the files move together, so any failure writes neither.
    written = 0
    if apply and not (args.record and errors):
        # The manifest goes first, and each file is replaced whole, so an interrupted run leaves a file at its source.
        try:
            if args.record:
                replace(MANIFEST, (json.dumps(manifest, indent=2) + "\n").encode())
            for path, _, new in writes:
                if path not in moved:
                    replace(path, new)
                    written += 1
        except OSError as error:
            errors.append(f"not every file was replaced, rerun to converge ({error})")
    for line in errors:
        print(line)
    print()
    pending = len(writes) - written
    print(
        f"{done} already redacted, {written} redacted, {pending} {'not written' if apply else 'to redact'}, {len(errors)} error(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
