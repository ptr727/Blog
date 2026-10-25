#!/usr/bin/env python3
"""Verify that the blog's Content-Security-Policy allows every script and embed the built site loads.

The policy is read from `checks/security-headers.txt`, and `deploy/Caddyfile`, which ships, must
send the same value. Without `script-src` the browser applies `default-src`, and so does this
check. Every inline script must carry a hash the policy lists. Every hash the policy lists
must match an inline script. A Hugo or theme update that changes a script's bytes then fails
here rather than in a reader's browser. A script loaded by URL must come from a host or a
scheme the policy names. An inline event handler or a `javascript:` URL fails outright, since a hash allows
neither without `'unsafe-hashes'`, which the blog policy does not carry. A script whose type the
browser runs is checked, an import map and a speculation rules block included. Any other type is
a data block that never runs, and the browser never checks an empty script, so neither needs a
hash.

A frame, a media file, or an object loads under its own directive. A post may carry raw HTML,
so it can add one from a host the policy does not name. Each such load must come from a host or a
scheme its directive names. The browser's fallbacks apply: `child-src` then `default-src` for a
frame, and `default-src` for the others. An `about:` URL fetches nothing, so no directive applies.
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
CADDYFILE = CHECKS.parent / "deploy" / "Caddyfile"
CSP = "Content-Security-Policy"

SCRIPT_TYPES = {
    "",
    "module",
    "importmap",
    "speculationrules",
    "application/ecmascript",
    "application/javascript",
    "application/x-ecmascript",
    "application/x-javascript",
    "text/ecmascript",
    "text/javascript",
    *(f"text/javascript1.{minor}" for minor in range(6)),
    "text/jscript",
    "text/livescript",
    "text/x-ecmascript",
    "text/x-javascript",
}


def blog_policy(headers_text):
    """The blog's policy as security-headers.txt holds it, or None where the blog sends none."""
    for line in headers_text.splitlines():
        site, _, header = line.partition("\t")
        name, _, value = header.partition(": ")
        if site == "blog" and name == CSP:
            return value
    return None


FALLBACKS = {
    "script-src": ("script-src", "default-src"),
    "frame-src": ("frame-src", "child-src", "default-src"),
    "media-src": ("media-src", "default-src"),
    "object-src": ("object-src", "default-src"),
}

EMBEDS = {
    ("iframe", "src"): "frame-src",
    ("frame", "src"): "frame-src",
    ("audio", "src"): "media-src",
    ("video", "src"): "media-src",
    ("source", "src"): "media-src",
    ("track", "src"): "media-src",
    ("embed", "src"): "object-src",
    ("object", "data"): "object-src",
}


def directive_sources(policy, directive):
    """The sources the browser applies to a directive, its fallbacks included."""
    directives = {}
    for part in policy.split(";"):
        tokens = part.split()
        if tokens:
            directives.setdefault(tokens[0], tokens[1:])
    for name in FALLBACKS[directive]:
        if name in directives:
            return directives[name]
    return []


def script_sources(policy):
    return directive_sources(policy, "script-src")


def digest(body):
    return (
        "'sha256-"
        + base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
        + "'"
    )


class ScriptScan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.inline = []
        self.loaded = []
        self.embeds = []
        self.findings = []
        self.body = None

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            url = (value or "").strip()
            if name.startswith("on"):
                self.findings.append(f"<{tag} {name}> is an inline event handler")
            elif name in ("href", "src", "action") and url.lower().startswith(
                "javascript:"
            ):
                self.findings.append(f"<{tag} {name}> is a javascript: URL")
            elif (tag, name) in EMBEDS and url and not url.lower().startswith("about:"):
                self.embeds.append((tag, name, url, EMBEDS[tag, name]))
        if tag != "script":
            return
        attr = dict(attrs)
        if (attr.get("type") or "").strip().lower() not in SCRIPT_TYPES:
            return
        if "src" not in attr:
            self.body = []
            return
        src = attr["src"] or ""
        if not src.strip().lower().startswith("javascript:"):
            self.loaded.append(src)

    def handle_data(self, data):
        if self.body is not None:
            self.body.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.body is not None:
            self.inline.append("".join(self.body))
            self.body = None


def allowed(src, sources):
    parts = urlsplit(src if not src.startswith("//") else "https:" + src)
    if parts.netloc:
        return f"{parts.scheme}://{parts.netloc}" in sources
    if parts.scheme:
        return f"{parts.scheme}:" in sources
    return "'self'" in sources


def check(public, policy):
    sources = script_sources(policy)
    embed_sources = {
        name: directive_sources(policy, name) for name in set(EMBEDS.values())
    }
    used = collections.defaultdict(list)
    findings = []
    for path in sorted(public.rglob("*.html")):
        rel = path.relative_to(public).as_posix()
        scan = ScriptScan()
        scan.feed(path.read_text(encoding="utf-8"))
        scan.close()
        findings += [f"{rel}: {finding}" for finding in scan.findings]
        findings += [
            f"{rel}: <script src={src}> is from a host or scheme that script-src does not name"
            for src in scan.loaded
            if not allowed(src, sources)
        ]
        findings += [
            f"{rel}: <{tag} {name}={src}> is from a host or scheme that {directive} does not name"
            for tag, name, src, directive in scan.embeds
            if not allowed(src, embed_sources[directive])
        ]
        for body in scan.inline:
            if body:
                used[digest(body)].append(rel)
    listed = {token for token in sources if token.startswith("'sha256-")}
    for token, pages in sorted(used.items()):
        if token not in listed:
            findings.append(
                f"{pages[0]}: inline script {token} is not in script-src, on {len(pages)} page(s)"
            )
    findings += [
        f"script-src lists {token}, which no inline script matches"
        for token in sorted(listed - used.keys())
    ]
    print(
        f"csp: {len(used)} distinct inline scripts, {len(listed)} hashes in script-src"
    )
    return findings


def load_policy(headers, caddyfile):
    """The blog's policy, or a refusal naming why it cannot be checked."""
    policy = blog_policy(headers.read_text(encoding="utf-8"))
    if policy is None:
        return None, f"{headers.name} holds no {CSP} for the blog"
    if f'{CSP} "{policy}"' not in caddyfile.read_text(encoding="utf-8"):
        return (
            None,
            f"{caddyfile.name} does not send the blog {CSP} {headers.name} holds",
        )
    return policy, None


def main(argv=None):
    parser = argparse.ArgumentParser(description=(__doc__ or "").partition("\n")[0])
    parser.add_argument(
        "public", type=pathlib.Path, help="the built site, as hugo wrote it"
    )
    args = parser.parse_args(argv)
    if not args.public.is_dir():
        sys.exit(f"FAIL: {args.public} is not a directory - run hugo first")
    policy, refusal = load_policy(HEADERS, CADDYFILE)
    if policy is None:
        sys.exit(f"FAIL: {refusal}")

    findings = check(args.public, policy)
    if not findings:
        print("PASS - the blog's policy allows every script and embed the site loads")
        return 0
    print(f"FAIL csp: {len(findings)} problem{'' if len(findings) == 1 else 's'}")
    for item in findings[:20]:
        print(f"  {item}")
    if len(findings) > 20:
        print(f"  ... and {len(findings) - 20} more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
