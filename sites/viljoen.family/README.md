# viljoen.family

The single-page genealogy site for the Viljoen family, served at `viljoen.family` from the blog's release bundle. See [OPERATIONS.md][operations] "The Family Site" for how it ships and which hostnames reach it. This file is not shipped.

## Contents

- [Contents](#contents)
- [Files](#files)
- [The Arms](#the-arms)
- [Page Design](#page-design)
- [How the Tree Is Drawn](#how-the-tree-is-drawn)
- [Facts on the Page and Their Sources](#facts-on-the-page-and-their-sources)
- [Local Preview](#local-preview)
- [Ideas Not Yet Done](#ideas-not-yet-done)

## Files

| File | What it is |
| --- | --- |
| `index.html` | The whole page, with inline CSS and the inline tree-drawing script |
| `crest.svg` | The full achievement (crest, helm, mantling, shield, name scroll), viewBox 336x418 |
| `favicon.svg` | The shield alone, cut from `crest.svg` |
| `apple-touch-icon.png` | 180x180, `favicon.svg` on parchment |
| `og-image.png` | 1200x630 Open Graph image, the crest beside the page title |

Every file in this directory except this README ships to the bundle's `family/` tree.

## The Arms

The blazon, from the Viljoen Family Website crest page ([hugenoot.org.za][hugenoot-crest]):

- **Shield:** Gules, a saltire Or (a gold St Andrew's cross on red).
- **Mantling:** Or and Gules.
- **Crest:** a pair of eagle's wings folded Or.

The arms derive from the French family Villon de Varennes, whose crest was a golden mural crown. At the 1976 Viljoen Festival the Viljoen Familiebond voted to replace it with the golden wings. Wikipedia's image shows only the shield, helm, and mantling, with no crest, and captions the arms "unregistered". The page therefore describes them as the family's arms and makes no claim of official registration.

`crest.svg` is a vector redrawing of the family's crest as Prof. Christo Viljoen shows it ([Viljoen Familie][viljoen-familie]). The pair of folded wings is drawn in profile, so one wing shows. It matches that image's 336x418 size, so the two overlay directly for comparison.

- Each part is a named group: `mantling-gold`, `mantling-red`, `mantling-stems`, `mantling-joins`, `shield`, `helmet`, `wing`, `torse`, `name-scroll`, and `viljoen-lettering`.
- Each side of the mantling is one group mirrored with `translate(342 0) scale(-1 1)`.
- The saltire is one filled path clipped to `#shield-clip`, which is built from `#shield-outline`.
- The lettering is vector paths rather than `<text>`, so it renders the same without the font. The page's `<h1>` is visually hidden text, so the name stays a real heading.
- `favicon.svg` reuses the shield outline and saltire paths. `apple-touch-icon.png` and `og-image.png` are Chromium renders, and they carry no metadata chunks.

## Page Design

- **Palette:** parchment `#f4ead3`, cards `#fbf5e4`, red `#9e1b22`, gold `#b8862b`, bark `#5b3f27`, leaf `#6f7d3a`, all CSS variables in `:root`.
- **Fonts (Google Fonts):** Cormorant Garamond for headings, EB Garamond for body text.
- **Frame:** a 2.5px red border plus an inner 1px gold rule (`.frame::before`) with rounded corners and four gold corner flourishes (`#corner` symbol). A negative margin on the masthead equals the frame's top margin (128px, or 96px on phones). That puts the top border behind the mantling, so change both values together.
- **Paper texture:** an inline SVG `feTurbulence` noise data URI plus a radial vignette on `html`.
- **Divider:** a simplified Huguenot cross (a Maltese cross with fleur points, balls on the tips, and a hanging dove), the `#huguenot-cross` symbol.
- **CSP:** the policy in `deploy/Caddyfile` allows `'unsafe-inline'` for scripts and styles because both are inline. Moving them to `site.css` and `site.js` lets the policy drop it. Test in a browser after any CSP change, because a blocked script fails silently and the tree simply does not draw.
- **Browser support:** the page uses `color-mix()`. Older browsers lose some tints, and the layout is unaffected.

## How the Tree Is Drawn

The tree is a stamboom. The children form the crown, and the stamouers card sits at the base of the trunk. Roots reach into a soil band labeled Clermont and Middelburg.

- **Markup:** the DOM is in genealogical order, as nested `<ol>`. `li.gen-a` holds the couple card, the soil band, and `ol.gen-b`, which has one `li` per child. CSS `order` puts the children above the couple, so the tree reads upward. The source and a screen reader still read from the progenitor down.
- **Name-carrying lines:** `li.line` marks b3 and b4. Their cards take the red border and "Viljoen line" badge, their limbs are thicker, and a "c generation to follow" stub continues each one.
- **Numbering and signs:** SAG de Villiers/Pama numbering (`a`, `b1` to `b6`, `b3c4`). The signs are `*` born, `~` baptized, `x` married (`x1`, `x2` for successive marriages), and a dagger for died. Each is an HTML entity inside `<abbr title>`, hidden from screen readers. On the cards a visually hidden word stands in for the sign. The legend under the tree already spells each word out, so its signs carry no hidden word. Dates use the SAG `dd.mm.yyyy` form.
- **Living people:** none are published. Only people born before about 1925 are shown.

The script at the bottom of `index.html` measures the couple card, the soil band, the child cards, and the stubs, then fills `svg.branches` inside `.tree`:

- Each limb is a cubic Bezier drawn as a filled shape that tapers from width `w0` to `w1` (`limb()`), not as a stroke.
- Leaves sprout at chosen positions along a limb, alternating sides (`leaves()`). The pattern is fixed rather than random, so every redraw looks the same. About one leaf in five is gold.
- **Roots:** seven tapering roots run from the bottom of the couple card into the soil band, in both layouts.
- **Wide layout** (six cards in a row): a trunk rises from the couple card to a fork. One S-curve branch runs from there to the bottom of each child card. A short limb continues from each name-carrying card to its stub.
- **Stacked layout** (900px wide or less): the cards form a column. The trunk rises up the left gutter from the couple card, with a twig into each card. A "Stamouers" jump link at the top leads to the couple card, which sits below the children.
- It redraws on resize, on load, when the fonts finish loading, and through a `ResizeObserver`. With JavaScript off the page still reads correctly, without branches.

## Facts on the Page and Their Sources

- **Francois Villion:** a Huguenot from Clermont, France, who arrived at the Cape in 1671 ([Wikipedia][wikipedia-viljoen]). He married Cornelia Campenaar of Middelburg, Netherlands, at the Cape in 1676 ([hugenoot.org.za][hugenoot-viljoen]). They farmed near Stellenbosch.
- **The six children** ([Descendants of Francois Villion][oocities-descend], which shows baptism years only):
  - b1 Pieter: baptized Cape Town 1677-02-07, never married
  - b2 Anna: baptized Cape Town 1678-05-19, married 1691-12-09 Heinrich Venter
  - b3 Henning: baptized Cape Town 1682-05-19, married 1707 Margaretha de Savoye. She was the daughter of Jacques de Savoye and Marie Madeleine le Clercq, who arrived in 1688 on the Oosterland.
  - b4 Johannes: baptized Cape Town 1684-09-24, married 1708-08-14 Catharina Snyman
  - b5 Cornelia: baptized Stellenbosch 1686-10-13, married 1702 Hercule du Preez, then 1722 Christian Maasdorp
  - b6 Francina: baptized Stellenbosch 1689-04-24, married Jacob Cloete
- **Next generation**, not yet on the page: Henning b3c4 married Susanna Durand and had 12 children. Johannes b4c2 married Aletta Olivier and had 8 children.
- **Still to verify** against the Familiebond's Familieregister (4 volumes, about 2,000 pages): all of the above. That includes the claim that the Viljoen name was carried forward through Henning and Johannes.
- **MyHeritage and Geni** returned nothing to automated fetches, and their content has not been reviewed.

## Local Preview

Serve the directory with any static server, for example `python3 -m http.server 8765 --bind 127.0.0.1 --directory sites/viljoen.family`. A phone viewport (375px) shows no horizontal overflow and no console errors.

## Ideas Not Yet Done

- Self-hosted fonts instead of Google Fonts, for privacy and a shorter CSP.
- The c generation on the tree, starting with the Henning and Johannes lines, in place of the stubs.
- An Afrikaans version of the page, or a language toggle (headings already carry Afrikaans subtitles).
- A contact line or a Familiebond membership link in the footer.

<!-- Local files -->
[operations]: ../../OPERATIONS.md

<!-- External links -->
[hugenoot-crest]: https://hugenoot.org.za/Viljoen/crest.htm
[hugenoot-viljoen]: https://hugenoot.org.za/Viljoen/
[oocities-descend]: https://www.oocities.org/viljoen_family/descend.htm
[viljoen-familie]: https://hcv625.wixsite.com/viljoen
[wikipedia-viljoen]: https://en.wikipedia.org/wiki/Viljoen
