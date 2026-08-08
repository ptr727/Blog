#!/usr/bin/env python3
"""Reorganise the content tree so its shape matches the published URLs.

wp2hugo files posts by year/month while the URL carries year/month/**day**, so the
source tree and the URL tree disagree. This makes them identical:

    content/posts/2024/05/29/slug.md   ->   /2024/05/29/slug/

The `url:` front matter is the authority, not the `date:` field - it is WordPress's own
permalink, and the two can legitimately disagree if a post was ever re-dated.

Standalone pages move to the content root, which is Hugo's idiomatic place for them:

    content/pages/2012/07/about/index.md   ->   content/about.md   ->   /about/

They were nested under a date only because wp2hugo's date-folder option applies to pages
as well as posts, which is meaningless for a page. A `content/pages/` section would also
make Hugo publish a `/pages/` listing URL, the same unwanted extra as `/posts/`.
"""

import pathlib
import os
import re
import shutil
import sys

FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
URL = re.compile(r"^url:\s*(\S+)\s*$", re.M)
DATED = re.compile(r"^/(\d{4})/(\d{2})/(\d{2})/([^/]+)/$")


def capture_root() -> pathlib.Path:
    """CAPTURE_ROOT, refused rather than guessed when unset.

    Duplicated in each script here rather than shared, because these get copied out to a
    scratch directory to run against a copy of the capture, and an import would break the
    moment one of them travelled alone.
    """
    root = os.environ.get("CAPTURE_ROOT", "")
    if not root:
        sys.exit("CAPTURE_ROOT is not set -- see example.env and ENVIRONMENT.md")
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


def url_of(p: pathlib.Path):
    m = FM.match(p.read_text(encoding="utf-8"))
    if not m:
        return None
    u = URL.search(m.group(1))
    return u.group(1).strip().strip("\"'") if u else None


def main(site: pathlib.Path, apply: bool):
    content = site / "content"
    moves, problems = [], []

    # --- posts: content/posts/<Y>/<M>/<slug>.md -> content/posts/<Y>/<M>/<D>/<slug>.md
    for p in sorted((content / "posts").rglob("*.md")):
        u = url_of(p)
        if not u:
            problems.append((p, "no url: front matter"))
            continue
        m = DATED.match(u)
        if not m:
            problems.append((p, f"url not /Y/M/D/slug/: {u}"))
            continue
        y, mo, d, slug = m.groups()
        dest = content / "posts" / y / mo / d / f"{slug}.md"
        if dest != p:
            moves.append((p, dest))

    # --- pages: anywhere under content/pages -> content/<slug>.md
    for p in sorted((content / "pages").rglob("*.md")):
        u = url_of(p)
        if not u:
            problems.append((p, "no url: front matter"))
            continue
        slug = u.strip("/").split("/")[-1]
        moves.append((p, content / f"{slug}.md"))

    print(f"posts and pages to relocate: {len(moves)}")
    for src, dst in moves[:4]:
        print(f"    {src.relative_to(content)}\n      -> {dst.relative_to(content)}")
    if problems:
        print(f"\nPROBLEMS ({len(problems)}):")
        for p, why in problems:
            print(f"    {p.relative_to(content)}: {why}")

    if apply:
        for src, dst in moves:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        # Remove directories left empty by the move.
        for _ in range(6):
            for d in sorted(content.rglob("*"), key=lambda x: -len(x.parts)):
                if d.is_dir() and not any(d.iterdir()):
                    d.rmdir()
        print("\nAPPLIED")
    else:
        print("\nDRY RUN - pass --apply")


if __name__ == "__main__":
    main(converted_site(sys.argv), "--apply" in sys.argv)
