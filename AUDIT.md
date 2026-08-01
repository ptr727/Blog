# AUDIT.md

How an agent audits **this repository** against its own committed ground truth and reports drift. The audit is read-only. It never edits the repo, and it never touches another repository.

The ground truth is what this repo commits: the payloads in [`repo-config/`](./repo-config/), the secrets manifest in [`spec/secrets.json`](./spec/secrets.json), and the prose authorities ([`GOVERNANCE.md`](./GOVERNANCE.md), [`CODESTYLE.md`](./CODESTYLE.md), [`WORKFLOW.md`](./WORKFLOW.md), [`OPERATIONS.md`](./OPERATIONS.md)). A live setting that disagrees with a committed payload is drift, and the payload is right until a human decides otherwise.

## Scope

This repo declares `types: ["source-only"]` and `workflowModel: release` with `lineEndings: "lf"`.

Two of those three are deliberate deviations from what the fleet spec would predict, recorded here rather than left to be rediscovered as drift:

- **`lineEndings: "lf"` on a `release` repo.** [`GOVERNANCE.md` "Line Endings"](./GOVERNANCE.md#line-endings) grants the native-platform default to operational repos only and holds `release` repos to the CRLF fleet default. Every consumer here is Linux: Hugo builds in CI, Caddy and OpenSSH read their config on Ubuntu, and the deploy scripts run there. Taking CRLF would mean an LF override for the shell scripts, the workflow YAML, the Caddyfile, the generated Caddy maps, and the content tree, which is the over-normalization that rule exists to prevent. The rule ties the ending to the workflow model when the thing that actually determines it is the consuming platform.
- **`types: ["source-only"]` rather than `docs`.** `docs` detects a "governance-only repo" and asserts that CI runs linting only with no build. Both are false here, since this repo builds a site with Hugo and gates it on a URL contract. `source-only` detects "no `build-*-task.yml`", which is true, and its checks describe the release shape this repo actually has. Both selectors resolve to the same 24 baseline files, so the choice costs nothing and only one of them is honest.

Three dimensions, each independently checkable:

1. **Settings and rulesets**, against the committed `repo-config/` payloads.
2. **Secrets**, by name only, against `spec/secrets.json`.
3. **The URL contract**, which is this repo's own reason to exist.

## 1. Settings and Rulesets

```sh
repo-config/configure.sh check ptr727/Blog release
```

Exits non-zero on any drift. It asserts rule presence, merge methods, and required checks rather than diffing bytes, so a ruleset GitHub has normalized does not false-positive.

Two facts specific to this repo:

- The `develop` payload is [`repo-config/develop.json`](./repo-config/develop.json), the `release` variant, which gates `develop` behind a pull request and the required status check. The `operational/develop.json` variant permits direct signed pushes and is **absent** here. Carrying it would apply the wrong ruleset.
- The required check binds by name, `Check pull request workflow status job`, and turns green only after the pull request workflow has run once.

## 2. Secrets

Names only. Never read, print, or log a secret value.

```sh
gh secret list --repo ptr727/Blog
gh secret list --repo ptr727/Blog --app dependabot
```

Assert that every name under `baseline.requires` is present in both stores, and that every name under `baseline.forbids` is absent. `CODEGEN_APP_ID` is forbidden: the App-token action takes `client-id`, and the deprecated `app-id` name silently does nothing.

The deploy credentials live in the `staging` and `production` GitHub Environments rather than in repository secrets, so a staging deploy cannot reach production. They are outside the baseline audit.

## 3. The URL Contract

The migration's whole risk is silent URL loss, so the contract is audited like any other ground truth. Both gates are demonstrated failing before they are trusted.

```sh
hugo --gc --minify --panicOnWarning
checks/check-url-parity.py public
checks/check-live-urls.sh <base-url>
```

- **The build gate** proves every URL that must render exists as a built page, that every legacy media URL resolves, and that every local asset reference points at a file that exists.
- **The live gate** proves the redirects, which the build cannot: a redirect is the web server's job. It follows each redirect to its destination rather than trusting the status code, because a redirect into a hole returns a perfectly healthy 301.
- **The floor assertions** fail when a list is truncated. Without them a shortened list makes every check below it pass while covering nothing.

A **missing** URL is a failure. An **extra** URL is reported and is not. New posts, tags, and pagination legitimately add URLs, and nothing legitimately removes one the old site served.

## Reporting

Rank findings most severe first, each with a `file:line` or a command and its output as evidence. A finding without evidence is an opinion.

State a verdict: **operational** when every applicable check passes, or **not operational** when any does not. A partial pass is not operational. Record any residual delta rather than leaving it in a session that ends.

Where a rule appears wrong rather than merely unmet, report the discrepancy rather than working around it locally. A local exception to a shared rule is drift that no later audit can distinguish from an oversight.
