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
and a file at neither is an error rather than a guess. The pinned Pillow version is
what makes the output reproducible byte for byte, so a change to it re-records the
results with `--record` in the same change.

A JPEG is written with its own quantization tables and chroma subsampling, so the
blocks outside a fill do not lose generation quality. Its color profile and its
allowlisted Exif segment are carried across, and the output goes through the same
lossless drop as `scripts/normalize-media.py`, so the metadata gate passes on it.
"""

import argparse
import hashlib
import importlib.util
import io
import json
import pathlib
import sys

from PIL import Image, ImageDraw, JpegImagePlugin

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "checks" / "media-redactions.json"
FILL = (0, 0, 0)

# The normalizer's filename carries a hyphen, so it loads by path rather than by import.
_spec = importlib.util.spec_from_file_location(
    "normalize", REPO / "scripts" / "normalize-media.py"
)
normalize = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(normalize)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redact(data: bytes, entry: dict) -> bytes:
    """Return the file's bytes with the entry's fills and crop applied."""
    source = Image.open(io.BytesIO(data))
    if source.format not in ("JPEG", "PNG") or source.mode not in ("RGB", "RGBA"):
        raise ValueError(f"unsupported {source.format} {source.mode}")
    image = source.copy()
    draw = ImageDraw.Draw(image)
    for x0, y0, x1, y1 in entry.get("fill", []):
        fill = FILL + (255,) if image.mode == "RGBA" else FILL
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=fill)
    if "crop" in entry:
        image = image.crop(tuple(entry["crop"]))

    out = io.BytesIO()
    options = {}
    if source.info.get("icc_profile"):
        options["icc_profile"] = source.info["icc_profile"]
    if source.format == "JPEG":
        if source.info.get("exif"):
            options["exif"] = source.info["exif"]
        image.save(
            out,
            "JPEG",
            qtables=source.quantization,
            subsampling=JpegImagePlugin.get_sampling(source),
            progressive=bool(source.info.get("progressive")),
            **options,
        )
    else:
        if source.info.get("dpi"):
            options["dpi"] = source.info["dpi"]
        image.save(out, "PNG", compress_level=9, **options)
    result = out.getvalue()
    return normalize.normalize_bytes(result) or result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply", action="store_true", help="write the files, rather than reporting"
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="write any missing or changed hashes into the manifest, implies --apply",
    )
    args = parser.parse_args()
    apply = args.apply or args.record

    manifest = json.loads(MANIFEST.read_text())
    done, pending, errors = 0, 0, []
    for name, entry in manifest["files"].items():
        path = REPO / name
        data = path.read_bytes()
        current = sha256(data)
        if args.record and "source" not in entry:
            entry["source"] = current
        if current == entry.get("result"):
            done += 1
            continue
        if current != entry.get("source"):
            errors.append(f"{name}: matches neither its source nor its result hash")
            continue
        new = redact(data, entry)
        if args.record:
            entry["result"] = sha256(new)
        elif sha256(new) != entry.get("result"):
            errors.append(f"{name}: redacted output does not match its result hash")
            continue
        pending += 1
        verb = "redacted" if apply else "would redact"
        print(f"{name}: {verb}")
        if apply:
            path.write_bytes(new)

    if args.record:
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    for line in errors:
        print(line)
    print()
    print(
        f"{done} already redacted, {pending} {'redacted' if apply else 'to redact'}, {len(errors)} error(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
