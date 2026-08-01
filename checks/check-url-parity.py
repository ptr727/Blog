#!/usr/bin/env python3
"""Verify the built site against the URL contract.

Checks that every URL which must render exists, that every legacy media URL resolves, and that
every local asset reference points at a file. Redirects need a running server and are checked
by check-live-urls.sh instead.
"""

import pathlib
import re
import sys
from urllib.parse import unquote

# A truncated list would make every assertion below it pass vacuously while the gate stays green.
# The floors sit under the known-good counts, so a list may grow but not collapse.
FLOORS = {
    "golden-urls.txt": 320,
    "redirect-urls.txt": 900,
    "golden-media-legacy.txt": 770,
}

CHECKS = pathlib.Path(__file__).resolve().parent


def load(name):
    lines = [ln.strip() for ln in (CHECKS / name).read_text().splitlines()]
    urls = [ln for ln in lines if ln]
    floor = FLOORS[name]
    if len(urls) < floor:
        sys.exit(f"FAIL {name}: {len(urls)} URLs, expected at least {floor} - the list has been truncated")
    return urls


def url_to_file(public, url):
    """Map a site URL to the file Hugo builds for it."""
    path = url.strip("/")
    return public / path / "index.html" if path else public / "index.html"


def check_render(public):
    golden = load("golden-urls.txt")
    missing = [u for u in golden if not url_to_file(public, u).is_file()]
    built = {
        "/" + str(p.parent.relative_to(public)).replace("\\", "/").strip(".") + "/"
        for p in public.rglob("index.html")
    }
    built = {u if u.startswith("/") else "/" + u for u in built}
    extra = sorted(built - set(golden))
    print(f"render : {len(golden) - len(missing)}/{len(golden)} golden URLs built")
    if extra:
        print(f"         {len(extra)} additional URLs built (not a failure)")
    return missing


def check_media(public):
    """Check that every legacy image URL resolves under the renamed media tree.

    The render gate covers pages only, so nothing else protects the image URL surface.
    """
    legacy = load("golden-media-legacy.txt")
    missing = []
    for url in legacy:
        rewritten = re.sub(r"^/wp-content/uploads/", "/media/", url)
        if rewritten == url:
            missing.append(f"{url} (does not match the R8 rewrite prefix)")
        elif not (public / rewritten.lstrip("/")).is_file():
            missing.append(url)
    print(f"media  : {len(legacy) - len(missing)}/{len(legacy)} legacy image URLs resolve after the R8 rewrite")
    return missing


def check_assets(public):
    """Check that every local asset a built page references exists on disk.

    Catches a media file renamed, dropped, or never localized.
    """
    # Minification drops the quotes around an attribute value that does not need them.
    # Matching only the quoted form checks a fraction of the references and calls it a pass.
    quoted = re.compile(r'(?:src|href|srcset)="(/(?:media|external)/[^"]+)"')
    bare = re.compile(r"(?:src|href|srcset)=(/(?:media|external)/[^\s\"'>]+)")
    refs, missing = set(), []
    for page in public.rglob("*.html"):
        text = page.read_text(encoding="utf-8", errors="ignore")
        refs.update(quoted.findall(text))
        refs.update(bare.findall(text))
    for ref in sorted(refs):
        # Imported references carry resize parameters a static file server ignores.
        # Some also escape an underscore, which a server decodes before looking up the file.
        path = unquote(ref.split("?", 1)[0].split("#", 1)[0])
        if not (public / path.lstrip("/")).is_file():
            missing.append(ref)
    print(f"assets : {len(refs) - len(missing)}/{len(refs)} local asset references resolve")
    return missing


def main(argv):
    if len(argv) != 2:
        sys.exit(f"usage: {argv[0]} <public-dir>")
    public = pathlib.Path(argv[1])
    if not public.is_dir():
        sys.exit(f"FAIL: {public} is not a directory - run hugo first")

    failures = []
    for label, missing in (
        ("render", check_render(public)),
        ("media", check_media(public)),
        ("assets", check_assets(public)),
    ):
        if missing:
            failures.append((label, missing))

    if not failures:
        print("\nPASS - the built site honors the URL contract")
        return 0

    print()
    for label, missing in failures:
        print(f"FAIL {label}: {len(missing)} missing")
        for item in missing[:20]:
            print(f"  {item}")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
