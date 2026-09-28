# Writing Lineage

How the family site in [`sites/viljoen.family/`][family-site] writes a line of descent. It holds two notations, the South African one and an international one. Any agent or author adding people to the page renders them from this file.

The page renders one notation at a time, and it currently renders the South African one. Switching means re-rendering every person, the legend, and the numbering note from the mapping below. Nothing on the page is notation-neutral, so the switch is a full re-render rather than a CSS change.

## The Data Behind Every Person

Record these fields for a person before rendering them in either notation. They are the same in both notations, and only the way they are written differs.

| Field | Meaning | GEDCOM tag |
| --- | --- | --- |
| Lineage path | The birth-order position of each ancestor from the progenitor down, for example progenitor, 3rd child, 4th child | none |
| Given names, surname | As spelled in the source, including an older spelling such as Villion | `NAME` |
| Birth | Date, date precision, place | `BIRT` |
| Baptism | Date, date precision, place | `BAPM` or `CHR` |
| Marriage | Its order (first, second), spouse, date, place | `MARR` |
| Divorce | Date | `DIV` |
| Death | Date, date precision, place | `DEAT` |
| Burial | Date, place | `BURI` |
| Name-carrying | Whether the surname continues through this line | none |
| Source | Where each fact comes from, and whether it is verified against the Familieregister | `SOUR` |

Date precision is one of exact, year only, about, before, or after. Keep the data date in ISO form (`1682-05-19`), and let the notation decide how it displays.

## Rules Both Notations Share

- **Birth order.** Children are numbered in birth order, whatever their sex. Where only baptism dates are known, baptism order stands in for birth order.
- **No living people.** A line stops at people born before about 1925. A later person does not appear, even as a count.
- **Signs are accessible.** Each sign or abbreviation sits inside `<abbr title="...">`. The visible sign is `aria-hidden`, and a visually hidden word (class `vh`) follows it for screen readers. The legend spells each word out already, so its signs carry no hidden word.
- **ASCII source.** A non-ASCII sign is written as an HTML entity or a numeric reference, never as the literal character.
- **Unverified facts are marked.** A fact not yet checked against the Familiebond's Familieregister is still published, with the page note saying so.

## South African Notation (de Villiers/Pama)

This is the notation of the de Villiers/Pama *Geslagsregister van die ou Kaapse families* and the registers that follow it. Afrikaans-speaking genealogy uses it, so it is the one Viljoen readers recognize.

**Numbering.** Each generation takes the next letter, and each person a number for their birth order within their parents' children.

- The progenitor (stamvader) is `a`. His children are `b1`, `b2`, and so on.
- A grandchild appends a segment: `b3c4` is the fourth child of `b3`.
- A full path concatenates every segment, for example `b3c4d2`. It needs no separator, because each letter starts a new segment.
- Where one register holds several progenitors of the same surname, they are `a1`, `a2`, and so on. A path then starts with the progenitor's number, for example `a1b2c4`. The page has one progenitor, so it writes a bare `a`.

**Signs.**

| Event | Sign | HTML | Example |
| --- | --- | --- | --- |
| Born | `*` | `&ast;` | `* 19.05.1682` |
| Baptized | `~` | `&#126;` | `~ 19.05.1682 Cape Town` |
| Married | `x` | plain letter | `x 1707 Margaretha de Savoye` |
| Married, first and second | `x1`, `x2` | plain letters | `x1 1702 Hercule du Preez` |
| Died | dagger | `&dagger;` | `&dagger; 1720` |
| Buried | still to verify | | |

**Dates.** Dates take the form `dd.mm.yyyy`, for example `19.05.1682`. A year-only date is the bare year.

## International Notation

No single international standard exists. The conventions below are the ones English-language genealogy and the GEDCOM exchange format use most. Each one maps one to one onto the South African notation.

**Numbering: d'Aboville.** Each generation appends the child's birth-order number, separated by a period. The progenitor is `1`, and his third child is `1.3`. That child's fourth child is `1.3.4`. It maps segment for segment onto de Villiers/Pama, and a tenth child is simply `.10`.

Three other systems exist, and none of them suits a tree drawing:

- **Register (NEHGS) and NGSQ (Record)** are the two main styles for a printed descendant book. They number people consecutively through the book rather than by lineage path, so a number says nothing about where the person sits in the tree.
- **Henry** is d'Aboville without the periods, so it needs letter substitutes past the ninth child.
- **Ahnentafel** numbers ancestors rather than descendants (the subject is 1, a father is 2n, a mother 2n+1). It suits a pedigree chart, not this tree.

**Event abbreviations.**

| Event | Abbreviation | Example |
| --- | --- | --- |
| Born | `b.` | `b. 19 May 1682` |
| Baptized | `bp.` | `bp. 19 May 1682, Cape Town` |
| Married | `m.` | `m. 1707 Margaretha de Savoye` |
| Married, first and second | `m. (1)`, `m. (2)` | `m. (1) 1702 Hercule du Preez` |
| Divorced | `div.` | `div. 1730` |
| Died | `d.` | `d. 1720` |
| Buried | `bur.` | `bur. 1720, Stellenbosch` |

**Dates.** Dates take the GEDCOM display form, day, abbreviated month, and year: `19 May 1682`. A qualifier comes first: `abt. 1680`, `bef. 1700`, `aft. 1690`.

**Symbols, as an alternative to abbreviations.** Continental genealogy writes events as symbols, most of them in the Unicode Miscellaneous Symbols block. They suit a compact card, but a reader must learn them from the legend.

| Event | Code point | HTML |
| --- | --- | --- |
| Born | U+002A ASTERISK | `&ast;` |
| Baptized | U+007E TILDE | `&#126;` |
| Married | U+26AD MARRIAGE SYMBOL | `&#9901;` |
| Divorced | U+26AE DIVORCE SYMBOL | `&#9902;` |
| Died | U+2020 DAGGER | `&dagger;` |
| Buried | U+26B0 COFFIN | `&#9904;` |

Check these symbols against the page fonts before using them. Cormorant Garamond and EB Garamond may not carry the Miscellaneous Symbols glyphs, and a fallback font renders them at a different weight.

## Mapping Between the Notations

| Item | South African | International (d'Aboville, abbreviations) |
| --- | --- | --- |
| Progenitor | `a` | `1` |
| Third child | `b3` | `1.3` |
| Fourth child of the third child | `b3c4` | `1.3.4` |
| Second progenitor in one register | `a2` | `2` |
| Baptism | `~ 19.05.1682 Cape Town` | `bp. 19 May 1682, Cape Town` |
| Second marriage | `x2 1722 Christian Maasdorp` | `m. (2) 1722 Christian Maasdorp` |
| Death | `&dagger; 1720` | `d. 1720` |
| Year-only date | `1707` | `1707` |

A switch also changes three things on the page besides the cards:

- the legend under the tree,
- the numbering sentence in the tree note, which names the system,
- the `.code` labels, including the `a` on the couple card and the `c` on the stubs.

## Still to Verify

These South African details are not confirmed by any source this file cites. Check them against the Familieregister before relying on them:

- the sign for buried,
- whether the date punctuation is `dd.mm.yyyy` or `dd/mm/yyyy`,
- whether `x1` and `x2` are the register's form for successive marriages,
- what `sv` and `dv` abbreviate in the register, since one source reads `sv` as *seun van* (son of) and another as *stamvader*,
- the Afrikaans event words (*gebore*, *gedoop*, *getroud*, *oorlede*, *begrawe*), if the Afrikaans page uses words rather than signs.

## Sources

- [Genealogical numbering systems][wikipedia-numbering], which covers de Villiers/Pama, d'Aboville, Henry, Register, NGSQ, and Ahnentafel.
- [The de Villiers/Pama numbering system][legacy-pama], which covers the letter-and-number segments, birth order, and the `a1` form for several progenitors.
- [Genealogy symbols][tamura-symbols], which gives the Unicode code points for the continental symbols.
- [Genealogical abbreviations][myheritage-abbreviations], the English event abbreviations.
- [FamilySearch GEDCOM 7][gedcom7], the event tags and the date form.
- [Genealogie symbolen en afkortingen][wazamar-symbols], the Dutch sign set that Cape genealogy inherits.

<!-- Local files -->
[family-site]: ./sites/viljoen.family/

<!-- External links -->
[gedcom7]: https://gedcom.io/specifications/FamilySearchGEDCOMv7.html
[legacy-pama]: https://www.legacyfamilytree.se/WEB_US/de_villiers_pama_numbering_system.htm
[myheritage-abbreviations]: https://www.myheritage.com/wiki/Understanding_abbreviations_used_in_genealogy_records
[tamura-symbols]: https://www.tamurajones.net/GenealogySymbols.xhtml
[wazamar-symbols]: https://www.wazamar.org/genealogie-a-z/a-z/symb-afk.htm
[wikipedia-numbering]: https://en.wikipedia.org/wiki/Genealogical_numbering_systems
