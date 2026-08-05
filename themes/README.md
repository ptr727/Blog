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

The commit was recovered by matching all 125 tracked blobs against upstream history rather than by reading a version marker, since the copy carries none. Every file matches that commit exactly except the two below, so the identification is not approximate.

### Local edits

Both sit in extension points the theme documents for this purpose, so neither is a fork of theme logic.

| File | Edit |
| --- | --- |
| `PaperMod/assets/css/extended/blank.css` | The theme's custom-CSS slot, which ships empty. Carries the Lexend body font and the `gallery` and `gallery-cols-*` rules the gallery shortcode needs. |
| `PaperMod/layouts/_partials/extend_head.html` | The theme's head-extension partial, which ships empty. Carries the Google Fonts preconnect and stylesheet links for Lexend. |

Both could live outside the vendored tree instead: Hugo resolves a project's own `assets/css/extended/` and `layouts/_partials/` ahead of the theme's, so moving them would make an update a clean directory replace with nothing to reapply. Worth doing at the next update rather than as a change of its own.

Separately, `layouts/` at the repository root already overrides two theme templates, for the reason recorded in [`TODO.md`](../TODO.md): PaperMod uses APIs Hugo deprecated in 0.158, and `--panicOnWarning` would otherwise fail on the theme rather than on content. Whether those overrides are still needed is answerable by diffing against the commit above, which is what this record exists for.

## Updating

Compare against the recorded commit first, so the local edits above are known before anything moves. Replace `PaperMod/` with the new upstream tree, reapply the two edits (or move them out, per the note above), update the table here, and confirm the site still builds under `--panicOnWarning`, which is the gate the theme has failed before.

No bot watches this. `.github/dependabot.yml` covers GitHub Actions only, since a vendored copy has no manifest to track, so an update is a deliberate act.
