"""Tests for check-csp-browser.py's host half, every record in them constructed rather than observed."""

import contextlib
import io
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import sibling

CHECKS = pathlib.Path(__file__).resolve().parent.parent
gate = sibling.load("check_csp_browser", CHECKS / "check-csp-browser.py")

BASE = "https://mirror.example/"
ALLOWED = ("img-src", "https://images.example")


def loaded(page, status=200):
    return {"page": page, "status": status}


def blocked(page, directive, url, disposition="enforce"):
    return {
        "page": page,
        "directive": directive,
        "blocked": url,
        "disposition": disposition,
    }


class PinTest(unittest.TestCase):
    def test_the_committed_dockerfile_pins_a_versioned_digest(self) -> None:
        image, version = gate.pinned_image(gate.DOCKERFILE.read_text(encoding="utf-8"))
        self.assertIn(f":v{version}-", image)
        self.assertIn("@sha256:", image)

    def test_a_tag_without_a_version_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            gate.pinned_image("FROM mcr.microsoft.com/playwright/python:latest\n")

    def test_the_committed_allow_list_parses(self) -> None:
        for directive, origin in gate.read_allow(
            gate.ALLOW.read_text(encoding="utf-8")
        ):
            self.assertTrue(directive.endswith("-src"), directive)
            self.assertEqual(gate.blocked_origin(origin), origin)


class ListTest(unittest.TestCase):
    def test_paths_keep_order_drop_repeats_and_add_search(self) -> None:
        paths = gate.read_paths(["/\n/a/\n\n", "/a/\n/b/\n"], search=True)
        self.assertEqual(paths, ["/", "/a/", "/b/", gate.SEARCH_PATH])

    def test_a_listed_search_page_is_not_added_twice(self) -> None:
        paths = gate.read_paths([f"{gate.SEARCH_PATH}\n/\n"], search=True)
        self.assertEqual(paths, [gate.SEARCH_PATH, "/"])

    def test_paths_not_asking_for_search_keep_only_their_own(self) -> None:
        paths = gate.read_paths(["/en/\n/af/\n"], search=False)
        self.assertEqual(paths, ["/en/", "/af/"])

    def test_an_allow_line_without_a_reason_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            gate.read_allow("img-src\thttps://images.example\n")

    def test_an_allow_list_reads_directive_and_origin(self) -> None:
        allow = gate.read_allow("img-src\thttps://images.example\tgone\n\n")
        self.assertEqual(allow, [ALLOWED])


class OriginTest(unittest.TestCase):
    def test_a_url_reduces_to_its_origin(self) -> None:
        origin = gate.blocked_origin("https://images.example/a/b.png?x=1")
        self.assertEqual(origin, "https://images.example")

    def test_a_keyword_passes_through(self) -> None:
        self.assertEqual(gate.blocked_origin("inline"), "inline")


class SummarizeTest(unittest.TestCase):
    def test_a_clean_run_has_no_findings(self) -> None:
        findings, allowed, count = gate.summarize(
            [loaded("/"), loaded("/a/")], [], True
        )
        self.assertEqual((findings, allowed, count), ([], {}, 2))

    def test_a_violation_is_counted_once_per_directive_and_origin(self) -> None:
        records = [
            loaded("/"),
            blocked("/", "style-src-elem", "inline"),
            loaded("/a/"),
            blocked("/a/", "style-src-elem", "inline", "report"),
        ]
        findings, _, _ = gate.summarize(records, [], True)
        self.assertEqual(
            findings,
            ["style-src-elem blocked inline 2 time(s) (enforce/report), first on /"],
        )

    def test_an_allowed_violation_is_counted_not_reported(self) -> None:
        records = [loaded("/"), blocked("/", "img-src", "https://images.example/1.png")]
        findings, allowed, _ = gate.summarize(records, [ALLOWED], True)
        self.assertEqual((findings, allowed), ([], {ALLOWED: 1}))

    def test_a_stale_allow_entry_fails_a_complete_run(self) -> None:
        findings, _, _ = gate.summarize([loaded("/")], [ALLOWED], True)
        self.assertEqual(len(findings), 1)
        self.assertIn("which nothing blocked", findings[0])

    def test_a_stale_allow_entry_passes_a_partial_run(self) -> None:
        findings, _, _ = gate.summarize([loaded("/")], [ALLOWED], False)
        self.assertEqual(findings, [])

    def test_a_page_that_is_not_200_fails(self) -> None:
        findings, _, _ = gate.summarize([loaded("/gone/", 404)], [], True)
        self.assertEqual(findings, ["/gone/ answered 404"])

    def test_a_probe_error_fails(self) -> None:
        records = [loaded("/"), {"page": "/", "error": "Timeout 30000ms exceeded."}]
        findings, _, _ = gate.summarize(records, [], True)
        self.assertEqual(findings, ["/: Timeout 30000ms exceeded."])


class MainTest(unittest.TestCase):
    def setUp(self) -> None:
        cache = tempfile.TemporaryDirectory()
        self.addCleanup(cache.cleanup)
        env = mock.patch.dict(os.environ, {"UV_CACHE_DIR": cache.name})
        env.start()
        self.addCleanup(env.stop)

    def run_main(self, records, argv=()):
        with (
            mock.patch.object(
                gate, "run_probe", return_value=(records, None)
            ) as self.probe,
            mock.patch.object(gate, "docker_command", return_value=["true"]),
            mock.patch.object(gate, "read_allow", return_value=[]),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            code = gate.main([BASE, *argv])
        return code, out.getvalue()

    def test_every_page_loaded_clean_passes(self) -> None:
        paths = gate.read_paths([gate.URLS.read_text(encoding="utf-8")], search=True)
        code, out = self.run_main([loaded(path) for path in paths])
        self.assertEqual(code, 0, out)
        self.assertIn("PASS", out)

    def test_a_run_over_another_list_loads_only_its_own_pages(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            urls = pathlib.Path(folder) / "family-urls.txt"
            urls.write_text("/en/\n/af/\n", encoding="utf-8")
            code, out = self.run_main(
                [loaded("/en/"), loaded("/af/")], ["--urls", str(urls)]
            )
        self.assertEqual(code, 0, out)
        self.assertEqual(self.probe.call_args.args[1], ["/en/", "/af/"])

    def test_a_page_that_never_reported_fails(self) -> None:
        code, out = self.run_main([loaded("/")])
        self.assertEqual(code, 1)
        self.assertIn(" pages reported a load", out)

    def test_a_probe_that_did_not_run_is_a_refusal(self) -> None:
        with (
            mock.patch.object(gate, "run_probe", return_value=(None, "exited 125")),
            mock.patch.object(gate, "docker_command", return_value=["true"]),
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            gate.main([BASE])
        self.assertIn("exited 125", str(raised.exception.code))

    def test_a_host_without_uv_fails_with_the_reason(self) -> None:
        with (
            mock.patch.object(gate.shutil, "which", return_value=None),
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            gate.main([BASE])
        self.assertEqual(raised.exception.code, "FAIL: uv is not on PATH")

    def test_a_relative_base_url_is_a_usage_error(self) -> None:
        with (
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            gate.main(["mirror.example"])
        self.assertEqual(raised.exception.code, 2)

    def test_a_list_naming_no_page_is_a_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            urls = pathlib.Path(folder) / "empty-urls.txt"
            urls.write_text("\n  \n", encoding="utf-8")
            with (
                mock.patch.object(gate, "run_probe") as probe,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as raised,
            ):
                gate.main([BASE, "--urls", str(urls)])
        self.assertEqual(raised.exception.code, 2)
        probe.assert_not_called()


class CommandTest(unittest.TestCase):
    def test_the_container_installs_the_tag_version_and_reaches_the_host(self) -> None:
        with mock.patch.object(gate.shutil, "which", return_value="/bin/uv"):
            command = gate.docker_command("img:v1.2.3-noble", "1.2.3", BASE, "/c")
        self.assertIn("playwright==1.2.3", command)
        self.assertEqual(command[command.index("--network") + 1], "host")
        self.assertEqual(command[-2:], ["--probe", BASE])

    def test_a_host_without_uv_is_refused(self) -> None:
        with (
            mock.patch.object(gate.shutil, "which", return_value=None),
            self.assertRaises(FileNotFoundError),
        ):
            gate.docker_command("img:v1.2.3-noble", "1.2.3", BASE, "/c")


class ProbeRunTest(unittest.TestCase):
    def test_records_are_read_one_per_line_from_the_paths_on_stdin(self) -> None:
        echo = "import json, sys\nfor line in sys.stdin: print(json.dumps({'page': line.strip(), 'status': 200}))"
        records, refusal = gate.run_probe(
            [sys.executable, "-c", echo], ["/", "/a/"], 60
        )
        self.assertIsNone(refusal)
        self.assertEqual(records, [loaded("/"), loaded("/a/")])

    def test_a_probe_that_exits_nonzero_is_a_refusal_naming_its_stderr(self) -> None:
        fail = "import sys; sys.exit('no browser')"
        records, refusal = gate.run_probe([sys.executable, "-c", fail], ["/"], 60)
        self.assertIsNone(records)
        self.assertIn("no browser", refusal or "")

    def test_a_probe_past_its_timeout_is_a_refusal(self) -> None:
        stall = "import time; time.sleep(30)"
        records, refusal = gate.run_probe([sys.executable, "-c", stall], ["/"], 1)
        self.assertIsNone(records)
        self.assertIn("timed out", refusal or "")

    def test_a_probe_that_cannot_start_is_a_refusal(self) -> None:
        missing = [str(CHECKS / "no-such-command")]
        records, refusal = gate.run_probe(missing, ["/"], 60)
        self.assertIsNone(records)
        self.assertIn("did not finish", refusal or "")


if __name__ == "__main__":
    unittest.main()
