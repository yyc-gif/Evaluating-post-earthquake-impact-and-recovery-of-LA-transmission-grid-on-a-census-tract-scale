# Provisional decision on multi-hazard loss, economic stock and social vulnerability

The analysis preserves SOVI_SCORE, T80 and Init_Supply; no final typology, recovery choice, built-environment variable, manuscript or figure was changed. Recommendation remains provisional pending author decisions on recovery and physical-form inputs.

## Recommendation

For an interpretable joint typology that explicitly distinguishes economic stock from normalized multi-hazard loss propensity, provisionally prefer **D: SOVI_SCORE + log1p(NRI_BUILDVALUE) + ALR_NPCTL**. The archived unadjusted rate percentile exists and its exact v1.19 methodology is documented. It preserves stock as a separate economic coordinate while reducing the stock/EAL redundancy. It is not pure hazard and still uses consequence composition and loss-derived weights. Its lower collinearity is supporting evidence, not the definition of its scientific value.

**B: SOVI_SCORE + EAL_SCORE is defensible if the intended coordinate is explicitly combined multi-hazard expected loss and exposure.** It is the leading compact alternative, not an equivalent replacement for stand-alone stock. The decision to use B must accept that absolute stock is no longer directly represented and that equal weighting inside the combined domain amplifies its single score relative to each of two separate coordinates. We do not recommend selecting it simply for higher silhouette or fewer columns.

Do not retain A as the default when independent social vulnerability is already mandatory: RISK mechanically includes the social/resilience Community Risk Factor. C remains scientifically possible when both absolute stock and total expected loss have an explicit purpose; its log-scale redundancy is material but not a universal numerical prohibition. ALR_VRA_NPCTL is not proposed because it reintroduces the social adjustment.

## Actual associations: all2,291 tracts unless a physical-form field has missing coverage

| Pair | Pearson / Spearman |
|---|---|
| SOVI_SCORE vs NRI_RISK_SCORE | 0.3805 / 0.3530 |
| SOVI_SCORE vs EAL_SCORE | -0.0440 / -0.0685 |
| SOVI_SCORE vs EAL_VALT | -0.0237 / -0.0685 |
| SOVI_SCORE vs NRI_BUILDVALUE | -0.2153 / -0.3515 |
| SOVI_SCORE vs log1p_NRI_BUILDVALUE | -0.3244 / -0.3515 |
| EAL_SCORE vs NRI_BUILDVALUE | 0.5853 / 0.8585 |
| EAL_SCORE vs log1p_NRI_BUILDVALUE | 0.8310 / 0.8585 |
| EAL_VALT vs NRI_BUILDVALUE | 0.9116 / 0.8585 |
| log1p_EAL_VALT vs log1p_NRI_BUILDVALUE | 0.8780 / 0.8585 |
| EAL_SCORE vs NRI_RISK_SCORE | 0.8933 / 0.8864 |
| EAL_SCORE vs Pop_Density | -0.2671 / -0.3655 |
| EAL_SCORE vs Pre_1970_Ratio | -0.1794 / -0.1999 |
| EAL_SCORE vs ALR_NPCTL | 0.6267 / 0.6275 |
| SOVI_SCORE vs ALR_NPCTL | 0.2173 / 0.2263 |

EAL_SCORE versus RESL_SCORE is undefined: RESL_SCORE is constant15.44, not zero correlation. EAL_SCORE and EAL_VALT have identical rank ordering (Spearman1), but their Pearson correlation0.5677 shows that percentile and dollar spacing are different. EAL_SCORE versus log1p(EAL_VALT) Pearson0.9375. Raw EAL_VALT skewness8.052 falls to0.806 on log1p; raw building-value skewness6.803 falls to0.464. Both main monetary fields are positive and complete. Agriculture has structural zeros, which remain valid zero losses; undefined exposure-normalized rates are not invented.

1. **Overlap with SOVI:** materially lower marginal overlap for EAL than RISK. The paired IID-tract bootstrap of absolute Pearson overlap difference gives estimate−0.3365,95% interval[−0.4068,−0.2580]; spatial dependence is not adjusted. This establishes a descriptive reduction, not independence. EAL_SCORE partial correlation with SOVI controlling log building stock and log population density is0.3468 (rank-residual partial0.4175), so the small marginal correlation conceals conditional association.
2. **Overlap with stock:** EAL_SCORE Pearson0.5853 with raw stock,0.8310 with log stock, Spearman0.8585. Raw total-dollar EAL versus raw stock Pearson0.9116. Total EAL is partly driven by asset quantity and population monetization, while differing loss rates and hazard composition provide additional information.
3. **Replacing stock:** B retains an economic-loss/exposure coordinate, but not the economic stock dimension itself. EAL_SCORE alone explains69.05% of log-stock variance linearly;30.95% remains unrepresented by that one linear coordinate. This is in-sample descriptive variance, not information-theoretic loss or out-of-sample accuracy. It cannot recover absolute stock differences, low-loss/high-stock tracts or the split between assets and human-equivalent expected loss.
4. **Score versus value:** use EAL_SCORE for nationally relative expected-loss position and log1p(EAL_VALT) when magnitude of annual-dollar losses is central. Raw dollars have substantial long-tail leverage. Neither representation is universally superior; they must not simultaneously double-weight the same EAL construct. ALR_NPCTL answers a different exposure-normalized question and belongs with explicit stock when retaining both dimensions is intended.
5. **Loss versus pure hazard:** the recommended inputs are multi-hazard expected-loss or loss-rate constructs, not PGA, loss-free hazard probability, wealth, poverty, or the earthquake-recovery scenario. No single-event or earthquake-only substitute is proposed.
6. **Scientific interpretation:** D separates stock and loss propensity; B combines expected loss and exposure. Neither can be labeled pure natural hazard. SOVI stays mandatory in both. Other feature-domain weights and all non-FEMA inputs are fixed for each controlled comparison.

## Collinearity and conditional evidence

| feature_set   |   max_vif |   condition_number_standardized |
|:--------------|----------:|--------------------------------:|
| A             |   4.69321 |                         4.64731 |
| B             |   1.71876 |                         2.34689 |
| C             |   5.34506 |                         4.79111 |
| D             |   1.75166 |                         2.57704 |
| B_value       |   1.71898 |                         2.35026 |
| C_value       |   7.37324 |                         5.83343 |

EAL_SCORE is75.63% linearly explained by SOVI, log stock and log density jointly; ALR_NPCTL is16.00% explained by those same controls. These are shared statistical variance fractions, not causal attribution. C full-model maximum VIF5.35 with log exposures versus D1.75 and B1.72. Thresholds alone do not decide whether a coordinate is meaningful. VIF here refers to simultaneous predictors and standardized condition numbers exclude arbitrary unit scaling.

## Controlled clustering evidence, not a variable-selection contest

There are24 matrix conditions: six definitions (A-D plus B/C dollar-value alternatives), raw versus log-exposure preprocessing, and two explicit domain budgets. Seed42 selects k by the existing k1-10 inertia-distance elbow; five seeds42-46 compare fixed k5 and the selected k. There are195 distinct fitted run records; identical fixed/selected k5 fits are reused, not counted twice. Every matrix has the same2,291 rows, T80/Init, four grid descriptors, housing-age ratio and population density. No new building variable or final clustering is inserted.

Primary comparability reproduces the original domain totals: recovery2/11, grid4/11, built2/11, social1/11, loss/exposure2/11. Each standardized coordinate is multiplied by sqrt(domain budget / domain coordinate count). B's one loss score receives the same total budget as A/C/D's two-coordinate loss/exposure domain. A second analysis uses1/5 per domain, held constant across all alternatives. Domain budgets and actual between-cluster contributions are exported separately. Changes caused by content, log transforms and domain weighting can be located independently.

| feature_set   |   silhouette_mean |   silhouette_sd |   minimum_cluster_size |   ari_saved_mean |   ari_vs_A_mean |
|:--------------|------------------:|----------------:|-----------------------:|-----------------:|----------------:|
| A             |          0.140333 |     0.000921875 |                     34 |         0.857248 |      nan        |
| B             |          0.144148 |     0.00804055  |                     34 |         0.371981 |        0.329277 |
| B_value       |          0.15541  |     0.015934    |                     34 |         0.388894 |        0.354274 |
| C             |          0.149126 |     0.00201692  |                     34 |         0.728666 |        0.721695 |
| C_value       |          0.147609 |     0.00157597  |                     34 |         0.705073 |        0.692973 |
| D             |          0.133931 |     0.000488534 |                     34 |         0.624934 |        0.580775 |

Within-condition seed-pair ARI at fixed k5, log exposures and original domain totals:

| feature_set   |      min |   median |      max |
|:--------------|---------:|---------:|---------:|
| A             | 0.511748 | 0.80508  | 0.980446 |
| B             | 0.273691 | 0.604077 | 0.990615 |
| B_value       | 0.394918 | 0.459593 | 0.991806 |
| C             | 0.837526 | 0.893614 | 0.971801 |
| C_value       | 0.921295 | 0.948786 | 0.998971 |
| D             | 0.911271 | 0.962835 | 0.998702 |

B's seed variability (median pairwise ARI0.6041, minimum0.2737) is unresolved evidence against claiming a settled robust clustering. D's median0.9628 is more stable in this condition but does not itself prove superior scientific content. Equal-domain conditions choose k4 while original totals typically choose k5/6; this demonstrates that a changed weight budget is substantively influential. The A/log/original-budget seed42 replay exactly reproduces saved labels (ARI1); comparisons with old labels are descriptive only and never used as a selection rule.

## Boundaries and remaining decisions

The new physical-form metrics are correlated on explicit matched subsets only; their source limitations remain unchanged. Neither imperfect age linkage nor unverified imperviousness is promoted. Conditional associations and cluster stability do not establish causality, hazard validation, or independence. No final variable allocation is approved by this audit. The unresolved recovery B-versus-T80 and built-environment choices require a later author decision; this audit keeps T80 as the existing formal input throughout.
