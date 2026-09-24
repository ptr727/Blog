"""Tests for `scripts/normalize-text.py`, on posts built here rather than taken from the archive."""

import importlib.util
import pathlib
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "normalize_text", SCRIPTS / "normalize-text.py"
)
normalize_text = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(normalize_text)

CURLY = "\N{LEFT DOUBLE QUOTATION MARK}quoted\N{RIGHT DOUBLE QUOTATION MARK}"


def substitute(*lines: str) -> list[str]:
    return normalize_text.substitute("\n".join(lines), []).split("\n")


class SubstituteTests(unittest.TestCase):
    def test_prose_is_substituted(self) -> None:
        self.assertEqual(substitute(CURLY), ['"quoted"'])

    def test_lazy_blockquote_continuation_is_kept(self) -> None:
        out = substitute(f"> {CURLY}", CURLY, "", CURLY)
        self.assertEqual(out, [f"> {CURLY}", CURLY, "", '"quoted"'])

    def test_fence_with_info_string_does_not_close(self) -> None:
        out = substitute("```", "```python", CURLY, "```", CURLY)
        self.assertEqual(out, ["```", "```python", CURLY, "```", '"quoted"'])

    def test_crlf_closer_closes(self) -> None:
        out = substitute("```\r", f"{CURLY}\r", "```\r", f"{CURLY}\r")
        self.assertEqual(out, ["```\r", f"{CURLY}\r", "```\r", '"quoted"\r'])

    def test_fence_ends_a_blockquote(self) -> None:
        out = substitute(f"> {CURLY}", "```", CURLY, "```", CURLY)
        self.assertEqual(out[-1], '"quoted"')


if __name__ == "__main__":
    unittest.main()
