# Supplement feedback — 2026-10-04

The updated paired PDF/PNG files are copied into the single author-review collection at `../final_submission_candidate_20261002/`. No publication promotion is performed.

| Figure | Author-requested correction |
|---|---|
| S01 | Remove duplicate boxplot flier symbols; keep every station mean as the same scatter symbol. San Fernando had 13 values outside the 1.5-IQR whiskers, explaining its former hollow circles. |
| S02 | Remove the distribution already shown in Main Figure 3; retain the four spatial maps, their geometry and shared availability scale. Reletter A–D. |
| S03 | Use “Origins”; retain utility classification from the allocation table, reduce origin/station marker sizes, remove station/crew count qualifiers and N=92 on travel axes. |
| S04 | Use the full largest-connected-component fraction label. Bring the shared B/C legend close to those panels, match Main Figure 4 policy identity, and remove the repeated source-loss panel. |
| S06 | Remove the former C hazard-aggregate mapping panel from this review artwork. Reletter former D as C and explain the tract service-loss change caused by replacing the distance-based mapping. Keep the 337-tract agreement denominator and 246-over-1-h count. |
| S07 | Use plain probability labels; strengthen station color visibility and reduce background topology prominence. Keep linear scales, endpoints, probabilities and Core-source identities. |
| S08 | Put low-side voltage explanations in the legend. State the planning-bound comparison in B's title, axis and caption. All 34 provider loadings and four closed capacity increments are unchanged. |
| S13 | Replace only the repeated crew-count axis qualifier with “reference crews”, following the instruction to check other labels. |

All Main artwork, S05, S09 and the remaining unrequested supplementary artwork are preserved byte-for-byte. Earlier review sources, including the removed panels, remain intact. No scientific entrypoint is executed.

`OUTPUT_QA.csv` records native dimensions, minimum text size, font embedding and file hashes. `INPUT_AND_PRESERVATION_HASHES.json` records scientific and unchanged-artwork guards. `PLOT_PARITY.json` records displayed values/scale identity. Only the named presentation functions are called by `build_supplement_feedback.py`; it requires the existing `la_grid` src package on the Python import path.
