#!/usr/bin/env python3
"""Verify the built site against the URL contract.

Checks that every URL which must render exists, that every legacy media URL resolves, that
every local asset reference points at a file, and that no carried media file is linked from
nowhere. Redirects need a running server and are checked by check-live-urls.sh instead.
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

# Media carried by the import that no built page links to.
# The other two media checks run outward from a reference and cannot see these: a legacy URL
# resolving proves an inbound link still lands, and a reference resolving proves it names a real
# file. Neither asks whether anything points at a given file, so an image the conversion dropped
# from a page stays reachable by URL, invisible on the site, and green in both directions.
# Every one traces to the WordPress conversion rather than to anything this repo does. Five empty
# gallery shortcodes across three posts are the identified cause of some of them, and the rest are
# unadjudicated. The count is exact rather than a bound, so restoring a gallery lowers it here in
# the same change and slack can never accumulate for a later regression to hide in.
ORPHANED_MEDIA = 120


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
            missing.append(f"{url} (does not match the @uploads rewrite prefix)")
        elif not (public / rewritten.lstrip("/")).is_file():
            missing.append(url)
    print(f"media  : {len(legacy) - len(missing)}/{len(legacy)} legacy image URLs resolve after the @uploads rewrite")
    return missing


def collect_refs(public):
    """Every local asset reference in the built pages.

    Read once and shared, since the assets and orphans checks are the same reference set
    read in opposite directions.
    """
    # Minification drops the quotes around an attribute value that does not need them.
    # Matching only the quoted form checks a fraction of the references and calls it a pass.
    quoted = re.compile(r'(?:src|href|srcset)="(/(?:media|external)/[^"]+)"')
    bare = re.compile(r"(?:src|href|srcset)=(/(?:media|external)/[^\s\"'>]+)")
    refs = set()
    for page in public.rglob("*.html"):
        text = page.read_text(encoding="utf-8", errors="ignore")
        refs.update(quoted.findall(text))
        refs.update(bare.findall(text))
    return refs


def ref_to_path(ref):
    """Map a reference to the path under the built site it names."""
    # Imported references carry resize parameters a static file server ignores.
    # Some also escape an underscore, which a server decodes before looking up the file.
    return unquote(ref.split("?", 1)[0].split("#", 1)[0]).lstrip("/")


def check_assets(public, refs):
    """Check that every local asset a built page references exists on disk.

    Catches a media file renamed, dropped, or never localized.
    """
    missing = [ref for ref in sorted(refs) if not (public / ref_to_path(ref)).is_file()]
    print(f"assets : {len(refs) - len(missing)}/{len(refs)} local asset references resolve")
    return missing


def check_orphans(public, refs):
    """Check that every carried media file is linked from some built page.

    The reverse of the assets check, and the only one that can see an image the conversion
    dropped from a page: it stays on disk and reachable by URL, so nothing else objects.
    """
    linked = {ref_to_path(ref) for ref in refs}
    carried, orphaned = 0, []
    for tree in ("media", "external"):
        root = public / tree
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            carried += 1
            # `linked` holds URL paths, which are always forward-slashed, so a native separator
            # here would match nothing and report every carried file as an orphan. check_render
            # normalizes for the same reason.
            rel = str(path.relative_to(public)).replace("\\", "/")
            if rel not in linked:
                orphaned.append(rel)
    orphaned.sort()
    print(f"orphans: {len(orphaned)} of {carried} carried media files are linked from no page")
    if len(orphaned) == ORPHANED_MEDIA:
        return []
    # The explanation is printed rather than returned, so the caller's count stays the orphan
    # count. A diagnostic carried in the failure list would make the reported total one too many.
    if len(orphaned) > ORPHANED_MEDIA:
        print(f"         expected {ORPHANED_MEDIA} - a page stopped linking media it used to link")
        return orphaned
    print(
        f"         expected {ORPHANED_MEDIA} - media was restored to a page, so lower "
        f"ORPHANED_MEDIA to {len(orphaned)} in this change rather than leaving the slack"
    )
    return orphaned


def main(argv):
    if len(argv) != 2:
        sys.exit(f"usage: {argv[0]} <public-dir>")
    public = pathlib.Path(argv[1])
    if not public.is_dir():
        sys.exit(f"FAIL: {public} is not a directory - run hugo first")

    refs = collect_refs(public)
    failures = []
    for label, missing in (
        ("render", check_render(public)),
        ("media", check_media(public)),
        ("assets", check_assets(public, refs)),
        ("orphans", check_orphans(public, refs)),
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
