#!/usr/bin/env python3
"""Apply the archive's character substitutions and the corrections in `text-corrections.json`.

Run on demand rather than in CI, because it rewrites files.

**Two passes, and neither restyles.** The first swaps each typographic character in
`SUBSTITUTIONS` for its ASCII form, a mechanical change that leaves every word where
it was. The second applies the manifest's corrections in one named file each, for
the doubled words and plain grammar slips a reviewer approved one at a time. A
correction is an exact string, or a pattern where the old text must not be kept here.
Nothing here decides what a defect is.

**Some text keeps its characters.** Front matter, a fenced code block, a blockquote,
and a line holding one of the manifest's protected tokens are left byte for byte, since
tool output, somebody else's words, and a product name each mean what they are written
as.

Both passes are idempotent. A substituted character is gone, and a correction whose
text is already in place is skipped, so a second run reports nothing. A correction
that matches neither its before nor its after, or matches more than once, is an error
rather than a guess.
"""

import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "scripts" / "text-corrections.json"
TREE = REPO / "content"

SUBSTITUTIONS = {
    "\u00a0": " ",
    "\u2011": "-",
    "\u2013": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2022": "-",
    "\u2026": "...",
    "\u2192": "->",
    "\u21d2": "=>",
}


def substitute(text: str, protected: list[str]) -> str:
    lines = text.split("\n")
    front_matter = lines[0] == "---"
    fence = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if front_matter:
            if index > 0 and line == "---":
                front_matter = False
            continue
        if fence:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(("```", "~~~")):
            fence = stripped[:3]
            continue
        if stripped.startswith(">") or any(token in line for token in protected):
            continue
        for old, new in SUBSTITUTIONS.items():
            line = line.replace(old, new)
        lines[index] = line
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply", action="store_true", help="write the files, rather than reporting"
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    corrections: dict[str, list[dict]] = {}
    for item in manifest["corrections"]:
        corrections.setdefault(item["file"], []).append(item)
    missing = sorted(
        set(corrections) - {str(p.relative_to(REPO)) for p in TREE.rglob("*.md")}
    )

    changed, errors = [], [f"{name}: no such file" for name in missing]
    for path in sorted(TREE.rglob("*.md")):
        name = str(path.relative_to(REPO))
        original = path.read_text(encoding="utf-8")
        text = substitute(original, manifest["protect"])
        applied = 0
        for item in corrections.get(name, []):
            # A pattern stands in where the text being replaced must not be kept here.
            pattern = re.compile(item.get("pattern") or re.escape(item["from"]))
            before, after = len(pattern.findall(text)), text.count(item["to"])
            if before == 1:
                text = pattern.sub(item["to"].replace("\\", "\\\\"), text)
                applied += 1
            elif before > 1 or after != 1:
                errors.append(
                    f"{name}: correction {pattern.pattern!r} matches {before} time(s)"
                )
        if text != original:
            changed.append(f"{name}: {applied} correction(s)")
            if args.apply:
                path.write_text(text, encoding="utf-8")

    verb = "normalized" if args.apply else "to normalize"
    for line in changed + errors:
        print(line)
    print()
    print(f"{len(changed)} file(s) {verb}, {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
