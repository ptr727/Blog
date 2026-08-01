# URL Parity Gate

The URL contract the migrated site must honor. `golden-urls.txt` and `redirect-urls.txt` are ground truth captured from the live WordPress.com site, and **every URL in both lists has been verified with a live request** - a URL is listed because the old site answered for it, not because a tool predicted it.

## Why this exists

A Hugo migration silently drops URLs. Nothing in the build fails, the site looks right, and the loss only surfaces months later as 404s in a log nobody reads. This gate turns that into a CI failure.

## How the list was built

Three sources unioned, then each candidate verified live.

| Source | Yield | Why it is not sufficient alone |
| --- | --- | --- |
| `sitemap.xml` | 111 | Lists only posts and pages. Omits every taxonomy term, archive, and paginated page - roughly 90% of the real URL set. |
| Recursive crawl (`wget --spider`) | 1,545 paths | Finds only what is linked. Misses date archives and pagination entirely, which the theme links from nowhere. |
| Derivation | 304 | Date archives and pagination computed from post dates and taxonomy post counts, at 10 posts per page. |

**A crawl cannot find an unlinked URL, and the largest classes here are unlinked.** The Blogger-era surface (below) is reachable from nothing on the current site and was found only by reasoning about the blog's history; the `?p=<id>` shortlinks likewise appear in no page. Treat "the crawl found everything" as false.

## The two lists

**`golden-urls.txt` - 328 URLs Hugo must render.** Missing any one is a hard CI failure.

| Shape | Count | Note |
| --- | --- | --- |
| Tag archives | 180 | WordPress serves `/tag/`; **Hugo defaults to `/tags/`** |
| Posts | 108 | `/YYYY/MM/DD/slug/` |
| Category archives | 12 | WordPress serves `/category/`; **Hugo defaults to `/categories/`** |
| Category pagination | 11 | `/category/<term>/page/N/` |
| Home pagination | 10 | `/page/N/` |
| Tag pagination | 4 | `/tag/<term>/page/N/` |
| Pages | 2 | `/about/`, `/viljoen-family/` |
| Home | 1 | |

The 180 tag archives are exactly the tags carried by a published post. WordPress keeps a term alive once created, so it also serves an empty 200 page for `brultech` and `phyn` (tags no published post uses) and for `review` (an empty tag that is also a 12-post category). Hugo generates a term page only where posts exist, so those three are redirects, not renders. This is why the render list is 180 tags and not the export's 183.

**`redirect-urls.txt` - 917 URLs that must resolve, but need not render.** These are WordPress-isms and Blogger-era leftovers with no Hugo equivalent; reproducing them would be absurd, and 404ing them discards real inbound links.

| Shape | Count | Disposition |
| --- | --- | --- |
| Attachment pages, nested | 216 | Redirect to the parent post |
| Per-term comment feeds | 192 | Redirect to the term archive |
| `?p=<id>` shortlinks | 110 | Redirect to the permalink, via `p-ids.map` |
| Attachment pages, root level | 107 | Redirect to the parent post, via `slugs.map` |
| Per-post comment feeds | 107 | Redirect to the parent post |
| Date archives | 83 | Redirect to `/all/` - **Hugo has no built-in year or month archive** |
| Blogger permalinks | 59 | Redirect to the current post, via `blogger.map` |
| Blogger monthly archives | 21 | Redirect to `/all/` |
| Author archive and pagination | 12 | Redirect to `/` - single-author blog, duplicates home |
| Blogger feed | 2 | Redirect to `/feed.xml` |
| Blogger static pages | 2 | `/p/<slug>.html` to `/<slug>/` |
| Empty term archives | 3 | `brultech`, `phyn`, `review` as above |
| Site and section feeds | 3 | `/feed/`, `/about/feed/`, `/comments/feed/` |

An **attachment page** is the page WordPress generates per uploaded image, served at both `/YYYY/MM/DD/post/attachment/` and a bare `/attachment/`, which makes a one-segment URL ambiguous with a real page. The sitemap resolves it: it lists exactly the posts and pages, so a one-segment URL absent from the sitemap is an attachment page. The images themselves keep their `wp-content/uploads/` paths and are covered separately by `golden-media-legacy.txt`.

## The Blogger-era surface

The blog ran on Blogger until mid-2012 on this same domain, and WordPress still 301s those URLs today. Nothing links to them, so no crawl finds them.

**Blogger truncated an auto-generated slug at 40 characters on a whole-word boundary.** For the 11 posts whose slug is longer, the URL Blogger actually served - and therefore the one in search indexes and in other people's links - is the truncated form. The WordPress importer registered the full slug, and both are live 301s. Mapping only the full form keeps the URL that never existed on Blogger and drops the one that did; `blogger.map` carries both, which is why it is 59 entries for 48 posts.

`/search/label/<Label>` is **not** a redirect. WordPress answers it with its generic search page, which returns 200 for a label that never existed, so the class is a soft 404 that looks alive. It is handled by choice rather than by preservation: `labels.map` sends each label to its term archive, and anything unmatched falls through to `/all/`.

## Verifying a claim about this contract

Every count above is derivable from the files, so check rather than trust:

```sh
wc -l checks/golden-urls.txt checks/redirect-urls.txt checks/golden-media-legacy.txt
```

The maps under `deploy/maps/` are regenerated by `checks/build-redirects.py`, which reads the WordPress export from the capture directory outside this repo. It selects the export **by content** and fails unless exactly one contains published posts - the capture holds both a full export and a media-only one with zero posts, and taking the wrong one yields empty maps that are indistinguishable from working ones until the redirects are live. Floor assertions catch the same collapse from any other cause.

## Directionality

The parity check fails on a **missing** URL and only notes an **extra** one. New posts, new tags, and deeper pagination legitimately add URLs; nothing legitimately removes a URL the old site served. That asymmetry is what makes the list append-only, which in turn is what makes the length-floor assertion at the top of the check sound - a truncated list would otherwise make every assertion below it pass vacuously.
