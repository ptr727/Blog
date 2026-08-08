#!/usr/bin/env python3
"""Reduce the converted site to content only.

Two jobs, both decided deliberately:

1. **Drop comments entirely.** The blog is read-only going forward - no comments, no
   interaction. Deleting the data file rather than scrubbing it means there is no PII
   question at all, no partial to write, and nothing to carry.

2. **Strip front matter to what actually drives the site.** wp2hugo carries every
   WordPress custom field through, which is 156 distinct keys across 108 posts, 127 of
   them WordPress internals (`_edit_last`, `_oembed_<md5>`, `_jetpack_*`, `_coblocks_*`,
   `_publicize_*`). None of it is content.

Kept, with the reason each earns its place:

  title       required
  date        required, drives the permalink and ordering
  url         the exact WordPress permalink - keeping it guarantees URL preservation
              independent of any hugo.yaml permalink config
  categories  taxonomy, 12 terms
  tags        taxonomy, 183 terms
  post_id     drives the ?p=<ID> shortlink redirect map - inbound-link surface
  cover       featured image, {alt, image}, on 33 posts

Dropped on purpose: `author` (single-author blog, the site knows), `guid` (GUID
preservation was dropped, and wp2hugo rewrote the scheme to https anyway, which would
have broken RSS), `parent_post_id` (null on every post), `blogger_*` (provenance from an
earlier Blogger migration), `publicize_*` (dead social-share links), `geo_*` (no template
consumes it), and every `_`-prefixed WordPress internal.
"""

import os
import re
import shutil
import sys
import pathlib
from pathlib import Path

import yaml

KEEP = ["title", "date", "url", "categories", "tags", "post_id", "cover"]
FM = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


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


def main(root: Path, apply: bool):
    stats = {"files": 0, "keys_before": 0, "keys_after": 0, "no_title": []}

    data = root / "data"
    if data.exists():
        n = sorted(p.name for p in data.iterdir())
        print(f"data/ to delete: {n}")
        if apply:
            shutil.rmtree(data)

    for p in sorted(root.joinpath("content").rglob("*.md")):
        raw = p.read_text(encoding="utf-8")
        m = FM.match(raw)
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        body = m.group(2)
        stats["files"] += 1
        stats["keys_before"] += len(fm)

        out = {k: fm[k] for k in KEEP if k in fm and fm[k] not in (None, "", [])}
        if not out.get("title"):
            # Recover a title from the slug rather than shipping an untitled page.
            slug = p.parent.name if p.name == "index.md" else p.stem
            out["title"] = slug.replace("-", " ").title()
            out = {"title": out["title"], **{k: v for k, v in out.items() if k != "title"}}
            stats["no_title"].append(f"{p.relative_to(root)} -> {out['title']!r}")
        stats["keys_after"] += len(out)

        # sort_keys=False preserves the KEEP order, which reads better than alphabetical.
        new = "---\n" + yaml.dump(out, sort_keys=False, allow_unicode=True, width=10**6) + "---\n" + body
        if apply:
            p.write_text(new, encoding="utf-8")

    print(f"\nfiles processed : {stats['files']}")
    print(f"front-matter keys: {stats['keys_before']} -> {stats['keys_after']}"
          f"  ({stats['keys_before'] - stats['keys_after']} removed)")
    if stats["no_title"]:
        print(f"\ntitle recovered from slug ({len(stats['no_title'])}):")
        for t in stats["no_title"]:
            print("   ", t)
    print("\nAPPLIED" if apply else "\nDRY RUN - pass --apply to write")


if __name__ == "__main__":
    main(converted_site(sys.argv), "--apply" in sys.argv)
