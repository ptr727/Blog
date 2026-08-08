#!/usr/bin/env python3
"""Enumerate every media URL referenced by the live WordPress.com site.

Pulls all posts and pages from the old platform's REST API, named by CAPTURE_SOURCE_API,
and extracts
every media reference from the rendered HTML. The rendered form is deliberate:
shortcodes are already expanded, so this sees what a reader's browser sees.

The critical output is the by-host breakdown. Media on the wp.com subdomain is in
the media library and will appear in the WXR export; media on lh*.ggpht.com and
googleusercontent.com is hotlinked from the Windows Live Writer era, is NOT in the
library, and will NOT be in the export. That subset is the migration's biggest
silent-data-loss risk, so it gets enumerated explicitly.

Writes: media-urls.tsv (host, url, post_id, post_url), posts.json (raw archive).
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

def env(name: str) -> str:
    """A required capture value, refused rather than guessed when unset.

    Duplicated across the scripts here rather than shared, because these get copied out to
    a scratch directory to run, and an import would break the moment one travelled alone.
    """
    v = os.environ.get(name, "")
    if not v:
        sys.exit(f"{name} is not set -- see example.env and ENVIRONMENT.md")
    return v


API = env("CAPTURE_SOURCE_API")
# Written into the capture, never beside this script. Anchoring on __file__ would put the
# inventory inside the repository the moment this file moved into it, which it now has.
OUT = Path(env("CAPTURE_ROOT")) / "inventory"

# src/href targets that are media rather than navigation.
MEDIA_EXT = re.compile(
    r"\.(?:jpe?g|png|gif|webp|avif|svg|ico|bmp|tiff?|mp4|m4v|mov|webm|mp3|m4a|wav|ogg|pdf|zip|7z|txt|csv|xlsx?|docx?)"
    r"(?:[?#]|$)",
    re.IGNORECASE,
)
# Attributes that can carry a media URL, including responsive-image sets.
ATTR = re.compile(r"""(?:src|href|data-orig-file|data-large-file|data-medium-file|poster)\s*=\s*["']([^"']+)["']""", re.I)
SRCSET = re.compile(r"""srcset\s*=\s*["']([^"']+)["']""", re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "blog-migration-audit/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def all_items(kind, extra=""):
    """Page through a collection until exhausted.

    Pages go through here too, with type=page, rather than a single number=100 request.
    That request was correct for this site and silently wrong for any site with more than
    a hundred pages, which is the shape of loss this whole capture exists to catch.
    """
    items, page = [], 1
    while True:
        data = fetch(f"{API}/{kind}/?number=100&page={page}{extra}&fields=ID,URL,slug,title,date,content")
        found = data.get("posts", [])
        if not found:
            break
        items.extend(found)
        if len(items) >= data.get("found", 0):
            break
        page += 1
    return items


def extract(html):
    urls = set()
    for m in ATTR.finditer(html or ""):
        urls.add(m.group(1).strip())
    for m in SRCSET.finditer(html or ""):
        for candidate in m.group(1).split(","):
            part = candidate.strip().split()
            if part:
                urls.add(part[0])
    return {u for u in urls if MEDIA_EXT.search(u)}


def main():
    posts = all_items("posts")
    pages = all_items("posts", extra="&type=page")
    everything = posts + pages
    print(f"fetched {len(posts)} posts + {len(pages)} pages", file=sys.stderr)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "posts.json").write_text(json.dumps(everything, indent=1), encoding="utf-8")

    rows, by_host, per_post = [], Counter(), defaultdict(set)
    for item in everything:
        for u in extract(item.get("content", "")):
            absolute = urllib.parse.urljoin(item["URL"], u)
            host = urllib.parse.urlparse(absolute).netloc.lower()
            by_host[host] += 1
            per_post[item["ID"]].add(absolute)
            rows.append((host, absolute, str(item["ID"]), item["URL"]))

    with (OUT / "media-urls.tsv").open("w", encoding="utf-8") as fh:
        fh.write("host\turl\tpost_id\tpost_url\n")
        for row in sorted(set(rows)):
            fh.write("\t".join(row) + "\n")

    unique = {r[1] for r in rows}
    print(f"\n{len(rows)} media references, {len(unique)} unique URLs\n")
    print(f"{'host':45} refs")
    for host, n in by_host.most_common():
        print(f"{host:45} {n}")

    # The at-risk subset, called out explicitly.
    risky = sorted(u for u in unique if re.search(r"(ggpht|googleusercontent)\.com", u))
    (OUT / "media-external-hotlinked.txt").write_text("\n".join(risky) + "\n", encoding="utf-8")
    print(f"\nNOT in the media library (absent from any WXR export): {len(risky)} unique URLs")
    print("  -> inventory/media-external-hotlinked.txt")


if __name__ == "__main__":
    main()
