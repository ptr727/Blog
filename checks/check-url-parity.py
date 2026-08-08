#!/usr/bin/env python3
"""Verify the built site against the URL contract.

Checks that every URL which must render exists, that every legacy media URL resolves, that
every local asset reference points at a file, and that the number of carried media files
linked from no page still equals its recorded baseline. Redirects need a running server and
are checked by check-live-urls.sh instead.
"""

import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote

# A truncated list would make every assertion below it pass vacuously while the gate stays green.
# The floors sit under the known-good counts, so a list may grow but not collapse.
FLOORS = {
    "golden-urls.txt": 320,
    "redirect-urls.txt": 900,
    "golden-media-legacy.txt": 770,
}

CHECKS = pathlib.Path(__file__).resolve().parent

# Media carried by the import that no built page links to.
# The other two media checks run outward from a reference and cannot see these: a legacy URL
# resolving proves an inbound link still lands, and a reference resolving proves it names a real
# file. Neither asks whether anything points at a given file, so an image the conversion dropped
# from a page stays reachable by URL, invisible on the site, and green in both directions.
# It opened at 120, of which 17 were conversion losses restored from the captured live site and 5
# were never orphans at all, being referenced only by an absolute URL this check could not read.
# The 98 that remain are adjudicated rather than unknown: 97 were uploaded to the old platform's
# media library and never placed on any published page, and one is that platform's site icon,
# superseded by the favicon set at the static root. Nothing here is a conversion loss, and no image
# the old site served from its own uploads went unimported. checks/README.md carries the method.
# The count is exact rather than a bound, so whatever lowers it lowers this in the same change and
# slack can never accumulate for a later regression to hide in.
ORPHANED_MEDIA = 98

# Every check above returns a list, and the shared summary called all of them "missing". That is
# what a URL that did not build is, and it is not what a stray node inside a gallery is: those are
# present, which is the whole complaint. The default stays "missing" so a check added later reads
# the way the older ones do unless it says otherwise.
FAILURE_NOUN = {"gallery": "stray nodes", "robots": "problems"}


def load(name):
    lines = [ln.strip() for ln in (CHECKS / name).read_text().splitlines()]
    urls = [ln for ln in lines if ln]
    floor = FLOORS[name]
    if len(urls) < floor:
        sys.exit(f"FAIL {name}: {len(urls)} URLs, expected at least {floor} - the list has been truncated")
    return urls


def url_to_file(public, url):
    """Map a site URL to the file Hugo builds for it."""
    path = url.strip("/")
    return public / path / "index.html" if path else public / "index.html"


def check_render(public):
    golden = load("golden-urls.txt")
    missing = [u for u in golden if not url_to_file(public, u).is_file()]
    built = {
        "/" + str(p.parent.relative_to(public)).replace("\\", "/").strip(".") + "/"
        for p in public.rglob("index.html")
    }
    built = {u if u.startswith("/") else "/" + u for u in built}
    extra = sorted(built - set(golden))
    print(f"render : {len(golden) - len(missing)}/{len(golden)} golden URLs built")
    if extra:
        print(f"         {len(extra)} additional URLs built (not a failure)")
    return missing


def check_media(public):
    """Check that every legacy image URL resolves under the renamed media tree.

    The render gate covers pages only, so nothing else protects the image URL surface.
    """
    legacy = load("golden-media-legacy.txt")
    missing = []
    for url in legacy:
        rewritten = re.sub(r"^/wp-content/uploads/", "/media/", url)
        if rewritten == url:
            missing.append(f"{url} (does not match the @uploads rewrite prefix)")
        elif not (public / rewritten.lstrip("/")).is_file():
            missing.append(url)
    print(f"media  : {len(legacy) - len(missing)}/{len(legacy)} legacy image URLs resolve after the @uploads rewrite")
    return missing


def check_robots(public):
    """Check that robots.txt exists and advertises this build's own sitemap.

    Four failures, one gate: the file absent, no Sitemap: line, a line naming another origin, and a
    line advertising a sitemap that was not built. Hugo emits no robots.txt unless enableRobotsTXT
    is set, which is why this site served none until that flag was turned on, and the file's only
    load-bearing line points at the sitemap a crawler is otherwise unlikely to find, being told
    rather than guessing.

    Every contract list is path-only and check-live-urls.sh joins whatever base URL it is handed, so
    this is the only place the gate *compares* an origin rather than joining one. Other absolute
    URLs are read here - the home page's canonical link, and absolute asset references - but they
    are read to resolve a reference rather than to check a host against another.

    What the comparison proves is internal consistency: the advertised origin matches the one the
    canonical link carries. Both come from baseURL, so this cannot tell that baseURL was the wrong
    value for the environment being deployed to - nothing in the artifact can, which is why that
    check belongs on the side that knows which host it is serving. It does catch an origin that was
    written rather than derived, a static robots.txt shadowing the template being the way that
    happens, and it catches a sitemap advertised but not built.
    """
    robots = public / "robots.txt"
    if not robots.is_file():
        # Naming one cause as the cause sends a reader to check a setting that is already correct.
        # enableRobotsTXT is the likely one and a partial build or the wrong output directory reach
        # the same state, which is the same reason the orphan messages name both of their causes.
        print("robots : missing")
        return [
            f"{robots} does not exist - likely enableRobotsTXT is unset in hugo.yaml, "
            "though a partial build or the wrong output directory look identical here"
        ]

    origin = site_origin(public)
    # errors="replace" rather than strict, or invalid UTF-8 raises out of the whole parity run and a
    # gate that exists to report a bad robots.txt stack-traces on one instead. A committed
    # static/robots.txt is the file most likely to carry it, and it is the case this check is for.
    text = robots.read_text(encoding="utf-8", errors="replace")
    advertised = re.findall(r"(?mi)^\s*Sitemap:\s*(\S+)\s*$", text)
    if not advertised:
        print("robots : built, no Sitemap line")
        return ["robots.txt carries no Sitemap: line - a crawler will not find the sitemap unaided"]

    wrong = [u for u in advertised if not u.startswith(origin + "/")]
    if wrong:
        print(f"robots : built, {len(wrong)} Sitemap line(s) naming another origin")
        return [f"{u} (this build's origin is {origin})" for u in wrong]

    # The summary is printed after the last assertion rather than before it, or the missing-sitemap
    # case reads as a pass on the line above its own failure. Every branch here prints exactly once.
    unbuilt = [u for u in advertised if not (public / u[len(origin) + 1 :]).is_file()]
    if unbuilt:
        print(f"robots : built, {len(unbuilt)} advertised sitemap(s) not built")
        return [f"{u} (advertised, but {u[len(origin) + 1:]} was not built)" for u in unbuilt]

    # Named rather than counted, since there is one today and the line is the thing being checked.
    print(f"robots : built, advertising {advertised[0]}")
    return []


def site_origin(public):
    """The site's own scheme and host, read from the artifact rather than assumed.

    Staging and production build with different base URLs, so a hardcoded host would check
    one environment's output against another's and silently match nothing.
    """
    home = public / "index.html"
    if not home.is_file():
        sys.exit(f"FAIL: {home} is missing - run hugo first")
    text = home.read_text(encoding="utf-8", errors="ignore")
    found = re.search(r'rel=["\']?canonical["\']?\s+href=["\']?(https?://[^/"\'>\s]+)', text)
    if not found:
        # Without the origin, every absolute reference reads as external and the orphan count
        # inflates by exactly the pages that use one. Guessing would be worse than stopping.
        sys.exit("FAIL: no canonical link on the home page - cannot determine the site's own origin")
    return found.group(1)


def collect_refs(public):
    """Every local asset reference in the built pages.

    Read once and shared, since the assets and orphans checks are the same reference set
    read in opposite directions.
    """
    # Minification drops the quotes around an attribute value that does not need them.
    # Matching only the quoted form checks a fraction of the references and calls it a pass.
    quoted = re.compile(r'(?:src|href|srcset)="(/(?:media|external)/[^"]+)"')
    bare = re.compile(r"(?:src|href|srcset)=(/(?:media|external)/[^\s\"'>]+)")
    # Hugo writes an absolute URL wherever a template resolves one against the base, which the
    # entry-cover images on every list page do. Read as external, those files look linked from
    # nowhere while being displayed, and a broken one is never checked at all.
    absolute = re.compile(re.escape(site_origin(public)) + r'(/(?:media|external)/[^\s"\'>]+)')
    refs = set()
    for page in public.rglob("*.html"):
        text = page.read_text(encoding="utf-8", errors="ignore")
        refs.update(quoted.findall(text))
        refs.update(bare.findall(text))
        refs.update(absolute.findall(text))
    return refs


def ref_to_path(ref):
    """Map a reference to the path under the built site it names."""
    # Imported references carry resize parameters a static file server ignores.
    # Some also escape an underscore, which a server decodes before looking up the file.
    return unquote(ref.split("?", 1)[0].split("#", 1)[0]).lstrip("/")


def check_assets(public, refs):
    """Check that every local asset a built page references exists on disk.

    Catches a media file renamed, dropped, or never localized.
    """
    missing = [ref for ref in sorted(refs) if not (public / ref_to_path(ref)).is_file()]
    print(f"assets : {len(refs) - len(missing)}/{len(refs)} local asset references resolve")
    return missing


def check_orphans(public, refs):
    """Check that every carried media file is linked from some built page.

    The reverse of the assets check, and the only one that can see an image the conversion
    dropped from a page: it stays on disk and reachable by URL, so nothing else objects.
    """
    linked = {ref_to_path(ref) for ref in refs}
    carried, orphaned = 0, []
    for tree in ("media", "external"):
        root = public / tree
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            carried += 1
            # `linked` holds URL paths, which are always forward-slashed, so a native separator
            # here would match nothing and report every carried file as an orphan. check_render
            # normalizes for the same reason.
            rel = str(path.relative_to(public)).replace("\\", "/")
            if rel not in linked:
                orphaned.append(rel)
    orphaned.sort()
    # No media at all is a broken build, not progress. Left to the comparison below it reads as
    # zero orphans, which is fewer than the baseline, and the advice would be to lower
    # ORPHANED_MEDIA to 0 - a gate talking the reader into switching it off.
    if carried == 0:
        print("orphans: no media files in the built site - the output is incomplete or mislocated")
        return ["public/media and public/external are both absent or empty"]
    print(f"orphans: {len(orphaned)} of {carried} carried media files are linked from no page")
    if len(orphaned) == ORPHANED_MEDIA:
        return []
    # The explanation is printed rather than returned, so the caller's count stays the orphan
    # count. A diagnostic carried in the failure list would make the reported total one too many.
    # A count is all this can observe, and two causes reach each direction. Naming one of them
    # would send a reader looking for a page that never changed.
    if len(orphaned) > ORPHANED_MEDIA:
        print(f"         expected {ORPHANED_MEDIA} - a page stopped linking media, or unlinked media was added")
        return orphaned
    print(
        f"         expected {ORPHANED_MEDIA} - media was linked from a page, or orphaned files were "
        f"removed; lower ORPHANED_MEDIA to {len(orphaned)} in this change rather than leaving the slack"
    )
    return orphaned


class GalleryScan(HTMLParser):
    """Collect anything inside a gallery container that is not one of its permitted children.

    A gallery is a flex row of figures, so its column widths are set by `.gallery-cols-N figure`.
    Anything else landing in there is not laid out by that rule and is rendered as one more item
    in the row.

    This reads the built HTML, so it sees fewer shapes than the markdown has, and deliberately:
    three source patterns reached it, a set caption written as text trailing a figure shortcode,
    a bare markdown image, and a linked one, and they arrive here as a bare text node, a `<p>`
    wrapping images, and an `<a>` with a `<br>` beside it. Enumerating source patterns would
    make this a list to extend every time the conversion surprises us again. Naming the one
    invariant instead, that a gallery holds figures and its own caption, covers the shape nobody
    has thought of yet, which is how the third of the three was found after the first two.
    """

    # A void element never closes, so counting it as an open tag desynchronizes the depth for the
    # rest of the document and every later gallery reads as containing whatever follows it.
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}
    ALLOWED = {"figure", "figcaption"}

    # There is deliberately no handle_startendtag override. HTMLParser's own implementation
    # forwards a self-closing tag to handle_starttag and then handle_endtag, so `<br/>`, `<br />`
    # and `<img/>` are already reported and already leave the depth balanced. Adding an override
    # to "support" them is what would break it, by counting a pair the base class already splits.
    # Verified on those three spellings and on a self-closing non-void `<figure/>`.

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.findings = []
        self.saw_gallery = False
        # None outside a gallery; otherwise the number of elements open within the current one,
        # so zero means the parser is looking at a direct child.
        self.depth = None

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if self.depth is None:
            if tag == "figure" and "gallery" in classes:
                self.depth = 0
                self.saw_gallery = True
            return
        if self.depth == 0 and tag not in self.ALLOWED:
            self.findings.append(f"<{tag}> as a direct child")
        if tag not in self.VOID:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.depth is None or tag in self.VOID:
            return
        if self.depth == 0:
            # The gallery's own closing tag.
            self.depth = None
        else:
            self.depth -= 1

    def handle_data(self, data):
        # Whitespace between elements is just the template's formatting.
        if self.depth == 0 and data.strip():
            self.findings.append(f"bare text {data.strip()[:60]!r}")


def check_galleries(public):
    """Check that every gallery holds only figures and its own caption.

    Neither the assets nor the orphans check can see this: both ask whether a reference resolves
    or is reached, and content misplaced inside a gallery resolves and is reached exactly as it
    would anywhere else. The defect is purely one of structure, so nothing that reasons about
    URLs can observe it, which is why it survived the conversion and every gate since.
    """
    findings, pages = [], 0
    for path in sorted(public.rglob("index.html")):
        html = path.read_text(encoding="utf-8", errors="replace")
        # Cheap reject first, since parsing every built page costs far more than one substring
        # test and galleries appear on a handful of them. The test is the bare word rather than
        # `class="gallery`, because minification drops the quotes around a value that does not
        # need them and says nothing about class order, so the quoted form skips a page whose
        # markup is merely spelled differently and the gate passes vacuously. This form cannot:
        # the parser below requires the class token `gallery`, so a page it would find always
        # contains this string. Matching a page that only mentions the word costs one parse.
        if "gallery" not in html:
            continue
        scan = GalleryScan()
        scan.feed(html)
        # Counted from what the parser actually found rather than from the reject above, so the
        # reported number stays "pages carrying a gallery" and not "pages the word appears on".
        if not scan.saw_gallery:
            continue
        pages += 1
        rel = str(path.relative_to(public)).replace("\\", "/")
        findings += [f"{rel}: {finding}" for finding in scan.findings]
    print(f"gallery: {pages} pages with galleries, {len(findings)} stray nodes inside one")
    return findings


def main(argv):
    if len(argv) != 2:
        sys.exit(f"usage: {argv[0]} <public-dir>")
    public = pathlib.Path(argv[1])
    if not public.is_dir():
        sys.exit(f"FAIL: {public} is not a directory - run hugo first")

    refs = collect_refs(public)
    failures = []
    for label, found in (
        ("render", check_render(public)),
        ("media", check_media(public)),
        ("assets", check_assets(public, refs)),
        ("orphans", check_orphans(public, refs)),
        ("gallery", check_galleries(public)),
        ("robots", check_robots(public)),
    ):
        if found:
            failures.append((label, found))

    if not failures:
        print("\nPASS - the built site honors the URL contract")
        return 0

    print()
    for label, found in failures:
        print(f"FAIL {label}: {len(found)} {FAILURE_NOUN.get(label, 'missing')}")
        for item in found[:20]:
            print(f"  {item}")
        if len(found) > 20:
            print(f"  ... and {len(found) - 20} more")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
