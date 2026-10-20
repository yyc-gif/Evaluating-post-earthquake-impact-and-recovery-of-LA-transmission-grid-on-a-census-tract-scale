# What these metrics mean

All cumulative service-loss metrics integrate the saved modeled deficit over 0-480 h. Units h are equivalent complete-service-loss hours, not electricity or clinical performance. Service loss denotes that time-integrated deficit.

- Population-weighted loss: normalized tract service deficit, weighted by tract population.
- Population/dependency-mass-weighted loss: population times represented dependency mass weighting; separately saved and retained even if identical within the fully resolved domain.
- Hospital-linked loss: equally weighted mean across the hospital-linked tracts, NOT hospital population weighting or actual hospital electricity.
- Q1-Q4: population weighting within each adopted social-vulnerability group. Q1 lowest, Q4 highest; these are not income classes.
- Signed gap: Q4 minus Q1 in each realization. Absolute gap: absolute value in each realization, then averaged; NOT absolute value of the mean signed gap.
- Population-weighted Gini: inequality of tract service loss, 0 equal, larger more unequal. It does not decide which strategy is equitable.
- T50/T80/T90: time to the stated population-service fraction. Missing/unreached stays NA, never replaced by zero or 480.
- Local/threshold/source-path loss: adopted decomposition, dependency-mass weighted; shares are saved per-realization fractions. Ratio of mean components is not substituted for mean fractions.
- Task count, completion and travel: saved scheduling outcomes, not re-executed here.

Means, realization ranges, existing bootstrap confidence intervals, and spatial tract percentiles are distinct. The explorer identifies their definitions. distributional effects effects join the same saved realization IDs before differencing, without new resampling. No correlation or direction of an outcome is treated as causality, optimality or a fairness verdict.

Spatial sign populations classify the population of tracts by mean paired effect. This is not mean benefiting population per realization and is not significance. The saved negative-effect frequency is an empirical frequency, not a p-value. Alternative vulnerability groupings re-evaluate the same executed strategies; alternative priority ranks were not executed.
