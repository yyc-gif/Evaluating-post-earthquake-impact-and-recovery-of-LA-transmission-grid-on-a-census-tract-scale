# Figure 7 scientific layout review

**LAYOUT PROPOSAL — NOT APPROVED FOR CURRENT SUITE**

The package proposes restoring the previously approved analytical roles of A (distributions) and B (standardized multivariable profiles). It does not update the official Figure Suite, model, scientific Stage 7, or manuscript.

- `FIGURE7_AUTHOR_APPROVAL_DECISION.md`: bounded recommendation and outstanding design approvals.
- `FIGURE7_OLD_VS_NEW_INFORMATION_AUDIT.md`: actual artwork, source-code and authorization comparison.
- `FIGURE7_CONSERVATIVE_RESTORATION.pdf/.png`: the sole full layout candidate; native 185 x 253 mm, vector PDF/600 dpi PNG.
- `FIGURE7_OLD_CURRENT_CANDIDATE_NATIVE_COMPARISON.pdf`: three actual full pages, each at the same native 185-mm width.
- `FIGURE7_AB_PANEL_SIDE_BY_SIDE_REVIEW.pdf`: two enlarged comparison pages, A and B separately; each crop is 240 mm wide.
- `FIGURE7_NA_FILL_SEPARATE_APPROVAL_COMPARISON.pdf`: current gray and white-only N/A alternatives. Neither official artwork nor Candidate A is changed by this comparison.
- `FIGURE7_ORIGINAL_UNIT_AND_STANDARDIZED_DATA_QA.csv`, `PLOTTED_FROZEN_VALUES.csv`, `A_EMPIRICAL_DISTRIBUTION_POINTS.csv`: full-precision means/scaling, exact observations and empirical distribution points.
- `REPRODUCIBILITY_AND_PROTECTION_QA.json`: independent numerical/source-stream/render/preservation checks.

There is no Candidate B. A different layout was not shown to add information beyond the conservative restoration. The actual source PDFs under `inputs/` are byte-identical archives, not new approved proposals; their historical classes/hotspot content must not be mistaken for current output. Original frozen files may contain historical unused sensitivity fields; only K3 is read or shown in the candidate.

## Reproduce only this package

Use Python 3.12, the existing NumPy/Pandas/Matplotlib/PyMuPDF/Pillow dependencies, ReportLab for the shared source utility, Windows Arial fonts and the actual pinned Git LFS payloads. No model/simulation modules or current suite builder are invoked.

```powershell
python docs/data_research/figure7_scientific_layout_author_review_20261013/prepare_sources.py
python docs/data_research/figure7_scientific_layout_author_review_20261013/build_layout_review.py
python docs/data_research/figure7_scientific_layout_author_review_20261013/verify_layout_review.py
```

`prepare_sources` records the actual source/author worktree preservation baseline and therefore requires their declared local archive paths. A clean clone with actual source LFS bytes can run the plotting script from committed inputs and independently check its numerics; original-local-worktree preservation cannot be re-certified when that worktree is absent. Input identities are independently rechecked against the pinned commits, not just filenames. Git history for 59d9001, 8f2dcb3, 0c5365c and 05a7864 is required for source verification.

On this workstation, Anaconda Python is used with the bundled pure-Python ReportLab directory appended to `sys.path` before `runpy.run_path`. Appending preserves the existing compiled NumPy/GIS runtime. Long local Windows paths use `\\?\` for file access.

After review, stop here. Any production generator, caption, artwork, mirror or packet change requires a new explicit author instruction.
