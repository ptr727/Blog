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
environment. Copy [`env.example`](./env.example) to `secrets/.env` and set both. `secrets/` is
gitignored as a whole directory, so a value naming one machine cannot reach a public repo by
being added to a file nobody remembered to ignore. CI passes them explicitly instead, which
keeps a pipeline run self-describing:

```sh
HUGO_BASEURL=<base-url> deploy/make-release.sh <deploy-root> "$(git rev-parse --short HEAD)"
```

**Always set `HUGO_BASEURL` for anything that is not production.** The base URL is baked into
the canonical tag, the feed links, and every absolute permalink, so a mirror built without it
serves pages that all point back at production. Nothing downstream catches this, because the
pages render at the right paths and the parity gate passes. The effective value is printed on
every build for that reason.

### Environment variables

| Variable | Effect |
| --- | --- |
| `DEPLOY_ROOT` | Fallback deploy root. The first argument wins. |
| `HUGO_BASEURL` | Overrides the site base URL. Hugo maps `HUGO_<KEY>` onto config natively. |
| `REQUIRE_BROTLI=1` | Fails rather than shipping gzip-only. CI sets this. |
| `NO_LINK_DEST=1` | Full copy instead of hard-linking from the previous release. |

## Layout

```text
<deploy-root>/
  current -> releases/<version>        relative symlink, swapped atomically
  releases/<version>/
    site/        the built site, precompressed
    Caddyfile    the redirect rules
    maps/        p-ids, slugs, blogger, labels, terms
```

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
