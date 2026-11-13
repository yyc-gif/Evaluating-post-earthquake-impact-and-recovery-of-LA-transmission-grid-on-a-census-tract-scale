# Independent IJDRS five-main artwork

**Remote delivery warning:** GitHub rejected the binary upload because the repository exceeded its LFS budget. See [delivery status](DELIVERY_STATUS.md). The complete artwork is verified locally; a code-and-records-only remote tree is not the completed artwork package.

This configuration is aligned with the three contributions in Section 2.3 of the actual author-controlled `LA_Grid_Manuscript_Revised.docx`, not the obsolete submission draft. It preserves the full accepted eight-main/eight-supplement masters and does not edit either manuscript copy. The earlier five-main proposal in `results/publication_artwork_20261111/IJDRS/` is a separate historical export configuration, not this contribution-aligned selection.

## Five-figure narrative

| IJDRS figure | Accepted sources | Scientific message | Selection reason |
|---|---|---|---|
| 1 Analytical framework | Master 1; verified compact spacing variant | Five-stage methodology and event-based repair/service updating | Keep the accepted methodological overview without adding more numbered methods figures. Only the two figure-pointer labels change. |
| 2 Damage-to-service mechanisms and baseline recovery | Master 3B/C/E and master 4's focal dynamic A/B charts | Physical-functionality, threshold and source-path contributions; spatial baseline recovery; alternative-route support | Direct contribution-1 evidence. Explicit decomposition and dynamic network support are both retained, rather than treating network methods alone as novelty. |
| 3 Restoration performance and distributional trade-offs | Master 5B; master 6B/C/D | Absolute performance, all Q1-Q4 groups, hospital-linked outcomes, signed and absolute disparities, and Gini | Direct contribution-2 evidence; targeted Q4 improvement is not made equivalent to lower overall burden or reduced disparity. Four outcome panels replace two complete stacked source figures. |
| 4 Resource dependence | Master 7, all eight panels | How crew and repair-duration conditions alter paired strategy effects | Resource dependence is a central contribution, not demoted as a generic sensitivity check. All four outcomes and their uncertainty conventions remain. |
| 5 Community recovery types and social vulnerability | Master 8, all four panels | Seven-coordinate fitted profiles and direct tract-level vulnerability/burden geography | Direct contribution-3 evidence. Retain class information, geography and the non-composite descriptive screen together. |

## Files

- [Individual main and proposed supplementary PDF/PNG/TIFF files](INDIVIDUAL_FIGURES.md).
- [Five-main review packet](ALL_MAIN_FIGURES_WITH_CAPTIONS.pdf), [proposed supplementary packet](ALL_SUPPLEMENT_PROPOSED_WITH_CAPTIONS.pdf), and [complete independent configuration](ALL_FIGURES_WITH_CAPTIONS.pdf).
- [Five main captions only](MAIN_CAPTIONS.md), [proposed supplementary captions](SUPPLEMENTARY_CAPTIONS.md), [panel crosswalk](FIGURE_PANEL_CROSSWALK.json), and [paragraph-level Section 4 editing plan](SECTION4_EDITING_PLAN.md). `CAPTIONS.md` is the combined caption source used by the builder, not a competing text version.
- `FIGURE_MANIFEST.json` binds actual output dimensions, hashes, typography and TIFF checks. `qa/ASSEMBLY_REGISTRY.json` records exact source and target rectangles. No image is approximated from a screenshot.
- [Scientific and actual-size visual review](qa/FINAL_VISUAL_QA.md) and [preservation boundaries](qa/PRESERVATION.md) describe the final inspection and remaining journal/placement limitations.

## Supplementary proposal

Thirteen numbered supplementary artworks preserve the reconstruction support, omitted baseline distributions, complete source-connectivity diagnostics, temporal policy curves, spatial redistribution and all eight original supplements. Only the two focal dynamic source-connectivity charts are deliberately repeated in the complete diagnostic figure, so the full focal/other-policy comparison and both station maps remain interpretable together. No panel is silently dropped. This is a proposal, not an assertion that IJDRS permits thirteen supplements.

The existing [aligned single-variable vulnerability/burden reference](../../publication_artwork_20261111/universal/accessibility/aligned_sovi_deficit.pdf) remains available as unnumbered accessibility support. Figure 5's bivariate hue/lightness map cannot preserve both variables independently in grayscale; it is not advertised as universally color-vision accessible.

## Reproduction

```powershell
python src/la_grid/plotting/build_ijdrs_five_figure.py
python -m pytest tests/test_ijdrs_five_figure_20261112.py -q
```

The default manuscript location is the verified Downloads copy. `--manuscript` may point to an identical copy; the hash guard rejects a different revision rather than silently reusing paragraph anchors. `--force` rebuilds the derivative artwork from the frozen vectors. No simulation, scheduling, uncertainty estimation, optimization or clustering code is invoked.

For collaborators without that private local DOCX, `--artwork-only` reproduces the figures using the registered manuscript review and paragraph plan. It explicitly does **not** claim to recheck alignment with a newer or unavailable Word file. No manuscript copy is included just to make artwork reproduction possible.

Use the pinned environment in `results/publication_artwork_20261111/requirements-artwork.txt` and Poppler 26.07.0 (`pdftoppm`). The compact vector input and accepted artwork are Git LFS payloads and must be hydrated. The inherited placement helper is bound by SHA256 in the source registry; it uses the pinned PyMuPDF API. Unchanged derivative files are reused only when their PDF, PNG, TIFF and preview hashes match, avoiding needless conversion and uploads.

## Approval boundary

This is an artwork configuration and manuscript-editing plan, not a submission-ready Word manuscript. Section 4 contains both obsolete references and substantive interpretation issues; the latter require author review, not a global number replacement. Main-figure choice, proposed supplementary packaging, current portal restrictions and final placement remain author/editorial gates. Original scientific findings and the three contribution statements are not rewritten here.
