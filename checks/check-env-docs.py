#!/usr/bin/env python3
"""Fail if a configuration value is declared without a description in ENVIRONMENT.md, or
described there and declared nowhere.

The declared surface is three things, and nothing else: the keys in example.env, the
vars.X and secrets.X a workflow references, and the KNOBS list below. A variable a script
merely reads is NOT in scope, because a script-local name and a configuration value are the
same shape and no pattern separates them, so widening this would report the difference as
findings nobody can clear. A new knob therefore has to be added to KNOBS by hand.

ENVIRONMENT.md is the single description of every configuration value. A new value gets
added wherever its author is working, which is rarely the doc, and no linter notices a
missing paragraph. This does.

Both directions matter and they catch different mistakes:

  undocumented  a value exists and nobody wrote down what it means.
  unused        a value is described but declared nowhere. Usually a rename that updated
                the code and left the prose, which is worse than an omission because it
                reads as current.

Read-only. Exit 1 on any finding.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "ENVIRONMENT.md"

# The one template, whose keys are the declared configuration surface.
TEMPLATES = [REPO / "example.env"]

# Workflow references. `vars.X` and `secrets.X` are the GitHub Environment surface, and a
# value added there is exactly as undocumented as one added to a template.
WORKFLOWS = sorted((REPO / ".github" / "workflows").glob("*.yml"))

# Set per invocation rather than stored, so they appear in no template and would otherwise
# be invisible to this check. Listed here because the doc has a table for them, and a knob
# nobody documented is the same failure as an undocumented file value.
KNOBS = {
    "ENV_FILE",
    "REQUIRE_BROTLI",
    "NO_LINK_DEST",
    "KEEP_RELEASES",
    "EXPECT_RELEASE",
    "CHECK_TAG",
    "MTIME_RESTORED",
}

# Real, stored GitHub Environment values, invisible to WORKFLOWS for a different reason.
# The hub-hosted deploy-site-task.yml reads these by its own vars.X/secrets.X reference.
# Since that reference lives outside this repo's own workflow files, this scan never sees them declared.
HUB_HOSTED_ENVIRONMENT_VALUES = {
    "SITE_BASE_URL",
    "DEPLOY_SSH_HOST",
    "DEPLOY_SSH_USER",
    "DEPLOY_SSH_KNOWN_HOSTS",
}

# Names that look like configuration to the patterns above but are not.
# ENVIRONMENT and RELEASE_ID are computed inside the workflow and passed down, and
# GITHUB_* is the runner's own namespace.
IGNORE = {"ENVIRONMENT", "RELEASE_ID", "SSH_TRANSPORT"}

DECL = re.compile(r"^([A-Z][A-Z0-9_]*)=", re.MULTILINE)
COMMENTED_DECL = re.compile(r"^#\s*([A-Z][A-Z0-9_]*)=", re.MULTILINE)
GH_REF = re.compile(r"\b(?:vars|secrets)\.([A-Z][A-Z0-9_]*)\b")
# A row is `| `NAME` | ...`, and the backticks are what separate a described value from a
# mention of one in a sentence. The trailing `=value` is optional because a knob is
# documented as REQUIRE_BROTLI=1, which names the value that switches it on.
DOC_ROW = re.compile(r"^\|\s*`([A-Z][A-Z0-9_]*)(?:=[^`]*)?`", re.MULTILINE)
# Values the doc names in prose rather than in a table row, which is how the three
# commented-out template keys and the two bot secrets are covered.
DOC_INLINE = re.compile(r"`([A-Z][A-Z0-9_]{2,})(?:=[^`]*)?`")


def main() -> int:
    if not DOC.exists():
        print(f"ERROR: {DOC.name} does not exist", file=sys.stderr)
        return 1

    doc_text = DOC.read_text(encoding="utf-8")
    documented_rows = set(DOC_ROW.findall(doc_text))
    documented_any = documented_rows | set(DOC_INLINE.findall(doc_text))

    declared: dict[str, set[str]] = {}

    def note(name: str, where: str) -> None:
        if name not in IGNORE:
            declared.setdefault(name, set()).add(where)

    for path in TEMPLATES:
        if not path.exists():
            print(f"ERROR: template {path} is missing", file=sys.stderr)
            return 1
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO).as_posix()
        for name in DECL.findall(text):
            note(name, rel)
        # A commented-out key is still a declared value: it documents the shape a
        # deployment has to supply from somewhere else.
        for name in COMMENTED_DECL.findall(text):
            note(name, rel)

    for path in WORKFLOWS:
        rel = path.relative_to(REPO).as_posix()
        for name in GH_REF.findall(path.read_text(encoding="utf-8")):
            note(name, rel)

    for name in KNOBS:
        note(name, "per-invocation knob")

    for name in HUB_HOSTED_ENVIRONMENT_VALUES:
        note(name, "read by the hub-hosted deploy-site-task.yml")

    undocumented = sorted(n for n in declared if n not in documented_any)
    # Only table rows count as "described", so a value the doc merely mentions in passing
    # is not treated as having a description it can be removed against.
    unused = sorted(n for n in documented_rows if n not in declared)

    for name in undocumented:
        where = ", ".join(sorted(declared[name]))
        print(f"undocumented: {name} declared in {where} but not described in {DOC.name}")
    for name in unused:
        print(f"unused: {name} described in {DOC.name} but declared nowhere")

    total = len(undocumented) + len(unused)
    if total:
        print(f"\n{total} finding(s). Describe the value in {DOC.name}, or remove the row.")
        return 1

    print(f"{len(declared)} configuration value(s), all described in {DOC.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
