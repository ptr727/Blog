# Vendored themes

This directory holds third-party theme source, copied in rather than fetched by a manager. It sits outside `PaperMod/` deliberately, so replacing that directory wholesale on an update does not take this record with it.

Vendoring is the decision; not recording what was vendored was the gap. Without an upstream ref there is no way to ask what changed upstream, whether a fix landed, or whether a local edit is still needed, and a 125-file copy is a large surface to carry blind.

## PaperMod

| | |
| --- | --- |
| Upstream | <https://github.com/adityatelange/hugo-PaperMod> |
| Commit | `154d006e0182dfc7da38008323976b02e6bfab4a` |
| Committed upstream | 2026-05-10 |
| Describes as | `v8.0-138-g154d006` |
| License | MIT, retained at `PaperMod/LICENSE` |

The commit was recovered by matching all 125 tracked blobs against upstream history rather than by reading a version marker, since the copy carries none.

### Local edits: none

All 125 files match that commit byte for byte, so the identification is exact rather than approximate and the tree is replaceable wholesale. Verify with a clone of upstream at that commit:

```sh
git clone https://github.com/adityatelange/hugo-PaperMod.git /tmp/papermod
git -C /tmp/papermod checkout 154d006e0182dfc7da38008323976b02e6bfab4a
diff -r --exclude=.git /tmp/papermod themes/PaperMod
```

Two files did carry edits, in extension points the theme documents for the purpose. They now live outside the vendored tree, where Hugo resolves a project's own `assets/` and `layouts/` ahead of the theme's. A third override has joined them since, and the customization table below lists all three:

| Customization | Now at | Replaces the theme's |
| --- | --- | --- |
| Lexend body font, and the `gallery` and `gallery-cols-*` rules the gallery shortcode needs | [`assets/css/extended/custom.css`](../assets/css/extended/custom.css) | `assets/css/extended/blank.css`, an empty slot the theme's head partial globs for |
| Google Fonts preconnect and stylesheet links for Lexend | [`layouts/_partials/extend_head.html`](../layouts/_partials/extend_head.html) | `layouts/_partials/extend_head.html`, an empty partial the theme's head partial calls |
| GitHub Discussions link for a post that sets a `discussions` URL in its front matter | [`layouts/_partials/extend_post_content.html`](../layouts/_partials/extend_post_content.html) | `layouts/_partials/extend_post_content.html`, an empty partial the theme's single-page template calls after the post body |

The first two belong together: the font the CSS selects is the font the partial loads. Neither is a fork of theme logic, and moving them changed no rendered byte. The third was added later rather than moved out of the tree, and it renders nothing on a post that sets no `discussions` URL, which is every archive post.

The customization table holds hooks the theme leaves empty for a site to fill. Five other files at the repository root replace a whole theme template instead, so each hides every upstream change to the template it replaces. Hugo reads a root `layouts/shortcodes/` file as the theme's `_shortcodes/` file of the same name. The root override table below lists all five:

| Override | Replaces the theme's | Change from the theme's template |
| --- | --- | --- |
| [`layouts/baseof.html`](../layouts/baseof.html) | `layouts/baseof.html` | `.Language.LanguageDirection` swapped for `.Language.Direction` |
| [`layouts/rss.xml`](../layouts/rss.xml) | `layouts/rss.xml` | `site.Language.LanguageCode` swapped for `site.Language.Locale`, and each item's `<guid>` marked `isPermaLink="false"`, using a post's `guid` front matter value in place of the permalink when one is set |
| [`layouts/_partials/templates/opengraph.html`](../layouts/_partials/templates/opengraph.html) | `layouts/_partials/templates/opengraph.html` | `site.Language.LanguageCode` swapped for `site.Language.Locale` |
| [`layouts/shortcodes/audio.html`](../layouts/shortcodes/audio.html) | `layouts/_shortcodes/audio.html` | Rewritten: not muted, `preload="metadata"`, a `<source>` typed from the file extension, and fallback text |
| [`layouts/shortcodes/video.html`](../layouts/shortcodes/video.html) | `layouts/_shortcodes/video.html` | Rewritten, the same way as `audio.html` |

Each swapped call is one Hugo deprecated in 0.158, for the reason recorded in [`TODO.md`](../TODO.md). `--panicOnWarning` would otherwise fail on the theme rather than on content. A swap is a workaround for upstream lag, so `baseof.html` and `opengraph.html` become removable once upstream makes the same swap. The other changes are site behavior that an update keeps. No post sets `guid`, so every feed item's GUID is its permalink. No post calls the `audio` or `video` shortcode.

Whether each swap is still needed is answerable by diffing against the commit recorded here, which is what this record exists for.

## Customization points

PaperMod exposes **no Hugo configuration for layout width**. No template reads a width parameter, so `hugo.yaml` cannot change it and the only levers are four CSS custom properties on `:root` in `PaperMod/assets/css/core/theme-vars.css`.

| Variable | Default | Consumed by | Computed |
| --- | --- | --- | --- |
| `--main-width` | `720px` | `.main` in `common/main.css`, `.footer` in `common/footer.css`, each as `calc(var(--main-width) + var(--gap) * 2)` | 768px |
| `--nav-width` | `1024px` | `.header-nav` in `common/header.css`, as `calc(var(--nav-width) + var(--gap) * 2)` | 1072px |
| `--gap` | `24px` | the outer padding in all three, and spacing throughout | |
| `--content-gap` | `20px` | vertical rhythm inside post content | |

Two things about this are easy to get wrong.

**The width is a fixed pixel cap with no responsive term.** `core/zmedia.css` is the theme's only media-query file, and it never touches `--main-width` or `--nav-width`. It changes `--gap` to `14px` below 768px and nothing else. So the content column is 720px from a small laptop to an ultrawide, and widening it means introducing a viewport term the theme does not have. The nav is already 304px wider than the content, so raising `--main-width` past `--nav-width` without raising both puts the content outside the header.

**Override these in [`assets/css/extended/custom.css`](../assets/css/extended/custom.css), never here.** `PaperMod/layouts/_partials/head.html` concatenates the core sheet, `zmedia.css` last within it, and then the `css/extended/*.css` glob after all of it, so a `:root` block in the extended file wins on source order with no `!important` and no theme edit.

That ordering carries a trap: media queries add no specificity, so a top-level `:root` in the extended file also overrides `zmedia.css` **inside its own breakpoint**. Redefining `--main-width` or `--nav-width` there is safe, because zmedia never sets them. Redefining `--gap` at top level is not, because it silently restores the 24px gutter on phones.

The content width is unchanged from the theme default, deliberately. 720px at the 18px body size is roughly 80 characters per line, which is already at the top of the readable range, so widening the prose is a regression dressed as an improvement. The constraint worth revisiting is that images and galleries inherit the same cap, which is a real loss on a wide display for a photo-heavy site; the fix for that is to let media break out of the column rather than to widen the column.

## Updating

Nothing is carried, so an update is a replace. Delete `PaperMod/`, drop the new upstream tree in its place, and update the upstream table at the top of the PaperMod section. Then confirm the site still builds under `--panicOnWarning`, which is the gate the theme has failed before. Run the `diff -r` above afterwards, so the next reader inherits the same guarantee.

Re-check the customization table before the replace, while the upstream table still names the old commit. Each file it overrides is a comment-only hook upstream today. If upstream adds content to one, the local override hides it without any build failure. The exception is `blank.css`, which the head partial bundles beside `custom.css` rather than shadowing. Added rules there still ship, so a diff only means checking for duplication. Use the clone from the `diff -r` check above, or make a fresh one. Diff the file each row replaces between the recorded commit and the new commit. A comment-only diff needs no action. Added markup or rules mean porting them into the override, or deciding they are unwanted.

Check the root override table at the same moment, before the replace. The `diff` below covers it too. Any change there is upstream editing a template an override hides. Port it into the override, and keep the change the table records. A row whose only change is a deprecated call becomes removable once upstream makes the same swap. The `--diff-filter=A` listing names templates upstream added, with `--no-renames` so a moved template shows too. A new template more specific than an overridden one outranks the root override with no diff and no build failure. A `home.rss.xml` beside `rss.xml` is one such case. Also compare each added name against the root `layouts/` tree, reading a root `shortcodes/` file as `_shortcodes/`. A match is a new whole-template override, so it joins the root override table.

```sh
OLD=154d006e0182dfc7da38008323976b02e6bfab4a
NEW=<new upstream commit>
git -C /tmp/papermod fetch origin
git -C /tmp/papermod diff "$OLD" "$NEW" -- \
  assets/css/extended/blank.css \
  layouts/_partials/extend_head.html \
  layouts/_partials/extend_post_content.html \
  layouts/baseof.html \
  layouts/rss.xml \
  layouts/_partials/templates/opengraph.html \
  layouts/_shortcodes/audio.html \
  layouts/_shortcodes/video.html
git -C /tmp/papermod diff --name-only --no-renames --diff-filter=A "$OLD" "$NEW" -- layouts
git -C /tmp/papermod grep -n -e extend_head -e extend_post_content -e templates/opengraph "$NEW" -- layouts
git -C /tmp/papermod checkout "$NEW"
```

Set `OLD` to the commit in the upstream table, and update that table afterwards. The `grep` confirms upstream still calls each overridden partial, since a partial upstream stops calling leaves an override that renders nothing and an empty diff. The `checkout` leaves the clone at the new commit for the `diff -r` run. Add a path to the `diff` command when a row joins the customization table or the root override table. Take it from the last column of the customization table, or from the second column of the root override table. Add the partial's path below `_partials/`, without its extension, to the `grep` when the row is a partial. Confirm each path exists at the new commit with `git -C /tmp/papermod cat-file -e "$NEW:<path>"`. A diff of a mistyped path prints nothing, the same as an unchanged file.

No bot watches this. `.github/dependabot.yml` covers GitHub Actions only, since a vendored copy has no manifest to track, so an update is a deliberate act.

Fetching the theme rather than copying it is the way to get a bot, and only one of the two mechanisms would work here. Dependabot's `gitsubmodule` ecosystem tracks a ref and needs no tags, so a submodule would be watched. Hugo Modules would not: PaperMod tags releases as `v8.0`, which is not valid semver, so Go can only pin it as a pseudo-version, and Dependabot does not upgrade pseudo-versions. Either mechanism first requires the tree to carry no local edits, which is now true. Weigh it against what a bot would have found: between 2026-05-10 and 2026-08-06, upstream's only commit edited its own README.
