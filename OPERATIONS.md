# OPERATIONS.md

How this site is built, released, served, and rolled back. [`GOVERNANCE.md`](./GOVERNANCE.md) holds the cross-cutting rules and [`WORKFLOW.md`](./WORKFLOW.md) the CI contract. This file is the operational procedure, and it is the one to read before touching a server.

## Environments

| Environment | Address | Fronted by | Purpose |
| --- | --- | --- | --- |
| Local mirror | a private hostname, set in `secrets/.env` | a reverse proxy on the maintainer's own network | Proves the artifact. The redirect rules, the maps, and the release mechanics. |
| Staging | on the VPS, behind the auth gate | Pangolin | Proves the infrastructure. Routing, TLS, and the deploy path. |
| Production | `blog.insanegenius.com` | Pangolin | The public site. |

The local mirror is not staging. It runs the same bundle against the same web server, so it catches a broken redirect or a bad permission for free, but it exercises none of the routing, authentication, or certificate machinery that only exists on the VPS. Passing locally says the artifact is right. It says nothing about whether the server in front of it is.

## The Release Bundle

A release is self-contained. The site, the web-server config, and the redirect maps travel together:

```text
<deploy-root>/
  current -> releases/<version>        relative symlink, swapped atomically
  releases/<version>/
    site/        the built site, precompressed
    Caddyfile    the redirect rules
    maps/        p-ids, slugs, blogger, labels, terms
```

Shipping the config inside the release is what makes a rollback honest. The rules and the content they refer to move as one, so reverting cannot leave the previous site being served by the current release's redirects.

`current` is a **relative** symlink. That frees the host path, so one bundle works at whatever root each environment mounts, with no rewriting.

## Local Verification Before a Pull Request

**CI cannot prove a redirect.** The validation workflow builds the site and checks the render half of the contract, which is every URL that must return a page. The other 917 URLs are the web server's job, and nothing in a build exercises them. A change to the Caddy config or to a generated map is therefore invisible to CI: the workflow goes green while the redirect it broke stays broken until someone follows a sixteen-year-old link.

So release to the local mirror and run the live check **before** opening a pull request that touches any of these:

| Path | Why it needs a running server |
| --- | --- |
| [`deploy/Caddyfile`](./deploy/Caddyfile) | The redirect rules. Rule order is load-bearing, and a regex that matches too much is silent. |
| [`deploy/maps/`](./deploy/maps/) | The lookup tables. A regenerated map can lose entries and still parse. |
| `content/`, `static/` | A moved or renamed page turns a redirect destination into a 404, which the build gate does not follow. |
| `hugo.yaml`, `layouts/` | Permalink and taxonomy changes move URLs underneath the redirects that point at them. |

```sh
set -a; . secrets/.env; set +a
deploy/make-release.sh
docker restart "$CADDY_CONTAINER"   # required: see below
checks/check-live-urls.sh "$HUGO_BASEURL"
```

**Restart every time, even though only some changes strictly need it.** Caddy expands `import` at config-parse time, both for the site config and for the `map` blocks that read `maps/*.map`, and it does not watch those files. Swapping the `current` symlink therefore changes what a *static file* request resolves to, per request, while the redirect rules and map tables stay exactly as they were when Caddy last loaded. Verified against the running mirror: a new map entry present in the live release on disk returned 404 until the container was restarted, then 301.

So the failure is specific. **When the release changed `deploy/Caddyfile` or anything under `deploy/maps/`**, checking without a restart exercises the **previous** rules, and a broken redirect reports `PASS` while the shipped artifact is broken. A content-only release does not have this problem, because the rules Caddy already holds are still the right ones.

The step is unconditional anyway, for two reasons. Deciding correctly means knowing whether anything reached the config, which is easy to get wrong when a change spans several paths or a map was regenerated as a side effect. And getting it wrong is silent, since the wrong answer is a green check rather than an error. A restart costs a few seconds on a static site, which is cheaper than reasoning about it each time.

Sourcing `secrets/.env` first puts the deploy root and the base URL in the environment, so no literal value is typed. `make-release.sh` then needs no arguments, because its deploy root falls back to `$DEPLOY_ROOT` and its version falls back to a timestamp. It still accepts both, and [Deploying](#deploying) below passes them explicitly, which is what CI does so a pipeline run names the commit it built rather than the clock. Either form works locally, and the argument wins over the environment.

It refuses to install a release that fails the build gate. `check-live-urls.sh` does take a base URL, which is where the sourced `$HUGO_BASEURL` goes. It follows all 1,245 URLs against the running mirror, checking each redirect's destination rather than trusting its status code.

Expect `PASS - 1245 URLs honored`. Anything less is a finding, and the output names each URL that failed and what it answered.

A documentation-only or workflow-only change does not need this. A change to the four paths above does, because for those CI's green is not evidence.

## Deploying

```sh
HUGO_BASEURL=<base-url> deploy/make-release.sh <deploy-root> "$(git rev-parse --short HEAD)"
checks/check-live-urls.sh <base-url>
```

The deploy root and the base URL are the only host-specific values. A local run reads them from an untracked `secrets/.env`, copied from [`deploy/env.example`](./deploy/env.example), and CI passes both explicitly. The whole `secrets/` directory is gitignored, so no address, path, or container name belonging to one machine reaches the published history.

**Always set `HUGO_BASEURL` for anything that is not production.** The base URL is baked into the canonical tag, the feed links, and every absolute permalink, so a mirror built without it serves pages that all point back at the production address. Nothing downstream catches this, because the pages render at the right paths and the build gate passes. The effective value is printed on every build for that reason.

| Variable | Effect |
| --- | --- |
| `DEPLOY_ROOT` | Fallback deploy root. The first argument wins. |
| `HUGO_BASEURL` | Overrides the site base URL. |
| `REQUIRE_BROTLI=1` | Fails rather than shipping gzip-only. CI sets this. |
| `NO_LINK_DEST=1` | Full copy instead of hard-linking from the previous release. |

The script builds, verifies the URL contract, precompresses, installs, swaps, and prunes. It refuses to continue at each step rather than shipping a release that is wrong in a way nobody would notice.

## Rollback

Point `current` at the previous release. The swap is a single rename, so a request sees either the old release or the new one and never a half-written state:

```sh
ln -sfn "releases/<previous>" "<deploy-root>/.current.tmp"
mv -Tf "<deploy-root>/.current.tmp" "<deploy-root>/current"
docker restart "$CADDY_CONTAINER"
```

The content reverts on the rename alone, because the container mounts the parent directory and the kernel resolves `current` per request. **The rules do not.** Caddy holds the Caddyfile and the maps as parsed config, so without the restart a rollback serves the previous release's content under the current release's redirects, which is precisely the mismatch that shipping the config inside the bundle exists to prevent.

The restart is therefore part of the rollback, not an optional follow-up. It costs a few seconds of downtime on a static site, which is the cheaper half of the trade.

Verify with `checks/check-live-urls.sh` against the environment before considering the rollback finished.

## Retention

Ten releases are kept. Unchanged files hard-link to the previous release, so the static tree is stored once rather than ten times, and a release costs roughly the size of the generated output.

The script asserts both halves of that rather than assuming them. It fails when the prune leaves more releases than the limit, and when hard-linking produces no shared files at all. Both have failed silently before, and on a compressing filesystem the disk usage looks plausible either way.

## Serving

Caddy serves the bundle and binds an internal port only. TLS and the public listener belong to the proxy in front of it, so `auto_https off` and `admin off` are deliberate.

The container mounts the deploy root **read-only**, and mounts the **parent** rather than `current`. Docker resolves a symlink at container-creation time, so mounting the symlink pins the container to whichever release was live at startup and every later deploy stays invisible until the container is recreated.

Routing differs by environment and the bundle does not. Traefik on the home host has the Docker provider enabled, so container labels route. Pangolin's Traefik on the VPS does not, so routing there is created in the Pangolin UI and labels are silently ignored.

### The bootstrap, and why it is not in the release

The container reads three host paths, and only one of them a release ever writes:

| Host path | Mounted at | Written by |
| --- | --- | --- |
| `$DEPLOY_ROOT` | `/srv/blog`, read-only | every release |
| `$CADDY_APPDATA/config` | `/config` | placed once, by hand |
| `$CADDY_APPDATA/data` | `/data` | Caddy itself, persisting state across a recreate |

[`deploy/bootstrap.Caddyfile`](./deploy/bootstrap.Caddyfile) goes in the `config` directory and is the **only** Caddy file outside the release bundle. It carries a single `import` and no rules of its own, deliberately: everything describing the site ships inside the release, so a rollback reverts the rules and the content together. Rules held here instead would leave a rolled-back site being served by the current release's redirects.

Because it sits outside the bundle, no release updates it. Install or refresh it explicitly:

```sh
set -a; . secrets/.env; set +a
install -m 644 deploy/bootstrap.Caddyfile "$CADDY_APPDATA/config/Caddyfile"
docker restart "$CADDY_CONTAINER"
```

A restart is needed whenever **any** Caddy config changes, not only this file. That includes `deploy/Caddyfile` and anything under `deploy/maps/`, because both are expanded at config-parse time and Caddy does not watch them. Only static file requests follow the `current` symlink per request. See "Local Verification Before a Pull Request" above, where skipping the restart is the difference between a real check and a false pass.

`CADDY_APPDATA` is recorded in `secrets/.env` for exactly this reason. No script reads it, so a rebuild would otherwise depend on someone remembering where the bootstrap goes.

## Redirects

The site answers 917 addresses it does not render, satisfied by 13 `redir` directives reading 5 map files, all inside the bundle. [`deploy/README.md`](./deploy/README.md) carries the per-class breakdown and the counts. This section covers the operational shape only, so the two do not restate each other.

Ordering is load-bearing, so every redirect lives in a single `route` block. Outside one, Caddy sorts directives by its own precedence rather than by file order, and the broad attachment rule claims the per-post comment feeds that the narrower rule must match first.

| Class | Mechanism |
| --- | --- |
| Attachment pages and per-post comment feeds | Two rules, the longer pattern first |
| Term feeds, date archives, author archives | One rule each, to the term, the archive index, or the home page |
| Legacy media paths | One rule, mapping the old upload prefix onto the current media tree |
| Blogger permalinks, pages, feed, and monthly archives | Rules plus `blogger.map` |
| WordPress shortlinks | `p-ids.map`, keyed on the query string |
| Bare attachment slugs | `slugs.map` |
| Blogger label archives | `labels.map`, defaulting to the archive index |
| Term archives the generator does not build | `terms.map` |

The maps are generated by `checks/build-redirects.py` from the source export, which lives outside this repository. It is a provenance script rather than a CI step, and its outputs are committed. It selects the export by content and refuses to run unless exactly one contains published posts, because the capture holds a full export and a media-only one, and reading the wrong one yields empty maps that are indistinguishable from working ones until the redirects are live.

## Server Hardening

The deploy account exists to receive a release and nothing else.

- The account is unprivileged and owns only the deploy root.
- Its key is restricted in `authorized_keys` with `restrict` and a forced command, so it cannot open a shell, allocate a terminal, or forward a port.
- Each environment has its own key, so a staging deploy cannot reach production.
- Unattended upgrades run with automatic reboot, which is safe because the site is static and the swap survives a restart.

## Backup and Restore

**The deploy root needs no backup.** The site is reproducible from this repository by running the deploy again, so the only thing worth protecting on the server is its configuration: the container definition, the proxy configuration, the deploy account and its restricted key, and the upgrade schedule.

A bare-metal restore is therefore rebuilding the host, restoring that configuration, and running a deploy. Treat any procedure that backs up the deploy root as protecting a copy of something git already holds.
