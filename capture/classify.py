#!/usr/bin/env python3
"""Split the verified URL set into what Hugo must render and what must redirect.

Reads the cached verification results so this can be re-run without re-hitting the
live site. The discriminator that matters: WordPress serves an attachment page for
every uploaded image, at BOTH /YYYY/MM/DD/post/attachment/ and a bare /attachment/.
A bare one-segment URL is therefore ambiguous with a real page, and the sitemap is
the authority - it lists exactly the posts and pages, so a one-segment URL absent
from it is an attachment page, not content.
"""

import os
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path



def env(name: str) -> str:
    """A required capture value, refused rather than guessed when unset.

    Duplicated across the scripts here rather than shared, because these get copied out to
    a scratch directory to run, and an import would break the moment one travelled alone.
    """
    v = os.environ.get(name, "")
    if not v:
        sys.exit(f"{name} is not set -- see .secrets/example.env and ENVIRONMENT.md")
    return v


# The capture, never this script's directory. Both outputs below are capture artifacts and
# must not be able to land in the repository's checks/, whose lists are append-only.
ROOT = Path(env("CAPTURE_ROOT"))
BASE = env("CAPTURE_SOURCE_URL")
UA = {"User-Agent": "Mozilla/5.0 (compatible; blog-migration-audit/1.0)"}

req = urllib.request.Request(f"{BASE}/sitemap.xml", headers=UA)
with urllib.request.urlopen(req, timeout=30) as r:
    sitemap = {
        re.sub(r"^https?://[^/]+", "", u).rstrip("/") + "/"
        for u in re.findall(r"<loc>([^<]+)</loc>", r.read().decode())
    }

rows = [
    line.rstrip("\n").split("\t")
    for line in (ROOT / "checks" / "url-verification.tsv").read_text(encoding="utf-8").splitlines()[1:]
]
status = {r[2]: (int(r[1]), r[3] if len(r) > 3 else "") for r in rows}

# The author archive and its pagination are served but linked from nowhere, and on a
# single-author blog they duplicate the home archive exactly. Verified live: /page/11/
# is the last one.
#
# Optional, and skipped loudly rather than silently. An account slug is not this
# repository's to carry, and a run without it produces a list short by the author URLs
# rather than a wrong one. Silence would be indistinguishable from a site that never
# served them.
AUTHOR_SLUG = os.environ.get("CAPTURE_AUTHOR_SLUG", "")
if AUTHOR_SLUG:
    for i in range(2, 12):
        status.setdefault(f"/author/{AUTHOR_SLUG}/page/{i}/", (200, ""))
    status.setdefault(f"/author/{AUTHOR_SLUG}/", (200, ""))
else:
    print("CAPTURE_AUTHOR_SLUG is not set: skipping the author archive backfill", file=sys.stderr)

POST = re.compile(r"^/\d{4}/\d{2}/\d{2}/[^/]+/$")
NESTED_ATTACH = re.compile(r"^/\d{4}/\d{2}/\d{2}/[^/]+/[^/]+/$")
DATE = re.compile(r"^/\d{4}/(\d{2}/)?$")
DATE_PAGED = re.compile(r"^/\d{4}/(\d{2}/)?page/\d+/$")
HOME_PAGED = re.compile(r"^/page/\d+/$")
TERM = re.compile(r"^/(tag|category)/[^/]+/(page/\d+/)?$")
AUTHOR = re.compile(r"^/author/[^/]+/(page/\d+/)?$")

golden, redirect, dropped = [], [], []
reason = Counter()

for url, (code, _loc) in sorted(status.items()):
    if code not in (200, 301, 302, 307, 308):
        dropped.append(url)
        continue
    if code != 200:
        redirect.append(url)
        reason["already a redirect on WordPress"] += 1
    elif NESTED_ATTACH.match(url):
        redirect.append(url)
        reason["attachment page (nested)"] += 1
    elif url.endswith("/feed/") and url != "/feed/":
        redirect.append(url)
        reason["per-post or per-term feed"] += 1
    elif url == "/feed/":
        redirect.append(url)
        reason["site feed -> /index.xml"] += 1
    elif AUTHOR.match(url):
        redirect.append(url)
        reason["author archive (single author, duplicates home)"] += 1
    elif DATE.match(url) or DATE_PAGED.match(url):
        # Decision (2026-07-29): Hugo has no built-in year/month archive, and these are
        # absent from the sitemap and linked from nowhere on the live site. Building them
        # would be the only custom templating in the migration, for URLs nothing points at.
        # One Caddy pattern rule sends them home instead.
        redirect.append(url)
        reason["date archive -> / (no Hugo equivalent, unlinked)"] += 1
    elif POST.match(url) or HOME_PAGED.match(url) or TERM.match(url) or url == "/":
        golden.append(url)
    elif url.rstrip("/").count("/") == 1:
        # One segment: a real page if the sitemap lists it, otherwise an attachment.
        if url in sitemap:
            golden.append(url)
        else:
            redirect.append(url)
            reason["attachment page (root level)"] += 1
    else:
        golden.append(url)

(ROOT / "checks" / "golden-urls.txt").write_text("".join(f"{u}\n" for u in sorted(golden)), encoding="utf-8")
(ROOT / "checks" / "redirect-urls.txt").write_text("".join(f"{u}\n" for u in sorted(redirect)), encoding="utf-8")

shape = Counter()
for u in golden:
    if u == "/":
        shape["home"] += 1
    elif POST.match(u):
        shape["post"] += 1
    elif TERM.match(u) and "/page/" in u:
        shape["taxonomy pagination"] += 1
    elif u.startswith("/tag/"):
        shape["tag archive"] += 1
    elif u.startswith("/category/"):
        shape["category archive"] += 1
    elif DATE.match(u):
        shape["date archive"] += 1
    elif DATE_PAGED.match(u) or HOME_PAGED.match(u):
        shape["date/home pagination"] += 1
    else:
        shape["page"] += 1

print(f"GOLDEN (Hugo must render):  {len(golden)}")
for k, v in shape.most_common():
    print(f"    {k:24} {v}")
print(f"\nREDIRECT:                   {len(redirect)}")
for k, v in reason.most_common():
    print(f"    {k:46} {v}")
print(f"\ndropped (4xx):              {len(dropped)}")
