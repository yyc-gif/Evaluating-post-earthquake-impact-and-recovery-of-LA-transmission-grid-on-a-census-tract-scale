# Recovery-mechanism exploration: registered protocol

Registered on 2026-10-15, before extracting new interval features or fitting new
partitions. Starting branch: `refs/heads/1021`; starting commit:
`5e6a950e2bf58fc72279991430dd0ed5731f6d3f`. The October 14 publication baseline
`b307e6deafc054864787a3db63ad95218be91659` is read-only.

## Questions and possible conclusions

Do frozen recovery responses support reproducible discrete groups, or useful
but resolution-dependent subdivisions of a continuous recovery gradient? Do
these representations describe withheld resource, policy and hazard responses
better than P2 or simple recovery rankings? K1/no meaningful discrete partition,
multiple defensible resolutions and negative results are admissible. No method
is required to retain K3, isolate the Q-source group, or improve silhouette.

## Inputs and limits

Retain all 2,299 positive-population tracts, exact eleven-digit GEOIDs, eight
zero-housing tracts, frozen population, SOVI quartiles and hospital flags. No
social/population/hazard-context information enters recovery clustering. Study
service calculations remain over 2,315 tracts. Reference: 2pc50/C57_D1,
Impact-first, M1_UTILITY_003, G1_BASELINE_050, 480 hours, 1,000 saved physical
realizations. Read the archived `e` station states: no network propagation,
source-gate calculation, scheduling, damage sampling or interpolation.

The prior engineering package's eight integral cases and three event-history
cases are the source authority, checked against their actual hashes. Resource
cases share physical samples; other earthquakes have their own matched frozen
samples and are scenario transfer, not the same earthquake realization. Stop
an affected analysis if its source is unavailable. Raw event archives are local
manifest-bound dependencies, not guaranteed by a clean Git clone.

## Representation A: absolute recovery shape

Intervals (hours): [0,6), [6,24), [24,72), [72,168), [168,480]. Integrate
right-continuous archived event states exactly; divide by interval duration,
then average over the 1,000 realizations. Each coordinate is mean availability
in [0,1]. No individual-tract normalization, clipping, smoothing or imputation.
Use equal interval squared-distance budgets of 1/5, multiplying by sqrt(1/5).
Do not z-score intervals: near-constant late availability must not be magnified
into a major separation. Equal intervals emphasize distinct operational stages
rather than allowing 312 late hours to dominate merely through duration.

Evaluate A-full (five intervals), and A-PCA: centered, unwhitened PCA of that
same weighted matrix, retaining the smallest component count with cumulative
explained variance >=95%. PCA is fitted to the full frozen feature cohort for
the reference solution and refitted on training tracts for resampling, always
using this criterion. Record retained components in every fit. No variance
criterion is tuned against clustering outcomes. These are two registered
versions of A, not an open representation search.

## Representation B: three engineering mechanisms

Coordinates: (1) mean initial modeled availability; (2) Unconstrained mean
equivalent service-deficit hours; (3) Impact-first minus matched Unconstrained
mean deficit hours. Initial availability represents initial state; baseline
burden includes damage/network/duration effects under idealized resources;
the increment represents combined finite resources, sequence and travel, not
travel alone. It is NOT five-policy MeanDelta. Do not also include total
Impact-first burden, which is their exact sum. Detailed early/late shape is
tested by A and described, not added as a correlated fourth B coordinate.

Use training-cohort means and population SD (ddof=0), with equal squared-distance
budgets 1/3 per construct. Full reference uses the full eligible cohort. This
intentionally tests initial-state information despite its known sparse tail;
do not hide its leverage. Record original-unit profiles and coordinate distance
contributions. A and B have different declared geometries; absolute silhouettes
are not common out-of-sample validation measures. No old equal-RQ budgets apply.

## Fits, computation and reproducibility

K=1..6, K-means++/Lloyd, n_init=50, max_iter=500, tol=1e-4, seeds42..46.
Reference fit per K: minimum full-cohort inertia among these registered seeds,
ties resolved by lower seed. Preserve every label and center. Ward uses the
same representation and Euclidean geometry, compared label-invariantly at
K=2..6. A-PCA is centered projection, not whitening. Equal tract fitting weights.
Single-thread BLAS; record versions and actual parameters. No GMM/medoid/index
search. Internal indices: inertia, full-cohort silhouette and sizes only.

Resampling: the first 30 previously saved 70% and 85% without-replacement draws
from engineering_value_20261015/SUBSAMPLING_ARRAYS.npz; 60 draws per K and
representation. Seed=42+repeat for the refit. Refit preprocessing/PCA, then
predict all tracts. Report full and held-out ARI, Hungarian intersection-aligned
cluster Jaccard, matched original-unit profile changes and all draw results.
Keep older 50%/bootstrap findings as historical, different-design evidence.
Spatial sensitivity: leave out each occupied 20-km EPSG:3310 centroid grid cell,
anchored at (0,0); retain every occupied cell. Refit and predict all tracts;
report withheld and full agreement, sizes, profile error. These blocks are not
independent geographic replications and are not a spatial significance test.

Report seed and Ward ARI, no assumed nested labels; cross-K overlap and stable
membership cores use explicit matching only. Inspect overlap with all 37 frozen
P2/K4 source-proxy tracts, not an arbitrary class-size rejection threshold.
For B, algebraically remove the initial coordinate from saved distances without
refitting or reallocating its budget; report its between-class distance leverage.

## Withheld engineering outcomes and benchmarks

Primary unfitted outcomes: Random-policy total deficit and realization-level
T80 median; C29 and C114 Impact-first total deficit; Northridge, LongBeach and
SanFernando Impact-first total deficit. Also report reduced/increased-resource
changes and Random-minus-Impact changes. T80 is the tract median across frozen
realization first-passage times, with unreached values kept censored, not480h.
Inspect the existing censor flags; do not replace missing times with zero.
Training Impact-first curves and B mechanism components are descriptions, not
validation. Other-policy/scenario outcomes are model-derived supporting evidence,
not independently observed customer outages.

On the same held-out tract splits, predict each outcome from training-group
means. Benchmarks: K=2..6 equal-frequency groups of reference Impact-first burden
or Impact-first realization T80 median; cutpoints learned on training tracts;
OLS and fixed additive spline (4 quantile knots, cubic, Ridge alpha1) of each
registered representation. Compare saved, independently refitted P2/K2..K4
predictions from the identical prior draws; no new P2 fitting. Always report
all outcomes and both sampling fractions; no favorable-endpoint selection.

Reuse earlier conventions: meaningful between-group burden contrasts >=5h,
T80 contrasts >=6h; meaningful held-out MAE improvement >=1h for burden and
>=2h for T80. These are engineering reporting conventions, not clinical or
field-calibrated tolerances. Robust contrast: direction and threshold maintained
in >=90% of registered draws; stable class: median matched Jaccard>=0.75 and
dissolution (J<0.5) in <=10% of draws. Spatial differences must be disclosed even
if random stability passes. Do not combine criteria into a numerical score.

A primary discrete-typology recommendation requires reproducible memberships,
meaningful persistent withheld contrasts AND meaningful predictive/descriptive
advantage over simple recovery groupings across policy and resource endpoints,
without concealing cases better described continuously. Stable quantization of
a gradient is not proof of discrete physical regimes. An inertia/silhouette
maximum alone cannot select K; smooth within-class curves and unstable boundaries
support continuous or optional descriptive representation. No post-hoc minimum
class size. Report all K2..6, with K1/no unique K retained as a conclusion.

## Context after fitting

Describe frozen SOVI, Q1..Q4, population, hospital-linked incidence and geography.
No quartiles recomputed. Contextual contrasts are not validation of physical
recovery. Report within-class SOVI IQR/range and Q4 proportions: similar recovery
can coexist with different vulnerability. Assess incremental social correspondence
using held-out SOVI prediction: baseline fixed additive recovery-response model
plus EPSG3310 x,y,x*y,x^2,y^2; compare addition of class indicators. A >=2-point
MAE improvement and >=5-point mean SOVI contrast are reporting thresholds, not
causal evidence. Frozen geography/trajectories share model assumptions; no IID
spatial p-values, causal claims or intervention-priority claims.

## Deliveries and approval boundary

Three compact diagnostic PDFs: actual mean step trajectories; withheld resource/
policy comparisons; vulnerability and profile/stability context. Full tables
retain every fit/draw/endpoint. Independent tests recheck arithmetic, fitted
labels, integrals, resampling, preserved source hashes and scope. Commit/push
this protocol and source registry before extraction/fitting; then commit/push
the completed package, verify explicit remote heads and actual LFS payload bytes.
Only this new directory may change. No manuscript/figure/Stage7 promotion or merge.
