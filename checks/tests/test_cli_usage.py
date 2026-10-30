"""Hold every tracked script to the fleet's command-line argument rule by running it.

Each script runs with `--help`, with `-h`, and with an unknown `--bogus-flag`. Help exits 0 and
prints the same text for both spellings, opening on a usage line that names the script. Help after
another argument answers the same way, rather than being refused as an extra one. The unknown
flag exits non-zero with a refusal naming it. A script needing a positional refuses on the missing
argument before it reaches the flag, so BEFORE_FLAG gives it one. Every other script is declared
in NO_REQUIRED_ARGUMENT. A script declared in neither fails, so a new one is classified the moment
it is tracked.

No run may change anything. Stubs ahead of the real commands on PATH record any call to them. The
home and working directories are empty scratch directories that must stay empty, and the tree's
status must not move. ENV_FILE names a file that does not exist, so make-release.sh refuses rather
than building should its argument check ever regress.
"""

import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent

BEFORE_FLAG = {
    "checks/csp_browser_gate.py": ("https://example.invalid",),
    "checks/csp_gate.py": ("public",),
    "checks/url_parity_gate.py": ("public",),
}

NO_REQUIRED_ARGUMENT = frozenset(
    {
        "capture/build_golden.py",
        "capture/build_redirects.py",
        "capture/classify.py",
        "capture/clean_content.py",
        "capture/enumerate_media.py",
        "capture/localize_external.py",
        "capture/restructure_content.py",
        "capture/run-wp2hugo.sh",
        "checks/check-live-urls.sh",
        "checks/env_docs_gate.py",
        "checks/github_env_gate.py",
        "checks/media_metadata_gate.py",
        "checks/media_redactions_gate.py",
        "checks/text_pii_gate.py",
        "deploy/make-release.sh",
        "scripts/normalize_media.py",
        "scripts/normalize_text.py",
        "scripts/redact_media.py",
    }
)

REFUSED_AS_OPTION = re.compile(
    r"(unknown|unrecogni[sz]ed) (option|argument)[^\n]*--bogus-flag", re.IGNORECASE
)

RECORDED = ("git", "gh", "curl", "wget", "ssh", "rsync", "docker", "hugo", "uv", "uvx")


def entry_points() -> list[str]:
    """Every tracked executable outside the vendored theme and the test directories."""
    listed = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "-s", "-z"],
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    found = []
    for record in filter(None, listed.split("\0")):
        mode, path = record.split(" ", 1)[0], record.split("\t", 1)[1]
        parts = pathlib.PurePosixPath(path).parts
        if mode == "100755" and parts[0] != "themes" and "tests" not in parts:
            found.append(path)
    return sorted(found)


def tree_status() -> str:
    return subprocess.run(
        [
            "git",
            "-C",
            str(REPO),
            "status",
            "--porcelain",
            "--ignored",
            "--untracked-files=all",
        ],
        capture_output=True,
        check=True,
        text=True,
    ).stdout


class CliUsageTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = pathlib.Path(scratch.name)
        stubs = self.root / "stubs"
        stubs.mkdir()
        self.record = self.root / "recorded"
        for name in RECORDED:
            stub = stubs / name
            stub.write_text(f'#!/bin/sh\necho {name} >>"{self.record}"\nexit 97\n')
            stub.chmod(0o755)
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("CAPTURE_", "DEPLOY_", "SITE_", "GH_", "GITHUB_"))
        }
        # A script importing a sibling would otherwise write __pycache__ into the tree.
        self.env.update(
            ENV_FILE=str(self.root / "absent.env"),
            PATH=f"{stubs}{os.pathsep}{os.environ.get('PATH', '')}",
            PYTHONDONTWRITEBYTECODE="1",
        )

    def fresh(self, path: str) -> None:
        """Empty home and working directories of this script's own, so one failure stays its own."""
        self.record.unlink(missing_ok=True)
        base = self.root / path.replace("/", "_")
        self.home, self.cwd = base / "home", base / "cwd"
        self.home.mkdir(parents=True)
        self.cwd.mkdir()
        self.env["HOME"] = str(self.home)

    def run_script(self, path: str, *args: str) -> subprocess.CompletedProcess[str]:
        interpreter = [sys.executable] if path.endswith(".py") else ["bash"]
        return subprocess.run(
            [*interpreter, str(REPO / path), *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.cwd,
            env=self.env,
            timeout=60,
        )

    def assert_no_effect(self, path: str, before: str) -> None:
        called = self.record.read_text().split() if self.record.exists() else []
        self.assertEqual([], called, f"{path} called a stubbed command")
        self.assertEqual([], list(self.home.iterdir()), f"{path} wrote into HOME")
        self.assertEqual(
            [], list(self.cwd.iterdir()), f"{path} wrote into its working directory"
        )
        self.assertEqual(before, tree_status(), f"{path} changed the tree")

    def test_every_entry_point_is_declared(self) -> None:
        found = set(entry_points())
        self.assertEqual(
            set(), found - NO_REQUIRED_ARGUMENT - set(BEFORE_FLAG), "undeclared"
        )
        self.assertEqual(
            set(),
            (NO_REQUIRED_ARGUMENT | set(BEFORE_FLAG)) - found,
            "declared, not tracked",
        )

    def test_help_answers_and_unknown_flag_is_refused(self) -> None:
        for path in entry_points():
            with self.subTest(path=path):
                self.fresh(path)
                before = tree_status()
                long, short = (
                    self.run_script(path, "--help"),
                    self.run_script(path, "-h"),
                )
                self.assertEqual(0, long.returncode, long.stderr)
                self.assertEqual(0, short.returncode, short.stderr)
                self.assertEqual(long.stdout, short.stdout)
                late = self.run_script(path, "extra", "--help")
                self.assertEqual(0, late.returncode, late.stderr)
                self.assertEqual(long.stdout, late.stdout)
                self.assertRegex(
                    long.stdout.splitlines()[0] if long.stdout else "",
                    rf"^usage: \S*{re.escape(pathlib.PurePosixPath(path).name)}\b",
                )
                refused = self.run_script(
                    path, *BEFORE_FLAG.get(path, ()), "--bogus-flag"
                )
                self.assertNotEqual(0, refused.returncode)
                self.assertNotIn("Traceback", refused.stderr)
                self.assertRegex(refused.stderr, REFUSED_AS_OPTION)
                self.assert_no_effect(path, before)


if __name__ == "__main__":
    unittest.main()
