# Deploy

How the site is built, released, and served. The release is a **self-contained bundle** carrying the site, the Caddyfile, and the redirect maps together, so a rollback reverts the redirect rules and the content they refer to as one unit.

## Required tools

| Tool | Used by | Needed for | Install |
| --- | --- | --- | --- |
| `hugo` (extended) | `make-release.sh` | building the site | see below |
| `python3` (3.10+) | `check-url-parity.py`, `capture/build-redirects.py` | the build-time gate, regenerating maps | `apt install python3` |
| PyYAML | `capture/clean-content.py` | reading front matter during a conversion | `apt install python3-yaml` |
| `rsync` | `make-release.sh` | installing a release, hard-linking unchanged files | `apt install rsync` |
| `gzip` | `make-release.sh` | precompression | coreutils, already present |
| `brotli` | `make-release.sh` | precompression | `apt install brotli` |
| `curl` | `check-live-urls.sh` | verifying a running server | `apt install curl` |
| `bash` 4.4+ | all scripts | arrays, `mapfile` | already present |
| `docker` | serving | running Caddy | orchestrated elsewhere |

**These scripts run on Linux, which is a dependency ceiling rather than an omission.** They use
`mv -Tf`, `find -printf`, `mapfile`, and `sed -i` without an argument, all of which are GNU or
bash 4.4 constructs absent from a stock macOS. Every consumer is Linux already: CI builds there,
the containers serve there, and the deploy account receives there. Editing is unaffected, and a
macOS or Windows contributor runs them through a container or a remote Linux host.

**Hugo must be the `extended` build**, and `hugo version` reports `+extended` when it is. Debian's archive does not carry a useful version, so install from the upstream release or via snap.

**`brotli` is easy to miss and degrades silently.** The Caddyfile serves `precompressed br gzip`, so without the binary every text response falls back to gzip while the site keeps working and nothing errors. `make-release.sh` warns loudly when it is absent, and `REQUIRE_BROTLI=1` turns that into a hard failure. **CI must set it.** Measured on the home page: 18,845 bytes raw, 6,395 gzip, 5,105 brotli.

[`capture/build-redirects.py`](../capture/build-redirects.py) additionally needs the capture directory holding the source export, which is not in this repo. It runs by hand rather than in CI, and its outputs under `deploy/maps/` are committed.

## Container contract

This repo produces a release tree and the config that serves it. It never names a host path or
an orchestrator variable, because the consumer may name both sides and the producer must name
neither. Seven facts are the whole contract:

1. The deploy root is bind-mounted **read-only** at `/srv/blog`. Mount the **parent**, never
   `current`, because a symlink is resolved once at container creation and mounting it pins the
   container to whichever release was live then.
2. The site config is at `/srv/blog/current/Caddyfile`.
3. A stable per-container config directory is mounted **read-only** at `/config`, holding a
   bootstrap that imports (2). Mount `/data` writable as well, and set `XDG_CONFIG_HOME=/data`.
4. Caddy binds `:8080`, plain HTTP, with `admin off` and `auto_https off`. TLS and the public
   listener belong to the fronting proxy.
5. Caddy runs with **`--watch`**. This is not optional. See
   [Reloading without a restart](#reloading-without-a-restart).
6. The release tree is world-readable and world-traversable, so any uid can serve it.
7. The container sets `SITE_ENV` and `SITE_ROBOTS`, which the bundle stamps on every response
   as `X-Blog-Env` and `X-Robots-Tag`, and `TRUSTED_PROXIES`. See
   [Identifying the environment](#identifying-the-environment) and
   [Trusting the proxy](#trusting-the-proxy).

## Building a release

```sh
set -a; . ~/.secrets/Blog.local.production.env; set +a
deploy/make-release.sh
checks/check-live-urls.sh "$SITE_BASE_URL"
```

The deploy root and the base URL are the only host-specific values, and they pair per
environment. Copy [`example.env`](../.secrets/example.env) to `~/.secrets/Blog.local.production.env`, which is the
file read when `ENV_FILE` is unset, and add `~/.secrets/Blog.<server>.<environment>.env` for each further
environment. A single environment therefore needs `~/.secrets/Blog.local.production.env` and nothing
else, since a differently named file is read only when `ENV_FILE` names it. The real files
live on the host, in `~/.secrets/`, never in this checkout. CI passes them explicitly instead, which
keeps a pipeline run self-describing:

```sh
SITE_BASE_URL=<base-url> deploy/make-release.sh <deploy-root> "$(git rev-parse --short HEAD)"
```

**That command-prefix form is CI-only.** A local run whose default environment file exists sources it after the command-prefix assignment and overwrites it, since `set -a` overwrites a value the caller exported first. Locally, select the environment through `ENV_FILE` instead, per the table below.

**One file per environment, named `~/.secrets/Blog.<server>.<environment>.env`, selected by `ENV_FILE`.**
Both halves are spelled out, so a name says which machine it describes as well as which
environment on it, and the four in the fleet read as one set. `~/.secrets/Blog.local.production.env` is
the default and is read when `ENV_FILE` is unset, so a single-environment host needs nothing
else:

```sh
deploy/make-release.sh                                       # ~/.secrets/Blog.local.production.env
ENV_FILE=~/.secrets/Blog.local.staging.env deploy/make-release.sh    # the staging site on the same host
```

A file whose `DEPLOY_SSH_HOST` is set describes a root on another machine, so this script refuses
to create that path here and asks for a local one to assemble a bundle into:

```sh
ENV_FILE=~/.secrets/Blog.vps.staging.env deploy/make-release.sh /path/to/bundle
```

Selecting the file is the only way to switch environments. The file is sourced with `set -a`,
which exports every assignment in it and **overwrites** a variable the caller exported first, so
`DEPLOY_ROOT=... deploy/make-release.sh` does not do what it looks like. The first argument
still wins, because it is read after the file. A named file that does not exist is a hard
failure rather than a fall-through to the ambient environment, since on a host running two sites
the ambient value is the other site's root.

**Always set `SITE_BASE_URL` for anything that is not production.** The base URL is baked into
the canonical tag, the feed links, and every absolute permalink, so a mirror built without it
serves pages that all point back at production. Nothing downstream catches this, because the
pages render at the right paths and the parity gate passes. `make-release.sh` bridges it to
Hugo's own `HUGO_BASEURL` internally, and the effective value is printed on every build for
that reason.

### Environment variables

| Variable | Effect |
| --- | --- |
| `ENV_FILE` | Which environment file to source. Defaults to `~/.secrets/Blog.local.production.env`. |
| `DEPLOY_ROOT` | Fallback deploy root. The first argument wins. |
| `SITE_BASE_URL` | Overrides the site base URL. Bridged internally to `HUGO_BASEURL`, the name Hugo maps `HUGO_<KEY>` onto config natively. |
| `REQUIRE_BROTLI=1` | Fails rather than shipping gzip-only. CI sets this. |
| `NO_LINK_DEST=1` | Full copy instead of hard-linking from the previous release. |

`checks/check-live-urls.sh` reads five more, and none of them reaches `make-release.sh`. Two
open the auth gate:

| Variable | Effect |
| --- | --- |
| `SITE_AUTH_TOKEN_ID` | Resource access token id, sent as the `P-Access-Token-Id` header. |
| `SITE_AUTH_TOKEN` | The token itself, sent as `P-Access-Token`. |

Set both or neither; half a pair is rejected as the typo it is. They go to curl through a
mode-`600` config file rather than as `-H` arguments, which keeps the credential out of the
`ps` output of one request per URL in the contract, and is also the only form that survives the `export -f` the
parallel checks run under. The token is sent to the base URL's own origin and to nothing else,
so a redirect that one day points off-site cannot carry it away.

Three more assert that the thing answering is the thing that was just deployed, all checked in
the preflight before a single URL is requested:

| Variable | Effect |
| --- | --- |
| `EXPECT_SITE_ENV` | Asserts the environment that answered, read from `X-Blog-Env`. |
| `EXPECT_RELEASE` | Asserts the release whose rules answered, read from `X-Blog-Release`. |
| `RELOAD_TIMEOUT` | Seconds to wait for that release to become live. Default 30. |

## Reloading without a restart

The container runs `caddy run --watch`, so a release goes live with **no restart**. The watcher
re-adapts the config on a timer and reloads it in process, and re-adapting re-executes every
`import`, which is how a new release's `Caddyfile` and `maps/*.map` are picked up through a
`/config/Caddyfile` that never itself changes.

**`--watch` does not need the admin API.** `admin off` makes `caddy reload` impossible, which
looks like it should rule out reloading entirely, and does not: `caddy reload` POSTs to the admin
endpoint while the watcher reloads in process. The log prints `admin endpoint disabled` and
`watching config file for changes` together.

**`XDG_CONFIG_HOME=/data` is required alongside it.** The watcher autosaves the adapted config on
every reload, to `$XDG_CONFIG_HOME/caddy`, which the image defaults to `/config`. A bind mount
over `/config` shadows the world-writable directory the image pre-creates there, so the autosave
has to `mkdir` and the outcome depends on the mount:

| `/config` mount | Result |
| --- | --- |
| read-only, no `XDG_CONFIG_HOME` | an ERROR line **per reload**, one per deploy, reload still succeeds |
| read-only, `XDG_CONFIG_HOME=/data` | clean |
| writable, no `XDG_CONFIG_HOME` | silent, and Caddy writes `caddy/autosave.json` into the config directory |

Mount `/config` read-only *and* set `XDG_CONFIG_HOME=/data`. Doing one without the other trades a
silent stray file for a per-deploy error, in the place a real error most needs to stand out.

**Without `--watch` the failure is silent.** Caddy expands `import` at config-parse time and does
not watch the imported files, so the content symlink moves while the rules stay as they were when
Caddy last loaded. The URL check then passes against a config that was never deployed. That is why
the release stamps its own version into the config it ships with, as `X-Blog-Release`, and why
`check-live-urls.sh` compares it to `EXPECT_RELEASE` before checking a single URL.

It **waits** for the match rather than sampling once. The reload is asynchronous, so a check
starting straight after a deploy races it and reads the previous release's config. `RELOAD_TIMEOUT`
bounds the wait, and a container that is not watching never converges, which is what turns a silent
staleness into a named failure.

**Content and rules do not switch together.** `file_server` resolves `current` per request, so new
content is live instantly while the rules follow on the next poll, about a quarter of a second
later. For that window the new content is served under the previous release's rules. Harmless while
every rule is a redirect, since a stale redirect lands on a page that exists in both releases. It
stops being harmless if a rule ever *gates* content rather than redirecting it, and at that point
the flip has to become a restart again.

## Identifying the environment

Every environment runs the **same bundle on the same port** in its own container, so nothing in a
response says which one answered. A proxy rule aimed at the wrong container connects happily and
serves the wrong environment under the right hostname, returning a healthy `200`. That is a
failure a reader reports before a monitor notices.

The bundle stamps two headers for that, taking both values from the container so the artifact
stays the same everywhere and still rolls back as one unit:

| Container variable | Header | Values |
| --- | --- | --- |
| `SITE_ENV` | `X-Blog-Env` | `production`, `staging`, and the local mirrors |
| `SITE_ROBOTS` | `X-Robots-Tag` | `index, follow` or `noindex, nofollow` |

Both are emitted at site level, outside the `route` block, which is what puts them on the error
path as well. Verified on all three response classes: `200` from `file_server`, `301` from a
`redir`, and `404` through `handle_errors`.

**Both carry a default, because an unset `{$VAR}` is silent.** It expands to an empty header
rather than an error, and `caddy validate` still reports a valid configuration, so a missing
value would otherwise reach production unnoticed. `SITE_ENV` defaults to `unset`, which
`EXPECT_SITE_ENV` then fails on.

**`SITE_ROBOTS` defaults to `index, follow`, which is deliberate and is not the safer-looking
choice.** The two failure directions are not symmetric:

- A **staging** container missing the value is still behind its auth gate, so nothing reaches it
  to index. The header is the second line of defence there, not the first.
- A **production** container that picked up `noindex` would deindex the site silently, and this
  site's entire migration exists to preserve sixteen years of search ranking. Recovery is
  measured in weeks of recrawling.

So the default is the value that is harmless on production, and `noindex` is reachable only by
asking for it explicitly.

`checks/check-live-urls.sh` asserts this when `EXPECT_SITE_ENV` is set, before it checks the
contract, since checking the contract against the wrong environment proves nothing.

## Trusting the proxy

A proxy fronts Caddy in every environment, so the peer address is always the proxy and the real
client arrives in `X-Forwarded-For`. `trusted_proxies` is what makes Caddy believe it. Without it,
`client_ip` and `remote_ip` are both the proxy and the forwarded header has no effect at all.

**The CIDRs come from the container, not the bundle.** The same artifact runs on hosts whose docker
subnets differ, so any literal in the bundle is wrong on one of them.

**Trusting a range means believing `X-Forwarded-For` from anything inside it**, so the range is a
security boundary, and it should be no wider than what can actually reach the port. Three
behaviours, all verified:

| `TRUSTED_PROXIES` | Result |
| --- | --- |
| unset | the bundle's default applies, all of RFC1918 |
| set but empty | the default is skipped and nothing is trusted |
| an explicit list | exactly those ranges |

The default exists so a host that forgets the variable keeps working. It is not a safe value
everywhere: **it is only correct where a proxy is the only thing that can reach Caddy.** Where the
port is reachable directly, RFC1918 makes every device on the network a trusted proxy, and anything
there can forge the client address in the access log. `TRUSTED_PROXIES=` (present, blank) is the
right answer there, because a client that is not a proxy has no forwarded header worth honouring.

Binding the port to `127.0.0.1` does **not** make direct access impossible. `docker-proxy` SNATs
host-originated traffic to the bridge gateway, which is itself inside RFC1918 and therefore inside
the default. Narrowing to the container subnet does not fix it either, since the gateway sits inside
that too and has to be excluded deliberately.

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

Every class below is a legacy shape, closed by the migration, so no count here moves when content is added. New content is served by the render half of the contract, never by these.

| Matcher | Class size | Shape |
| --- | --- | --- |
| `@post_child` | 216 | `/YYYY/MM/DD/post/<child>/` -> the post, attachment pages |
| `@term_feed` | 192 | `/tag/<t>/feed/` and `/category/<c>/feed/` -> the term archive |
| `@post_id` | 110 | `/?p=<id>` -> the permalink, via `p-ids.map` |
| `@post_child_feed` | 107 | `/YYYY/MM/DD/post/<child>/feed/` -> the post, ordered **before** `@post_child` |
| `@mapped` via `slugs.map` | 107 | bare `/<attachment-slug>/` -> best destination |
| `@date_archive` | 83 | `/YYYY/`, `/YYYY/MM/`, and their pagination -> `/all/`. The matcher accepts any date, including dates absent from the list |
| `@mapped` via `blogger.map` | 59 | `/YYYY/MM/slug.html` -> the current post |
| `@blogger_archive` | 21 | `/YYYY_MM_01_archive.html` -> `/all/`, any date, including ones never covered |
| `@author` | 12 | `/author/<name>/`, its pagination and feed -> `/` |
| `@site_feed` | 3 | `/feed/`, `/comments/feed/`, `/about/feed/` -> `/feed.xml` |
| `@mapped` via `terms.map` | 3 | the three empty term archives |
| `@blogger_feed` | 2 | `/feeds/posts/default` -> `/feed.xml`, Blogger's Atom feed |
| `@blogger_page` | 2 | `/p/<slug>.html` -> `/<slug>/`, Blogger's static-page shape |

**Those thirteen classes account for every line in [`checks/redirect-urls.txt`](../checks/redirect-urls.txt), with nothing in the contract outside the table.** Completeness is the property worth holding, and the list's line count is how to check it.

`@uploads` is deliberately absent from that table and from the redirect contract. It rewrites `/wp-content/uploads/(.*)` to `/media/$1`, preserving all 778 legacy image URLs, which are gated by `golden-media-legacy.txt` on their own. Counting them here would double-count a set that has its own list.

`@label` is the fourteenth class and is deliberately **not** in the contract. `/search/label/<Label>` was never a redirect: the old platform answered it with a generic search page that returns 200 for a label that never existed, so it is a soft 404 that looks alive. `labels.map` sends each label to its term archive and defaults anything unmatched to `/all/`, which is a choice rather than a preservation.

Two orderings are load-bearing. `@post_child_feed` precedes `@post_child` because both match the same shape and the broader one would claim both. No golden URL is five segments under a date, so `@post_child` cannot swallow a page that must render, and `@uploads` rewrites under a prefix no rendered page occupies.

`blogger.map` carries more entries than there are Blogger-era posts, because that platform served a long title at a truncated address and both forms answer. The mechanism is in [`capture/README.md`](../capture/README.md), beside the generator that implements it. `slugs.map` is generated by [`capture/build-redirects.py`](../capture/build-redirects.py), which recovers each attachment's parent from the media inventory, since all 107 have `post_parent = 0` in the export. 85 resolve to a real post and the remaining 22 were never used anywhere, so `/` is correct for them.

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
