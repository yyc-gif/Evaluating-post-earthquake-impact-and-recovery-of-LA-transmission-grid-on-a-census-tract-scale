# Seven versus eight variables: scientific decision for author review

**AUTHOR REVIEW - NOT FORMAL STAGE 7. No formal specification or k is promoted.** Starting authority `ef40eba552a2b33eea364d23a8695d3d96edb326`. All comparisons hold 2pc50, Impact-first, C57_D1, M1_UTILITY_003, G1_BASELINE_050, 480 h and 1,000 existing realizations fixed. DeltaB is matched Impact-first minus Unconstrained, never a new travel-only or damage simulation. Spectral Grid_Impact is not the population-impact restoration-policy score.

## A. Does BUILDVALUE add useful economic exposure?

**Yes as a separately declared building-asset stock construct; no clear evidence that it should automatically replace A as the primary community-recovery specification.** Log assets has Pearson correlation 0.3602 with log population and -0.3160 with SOVI; all-seven conditional R2=0.2804, VIF=1.3896. Economic stock is not numerically redundant, and the source is clean, complete and version-specific. It broadens construct coverage beyond people, but its relevance depends on whether RQ3 explicitly concerns assets as well as residents.

At k4/seed42, B separates groups with much greater SOVI/stock contrast: one large group's mean SOVI is 81.46 and median stock $406.6m, another's 38.67 and $619.8m. A has SOVI 77.92/$437.4m versus 49.52/$512.4m. These are input-based descriptions, not independent validation or household wealth/outage-loss findings. B's log-stock coordinate accounts for only 1.95% of separation, while SOVI rises from 10.90% in A to 22.54% in B. The reorganization is not simply an extreme-stock class.

A versus B median ARI at k3/4/5/6 is about 0.874/0.601/0.801/0.480. This is substantively different, not a cosmetic extra column. The change includes both adding assets and splitting population's exposure budget from 1/6 to 1/12. Equal-RQ3 B also reduces SOVI to 1/9 and materially changes k4 membership (B agreement about 0.50). Neither comparison identifies a pure asset-addition causal effect.

Asset-P99 leaveout training then prediction of all tracts yields B ARI 0.966-0.987 across k3-6, and B-minus-Init 0.982-0.989. The highest values are not creating a new tiny asset-only cluster under the registered log budgets. This robustness check is not permission to remove assets or records from the source.

## B. Should Init_Supply remain?

It carries a distinct initial-state RQ1 meaning but is **highly influential and conditional**, not an innocuous coordinate. Zero fraction 66.68%; maximum z 9.73; top 23 records supply 62.48% of its SS. A/B have the same modeled favorable 34-tract group at k4-6, mean initial service 1.8153%, mean deficit 23.601 h. This reflects frozen model differences, with substantial scaling leverage. The minus-Init ablations reorganize the wider typology and reallocate RQ1 weights. Retaining it is defensible only if isolating that rare modeled state serves the stated typology purpose; otherwise authors may choose a separately justified descriptive role. No replacement transform or automatic omission is approved.

## C. Does the 2,299 cohort improve representation?

**Yes.** It adds 16,979 valid frozen residents without feature missingness, and old geometry exclusions are unnecessary. The eight records do not form an added-only group at k3-5. At k6, A and A-minus-Init can isolate 12 special-use low-population tracts, five added, with median 43.5 residents. These are valid exposure extremes, not corrupted rows, but a tiny class is conditional on resolution/weight choices. A's cohort ARI at k6 about 0.47 and seed-pair median about 0.65 warn against a robust k6 claim. Excluding legitimate residents would hide this scope sensitivity. Keep all 2,315 in original service/distributional calculations.

## D. Are the weights defensible?

**As a transparent normative RQ balance, yes; as statistically optimal or guaranteeing equal observed separation, no.** Each domain is exactly 1/3 of total weighted standardized SS and budgets are applied by square roots. Full pairwise/conditional statistics do not show mathematical duplication of the eight proposed coordinates. Shared W/trajectories create mechanistic dependence, distinct from algebraic duplicates.

| specification   | domain   |   squared_distance_budget |   fraction_of_between |
|:----------------|:---------|--------------------------:|----------------------:|
| A               | RQ1      |                    0.3333 |                0.3105 |
| A               | RQ2      |                    0.3333 |                0.5508 |
| A               | RQ3      |                    0.3333 |                0.1387 |
| B               | RQ1      |                    0.3333 |                0.3001 |
| B               | RQ2      |                    0.3333 |                0.4496 |
| B               | RQ3      |                    0.3333 |                0.2504 |
| A-minus-Init    | RQ1      |                    0.3333 |                0.5782 |
| A-minus-Init    | RQ2      |                    0.3333 |                0.3811 |
| A-minus-Init    | RQ3      |                    0.3333 |                0.0407 |
| B-minus-Init    | RQ1      |                    0.3333 |                0.3759 |
| B-minus-Init    | RQ2      |                    0.3333 |                0.3842 |
| B-minus-Init    | RQ3      |                    0.3333 |                0.2399 |
| B-equal-RQ3     | RQ1      |                    0.3333 |                0.3375 |
| B-equal-RQ3     | RQ2      |                    0.3333 |                0.5997 |
| B-equal-RQ3     | RQ3      |                    0.3333 |                0.0628 |

At k4/seed42, RQ3 separation is 13.87% for A, 25.04% for B, 4.07% for A-minus-Init and 23.99% for B-minus-Init. Equal-RQ3 B has only 6.28%. A priori equal input budgets do not equalize how many clusters each construct defines. No evidence licenses outcome-optimized reweighting here. **The proposal needs explicit author acceptance, not automatic numerical revision**; if RQ3 population/vulnerability must be strongly visible, these differences require substantive discussion before choosing a primary fit.

## E. Which candidate is clearest?

**No unconditional winner is established. Keep A as the parsimonious registered reference and B as the economic-exposure extension for review.** A is closest to the prior source-audited RQs without adding an asset-consequence claim; B supplies a defensible distinct stock dimension and often a clearer social/asset contrast. A-minus-Init is not automatically preferred: its k4 solution is highly structural with little RQ3 separation. B-minus-Init also has pronounced spatial k4 sensitivity. The choice depends on the intended role of rare initial states and whether economic asset stock is explicitly within RQ3. Authors must decide these construct priorities before any promotion; do not declare a universally best specification or select k from these profiles.

## Registered evidence and limitations

200 primary/cohort/ablation/weight fits: k3-6, seeds42-46, n_init50, max_iter500, tol1e-4, Lloyd. Seed42/k4 is a predeclared display only. 120 additional tail/spatial stress fits are separate. No silhouette optimization, old label matching, or preferred manuscript narrative is used. Diagnostic D labels are sorted by mean deficit then population, never formal IDs. Input profiles are not independent validation.

| specification   |   k | kind                       |    min |   median |    max |
|:----------------|----:|:---------------------------|-------:|---------:|-------:|
| A               |   4 | asset_P99_leaveout         | 0.9984 |   0.9984 | 0.9984 |
| A               |   4 | seed_pair                  | 0.9903 |   1.0000 | 1.0000 |
| A               |   4 | spatial_leave_quadrant_out | 0.6161 |   0.7280 | 0.9311 |
| A-minus-Init    |   4 | asset_P99_leaveout         | 0.9903 |   0.9903 | 0.9903 |
| A-minus-Init    |   4 | seed_pair                  | 1.0000 |   1.0000 | 1.0000 |
| A-minus-Init    |   4 | spatial_leave_quadrant_out | 0.2527 |   0.8735 | 0.9554 |
| B               |   4 | asset_P99_leaveout         | 0.9660 |   0.9660 | 0.9660 |
| B               |   4 | seed_pair                  | 0.9830 |   1.0000 | 1.0000 |
| B               |   4 | spatial_leave_quadrant_out | 0.5184 |   0.6978 | 0.8434 |
| B-equal-RQ3     |   4 | asset_P99_leaveout         | 0.9852 |   0.9852 | 0.9852 |
| B-equal-RQ3     |   4 | seed_pair                  | 0.9741 |   0.9836 | 1.0000 |
| B-equal-RQ3     |   4 | spatial_leave_quadrant_out | 0.6115 |   0.8353 | 0.9687 |
| B-minus-Init    |   4 | asset_P99_leaveout         | 0.9819 |   0.9819 | 0.9819 |
| B-minus-Init    |   4 | seed_pair                  | 0.9955 |   0.9985 | 1.0000 |
| B-minus-Init    |   4 | spatial_leave_quadrant_out | 0.2362 |   0.2592 | 0.8847 |

Random initialization stability is high at k4 but spatial leave-quadrant-out agreement can be much lower (B-minus-Init k4 as low as~0.24; A-minus-Init~0.25). Internal points give complete common geographic support, but quadrant tests alter training composition and refit scalers; they are not a prediction-validation study or a comprehensive spatial-error model. Within-cluster distributions, profiles and membership comparisons for **every** registered condition are preserved, not only the displayed example.

Remaining limits: direct upstream Census batch for formal population unresolved; NRI stock is 2022 dollars, not observed outage damages; full source event/integral archives are manifest-bound locally but not all Git-tracked; the fixed 2pc50 field is a probabilistic benchmark, not a unique coherent rupture; independent external electricity/customer restoration outcomes are not used as typology validation. Frozen Q1-Q4, hospital-linked outcomes, Gini/gaps, formal curves and formal Stage7 remain unchanged.

## Required author decisions

1. Is economic building stock explicitly part of RQ3, or a descriptive companion to the population/vulnerability typology?
2. Is the rare 34-tract modeled initial-service state a meaningful intended type, or should Init be descriptive with the ablation as a candidate?
3. Accept the all-positive-population scope and disclose special-use low-population leverage, rather than hiding it through residential admission.
4. Accept normative domain budgets and observed unequal separation; any future change requires a new declared comparison, not tuning to preferred labels.
5. Resolve the upstream frozen Census population release without replacing values. No author-approved formal model or k is established here.
