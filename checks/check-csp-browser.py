#!/usr/bin/env python3
"""Load a running site in headless Chromium and report what its Content-Security-Policy blocks.

`check-csp-scripts.py` proves the built scripts match the policy's hashes. It cannot see what a
browser blocks at run time: a style, a font, a fetch, an image, or a script a proxy injects. This
check loads each page in a URL list against a mirror. It records every `securitypolicyviolation`
event in the page and in each frame it holds, as it fires. The event fires for an enforcing policy
and a Report-Only one alike. Each page is scrolled to its end so lazy images load, and its
code-copy buttons are clicked. The search page also gets a typed query, so the index fetch and the
results run.

The browser runs in the Playwright image `browser/Dockerfile` pins, where Dependabot moves it. The
Playwright package is installed at the image tag's own version, so the two never disagree. The
host needs Docker and `uv`, and nothing else.

A violation fails the run unless `csp-browser-allow.txt` lists its directive and blocked origin.
On a run over the default list, an entry nothing matched fails it too, so the list cannot outlive
what it excuses. A page that does not answer `200` fails the run, since a trial over error pages
proves nothing.
"""

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urljoin, urlsplit

CHECKS = pathlib.Path(__file__).resolve().parent
DOCKERFILE = CHECKS / "browser" / "Dockerfile"
ALLOW = CHECKS / "csp-browser-allow.txt"
URLS = CHECKS / "golden-urls.txt"
SEARCH_PATH = "/search/"
SEARCH_QUERY = "raid"
IMAGE = re.compile(r"^FROM\s+(\S+:v(\d+\.\d+\.\d+)-\S+)\s*$", re.MULTILINE)


def pinned_image(dockerfile_text):
    """The image reference the Dockerfile pins and the Playwright version its tag names."""
    found = IMAGE.search(dockerfile_text)
    if found is None:
        raise ValueError("no FROM line naming a vX.Y.Z Playwright tag")
    return found.group(1), found.group(2)


def read_paths(texts):
    """The site paths the lists name, in order, once each, the search page always among them."""
    paths = []
    for text in texts:
        for line in text.splitlines():
            path = line.strip()
            if path and path not in paths:
                paths.append(path)
    if SEARCH_PATH not in paths:
        paths.append(SEARCH_PATH)
    return paths


def read_allow(text):
    """The allow list as (directive, origin) pairs, each line also carrying its reason."""
    entries = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 3 or not all(field.strip() for field in fields):
            raise ValueError(
                f"line {number}: want directive, origin, and reason, tab separated"
            )
        entries.append((fields[0].strip(), fields[1].strip()))
    return entries


def blocked_origin(blocked):
    """A blocked URL reduced to its origin, or the keyword the browser reports in its place."""
    parts = urlsplit(blocked)
    if parts.scheme in ("http", "https") and parts.netloc:
        return f"{parts.scheme}://{parts.netloc}"
    return blocked


def summarize(records, allow, complete):
    """Fold the probe's records into findings, allowed counts, and pages loaded.

    An allow entry nothing matched is a finding only where the run covered the whole default list.
    """
    violations = {}
    failures = []
    loaded = 0
    for record in records:
        if "status" in record:
            loaded += 1
            if record["status"] != 200:
                failures.append(f"{record['page']} answered {record['status']}")
            continue
        if "error" in record:
            failures.append(f"{record['page']}: {record['error']}")
            continue
        key = (record["directive"], blocked_origin(record["blocked"]))
        entry = violations.setdefault(
            key, {"count": 0, "page": record["page"], "disposition": set()}
        )
        entry["count"] += 1
        entry["disposition"].add(record["disposition"])
    allowed = {key: violations.pop(key)["count"] for key in allow if key in violations}
    findings = failures + [
        f"{directive} blocked {origin} {entry['count']} time(s)"
        f" ({'/'.join(sorted(entry['disposition']))}), first on {entry['page']}"
        for (directive, origin), entry in sorted(violations.items())
    ]
    findings += [
        f"the allow list names {directive} {origin}, which nothing blocked"
        for directive, origin in allow
        if complete and (directive, origin) not in allowed
    ]
    return findings, allowed, loaded


def docker_command(image, version, base_url, cache):
    uv = shutil.which("uv")
    if uv is None:
        raise FileNotFoundError("uv is not on PATH")
    return [
        "docker",
        "run",
        "--rm",
        "-i",
        "--network",
        "host",
        "-u",
        f"{os.getuid()}:{os.getgid()}",
        "-e",
        "HOME=/tmp",
        "-e",
        "UV_CACHE_DIR=/uv-cache",
        "-v",
        f"{uv}:/usr/local/bin/uv:ro",
        "-v",
        f"{cache}:/uv-cache",
        "-v",
        f"{CHECKS}:/checks:ro",
        image,
        "uv",
        "run",
        "--no-project",
        "--python",
        "/usr/bin/python3",
        "--with",
        f"playwright=={version}",
        "python",
        "/checks/check-csp-browser.py",
        "--probe",
        base_url,
    ]


def run_probe(command, paths, timeout):
    """The probe's records, one JSON object per output line, or a refusal naming why none came."""
    try:
        done = subprocess.run(
            command,
            input="\n".join(paths) + "\n",
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, f"the browser probe did not finish: {error}"
    if done.returncode != 0:
        return (
            None,
            f"the browser probe exited {done.returncode}: {done.stderr[-2000:]}",
        )
    return [json.loads(line) for line in done.stdout.splitlines() if line], None


LISTENER = """
document.addEventListener('securitypolicyviolation', (e) => window.__cspReport({
  directive: e.effectiveDirective, blocked: e.blockedURI, disposition: e.disposition}));
"""


def probe(base_url, paths):
    """Run inside the container, writing one JSON record per page and per violation."""
    from playwright.sync_api import Error, sync_playwright

    def emit(record):
        print(json.dumps(record), flush=True)

    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        context = browser.new_context()
        violations = []
        context.expose_binding(
            "__cspReport", lambda _, record: violations.append(record)
        )
        context.add_init_script(LISTENER)
        page = context.new_page()
        for path in paths:
            try:
                response = page.goto(urljoin(base_url, path), wait_until="load")
                emit({"page": path, "status": response.status if response else 0})
                page.evaluate(
                    "async () => { for (let y = 0; y < document.body.scrollHeight;"
                    " y += innerHeight) { scrollTo(0, y);"
                    " await new Promise(r => setTimeout(r, 50)); } }"
                )
                for button in page.locator(".copy-code").all():
                    button.dispatch_event("click")
                if path == SEARCH_PATH:
                    page.locator("#searchInput:enabled").press_sequentially(
                        SEARCH_QUERY
                    )
                    page.locator("#searchResults li").first.wait_for()
                page.wait_for_load_state("networkidle")
            except Error as error:
                emit({"page": path, "error": str(error).splitlines()[0]})
            for violation in violations:
                emit({"page": path, **violation})
            violations.clear()
        browser.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=(__doc__ or "").partition("\n")[0])
    parser.add_argument("base_url", help="the running mirror, such as $SITE_BASE_URL")
    parser.add_argument(
        "--urls",
        type=pathlib.Path,
        action="append",
        help=f"a list of site paths, repeatable (default {URLS.name})",
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="run the browser half, reading paths on stdin (inside the container)",
    )
    parser.add_argument(
        "--timeout", type=int, default=3600, help="seconds the whole run may take"
    )
    args = parser.parse_args(argv)
    if not urlsplit(args.base_url).netloc:
        parser.error(f"{args.base_url} is not an absolute URL")
    if args.probe:
        probe(args.base_url, [line.strip() for line in sys.stdin if line.strip()])
        return 0

    image, version = pinned_image(DOCKERFILE.read_text(encoding="utf-8"))
    allow = read_allow(ALLOW.read_text(encoding="utf-8"))
    paths = read_paths(p.read_text(encoding="utf-8") for p in (args.urls or [URLS]))
    cache = pathlib.Path(
        os.environ.get("UV_CACHE_DIR")
        or pathlib.Path(tempfile.gettempdir()) / "blog-csp-browser-uv"
    )
    cache.mkdir(parents=True, exist_ok=True)
    print(f"csp-browser: {len(paths)} pages against {args.base_url}, {image}")
    try:
        command = docker_command(image, version, args.base_url, cache)
    except FileNotFoundError as error:
        sys.exit(f"FAIL: {error}")
    records, refusal = run_probe(command, paths, args.timeout)
    if records is None:
        sys.exit(f"FAIL: {refusal}")

    findings, allowed, loaded = summarize(records, allow, args.urls is None)
    for (directive, origin), count in sorted(allowed.items()):
        print(f"  allowed: {directive} blocked {origin} {count} time(s)")
    if loaded != len(paths):
        findings.insert(0, f"{loaded} of {len(paths)} pages reported a load")
    if not findings:
        print(f"PASS - {loaded} pages loaded with no violation the allow list lacks")
        return 0
    print(
        f"FAIL csp-browser: {len(findings)} problem{'' if len(findings) == 1 else 's'}"
    )
    for item in findings:
        print(f"  {item}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
