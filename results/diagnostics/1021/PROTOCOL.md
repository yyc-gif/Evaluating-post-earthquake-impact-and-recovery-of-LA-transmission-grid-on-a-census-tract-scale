# 1021: independently assessing clustering resolution

Status: preregistered before new validation fits. October 15, 2026.
This is exploratory scientific-methodology work, not a change to the publication.

## Baseline and questions

Frozen integrated branch: `2026-10-14`, commit
`b307e6deafc054864787a3db63ad95218be91659`. Local and remote HEAD agreed and
the source worktree was clean before creating the independent `1021` worktree.
The baseline includes completed figure corrections after the older scientific
source commit `937fa2b1ab9953d8411a08fbbd0400cf3b52bd8f`.

Do these features support reproducible discrete groups, at what resolution, and
under what sampling and geometric assumptions? Plausible outcomes include K2,
K3, K4, K5, another tested K, no unique K, or primarily continuous structure.
Historical K3/K4 are comparisons, not acceptance targets. Already known prior
silhouettes, geographic results, and the 37-tract K4 group are not new evidence.

## Frozen geometry and authority

Use `results/stage7/2026-10-14/`, checked against `ARTIFACT_HASHES.json`.
Exactly 2,299 positive-population GEOIDs, 9,066,522 residents, eight positive-
population zero-housing tracts, and 16 excluded zero-population tracts. The full
2,315-tract service domain and all vulnerability quartiles remain unchanged.

Coordinates, in order: Init_Supply, Grid_Impact, Redundancy_HHI,
B_Unconstrained, MeanDelta, SOVI_SCORE, log1p_Population. Subtract frozen full-
cohort means, divide by population SD (ddof=0), and multiply by square roots of
budgets (1/9,1/9,1/9,1/6,1/6,1/6,1/6). Retain the saved matrix exactly for fits.
No row/population weights, outlier removal, imputation, jitter or NCV14.

MeanDelta is the equal descriptive mean of five matched policy increments:
Impact-, Hospital-, Degree-, Betweenness-, and Vulnerability-first relative to
Unconstrained. Preserve 2pc50/C57_D1/M1_UTILITY_003/G1_BASELINE_050, 480 h and
1,000 physical realizations. No physical simulation or schedule is regenerated.

## Settings and bounded computation

All K-means: k-means++, n_init=50, Lloyd, max_iter=500, tol=1e-4, single-threaded
numerical libraries. Observed K1-8: seeds 42-46; use the minimum-inertia saved
new fit as each K reference, breaking ties by lower seed. Also compare exact
historical memberships label-invariantly. Archive individual labels and fits.

Independent deterministic streams use NumPy SeedSequence([1021, stage, repetition,
optional_K]). Stage IDs: Gap axis=10/PCA=11; random splits=20; spatial splits=21;
bootstrap=30; feature diagnostic=40. Fit random_state is an integer drawn from
that stream. Different K within a resample use the same sampled rows. No adaptive
extra replicates or metric-based changes after viewing results. A separate tiny
smoke run is allowed; it must not be represented as the full experiment.

## Primary evidence

### Gap statistic: K1-8, 64 references per distribution

W_k is squared-Euclidean WCSS, equivalent to the pairwise squared-distance
definition. Gap(k)=mean_b(log W*_kb)-log W_k. Report reference SD (ddof=1),
MCSE=SD/sqrt(64), and s_k=SD*sqrt(1+1/64). Select the smallest k<=7 satisfying
Gap(k)>=Gap(k+1)-s_(k+1). If none qualifies, report unresolved at the upper
boundary, NOT a verified K8 optimum. Compute both references independently:

1. Uniform over each observed weighted-coordinate min-max interval.
2. Center X, take its full SVD right rotation V, sample uniformly in each
   rotated-coordinate min-max interval, rotate back and restore the mean.

Do not restandardize reference draws: that would change the geometry. These
box nulls do not preserve zero inflation, bounded marginals, mechanistic
dependence, geography or the observed covariance exactly. A rejection of a box
null does not establish physically discrete community types. Report reference
dependence and paired-reference step uncertainty, not a significance claim.

### Prediction strength: K2-6, 50 random half splits

Independently fit both halves. Classify validation observations by the nearest
training centroid. For each independently fitted validation cluster, count
unordered pairs assigned together by training: sum_j choose(n_cj,2)/choose(n_c,2).
Prediction strength is the MINIMUM across validation clusters, not ARI.
Report both train/validation directions and their mean per split; the primary
summary is the mean of these bidirectional split values. Preserve per-cluster
pair counts and distributions, including small groups. A cluster with fewer
than two validation members is undefined, not perfect; report invalid runs and
do not silently drop them from the denominator. Report largest K with mean
strength >=0.8, and separately >=0.9, provided all splits are defined. These
are literature conventions, not formal confidence tests. Report P10/P50/P90,
SD and split-to-split variability; percentile ranges are NOT IID-tract CIs.

Spatial sensitivity: assign centroid locations in EPSG:3310 to a fixed 20-km
grid anchored at (0,0); randomly split occupied grid cells into two sets, with
20 fixed seeds and no rebalancing using features. Fit and evaluate both ways.
Report row counts, empty/singleton classes and prediction strength. Cells near
boundaries are not buffered; this tests spatial transfer, not independent
external validation. Also leave each of four centroid-coordinate median
quadrants out once, fit on the rest, and compare held-out and full predicted
labels with the full fit. Quadrants are descriptive sensitivity, not four
independent validation datasets. Geographic assignments are saved by GEOID.

### Bootstrap cluster-wise stability: K2-6, 100 replicates

Sample n rows with replacement, refit independently using all multiplicities.
For each original reference cluster, restrict it to unique in-bag GEOIDs and
find the maximum Jaccard with a bootstrap cluster on that same unique support.
Matching is independently maximum per original cluster (not one-to-one
Hungarian matching). Archive sample indices and labels. Report mean, median,
P10/P90, dissolution J<0.5, recovery J>=0.75, unique support and minimum sizes.
These operational cutoffs are fixed before running, not scientific validity
thresholds. As a separate extension, nearest-centroid predict all original
observations and report full-support Jaccard; do not conflate it with in-bag
stability. Bootstrap IID sampling does not account for spatial dependence.

Explicitly compare the historical 37-member K4 set by exact GEOID, capture,
precision and Jaccard under all bootstrap, spatial and algorithm comparisons.
Its size is NOT an exclusion rule. The Q Core-source proxy is a modeling
assumption, regardless of statistical stability.

## Secondary and explanatory evidence

Calculate full-cohort Silhouette, negative-silhouette fraction, CH and DB for
all observed K2-8 fits, and Ward hierarchical partitions (same weighted-space
Euclidean geometry) at K2-8. Compare Ward/K-means by ARI and cluster-wise
Jaccard. These internal indices are correlated; do not count them as votes.
Use normalized inertia and its step reductions descriptively, not a fabricated
sharp elbow. Do not fit GMM: the pronounced atom at zero and model-derived
dependencies make Gaussian component counts difficult to interpret here.

Registered Init_Supply diagnostic: set ONLY its weighted coordinate to zero
without redistributing any remaining budget, then fit seeds 42-46 at K2-6.
This is a projection diagnostic, NOT a replacement primary matrix or a tuned
weight scheme. Separately describe existing historical redistributed-budget
ablations if used; do not equate the two. Compare rare-set Jaccard and ARI.
No jitter, clipping or invented measurement-error model is authorized.

Reuse hash-checked frozen policy-set sensitivity tables, explicitly separating
those previous results from new experiments. Policy-set dependence is distinct
from IID resampling or random-initialization stability.

Describe original-unit feature distributions and resident representation for
K2-6, including frozen quartile composition. These are INPUT descriptions, not
external validation. Inspect continuous distributions, cluster overlap,
negative silhouettes, algorithm disagreement and reference-sensitive K to
evaluate the continuous-gradient alternative. No new composite decision score.

## Interpretation rules and preservation

Report contradictions. No unique K unless primary methods give compatible
resolution and spatial/cluster-wise diagnostics do not materially contradict
that interpretation. If criteria disagree, recommend a conditional resolution
or reduce the manuscript's claim to a descriptive discretization. Never choose
K3 because of three RQs, reject K4 because it is small, or choose K5 solely
because silhouette is largest. Even concordant diagnostics are conditional on
the frozen hazard, proxy gate, policy ensemble, features and weights.

Only `results/diagnostics/1021/` may change. Record exact inputs, environment,
all seeds/replicates, protocol commit, source baseline, row/column hashes,
source-worktree status/index, and preservation checks. Independently test pair
counting, Gap selection and bootstrap Jaccard with hand-calculable examples;
independently recalculate outputs and compare the historical saved fits.
Commit and push this protocol BEFORE substantive experiments, then commit and
push complete results. No merge or formal scientific promotion.

## Methodological sources

- Tibshirani, Walther & Hastie (2001), Gap statistic:
  https://doi.org/10.1111/1467-9868.00293
  https://web.stanford.edu/~hastie/Papers/gap.pdf
- Tibshirani & Walther (2005), Prediction Strength:
  https://doi.org/10.1198/106186005X59243
  https://gwalther.su.domains/predictionstrength.pdf
- Hennig (2007), cluster-wise stability:
  https://doi.org/10.1016/j.csda.2006.11.025
  https://www.homepages.ucl.ac.uk/~ucakche/papers/clusta.pdf
- R cluster package documents the distinct Gap 1SE rules:
  https://stat.ethz.ch/R-manual/R-devel/library/cluster/html/clusGap.html

Source retrieval checked October 15, 2026. Some author-hosted PDFs timed out
in the web tool; publisher/author search records and R documentation were
available. No reliance on a third-party implementation as the authority.
