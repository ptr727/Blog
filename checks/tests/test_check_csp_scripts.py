"""Tests for check-csp-scripts.py, every page in them constructed rather than built."""

import contextlib
import importlib.util
import io
import pathlib
import tempfile
import unittest

CHECKS = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "check_csp_scripts", CHECKS / "check-csp-scripts.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load check-csp-scripts.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

THEME = "document.body.dataset.ready=1"
PAGE = f"<!doctype html><html><head><script>{THEME}</script></head><body></body></html>"


def policy(*sources):
    return f"default-src 'self'; script-src {' '.join(sources)}; img-src 'self'"


class CheckTest(unittest.TestCase):
    def run_gate(self, pages, sources):
        with tempfile.TemporaryDirectory() as tmp:
            public = pathlib.Path(tmp)
            for rel, html in pages.items():
                path = public / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(html, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                return gate.check(public, sources)

    def test_a_listed_hash_for_every_inline_script_passes(self) -> None:
        sources = ["'self'", gate.digest(THEME)]
        pages = {"index.html": PAGE, "a/index.html": PAGE}
        self.assertEqual(self.run_gate(pages, sources), [])

    def test_an_unlisted_inline_script_fails_with_its_hash(self) -> None:
        findings = self.run_gate({"index.html": PAGE}, ["'self'"])
        self.assertEqual(len(findings), 1)
        self.assertIn(gate.digest(THEME), findings[0])
        self.assertIn("not in script-src", findings[0])

    def test_a_hash_no_script_matches_fails(self) -> None:
        stale = gate.digest("retired()")
        sources = ["'self'", gate.digest(THEME), stale]
        findings = self.run_gate({"index.html": PAGE}, sources)
        self.assertEqual(
            findings, [f"script-src lists {stale}, which no inline script matches"]
        )

    def test_a_changed_byte_is_a_different_script(self) -> None:
        sources = ["'self'", gate.digest(THEME)]
        changed = PAGE.replace(THEME, THEME + ";")
        findings = self.run_gate({"index.html": changed}, sources)
        self.assertEqual(len(findings), 2)

    def test_the_hash_covers_the_raw_text_without_decoding_references(self) -> None:
        body = "if (a &amp;&amp; b) {}"
        html = f"<script>{body}</script>"
        findings = self.run_gate({"index.html": html}, ["'self'", gate.digest(body)])
        self.assertEqual(findings, [])

    def test_data_blocks_and_empty_scripts_are_not_checked(self) -> None:
        html = (
            '<script type="application/ld+json">{"@type": "BlogPosting"}</script>'
            "<script></script>"
        )
        self.assertEqual(self.run_gate({"index.html": html}, ["'self'"]), [])

    def test_a_module_script_is_checked(self) -> None:
        html = f'<script type="module">{THEME}</script>'
        self.assertEqual(len(self.run_gate({"index.html": html}, ["'self'"])), 1)

    def test_a_script_url_needs_its_origin_named(self) -> None:
        own = '<script src="/assets/js/search.js"></script>'
        other = '<script src="https://cdn.example.test/embed.js"></script>'
        relative = '<script src="//cdn.example.test/embed.js"></script>'
        self.assertEqual(self.run_gate({"index.html": own}, ["'self'"]), [])
        for html in (other, relative):
            with self.subTest(html):
                findings = self.run_gate({"index.html": html}, ["'self'"])
                self.assertEqual(len(findings), 1)
                self.assertIn("does not name", findings[0])
        named = ["'self'", "https://cdn.example.test"]
        self.assertEqual(self.run_gate({"index.html": other}, named), [])

    def test_handlers_and_javascript_urls_fail(self) -> None:
        for html, expected in (
            ('<button onclick="go()">Go</button>', "inline event handler"),
            ('<a href=" JavaScript:go()">Go</a>', "javascript: URL"),
        ):
            with self.subTest(html):
                findings = self.run_gate({"index.html": html}, ["'self'"])
                self.assertEqual(len(findings), 1)
                self.assertIn(expected, findings[0])


class PolicyTest(unittest.TestCase):
    def test_the_blog_script_sources_are_read(self) -> None:
        blog = policy("'self'", "'sha256-AAAA'")
        family = policy("'none'")
        text = (
            "blog\tReferrer-Policy: no-referrer\n"
            f"blog\tContent-Security-Policy: {blog}\n"
            f"family\tContent-Security-Policy: {family}\n"
        )
        self.assertEqual(gate.script_sources(text), ["'self'", "'sha256-AAAA'"])

    def test_a_blog_without_a_policy_reads_as_none(self) -> None:
        family = policy("'self'")
        text = f"family\tContent-Security-Policy: {family}\n"
        self.assertIsNone(gate.script_sources(text))

    def test_the_carried_blog_policy_never_allows_every_inline_script(self) -> None:
        sources = gate.script_sources(gate.HEADERS.read_text(encoding="utf-8"))
        self.assertIsNotNone(sources)
        assert sources is not None
        self.assertIn("'self'", sources)
        self.assertNotIn("'unsafe-inline'", sources)


if __name__ == "__main__":
    unittest.main()
