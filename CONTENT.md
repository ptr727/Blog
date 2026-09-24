# Writing a Post

How a post on this site is written and filed. [`OPERATIONS.md`][operations] holds the procedures that publish it and [`CODESTYLE.md`][codestyle] the rules for the code around it. This file is the content half, and it exists because no gate has an opinion about the writing.

Everything here applies to `content/`. The imported archive under it predates these rules and keeps its own voice, so read this as the contract for a new post rather than as a description of all 109 old ones.

## Where a Post Lives

A post is one Markdown file, never a page bundle, at:

```text
content/posts/<YYYY>/<MM>/<DD>/<slug>.md
```

The tree mirrors the address the site serves, which is what makes a file findable from a URL and a URL predictable from a file. The date in the path is the date in the front matter.

**The slug is decided before the post merges and never after.** A published path is an address this site is contracted to answer, so renaming the file breaks it, and the URL contract in [`checks/`][checks] has no remedy for a URL that used to work. Editing a post moves nothing and is always safe.

## Front Matter

Five keys, in this order, and nothing else:

```yaml
---
title: Moving This Blog From WordPress to Hugo
date: '2026-08-01T12:00:00+00:00'
url: /2026/08/01/moving-this-blog-from-wordpress-to-hugo/
categories:
- solution
- cloud
tags:
- hugo
- migration
---
```

- **`title`** is title case, and it is what the theme renders as the page heading. The body carries no `#` of its own.
- **`date`** is a quoted RFC3339 string. Hugo reads an unquoted one as a date object and formats it back differently.
- **`url`** repeats the permalink the configuration would generate anyway. Every post carries it, so a post that omits it is the odd one out rather than the tidy one.
- **`categories`** and **`tags`** are block sequences, with each item's hyphen at column zero.

An optional `cover` is a nested map of `alt` and `image`. No post carries `draft`, `description`, `summary`, `series`, `weight`, or `aliases`. A `post_id` on an old post is a WordPress import artifact, and a new post never gets one.

`archetypes/default.md` encodes this, so the path decides the rest:

```sh
hugo new content posts/2026/07/22/a-post-about-something.md
```

The `url` is derived from the directory, so the two cannot disagree. Fill in the taxonomy, which the archetype leaves as `uncategorized` and `replace-me` so an unfilled one is visible rather than silently shipped.

## Taxonomy

**Categories are a closed set.** The twelve in use are `backup`, `cloud`, `homeautomation`, `network`, `performance`, `power`, `problem`, `research`, `review`, `solution`, `storage`, and `uncategorized`. Pick from those. Adding a thirteenth is a decision about how the archive is organized rather than a detail of one post.

**Tags are open, and each new one costs an address.** A tag builds its own archive page, so a tag used once creates a URL the site then serves forever. Reuse an existing tag where one fits. All tags are lowercase, and a multi-word tag is hyphenated.

The parity gate reports both as `additional URLs built (not a failure)`, so nothing stops a new tag. The cost is that the address is permanent, not that the build complains.

## Media

Images go under `static/media/<YYYY>/<MM>/` and are referenced as `/media/<YYYY>/<MM>/<file>`. The year and month are the post's, and the filename is lowercase and hyphenated.

`static/external/` is the tree of images the old site hotlinked from elsewhere, pulled local during the migration and named by content hash. It takes nothing new.

Embed with the `figure` shortcode, and wrap a set in `gallery`:

```text
{{< figure src="/media/2026/07/frame-decode.png" alt="The decoded frame beside the app's own reading" >}}

{{< gallery cols="2" >}}
{{< figure src="/media/2026/07/one.png" alt="..." >}}
{{< figure src="/media/2026/07/two.png" alt="..." >}}
{{< /gallery >}}
```

**Alt text is required and describes the image**, since it is what a reader without the image gets.

**Every image is normalized before it is committed.** Run [`scripts/normalize-media.py`][normalize]. It keeps only what a picture needs in order to render, the dimensions and, on every format but GIF, the color profile, plus the orientation and the capture timestamp on a JPEG, the one format here whose Exif the gate admits. A JPEG keeps its timestamp only when its whole Exif segment already passes the gate. An Exif segment holding anything the gate does not admit is dropped whole, its timestamp with it, and only an orientation other than upright is written back. A JPEG whose Orientation is not a single SHORT is refused, since browsers ignore any other shape while other decoders honor it. So is one whose Orientation holds two different values, twice in its main directory, IFD0, or once there and once in a directory reached from it, since decoders differ on which of the two they read. So is one holding an Orientation in, or reached from, an IFD0 that sits inside the TIFF header or whose entries run past the end of its Exif segment, since decoders differ on whether they read that IFD0 at all. A directory past IFD0 whose entries run past the end is read as far as it goes, and the JPEG is refused where reading it changes the Orientation. An Orientation entry the end of the segment cuts off is refused wherever it sits. An IFD0 holding no Orientation counts as upright, since a browser reads IFD0, so a turn held only in a directory reached from it is refused too. A JPEG with two Exif segments is refused rather than cleaned. A PNG or WebP keeps no Exif at all, so it keeps no timestamp. The normalizer refuses one whose Orientation a JPEG would be refused for, or that turns the picture, since dropping that Exif could turn it back. A color profile stays only when it is byte for byte one of the standard sRGB or Display P3 profiles the gate pins by digest. The normalizer refuses any other, so convert that picture to sRGB first. A PNG keeps its gamma and chromaticity only at the sRGB values, and its pixel density only as square pixels, and the normalizer refuses any other. Its significant bits and background color stay only at full depth and zero, since no browser draws by them, and go otherwise. A palette in a truecolor PNG only suggests one, so it goes too. The normalizer refuses a palette in a grayscale PNG. It also refuses a palette that is empty, holds a partial entry, follows the picture data, or runs past what the bit depth addresses. It refuses an animated PNG too, since GIF and WebP carry the animation here. It writes a GIF's unused graphic control fields as zero. It does the same for a GIF's sort flags, color resolution, background index, aspect ratio, and table size where no table follows. It drops a GIF's global color table where every image carries its own, and writes its version as 89a. It writes a WebP animation's background color as zero, and drops fill bytes between JPEG segments. It refuses a JPEG holding fill bytes inside a scan, and a PNG whose gamma, chromaticity, profile, transparency, or density chunk sits where a decoder does not read it. Everything else goes, and it never asks what the removed thing was. Location, device, and authorship are not on the list, so they go without anyone thinking of them. That is the point. A rule that enumerates hiding places is only as good as its last revision. The removal is lossless on every format carried here, so an original is not degraded in order to clean it. [`checks/check-media-metadata.py`][metadata] fails the build on anything left over, and it reads inside a `.zip`. Then inspect the image at full resolution. Redact a house number, a license plate, a face, a serial number, a rating plate, a barcode, and a hardware address. "What Identifies" below gives the full checklist and the narrower rule for an image already published. Cover each one with a flat opaque fill, never a blur or a mosaic. Both can be reversed for a short string drawn from a known alphabet. A fill also tells the reader that something was removed. Verify both halves. `python3 checks/check-media-metadata.py` passes, and a full-resolution crop of each redacted area is unreadable.

**The text of a post is gated the same way.** [`checks/check-text-pii.py`][text-pii] reads every Markdown file under `content/` outside the imported archive years, the same boundary `.github/prose-gate-excludes` draws for the prose gate. It reads front matter and code blocks too, since a pasted configuration is where a hardware address usually hides. It reports an email address, a hardware address, a public IP address, a coordinate pair, a URL carrying coordinates or naming a sensor or station, a street address, and a phone number. Each finding names the file, the line, and the class, and never the value, so the CI log does not republish it. A documentation-range or private address is not public and is not reported. Voice still requires a placeholder for a private one. A hardware address is read in its colon, hyphen, and dotted forms. A bare run of twelve hex digits is not, since a short commit hash has the same shape. A four-part number directly after a word such as version, build, or firmware is read as a version rather than an address. Run `python3 checks/check-text-pii.py` locally, the same command the validate action runs.

**A value a post prints on purpose is declared, not passed silently.** A vendor's support email or a public service's address goes in [`checks/text-pii-allow.json`][text-pii-allow] as an entry under `allow`, with a `class` naming what the gate reported, exactly one of `value` (the exact text) or `pattern` (a regular expression the whole value must match), and a `reason`. An entry is bound to its class, so a pattern declared for one class never silences another. An entry that matches nothing in scope fails the gate, so the list holds only values a post still prints. Any other false positive is declared the same way. The tests in `checks/tests/` run in the same action, and every value in them is constructed.

**Every image added must be linked from a page.** `ORPHANED_MEDIA` in [`checks/check-url-parity.py`][parity] is an exact count rather than a ceiling, so an unlinked file moves it and fails the gate. That is deliberate: it is the only check that can see an image the site carries and no page shows.

## What Identifies

"Media" above says to strip the metadata and redact the obvious. This section is the part that is not obvious.

**Two questions decide it. Does this locate the home, or does it identify a person?** Every rule below is one of those two applied.

### Adding an Image to a Post

**This is the checklist for the moment an image is added, and the default is broad.** Redaction costs almost nothing here, because a shot can be reframed, retaken, or cropped before anyone sees it. An author who wants a label in frame says so and keeps it. That freedom is what makes a wide default affordable.

Check for each of these, redact on sight, and argue afterwards if the image needs it:

- A face, including the author's own. A published name is not a published likeness.
- Precise location. A house number, a street sign, a curbside plate, a shipping label, a neighbor's facade, or a civic landmark.
- A serial number, a service tag, a hardware address, a barcode, or a QR code. A code still scans after its printed digits go soft, so legibility is not the test.
- An account handle, an email address, or a hostname.
- A BSSID, and the SSID beside it. Public databases map an access point's hardware address to the coordinates where it was seen.
- A service identifier that still resolves, such as a sensor ID or a map link carrying coordinates. Link the service rather than the instance.
- A child's name, and most of all where it labels a room beside an occupancy time.
- Anything belonging to someone else. That consent was never the author's to give.
- A private-range address, which Voice already requires replacing with a placeholder, in a screenshot as much as in prose.

### Never In Scope

These are settled, in new media and old alike, and reopening one wastes a reviewer's time.

- **The author's own name.** It is on the About page and in the site config. In a nav bar or a window title it is interface chrome.
- **Coarse location.** A city, a country, or a timezone. The street and the block are a different matter.
- **Generic room and device labels.** A thermostat zone named for a room, or an automation entity named for an appliance.

### Remediating an Image Already Published

**A wide default is affordable in new media and destructive in old.** Nothing in the imported archive can be reframed or retaken, so a fill there removes meaning that no longer exists anywhere else.

**The archive's bar is narrow because its images have been public for years.** A fill there covers a street address or house number, an email address, a phone number, people's names on clothing, a clearly visible face, a landmark or a neighbor's property that places the home, an SSID or BSSID, a VIN or license plate, and a child's name beside an occupancy time. The author's name and handle, private-range and long-reassigned public addresses, machine names, serials and barcodes on retired equipment, and public credits all stay. So does a face too faint to recognize.

Treat that as a judgment about the archive, never as a precedent for a new post.

**Every archive redaction is data, never a hand edit.** [`checks/media-redactions.json`][redactions] names each file, its fills or crop, and why. [`scripts/redact-media.py`][redact] applies it after the metadata normalizer, and records the hash each file starts from and lands on. So a run is deterministic, and a second run changes nothing. [`checks/check-media-redactions.py`][redactions-check] fails the build on a declared file that is not at its redacted result. To change an entry, restore the file's original from history, run the metadata normalizer on it, edit the entry, and run `uv run scripts/redact-media.py --record`. A restored file that any committed revision of the manifest records as a result is refused, since it already carries an earlier round's fills.

**The archive's text follows the same model.** [`scripts/normalize-text.py`][normalize-text] replaces typographic characters with ASCII outside fenced code, blockquotes, front matter, and lines holding a protected product name. It then applies the corrections listed one by one in [`scripts/text-corrections.json`][text-corrections]: doubled words, grammar slips, a title's HTML entity, and two links that located the home. Nothing else in an old post is restyled, its punctuation included.

### Judging One

**Look at what the photograph is of.** A frame may hold a photograph, a printed advertisement, or a screen showing either. Faces in an advertisement belong to the advertiser.

**Read the post first.** Redacting a value the post prints in its own code block protects nothing and costs the screenshot its worked example.

**A fill over distant or defocused background is cost with no protection.** Where a locator is not readable, covering it only damages the image.

**Some frames cannot be patched.** One frame can carry a street sign, a neighbor's facade, and a ridgeline at once. Crop to the subject, or drop it.

**A partial redaction is worse than none, because it looks handled.** Cover the whole value rather than the part that named it.

**A filename is published.** Hugo serves `static/` verbatim, so a name in a filename reaches the URL, where a fill cannot touch it.

**A credential is rotated, not redacted.** Editing the image stops further exposure and revokes nothing.

## Links

**Posts use inline links.** This is the opposite of every other Markdown file in this repository, which uses reference-style definitions at the bottom, and the difference is deliberate. A post is read end to end by someone who cannot see its source, where a doc is read one section at a time by someone who can.

- An external link is absolute: `[Hugo](https://gohugo.io/)`.
- A link to another post is a root-relative permalink: `[From Blogger to WordPress](/2012/07/15/from-blogger-to-wordpress/)`.
- A link to a file in this repository is an absolute GitHub URL, because the post is served from a different origin and a repo-relative path resolves to nothing there.
- **A link goes on the first mention, and only there.** A later mention stays plain text, so a reader meets each link once, at the point the post introduces it. Link a tool, project, product, or person a reader would go and look up. A name they already know, such as Android or Wi-Fi, stays plain text.

`refLinksErrorLevel: ERROR` fails the build on an unresolved `ref`, so a broken internal reference never ships. It says nothing about a root-relative path that points at a page which does not exist, which the parity gate catches instead.

## Structure

- **No `#` in the body.** The theme renders `title`.
- **`##` carries the spine, `###` only for genuinely nested steps.** The migration post uses `###` for numbered procedure steps inside one section and nowhere else.
- **A heading states a finding rather than labeling a topic.** "Your export is not a complete copy of your media" beats "Media". Sentence case, no trailing question mark.
- **No hand-written table of contents.** The theme generates one from the headings.
- **Three unheaded paragraphs open a post**: the concrete situation, what the post is really about, and one sentence on what it covers.
- **Every fenced code block carries a language tag**, so highlighting picks the right lexer instead of guessing.

## Voice

The fleet's prose rules apply to a post, with the vocabulary unrestricted and the structure restricted. Read the `comment-and-doc-style` Skill for the full set. One of them does not carry over. The fleet caps a sentence at twenty-five words across agent-authored prose, taking the structural half of ASD-STE100 as its house style. That controlled language was written for maintenance and assembly instructions, where a reader follows one action at a time. A post is narrative, and it carries causality, asides, and rhythm. Rhythm needs sentences of differing length, so the rules below replace that cap for a post, and nowhere else. What the fleet's rules mean here:

- **First person singular, past tense, for what was done.** Second person imperative for advice to the reader. Present tense for how a thing works.
- **US English spelling.**
- **Spell out an abbreviation on first use**, as the expansion followed by the abbreviation in parentheses, such as "Bluetooth Low Energy (BLE)". Later uses take the abbreviation alone. Units, and abbreviations every reader already knows, such as AC, HVAC, PSU, UV, USB, ASCII, and JSON, are exempt.
- **Punctuation is ASCII.** No em dash or en dash, recast as a comma or two sentences rather than a spaced hyphen. No curly quotes, no ellipsis character, no arrows. Write a relational or arithmetic operator as `<=`, `>=`, `!=`, or `+/-` in flowing prose, and keep the symbol only next to a number.
- **A unit or scientific symbol is the exception**, because its ASCII form would be a lie. Degree, micro, ohm, and pi stay as themselves rather than being approximated or spelled out. Any other non-ASCII character is a defect rather than a judgment call.
- **No semicolon joining a sentence.**
- **No spaced hyphen joining or interrupting a sentence.**
- **Sentences stay under thirty-five words, and forty is the defect.** Between those two, recast rather than split where a split would leave a fragment or drop the link between a cause and its effect. Active voice.
- **One idea per sentence, which is what length only approximates.** A third independent clause is a signal rather than a limit. Reread that sentence, and split it where it turned out to carry two ideas. A sentence that chains "and", then "which", then "because" is the shape to catch, whatever any count says.
- **No comma splice.** Two independent clauses take a period or a conjunction, never a bare comma. A short parallel series is the exception, where clauses of the same shape are the point, such as "Pull the APK, automate it."
- **A paragraph runs to about five sentences, or a hundred and twenty words.** A wall of text is what a reader leaves, and the word count is the half that matters most on a phone.
- **Vary sentence length within a paragraph.** Sentences all of one length read mechanically however short they are, so a long one after two short ones is doing work.
- **The post reads at a Flesch reading ease of fifty or better**, measured over the prose paragraphs alone. Front matter, fenced blocks, tables, and alt text are left out. One number over the whole post catches drift that no single-sentence rule sees. Syllable counting differs between tools, so a score near the floor is a prompt to reread rather than a verdict. Nothing computes it for you.
- **Bold marks what a skimmer must not miss.** At most one span per paragraph, and at most one series of parallel lead-ins per section. It is emphasis, not decoration.
- **A number is exact and is verified before it is written.** The post is the only place most of these numbers appear, so a wrong one is not caught anywhere else.

**No data that identifies a machine.** A post never carries a real MAC address, hostname, serial number, device name, IP address, or absolute home path, and neither does a screenshot. Use a constructed placeholder that carries the same shape, and say it is one. "What Identifies" above carries the same rule for a photograph.

## What Is and Is Not Gated

This is the reason this file exists, so it is worth stating plainly.

| Check | Reaches a post |
| --- | --- |
| `hugo --gc --minify --panicOnWarning` | yes, it must build |
| [`checks/check-url-parity.py`][parity] | yes, for URLs, asset references, and the orphan count |
| `checks/check-live-urls.sh` | yes, against a running server |
| markdownlint | no, `content/.markdownlint-cli2.jsonc` ignores the tree |
| CSpell | no, `cspell.json` ignores the tree |
| `prose_lint.py` | yes, for characters and punctuation on changed lines. `.github/prose-gate-excludes` leaves out the imported posts' years |
| [`checks/check-text-pii.py`][text-pii] | yes, for personal data in the text, outside the same archive years |

Nothing above judges the writing itself. A human does, before the post merges, and that read is the only gate for it.

## Corrections

A fact in a published post that proves wrong is corrected in the post. It is not footnoted somewhere else and not left standing with a note elsewhere saying it is wrong.

**A post may cite a README. A README never cites a post.** [`OPERATIONS.md`][operations] under "Configuration Layout" holds this rule and the reasoning: a doc that sends a reader to published prose for an operational fact has put that fact where it cannot be kept current.

<!-- Repo -->

[checks]: ./checks/
[codestyle]: ./CODESTYLE.md
[operations]: ./OPERATIONS.md
[metadata]: ./checks/check-media-metadata.py
[normalize]: ./scripts/normalize-media.py
[text-pii]: ./checks/check-text-pii.py
[text-pii-allow]: ./checks/text-pii-allow.json
[normalize-text]: ./scripts/normalize-text.py
[parity]: ./checks/check-url-parity.py
[redact]: ./scripts/redact-media.py
[redactions]: ./checks/media-redactions.json
[redactions-check]: ./checks/check-media-redactions.py
[text-corrections]: ./scripts/text-corrections.json
