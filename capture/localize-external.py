#!/usr/bin/env python3
"""Download every externally-hosted image and rewrite the content to point at local copies.

wp2hugo skips these entirely ("non-relative link (skipped for download)"), and they are
absent from the WordPress export too, because they were never in the media library - they
are hotlinks from the Windows Live Writer and Blogger era. If they are not localized they
remain a permanent dependency on Google serving 15-year-old URLs.

Two traps this handles, both of which return HTTP 200 and look like success:

1. **The `-h` wrapper.** A Picasa/ggpht URL whose size segment ends in `-h` (`/s1600-h/`)
   serves an HTML *page* containing an `<img>` tag, not the image. Fetching it naively
   yields a 400-byte HTML file with a 200 status. The fix is to parse the wrapper and
   follow the `<img src>` it names, which is Google's own answer rather than a guess.
2. **Non-image bodies generally.** Anything whose magic bytes are not an image is a
   failure regardless of status code, and is reported rather than written.

Writes images to static/external/ named by a hash of the source URL (these URLs carry
percent-encoded brackets and other characters that do not survive a filesystem), records
the mapping in external-media-map.tsv for auditability, and rewrites every reference.
"""

import hashlib
import pathlib
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter

UA = {"User-Agent": "Mozilla/5.0 (compatible; blog-migration-audit/1.0)"}
EXT_HOST = re.compile(r"^https?://[a-z0-9.-]*\.(?:ggpht|googleusercontent)\.com/", re.I)
URL_IN_CONTENT = re.compile(r"https?://[a-z0-9.-]*\.(?:ggpht|googleusercontent)\.com/[^\s\"'\)\]<>]+", re.I)
IMG_IN_WRAPPER = re.compile(rb'<img\s+src="([^"]+)"', re.I)

MAGIC = [
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
    (b"BM", ".bmp"),
]
# RIFF is a container, not a format: WAV and AVI share the header. Matching it alone would
# accept a sound file as an image, which is precisely the failure the magic-byte check
# exists to prevent, so WEBP is confirmed at bytes 8 to 12 in sniff() below.


def capture_root() -> pathlib.Path:
    """CAPTURE_ROOT, refused rather than guessed when unset.

    Duplicated in each script here rather than shared, because these get copied out to a
    scratch directory to run against a copy of the capture, and an import would break the
    moment one of them travelled alone.
    """
    root = os.environ.get("CAPTURE_ROOT", "")
    if not root:
        sys.exit("CAPTURE_ROOT is not set -- see .secrets/example.env and ENVIRONMENT.md")
    return pathlib.Path(root)


def converted_site(argv) -> pathlib.Path:
    """The converted site: a first argument, else the one generated-* under the capture.

    Ambiguity aborts rather than picking, the same rule build-redirects.py applies to the
    export. wp2hugo stamps the directory with a run timestamp, so there is no fixed name
    to default to and a glob that matched two would otherwise choose by filesystem order.
    """
    if len(argv) > 1 and not argv[1].startswith("--"):
        return pathlib.Path(argv[1])
    found = sorted((capture_root() / "converted").glob("generated-*"))
    if len(found) != 1:
        sys.exit(
            f"expected exactly one converted site under {capture_root()}/converted, found {len(found)}"
            + "".join(f"\n  {p}" for p in found)
            + "\npass one as the first argument"
        )
    return found[0]


def sniff(data: bytes):
    for sig, ext in MAGIC:
        if data.startswith(sig):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def fetch(url: str, depth: int = 0):
    """Return (bytes, ext) or (None, reason). Follows one level of `-h` HTML wrapper."""
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 - network is the expected failure here
        return None, type(e).__name__

    ext = sniff(body)
    if ext:
        return body, ext

    # Not an image. If it is Google's `-h` wrapper page, it names the real image.
    # A wrapper page is HTML, and HTML does not reliably start with <html>. A doctype, a
    # comment or leading whitespace are all ordinary, and requiring the tag meant a wrapper
    # that opened with <!doctype html> was reported as "not an image" rather than followed.
    head = body.lstrip()[:64].lower()
    if depth == 0 and (head.startswith(b"<html") or head.startswith(b"<!doctype html")):
        m = IMG_IN_WRAPPER.search(body)
        if m:
            return fetch(m.group(1).decode("utf-8", "replace"), depth + 1)
        # Fall back to the documented convention if the tag is absent.
        stripped = re.sub(r"/(s\d+|w\d+|h\d+)-h/", r"/\1/", url)
        if stripped != url:
            return fetch(stripped, depth + 1)
    return None, "not an image"


def main(site: pathlib.Path, apply: bool):
    content = site / "content"
    urls = sorted({m.group(0) for p in content.rglob("*.md") for m in URL_IN_CONTENT.finditer(p.read_text(encoding="utf-8", errors="replace"))})
    print(f"external image URLs referenced in content: {len(urls)}")

    out_dir = site / "static" / "external"
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping, failures, stats = {}, [], Counter()

    for i, u in enumerate(urls, 1):
        body, ext = fetch(u)
        if body is None:
            failures.append((u, ext))
            stats[f"FAILED: {ext}"] += 1
            continue
        name = hashlib.sha256(u.encode()).hexdigest()[:16] + ext
        if apply:
            (out_dir / name).write_bytes(body)
        mapping[u] = f"/external/{name}"
        stats[f"ok{ext}"] += 1
        if i % 50 == 0:
            print(f"  {i}/{len(urls)}", flush=True)

    for k, v in sorted(stats.items()):
        print(f"  {v:4}  {k}")

    if apply and mapping:
        rewritten = 0
        for p in content.rglob("*.md"):
            t = orig = p.read_text(encoding="utf-8")
            for u, local in mapping.items():
                if u in t:
                    t = t.replace(u, local)
            if t != orig:
                p.write_text(t, encoding="utf-8")
                rewritten += 1
        print(f"\ncontent files rewritten: {rewritten}")
        # Anchored on the capture, not walked up from the site. The old relative form
        # assumed the site sat exactly two levels down, which is true of a wp2hugo output
        # directory and false of any copy taken somewhere else to work on.
        inv = capture_root() / "inventory"
        inv.mkdir(parents=True, exist_ok=True)
        (inv / "external-media-map.tsv").write_text(
            "source_url\tlocal_path\n" + "".join(f"{u}\t{v}\n" for u, v in sorted(mapping.items())),
            encoding="utf-8",
        )

    print("\nAPPLIED" if apply else "\nDRY RUN - pass --apply")
    if failures:
        # Non-zero in both modes. An image that cannot be fetched is a reference this site
        # would keep pointing at someone else's server, which is the dependency this script
        # exists to remove, so a partial run must not read as a success to whatever ran it.
        # A dry run counts too: what fails to fetch now fails to fetch under --apply.
        print(f"\nUNRESOLVED ({len(failures)}):")
        for u, why in failures[:20]:
            print(f"  {why:14} {u[:110]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(converted_site(sys.argv), "--apply" in sys.argv))
