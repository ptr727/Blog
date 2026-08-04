# OPERATIONS.md

How this site is built, released, served, and rolled back. [`GOVERNANCE.md`](./GOVERNANCE.md) holds the cross-cutting rules and [`WORKFLOW.md`](./WORKFLOW.md) the CI contract. This file is the operational procedure, and it is the one to read before touching a server.

## Environments

Four environments, in two pairs. Each pair is one publish site and one staging site, and the local pair exists to rehearse the remote one.

| Environment | Address | Fronted by | Purpose |
| --- | --- | --- | --- |
| Local publish mirror | a private hostname, set in `secrets/.env` | Traefik, on the maintainer's own network | Proves the artifact. The redirect rules, the maps, and the release mechanics. |
| Local staging mirror | a second private hostname, set in `secrets/staging.env` | Traefik | Proves that two environments on one host stay independent, before that matters on a server. |
| Staging | `blog.vps.insanegenius.net`, behind the auth gate | Pangolin | Proves the infrastructure. Routing, TLS, and the deploy path. |
| Production | `blog.insanegenius.com` | Pangolin | The public site. |

The local mirrors are not staging. They run the same bundle against the same web server, so they catch a broken redirect or a bad permission for free, but they exercise none of the routing, authentication, or certificate machinery that only exists on the VPS. Passing locally says the artifact is right. It says nothing about whether the server in front of it is.

**The two words are `production` and `staging`, spelled out, in every position.** No `prod`, no `stage`. The same two name the container, the deploy root, the environment file, the `X-Blog-Env` value, and the GitHub Environment. This is not tidiness: the environment name is a value that gets **compared**, by `EXPECT_SITE_ENV` and by the deploy, so a spelling that differs in one position fails a deploy for a reason that reads like an outage. The local mirrors prefix the same words, `mirror-production` and `mirror-staging`, so a header names exactly one of the four environments in the fleet.

Each environment is one file under `secrets/`, selected with `ENV_FILE`, holding the deploy root, the base URL, and the container name. Selecting the file is how an environment is chosen: the file is sourced with `set -a`, so it overwrites a `DEPLOY_ROOT` the caller exported and setting that variable by hand does not switch anything. A named file that does not exist is a hard failure rather than a fall-through, because on a host serving two sites the ambient value is the other site's root.

**The staging FQDN sits under the VPS wildcard deliberately.** `blog.vps.insanegenius.net` needs no new certificate and no new DNS record, and it keeps the staging name off the production domain.

**Staging keeps its auth gate on.** It serves a byte-identical copy of the public site, so exposing it publicly would hand every crawler a duplicate of a site whose entire migration risk is URL preservation. `checks/check-live-urls.sh` gets through with a Pangolin resource access token instead. See [Checking a Site Behind the Auth Gate](#checking-a-site-behind-the-auth-gate).

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

## The URL Contract

This site has served the same domain across earlier platforms, so its whole operational risk is silent URL loss. Everything below exists to make that risk visible.

**The contract is ground truth.** [`checks/golden-urls.txt`](./checks/golden-urls.txt) and [`checks/redirect-urls.txt`](./checks/redirect-urls.txt) record URLs verified with a live request, not predicted from the content tree. The lists are **append-only**: nothing legitimately removes a URL the site has served, so a change that would drop one is a change to reject rather than a list to shorten. A list-driven check also carries a length floor, or a truncated list passes while checking almost nothing.

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
checks/check-live-urls.sh "$HUGO_BASEURL"
```

Against the staging mirror, name its file in both places, since the sourced values and the ones `make-release.sh` reads must describe the same environment:

```sh
set -a; . secrets/staging.env; set +a
ENV_FILE=secrets/staging.env deploy/make-release.sh
checks/check-live-urls.sh "$HUGO_BASEURL"
```

**There is no restart step, and that depends on one flag.** The container runs `caddy run --watch`, which re-adapts the config on a timer and reloads it in process. Re-adapting re-executes every `import`, so a new release's `Caddyfile` and `maps/*.map` are picked up through the unchanged `/config/Caddyfile` that the watcher actually names. Measured on this host: content is live the instant the symlink moves, and the rules follow within about a quarter of a second.

**The watcher dies silently after one failed config load.** Verified: a flip to a valid release reloads, a flip to a missing one logs the failure and retains the last good config, and a flip back to a valid release **never reloads again**. Nothing in the log says it has given up. Every later deploy then lands content without its rules, which is the failure this section's release stamp exists to catch, and a restart is the only fix. Anything that breaks `current` even briefly, including a test, ends that container's ability to pick up releases.

**`--watch` needs no admin API**, which is the part worth knowing, because `admin off` makes `caddy reload` impossible and that looks like it should rule out reloading altogether. It does not. `caddy reload` POSTs to the admin endpoint; the watcher reloads in process and never uses it. The log prints `admin endpoint disabled` and `watching config file for changes` together.

**Without that flag the failure is silent and specific.** Caddy expands `import` at config-parse time and does not watch the imported files, so swapping `current` changes what a *static file* request resolves to, per request, while the redirect rules and map tables stay as they were when Caddy last loaded. Verified both ways against a two-release fixture whose `Caddyfile` was byte-identical and whose map differed: with `--watch`, a flip moved a redirect from 301 to 404 and its replacement from 404 to 301. Without it, neither moved.

That is why the check verifies the config rather than trusting it. **When the release changed `deploy/Caddyfile` or anything under `deploy/maps/`**, a check run against stale rules exercises the **previous** config, and a broken redirect reports `PASS` while the shipped artifact is broken. The wrong answer is a green check rather than an error, which is the worst shape a failure can take here.

So the bundle stamps its own version as `X-Blog-Release`, and `check-live-urls.sh` compares it against `EXPECT_RELEASE` before checking a single URL. It **waits** for a match rather than sampling once, because the reload is asynchronous and a check that starts immediately after a deploy will otherwise race it. The timeout is what still catches a container that is not watching at all, since that one never converges:

```sh
EXPECT_RELEASE=<version> checks/check-live-urls.sh "$HUGO_BASEURL"
```

Sourcing the environment file first puts the deploy root and the base URL in the environment, so no literal value is typed. `make-release.sh` then needs no arguments, because its deploy root falls back to `$DEPLOY_ROOT` and its version falls back to a timestamp. It still accepts both, and [Deploying](#deploying) below passes them explicitly, which is what CI does so a pipeline run names the commit it built rather than the clock. Either form works locally, and the argument wins over the environment.

`ENV_FILE` is set as well as sourced, and the redundancy is deliberate. The script sources its own file regardless, so leaving `ENV_FILE` off would build and install against `secrets/.env` while the shell's `$HUGO_BASEURL` still named staging, and the run would check the staging site after publishing to the production root. The script prints the file it read, on every build, for that reason.

It refuses to install a release that fails the build gate. `check-live-urls.sh` does take a base URL, which is where the sourced `$HUGO_BASEURL` goes. It follows all 1,245 URLs against the running mirror, checking each redirect's destination rather than trusting its status code.

Expect `PASS - 1245 URLs honored`. Anything less is a finding, and the output names each URL that failed and what it answered.

A documentation-only or workflow-only change does not need this. A change to the four paths above does, because for those CI's green is not evidence.

## Checking a Site Behind the Auth Gate

Staging keeps Pangolin's authentication on, so an unauthenticated request never reaches the site. `check-live-urls.sh` presents a Pangolin resource access token when both halves of the pair are set, and sends nothing when neither is:

```sh
set -a; . secrets/staging.env; set +a
checks/check-live-urls.sh "$HUGO_BASEURL"
```

| Variable | Header |
| --- | --- |
| `PANGOLIN_ACCESS_TOKEN_ID` | `P-Access-Token-Id` |
| `PANGOLIN_ACCESS_TOKEN` | `P-Access-Token` |

Set both or neither. Half a pair is a typo rather than a choice, and it is rejected as one rather than presented as a failing site.

Three properties of how the credential is handled, each there for a reason worth keeping:

- **It travels in a mode-`600` curl config file, not in `-H` arguments.** A command line is readable in `ps` for the life of the process, and this runs 1,245 of them. The config file is also the only form that survives the `export -f` the parallel checks run under, because bash cannot export an array.
- **It is sent to the base URL's own origin and nowhere else.** The check follows every redirect's destination, and every destination in the contract is same-origin today. A rule that one day points off-site must not mail the credential to whoever is on the other end.
- **A preflight request runs before the 1,245.** Behind an auth gate a wrong token fails *every* URL, and the output then reads as a site that has vanished rather than as a bad credential. The two are indistinguishable from the far end of a CI log, so the run stops on the first request with a message naming which of the two it was.

## Deploying

```sh
HUGO_BASEURL=<base-url> deploy/make-release.sh <deploy-root> "$(git rev-parse --short HEAD)"
checks/check-live-urls.sh <base-url>
```

The deploy root and the base URL are the only host-specific values. A local run reads them from an untracked file under `secrets/`, one per environment, copied from [`deploy/env.example`](./deploy/env.example), and CI passes both explicitly. The whole `secrets/` directory is gitignored, so no address, path, or container name belonging to one machine reaches the published history.

**Always set `HUGO_BASEURL` for anything that is not production.** The base URL is baked into the canonical tag, the feed links, and every absolute permalink, so a mirror built without it serves pages that all point back at the production address. Nothing downstream catches this, because the pages render at the right paths and the build gate passes. The effective value is printed on every build for that reason.

| Variable | Effect |
| --- | --- |
| `ENV_FILE` | Which environment file to source. Defaults to `secrets/.env`. |
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
```

The content reverts on the rename alone, because the container mounts the parent directory and the kernel resolves `current` per request. The rules follow on the watcher's next poll, within about a quarter of a second, since a rollback is a config change like any other and re-adapting re-reads the reverted release's `Caddyfile` and maps.

**For that fraction of a second the reverted content is served under the newer release's rules.** That is the same window every deploy has, in the other direction, and it is harmless while every rule is a redirect: a stale redirect sends a visitor to a page that exists in both releases. It would stop being harmless if a rule ever *gated* content rather than redirecting it, and at that point the flip has to become a restart again.

Verify with `EXPECT_RELEASE` set to the release being rolled back **to**, which is what proves the rules actually reverted rather than assuming they did.

Verify with `checks/check-live-urls.sh` against the environment before considering the rollback finished.

## Retention

Ten releases are kept. Unchanged files hard-link to the previous release, so the static tree is stored once rather than ten times, and a release costs roughly the size of the generated output.

The script asserts both halves of that rather than assuming them. It fails when the prune leaves more releases than the limit, and when hard-linking produces no shared files at all. Both have failed silently before, and on a compressing filesystem the disk usage looks plausible either way.

## Who Owns What

The site and the server it runs on are maintained separately, so the boundary is written down rather than inferred. This repo owns the artifact and what proves it correct; the host owns where a release may be written and what happens to it afterwards.

| This repo | The host |
| --- | --- |
| The GitHub Actions workflow | The SSH endpoint and its forced command |
| `deploy/make-release.sh`, the bundle layout, and the Caddyfile inside it | The bootstrap `import`, the containers, and their environment variables |
| `checks/check-live-urls.sh` and the URL contract | Config-watchdog and release-prune timers |
| The release id and the `@@RELEASE@@` stamp | Proxy resources, routing, tokens, and TLS |
| What a release contains | Where a release may be written, and what happens after |

The two meet at the container contract in [`deploy/README.md`](./deploy/README.md#container-contract). A defect on the host side is fixed on the host; a pipeline that needs the contract to say something different asks for a contract change rather than growing a second copy of the other side's work.

## Serving

Caddy serves the bundle and binds an internal port only. TLS and the public listener belong to the proxy in front of it, so `auto_https off` and `admin off` are deliberate.

The container mounts the deploy root **read-only**, and mounts the **parent** rather than `current`. Docker resolves a symlink at container-creation time, so mounting the symlink pins the container to whichever release was live at startup and every later deploy stays invisible until the container is recreated.

Routing differs by environment and the bundle does not. Traefik on the home host has the Docker provider enabled, so container labels route. Pangolin's Traefik on the VPS does not, so routing there is created in the Pangolin UI and labels are silently ignored.

**Each environment is its own container with its own deploy root**, rather than one server addressing several roots. That is what keeps the bundle's config internal: the Caddyfile inside a release names `/srv/blog/current`, one root, and knows nothing about a sibling. A single server covering both would have to name both roots in a config held outside either bundle, and that config could not then roll back with the content it serves. Both containers bind the same internal port and are told apart by hostname, which the proxy in front resolves.

That last sentence is also the risk. **The container is the only thing that distinguishes one environment from another**, so a proxy rule aimed at the wrong one serves the wrong site under the right hostname and returns a healthy `200` with nothing logged anywhere. The bundle stamps `X-Blog-Env` and `X-Robots-Tag` from container variables so a response says which environment produced it, and `checks/check-live-urls.sh` fails on a mismatch when `EXPECT_SITE_ENV` is set. [`deploy/README.md`](./deploy/README.md#identifying-the-environment) carries the mechanism and, more importantly, why `SITE_ROBOTS` defaults to `index, follow` rather than to the safer-looking `noindex`.

Caddy also sets `trusted_proxies`, because a proxy fronts it in every environment and the peer address is therefore always the proxy. Without it the access log records that one internal address as the client for every request the site serves, and `X-Forwarded-For` is ignored rather than trusted. The ranges come from the container, since the same bundle runs on hosts whose docker subnets differ. **Exclude the bridge gateway from whatever range is trusted**: it is inside the subnet and it is how the host itself reaches the container, so trusting the subnet trusts every process on the host. Verified on the home mirrors by forging a header from the host, which succeeded until the gateway was excluded. **Trusting a range means believing `X-Forwarded-For` from anything in it**, so it is a security boundary rather than a formality, and the bundle's RFC1918 default is only correct where a proxy is genuinely the only thing that can reach the port. [`deploy/README.md`](./deploy/README.md#trusting-the-proxy) carries the three behaviours and why binding to `127.0.0.1` does not make direct access impossible.

### The bootstrap, and why it is not in the release

The container reads three host paths, and only one of them a release ever writes:

| Host path | Mounted at | Written by |
| --- | --- | --- |
| `$DEPLOY_ROOT` | `/srv/blog`, read-only | every release |
| `$CADDY_APPDATA/config` | `/config` | placed once, by hand |
| `$CADDY_APPDATA/data` | `/data` | Caddy itself, persisting state across a recreate |

[`deploy/bootstrap.Caddyfile`](./deploy/bootstrap.Caddyfile) goes in the `config` directory and is the **only** Caddy file outside the release bundle. It carries a single `import` and no rules of its own, deliberately: everything describing the site ships inside the release, so a rollback reverts the rules and the content together. Rules held here instead would leave a rolled-back site being served by the current release's redirects.

Because it sits outside the bundle, no release updates it. Install or refresh it explicitly, once per environment, which is the same command against a different sourced file:

```sh
set -a; . secrets/.env; set +a          # or secrets/staging.env
install -m 644 deploy/bootstrap.Caddyfile "$CADDY_APPDATA/config/Caddyfile"
docker restart "$CADDY_CONTAINER"   # only this file needs one, see below
```

**A container started before its environment has a release restart-loops**, because the bootstrap imports a path that does not exist yet. Create the directories, install the bootstrap, cut the first release, and start the container in that order. The container definition can also be held disabled until the release exists, which is the same fix from the other side.

**This is the one file whose change still needs a restart**, and the reason is a nice inversion of why everything else does not. The watcher polls `/config/Caddyfile` and reloads when the *adapted result* changes, which is how a release reaches it at all: this file never changes, but re-adapting re-executes its `import` and picks up the new release behind it. Editing this file itself is the case the watcher handles worst, because a bootstrap that no longer parses leaves nothing to reload into. Restart, and read the log.

Everything inside the bundle, `deploy/Caddyfile` and anything under `deploy/maps/`, reloads without one. See "Local Verification Before a Pull Request" above.

`CADDY_APPDATA` is recorded in each environment's file for exactly this reason. No script reads it, so a rebuild would otherwise depend on someone remembering where the bootstrap goes.

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
- **One key covers both environments**, rather than one per environment. Recorded here as a decision rather than an omission, because the opposite is the obvious default and this file asserted it until the two environments actually existed. A per-environment split pays off only where the two keys never share a machine, and here they would: both private keys sit on the maintainer's one workstation, and both secrets in one GitHub store, so whatever reaches one reaches the other. The split would buy a boundary that is already crossed everywhere it is held.
- **The forced command is therefore the only boundary left, and it is confined to the parent of both roots.** That is what a single key costs: `rrsync` pins a key to one directory, so the two deploy roots sit under one parent and one pinned command covers both. The roots are `/srv/blog/sites/production` and `/srv/blog/sites/staging`, and the confinement root is `/srv/blog/sites`.
- **That parent holds content and nothing else, which is why it is not `/srv/blog`.** `/srv/blog` is the deploy account's home directory and contains `/srv/blog/.ssh/authorized_keys`. Confining the key there would let it rewrite the very file that defines what the key may do, and a `--delete` at the root would take `.ssh` with it. Confinement that encloses its own definition is not confinement. The extra `sites/` level is a security boundary rather than tidiness.
- Unattended upgrades run with automatic reboot, which is safe because the site is static and the swap survives a restart.

A deploy key that can write a release can already rewrite the site's Caddy config, because [`deploy/Caddyfile`](./deploy/Caddyfile) ships inside the bundle and the bootstrap imports it. Withholding the container's `/config` directory from the same key therefore protects nothing, which is why the bootstrap stays outside the deploy path for the reason given below and not for a security one.

## Backup and Restore

**The deploy root needs no backup.** The site is reproducible from this repository by running the deploy again, so the only thing worth protecting on the server is its configuration: the container definition, the proxy configuration, the deploy account and its restricted key, and the upgrade schedule.

A bare-metal restore is therefore rebuilding the host, restoring that configuration, and running a deploy. Treat any procedure that backs up the deploy root as protecting a copy of something git already holds.
