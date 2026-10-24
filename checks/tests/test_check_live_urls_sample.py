"""Tests for the sampled mode of check-live-urls.sh, against a constructed local server."""

import collections
import functools
import http.server
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from collections.abc import Iterator
from typing import Any, ClassVar, Self, cast

CHECKS = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = CHECKS / "check-live-urls.sh"
README = CHECKS.parent / "deploy" / "README.md"
CADDYFILE = CHECKS.parent / "deploy" / "Caddyfile"
LISTS = (
    "golden-urls.txt",
    "redirect-urls.txt",
    "golden-media-live.txt",
    "security-headers.txt",
)

# The edge's crawl scenario overflows past 40 distinct paths, and the sample keeps a margin under it.
MAX_PATHS = 30
RENDER_CLASSES = {
    "home",
    "home pagination",
    "post",
    "page",
    "tag archive",
    "category archive",
    "term pagination",
    "redirect destination",
}
MEDIA_CLASSES = {"media", "external", "legacy upload"}
FAMILY_PAGES = {"/", "/en/", "/af/"}
DESTINATION = "/followed-destination/"
MISSING_PROBE = "/media/live-check-missing.png"


def expected_headers(site: str) -> list[tuple[str, str]]:
    """The (name, value) pairs security-headers.txt holds for one site, in file order."""
    pairs = []
    for line in (
        (CHECKS / "security-headers.txt").read_text(encoding="utf-8").splitlines()
    ):
        row_site, header = line.split("\t", 1)
        if row_site == site:
            name, value = header.split(": ", 1)
            pairs.append((name, value))
    return pairs


def clean_env(**extra: str) -> dict[str, str]:
    """An environment carrying no site variable from the caller's shell."""
    env = {
        name: os.environ[name]
        for name in ("PATH", "HOME", "LANG")
        if name in os.environ
    }
    env.update(extra)
    return env


def run(
    script: pathlib.Path, *args: str, **env: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        timeout=300,
        env=clean_env(**env),
        check=False,
    )


def plan(script: pathlib.Path = SCRIPT) -> list[list[str]]:
    result = run(script, "--print-sample")
    if result.returncode != 0:
        raise AssertionError(f"--print-sample failed: {result.stderr}")
    return [line.split("\t") for line in result.stdout.splitlines()]


def readme_classes() -> collections.Counter[tuple[str, int]]:
    """The redirect table's rows as (matcher, class size), backticks dropped."""
    section = README.read_text(encoding="utf-8").split(
        "## How the redirects are expressed"
    )[1]
    section = section.split("\n## ")[0]
    rows = re.findall(r"^\| (`@[^|]+?) \| (\d+) \|", section, re.MULTILINE)
    return collections.Counter((cell.replace("`", ""), int(n)) for cell, n in rows)


class SamplePlanTests(unittest.TestCase):
    def test_every_redirect_class_in_the_table_is_sampled_with_its_size(self) -> None:
        # A label's parenthetical splits the two blogger.map rows, which share a matcher cell.
        sampled = collections.Counter(
            (re.sub(r" \(.*\)$", "", cls), int(size))
            for kind, cls, size, _ in plan()
            if kind == "redirect"
        )
        expected = readme_classes()
        self.assertEqual(len(expected), 17)
        self.assertEqual(sampled, expected)

    def test_render_media_and_family_are_each_sampled(self) -> None:
        entries = plan()
        by_kind: dict[str, set[str]] = collections.defaultdict(set)
        for kind, cls, _, url in entries:
            by_kind[kind].add(cls)
            if kind == "family":
                by_kind["family pages"].add(url)
        self.assertLessEqual(RENDER_CLASSES, by_kind["render"])
        self.assertLessEqual(MEDIA_CLASSES, by_kind["media"])
        self.assertEqual(by_kind["family pages"], FAMILY_PAGES)

    def test_every_sampled_url_comes_from_its_list(self) -> None:
        source = {
            "render": "golden-urls.txt",
            "redirect": "redirect-urls.txt",
            "media": "golden-media-live.txt",
        }
        for kind, cls, _, url in plan():
            if kind in source and cls != "redirect destination":
                listed = (CHECKS / source[kind]).read_text(encoding="utf-8").split()
                self.assertIn(url, listed)

    def test_each_redirect_destination_is_a_fixed_caddyfile_target(self) -> None:
        caddyfile = (CHECKS.parent / "deploy" / "Caddyfile").read_text(encoding="utf-8")
        fixed = set(
            re.findall(r"^\s*redir @\w+ (/[^\s{]*) 301$", caddyfile, re.MULTILINE)
        )
        entries = plan()
        sampled = {url for _, cls, _, url in entries if cls == "redirect destination"}
        rendered = {url for kind, _, _, url in entries if kind == "render"}
        self.assertTrue(sampled)
        self.assertLessEqual(sampled, fixed)
        # A sampled redirect is not followed, so a fixed target missing here goes unchecked.
        self.assertLessEqual(fixed, rendered)

    def test_two_runs_sample_the_same_urls(self) -> None:
        self.assertEqual(plan(), plan())

    def test_sample_is_within_the_edge_budget(self) -> None:
        budget = {
            cls: (int(n), int(limit))
            for kind, cls, n, limit in plan()
            if kind == "budget"
        }
        paths, path_limit = budget["distinct non-static paths"]
        statics, static_limit = budget["static requests"]
        self.assertLessEqual(path_limit, MAX_PATHS)
        self.assertLessEqual(paths, path_limit)
        self.assertLessEqual(statics, static_limit)


class GrownSampleTests(unittest.TestCase):
    """A copy of the script whose sample has been grown past its budget."""

    def setUp(self) -> None:
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for name in LISTS:
            (self.tmp / name).symlink_to(CHECKS / name)
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("SAMPLE_PER_CLASS=1\n", text)
        self.script = self.tmp / SCRIPT.name
        self.script.write_text(
            text.replace("SAMPLE_PER_CLASS=1\n", "SAMPLE_PER_CLASS=2\n"),
            encoding="utf-8",
        )

    def test_print_sample_refuses_a_grown_sample(self) -> None:
        result = run(self.script, "--print-sample")
        self.assertEqual(result.returncode, 1)
        self.assertIn("over its budget", result.stderr)

    def test_a_sampled_run_refuses_before_its_first_request(self) -> None:
        with MockSite() as site:
            result = run(self.script, site.base, SAMPLE_CONTRACT="1")
            self.assertEqual(result.returncode, 1)
            self.assertIn("over its budget", result.stderr)
            self.assertEqual(site.requested, [])


class OptInTests(unittest.TestCase):
    def test_only_1_or_nothing_selects_the_mode(self) -> None:
        for value in ("0", "yes", "true"):
            result = run(SCRIPT, "http://127.0.0.1:9", SAMPLE_CONTRACT=value)
            self.assertEqual(result.returncode, 2, value)
            self.assertIn("SAMPLE_CONTRACT takes 1 or nothing", result.stderr)


class Handler(http.server.BaseHTTPRequestHandler):
    """Answers every redirect source with a 301 to one shared destination, and anything else as a page or an image."""

    redirects: ClassVar[set[str]] = set()
    requested: ClassVar[list[str]] = []
    page: ClassVar[bytes] = b"<html></html>"
    site_headers: ClassVar[list[tuple[str, str]]] = []

    def headers_for(self, path: str) -> list[tuple[str, str]]:
        """The headers this response carries, which a test narrows for one path."""
        return self.site_headers

    def do_GET(self) -> None:
        self.requested.append(self.path)
        if self.path.split("?", 1)[0] == MISSING_PROBE:
            self.answer(404, body=b"<html></html>", content_type="text/html")
        elif self.path.startswith("/wp-content/uploads/"):
            # Caddy's rule drops the query, as here.
            path = self.path.split("?", 1)[0]
            self.answer(301, location="/media/" + path.split("/uploads/", 1)[1])
        elif self.path.startswith(("/media/", "/external/")):
            self.answer(200, body=b"\x89PNG", content_type="image/png")
        elif self.path in self.redirects:
            self.answer(301, location=DESTINATION)
        else:
            self.answer(200, body=self.page, content_type="text/html")

    def answer(
        self, code: int, location: str = "", body: bytes = b"", content_type: str = ""
    ) -> None:
        self.send_response(code)
        for name, value in self.headers_for(self.path):
            self.send_header(name, value)
        if location:
            self.send_header("Location", location)
        if content_type:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


def family_page() -> bytes:
    """A page carrying every title the script expects of a family page."""
    script = SCRIPT.read_text(encoding="utf-8")
    titles = re.findall(
        r'"/[^"|]*\|([^"]+)"', script.split("FAMILY_PAGES=(", 1)[1].split("\n", 1)[0]
    )
    return "".join(f"<title>{title}</title>" for title in titles).encode()


class MockSite:
    def __init__(
        self,
        page: bytes = Handler.page,
        site: str = "blog",
        handler: type[Handler] = Handler,
    ) -> None:
        self.page = page
        self.headers = expected_headers(site)
        self.base_handler = handler

    def __enter__(self) -> Self:
        redirects = (CHECKS / "redirect-urls.txt").read_text(encoding="utf-8").split()

        SiteHandler = cast(
            "type[Handler]", type("SiteHandler", (self.base_handler,), {})
        )
        SiteHandler.site_headers = self.headers
        SiteHandler.redirects = set(redirects)
        SiteHandler.requested = []
        SiteHandler.page = self.page
        self.handler = SiteHandler
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), SiteHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        return self

    @property
    def requested(self) -> list[str]:
        return self.handler.requested

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()


def non_static(paths: list[str]) -> set[str]:
    return {
        p for p in paths if not p.startswith(("/media/", "/external/", "/wp-content/"))
    }


class SampledRunTests(unittest.TestCase):
    def test_sampled_run_requests_exactly_the_planned_paths(self) -> None:
        entries = plan()
        planned = {"/"} | {
            url for kind, _, _, url in entries if kind in ("render", "redirect")
        }
        with MockSite() as site, MockSite(family_page(), "family") as family:
            result = run(
                SCRIPT,
                site.base,
                SAMPLE_CONTRACT="1",
                SITE_EXTRA_BASE_URL=family.base,
            )
            requested = list(site.requested)
            family_requested = set(family.requested)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("sampled URLs honored", result.stdout)
        self.assertNotIn(DESTINATION, requested)
        self.assertEqual(non_static(requested), planned)
        self.assertEqual(family_requested, FAMILY_PAGES)
        budget = {cls: int(n) for kind, cls, n, _ in entries if kind == "budget"}
        self.assertEqual(
            len(planned) + len(family_requested), budget["distinct non-static paths"]
        )
        statics = [p for p in requested if p not in non_static(requested)]
        self.assertEqual(len(statics), budget["static requests"])

    def test_full_run_is_the_default_and_follows_every_redirect(self) -> None:
        listed = set((CHECKS / "golden-urls.txt").read_text(encoding="utf-8").split())
        listed |= set(
            (CHECKS / "redirect-urls.txt").read_text(encoding="utf-8").split()
        )
        with MockSite() as site:
            result = run(SCRIPT, site.base)
            requested = list(site.requested)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("sampl", result.stdout)
        self.assertIn(DESTINATION, requested)
        self.assertEqual(non_static(requested), listed | {"/", DESTINATION})

    def test_media_requests_carry_a_query_no_earlier_run_sent(self) -> None:
        tokens = []
        for _ in range(2):
            with MockSite() as site:
                result = run(SCRIPT, site.base)
                requested = list(site.requested)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            media = [p for p in requested if p not in non_static(requested)]
            self.assertTrue(any(p.startswith("/wp-content/") for p in media))
            for p in media:
                self.assertRegex(p, r"live-check=", p)
            found = {re.findall(r"live-check=([^&]+)", p)[-1] for p in media}
            self.assertEqual(len(found), 1, media)
            tokens.append(found.pop())
        self.assertNotEqual(tokens[0], tokens[1])


# The headers a site sets that are not security headers, so the sync case leaves them to their own checks.
NOT_SECURITY = {"cache-control", "vary", "x-blog-env", "x-blog-release", "x-robots-tag"}
Header = tuple[str, str, bool]


@functools.cache
def caddy_image() -> str:
    """The image checks/caddy/Dockerfile pins, built once per run."""
    built = subprocess.run(
        ["docker", "build", "-q", str(CHECKS / "caddy")],
        capture_output=True,
        text=True,
        timeout=600,
        check=True,
    )
    return built.stdout.strip()


def adapt(caddyfile: str) -> dict[str, Any]:
    """Caddy's own JSON for a Caddyfile, adapted offline with the release's maps in place."""
    with tempfile.TemporaryDirectory() as tmp:
        (pathlib.Path(tmp) / "Caddyfile").write_text(caddyfile, encoding="utf-8")
        adapted = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "-v",
                f"{tmp}:/etc/caddy:ro",
                "-v",
                f"{CADDYFILE.parent / 'maps'}:/srv/blog/current/maps:ro",
                caddy_image(),
                "caddy",
                "adapt",
                "--config",
                "/etc/caddy/Caddyfile",
                "--adapter",
                "caddyfile",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    if adapted.returncode != 0:
        raise AssertionError(f"caddy adapt failed: {adapted.stderr}")
    config: dict[str, Any] = json.loads(adapted.stdout)
    return config


def header_ops(
    routes: list[dict[str, Any]], scoped: bool, top: bool
) -> Iterator[Header]:
    """Each (name, value, scoped) a headers handler writes, scoped where a matcher or a status requirement narrows it."""
    for route in routes:
        # A top-level host matcher picks the site rather than narrowing it.
        keys = {k for m in route.get("match", []) for k in m}
        narrowed = scoped or bool(keys - {"host"} if top else keys)
        for handler in route.get("handle", []):
            if handler["handler"] == "subroute":
                yield from header_ops(handler.get("routes", []), narrowed, False)
            if handler["handler"] != "headers":
                continue
            response = handler.get("response", {})
            required = narrowed or "require" in response
            for op in ("set", "add"):
                for name, values in response.get(op, {}).items():
                    yield name.lower(), ", ".join(values), required
            for name in [*response.get("delete", []), *response.get("replace", {})]:
                yield name.lower(), "", True


def site_headers(caddyfile: str) -> dict[str, list[tuple[str, str]]]:
    """Per site, the lowercased headers outside NOT_SECURITY it sets on every response, refusing any it narrows."""
    server = next(iter(adapt(caddyfile)["apps"]["http"]["servers"].values()))
    sites: dict[str, list[tuple[str, str]]] = {}
    narrowed = []
    for route in server.get("routes", []):
        hosts = [h for m in route.get("match", []) for h in m.get("host", [])]
        site = "family" if "viljoen.family" in hosts else "blog"
        for name, value, scoped in header_ops([route], False, True):
            if name in NOT_SECURITY:
                continue
            if scoped:
                narrowed.append(f"{site} {name}")
            else:
                sites.setdefault(site, []).append((name, value))
    for name, _, _ in header_ops(
        server.get("errors", {}).get("routes", []), True, True
    ):
        if name not in NOT_SECURITY:
            narrowed.append(f"errors {name}")
    if narrowed:
        raise AssertionError(
            f"{', '.join(narrowed)} reach fewer responses than the live check asserts them on"
        )
    return sites


def without(name: str, target: str) -> type[Handler]:
    """A handler that leaves one header off the responses to one path, the query ignored."""

    class Omitting(Handler):
        def headers_for(self, path: str) -> list[tuple[str, str]]:
            if path.split("?", 1)[0] != target:
                return self.site_headers
            return [(n, v) for n, v in self.site_headers if n != name]

    return Omitting


class SecurityHeaderTests(unittest.TestCase):
    def sampled(
        self, handler: type[Handler] = Handler, family: type[Handler] = Handler
    ) -> subprocess.CompletedProcess[str]:
        with (
            MockSite(handler=handler) as site,
            MockSite(family_page(), "family", family) as fam,
        ):
            return run(
                SCRIPT, site.base, SAMPLE_CONTRACT="1", SITE_EXTRA_BASE_URL=fam.base
            )

    def test_a_missing_header_fails_on_every_kind_of_response(self) -> None:
        entries = plan()
        first = {kind: url for kind, _, _, url in reversed(entries)}
        hsts = "Strict-Transport-Security"
        for what, path in (
            ("preflight", "/"),
            ("render", first["render"]),
            ("redirect", first["redirect"]),
            ("media", first["media"]),
            ("missing", MISSING_PROBE),
        ):
            with self.subTest(what):
                result = self.sampled(handler=without(hsts, path))
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertRegex(
                    result.stdout,
                    rf"{what} \S*{re.escape(path)}\S* sends {hsts} '<none>'",
                )
        csp = "Content-Security-Policy"
        result = self.sampled(family=without(csp, "/en/"))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(f"family /en/ sends {csp} '<none>'", result.stdout)

    def test_headers_are_asserted_on_the_config_the_reload_converges_on(self) -> None:
        class Reloading(Handler):
            def headers_for(self, path: str) -> list[tuple[str, str]]:
                if self.requested.count("/") < 2:
                    return [("X-Blog-Release", "old")]
                return [*self.site_headers, ("X-Blog-Release", "new")]

        with MockSite(handler=Reloading) as site:
            result = run(SCRIPT, site.base, SAMPLE_CONTRACT="1", EXPECT_RELEASE="new")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("rules from release new (after 1s)", result.stdout)

    def test_a_followed_destination_missing_a_header_fails(self) -> None:
        hsts = "Strict-Transport-Security"
        with MockSite(handler=without(hsts, DESTINATION)) as site:
            result = run(SCRIPT, site.base)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(f"{DESTINATION} destination sends {hsts} '<none>'", result.stdout)

    def test_a_weakened_value_fails(self) -> None:
        class Weakened(Handler):
            def headers_for(self, path: str) -> list[tuple[str, str]]:
                return [
                    (n, "max-age=60" if n == "Strict-Transport-Security" else v)
                    for n, v in self.site_headers
                ]

        result = self.sampled(handler=Weakened)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(
            "sends Strict-Transport-Security 'max-age=60', expected 'max-age=31536000'",
            result.stdout,
        )

    def test_a_compliant_run_names_each_host_unconfirmed_off_the_edge(self) -> None:
        result = self.sampled()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count(" UNCONFIRMED, so this run reached"), 2)

    def test_both_edge_headers_read_as_proxied(self) -> None:
        class Edge(Handler):
            def version_string(self) -> str:
                return "cloudflare"

            def headers_for(self, path: str) -> list[tuple[str, str]]:
                return [*self.site_headers, ("CF-RAY", "0-TEST")]

        result = self.sampled(handler=Edge, family=Edge)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count(" proxied\n"), 2)
        self.assertNotIn("UNCONFIRMED", result.stdout)


class CaddyfileSyncTests(unittest.TestCase):
    """Caddy's own parser reads the Caddyfile, so no grammar is re-derived here."""

    def test_expected_values_are_the_caddyfile_values(self) -> None:
        sites = site_headers(CADDYFILE.read_text(encoding="utf-8"))
        for site in ("blog", "family"):
            with self.subTest(site):
                expected = [(n.lower(), v) for n, v in expected_headers(site)]
                self.assertEqual(sorted(sites[site]), sorted(expected))

    def test_any_header_outside_the_known_markers_is_read(self) -> None:
        for directive in (
            'header X-XSS-Protection "0"',
            'route {\n\t\theader X-XSS-Protection "0"\n\t}',
        ):
            with self.subTest(directive):
                sites = site_headers(f":8080 {{\n\t{directive}\n}}\n")
                self.assertEqual(sites["blog"], [("x-xss-protection", "0")])

    def test_a_security_header_reaching_fewer_responses_is_refused(self) -> None:
        for directive in (
            "header @page {\n\t\tX-Frame-Options DENY\n\t}\n\t@page path /x",
            "header /af/* X-Frame-Options DENY",
            "handle /x {\n\t\theader X-Frame-Options DENY\n\t}",
            "header {\n\t\tX-Frame-Options DENY\n\t\tmatch {\n\t\t\tstatus 2xx\n\t\t}\n\t}",
            "header /assets/* -Referrer-Policy",
            "handle_errors {\n\t\theader X-Frame-Options DENY\n\t}",
        ):
            with (
                self.subTest(directive),
                self.assertRaisesRegex(AssertionError, "fewer responses"),
            ):
                site_headers(f":8080 {{\n\t{directive}\n}}\n")


if __name__ == "__main__":
    unittest.main()
