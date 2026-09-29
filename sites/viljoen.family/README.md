# viljoen.family

The single-page genealogy site for the Viljoen family, served at `viljoen.family` from the blog's release bundle. See [OPERATIONS.md][operations] "The Family Site" for how it ships and which hostnames reach it. [GENEALOGY.md][genealogy] holds the two lineage notations the page can render and the mapping between them. This file is not shipped.

## Contents

- [Contents](#contents)
- [Files](#files)
- [The Arms](#the-arms)
- [Page Design](#page-design)
- [How the Tree Is Drawn](#how-the-tree-is-drawn)
- [Facts on the Page and Their Sources](#facts-on-the-page-and-their-sources)
- [Languages](#languages)
- [Local Preview](#local-preview)
- [Ideas Not Yet Done](#ideas-not-yet-done)

## Files

| File | What it is |
| --- | --- |
| `index.html` | The English page, served at `/` and `/en/` |
| `af/index.html` | The Afrikaans page, served at `/af/` |
| `site.css` | The styles both pages share |
| `site.js` | The tree-drawing script both pages share |
| `crest.svg` | The full achievement (crest, helm, mantling, shield, name scroll), viewBox 336x418 |
| `favicon.svg` | The shield alone, cut from `crest.svg` |
| `apple-touch-icon.png` | 180x180, `favicon.svg` on parchment |
| `og-image.png` | 1200x630 Open Graph image, the crest beside the page title |

Every file in this directory except this README ships to the bundle's `family/` tree.

## The Arms

The blazon, from Prof. H.C. Viljoen's coat-of-arms page, which also records the Familiebond's 1976 vote on the crest ([hugenoot.org.za][hugenoot-crest]):

- **Shield:** Gules, a saltire Or (a gold St Andrew's cross on red).
- **Mantling:** Or and Gules.
- **Crest:** a pair of eagle's wings folded Or.

The arms derive from the French family Villon de Varennes, whose crest was a golden mural crown. At the 1976 Viljoen Festival the Viljoen Familiebond voted to replace it with the golden wings. Wikipedia's image shows only the shield, helm, and mantling, with no crest, and captions the arms "unregistered". The page therefore describes them as the family's arms and makes no claim of official registration.

`crest.svg` is a vector redrawing of the family's crest as Prof. Christo Viljoen shows it ([Viljoen Family Association][viljoen-familie]). The pair of folded wings is drawn in profile, so one wing shows. It matches that image's 336x418 size, so the two overlay directly for comparison.

- Each part is a named group: `mantling-gold`, `mantling-red`, `mantling-stems`, `mantling-joins`, `shield`, `helmet`, `wing`, `torse`, `name-scroll`, and `viljoen-lettering`.
- Each side of the mantling is one group mirrored with `translate(342 0) scale(-1 1)`.
- The saltire is one filled path clipped to `#shield-clip`, which is built from `#shield-outline`.
- The lettering is vector paths rather than `<text>`, so it renders the same without the font. The page's `<h1>` is visually hidden text, so the name stays a real heading.
- `favicon.svg` reuses the shield outline and saltire paths. `apple-touch-icon.png` and `og-image.png` are Chromium renders, and they carry no metadata chunks.

## Page Design

- **Palette:** parchment `#f4ead3`, cards `#fbf5e4`, red `#9e1b22`, gold `#b8862b`, bark `#5b3f27`, leaf `#6f7d3a`, all CSS variables in `:root`.
- **Fonts (Google Fonts):** Cormorant Garamond for headings, EB Garamond for body text.
- **Type scale:** the root size starts at the reader's default font size and grows with the viewport up to 125% of it, which at the usual 16px default is 16px at 1143px wide or less and 20px at about 2286px, and the frame, masthead, and couple card widths are in `rem`, so on a wide screen the whole page scales up rather than leaving the text small in a narrow column. No text sits below `1rem` except the "Viljoen line" badge, and the "c generation to follow" stub at `68.75em` wide or less, both `.95rem`. The stub wraps inside its column rather than spilling into the next one, since the column widths follow the viewport while the stub follows the reader's font size. Cormorant Garamond has a smaller x-height than EB Garamond, so its italic lines (the eyebrow, the section subtitles, and the footer) are set at `1.125rem`, above the `1rem` floor.
- **Frame:** a 2.5px red border plus an inner 1px gold rule (`.frame::before`) with rounded corners and four gold corner flourishes (`#corner` symbol). The frame's top margin and the masthead's negative margin both read `--crest-drop`, which puts the top border behind the mantling. Above the phone breakpoint it is `min(8rem, 29.36vw)`, the masthead width `min(21.25rem, 78vw)` scaled by 128/340. On phones it is `min(6rem, 22.02vw)`, the same width scaled by 96/340, so the border sits a little higher on the crest there. So on phones, and again on every wider window, the border meets the crest at one point whatever the width and font size.
- **Breakpoints:** all four are in `em`, so a reader with a larger default font gets each layout at a proportionally wider window, and the cards, stubs, and language link keep room for the larger text. At a 16px default font they are 1100px (`68.75em`, smaller stubs), 1000px (`62.5em`, stacked layout), 660px (`41.25em`, language link below the crest), and 520px (`32.5em`, phones).
- **Paper texture:** an inline SVG `feTurbulence` noise data URI plus a radial vignette on `html`.
- **Divider:** a simplified Huguenot cross (a Maltese cross with fleur points, balls on the tips, and a hanging dove), the `#huguenot-cross` symbol.
- **CSP:** the policy in `deploy/Caddyfile` allows only `'self'` for scripts, since the one script is `site.js`. Styles keep `'unsafe-inline'` for the `style` attributes and the `<style>` block the script writes into the tree's SVG. Test in a browser after any CSP change, because a blocked script fails silently and the tree simply does not draw.
- **Browser support:** the page uses `color-mix()`. Older browsers lose some tints, and the layout is unaffected.

## How the Tree Is Drawn

The tree is a stamboom. The children form the crown, and the stamouers card sits at the base of the trunk. Roots reach into a soil band labeled Clermont and Middelburg.

- **Markup:** the DOM is in genealogical order, as nested `<ol>`. `li.gen-a` holds the couple card, the soil band, and `ol.gen-b`, which has one `li` per child. CSS `order` puts the children above the couple, so the tree reads upward. The source and a screen reader still read from the progenitor down.
- **Name-carrying lines:** `li.line` marks b3 and b4. Their cards take the red border and "Viljoen line" badge, their limbs are thicker, and a "c generation to follow" stub continues each one.
- **Numbering and signs:** SAG de Villiers/Pama numbering (`a`, `b1` to `b6`, `b3c4`). The signs are `*` born, `~` baptized, `x` married (`x1`, `x2` for successive marriages), and a dagger for died. The `x` signs are plain letters, and the others are HTML entities. Each sits in an `aria-hidden` span inside `<abbr title>`. On the cards a visually hidden word stands in for the sign. The legend under the tree already spells each word out, so its signs carry no hidden word. Dates use the SAG `dd.mm.yyyy` form.
- **Living people:** none are published. Only people born before about 1925 are shown.

`site.js` measures the couple card, the soil band, the child cards, and the stubs, then fills `svg.branches` inside `.tree`:

- Each limb is a cubic Bezier drawn as a filled shape that tapers from width `w0` to `w1` (`limb()`), not as a stroke.
- Leaves sprout at chosen positions along a limb, alternating sides (`leaves()`). The pattern is fixed rather than random, so every redraw looks the same. About one leaf in five is gold.
- **Scale:** every width, offset, and leaf size is set for a 16px root and multiplied by the actual root size, and the fork gap, stub gap, soil band, and stacked gutter in `site.css` are in `rem`, so the tree keeps its proportions to the cards at any viewport and default font size.
- **Seamless joins:** all the wood is drawn twice, first as an outline layer and then as a fill layer on top, so overlapping pieces read as one shape with no line where they meet. The trunk's bark shading sits on top of that, masked out under a blurred copy of the branches, so it fades where each branch leaves the trunk instead of ending in an edge. Every branch starts inside the piece it grows from. In the wide layout the limbs also start pointing straight up, the way the trunk ends, so its sides run on into theirs.
- **Roots:** seven tapering roots fan out from under the middle of the couple card into the soil band, in both layouts. They start straight down within a 30px span (at a 16px root), the trunk's base width in the wide layout, so there the roots leave the card as the trunk continued.
- **Wide layout** (six cards in a row): a trunk rises from the couple card to a fork, where it ends pointing straight up, 24px wide at a 16px root. One S-curve limb rises from inside the trunk's top to the bottom of each child card, the starts spread across the trunk's width with the outer two flush with its sides. A short limb continues from each name-carrying card to its stub.
- **Stacked layout** (`62.5em` wide or less, 1000px at a 16px default font): the cards form a column, at most `32.875rem` wide so it widens with the reader's font size. The trunk rises up the left gutter from the couple card, with a twig into each card starting on the trunk's center line. A "Stamouers" jump link at the top leads to the couple card, which sits below the children.
- It redraws on resize, on load, when the fonts finish loading, and through a `ResizeObserver`. With JavaScript off the page still reads correctly, without branches.

## Facts on the Page and Their Sources

The Familiebond's pages are the source of truth. Prof. H.C. (Christo) Viljoen maintains them. He is the author of the Viljoen Familieregister (4th edition, 2021), which the Huguenot Society of South Africa publishes. Where another source differs, the page follows the Familiebond. [Wikipedia][wikipedia-viljoen], for example, gives the arrival as 1671.

- **Francois Vilion** ([Stamouers][viljoen-familie-stamouers]): of Clermont, France. He sailed from Texel as a VOC soldier on 1671-10-11 and reached Table Bay on 1672-02-14. He married Cornelia Campenaar of Middelburg, Netherlands, in Cape Town on 1676-05-17. From 1682 he farmed Idasvallei near Stellenbosch, where he died, probably in 1689.
- **The six children** ([Eerste geslagte][viljoen-familie-eerste-geslagte]):
  - b1 Pieter: baptized Cape Town 1677-02-07, never married
  - b2 Anna: baptized Cape Town 1678-05-19, married 1691-12-09 Heinrich Venter
  - b3 Henning: baptized Cape Town 1682-05-19, married 1707 Margaretha de Savoye. She was the daughter of Jacques de Savoye and Marie Madeleine le Clerq, who arrived in 1688 on the Oosterlandt.
  - b4 Johannes: baptized Cape Town 1684-09-24, married 1708-08-14 Catharina Snyman
  - b5 Cornelia: baptized Stellenbosch 1686-10-13, married 1702 Hercul&eacute; du Preez, then 1722 Christian Maasdorp
  - b6 Francina: baptized Stellenbosch 1689-04-24, married Jacob Cloete
- **The name** was carried forward only through Henning b3 and Johannes b4, each through one son of the same name, b3c4 and b4c2. It took its present spelling, Viljoen, in the second generation.
- **Next generation**, not yet on the page: Henning b3c4 married Susanna Durand on 1732-11-06 and had 12 children. Johannes b4c2 married Aletta Olivier on 1744-03-08 and had 8 children. The same page lists both families in full.
- **MyHeritage and Geni** returned nothing to automated fetches, and their content has not been reviewed.

## Languages

The page exists in English and Afrikaans, as two HTML files that share `site.css`, `site.js`, and every image.

- **Choosing the language.** Caddy redirects `/` to `/af/` when Afrikaans is the browser's first `Accept-Language`, and sends `Vary: Accept-Language`. The `/en/` and `/af/` addresses never redirect, so a visitor's choice holds.
- **The switch.** A link in the corner, or under the crest on phones, leads to the other language's explicit address. Both pages carry `hreflang` alternates and their own canonical URL.
- **Keeping them in step.** `af/index.html` is a translation of `index.html` with the same markup. A change to one page's structure goes into the other in the same commit. The CSS names the one string it carries, the "Viljoen line" badge, per language with `:lang(af)`.
- **Mixed text.** English left on the Afrikaans page, such as the section subtitles and the blazon, carries `lang="en"`.

## Local Preview

Serve the directory with any static server, for example `python3 -m http.server 8765 --bind 127.0.0.1 --directory sites/viljoen.family`. A phone viewport (375px) shows no horizontal overflow and no console errors. A static server serves `/af/` directly. The language redirect, the `/en/` address the Afrikaans switch links to, and the CSP need Caddy.

## Ideas Not Yet Done

- Self-hosted fonts instead of Google Fonts, for privacy and a shorter CSP.
- The c generation on the tree, starting with the Henning and Johannes lines, in place of the stubs.
- A contact line or a Familiebond membership link in the footer.

<!-- Local files -->
[genealogy]: ../../GENEALOGY.md
[operations]: ../../OPERATIONS.md

<!-- External links -->
[hugenoot-crest]: https://hugenoot.org.za/Viljoen/crest.htm
[viljoen-familie]: https://hcv625.wixsite.com/viljoen
[viljoen-familie-eerste-geslagte]: https://hcv625.wixsite.com/viljoen/eerste-geslagte
[viljoen-familie-stamouers]: https://hcv625.wixsite.com/viljoen/stamouers
[wikipedia-viljoen]: https://en.wikipedia.org/wiki/Viljoen
