#!/usr/bin/env python3
"""Generate the Caddy redirect maps from the WordPress export.

Reads the export and the capture inventory, which live outside this repo, and writes the
committed maps under deploy/maps/. See capture/README.md for when to run it.

The capture directory comes from CAPTURE_ROOT, and a first argument wins over it. This
generates rather than gates, which is why it sits in capture/ beside the other scripts
that read the capture rather than in checks/ beside the gates.
"""

import os
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

NS = {"wp": "http://wordpress.org/export/1.2/"}

# Anchored on the repository rather than on this file's own directory, because the two
# lists below live in checks/ and the maps in deploy/maps/, and neither follows this
# script if it moves again.
REPO = pathlib.Path(__file__).resolve().parent.parent
CHECKS = REPO / "checks"

# Blogger truncates an auto-generated slug at this many characters, on a whole-word boundary.
# For a longer slug the truncated form is the URL Blogger served, and so the one in search indexes.
# The WordPress importer registers the full slug, and both answer, so both are mapped.
BLOGGER_SLUG_LIMIT = 40

# A one-segment URL naming a file the site serves at the root, rather than a page slug.
# The resolver below reads these as unresolvable attachment slugs and sends them to the home
# page, which is the right answer for a slug nothing claims and the wrong one for a file that
# exists: /robots.txt/ should reach /robots.txt. Named here rather than hand-edited into the
# generated map, because the map is rewritten from the capture and a hand edit does not survive.
# /osd.xml/ stays out deliberately. It was the old platform's OpenSearch description and this
# site emits no such file, so the home page remains the honest destination for it.
WELL_KNOWN = {"/robots.txt/": "/robots.txt"}


def text(el, path):
    node = el.find(path, NS)
    return node.text if node is not None and node.text else ""


def path_of(url):
    """Strip the scheme and host, leaving a rooted path with a trailing slash."""
    return re.sub(r"^https?://[^/]+", "", url).rstrip("/") + "/"


def blogger_truncate(slug, limit=BLOGGER_SLUG_LIMIT):
    """Join the slug's words while the result stays within `limit` characters."""
    out = ""
    for word in slug.split("-"):
        candidate = word if not out else f"{out}-{word}"
        if len(candidate) > limit:
            break
        out = candidate
    return out


def write_map(path, pairs):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{k} {v}\n" for k, v in pairs), encoding="utf-8")
    return len(pairs)


def main(argv):
    # CAPTURE_ROOT is the default and an argument wins over it, the same shape DEPLOY_ROOT
    # uses. Unset and unsupplied is refused rather than guessed: a wrong-but-plausible
    # capture yields maps that are empty and indistinguishable from working ones.
    # --print-export names the selected export and writes nothing. run-wp2hugo.sh calls it
    # rather than reimplementing the choice, so the conversion and the maps are provably
    # built from the same file. A shell reimplementation cannot match this anyway: the test
    # is that ONE item carries both post_type=post and status=publish, and two greps over a
    # whole file would accept a media-only export that happens to contain both words.
    args = [a for a in argv[1:] if a != "--print-export"]
    print_export = "--print-export" in argv[1:]
    # An unknown option is refused rather than taken as a path. Without this, `--help` is
    # read as a capture directory and the run fails with "no export XML found under --help",
    # which sends the reader looking for a missing file rather than a mistyped flag.
    unknown = [a for a in args if a.startswith("-")]
    if unknown:
        print(f"unknown option: {unknown[0]}", file=sys.stderr)
        print(f"usage: {argv[0]} [--print-export] [capture-dir]", file=sys.stderr)
        return 2
    if len(args) > 1:
        print(f"usage: {argv[0]} [--print-export] [capture-dir]", file=sys.stderr)
        return 2
    root = args[0] if args else os.environ.get("CAPTURE_ROOT", "")
    if not root:
        print(f"usage: {argv[0]} [--print-export] [capture-dir]", file=sys.stderr)
        print("CAPTURE_ROOT is not set and no capture directory was given", file=sys.stderr)
        print("see .secrets/example.env and ENVIRONMENT.md", file=sys.stderr)
        return 2
    capture = pathlib.Path(root)
    out = REPO / "deploy" / "maps"

    # An account holds several exports, and a media-only one carries the attachments but no posts.
    # Filesystem order decides which a glob returns, and the wrong one yields empty maps that look valid.
    # Selection is by content, and an ambiguous result aborts rather than guesses.
    candidates = sorted(capture.glob("export/raw/**/*.xml"))
    if not candidates:
        print(f"no WordPress export XML found under {capture}/export/raw", file=sys.stderr)
        return 1
    with_posts = []
    for path in candidates:
        tree = ET.parse(path).getroot()
        if any(
            text(i, "wp:post_type") == "post" and text(i, "wp:status") == "publish" for i in tree.iter("item")
        ):
            with_posts.append((path, tree))
    if len(with_posts) != 1:
        print(f"expected exactly 1 export containing published posts, found {len(with_posts)}:", file=sys.stderr)
        for path, _ in with_posts:
            print(f"  {path}", file=sys.stderr)
        return 1
    src, root = with_posts[0]
    if print_export:
        print(src)
        return 0
    print(f"export: {src}")

    posts, attachments, blogger, terms = {}, [], [], []
    for item in root.iter("item"):
        pid = text(item, "wp:post_id")
        ptype = text(item, "wp:post_type")
        published = text(item, "wp:status") == "publish"
        if ptype in ("post", "page") and published:
            posts[pid] = path_of(text(item, "link"))
            # Any blogger_* postmeta marks a post from before the move off Blogger.
            # The permalink value is a numeric post id rather than a path.
            # The old path is rebuilt from the publish date and the slug.
            if ptype == "post" and any(
                text(m, "wp:meta_key").startswith("blogger_") for m in item.findall("wp:postmeta", NS)
            ):
                blogger.append((text(item, "wp:post_date"), text(item, "wp:post_name"), posts[pid]))
        elif ptype == "attachment":
            attachments.append((text(item, "wp:post_name"), text(item, "wp:post_parent")))

    for tag in root.iter("{http://wordpress.org/export/1.2/}tag"):
        terms.append((text(tag, "wp:tag_slug"), "tag"))
    for cat in root.iter("{http://wordpress.org/export/1.2/}category"):
        terms.append((text(cat, "wp:category_nicename"), "category"))

    # --- p-ids.map : /?p=<id> -> permalink
    n_pids = write_map(out / "p-ids.map", sorted(posts.items(), key=lambda kv: int(kv[0])))

    # --- blogger.map : /YYYY/MM/<slug>.html -> permalink, both slug forms
    bmap = {}
    truncated = 0
    for date, name, dest in blogger:
        prefix = f"/{date[:4]}/{date[5:7]}"
        bmap[f"{prefix}/{name}.html"] = dest
        short = blogger_truncate(name)
        if short != name:
            bmap[f"{prefix}/{short}.html"] = dest
            truncated += 1
    n_blogger = write_map(out / "blogger.map", sorted(bmap.items()))

    # Blogger label archives, keyed on the label rather than on a path.
    # Destinations come from the golden render list, not the export's term table, which disagrees with it.
    # A term the generator does not build is itself a redirect, so pointing a label at one chains them.
    # Reading the render list also resolves a slug that exists as both a tag and a category.
    # Map lookups are case-sensitive, so each slug is emitted alongside a capitalized variant.
    rendered = set()
    for line in (CHECKS / "golden-urls.txt").read_text(encoding="utf-8").splitlines():
        if m := re.match(r"^/(tag|category)/([^/]+)/$", line.strip()):
            rendered.add((m.group(2), m.group(1)))
    destinations = {}
    for slug, kind in sorted(set(terms)):
        if slug and (slug, kind) in rendered:
            destinations[slug] = f"/{kind}/{slug}/"
    labels = {}
    for slug, dest in destinations.items():
        labels[slug] = dest
        # Capitalizing a slug that starts with a digit changes nothing, yielding one entry instead of two.
        labels[slug.capitalize()] = dest
    n_labels = write_map(out / "labels.map", sorted(labels.items()))
    n_terms = len(destinations)

    # WordPress keeps a taxonomy term alive once created and answers an empty one with a 200 page.
    # Hugo builds a term page only where posts exist, so an empty term would become a hard 404.
    # Each redirects to the same-named category where one exists, otherwise to the archive index.
    empty_terms = {}
    for slug, kind in sorted(set(terms)):
        if slug and (slug, kind) not in rendered:
            counterpart = f"/category/{slug}/"
            target = counterpart if (slug, "category") in rendered else "/all/"
            empty_terms[f"/{kind}/{slug}/"] = target
    n_empty = write_map(out / "terms.map", sorted(empty_terms.items()))

    # Only the one-segment URLs no Caddyfile rule already covers.
    # An entry duplicating a rule is dead weight that also shadows it.
    covered = re.compile(
        r"^/\d{4}(/\d{2})?(/page/\d+)?/?$"  # date archives and their pagination
        r"|^/feed/?$"  # site feed
        r"|^/author/"  # author archive
        r"|^/\d{4}/\d{2}/\d{2}/"  # anything under a post date
        r"|^/(tag|category)/[^/]+/feed/?$"  # term feeds
        r"|^/p/[^/]+\.html$"  # Blogger static pages
    )
    # The repo's list, not the capture's, which is a frozen snapshot from before the contract grew.
    redirects = (CHECKS / "redirect-urls.txt").read_text(encoding="utf-8").splitlines()
    needed = [u for u in (line.strip() for line in redirects) if u and u.count("/") == 2 and not covered.match(u)]

    # Attachments with a real post_parent resolve directly.
    by_slug = {s: posts[p] for s, p in attachments if s and p in posts}

    # An unattached attachment carries no parent, which is why it appears as a bare one-segment URL.
    # The export cannot resolve it, but the media inventory records which post embeds the file.
    # Recovering the parent that way lands a visitor on the post that showed the image.
    file_to_post = {}
    inv = capture / "inventory" / "media-urls.tsv"
    if inv.exists():
        for line in inv.read_text(encoding="utf-8").splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) >= 4:
                stem = pathlib.PurePosixPath(parts[1].split("?")[0]).stem.lower()
                stem = re.sub(r"-\d{2,4}x\d{2,4}$", "", stem)
                file_to_post.setdefault(stem, re.sub(r"^https?://[^/]+", "", parts[3]))

    resolved, via_parent, via_media, orphan = [], 0, 0, []
    for u in needed:
        slug = u.strip("/")
        if u in WELL_KNOWN:
            resolved.append((u, WELL_KNOWN[u]))
        elif slug in by_slug:
            resolved.append((u, by_slug[slug]))
            via_parent += 1
        elif slug.lower() in file_to_post:
            resolved.append((u, file_to_post[slug.lower()]))
            via_media += 1
        else:
            resolved.append((u, "/"))
            orphan.append(u)
    n_slugs = write_map(out / "slugs.map", sorted(resolved))

    # A wrong export, a renamed key, or a missing inventory all produce a map that is empty or nearly so.
    # An empty map is indistinguishable from a working one until the redirects are live.
    # The floors sit under the known-good counts, so a re-export may move while a collapse may not.
    floors = {
        "p-ids.map": (n_pids, 105),
        "blogger.map": (n_blogger, 55),
        "labels.map": (n_labels, 380),
        "slugs.map": (n_slugs, 100),
    }
    failed = [f"{name}: {count} entries, expected at least {floor}" for name, (count, floor) in floors.items() if count < floor]
    if failed:
        print("map generation collapsed:", file=sys.stderr)
        for line in failed:
            print(f"  {line}", file=sys.stderr)
        return 1

    print(f"p-ids.map   : {n_pids} entries  (/?p=<id> -> permalink)")
    print(f"blogger.map : {n_blogger} entries  ({truncated} posts also mapped under a truncated Blogger slug)")
    print(f"labels.map  : {n_labels} entries  ({n_terms} terms, each with a capitalized variant)")
    print(f"terms.map   : {n_empty} entries  (term archives WordPress serves that Hugo will not build)")
    print(f"slugs.map   : {n_slugs} entries")
    print(f"              {via_parent:3} via WXR post_parent")
    print(f"              {via_media:3} via the media inventory (unattached, file is embedded in a post)")
    print(f"              {len(orphan):3} unresolvable -> /")
    if orphan:
        print("\n  unresolvable:")
        for u in orphan:
            print(f"    {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
