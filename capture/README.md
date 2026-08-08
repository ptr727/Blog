# Provenance Capture

Everything in this repository is derived. What it was derived *from* is a capture directory that lives outside it, and this directory holds the scripts that read that capture.

The capture's path is `CAPTURE_ROOT`, in `secrets/<server>.<environment>.env`, recorded there alongside the other values that name a machine rather than the project. It is not a git repository, so it has no history to revert to, and it is read-only in normal use. Nothing here writes into it except the steps below that say they do.

**None of this runs in CI, and none of it runs on a schedule.** These are provenance tools, run by hand, and their outputs are committed. That is the whole difference between this directory and [`checks/`](../checks/), which holds gates that run on every change.

## What is under the capture

| Under the capture | Holds | Recoverable |
| --- | --- | --- |
| `export/raw/` | the WordPress content export, WXR XML | yes, from the WordPress account while it exists |
| `export/media-tar/` | the media export, the only trustworthy copy of the images | yes, from the same place |
| `mirror/` | a crawl of the old platform as it served, including the media it linked from other hosts | no, once the old hosting ends |
| `inventory/` | the URL and media inventories derived from that crawl | no, for the same reason |

**The mirror spans more hosts than the blog.** It was taken across the blog itself, the platform's image CDN, and the Google hosts that served the hotlinked images, which is why it holds media that was never in the media library. That matters beyond the migration: [`checks/README.md`](../checks/README.md) adjudicates orphaned media against this tree, and an adjudication is only as good as what the crawl reached.

**The capture holds personal data and is never committed.** The WXR carries commenter email addresses and IP addresses, and the mirror carries the same data rendered into HTML. The conversion resolves this by dropping comments entirely rather than scrubbing them, so there is no partial to get wrong, and the site this repository builds has none. The capture itself keeps them, which is one more reason it stays outside git.

## The two exports, and the counts they must reconcile

Two downloads from the WordPress account, both from Tools then Export.

1. **The content export.** Choose **All content** and do not filter by date or type. One WXR XML file. This carries the post and page bodies in raw form, the comments, the categories and tags, and pointers to the media. It is the primary input and the one thing that cannot be fetched from outside the account.
2. **The media library export.** A separate menu item on the same page, producing a `.tar` organized into year and month folders. Not strictly required, because the crawl captures what the posts reference, but worth taking for two reasons: it includes media that was uploaded and never embedded in a post, which the XML omits entirely, and it avoids rate-limiting during conversion.

**Verify the export against what the live site reported before trusting it.** A partial export is the common way a migration loses posts without reporting anything, so a mismatch is a stop-and-investigate rather than a rounding error. These are a **measurement of the old platform taken 2026-07-29**, not values this repository can check, and they are recorded because nothing else will ever be able to state them again:

| | Measured |
| --- | --- |
| Posts | 108 |
| Pages | 2 |
| Comments | 397 |
| Categories | 12 |
| Tags | 183 |
| Media assets | 941, being 675 in the library and 266 hotlinked |

**Do not cancel the old plan, delete the site, or change DNS until the cutover is done and has held.** The conversion fetches media over HTTP from the live site, so cancelling early loses images, and deleting the site destroys the ability to re-export. The DNS change *is* the cutover and comes last.

## Rebuilding from the exports

In order. Each Python step is a dry run by default and takes `--apply` to write.

```sh
set -a; . secrets/local.production.env; set +a

capture/run-wp2hugo.sh                        # convert, into $CAPTURE_ROOT/converted/
capture/clean-content.py --apply              # drop comments, reduce the front matter
capture/restructure-content.py --apply        # reshape the tree to match the URLs
capture/localize-external.py --apply          # pull the hotlinked images local
capture/build-redirects.py                    # regenerate deploy/maps/
```

`build-redirects.py` is the only one that writes into this repository, and what it writes is committed. The other four write into the capture.

**The export is selected by content, never by filename.** An account holds several exports and a media-only one carries the attachments and no posts, so a glob would choose by filesystem order and converting the wrong one yields a site that builds and is empty. `build-redirects.py` makes the choice, and `run-wp2hugo.sh` asks it with `--print-export` rather than repeating the logic, so the conversion and the maps are provably built from the same file.

## What the conversion does not carry

**Hotlinked images are in no export.** Images embedded from other hosts during the Windows Live Writer and Blogger era were never in the media library, so they are absent from the WXR, and the converter skips them as non-relative links. Left alone they stay a permanent dependency on someone else serving fifteen-year-old URLs. `localize-external.py` downloads them, names each by a hash of its source URL, because the originals carry characters that do not survive a filesystem, then rewrites every reference and records the mapping in the capture's inventory.

**Comments are dropped rather than scrubbed.** The blog is read-only going forward, so the data file is deleted outright. There is no partial scrub to get wrong and nothing to carry.

**Front matter is reduced to what drives the site.** The converter carries every WordPress custom field through, most of them platform internals that no template reads. `clean-content.py` keeps a short list and drops the rest. The list is in the script rather than restated here, so a reader can diff it against a new export.

## Three results that look like success and are not

- **A Picasa or ggpht URL whose size segment ends in `-h` returns HTTP 200 with an HTML page**, not an image, and a naive fetch writes a few hundred bytes of markup with a successful status. `localize-external.py` parses the wrapper and follows the `<img src>` it names, which is the platform's own answer rather than a guess.
- **Any non-image body is a failure regardless of status.** The magic bytes are checked, and anything that is not an image is reported rather than written.
- **Selecting the export by filename yields empty maps that pass every check** until the redirects are live. See the note above on selection by content.

## How the URL contract was captured

The contract in [`checks/`](../checks/) was not derived from the content tree. It was measured against the live old platform, by union of three sources and then verified URL by URL:

| Script | Did |
| --- | --- |
| `enumerate-media.py` | pulled every post and page from the platform's REST API in **rendered** form, so shortcodes were expanded and a media reference was seen as a browser sees it, and split the results by host to separate library media from hotlinks |
| `build-golden.py` | unioned the crawl, the sitemap and a derivation of the archive and pagination shapes, then requested every candidate against the live site and recorded what it answered |
| `classify.py` | split the verified set into what must render and what must redirect, using the sitemap as the discriminator for bare one-segment URLs, which are ambiguous between a real page and an attachment page |

**These three cannot run again once the old hosting ends.** They are carried as the record behind an append-only contract, not as a step anyone re-runs. An append to `golden-urls.txt` is only reviewable against the derivation that produced the original, which is why the derivation is here rather than lost with the platform.

**They write into the capture and never into `checks/`.** The committed lists are grown by hand from a log finding, per that directory's own maintenance rules. A script that could rewrite them would be able to replace a verified contract with an inferior re-derivation.

## Two properties of the maps that are easy to break

**The Blogger map holds more entries than there are Blogger-era posts.** That platform truncated an auto-generated slug at a fixed length on a whole-word boundary, so a long title was served at the truncated address and that is the address in search indexes. The importer registered the full slug, both answer, and both are mapped. The limit is a named constant in `build-redirects.py`, and changing it changes how many entries the map has.

**A term archive the old platform served is not always one Hugo builds.** Where it does not, the URL still has to answer, which is why the maps carry terms that no longer exist as pages.

## What lived in the capture and is not carried

Seven scripts stayed behind, and each is named here so nobody goes looking for something that was deliberately left.

| In the capture | Did | Why it is not here |
| --- | --- | --- |
| `crawl/spider.sh` | enumerated every URL the live site served, politely and with an identifying user agent | A short flag list against a site that will be gone. Its output, the crawl log, is the durable artifact and is in the capture. |
| `crawl/mirror.sh` | took the offline snapshot, spanning the blog and the image hosts | Same, and its span-host list is recorded above because the orphan adjudication depends on it. |
| `inventory/fetch-at-risk.sh` | downloaded every hotlinked image with its size and SHA-256 | The manifest it wrote is the durable artifact. Re-verification reads the manifest and never re-fetches. |
| `inventory/fetch-missing.sh` | fetched library media the crawl did not reach | Same shape, same reason. |
| `inventory/fetch-unattached.sh` | fetched media listed in the export but never embedded in a post | Same shape, same reason. |
| `build-redirects.py` at the capture root | an older copy of the generator | **Stale.** Superseded by the copy here. |
| a second copy under the capture's own `checks/` | byte-identical to the one above | **Stale.** Superseded by the copy here. That directory belongs to the capture and is not this repository's `checks/`. |

**The two stale copies are named by path on purpose**, so that finding one is not mistaken for finding a source. Neither has the fixes this copy carries.

## Variables

Every path and address is a variable, so nothing here names a machine. [`example.env`](../example.env) lists them and [`ENVIRONMENT.md`](../ENVIRONMENT.md) describes them.

A required value that is unset stops the script and names what is missing, rather than falling back to something plausible. A wrong-but-valid capture directory produces empty maps that are indistinguishable from working ones until the redirects are live, which is the failure this rule exists for.

`CAPTURE_SOURCE_URL` is the **old** platform. It holds the same string as `HUGO_BASEURL` after the cutover and means something different, so merging the two would point a verification run at the new site while every check still passed.

## This directory is the source

Edit the copy here and run it from here. A copy found in the capture is an artifact of when it ran, not a place to make a change.
