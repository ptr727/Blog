# Deploy

How the site is built, released, and served. The release is a **self-contained bundle** carrying the site, the Caddyfile, and the redirect maps together, so a rollback reverts the redirect rules and the content they refer to as one unit.

## Required tools

| Tool | Used by | Needed for | Install |
| --- | --- | --- | --- |
| `hugo` (extended) | `make-release.sh` | building the site | see below |
| `python3` (3.10+) | `check-url-parity.py`, `build-redirects.py` | the build-time gate, regenerating maps | `apt install python3` |
| `rsync` | `make-release.sh` | installing a release, hard-linking unchanged files | `apt install rsync` |
| `gzip` | `make-release.sh` | precompression | coreutils, already present |
| `brotli` | `make-release.sh` | precompression | `apt install brotli` |
| `curl` | `check-live-urls.sh` | verifying a running server | `apt install curl` |
| `bash` 4.4+ | all scripts | arrays, `mapfile` | already present |
| `docker` | serving | running Caddy | orchestrated elsewhere |

**Hugo must be the `extended` build**, and `hugo version` reports `+extended` when it is. Debian's archive does not carry a useful version, so install from the upstream release or via snap.

**`brotli` is easy to miss and degrades silently.** The Caddyfile serves `precompressed br gzip`, so without the binary every text response falls back to gzip while the site keeps working and nothing errors. `make-release.sh` warns loudly when it is absent, and `REQUIRE_BROTLI=1` turns that into a hard failure. **CI must set it.** Measured on the home page: 18,845 bytes raw, 6,395 gzip, 5,105 brotli.

`checks/build-redirects.py` additionally needs the capture directory holding the source export, which is not in this repo and is passed to it as an argument. It is a provenance script rather than a CI step, and its outputs under `deploy/maps/` are committed.

## Container contract

This repo produces a release tree and the config that serves it. It never names a host path or
an orchestrator variable, because the consumer may name both sides and the producer must name
neither. Five facts are the whole contract:

1. The deploy root is bind-mounted **read-only** at `/srv/blog`. Mount the **parent**, never
   `current`, because a symlink is resolved once at container creation and mounting it pins the
   container to whichever release was live then.
2. The site config is at `/srv/blog/current/Caddyfile`.
3. A stable per-container config directory is mounted at `/config`, holding a bootstrap that
   imports (2). Mount `/data` as well to persist Caddy state across a recreate. The image ships
   `/data/caddy`, so this is persistence rather than a startup requirement.
4. Caddy binds `:8080`, plain HTTP, with `admin off` and `auto_https off`. TLS and the public
   listener belong to the fronting proxy.
5. The release tree is world-readable and world-traversable, so any uid can serve it.

## Building a release

```sh
deploy/make-release.sh
checks/check-live-urls.sh "$HUGO_BASEURL"
```

The deploy root and the base URL are the only host-specific values, and they pair per
environment. Copy [`env.example`](./env.example) to `secrets/<environment>.env` and set both.
`secrets/` is gitignored as a whole directory, so a value naming one machine cannot reach a
public repo by being added to a file nobody remembered to ignore. CI passes them explicitly
instead, which keeps a pipeline run self-describing:

```sh
HUGO_BASEURL=<base-url> deploy/make-release.sh <deploy-root> "$(git rev-parse --short HEAD)"
```

**One file per environment, selected by `ENV_FILE`.** `secrets/.env` is the default and is read
when `ENV_FILE` is unset, so a single-environment host needs nothing else:

```sh
deploy/make-release.sh                                  # secrets/.env
ENV_FILE=secrets/staging.env deploy/make-release.sh     # the staging site on the same host
```

Selecting the file is the only way to switch environments. The file is sourced with `set -a`,
which exports every assignment in it and **overwrites** a variable the caller exported first, so
`DEPLOY_ROOT=... deploy/make-release.sh` does not do what it looks like. The first argument
still wins, because it is read after the file. A named file that does not exist is a hard
failure rather than a fall-through to the ambient environment, since on a host running two sites
the ambient value is the other site's root.

**Always set `HUGO_BASEURL` for anything that is not production.** The base URL is baked into
the canonical tag, the feed links, and every absolute permalink, so a mirror built without it
serves pages that all point back at production. Nothing downstream catches this, because the
pages render at the right paths and the parity gate passes. The effective value is printed on
every build for that reason.

### Environment variables

| Variable | Effect |
| --- | --- |
| `ENV_FILE` | Which environment file to source. Defaults to `secrets/.env`. |
| `DEPLOY_ROOT` | Fallback deploy root. The first argument wins. |
| `HUGO_BASEURL` | Overrides the site base URL. Hugo maps `HUGO_<KEY>` onto config natively. |
| `REQUIRE_BROTLI=1` | Fails rather than shipping gzip-only. CI sets this. |
| `NO_LINK_DEST=1` | Full copy instead of hard-linking from the previous release. |

`checks/check-live-urls.sh` reads two more, and neither reaches `make-release.sh`:

| Variable | Effect |
| --- | --- |
| `PANGOLIN_ACCESS_TOKEN_ID` | Resource access token id, sent as the `P-Access-Token-Id` header. |
| `PANGOLIN_ACCESS_TOKEN` | The token itself, sent as `P-Access-Token`. |

Set both or neither; half a pair is rejected as the typo it is. They go to curl through a
mode-`600` config file rather than as `-H` arguments, which keeps the credential out of the
`ps` output of 1,245 requests, and is also the only form that survives the `export -f` the
parallel checks run under. The token is sent to the base URL's own origin and to nothing else,
so a redirect that one day points off-site cannot carry it away.

## Layout

```text
<deploy-root>/
  current -> releases/<version>        relative symlink, swapped atomically
  releases/<version>/
    site/        the built site, precompressed
    Caddyfile    the redirect rules
    maps/        p-ids, slugs, blogger, labels, terms
```

## How the redirects are expressed

Everything the site does not render is the web server's job, and the workload constrains which server can serve it. Two requirements are load-bearing, so a replacement has to meet both:

- **The query string must be matchable.** 110 `?p=<id>` shortlinks redirect on the query alone. A server that matches on the path only would resolve `/?p=123` as `/`, redirect the homepage, and carry the query through to it.
- **There must be a lookup primitive.** 279 of the 917 resolve through map files rather than patterns, since no rule can derive their destination, and the five maps carry 661 entries between them. A linear scan of that many rules per request is the wrong shape.

The Caddyfile carries **13 `redir` directives**, reading **5 map files** through **3 `map` blocks**. Ten directives match on a pattern and three resolve through a map lookup, which is used wherever no pattern can derive the destination from the input.

Directives and URL classes are not one to one, in both directions. `@mapped` is a single directive serving three classes, because their key spaces are disjoint and merging them keeps one lookup on the hot path. `@uploads` is one directive covering a URL set that is gated separately.

Each row below is a **URL class**, named by the matcher that serves it, so the table can be checked against [`Caddyfile`](./Caddyfile) by grep rather than by trust.

| Matcher | Class size | Shape |
| --- | --- | --- |
| `@post_child` | 216 | `/YYYY/MM/DD/post/<child>/` -> the post, attachment pages |
| `@term_feed` | 192 | `/tag/<t>/feed/` and `/category/<c>/feed/` -> the term archive |
| `@post_id` | 110 | `/?p=<id>` -> the permalink, via `p-ids.map` |
| `@post_child_feed` | 107 | `/YYYY/MM/DD/post/<child>/feed/` -> the post, ordered **before** `@post_child` |
| `@mapped` via `slugs.map` | 107 | bare `/<attachment-slug>/` -> best destination |
| `@date_archive` | 83 | `/YYYY/`, `/YYYY/MM/`, and their pagination -> `/all/` |
| `@mapped` via `blogger.map` | 59 | `/YYYY/MM/slug.html` -> the current post |
| `@blogger_archive` | 21 | `/YYYY_MM_01_archive.html` -> `/all/`, any date, including ones never covered |
| `@author` | 12 | `/author/<name>/`, its pagination and feed -> `/` |
| `@site_feed` | 3 | `/feed/`, `/comments/feed/`, `/about/feed/` -> `/feed.xml` |
| `@mapped` via `terms.map` | 3 | the three empty term archives |
| `@blogger_feed` | 2 | `/feeds/posts/default` -> `/feed.xml`, Blogger's Atom feed |
| `@blogger_page` | 2 | `/p/<slug>.html` -> `/<slug>/`, Blogger's static-page shape |

**Those thirteen classes sum to 917**, which is the line count of [`checks/redirect-urls.txt`](../checks/redirect-urls.txt) and the whole redirect contract.

`@uploads` is deliberately absent from that table and from the 917. It rewrites `/wp-content/uploads/(.*)` to `/media/$1`, preserving all 778 legacy image URLs, which are gated by `golden-media-legacy.txt` on their own. Counting them here would double-count a set that has its own list.

`@label` is the fourteenth class and is deliberately **not** in the contract. `/search/label/<Label>` was never a redirect: the old platform answered it with a generic search page that returns 200 for a label that never existed, so it is a soft 404 that looks alive. `labels.map` sends each label to its term archive and defaults anything unmatched to `/all/`, which is a choice rather than a preservation.

Two orderings are load-bearing. `@post_child_feed` precedes `@post_child` because both match the same shape and the broader one would claim both. No golden URL is five segments under a date, so `@post_child` cannot swallow a page that must render, and `@uploads` rewrites under a prefix no rendered page occupies.

`blogger.map` carries 59 entries rather than 48 because Blogger truncated an auto-generated slug at 40 characters on a whole-word boundary, so a long-titled post was served at the truncated URL and that is the form in search indexes. `slugs.map` is generated by `checks/build-redirects.py`, which recovers each attachment's parent from the media inventory, since all 107 have `post_parent = 0` in the export. 85 resolve to a real post and the remaining 22 were never used anywhere, so `/` is correct for them.

## What the script asserts

Each of these fails silently when it fails, which is why it is checked rather than assumed:

- **The URL contract**, via `check-url-parity.py`, before anything is installed.
- **World-readability of the finished release.** `--chmod` and `--no-g` apply only to files
  rsync newly transfers. A file supplied by `--link-dest` is a hard link to the previous
  release's inode and keeps that inode's mode and ownership, so a badly moded file rides the
  link chain into every later release and no change to the rsync options reaches it. Rebuild
  once with `NO_LINK_DEST=1` to mint fresh inodes and break the chain.
- **That hard-linking actually shared something.** Without sharing, every release costs a full copy, and on a compressing filesystem `du` under-reports enough to look correct. Expect roughly 1,050 of 2,500 files to link, because the static tree shares while generated HTML legitimately does not, so a release costs about 9 MB against 572 MB.
- **That the prune kept what it claims.** A prune that silently keeps 40 releases is a
  disk-full outage later.

`umask 022` is pinned because the release and staging directories come from `mkdir` rather than rsync and would otherwise inherit the caller's umask. Under `umask 077` they land 700, and Caddy cannot then traverse into the release at all.
