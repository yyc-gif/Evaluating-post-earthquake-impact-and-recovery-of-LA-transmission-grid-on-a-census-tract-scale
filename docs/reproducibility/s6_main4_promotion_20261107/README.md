# Figure S6 promotion verification

Source branch: `research/c1-mechanism-actionability-20261105`; source commit: `75cd19d4a0249d006efa00d4532762d0ee406c5a`.

Review branch: `review/s6-main4-20261107`.

The separate collection is `results/figure_review_s6_main4_20261107/`, with exact artwork mirrors under `results/figures_s6_main4_20261107/`. Existing artwork and all existing scientific results are retained unchanged. No archived file, source table or manuscript is edited. Figures are copied from verified pinned payloads, not redrawn from screenshots or reconstructed by rerunning simulations.

```powershell
python src/la_grid/plotting/build_s6_main4_review.py
python docs/reproducibility/s6_main4_promotion_20261107/verify.py
python -m pytest tests/test_s6_main4_promotion_20261107.py -q
```

`verify.py` checks exact rebuild hashes, original artwork preservation, per-panel pixel identity, fonts, figure bounds and packet ordering. It creates local-only visual previews, excluded from Git to avoid uploading redundant raster inspection files. Original/revised artwork copies use identical LFS payloads; only changed packets and text/metadata require new payloads.

The manuscript insertion and figure-reference edits are supplied separately because no editable manuscript is tracked in this checkout. See the collection's `PROMOTION_REPORT.md` and `MANUSCRIPT_INTEGRATION.md`.
