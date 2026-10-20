# 1021 scientific decision

## Conclusion

**The seven-variable space does not establish one uniquely reproducible discrete
regional community taxonomy. K2 is the strongest coarse partition under random
resampling, but it is not spatially robust enough to call a universal set of
community types. Do not replace K3 automatically with K4 or K5.** The most
defensible manuscript change would be to reduce the claim of discrete types,
and emphasize continuous, scenario- and policy-conditioned community profiles.
A retained K3 would be an explicitly descriptive three-way discretization, not
an independently validated natural number of communities. No formal change is
made here.

## Evidence, not votes

All new fits use the unchanged 2,299-row, seven-coordinate matrix and budgets.
The protocol was pushed as `e10957e0f96be5d80c1e7d4781a84e52afcb6d6b` before
experiments; the implementation/input registry was pushed as
`0c344e7d8b5e8cc0f6cc073e1d8c2bcfdf8d785d`. Full experiments use 64 references
per Gap null, 50 random splits, 20 spatial-cell splits and 100 bootstraps.

| Resolution | Mean silhouette across seeds | Random prediction strength | Spatial prediction strength | Cluster-wise bootstrap mean J range |
|---|---:|---:|---:|---:|
| K2 | 0.24244 | 0.90032 | 0.71165 | 0.960-0.975 |
| K3 | 0.24872 | 0.53529 | 0.53113 | 0.579-0.916 |
| K4 | 0.25305 | 0.60153 | 0.40280 | 0.671-0.937 |
| K5 | 0.26327 | 0.52756 | 0.39307 | 0.547-0.925 |
| K6 | 0.25997 | 0.54617 | 0.36173 | 0.754-0.936 |

Prediction strength is minimum validation-cluster pair agreement, averaged over
both split directions and repetitions. Bootstrap J uses unique in-bag support,
not duplicated draws; columns above do not represent independent votes.

**Gap:** both registered references select K1 using the smallest-K one-SE rule.
Axis Gap falls from 1.76755 at K1 to 1.38774 at K2; PCA Gap falls from 1.87432
to 1.65698. MCSEs are about 0.0010-0.0014, much smaller than these first-step
differences. The PCA curve subsequently rises and is highest at K8; choosing
that global maximum instead would switch the preregistered rule after seeing
results. Both curves are nonmonotone, not evidence of a sharp K3/K4 elbow.

K1 here means no extra partition under these particular box-reference rules,
not that the tracts are physically homogeneous or that continuous structure is
proved. Uniform boxes cannot reproduce the zero-heavy initial-state marginal,
boundedness, network dependencies or spatial structure of these inputs. PCA
rotation changes the reference support, not this limitation. No null model
with preserved mechanistic dependence was tested.

**Prediction strength:** only K2 reaches the registered mean 0.8 and 0.9
conventions on random splits. Its mean 0.90032 is only marginally above 0.9;
split SD is 0.04802 (MCSE about 0.00679). P10-P90 is 0.84160-0.95461;
20/50 splits are below 0.9 and one below 0.8. No tested K reaches 0.8 on the
20-km spatial split. No singleton/undefined pair statistic occurred, although
validation groups as small as four tracts occur at higher K. Their finite pair
denominators are retained, not suppressed.

**Other internal indices:** CH is highest at K2, DB lowest at K6, and mean
silhouette highest at K5. The latter is 0.26327, with substantial seed
dependence at K5; these modest compactness/separation values are not external
validation. WCSS decreases smoothly. K2-8 are all reported, including negative
silhouettes and per-cluster distributions.

**Algorithm and geography:** Ward/K-means ARI is 0.553, 0.683, 0.650 and 0.675
at K2-5. Thus even the best random-resampling resolution is not recovered
unchanged by another Euclidean compactness procedure. Leave-quadrant-out
held-out ARI ranges are 0.371-0.881 (K2), 0.302-0.872 (K3), 0.229-0.800 (K4),
and 0.282-0.948 (K5). The 20-km design has only 15 occupied cells, shares
unbuffered boundaries, and can place all 37 proxy-associated tracts on one
side. This is a geographic-transfer sensitivity, not independent spatial
validation. These new quadrants use centroid coordinate medians; they must
not be equated with earlier different geographic block constructions.

## What the partitions describe

Reference fits use the lowest WCSS across seeds 42-46, as preregistered. Their
numeric cluster IDs are model-specific, not the official C1/C2/C3 registry.

- K2: 849 tracts / 3,021,555 residents versus 1,450 / 6,044,967. Mean spectral
  impact is 0.269 versus 0.021; baseline deficit 35.18 versus 29.52 h; added
  constraint deficit 5.17 versus 2.31 h; SOVI 49.04 versus 76.73. This is a
  meaningful coarse contrast, with broad within-class overlap, not a causal
  assertion that social vulnerability protects service.
- K3: reference sizes 428/1,239/632. It separates greater constraint increments
  (7.10 h) from higher baseline burden (37.23 h) and the larger, higher-SOVI
  group (78.78; increment 1.75 h). This is interpretable, but the 428-member
  class has mean bootstrap J 0.579 and dissolution frequency 50%. Interpretability
  therefore does not establish reproducibility. Seed 42 exactly reproduces the
  historical K3; the preregistered minimum-WCSS seed 46 differs slightly
  (historical ARI 0.99411). Neither historical labels nor official outputs changed.
- K4: reference sizes 1,217/429/616/37; seed 42 exactly matches historical K4.
  It isolates the initial-state proxy group, but several main classes also
  show bootstrap dissolution. Spatial prediction strength is lower than K3,
  despite earlier geographic checks favoring K4 under their different design.
- K5: reference sizes 588/37/432/1,230/12. The 12-member class represents 754
  residents and contains five of the eight zero-housing tracts. Its mean
  bootstrap J is 0.547 and dissolution frequency 44%. Its small size alone is
  not a rejection criterion; its instability, specialized population support
  and sensitivity to optimization are the relevant cautions. Do not choose K5
  solely because mean silhouette is highest.

The profile differences above are in fitting variables and are descriptions,
not independent scientific validation. Quartile composition and population
coverage are fully reported in `outputs/ORIGINAL_UNIT_PROFILES.csv`.

## The 37-tract group: stable conditional state, not established resilience

The exact historical set is exported with original GEOIDs and populations.
It represents 130,518 residents (1.440%). Its mean Init_Supply is 0.017523:
only 1.752% initial modeled availability, not high absolute electrical service.
Mean Unconstrained burden is 21.75 h and added constraint burden 8.05 h.
Its frozen-model association with the retained STATION Q Core-source proxy
is prior physical-model evidence, not newly simulated or independently
physically validated here.

For the original matrix, K4 seed comparisons give rare-set J 0.974-1.000.
But unique-in-bag bootstrap J has mean 0.671, P10 0.0746, P90 1.000,
dissolution frequency 32%, and recovery frequency 67%. Full-support predicted
J is 0.673, dissolution 31%. Ward does not isolate the same set at K4
(J 0.122), but captures more of it at K5-8 (J 0.730).

Removing only Init from distance, WITHOUT redistributing its budget, reduces
rare-set J to about 0.079 at K4 while whole-partition ARI remains 0.935-0.949.
Thus much of the broader partition persists but the rare distinction depends
strongly on this coordinate. This is not the historical ablation that also
redistributed RQ1 weights. It is not a recommendation to delete Init.

Init has 1,533 exact zeros (66.681%); the 23 largest centered squared
deviations account for 62.480% of its variance. Neither this sparsity nor the
group's size makes it invalid. They explain why geometric stability must be
separated from the plausibility of the Core-source representation. Weak
prediction-strength classes are not consistently just the rare group:
their average rare-set fraction is below 9% at random-split K4 and below
0.2% at spatial-split K4.

## Policy dependence and scope

Existing, hash-checked policy-set evidence is copied as PRIOR evidence, not
newly fitted. For P2 K3, policy-set ARI is 0.619-0.793 with cohort scaling and
0.603-0.831 with fixed main-five scaling; K4 is 0.553-0.858 and 0.556-0.842.
These include the registered leave-one-policy-out and plus-Random comparisons.
This dependence persists despite random-seed stability. Vulnerability-first
uses frozen Q4 in its policy construction; SOVI also enters the clustering.
No quartile or policy has been recalculated. No claim of external validation
is based on the shared recovery/SOVI information.

## Decision boundary

Favor continuous burden/network/vulnerability descriptions in strong scientific
claims. If a categorical summary is needed, K2 has the clearest random-sample
support, while K3 remains a useful but conditional three-profile description.
Neither is certified as a unique regional truth. K4 should be retained as a
source-state sensitivity, not promoted solely on previous geographic results;
K5 has no combined validation advantage sufficient to override these problems.
Additional work would need independent empirical service/engineering evidence
or a justified dependence-preserving null, not another unconstrained K search.
Author approval is required for any change in the manuscript's typology claim.

## Numerical QA note

All observed WCSS, 1,024 null-fit WCSS/draw hashes, 700 prediction-strength
directions and 4,000 bootstrap set comparisons were independently recalculated.
sklearn's tolerance-stopped fitted centers differ slightly from means of final
reassigned labels: maximum re-centering gain is 0.009421 WCSS. The verifier
uses the ACTUAL fitted centers for the actual objective; no tolerance was
relaxed and no fit was altered. PCA replay uses the same registered single-
thread arithmetic to reproduce draw hashes exactly. All 950 protected files,
original-worktree status/index and formal tracked artifacts remain unchanged.
