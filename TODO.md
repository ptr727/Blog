# TODO

Running backlog for this repo, kept in a committed file so the work survives across sessions. How the migration was done is a [post on the blog][migration-post] rather than a section here.

## State

The site is built, gated in CI, and deployed to staging by pipeline. It is not yet serving its public address.

| Piece | State |
| --- | --- |
| Content and media | done. Carries every migrated post and page, with the media hash-verified against the export tar |
| Media integrity | closed for the files themselves. The conversion's only loss was 19 images, inside five galleries, restored from the capture, and the 98 files with no page links are adjudicated rather than unknown, with `ORPHANED_MEDIA` failing if that count moves either way. How media was *presented* was a separate loss, found later and now gated |
| URL contract | done. 328 render, 917 redirect, 778 legacy image URLs, all gated |
| Deploy shape | done. Proven on two local mirrors and on the VPS, by hand and by pipeline |
| CI workflows | green. Validation runs on every pull request and feeds the required check |
| GitHub repo | public, both rulesets active, `configure.sh check` exits 0 |
| Release pipeline | proven end to end. `1.0.17-g4b2def3ee9` is the newest, a prerelease from `develop` |
| Fleet conformance | cataloged in the hub registry, audited, and carrying the current canonical |
| Deploy pipeline | `deploy-site.yml` is dispatchable and has deployed staging from CI end to end, through a transport retested against the real host |
| VPS staging | live at `blog.vps.insanegenius.net`, behind the auth gate, serving a pipeline release |
| VPS production | **M7a done 2026-08-08.** Serving release `20260808-041050` at `blog.insanegenius.net`, answering `200` unauthenticated, verified 9/9 from the host side with the built `baseURL` read from the deployed bytes. DNS for the public name is still on the old platform |
| Operations | not started. Neither the periodic log review nor the off-host log pull has run on its cadence |

## Blocked on the maintainer

- Install `shellcheck`, `shfmt`, `nodejs`, and `npm`, then `markdownlint-cli2` and `cspell`, so the lint gate can run locally instead of only in CI. Every one of them currently runs here through Docker, which works but is slower than it should be for an edit loop.
- Read the migration post before it ships, since it is written in the maintainer's voice and has not been reviewed.

## Next, in dependency order

- **Prove a rollback through the pipeline.** A forced mid-deploy failure, then a flip back to the previous release, verified by `EXPECT_RELEASE` rather than by the transport exiting zero. The server side has been measured at well under a second by hand; what is unproven is that a **pipeline** run leaves the site serving when its deploy fails part way.
- **Production is deployed, which the VPS agent calls M7a, done 2026-08-08.** `blog.insanegenius.net` serves release `20260808-041050`, answering `200` unauthenticated on a Let's Encrypt certificate issued 2026-08-07. The host side verified it independently, 9/9 unauthenticated with the built `baseURL` read from the deployed bytes rather than from this repo's config, across a 3,095-request gate run with no unexplained 404s. What remains is **M7b, the `.com` cutover**, and the sub-items below are where this repo stands against it, two of them owed and one already answered. The VPS agent's §19, §20, §23 and §24 carry the detail and that file is not in the repository, so pull it first per [`OPERATIONS.md`](./OPERATIONS.md) "The Channel Between the Two Sides":
  - **`HUGO_BASEURL` on the `production` environment is set to `https://blog.insanegenius.net/`**, done 2026-08-07. It held `https://blog.insanegenius.com/`, the live WordPress address, which is what the workflow both builds with and points the live check at, so a deploy would have baked the old platform's address into every canonical tag, feed link and `sitemap.xml` and then run 1,245 requests at the live site to verify it. **Setting it back to `.com` at M7b is the other half and is not done.**
  - **Production emits `X-Robots-Tag: noindex, nofollow` for the length of the rehearsal**, deliberately, because `.net` serves a public duplicate of a live site and Certificate Transparency publishes the hostname. Where a check asserts `index, follow`, make the expected value a parameter rather than flipping a literal, since it reverts at M7b and a hardcoded literal is one more thing to remember at the wrong moment.
  - **The two questions in §19.3 are answered.** `HUGO_BASEURL` holds the interim `.net` name, per the item above. Exactly one place hardcodes `blog.insanegenius.com`: `baseURL` on line 1 of `hugo.yaml`, which is the production default every environment overrides through `HUGO_BASEURL`. Nothing under `checks/`, `deploy/`, `layouts/`, or `.github/` carries it.
- **Decide what `robots.txt` says, now before the cutover rather than before the first deploy.** Production answers 404 for it, so `X-Robots-Tag` is the only thing keeping the interim hostname out of an index. Crawlers are already asking: OAI-SearchBot, ClaudeBot, GPTBot, and Scrapy each arrived within three hours of the certificate being issued, at a hostname with no inbound links.
  - **The deploy did not fix the 404, which is the part that reads the wrong way round, and is now measured rather than predicted.** The VPS agent raised this in §22.10 and asked two questions of this side. Both are now measured rather than assumed: **this site emits no `robots.txt` at all**, because `hugo.yaml` sets no `enableRobotsTXT`, so the 404 survives the deploy and `X-Robots-Tag` stays the only control. **`sitemap.xml` is emitted** and becomes fetchable on the interim name at that same deploy, listing whatever `HUGO_BASEURL` was built with, which is the second reason that variable mattered. Read together: after the rehearsal deploy a crawler gets a full sitemap and no robots file.
  - **At the cutover this stops being a gap and becomes a loss, which is the half neither side had checked.** The live `.com` blog **serves a `robots.txt` today, carrying a `Sitemap:` line**. Since this site emits none, M7b is not a return to a previous state, it is a move from having crawl directives to having none on a site that has had them for years, and the sitemap pointer goes with them. The VPS agent measured this from the outside in §23.3, will not put a file in this repository's bundle, and has made it a decision that blocks step 1 of the M7b checklist rather than one discovered after it. The minimum that preserves today's behavior is `User-agent: *`, no `Disallow`, and the `.com` sitemap line, since every `Disallow` the old platform serves names a WordPress path this site does not have. **Deliberately undecided**, and the three options are to preserve today's behavior, to write what this site actually wants, or to keep emitting nothing and accept the loss.
- **Nothing checks that media survived the trip to the server.** The VPS agent noticed in §24.3 that a 3,095-request gate run fetched no image at all, and asked whether `golden-media-legacy.txt` is wired in. It is, but only at build time, in `check-url-parity.py`, against files on disk. The live check requests pages and redirects and never an image, so a media tree lost **between the build and the server**, a partial upload, is caught by neither: the build passed before the loss and the live gate never asks. On a site whose value is eighteen years of posts with images in them, that is the gap worth closing rather than the one that was suspected. A handful of media URLs in the live check would close it, chosen to cover both trees rather than to be exhaustive, since the build gate already proves the set.
- Lower the `blog` A-record TTL to 60s a day ahead, then flip it to the VPS, unproxied.
- **Publish a release from `main`, once the pipeline has soaked.** `1.0.11` is the newest release from `main` and was cut on 2026-08-01, ahead of every deploy change, so the next one is the first that would describe a site actually serving its public address. The mechanism is proven and is not what this waits on: it waits on the switchover being trusted rather than merely green, which is what the log review under **Recurring operations** establishes and no gate can. A release cut before that names a state that has not held yet.
- Add the weekly non-blocking external-link-check workflow, which is the one gate that cannot be blocking because it fails on other people's outages.
- Decommission WordPress.com only after **30 clean days**, and downgrade to free rather than deleting, which keeps the media reachable as a safety net and preserves the ability to re-export. Do not start sooner: the conversion fetched media over HTTP from the live site.

## Recurring operations

**Everything above ends; this section does not.** The list above finishes when the site serves its public address, and these two start there and never stop. Both are written down as procedures and neither has run on its cadence yet, which is the shape a recurring duty has right before it silently becomes a one-off. An end-to-end exercise of this system is a deploy **plus** the operations that follow it, so a run that proves staging and production and stops has proven the half that has an obvious finish line.

- **Review the logs for non-200s**, daily for the first week after cutover, then monthly. Real traffic finds what the golden list missed and the crawl that produced the list cannot. Append anything new to `checks/golden-urls.txt` and add a redirect. Read the edge as well as Caddy: a request the proxy refused never reaches the site's log, so a count taken from Caddy alone is a floor, and a staging probe for `/wp-login.php` answered by the auth gate rather than by the site is the shape of what Caddy never sees. The procedure, the three tiers and what each is blind to, and the inward pass that names content nobody has ever requested are in [`OPERATIONS.md`](./OPERATIONS.md) "Log Review".
- **Pull the log off the VPS, on a schedule**, which is [#53][issue-53]. The access log is deliberately outside the nightly encrypted archives, because those are fourteen full copies with no dedupe and an append-only file would be multiplied by fourteen for no recovery benefit. So the VPS's 400-day window is the **only** copy until this runs. The two rsync lines are now written, parameterized, and tested against the live host, and they are not installed, because installing needs root. **Until they are, say plainly that "backed up" describes a design rather than a fact in anything built on top of that log.**

## Owed to the hub

Nothing. The spec update this repo owed the hub has landed: [ProjectTemplate#560][hub-type-pr] authored the `hugo` type, the `self-hosted` target, the `deploy-ssh` mechanism, guarantees D4.6 and D5.6, and a reference leaf pair, all measured from what this repo actually runs rather than from the prediction the intake carried. [#456][hub-issue] and [#558][hub-spec-issue] are closed with it.

**It is on the hub's `develop` and not on `main`, so it is not ground truth yet.** The registry entry that reclassifies this repo to `types: ["hugo", "source-only"]` with both publish targets sits on the same unpromoted branch. Until the hub promotes, this repo stays `source-only` for audit purposes, and the anticipatory evaluation of the nine `hugo` checks is in [the audit report](./reports/Blog/audit.md).

Two things become due at that promotion, neither of them work this repo can do first:

- The two `driftNotes` the hub's registry carries for `hugo.vendored.provenance` and `hugo.generator.pinned` describe work [#30][pr-30] already finished, so they are reconciled away rather than carried. Filed as [ProjectTemplate#563][issue-563], with the measurement that nothing retires them mechanically despite the intent to: the freshness check is gated on a repo having no findings at all, and this repo has one it cannot clear.
- This repo's [`spec/secrets.json`](./spec/secrets.json) note states `types: ["source-only"]` in prose and needs the second type once the registry declares it.

The reference leaf the hub now ships carries one step this repo's deploy does not, a prune of the remote release tree. That is the corrected form of the check rather than a gap here: this repo's credential cannot observe the destination, so the leaf's own comments say to delete the step and record the ownership on the host side, which is what the entry above tracks.

## Open decisions

- **Where the operational tooling lives, given that today it lives nowhere.** `vps-backup-pull`, its `systemd` units, and the environment variables naming both ends of the copy are an operational asset built from another agent's instructions, and they exist only on the Proxmox host. That host is the machine the backup runs *from*, so losing it loses both the copies and the means of making them, and the instructions that produced them are in a channel file this repository deliberately does not carry. Two candidate homes, and the choice is open: **here**, beside the deploy tooling the same host runs, or **the home-automation config repository**, with the rest of that host's configuration. The argument for the second is that nothing about the pull is specific to this site; the argument for the first is that [`OPERATIONS.md`](./OPERATIONS.md) "Log Review" is the thing that stops working without it.
  - **The same question covers the migration toolchain in the capture directory**, which is fourteen scripts: the `wp2hugo` run, the content restructure and clean passes, external-media localization, the crawl and mirror, the golden-URL build, and the media inventory. Some are worth keeping only if generalized, and some are cheaper to rewrite than to maintain, so this is a per-script call rather than one decision.
  - **One of them is already three copies with two of them stale**, which is the concrete version of this risk rather than a hypothetical one. `build-redirects.py` exists at the capture root, again under the capture's own `checks/`, and here at [`checks/build-redirects.py`](./checks/build-redirects.py). The two capture copies are identical to each other at 115 lines; the copy in this repository is the maintained one at 225. Nothing detects that, because the capture is not a git repository and is read-only in normal use.
- **What `robots.txt` says, which is undecided and is the last non-mechanical item before M7b.** Recorded under "Next" above, where it blocks the cutover.
- `/robots.txt/` and `/osd.xml/` currently sit in `slugs.map` pointing at `/`. The first would be better pointing at the real `/robots.txt`.
- Content is capped at a fixed 720px on every screen, because PaperMod's width is four CSS variables with no responsive term and no Hugo parameter. The prose measure is right and should stay; images and galleries inheriting the same cap is the part that costs something on a wide display. The knobs, the override location, and the `--gap` trap are documented under "Customization points" in [`themes/README.md`](./themes/README.md).

## Deliberate deviations from the fleet baseline

Both are recorded in [AUDIT.md](./AUDIT.md) and reported to [ProjectTemplate#456][hub-issue], so neither reads as drift later.

- `lineEndings: "lf"` on a `release` repo, where the rule grants the native-platform default to operational repos only. Every consumer here is Linux.
- `types: ["source-only"]` rather than the `docs` the hub proposed, because both `docs` predicates are false for a repo that builds a site and gates a URL contract.

## Hub conformance, and what is open against the hub

Reconverged 2026-08-05, and the run is written up in [`reports/Blog/audit.md`](./reports/Blog/audit.md). This repo is cataloged in [`registry/repos.json`][hub-registry] and the hub authored [`reports/blog/audit.md`][hub-report]. Before that it was in no registry, so no hub tool had ever measured it and the fleet ledger under-counted by exactly this repo.

**Measured against hub `main` `3b802b9eb9a841c0149d018f4db6ffa1b9419051`**, and the ref is named because `main` moves, which is the trap below. Every verbatim unit now matches: the re-vendor of `repo-config/configure.sh` this record previously owed, for the jq portability defect reported as [#549][issue-549] and fixed at the hub in [#553][pr-553], landed with this change. The links above are pinned to that same ref rather than to `main`, so this record stays checkable after the hub moves again.

Three findings are open at the hub, recorded here rather than only in the issues because each changes what a fleet audit of this repo means. The first two are not work this repo can do. The third is, once the change answering it is ground truth, and what it will ask is stated below the table.

| Issue | What it means here |
| --- | --- |
| [#550][issue-550] | Nothing detects a repo missing from the registry, which is how this repo stayed invisible. Three other repos are still absent. |
| [#552][issue-552] | The audit flags any carried `AGENTS.md` naming the template repo, and the byte-locked `Fleet Bootstrap` section names it. Carrying the canonical correctly cannot pass, and it is the one finding the current run cannot clear. |
| [#597][issue-597] | Filed from here, after a mandatory pre-merge gate in `OPERATIONS.md` was skipped on [#40][pr-40]. The ruling is that a verification a runner cannot perform needs a declared destination, not a better per-repo pointer. Answered by [#598][pr-598], which this repo owes work against once it is ground truth. |

**What [#598][pr-598] will ask of this repo, once it is ground truth.** It is merged to the hub's `develop` and not to `main`, so it binds nothing yet, per the trap below about reading `main` as ground truth. It makes `Local Verification` a sixth declared `OPERATIONS.md` heading, leading the file as the only pre-merge one. This repo's `OPERATIONS.md` carries **13 level-two headings and matches none of the five declared today**, so the work is a rename and reorder rather than new prose: `Local Verification Before a Pull Request` becomes `Local Verification`, and `Backup and Restore` is one word from the declared `Backup and Recovery`. Both are near-misses rather than absences, which is the shape a heading check will mostly find in a repo that wrote its operational document before the spec declared headings. Do not start until the hub promotes it.

No audit will report this meanwhile. `OPERATIONS.md` is presence-checked only, which is why the 2026-08-05 run above reported nothing about a file using none of the declared headings, and the heading check belongs to a hub cluster that has not shipped.

Two more are resolved and are named because their absence from the table would otherwise read as an oversight. [#554][issue-554] made `spec/audit.py` report two DEFECTs here that no agent action could clear, and the fix is in the hub `main` this run measured against, so those two findings are gone. [#456][hub-issue] and [#558][hub-spec-issue] were the static-site type, now authored, per the section above.

**The live ruleset bypass is deliberate and stays.** Both rulesets carry the `RepositoryRole` admin entry. The owner is automatically an admin and holds that capability regardless, so the entry grants nothing new, and the payloads stopped declaring it because code should not be in the business of granting a bypass at all. `configure.sh check` reports it as unmanaged and exits 0, and the hub audit no longer disagrees.

## Traps

Each of these was hit or nearly hit, and each is cheap to re-trip.

- **Hugo taxonomy config is `singular: plural`, and the plural is also the front-matter key.** Setting `category: category` makes Hugo match nothing and generate zero term pages while still producing a plausible empty `/category/` listing. Control the URL with `permalinks`.
- **Never populate media over HTTP, and never trust a file count.** WordPress.com serves optimized derivatives at the same URL and filename. Verify by content hash against the export tar.
- **A Picasa URL ending in `-h` serves an HTML wrapper, not an image, with a 200 status.** Check magic bytes rather than status codes when fetching any binary.
- **PaperMod uses APIs Hugo deprecated in 0.158**, so `--panicOnWarning` fails on the theme rather than on content. The two overrides in `layouts/` exist to keep that flag on, and they are the reason the flag is a real gate.
- **`caddy run --watch` reloads rules and maps with `admin off`, and without it the deploy is silently stale.** `admin off` blocks `caddy reload`, which looks like it rules out reloading, and does not: the watcher reloads in process and never touches the admin endpoint. The watcher names only `/config/Caddyfile`, which never changes, and works anyway because Caddy re-adapts the whole config each poll and re-adapting re-executes the `import`. Drop the flag and the content symlink moves while the rules do not, so the URL check passes against a config that was never deployed. `X-Blog-Release` and `EXPECT_RELEASE` exist to turn that into an error.
- **The reload is asynchronous, so a check run straight after a deploy races it.** Content follows the symlink per request and is live instantly, the rules land about a quarter of a second later. Caught in practice: two environments deployed in one loop, the first passed and the second failed on a header that had not appeared yet. The check waits for `EXPECT_RELEASE` rather than sampling once, and the timeout is what still catches a container that is not watching at all.
- **A bind mount over `/config` shadows the world-writable `caddy/` the image pre-creates there**, so the `--watch` autosave has to `mkdir` and fails on a read-only mount, logging an ERROR once per deploy. `XDG_CONFIG_HOME=/data` moves it. Mount `/config` read-only *and* set that variable, since doing one alone trades a stray `autosave.json` in appdata for a per-deploy error.
- **`caddy run --watch` stops watching permanently after ONE failed config load, and says nothing.** Reproduced: flip `current` to a valid release and it reloads; point it at a missing release and it logs the failure and keeps the last good config; **restore it to a valid release and it never reloads again**. The log's last line is the original failure, then silence, and every other signal says the container is healthy. A restart is the only remedy, and it is the one nobody would try. Consequence for this repo: a deploy after any config-load failure lands content without rules, which `EXPECT_RELEASE` catches but cannot fix. The invariant worth monitoring is that the served `X-Blog-Release` equals the one in `<deploy-root>/current/Caddyfile`.
- **A dangling `current` reads as a release mismatch unless you look for it.** Caddy keeps its **last good config** when the imported release vanishes, rather than dying, so `X-Blog-Env` and `X-Blog-Release` stay correct and plausible while every URL 404s underneath them. A monitor checking only the environment header reports the site healthy. The preflight distinguishes the two: a non-200 that still carries the server's own headers is a broken symlink, not a deploy that never landed.
- **`--link-dest` on a remote deploy needs no bookkeeping: point it at `current`.** The flip happens after the upload, so at upload time `current` is still the previous release. A missing `--link-dest` is a warning and exit 0, not an error, so the first deploy degrades to a full copy on its own. Verified: same inode across releases through the symlink, link count 2.
- **The docker bridge gateway is inside the bridge subnet, so trusting the subnet trusts the host.** Verified here, not inherited: with `TRUSTED_PROXIES=172.18.0.0/16`, a request from this host straight to the container's bridge address forged `client_ip` successfully. Publishing no host port does not close it, because the bridge address is reachable from the host regardless. The value is now the subnet with the gateway's `/32` excluded, which is 16 CIDR blocks and cannot be written shorter. Re-tested both ways after: forgery ignored, real clients through Traefik still resolved.
- **`trusted_proxies` is a security boundary, and its RFC1918 default is only safe behind a proxy.** Trusting a range means believing `X-Forwarded-For` from anything in it, so on a host where the port is reachable directly, the default makes every device on the network able to forge the logged client address. `TRUSTED_PROXIES=` set-but-empty skips the default and trusts nothing, which is correct there; unset applies the default; an explicit list is exactly itself. All three verified. Binding to `127.0.0.1` does not close it, `docker-proxy` SNATs host traffic to the bridge gateway, which is inside RFC1918.
- **A hard link keeps its inode's mode and ownership**, so `--chmod` and `--no-g` govern only newly transferred files. A badly moded file rides the link chain into every later release. `NO_LINK_DEST=1` mints fresh inodes.
- **`DEPLOY_ROOT=... deploy/make-release.sh` does not select an environment.** The script sources its environment file with `set -a`, which exports every assignment in it and overwrites whatever the caller exported first, so the variable is set and then silently replaced. `ENV_FILE` selects the file, and the first argument overrides the root, because it is read afterwards. With two sites on one host the failure is not an error: it publishes to the other site. A named `ENV_FILE` that does not exist is a hard failure for the same reason.
- **`content/` is an imported archive.** Prose, spelling, and style sweeps do not reach it, and `cspell.json` ignores it deliberately.
- **A gate is trusted only after it has been demonstrated failing.** Every gate here has been. A list-driven check also needs a length floor, or a truncated list passes while checking almost nothing.
- **Do not name any workflow `build-*-task.yml`** while the repo declares `source-only`, since `detect` is literally `["no build-*-task.yml"]`.
- **Do not edit `.markdownlint-cli2.jsonc`, `repo-config/configure.sh`, or the two ruleset payloads.** They are carried verbatim and byte-matched against the hub. Scope a glob in the workflow instead. A reviewer finding a real defect in one of them is answered by declining locally and filing it at the hub, never by editing the file to satisfy the review.
- **The hub's `main` can promote while a convergence pull request is open**, so ground truth moves underneath work that was correct when it started. It happened twice in one session on 2026-08-03, and the second time added drift the branch could not have known about. Re-run the audit against the hub ref actually carried before claiming convergence, and name that ref in the change, or the claim ages into a false one.
- **A query that matches nothing reads as a clean result.** It has cost three separate false passes: a review-thread poll that could not see suppressed findings, a reviewer filter written in the wrong API's login form, and an audit loop whose `jq` path had moved. Each returned empty, and empty looked like nothing to report. Assert the query matched before reading what it returned, which is what `jq -e` and a non-empty check are for.
- **The hub authors `scripts/pr_review.py`, and hand-rolling the review loop re-discovers its bugs.** One `status` call reports rounds, head coverage, unresolved threads, suppressed findings across every round, and whether a request was ever picked up. `wait` runs the backoff in-process, so a review wait costs one turn rather than one per poll. It is read-only by design and the mutations stay explicit, so fetch and run it rather than reimplementing it. Its README documents the traps below as the reason it exists.
- **A review request can sit forever without being picked up, which looks exactly like patience.** Copilot raises a `copilot_work_started` timeline event within about half a minute of accepting; a request that never draws one is not slow, it is inert, and elapsed time cannot tell them apart. The event is REST-only. Recover by clearing the request with `union: false` and an empty `botIds`, then requesting again, after reading the pending set so a human reviewer is not dropped.
- **The Copilot reviewer's login differs by API, and a wrong-form filter reads as a clean review.** REST reports `copilot-pull-request-reviewer[bot]`, GraphQL omits the suffix. A filter written in the other form matches nothing, and an empty result is indistinguishable from no findings. Assert the filter matched before trusting what it returned.
- **A Copilot review hides findings in the review body, where the thread API cannot see them.** The `reviewThreads` query returns line threads only, so a review carrying `Suppressed comments (N)` in a `<details>` block reports zero unresolved while real findings sit unread. Read the review body itself, not just the threads, before calling a review loop finished.
- **`gh pr merge --delete-branch` on a `develop -> main` promotion deletes `develop`.** Use a plain `gh pr merge --merge`.

## Reference

The URL contract lives in this repo and is the thing CI enforces.

| Path | Contents |
| --- | --- |
| [`checks/golden-urls.txt`](./checks/golden-urls.txt) | 328 URLs that must render |
| [`checks/redirect-urls.txt`](./checks/redirect-urls.txt) | 917 URLs that must redirect |
| [`checks/golden-media-legacy.txt`](./checks/golden-media-legacy.txt) | 778 legacy image URLs that must still resolve |
| [`checks/README.md`](./checks/README.md) | how the contract was derived |
| [`deploy/README.md`](./deploy/README.md) | the release mechanics and the redirect design |

The provenance store holds the raw exports, the media tar, and the crawl. It lives outside this repo, is never published, and is passed to `checks/build-redirects.py` as an argument, which is why that script is a provenance tool rather than a CI step.

Secrets and variables, per environment. The App-token pair is repository-scoped rather than per-environment.

| Name | Kind |
| --- | --- |
| `DEPLOY_SSH_PRIVATE_KEY` | secret |
| `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_SSH_KNOWN_HOSTS` | variable |
| `HUGO_BASEURL` | variable |
| `PANGOLIN_ACCESS_TOKEN_ID`, `PANGOLIN_ACCESS_TOKEN` | secret, staging only |
| `CODEGEN_APP_CLIENT_ID`, `CODEGEN_APP_PRIVATE_KEY` | secret, both stores |

`DEPLOY_SSH_PRIVATE_KEY` holds the same key in both environments, per the decision above. The environment split still carries the base URL, the SSH endpoint, and the staging-only token pair, so it is not decorative.

The deploy root is deliberately absent from this table. The rsync destination is anchored at the deploy key's confinement root, so the workflow names an environment rather than a host path, and a declared-but-unread name is drift no audit can tell from a missing one. The local `DEPLOY_ROOT` in `secrets/<server>.<environment>.env` is a different value and is still read.

<!-- Repo -->

[issue-53]: https://github.com/ptr727/Blog/issues/53
[migration-post]: ./content/posts/2026/08/01/moving-this-blog-from-wordpress-to-hugo.md
[pr-30]: https://github.com/ptr727/Blog/pull/30
[pr-40]: https://github.com/ptr727/Blog/pull/40

<!-- External -->

[hub-issue]: https://github.com/ptr727/ProjectTemplate/issues/456
[hub-registry]: https://github.com/ptr727/ProjectTemplate/blob/3b802b9eb9a841c0149d018f4db6ffa1b9419051/registry/repos.json
[hub-report]: https://github.com/ptr727/ProjectTemplate/blob/3b802b9eb9a841c0149d018f4db6ffa1b9419051/reports/blog/audit.md
[hub-spec-issue]: https://github.com/ptr727/ProjectTemplate/issues/558
[hub-type-pr]: https://github.com/ptr727/ProjectTemplate/pull/560
[issue-549]: https://github.com/ptr727/ProjectTemplate/issues/549
[issue-550]: https://github.com/ptr727/ProjectTemplate/issues/550
[issue-552]: https://github.com/ptr727/ProjectTemplate/issues/552
[issue-554]: https://github.com/ptr727/ProjectTemplate/issues/554
[issue-563]: https://github.com/ptr727/ProjectTemplate/issues/563
[issue-597]: https://github.com/ptr727/ProjectTemplate/issues/597
[pr-553]: https://github.com/ptr727/ProjectTemplate/pull/553
[pr-598]: https://github.com/ptr727/ProjectTemplate/pull/598
