# Engineering and descriptive value: preregistered follow-up

October 15, 2026. Starting 1021 commit:
3f10ff621a2aab36d056f6dfcb6be8dc750f91aa. Publication baseline remains
b307e6deafc054864787a3db63ad95218be91659. No official file may change.
This protocol is committed and pushed before comparing new outcomes by class.
Availability inspection has examined filenames, schemas, dimensions and identities,
not class-outcome differences. No new K search or weight selection.

## Questions and limits

Does K3 offer a reproducible compression of engineering recovery behavior not
directly fitted, beyond a coarser K2 partition or simple single-variable groups?
Could continuous descriptions be preferable? Contradictory evidence is retained.
Clusters are deterministic functions of the seven inputs: they cannot create
information absent from those inputs. Unfitted outcomes can support descriptive
utility, NOT prove additional causal information or external physical validity.

## Frozen feature geometry and references

Use the unchanged 2,299 positive-population tract matrix, eight zero-housing
tracts, exact GEOIDs, population, quartiles, ddof=0 standardization and budgets
[1/9,1/9,1/9,1/6,1/6,1/6,1/6]. Equal tract fitting weights. All original 2,315
tracts remain in service outputs. No NCV14 and no trimmed or imputed observations.

K3 and K4 reference memberships are the exact saved historical P2 labels in
results/stage7/2026-10-14/preprocessing_and_labels.npz (not the slightly different
minimum-WCSS K3 seed46 from the preceding validation). K2 is the preceding
registered seed42 fit in outputs/ALL_FITTED_ARRAYS.npz. Reference counts and
source hashes are checked. All labels are model-specific.

No physical, scheduling, fragility, propagation or GA calculation is run.

## Outcome availability and extraction, fixed before class comparisons

The manifest-bound local Formal_Experiment_20260923 archive contains verified
tract integral shards and saved station-service event states. Use those states
only: a linear projection through the SAME archived normalized tract weights is
post-processing saved service, not regenerating physical trajectories. Do not
rerun source gating. Preserve original event times and stored e values.

1. Primary policy-transfer outcome: Random-policy mean 0-480 h tract deficit
   under 2pc50/C57_D1/M1/G1. Random is excluded from the five-policy fit ensemble.
2. Primary temporal outcome: tract realization-median T80 under Impact-first,
   defined as first saved event with normalized modeled tract availability >=0.8.
   Preserve nonreaching realizations as NaN plus a separate unreached fraction,
   NEVER as T80=480. Summarize reached-only mean/P10/P50/P90 and report censoring.
   If censoring is present, comparisons of reached-only summaries are conditional;
   no false claim about an unconditional median is allowed.
3. Supporting temporal outcomes under Impact-first, Random and Unconstrained:
   equivalent deficit hours in [0,24], [24,72], [72,480], and the same T80 summaries.
   Use exact piecewise-constant event overlap, not interpolated trajectories.
4. Prespecified transfer contexts, all Impact-first: 2pc50/C29_D1,
   2pc50/C114_D1, Northridge/C57_D1, LongBeach/C57_D1, SanFernando/C57_D1.
   Use saved integral means, not new scenarios or schedules. Other hazards have
   their OWN frozen physical realization identities, not paired earthquake events.

All use 1,000 evaluation realizations, 480 h, mapping M1_UTILITY_003, stored
G1_BASELINE_050, original station/tract order and frozen population. Check metadata,
NPZ SHA, physical hashes, per-event manifest and identity. Resource alternatives
must match the 2pc50 physical hashes. Verify projection against saved integral
arrays and source-population aggregate summaries. Export selected manifest/source
hashes and derived tract values. If any source fails, record that outcome as
unavailable; do not substitute another favored outcome.

Legacy saved T80 tables are provenance checks only until their aggregation,
policy and gate definitions can be established. They must not silently replace
realization-level threshold times. Sources share network, mapping, damage and
restoration assumptions: NONE are independent external outage observations.

## Meaningful differences, fixed engineering conventions

These are transparent interpretive cutoffs, not empirically calibrated outage
damage thresholds or tests of significance:

- Total/late deficit: 5 equivalent full-service-deficit hours between groups.
- Early (0-24) deficit: 2 equivalent hours; intermediate (24-72): 3 hours.
- Reached-only T80 location: 6 hours; T80 inter-realization P90-P10 width: 6 h.
- Unreached probability: 0.05 absolute (five percentage points).

Report all smaller differences as well. No percentile search, posterior outcome
selection, composite validity score or significance-based filtering.

## Benchmarks and held-out comparisons

For each K2/K3/K4, compare with K-bin empirical quantile groups on each single
fitting quantity: B_Unconstrained, MeanDelta, SOVI_SCORE and B_Unconstrained +
MeanDelta. Learn cuts on training tracts; duplicate cuts may collapse bins and
must be reported, not broken artificially using GEOIDs or outcome values.

Also compare seven-input OLS and a fixed additive continuous model: per-feature
SplineTransformer(n_knots=4, degree=3, knots='quantile', include_bias=False),
then Ridge(alpha=1). No tuning. These assess descriptive compression/prediction,
not causal validity or an exhaustive optimal continuous model.

Train outcome predictors ONLY on training rows. For a K-means model, predict
held-out labels with training centroids and use training-class outcome means.
Evaluate held-out MAE and RMSE on every available outcome, with same test rows
across models. For missing reached-only outcomes use available TRAINING values
only and report tested counts. If a class has no training support for an outcome,
record that prediction unavailable rather than imputing a favorable value.

Prespecified practically notable MAE improvements: 1 h for total/late deficit,
0.5 h early/intermediate, 2 h T80 and 0.02 unreached probability. Report paired
K3-K2, K4-K3, K3-simple-benchmark and K3-continuous-model differences. Repeat
intervals describe sensitivity, not independent-observation confidence intervals.

## Subsampling without replacement

100 independent 70% samples and 100 independent 85% samples, sizes floor(f*n).
Use SeedSequence([1021,70,repeat]) and [1021,85,repeat]. Same rows across K and
benchmarks within each repeat. K-means++/50 starts/Lloyd/500 iterations/tol1e-4;
fit seeds drawn in K order from that stream after row selection. Fixed full-
cohort standardizer and budgets, no reweighting. Single-thread arithmetic.

Preserve sampled indices, centers, all-tract predictions, train labels and all
scores. Evaluate full-cohort and held-out ARI and class-wise Jaccard. Hungarian
matching is ONLY for mapping same-K resample labels to the frozen reference;
all ARIs and cross-K comparisons are label-invariant. Each matched recovery
profile is compared with the full-reference profile in actual units. Report
all repetitions, including failed/weak ones. Profile reproducibility tolerances:
1 h for total/late deficits, 0.5 h early/intermediate, 2 h T80, 0.02 unreached.

Stable membership cores: proportion of all 200 fitted partitions assigning each
tract to its own reference class >=0.90. Report 70% and 85% separately, pooled,
and held-out-only frequencies/denominators. No core is an eligibility exclusion.
Define core status as a diagnostic, never discard noncore tracts from outcomes.
Keep previous 50% prediction-strength and bootstrap evidence visible and unchanged.

## Cross-K persistence, no nesting assumption

Export K2xK3, K3xK4 and K2xK4 overlap tables (counts, populations, both conditional
fractions and Jaccard), ARI and mutual information. Do not force one-to-one
matching across unequal K. Report best pairwise matches and shared subsets'
outcome profiles. Compare K3 outcome contrasts to K2, tracking whether a meaningful
contrast is preserved in >=80% of registered subsamples. This is a declared
descriptive persistence convention, not a proof of natural classes.

## Decision interpretation

Support a stronger claim of useful K3 compression only if: it provides meaningful
unfitted engineering contrasts; these survive subsampling; and held-out performance
or descriptive distinctions improve materially over K2 and transparent benchmarks.
Do not count correlated early/late/total summaries as independent votes. Even a
successful result supports MODEL-CONDITIONED usefulness, not independent external
validation or a unique true K. If continuous models capture the same relationships
or group assignments remain unstable, retain K3 only as an optional description.
State mixed evidence explicitly rather than forcing one winner.

No official manuscript, figure, archived simulation or prior diagnostic may change.
Only this new subdirectory is added. Commit/push protocol first, then completed
evidence; independently verify arithmetic, invariance, remote HEAD and LFS bytes.
