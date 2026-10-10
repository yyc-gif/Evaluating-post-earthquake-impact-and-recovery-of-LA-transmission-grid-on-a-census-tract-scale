# Complete 20k initialization/parameter factorial and no-prior controls

All 228 case/seed records are complete: 12 new seeds (200–211) × 19 configurations × 20,000 distinct objective evaluations = **4,560,000 separately budgeted exact planning evaluations**. Whole 92-station final permutation and SHA-256 are retained for each run in GitHub Actions artifacts. The scientific evaluator and 64 planning realizations are unchanged; no independent physical samples were generated.

**Comparison scope:** 16 factorial combinations of population 50/100, tournament 3/5, mutation 0.10/0.20, and 0 or floor(P/4) inversion neighbors. Three additional no-quality or no-prior-archive controls. The 10 factorial main/two-factor terms and 18 baseline comparisons use separate Bonferroni-adjusted simultaneous 95% t intervals. GA-seed variation only—not physical-sample uncertainty.

## Factorial effects (20k)

| Contrast | Mean (h) | 95% simultaneous interval (h) | Wins / n |
|---|---:|---:|---:|
| population | +0.000261 | [-0.001081, +0.001604] | 3/12 |
| tournament | -0.001816 | [-0.002796, -0.000835] | 12/12 |
| mutation | -0.000753 | [-0.002585, +0.001078] | 9/12 |
| neighbors | +0.000016 | [-0.001140, +0.001171] | 7/12 |
| population×tournament | -0.001274 | [-0.003601, +0.001052] | 9/12 |
| population×mutation | +0.000510 | [-0.002344, +0.003363] | 7/12 |
| population×neighbors | -0.001147 | [-0.003280, +0.000986] | 8/12 |
| tournament×mutation | +0.000321 | [-0.003406, +0.004049] | 6/12 |
| tournament×neighbors | +0.000206 | [-0.002001, +0.002414] | 6/12 |
| mutation×neighbors | +0.000782 | [-0.000888, +0.002453] | 3/12 |

## Factorial individual variants (20k)

| Contrast | Mean (h) | 95% simultaneous interval (h) | Wins / n |
|---|---:|---:|---:|
| heuristic_only_no_quality | +0.008974 | [+0.002501, +0.015447] | 1/12 |
| impact_only_archive_no_quality | +0.007071 | [+0.002600, +0.011543] | 0/12 |
| p100_k3_m10_nnone | +0.001324 | [-0.002866, +0.005515] | 6/12 |
| p100_k3_m20_nnone | -0.000050 | [-0.004161, +0.004061] | 5/12 |
| p100_k3_m20_nquarter | -0.000361 | [-0.005818, +0.005096] | 6/12 |
| p100_k5_m10_nnone | -0.001650 | [-0.004913, +0.001612] | 8/12 |
| p100_k5_m10_nquarter | -0.002669 | [-0.006215, +0.000877] | 10/12 |
| p100_k5_m20_nnone | -0.002501 | [-0.006295, +0.001294] | 10/12 |
| p100_k5_m20_nquarter | -0.002077 | [-0.005909, +0.001755] | 9/12 |
| p50_k3_m10_nnone | -0.000487 | [-0.005148, +0.004174] | 7/12 |
| p50_k3_m10_nquarter | +0.000107 | [-0.004484, +0.004699] | 5/12 |
| p50_k3_m20_nnone | -0.001496 | [-0.006311, +0.003319] | 8/12 |
| p50_k3_m20_nquarter | -0.000804 | [-0.005526, +0.003918] | 5/12 |
| p50_k5_m10_nnone | -0.001444 | [-0.004774, +0.001887] | 8/12 |
| p50_k5_m10_nquarter | -0.001197 | [-0.005966, +0.003571] | 9/12 |
| p50_k5_m20_nnone | -0.002788 | [-0.007306, +0.001729] | 8/12 |
| p50_k5_m20_nquarter | -0.001965 | [-0.006509, +0.002579] | 9/12 |
| random_only_archive_no_quality | +0.022874 | [+0.013973, +0.031775] | 0/12 |


### Conclusions bounded to this phase

- Tournament 5 improves the across-factor mean at 20k; the effect has not been established at 100k or 500k, nor has practical relevance been prospectively defined.
- No-prior comparisons are poorer than warm-started GA at 20k, yet all 12 random-only archive runs still beat Impact-first within the same fixed planning objective. This distinguishes inherent algorithmic search from inherited prior-solution benefit; it is not generalization evidence.
- Interaction confidence intervals include zero at this budget; this cannot be interpreted as equivalence.
- Higher-budget confirmation and independent GA-vs-non-GA comparisons were separately prespecified and are tracked independently. No formal candidate is promoted.

