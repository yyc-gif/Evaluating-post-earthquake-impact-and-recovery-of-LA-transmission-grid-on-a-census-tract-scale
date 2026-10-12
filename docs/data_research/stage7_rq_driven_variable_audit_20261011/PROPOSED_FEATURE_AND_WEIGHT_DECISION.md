# Proposed RQ-driven measurements and domain budgets

**Decision status: author-review proposal only.** No new K-means, PCA, k selection, outcome-optimized weights, fitted weighted matrix, formal typology promotion or manuscript/figure edit. Prior five-domain CORE3/W1 stability does not validate this new construct specification.

## Research questions and selected constructs

RQ1 asks how hazard/network dependency produces disruption. Proposed coordinates: **Init_Supply** (initial service state), **Grid_Impact** (spectral structural criticality), **Redundancy_HHI** (dependency concentration). RQ2 asks about restoration under resources/logistics; under fixed 2pc50 and Impact-first propose **B_480_hr** (cumulative deficit) and **Delta_B_logistics** (matched constrained-minus-Unconstrained increment). RQ3 asks how burdens distribute across vulnerability and places; Route A proposes **SOVI_SCORE** and **log1p(Population)**. The latter is numerically frozen and reproducible; direct population source-vintage documentation remains an author action, not a reason to substitute a new population. These seven candidate coordinates measure distinct declared constructs, not every available graph or census statistic.

The existing framework figure `results/figure_review/Main/Fig01.pdf` and its three-question `provenance/figure_review_history/candidate_v2.1_layout/STORY_EVIDENCE_MATRIX.md` were source/hash checked, not regenerated. This audit uses the three RQs as construct organization, not current cluster narratives as an eligibility rule.

## RQ1 structural alternatives are not statistically rejected

| target           |   conditional_linear_R2 |    VIF |   additive_spline_cv_R2 |
|:-----------------|------------------------:|-------:|------------------------:|
| Init_Supply      |                  0.0214 | 1.0219 |                  0.0662 |
| Grid_Impact      |                  0.1757 | 1.2131 |                  0.3589 |
| Grid_Degree      |                  0.3128 | 1.4552 |                  0.4041 |
| Grid_Betweenness |                  0.3559 | 1.5524 |                  0.5369 |
| Redundancy_HHI   |                  0.0192 | 1.0196 |                  0.3452 |

Impact-Degree Pearson=-0.1519; Impact-Betweenness=0.2735; Degree-Betweenness=0.4695. Degree and Betweenness have complementary empirical structural information; **they are CONDITIONAL, not EXCLUDE for multicollinearity**. One primary spectral coordinate is a parsimonious construct choice. Authors may declare local adjacency or brokerage as additional measurements, but must split the same structural-importance budget and justify the added construct. Do not select them because they explain B well or recreate preferred clusters.

All four graph descriptors were independently reprojected from stored station metrics and exact normalized W; maximum errors are in `GRID_DEFINITION_QA.json`. Spectral Grid_Impact is not the repair policy's population-impact score. The stored degree is used as defined in the frozen graph, not relabeled as a power capacity. HHI is tract dependency concentration, not independent electrical-path redundancy.

Init_Supply has 1529/2291 exact zeros (66.74%) and max 0.024500. Grid_Impact has 765 exact zeros (33.39%). Zero and near-zero distributions are in the register. This severe 2pc50 initial-state sparsity limits resolution and can accentuate standardized tails; no values are clipped, imputed, excluded or rescaled into a new fitted matrix here. Tiny floating-point excursions are reported with numeric tolerance, not edited away.

## Joint information audit

All primary and extended proposed/diagnostic pairwise matrices use the **same 2,291 residential tract IDs**, in exact sorted order. Pearson, Spearman, bidirectional nearest-neighbor mutual information, directional five-fold additive-spline R-squared, conditional linear explained variance and VIF are retained. Pairwise files classify mathematical transform identities, shared trajectories/composite sources, shared mapping and empirical associations. The extended matrix intentionally includes inadmissible alternatives and the recovery arithmetic triplet for diagnosis only; its infinite VIFs are expected, not an estimable model.

For the seven primary coordinates, linear conditional R-squared ranges 0.0655-0.3576, VIF 1.0701-1.5567. They are not linearly interchangeable. Nonlinear information can still be substantial (e.g. Init_Supply spline CV R-squared 0.5921); shared W and fixed event trajectories provide real mechanistic dependence. Random tract CV does not establish spatially independent generalization, and MI with many ties/zeros is descriptive. No p-value, VIF cutoff or correlation threshold is used as an automatic feature admission rule.

Mathematical duplication (B_c=B_u+Delta; AUC=1-B/480; Population/log transform) is different from composite-source overlap (SVI alternatives), empirical correlation (B versus T80), or a physical/mechanistic relation (dependency, initial loss and later recovery). None alone proves causal mediation. No cluster labels, ARI, silhouette, selected k or manuscript profile was used.

## Cohorts and explicit exclusions

Full modeled domain=2,315; prior residential cohort=2,291; historical CORE3 reference=2,287. Proposed primary statistics use residential 2,291 for continuity, **not** historical CORE3 geometry admission. Regained four: 06037189703, 06037301601, 06037301602, 06037404600. None has missing primary coordinates. All seven are actually complete on the full 2,315 domain, so retaining the residential restriction is an explicit scientific scope decision, not a data-quality necessity.

The 24 residential exclusions are individually listed in `TRACT_COHORT_AND_MISSINGNESS.csv`: 23 zero housing-unit records and one zero frozen-population record. The study-wide model retains them. Old geometry discrepancies do not require exclusion for these non-geometry-dependent measures. No zero imputation or generic complete-case deletion occurred. Authors must confirm **residential 2,291 versus full-domain 2,315** before future clustering; this audit does not silently promote either.

## Proposed squared-distance budget, not a fitted matrix

After author approval of measurements and cohort, a future analysis could standardize the selected coordinates on that fixed cohort and use squared distance sum_v a_v (z_rv-z_sv)^2. A coordinate's multiplier would be sqrt(a_v); the table below is a normative domain-balance proposal, **not statistically optimal**, not fitted and not applied.

| Domain | Construct | Proposed coordinate | Squared-distance budget a_v |
|---|---|---|---:|
| RQ1 | Initial modeled state | Init_Supply | 1/9 |
| RQ1 | Structural criticality | Grid_Impact | 1/9 |
| RQ1 | Dependency concentration | Redundancy_HHI | 1/9 |
| RQ2 | Cumulative deficit | B_480_hr | 1/6 |
| RQ2 | Fixed constraint increment | Delta_B_logistics | 1/6 |
| RQ3 | Composite vulnerability | SOVI_SCORE | 1/6 |
| RQ3 | Population exposure scale | log1p(Population) | 1/6 |

Each domain totals **1/3**, total 1. If Degree/Betweenness is additionally justified within structural importance, split that construct's 1/9 among retained structural measurements; do not increase RQ1's total. If a third genuinely independent RQ3 construct is later admitted, explicitly revise within-domain construct budgets rather than append equal global weight. Heating is not presently primary. Do not include B_unconstrained or T80 as extra recovery coordinates, four SVI themes as four social coordinates, or Population*B as another exposure coordinate.

## Required author decisions and remaining limitations

1. Approve the fixed 2pc50 hazard benchmark separately from fixed Impact-first C57_D1 policy/M1/G1 reference; no independent optimized direct-community benefit is claimed.
2. Confirm residential versus full-domain typology scope; do not inherit the old four geometry exclusions.
3. Resolve the upstream Census release/batch for frozen formal population without replacing the values. The current 2020-based claim is documented but not independently authenticated to an original release in this task.
4. Decide whether adjacency/brokerage adds a declared structural construct; the data do not require their deletion as redundant.
5. Decide whether electric heating merits a narrow, uncertainty-aware separate sensitivity analysis. No complete broadly valid third electricity-dependence coordinate was admitted.
6. Approve any later standardization/domain-budget implementation and treatment of initial-state sparsity. No automatic trimming or weighting occurs here.
7. Make the manifest-bound bulk trajectory archive available if source-level clean-clone replication is required; current Git does not contain all those bulk payloads.

The proposal is scientifically interpretable but not an author-approved new typology. Qualifying variables as numerically clean does not make incomplete external release metadata resolved, service proxies actual outage observations, or static graph analysis electrical power-flow feasibility.
