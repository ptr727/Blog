"""Tests for check-csp.py, every page and stylesheet in them constructed rather than built."""

import contextlib
import importlib.util
import io
import pathlib
import tempfile
import unittest

CHECKS = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("check_csp", CHECKS / "check-csp.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load check-csp.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

THEME = "document.body.dataset.ready=1"
PAGE = f"<!doctype html><html><head><script>{THEME}</script></head><body></body></html>"
ORIGIN = "https://site.example.test"
OTHER = "https://cdn.example.test"


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
                return gate.check(public, csp or policy(*sources), ORIGIN)

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
        named = ["'self'", OTHER]
        findings = self.run_gate({"index.html": other}, named)
        self.assertEqual(
            findings,
            [f"the policy names {OTHER} under script-src, which allows another host"],
        )

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

    def test_the_fallback_order_holds(self) -> None:
        html = '<iframe src="data:text/html,x"></iframe>'
        for csp, findings in (
            ("default-src 'self'; frame-src data:", 0),
            ("default-src 'self'; child-src data:", 0),
            ("default-src data:", 0),
            ("default-src data:; frame-src 'self'", 1),
            ("default-src data:; child-src 'self'", 1),
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

    def test_every_fetch_from_another_host_fails_under_its_directive(self) -> None:
        for html, directive in (
            (f'<img src="{OTHER}/a.png">', "img-src"),
            (f'<img src="/a.png" srcset="/a.png 1x, {OTHER}/b.png 2x">', "img-src"),
            (f'<picture><source srcset="{OTHER}/a.webp"></picture>', "img-src"),
            (f'<video poster="{OTHER}/a.jpg"></video>', "img-src"),
            (f'<svg><image href="{OTHER}/a.svg"/></svg>', "img-src"),
            (f'<link rel="stylesheet" href="{OTHER}/a.css">', "style-src"),
            (f'<link rel="icon" href="{OTHER}/favicon.ico">', "img-src"),
            (f'<link rel="preload" as="font" href="{OTHER}/a.woff2">', "font-src"),
            (f'<link rel="preload" href="{OTHER}/a">', "default-src"),
            (f'<link rel="modulepreload" href="{OTHER}/a.js">', "script-src"),
            (f'<link rel="manifest" href="{OTHER}/a.json">', "manifest-src"),
            (f'<link rel="preconnect" href="{OTHER}">', "default-src"),
            ('<link rel="dns-prefetch" href="//cdn.example.test">', "default-src"),
            (f'<p style="background: url({OTHER}/a.png)">x</p>', "img-src"),
            (f"<style>@import '{OTHER}/a.css';</style>", "style-src"),
            (f'<style>@import"{OTHER}/a.css";</style>', "style-src"),
            (
                f'<link rel="preload" as="fetch" href="{OTHER}/index.json">',
                "connect-src",
            ),
        ):
            with self.subTest(html):
                findings = self.run_gate({"index.html": html}, [])
                self.assertEqual(len(findings), 1, findings)
                self.assertIn(f"{directive} does not name", findings[0])

    def test_a_link_that_loads_nothing_is_not_checked(self) -> None:
        html = (
            f'<link rel="canonical" href="{OTHER}/a/">'
            f'<link rel="alternate" type="application/rss+xml" href="{OTHER}/feed.xml">'
            '<link rel="stylesheet">'
        )
        self.assertEqual(self.run_gate({"index.html": html}, []), [])

    def test_the_site_itself_passes_by_path_and_by_its_own_origin(self) -> None:
        html = (
            '<img src="/media/a.png" srcset="/media/a.png 1x, /media/b.png 2x">'
            f'<link rel="icon" href="{ORIGIN}/favicon.ico">'
            '<link rel="preload" as="font" href="/fonts/a.woff2" crossorigin>'
        )
        self.assertEqual(self.run_gate({"index.html": html}, []), [])
        elsewhere = html.replace(ORIGIN, ORIGIN + ":8443")
        self.assertEqual(len(self.run_gate({"index.html": elsewhere}, [])), 1)

    def test_a_stylesheet_is_read_by_where_each_url_sits(self) -> None:
        css = (
            "/* url(https://comment.example.test/a.png) */"
            f'@import url("{OTHER}/a.css");'
            f"@font-face {{ font-family: A; src: url('{OTHER}/a.woff2') format('woff2'); }}"
            f"body {{ background: url({OTHER}/b.png), url(#grain); }}"
        )
        findings = self.run_gate({"assets/site.css": css}, [])
        self.assertEqual(
            [f.split(" does not name")[0].rsplit(" ", 1)[1] for f in findings],
            ["style-src", "font-src", "img-src"],
        )
        self.assertTrue(all(f.startswith("assets/site.css: url(") for f in findings))

    def test_a_listed_scheme_passes_in_a_stylesheet(self) -> None:
        css = "html { background: url(\"data:image/svg+xml,%3Csvg filter='url(%23n)'/%3E\"); }"
        csp = "default-src 'self'; img-src 'self' data:"
        self.assertEqual(self.run_gate({"site.css": css}, [], csp), [])
        self.assertEqual(len(self.run_gate({"site.css": css}, [])), 1)

    def test_a_style_block_and_a_font_face_in_it_are_read(self) -> None:
        html = f"<style>@font-face {{ src: url({OTHER}/a.woff2); }}</style>"
        findings = self.run_gate({"index.html": html}, [])
        self.assertEqual(len(findings), 1)
        self.assertIn("<style> url(", findings[0])
        self.assertIn("font-src does not name", findings[0])

    def test_a_named_host_fails_even_where_nothing_uses_it(self) -> None:
        csp = f"default-src 'self'; font-src {OTHER}"
        findings = self.run_gate({"index.html": "<p>x</p>"}, [], csp)
        self.assertEqual(
            findings,
            [f"the policy names {OTHER} under font-src, which allows another host"],
        )


class PolicyTest(unittest.TestCase):
    def test_each_site_policy_is_read(self) -> None:
        blog = policy("'self'", "'sha256-AAAA'")
        family = policy("'none'")
        text = (
            "blog\tReferrer-Policy: no-referrer\n"
            f"blog\tContent-Security-Policy: {blog}\n"
            f"family\tContent-Security-Policy: {family}\n"
        )
        self.assertEqual(gate.site_policy(text, "blog"), blog)
        self.assertEqual(gate.site_policy(text, "family"), family)

    def test_a_site_without_a_policy_reads_as_none(self) -> None:
        family = policy("'self'")
        text = f"family\tContent-Security-Policy: {family}\n"
        self.assertIsNone(gate.site_policy(text, "blog"))

    def test_script_src_is_read_and_default_src_stands_in_for_it(self) -> None:
        sources = gate.directive_sources(
            policy("'self'", "'sha256-AAAA'"), "script-src"
        )
        self.assertEqual(sources, ["'self'", "'sha256-AAAA'"])
        fallback = gate.directive_sources(
            "default-src 'self'; img-src 'self'", "script-src"
        )
        self.assertEqual(fallback, ["'self'"])
        self.assertEqual(gate.directive_sources("img-src 'self'", "script-src"), [])

    def test_a_host_or_a_network_scheme_is_named_and_nothing_else(self) -> None:
        csp = (
            f"default-src 'self'; img-src 'self' data: blob: {OTHER} https:; "
            "connect-src wss: *; script-src 'sha256-AAAA' 'unsafe-inline'; "
            "sandbox allow-scripts; report-to csp-group"
        )
        self.assertEqual(
            gate.named_hosts(csp),
            [
                ("img-src", OTHER),
                ("img-src", "https:"),
                ("connect-src", "wss:"),
                ("connect-src", "*"),
            ],
        )

    def load(self, headers, caddyfile, site="blog"):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "security-headers.txt").write_text(headers, encoding="utf-8")
            (root / "Caddyfile").write_text(caddyfile, encoding="utf-8")
            return gate.load_policy(
                root / "security-headers.txt", root / "Caddyfile", site
            )

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

    def test_a_header_file_without_a_site_policy_refuses(self) -> None:
        loaded, refusal = self.load("blog\tReferrer-Policy: no-referrer\n", "")
        self.assertIsNone(loaded)
        self.assertIn("holds no Content-Security-Policy for the blog", refusal or "")

    def test_the_family_policy_loads_from_its_own_line(self) -> None:
        family = "default-src 'self'; img-src 'self' data:"
        sent = f'header {{\n\tContent-Security-Policy "{family}"\n}}\n'
        held = (
            f"blog\tContent-Security-Policy: {policy()}\n"
            f"family\tContent-Security-Policy: {family}\n"
        )
        self.assertEqual(self.load(held, sent, "family"), (family, None))


if __name__ == "__main__":
    unittest.main()
