# viljoen.family

The single-page genealogy site for the Viljoen family, served at `viljoen.family` from the blog's release bundle. See [OPERATIONS.md][operations] "viljoen.family" for how it ships and which hostnames reach it. This file is not shipped.

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
| `crest.svg` | The full achievement (crest, helm, mantling, shield), hand-written SVG, viewBox 400x440 |
| `favicon.svg` | The shield alone |

Every file in this directory except this README ships to the bundle's `family/` tree.

## The Arms

The blazon, from the Viljoen Family Website crest page ([hugenoot.org.za][hugenoot-crest]):

- **Shield:** Gules, a saltire Or (a gold St Andrew's cross on red).
- **Mantling:** Or and Gules.
- **Crest:** a pair of eagle's wings folded Or.

The arms derive from the French family Villon de Varennes, whose crest was a golden mural crown. At the 1976 Viljoen Festival the Viljoen Familiebond voted to replace it with the golden wings. Wikipedia's image shows only the shield, helm, and mantling, with no crest, and captions the arms "unregistered". The page therefore describes them as the family's arms and makes no claim of official registration.

The drawing in `crest.svg` is an original rendering of that blazon:

- The helm is an esquire's closed helm in profile.
- The wreath has six twists, alternating Or and Gules.
- The mantling is one side (`#mantle`) mirrored with `translate(400,0) scale(-1,1)`.
- The wings are one wing (`#wing`) mirrored with `translate(404,0) scale(-1,1)`.
- The saltire is two stroked lines clipped to the shield. Darker 44px strokes under 38px gold strokes give the edge line and a clean crossing.
- The SVG carries no text. The "Viljoen" ribbon is HTML, so the name stays a real `<h1>`.

## Page Design

- **Palette:** parchment `#f4ead3`, cards `#fbf5e4`, red `#9e1b22`, gold `#b8862b`, bark `#5b3f27`, leaf `#6f7d3a`, all CSS variables in `:root`.
- **Fonts (Google Fonts):** IM Fell English SC for the name on the ribbon, Cormorant Garamond for headings, EB Garamond for body text.
- **Frame:** a 2.5px red border plus an inner 1px gold rule (`.frame::before`) with rounded corners and four gold corner flourishes (`#corner` symbol). A negative margin on the masthead equals the frame's top margin (128px, or 96px on phones). That puts the top border behind the mantling, so change both values together.
- **Paper texture:** an inline SVG `feTurbulence` noise data URI plus a radial vignette on `html`.
- **Divider:** a simplified Huguenot cross (a Maltese cross with fleur points, balls on the tips, and a hanging dove), the `#huguenot-cross` symbol.
- **CSP:** the policy in `deploy/Caddyfile` allows `'unsafe-inline'` for scripts and styles because both are inline. Moving them to `site.css` and `site.js` lets the policy drop it. Test in a browser after any CSP change, because a blocked script fails silently and the tree simply does not draw.
- **Browser support:** the page uses `color-mix()`. Older browsers lose some tints, and the layout is unaffected.

## How the Tree Is Drawn

The script at the bottom of `index.html` measures the ribbon, the couple card, and the child cards, then fills `svg.branches` inside `.tree`:

- Each limb is a cubic Bezier drawn as a filled shape that tapers from width `w0` to `w1` (`limb()`), not as a stroke.
- Leaves sprout at chosen positions along a limb, alternating sides (`leaves()`). The pattern is fixed rather than random, so every redraw looks the same. About one leaf in five is gold.
- **Wide layout** (six cards in a row): a trunk runs from the ribbon to the couple, then one S-curve branch runs to each child.
- **Stacked layout** (900px wide or less): the cards form a column. The script draws a stem down the left gutter, with a twig into each card.
- It redraws on resize, on load, when the fonts finish loading, and through a `ResizeObserver`. With JavaScript off the page still reads correctly, without branches.

## Facts on the Page and Their Sources

- **Francois Villion:** a Huguenot from Clermont, France, who arrived at the Cape in 1671 ([Wikipedia][wikipedia-viljoen]). He married Cornelia Campenaar of Middelburg, Netherlands, at the Cape in 1676 ([hugenoot.org.za][hugenoot-viljoen]). They farmed near Stellenbosch.
- **The six children** ([Descendants of Francois Villion][oocities-descend], which shows baptism years only):
  - b1 Pieter: baptised Cape Town 1677-02-07, never married
  - b2 Anna: baptised Cape Town 1678-05-19, married 1691-12-09 Heinrich Venter
  - b3 Henning: baptised Cape Town 1682-05-19, married 1707 Margaretha de Savoye. She was the daughter of Jacques de Savoye and Marie Madeleine le Clercq, who arrived in 1688 on the Oosterland.
  - b4 Johannes: baptised Cape Town 1684-09-24, married 1708-08-14 Catharina Snyman
  - b5 Cornelia: baptised Stellenbosch 1686-10-13, married 1702 Hercule du Preez, then 1722 Christian Maasdorp
  - b6 Francina: baptised Stellenbosch 1689-04-24, married Jacob Cloete
- **Next generation**, not yet on the page: Henning b3c4 married Susanna Durand and had 12 children. Johannes b4c2 married Aletta Olivier and had 8 children.
- **Still to verify** against the Familiebond's Familieregister (4 volumes, about 2,000 pages): all of the above. That includes the claim that the Viljoen name was carried forward through Henning and Johannes.
- **MyHeritage and Geni** returned nothing to automated fetches, and their content has not been reviewed.

## Local Preview

Serve the directory with any static server, for example `python3 -m http.server 8765 --bind 127.0.0.1 --directory sites/viljoen.family`. A phone viewport (375px) shows no horizontal overflow and no console errors.

## Ideas Not Yet Done

- A PNG render of the crest and a 1200x630 Open Graph image with `og:` meta tags, so shared links show the crest.
- Self-hosted fonts instead of Google Fonts, for privacy and a shorter CSP.
- A second generation on the tree, starting with the Henning and Johannes lines.
- An Afrikaans version of the page, or a language toggle (headings already carry Afrikaans subtitles).
- A contact line or a Familiebond membership link in the footer.
- `apple-touch-icon.png` (180x180), rendered from `favicon.svg`.

<!-- Local files -->
[operations]: ../../OPERATIONS.md

<!-- External links -->
[hugenoot-crest]: http://www.hugenoot.org.za/Viljoen/crest.htm
[hugenoot-viljoen]: http://www.hugenoot.org.za/Viljoen/
[oocities-descend]: https://www.oocities.org/viljoen_family/descend.htm
[wikipedia-viljoen]: https://en.wikipedia.org/wiki/Viljoen
