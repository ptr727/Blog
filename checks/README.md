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

Two properties of the maps are non-obvious and easy to break when regenerating them.

**`blogger.map` carries 59 entries for 48 posts.** Blogger truncated an auto-generated slug at 40 characters on a whole-word boundary, so for the 11 posts with a longer slug the URL actually served, and therefore the one in search indexes and in other people's links, is the truncated form. Both forms are live redirects. A map holding only the full slug keeps the URL that never existed and drops the one that did.

**`/search/label/<Label>` is not a redirect.** The old platform answers it with a generic search page that returns 200 for a label that never existed, so the class is a soft 404 that looks alive. It is handled by choice rather than by preservation: `labels.map` sends each label to its term archive, and anything unmatched falls through to `/all/`.

## Maintaining the contract

**Adding a URL.** Real traffic finds what the lists missed. When a server log shows a 404 for an address that should work, append it to the appropriate list and add a redirect rule or map entry to cover it. The lists are append-only, per Directionality below.

**Regenerating the maps.** `build-redirects.py` rebuilds everything under `deploy/maps/` from the source export, which lives in a capture directory outside this repo and is passed as an argument. **That directory's path is `CAPTURE_ROOT` in `secrets/local.production.env`**, and `OPERATIONS.md` "Rebuilding from the Exports" records what it holds and which parts of it a person can fetch again. It is a provenance tool rather than a CI step, and it selects the export **by content**, failing unless exactly one candidate contains published posts. The capture holds both a full export and a media-only one with zero posts, and taking the wrong one yields empty maps that are indistinguishable from working ones until the redirects are live.

**Checking a count.** Every count above is derivable from the files, so check rather than trust:

```sh
wc -l checks/golden-urls.txt checks/redirect-urls.txt checks/golden-media-legacy.txt
```

## Directionality

The parity check fails on a **missing** URL and only notes an **extra** one. New posts, new tags, and deeper pagination legitimately add URLs, and nothing legitimately removes a URL the site has served. That asymmetry is what makes the lists append-only, which in turn is what makes the length-floor assertion in `check-live-urls.sh` sound: without it a truncated list would make every assertion below it pass vacuously.

Media is the one surface checked in **both** directions, and it has to be, because each direction is blind to the other's failure. Outward from a reference, the legacy list proves an inbound link still lands and the asset check proves a reference names a real file. Neither asks whether anything points at a given file, so an image dropped from a page during the conversion stays on disk, stays reachable at its own URL, and reports green in both directions while appearing nowhere on the site. The orphan check reads inward from the file and is the only one that sees it.

Its constant is an exact count rather than a bound. A ceiling would let a drop leave slack behind for a later regression to hide in, so whatever lowers the count lowers the constant in the same change, and the check names the new number when it drops.

A count is all the check can observe, and two causes reach each direction: it rises when a page stops linking media **or** when unlinked media is added, and it falls when media is linked from a page **or** when orphaned files are deleted. The messages name both, because naming one would send a reader looking for a page that never changed.

**Both directions read absolute references as well as relative ones.** Hugo writes an absolute URL wherever a template resolves one against the base, which the entry-cover image on every list page does. Reading only rooted paths made those files look linked from nowhere while they were being displayed, and left a broken one unchecked in the other direction. The origin is read from the home page's canonical link rather than assumed, since staging and production build with different base URLs and a hardcoded host would check one environment's output against another's. No canonical link is a hard failure, because a guessed origin inflates the orphan count by exactly the pages that use one.

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
