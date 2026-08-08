# URL Parity Gate

The URL contract this site must honor. `golden-urls.txt` and `redirect-urls.txt` are ground truth: a URL is listed because a live request confirmed the site answers for it, never because a tool predicted it.

## Why this exists

A static-site build silently drops URLs. Nothing fails, the site looks right, and the loss surfaces months later as 404s in a log nobody reads. These lists turn that into a CI failure.

The contract is enforced by two gates, because one cannot cover both halves:

| Gate | Proves | Runs |
| --- | --- | --- |
| [`check-url-parity.py`](./check-url-parity.py) | Every URL that must render exists as a built page, every legacy image URL resolves, every local asset reference points at a real file, and the count of carried media linked from no page still equals its recorded baseline | Against `public/`, in CI and before any release is installed |
| [`check-live-urls.sh`](./check-live-urls.sh) | Every redirect resolves, and its destination answers | Against a running server, which is the only thing that exercises a redirect |

## The two lists

**`golden-urls.txt`, 328 URLs Hugo must render.** Missing any one is a hard CI failure.

**Every count on this page describes the two lists, not the site.** The lists are the legacy contract, closed by the migration, so a new post adds a URL the parity gate reports as `additional URLs built (not a failure)` and changes nothing here. A count moves only when a log review finds a legacy address the crawl missed, which is a deliberate append.

| Shape | Count | Note |
| --- | --- | --- |
| Tag archives | 180 | The site serves `/tag/`, and **Hugo defaults to `/tags/`** |
| Posts | 108 | `/YYYY/MM/DD/slug/` |
| Category archives | 12 | The site serves `/category/`, and **Hugo defaults to `/categories/`** |
| Category pagination | 11 | `/category/<term>/page/N/` |
| Home pagination | 10 | `/page/N/` |
| Tag pagination | 4 | `/tag/<term>/page/N/` |
| Pages | 2 | `/about/`, `/viljoen-family/` |
| Home | 1 | |

The 180 tag archives are exactly the tags the migrated posts carry. Three further terms answer with an empty page and are redirects rather than renders: `brultech` and `phyn`, which no published post uses, and `review`, an empty tag that is also a 12-post category. Hugo generates a term page only where posts exist, which is why the render list is 180 tags rather than 183.

**`redirect-urls.txt`, 917 URLs that must resolve but need not render.** These have no Hugo equivalent. Reproducing them would be absurd, and 404ing them discards real inbound links.

| Shape | Count | Disposition |
| --- | --- | --- |
| Attachment pages, nested | 216 | Redirect to the parent post |
| Per-term comment feeds | 192 | Redirect to the term archive |
| `?p=<id>` shortlinks | 110 | Redirect to the permalink, via `p-ids.map` |
| Attachment pages, root level | 107 | Redirect to the parent post, via `slugs.map` |
| Per-post comment feeds | 107 | Redirect to the parent post |
| Date archives | 83 | Redirect to `/all/`, since **Hugo has no built-in year or month archive**. The matcher accepts any date, including dates absent from the list |
| Blogger permalinks | 59 | Redirect to the current post, via `blogger.map` |
| Blogger monthly archives | 21 | Redirect to `/all/` |
| Author archive and pagination | 12 | Redirect to `/`, a single-author blog duplicating home |
| Blogger feed | 2 | Redirect to `/feed.xml` |
| Blogger static pages | 2 | `/p/<slug>.html` to `/<slug>/` |
| Empty term archives | 3 | `brultech`, `phyn`, `review`, as above |
| Site and section feeds | 3 | `/feed/`, `/about/feed/`, `/comments/feed/` |

An **attachment page** is the page the old platform generated per uploaded image, served at both `/YYYY/MM/DD/post/attachment/` and a bare `/attachment/`. That makes a one-segment URL ambiguous with a real page, and the sitemap resolves it: the sitemap lists exactly the posts and pages, so a one-segment URL absent from it is an attachment page. The images themselves keep their `wp-content/uploads/` paths and are covered separately by `golden-media-legacy.txt`.

## Legacy URL shapes worth knowing

**`/search/label/<Label>` is not a redirect.** The old platform answers it with a generic search page that returns 200 for a label that never existed, so the class is a soft 404 that looks alive. It is handled by choice rather than by preservation: `labels.map` sends each label to its term archive, and anything unmatched falls through to `/all/`.

The other property worth knowing belongs to the generator rather than to the contract, so it is in [`capture/README.md`](../capture/README.md): `blogger.map` holds more entries than there are Blogger-era posts, because that platform served a long title at a truncated address and both forms still answer.

## Maintaining the contract

**Adding a URL.** Real traffic finds what the lists missed. When a server log shows a 404 for an address that should work, append it to the appropriate list and add a redirect rule or map entry to cover it. The lists are append-only, per Directionality below.

**Regenerating the maps.** The generator is [`capture/build-redirects.py`](../capture/build-redirects.py), and it lives there rather than here because it generates rather than gates. [`capture/README.md`](../capture/README.md) covers how to run it and how it chooses its input.

**Checking a count.** Every count above is derivable from the files, so check rather than trust:

```sh
wc -l checks/golden-urls.txt checks/redirect-urls.txt checks/golden-media-legacy.txt checks/golden-media-live.txt
```

## `golden-media-live.txt`, and why the media set needs a second list

`golden-media-legacy.txt` proves the **set**, at build time, against files on disk. That cannot prove the files reached the server or that the server can read them, and the live check requested pages and redirects and never one image, so a media tree lost between a passing build and the server was caught by neither gate. `golden-media-live.txt` closes that, and it is fetched by `check-live-urls.sh` against a running server.

**It is a handful rather than exhaustive, deliberately.** The set is already proven, so this is a delivery check, and its entries are chosen to cover both trees and a spread of years because the trees arrive by different routes and a partial transfer is unlikely to land evenly.

| Entry shape | Proves |
| --- | --- |
| `/media/` paths | the imported uploads tree arrives and is served |
| `/external/` paths | the tree of media localized from other hosts arrives too |
| `/wp-content/uploads/` paths | the `@uploads` rule still lands on the image, which nothing else exercises against a running server |

**Three assertions rather than one, because each catches a different loss.** A file missing from the transfer answers 404. A file whose mode went wrong answers 403, which is the case this exists for. A file truncated to nothing still answers 200, so the byte count is asserted. And a server that answers an error page for a missing asset answers 200 with `text/html`, so the content type is asserted as well. The check follows one redirect by hand rather than passing `-L` to curl, for the reason `check_redirect` does: `-L` would carry the auth-gate credential to wherever the rule points.

**The mode case is why this is not theoretical.** A hard-linked file carries its inode's mode, so a media file that acquires a bad one rides the chain into every later release, present and correctly named and unreadable to the server. A build-time `is_file()` on the runner cannot see it, and neither can a check that never requests an image.

## Directionality

The parity check fails on a **missing** URL and only notes an **extra** one. New posts, new tags, and deeper pagination legitimately add URLs, and nothing legitimately removes a URL the site has served. That asymmetry is what makes the lists append-only, which in turn is what makes the length-floor assertion in `check-live-urls.sh` sound: without it a truncated list would make every assertion below it pass vacuously.

Media is the one surface checked in **both** directions, and it has to be, because each direction is blind to the other's failure. Outward from a reference, the legacy list proves an inbound link still lands and the asset check proves a reference names a real file. Neither asks whether anything points at a given file, so an image dropped from a page during the conversion stays on disk, stays reachable at its own URL, and reports green in both directions while appearing nowhere on the site. The orphan check reads inward from the file and is the only one that sees it.

Its constant is an exact count rather than a bound. A ceiling would let a drop leave slack behind for a later regression to hide in, so whatever lowers the count lowers the constant in the same change, and the check names the new number when it drops.

A count is all the check can observe, and two causes reach each direction: it rises when a page stops linking media **or** when unlinked media is added, and it falls when media is linked from a page **or** when orphaned files are deleted. The messages name both, because naming one would send a reader looking for a page that never changed.

**Both directions read absolute references as well as relative ones.** Hugo writes an absolute URL wherever a template resolves one against the base, which the entry-cover image on every list page does. Reading only rooted paths made those files look linked from nowhere while they were being displayed, and left a broken one unchecked in the other direction. The origin is read from the home page's canonical link rather than assumed, since staging and production build with different base URLs and a hardcoded host would check one environment's output against another's. No canonical link is a hard failure, because a guessed origin inflates the orphan count by exactly the pages that use one.

## The robots check, and the one thing no gate here can do

Hugo emits no `robots.txt` unless `enableRobotsTXT` is set, so this site served none until the flag was turned on, and the old platform serves one. The `Sitemap:` line is load-bearing in a way the crawl rules are not: across the interim hostname's first full day of traffic, every request for `sitemap.xml` came from `curl` and none from a crawler, because a crawler is told where a sitemap is rather than guessing it. Four failures are gated — the file absent, no `Sitemap:` line, a line naming another origin, and a line advertising a sitemap that was not built — and all four were demonstrated failing before the check was trusted.

**The `Sitemap:` line is the one place this gate compares an origin rather than joining one.** Every list is path-only and `check-live-urls.sh` joins whatever base URL it is handed, which is deliberate and is what lets one contract cover four environments. Other absolute URLs are read here, the home page's canonical link and the absolute asset references described above among them, but they are read to resolve a reference rather than to check one host against another.

**What that comparison proves is internal consistency, and it is worth being exact about the limit.** The advertised origin must match the one read from the home page's canonical link, and both are derived from the same `baseURL`, so they agree whenever the build is coherent — including when `baseURL` held the wrong value for the environment being deployed to. **Nothing inside the artifact can detect that**, which is why the check belongs on the side that knows which host it is serving: the VPS side reads the origin out of the deployed `sitemap.xml`, `og:url` and `feed.xml` and reports the counts either way. A build baked with the wrong host still passes all 1,245 URLs here, and it passes this too.

What the comparison does catch is an origin that was **written rather than derived** — a committed `static/robots.txt` shadowing the template is the way that happens, and pasting the old platform's `.com` sitemap line into one is the specific mistake it would catch — along with a sitemap advertised but never built.

`/robots.txt/`, with a trailing slash, is a URL the old platform served and is in the redirect contract. It resolves through `slugs.map` like any other one-segment legacy URL, and the generator special-cases it to the real file rather than to the home page. `/osd.xml/` stays pointed at the home page deliberately: it was the old platform's OpenSearch description and this site emits no such file.

## The gallery check, which no direction above can reach

Every check above reasons about a URL: whether it renders, whether it resolves, whether anything points at it. Content misplaced **inside** a gallery satisfies all of that. The file exists, the reference resolves, and something links it, so the media surface is green in both directions while the page is laid out wrong. The defect is one of structure, which is why three variants of it survived the conversion and every gate since.

A gallery is a flex row whose column widths come from `.gallery-cols-N figure`. Anything in there that is not a `figure` gets no width from that rule and is rendered as one more item in the row. So the check reads the built pages and fails on any direct child of a gallery container that is not a `figure` or the gallery's own `figcaption`.

The three shapes it found, all of them conversion artifacts, and each verified against the captured live site before being changed:

| Shape in the markdown | What the old platform had |
| --- | --- |
| Caption text appended after the last `figure` shortcode's `}}` | `<figcaption class="blocks-gallery-caption">`, a caption for the **set** |
| A bare `![](…)` image | `<li class="blocks-gallery-item"><figure>` |
| A linked `[![](…)](…)` image | the same, with an `<a>` **inside** the figure |

**The first shape is why the capture is consulted rather than the markup.** A reviewer reading only the source reasonably suggests moving the text into the last figure's `caption` parameter, which is what a per-image caption would need. The capture shows all eleven were gallery-level captions, so that fix would have attributed a caption for a set of four images to whichever one happened to be last, and it would have looked correct.

The gallery shortcode therefore takes a `caption` of its own and renders the container as a `figure`, since `figcaption` is only valid as a figure's child. The theme already styles `figure > figcaption`, so a set caption needs no rule beyond a full-width flex basis to keep it off the end of the last row.

## What the orphans are

The count is not a backlog. It opened at 120 and was adjudicated against the captured live site under `blog-capture/mirror/`, which holds a crawl of the old platform including all 328 URLs the contract requires:

| | |
| --- | --- |
| 17 | conversion losses, restored. The conversion emitted five `gallery` shortcodes empty |
| 5 | never orphans, referenced only by an absolute URL the check could not read |
| 97 | uploaded to the old platform's media library and never placed on a published page |
| 1 | that platform's site icon, superseded by the favicon set at the static root |

**No image the old site served from its own uploads went unimported**, and no conversion loss remains. Anything that raises the count from here is therefore new, which is what makes the exact constant worth keeping.

Three traps in that adjudication, each of which produced a wrong answer first and each cheap to re-trip:

- **A regex cannot read nested elements.** The galleries are `wp-block-gallery` figures containing `wp-block-image` figures, and matching them by pattern reported a fictional 194-figure loss. An HTML parser gives the real number.
- **Only a surplus in the mirror is a finding.** A mirror page parsed as having *fewer* figures than the markdown means the parser missed that page's markup, never that images were lost.
- **The old platform generated an attachment page per upload, and a foreign host may also serve `/wp-content/uploads/`.** Counting attachment pages as places an image was displayed makes every unused upload look published, and matching an uploads path without checking its host attributes another site's file to this one. Both were hit here.
