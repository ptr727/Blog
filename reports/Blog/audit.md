# Blog Audit

Self-audit of this repository against its own committed ground truth, per [AUDIT.md](../../AUDIT.md). Read-only, and confined to this repository.

**Date:** 2026-08-01
**Hub ref carried:** `ptr727/ProjectTemplate` `main` `6501479`
**Declared:** `types: ["source-only"]`, `workflowModel: release`, `lineEndings: "lf"`

## Verdict

**Not operational.** Two of the three dimensions cannot be checked at all, because the repository does not exist on GitHub yet. Nothing has been pushed, so there is no remote, no ruleset, no secret, and no environment.

This is the expected state at this point rather than a failure, and it is recorded here rather than left in a session, per [`STANDUP.md` section 5][standup], which allows a repo to stand up with residual deltas tracked in a report plus an issue. The issue is [ProjectTemplate#456][hub-issue].

Every check that can run locally passes. The value of that is limited, and stating it plainly is the point of this report: local checks pass by construction because the same person wrote the checks and the thing being checked. Only a real CI run and a real deploy test the parts that matter, and neither has happened.

| Dimension | Result |
| --- | --- |
| 1. Settings and rulesets | **Blocked.** No repository on GitHub |
| 2. Secrets | **Blocked.** No repository on GitHub |
| 3. The URL contract | **Pass** |
| Baseline file presence | **Pass.** 23 of 23 |
| Verbatim fidelity | **Pass.** 4 of 4 |
| Publish and release | **Deferred**, deliberately. See below |

## 1. Settings and Rulesets

Blocked. `repo-config/configure.sh check ptr727/Blog release` cannot run against a repository that does not exist.

What is verifiable locally is that the payloads are internally consistent and that the required check is bound by a name the workflow actually produces, which is the ordering trap that deadlocks a first pull request:

```text
repo-config/main.json  required_status_checks: ["Check pull request workflow status job"]
.github/workflows/test-pull-request.yml:26  name: Check pull request workflow status job
```

The two strings match. They are one string renamed together, never independently.

The carried `develop` payload is the `release` variant (`repo-config/develop.json`), carrying `pull_request`, `required_status_checks`, `required_linear_history`, `copilot_code_review`, `deletion`, `non_fast_forward`, and `required_signatures`. The `operational/develop.json` variant is absent, which is correct for this workflow model.

## 2. Secrets

Blocked. `gh secret list` cannot run against a repository that does not exist.

The manifest in `spec/secrets.json` declares:

- `requires`: `CODEGEN_APP_CLIENT_ID`, `CODEGEN_APP_PRIVATE_KEY`, in **both** the Actions and Dependabot stores
- `forbids`: `CODEGEN_APP_ID`

No secret value has been read, printed, or logged.

## 3. The URL Contract

**Pass.** This is the only dimension with real evidence behind it, because it is the only one that does not need GitHub.

```text
$ hugo --gc --minify --panicOnWarning
Pages 514 | Total in 462 ms | zero warnings

$ checks/check-url-parity.py public
render : 328/328 golden URLs built
         207 additional URLs built (not a failure)
media  : 778/778 legacy image URLs resolve after the R8 rewrite
assets : 1012/1012 local asset references resolve
PASS - the built site honors the URL contract
```

Contract sizes, matching the committed lists: 328 render, 917 redirect, 778 legacy media.

Floor assertions are present and below the real counts, so a truncated list fails rather than passing while covering nothing:

```text
checks/check-live-urls.sh:18  FLOOR=(["golden-urls.txt"]=320 ["redirect-urls.txt"]=900)
```

The 207 extra built URLs are the new post added this session plus its four new term archives and their pagination. An extra URL is reported and is not a failure. A missing one would be.

**The live gate has not run this session.** `checks/check-live-urls.sh` is what proves the 917 redirects, and a redirect is the web server's job that no build can prove. It has previously passed against the local mirror for all 1,245 URLs, but that predates this session's changes and is not re-evidenced here. Treat the redirect half of the contract as asserted rather than currently proven.

## Baseline File Presence

**Pass, 23 of 23** applicable to `types: ["source-only"]` plus `workflowModel: release`.

`OPERATIONS.md` is retained although it left the required set when the workflow model changed from `operational` to `release`. It is accurate and useful, and carrying an extra file is not drift.

## Verbatim Fidelity

**Pass, 4 of 4**, compared after line-ending normalization as [`spec/fidelity-model.md`][fidelity] specifies:

```text
.markdownlint-cli2.jsonc      match
repo-config/configure.sh      match
repo-config/main.json         match
repo-config/develop.json      match
```

Eight carried files arrived CRLF and were normalized to LF to satisfy this repository's declared `lineEndings`. That is governed drift rather than a fidelity deviation, and it is reported to the hub as an onboarding trap, since nothing in the standup text says to normalize after carrying.

## Lint and Prose

Every gate the validation workflow runs was executed locally, through Docker, since the host lacks the tools:

```text
actionlint                                   clean
editorconfig-checker                         clean
markdownlint-cli2 (workflow globs)           0 issues in 14 files
cspell (README.md, HISTORY.md)               0 issues
shellcheck (default severity)                clean
shfmt -d                                     clean
```

Prose rules, using the hub's `scripts/prose_lint.py` against every file this repo authors:

```text
charset, dupword, comment-wrap, comment-case   0 findings
dash, semicolon, charset-unknown               15 findings
```

The 15 remaining are backlog rules that report without gating, and the correct-as-you-next-edit rule leaves them alone until their file is touched:

- `checks/README.md`, 14. Not edited this session.
- `layouts/rss.xml`, 1. **Kept deliberately.** The copyright sign is the argument to `strings.TrimPrefix "© "`, so it is a string literal that must match the character it strips, not typography. It is a functional deviation, not an unswept one.

## Publish and Release: Deferred

`publish` is empty and `releaseTrigger` is `none` in the proposed registry entry, deliberately.

This repository deploys a built site to a VPS over SSH, which is a release surface the fleet spec has no type for. The hub's position, which this repo follows, is to declare the deferral rather than hide it, and to report the measured shape after CI has run and a deploy has actually happened rather than predicting it. Tracked in [ProjectTemplate#456][hub-issue].

The VPS does not exist yet, so there is nothing to measure.

## Deliberate Deviations

Both are recorded in [AUDIT.md](../../AUDIT.md) and reported upstream, so neither can later read as drift.

1. **`lineEndings: "lf"` on a `release` repo.** `GOVERNANCE.md` "Line Endings" grants the native-platform default to operational repos only. Every consumer here is Linux, and the fleet CRLF default would need an LF override for the scripts, the workflow YAML, the Caddyfile, the generated maps, and the content tree, which is the over-normalization that rule exists to prevent. The rule keys on `workflowModel` when the determining factor is the consuming platform.
2. **`types: ["source-only"]` rather than `docs`.** Both `docs` predicates are false: it detects a "governance-only repo" and asserts lint-only CI with no build, while this repo builds a site and gates a URL contract. `source-only` detects "no `build-*-task.yml`", which is true. Both selectors resolve to the same baseline file set, so only one of them is honest and it costs nothing.

## Residual Deltas

Carried forward rather than closed:

- The repository does not exist on GitHub. Dimensions 1 and 2 stay unverifiable until it does, and the first CI run is the first real test of the workflows.
- The live redirect gate has not run against this session's build.
- `merge-bot-pull-request.yml` is not carried. Dependabot is configured, so its pull requests will sit open until either the merge bot is added or they are merged by hand. The bot needs the App secrets, so it cannot be proven before those exist.
- `checks/README.md` carries 14 prose backlog findings.

<!-- Repo -->

[fidelity]: https://github.com/ptr727/ProjectTemplate/blob/main/spec/fidelity-model.md
[standup]: https://github.com/ptr727/ProjectTemplate/blob/main/STANDUP.md

<!-- External -->

[hub-issue]: https://github.com/ptr727/ProjectTemplate/issues/456
