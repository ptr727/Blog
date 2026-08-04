# TODO

Running backlog for this repo, kept in a committed file so the work survives across sessions. How the migration was done is a [post on the blog][migration-post] rather than a section here.

## State

The site is built and gated in CI. It is on GitHub, and it is not yet serving its public address.

| Piece | State |
| --- | --- |
| Content and media | done. 514 pages, 778 media files hash-verified against the export tar |
| URL contract | done. 328 render, 917 redirect, 778 legacy image URLs, all gated |
| Deploy shape | done and proven against a running Caddy, on a local publish mirror and a local staging mirror |
| CI workflows | green. Validation runs on every pull request and feeds the required check |
| GitHub repo | public, both rulesets active, `configure.sh check` exits 0 |
| Release pipeline | proven end to end. Release `1.0.11` carries the tag, source archive, README, and LICENSE |
| Fleet conformance | cataloged in the hub registry, audited, and carrying the current canonical |
| VPS | untouched |

## Blocked on the maintainer

- Install `shellcheck`, `shfmt`, `nodejs`, and `npm`, then `markdownlint-cli2` and `cspell`, so the lint gate can run locally instead of only in CI. Every one of them currently runs here through Docker, which works but is slower than it should be for an edit loop.
- Read the migration post before it ships, since it is written in the maintainer's voice and has not been reviewed.

## Next, in dependency order

- Provision the VPS: an unprivileged `blogdeploy` user, the deploy root, and `unattended-upgrades` with automatic reboot.
- Move the two deploy roots under one parent, `/srv/blog/{production,staging}`, and restrict the **single** deploy key with `restrict,command=...`, no pty and no forwarding, pinned to that parent. One key rather than one per environment is a deliberate decision, recorded with its reasoning in [OPERATIONS.md](./OPERATIONS.md#server-hardening): the split only pays where the two keys never share a machine, and both sit on one workstation and in one secret store. The cost is that the forced command can no longer separate the environments, which is why the roots share a parent.
- Add the staging DNS record for `blog.vps.insanegenius.net` and expose it through Pangolin. It sits under the existing VPS wildcard, so no new certificate is needed, and **authentication stays on**: staging serves a byte-identical copy of the public site, and an open one is a duplicate handed to every crawler. `check-live-urls.sh` gets through with a resource access token instead.
- Write `deploy-site.yml` and prove it: a dry run that mutates nothing, then a real run, then a forced mid-deploy failure to confirm rollback keeps the site up. Report the measured deploy shape back to [ProjectTemplate#456][hub-issue], which is waiting on it before the publish type can be defined.
- Deploy to a temporary production FQDN and validate there before touching the live record. Lower the `blog` A-record TTL to 60s a day ahead, then flip it to the VPS, unproxied.
- Watch server logs for 404s daily for the first week, because real traffic finds what the golden list missed. Append anything new to `checks/golden-urls.txt` and add a redirect.
- Add the weekly non-blocking external-link-check workflow, which is the one gate that cannot be blocking because it fails on other people's outages.
- Decommission WordPress.com only after **30 clean days**, and downgrade to free rather than deleting, which keeps the media reachable as a safety net and preserves the ability to re-export. Do not start sooner: the conversion fetched media over HTTP from the live site.

## Open decisions

- `/robots.txt/` and `/osd.xml/` currently sit in `slugs.map` pointing at `/`. The first would be better pointing at the real `/robots.txt`.

## Deliberate deviations from the fleet baseline

Both are recorded in [AUDIT.md](./AUDIT.md) and reported to [ProjectTemplate#456][hub-issue], so neither reads as drift later.

- `lineEndings: "lf"` on a `release` repo, where the rule grants the native-platform default to operational repos only. Every consumer here is Linux.
- `types: ["source-only"]` rather than the `docs` the hub proposed, because both `docs` predicates are false for a repo that builds a site and gates a URL contract.

## Hub conformance, and what is open against the hub

Reconverged 2026-08-03. This repo is cataloged in [`registry/repos.json`][hub-registry] and the hub authored [`reports/blog/audit.md`][hub-report]. Before that it was in no registry, so no hub tool had ever measured it and the fleet ledger under-counted by exactly this repo.

**Measured against hub `main` `3b802b9eb9a841c0149d018f4db6ffa1b9419051`**, and the ref is named because `main` moves, which is the trap below. Every verbatim section of `AGENTS.md` and `GOVERNANCE.md` byte-matches, as do both ruleset payloads and `.markdownlint-cli2.jsonc`. The one exception is `repo-config/configure.sh`, one commit behind on [ProjectTemplate#553][pr-553], which fixes the jq portability defect this repo reported as [#549][issue-549] and is owed a re-vendor. Both links above are pinned to that same ref rather than to `main`, so this record stays checkable after the hub moves again.

Four findings are open at the hub. None is work this repo can do, and each changes what a fleet audit of this repo means, which is why they are recorded here rather than only in the issues.

| Issue | What it means here |
| --- | --- |
| [#550][issue-550] | Nothing detects a repo missing from the registry, which is how this repo stayed invisible. Three other repos are still absent. |
| [#552][issue-552] | The audit flags any carried `AGENTS.md` naming the template repo, and the byte-locked `Fleet Bootstrap` section names it. Carrying the canonical correctly cannot pass. |
| [#554][issue-554] | `spec/audit.py` still compares `bypass_actors` after the payloads stopped declaring it, so this repo reports two DEFECTs that no agent action can clear. |
| [#456][hub-issue] | The static-site type, still waiting on a measured deploy shape from the VPS work below. |

**The live ruleset bypass is deliberate and stays.** Both rulesets carry the `RepositoryRole` admin entry. The owner is automatically an admin and holds that capability regardless, so the entry grants nothing new, and the payloads stopped declaring it because code should not be in the business of granting a bypass at all. `configure.sh check` reports it as unmanaged and exits 0. Only `spec/audit.py` disagrees, which is [#554][issue-554].

## Traps

Each of these was hit or nearly hit, and each is cheap to re-trip.

- **Hugo taxonomy config is `singular: plural`, and the plural is also the front-matter key.** Setting `category: category` makes Hugo match nothing and generate zero term pages while still producing a plausible empty `/category/` listing. Control the URL with `permalinks`.
- **Never populate media over HTTP, and never trust a file count.** WordPress.com serves optimized derivatives at the same URL and filename. Verify by content hash against the export tar.
- **A Picasa URL ending in `-h` serves an HTML wrapper, not an image, with a 200 status.** Check magic bytes rather than status codes when fetching any binary.
- **PaperMod uses APIs Hugo deprecated in 0.158**, so `--panicOnWarning` fails on the theme rather than on content. The two overrides in `layouts/` exist to keep that flag on, and they are the reason the flag is a real gate.
- **A hard link keeps its inode's mode and ownership**, so `--chmod` and `--no-g` govern only newly transferred files. A badly moded file rides the link chain into every later release. `NO_LINK_DEST=1` mints fresh inodes.
- **`DEPLOY_ROOT=... deploy/make-release.sh` does not select an environment.** The script sources its environment file with `set -a`, which exports every assignment in it and overwrites whatever the caller exported first, so the variable is set and then silently replaced. `ENV_FILE` selects the file, and the first argument overrides the root, because it is read afterwards. With two sites on one host the failure is not an error: it publishes to the other site. A named `ENV_FILE` that does not exist is a hard failure for the same reason.
- **`content/` is an imported archive.** Prose, spelling, and style sweeps do not reach it, and `cspell.json` ignores it deliberately.
- **A gate is trusted only after it has been demonstrated failing.** Every gate here has been. A list-driven check also needs a length floor, or a truncated list passes while checking almost nothing.
- **Do not name any workflow `build-*-task.yml`** while the repo declares `source-only`, since `detect` is literally `["no build-*-task.yml"]`.
- **Do not edit `.markdownlint-cli2.jsonc`, `repo-config/configure.sh`, or the two ruleset payloads.** They are carried verbatim and byte-matched against the hub. Scope a glob in the workflow instead. A reviewer finding a real defect in one of them is answered by declining locally and filing it at the hub, never by editing the file to satisfy the review.
- **The hub's `main` can promote while a convergence pull request is open**, so ground truth moves underneath work that was correct when it started. It happened twice in one session on 2026-08-03, and the second time added drift the branch could not have known about. Re-run the audit against the hub ref actually carried before claiming convergence, and name that ref in the change, or the claim ages into a false one.
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
| `DEPLOY_ROOT`, `HUGO_BASEURL` | variable |
| `PANGOLIN_ACCESS_TOKEN_ID`, `PANGOLIN_ACCESS_TOKEN` | secret, staging only |
| `CODEGEN_APP_CLIENT_ID`, `CODEGEN_APP_PRIVATE_KEY` | secret, both stores |

`DEPLOY_SSH_PRIVATE_KEY` now holds the same key in both environments, per the decision above. The environment split still carries the deploy root, the base URL, and the staging-only token pair, so it is not decorative.

<!-- Repo -->

[migration-post]: ./content/posts/2026/08/01/moving-this-blog-from-wordpress-to-hugo.md

<!-- External -->

[hub-issue]: https://github.com/ptr727/ProjectTemplate/issues/456
[hub-registry]: https://github.com/ptr727/ProjectTemplate/blob/3b802b9eb9a841c0149d018f4db6ffa1b9419051/registry/repos.json
[hub-report]: https://github.com/ptr727/ProjectTemplate/blob/3b802b9eb9a841c0149d018f4db6ffa1b9419051/reports/blog/audit.md
[issue-549]: https://github.com/ptr727/ProjectTemplate/issues/549
[issue-550]: https://github.com/ptr727/ProjectTemplate/issues/550
[issue-552]: https://github.com/ptr727/ProjectTemplate/issues/552
[issue-554]: https://github.com/ptr727/ProjectTemplate/issues/554
[pr-553]: https://github.com/ptr727/ProjectTemplate/pull/553
