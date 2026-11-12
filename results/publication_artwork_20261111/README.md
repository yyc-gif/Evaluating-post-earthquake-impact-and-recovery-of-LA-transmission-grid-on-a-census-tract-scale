# Universal artwork and IJDRS submission candidate

Primary target confirmed by the author on 2026-11-11: **International Journal of Disaster Risk Science (IJDRS), Springer Nature**. This supersedes the earlier working IJDRR assumption; the two journals are not interchangeable.

## One scientific authority, separate delivery layers

- The accepted eight-main/eight-supplement collection remains unchanged at `results/figure_review_s6_main4_20261107/`, commit `68c83459e60ef31f7e86af9155d5a11e1680235d`. Its original PDFs, PNGs, captions and scientific sources are not overwritten.
- `universal/MASTERS.json` assigns stable scientific identities, records accepted-source hashes and points to exact-appearance optimized PDFs where worthwhile. The complete original resources and generating code remain available for editing; font-subset delivery PDFs are not a substitute for those originals.
- `universal/layout_variants/workflow_compact.pdf` is a scientifically equivalent spacing variant, not an automatic replacement of the accepted workflow. Its graphics are translated, not scaled. Small 7-pt labels are raised to 7.5 pt using the already embedded Arial font.
- `IJDRS/` contains a five-main-figure candidate, eleven proposed supplementary artworks, separate captions, a reference crosswalk and 600-dpi RGB TIFFs. Supplementary acceptance and current portal restrictions are **not certified**. No manuscript references or tables are changed in place.
- `universal/accessibility/aligned_sovi_deficit.pdf` restores the existing unnumbered, single-variable map reference from verified Git history. It is not a seventeenth numbered master figure.

No unnecessary copies of the sixteen existing PDF/PNG pairs are made. Registry links are repository-relative. The IJDRS TIFFs are one real raster derivative per scientific figure, not renamed PNGs. Existing high-resolution PNGs remain the review/sharing copies. EPS is not fabricated; conversion support and transparency/font behavior must be checked before an EPS-only submission. The optional path-based SVG trial failed its appearance round-trip gate and is not delivered as production artwork. Original vector PDFs and generating code remain available.

Open the [individual-figure index](universal/INDIVIDUAL_FIGURES.md) for every master PDF, caption-free PNG and IJDRS TIFF. Original complete-resource PDFs are the editing authority; the registry also identifies optimized delivery alternatives when available.

The [shared terminology key](universal/TERMINOLOGY.md) explains scenario identifiers and distinguishes service availability, integrated deficit, T80 and the two uncertainty conventions.

The complete accepted eight-main/eight-supplement reading collections remain available without redundant reuploads: [main figures](../figure_review_s6_main4_20261107/ALL_MAIN_FIGURES.pdf), [supplementary figures](../figure_review_s6_main4_20261107/ALL_SUPPLEMENT_FIGURES.pdf), and [all sixteen with accepted captions](../figure_review_s6_main4_20261107/ALL_FIGURES_WITH_CAPTIONS.pdf). The new journal-neutral caption file only expands necessary definitions; the IJDRS five-main and proposed-supplement packets use those definitions and their separate reference crosswalk.

## Reproduction

Requirements are listed in `requirements-artwork.txt`. These operations read saved artwork only; they do not import or run earthquake, restoration, optimization or clustering models.

```powershell
python src/la_grid/plotting/publication_artwork.py build
python -m pytest tests/test_publication_artwork_20261111.py -q
```

The accepted scientific figure builder remains separate. This export layer does not rerun it or route it to a reduced figure set.

On-demand examples:

```powershell
python src/la_grid/plotting/publication_artwork.py export --identity strategy_performance --format tiff --dpi 1200 --output results/publication_artwork_20261111/tmp/strategy_1200.tif
python src/la_grid/plotting/publication_artwork.py export --identity strategy_performance --format png --dpi 600 --width-mm 174 --output results/publication_artwork_20261111/tmp/strategy_174mm.png
```

The exporter rejects an automatic reduction below 7-pt effective lettering. That guard is a project readability choice, not an invented IJDRS rule. A single-column reduction of a dense double-column master usually requires a new layout, not a higher DPI. JPEG and CMYK are not automatic fallbacks for scientific linework.

## Review records

- `ARTWORK_STANDARD.md`: journal-neutral design and conversion rules.
- `JOURNAL_COMPLIANCE.md`: verified requirements, general advice and unresolved gates.
- `IJDRS/EDITORIAL_CONFIGURATION.md`: scientific selection and permission alternatives.
- `qa/OBJECT_PREFLIGHT.json`: dimensions, stored PDF-object contributions, fonts and raster resolution.
- `qa/COMPACT_LAYOUT_QA.json`: measured whitespace removal and unscaled retained graphics.
- `qa/ACCESSIBILITY_REVIEW.pdf`: native-width grayscale and selected color-vision simulations; review-only raster previews, not production masters.
- `PREFLIGHT_SUMMARY.md`: the final sixteen-figure technical table and practical actions.

All scientific findings, saved repair events, maps, memberships, vulnerability definitions and original research files are preserved. Journal-specific numbering exists only in the derived candidate configuration.
