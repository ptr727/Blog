# OPERATIONS.md

How this site is built, released, served, and rolled back. [`GOVERNANCE.md`](./GOVERNANCE.md) holds the cross-cutting rules and [`WORKFLOW.md`](./WORKFLOW.md) the CI contract. This file is the operational procedure, and it is the one to read before touching a server.

## Current State

**`blog.insanegenius.com` is served by the VPS production site.** Its DNS moved off WordPress.com on 2026-10-04. The `production` environment's `SITE_BASE_URL` is `https://blog.insanegenius.com/`, and the production container serves `X-Robots-Tag: index, follow`. This repository's builds appear in these places, and each one shows a change only after its own deploy:

- The VPS production site at `blog.insanegenius.com`, updated by `deploy-site.yml` with `environment=production`.
- The VPS staging site at `blog.vps.insanegenius.net`, behind the auth gate, updated by `deploy-site.yml` with `environment=staging`.
- The two local mirrors on the maintainer's homelab, updated only by `make-release.sh` from the maintainer's machine.

The interim hostname `blog.insanegenius.net` has no DNS record, and no setting here names it.

**The old WordPress.com site is kept rather than deleted.** On or after 2026-11-03, 30 clean days after the cutover, downgrade it to the free plan. That keeps the old media reachable as a safety net, and keeps the ability to export again.

No gate here catches a wrong `SITE_BASE_URL`, for the reason in [`checks/README.md`](./checks/README.md) "The robots check, and the one thing no gate here can do".

## Threat Model

What earns hardening effort here, and what does not.

**Hostile input reaches code in this tree through three surfaces.**

- Requests to the public sites, from browsers, crawlers, and scanners.
- A pull request's checks, which run whatever code the pull request carries. A fork's run gets a read-only token and no secrets, so its reach ends with that run.
- Upstream releases that Dependabot proposes. The merge bot merges each one into `develop` and `main` once the required checks pass, with no human review.

Hardening pays for itself where a hostile input on one of these surfaces can do damage beyond failing its own check.

**The media tooling is not such a place.** The media gate and the normalizer read the maintainer's own images and captured media. A fork can put a crafted file in front of the gate, and the worst outcome is that its own check fails. The tooling exists to keep the maintainer's metadata from leaking and to catch accidental damage, such as a truncated copy. Its existing checks stay, and nothing new is added to defend it against a crafted file.

**A hardening finding needs damage before it earns work.** Before fixing or filing one, name an input that reaches the code and the damage it does beyond failing its own check. Where there is none, decline the finding with that absence as the evidence, cite this section, and file nothing. A reviewer, human or bot, can always find one more malformed-input edge, so a correct finding is not by itself a reason to act. Two cases are worked anyway, each with the smallest change that settles it:

- A fuzzer failure, since it blocks every merge until it passes.
- A functional gap that a real committed file hits, such as metadata the normalizer cannot remove.

## Local Verification

What verifying a change here requires, including the half a pipeline cannot reach.

**CI cannot prove a redirect.** The validation workflow builds the site and checks the render half of the contract, which is every URL that must return a page. Most of the contract is not pages, and those URLs are the web server's job, which nothing in a build exercises. A change to the Caddy config or to a generated map is therefore invisible to CI: the workflow goes green while the redirect it broke stays broken until someone follows a sixteen-year-old link.

So release to the local mirror and run the live check **before** opening a pull request that touches any of these:

| Path | Why it needs a running server |
| --- | --- |
| [`deploy/Caddyfile`](./deploy/Caddyfile) | The redirect rules. Rule order is load-bearing, and a regex that matches too much is silent. |
| [`deploy/maps/`](./deploy/maps/) | The lookup tables. A regenerated map can lose entries and still parse. |
| `content/`, `static/` | A moved or renamed page turns a redirect destination into a 404, which the build gate does not follow. |
| `hugo.yaml`, `layouts/` | Permalink and taxonomy changes move URLs underneath the redirects that point at them. |

```sh
set -e
set -a; . ~/.secrets/blog.local.production.env; set +a
RELEASE="$(git rev-parse --short HEAD)"
ENV_FILE=~/.secrets/blog.local.production.env deploy/make-release.sh "" "$RELEASE"
EXPECT_RELEASE="$RELEASE" checks/check-live-urls.sh "$SITE_BASE_URL"
```

Name the file in both places, even when it is the default, since `make-release.sh` sources `ENV_FILE` independently of the shell above and a value already exported earlier in the same session would otherwise win silently over the sourced one. The empty first argument leaves the deploy root at the sourced `DEPLOY_ROOT`, and `RELEASE` is reused so `EXPECT_RELEASE` verifies the release the command just built rather than skipping the release-stamp guard. `set -e` matters here too: a failed `git rev-parse` would otherwise leave `RELEASE` empty, which silently skips the check's own release-stamp verification instead of failing loud:

```sh
set -e
set -a; . ~/.secrets/blog.local.staging.env; set +a
RELEASE="$(git rev-parse --short HEAD)"
ENV_FILE=~/.secrets/blog.local.staging.env deploy/make-release.sh "" "$RELEASE"
EXPECT_RELEASE="$RELEASE" checks/check-live-urls.sh "$SITE_BASE_URL"
```

**There is no restart step, and that depends on one flag.** The container runs `caddy run --watch`, which re-adapts the config on a timer and reloads it in process. Re-adapting re-executes every `import`, so a new release's `Caddyfile` and `maps/*.map` are picked up through the unchanged `/config/Caddyfile` that the watcher actually names. Content is live the instant the symlink moves, and the rules follow on the watcher's next poll.

**The watcher dies silently after one failed config load.** Verified: a flip to a valid release reloads, a flip to a missing one logs the failure and retains the last good config, and a flip back to a valid release **never reloads again**. Nothing in the log says it has given up. Every later deploy then lands content without its rules, which is the failure this section's release stamp exists to catch, and a restart is the only fix. Anything that breaks `current` even briefly, including a test, ends that container's ability to pick up releases.

**`--watch` needs no admin API**, which is the part worth knowing, because `admin off` makes `caddy reload` impossible and that looks like it should rule out reloading altogether. It does not. `caddy reload` POSTs to the admin endpoint, but the watcher reloads in process and never uses it. The log prints `admin endpoint disabled` and `watching config file for changes` together.

**Without that flag the failure is silent and specific.** Caddy expands `import` at config-parse time and does not watch the imported files, so swapping `current` changes what a *static file* request resolves to, per request, while the redirect rules and map tables stay as they were when Caddy last loaded. Verified both ways against a two-release fixture whose `Caddyfile` was byte-identical and whose map differed: with `--watch`, a flip moved a redirect from 301 to 404 and its replacement from 404 to 301. Without it, neither moved.

That is why the check verifies the config rather than trusting it. **When the release changed `deploy/Caddyfile` or anything under `deploy/maps/`**, a check run against stale rules exercises the **previous** config, and a broken redirect reports `PASS` while the shipped artifact is broken. The wrong answer is a green check rather than an error, which is the worst shape a failure can take here.

So the bundle stamps its own version as `X-Blog-Release`, and `check-live-urls.sh` compares it against `EXPECT_RELEASE` before checking a single URL. It **waits** for a match rather than sampling once, because the reload is asynchronous and a check that starts immediately after a deploy will otherwise race it. The timeout is what still catches a container that is not watching at all, since that one never converges:

```sh
EXPECT_RELEASE=<version> checks/check-live-urls.sh "$SITE_BASE_URL"
```

Sourcing the environment file first puts the deploy root and the base URL in the environment, so no literal value is typed. `make-release.sh` then needs no arguments, because its deploy root falls back to `$DEPLOY_ROOT` and its version falls back to a timestamp. It still accepts both arguments, and the deploy workflow passes a bundle path and a version, as [Deploying](#deploying) below shows. Either form works locally, and the argument wins over the environment.

`ENV_FILE` is set as well as sourced, and the redundancy is deliberate. The script sources its own file regardless, so leaving `ENV_FILE` off would build and install against `~/.secrets/blog.local.production.env` while the shell's `$SITE_BASE_URL` still named staging, and the run would check the staging site after publishing to the production root. The script prints the file it read, on every build, for that reason.

It refuses to install a release that fails the build gate. `check-live-urls.sh` does take a base URL, which is where the sourced `$SITE_BASE_URL` goes. It follows every URL in the contract against the running mirror, checking each redirect's destination rather than trusting its status code.

Expect a `PASS` naming the number of URLs honored. That is the three lists' combined length, plus the family pages where `SITE_EXTRA_BASE_URL` is set. Anything less is a finding, and the output names each URL that failed and what it answered.

A documentation-only or workflow-only change does not need this. A change to the four paths above does, because for those CI's green is not evidence.

**The Python gates run per directory, the way CI runs them.** The validator gates [`checks/`](./checks/) and [`scripts/`](./scripts/), the two directories the workflows declare in its `python-directories` input, with ruff, mypy, and a test suite under coverage. `checks/` is standard library only, so its tools run through `uvx` and its suite runs under `unittest`. `scripts/` installs Pillow, pytest, and pytest-cov from its `requirements.txt`, which holds the one Pillow pin, and runs its suite under pytest. [`capture/`](./capture/) is not declared, because it is one-shot WordPress migration tooling that has already run and owes no test suite, so the validator's warning about its files is expected.

```sh
set -e
cd checks
uvx ruff@latest check .
uvx ruff@latest format --check .
uvx mypy@latest
uvx coverage@latest run -m unittest discover -s tests
cd ../scripts
uv venv --clear --python 3.13
uv pip install -r requirements.txt
uvx ruff@latest check .
uvx ruff@latest format --check .
uvx mypy@latest --python-executable .venv/bin/python
.venv/bin/python -m pytest
```

## Runbooks

The procedures that change what the servers are serving. Read [Local Verification](#local-verification) first, since every one of them starts from a release that has already passed its gates.

### Deploying

```sh
SITE_BASE_URL=<base-url> deploy/make-release.sh <bundle-path> <release-id>
EXPECT_RELEASE=<release-id> checks/check-live-urls.sh <base-url>
```

The deploy root and the base URL are the only host-specific values. A local run reads them from a file under `~/.secrets/`, one per environment, copied from [`.secrets/example.env`](./.secrets/example.env). CI passes the base URL and a scratch bundle path, then uploads the bundle to the host's deploy root. The real files live on the host, never in this checkout.

**The command-prefix form above is CI-only.** A local run whose default environment file exists sources it after the command-prefix assignment and overwrites it, since `set -a` overwrites a value the caller exported first. Locally, select the environment through `ENV_FILE` instead, as the two examples earlier in this section do.

**A VPS release is named by its deploy run, never by a commit.** The hub's deploy task names each release `<UTC yyyymmdd-HHMMSS>-<run id>-<run attempt>` and verifies the site against that id itself. To check a VPS site by hand afterwards, pass that id as `EXPECT_RELEASE`. Read it from the **Deploy site job**'s log, where `make-release.sh` prints `==> installing release <id>` with the id ending in the run's own id and attempt. The Validate sources job prints the same line earlier in the run, for a scratch bundle stamped with a bare timestamp, so the first match of a log search is the wrong id. Never copy it from the site's `X-Blog-Release` header, since a stale config still serves the previous id and the check would then pass against it. A short SHA never matches, so the check waits out its timeout and fails.

**Always set `SITE_BASE_URL` for anything that is not production.** The base URL is baked into the canonical tag, the feed links, and every absolute permalink, so a mirror built without it serves pages that all point back at the production address. Nothing downstream catches this, because the pages render at the right paths and the build gate passes. `make-release.sh` bridges it to Hugo's own `HUGO_BASEURL` internally, and the effective value is printed on every build for that reason.

**Never promote a staging build to production.** The base URL is baked into the canonicals, the feeds, and every absolute permalink at build time. A staging artifact served as production points every page at the staging host. Each environment's deploy builds its own release from the ref instead.

**The deploy workflow reaches only the VPS `staging` and `production` sites.** Dispatching it with `environment=staging` deploys `blog.vps.insanegenius.net`, never a local mirror. The two local mirrors are deployed from the maintainer's own machine with `make-release.sh` and nothing else. So "deploy staging" names two different targets depending on who says it. A run reporting that staging deployed says nothing about what a local mirror serves, so check the mirror itself.

**`make-release.sh` builds the working tree, not the commit.** Hugo reads the checkout as it stands, so an uncommitted file ships. The release carries whatever version you pass. The documented local procedure passes a commit SHA, and a VPS deploy passes its run-based id. It defaults to a timestamp when you pass nothing. A SHA then names a commit that does not describe what is served. `EXPECT_RELEASE` still matches, because it compares the stamp against itself rather than against the tree. Commit before deploying, or read the release id as a label rather than a description.

| Variable | Effect |
| --- | --- |
| `ENV_FILE` | Which environment file to source. Defaults to `~/.secrets/blog.local.production.env`. |
| `DEPLOY_ROOT` | Fallback deploy root. The first argument wins. |
| `SITE_BASE_URL` | Overrides the site base URL. |
| `REQUIRE_BROTLI=1` | Fails rather than shipping gzip-only. CI sets this. |
| `NO_LINK_DEST=1` | Full copy instead of hard-linking from the previous release. |

The script builds, verifies the URL contract, precompresses, installs, swaps, and prunes. It refuses to continue at each step rather than shipping a release that is wrong in a way nobody would notice.

### Rollback

Point `current` at the previous release. The swap is a single rename, so a request sees either the old release or the new one and never a half-written state:

```sh
ln -sfn "releases/<previous>" "<deploy-root>/.current.tmp"
mv -Tf "<deploy-root>/.current.tmp" "<deploy-root>/current"
```

The content reverts on the rename alone, because the container mounts the parent directory and the kernel resolves `current` per request. The rules follow on the watcher's next poll. A rollback is a config change like any other, and re-adapting re-reads the reverted release's `Caddyfile` and maps.

**Until that poll the reverted content is served under the newer release's rules.** That is the same window every deploy has, in the other direction. It is harmless while every rule is a redirect, since a stale redirect sends a visitor to a page that exists in both releases. It would stop being harmless if a rule ever *gated* content rather than redirecting it. At that point the flip has to become a restart again.

Verify with `EXPECT_RELEASE` set to the release being rolled back **to**, which is what proves the rules actually reverted rather than assuming they did.

Verify with `checks/check-live-urls.sh` against the environment before considering the rollback finished.

### Retention

Ten releases are kept at every deploy root, by two independent mechanisms that agree on the number rather than by one mechanism reaching both.

**On a local mirror, [`deploy/make-release.sh`](./deploy/make-release.sh) prunes as its last step.** Unchanged files hard-link to the previous release, so the static tree is stored once rather than ten times, and a release costs roughly the size of the generated output.

The script asserts both halves of that rather than assuming them. It fails when the prune leaves more releases than the limit, and when hard-linking produces no shared files at all. Both have failed silently before, and on a compressing filesystem the disk usage looks plausible either way.

**At a VPS deploy root, the host's `blog-prune-releases.timer` prunes and nothing in this repo does.** It runs daily and keeps ten release bundles per environment, and the release `current` resolves to is retained unconditionally without consuming one of the ten, so the live site survives even a misconfigured count. **Name the unit rather than the number**, because a second daily retention runs on the same host, `pangolin-backup.timer`, and it keeps fourteen encrypted config archives. "Ten, daily" identifies neither of them once it is read on its own. It orders by modification time rather than by name, because the release id is a caller-supplied argument and a label passed in place of a timestamp would sort wrongly and retire the wrong releases. It refuses outright, removing nothing, when `current` dangles or is not a symlink, since a broken `current` means the site is already serving nothing and guessing which release was meant to be live is the wrong move while it is.

**Nothing prunes on the deploy path, and that is what keeps the deploy key's capability small.** A prune racing a deploy could take the rollback target, where a lingering release only costs disk. This is also why the key needs no delete capability, which is the property "Server Hardening" depends on. The count and the timer belong to the host, so this section records what the host declares rather than holding a second copy of it. See "Who Owns What".

### Working With the VPS

**Every path and hostname on this page is a value in `~/.secrets/`, never a literal to be remembered or asked for.** The convention is the one "Environments" describes and `CAPTURE_ROOT` already follows: a value naming a machine rather than the project lives in the environment file, is sourced with `set -a`, and is read from there rather than searched for. The VPS values are environment-independent, because there is one such host rather than one per environment, so they sit in the default file alongside `CAPTURE_ROOT`.

```sh
set -a; . ~/.secrets/blog.local.production.env; set +a
ssh "$VPS_SSH_HOST" true && echo reachable
```

| Value | Names | Side |
| --- | --- | --- |
| `VPS_SSH_HOST` | the administrative login | the VPS |
| `VPS_TRAEFIK_LOG` | today's live access log, still being appended to | the VPS |
| `LOG_ARCHIVE_ROOT` | the off-host copy of the rotated logs | the backup host |

**There are two credentials to this host and picking the wrong one is the first mistake to avoid.** `DEPLOY_SSH_USER` is held per environment and used only by the deploy. It reaches a confined account behind an `rrsync` forced command that can write the release trees and read nothing else. `VPS_SSH_HOST` is the ordinary administrative login used for everything on this page. They are deliberately separate credentials with different blast radii. Reaching for the deploy account to read a log fails in a way that reads like an outage. Reaching for the admin account to deploy grants far more than the deploy needs.

**The off-host copy, maintained outside this repository, writes the rotated access logs to `LOG_ARCHIVE_ROOT`, and this section covers nothing more about it.** Its installation, how the VPS itself is provisioned, and its trust model are the backup host's own configuration to document, not this repository's. What "Logs and Debugging" needs from its schedule and copy behavior, to read the logs correctly, is covered there instead. Read the unit and its last run on the backup host rather than trusting a schedule written down anywhere, including here.

**`LOG_ARCHIVE_ROOT` is spelled the same way on both sides, so there is nothing to reconcile.** The pull writes it and the log review reads it, under the one name. Every value this repository reads or writes is described once, in [`ENVIRONMENT.md`](./ENVIRONMENT.md), and [`checks/check-env-docs.py`](./checks/check-env-docs.py) fails if one is declared without a description or described without existing.

```sh
set -a; . ~/.secrets/blog.local.production.env; set +a
ls -d "$LOG_ARCHIVE_ROOT"
```

**Today's traffic is never in the off-host copy, and that is deliberate.** Rotation is what makes a file eligible to be pulled, so a live log would be copied as a torn prefix and fetched again on the next run. An analysis covering today therefore reads `VPS_TRAEFIK_LOG` over SSH and everything older from `LOG_ARCHIVE_ROOT`, and treats the two as one series joined on `StartUTC` rather than on which file a line came from.

**What this section does not cover, and where it lives instead.** Reading the logs for content is "Logs and Debugging". The boundary of which side fixes what is "Who Owns What". What a rebuild restores, including the host-key step that blocks both deploy and rollback, is "Backup and Recovery".

### Server Hardening

The deploy account exists to receive a release and nothing else.

- The account is unprivileged and owns only the deploy root.
- Its key is restricted in `authorized_keys` with `restrict` and a forced command, so it cannot open a shell, allocate a terminal, or forward a port.
- **One key covers both environments**, rather than one per environment. Recorded here as a decision rather than an omission, because the opposite is the obvious default and this file asserted it until the two environments actually existed. A per-environment split pays off only where the two keys never share a machine, and here they would: both private keys sit on the maintainer's one workstation, and both secrets in one GitHub store, so whatever reaches one reaches the other. The split would buy a boundary that is already crossed everywhere it is held.
- **The forced command is therefore the only boundary left, and it is confined to the parent of both roots.** That is what a single key costs: `rrsync` pins a key to one directory, so the two deploy roots sit under one parent and one pinned command covers both. The roots are `/srv/blog/sites/production` and `/srv/blog/sites/staging`, and the confinement root is `/srv/blog/sites`.
- **The deploy workflow's ref gate is a security control rather than a tidiness check, and it is load-bearing for the same reason.** One key confined to the parent of both roots means a run's environment name, not a credential, decides which of the two trees it writes into. The two GitHub Environments hold separate secrets and separate variables, and that separation stops at the runner: whichever key is installed reaches both trees. So the gate refusing a production deploy from any ref but the default branch is the boundary the credentials do not draw, and it is dispatchable by anyone who can dispatch the workflow. Treat it as part of this list rather than as workflow housekeeping.
- **That parent holds content and nothing else, which is why it is not `/srv/blog`.** `/srv/blog` is the deploy account's home directory and contains `/srv/blog/.ssh/authorized_keys`. Confining the key there would let it rewrite the very file that defines what the key may do, and a `--delete` at the root would take `.ssh` with it. Confinement that encloses its own definition is not confinement. The extra `sites/` level is a security boundary rather than tidiness.
- Unattended upgrades run with automatic reboot, which is safe because the site is static and the swap survives a restart.

A deploy key that can write a release can already rewrite the site's Caddy config, because [`deploy/Caddyfile`](./deploy/Caddyfile) ships inside the bundle and the bootstrap imports it. Withholding the container's `/config` directory from the same key therefore protects nothing, which is why the bootstrap stays outside the deploy path for the reason given below and not for a security one.

### The Deploy Key

The deploy key is the one credential CI holds for the host. Each rule below covers a way it has gone wrong or could.

- **Generate the key on the maintainer's workstation, and send the host only the `.pub`.** The private half goes to the GitHub secrets and a vault, never to the server.
- **Keep a vault copy, because GitHub secrets are write-only.** A secret can be replaced but never read back. Without the vault copy, a lost workstation means rotating rather than recovering.
- **Rotation swaps one line, in an order that never breaks a deploy.** Add the new key as a second line with the same `restrict` and forced command. Replace the secret in both GitHub Environments, since one key covers both. Then delete the old line.
- **Test a revocation from the server's log, not from the client's message.** `Permission denied` also appears when the client fails to sign, for example with a mismatched key pair. The server then never verified a signature at all. Before revoking, confirm the test logs `Accepted publickey` for the deploy user. After revoking, confirm the same test reached sshd and logged no `Accepted publickey`. The key's fingerprint on a refusal appears only at `LogLevel VERBOSE`.

**The confinement is testable without the private key.** Running the forced command directly tests authorization apart from authentication. The shape is an `rsync -e` wrapper, which rsync calls with the host and then the remote command. The wrapper drops the host argument and runs `sudo -u <deploy user> env SSH_ORIGINAL_COMMAND="<the remote command>" <the forced command>`, with the forced command copied from `authorized_keys`. The `env` must follow `sudo`, because `sudo` scrubs the environment. An `rrsync error: Not invoked via sshd` means the variable never arrived, not that the guard held. Three results show the confinement holds:

- A write to each environment root succeeds.
- A path containing `..` is refused.
- An absolute path is remapped under the confinement root and fails on a missing parent, and `authorized_keys` checksums the same before and after.

Run a `--delete` check separately, by deploying after withdrawing a page. The write checks only overwrite existing files, so they pass with `--delete` broken.

**A transfer by hand with the key meets three client traps.**

- `-i` adds a key rather than replacing the others. An agent holding several keys reaches the server's attempt limit first, failing with `Too many authentication failures`. Pass `-o IdentitiesOnly=yes`.
- `IdentitiesOnly` still offers every `IdentityFile` a matching `Host` block adds, a `Host *` one included. Read `ssh -G <host>` to list them.
- `rsync -a` keeps the source mtimes, so an old mtime on the server is not a failed deploy. Read where `current` points instead.

## Backup and Recovery

What state exists outside git, and how each piece comes back.

**The deploy root needs no backup.** The site is reproducible from this repository by running the deploy again, so the only thing worth protecting on the server is its configuration: the container definition, the proxy configuration, the deploy account and its restricted key, and the upgrade schedule.

A bare-metal restore is therefore rebuilding the host, restoring that configuration, and running a deploy. Treat any procedure that backs up the deploy root as protecting a copy of something git already holds.

**A rebuild regenerates the host's SSH keys, and the deploy verifies them, so one step belongs to this side.** Cloud-init deletes and recreates host keys when the instance identity changes, and the deploy transport sets `StrictHostKeyChecking=yes` against a pinned `DEPLOY_SSH_KNOWN_HOSTS`, held per environment. A rebuilt host therefore presents a key the pinned value does not match, and every deploy fails closed until the value is replaced **on both environments**. That blocks the rollback path as well as the deploy path, at exactly the moment a rebuild makes both matter. Read the new fingerprint and update both environments before the first deploy that follows a rebuild.

## Logs and Debugging

Where the running site's own record lives, and how to read it without being fooled by it.

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
| Pangolin's request audit log, on the VPS only | which authorization decision the gate made, kept for 7 days | the status, headers, query, and user agent, so a request the gate rejected is read from Traefik's line for it instead |
| Caddy, per environment | path, status, and the `X-Blog-Release` that answered | anything the tiers above rejected, which never arrives |

**A 404 count taken from Caddy alone is therefore a floor, not a total.** A request the edge refused is a reader who found nothing just as surely, and it appears in no Caddy log. Read the edge for what never arrived and Caddy for what arrived and failed, and treat the two as one answer.

**`ServiceName` is what separates those two cases inside the edge log itself**, which is otherwise a distinction this table draws conceptually and leaves you no way to apply. A Traefik line carrying a service name was routed, so the 404 came from the site. A line with the field absent matched no router at all, so the edge answered and the site never saw the request. The second kind is the one Caddy is structurally blind to, and it is rare enough that it reads as noise in a total and is worth listing individually.

**When `ServiceName` is absent the edge answered, and `entryPointName` with `RequestScheme` say why**, which is the difference between a finding and a fault. The common cause is a cleartext request to the TLS port: the `websecure` router carries `tls` and therefore matches TLS requests only, so a plaintext request to 443 matches nothing and Traefik answers its own 404 with a body of a few dozen bytes. That is correct behavior rather than a gap, and it needs no action. Read the two fields together before treating a routerless 404 as a routing problem, because the shape that does deserve investigation is a routerless 404 arriving over **https**, which means a hostname the proxy serves no route for.

Two properties of the Caddy side are worth knowing before parsing it. Its access log is `format console`, so each line is a timestamp, a level, and a logger name followed by a JSON object rather than being JSON itself, and a parser that assumes one object per line reads nothing. And `trusted_proxies` is what makes `client_ip` the reader rather than the proxy, which is the same setting "Serving" describes as a security boundary. Without it every request in the log appears to come from one internal address, and the inward pass cannot distinguish a reader from a health check.

### Reading a 404 list without being fooled by it

The outward pass is four filters over the edge log, and each one exists because skipping it produced a wrong answer once.

**Exclude this repository's own deploy gate first.** `check-live-urls.sh` requests the whole URL contract on every deploy, so an unfiltered day is mostly a recording of our own `curl`. A count that omits this step is measuring the pipeline rather than the readers, and it will be an order of magnitude too large.

The mechanism is the `X-Blog-Check` request header, which the scripted checks send on every request they make, so `jq 'select(.["request_X-Blog-Check"] == null)'` is the filter. It is only as complete as the tagging is, which is the first bullet below. Its value is a source and an id rather than a boolean, so a run is identifiable rather than merely excludable. Real values look like `github/31322640628-1` from CI and `proxmox/media-dev` from here. Older lines also carry `vps/smoke`, sent by a host-side smoke script that is retired. The shape is enforced by `check-live-urls.sh`, which takes exactly one `/` and only letters, digits, `.`, `_`, `-`. A placeholder written with angle brackets is therefore a description rather than something to paste.

- **The field exists only because the edge is configured to log that header**, which is the host side's to hold and not this repository's. An absent field therefore has two meanings, an untagged request or a capture that stopped, and they are not distinguishable from the log alone. Confirm the capture is live before reading a day's absence as a day of real traffic.

- **A hand probe carries it only because whoever runs it adds it.** `check-live-urls.sh` sends it on every request and a bare `curl` sends nothing, so an interactive probe passes `-H "X-Blog-Check: proxmox/media-dev"`. The source half stays `proxmox`, which is where the probe came from, and the id half is where the purpose goes. Two untagged probes turned up against 3,100 tagged ones in the 2026-08-09 deploy window.
- **Absence is not proof of a human**, since a scanner sends no header either, so this pairs with the scanner-shape filters below rather than replacing them. The field is forgeable and must never reach auth, rate limiting, robots handling, or caching.
- **Before 2026-08-09 the log carries no such field**, and user agent is the only key for those days: on 2026-08-08, 9,285 of 9,996 requests were `curl/8.5.0`, leaving 711 real ones. That key is a coincidence rather than a rule, since the CI runner's curl and the host's are byte-identical and only the rotating client address separates them, which is why the header exists.
- **The header won over four alternatives, and each lost for a reason that still holds.** Other consumers read the user agent, and a runner image bumping curl would silently break a filter built on it. A query parameter pollutes the path, which is the analysis key, and collides with the `?p=` redirects. A source address fails because CI runner addresses rotate daily. A separate check hostname would exercise a different router and certificate, so the check would stop testing what production serves.

**A referer does not implicate this site unless it points somewhere else.** The rule worth applying is that a 404 carrying a referer is a broken link and a 404 without one is a typed or probed address, and it fails on scanners, which set `Referer` to the request URL itself. Every one of the 36 referer-bearing site-host 404s on 2026-08-08 was self-referential, so the unrefined rule reported three dozen broken links on a site that had none. Discard the matches before counting, and **normalize the scheme rather than comparing it**, because a scanner reaching an HTTPS site routinely sends an `http://` referer for the same address. Comparing against the request's own scheme therefore matches nothing and leaves every false positive in place: on the 2026-08-08 data the naive form kept all 36 where the normalized form kept none.

```sh
# Narrow to this site's own 404s, then keep only referers pointing somewhere else.
# No null guard is needed anywhere here: == and + both tolerate a null host. Swap the
# equality for startswith and one becomes mandatory, which is the trap described below.
jq -c 'select(.DownstreamStatus == 404)
  | select(.RequestHost == "blog.example.com")
  | select((.["request_Referer"] // "") != "")
  | select((.["request_Referer"] | sub("^https?://"; "")) != (.RequestHost + .RequestPath))'
```

Widen `== 404` to `>= 400` for the whole non-200 sweep the table above describes. The 404 list is the half with an action, which is why it is the default here.

**Filter the scanner shapes by shape, never by investigating them.** A site that used to run WordPress attracts probes for `.env` and its dozen variants, `wp-config.php`, `.git/config`, `phpinfo.php`, cloud credential files, and framework config paths. They dominate the raw list and none is ever a finding. What is left after the three filters above is small enough to read line by line, which is the point of running them.

**Then cross-reference what remains against the contract**, because that is the only step with an action. A surviving 404 whose path appears in [`checks/golden-urls.txt`](./checks/golden-urls.txt) or in [`deploy/maps/`](./deploy/maps/) is a redirect that is not working. A surviving 404 shaped like real content and present in neither is the case this whole pass exists to find, and it is added to the golden list with a redirect per that file's maintenance rules. A run where nothing survives is the expected result and should be recorded as one.

**A missing `Host` header is the third way this data breaks a filter.** `RequestHost` is null on a request that sends none, which router exploits do. String functions reject that where arithmetic tolerates it, so `.RequestHost | startswith(...)` fails with `startswith() requires string inputs` and takes the whole run with it, while `.RequestHost + .RequestPath` quietly yields the path alone. The failure is loud but partial, which is the worst combination, since it aborts part way through a file having already printed real output. Guard the string functions with `// ""`. Equality and concatenation both tolerate a null, so a guard on those is inert and reads as protection that is not there.

**Two `jq` mistakes each read as a plausible answer rather than as an error.** A hyphenated key parses as subtraction, so `.request_User-Agent` silently is not the field you meant and `.["request_User-Agent"]` is, and the same holds for `Referer`. And `jq 'select(...)'` with no projection pretty-prints each match across many lines, so piping it to `wc -l` counts lines rather than records and overstates by roughly the width of the object. It reported 37 and 1,332 where the true counts were 1 and 36. Project with `@tsv` or pass `-c` before counting anything.

### Retention Is the Prerequisite, and It Belongs to the Host

**On the VPS the reviewable record is Traefik's access log**, at `/var/log/traefik/access.log`, one JSON object per line, one line per request, across every hostname the host serves. `RequestPath` carries the query string, so the legacy `/?p=<id>` traffic is visible as itself. The log records only three request headers, which appear as the keys `request_Referer`, `request_User-Agent`, and `request_X-Blog-Check`, and omits the rest from the record rather than stripping them from the request, which still arrives intact. That omission is what keeps the Pangolin resource access token out of a file that is retained and copied, and query strings are logged in full, so treat an extract as sensitive. That keep-list is the host's to hold and is the precondition the outward pass depends on: a header absent from it does not appear in the log at all, which is indistinguishable from a request that never sent one.

**That log rotates and is eventually deleted, on a schedule the host sets and can change.** The window is long, and it is finite, so anything the inward pass depends on has to be copied off the host before the archive ages out. Read the current retention from the host rather than from this file, because a number written here is a number nothing checks.

**Caddy's container log is the runtime log rather than the access log**, bounded by the container's own log rotation. It is where a failed config load and a dead `--watch` surface. It is not durable across a container recreate, since the Docker `json-file` log lives under the container id, and an operator editing the compose file is the event that discards it. A release deploy is not: an rsync and a symlink flip run no Docker operation at all.

**Release attribution comes from a join rather than from a header.** Traefik cannot log a response header, so no access-log line names the release that answered. Join `StartUTC` against the release flip instead, which is exact outside a deploy window and ambiguous only inside one.

**Retention on the local mirrors is a different question and is unsolved.** Those containers use Docker's `json-file` driver with the built-in defaults, so a mirror's log grows without bound and is discarded when its container is recreated. That matters less than it did on the VPS, because the mirrors serve no readers, and it belongs to the host rather than to this repository, the same split "Retention" and "Who Owns What" describe for release pruning.

**The off-host copy of the access log exists, and the schedule that maintains it is younger than the copy.** The pull to the backup host is installed as a `systemd` timer running daily at 09:00 UTC, chosen to sit behind both producers on the VPS rather than beside them, and its first copy was made by hand rather than by the timer. Read the unit and its last run on the backup host rather than trusting this paragraph, for the same reason retention is read from the VPS: a claim about a schedule is only worth what the machine says.

**A rename on the VPS does not propagate to that copy, and nothing reports the divergence.** The pull passes no `--delete` for the logs, deliberately, since an append-only record must never be removed by a transfer. So a file **the VPS** renames, merges, or re-compresses after it has been pulled keeps its old name **on the backup host** forever, alongside the new one, and a count that walks that archive by filename double-counts the overlap. This has already happened once, to two archives whose names were a day ahead of their contents. **Read a date from a line's `StartUTC` rather than from the filename that holds it.** The reconciliation itself now travels with the data: the VPS keeps an append-only `RECONCILE.md` **inside the archive directory**, so the pull carries it automatically and a rename does not depend on someone rereading a channel file. It records what a file contained rather than what it was called, and it is counted among the pulled log files. **The VPS keeps a `MANIFEST.txt` in the same directory**, so expect the count to exceed the number of logs by two rather than by one, and expect any further explanatory file the host side adds to raise it again. Read the count as logs-plus-prose rather than as a number with a fixed offset.

**A journal with one entry is not evidence of one copy.** The pull can be run directly as well as by its timer, and a direct run writes no service record. Directory mtimes on the backup host are the copy times, where the file mtimes are the VPS's, so those are what to read when establishing when something arrived.

## Tool Usage

The tools this repository's operations reach for, and the behavior of each that is not obvious from its help text.

### Checking a Site Behind the Auth Gate

Staging keeps Pangolin's authentication on, so an unauthenticated request never reaches the site. `check-live-urls.sh` presents a Pangolin resource access token when both halves of the pair are set, and sends nothing when neither is:

```sh
set -a; . ~/.secrets/blog.vps.staging.env; set +a
checks/check-live-urls.sh "$SITE_BASE_URL"
```

The gate is the VPS staging environment's, so this is `~/.secrets/blog.vps.staging.env`. The local staging mirror sits behind Traefik on the maintainer's own network and carries neither half of the pair.

| Variable | Header |
| --- | --- |
| `SITE_AUTH_TOKEN_ID` | `P-Access-Token-Id` |
| `SITE_AUTH_TOKEN` | `P-Access-Token` |

Set both or neither. Half a pair is a typo rather than a choice, and it is rejected as one rather than presented as a failing site. A pair is also refused unless its base URL starts with a lowercase `https://`, since a token sent over plain HTTP travels in the clear.

Three properties of how the credential is handled, each there for a reason worth keeping:

- **It travels in a mode-`600` curl config file, not in `-H` arguments.** A command line is readable in `ps` for the life of the process, and this runs one per URL in the contract. The config file is also the only form that survives the `export -f` the parallel checks run under, because bash cannot export an array.
- **It is sent to the base URL's own origin and nowhere else.** The check follows every redirect's destination, and every destination in the contract is same-origin today. A rule that one day points off-site must not mail the credential to whoever is on the other end.
- **A preflight request runs before the rest.** Behind an auth gate a wrong token fails *every* URL, and the output then reads as a site that has vanished rather than as a bad credential. The two are indistinguishable from the far end of a CI log, so the run stops on the first request with a message naming which of the two it was.

The family site's staging host sits behind a gate of its own. A Pangolin token opens exactly one resource, so the blog's pair gets the login page there. The same run checks the family site when `SITE_EXTRA_BASE_URL` is set, sending a second pair to that origin alone:

| Variable | Header |
| --- | --- |
| `SITE_EXTRA_AUTH_TOKEN_ID` | `P-Access-Token-Id` |
| `SITE_EXTRA_AUTH_TOKEN` | `P-Access-Token` |

The family token is created with Pangolin's session persistence off. The check sends both headers on every request and keeps no cookie, so a persisted session would only hand a cookie to nobody. The token never goes in the `p_token` query parameter. Pangolin answers that form with a redirect and a session cookie rather than the page, and the proxy's access log records the query. The family pair gets neither the preflight nor redirect following. Its three pages are requested after the URL contract. A wrong family token therefore surfaces at the end of the run, as a `302` on each page. Where `EXPECT_SITE_ENV` is set, each family page must also report that `X-Blog-Env`, and where `EXPECT_RELEASE` is set, that `X-Blog-Release`. The deploy workflow runs this part too, from the values [`ENVIRONMENT.md`](./ENVIRONMENT.md#the-github-environments) lists, and a local run does from any environment file that sets `SITE_EXTRA_BASE_URL`.

## Configuration Layout

What this repository holds, what the host holds, and which side owns each piece.

### Environments

Four environments, in two pairs. Each pair is one publish site and one staging site, and the local pair exists to rehearse the remote one.

| Environment | Address | Fronted by | Purpose |
| --- | --- | --- | --- |
| Local publish mirror | a private hostname, set in `~/.secrets/blog.local.production.env` | Traefik, on the maintainer's own network | Proves the artifact. The redirect rules, the maps, and the release mechanics. |
| Local staging mirror | a second private hostname, set in `~/.secrets/blog.local.staging.env` | Traefik | Proves that two environments on one host stay independent, before that matters on a server. |
| Staging | `blog.vps.insanegenius.net`, behind the auth gate, set in `~/.secrets/blog.vps.staging.env` | Pangolin | Proves the infrastructure. Routing, TLS, and the deploy path. |
| Production | `blog.insanegenius.com`, set in `~/.secrets/blog.vps.production.env` | Pangolin | The public site, per [Current State](#current-state). |

The local mirrors are not staging. They run the same bundle against the same web server, so they catch a broken redirect or a bad permission for free, but they exercise none of the routing, authentication, or certificate machinery that only exists on the VPS. Passing locally says the artifact is right. It says nothing about whether the server in front of it is.

**The two words are `production` and `staging`, spelled out, in every position.** No `prod`, no `stage`. The same two name the container, the deploy root, the environment file, the `X-Blog-Env` value, and the GitHub Environment. This is not tidiness: the environment name is a value that gets **compared**, by `EXPECT_SITE_ENV` and by the deploy, so a spelling that differs in one position fails a deploy for a reason that reads like an outage. The local mirrors prefix the same words, `mirror-production` and `mirror-staging`, so a header names exactly one of the four environments in the fleet.

Each environment is one file under `~/.secrets/`, named `blog.<server>.<environment>.env`, selected with `ENV_FILE`, and holding the deploy root, the base URL, and the container name. The name carries both halves because the two pairs differ in server as well as environment, so a file says which machine it describes rather than leaving that to the value inside it, and the four in the table above are the four files. `~/.secrets/blog.local.production.env` is the one read when `ENV_FILE` is unset. Selecting the file is how an environment is chosen: the file is sourced with `set -a`, so it overwrites a `DEPLOY_ROOT` the caller exported and setting that variable by hand does not switch anything. A named file that does not exist is a hard failure rather than a fall-through, because on a host serving two sites the ambient value is the other site's root.

**The staging FQDN sits under the VPS wildcard deliberately.** `blog.vps.insanegenius.net` needs no new certificate and no new DNS record, and it keeps the staging name off the production domain.

**Staging keeps its auth gate on.** It serves a byte-identical copy of the public site, so exposing it publicly would hand every crawler a duplicate of a site whose entire migration risk is URL preservation. `checks/check-live-urls.sh` gets through with a Pangolin resource access token instead. See [Checking a Site Behind the Auth Gate](#checking-a-site-behind-the-auth-gate).

### The Release Bundle

A release is self-contained. The site, the web-server config, and the redirect maps travel together:

```text
<deploy-root>/
  current -> releases/<version>        relative symlink, swapped atomically
  releases/<version>/
    site/        the built site, precompressed
    Caddyfile    the redirect rules
    maps/        p-ids, slugs, blogger, labels, terms
    family/      the viljoen.family page, precompressed
```

Shipping the config inside the release is what makes a rollback honest. The rules and the content they refer to move as one, so reverting cannot leave the previous site being served by the current release's redirects.

`current` is a **relative** symlink. That frees the host path, so one bundle works at whatever root each environment mounts, with no rewriting.

### The URL Contract

This site has served the same domain across earlier platforms, so its whole operational risk is silent URL loss. Everything below exists to make that risk visible.

**The contract is ground truth.** [`checks/golden-urls.txt`](./checks/golden-urls.txt) and [`checks/redirect-urls.txt`](./checks/redirect-urls.txt) record URLs verified with a live request, not predicted from the content tree. The lists are **append-only**: nothing legitimately removes a URL the site has served, so a change that would drop one is a change to reject rather than a list to shorten. A list-driven check also carries a length floor, or a truncated list passes while checking almost nothing.

### The Migration Record

**The procedure and the facts live in the directory READMEs.** [`capture/README.md`](./capture/README.md) is the authority on how the inputs were captured and what is derived from them, [`checks/README.md`](./checks/README.md) on the URL contract, and [`deploy/README.md`](./deploy/README.md) on how the redirects are expressed. Each sits beside the thing it describes, which is what keeps it true.

**The migration also has an account of itself, as a post on the site.** It is the casual version, what was done and how it went, and it is worth reading before changing anything under [`checks/`](./checks/) or [`deploy/maps/`](./deploy/maps/), because those hold values that no code derives.

**The direction between them is one-way.** A post may cite a README. A README never cites the post. A doc that sends a reader to published prose for an operational fact has put the fact where it cannot be kept current, and where correcting it means editing something people have already read.

**The post is content, so it sits under the URL contract.** Editing it moves nothing. Renaming it or taking it down breaks an address the site serves. A fact in it that proves wrong is corrected in the post rather than footnoted here. [`CONTENT.md`](./CONTENT.md) holds that rule for every post, along with where a post goes, what its front matter carries, and how it is written.

#### Rebuilding from the Exports

Everything derived is in this repository. Everything it was derived *from* is a capture directory outside it, at `CAPTURE_ROOT`, which is where a rebuild starts. The capture is not a git repository, so it has no history to revert to, and it is read-only in normal use.

**[`capture/README.md`](./capture/README.md) holds the procedure**: what is under the capture and which parts of it can be fetched again, the two exports and the counts they must reconcile against, the ordered rebuild, and the results that look like success and are not.

### Serving

Caddy serves the bundle and binds an internal port only. TLS and the public listener belong to the proxy in front of it, so `auto_https off` and `admin off` are deliberate.

The container mounts the deploy root **read-only**, and mounts the **parent** rather than `current`. Docker resolves a symlink at container-creation time, so mounting the symlink pins the container to whichever release was live at startup and every later deploy stays invisible until the container is recreated.

Routing differs by environment and the bundle does not. Traefik on the home host has the Docker provider enabled, so container labels route. Pangolin's Traefik on the VPS does not, so routing there is created in the Pangolin UI and labels are silently ignored.

**Each environment is its own container with its own deploy root**, rather than one server addressing several roots. That is what keeps the bundle's config internal: the Caddyfile inside a release names `/srv/blog/current`, one root, and knows nothing about a sibling. A single server covering both would have to name both roots in a config held outside either bundle, and that config could not then roll back with the content it serves. Both containers bind the same internal port and are told apart by hostname, which the proxy in front resolves.

That last sentence is also the risk. **The container is the only thing that distinguishes one environment from another**, so a proxy rule aimed at the wrong one serves the wrong site under the right hostname and returns a healthy `200` with nothing logged anywhere. The bundle stamps `X-Blog-Env` and `X-Robots-Tag` from container variables so a response says which environment produced it, and `checks/check-live-urls.sh` fails on a mismatch when `EXPECT_SITE_ENV` is set. [`deploy/README.md`](./deploy/README.md#identifying-the-environment) carries the mechanism and, more importantly, why `SITE_ROBOTS` defaults to `index, follow` rather than to the safer-looking `noindex`.

Caddy also sets `trusted_proxies`, because a proxy fronts it in every environment and the peer address is therefore always the proxy. Without it the access log records that one internal address as the client for every request the site serves, and `X-Forwarded-For` is ignored rather than trusted. The ranges come from the container, since the same bundle runs on hosts whose docker subnets differ. **Exclude the bridge gateway from whatever range is trusted**: it is inside the subnet and it is how the host itself reaches the container, so trusting the subnet trusts every process on the host. Verified on the home mirrors by forging a header from the host, which succeeded until the gateway was excluded. **Trusting a range means believing `X-Forwarded-For` from anything in it**, so it is a security boundary rather than a formality, and the bundle's RFC1918 default is only correct where a proxy is genuinely the only thing that can reach the port. [`deploy/README.md`](./deploy/README.md#trusting-the-proxy) carries the three behaviors and why binding to `127.0.0.1` does not make direct access impossible.

#### The bootstrap, and why it is not in the release

The container reads three host paths, and only one of them a release ever writes:

| Host path | Mounted at | Written by |
| --- | --- | --- |
| `$DEPLOY_ROOT` | `/srv/blog`, read-only | every release |
| `$CADDY_APPDATA/config` | `/config` | placed once, by hand |
| `$CADDY_APPDATA/data` | `/data` | Caddy itself, persisting state across a recreate |

[`deploy/bootstrap.Caddyfile`](./deploy/bootstrap.Caddyfile) goes in the `config` directory and is the **only** Caddy file outside the release bundle. It carries a single `import` and no rules of its own, deliberately: everything describing the site ships inside the release, so a rollback reverts the rules and the content together. Rules held here instead would leave a rolled-back site being served by the current release's redirects.

Because it sits outside the bundle, no release updates it. Install or refresh it explicitly, once per environment, which is the same command against a different sourced file:

```sh
set -a; . ~/.secrets/blog.local.production.env; set +a   # or any other ~/.secrets/blog.<server>.<environment>.env
install -m 644 deploy/bootstrap.Caddyfile "$CADDY_APPDATA/config/Caddyfile"
docker restart "$CADDY_CONTAINER"   # only this file needs one, see below
```

**A container started before its environment has a release restart-loops**, because the bootstrap imports a path that does not exist yet. Create the directories, install the bootstrap, cut the first release, and start the container in that order. The container definition can also be held disabled until the release exists, which is the same fix from the other side.

**This is the one file whose change still needs a restart**, and the reason is a nice inversion of why everything else does not. The watcher polls `/config/Caddyfile` and reloads when the *adapted result* changes, which is how a release reaches it at all: this file never changes, but re-adapting re-executes its `import` and picks up the new release behind it. Editing this file itself is the case the watcher handles worst, because a bootstrap that no longer parses leaves nothing to reload into. Restart, and read the log.

Everything inside the bundle, `deploy/Caddyfile` and anything under `deploy/maps/`, reloads without one. See "Local Verification" above.

`CADDY_APPDATA` is recorded in each environment's file for exactly this reason. No script reads it, so a rebuild would otherwise depend on someone remembering where the bootstrap goes.

### Redirects

The site answers far more addresses than it renders, satisfied by a small set of `redir` directives and the map files they read, all inside the bundle. [`deploy/README.md`](./deploy/README.md) carries the per-class breakdown and the counts. This section covers the operational shape only, so the two do not restate each other.

Ordering is load-bearing, so every redirect lives in a single `route` block. Outside one, Caddy sorts directives by its own precedence rather than by file order, and the broad attachment rule claims the per-post comment feeds that the narrower rule must match first.

| Class | Mechanism |
| --- | --- |
| Attachment pages and per-post comment feeds | Two rules, the longer pattern first |
| Term feeds, date archives, author archives | One rule each, to the term, the archive index, or the home page |
| Legacy media paths | One rule, mapping the old upload prefix onto the current media tree |
| Blogger permalinks, pages, feed, and monthly archives | Rules plus `blogger.map` |
| WordPress shortlinks | `p-ids.map`, keyed on the query string |
| Bare attachment slugs, root files, and retired pages | `slugs.map` |
| Blogger label archives | `labels.map`, defaulting to the archive index |
| Term archives the generator does not build | `terms.map` |

The maps are generated by [`capture/build-redirects.py`](./capture/build-redirects.py) and the generated files are committed, so a deploy never regenerates them. How it selects its input, and why that selection is the part to get right, is in [`capture/README.md`](./capture/README.md).

### The Family Site

The bundle also carries `viljoen.family`, a single static page whose source is [`sites/viljoen.family/`](./sites/viljoen.family/). `make-release.sh` copies it to `family/` beside `site/`, leaving out its README, and precompresses it the same way. It shares the release, the containers, and the rollback with the blog, so a family change ships as a blog release.

A second site block in `deploy/Caddyfile` serves it on the same port, selected by the `Host` header the proxy forwards. Any other hostname falls through to the blog's `:8080` block, so the blog's redirects never answer on the family host. The family block carries its own security headers and CSP, and answers a missing path with the page itself at a `404` status. It also routes the page's two languages: `/` redirects to `/af/` for a browser whose first language is Afrikaans, while `/en/` and `/af/` never redirect.

Two container variables belong to it, both part of the [container contract](./deploy/README.md#container-contract). `FAMILY_SITE_ROBOTS` sets the family site's `X-Robots-Tag` apart from the blog's `SITE_ROBOTS`, for the reason given in [Identifying the environment](./deploy/README.md#identifying-the-environment). `FAMILY_SITE_ADDRESS` adds a local mirror's private name, per [Serving the family site on a local name](./deploy/README.md#serving-the-family-site-on-a-local-name).

**A rollback to a release older than the family block drops it.** Every hostname then reaches the blog block, so `viljoen.family` serves the blog until a release carrying the block is live again. On production that copy is indexable. A production rollback to a release that predates `FAMILY_SITE_ROBOTS` stamps the family site with the blog's `SITE_ROBOTS`. That deindexes it whenever the blog holds `noindex`. A local mirror rolled back to a release that predates `FAMILY_SITE_ADDRESS` loses its private family name, which then serves the blog.

| Hostname | Reaches |
| --- | --- |
| `viljoen.family` | The production container |
| `viljoen.vps.insanegenius.net` | The staging container, behind the auth gate |
| The private names in a local mirror's `FAMILY_SITE_ADDRESS` | That local mirror |

Pointing these names at their containers is the host side's work, per [Who Owns What](#who-owns-what). So are the DNS records, the certificates, and the redirects that send the family's other domains to `viljoen.family`, and the host side documents them.

### Who Owns What

The site and the server it runs on are maintained separately, so the boundary is written down rather than inferred. This repo owns the artifact and what proves it correct, and the host owns where a release may be written and what happens to it afterwards.

| This repo | The host |
| --- | --- |
| The GitHub Actions workflow | The SSH endpoint and its forced command |
| `deploy/make-release.sh`, the bundle layout, and the Caddyfile inside it | The bootstrap `import`, the containers, and their environment variables |
| `checks/check-live-urls.sh` and the URL contract | Config-watchdog and release-prune timers |
| The release id and the `@@RELEASE@@` stamp | Proxy resources, routing, tokens, TLS, DNS, and redirects from other domains |
| What a release contains | Where a release may be written, and what happens after |

The two meet at the container contract in [`deploy/README.md`](./deploy/README.md#container-contract). A defect on the host side is fixed on the host. A pipeline that needs the contract to say something different asks for a contract change rather than growing a second copy of the other side's work.
