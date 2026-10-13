# Figure 7 panel story and predeclared display choices

This document declares the layout before rendering any candidate. It is a proposal, not an approval or a current-suite change.

Question: how do earthquake-conditioned initial disruption and dependency, baseline/constraint-related recovery, social vulnerability, population scale and selected multi-hazard screening burden jointly differ across the three saved types?

## A: six distributions

Keep the previous two-by-three, overlaid class-distribution concept. Select two coordinates per RQ, by complementary construct meaning, not by attractive separation:

| RQ | Coordinate | Why display its distribution |
|---|---|---|
| RQ1 | Grid_Impact | Structural spectral criticality; distinguish skew/near-zero mass from a mean-only contrast. Not the Impact-first repair score. |
| RQ1 | Redundancy_HHI | Concentration of tract-station dependency. Similar class means must not hide wide within-class variability or substantial overlap. |
| RQ2 | B_Unconstrained | Baseline modeled restoration deficit, in equivalent full-service-deficit hours over 0-480 h. |
| RQ2 | MeanDelta | Additional constraint-related deficit across the five declared policies, in the same hour units; not an identified travel-only effect. |
| RQ3 | SOVI_SCORE | Frozen FEMA v1.19 social vulnerability, 0-100, with original quartiles unchanged. |
| RQ3 | FEMA_NCV14_CA_v119 | Researcher-derived fourteen-hazard frequency-area screen, California scaled. Show overlap as well as differences from social vulnerability; not official FEMA risk. |

Propose empirical cumulative distribution functions for all six coordinates, with shared class-specific x scales and colored median dots at cumulative fraction 0.5. This is explicitly a chart-encoding change from historical smoothed KDE, requiring approval. It avoids smoothing zero/near-zero concentrations and ties, and displays quantile spread, overlap and tails without inventing peaks. ECDF slopes/plateaus are not density modes: exact modality is less immediate than in a defensibly estimated continuous density, and no modality claim will be made. All observations are retained; each class ECDF ends at one. Classes are normalized separately, not weighted by their size.

Init_Supply is not one of the six A coordinates because a smooth density would be inappropriate for its severe zero mass and rare source-proxy tail. It remains an unchanged fitted coordinate, appears in B, and receives explicit zero/positive and quantile accounting in the eight-coordinate QA table. This omission does not authorize removing, transforming or clipping it. Population remains in B as the actual fitted log1p coordinate, with resident totals in the review caption and QA; it is not replaced by density or dropped from the model. The six-coordinate selection is a display budget, not feature selection or independent scientific validation.

## B: all eight standardized profiles

Rows: Init, spectral grid impact, HHI / Unconstrained deficit, MeanDelta / SOVI, log1p population, NCV14. Columns: C1-C3. Use cohort-standardized class means `mean_c((x_j-mu_j)/sigma_j)` with the saved 2,299-cohort mean and population SD. A zero-centered diverging heatmap, printed values and RQ separators provide one shared scale. Class headers retain the three saved colors; heatmap colors encode z-score, not class identity.

These are ordinary z-score means, **not** square-root-budget-weighted coordinates. Weighted fitting coordinates are `sqrt(w_j)*z_j`. Realized between-class SS additionally depends on class sizes and squares of means; it is not identical to the colors or magnitude of any one cell. Exact original-unit means, medians, z means and distance diagnostics will be separately exported.

## C/D: locked current artwork

Copy the current PDF's complete lower C/D region as existing vector artwork. Do not reconstruct either map from geometry or rerun recovery. Keep class IDs/colors, geography, projection, extent, N/A and Q4 styles, continuous D3 values, colorbar and legends. Candidate height is proposed at the historical 253 mm rather than current 245 mm to fit eight readable profile rows: the intact lower 113-mm region translates downward by 8 mm, with no scaling. This placement/page-height change is explicit and also requires approval.

Current gray N/A is retained in Candidate A. Historical white N/A is evaluated only in a separate fill comparison, with unchanged outlines/geometry; that alternative is not silently applied. Sixteen N/A zero-population tracts remain distinct from all eight classified positive-population zero-housing tracts.

## Candidate B gate

Do not create a second layout merely for variety. Candidate A already preserves the four questions and restores the missing distribution/profile functions. Unless an actual readability failure requires a materially different solution, retain a single conservative candidate and state that no separate B is justified.
