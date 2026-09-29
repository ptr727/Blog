#!/usr/bin/env python3
"""Fail if the variables and secrets GitHub holds differ from the ones ENVIRONMENT.md lists.

ENVIRONMENT.md's "The GitHub Environments" table names every stored value, its kind, and each
store holding it: a deployment environment such as `staging`, `repository` for the Actions
repository store, or `dependabot` for the Dependabot secret store. This reads the names GitHub
holds in each store and compares them against that table, in both directions:

  missing     the table lists a value a store does not hold, which a workflow then reads as empty.
  unlisted    a store holds a value the table does not list, usually a rename that left the old
              name behind.
  wrong kind  a value is held as a variable where the table says secret, or the reverse.

The repository read is the one this checkout's origin names. Every environment GitHub has is read, so a value set on an environment the table never names is
reported as unlisted rather than passed over.

Only names are read. A secret's value is not readable at all, and a variable's value is
projected away inside gh before any output reaches this script.

Runs locally, under a gh login that can administer the repository. Listing environment secrets
needs that, and a workflow's GITHUB_TOKEN cannot, which is why CI does not run this.

Exit 0 when GitHub matches the table, 1 on any finding, 2 when GitHub could not be read, so a
failed query is never reported as agreement.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "ENVIRONMENT.md"
SECTION = "## The GitHub Environments"

REPOSITORY = "repository"
DEPENDABOT = "dependabot"
KINDS = ("variable", "secret")

NAME = re.compile(r"`([A-Z][A-Z0-9_]*)`")
STORE = re.compile(r"`([A-Za-z0-9_.-]+)`")
SEPARATOR = re.compile(r"[-:\s]+")
ORIGIN = re.compile(r"github\.com[:/]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")

# One stored value, as (store, kind, name).
Entry = tuple[str, str, str]
Lister = Callable[[str, str], set[str]]


class QueryError(Exception):
    """GitHub could not be read, which is a boundary rather than a finding."""


def read_table(text: str) -> set[Entry]:
    """Return every (store, kind, name) the GitHub table lists, or raise ValueError on a malformed row."""
    start = text.find(f"\n{SECTION}\n")
    if start < 0:
        raise ValueError(f"{DOC.name} has no '{SECTION}' section")
    end = text.find("\n## ", start + 1)
    section = text[start : end if end >= 0 else len(text)]

    listed: set[Entry] = set()
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[0] == "Value" or SEPARATOR.fullmatch(cells[0]):
            continue
        # Every row is parsed or refused, since a row skipped for its shape would read as a value nobody listed.
        if len(cells) != 4:
            raise ValueError(f"row '{line[:60]}' has {len(cells)} cells, expected 4")
        match = NAME.fullmatch(cells[0])
        if match is None:
            raise ValueError(f"row '{line[:60]}' does not name its value as `NAME`")
        name, kind = match.group(1), cells[1]
        if kind not in KINDS:
            raise ValueError(f"{name} has kind '{kind}', expected variable or secret")
        stores = STORE.findall(cells[2])
        if not stores:
            raise ValueError(f"{name} names no store in its 'Held on' cell")
        # The Dependabot store holds secrets only, so a variable listed there could never be registered.
        if kind == "variable" and DEPENDABOT in stores:
            raise ValueError(
                f"{name} is a variable listed on {DEPENDABOT}, which holds secrets only"
            )
        listed.update((store, kind, name) for store in stores)
    if not listed:
        raise ValueError(f"'{SECTION}' in {DOC.name} lists no values")
    return listed


def origin_repo() -> str:
    """Return this checkout's origin as owner/repo."""
    # Named explicitly rather than left to gh, whose own resolution prefers GH_REPO and could read another repository.
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise QueryError("git is not installed") from error
    match = ORIGIN.search(result.stdout.strip()) if result.returncode == 0 else None
    if match is None:
        raise QueryError(
            f"origin is not a GitHub repository: {result.stdout.strip() or result.stderr.strip()}"
        )
    return f"{match.group(1)}/{match.group(2)}"


def gh_names(repo: str, path: str, key: str) -> set[str]:
    """List the `name` of every item under `key` at a repository API path, through gh."""
    command = [
        "gh",
        "api",
        "--paginate",
        f"repos/{repo}/{path}",
        "--jq",
        f".{key}[].name",
    ]
    try:
        result = subprocess.run(
            command, cwd=REPO, capture_output=True, text=True, check=False
        )
    except FileNotFoundError as error:
        raise QueryError("gh is not installed") from error
    if result.returncode != 0:
        raise QueryError(f"gh api {path} failed: {result.stderr.strip()}")
    return {line for line in result.stdout.splitlines() if line}


def read_github(names: Lister) -> set[Entry]:
    """Return every (store, kind, name) GitHub holds for this repository."""
    held: set[Entry] = set()

    def add(store: str, kind: str, found: set[str]) -> None:
        held.update((store, kind, name) for name in found)

    add(REPOSITORY, "secret", names("actions/secrets", "secrets"))
    add(REPOSITORY, "variable", names("actions/variables", "variables"))
    add(DEPENDABOT, "secret", names("dependabot/secrets", "secrets"))
    for environment in sorted(names("environments", "environments")):
        # An environment sharing a store label would merge its values into that store.
        if environment in (REPOSITORY, DEPENDABOT):
            raise QueryError(
                f"an environment is named '{environment}', the same as a store label, so its values cannot be told apart"
            )
        path = f"environments/{quote(environment, safe='')}"
        add(environment, "secret", names(f"{path}/secrets", "secrets"))
        add(environment, "variable", names(f"{path}/variables", "variables"))
    return held


def compare(listed: set[Entry], held: set[Entry]) -> list[str]:
    """Describe every difference between the table and GitHub, one line each."""
    findings: list[str] = []

    def other(kind: str) -> str:
        return "secret" if kind == "variable" else "variable"

    for store, kind, name in sorted(listed - held):
        if (store, other(kind), name) in held:
            findings.append(
                f"wrong kind: {name} on {store} is held as a {other(kind)}, listed as a {kind}"
            )
        else:
            findings.append(
                f"missing: {name} is listed as a {kind} on {store}, which does not hold it"
            )
    for store, kind, name in sorted(held - listed):
        # Already reported above as the wrong kind, unless the store also holds the listed kind.
        counterpart = (store, other(kind), name)
        if counterpart in listed and counterpart not in held:
            continue
        findings.append(
            f"unlisted: {store} holds the {kind} {name}, which {DOC.name} does not list"
        )
    return findings


def main() -> int:
    try:
        listed = read_table(DOC.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    try:
        repo = origin_repo()
        held = read_github(lambda path, key: gh_names(repo, path, key))
    except QueryError as error:
        print(
            f"ERROR: GitHub could not be read, so nothing was compared: {error}",
            file=sys.stderr,
        )
        return 2

    findings = compare(listed, held)
    for finding in findings:
        print(finding)
    if findings:
        print(
            f"\n{len(findings)} finding(s) against {repo}. Register the value on GitHub, or correct the table in {DOC.name}."
        )
        return 1

    stores = sorted({store for store, _, _ in listed})
    print(
        f"{repo}: {len(listed)} value(s) across {len(stores)} store(s), all held on GitHub as {DOC.name} lists"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
