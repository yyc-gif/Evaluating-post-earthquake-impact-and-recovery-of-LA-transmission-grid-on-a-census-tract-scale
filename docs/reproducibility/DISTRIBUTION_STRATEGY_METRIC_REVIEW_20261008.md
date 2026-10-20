# Distribution, strategy visibility and metric review - 2026-10-08

Base: `34e93cae76fb3c229909b4044b761d88265bfc18`, revision/reviewer-driven-core-rebuild-v2.

| Artwork | Implemented correction | Evidence retained |
|---|---|---|
| S01 | Violin density, median, interquartile segment and observed range replace the station point cloud. | Exactly 92 station-average damage-state values per scenario; no new damage draws. Initial-service maps remain identical. |
| Fig04 | Two adjacent, identically scaled recovery views separate four focal policies from the four other scheduled policies. Solid, fully visible curves replace near-transparent overplotting. | All eight scheduled policies; the same Unconstrained reference in both views. Lower outcome panels remain identical. |
| S04 | Dynamic largest-component fraction and within-component mean degree use the same policy separation as Fig04. Grouped legend uses the same actual curve colors. | All eight policies and Unconstrained; static node-removal panel unchanged. |
| S10 | Three equally scaled EPSG:3310 maps replace equal-aspect longitude/latitude plotting. Small numbered locators and adjacent station-name lists replace long leaders. | Same first-five stations in each existing sequence, hospital-linked tracts and Q4 membership. |
| S11 | Parallel service-loss labels distinguish integrals from the time-to-80% column; no heatmap grid crosses values. | Same eight-policy, 2pc50/C57_D1 mean differences relative to Unconstrained, on the same true-hour color scale. |

## Priority-map interpretation

S10C adds continuous tract-population context, with a logarithmic color scale and no highest-population threshold. Population is not presented as the Impact-first station score. Impact-first uses the existing population affected by station removal in the intact-graph scoring model, including network/source-path effects. No new priority rule or mapping has been constructed. All three maps share extent and physical aspect. Station rank labels identify the fixed sequence, not realized task completion times.

## Service loss and recovery time answer different questions

Population-weighted service loss integrates unavailable modeled service over 0-480 h. T80 is the time at which population-weighted availability first reaches 80%. The same existing 1,000-realization tables give within-policy Pearson correlations of 0.610-0.702 and Spearman correlations of 0.592-0.680. Association does not make the two estimands interchangeable: Vulnerability-first relative to Hospital-first decreases mean service loss by 0.048616 h but increases mean T80 by 0.466293 h. T80 therefore remains, with explicit threshold-time wording rather than an undefined recovery-duration label.

Other existing evidence describes early recovery availability, evolving connected-network structure and source-connected availability/redundancy. Q1-Q4 separation and population-weighted Gini describe the distribution of service loss; they are not independent physical recovery-time endpoints. Their interpretation must remain distinct.

## Full resource evidence

S12/S13 remain complete all-eight-policy absolute-outcome supplements to Fig06's policy contrasts across the tested crew and duration cases. Neither artwork was changed. Direct-community remains sequence-equivalent to Impact-first, not an extra policy. No policy is removed by this presentation round. Separating coincident curves is preferable to losing the complete comparison or making secondary results nearly invisible.

## Validation and provenance

`DISTRIBUTION_STRATEGY_METRIC_REVIEW_20261008.json` records source-table hashes, station-distribution summaries, correlations, existing metric means and each edited artwork's identity. `DISTRIBUTION_STRATEGY_PRESENTATION_VERIFICATION_20261008.json` records final validation results.

The review folder and the publication-facing mirrors are synchronized. The 38-page packet alternates each of the 19 current artwork groups with its caption. PDF text remains embedded Arial, with at least 7 pt text in every edited artwork, native 185 mm width and 600-dpi PNG previews. Actual previews of all five edited figures were opened. Untouched regions in S01/Fig04/S04 are pixel-identical; S12/S13 are byte-identical to the base. The 260 protected scientific file hashes are unchanged. No simulation, sampling, scheduling, GA, trajectory generation, mapping or clustering stage was executed. Density estimation, map projection and correlations here are display/review operations on existing saved results.

Regression tests: 49 passed. Canonical resume results are recorded in the companion verification file after validation. Unrelated pre-existing staged provenance files are excluded from these commits.
