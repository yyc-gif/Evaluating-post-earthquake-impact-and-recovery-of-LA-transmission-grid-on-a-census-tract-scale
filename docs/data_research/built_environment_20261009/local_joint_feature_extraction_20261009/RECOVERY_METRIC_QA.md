# Recovery metric extraction and validation

B is the mean normalized cumulative modeled service deficit, integrated as previous-state steps over 0–480 h in each of the same 1,000 saved evaluation realizations. Mapping mass is unchanged. AUC_480 is exactly 1 - B_480_hr / 480 and is not an additional independent outcome.

T80 is the first exact completion-event time at which the **mean tract service trajectory** reaches 0.8. It is not the mean of individual-realization threshold crossings. The source implementation is src/la_grid/revision/formal/stage7.py; the legacy core KPI function also takes the first crossing of its supplied series. No Stage 3 Unconstrained result is used.

All 2,315 tracts match; the residential subset has exactly 2,291 original members. Recovery values are complete. Maximum saved-vs-reconstructed T80 error: 7.11e-15 h; initial-service error 9.9e-17; station-integral error 0 h. All 1,000 NPZ hashes and physical identities pass. All mean trajectories reach T80 before 480 h.

| comparison | N | Pearson | Spearman |
|---|---:|---:|---:|
| B_480_hr vs T80 | 2291 | 0.912150 | 0.929190 |
| B_480_hr vs Init_Supply | 2291 | -0.252442 | -0.279606 |
| T80 vs Init_Supply | 2291 | -0.108296 | -0.114210 |

Raw B skewness = 0.478207; log1p(B) skewness = 0.063493. Quantiles and extreme tracts are exported. This diagnoses long-tail compression without selecting a transform or a clustering feature. These correlations are descriptive tract associations, not independent causal evidence or a variable-selection rule.

On the residential subset, Init_Supply is exactly zero for 1,529/2,291 tracts (66.74%), with median zero and maximum 0.0245. This is the preserved formal source-connected initial-service measure, not an imputed zero. B spans20.537–57.341h and T80 spans34.340–69.686h; B has no zero values. The fixed480h horizon remains identical across realizations and is not substituted with the T80 crossing window.

Additional tail diagnostic (same highest raw-B1% tracts): squared-deviation contribution to variance is 10.89% for rawB and 7.60% for log1pB. Maximum standardized deviation falls from 4.562 to 3.595. RawB skewness is moderate, not evidence by itself of severe tail domination. Log compression is measurable, but no transform is selected.
