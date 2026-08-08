# OPERATIONS.md

How this site is built, released, served, and rolled back. [`GOVERNANCE.md`](./GOVERNANCE.md) holds the cross-cutting rules and [`WORKFLOW.md`](./WORKFLOW.md) the CI contract. This file is the operational procedure, and it is the one to read before touching a server.

## Environments

Four environments, in two pairs. Each pair is one publish site and one staging site, and the local pair exists to rehearse the remote one.

| Environment | Address | Fronted by | Purpose |
| --- | --- | --- | --- |
| Local publish mirror | a private hostname, set in `secrets/local.production.env` | Traefik, on the maintainer's own network | Proves the artifact. The redirect rules, the maps, and the release mechanics. |
| Local staging mirror | a second private hostname, set in `secrets/local.staging.env` | Traefik | Proves that two environments on one host stay independent, before that matters on a server. |
| Staging | `blog.vps.insanegenius.net`, behind the auth gate, set in `secrets/vps.staging.env` | Pangolin | Proves the infrastructure. Routing, TLS, and the deploy path. |
| Production | `blog.insanegenius.com`, set in `secrets/vps.production.env` | Pangolin | The public site. |

The local mirrors are not staging. They run the same bundle against the same web server, so they catch a broken redirect or a bad permission for free, but they exercise none of the routing, authentication, or certificate machinery that only exists on the VPS. Passing locally says the artifact is right. It says nothing about whether the server in front of it is.

**The two words are `production` and `staging`, spelled out, in every position.** No `prod`, no `stage`. The same two name the container, the deploy root, the environment file, the `X-Blog-Env` value, and the GitHub Environment. This is not tidiness: the environment name is a value that gets **compared**, by `EXPECT_SITE_ENV` and by the deploy, so a spelling that differs in one position fails a deploy for a reason that reads like an outage. The local mirrors prefix the same words, `mirror-production` and `mirror-staging`, so a header names exactly one of the four environments in the fleet.

Each environment is one file under `secrets/`, named `<server>.<environment>.env`, selected with `ENV_FILE`, and holding the deploy root, the base URL, and the container name. The name carries both halves because the two pairs differ in server as well as environment, so a file says which machine it describes rather than leaving that to the value inside it, and the four in the table above are the four files. `secrets/local.production.env` is the one read when `ENV_FILE` is unset. Selecting the file is how an environment is chosen: the file is sourced with `set -a`, so it overwrites a `DEPLOY_ROOT` the caller exported and setting that variable by hand does not switch anything. A named file that does not exist is a hard failure rather than a fall-through, because on a host serving two sites the ambient value is the other site's root.

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

## The Migration Record

**The migration is documented once, as a post on the site, and that post is the artifact to reference.** [`content/posts/2026/08/01/moving-this-blog-from-wordpress-to-hugo.md`](./content/posts/2026/08/01/moving-this-blog-from-wordpress-to-hugo.md) holds how the URL surface was captured, why the contract splits into a render half and a redirect half, why the Blogger permalink map needs more entries than the posts it covers, why the media had to come from the export tar and be hash-verified, and which Hugo taxonomy default moves every archive to a new address without reporting anything.

**Read it before changing anything under [`checks/`](./checks/) or [`deploy/maps/`](./deploy/maps/).** Both hold values that no code derives and no test explains, and the reasoning behind them is in the post rather than beside them. Cite the post rather than restating it. This file is the procedure and the post is the account of how the procedure came to be, so where the two disagree this file governs what to do while the post explains why the check exists.

**The post is content, so it sits under the URL contract.** Editing it moves nothing. Renaming it or taking it down breaks an address the site serves. A fact in it that proves wrong is corrected in the post rather than footnoted here.

### Rebuilding from the Exports

Everything derived is in this repository. Everything it was derived *from* is in a capture directory outside it, which is where a rebuild starts. **The capture path is `CAPTURE_ROOT` in `secrets/local.production.env`**, recorded alongside the other values that name a machine rather than the project, so it is read from there rather than searched for. The capture is not a git repository, so it has no history to revert to, and it is read-only in normal use.

| Under the capture | Holds | Recoverable |
| --- | --- | --- |
| `export/raw/` | the WordPress content export, WXR XML | yes, from the WordPress account while it exists |
| `export/media-tar/` | the media export, the only trustworthy copy of the images | yes, from the same place |
| `mirror/` | a crawl of the old platform as it served, including the media it linked from other hosts | no, once the old hosting ends |
| `inventory/` | the URL and media inventories derived from that crawl | no, for the same reason |

The two exports are the only inputs a person has to fetch, and `EXPORT-INSTRUCTIONS.md` at the root of the capture records which two menu items produce them and the counts each has to reconcile against. The counts are the point, because a partial export is the common way a migration loses posts without reporting anything.

[`checks/build-redirects.py`](./checks/build-redirects.py) takes the capture directory as its one argument and rebuilds everything under `deploy/maps/` from it. It selects the export **by content** rather than by filename and fails unless exactly one candidate holds published posts, because the capture also holds a media-only export whose zero posts produce empty maps that are indistinguishable from working ones until the redirects are live.

## Local Verification Before a Pull Request

**CI cannot prove a redirect.** The validation workflow builds the site and checks the render half of the contract, which is every URL that must return a page. Most of the contract is not pages, and those URLs are the web server's job, which nothing in a build exercises. A change to the Caddy config or to a generated map is therefore invisible to CI: the workflow goes green while the redirect it broke stays broken until someone follows a sixteen-year-old link.

So release to the local mirror and run the live check **before** opening a pull request that touches any of these:

| Path | Why it needs a running server |
| --- | --- |
| [`deploy/Caddyfile`](./deploy/Caddyfile) | The redirect rules. Rule order is load-bearing, and a regex that matches too much is silent. |
| [`deploy/maps/`](./deploy/maps/) | The lookup tables. A regenerated map can lose entries and still parse. |
| `content/`, `static/` | A moved or renamed page turns a redirect destination into a 404, which the build gate does not follow. |
| `hugo.yaml`, `layouts/` | Permalink and taxonomy changes move URLs underneath the redirects that point at them. |

```sh
set -a; . secrets/local.production.env; set +a
deploy/make-release.sh
checks/check-live-urls.sh "$HUGO_BASEURL"
```

Against the staging mirror, name its file in both places, since the sourced values and the ones `make-release.sh` reads must describe the same environment:

```sh
set -a; . secrets/local.staging.env; set +a
ENV_FILE=secrets/local.staging.env deploy/make-release.sh
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

`ENV_FILE` is set as well as sourced, and the redundancy is deliberate. The script sources its own file regardless, so leaving `ENV_FILE` off would build and install against `secrets/local.production.env` while the shell's `$HUGO_BASEURL` still named staging, and the run would check the staging site after publishing to the production root. The script prints the file it read, on every build, for that reason.

It refuses to install a release that fails the build gate. `check-live-urls.sh` does take a base URL, which is where the sourced `$HUGO_BASEURL` goes. It follows every URL in the contract against the running mirror, checking each redirect's destination rather than trusting its status code.

Expect a `PASS` naming the number of URLs honored, which is the two lists' combined length and grows as they do. Anything less is a finding, and the output names each URL that failed and what it answered.

A documentation-only or workflow-only change does not need this. A change to the four paths above does, because for those CI's green is not evidence.

## Checking a Site Behind the Auth Gate

Staging keeps Pangolin's authentication on, so an unauthenticated request never reaches the site. `check-live-urls.sh` presents a Pangolin resource access token when both halves of the pair are set, and sends nothing when neither is:

```sh
set -a; . secrets/vps.staging.env; set +a
checks/check-live-urls.sh "$HUGO_BASEURL"
```

The gate is the VPS staging environment's, so this is `secrets/vps.staging.env`. The local staging mirror sits behind Traefik on the maintainer's own network and carries neither half of the pair.

| Variable | Header |
| --- | --- |
| `PANGOLIN_ACCESS_TOKEN_ID` | `P-Access-Token-Id` |
| `PANGOLIN_ACCESS_TOKEN` | `P-Access-Token` |

Set both or neither. Half a pair is a typo rather than a choice, and it is rejected as one rather than presented as a failing site.

Three properties of how the credential is handled, each there for a reason worth keeping:

- **It travels in a mode-`600` curl config file, not in `-H` arguments.** A command line is readable in `ps` for the life of the process, and this runs one per URL in the contract. The config file is also the only form that survives the `export -f` the parallel checks run under, because bash cannot export an array.
- **It is sent to the base URL's own origin and nowhere else.** The check follows every redirect's destination, and every destination in the contract is same-origin today. A rule that one day points off-site must not mail the credential to whoever is on the other end.
- **A preflight request runs before the rest.** Behind an auth gate a wrong token fails *every* URL, and the output then reads as a site that has vanished rather than as a bad credential. The two are indistinguishable from the far end of a CI log, so the run stops on the first request with a message naming which of the two it was.

## Deploying

```sh
HUGO_BASEURL=<base-url> deploy/make-release.sh <deploy-root> "$(git rev-parse --short HEAD)"
checks/check-live-urls.sh <base-url>
```

The deploy root and the base URL are the only host-specific values. A local run reads them from an untracked file under `secrets/`, one per environment, copied from [`deploy/env.example`](./deploy/env.example), and CI passes both explicitly. The whole `secrets/` directory is gitignored, so no address, path, or container name belonging to one machine reaches the published history.

**Always set `HUGO_BASEURL` for anything that is not production.** The base URL is baked into the canonical tag, the feed links, and every absolute permalink, so a mirror built without it serves pages that all point back at the production address. Nothing downstream catches this, because the pages render at the right paths and the build gate passes. The effective value is printed on every build for that reason.

| Variable | Effect |
| --- | --- |
| `ENV_FILE` | Which environment file to source. Defaults to `secrets/local.production.env`. |
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

Ten releases are kept at every deploy root, by two independent mechanisms that agree on the number rather than by one mechanism reaching both.

**On a local mirror, [`deploy/make-release.sh`](./deploy/make-release.sh) prunes as its last step.** Unchanged files hard-link to the previous release, so the static tree is stored once rather than ten times, and a release costs roughly the size of the generated output.

The script asserts both halves of that rather than assuming them. It fails when the prune leaves more releases than the limit, and when hard-linking produces no shared files at all. Both have failed silently before, and on a compressing filesystem the disk usage looks plausible either way.

**At a VPS deploy root, the host's `blog-prune-releases.timer` prunes and nothing in this repo does.** It runs daily and keeps ten release bundles per environment, and the release `current` resolves to is retained unconditionally without consuming one of the ten, so the live site survives even a misconfigured count. **Name the unit rather than the number**, because a second daily retention runs on the same host, `pangolin-backup.timer`, and it keeps fourteen encrypted config archives. "Ten, daily" identifies neither of them once it is read on its own. It orders by modification time rather than by name, because the release id is a caller-supplied argument and a label passed in place of a timestamp would sort wrongly and retire the wrong releases. It refuses outright, removing nothing, when `current` dangles or is not a symlink, since a broken `current` means the site is already serving nothing and guessing which release was meant to be live is the wrong move while it is.

**Nothing prunes on the deploy path, and that is what keeps the deploy key's capability small.** A prune racing a deploy could take the rollback target, where a lingering release only costs disk. This is also why the key needs no delete capability, which is the property "Server Hardening" depends on. The count and the timer belong to the host, so this section records what the host declares rather than holding a second copy of it. See "Who Owns What".

## Working With the VPS

**Every path and hostname on this page is a value in `secrets/`, never a literal to be remembered or asked for.** The convention is the one "Environments" describes and `CAPTURE_ROOT` already follows: a value naming a machine rather than the project lives in the environment file, is sourced with `set -a`, and is read from there rather than searched for. The VPS values are environment-independent, because there is one such host rather than one per environment, so they sit in the default file alongside `CAPTURE_ROOT`.

```sh
set -a; . secrets/local.production.env; set +a
ssh "$VPS_SSH_HOST" true && echo reachable
```

| Value | Names | Side |
| --- | --- | --- |
| `VPS_SSH_HOST` | the administrative login | the VPS |
| `VPS_TRAEFIK_LOG` | today's live access log, still being appended to | the VPS |
| `VPS_TRAEFIK_LOG_ARCHIVE` | the rotated access logs, and the source of the off-host copy | the VPS |
| `VPS_COMMS_DIR` | the two agent channel files | the VPS |
| `LOG_ARCHIVE_ROOT` | the off-host copy of the rotated logs | the backup host |
| `BACKUP_ARCHIVE_ROOT` | the off-host encrypted archives and the plaintext hostconfig tree beside them | the backup host |

**There are two credentials to this host and picking the wrong one is the first mistake to avoid.** `DEPLOY_SSH_USER`, held per environment and used only by the deploy, reaches a confined account behind an `rrsync` forced command that can write one release tree and read nothing else. `VPS_SSH_HOST` is the ordinary administrative login used for everything on this page. They are deliberately separate credentials with different blast radii, so reaching for the deploy account to read a log fails in a way that reads like an outage, and reaching for the admin account to deploy grants far more than the deploy needs.

**The off-host copy is made by a script in this repository, [`ops/vps-backup-pull`](./ops/vps-backup-pull), on a `systemd` timer on the backup host.** It copies three things off the VPS into `BACKUP_ARCHIVE_ROOT` and `LOG_ARCHIVE_ROOT`: the encrypted archives, a plaintext copy of the same non-secret host files, and the rotated access logs. What it does, the three behaviors that look like bugs and are not, how to install it, and how to check it ran are in [`ops/README.md`](./ops/README.md). Read the unit and its last run on the backup host rather than trusting a schedule written down anywhere, including here.

**It is a pull rather than a push, and nothing on the VPS knows it happens.** That direction is the security property rather than an implementation detail: the backup host holds a key the VPS trusts, and the VPS holds no credential reaching any other system, so a compromise of the web server cannot walk into the backups that exist to survive it.

**Both sides use one set of names, so there is nothing to reconcile.** The pull writes `BACKUP_ARCHIVE_ROOT` and `LOG_ARCHIVE_ROOT` and the log review reads the same two, spelled the same way, and [`ops/install.sh`](./ops/install.sh) generates the pull's `EnvironmentFile` from this repository's `secrets/` file by copying rather than translating. That is deliberate and was not the first attempt: the two sides briefly had separate names for the same four directories, which needed a mapping table in this file and a translation step in the installer, and both disappeared when the names were unified. A value that exists once cannot disagree with itself.

```sh
set -a; . secrets/local.production.env; set +a
ls -d "$LOG_ARCHIVE_ROOT" "$BACKUP_ARCHIVE_ROOT"
```

**Today's traffic is never in the off-host copy, and that is deliberate.** Rotation is what makes a file eligible to be pulled, so a live log would be copied as a torn prefix and fetched again on the next run. An analysis covering today therefore reads `VPS_TRAEFIK_LOG` over SSH and everything older from `LOG_ARCHIVE_ROOT`, and treats the two as one series joined on `StartUTC` rather than on which file a line came from.

**The plaintext `hostconfig` tree under `BACKUP_ARCHIVE_ROOT` is the readable copy of the VPS's own configuration**, carrying the same non-secret files the encrypted archives hold. It exists so a rebuild does not depend on the encryption key, which is not on the backup host and must never be put there, because beside the ciphertext it would make the encryption decorative. What that tree covers is whatever the VPS advertises, read from the host rather than duplicated here, so it tracks the host instead of drifting from a list.

**The channel transfers are the one exception, and they must stay literal.** The permission allowlist in `.claude/settings.local.json` matches the text of a command rather than what it expands to, so substituting `"$VPS_SSH_HOST:$VPS_COMMS_DIR/..."` into those two `rsync` lines turns an allowed command into one that prompts, while looking like a tidy-up that changed nothing. Use the values above everywhere else, and leave the two commands under "The Channel Between the Two Sides" spelled out exactly as they are written there.

**What this section does not cover, and where it lives instead.** Reading the logs for content is "Log Review"; exchanging rounds with the agent that owns the host is "The Channel Between the Two Sides"; the boundary of which side fixes what is "Who Owns What"; and what a rebuild restores, including the host-key step that blocks both deploy and rollback, is "Backup and Restore".

## Log Review

**Real traffic is the only source that finds what every check here is blind to.** The URL contract proves the URLs someone thought to list and the redirects derived from the export. It cannot know about a URL nobody recorded, because the lists are their own standard: the gates check the built site and the running server against those lists, never against the old platform that served the addresses. An address the crawl missed is therefore missing from every gate that reads them, and a visitor following a sixteen-year-old link is the one reader who tests for it.

Review runs in both directions, which are the same two the media checks read and have the same blind spots for the same reason.

| Direction | Question | Signal | Cadence |
| --- | --- | --- | --- |
| Outward | What did someone ask for that is not here? | non-200 responses | daily for the first week after cutover, then monthly |
| Inward | What is here that nobody has ever asked for? | URLs absent from every 200 | quarterly at the earliest, and a long tail by nature |

**The outward pass is the one with an action.** A 404 on a path shaped like real content means the golden list missed a URL: add it to [`checks/golden-urls.txt`](./checks/golden-urls.txt) and add a redirect, per that file's own maintenance rules. Expect the raw counts to be dominated by scanners probing for `wp-login.php`, `.env`, and `.git/config`, which is noise from a site that used to run WordPress and should be filtered by shape rather than investigated.

**The inward pass answers a question nothing else can.** Subtracting every URL that has ever returned 200 from the set the site builds names the content no reader has reached. It is slow evidence and deliberately so, since a post can go a year without a visit and still be worth keeping. Its first concrete use is the carried media that no page links and that the old platform never published, counted exactly by the parity gate and broken down in [`checks/README.md`](./checks/README.md): if nothing requests those files across a year, that settles whether carrying them is preservation or clutter, and no reasoning from the repository alone can settle it.

### The log is three tiers, and each is blind to something

A request crosses the proxy before it reaches the site, so no single log answers both questions.

| Tier | Sees | Cannot see |
| --- | --- | --- |
| Traefik, or Pangolin's Traefik on the VPS | every request reaching the host, including unknown hostnames, TLS failures, and traffic aimed at names this site does not serve | which release answered, since Traefik logs request headers and not response headers |
| Pangolin, on the VPS only | requests the auth gate rejected | anything on the local mirrors, which have no gate |
| Caddy, per environment | path, status, and the `X-Blog-Release` that answered | anything the tiers above rejected, which never arrives |

**A 404 count taken from Caddy alone is therefore a floor, not a total.** A request the edge refused is a reader who found nothing just as surely, and it appears in no Caddy log. Read the edge for what never arrived and Caddy for what arrived and failed, and treat the two as one answer.

**`ServiceName` is what separates those two cases inside the edge log itself**, which is otherwise a distinction this table draws conceptually and leaves you no way to apply. A Traefik line carrying a service name was routed, so the 404 came from the site. A line with the field absent matched no router at all, so the edge answered and the site never saw the request. The second kind is the one Caddy is structurally blind to, and it is rare enough that it reads as noise in a total and is worth listing individually. On 2026-08-08, 99 of 101 site-host 404s carried `1-Blog-Production-service@http` and 2 carried nothing, the pair being `/` and `/favicon.ico` from one client inside the same second.

Two properties of the Caddy side are worth knowing before parsing it. Its access log is `format console`, so each line is a timestamp, a level, and a logger name followed by a JSON object rather than being JSON itself, and a parser that assumes one object per line reads nothing. And `trusted_proxies` is what makes `client_ip` the reader rather than the proxy, which is the same setting "Serving" describes as a security boundary. Without it every request in the log appears to come from one internal address, and the inward pass cannot distinguish a reader from a health check.

### Reading a 404 list without being fooled by it

The outward pass is four filters over the edge log, and each one exists because skipping it produced a wrong answer once.

**Exclude this repository's own deploy gate first.** `check-live-urls.sh` requests the whole URL contract on every deploy, so an unfiltered day is mostly a recording of our own `curl`. Filter on user agent: on 2026-08-08, 9,285 of 9,996 requests were `curl/8.5.0` and the 711 that remained are the entire real dataset. A count that omits this step is measuring the pipeline rather than the readers, and it will be an order of magnitude too large.

**A referer does not implicate this site unless it points somewhere else.** The rule worth applying is that a 404 carrying a referer is a broken link and a 404 without one is a typed or probed address, and it fails on scanners, which set `Referer` to the request URL itself. Every one of the 36 referer-bearing site-host 404s on 2026-08-08 was self-referential, so the unrefined rule reported three dozen broken links on a site that had none. Compare the referer against `scheme://RequestHost + RequestPath` and discard the matches before counting.

**Filter the scanner shapes by shape, never by investigating them.** A site that used to run WordPress attracts probes for `.env` and its dozen variants, `wp-config.php`, `.git/config`, `phpinfo.php`, cloud credential files, and framework config paths. They dominate the raw list and none is ever a finding. What is left after the three filters above is small enough to read line by line, which is the point of running them.

**Then cross-reference what remains against the contract**, because that is the only step with an action. A surviving 404 whose path appears in [`checks/golden-urls.txt`](./checks/golden-urls.txt) or in [`deploy/maps/`](./deploy/maps/) is a redirect that is not working. A surviving 404 shaped like real content and present in neither is the case this whole pass exists to find, and it is added to the golden list with a redirect per that file's maintenance rules. A run where nothing survives is the expected result and should be recorded as one.

**Two `jq` mistakes each read as a plausible answer rather than as an error.** A hyphenated key parses as subtraction, so `.request_User-Agent` silently is not the field you meant and `.["request_User-Agent"]` is, and the same holds for `Referer`. And `jq 'select(...)'` with no projection pretty-prints each match across many lines, so piping it to `wc -l` counts lines rather than records and overstates by roughly the width of the object. It reported 37 and 1,332 where the true counts were 1 and 36. Project with `@tsv` or pass `-c` before counting anything.

### Retention Is the Prerequisite, and It Belongs to the Host

**On the VPS the reviewable record is Traefik's access log**, at `/var/log/traefik/access.log`, one JSON object per line, one line per request, across every hostname the host serves. `RequestPath` carries the query string, so the legacy `/?p=<id>` traffic is visible as itself. Request headers are dropped except `Referer` and `User-Agent`, which is what keeps the Pangolin resource access token out of a file that is retained and copied, and query strings are logged in full, so treat an extract as sensitive.

**That log rotates and is eventually deleted, on a schedule the host sets and can change.** The window is long, and it is finite, so anything the inward pass depends on has to be copied off the host before the archive ages out. Read the current retention from the host rather than from this file, because a number written here is a number nothing checks.

**Caddy's container log is the runtime log rather than the access log**, bounded by the container's own log rotation. It is where a failed config load and a dead `--watch` surface. It is not durable across a container recreate, since the Docker `json-file` log lives under the container id, and an operator editing the compose file is the event that discards it. A release deploy is not: an rsync and a symlink flip run no Docker operation at all.

**Release attribution comes from a join rather than from a header.** Traefik cannot log a response header, so no access-log line names the release that answered. Join `StartUTC` against the release flip instead, which is exact outside a deploy window and ambiguous only inside one.

**Retention on the local mirrors is a different question and is unsolved.** Those containers use Docker's `json-file` driver with the built-in defaults, so a mirror's log grows without bound and is discarded when its container is recreated. That matters less than it did on the VPS, because the mirrors serve no readers, and it belongs to the host rather than to this repository, the same split "Retention" and "Who Owns What" describe for release pruning.

**The off-host copy of the access log exists, and the schedule that maintains it is younger than the copy.** The pull to the backup host is installed as a `systemd` timer running daily at 09:00 UTC, chosen to sit behind both producers on the VPS rather than beside them, and its first copy was made by hand rather than by the timer. Read the unit and its last run on the backup host rather than trusting this paragraph, for the same reason retention is read from the VPS: a claim about a schedule is only worth what the machine says.

**A rename on the VPS does not propagate to that copy, and nothing reports the divergence.** The pull passes no `--delete` for the logs, deliberately, since an append-only record must never be removed by a transfer. So a file **the VPS** renames, merges, or re-compresses after it has been pulled keeps its old name **on the backup host** forever, alongside the new one, and a count that walks that archive by filename double-counts the overlap. This has already happened once, to two archives whose names were a day ahead of their contents. **Read a date from a line's `StartUTC` rather than from the filename that holds it.** The reconciliation itself now travels with the data: the VPS keeps an append-only `RECONCILE.md` **inside the archive directory**, so the pull carries it automatically and a rename does not depend on someone rereading a channel file. It records what a file contained rather than what it was called, and it is counted among the pulled log files. **The VPS keeps a `MANIFEST.txt` in the same directory**, so expect the count to exceed the number of logs by two rather than by one, and expect any further explanatory file the host side adds to raise it again. Read the count as logs-plus-prose rather than as a number with a fixed offset.

**A journal with one entry is not evidence of one copy.** The pull can be run directly as well as by its timer, and a direct run writes no service record. Directory mtimes on the backup host are the copy times, where the file mtimes are the VPS's, so those are what to read when establishing when something arrived.

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

### The Channel Between the Two Sides

The two sides are maintained by two agents that share no filesystem, no repository, and no session. They exchange rounds through two files on the VPS, in `/srv/agent-comms/`, each named for its author rather than for a direction, because every directional word inverts depending on which side reads it:

| File | Author | From this side |
| --- | --- | --- |
| `vps-agent.md` | the host | pull it, and never write it |
| `blog-agent.md` | this repo | pull it, append a round, push it back |

The working copies live in `comms/`, which is gitignored, so they are found by name rather than in whichever session directory last held them:

```sh
rsync -a root@<vps-host>:/srv/agent-comms/vps-agent.md comms/vps-agent.md
rsync -a --no-o --no-g --chmod=F644 comms/blog-agent.md root@<vps-host>:/srv/agent-comms/blog-agent.md
```

**Spell both commands out rather than reading the host and directory from `secrets/`**, which is the opposite of the rule "Working With the VPS" sets for every other path, and is deliberate. These two are allowlisted in `.claude/settings.local.json`, and an allow rule matches the text of the command rather than the value it expands to, so replacing the literals with `$VPS_SSH_HOST` and `$VPS_COMMS_DIR` turns an allowed transfer into one that prompts. The same rule is why neither may be chained behind `cd` or `&&`: an allow rule matches a standalone command only.

**The push suppresses owner and group deliberately.** `-a` implies `-o` and `-g`, and the transfer connects as root, so a plain `rsync -a` carries this workstation's numeric uid onto a host that has no such user and leaves the file owned by a number.

Four rules, each covering a way the channel has already failed or could:

- **Never pass `--delete`.** Nothing in that directory should be removed by a transfer, and no permission scheme prevents it, since both sides connect as root.
- **Write only the file this side authors.** The other file is read-only here by convention alone.
- **Re-pull immediately before appending.** Both sides can write in the same minute, so a copy pulled an hour ago is not a base to push from. Pushing this side's file is a read-modify-write, and it is the one operation that can silently drop a round.
- **Timestamp every round from `date`, and add a changelog row.** Nothing sequences the rounds, so the timestamps are the only thing distinguishing a round that arrived late from a round that disagrees. A guessed timestamp is worse than none: a future-dated round sorts ahead of a genuinely later reply, which is the confusion the header exists to prevent.

**Convention is the only thing protecting either file, so the copies are what matter.** Each side connects as root, so nothing stops either file being overwritten, and one has been. What protects the record is the host's nightly backup, which covers both files and reaches an off-host copy, plus the maintainer's own copy.

**This repository holds the channel's rules and not its contents.** The rounds themselves stay out of git: they carry host detail this repository does not own, and publishing them here would put a second, unreviewed copy of the server's internals in a public repository to gain a backup the host already has.

**A transfer into that directory uses `rsync` rather than `scp` for a reason worth keeping.** The host sets `fs.protected_regular = 2`, which refuses `O_CREAT` on an existing file in a group-writable sticky directory whose owner differs from the file's, and root does not bypass it. `scp` and `sftp` open with `O_CREAT` and fail there. `rsync` writes a temporary file and renames, so it succeeds. The directory's current ownership keeps the rule from applying at all, and the failure returns the moment anyone tightens the permissions.

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
set -a; . secrets/local.production.env; set +a   # or any other secrets/<server>.<environment>.env
install -m 644 deploy/bootstrap.Caddyfile "$CADDY_APPDATA/config/Caddyfile"
docker restart "$CADDY_CONTAINER"   # only this file needs one, see below
```

**A container started before its environment has a release restart-loops**, because the bootstrap imports a path that does not exist yet. Create the directories, install the bootstrap, cut the first release, and start the container in that order. The container definition can also be held disabled until the release exists, which is the same fix from the other side.

**This is the one file whose change still needs a restart**, and the reason is a nice inversion of why everything else does not. The watcher polls `/config/Caddyfile` and reloads when the *adapted result* changes, which is how a release reaches it at all: this file never changes, but re-adapting re-executes its `import` and picks up the new release behind it. Editing this file itself is the case the watcher handles worst, because a bootstrap that no longer parses leaves nothing to reload into. Restart, and read the log.

Everything inside the bundle, `deploy/Caddyfile` and anything under `deploy/maps/`, reloads without one. See "Local Verification Before a Pull Request" above.

`CADDY_APPDATA` is recorded in each environment's file for exactly this reason. No script reads it, so a rebuild would otherwise depend on someone remembering where the bootstrap goes.

## Redirects

The site answers far more addresses than it renders, satisfied by a small set of `redir` directives and the map files they read, all inside the bundle. [`deploy/README.md`](./deploy/README.md) carries the per-class breakdown and the counts. This section covers the operational shape only, so the two do not restate each other.

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
- **The deploy workflow's ref gate is a security control rather than a tidiness check, and it is load-bearing for the same reason.** One key confined to the parent of both roots means a run's environment name, not a credential, decides which of the two trees it writes into. The two GitHub Environments hold separate secrets and separate variables, and that separation stops at the runner: whichever key is installed reaches both trees. So the gate refusing a production deploy from any ref but the default branch is the boundary the credentials do not draw, and it is dispatchable by anyone who can dispatch the workflow. Treat it as part of this list rather than as workflow housekeeping.
- **That parent holds content and nothing else, which is why it is not `/srv/blog`.** `/srv/blog` is the deploy account's home directory and contains `/srv/blog/.ssh/authorized_keys`. Confining the key there would let it rewrite the very file that defines what the key may do, and a `--delete` at the root would take `.ssh` with it. Confinement that encloses its own definition is not confinement. The extra `sites/` level is a security boundary rather than tidiness.
- Unattended upgrades run with automatic reboot, which is safe because the site is static and the swap survives a restart.

A deploy key that can write a release can already rewrite the site's Caddy config, because [`deploy/Caddyfile`](./deploy/Caddyfile) ships inside the bundle and the bootstrap imports it. Withholding the container's `/config` directory from the same key therefore protects nothing, which is why the bootstrap stays outside the deploy path for the reason given below and not for a security one.

## Backup and Restore

**The deploy root needs no backup.** The site is reproducible from this repository by running the deploy again, so the only thing worth protecting on the server is its configuration: the container definition, the proxy configuration, the deploy account and its restricted key, and the upgrade schedule.

A bare-metal restore is therefore rebuilding the host, restoring that configuration, and running a deploy. Treat any procedure that backs up the deploy root as protecting a copy of something git already holds.

**A rebuild regenerates the host's SSH keys, and the deploy verifies them, so one step belongs to this side.** Cloud-init deletes and recreates host keys when the instance identity changes, and the deploy transport sets `StrictHostKeyChecking=yes` against a pinned `DEPLOY_SSH_KNOWN_HOSTS`, held per environment. A rebuilt host therefore presents a key the pinned value does not match, and every deploy fails closed until the value is replaced **on both environments**. That blocks the rollback path as well as the deploy path, at exactly the moment a rebuild makes both matter. Read the new fingerprint and update both environments before the first deploy that follows a rebuild.
