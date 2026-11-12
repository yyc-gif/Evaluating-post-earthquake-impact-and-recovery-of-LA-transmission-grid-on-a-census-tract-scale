# Artwork preparation completed; submission certification remains gated

Source: `review/fig1-moduleD-s5-final-20261109`, commit `68c83459e60ef31f7e86af9155d5a11e1680235d`. Delivery branch: `review/publication-masters-ijdrs-20261111`. The source branch and its complete eight-main/eight-supplement collection are not overwritten or renumbered.

## Delivered

- [All sixteen individual PDF/PNG/TIFF links](universal/INDIVIDUAL_FIGURES.md), [journal-neutral captions](universal/CAPTIONS.md), stable identities and source hashes in [MASTERS.json](universal/MASTERS.json).
- Fifteen exact-appearance optimized PDFs, with the already-small S5 referenced unchanged. Total preferred PDF bytes fall from 105,372,855 to 84,548,279 (19.76%). Original complete-resource PDFs and all original PNGs remain available.
- Figure 1: original 37,843,115 bytes / 185 x 265.29 mm; exact-appearance delivery 35,576,209 bytes; [compact vector variant](universal/layout_variants/workflow_compact.pdf) / [600-dpi PNG](universal/layout_variants/workflow_compact.png), 185 x 237.35 mm, minimum text 7.5 pt. GIS Form streams, not raster images, dominate the original bytes. No image recompression or geometry simplification is used.
- Separate IJDRS candidate: [five-main packet](IJDRS/MAIN_WITH_CAPTIONS.pdf), [eleven-artwork supplement proposal](IJDRS/SUPPLEMENT_PROPOSAL_WITH_CAPTIONS.pdf), sixteen caption-free 600-dpi TIFFs, [captions](IJDRS/CAPTIONS.md) and [reference crosswalk](IJDRS/FIGURE_REFERENCE_CROSSWALK.json).
- [Sixteen-figure preflight](PREFLIGHT_SUMMARY.md), [measured placement/font records](qa/PLACEMENT_METRICS.json), [actual visual inspection](qa/FINAL_VISUAL_INSPECTION.md), [accessibility review](qa/ACCESSIBILITY_REVIEW.pdf), single-variable companion and [portable export configurations](EXPORT_PROFILES.json).

## Scientific/editorial judgment

The five-main proposal uses original masters 1, 3, 4, 5 and 6: workflow, damage-to-service context, network/source mechanism, strategy performance and distributional effects. All four source-connectivity panels remain. The other three main figures and eight supplements are retained in the eleven-artwork proposal, not deleted.

This selection is conditional on that being the paper's main argument. If GA improvement is a headline contribution, the actual held-out GA evaluation (original S4) deserves a main slot; seek editorial permission rather than implying that the workflow is performance evidence. The same applies to resource sensitivity if it becomes central. The full eight-main collection remains available for a permission request or another journal.

## Submission gates

The currently linked official IJDRS instructions specify five figures and three tables without special permission, TIFF/JPEG and at least 300 dpi. The submission portal returned 403, so current upload limits, final placement dimensions, color rules and acceptance/count of supplementary files are not certified. Eleven supplemental figures are a proposal, not an entitlement. The available older manuscript has five numbered scientific tables but is not the current submission authority; no table or manuscript was edited.

Existing 7-7.5-pt details must not be blindly reduced. Grayscale does not preserve the full bivariate information. No approved SVG/EPS is claimed: the SVG conversion failed its declared appearance gate. These are explicit portability limits, not hidden by a DPI tag or a successful command.

## Verification and preservation

Seventeen focused tests pass. Fresh packet/TIFF/review regeneration and hash-checked reuse are documented in `qa/REBUILD_QA.json`. All thirty-two original numbered PDF/PNG payloads match the starting authority. No simulation, scheduling, GA, clustering, formal Stage 7 or manuscript operation was run.

Historical protection scope is explicit in `qa/PRESERVATION_SCOPE.json`: 482 of the old 950 listed paths exist in this baseline Git tree, with only 42 materialized payloads. The other 468 were already absent from the baseline. This task preserves existing Git identities and does not falsely claim a new complete 950-payload audit.

Remote delivery is complete only when `qa/REMOTE_DELIVERY.json` records actual LFS payload downloads and the delivery receipt records matching local/remote branch heads. No merge or force-push is authorized.

## Reproduction

Use the pinned `requirements-artwork.txt` environment and hydrate the thirty-two accepted Main/Supplement artwork inputs, not all historical scientific LFS archives. Run:

```powershell
python src/la_grid/plotting/publication_artwork.py build
python -m pytest tests/test_publication_artwork_20261111.py -q
```

The export layer reads saved artwork and source registries only. It does not call the scientific pipeline. On-demand raster size/resolution examples and format cautions are in the README and `OTHER_JOURNAL_EXPORTS.md`.
