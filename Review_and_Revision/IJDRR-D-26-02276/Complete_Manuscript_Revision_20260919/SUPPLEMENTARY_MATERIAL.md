# Supplementary material for distributional consequences of postearthquake restoration sequences

This supplement provides reproducible definitions, candidate history, additional statistical summaries, and limits on the interpretation of saved evidence. All scientific outcomes refer to result commit 87110dad035ddb6eb694235330cd2547d9ba5588. Main-text sequence labels Balanced and HospFirst denote recovered deterministic weighted-priority initializers; Efficiency denotes the retained finite-budget search candidate. File labels GA-Balanced and GA-HospFirst are retained only for provenance.

## S1 Data domains and physical scenario

### S1.1 Task and service domains

The 310-record inventory is distinct from its 302-asset scheduling component and the 196-node SCE candidate-service layer. Inventory records 301479, 303265, 304137, and 305021 have unresolved network registration and retain missing state. Records 306980 and 309598 are identified but source-unreachable in the reference representation. Records 303547 and 307683 belong to a separate two-node component without a resolved strict-SCE attachment. None of these eight records is assigned a task. For the identified nontask records, the retained no-damage raw representation is kept; connectivity still determines their effective state. No repair of an excluded record is fabricated.

The primary component contains 20 of the 21 reference source IDs; the other source is in the separate component. Source membership is fixed, but a source is active only if its raw functionality meets the threshold. The reference IDs are 300232, 301318, 302376, 302865, 303473, 303547, 306001, 306365, 306450, 306473, 306489, 307039, 307373, 307512, 307693, 308540, 308581, 309553, 309569, 309703, and 310199. This is not an inventory of verified generation capacity or actual plant operating status.

Strict-SCE membership uses full tract polygons and agreement of the CEC and SCE territory layers, rather than tract centroids or city names. The public SCE circuit, substation, and named-system records provide candidate and attachment evidence. Class A uses physical identity, B a unique supported named-system interface, and C no usable match. Equal candidate weights do not estimate load shares. Population is a tract count, not electricity demand or customer count. The retained coverage file contains the exact population and SOVI values used in every result.



Table S1. Tract evidence strata and population.

| Stratum | Candidate composition | Tracts | Population |
|---|---|---|---|
| S1 | A only | 444 | 1,936,737 |
| S2 | Resolved A/B; no C | 318 | 1,384,566 |
| S3 | Resolved A/B with C | 43 | 199,079 |
| S4 | C only; normalized burden NA | 12 | 51,770 |

Total: 817 tracts and 3,572,152 people. Classes A/B/C refer to attachment evidence, not utility ownership.



S1 direct-only tracts contain 1,936,737 people; S2 tracts with resolved A/B but no C contain 1,384,566; the partially unresolved S3 group contains 199,079; and S4 contains 51,770. Fifty-five tracts contain some Class C mass, but only twelve have no represented portion. Unresolved candidate mass and population living in partly unresolved tracts are different quantities. Missingness is not demonstrably random: the retained population-weighted SOVI mean is 81.52 in S4 versus 70.74 in S1. No imputed recovery value is assigned to S4.

### S1.2 Hazard and fragility

Station PGA comes from the frozen 2%-in-50-year CGS field. The preprocessed station table, not a new nearest-station substitution, supplies all 302 values. The active anchored parameterization assigns low voltage from 34.5 to below 150 kV, medium from 150 to below 350 kV, and high at 350 kV or above, using retained maximum voltage attributes. These classes contain 249, 51, and two task assets. Some inventory voltages were inferred during the earlier source-data preparation; this parameter coverage does not validate every individual asset's equipment or anchorage. No new fragility class was created for this comparison.



Table S2. Adopted anchored fragility parameters.

| Voltage class (assets) | Parameter | DS1 | DS2 | DS3 | DS4 |
|---|---|---|---|---|---|
| Low (249) | Median PGA, g | .15 | .29 | .45 | .90 |
| Low | Log dispersion β | .70 | .55 | .45 | .45 |
| Medium (51) | Median PGA, g | .15 | .25 | .35 | .70 |
| Medium | Log dispersion β | .60 | .50 | .40 | .40 |
| High (2) | Median PGA, g | .11 | .15 | .20 | .47 |
| High | Log dispersion β | .50 | .45 | .35 | .40 |

Low: 34.5–<150 kV; medium: 150–<350 kV; high: ≥350 kV. These adopted classes do not establish asset-specific calibration.



For class-specific median μ(d) and log dispersion β(d), the exceedance probability is Φ((ln PGA−ln μ(d))/β(d)). Adjacent exceedances give mutually exclusive DS probabilities; the first and last categories use one minus the DS1 exceedance and the DS4 exceedance. At five stations, adjacent adopted curves cross slightly, producing negative DS2 probabilities before cleanup. Negative category mass was clipped to zero and the five rows renormalized in the frozen probability table. This is a disclosed local regularization of nonnested curves, not machine roundoff and not evidence that every hazard input is invalid.

The negative magnitudes were 1.9196×10⁻⁵ at 300429, 1.7675×10⁻⁵ at 301214, 1.5007×10⁻⁶ at 306152, 1.7990×10⁻⁵ at 306489, and 1.1343×10⁻⁶ at 307693. The largest absolute category-probability change was 1.9196×10⁻⁵ and the largest absolute expected-workload change was 0.000554 h. These frozen corrections apply identically to every sequence. They are not silently replaced during manuscript preparation.

### S1.3 Stored uncertainty and event execution

The master seed is 42. For realization IDs 0–31, a SeedSequence formed from master seed and realization ID supplies separate damage and duration streams. One uniform variate per station selects from the frozen damage CDF. A second stream supplies the inverse CDF of the relevant Normal distribution conditioned above zero. DS0 receives no task and zero duration. The stored vectors, rather than new draws, are used in the corrected reevaluation and both targeted comparisons. The sample averages 300.469 damaged assets, with a range of 298–302. Mean DS0–DS4 counts are 1.531, 4.250, 12.219, 125.625, and 158.375. The strong represented damage reflects the fixed intensity/fragility scenario; it is not a claim about a typical Los Angeles earthquake.

Each crew begins available at zero. Its earliest-release event is selected by available time then numeric crew index. For the next fixed-list task, arrival equals release plus base-to-task or previous-task-to-task directed travel. Completion adds the supplied realized duration; the same time releases the crew and changes raw functionality to one. There is no second CDF restoration clock, task reranking, duration foreknowledge for priority, or simultaneous crew sharing. Event integration uses zero plus unique completion times. All represented service deficits are zero at the final completion horizon in the retained runs.

Road times come from the retained OpenStreetMap directed-road graph and explicit access representations. Existing-edge projection preserves direction and travel-time convention. Facility-centroid access connectors use the stated 15 km/h design speed; they are not mapped internal facility roads. All 11×302 base-to-task and 302×302 task-to-task cells are supplied without fallback. C57 retains an allocation proxy totaling 47 LADWP-labeled and ten SCE-labeled crews at eleven origins. Eligibility is pooled, regardless of these labels. No claim is made about actual emergency staffing, legal mutual aid, road damage, or shifts.

## S2 Priority construction and candidate provenance

### S2.1 Components and the surrogate

For each service candidate, population priority sums tract population times its candidate weight. Hospital priority sums a binary hospital-tract indicator times that weight. SOVI priority sums population times NRI-derived SOVI_SCORE times weight. All SOVI values in the domain are finite and positive; the minimum is 1.81, so the nonnegative shift is zero. Candidate priorities aggregate to their selected A/B upstream asset. Class C population candidate mass 145,897.583, hospital candidate mass 0.6667, and SOVI-weighted candidate mass approximately 9,848,051.566 remain unassigned. There is no redistribution to A/B assets.

Each asset component is min–max normalized across the task domain. Hospital-first sorts hospital score descending, population score descending, then station ID ascending. Balanced and HospFirst initializers sort their weighted priority descending with the original domain order resolving ties. Efficiency uses its retained search permutation. Every sequence contains all 302 IDs once; execution removes DS0 without reranking.

For policy p, q(i)=[w(pop)Pop(i)+w(hosp)Hosp(i)+w(sovi)SOVI(i)]/[w(pop)+w(hosp)+w(sovi)]. Expected workload is Σ(d=1..4)P(i,d)E[T(d)|T(d)>0]. The conditioned means are 1.0276239313, 6.1657435880, 12.0177513562, and 36.0532540685 h. Surrogate decoding schedules every domain asset with these expected workloads, the same C57 origins, and directed travel. Its fitness is weighted completion benefit minus makespan penalty, evaluated with a horizon of 504 h fixed before the search.

Fₚ = Σᵢqᵢ max(Tₘₐₓ − Cᵢ, 0) / (Tₘₐₓ Σᵢqᵢ) − wₘ Cₘₐₓ/Tₘₐₓ;  Tₘₐₓ = 504 h.  (S1)

This formula represents additive station completion value. It contains no explicit source-dependent marginal benefit, cumulative tract burden, Gini, group gap, or optimized community equity. Hospital weight 20 is a policy-design choice defining a hospital-dominant benchmark. It is not calibrated to preferences or utility data. The old source-role/voltage/line-count importance blend is absent.

### S2.2 Search budget and correction of candidate retention

The original search comprised ten seeds (42–51) per objective, population 100, and 100 generations. Each initial population included 98 random permutations, a descending-priority initializer, and an ascending-expected-workload initializer. Ordered crossover used probability 0.8; inversion mutation probability 0.2; tournament size was three. Generational replacement was nonelitist and the stopping rule was the same fixed budget for every seed. A retained five-generation same-seed repeat had exact matching results. Ten final sequences per policy were distinct, and the late-generation improvements and seed spread did not establish convergence to an optimum.

The original output chose the best member of the final generation. Saved generation scores show higher earlier fitness in 28 of 30 runs. For Balanced and HospFirst, the deterministic priority initializers can be reconstructed from the frozen inputs and reach the highest recorded objective values, at generation zero. These are the two candidates now reevaluated. Other unsaved intermediate chromosomes are not reconstructed or assigned hypothetical community outcomes. Efficiency retains the saved best final sequence, seed 47, which reaches that policy's highest recorded score.

An independent best-so-far archive and explicit deterministic-incumbent comparison now prevent returning a known inferior candidate. The archive does not enter selection or replacement and consumes no additional random variates. No search was rerun for this correction. Figure S1 displays the retained generation-best records, which can decrease under nonelitist replacement; they are not mislabeled best-so-far curves. Table S3 separates original returned scores, recoverable candidates, and the same-objective Hospital-first benchmark. Scores in different objective rows cannot be compared as a common utility scale.



Table S3a. Policy-design coefficients.

| Objective | Population | Hospital | SOVI | Makespan |
|---|---|---|---|---|
| Balanced | 1 | 3 | 1 | 0.5 |
| HospFirst | 1 | 20 | 1 | 0.1 |
| Efficiency | 1 | 1 | 1 | 2 |

The first three coefficients normalize service priority; the last penalizes makespan separately. All are design assumptions.





Table S3b. Same-objective candidate scores and provenance.

| Objective | Original returned | Adopted candidate | Hospital-first |
|---|---|---|---|
| Balanced | 0.780985337154 | 0.793690122004 | 0.792733835572 |
| HospFirst | 0.900607781997 | 0.916459946176 | 0.916319981609 |
| Efficiency | 0.368272354637 | 0.368272354637 | 0.338924957558 |

Compare columns within a row only. Balanced/HospFirst adopted candidates are reconstructed deterministic priority initializers; Efficiency is the saved seed-47 search sequence. Unsaved intermediate chromosomes and global optima are not claimed recovered.



![Figure S1. Retained generation-best fitness records for ten seeds per objective. Dashed lines show the adopted candidate scores. Nonelitist records may decrease; these are not best-so-far curves. Scores cannot be compared across policy objectives. Balanced/HospFirst adopted sequences are reconstructed deterministic initializers; no new search was run.](Figures/Figure_S1_Search_records.png)

Figure S1. Retained generation-best fitness records for ten seeds per objective. Dashed lines show the adopted candidate scores. Nonelitist records may decrease; these are not best-so-far curves. Scores cannot be compared across policy objectives. Balanced/HospFirst adopted sequences are reconstructed deterministic initializers; no new search was run.

Across the original ten final-generation results, mean (SD), min, and max fitness were Balanced 0.7597 (0.0134), 0.7427–0.7810; HospFirst 0.8851 (0.0106), 0.8655–0.9006; and Efficiency 0.3279 (0.0262), 0.2904–0.3683. Mean improvement over the final 20 generations was 0.0014, 0.0028, and 0.0031, respectively. These are historical finite-budget diagnostics, not the corrected candidate scores. Balanced/HospFirst search did not establish improvement over their recoverable initializers. Their new performance must not be credited to genetic evolution.

Balanced and HospFirst share the same exact rank as Hospital-first for 195 and 224 of the 302 assets, respectively; Efficiency shares one. Sequence selection used the original ex-ante objective, never the corrected community outcomes. Nevertheless, the 32 physical realizations had already been used for evaluation: this is a corrected comparison on an existing evaluation sample. No further outcome-driven candidate selection was performed, and no independent generalization claim follows from the paired intervals.

## S3 Statistical definitions and additional results

### S3.1 Population denominators and group membership

The population-weighted normalized measure averages N(r)=B(r)/R(r) with full tract population over R>0. It estimates the average deficit duration of each tract's represented candidate portion, weighted by the people living in that tract. The availability-consistent measure averages the same N with population×R weights. It estimates deficit across the represented population–candidate mass and is exactly the area below resolved population availability. Neither denominator creates information for the unresolved portion. Twelve tracts with R=0 are excluded from both normalized measures and retained as unresolved in population partitions.

SOVI quartiles use the empirical tract distribution, not population-equal groups, and are fixed before strategy comparisons. Ties at cutpoints are retained according to the original quantile binning. Cutpoints are approximately 1.810, 52.640, 75.350, 88.390, and 99.840. Main-text Q4 denotes higher values of the NRI-derived score, not CDC SVI and not a causal designation of individual hardship.



Table S4. Fixed vulnerability quartiles and metric denominators.

| Quartile | All tracts | All population | Population in R>0 tracts |
|---|---|---|---|
| Q1 | 205 | 812,549 | 808,424 |
| Q2 | 205 | 915,074 | 907,863 |
| Q3 | 203 | 910,124 | 890,003 |
| Q4 | 204 | 934,405 | 914,092 |

Quartiles use tract NRI-derived SOVI_SCORE. Population-normalized group burden uses the final column, not the total population column.



Within each realization, Gini uses the population-weighted Lorenz curve of N among R>0 tracts. Equivalently, it is the weighted sum of absolute pairwise burden differences divided by twice the weighted mean times squared total weight. An all-zero burden vector is assigned Gini zero; no fully unresolved tract is assigned a numeric N for this calculation. Quartile burden uses each group's own identifiable population denominator. Hospital burden is the simple mean across 47 hospital tracts rather than a hospital-record or population-weighted mean.

### S3.2 Pairing and classification

For each metric, the strategy effect is its value minus Hospital-first in the same realization and condition. The DS4 interaction is the DS4×2 strategy effect minus the corresponding baseline strategy effect. The same realization bootstrap indices are used throughout: 10,000 resamples, seed 20260919, percentile 2.5% and 97.5% endpoints. The unit is the physical realization, not tract or strategy. These pointwise intervals are not familywise error-controlled tests. Baseline results reused from the original evaluation retain their point values; common bootstrap indexing can slightly change interval endpoints relative to earlier seed-offset calculations.

For winners and delays, ΔN is the paired tract-normalized burden difference. Improved means ΔN<−1 h; worsened means ΔN>1 h; otherwise near-zero. The threshold is practical and does not encode statistical significance or equivalence. One statistic classifies each tract's average ΔN across realizations, then sums population. The other classifies each realization first and averages its population shares. Direction probability is the fraction of realizations with ΔN<0, without the ±1 h threshold, and is NA for fully unresolved tracts. Percentages in the main text use the full 3,572,152-person domain; corresponding identifiable-population percentages remain available in the saved table.



Table S5. Baseline population classification under two averaging operations.

| Sequence | Mean-effect improved | Mean-effect worsened | Realization-first improved | Realization-first worsened |
|---|---|---|---|---|
| Balanced | 13.02% | 1.10% | 15.02% | 6.23% |
| HospFirst | 7.37% | 0.33% | 7.75% | 3.64% |
| Efficiency | 1.74% | 80.07% | 13.31% | 76.57% |

All percentages use 3,572,152 people. Mean-effect classification applies ±1 h to each tract’s 32-realization mean; realization-first classifies each draw then averages shares. Unresolved is 1.45% in both. The ±1 h threshold is not a significance test.



The two averaged population measures agree on the main baseline ordering, but their magnitudes differ. Evidence-stratum differences also remain visible: relative to Hospital-first, Balanced/HospFirst mean population-normalized burdens are −0.298/−0.210 h in direct-only tracts, −0.343/−0.148 h in resolved A/B tracts without C, and +0.066/+0.133 h in partly unresolved tracts. These are descriptive strata, not randomized causal subgroups. Figure S2 displays this boundary rather than implying that every evidence class benefits.

![Figure S2. Denominator and representation boundaries. Panel A separates direct-only, resolved A/B, and partly unresolved evidence strata. Panel B compares full-population weighting of normalized tract burdens with population×resolved-mass weighting. These are descriptive strata; fully unresolved tracts have no numeric burden and are not plotted as zero.](Figures/Figure_S2_Denominators_and_coverage.png)

Figure S2. Denominator and representation boundaries. Panel A separates direct-only, resolved A/B, and partly unresolved evidence strata. Panel B compares full-population weighting of normalized tract burdens with population×resolved-mass weighting. These are descriptive strata; fully unresolved tracts have no numeric burden and are not plotted as zero.

The full electronic statistical tables accompanying the manuscript contain means, SD, medians, IQR, paired effects, direction frequencies, and lowest-metric frequencies for all reported conditions. T50/T80/T90 and logistics values are absent for offline A/B conditions because their trajectories were not reconstructed. Table S5 focuses on the distinction between mean-effect and realization-first population classifications; the electronic tables preserve the remaining metric detail without expanding the main text into a catalogue of ranks.

## S4 What the targeted contrasts can identify

### S4.1 Candidate influence contrast

For mixed A/B tracts, the weight changes preserve total A+B mass and all C weights. They do not reallocate mass at the time of missing state; they specify alternative fixed evaluation weights. Sequences and their source-connected states are unchanged. With interface deficit I(i)=∫[1−effective(i,t)]dt, tract burden is a linear sum of identifiable interface deficits weighted by the candidate-to-interface incidence matrix. This permits offline reevaluation of integrated burdens.

New Balanced/HospFirst baseline runs save the interface integrals directly. Old Hospital-first/Efficiency baseline files retain tract-integrated burdens. The corresponding incidence matrix has 117 upstream targets but rank 116; interfaces 300829 and 303005 cannot be individually identified from those data and remain a combined contribution. The frozen candidate influence contrasts are identifiable without splitting that pair. Baseline reconstructed burdens differ from retained values by less than 2×10⁻¹² h. This numerical statement establishes consistency of this linear calculation, not feeder validation or recovery of event-time information.

Class B's own distribution-asset damage is not supplied by the influence test. Nor does it estimate true A/B load shares or test a policy newly designed for those shares. The λ values 0.5 and 2 are prespecified design stresses. Population-effect directions persist, while Efficiency's signed group-gap point estimate crosses zero and its Q4 excess changes by roughly one hour on either side of baseline. Claims should distinguish overall direction from group-level sensitivity.

### S4.2 Severe-damage relative duration contrast

The same stored DS vector and the same policy list are used, with DS4 duration doubled and all other durations unchanged. It is necessary to recompute scheduling because crew availability and later travel origins depend on previous completion. The test is not an optimization under the doubled expected workload. It is also not a uniform rescaling of trajectories, a resampling experiment, or evidence that a 72 h DS4 location parameter is more realistic.

For Balanced and HospFirst, both baseline and DS4×2 task events were saved. Their mean counts of changed crew assignments are about 220 per realization; average arrival increases by approximately 32.14 h. This supports a logistics explanation for why a new schedule is needed. It does not by itself assign every community difference to a station's own completion. Old baseline Hospital-first/Efficiency task events were not recreated through additional simulations.

The upstream contribution table provides an additive accounting of population-normalized burden contrasts. In the baseline Efficiency–Hospital-first comparison, interfaces 310167, 302187, and 301489 contribute about 2.375, 2.363, and 2.027 h, increasing to 4.166, 4.008, and 3.464 h under DS4×2. They are model interface contributions, not proven real-world critical facilities or causal explanations for community vulnerability. No arbitrary attribution is made within the unresolved 300829/303005 pair.

## S5 Reproducibility and retained evidence

Scientific result commit 87110dad035ddb6eb694235330cd2547d9ba5588 retains original and corrected results separately. The correction executed 64 new baseline chains for Balanced/HospFirst and reused the original 64 Hospital-first/Efficiency chains. The severe-damage comparison executed 128 chains. These 256 policy–condition evaluations use only the original 32 sets of physical samples. Offline λ comparisons add no physical chains. A recorded initial input-type failure occurred before scheduling and produced no scientific trajectory; it is not hidden or counted as an additional completed realization.

The folder Targeted_Methodological_Strengthening_20260919 contains FROZEN_CANDIDATE_SEQUENCES.csv, CANDIDATE_OBJECTIVE_COMPARISON.csv, REALIZATION_STRATEGY_METRICS.csv, PAIRED_EFFECTS.csv, GROUP_ABSOLUTE_BURDEN.csv, TRACT_PAIRED_EFFECTS.csv, WINNER_LOSER_POPULATION.csv, and TARGETED_SCIENTIFIC_EVIDENCE.npz. The checkpoint archive and compressed task-event table preserve the new trajectories and schedules. The separate original pilot folder retains the 32 physical vectors, damage probabilities, final-generation candidates, and generation records. No original artifact has been overwritten.

Source provenance is distinct from output reproducibility. The retained 310 input-readiness table supplies PGA and adopted fragility parameters; CEC/HIFLD inputs provide inventory and network geometry; CGS Map Sheet 48 supplies the primary intensity field; official SCE planning GIS supplies candidate evidence; the frozen coverage table supplies tract IDs, population, NRI-derived SOVI, and hospital indicators; and directed OpenStreetMap routing plus explicit access proxies supplies travel. The table values are the versioned inputs, not a claim that the latest online datasets are identical. Provider terms govern third-party redistribution.

The reproducibility package does not make the model a validated predictor. Its fixed graph, 21-source reference scenario, candidate weights, residual functionality assumptions, uncalibrated task durations, independent conditional damage draws, and pooled crews remain the conditions under which the comparisons apply. Main-text references provide the cited literature and data-provider links.
