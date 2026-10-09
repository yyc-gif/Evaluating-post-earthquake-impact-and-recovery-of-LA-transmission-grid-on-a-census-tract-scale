# Outcome-measure and visual-identity update — 2026-10-08

Presentation changes only, based on revision commit `4a3e1f0056e487dd62f81b35705d6407d44654b0`.

| Figure | Author-requested correction |
|---|---|
| Fig01 | Section 5 separates the 0–480 h service-loss integral from T80 threshold-crossing time; shows Q1–Q4, group separation, Gini, spatial effects and community patterns. Unspecified Lower/Higher curves are removed. Resources point to Fig06; mapping/gate and planning-limit checks point to S06/S08. Stages 1–4 are unchanged. |
| Fig04 | Retains eight scheduled policies and Unconstrained. Secondary recovery curves use opacity 0.55 instead of 0.25; four core policies and Unconstrained remain emphasized. Grouped key synchronized with S04. |
| Fig05/Fig06/S12/S13 | High-low descriptors use a plain hyphen. Fig06 names Hospital-first, Impact-first and Degree-first rather than “each named reference”. No metric, reference, interval or numerical value changes. |
| Fig07/S09 | Explicit cluster-ID colors remain shared. C4 uses muted cyan and C5 brick red; gray is reserved for the same 24 N/A tracts. Quantitative heatmaps, hotspot scores, cluster membership and all map geometry are unchanged. |

## Scientific distinctions

Service loss is the integral of modeled unavailable service over 0–480 h; T80 is the first crossing of 80% modeled service. They are complementary outcomes with different estimands. The current analysis also reports vulnerability quartiles, signed and absolute between-group differences, population-weighted Gini, tract-level spatial effects and community typology/hotspots. The framework presents these families without claiming only overall and hospital-linked tract outcomes exist.

Centrality-first specifically ranks station removal by relative network algebraic-connectivity (lambda2) reduction in the initial largest connected component (`compute_impact_centrality`). Degree, betweenness and closeness are separate centrality rankings; population-impact-based Impact-first is different. No strategy name/key, sequence or result row is changed and no scheduled policy is removed.

Fig06 retains the complete tested crew and repair-duration OFAT families. Mapping cutoff, source connectivity, functionality threshold and SCE planning bounds are dependency/service-model assumptions, shown separately in S06/S08. No new travel-time/base-allocation experiment or untested resource interaction is inferred.

## Verification

All nine changed native PDFs and rendered previews were opened and inspected. PDF text remains Arial, at least 7 pt; widths remain 185 mm and PNG previews remain 600 dpi. No observed new overlap or clipped labels. Fig01 pixels outside section 5 match the baseline. All 38 current artwork files match their manifest and their flat publication copies; the full packet has 38 pages (figure followed by caption). Existing tests: 49 passed. All 260 protected scientific-file hashes are unchanged. Canonical archive validation is recorded in the companion verification JSON after resume. Unrelated staging is preserved and excluded from these commits.
