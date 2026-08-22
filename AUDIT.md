# AUDIT.md

How an agent audits **this repository** against its own committed ground truth and reports drift. The audit is read-only. It never edits the repo, and it never touches another repository.

The ground truth is the hub's committed [`repo-config/`](https://github.com/ptr727/ProjectTemplate/tree/main/repo-config) payloads, which this repo does not carry a copy of, the secrets manifest in [`spec/secrets.json`](./spec/secrets.json), and the prose authorities ([`GOVERNANCE.md`](./GOVERNANCE.md), [`CODESTYLE.md`](./CODESTYLE.md), [`WORKFLOW.md`](./WORKFLOW.md), [`OPERATIONS.md`](./OPERATIONS.md)). A live setting that disagrees with the hub's payload is drift, and the payload is right until a human decides otherwise.

## Scope

This repo declares `types: ["source-only"]` and `workflowModel: release` with `lineEndings: "lf"`.

Two of those three are deliberate deviations from what the fleet spec would predict, recorded here rather than left to be rediscovered as drift:

- **`lineEndings: "lf"` on a `release` repo.** [`GOVERNANCE.md` "Line Endings"](./GOVERNANCE.md#line-endings) grants the native-platform default to operational repos only and holds `release` repos to the CRLF fleet default. Every consumer here is Linux: Hugo builds in CI, Caddy and OpenSSH read their config on Ubuntu, and the deploy scripts run there. Taking CRLF would mean an LF override for the shell scripts, the workflow YAML, the Caddyfile, the generated Caddy maps, and the content tree, which is the over-normalization that rule exists to prevent. The rule ties the ending to the workflow model when the thing that actually determines it is the consuming platform.
- **`types: ["source-only"]` rather than `docs`.** `docs` detects a "governance-only repo" and asserts that CI runs linting only with no build. Both are false here, since this repo builds a site with Hugo and gates it on a URL contract. `source-only` detects "no `build-*-task.yml`", which is true, and its checks describe the release shape this repo actually has. Both selectors resolve to the same 24 baseline files, so the choice costs nothing and only one of them is honest.

Three dimensions, each independently checkable:

1. **Settings and rulesets**, against the hub's committed `repo-config/` payloads.
2. **Secrets**, by name only, against `spec/secrets.json`.
3. **The URL contract**, which is this repo's own reason to exist.

## 1. Settings and Rulesets

```sh
# From a hub checkout, which hosts the script rather than this repo carrying a copy.
repo-config/configure.sh check ptr727/Blog release
```

Exits non-zero on any drift. It asserts rule presence, merge methods, and required checks rather than diffing bytes, so a ruleset GitHub has normalized does not false-positive.

Two facts specific to this repo:

- The `develop` payload is the hub's [`repo-config/develop.json`](https://github.com/ptr727/ProjectTemplate/blob/main/repo-config/develop.json), the `release` variant, which gates `develop` behind a pull request and the required status check. The `operational/develop.json` variant permits direct signed pushes and does not apply here, since this repo's `workflowModel` is `release`.
- The required check binds by name, `Check pull request workflow status job`, and turns green only after the pull request workflow has run once.

## 2. Secrets

Names only. Never read, print, or log a secret value.

Two scopes, checked separately, because a name present in one is not present in the other. The **repository** scope carries the merge bot's credentials, and the **environment** scope carries the deploy's. This is the only repo in the fleet whose publishing credentials are environment-scoped, so a check written for repository secrets alone reports a clean pass over an unconfigured deploy.

### Repository scope

```sh
gh secret list --repo ptr727/Blog
gh secret list --repo ptr727/Blog --app dependabot
```

Assert that every name under `baseline.requires` is present in both stores, and that every name under `baseline.forbids` is absent. `CODEGEN_APP_ID` is forbidden: the App-token action takes `client-id`, and the deprecated `app-id` name silently does nothing.

### Environment scope

`configure.sh check` does not reach these and says so, deferring the secrets question to a manual verification. Assert them against `spec/secrets.json`:

```sh
# Read the lists first, so a moved key fails here rather than emptying the loop below.
envs=$(jq -e -r '.environments.names[]' spec/secrets.json) || exit 1
jq -e '.environments.environmentSecrets' spec/secrets.json > /dev/null || exit 1

for env in $envs; do
  gh secret list   --repo ptr727/Blog --env "$env" --json name --jq '.[].name'
  gh variable list --repo ptr727/Blog --env "$env" --json name --jq '.[].name'
done
```

`--json name` is not decoration. The bare `gh variable list` prints a value column, and when its output is captured rather than shown it prints each value in full, so an audit run without it writes the deploy endpoint into its own log. Never request the `value` field here, and never use `gh variable view`, which prints one by design.

**Assert the query matched before reading what it returned.** A `jq` path that no longer resolves yields nothing, a loop over nothing runs zero times, and a check that counts failures reports none. Every lookup is `jq -e`, which exits non-zero on a null or missing key, and each is **assigned before it is iterated**: command substitution in a `for` header discards the exit status, so a guard written there is a guard that never fires.

Three assertions, and the third is the one presence-checking misses:

- Every name under `environments.secrets` and `environments.variables` is present in **every** environment named in `environments.names`.
- Every name under `environmentSecrets.<env>` is present in that environment.
- A name under `environmentSecrets` is **absent** from an environment that does not list it. `production` holding a Pangolin access token is a finding rather than a harmless extra: production answers unauthenticated, so a token there means a check could pass through a gate production is not supposed to have.

A **declared but unset** name is drift in the same way an undeclared one is. The deploy root is deliberately not declared, because the rsync destination is anchored at the deploy key's confinement root and the workflow names an environment rather than a host path.

Never read, print, or log a value. Every command above lists names.

## 3. The URL Contract

This site's whole risk is silent URL loss, so the contract is audited like any other ground truth. Both gates are demonstrated failing before they are trusted.

```sh
hugo --gc --minify --panicOnWarning
checks/check-url-parity.py public
checks/check-live-urls.sh <base-url>
```

- **The build gate** proves every URL that must render exists as a built page, that every legacy media URL resolves, and that every local asset reference points at a file that exists.
- **The live gate** proves the redirects, which the build cannot: a redirect is the web server's job. It follows each redirect to its destination rather than trusting the status code, because a redirect into a hole returns a perfectly healthy 301.
- **The floor assertions** fail when a list is truncated. Without them a shortened list makes every check below it pass while covering nothing.

A **missing** URL is a failure. An **extra** URL is reported and is not. New posts, tags, and pagination legitimately add URLs, and nothing legitimately removes one the site has served.

## Reporting

Rank findings most severe first, each with a `file:line` or a command and its output as evidence. A finding without evidence is an opinion.

State a verdict: **operational** when every applicable check passes, or **not operational** when any does not. A partial pass is not operational. Record any residual delta rather than leaving it in a session that ends.

Where a rule appears wrong rather than merely unmet, report the discrepancy rather than working around it locally. A local exception to a shared rule is drift that no later audit can distinguish from an oversight.
