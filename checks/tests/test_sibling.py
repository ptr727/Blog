"""Tests for sibling.py, every script in them constructed rather than observed."""

import pathlib
import tempfile
import unittest

import sibling


class LoadTest(unittest.TestCase):
    def test_a_hyphenated_script_loads_as_the_module_named(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / "some-check.py"
            path.write_text("ANSWER = 42\n", encoding="utf-8")
            module = sibling.load("some_check", path)
        self.assertEqual(module.__name__, "some_check")
        self.assertEqual(module.ANSWER, 42)

    def test_a_path_no_loader_reads_is_refused_by_name(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / "notes.txt"
            path.write_text("ANSWER = 42\n", encoding="utf-8")
            with self.assertRaisesRegex(ImportError, "cannot load notes.txt"):
                sibling.load("notes", path)


if __name__ == "__main__":
    unittest.main()
