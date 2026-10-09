# AUDIT.md

How an agent audits **this repository** against its ground truth and reports drift. The audit is read-only: it never edits this repo, and it reads the hub only, never writes to it or any other repository.

The ground truth is the hub's committed `repo-config/` payloads and secrets manifest, neither of which this repo carries a copy of, and the prose authorities ([`GOVERNANCE.md`][governance], [`CODESTYLE.md`][codestyle], [`WORKFLOW.md`][workflow], [`OPERATIONS.md`][operations], [`ENVIRONMENT.md`][environment]). A live setting that disagrees with the hub's payload is drift, and the payload is right until a human decides otherwise.

## Scope

This repo declares `types: ["hugo", "source-only", "python"]` and `workflowModel: release` with `lineEndings: "lf"`, the fleet default for a release repo.

One audit finding is expected rather than drift. `capture/` is one-shot migration tooling that has already run, so it is deliberately left out of the declared Python directories. A python-directories finding naming files under `capture/` is that decision, not a gap.

Three dimensions, each independently checkable:

1. **Settings and rulesets**, against the hub's committed `repo-config/` payloads.
2. **Secrets**, by name only, against the hub's manifest for the repository scope and against [`ENVIRONMENT.md`][environment] for the environment scope.
3. **The URL contract**, which is this repo's own reason to exist.

## 1. Settings and Rulesets

```sh
# From a hub checkout, which hosts the script rather than this repo carrying a copy.
repo-config/configure.sh check ptr727/Blog release
```

Exits non-zero on any drift. It asserts rule presence, merge methods, and required checks rather than diffing bytes, so a ruleset GitHub has normalized does not false-positive.

Two facts specific to this repo:

- The `develop` payload is the hub's `repo-config/develop.json`, the `release` variant, which gates `develop` behind a pull request and the required status check. The `operational/develop.json` variant permits direct signed pushes and does not apply here, since this repo's `workflowModel` is `release`.
- The required check binds by name, `Check pull request workflow status job`, and turns green only after the pull request workflow has run once.

## 2. Secrets

Names only. Never read, print, or log a secret value.

Two scopes, checked separately, because a name present in one is not present in the other. The **repository** scope carries the merge bot's credentials, and the **environment** scope carries the deploy's. This is the only repo in the fleet whose publishing credentials are environment-scoped, so a check written for repository secrets alone reports a clean pass over an unconfigured deploy.

### Repository scope

This repo carries no secrets registry of its own. The required and forbidden repository-secret names are the fleet baseline plus whatever the registry entry's `requiredSecrets` adds, both resolved and cross-checked against the live stores by the hub's own runner:

```sh
# From a hub checkout, which hosts the registry rather than this repo carrying a copy.
python3 spec/audit.py Blog
```

The baseline is two required names, `CODEGEN_APP_CLIENT_ID` and `CODEGEN_APP_PRIVATE_KEY`, in both the Actions and the Dependabot store, and one forbidden name, `CODEGEN_APP_ID`. `CODEGEN_APP_ID` is forbidden because the App-token action takes `client-id`, and the deprecated `app-id` name silently does nothing. Read the names from the run rather than from this paragraph when the two disagree, since the hub computes them and this restates them.

```sh
gh secret list --repo ptr727/Blog
gh secret list --repo ptr727/Blog --app dependabot
```

### Environment scope

No fleet tool reaches these. `configure.sh check` asserts that each environment the registry declares exists and carries its declared branch policy, and says outright that it reads neither secrets nor variables.

One key covers both environments, a deliberate decision recorded in `OPERATIONS.md`. The per-environment split only pays where the two keys never share a machine. Both sit on one workstation and in one secret store. The split still carries the base URLs, the SSH endpoint, and the staging-only access tokens, so it is not decorative.

`ENVIRONMENT.md`'s "The GitHub Environments" table declares every secret and variable name, its kind, and each store holding it. This repo's own check compares that table against GitHub:

```sh
python3 checks/check-github-env.py
```

It compares in both directions and reports three kinds of finding. A store lacks a declared name, a store holds a name the table does not list, or a value is held as the wrong kind. The second is the one presence-checking misses. A Pangolin access token on `production` is reported as unlisted rather than passed as a harmless extra. Production answers unauthenticated, so a token there means a check could pass through a gate production is not supposed to have.

It needs a `gh` login that can administer the repository, since listing environment secrets requires that. Exit 2 means GitHub could not be read, which is not a pass. The deploy root is deliberately not declared. The rsync destination is anchored at the deploy key's confinement root, and the workflow names an environment rather than a host path.

Never read, print, or log a value. The check reads names only. A name checked by hand is listed with `--json name`, since the bare `gh variable list` prints each value in full when its output is captured. Never use `gh variable view`, which prints one by design.

## 3. The URL Contract

This site's whole risk is silent URL loss, so the contract is audited like any other ground truth. Both gates are demonstrated failing before they are trusted.

```sh
hugo --gc --minify --panicOnWarning
checks/check-url-parity.py public
checks/check-live-urls.sh <base-url>
```

Run the live gate against a local mirror, which checks every URL. Against the VPS production site, set `SAMPLE_CONTRACT=1`, because the edge there bans a client that requests the whole contract.

- **The build gate** proves every URL that must render exists as a built page, that every legacy media URL resolves, and that every local asset reference points at a file that exists.
- **The live gate** proves the redirects, which the build cannot: a redirect is the web server's job. It follows each redirect to its destination rather than trusting the status code, because a redirect into a hole returns a perfectly healthy 301. A sampled production run checks each redirect's status and `Location` without following it, so an audit proves destinations on a local mirror.
- **The floor assertions** fail when a list is truncated. Without them a shortened list makes every check below it pass while covering nothing.

A **missing** URL is a failure. An **extra** URL is reported and is not. New posts, tags, and pagination legitimately add URLs, and nothing legitimately removes one the site has served.

## Reporting

Rank findings most severe first, each with a `file:line` or a command and its output as evidence. A finding without evidence is an opinion.

State a verdict: **operational** when every applicable check passes, or **not operational** when any does not. A partial pass is not operational. Record any residual delta rather than leaving it in a session that ends.

Where a rule appears wrong rather than merely unmet, report the discrepancy rather than working around it locally. A local exception to a shared rule is drift that no later audit can distinguish from an oversight.

<!-- Repo -->

[codestyle]: ./CODESTYLE.md
[environment]: ./ENVIRONMENT.md
[governance]: ./GOVERNANCE.md
[operations]: ./OPERATIONS.md
[workflow]: ./WORKFLOW.md
