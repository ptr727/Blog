# ENVIRONMENT.md

Every configuration value this repository reads or writes, described once. [`OPERATIONS.md`](./OPERATIONS.md) is the procedure and this is the reference the procedure points at, so a value is explained here and named elsewhere.

**A description lives here and nowhere else.** The `.example` files state the format, the scripts state the defaults, and this file states what a value means. [`checks/check-env-docs.py`](./checks/check-env-docs.py) fails if a value is declared or consumed anywhere and has no row below, or has a row and is declared nowhere, so the two stay in step without depending on anyone remembering.

**Values are grouped by where they live rather than by what reads them**, because where a value lives determines who can change it, what happens when it is wrong, and whether it reaches a public history.

## The mechanism

A local run reads one file. `secrets/<server>.<environment>.env` is sourced with `set -a`, selected by `ENV_FILE`, and defaults to `secrets/local.production.env`. The whole `secrets/` directory is gitignored, so a value naming a machine never reaches the published history, and [`example.env`](./example.env) is the tracked template that documents the shape.

Two consequences of `set -a` are worth stating because both have surprised someone. Sourcing overwrites a variable the caller exported first, so exporting `DEPLOY_ROOT` by hand does not switch environments and only `ENV_FILE` does. And a named file that does not exist is a hard failure rather than a fall-through, because on a host serving two sites the ambient value is the other site's root.

CI reads no file. The deploy workflow resolves the same values from the GitHub Environment, which is why the shapes have to match even though the sources do not.

## Repository environment files

Held in `secrets/<server>.<environment>.env`, one file per environment. Template: [`example.env`](./example.env).

| Value | Names | Notes |
| --- | --- | --- |
| `DEPLOY_ROOT` | where a release is written, and what the container mounts read-only at `/srv/blog` | The first argument to `make-release.sh` wins over it. |
| `HUGO_BASEURL` | the site base URL | Baked into the canonical tag, the feed links, and every absolute permalink. Must be set for anything that is not production, or a mirror serves pages pointing at production and every gate still passes. |
| `CADDY_APPDATA` | the container's persistent state root, deliberately outside `DEPLOY_ROOT` | Holds `config/` with the bootstrap Caddyfile and `data/` with Caddy state. A release writes neither. Nothing reads this value, so it is recorded to keep a rebuild from depending on memory. |
| `CADDY_CONTAINER` | the container serving this environment | A release needs no restart, because Caddy reloads in process. Restarting is the remedy when the watcher dies, which it does silently after one failed load. |
| `EXPECT_SITE_ENV` | the environment that must answer, compared against the `X-Blog-Env` header the bundle stamps | A proxy rule aimed at the wrong container returns a healthy 200 under the right hostname, so the check refuses to start rather than proving nothing. |
| `PANGOLIN_ACCESS_TOKEN_ID` | the resource access token's id, for an environment behind the auth gate | Set both or neither. Leave both unset for a site that is public. |
| `PANGOLIN_ACCESS_TOKEN` | the token itself | Read by `check-live-urls.sh`. Staging keeps its gate on because it serves a byte-identical copy of the public site. |
| `CAPTURE_ROOT` | the provenance capture, holding the WordPress exports, the crawl of the old platform, and the inventories derived from it | Every script under [`capture/`](./capture/) reads beneath it, and all but one write there too. The exception is [`capture/build-redirects.py`](./capture/build-redirects.py), which writes the committed maps under `deploy/maps/` in this repository, and which also accepts the capture as a first argument that wins over this value. Environment-independent, so it belongs in the default file only. |
| `CAPTURE_SOURCE_URL` | the old platform's base URL, the site the crawl and the URL verification ran against | **Not `HUGO_BASEURL`.** The two hold the same string after the cutover and mean different things, so merging them points a verification run at the new site while every check still passes. Environment-independent. |
| `CAPTURE_SOURCE_API` | the old platform's REST API for that site, carrying its numeric site id | Read for the post and page bodies in **rendered** form, which is what expands shortcodes so a media reference is seen the way a reader's browser sees it. Environment-independent. |
| `CAPTURE_AUTHOR_SLUG` | the old platform's author slug, used to backfill the author archive and its pagination | Optional, and an account name rather than a site value, which is why it is a variable at all. Unset, [`capture/classify.py`](./capture/classify.py) skips the backfill and says so, rather than emitting a list that is silently short by the author URLs. Environment-independent. |
| `VPS_SSH_HOST` | the VPS administrative login | Not the deploy account. See "Two credentials" below. Environment-independent. |
| `VPS_TRAEFIK_LOG` | today's live access log on the VPS, still being appended to | Never pulled, because rotation is what makes a file eligible. An analysis covering today reads it over SSH. Nothing sources it. |
| `VPS_TRAEFIK_LOG_ARCHIVE` | the rotated access logs on the VPS, and the source of the off-host copy | Also read by the pull, below. |
| `VPS_COMMS_DIR` | the two agent channel files on the VPS | Nothing sources it, and the transfer commands in `OPERATIONS.md` are spelled out rather than using it. See "The one place indirection is wrong" below. |
| `BACKUP_ARCHIVE_ROOT` | the off-host encrypted archives and the plaintext `hostconfig` tree beside them | Written by the pull, read by a rebuild. |
| `LOG_ARCHIVE_ROOT` | the off-host copy of the rotated logs | Written by the pull, read by the log review. |

Three more are named in the template but commented out, because CI resolves them from the GitHub Environment and a local run deploys to a path and needs none of them: `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_SSH_KNOWN_HOSTS`. They are listed there so the local file and the environment describe the same shape.

## The backup host

Held in `/etc/vps-backup-pull.env`, read by `vps-backup-pull` through the unit's `EnvironmentFile`. Template: [`example.env`](./example.env). [`ops/install.sh`](./ops/install.sh) generates it by copying from the repository environment file, which is why the four shared names are spelled identically in both.

| Value | Names | Notes |
| --- | --- | --- |
| `VPS_SSH_HOST` | where to pull from | Required. No default. |
| `BACKUP_ARCHIVE_ROOT` | where the archives and host config land | Required. No default. |
| `LOG_ARCHIVE_ROOT` | where both log sets land | Required unless `--no-logs`. No default. Mode 700, because query strings are logged in full. |
| `VPS_ARCHIVE_DIR` | the encrypted archives on the VPS | Defaults to the documented layout. |
| `VPS_TRAEFIK_LOG_ARCHIVE` | the rotated edge access logs on the VPS | Defaults to the documented layout. |
| `VPS_BLOG_LOG_DIR` | one-off Caddy container dumps on the VPS, kept from before rotation existed | Defaults to the documented layout. |
| `SSH_OPTS` | the SSH options the transfer uses | `BatchMode` makes an unusable key fail immediately rather than hanging a timed run on a password prompt nobody sees. |

**The three marked required carry no default on purpose.** An address and a destination belong to one host, and a wrong-but-valid destination is a backup nobody can find, so the pull names what is missing and refuses to run rather than falling back to something plausible.

**`systemd` parses this file itself rather than passing it to a shell**, so there is no expansion and no command substitution, and a `$` or a backtick is a literal character. It does strip matching quotes, verified rather than assumed, so a value containing spaces is quoted and arrives without them. That matters because [`example.env`](./example.env) is also sourced by a shell for the other destination, where an unquoted value would run everything after the first space as a command.

## The GitHub Environments

Held on the `production` and `staging` environments. The deploy workflow reads no file.

| Value | Kind | Names |
| --- | --- | --- |
| `HUGO_BASEURL` | variable | the base URL, used twice: the site is built with it and `check-live-urls.sh` is pointed at it |
| `DEPLOY_SSH_HOST` | variable | the deploy endpoint |
| `DEPLOY_SSH_USER` | variable | the confined deploy account |
| `DEPLOY_SSH_KNOWN_HOSTS` | variable | the pinned host key. A variable rather than a secret, deliberately, since it is public by nature |
| `DEPLOY_SSH_PRIVATE_KEY` | secret | the deploy key, held behind an `rrsync` forced command |
| `PANGOLIN_ACCESS_TOKEN_ID` | secret | as above, for an environment behind the gate |
| `PANGOLIN_ACCESS_TOKEN` | secret | as above |

**`HUGO_BASEURL` being read twice is the trap worth knowing.** A wrong value bakes the wrong address into every canonical tag and then runs the full URL contract against that same wrong address, so the deploy verifies itself and passes.

**A host rebuild regenerates the SSH host keys and the pinned value stops matching**, which fails every deploy closed and blocks the rollback path at the same moment a rebuild makes both matter. Replace `DEPLOY_SSH_KNOWN_HOSTS` on **both** environments before the first deploy after a rebuild.

Two repository-level secrets are unrelated to deployment and exist for the merge bot: `CODEGEN_APP_CLIENT_ID` and `CODEGEN_APP_PRIVATE_KEY`.

## Per-invocation knobs

Set on the command line for one run rather than stored anywhere.

| Value | Effect |
| --- | --- |
| `ENV_FILE` | which environment file to source. Defaults to `secrets/local.production.env` |
| `REQUIRE_BROTLI=1` | fail rather than shipping gzip-only. CI sets it |
| `NO_LINK_DEST=1` | full copy instead of hard-linking from the previous release |
| `KEEP_RELEASES` | how many releases `make-release.sh` leaves behind |
| `EXPECT_RELEASE` | the release id `check-live-urls.sh` requires the live site to report, which is what makes a rollback verifiable rather than merely exiting zero |
| `CHECK_TAG` | the `X-Blog-Check` provenance this run announces on every request. **`<source>/<id>` is enforced, not merely expected**: exactly one `/`, which is the separator and the only one allowed, with both halves non-empty and each drawn from letters, digits, `.`, `_`, `-`. Rarely set by hand, since `check-live-urls.sh` derives `github/<run-id>-<attempt>` under Actions and `proxmox/manual` elsewhere. Set it to name a purpose for a hand run, as `proxmox/media-dev` |

## Two credentials to the VPS, and why they are separate

`DEPLOY_SSH_USER` reaches a confined account behind an `rrsync` forced command that can write one release tree and read nothing else. `VPS_SSH_HOST` is the ordinary administrative login used for reading logs, reading the archive directory, and moving the channel files. Reaching for the deploy account to read a log fails in a way that reads like an outage, and reaching for the admin account to deploy grants far more than the deploy needs.

## The one place indirection is wrong

The two channel transfers under [`OPERATIONS.md`](./OPERATIONS.md) "The Channel Between the Two Sides" spell out the host and directory rather than using `VPS_SSH_HOST` and `VPS_COMMS_DIR`. The permission allowlist matches the text of a command rather than what it expands to, so substituting the variables turns an allowed transfer into one that prompts, while looking like a tidy-up that changed nothing. The same rule is why neither may be chained behind `cd` or `&&`.

## Rules

- **One name per thing.** A value that appears on two sides is spelled identically on both, so neither side needs translating into the other.
- **No value naming a machine reaches git.** Not in a script default, not in a unit, not in a template. The `.example` files carry placeholders, and the real values live in `secrets/` or on the host.
- **A description belongs here and a reference belongs everywhere else.** A `.example` file says what the format is, and this file says what the value means.
- **Nothing sources some of these, and that is recorded rather than hidden.** A value kept only so a rebuild does not depend on memory is still worth holding, but a reader should not have to discover that no code reads it.
