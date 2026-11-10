# Figure 1 Module 4 and Compact S5 Correction

This record documents a presentation-only correction on `review/fig1-moduleD-s5-final-20261109`.

Figure 1 reuses the authentic workflow-generated vector PDF and its matched PNG from commit `ea692f4dd6d1763a91b4b8f5c11e45ce6a8a1f15`. The source is the saved `2pc50` population-weighted recovery-curve table, not an illustrative redraw. The generation audit and exact source hashes are in `results/figure_review_s6_main4_20261107/QA/NUMERICAL_AND_PRESERVATION_QA.json` and `QA/SOURCE_IDENTITIES.json`.

Supplementary Figure S5 is 185 x 145 mm. Its three panels, four restoration strategies, saved means and paired 5th-95th percentile ranges are retained. The complete visible composition, including strategy labels, axes, titles and legends, is centered.

## Files

- `FIGURE1_S5_CORRECTION_REPORT.md` records the source decision, visual review, dimensions and test scope.
- `ARTWORK_BASELINE_COMPARISON.csv` compares all 32 numbered PDF/PNG files with the starting branch commit.
- `INDEPENDENT_FIGURE_QA.json` records hashes, numerical checks, layout measurements and packet counts.
- `FIRST_CANONICAL_BUILD_HASHES.json` is the deterministic-rebuild baseline.
- `verify_fig1_s5_delivery.py` independently verifies frozen inputs, output identity, S5 composition, mirrors and packets.

The source CSV and saved workflow artwork are manifest-bound Git LFS dependencies. A clean clone must fetch their actual LFS payloads before running the verifier. No recovery model, simulation, schedule, or manuscript was changed.

## Reproduction

```powershell
python src/la_grid/plotting/build_s6_main4_review.py
python docs/reproducibility/figure1_workflow_curves_compact_s5_20261109/verify_fig1_s5_delivery.py --snapshot
python src/la_grid/plotting/build_s6_main4_review.py
python docs/reproducibility/figure1_workflow_curves_compact_s5_20261109/verify_fig1_s5_delivery.py --verify-rebuild
python -m pytest tests/test_s6_main4_promotion_20261107.py -q
python -m pytest tests/test_current_figure_suite_integration.py::test_figure1_builder_reuses_the_saved_workflow_output -q
```
