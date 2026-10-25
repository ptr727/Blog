#!/usr/bin/env python3
"""Verify that each site's Content-Security-Policy allows every fetch its pages make, and names no other host.

Each site's policy is read from `checks/security-headers.txt`, and `deploy/Caddyfile`, which
ships, must send the same value. The blog is the built site, and the family site is its tree in
`sites/viljoen.family/`, which ships as committed. Every page and stylesheet of each is read
against its own site's policy. The browser's fallbacks apply: a directive the policy leaves out
reads as `default-src`, and a frame reads `child-src` first.

Every inline script must carry a hash the policy lists, and every hash the policy lists must
match an inline script. A Hugo or theme update that changes a script's bytes then fails here
rather than in a reader's browser. An inline event handler or a `javascript:` URL fails outright,
since a hash allows neither without `'unsafe-hashes'`, which neither policy carries. A script
whose type the browser runs is checked, an import map and a speculation rules block included.
Any other type is a data block that never runs, and the browser never checks an empty script,
so neither needs a hash.

Every other fetch must come from the site itself or from a scheme its directive names. That
covers scripts, frames, media, objects, images and their `srcset` candidates, posters, SVG
images, and each `<link>` that loads something. It covers CSS too, in a stylesheet, a `<style>`
block, or a `style` attribute. There `@import` loads under `style-src`, a `url()` inside
`@font-face` under `font-src`, and any other `url()` under `img-src`. A preconnect or a DNS
prefetch reaches a host without any directive governing it, so it is held to `default-src`.
An absolute URL on the site's own origin, read from its home page's canonical link, is the
site itself. An `about:` URL and a fragment fetch nothing, so no directive applies.

A policy naming a host fails, as does one naming a network scheme such as `https:`, which allows
every host. Every resource is then served from the site itself, and a change that loads one from
elsewhere fails the release build. A scheme such as `data:` names no host and stays allowed
where a directive lists it.
"""

import argparse
import base64
import collections
import hashlib
import importlib.util
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

CHECKS = pathlib.Path(__file__).resolve().parent
HEADERS = CHECKS / "security-headers.txt"
CADDYFILE = CHECKS.parent / "deploy" / "Caddyfile"
FAMILY = CHECKS.parent / "sites" / "viljoen.family"
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


def load_sibling(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def site_policy(headers_text, site):
    """A site's policy as security-headers.txt holds it, or None where the site sends none."""
    for line in headers_text.splitlines():
        name, _, header = line.partition("\t")
        field, _, value = header.partition(": ")
        if name == site and field == CSP:
            return value
    return None


FALLBACKS = {
    "default-src": ("default-src",),
    "script-src": ("script-src", "default-src"),
    "frame-src": ("frame-src", "child-src", "default-src"),
    "media-src": ("media-src", "default-src"),
    "object-src": ("object-src", "default-src"),
    "img-src": ("img-src", "default-src"),
    "style-src": ("style-src", "default-src"),
    "font-src": ("font-src", "default-src"),
    "manifest-src": ("manifest-src", "default-src"),
}

FETCHES = {
    ("iframe", "src"): "frame-src",
    ("frame", "src"): "frame-src",
    ("audio", "src"): "media-src",
    ("video", "src"): "media-src",
    ("source", "src"): "media-src",
    ("track", "src"): "media-src",
    ("embed", "src"): "object-src",
    ("object", "data"): "object-src",
    ("img", "src"): "img-src",
    ("input", "src"): "img-src",
    ("video", "poster"): "img-src",
    ("image", "href"): "img-src",
    ("image", "xlink:href"): "img-src",
}

SRCSETS = {("img", "srcset"), ("source", "srcset")}

LINK_RELS = {
    "stylesheet": "style-src",
    "icon": "img-src",
    "apple-touch-icon": "img-src",
    "mask-icon": "img-src",
    "manifest": "manifest-src",
    "modulepreload": "script-src",
    "prefetch": "default-src",
    "preconnect": "default-src",
    "dns-prefetch": "default-src",
}

PRELOAD_AS = {
    "font": "font-src",
    "image": "img-src",
    "script": "script-src",
    "style": "style-src",
    "audio": "media-src",
    "video": "media-src",
    "track": "media-src",
}

NETWORK_SCHEMES = {"http", "https", "ws", "wss"}

COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
IMPORT = re.compile(
    r"""@import\s+(?:url\(\s*)?(?:"([^"]*)"|'([^']*)'|([^\s"');]+))""", re.IGNORECASE
)
FONT_FACE = re.compile(r"@font-face\s*\{[^}]*\}", re.IGNORECASE)
URL = re.compile(r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^\s"')]*))\s*\)""", re.IGNORECASE)


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


def named_hosts(policy):
    """Each directive's sources that allow a load from another host, as (directive, source)."""
    hosts = []
    for part in policy.split(";"):
        tokens = part.split()
        for token in tokens[1:]:
            scheme = token[:-1].lower() if token.endswith(":") else None
            if not token.startswith("'") and (
                scheme is None or scheme in NETWORK_SCHEMES
            ):
                hosts.append((tokens[0], token))
    return hosts


def digest(body):
    return (
        "'sha256-"
        + base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
        + "'"
    )


def first(match):
    return next(group for group in match.groups() if group is not None)


def css_fetches(text):
    """Each fetch a stylesheet makes, as (directive, url), in the order the text gives them."""
    text = COMMENT.sub("", text)
    found = [("style-src", first(m)) for m in IMPORT.finditer(text)]
    text = IMPORT.sub("", text)
    for face in FONT_FACE.findall(text):
        found += [("font-src", first(m)) for m in URL.finditer(face)]
    text = FONT_FACE.sub("", text)
    found += [("img-src", first(m)) for m in URL.finditer(text)]
    return found


def srcset_urls(value):
    return [candidate.split()[0] for candidate in value.split(",") if candidate.split()]


def link_fetch(attr):
    """The directive a `<link>` loads under, or None where it loads nothing."""
    rels = (attr.get("rel") or "").lower().split()
    if "preload" in rels:
        return PRELOAD_AS.get((attr.get("as") or "").strip().lower(), "default-src")
    for rel in rels:
        if rel in LINK_RELS:
            return LINK_RELS[rel]
    return None


class PageScan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.inline = []
        self.fetches = []
        self.findings = []
        self.body = None
        self.style = None

    def fetch(self, label, url, directive):
        self.fetches.append((label, url, directive))

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            url = (value or "").strip()
            if name.startswith("on"):
                self.findings.append(f"<{tag} {name}> is an inline event handler")
            elif name in ("href", "src", "action") and url.lower().startswith(
                "javascript:"
            ):
                self.findings.append(f"<{tag} {name}> is a javascript: URL")
            elif (tag, name) in FETCHES and url:
                self.fetch(f"<{tag} {name}={url}>", url, FETCHES[tag, name])
            elif (tag, name) in SRCSETS:
                for each in srcset_urls(url):
                    self.fetch(f"<{tag} {name}> candidate {each}", each, "img-src")
            elif name == "style":
                for directive, each in css_fetches(url):
                    self.fetch(f"<{tag} style> url({each})", each, directive)
        attr = dict(attrs)
        if tag == "link":
            directive = link_fetch(attr)
            href = (attr.get("href") or "").strip()
            if directive and href:
                self.fetch(f"<link rel={attr.get('rel')} href={href}>", href, directive)
        elif tag == "style":
            self.style = []
        elif tag == "script":
            self.script(attr)

    def script(self, attr):
        if (attr.get("type") or "").strip().lower() not in SCRIPT_TYPES:
            return
        if "src" not in attr:
            self.body = []
            return
        src = (attr["src"] or "").strip()
        if not src.lower().startswith("javascript:"):
            self.fetch(f"<script src={src}>", src, "script-src")

    def handle_data(self, data):
        if self.body is not None:
            self.body.append(data)
        if self.style is not None:
            self.style.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.body is not None:
            self.inline.append("".join(self.body))
            self.body = None
        elif tag == "style" and self.style is not None:
            for directive, url in css_fetches("".join(self.style)):
                self.fetch(f"<style> url({url})", url, directive)
            self.style = None


def allowed(src, sources, origin):
    parts = urlsplit(src if not src.startswith("//") else "https:" + src)
    if parts.netloc:
        own = f"{parts.scheme}://{parts.netloc}"
        return own in sources or (own == origin and "'self'" in sources)
    if parts.scheme:
        return f"{parts.scheme}:" in sources
    return "'self'" in sources


def fetches_nothing(url):
    return not url or url.startswith("#") or url.lower().startswith("about:")


def check(root, policy, origin):
    """Every finding for one site's tree against its policy, each prefixed with its file."""
    sources = {name: directive_sources(policy, name) for name in FALLBACKS}
    used = collections.defaultdict(list)
    findings = [
        f"the policy names {source} under {directive}, which allows another host"
        for directive, source in named_hosts(policy)
    ]
    for path in sorted([*root.rglob("*.html"), *root.rglob("*.css")]):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".css":
            fetches = [(f"url({url})", url, d) for d, url in css_fetches(text)]
        else:
            scan = PageScan()
            scan.feed(text)
            scan.close()
            findings += [f"{rel}: {finding}" for finding in scan.findings]
            fetches = scan.fetches
            for body in scan.inline:
                if body:
                    used[digest(body)].append(rel)
        findings += [
            f"{rel}: {label} is from a host or scheme that {directive} does not name"
            for label, url, directive in fetches
            if not fetches_nothing(url) and not allowed(url, sources[directive], origin)
        ]
    listed = {token for token in sources["script-src"] if token.startswith("'sha256-")}
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


def load_policy(headers, caddyfile, site):
    """A site's policy, or a refusal naming why it cannot be checked."""
    policy = site_policy(headers.read_text(encoding="utf-8"), site)
    if policy is None:
        return None, f"{headers.name} holds no {CSP} for the {site} site"
    if f'{CSP} "{policy}"' not in caddyfile.read_text(encoding="utf-8"):
        return (
            None,
            f"{caddyfile.name} does not send the {site} {CSP} {headers.name} holds",
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
    site_origin = load_sibling(
        "check_url_parity", CHECKS / "check-url-parity.py"
    ).site_origin

    findings = []
    for site, root in (("blog", args.public), ("family", FAMILY)):
        policy, refusal = load_policy(HEADERS, CADDYFILE, site)
        if policy is None:
            sys.exit(f"FAIL: {refusal}")
        print(f"==> {site}")
        findings += [
            f"{site}: {item}" for item in check(root, policy, site_origin(root))
        ]
    if not findings:
        print(
            "PASS - each site's policy allows every fetch its pages make, and names no other host"
        )
        return 0
    print(f"FAIL csp: {len(findings)} problem{'' if len(findings) == 1 else 's'}")
    for item in findings[:20]:
        print(f"  {item}")
    if len(findings) > 20:
        print(f"  ... and {len(findings) - 20} more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
