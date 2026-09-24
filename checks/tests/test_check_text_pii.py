"""Tests for check-text-pii.py, every value in them constructed rather than observed."""

import contextlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest

CHECKS = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "check_text_pii", CHECKS / "check-text-pii.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load check-text-pii.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

POSITIVE = {
    "email": ["Write to someone@example.com for a copy."],
    "hardware address": [
        "The board reports 02:00:00:ab:cd:ef on boot.",
        "The board reports 02-00-00-AB-CD-EF on boot.",
        "The switch lists 0200.00ab.cdef on that port.",
        "MAC:02:00:00:ab:cd:ef",
        "02:00:00:ab:cd:ef: link up",
        "BD:02:00:00:ab:cd:ef",
        "MAC-02:00:00:ab:cd:ef",
        "MAC-02-00-00-ab-cd-ef",
        "HWaddr-02-00-00-ab-cd-ef",
    ],
    "public ip": [
        "The resolver answers on 1.1.1.1 today.",
        "The resolver answers on 2606:4700:4700::1111 today.",
    ],
    "coordinates": [
        "The unit sits at 12.345, -67.890 in the yard.",
        "The unit sits at 12.345 N 67.890 W in the yard.",
        """The unit sits at 12°20'42"N 67°53'24"W in the yard.""",
        "The feature is [-167.8901, 12.3456] in the file.",
        "The unit sits at 167.890 E, 12.345 N in the yard.",
        "The unit sits at 12.345 N, -67.890 in the yard.",
        "The unit sits at 12.345, 67.890 W in the yard.",
        "The unit sits at 67.890 W, 12.345 in the yard.",
        "latitude: 12.345",
        "home_latitude: 12.345",
        "gps_lon=-67.890",
        "lat 12.345",
        '{"lat": 12.345, "lon": -67.890}',
        "homeLatitude: 12.345",
        '{"gpsLat": 12.345}',
        "homeLongitude=-67.890",
    ],
    "coordinate url": [
        "See https://www.openstreetmap.org/?mlat=12.345&mlon=-67.890 for the spot.",
        "See https://maps.example.com/place/@12.345,-67.890,17z for the spot.",
    ],
    "instance url": [
        "The feed is https://www.wunderground.com/dashboard/pws/KXX0000 now.",
        "The feed is https://map.example.com/?sensor=12345 now.",
    ],
    "street address": [
        "Deliveries go to 123 Example Street most days.",
        "Deliveries go to 4567 NE 89th St most days.",
        "Mail goes to PO Box 1234 instead.",
    ],
    "phone": [
        "Call (555) 555-0123 after five.",
        "Call +1 555 555 0123 after five.",
        "Call +44 20 5550 0123 after five.",
    ],
}

NEGATIVE = [
    "Install version 1.2.3.4 from the vendor.",
    "The retina asset is icon@2x.png beside the post.",
    "The job ran at 12:30:45 on 2026-08-01.",
    "The gateway sits at 192.0.2.1 and 2001:db8::1 in the example.",
    "The router hands out 10.0.0.5 on the private side.",
    "| Model | 122.294 | 120.172 | 89.258 |",
    "Paris is a city in France.",
    "date: 2026-08-01T10:00:00-07:00",
    "The sizes are 123.456, 45.678 mm and 100.000/12.500 in.",
    "The board is long: 12.345 cm.",
    "The job wrote backup-26-08-01-12-30-45.tar overnight.",
    "The roof is flat 12.345 m across.",
    "FLAT 12.345",
]


class Tree:
    """A throwaway repository root with an archive boundary and posts."""

    def __init__(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._dir.name)
        excludes = self.root / ".github" / "prose-gate-excludes"
        excludes.parent.mkdir(parents=True)
        excludes.write_text("# archive\ncontent/posts/2010/\n", encoding="utf-8")

    def post(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def allow(self, entries: list[object]) -> None:
        path = self.root / "checks" / "text-pii-allow.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"allow": entries}), encoding="utf-8")

    def run(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gate.main(["--root", str(self.root)])
        return code, out.getvalue()

    def close(self) -> None:
        self._dir.cleanup()


class ScanLineTests(unittest.TestCase):
    def test_each_class_is_found(self) -> None:
        for kind, lines in POSITIVE.items():
            for line in lines:
                with self.subTest(line=line):
                    self.assertIn(kind, {k for k, _ in gate.scan_line(line)})

    def test_lookalikes_pass(self) -> None:
        for line in NEGATIVE:
            with self.subTest(line=line):
                self.assertEqual([], list(gate.scan_line(line)))


class GateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = Tree()

    def tearDown(self) -> None:
        self.tree.close()

    def test_current_tree_passes(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(0, gate.main([]), out.getvalue())

    def test_constructed_post_fails_on_every_class_without_echoing_values(self) -> None:
        lines = [line for group in POSITIVE.values() for line in group]
        self.tree.post("content/posts/2026/01/02/leaky.md", "\n".join(lines) + "\n")
        code, out = self.tree.run()
        self.assertEqual(1, code)
        for kind in POSITIVE:
            self.assertIn(f": {kind}\n", out)
        for kind, line in ((k, v) for k, group in POSITIVE.items() for v in group):
            for _, value in gate.scan_line(line):
                self.assertNotIn(value, out, kind)
        self.assertIn("content/posts/2026/01/02/leaky.md:1: email", out)
        self.assertIn("To fix, remove each value or declare it, see", out)

    def test_archive_years_are_out_of_scope(self) -> None:
        self.tree.post("content/posts/2010/01/02/old.md", POSITIVE["email"][0] + "\n")
        self.assertEqual(0, self.tree.run()[0])

    def test_pages_outside_posts_are_in_scope(self) -> None:
        self.tree.post("content/about.md", POSITIVE["phone"][0] + "\n")
        self.assertEqual(1, self.tree.run()[0])

    def test_declared_value_passes(self) -> None:
        self.tree.post("content/posts/2026/01/02/a.md", POSITIVE["email"][0] + "\n")
        self.tree.allow(
            [
                {
                    "class": "email",
                    "value": "someone@example.com",
                    "reason": "a constructed address",
                }
            ]
        )
        self.assertEqual(0, self.tree.run()[0])

    def test_declared_pattern_passes(self) -> None:
        self.tree.post("content/posts/2026/01/02/a.md", POSITIVE["email"][0] + "\n")
        self.tree.allow(
            [
                {
                    "class": "email",
                    "pattern": r"[\w.]+@example\.com",
                    "reason": "a reserved domain",
                }
            ]
        )
        self.assertEqual(0, self.tree.run()[0])

    def test_declaration_is_bound_to_its_class(self) -> None:
        self.tree.post("content/posts/2026/01/02/a.md", POSITIVE["email"][0] + "\n")
        self.tree.allow([{"class": "phone", "pattern": ".*", "reason": "wrong class"}])
        code, out = self.tree.run()
        self.assertEqual(1, code)
        self.assertIn(": email\n", out)

    def test_unused_declaration_fails(self) -> None:
        self.tree.post("content/posts/2026/01/02/a.md", "Nothing to see.\n")
        self.tree.allow(
            [
                {
                    "class": "email",
                    "value": "someone@example.com",
                    "reason": "no longer printed",
                }
            ]
        )
        code, out = self.tree.run()
        self.assertEqual(1, code)
        self.assertIn("entry 0 (email) matches nothing", out)
        self.assertIn("findings: 0, unused allow list entries: 1.", out)
        self.assertIn("To fix, drop each unused entry, see", out)
        self.assertNotIn("someone@example.com", out)

    def test_malformed_declarations_are_refused(self) -> None:
        self.tree.post("content/posts/2026/01/02/a.md", "Nothing to see.\n")
        base = {
            "class": "email",
            "value": "someone@example.com",
            "reason": "constructed",
        }
        for entry in (
            {k: v for k, v in base.items() if k != "reason"},
            {**base, "reason": None},
            {**base, "reason": False},
            {"class": "email", "pattern": 5, "reason": "constructed"},
            {"class": "email", "pattern": "(", "reason": "constructed"},
            "not an object",
        ):
            with self.subTest(entry=entry):
                self.tree.allow([entry])
                with self.assertRaises(SystemExit):
                    self.tree.run()

    def test_line_numbers_count_newlines_only(self) -> None:
        self.tree.post(
            "content/posts/2026/01/02/a.md", "one\x0ctwo\n" + POSITIVE["email"][0]
        )
        self.assertIn("a.md:2: email", self.tree.run()[1])


if __name__ == "__main__":
    unittest.main()
