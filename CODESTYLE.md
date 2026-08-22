# Code Style and Formatting Rules

This is the single code-style guide for the fleet. The **General** section applies to every language. Each **language section** (.NET, Shell, Hugo, Python) is self-contained: a repo follows only the section(s) for the languages it ships and ignores the rest. A repo keeps the whole file rather than trimming it. An unused-language section costs nothing, the same whole-file model as [`.editorconfig`][root], whose inert `[*.cs]` block a non-.NET repo keeps.

Cross-cutting *process* rules (PR titles, branching, US English, Markdown style, comments philosophy, workflow YAML, PR review etiquette, and the verification discipline that defines the pre-push lint gate) live in [GOVERNANCE.md][governance] and are not repeated here.

## General

These rules apply to every language in the repo.

### Tooling Names and Casing

Use each tool's official casing in task labels, docs, and prose, per the `comment-and-doc-style` Skill at `.agents/skills/comment-and-doc-style/SKILL.md` in the hub (not a repo-relative link, that path is hub-local and not carried into every fleet repo).

### Clean-Compile Verification

Each language defines a **clean-compile** verification: the combination of build, formatter, linter, and code-analysis tools that must report clean before a commit. It is exposed as one or more **named** VS Code tasks (or, where a language ships no tasks, documented commands), and those definitions are the same across the fleet. The concrete names live in each language section below.

- **Run it after every code change, and it is not the whole gate.** The relevant language's clean-compile must pass before you commit. CI runs those same language checks as a backstop **plus everything else its validation workflow runs**, and all of it reports into the one required status, so a green clean-compile does not predict a green CI. That remainder is at least the doc-lint set (markdownlint, cspell, actionlint, `editorconfig-checker`) and whatever spec, config, and script gates the repo carries, so read the workflow for the full list rather than assuming this sentence enumerates it. What has to pass before a push is the repo's **whole** lint gate, per [GOVERNANCE.md "Verification Discipline"][governance-verification-discipline]. Each linter's known-working invocation is in [GOVERNANCE.md "Running the Linters Locally"][governance-running-the-linters-locally].
- **The named task definition is the canonical spec** - its exact command sequence, arguments, and strictness. You may run it through the VS Code task **or** by invoking the equivalent native commands directly, and either is fine **only if the sequence, arguments, and strictness match exactly**. No shortcuts and no more-lenient options (for example, never drop `--verify-no-changes` or loosen a `--severity`).
- **A local commit/pre-commit gate is the repo's choice.** No single hook runner fits every language (a `dotnet`-tool runner like Husky.Net suits .NET but not Python), so none is mandated, but that is **not** a recommendation against commit gates. CI is the authoritative backstop regardless, and a local gate is an additive convenience a repo may wire and keep: Husky.Net (and `dotnet husky run` as a style step) for .NET, `pre-commit` for Python. Keeping a working gate is not drift.

### Analyzer Diagnostics and Suppressions

- **A new port is not a license to silence diagnostics.** Brownfield / just-ported status never justifies relaxing analyzer or linter severities or muting newly surfaced warnings. Fix them. (The only brownfield allowance is the one-time git-signing / line-ending migration described in [GOVERNANCE.md][governance] and [README.md][readme], which has nothing to do with code analysis.)
- **Suppress only genuine false-positives or deliberate, documented exceptions**, always at the **narrowest scope that fits**, in this order of preference:
  1. An **in-code annotation on the specific symbol**, with a justification, in the language's attribute/comment form, never a blanket pragma spanning a region.
  2. The **owning project's local config** when the exception is project-wide for one project (e.g. a test project's own `.editorconfig` / `pyproject.toml`).
  3. The **root / shared config** only when the suppression is genuinely applicable to **every** project in the repo.
- **Never blanket-relax a batch of rules project-wide** to get a port to build. The per-language mechanics (which attribute, which config key) are in each language section.

### Markdown and Spelling

These apply repo-wide, in every directory: Markdown lints clean via `markdownlint-cli2` against the shared config, spelling is US English via CSpell against the shared `cspell.json`, the CI spelling gate covers `README.md` and `HISTORY.md` only, `HISTORY.md` mirrors the README's opening, and "Markdown" is a proper noun in prose. The full rules are in the `comment-and-doc-style` Skill referenced above.

## .NET

*This section applies only to the .NET side. A repo with no .NET projects still carries it (the file is carried whole) and ignores it.*

The style guide for any .NET projects in this repo: the zero-warnings build policy and its three-task clean-compile chain, central `Directory.Build.props`/`Directory.Packages.props` configuration, C# language and naming conventions, XML documentation, analyzer suppression scope, the library-versus-application logging split, async and error-handling patterns, xUnit v3 + AwesomeAssertions testing conventions, and AOT-compatible project configuration.

This is packaged as the `dotnet-codestyle` Skill at `.agents/skills/dotnet-codestyle/SKILL.md` in the hub, not a repo-relative link since that path is hub-local and not carried into every fleet repo. The summary above sketches the scope. Read the skill for the full rules, code examples, and mechanics.

## Shell

The deploy and check scripts are Bash. They run on a Linux host and in CI, never on Windows, so `.gitattributes` and `.editorconfig` pin them to LF.

### Linter and Formatter

`shellcheck` is the linter and `shfmt` the formatter. The clean-compile is `shellcheck` clean at default severity plus `shfmt -d`, both reporting nothing before a commit.

### Conventions

- **Every script opens with `set -Eeuo pipefail`.** A deploy that continues past a failed step is worse than one that stops, and `-E` lets an `ERR` trap inherit into functions, subshells, and command substitutions if one is ever added.
- **Pin `umask` in any script that creates files a service reads.** An inherited umask is invisible until a file lands unreadable.
- **Use `if` rather than `&&` for a conditional whose test may be false as the last command in a loop body or function.** Under `set -e` the false test becomes the block's exit status and terminates the script, which is precisely the case a tolerated-absence branch exists to handle.
- **Quote every expansion.** An unquoted path splits on whitespace, and the failure surfaces only on the one file with a space in its name.
- **Prefer an array to a string for command arguments.** A string re-splits on spaces, and an empty string becomes an empty argument rather than nothing.
- **Assert an outcome rather than trusting a command.** A prune that silently keeps everything, or a copy that silently shares nothing, reads as success until the disk fills.

### Verification

A script that gates a deploy is demonstrated failing before it is trusted. Break the thing it checks, confirm a non-zero exit and a message naming the fault, then restore. A gate that has only ever passed is indistinguishable from one that checks nothing.

## Hugo

The site is Hugo with a vendored theme. There is no plugin system and no build script, so the configuration and the templates are the code.

- **The build gate is `hugo --gc --minify --panicOnWarning`.** A deprecation warning fails the build rather than scrolling past.
- **Override a theme template rather than editing the theme in place.** A file in `layouts/` wins over the same path in `themes/`, which keeps the vendored copy replaceable.
- **`taxonomies` is a `singular: plural` map, and the plural is also the front-matter key.** Renaming the singular to change a URL silently matches nothing and generates zero term pages. Control the URL with `permalinks`.
- **Never hand-edit generated output.** `public/` is rebuilt by every run and is not committed.

## Python

*This section applies only to the Python side. A repo with no Python projects still carries it (the file is carried whole) and ignores it.*

The style guide for any Python project(s) in this repo: the build-versus-lint-only profile split, the uv/ruff/pyright/mypy/pytest toolchain, `src` layout, formatting and linting, comment and docstring conventions, type hints, naming, imports, patterns to avoid, test conventions, and versioning.

This is packaged as the `python-codestyle` Skill at `.agents/skills/python-codestyle/SKILL.md` in the hub, not a repo-relative link since that path is hub-local and not carried into every fleet repo. The summary above sketches the scope. Read the skill for the full rules and the profile-adaptation guidance.

<!-- Repo -->

[governance]: ./GOVERNANCE.md
[governance-running-the-linters-locally]: ./GOVERNANCE.md#running-the-linters-locally-known-working-invocations
[governance-verification-discipline]: ./GOVERNANCE.md#verification-discipline
[readme]: ./README.md
[root]: ./.editorconfig
