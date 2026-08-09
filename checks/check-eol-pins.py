#!/usr/bin/env python3
"""Fail if a tracked shebang file has no LF pin, or a .gitattributes pattern matches nothing.

`.gitattributes` keeps git passive with `* -text` and then names the files whose line
endings are load-bearing. That design is right and it has one weakness: the pins are a
hand-maintained list, so a new execution-sensitive file is pinned only if its author
remembers, and nothing reads the list back. Both directions have already failed here.

  unpinned    `ops/vps-backup-pull` is extensionless, so no `*.sh` or `*.py` rule reached
              it, and a CRLF checkout would hand systemd a broken interpreter line.
  dead        `deploy/blog-deploy-shell` and `deploy/authorized_keys` were pinned and have
              never been tracked in this repository. That is the worse half: a pin for a
              file that does not exist binds nothing while reading as coverage, and its
              comment claimed the extensionless case was handled, which is why the file
              that actually needed it went unnoticed.

So this gate reads both directions, and neither is a style rule. A shebang on line one is
the test for the first, because that is exactly the property a CRLF breaks. Executability
is deliberately not the test: the mode bit and the interpreter line move independently,
and it is the interpreter line that fails.

Text-format files a daemon parses, the Caddy configs and the map tables, are pinned for
the same reason and are not detectable by any property of their contents, so they stay a
named list and only the dead-pattern direction covers them.

Read-only. Exit 1 on any finding.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ATTRIBUTES = REPO / ".gitattributes"

# `* -text` is the passive default the pins sit on top of, and it is expected to match
# every tracked file. Reporting it as a pattern that "matches nothing" is impossible, but
# excluding it keeps the dead-pattern check about the named pins.
BASELINE = {"*"}


def git(*args: str) -> str:
    """Run git in the repository and return stdout, failing loudly rather than silently."""
    result = subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def tracked_files() -> list[str]:
    return [line for line in git("ls-files", "-z").split("\0") if line]


def patterns() -> list[tuple[int, str]]:
    """The pattern from every non-comment, non-blank line, with its line number."""
    found = []
    for number, raw in enumerate(ATTRIBUTES.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        found.append((number, line.split()[0]))
    return found


def has_shebang(path: Path) -> bool:
    """True if the file opens `#!`, read as bytes so a binary file cannot raise."""
    try:
        with path.open("rb") as handle:
            return handle.read(2) == b"#!"
    except OSError:
        return False


def eol_attribute(paths: list[str]) -> dict[str, str]:
    """The resolved `eol` attribute per path, from git rather than by re-implementing the
    match rules, because a hand-rolled matcher is a second source of truth that can differ
    from the one git actually applies on checkout."""
    if not paths:
        return {}
    payload = "\0".join(paths) + "\0"
    result = subprocess.run(
        ["git", "-C", str(REPO), "check-attr", "--stdin", "-z", "eol"],
        input=payload,
        capture_output=True,
        text=True,
        check=True,
    )
    # -z emits a flat NUL-separated stream of path, attribute, value triples.
    fields = [field for field in result.stdout.split("\0") if field != ""]
    return {fields[i]: fields[i + 2] for i in range(0, len(fields) - 2, 3)}


def main() -> int:
    findings: list[str] = []
    files = tracked_files()

    # Direction one: a tracked shebang file whose resolved eol is not lf.
    shebangs = sorted(f for f in files if has_shebang(REPO / f))
    if not shebangs:
        print("error: no tracked shebang files found, so this gate checked nothing")
        return 1
    resolved = eol_attribute(shebangs)
    for path in shebangs:
        if resolved.get(path) != "lf":
            findings.append(
                f"unpinned: {path} opens with a shebang and resolves to "
                f"eol={resolved.get(path, 'unspecified')}. Add a line to .gitattributes."
            )

    # Direction two: a pin naming a file the repository does not carry.
    for number, pattern in patterns():
        if pattern in BASELINE:
            continue
        if not git("ls-files", "--", pattern).strip():
            findings.append(
                f"dead: .gitattributes:{number} pattern {pattern!r} matches no tracked "
                f"file, so it binds nothing while reading as coverage."
            )

    if findings:
        for finding in findings:
            print(f"error: {finding}")
        print(f"\nFAIL - {len(findings)} line-ending pin finding(s)")
        return 1

    print(
        f"PASS - {len(shebangs)} shebang files pinned to LF, "
        f"{len(patterns()) - len(BASELINE)} patterns all matching tracked files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
