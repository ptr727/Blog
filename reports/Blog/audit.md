# Blog Audit

Self-audit of this repository against its own committed ground truth, per [AUDIT.md](../../AUDIT.md). Read-only, and confined to this repository.

**Date:** 2026-08-01
**Hub ref carried:** `ptr727/ProjectTemplate` `main` `6501479`
**Declared:** `types: ["source-only"]`, `workflowModel: release`, `lineEndings: "lf"`

## Verdict

**Operational.** Every applicable check passes against the live repository.

The publish and release surface is **deferred**, not failed. That deferral is declared rather than hidden, and is tracked in [ProjectTemplate#456][hub-issue], which [`STANDUP.md` section 5][standup] permits.

| Dimension | Result |
| --- | --- |
| 1. Settings and rulesets | **Pass.** `configure.sh check` exits 0 |
| 2. Secrets | **Pass.** Both required present in both stores, forbidden one absent |
| 3. The URL contract | **Pass.** Enforced by CI, not only locally |
| Baseline file presence | **Pass.** 23 of 23 |
| Verbatim fidelity | **Pass.** 4 of 4 |
| Publish and release | **Deferred**, deliberately |

## 1. Settings and Rulesets

**Pass.**

```text
$ repo-config/configure.sh check ptr727/Blog release
... 31 assertions, all ok ...
Configuration matches on ptr727/Blog.
exit 0
```

Both rulesets are active and carry every expected rule. `develop` allows squash only, `main` allows merge only, and both bind the required check by the same name the workflow produces:

```text
'develop' required checks = ["Check pull request workflow status job"]
'main'    required checks = ["Check pull request workflow status job"]
```

The ordering constraint was honored at standup: the workflow was dispatched once and reported before any ruleset was applied. Applying first would have deadlocked the first pull request, because the required check binds by name and only appears after a run.

`has_discussions = true`, derived by `configure.sh` from public visibility rather than from a committed setting. `default_branch = main`. Dependabot vulnerability alerts and automated security updates are enabled.

## 2. Secrets

**Pass.** Names only. No secret value was read, printed, or logged.

| Name | Actions | Dependabot |
| --- | --- | --- |
| `CODEGEN_APP_CLIENT_ID` | present | present |
| `CODEGEN_APP_PRIVATE_KEY` | present | present |
| `CODEGEN_APP_ID` (forbidden) | absent | absent |

`CODEGEN_APP_ID` is forbidden because the App-token action takes `client-id`, and the deprecated `app-id` name silently does nothing.

The `staging` and `production` environments do not exist yet, which is correct: they hold deploy credentials for a VPS that has not been provisioned, and `AUDIT.md` places them outside the baseline audit.

## 3. The URL Contract

**Pass, and now enforced by CI rather than only locally**, which is the material change from the pre-standup state.

From the first run on `main`:

```text
hugo v0.164.0+extended            (pinned by version and sha256)
Pages 514 | Total in 858 ms       (zero warnings under --panicOnWarning)
render : 328/328 golden URLs built
media  : 778/778 legacy image URLs resolve after the @uploads rewrite
assets : 1012/1012 local asset references resolve
PASS - the built site honors the URL contract
```

Every gate in the validation job passed on its first attempt: markdownlint, cspell, actionlint, `editorconfig-checker`, shellcheck, `shfmt -d`, config validation, the Hugo build, and the contract check.

Floor assertions are present and below the real counts, so a truncated list fails rather than passing while covering nothing:

```text
checks/check-live-urls.sh:18  FLOOR=(["golden-urls.txt"]=320 ["redirect-urls.txt"]=900)
```

**The redirect half is proven, against a running server rather than a build.** `deploy/make-release.sh` installs the build on the local mirror, then `checks/check-live-urls.sh` follows all 1,245 URLs against it, checking each redirect's destination rather than trusting its status code:

```text
==> checking 328 URLs that must render
==> checking 917 URLs that must redirect
PASS - 1245 URLs honored
```

That is a local mirror, not CI and not production. CI cannot run it, because the validation workflow has no server to point at, so this remains a pre-pull-request step documented in [OPERATIONS.md](../../OPERATIONS.md) rather than an automated gate. It becomes automatable once staging exists.

## Baseline File Presence

**Pass, 23 of 23** applicable to `types: ["source-only"]` plus `workflowModel: release`.

`OPERATIONS.md` is retained although it left the required set when the workflow model changed from `operational` to `release`. Carrying an extra file is not drift.

## Verbatim Fidelity

**Pass, 4 of 4**, compared after line-ending normalization as [`spec/fidelity-model.md`][fidelity] specifies: `.markdownlint-cli2.jsonc`, `repo-config/configure.sh`, `repo-config/main.json`, `repo-config/develop.json`.

Eight carried files arrived CRLF and were normalized to LF to satisfy this repository's declared `lineEndings`. That is governed drift rather than a fidelity deviation, and it is reported upstream as an onboarding trap, since nothing in the standup text says to normalize after carrying.

## Publish and Release: Deferred

`publish` is empty and `releaseTrigger` is `none`, deliberately.

This repository will deploy a built site to a VPS over SSH, which is a release surface the fleet spec has no type for. The measured shape will be reported to [ProjectTemplate#456][hub-issue] once CI has run a deploy, rather than predicted now. The VPS does not exist, so there is nothing to measure.

`publish-release.yml` exists and is dispatch-only, but has never been dispatched. The release path is therefore untested.

## Deliberate Deviations

Both are recorded in [AUDIT.md](../../AUDIT.md) and reported upstream, so neither can later read as drift.

1. **`lineEndings: "lf"` on a `release` repo.** `GOVERNANCE.md` "Line Endings" grants the native-platform default to operational repos only. Every consumer here is Linux, and the fleet CRLF default would need an LF override for the scripts, the workflow YAML, the Caddyfile, the generated maps, and the content tree, which is the over-normalization that rule exists to prevent. The rule keys on `workflowModel` when the determining factor is the consuming platform.
2. **`types: ["source-only"]` rather than `docs`.** Both `docs` predicates are false: it detects a "governance-only repo" and asserts lint-only CI with no build, while this repo builds a site and gates a URL contract. `source-only` detects "no `build-*-task.yml`", which is true. Both selectors resolve to the same baseline file set, so only one of them is honest and it costs nothing.

## Residual Deltas

Carried forward rather than closed:

- The redirect half of the contract is proven only against the local mirror, by hand, before a pull request. CI has no server to point at, so nothing enforces it automatically until staging exists.
- `publish-release.yml` has never been dispatched, so the release path is untested.
- No deploy exists, so the publish surface stays deferred and the registry entry stays `publish: []`.
- `checks/README.md` carries a small prose backlog of `dash` and `semicolon` findings, left for the next edit of that file per the correct-as-you-next-edit rule.

<!-- Repo -->

[fidelity]: https://github.com/ptr727/ProjectTemplate/blob/main/spec/fidelity-model.md
[standup]: https://github.com/ptr727/ProjectTemplate/blob/main/STANDUP.md

<!-- External -->

[hub-issue]: https://github.com/ptr727/ProjectTemplate/issues/456
