#!/usr/bin/env python3
"""Fail when a file declared in `media-redactions.json` is not its redacted result.

The manifest records the hash each redaction produces, so this needs no image
decoder. A file replaced by its original, re-exported, or edited by hand fails here,
and `scripts/redact-media.py` is what brings it back.
"""

import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "checks" / "media-redactions.json"


def main() -> int:
    files = json.loads(MANIFEST.read_text())["files"]
    failures = []
    for name, entry in files.items():
        path = REPO / name
        if not path.is_file():
            failures.append(f"{name}: missing")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry.get("result"):
            failures.append(f"{name}: not its redacted result")
    for line in failures:
        print(line)
    if failures:
        print(
            f"\n{len(failures)} file(s) fail. Run scripts/redact-media.py, see CONTENT.md."
        )
        return 1
    print(f"redactions: {len(files)} file(s), every one at its redacted result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
