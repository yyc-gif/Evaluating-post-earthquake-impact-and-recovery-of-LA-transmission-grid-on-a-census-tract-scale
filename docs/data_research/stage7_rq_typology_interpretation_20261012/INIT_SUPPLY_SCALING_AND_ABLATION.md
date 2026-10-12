# Init_Supply: model information versus numerical leverage

**AUTHOR REVIEW - NOT FORMAL STAGE 7.**

**Recommended status: retain with explicit rare-model-state interpretation and strong sensitivity limitations.** It is not an unqualified indicator of community resilience. It carries verified initial-state information that is distinct from cumulative recovery; its very sparse distribution nevertheless dominates the isolated 34-tract class.

There are 1,533/2,299 exact zeros (66.6812%). Near-zero counts and nonzero quantiles are in `INIT_DISTRIBUTION_AND_LEVERAGE.csv`; no zeros are replaced. The maximum is 0.0245, mean 0.000581681, SD 0.002457355. Standardization maps zero to -0.23671 and maximum to 9.73336. The highest 23 observations account for 62.4799% of Init's global centered sum of squares, despite only 1% of tracts. Under the A budget, they account for 6.9422% of total weighted global sum of squares.

## Algebraically isolate the two ablation effects, without fitting

Fix the exact 34 membership and the existing full-cohort standardization. Its weighted centroid separation from the global centroid in A is 216.762652; Init accounts for 89.1135%. Dropping Init while leaving all other budgets fixed reduces it to 23.597775. Redistributing the RQ1 budget to Impact/HHI (each 1/6) increases the remainder only to 23.959970. This separates variable-presence leverage from reallocation: the latter adds 0.362195, about 1.535% of the non-Init remainder, not an explanation for the 89% collapse. B gives 216.818014, 23.653137 and 24.015332 respectively.

The fixed-other-budget calculation is an algebraic counterfactual (RQ1 budget 2/9), **not a newly fitted or proposed weighted model**. Actual registered minus-Init fits also change RQ1 budgets; their membership differences cannot be described as a pure deletion effect. Total standardized squared variation is 2,299 for full and redistributed models, versus 2,043.5556 when Init is omitted with other budgets fixed. Euclidean weights are square roots of the recorded budgets.

## Whole-partition versus rare-class leverage

The 89.11% value applies to the rare class centroid, **not the entire typology**. In A/k4/seed42, Init contributes 255.4444/2,299=11.11% of global weighted variation by design; between-class Init SS is 200.1248 and within-class SS 55.3197. Init accounts for 22.42% of all-coordinate between-class SS. Inside the rare class, its within-class SS is 6.9714 (approximately 31.32% of the rare class's total within-class variation). Other classes remain strongly structured by B, Delta and SOVI. All 60 per-coordinate total/within/between decompositions are in `DOMAIN_AND_COORDINATE_OBSERVED_VARIATION.csv`. Declared equal RQ budgets do not imply equal observed separation: for this A/k4 partition, RQ2 contributes about 55.08%, RQ1 31.05% and RQ3 13.87% of between-class variation. These are post-fit descriptions, not optimized weights.

## Other coordinates and original units

The group's mean B is 23.6011 versus 34.0537 h outside (about -2.00 cohort SD); this is meaningful modeled recovery contrast. Its mean Delta B (2.1437 versus 2.2898 h), SOVI (67.986 versus 66.486), log population, impact and HHI provide much weaker centroid contrasts. The non-Init weighted centroid separation remains nonzero but the registered ablations do not recover an independent 34-member class: A-minus/k4 best match retains 21 in a class of 946, B-minus/k4 retains 25 in 1,279. At k3 the main fits pool the rare state into broad classes. Stability alone is not construct validity.

## Decision and author approval

Keep Init provisionally because frozen Q-source/mapping evidence explains the rare survival condition. Treat k4/k5's 34-member class as **Q-proxy-dependent rare mean-initial-state geography**, not a general community recovery regime. k3 can retain the coordinate without making it a separate class. Moving Init to descriptive-only is a scientifically defensible alternative if the author's goal excludes local source-proxy state distinctions, but is not compelled merely by sparsity; adopting an ablated model requires explicit authorization. No transform, winsorization, jitter, new weighting, model fit, source-role validation or formal replacement is introduced.
