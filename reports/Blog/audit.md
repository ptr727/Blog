# Blog Audit

Self-audit of this repository against its own committed ground truth, per [AUDIT.md](../../AUDIT.md), and against the fleet ground truth the hub publishes. Read-only, and confined to this repository. It replaces the 2026-08-01 run rather than editing it, which is what the run-stamp discipline asks for: a run records what it observed, and a later run supersedes the whole file.

**Date:** 2026-08-05
**Hub ref carried:** `main` `3b802b9`
**Run stamps:** `audit run 2026-08-05T14:12:14Z | hub 3b802b9` and `audit run 2026-08-05T14:13:11Z | hub 2a1afc0` (the second reads the hub's unpromoted `develop`)
**Declared:** `types: ["source-only"]`, `workflowModel: release`, `lineEndings: "lf"`, `releaseTrigger: dispatch-only`

## Verdict

**Operational.** Every applicable check passes, and the two open drift findings are both blocked on something outside this repository.

| Dimension | Result |
| --- | --- |
| 1. Settings and rulesets | **Pass.** `configure.sh check` exits 0 on 22 assertions |
| 2. Secrets, repository scope | **Pass.** Both required present in both stores, the forbidden one absent |
| 3. Secrets, environment scope | **Pass.** Both environments carry every declared name |
| 4. The URL contract | **Pass.** Gated in CI on the build, and against the running site on a deploy |
| 5. Hub conformance run | **Pass** on the mechanized subset, two drifts outstanding |
| 6. The `hugo` type, hand-evaluated | **Pass** on eight of nine checks, one drift |
| Release | **Pass.** Dispatch-only, newest is `1.0.17-g4b2def3ee9` from `develop` |
| Deploy | **Pass.** Proven end to end against VPS staging by pipeline |

## What Changed Since the Previous Run

The 2026-08-01 run recorded the deploy as deferred and the VPS as not provisioned. Both have since happened, so the deferral this repository declared is closed rather than carried:

- `deploy-site.yml` is dispatchable and has deployed staging from CI end to end, verified against the live site by release id rather than by the transport's exit status.
- The `staging` and `production` environments exist and hold their credentials.
- The hub authored the `hugo` type and the `self-hosted` target from this repository's measured shape, which is what [ProjectTemplate#456][hub-issue] and [#558][hub-spec-issue] were holding for. Both are closed.

## 1. Settings and Rulesets

**Pass.**

```text
$ repo-config/configure.sh check
... 22 assertions, all ok ...
Configuration matches on ptr727/Blog.
exit 0
```

This run is the first with the re-vendored comparator, which compares `copilot_code_review` parameters as well as `pull_request` and `required_status_checks`, so three parameterized rules per ruleset are now compared rather than two.

Both rulesets are active. `develop` allows squash only, `main` allows merge only, and both bind the required check by the name the workflow produces. `has_discussions = true` follows public visibility, `default_branch = main`, and both Dependabot security features are enabled.

Each ruleset carries a `RepositoryRole 5` bypass entry that the payloads do not declare. `configure.sh check` reports it as unmanaged and exits 0, which is the correct reading: the owner holds that capability by role regardless, so the entry grants nothing the payload could withhold.

## 2. Secrets, Repository Scope

**Pass.** Names only. No secret value was read, printed, or logged.

| Name | Actions | Dependabot |
| --- | --- | --- |
| `CODEGEN_APP_CLIENT_ID` | present | present |
| `CODEGEN_APP_PRIVATE_KEY` | present | present |
| `CODEGEN_APP_ID` (forbidden) | absent | absent |

## 3. Secrets, Environment Scope

**Pass**, against [`spec/secrets.json`](../../spec/secrets.json)'s `environments` block. No fleet tool reads this block, because neither the hub's validator nor its audit runner can enumerate an environment-scoped store, so this section is the only thing that checks these names at all.

| Name | Kind | `staging` | `production` |
| --- | --- | --- | --- |
| `DEPLOY_SSH_PRIVATE_KEY` | secret | present | present |
| `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_SSH_KNOWN_HOSTS` | variable | present | present |
| `HUGO_BASEURL` | variable | present | present |
| `PANGOLIN_ACCESS_TOKEN_ID`, `PANGOLIN_ACCESS_TOKEN` | secret, staging only | present | absent, as declared |

A third environment, `copilot`, exists and holds no variables, no secrets, and no protection rules. GitHub creates it for its coding agent. It is recorded here because an environment that appears without being declared is exactly what this section exists to notice, and because an empty one is the only safe shape for it: `secrets: inherit` in [`deploy-site.yml`](../../.github/workflows/deploy-site.yml) passes repository secrets to the callee, and no path binds `copilot` to a deploy.

## 4. The URL Contract

**Pass, on both halves, and the second half now runs in CI.**

The build half is gated on every pull request. [`checks/check-url-parity.py:16`](../../checks/check-url-parity.py) declares floors under the known-good counts, so a truncated list fails rather than passing while covering nothing, and [`.github/workflows/validate-task.yml:88`](../../.github/workflows/validate-task.yml) runs it against the built tree.

The live half was a hand-run step against a local mirror at the previous audit. It is now the terminal step of the deploy ([`deploy-site-task.yml:155`](../../.github/workflows/deploy-site-task.yml)), which runs [`checks/check-live-urls.sh:18`](../../checks/check-live-urls.sh) against the environment it just wrote, with its own floors, `EXPECT_SITE_ENV`, and `EXPECT_RELEASE`. All 1,245 URLs were verified this way against VPS staging behind its auth gate, in run `30959030274` on 2026-08-04: 328 that must render, 917 that must redirect, `PASS - 1245 URLs honored`.

## 5. Hub Conformance Run

The hub's `spec/audit.py` was run three times against this repository: `main`, `develop`, and the convergence branch, all from a full hub clone so the stale-versus-modified classification could walk the canonical's history.

Findings before the fixes in this change, identical on `main` and `develop`:

```text
DRIFT  branch: 1 path(s) changed on both main and develop since the merge-base ...
DRIFT  carried: AGENTS.md references the template repo by name or link
DRIFT  verbatim: repo-config/configure.sh matches a past hub revision, not the current canonical
LETTER history: HISTORY.md intro does not mirror the README intro
```

After, on the convergence branch:

```text
DRIFT  branch: 1 path(s) changed on both main and develop since the merge-base ...
DRIFT  carried: AGENTS.md references the template repo by name or link
1 repo(s) audited; 0 defect/letter/error finding(s).
```

Both remaining findings are blocked outside this change:

- **The branch drift is a promotion, not a divergence.** `.github/workflows/validate-task.yml` changed on both branches since the merge-base, because the same Dependabot bump landed on each independently and `develop` also carries the generator-pin change. Compared directly, `develop` supersedes `main` on every line of that file, so the reconciliation is the `develop -> main` promotion and nothing else.
- **The `AGENTS.md` finding cannot be cleared from here.** The `Fleet Bootstrap` section is byte-locked across the fleet and names the hub, while the same audit forbids a carried file from naming it. Carrying the canonical correctly cannot pass, which is [ProjectTemplate#552][issue-552].

## 6. The `hugo` Type, Hand-Evaluated

The hub authored a nine-check `hugo` type from this repository's measured deploy shape. It is on the hub's `develop` and **not** on `main`, so it is not ground truth yet and this section is anticipatory: it records what a promoted type would find, so the promotion is not the first time anyone looks.

**Nothing mechanizes these checks.** `spec/audit.py` does not read `spec/project-types.json` at all, so a clean run of it says nothing about any of the nine, and reading one as evidence would be the empty-query trap this repository has been caught by before. Every row below was evaluated by hand against the file it cites.

| Check | Verdict | Evidence |
| --- | --- | --- |
| `hugo.build.strict` | **Pass** | `hugo --gc --minify --panicOnWarning` at [`validate-task.yml:83`](../../.github/workflows/validate-task.yml) and [`deploy/make-release.sh:94`](../../deploy/make-release.sh), the same command on both paths |
| `hugo.urls.parity` | **Pass** | Floors at [`check-url-parity.py:16`](../../checks/check-url-parity.py) and [`check-live-urls.sh:18`](../../checks/check-live-urls.sh), both under the committed counts |
| `hugo.output.uncommitted` | **Pass** | `public/` ignored at [`.gitignore:5`](../../.gitignore), nothing tracked under it, and the markdown glob excludes `content/**`, `themes/*/**`, and `public/**` |
| `hugo.generator.pinned` | **Pass** | Version and SHA256 declared once, in [`.github/actions/install-hugo/action.yml:26`](../../.github/actions/install-hugo/action.yml), verified before install |
| `hugo.vendored.provenance` | **Pass** | Upstream, commit, and local edits recorded at [`themes/README.md:12`](../../themes/README.md) |
| `hugo.deploy.environment` | **Pass** | Environment re-asserted in its own job at [`deploy-site-task.yml:38`](../../.github/workflows/deploy-site-task.yml), bound at `:62`, every host value from `vars` |
| `hugo.deploy.atomic` | **Pass** | Upload to `releases/<id>/` at `:124`, pointer flipped by `rsync` through a temporary and a rename at `:140`, no `--delete` anywhere |
| `hugo.deploy.verified` | **Pass** | `EXPECT_RELEASE` and `EXPECT_SITE_ENV` at `:155`, polled to a bounded timeout at [`check-live-urls.sh:155`](../../checks/check-live-urls.sh), with an unreachable host reported distinctly at `:144` |
| `hugo.deploy.retention` | **Drift** | See below |

**`hugo.deploy.retention` is the one that does not pass cleanly.** The check accepts two shapes, and this repository is the second: the deploy credential is a forced `rsync` command confined write-only, so it can neither delete a release nor read the destination back to count one, and the prune therefore belongs to the host. That ownership is recorded, at [`OPERATIONS.md:176`](../../OPERATIONS.md). What is not recorded is the count that binds the host: the "Ten releases are kept" in the Retention section above it describes `deploy/make-release.sh`, which installs on the local mirrors and prunes there, and no line says what the VPS containers keep or that their timer exists. The check asks for a declared count at the destination, and the destination the pipeline writes to has none.

This is a documentation gap rather than a disk-space one, and it is not this repository's to fill alone, since the count is the host's to declare. It is carried as a residual delta below rather than guessed at here.

**One observation that no check covers.** The build command is written out twice, at the two citations in the first row, with nothing asserting the two copies agree. That is the same shape as the generator pin before [#29][issue-29] moved it into a composite action, one class down in severity: a one-sided edit would validate with one command and ship a tree built by another. The pin itself is now single-sourced, so the exposure is the flag set rather than the generator.

## Baseline File Presence and Verbatim Fidelity

**Pass.** Every carried file the scope selectors resolve to is present, and every verbatim unit matches the hub canonical after line-ending normalization, which is what this change's re-vendor of `repo-config/configure.sh` restored.

## Deliberate Deviations

Both are unchanged, recorded in [AUDIT.md](../../AUDIT.md), and reported upstream, so neither reads as drift later.

1. **`lineEndings: "lf"` on a `release` repo**, where the rule grants the native-platform default to operational repos only. Every consumer here is Linux.
2. **`types: ["source-only"]` rather than `docs`**, because both `docs` predicates are false for a repository that builds a site and gates a URL contract. The hub's unpromoted `develop` adds `hugo` alongside it, which resolves this deviation rather than replacing it.

## Residual Deltas

Carried forward rather than closed:

- **The retention count at the VPS destination is undeclared**, per section 6. Confirming that the host's prune timer exists and what it keeps is a question for the host side, and the answer belongs in `OPERATIONS.md` next to the ownership line that already points there.
- **The deploy transport's new SSH options have not been exercised against the real host**, which is [#33][issue-33]. They fail closed where the previous configuration failed open, so a stale `DEPLOY_SSH_KNOWN_HOSTS` now stops a deploy rather than being tolerated.
- **A rollback through the pipeline is unproven.** The server side rolls back in well under a second by hand, and a two-phase upload-then-flip should make a part-way failure safe, but no failing run has demonstrated it.
- **The `hugo` type is not ground truth yet.** Section 6 is anticipatory until the hub promotes it to `main`, at which point this repository's registry entry, its own `spec/secrets.json` note, and the type row above all become measurable rather than predicted.

<!-- Repo -->

[issue-29]: https://github.com/ptr727/Blog/issues/29
[issue-33]: https://github.com/ptr727/Blog/issues/33

<!-- External -->

[hub-issue]: https://github.com/ptr727/ProjectTemplate/issues/456
[hub-spec-issue]: https://github.com/ptr727/ProjectTemplate/issues/558
[issue-552]: https://github.com/ptr727/ProjectTemplate/issues/552
