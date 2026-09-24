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
as. Inline code is substituted, because a curly quote or a dash inside a command is the
old platform's typography and breaks the command when pasted.

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
FENCE = re.compile(r"(`{3,}|~{3,})")
CLOSER = re.compile(r"(`{3,}|~{3,})[ \t]*\r?")
BLOCK = re.compile(
    r"#{1,6}(\s|$)|[-*+][ \t]+\S|0*1[.)][ \t]+\S|([-*_])[ \t]*(\2[ \t]*){2,}\r?$"
)

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
    first = next((i for i, line in enumerate(lines) if line.strip()), 0)
    front_matter = lines[first].rstrip("\r") == "---"
    fence, quote = None, False
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if front_matter:
            if index > first and line.rstrip("\r") == "---":
                front_matter = False
            continue
        if fence:
            closer = CLOSER.fullmatch(stripped)
            if (
                closer
                and closer.group(1)[0] == fence[0]
                and len(closer.group(1)) >= len(fence)
            ):
                fence = None
            continue
        opener = FENCE.match(stripped)
        if opener:
            fence, quote = opener.group(1), False
            continue
        quote = stripped.startswith(">") or (
            quote
            and bool(stripped.strip())
            and (line.startswith(("    ", "\t")) or not BLOCK.match(stripped))
        )
        if quote or any(token in line for token in protected):
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
        set(corrections) - {p.relative_to(REPO).as_posix() for p in TREE.rglob("*.md")}
    )

    changed, errors = [], [f"{name}: no such file" for name in missing]
    writes: list[tuple[pathlib.Path, str]] = []
    for path in sorted(TREE.rglob("*.md")):
        name = path.relative_to(REPO).as_posix()
        original = path.read_bytes().decode("utf-8")
        text = substitute(original, manifest["protect"])
        applied = 0
        for item in corrections.get(name, []):
            # A pattern stands in where the text being replaced must not be kept here.
            pattern = re.compile(item.get("pattern") or re.escape(item["from"]))
            label = f"{name}: correction {pattern.pattern!r}"
            done = len(pattern.findall(text)) == 0 and text.count(item["to"]) == 1
            if done:
                continue
            if len(pattern.findall(text)) != 1:
                errors.append(f"{label} matches {len(pattern.findall(text))} time(s)")
                continue
            result = pattern.sub(item["to"].replace("\\", "\\\\"), text)
            # A later run skips only a result with no match left and exactly one replacement.
            if pattern.findall(result) or result.count(item["to"]) != 1:
                errors.append(f"{label} would not read as applied on the next run")
                continue
            text = result
            applied += 1
        if text != original:
            changed.append(f"{name}: {applied} correction(s)")
            writes.append((path, text))

    # Nothing is written when any correction fails, so a failed run leaves the tree as it was.
    if args.apply and not errors:
        for path, text in writes:
            path.write_bytes(text.encode("utf-8"))

    verb = "normalized" if args.apply and not errors else "to normalize"
    for line in changed + errors:
        print(line)
    print()
    print(f"{len(changed)} file(s) {verb}, {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
