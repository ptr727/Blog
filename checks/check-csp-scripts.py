#!/usr/bin/env python3
"""Verify that the blog's Content-Security-Policy allows every script the built site runs.

The policy is read from `checks/security-headers.txt`, which a unit case holds equal to the
Caddyfile. Every inline script must carry a hash the policy lists, and every hash the policy
lists must match an inline script, so a Hugo or theme update that changes a script's bytes fails
here rather than in a reader's browser. A script loaded by URL must come from an origin the
policy names, and an inline event handler or a `javascript:` URL fails outright, since a hash
cannot allow either.
"""

import argparse
import base64
import collections
import hashlib
import pathlib
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

CHECKS = pathlib.Path(__file__).resolve().parent
HEADERS = CHECKS / "security-headers.txt"
CSP = "Content-Security-Policy"

# A script element whose type is none of these is a data block, which the browser never runs.
SCRIPT_TYPES = {"", "module", "text/javascript", "application/javascript"}


def script_sources(headers_text):
    """The script-src tokens of the blog's policy, or None where the blog sends no policy."""
    for line in headers_text.splitlines():
        site, _, header = line.partition("\t")
        name, _, value = header.partition(": ")
        if site != "blog" or name not in (CSP, CSP + "-Report-Only"):
            continue
        for directive in value.split(";"):
            tokens = directive.split()
            if tokens and tokens[0] == "script-src":
                return tokens[1:]
        return []
    return None


def digest(body):
    return "'sha256-" + base64.b64encode(hashlib.sha256(body.encode()).digest()).decode() + "'"


class ScriptScan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.inline = []
        self.loaded = []
        self.findings = []
        self.body = None

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name.startswith("on"):
                self.findings.append(f"<{tag} {name}> is an inline event handler")
            elif name in ("href", "src", "action") and (value or "").strip().lower().startswith("javascript:"):
                self.findings.append(f"<{tag} {name}> is a javascript: URL")
        if tag != "script":
            return
        attr = dict(attrs)
        if (attr.get("type") or "").strip().lower() not in SCRIPT_TYPES:
            return
        if attr.get("src") is not None:
            self.loaded.append(attr["src"] or "")
        else:
            self.body = []

    def handle_data(self, data):
        if self.body is not None:
            self.body.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.body is not None:
            self.inline.append("".join(self.body))
            self.body = None


def allowed(src, sources):
    parts = urlsplit(src if not src.startswith("//") else "https:" + src)
    if not parts.netloc:
        return "'self'" in sources
    return f"{parts.scheme}://{parts.netloc}" in sources


def check(public, sources):
    used = collections.defaultdict(list)
    findings = []
    for path in sorted(public.rglob("*.html")):
        rel = str(path.relative_to(public)).replace("\\", "/")
        scan = ScriptScan()
        scan.feed(path.read_text(encoding="utf-8", errors="replace"))
        scan.close()
        findings += [f"{rel}: {finding}" for finding in scan.findings]
        findings += [
            f"{rel}: <script src={src}> is from an origin script-src does not name"
            for src in scan.loaded
            if not allowed(src, sources)
        ]
        for body in scan.inline:
            # An empty element runs nothing, and the browser does not check it against the policy.
            if body:
                used[digest(body)].append(rel)
    listed = {token for token in sources if token.startswith("'sha256-")}
    for token, pages in sorted(used.items()):
        if token not in listed:
            findings.append(f"{pages[0]}: inline script {token} is not in script-src, on {len(pages)} page(s)")
    findings += [f"script-src lists {token}, which no inline script matches" for token in sorted(listed - used.keys())]
    print(f"csp: {len(used)} distinct inline scripts, {len(listed)} hashes in script-src")
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("public", type=pathlib.Path, help="the built site, as hugo wrote it")
    args = parser.parse_args(argv)
    if not args.public.is_dir():
        sys.exit(f"FAIL: {args.public} is not a directory - run hugo first")
    sources = script_sources(HEADERS.read_text(encoding="utf-8"))
    if sources is None:
        sys.exit(f"FAIL: {HEADERS.name} holds no {CSP} for the blog")

    findings = check(args.public, sources)
    if not findings:
        print("PASS - the blog's script-src allows every script the site runs")
        return 0
    print(f"FAIL csp: {len(findings)} problem{'' if len(findings) == 1 else 's'}")
    for item in findings[:20]:
        print(f"  {item}")
    if len(findings) > 20:
        print(f"  ... and {len(findings) - 20} more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
