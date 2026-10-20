# Supplement corrections requested by the author

Source artwork commit: `5bf3a86314eb0e028727b29382364a73ed773579`.

The current author packet contains 7 main figures and 12 supplement figures (S01 and S03–S13). S02's spatial service maps are incorporated into S01, not discarded. Existing numbering is retained for the other figures.

| Figure | Correction | Scope |
|---|---|---|
| S01/S02 | One combined figure: A station damage severity; B the four initial tract-service maps with a common scale | Native panels at their original physical size; station damage is distinct from tract service |
| S06 | Remove the entire old tract-level two-mapping difference panel; retain cutoff and SCE-record support; add service-requirement and functionality-threshold sensitivities | Saved formal summary rows only; one production mapping |
| S07 | Circular station marker diameter reduced to 80% | Station coordinates, network edges, colors, values and Core-source triangles unchanged |
| S08 | A/B headings use Arial Bold 9.5 pt; shorten the excess gap below B's heading | Planning and capacity-domain numbers unchanged |
| S09 | Align upper-panel axes/titles; locate the C1–C5 cluster key over A only | PCA, cluster membership, palette and numerical diagnostics unchanged |
| S12/S13 | Verify matching A/B/C/D metric titles, fonts and scenario coding | Artwork bytes unchanged; separate crew and duration scenario families |

## Why the sensitivities remain separate

S06 covers mapping support and the assumptions that turn station functionality into modeled service. S12 and S13 cover different, one-factor restoration-resource scenario families. Combining all three would mix external mapping evidence with workload/logistics effects and crowd the figure. Capacity/planning evidence remains in S08.

S06 B retains the distance-based benchmark only as an external comparison on 337 tracts; it is not a second production mapping. The deleted CDF of differences between two mappings is retained only in historical artwork, outside the author collection.

## Exact S06 C/D source selection

For each of Impact-first, Hospital-first and Degree-first, read:

`Formal_Experiment_20260923/Formal_Offline_Evaluation/2pc50__C57_D1__<policy>__SUMMARY.parquet`.

Filter `mapping=M1_UTILITY_003` and `comparison_domain=mapping_native_domain`. There are exactly 1,000 realization IDs for each gate. Read the existing population-weighted service-loss field `population_weighted_normalized_burden_hr`; do not invoke the offline evaluation module.

- C: `G0_NO_GATE − G1_BASELINE_050`. G0 removes **both** the functionality threshold and source-connectivity requirements; it is not a source-only relaxation at threshold 0.5.
- D: `G2_RELAXED_005 − G1_BASELINE_050` and `G3_STRICT_075 − G1_BASELINE_050`, with the same 14 Core sources.
- Display mean within-realization differences and their 5th–95th realization ranges. These are not bootstrap confidence intervals. Integrals cover 0–480 h.
- Vulnerability-first does not have this saved formal gate grid. It is not added by a new evaluation or by borrowing another policy's values.

The accompanying JSON records every displayed mean/range, sample count, table path and SHA-256. All scientific tables, physical samples, schedules and trajectory archives are read-only.

## Visual checks

The actual native PDFs and rendered page images for S01, S06–S09, S12 and S13 were opened. New artwork remains 185 mm wide; minimum text is at least 7 pt and fonts are embedded Arial subsets. S01's four maps keep the same scale and geographic extent. S08 A and B have the same actual title font and size. S09's upper axes and title baselines align; the compact cluster key is confined to A's column. S12 and S13 already have identical parallel metric wording and legible panel spacing, so they were not redrawn.

Earlier source files are preserved under `provenance/figure_review_history/supplement_before_20261006/`. The exact current author files, publication copies, captions, inventory, gallery and complete packet are synchronized.
