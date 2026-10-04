# Hospital/resource author-feedback audit — 2026-10-04

## Scope and changes

Only author-review Figure 6 and Supplementary Figures S10/S12/S13, their paired PNGs, captions, source manifest and aggregate review PDFs are updated. Historical artwork remains at its original source paths. `results/figures/` is untouched; this is not promotion.

- S10: removed the numbered circles and the repeated hospital-outcome boxplot. The first five stations in the existing Hospital-first sequence are teal and have leader lines to their actual station names. No ranking is recalculated.
- Duplicate check: former S10B and Main Fig04B both use `hospital_mean_normalized_burden_hr` for 2pc50 / C57_D1 / M1_UTILITY_003 / G1_BASELINE_050. S10 used four-policy 1.5-IQR boxplots; Main uses all-policy 5–95 realization ranges. The outcome, source and condition are the same; only its representation differed. S10 now explains policy construction alone. Main Fig04 retains the baseline policy-outcome comparison.
- Main Fig06: retained the existing Q4, population-weighted and absolute Q4–Q1 matched contrasts, and added the hospital-linked tract mean. The two columns separate crew availability and repair duration. All four outcomes retain real hour scales, zero lines, and the same scale across the two scenario families. References remain gray-circle Hospital-first, orange-square Impact-first and open-green-triangle Degree-first. These are policy contrasts, not absolute-outcome sensitivity ranges.
- S12/S13: retained all eight scheduled policies and all four tested levels. Both use the same four absolute outcomes, core-policy emphasis, marker/color identities and 5–95 realization-range definition. Crew levels are labeled as reference-relative multipliers (0.51, 1.00, 1.51, 2.00); duration levels are 0.75, 1.00, 1.25, 1.50. No crew/station counts appear in plot titles, legends or axes. Exact condition identities remain in captions/source tables.

## Numerical/provenance checks

All 63 existing Fig06 contrast rows are reused exactly. Fourteen hospital-linked mean/CI rows are copied from the existing Vulnerability pairwise/resource tables. Seven Degree-first hospital-linked means are display differences of the saved, matched 1,000-realization outcome rows; corresponding confidence intervals are absent, explicitly not drawn, and no bootstrap is performed. A missing interval is not interpreted as zero uncertainty. The existing three Degree metrics keep their already-saved intervals.

S12/S13 retain the same source realization sets and metric definitions. Means and 5th/95th percentiles are plot summaries of existing output records, not newly generated damage/recovery results. Each condition/policy contains exactly 1,000 saved realizations; all 56 distinct condition/policy groups are present. Tables under this derivative folder record every display coordinate and source field.

## Actual artwork inspection

Native PDF-rendered previews and labels were opened for all four updated figures. S10 station labels have no overlap with one another; leader lines identify the corresponding teal dots. The legend is outside the map. Fig06 zero lines, tick units, family columns and hospital panels are visible at native width. S12/S13 keep all strategies, separate interval marks horizontally, and have legends outside the data region. A native PDF crop additionally confirmed all four duration tick labels when a resized preview appeared to omit digits.

All four PDFs are 185 mm wide, use embedded Arial/Arial Bold, have no off-page text, and have minimum text sizes 7.0 pt (Fig06) or 7.5 pt (S10/S12/S13). PNG previews are exported at 600 dpi without modifying source geometry or plot data. Fig06 is 224 mm high, S10 126 mm, S12/S13 180 mm.

## Preservation

`BEFORE_HASH_GUARD.json` protects 31 scientific-source files, all 33 current publication files and the other 32 individual review artwork files. All match after rendering. `READ_INPUT_HASHES.json` identifies the exact read-only plotting inputs. No sampling, scheduling, dispatch, GA, trajectory evaluation, clustering, capacity computation or bootstrap entrypoint is called. Scientific source hash changes = 0; publication hash changes = 0; other review-artwork hash changes = 0. Unrelated staging is separately guarded.

## Distinct evidence roles

- Main Fig04: baseline outcomes across all policies.
- S10: Hospital-first target construction and identifiable priority stations.
- Main Fig06: how matched policy contrasts differ across tested crew/duration conditions, covering all four requested outcome classes.
- S12/S13: full-policy absolute outcome distributions across all tested crew/duration conditions; these retain strategies absent from Main Fig06 references.

No universal monotonic scarcity claim, continuous response curve, interpolation, crew×duration interaction, hospital electricity-delivery inference or clinical-capacity interpretation is introduced.

## Validation results

- `python -m pytest`: 49/49 passed.
- `git diff --check`: passed.
- Canonical resume: Stages 01–09 passed validation/reuse. Stage 10 stopped on the pre-existing publication S03/source-authority mismatch (`results/figures/FigS03_Crew_Bases_and_Directed_Travel.pdf` versus its indexed historical source). This mismatch also preceded this round and concerns neither the updated review S10/S12/S13 nor review Main Fig06. It is not concealed or repaired by modifying the protected publication collection.
- Protected July archive ref remains `182686868cffe962739804f6bc0ccecaed73d601`.
- All 40 individual review PDF/PNG hashes match their manifest; the complete caption packet contains 20 figure pages followed by their 20 caption pages.
