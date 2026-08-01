# TODO

Migration of `blog.insanegenius.com` from WordPress.com to Hugo, deployed to a self-hosted VPS. This file is the durable work plan - it outlives any agent session and is the thing to read first when picking the work back up.

Phases run in order. A phase is done when its **Gate** is met, not when its steps have been attempted.

- [Status](#status)
- [Blocked on Pieter](#blocked-on-pieter)
- [Phase A - Create Content](#phase-a---create-content)
- [Phase B - Create Repo](#phase-b---create-repo)
- [Phase C - Configure Repo](#phase-c---configure-repo)
- [Phase D - Validate CI](#phase-d---validate-ci)
- [Phase E - Finalize VPS and Server](#phase-e---finalize-vps-and-server)
- [Phase F - Configure Staging](#phase-f---configure-staging)
- [Phase G - Validate Sync to Staging](#phase-g---validate-sync-to-staging)
- [Phase H - Validate Staging Content](#phase-h---validate-staging-content)
- [Phase I - Deploy to Live](#phase-i---deploy-to-live)
- [Phase J - Validate Live](#phase-j---validate-live)
- [Phase K - Decommission WordPress.com](#phase-k---decommission-wordpresscom)
- [Web Server](#web-server-caddy-in-docker-behind-pangolins-traefik)
- [Open Decisions](#open-decisions)
- [Traps](#traps)
- [Reference](#reference)

## Status

| Phase | State |
| --- | --- |
| Capture (pre-work) | **done** - exports, media, and the URL contract are captured and verified |
| A - Create content | **done** - 505 pages; page parity 328/328, assets 1012/1012, media 778/778, strict build clean |
| B - Create repo | **local repo done**, content landed and gated; GitHub repo not yet created |
| D - Validate CI | **gates done**, workflows not written |
| E - VPS and server | **deploy shape done and proven locally**; VPS itself untouched |
| Local mirror | **live** on a private hostname, all 1,245 URLs honored through a reverse proxy and TLS |
| C, F onward | not started |

This repo is now the source of truth: 568 MB of source across ~1,300 files, all 778 media hash-verified against the export tar. A separate capture directory, held outside the repo and never published, remains the provenance store for the raw exports, the media tar, and the crawl. `checks/build-redirects.py` still needs it and takes its location as an argument, which is why it is a provenance script rather than a CI step.

**A local mirror runs continuously**, served by Caddy in Docker behind this host's Traefik. It is not staging: it proves the artifact (the redirect rules, the maps, the release mechanics), while staging on the VPS will prove the infrastructure (Pangolin routing, the auth gate, real TLS, and the SSH deploy).

Release a new build to it with:

```sh
deploy/make-release.sh
checks/check-live-urls.sh "$HUGO_BASEURL"
```

## Blocked on Pieter

Nothing on GitHub exists yet. `ptr727/Blog` has never been created, so there is no remote, no ruleset, no secret, and no environment. Every local step passes without them, which is why this is stated here rather than left in a checklist (raised upstream as ProjectTemplate#490).

1. **Create `ptr727/Blog` private.** An outward-facing write, so it needs explicit permission for that specific repo. The local `main` fast-forwards cleanly to `develop` and all commits are signed, so the greenfield preconditions hold.
2. **Install the GitHub App** and set `CODEGEN_APP_CLIENT_ID` and `CODEGEN_APP_PRIVATE_KEY` in **both** the Actions and Dependabot stores. The App must be installed, not only created. Set the values directly rather than passing them through an agent. `CODEGEN_APP_ID` must stay absent, since it is a `forbids` and the deprecated input silently does nothing.
3. **Install the missing lint tools:** `shellcheck`, `shfmt`, and `nodejs` with `npm` for `markdownlint-cli2` and `cspell`. `.vscode/tasks.json` references all four, and none is present. `brotli` is installed.

The deploy credentials for `staging` and `production` are not blocking yet, because the VPS does not exist.

**Ordering trap.** The `main` ruleset requires a check named `Check pull request workflow status job`, which only turns green after the pull request workflow has run once. Applying the rulesets before that workflow exists and has run deadlocks the first pull request, and on an operational repo `develop -> main` is still a pull request. Stand up the workflow, push, let it run once, then apply.

## Phase A - Create Content

- [x] Convert the WordPress export with `wp2hugo` (108 posts, 2 pages)
- [x] Drop comments entirely - read-only blog, no interaction. `data/` deleted, no partial, no PII to scrub
- [x] Strip front matter to content only: 1,992 keys -> 685. Kept `title`, `date`, `url`, `categories`, `tags`, `post_id`, `cover`
- [x] Fix `hugo.yaml`: taxonomy permalinks so `/category/` and `/tag/` stay singular, `refLinksErrorLevel: ERROR`, `enableGitInfo: false`, comments and share buttons off
- [x] **URL parity passes: 328/328 render, 0 missing**
- [x] **Replaced all library media from the official tar.** **167 of 778** files that `wp2hugo --download-media` fetched were degraded derivatives - 21%, 135 MB - one 205x smaller than the original. All 778 now hash-match the export
- [x] **Localized 270 externally-hosted images.** `wp2hugo` skips these entirely ("non-relative link (skipped for download)"), and they are absent from the WordPress export too. Now in `static/external/`, all references rewritten
- [x] Removed 48 Blogger analytics beacons (`googleusercontent.com/tracker/...`) - 1x1 pixels that 404 today and are not content
- [x] Rewrote 9 self-references that pointed at the old `blogdotinsanegenius.wordpress.com` subdomain, which would die with the WordPress site
- [x] Generated favicon variants; unwrapped a dead 2015 link to a local Windows filesystem path
- [x] Overrode two PaperMod templates that use APIs Hugo deprecated in 0.158 - upstream still ships them, so this is the only way `--panicOnWarning` can stay a real gate
- [x] **Build passes `hugo --gc --minify --panicOnWarning` with zero warnings**
- [x] Verified rendering: 261 `<figure>` blocks, 76 code blocks with syntax highlighting, 5 YouTube embeds
- [x] **Asset integrity: 1,012 local references, 0 missing. Zero remaining ggpht/googleusercontent/Photon references.** The earlier count of 937 missed `href` links to media and `srcset`
- [x] Fixed two defects found on review: `params.author` was a map, so `map[name:Pieter Viljoen]` rendered literally on **345 pages**; and the Archive menu item pointed at `/archives/` when the page publishes at `/all/`
- [x] **Restructured the content tree to mirror the URLs.** `content/posts/2024/05/29/slug.md` -> `/2024/05/29/slug/`, so a post's file is derivable from its URL and vice versa. 108 posts across 94 posting-day directories
- [x] **Static pages moved to the content root** - `content/about.md`, `content/viljoen-family.md`. A `content/pages/` section would publish an unwanted `/pages/` listing URL, the same problem `/posts/` had
- [x] **Suppressed the `/posts/` section listing** (12 URLs WordPress never served). Home page and `/all/` already cover it
- [x] **Renamed `static/wp-content/uploads/` to `static/media/`** and rewrote 797 references. Rule R8 maps every legacy image URL, so external hotlinks and Google Images results still resolve
- [x] **Added a media parity gate** - `checks/golden-media-legacy.txt` records all 778 legacy image URLs, because the page parity gate covers pages only and nothing else protected the image URL surface

**Gate: MET.** 505 pages. Page parity **328/328**, asset references **1,012/1,012**, media parity **778/778**, strict `--panicOnWarning` build clean.

Kept deliberately: `/all/` (year-by-year index, and a much better redirect target for the 78 legacy date archives than the home page), `/search/` (PaperMod client-side search over an `index.json` Hugo **regenerates every build**, so it never goes stale), and the 193 `/page/1/` URLs, which are meta-refresh **redirect stubs** rather than duplicate content - removing them would turn working redirects into 404s.

## Phase B - Create Repo

Local work is complete. The GitHub side has not started, and everything below the divider is blocked on it.

- [x] `.gitignore`, `.editorconfig`, `.gitattributes`, `.editorconfig-checker.json` landed before the first content commit, with LF defaults and a byte-preserve rule for the two media trees
- [x] Signing verified live before the first commit, so the greenfield window never closed. All 24 commits are signed and carry the global noreply identity, with no repo-local override
- [x] Content landed in slices with the local gates green between each. CI could not gate them, because no CI exists yet
- [x] Repo size measured: 568 MB of source, 536 MB packed, under GitHub's 1 GB warning, so no LFS
- [x] **Instruction set carried from hub `main`** `1d5b076`, every verbatim section byte-checked rather than assumed. 23 of 24 applicable baseline files present
- [ ] **Create `ptr727/Blog` private, with `main` and `develop`** - needs pieter, see [Blocked on Pieter](#blocked-on-pieter)
- [ ] Fast-forward `main` to `develop` before the first push, so `main` is ground truth from day one rather than 23 commits stale
- [ ] Push both branches, then let the pull request workflow run once before any ruleset is applied

**Gate:** repo exists, both branches protected, content committed, `git count-objects -vH` within budget.

## Phase C - Configure Repo

- [ ] `repo-config/configure.sh apply ptr727/Blog operational`
- [ ] Create GitHub Environments `staging` and `production`, each with a deployment-branch policy
- [ ] Set secrets and variables (see [Reference](#reference))
- [ ] Confirm `CODEGEN_APP_ID` is **absent** - it is a `forbids`
- [ ] `repo-config/configure.sh check ptr727/Blog operational` exits 0

**Gate:** `configure.sh check` exits 0; required check bound on `main`.

## Phase D - Validate CI

The gates exist and are proven. No workflow runs them yet.

- [x] `checks/check-url-parity.py` **fails the build** when a golden URL goes missing, proven by removing a post, and independently by removing one media file, which trips the media and asset checks separately
- [x] Length-floor assertions fire when a list is truncated, proven by cutting `golden-urls.txt` to 50 entries that all exist. Without the floor those 50 would have passed
- [x] `checks/check-live-urls.sh` proves the redirects a build cannot, and follows each one to its destination, proven by pointing a map entry at a page that does not exist
- [ ] `.github/workflows/test-pull-request.yml`, the last missing baseline file, `interface` fidelity
- [ ] Aggregator job named exactly `Check pull request workflow status job`, byte-identical to the ruleset context
- [ ] The remaining workflows: `validate-task`, `deploy-site`, `deploy-vps-task`, `publish-release`, `merge-bot-pull-request`
- [ ] No `needs:` references a job that does not exist
- [ ] Every action SHA-pinned with a version comment
- [ ] Set `REQUIRE_BROTLI=1` in CI, so a runner without the binary fails rather than shipping gzip-only

**Gate:** a PR that would drop a legacy URL cannot merge, demonstrated rather than assumed.

## Phase E - Finalize VPS and Server

The artifact is built and proven against a real server. The VPS itself is untouched.

- [x] **Web server decided: Caddy in Docker behind Pangolin's Traefik** - see [Web Server](#web-server-caddy-in-docker-behind-pangolins-traefik)
- [x] `deploy/Caddyfile` written with **11 rules and 5 maps**, all inside the release bundle so a rollback reverts rules and content together
- [x] `deploy/make-release.sh` builds, verifies, precompresses, installs, swaps atomically, and prunes, asserting each outcome rather than trusting it
- [x] **All 917 redirects verified against a running server**, not just the maps generated
- [x] `deploy/README.md` and `OPERATIONS.md` written, including the container contract and the rebuild procedure
- [ ] Provision the VPS: unprivileged `blogdeploy` user, the deploy root, `unattended-upgrades` with automatic reboot
- [ ] `authorized_keys` with `restrict,command=...`, no pty and no forwarding, so the key can only rsync into `releases/` and swap the symlink
- [ ] Generate per-environment Ed25519 deploy keys so staging cannot reach production
- [ ] Create the Pangolin site and resources

**Gate:** the deploy key can do nothing but rsync into `releases/`, and the runbook is rebuild-complete.

## Phase F - Configure Staging

- [ ] Choose the staging FQDN (e.g. `blog-staging.insanegenius.com`) and add a Cloudflare A record to the VPS
- [ ] Expose it through Pangolin as a public resource with **no auth** - it must be reachable by CI's live-URL check
- [ ] Confirm TLS issues cleanly
- [ ] Keep staging and production configuration identical apart from hostname and root, so staging actually proves production

**Gate:** the staging FQDN serves a placeholder over valid TLS.

## Phase G - Validate Sync to Staging

- [ ] Run `deploy-site.yml` with `dry_run: true` - confirm nothing on the server mutates
- [ ] Run for real; confirm `cp -al` hard-link seeding works (10 releases should cost ~600 MB, not 5.6 GB)
- [ ] Confirm the `mv -T` symlink swap is atomic and visible to the server without a restart
- [ ] Force a failure mid-deploy and confirm rollback re-points `current` and the site stays up
- [ ] Confirm the prune keeps 10 releases and **asserts** the count rather than trusting itself

**Gate:** deploy, rollback, and prune all demonstrated; disk usage as predicted.

## Phase H - Validate Staging Content

- [ ] `checks/check-live-urls.sh <staging-fqdn>` - all 328 golden URLs return 200
- [ ] All 917 redirect URLs return 301/308 to the right target, including the `?p=<ID>` query-string cases and the 59 Blogger `.html` permalinks
- [ ] Click through the gallery, code-block, and embed posts
- [ ] Confirm no page references `blog.insanegenius.com` absolutely, or wordpress.com, or `i0.wp.com`
- [ ] Check `/feed.xml` is valid RSS
- [ ] Lighthouse or equivalent sanity pass

**Gate:** every URL in both lists resolves correctly against a real server.

## Phase I - Deploy to Live

- [ ] Merge `develop -> main` with `gh pr merge --merge`. **Never `--delete-branch`** - that trap deletes `develop`
- [ ] Dispatch `publish-release.yml` on `main`: versions with NBGV, builds, deploys production, runs the live check, then cuts the tag
- [ ] Deploy to a temporary production FQDN first (e.g. `new.blog.insanegenius.com`) and validate there
- [ ] Lower the `blog` A-record TTL to 60s a day ahead
- [ ] Flip the `blog` A record to the VPS IP, **grey cloud** (unproxied)

**Gate:** the real hostname resolves to the VPS and serves the site over valid TLS.

## Phase J - Validate Live

- [ ] `checks/check-live-urls.sh https://blog.insanegenius.com` - clean
- [ ] Confirm the GitHub Release tag exists and matches the deployed commit
- [ ] Watch server logs for 404s daily for the first week - real traffic finds what the golden list missed
- [ ] Append any newly-found URL to `golden-urls.txt` and add a redirect
- [ ] Add the weekly non-blocking external-link-check workflow

**Gate:** a week of clean logs.

## Phase K - Decommission WordPress.com

**Do not start before 30 clean days.** The conversion fetches media over HTTP from the live site; cancelling early destroys anything not already captured.

- [ ] Final WXR export to cold storage
- [ ] **Downgrade to free - do not delete the site.** It keeps `blogdotinsanegenius.wordpress.com` media reachable as a safety net and preserves the ability to re-export
- [ ] Optionally flip the Cloudflare orange cloud on, once the URL set has stabilized

**Gate:** plan cancelled, rollback path consciously given up.

## Web Server: Caddy in Docker behind Pangolin's Traefik

**Decided.** Pangolin's Traefik already owns 80/443 and terminates TLS, so a host-installed Caddy would collide on ports and its auto-TLS advantage is redundant. The choice therefore came down to which server can express the redirect workload, and specifically the `?p=<ID>` query-string class.

**static-web-server was evaluated and disqualified.** Its `src/redirects.rs` matches on `uri.path()` only - the query string is never an input - and it then force-appends the client's query to the destination. So `/?p=123` would match `/`, redirect the **homepage**, and carry `?p=123` through. It also has no lookup primitive: redirects are a linear regex scan per request. Two further traps had it been chosen: `--follow-symlinks` defaults to false (the whole site would 403) and `--use-relative-root` defaults to false (the root would pin to one release at boot).

nginx is functionally equal to Caddy but costs more maintenance: `map_hash_bucket_size` must be tuned or it refuses to start, and the stock image has no brotli module. Traefik alone cannot serve static files natively at all.

### Redirect design: 11 regex rules + 5 map files cover all 917

| Rule | Covers | Shape |
| --- | --- | --- |
| R1 | 216 | `/YYYY/MM/DD/post/<child>/` -> `/YYYY/MM/DD/post/` (attachment pages **and** per-post feeds, same shape) |
| R2 | 107 | `/YYYY/MM/DD/post/<child>/feed/` -> `/YYYY/MM/DD/post/` (must be ordered **before** R1) |
| R3 | 78 | `/YYYY/` and `/YYYY/MM/` -> `/` |
| R4 | 5 | `/YYYY/page/N/` -> `/` |
| R5 | 11 | `/author/<name>/` and its pagination -> `/` |
| R6 | 1 | `/feed/` -> `/feed.xml` |
| R7 | 192 | `/tag/<t>/feed/` and `/category/<c>/feed/` -> the term archive |
| R8 | 778 | `/wp-content/uploads/(.*)` -> `/media/$1` - preserves every legacy image URL after the media tree was renamed |
| R9 | 2 | `/p/<slug>.html` -> `/<slug>/` - Blogger's static-page URL shape |
| R10 | 2 | `/feeds/posts/default` (and `?alt=rss`) -> `/feed.xml` - Blogger's Atom feed |
| R11 | wildcard | `/YYYY_MM_01_archive.html` -> `/2009/04/10/archived-content-and-templates/` |
| `slugs.map` | 107 | bare `/<attachment-slug>/` -> best destination |
| `p-ids.map` | 110 | `/?p=<id>` -> permalink |
| `blogger.map` | **59** | `/YYYY/MM/slug.html` -> current post URL (pre-2012 Blogger permalinks), both the full and the truncated slug |

### The Blogger-era URL surface

The blog ran on **Blogger until mid-2012** on the same `blog.insanegenius.com` domain - 48 of the 108 posts predate the move, and WordPress has been 301-redirecting their old `/YYYY/MM/slug.html` permalinks ever since. **All 48 still resolve on the live site**, verified.

No crawl finds them, because nothing on the current site links to them, and they carry no day segment so no regex can derive the target - hence a map. They were discovered only by asking why five posts shared a single date, and would otherwise have 404'd silently after cutover.

**How the map is actually built** (2026-07-31 - the previous description of this was wrong and cost a re-derivation). The `blogger_<hash>_permalink` postmeta holds a **numeric Blogger post id**, not a path, so it cannot produce the map. The source path is derived instead from `wp:post_date` + `wp:post_name`, restricted to the posts carrying any `blogger_*` postmeta: `/YYYY/MM/<post_name>.html`. That derivation reproduces the original 48-entry map byte for byte.

**The map was 48 entries and should have been 59.** Blogger truncated an auto-generated slug to **40 characters on a whole-word boundary**, so for the 11 posts whose slug exceeds 40 characters the URL Blogger actually served - and therefore the one in Google's index and in anyone else's links - is the *truncated* form, which was the one missing. WordPress registers redirects for both forms. All 11 truncated URLs were verified live returning 301 to the correct post, against a fabricated control slug that correctly 404s, so this is a real registered redirect and not a catch-all. The rule is: join the slug's words with hyphens while the total stays within 40 characters.

Three further Blogger-era classes were found live at the same time, none of them previously in the contract - `/p/<slug>.html` for static pages (fakes 404, so these are real), `/feeds/posts/default` for the Atom feed, and a `*_archive.html` **wildcard** that sends any `/YYYY_MM_01_archive.html` to one post regardless of the date, including dates the blog never covered. `/search/label/<Label>` is **not** a redirect - WordPress serves its generic search page there and a nonsense label returns 200 just the same, so it is a soft 404 today and needs a decision rather than preservation. Blogger comment feeds (`/feeds/<id>/comments/default`) genuinely 404 and are correctly out of scope.

Related finding, settled with evidence: the five posts sharing 2008-04-01 are **genuine publish timestamps, not a migration artifact**. The archived Blogger **Atom feed** from 2008-05-07 carries `published` and `updated` as separate fields per entry, and they differ - e.g. published 20:47:00, updated 21:03:19. So `published` cannot be an edit timestamp, and Blogger stored millisecond precision in both, so no granularity was lost. `published` ends `.000` (a set value) while `updated` carries real millisecond precision (a system write). Each post was edited 2-16 minutes after its own publication.

`published` records when a post went live, not when it was written, so publishing a backlog of drafts in one ~28 minute session is fully consistent with the maintainer's recollection of not having written them that evening. **The dates stay** - they are load-bearing for the current URLs, the 48 Blogger permalinks, and 16 years of inbound links.

Separately: every `post_modified` in the export reads **2026-06-08 11:45**, seconds apart in descending order - WordPress.com bulk-touched the whole archive. It hit `post_modified` only; `post_date` was untouched. Worth knowing before trusting any modified timestamp from this export.

Verified: **zero golden URLs are 5-segment under a date**, so R1 cannot swallow a page that must render. R8 is a prefix rewrite under `/wp-content/uploads/`, which no rendered page occupies.

`slugs.map` is generated by `build-redirects.py`. Every one of those 107 attachments has `post_parent = 0` in the WXR - unattached, which is exactly why they surface as bare URLs - so the parent is recovered from the media inventory instead, by finding which post embeds the image file. **85 of 107 resolve to a real post**; the remaining 22 were uploaded but never used anywhere, so `/` is correct for them.

### Wiring

Caddy binds an internal port only, with `auto_https off` and `admin off`. The container joins Pangolin's external `pangolin` network with **no published ports**, and is addressed by container name.

- **Pangolin's Traefik does not have the Docker provider enabled.** Traefik labels on the container are silently ignored. Routing is created in the Pangolin UI: Sites -> Add Site -> **Local**, then Resources -> HTTP/HTTPS, target `http` / `blog` / the internal port.
- **Auth is ON by default for public resources.** Authentication tab -> turn "Use Platform SSO" **off** and save, or CI's live-URL check gets an auth wall.
- **Bind-mount `/srv/blog` (the parent), never `/srv/blog/current`.** Docker resolves a symlink at container-creation time, so mounting the symlink pins the container to one release forever. Mounting the parent lets the kernel resolve the symlink per request, and an atomic `mv -T` swap is visible immediately with no restart. Mount at the identical host path so absolute symlink targets resolve the same inside.
- Precompress HTML/CSS/JS/SVG/XML in CI and serve with `file_server { precompressed br gzip }`. Traefik forwards `Accept-Encoding` unchanged and adds no compression of its own. Do not precompress the media.

## Open Decisions

- [ ] Staging FQDN name
- [ ] `/robots.txt/` and `/osd.xml/` currently land in `slugs.map` pointing at `/`; the first would be better pointing at the real `/robots.txt`
- [ ] Point the 78 legacy date-archive redirects at `/all/` rather than `/` - a visitor following a `/2015/` link then lands somewhere they can actually find 2015 posts (one-line change to rule R3)
- [ ] Theme is PaperMod. Not lock-in: content, media, shortcodes, permalinks and the URL contract are all theme-independent. Switching means replacing the theme directory, rewriting ~14 `params` keys, deleting the 2 template overrides, and re-homing `archives.md`/`search.md`. The parity gate protects the URL contract through any such change

## Traps

Each of these was hit or nearly hit. They are cheap to re-trip.

- **Hugo taxonomy config is `singular: plural`, and the plural is also the front-matter key.** Setting `category: category` makes Hugo look for `category:` in front matter, match nothing, and generate zero term pages while still creating a plausible-looking empty `/category/` list page. Control the URL with `permalinks`, not by renaming the taxonomy
- **Never populate media from HTTP.** WordPress.com serves optimized derivatives at the same URL and filename. `wp2hugo --download-media` got **167 of 778 wrong** (21%, 135 MB). A file-count reconciliation passes cleanly while the bytes are wrong - only a content hash against the export catches it
- **`wp2hugo` does not localize external media** despite its docs. It logs "non-relative link (skipped for download)" and moves on
- **A Picasa/ggpht URL ending in `-h` (`/s1600-h/`) serves an HTML wrapper page, not an image** - with a 200 status. A naive "status 200 and non-empty" check passes on 121 of 266 files that are actually 400-byte HTML. The wrapper contains an `<img src>` naming the real image; follow that
- **Check magic bytes, not status codes,** when fetching binary assets from anywhere
- **PaperMod uses APIs Hugo deprecated in 0.158** (`.Language.LanguageDirection`, `.Language.LanguageCode`) and upstream has not fixed them. `--panicOnWarning` fails on the theme, not on your content. Override the two templates in `layouts/` rather than dropping the flag
- **The `wp2hugo` nginx.conf is a stub** - the `?p=` rules are a commented example, not a generated map. Build it from `export/post-id-map.tsv`
- **`wp2hugo` rewrote the RSS GUID scheme to `https`** where WordPress serves `http`. Irrelevant now that GUID preservation is dropped, but it would have marked every post unread
- **Do not name any workflow `build-*-task.yml`** while the repo declares `source-only` - `detect` is literally `["no build-*-task.yml"]` and the declaration would become false
- **Do not edit `.markdownlint-cli2.jsonc`** - it is carried `fidelity: verbatim, whole: true`. Scope the markdownlint glob in the workflow instead
- **Do not run `pkill -f` with a pattern matching the agent's own shell.** It kills the session
- **`gh pr merge --delete-branch` on a `develop -> main` promotion deletes `develop`**

## Reference

**The URL contract lives in the repo.** The capture holds a frozen copy from before the contract grew, so read and edit the repo's.

| Path in this repo | Contents |
| --- | --- |
| `checks/golden-urls.txt` | 328 URLs that must render |
| `checks/redirect-urls.txt` | 917 URLs that must redirect |
| `checks/golden-media-legacy.txt` | 778 legacy `/wp-content/uploads/` image URLs that must still resolve |
| `checks/README.md` | how the URL contract was derived |
| `deploy/maps/` | the five generated Caddy redirect maps |

**Provenance**, all under the capture directory, which lives outside the repo, is never published, and is passed to `checks/build-redirects.py` as an argument:

| Path | Contents |
| --- | --- |
| `export/raw/` | **two** WXR exports, one full and one media-only with zero posts. The generator selects by content and refuses to guess |
| `export/media-tar/` | 778 extracted media files - **the authoritative media source** |
| `inventory/media-urls.tsv` | which post embeds which file, recovering the parent of an unattached attachment |
| `media-at-risk/` | 266 Google-hosted files that exist in no export |
| `converted/generated-2026-07-29-18-54-51/` | the original conversion, superseded by the repo |
| `checks/` | the frozen pre-growth copy of the lists. **Not the contract** |
| `mirror/` | 623 MB browsable "before" snapshot of the live site |

**Secrets and variables**, per environment (`staging`, `production`). The App-token pair is repository-scoped rather than per-environment:

| Name | Kind |
| --- | --- |
| `DEPLOY_SSH_PRIVATE_KEY` | secret |
| `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_SSH_KNOWN_HOSTS` | variable |
| `DEPLOY_ROOT`, `HUGO_BASEURL` | variable |
| `CODEGEN_APP_CLIENT_ID`, `CODEGEN_APP_PRIVATE_KEY` | secret, both stores (fleet baseline) |

**Host:** a RackNerd KVM running Ubuntu 24.04, with 60 GB of disk, 4 GB of RAM, and **no IPv6**, which is why the deploy is IPv4-only. It runs Pangolin, so Traefik owns 80/443 and the site is served behind it. The address and credentials live in `secrets/.env` and in the GitHub environment secrets, never here.

**Hub coordination:** [ptr727/ProjectTemplate#456](https://github.com/ptr727/ProjectTemplate/issues/456) is the agent-to-agent channel. Blog is the pilot adopter for the scripted-CI work. The VPS deploy **is** a publish (this was argued and conceded); the eventual registry entry is `types: ["hugo"]` with `publish: [{self-hosted, ssh-deploy}, {github-release, none}]`, interim `source-only` plus a driftNote.
