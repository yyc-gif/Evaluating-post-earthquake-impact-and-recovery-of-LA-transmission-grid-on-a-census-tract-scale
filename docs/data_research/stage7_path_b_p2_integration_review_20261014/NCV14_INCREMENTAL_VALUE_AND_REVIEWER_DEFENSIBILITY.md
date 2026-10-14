# NCV14: supplementary environmental-hazard context

Status: retained only as a researcher-derived geographic screening descriptor. No NCV14 value is in P2, and no new index or weight is calculated here. Source authorities are 49cc153 and 0c5365; exact file SHA256s are in SOURCE_PAYLOAD_HASHES.csv. This is not FEMA's RISK_SCORE, a comprehensive vulnerability/disaster-risk index, physical intensity validation or a prediction of multi-hazard power failures.

| variable         |   Pearson |   Spearman |
|:-----------------|----------:|-----------:|
| Init_Supply      |   -0.1714 |     0.0470 |
| Grid_Impact      |   -0.1578 |    -0.2142 |
| Redundancy_HHI   |    0.1022 |     0.0581 |
| B_Unconstrained  |    0.1020 |     0.1798 |
| MeanDelta        |   -0.3256 |    -0.3877 |
| SOVI_SCORE       |   -0.0313 |    -0.0195 |
| log1p_Population |    0.1053 |     0.1221 |

The seven P2 coordinates jointly explain 18.17% of NCV14 variance in a descriptive linear regression (VIF 1.222). P2/K3 class means explain only 6.38% of NCV14 variance: most variation remains within classes. SOVI association is small, while the inverse association with MeanDelta is stronger; neither establishes independence or a causal hazard/recovery interaction.

| class_id   |    n |   mean |   median |    P10 |    P90 |
|:-----------|-----:|-------:|---------:|-------:|-------:|
| C1         | 1235 | 0.6501 |   0.6255 | 0.5625 | 0.7744 |
| C2         |  428 | 0.5967 |   0.5681 | 0.5207 | 0.7543 |
| C3         |  636 | 0.6246 |   0.6332 | 0.5534 | 0.6815 |

The context shows that environmental screening burden, social vulnerability and modeled recovery penalties need not align. C1 has the highest mean NCV14 and highest SOVI but lower added constraint deficit; C2 has greater constraint deficit yet lower mean NCV14. Broad overlapping distributions rule out a new class-level risk ranking. A concise supplemental table and, if the author intends to discuss this geographic contrast, the optional context map are sufficient. Do not add another numbered graphic merely to display an unused variable.

## Methodological boundary

Williams, Summers and Harwell (2024), Sustainability 16, 10778, doi:10.3390/su162310778, provides a county-scale frequency-area/min-max/sum precedent. The frozen audit did not establish an exact original county aggregate replication: its hazard roster, normalization universe and numerical workbook were not unambiguously recovered. FEMA NRI v1.19 provides hazard-specific input fields, not this official composite. Our tract scale, fourteen-hazard roster and California reference scaling are researcher extensions and must be named as such. A later public catalog listing alone would not establish identity with the original numerical workbook.

For each retained hazard h, x_i,h=AFREQ_i,h*EXP_AREA_i,h/AREA_i. Hazard components are min-max scaled across valid California reference records, summed with equal nominal hazard weights, then the complete-case California sum is min-max scaled. The fourteen retained hazards are coastal flood, cold wave, drought, earthquake, hail, heat wave, landslide, lightning, riverine flood, strong wind, tornado, tsunami, wildfire and winter weather. Four target-all-null hazards are excluded, not filled with zero. Cold wave is locally constant zero. All 2,299 positive-population tracts have the frozen NCV14 value; that completeness is not proof of complete direct physical observation.

Heat wave, hail and strong wind account for about 89.5% of signed covariance contribution to local index variance. These are effective regional contributions, not optimized weights or independent hazard probabilities. NOAA reporting, buffers/fishnets and warning-zone crosswalks create coarse/shared geography and reporting biases. A documented heat period/frequency discrepancy and strong-wind period wording conflict remain source limitations. AFREQ may already encode area support; multiplying by EXP_AREA/AREA may repeat geographic exposure weighting. It is a screening construction, not an independent frequency-times-probability identity.

Earthquake's released frequency surrogate and the independent CGS 2pc50 PGA represent different thresholds and supports. Earthquake is a high-background, low-contrast component locally; its weak or signed negative contribution to relative index variance does not mean absence of earthquake hazard. Heat/hail/wind overlap and the low earthquake contrast prevent describing the regional index as balanced information about fourteen independent hazards.

Previously saved hazard-removal ranks and California-versus-Los-Angeles normalization sensitivity are included. CA/LA rank correlation is about 0.983, but this does not validate physical intensity or weights. Historical NCV14-fitted clustering sensitivity must not be claimed as validation of P2: removing a contextual hazard cannot change a model that never fits it. No new hazard-removal fits are warranted.
