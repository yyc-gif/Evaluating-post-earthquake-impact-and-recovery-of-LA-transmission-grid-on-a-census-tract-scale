# Final visual acceptance, 2026-11-12

## Inspection actually performed

- Inspected all sixteen accepted native-width PDF previews individually and all sixteen actual TIFF derivatives at native-width preview size. The latter are caption-free, genuine 600-dpi RGB/LZW files.
- Independently rendered the original, optimized and compact Figure 1 with Poppler 26.07.0 at 150 dpi. The original and exact-appearance optimized PDFs are pixel-identical in that independent renderer as well.
- Rendered every page of the five-main and eleven-proposed-supplement packets with Poppler. Inspected all sixteen caption regions and whole-page main 1/main 5/proposed S3/S10 compositions, in addition to the individual artwork inspections. No cut-off caption, missing symbol or overlapping caption/artwork was observed.
- Inspected native grayscale and severity-100 protan/deutan/tritan simulations for the strategy and community figures; the complete twenty-two-page accessibility review includes all sixteen grayscale pages.
- Inspected Figure 1 at 185, 174 and 85 mm. The 85-mm reduction is not usable; 174 mm remains small and is not a declaration of Springer compliance.

## Figure 1

The five stages and all scientific content remain. Compact dimensions are 185 x 237.35 mm rather than 185 x 265.29 mm. Maps, crew bars and recorded event states are translated, not scaled. Ten 7-pt labels become 7.5 pt. All five priority markers, five crew rows, time ticks, travel/repair legend and the event-state update are readable in the full-width render. Actual travel intervals are genuinely short relative to repair intervals; they are not artificially enlarged.

The strip builder conservatively omits 1,151 outside-strip Form calls and 1,227 unused XObject references. It does not simplify GIS leaf paths. Decimal unit transforms prevent unintended scale changes. The initial whole-page-per-strip approach had excessive rendering memory and was superseded, not delivered as an accepted implementation.

The compact reflow is **not** described as pixel-identical to the differently arranged original. Its universal version has 10,422 changed non-typographic pixels among 24,403,293 compared pixels (0.0427%), confined to original edge neighborhoods/quantization. Maximum RGB-channel difference is 25/255 and mean absolute RGB difference is 0.001582/255. Exact geometry transforms and source text preservation accompany that bounded antialiasing check. The fifteen retained lossless delivery PDFs, by contrast, pass exact 150/600-dpi appearance checks.

The compact PDF is 38,531,711 bytes: it solves vertical layout, not file size. The exact-appearance full-height delivery PDF is 35,576,209 bytes. Both roles are explicit; no arbitrary 10-MB goal is imposed.

## Remaining production cautions

The original Figure 8 population tick boxes do not overlap: the 12,000 label ends at x=462.341 pt and 14,000 begins at x=465.531 pt, leaving 3.190 pt. It was retained rather than altered on the basis of a rescaled screen impression.

The bivariate map loses an independent color dimension in grayscale. Class maps and overlapping policy curves are not universally distinguishable under all simulations. Printed profile values, ECDF line styles, named outcome rows, the aligned single-variable reference and accessible descriptions remain important. A grayscale-only journal needs a specific adaptation, not a claim that the current palette solves every condition.

Native details elsewhere are 7-7.5 pt; some figures are tall (notably original S7 at 264 mm). Final placement, color-production policy and journal-specific page constraints must be confirmed. No unsupported maximum height, byte limit or ESM allowance is invented. The SVG trial exceeded its round-trip limits and is excluded from production delivery; PDF and TIFF remain the validated choices.

The compact centered S5 remains exactly the accepted 185 x 145 mm source. No numerical result, map membership, repair event or scientific source was changed.
