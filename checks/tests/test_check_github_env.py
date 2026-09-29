"""Tests for check-github-env.py, every value in them constructed rather than observed."""

import contextlib
import importlib.util
import io
import pathlib
import unittest
from unittest import mock

CHECKS = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "check_github_env", CHECKS / "check-github-env.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load check-github-env.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

DOC = """# Environment

## The GitHub Environments

Intro prose naming `NOT_A_ROW` in passing.

| Value | Kind | Held on | Names |
| --- | --- | --- | --- |
| `BASE_URL` | variable | `staging`, `production` | the base URL |
| `TOKEN` | secret | `staging` | a token |
| `BOT_KEY` | secret | `repository`, `dependabot` | the bot key |

## Per-invocation knobs

| Value | Effect |
| --- | --- |
| `KNOB` | not a GitHub value |
"""

LISTED = {
    ("staging", "variable", "BASE_URL"),
    ("production", "variable", "BASE_URL"),
    ("staging", "secret", "TOKEN"),
    ("repository", "secret", "BOT_KEY"),
    ("dependabot", "secret", "BOT_KEY"),
}


def lister(stores: dict[str, set[str]]):
    """Build a fake gh lister from API path to the names it returns."""

    def names(path: str, key: str) -> set[str]:
        return set(stores.get(path, set()))

    return names


class ReadTableTests(unittest.TestCase):
    def test_reads_only_the_github_section(self) -> None:
        self.assertEqual(gate.read_table(DOC), LISTED)

    def test_missing_section_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            gate.read_table("# Environment\n\nNo table here.\n")

    def test_row_without_a_store_is_refused(self) -> None:
        doc = DOC.replace(
            "| `TOKEN` | secret | `staging` |", "| `TOKEN` | secret | nowhere |"
        )
        with self.assertRaises(ValueError):
            gate.read_table(doc)

    def test_unknown_kind_is_refused(self) -> None:
        doc = DOC.replace("| `TOKEN` | secret |", "| `TOKEN` | password |")
        with self.assertRaises(ValueError):
            gate.read_table(doc)

    def test_variable_on_dependabot_is_refused(self) -> None:
        doc = DOC.replace(
            "| `BOT_KEY` | secret | `repository`, `dependabot` |",
            "| `BOT_KEY` | variable | `dependabot` |",
        )
        with self.assertRaises(ValueError):
            gate.read_table(doc)


class ReadGithubTests(unittest.TestCase):
    def test_reads_every_store_and_every_environment(self) -> None:
        held = gate.read_github(
            lister(
                {
                    "actions/secrets": {"BOT_KEY"},
                    "actions/variables": set(),
                    "dependabot/secrets": {"BOT_KEY"},
                    "environments": {"staging", "production", "empty"},
                    "environments/staging/variables": {"BASE_URL"},
                    "environments/staging/secrets": {"TOKEN"},
                    "environments/production/variables": {"BASE_URL"},
                }
            )
        )
        self.assertEqual(held, LISTED)

    def test_environment_name_is_escaped_in_the_path(self) -> None:
        seen: list[str] = []

        def names(path: str, key: str) -> set[str]:
            seen.append(path)
            return {"a b"} if path == "environments" else set()

        gate.read_github(names)
        self.assertIn("environments/a%20b/secrets", seen)


class CompareTests(unittest.TestCase):
    def test_agreement_has_no_findings(self) -> None:
        self.assertEqual(gate.compare(LISTED, set(LISTED)), [])

    def test_missing_value(self) -> None:
        held = LISTED - {("staging", "secret", "TOKEN")}
        self.assertEqual(
            gate.compare(LISTED, held),
            ["missing: TOKEN is listed as a secret on staging, which does not hold it"],
        )

    def test_unlisted_value_on_an_unnamed_environment(self) -> None:
        held = LISTED | {("copilot", "secret", "STRAY")}
        self.assertEqual(
            gate.compare(LISTED, held),
            [
                "unlisted: copilot holds the secret STRAY, which ENVIRONMENT.md does not list"
            ],
        )

    def test_wrong_kind_is_one_finding(self) -> None:
        held = (LISTED - {("staging", "secret", "TOKEN")}) | {
            ("staging", "variable", "TOKEN")
        }
        self.assertEqual(
            gate.compare(LISTED, held),
            ["wrong kind: TOKEN on staging is held as a variable, listed as a secret"],
        )

    def test_both_kinds_held_reports_the_extra_one(self) -> None:
        held = LISTED | {("staging", "variable", "TOKEN")}
        self.assertEqual(
            gate.compare(LISTED, held),
            [
                "unlisted: staging holds the variable TOKEN, which ENVIRONMENT.md does not list"
            ],
        )


class MainTests(unittest.TestCase):
    def run_main(self, held=None, error=None) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        read = mock.Mock(return_value=held, side_effect=error)
        with (
            mock.patch.object(gate.DOC.__class__, "read_text", return_value=DOC),
            mock.patch.object(gate, "read_github", read),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = gate.main()
        return code, out.getvalue(), err.getvalue()

    def test_agreement_exits_zero(self) -> None:
        code, out, _ = self.run_main(held=set(LISTED))
        self.assertEqual(code, 0)
        self.assertIn("5 value(s) across 4 store(s)", out)

    def test_finding_exits_one(self) -> None:
        code, out, _ = self.run_main(held=LISTED - {("staging", "secret", "TOKEN")})
        self.assertEqual(code, 1)
        self.assertIn("missing: TOKEN", out)

    def test_unreadable_github_exits_two_not_zero(self) -> None:
        code, out, err = self.run_main(
            error=gate.QueryError("gh api environments failed: HTTP 403")
        )
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("nothing was compared", err)

    def test_gh_failure_raises_query_error(self) -> None:
        failed = mock.Mock(returncode=1, stdout="", stderr="HTTP 401: Bad credentials")
        with (
            mock.patch.object(gate.subprocess, "run", return_value=failed),
            self.assertRaises(gate.QueryError),
        ):
            gate.gh_names("environments", "environments")

    def test_missing_gh_raises_query_error(self) -> None:
        with (
            mock.patch.object(gate.subprocess, "run", side_effect=FileNotFoundError),
            self.assertRaises(gate.QueryError),
        ):
            gate.gh_names("environments", "environments")


if __name__ == "__main__":
    unittest.main()
