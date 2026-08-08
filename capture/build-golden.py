#!/usr/bin/env python3
"""Build the golden URL list: every URL the live WordPress site actually serves.

Three sources, unioned, then every candidate verified against the live site:

  1. The recursive crawl - finds linked pages, but misses anything unlinked.
  2. The sitemap - only 111 URLs, misses taxonomy terms entirely.
  3. Derivation - date archives and pagination are served but linked from nowhere,
     so no crawl can find them. Computed from post dates and taxonomy post counts.

Verification is what makes the list authoritative: a candidate is kept only if the
live site answers for it. The output is split by how Hugo must satisfy each URL:

  golden-urls.txt   - must render as a page (200)
  redirect-urls.txt - must redirect (301/308), or is a WordPress-ism with no Hugo
                      equivalent (attachment pages, per-post comment feeds) that we
                      choose to redirect to the parent post rather than reproduce.
"""

import json
import math
import os
import re
import sys
import threading
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from queue import Queue

def env(name: str) -> str:
    """A required capture value, refused rather than guessed when unset.

    Duplicated across the scripts here rather than shared, because these get copied out to
    a scratch directory to run, and an import would break the moment one travelled alone.
    """
    v = os.environ.get(name, "")
    if not v:
        sys.exit(f"{name} is not set -- see example.env and ENVIRONMENT.md")
    return v


BASE = env("CAPTURE_SOURCE_URL")
API = env("CAPTURE_SOURCE_API")
PER_PAGE = 10  # measured against the old platform: the post count paginated to /page/11/
# The capture, never this script's directory. Both outputs below are capture artifacts and
# must not be able to land in the repository's checks/, whose lists are append-only and are
# grown by hand from a log finding rather than regenerated.
ROOT = Path(env("CAPTURE_ROOT"))
UA = {"User-Agent": "Mozilla/5.0 (compatible; blog-migration-audit/1.0)"}


def api(path):
    req = urllib.request.Request(f"{API}/{path}", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def norm(p):
    p = re.sub(r"^https?://[^/]+", "", p)
    p = p.split("#")[0]
    if not p.startswith("/"):
        p = "/" + p
    return p if p.endswith("/") else p + "/"


def pages_for(count):
    """Pagination URLs beyond page 1 for an archive holding `count` posts."""
    return range(2, math.ceil(count / PER_PAGE) + 1) if count > PER_PAGE else []


def build_candidates():
    cand = {"/"}

    # 1. Crawl
    log = (ROOT / "crawl" / "spider.log").read_text(encoding="utf-8", errors="replace")
    # Built from CAPTURE_SOURCE_URL rather than written in, so the pattern and the site the
    # crawl actually ran against cannot drift apart.
    crawled = {norm(u) for u in re.findall(re.escape(BASE) + r"[^\s]*", log)}
    cand |= {u for u in crawled if not u.startswith("/wp-content/")}
    print(f"  crawl:      {len(crawled)} paths")

    # 2. Sitemap
    try:
        req = urllib.request.Request(f"{BASE}/sitemap.xml", headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            sm = {norm(u) for u in re.findall(r"<loc>([^<]+)</loc>", r.read().decode())}
        cand |= sm
        print(f"  sitemap:    {len(sm)} URLs")
    except Exception as e:  # noqa: BLE001 - the sitemap is a nice-to-have source
        print(f"  sitemap:    FAILED ({e})", file=sys.stderr)

    # 3. Derivation - the part no crawl can reach.
    posts = json.loads((ROOT / "inventory" / "posts.json").read_text(encoding="utf-8"))
    derived = set()

    ym = Counter()
    for p in posts:
        d = p.get("date", "")
        if len(d) >= 7:
            ym[(d[:4], d[5:7])] += 1
    years = Counter()
    for (y, m), n in ym.items():
        derived.add(f"/{y}/{m}/")
        years[y] += n
        for i in pages_for(n):
            derived.add(f"/{y}/{m}/page/{i}/")
    for y, n in years.items():
        derived.add(f"/{y}/")
        for i in pages_for(n):
            derived.add(f"/{y}/page/{i}/")

    for i in pages_for(len(posts)):
        derived.add(f"/page/{i}/")

    for kind, key, field in (("category", "categories", "categories"), ("tag", "tags", "tags")):
        data = api(f"{field}?number=500")[key]
        for t in data:
            derived.add(f"/{kind}/{t['slug']}/")
            for i in pages_for(t["post_count"]):
                derived.add(f"/{kind}/{t['slug']}/page/{i}/")

    derived.add("/feed/")
    cand |= derived
    print(f"  derived:    {len(derived)} URLs (date archives + pagination, unlinked)")
    return sorted(cand)


def verify(urls, workers=6):
    """HEAD every candidate. Redirects are recorded, not followed."""
    out, q, lock = {}, Queue(), threading.Lock()
    for u in urls:
        q.put(u)

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(NoRedirect)

    def worker():
        while True:
            try:
                u = q.get_nowait()
            except Exception:  # noqa: BLE001 - empty queue ends the worker
                return
            code, loc = 0, ""
            for _ in range(3):
                try:
                    req = urllib.request.Request(BASE + u, headers=UA, method="HEAD")
                    with opener.open(req, timeout=25) as r:
                        code, loc = r.status, r.headers.get("Location", "")
                    break
                except urllib.error.HTTPError as e:
                    code, loc = e.code, e.headers.get("Location", "")
                    break
                except Exception:  # noqa: BLE001 - transient, retry
                    continue
            with lock:
                out[u] = (code, loc)
                if len(out) % 200 == 0:
                    print(f"    verified {len(out)}/{len(urls)}", flush=True)
            q.task_done()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out


def main():
    print("Building candidate set:")
    cand = build_candidates()
    print(f"  UNION:      {len(cand)} candidates\n")

    print("Verifying against the live site:")
    res = verify(cand)

    # An attachment page is /YYYY/MM/DD/post/attachment/ - a WordPress-ism with no Hugo
    # equivalent. The image itself stays at its wp-content path; the page redirects home
    # to its parent post. Per-post /feed/ endpoints get the same treatment.
    attach = re.compile(r"^/\d{4}/\d{2}/\d{2}/[^/]+/[^/]+/$")
    feed = re.compile(r"/feed/$")

    golden, redirect, dropped = [], [], []
    for u, (code, loc) in sorted(res.items()):
        if code in (301, 302, 307, 308):
            redirect.append((u, code, loc))
        elif code == 200:
            (redirect if (attach.match(u) or (feed.search(u) and u != "/feed/")) else golden).append(
                (u, code, "")
            )
        else:
            dropped.append((u, code, loc))

    (ROOT / "checks").mkdir(exist_ok=True)
    (ROOT / "checks" / "golden-urls.txt").write_text("".join(f"{u}\n" for u, _, _ in golden), encoding="utf-8")
    (ROOT / "checks" / "redirect-urls.txt").write_text("".join(f"{u}\n" for u, _, _ in redirect), encoding="utf-8")
    with (ROOT / "checks" / "url-verification.tsv").open("w", encoding="utf-8") as fh:
        fh.write("class\tstatus\turl\tlocation\n")
        for name, rows in (("golden", golden), ("redirect", redirect), ("dropped", dropped)):
            for u, c, loc in rows:
                fh.write(f"{name}\t{c}\t{u}\t{loc}\n")

    print(f"\n  GOLDEN (must render):  {len(golden)}")
    print(f"  REDIRECT:              {len(redirect)}")
    print(f"  dropped (4xx/5xx/0):   {len(dropped)}")
    print("\n  golden by shape:")
    shape = Counter()
    for u, _, _ in golden:
        if u == "/":
            shape["home"] += 1
        elif re.match(r"^/\d{4}/\d{2}/\d{2}/[^/]+/$", u):
            shape["post"] += 1
        elif "/page/" in u:
            shape["pagination"] += 1
        elif u.startswith("/tag/"):
            shape["tag archive"] += 1
        elif u.startswith("/category/"):
            shape["category archive"] += 1
        elif re.match(r"^/\d{4}/(\d{2}/)?$", u):
            shape["date archive"] += 1
        else:
            shape["page/other"] += 1
    for k, v in shape.most_common():
        print(f"    {k:20} {v}")
    if dropped:
        print(f"\n  sample dropped: {[u for u, _, _ in dropped[:5]]}")


if __name__ == "__main__":
    main()
