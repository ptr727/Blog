# Writing a Post

How a post on this site is written and filed. [`OPERATIONS.md`][operations] holds the procedures that publish it and [`CODESTYLE.md`][codestyle] the rules for the code around it. This file is the content half, and it exists because no gate has an opinion about the writing.

Everything here applies to `content/`. The imported archive under it predates these rules and is not swept to match them, so read this as the contract for a new post rather than as a description of all 109 old ones.

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

**Every image added must be linked from a page.** `ORPHANED_MEDIA` in [`checks/check-url-parity.py`][parity] is an exact count rather than a ceiling, so an unlinked file moves it and fails the gate. That is deliberate: it is the only check that can see an image the site carries and no page shows.

## Links

**Posts use inline links.** This is the opposite of every other Markdown file in this repository, which uses reference-style definitions at the bottom, and the difference is deliberate. A post is read end to end by someone who cannot see its source, where a doc is read one section at a time by someone who can.

- An external link is absolute: `[Hugo](https://gohugo.io/)`.
- A link to another post is a root-relative permalink: `[From Blogger to WordPress](/2012/07/15/from-blogger-to-wordpress/)`.
- A link to a file in this repository is an absolute GitHub URL, because the post is served from a different origin and a repo-relative path resolves to nothing there.

`refLinksErrorLevel: ERROR` fails the build on an unresolved `ref`, so a broken internal reference never ships. It says nothing about a root-relative path that points at a page which does not exist, which the parity gate catches instead.

## Structure

- **No `#` in the body.** The theme renders `title`.
- **`##` carries the spine, `###` only for genuinely nested steps.** The migration post uses `###` for numbered procedure steps inside one section and nowhere else.
- **A heading states a finding rather than labeling a topic.** "Your export is not a complete copy of your media" beats "Media". Sentence case, no trailing question mark.
- **No hand-written table of contents.** The theme generates one from the headings.
- **Three unheaded paragraphs open a post**: the concrete situation, what the post is really about, and one sentence on what it covers.
- **Every fenced code block carries a language tag**, so highlighting picks the right lexer instead of guessing.

## Voice

The fleet's prose rules apply to a post the same way they apply to a comment, with the vocabulary unrestricted and the structure restricted. Read the `comment-and-doc-style` Skill for the full set. What that means here:

- **First person singular, past tense, for what was done.** Second person imperative for advice to the reader. Present tense for how a thing works.
- **US English spelling.**
- **ASCII only.** No em dash or en dash, recast as a comma or two sentences rather than a spaced hyphen. No curly quotes, no ellipsis character, no arrows. A unit or scientific symbol whose ASCII form would be a lie stays, so degree and micro are fine.
- **No semicolon joining a sentence.**
- **No spaced hyphen joining or interrupting a sentence.**
- **Short sentences, twenty-five words as the cap.** Active voice.
- **Bold carries the load-bearing claim**, once or twice a section. It is emphasis, not decoration.
- **A number is exact and is verified before it is written.** The post is the only place most of these numbers appear, so a wrong one is not caught anywhere else.

**No data that identifies a machine.** A post never carries a real MAC address, hostname, serial number, device name, IP address, or absolute home path, and neither does a screenshot. Use a constructed placeholder that carries the same shape, and say it is one.

## What Is and Is Not Gated

This is the reason this file exists, so it is worth stating plainly.

| Check | Reaches a post |
| --- | --- |
| `hugo --gc --minify --panicOnWarning` | yes, it must build |
| [`checks/check-url-parity.py`][parity] | yes, for URLs, asset references, and the orphan count |
| `checks/check-live-urls.sh` | yes, against a running server |
| markdownlint | no, `content/.markdownlint-cli2.jsonc` ignores the tree |
| CSpell | no, `cspell.json` ignores the tree |
| `prose_lint.py` | no, it reads tracked prose outside `content/` |

Nothing above reads the writing. A human does, before the post merges, and that read is the only gate this file has.

## Corrections

A fact in a published post that proves wrong is corrected in the post. It is not footnoted somewhere else and not left standing with a note elsewhere saying it is wrong.

**A post may cite a README. A README never cites a post.** [`OPERATIONS.md`][operations] under "Configuration Layout" holds this rule and the reasoning: a doc that sends a reader to published prose for an operational fact has put that fact where it cannot be kept current.

<!-- Repo -->

[checks]: ./checks/
[codestyle]: ./CODESTYLE.md
[operations]: ./OPERATIONS.md
[parity]: ./checks/check-url-parity.py
