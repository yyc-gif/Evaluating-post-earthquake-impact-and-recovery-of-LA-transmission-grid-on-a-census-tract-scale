# Engineering value of the seven-variable community representation

## Decision

**K3 has limited, interpretable engineering value as a descriptive compression,
but does not gain sufficient support as a reproducible three-type classification.
Retain it only as an optional descriptive representation. Prefer continuous
recovery/context relationships for substantive claims; K2 captures much of the
dominant held-out recovery contrast. Do not promote K4 automatically.**

This is not a finding that all tracts behave alike. It separates useful recovery
patterns from a claim that individual tracts belong to stable discrete types.

## What was actually tested

Protocol d64cc2dd3a3ed9f733414a0dd32149bf9343d9d9 was pushed before new
class-outcome comparisons. All 2,299 tracts, seven coordinates and budgets are
unchanged. The actual historical K3 (1,235/428/636) and K4 (37/1,217/429/616)
are compared with the earlier registered K2. No additional K search occurred.

Eight saved cases and 3,000 event-state records were source/hash checked.
Thirty-four evaluated outcome summaries are NOT 34 independent validations:
many summarize the same recovery paths. Random-policy results are excluded
from fitting, but share frozen network/damage/mapping assumptions. Resource
and alternative-hazard cases are additional model scenarios, not external
observations. None demonstrates observed customer-outage accuracy.

## Evidence for useful engineering descriptions

Equal-tract class means (deficit hours, or mean of tract realization-median
time to 80% modeled service) are:

| Historical K3 class | Tracts | Random-policy deficit | Time to 80%, Impact priority | Deficit with 29 crews |
|---|---:|---:|---:|---:|
| C1 | 1,235 | 37.03 h | 33.26 h | 40.04 h |
| C2 | 428 | 34.59 h | 36.07 h | 55.80 h |
| C3 | 636 | 47.89 h | 39.96 h | 47.65 h |

C3 has greater burden under Random; C2 instead has the greatest burden when
crews are reduced to 29. Thus a single ordering of good/bad recovery types is
inadequate. This provides model-internal support for distinguishing baseline
network/recovery difficulty from sensitivity to limited restoration resources.
It does not prove that K3 is needed to express those mechanisms: they are
already continuous dimensions represented in the fitted variables.

C2 exceeds C1 by 15.76 h in the 29-crew case, and this sign/difference remains
above the preregistered 5-h threshold in all 200 subsamples. However, its
8.15-h excess over C3 persists as a >=5-h difference in only 62% of 70% samples
and 55% of 85% samples, below the registered 80% persistence convention.
The C1-C3 contrasts are more reproducible: Random deficit differs by 10.85 h
and Impact-priority recovery time by 6.70 h; both exceed registered thresholds
in every subsample. K2 already captures a broad related contrast.

## Held-out value relative to simpler representations

Each of 100 samples at 70% and 100 at 85% refitted K2/K3/K4 using training
features only; outcome means were estimated only on training tracts. Quantile
benchmarks learned their cuts on training data. All paired results are retained.

| Outcome | K2 MAE | K3 MAE | K4 MAE | Continuous linear | Continuous additive |
|---|---:|---:|---:|---:|---:|
| Random-policy deficit | 5.382 h | 5.114 h | 4.933 h | 4.313 h | 3.768 h |
| Impact-priority tract-median T80 | 4.762 h | 4.799 h | 4.806 h | 2.626 h | 1.952 h |

K3 improves Random-deficit MAE over K2 by only 0.281 h (70%) and 0.255 h (85%),
below the preregistered notable 1-h improvement in every repetition. It does
not improve the time-to-80% outcome over K2. Baseline-deficit thirds perform
about as well for Random deficit, and better for time to 80%. K3 outperforms
SOVI-only or constraint-increment-only thirds for some outcomes, so it is not
merely a vulnerability ranking; it nevertheless does not dominate appropriate
simple benchmarks.

In the 29-crew case, K3 gains only 0.501/0.446 h over K2; constraint-increment
thirds perform better than K3. Across the five prespecified transfer contexts,
mean K3 gains over K2 remain below 1 h. Northridge is the strongest case
(0.801/0.724 h), but only 62%/50% of repetitions reach the 1-h convention.
The additive continuous model outperforms K3 in all those contexts.

These are tract-level model-outcome prediction comparisons, NOT predictions
on independent earthquake realizations or empirical outages. Continuous models
are fixed, untuned benchmarks, not asserted to be optimal physical models.
Clusters, being functions of the seven inputs, cannot add information beyond
those inputs in the information-theoretic sense.

## Membership and cross-K persistence

| K | Mean all-tract ARI, 70% | Mean all-tract ARI, 85% | Pooled stable cores by reference class |
|---|---:|---:|---|
| 2 | 0.967 | 0.976 | 828/849; 1,424/1,450 |
| 3 | 0.840 | 0.828 | 1,206/1,235; 41/428; 581/636 |
| 4 | 0.903 | 0.957 | 0/37; 1,184/1,217; 352/429; 572/616 |

Core means >=90% agreement with the original class across all 200 fits, not
an eligibility filter. Held-out-only frequencies lead to the same 41-tract C2
core. All 37 historical Q-proxy tracts belong to those 41. The durable part of
the 428-tract class is therefore mainly the known initial-state source-proxy
exception, not the full broad resource-sensitive group. Even the mean Random
burden of that core (24.02 h) is unlike the whole C2 (34.59 h).

Larger samples do not uniformly rescue K3: its C2 profile stays within the
registered Random-deficit tolerance in 62%/55% of repetitions. Its 29-crew
profile meets tolerance in 62%/55%. K4 improves the stability of the broader
groups, but the rare group has no pooled >=90% core and does not yield a
material primary-outcome prediction improvement over K3. No class is rejected
because it is small.

K2 and K3 are not nested: 237 C2 tracts belong to one K2 group and 191 to the
other. Their label-invariant ARI is 0.640. K3-K4 ARI is 0.911; 386 C2 members
join K4's main constraint-related class, 37 join its source-proxy class, and
five join another class. Best matches and all overlap cells, not a forced
one-to-one cross-K mapping, are reported.

Earlier 50% prediction-strength and bootstrap results remain unchanged.
Prediction strength and this follow-up's ARI are different estimands; higher
70/85% ARI is not evidence that the earlier weak split-prediction result was
incorrect. No new spatial validation has been manufactured; previous geographic
and policy-set dependence still limits generalization.

## Scientific claims that are and are not supported

Supported: under the frozen model, communities with similar baseline deficits
can differ in their response to restoration-resource and priority choices.
A three-profile display can help describe this interaction, provided uncertain
memberships and the source-proxy mechanism remain visible.

Not supported: three naturally distinct, externally validated or individually
stable community regimes; a universal high-risk/high-vulnerability/slow-recovery
ordering; improved outage prediction over continuous seven-input descriptions;
or physical resilience inferred from the Q-linked group's higher initial service.

Recommendation: retain K3 only as an optional model-conditioned descriptive
summary. K2 is the stronger coarse partition, but is not a substitute for the
continuous restoration and community-context evidence. Any manuscript change
still requires author approval; no official artifact is changed here.
