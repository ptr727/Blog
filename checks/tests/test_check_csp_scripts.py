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
    def run_gate(self, pages, sources, csp=None):
        with tempfile.TemporaryDirectory() as tmp:
            public = pathlib.Path(tmp)
            for rel, html in pages.items():
                path = public / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(html, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                return gate.check(public, csp or policy(*sources))

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

    def test_every_type_the_browser_runs_is_checked(self) -> None:
        for kind in (
            "module",
            "importmap",
            "speculationrules",
            "Application/X-JavaScript",
        ):
            with self.subTest(kind):
                html = f'<script type="{kind}">{THEME}</script>'
                findings = self.run_gate({"index.html": html}, ["'self'"])
                self.assertEqual(len(findings), 1)

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

    def test_a_valueless_src_body_is_not_hashed(self) -> None:
        html = f"<script src>{THEME}</script>"
        self.assertEqual(self.run_gate({"index.html": html}, ["'self'"]), [])

    def test_a_scheme_url_needs_its_scheme_named(self) -> None:
        for scheme in ("data", "blob"):
            with self.subTest(scheme):
                html = f'<script src="{scheme}:text/javascript,go()"></script>'
                findings = self.run_gate({"index.html": html}, ["'self'"])
                self.assertEqual(len(findings), 1)
                self.assertIn("does not name", findings[0])
                named = ["'self'", f"{scheme}:"]
                self.assertEqual(self.run_gate({"index.html": html}, named), [])

    def test_handlers_and_javascript_urls_fail(self) -> None:
        for html, expected in (
            ('<button onclick="go()">Go</button>', "inline event handler"),
            ('<a href=" JavaScript:go()">Go</a>', "javascript: URL"),
            ('<script src="javascript:go()">fallback()</script>', "javascript: URL"),
        ):
            with self.subTest(html):
                findings = self.run_gate({"index.html": html}, ["'self'"])
                self.assertEqual(len(findings), 1)
                self.assertIn(expected, findings[0])

    def test_an_embed_from_another_host_fails_under_its_directive(self) -> None:
        for html, directive in (
            ('<iframe src="https://maps.example.test/x"></iframe>', "frame-src"),
            ('<frame src="https://maps.example.test/x">', "frame-src"),
            ('<video src="https://cdn.example.test/a.mp4"></video>', "media-src"),
            ('<audio src="https://cdn.example.test/a.mp3"></audio>', "media-src"),
            (
                '<video><source src="https://cdn.example.test/a.webm"></video>',
                "media-src",
            ),
            (
                '<video><track src="https://cdn.example.test/a.vtt"></video>',
                "media-src",
            ),
            ('<embed src="https://cdn.example.test/a.swf">', "object-src"),
            ('<object data="https://cdn.example.test/a.pdf"></object>', "object-src"),
        ):
            with self.subTest(html):
                findings = self.run_gate({"index.html": html}, ["'self'"])
                self.assertEqual(len(findings), 1)
                self.assertIn(f"{directive} does not name", findings[0])

    def test_an_embed_from_the_site_itself_passes_under_default_src(self) -> None:
        html = '<video src="/media/a.mp4"></video><iframe src="/demo/"></iframe>'
        self.assertEqual(self.run_gate({"index.html": html}, ["'self'"]), [])

    def test_a_named_host_passes_and_the_fallback_order_holds(self) -> None:
        html = '<iframe src="https://maps.example.test/x"></iframe>'
        host = "https://maps.example.test"
        for csp, findings in (
            (f"default-src 'self'; frame-src {host}", 0),
            (f"default-src 'self'; child-src {host}", 0),
            (f"default-src {host}", 0),
            (f"default-src {host}; frame-src 'self'", 1),
            (f"default-src {host}; child-src 'self'", 1),
        ):
            with self.subTest(csp):
                found = self.run_gate({"index.html": html}, [], csp)
                self.assertEqual(len(found), findings, found)

    def test_object_src_none_refuses_even_the_site_itself(self) -> None:
        html = '<object data="/a.pdf"></object>'
        csp = "default-src 'self'; object-src 'none'"
        findings = self.run_gate({"index.html": html}, [], csp)
        self.assertEqual(len(findings), 1)
        self.assertIn("object-src does not name", findings[0])

    def test_an_embed_without_a_value_or_with_about_blank_is_not_checked(self) -> None:
        html = (
            '<iframe src=""></iframe><video src></video><object></object>'
            '<iframe src="about:blank"></iframe>'
        )
        self.assertEqual(self.run_gate({"index.html": html}, ["'self'"]), [])

    def test_a_javascript_embed_is_reported_once(self) -> None:
        html = '<iframe src=" javascript:go()"></iframe>'
        findings = self.run_gate({"index.html": html}, ["'self'"])
        self.assertEqual(len(findings), 1)
        self.assertIn("javascript: URL", findings[0])


class PolicyTest(unittest.TestCase):
    def test_the_blog_policy_is_read(self) -> None:
        blog = policy("'self'", "'sha256-AAAA'")
        family = policy("'none'")
        text = (
            "blog\tReferrer-Policy: no-referrer\n"
            f"blog\tContent-Security-Policy: {blog}\n"
            f"family\tContent-Security-Policy: {family}\n"
        )
        self.assertEqual(gate.blog_policy(text), blog)

    def test_a_blog_without_a_policy_reads_as_none(self) -> None:
        family = policy("'self'")
        text = f"family\tContent-Security-Policy: {family}\n"
        self.assertIsNone(gate.blog_policy(text))

    def test_script_src_is_read_and_default_src_stands_in_for_it(self) -> None:
        sources = gate.script_sources(policy("'self'", "'sha256-AAAA'"))
        self.assertEqual(sources, ["'self'", "'sha256-AAAA'"])
        fallback = gate.script_sources("default-src 'self'; img-src 'self'")
        self.assertEqual(fallback, ["'self'"])
        self.assertEqual(gate.script_sources("img-src 'self'"), [])

    def load(self, headers, caddyfile):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "security-headers.txt").write_text(headers, encoding="utf-8")
            (root / "Caddyfile").write_text(caddyfile, encoding="utf-8")
            return gate.load_policy(root / "security-headers.txt", root / "Caddyfile")

    def test_a_policy_the_caddyfile_sends_loads(self) -> None:
        blog = policy("'self'")
        sent = f'header {{\n\tContent-Security-Policy "{blog}"\n}}\n'
        held = f"blog\tContent-Security-Policy: {blog}\n"
        self.assertEqual(self.load(held, sent), (blog, None))

    def test_a_caddyfile_sending_another_value_refuses(self) -> None:
        sent_policy = policy("'self'")
        held_policy = policy("'self'", "'sha256-AAAA'")
        sent = f'header {{\n\tContent-Security-Policy "{sent_policy}"\n}}\n'
        held = f"blog\tContent-Security-Policy: {held_policy}\n"
        loaded, refusal = self.load(held, sent)
        self.assertIsNone(loaded)
        self.assertIn("Caddyfile does not send", refusal or "")

    def test_a_header_file_without_a_blog_policy_refuses(self) -> None:
        loaded, refusal = self.load("blog\tReferrer-Policy: no-referrer\n", "")
        self.assertIsNone(loaded)
        self.assertIn("holds no Content-Security-Policy", refusal or "")


if __name__ == "__main__":
    unittest.main()
