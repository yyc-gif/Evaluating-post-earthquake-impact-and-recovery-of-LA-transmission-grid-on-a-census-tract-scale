# Distributional consequences of postearthquake restoration sequences under uncertain task workloads in Los Angeles

Yinchen Yi, Yutong Li, and Marta C. González

Department of Civil and Environmental Engineering, University of California, Berkeley, Berkeley, CA 94720, USA

Corresponding author: Yinchen Yi; nemoyi@berkeley.edu

## Abstract

Restoration sequences can redistribute community burdens even when their system completion times are similar. We compare four fixed sequences in a conditional Los Angeles study linking 302 repair-capable network assets, 57 pooled crews, and official Southern California Edison distribution-service candidates for 817 census tracts. Thirty-two paired damage and positive-duration realizations under a fixed 2%-in-50-year ground-motion field pass through event scheduling, completion-step asset restoration, source connectivity, and tract-level service-access intervals. Burden integrates the deficit of identifiable candidate availability; it does not measure observed customer outage hours. Relative to Hospital-first, two weighted-priority sequences reduce mean population-normalized burden by only 0.295 and 0.166 h, respectively. Their distributional effects differ: the hospital-dominant sequence reduces burden in the highest-vulnerability quartile by 0.413 h but increases it in the lowest by 0.117 h. An efficiency-oriented search comparator yields a lower burden Gini, 0.1765 versus 0.2187, while increasing mean burden in every quartile and population burden by 15.076 h. Doubling only severe-damage task durations raises this excess to 26.245 h. Varying the relative influence of two attachment classes preserves overall effect directions but alters some between-group relationships. The results distinguish reducing overall burden, benefiting higher-vulnerability communities, and equalizing burdens. They support conditional comparison of restoration decisions, rather than optimal equitable policies or predictions of delivered electricity.

Keywords: Earthquake scenarios; Restoration sequencing; Community burden; Distributional consequences; Paired uncertainty; Service-access proxy

## 1 Introduction

Restoration planning decides not only when a damaged infrastructure system finishes repair but also which communities wait during that process. A sequence that finishes slightly earlier need not reduce the accumulated burden experienced through the network. Nor does a more equal distribution of delay necessarily mean that any community is better off. These distinctions matter when limited crews must follow priorities set before the full consequences of uncertain damage and task durations are known.

Evaluating a restoration decision therefore requires several views of the same consequences: the accumulated population burden, the absolute burdens of different vulnerability groups, and the dispersion of those burdens. Comparing these views under shared damage and workload conditions separates differences due to the restoration sequence from differences due to the physical sample. It also makes a practical distinction visible: a decision can benefit a higher-vulnerability group without reducing the gap between groups, or reduce relative inequality while increasing everyone's group-average burden.

We examine these relationships in a Los Angeles case with a mixed-owner regional task network, a pooled crew scenario, and community outcomes in a conservatively defined Southern California Edison (SCE) candidate-service domain. Thirty-two physical realizations are shared across four fixed sequences. Two separate contrasts then change candidate influence and the relative duration of severe-damage tasks, allowing us to distinguish comparisons that persist under these conditions from group judgments that depend on them.

### 1.1 Related research and the remaining question

Restoration research provides the logistics basis for this comparison. Çağnan et al. (2006) used discrete-event simulation to examine geographically varying restoration and resource bottlenecks in Los Angeles. Xu et al. (2007) optimized inspection, damage assessment, and repair schedules and evaluated them through restoration simulation. Cavdaroglu et al. (2013) connected infrastructure restoration and work-group scheduling rather than treating them as independent decisions. These studies show how sequencing, travel, resources, and uncertainty enter restoration decisions; they motivate retaining an explicit crew calendar when comparing community consequences.

Community-centered resilience broadens the evaluation beyond component completion. Logan and Guikema (2020) argued for assessing access to essential services, while Lin et al. (2022) distinguished dimensions of equity relevant to grid resilience. This perspective motivates following the consequences of a repair sequence through service access to communities. It also calls for keeping absolute group burdens alongside relative gaps and inequality measures, since these quantities answer different questions about who benefits and who waits.

Related physical and optimization studies address complementary parts of this problem. Cheng et al. (2024) coupled probabilistic earthquake damage with DC load-flow analysis and census-tract load shedding in Los Angeles. Toplu-Tutay et al. (2024) incorporated equity metrics into stochastic substation-hardening and power-flow decisions, and Jiang et al. (2025) addressed repair-duration uncertainty and equitable restoration decisions through a predict-then-optimize framework. Together, these studies establish approaches for quantifying physical consequences and embedding equity in decision objectives. The comparison pursued here focuses instead on how several evaluation criteria agree or conflict for the same fixed restoration decisions, and on which of those judgments depend on selected representation and workload assumptions.

This focus connects the logistics literature's explicit treatment of crews and uncertain work to the service-access literature's concern with community consequences. It evaluates population burden, absolute group burden, and relative inequality jointly, rather than using any one of them as a substitute for the others. Holding the physical realizations and decisions fixed in the targeted comparisons then identifies a specific boundary of the evidence: stability of an overall comparison need not imply stability of its interpretation for particular groups.

### 1.2 Research questions

We ask three questions. First, how do Hospital-first, two weighted-priority sequences, and an efficiency-oriented search sequence differ in population burden and logistics under paired task uncertainty? Second, which vulnerability groups and tracts have lower or higher modeled burden, and do aggregate improvement, benefit to higher-vulnerability communities, and smaller group gaps coincide? Third, how do these contrasts change when proxy-attached service candidates receive less or more influence, or when severe-damage tasks take relatively longer?

The study contributes a paired set of comparison evidence linking these three questions. It quantifies whether small population-level differences conceal different group consequences, identifies who bears additional burden when relative inequality falls, and distinguishes overall comparisons that persist under the two targeted contrasts from group judgments that remain assumption-dependent. The resulting evidence supports conditional restoration decisions in a source-connected service-access model. Figure 1 summarizes the design, and Table 1 identifies the data and scenario assumptions under which the comparisons apply.

![Figure 1. Conditional study design. The same physical realizations feed four fixed sequences. The A/B influence comparison is an offline change of evaluation weights; the DS4 comparison reschedules the same tasks with relatively longer severe-damage actions. Neither adds physical draws or optimizes a new policy.](Figures/Figure_1_Study_design.png)

Figure 1. Conditional study design. The same physical realizations feed four fixed sequences. The A/B influence comparison is an offline change of evaluation weights; the DS4 comparison reschedules the same tasks with relatively longer severe-damage actions. Neither adds physical draws or optimizes a new policy.

## 2 Study domain and methods

### 2.1 Network assets and candidate-service population

The inventory was selected from a retained 4,260-record California Energy Commission (CEC)/Homeland Infrastructure Foundation-Level Data (HIFLD) compilation: 3,374 SUBSTATION records, 2,775 marked IN SERVICE, 2,548 with valid coordinates and original maximum voltage of at least 34.5 kV, and 310 within the fixed study-area polygon. These are database selection counts, not the size of a complete Los Angeles electrical network. Supplement S1.1 gives the selection rules and the unrecovered historical selection behind the superseded 92-node model. Registration in the retained network supports meaningful states for 306 records. The primary connected component contains 302 assets and all 117 distinct upstream targets used by the resolved SCE service candidates. These 302 assets form the repair-task domain. They include 230 records labeled SCE, 34 Los Angeles Department of Water and Power (LADWP), 16 other owners, and 22 with unknown owner; they should not be described as 302 SCE substations.

Eight inventory records are outside the task domain: four unresolved registrations, two identified source-less isolates, and a two-node component with a reference source but no resolved SCE service attachment. They remain represented according to their fixed state semantics but receive no repair tasks. This exclusion prevents crews from spending time on assets outside the represented primary outcome; it does not establish that these assets lack real-world importance. The retained facility graph has 310 nodes and 1,040 undirected edges. Adjacency follows physical line paths without an intervening registered station or its projection anchor (Supplement S1.1). It is a geometric proxy, not a power-flow equivalent; no power balance, line capacity, voltage limit, switching feasibility, or load shedding is solved.

Community outcomes cover 817 census tracts with 3,572,152 people in the retained population table. A tract qualifies for this strict SCE domain only when its entire polygon is covered by both CEC-SCE and official SCE territory polygons, without conflicting community-retail utility overlap, subject to a 1 m² numerical geometry tolerance. Ambiguous tracts and LADWP outcomes are outside the primary analysis. This area rule is not a population-allocation model.

Official SCE distribution-circuit geometries intersecting these tracts identify 196 distinct candidate service nodes and 2,041 tract–candidate relations. Multiple bank or circuit records are consolidated by supported station identity. Each tract has one to seven candidates. The public GIS snapshot was retained on 14 September 2026; a provider date table reported 15 August 2026, without guaranteeing the update date of every geometry. Table S6 records the retained data versions, fields, and unresolved release dates. In particular, the tract-geometry release and the population estimate year/original Census table cannot be established from the retained provenance; neither is inferred from the NRI or housing-data year. The study uses a multi-epoch reference representation rather than a reconstruction of a particular operating day (CEC, n.d.; SCE, 2026).



Table 1. Study inputs, decisions, and interpretation boundaries.

| Component | Adopted representation | Evidence or limitation |
|---|---|---|
| Task assets | 302 assets in the primary component of a 310-record inventory | Mixed owners; all resolved service attachments fall in this component. |
| Hazard and damage | Fixed CGS 2%-in-50-year PGA; voltage-class fragility; 32 stored damage vectors | Conditional scenario, not 32 earthquake ruptures; no new correlated intensity fields. |
| Task duration | Positive-conditioned Normal DS1–DS4: (1,0.5), (6,3), (12,4), (36,12) h | Scenario on-site actions, not calibrated permanent repair times. |
| Resources and roads | 57 pooled crews; 11 origins; directed base–task and task–task travel | Allocation and access proxies; static roads; no crew-count contrast. |
| Dispatch | Full sequence filtered by DS>0; earliest free crew; completion = arrival + duration | Duration affects crew release, never pending-task order. |
| Raw restoration | DS residuals 1, 0.50, 0.09, 0.04, 0.03; damaged assets become 1 at completion | Completion-step assumption; no additional repair CDF. |
| Network availability | Functionality threshold 0.5; components with an active reference source; fixed 21-source set | Connectivity proxy; no power-flow, capacity, or switching solution. |
| Service candidates | 817 strict-SCE tracts; 196 candidates: 113 A, 71 B, 12 C | Official candidate evidence; equal weights are not actual service shares. |
| Population and missingness | 3,572,152 total; 3,520,382 in 805 partly/fully represented tracts | 12 fully unresolved tracts, 51,770 people, retain NA burden. |
| Sequences | Hospital-first; deterministic Balanced/HospFirst initializers; retained Efficiency search candidate | Fixed ex-ante lists; no global-optimality or equity-optimization claim. |
| Candidate-influence contrast | Relative B influence λ=0.5 or 2 in mixed A/B tracts | Fixed decisions; total resolved and C masses unchanged; offline burdens only. |
| Relative-duration contrast | Stored DS4 durations ×2; all other inputs and sequences fixed | Paired rescheduling; no new draws or reoptimization. |

Provider and scenario details appear in Sections 2.1–2.7 and Supplement S1–S4.



### 2.2 Service attachments and unresolved mass

Candidate membership and service share are separate pieces of information. An official circuit intersection supports a candidate relationship, but not the fraction of tract demand supplied. For the baseline, each candidate of tract r receives equal weight w(r,j)=1/|O(r)|, where O(r) is its official candidate set. These weights are never renormalized after a candidate becomes unavailable or unresolved.

There are three attachment classes. Class A contains 113 service nodes identified with the same physical asset as a registered network station. Their service state is that station's effective state, including its own sampled damage and restoration; no duplicate damage draw is made. Class B contains 71 nodes attached to a unique registered upstream interface using the official named-system field and the frozen name/alias crosswalk. They inherit that interface's effective state. This is a logical supply-dependency proxy, not a verified physical circuit, and the Class B distribution facility's own damage is outside the model. The 12 Class C nodes have no supported unique upstream attachment and remain missing, not failed or recovered.

The corresponding population-weighted candidate masses are 79.8622% for A, 16.0535% for B, and 4.0843% for C. Of the 817 tracts, 444 have only A candidates; 318 have resolved A/B candidates without C; 43 mix resolved and unresolved candidates; and 12 have only C. The last group contains 51,770 people. Its normalized burdens and direction probabilities remain undefined throughout. The other 805 tracts contain 3,520,382 people, including the partially identifiable communities. Missing candidate evidence is therefore kept visible rather than converted into zero burden.

For tract r, R(r) is the sum of its identifiable A/B weights and U(r)=1−R(r) is unresolved mass. At time t, L(r,t) is the weighted sum of known available candidate states. The reported service-access interval is [L(r,t), L(r,t)+U(r)]. It describes uncertainty in unsupported candidate state, not a statistical confidence interval or a bound on delivered electrical power. In this experiment R and U are time-invariant. Class A and B differ in modeled damage scope; the weighting contrast below assesses one consequence of that representation without claiming to supply the missing distribution-damage model.

### 2.3 Paired damage and on-site task duration

The primary intensity input is a fixed California Geological Survey 2%-probability-of-exceedance-in-50-years PGA field. This is a spatial hazard map, not one physically coherent earthquake rupture or an annualized loss calculation. Retained PGA values and voltage-class fragility parameters cover all 302 task assets. Lognormal exceedance functions are converted into probabilities for damage states DS0–DS4 using the adopted Hazus-based parameterization (FEMA, 2013). Supplement S1 specifies the parameters and a small, disclosed probability cleanup at five stations where exceedance curves cross.

One damage vector and one duration vector were generated for each of 32 realization IDs and then stored. Conditional on the fixed PGA field, station damage draws use separate random variates; no additional spatially correlated ground-motion field or cross-asset dependence model is sampled. Thus the ensemble represents damage and task-duration uncertainty within a fixed model, not 32 independent regional earthquakes. All four sequences use exactly the same physical vectors within each realization.

Only DS>0 assets become tasks. Undamaged assets do not enter the queue and have duration zero. For DS1–DS4, positive-conditioned Normal distributions use location and standard deviation pairs (1,0.5), (6,3), (12,4), and (36,12) h. Their conditional means are approximately 1.028, 6.166, 12.018, and 36.053 h. These are scenario-based on-site restoration action durations, not empirical or utility-calibrated permanent repair times. They exclude travel, mobilization, material waiting, and reconstruction. At dispatch, duration is used to determine completion and the crew's next release, but it is never used to reorder pending tasks or choose a sequence.

### 2.4 Event scheduling and effective network state

The resource scenario has 57 pooled crews initially available at 11 retained origin proxies. The underlying allocation labels 47 crews LADWP and 10 SCE, but imposes no utility-specific task eligibility. It is a regional resource budget, not verified postearthquake staffing. Every task and origin pair uses retained directed road travel times. Facility-access connectors are explicit proxies; no straight-line travel fallback, missing-value travel penalty, or arbitrary 24 h substitution is used. Roads, travel times, and origins are fixed across all comparisons, without congestion or earthquake road damage.

Each policy provides a complete 302-ID priority list. Removing DS0 assets yields the realization queue without reranking. The next task is assigned to the earliest available crew, with exact ties broken by ascending crew index. Travel is from that crew's origin for its first task and from its previous task thereafter. Arrival equals crew availability plus directed travel; completion equals arrival plus the stored realized duration. The crew is released at completion. Tasks are not preempted or shared between crews, and the queue does not adapt to future service outcomes.

Initial raw functionality is 1.00, 0.50, 0.09, 0.04, or 0.03 for DS0–DS4. A damaged asset retains its residual value until completion and becomes 1 at that event. There is no additional continuous repair CDF. Evaluation times are zero and the unique task-completion times, ending when all tasks finish. At each event, stations with raw functionality at least 0.5 define the functional subgraph. Components containing at least one active member of the fixed 21-node reference source set are retained. Effective state equals raw state inside those components and zero otherwise. Source membership is a reference availability scenario, not a verified list of operating Los Angeles generation sources. Source nodes can themselves be unavailable under the functionality threshold.

Repair completion therefore does not guarantee an immediate increase in effective availability: another path or source may still be unavailable. The four unresolved network registrations retain a separate missing-state mask; disconnected but identified assets retain meaningful numeric zero. Candidate A/B states are direct lookups of their selected effective upstream state. The resulting quantities are source-connected upstream availability proxies, not power supplied to customers.

### 2.5 Fixed sequences and the planning surrogate

Hospital-first orders the complete task domain by descending hospital-priority score, then population-priority score, then ascending station ID. Hospital priority uses a binary indicator for each of 47 tracts containing 53 retained hospital records; multiple records in one tract do not multiply its weight. This metric does not represent hospital operating capacity. Population and vulnerability priorities likewise originate from the 817-tract domain, propagate through candidate weights, and aggregate to A/B upstream assets. Vulnerability priority uses population multiplied by the retained Federal Emergency Management Agency National Risk Index (NRI) SOVI_SCORE, not the CDC Social Vulnerability Index. Components are independently min–max normalized over the 302 assets. Class C priority mass remains unassigned.

For the other policies, service priority is a weighted average of population, hospital, and SOVI components. The Balanced weights are (1,3,1), the hospital-dominant HospFirst weights (1,20,1), and the Efficiency weights (1,1,1). Their makespan penalty coefficients are 0.5, 0.1, and 2.0. These are policy-design coefficients. In particular, 20 creates a strongly hospital-dominant archetype; it is not an empirical preference or an optimal societal weight. No network-importance term is included.

The surrogate schedules all 302 assets using ex-ante expected workload: the probability-weighted positive duration over DS1–DS4. It uses the same crew origins and travel convention but never sees realized damage, realized duration, or community trajectories. For a sequence, completion benefit is the priority-weighted sum of max(504−completion,0), divided by 504 times total priority; fitness subtracts the makespan coefficient times makespan/504. This static additive objective does not directly optimize source-connected tract burden, T80, group gaps, or Gini. Scores are compared only under the same policy objective, not across differently weighted objectives.

The retained genetic algorithm (GA) search used populations of 100, 100 generations, ordered crossover probability 0.8, inversion mutation probability 0.2, tournament size three, and ten seeds per policy. Examination of retained candidates identified deterministic priority-sorted initializers that attained the highest recorded Balanced and HospFirst fitness values. These two weighted-priority sequences are used here; they are not described as GA optima. Efficiency retains the highest-scoring saved finite-budget search sequence. Supplement S2 documents candidate retention, seed variation, deterministic incumbents, and the absence of any global-optimality guarantee.

Candidate selection was based on the original ex-ante objective, not on the 32 community outcomes. The physical sample had, however, already been evaluated before candidate correction. This study is a corrected reevaluation on an existing sample with paired assumption contrasts, not a new independent validation set. No further sequence, weight, or sample was selected after observing the corrected community comparisons.

### 2.6 Burden and distributional measures

For realization m and policy p, restoration burden B(r) integrates R(r)−L(r,t) over the event horizon H. Because state is a right-continuous step function, integration uses the state after each event over the interval until the next event. In the evaluated trajectories, the resolved candidate deficit is zero at the final horizon. Permanently unresolved C mass is not included as an outage deficit. Normalized burden N(r)=B(r)/R(r) is defined only for R(r)>0. Both B and N have time dimensions, but N is a normalized modeled availability deficit in hours, not observed resident outage time.

Bᵣ = ∫₀ᴴ [Rᵣ − Lᵣ(t)] dt;     Nᵣ = Bᵣ/Rᵣ, for Rᵣ > 0.  (1)

We report two distinct population summaries. The population-weighted mean of tract-normalized burden gives each tract's full population weight after division by its represented mass. Its denominator is 3,520,382 people in the 805 partially or fully identifiable tracts. The availability-consistent cumulative deficit divides population-weighted B by population-weighted R, with denominator approximately 3,426,254.42 population–candidate-mass units. The second summary gives less weight to tracts with less represented candidate mass. These are different, reasonable estimands; they are not interchangeable.

N̄ₚ = ΣᵣPᵣNᵣ / ΣᵣPᵣ;     Bₚᵣ = ΣᵣPᵣBᵣ / ΣᵣPᵣRᵣ.  (2)  Sums are over Rᵣ > 0.

Population resolved availability is the population-weighted L divided by the same population-weighted R denominator used by the second burden measure. T80 is its first event time reaching 0.8, without interpolation. T50 and T90 are secondary supplementary metrics. Hospital-tract burden is the unweighted mean N among the 47 retained hospital tracts. These are tract service-access measures, not operational hospital recovery.

SOVI quartiles are fixed once across the 817 tracts; Q1 and Q4 denote the lowest and highest scores. Within each quartile, mean N is population-weighted over R>0 tracts. The signed gap is Q4 minus Q1; the absolute gap is calculated within each realization before averaging. A negative signed gap means lower modeled Q4 burden, not that social equity has been achieved. Population-weighted Gini is calculated from N among the identifiable tracts. Lower Gini denotes lower relative dispersion; its interpretation must be checked against all four absolute group levels.

For each comparator relative to Hospital-first, we classify a tract as improved below −1 h, worsened above +1 h, and near-zero otherwise. This practical threshold is not a significance test. Classification of each tract's mean paired effect across 32 realizations is reported separately from classifying each realization and then averaging population shares. Population percentages use the entire 817-tract population unless explicitly stated otherwise; the 12 unresolved tracts are a separate group with burden and directional probability missing. Supplement S3 gives formulas, quartile composition, and the two population denominators.

### 2.7 Targeted contrasts and statistical interpretation

The first contrast changes only evaluation weights in tracts containing both A and B candidates. If A(r) and B(r) are their original weight totals, A weights are multiplied by R(r)/(A(r)+λB(r)) and B weights by λR(r)/(A(r)+λB(r)), with λ=0.5 or 2; λ=1 is the baseline. Class C mass, total resolved mass, official candidates, and attachments remain unchanged. Nonmixed tracts are unchanged. Sequences, priorities, physical vectors, sources, roads, and crews are fixed. This tests the evaluation of fixed decisions under two design stresses, not policy redesign under another mapping. The values are not an empirical range of true service shares.

The A/B contrast uses saved or identifiable reconstructed upstream deficit integrals. It supports burden, group summaries, Gini, and paired classification, but not reconstruction of event ordering or T80. The two inseparable interface contributions 300829 and 303005 remain a combined term. Supplement S4 describes the information available for this offline computation. No temporal claims are drawn from those integrals.

The second contrast doubles only stored DS4 task durations, preserving DS0–DS3 values and every policy sequence. The event scheduler and subsequent state propagation are reexecuted because longer tasks alter crew release and later arrivals. No duration is redrawn and no policy is reoptimized for the new workload. This asks how the same decisions perform when severe-damage actions are relatively more time-consuming, not whether a different duration is empirically more accurate. It is not crossed with the A/B weighting contrast.

All strategy comparisons and changes in those comparisons are paired by realization ID. We report means, dispersion, median/IQR in the supplement, direction frequencies, and percentile 95% paired bootstrap intervals based on 10,000 resamples of the 32 realization units. The same resampling indices are used across policies and conditions. Tracts and policy runs are not treated as independent physical realizations. Intervals quantify variability in this sample under the stated model; they do not cover omitted physical processes, prove equivalence when crossing zero, or serve as simultaneous multiple-comparison guarantees. Effects are interpreted by magnitude and group consequences rather than a binary significance rule.

## 3 Results

### 3.1 Small overall differences coexist with different community consequences

Table 2 reports baseline means and paired differences. Hospital-first has mean population-normalized burden 44.131 h. Balanced and HospFirst reduce it to 43.836 and 43.965 h, respectively: reductions of 0.295 h (95% paired interval 0.169–0.404 h) and 0.166 h (0.064–0.257 h), about 0.67% and 0.38%. These are modest changes despite intervals excluding zero. The availability-consistent cumulative burden gives the same overall ordering, with means 43.589, 43.284, and 43.414 h. This agreement does not make the denominators identical.

The corresponding hospital-tract burden differences are −0.041 h [−0.145,0.080] and −0.022 h [−0.104,0.066]. Population T80 differences are −0.214 h [−0.756,0.274] and −0.197 h [−0.735,0.204]. Makespan and total travel differences are also small, with intervals spanning zero. The evidence establishes neither a substantial hospital or logistics advantage nor formal equivalence.

Efficiency has a markedly different outcome: population-normalized burden 59.207 h, an excess of 15.076 h [13.959,16.170] over Hospital-first; hospital-tract burden is 12.244 h higher [10.990,13.471]. Its mean makespan difference is only 0.002 h [−2.354,2.508], and total travel differs by 1.064 h [−0.004,2.079]. Its label describes the surrogate's emphasis, not an established advantage in these realized logistics measures.



Table 2a. Baseline means across the same 32 physical realizations.

| Metric | Hospital-first | Balanced | HospFirst | Efficiency |
|---|---|---|---|---|
| Population-normalized burden (h) | 44.131 | 43.836 | 43.965 | 59.207 |
| Availability-consistent burden (h) | 43.589 | 43.284 | 43.414 | 58.852 |
| Population resolved T80 (h) | 62.000 | 61.787 | 61.803 | 73.790 |
| Hospital-tract burden (h) | 43.442 | 43.401 | 43.419 | 55.686 |
| Burden Gini | 0.2187 | 0.2184 | 0.2201 | 0.1765 |
| Makespan (h) | 165.552 | 165.505 | 165.568 | 165.554 |
| Total travel (crew-hours) | 121.161 | 120.830 | 120.414 | 122.225 |

Burden hours are integrated deficits of a modeled service-access proxy, not observed outage hours. See Eq. 2 for the two population denominators.





Table 2b. Paired differences from Hospital-first, with 95% bootstrap intervals.

| Metric | Balanced − HF | HospFirst − HF | Efficiency − HF |
|---|---|---|---|
| Population-normalized burden (h) | −0.295 [−0.404, −0.169] | −0.166 [−0.257, −0.064] | +15.076 [+13.959, +16.170] |
| Availability-consistent burden (h) | −0.305 [−0.415, −0.178] | −0.174 [−0.265, −0.072] | +15.264 [+14.159, +16.346] |
| Population resolved T80 (h) | −0.214 [−0.756, +0.274] | −0.197 [−0.735, +0.204] | +11.790 [+8.418, +15.369] |
| Hospital-tract burden (h) | −0.041 [−0.145, +0.080] | −0.022 [−0.104, +0.066] | +12.244 [+10.990, +13.471] |
| Burden Gini | −0.0003 [−0.0023, +0.0016] | +0.0014 [+0.0001, +0.0028] | −0.0423 [−0.0533, −0.0316] |
| Makespan (h) | −0.047 [−0.141, +0.047] | +0.016 [−0.073, +0.102] | +0.002 [−2.354, +2.508] |
| Total travel (crew-hours) | −0.331 [−1.148, +0.507] | −0.746 [−1.837, +0.386] | +1.064 [−0.004, +2.079] |

Negative means a lower metric than Hospital-first. Intervals resample 32 realization units 10,000 times; no equivalence or simultaneous-testing claim follows.



Balanced has lower population-normalized burden than Hospital-first in 29 of 32 realizations and HospFirst in 27. Among all four policies, the lowest-burden frequencies are 6.25% for Hospital-first, 68.75% for Balanced, 25% for HospFirst, and zero for Efficiency. In contrast, Efficiency has the lowest makespan in 53.125% of realizations when ties are fractionally allocated, yet no clear mean makespan advantage. Ranking frequency, average effect, and effect uncertainty describe different aspects of performance; they do not identify one overall winner.

### 3.2 Benefiting higher vulnerability communities is not the same as equalizing burdens

Figure 2 places group levels next to paired group effects. Under Hospital-first, mean burden decreases from Q1 to Q4: 49.469, 45.198, 42.926, and 39.523 h. This is a conditional model result, not evidence that higher-vulnerability communities in Los Angeles experience less actual disruption. All four group means are slightly lower under Balanced, by 0.143, 0.223, 0.359, and 0.438 h.

HospFirst instead increases Q1 burden by 0.117 h [0.039,0.197] while reducing Q4 burden by 0.413 h [0.269,0.549]. Its Q2 and Q3 changes are −0.046 and −0.293 h. The higher-vulnerability group therefore improves relative to Hospital-first while a lower-vulnerability group bears a small additional modeled burden. Because Q4 starts below Q1, the absolute Q4–Q1 gap increases from 9.946 to 10.475 h. Balanced also increases the absolute gap, to 10.241 h, even though all four group means improve. The average gap is not an adequate substitute for group levels.

Efficiency reduces the mean Gini from 0.2187 to 0.1765 and the mean absolute Q4–Q1 gap from 9.946 to 2.666 h. Nevertheless, its Q1–Q4 burdens are 62.437, 56.619, 57.019, and 61.049 h, all above Hospital-first. Q4 incurs the largest increase, 21.526 h [20.355,22.652]. Reduced relative dispersion here accompanies deterioration in every group mean. Balanced's Gini is 0.2184, close to Hospital-first; HospFirst's is 0.2201. These differences should not be interpreted as an isolated effect of hospital or vulnerability weighting because the benchmark coefficient sets change several terms at once.

![Figure 2. Absolute group burdens and relative distributional measures under baseline assumptions. Q1–Q4 are fixed NRI-derived vulnerability quartiles. Panels B and C show paired mean differences and 95% realization-bootstrap intervals. Panel D shows four evaluated policy points, not a Pareto frontier. Lower Gini for Efficiency coexists with higher burden in every quartile.](Figures/Figure_2_Group_burdens.png)

Figure 2. Absolute group burdens and relative distributional measures under baseline assumptions. Q1–Q4 are fixed NRI-derived vulnerability quartiles. Panels B and C show paired mean differences and 95% realization-bootstrap intervals. Panel D shows four evaluated policy points, not a Pareto frontier. Lower Gini for Efficiency coexists with higher burden in every quartile.

Tract-level effects further distinguish average improvement from uniform benefit. Using each tract's 32-realization mean effect and the ±1 h threshold, Balanced improves 110 tracts containing 13.02% of the entire study population and worsens nine containing 1.10%; HospFirst improves 61 containing 7.37% and worsens three containing 0.33%. Their worsened tracts are all in Q1 under this classification. Efficiency improves 14 tracts containing 1.74% but worsens 663 containing 80.07%. The unresolved share is always 1.45%, not near-zero. Figure 3 reports the full partition, including the large near-zero groups for the two weighted-priority sequences.

These percentages are not the proportion delayed in each realization. Classifying first within each realization and then averaging gives worsened population shares of 6.23%, 3.64%, and 76.57% for Balanced, HospFirst, and Efficiency. Balanced's realization-specific worsened share ranges from 0.29% to 51.85%. A small favorable overall mean does not promise that most tracts benefit in every draw. Supplement S3 retains both statistical objects.

![Figure 3. Population shares classified by burden changes relative to Hospital-first. Panel A classifies each tract’s mean effect over 32 realizations; panel B averages classifications performed separately within each realization. Improved is below −1 h, worsened above +1 h, and near-zero between those thresholds. These are practical classes, not significance tests. Twelve unresolved tracts remain separate; all percentages use the full 3,572,152-person domain.](Figures/Figure_3_Tract_classification.png)

Figure 3. Population shares classified by burden changes relative to Hospital-first. Panel A classifies each tract’s mean effect over 32 realizations; panel B averages classifications performed separately within each realization. Improved is below −1 h, worsened above +1 h, and near-zero between those thresholds. These are practical classes, not significance tests. Twelve unresolved tracts remain separate; all percentages use the full 3,572,152-person domain.

### 3.3 Targeted assumptions affect group relationships and the magnitude of costs

Across λ=0.5,1,2, the population-normalized burden differences relative to Hospital-first are −0.300/−0.295/−0.291 h for Balanced, −0.177/−0.166/−0.154 h for HospFirst, and +15.134/+15.076/+15.053 h for Efficiency. Overall directions persist in these two fixed-decision evaluation stresses. Group relationships are more sensitive. Efficiency's Q4 excess is 22.558, 21.526, and 20.377 h, while its own mean signed Q4−Q1 gap changes from +0.495 to −1.388 to −3.540 h. The point estimate therefore changes sign; this is not a claim of a statistically established sign reversal. No temporal threshold is inferred from this integral-only contrast.

When stored DS4 durations are doubled, Hospital-first mean population-normalized burden becomes 77.025 h. Balanced and HospFirst remain modestly lower, at 76.789 and 76.848 h. Efficiency rises to 103.270 h. Its excess over Hospital-first is now 26.245 h [23.709,28.647], an increase in the policy contrast of 11.169 h [9.303,12.880]. Its Q4 excess rises from 21.526 to 37.830 h, a contrast change of 16.303 h [14.317,18.168]. Figure 4 and Table 3 distinguish effects within each duration condition from this paired change in effects.

Efficiency still has a lower Gini, 0.1799 versus 0.2273, while every quartile has higher absolute burden. Its relative mean makespan and travel changes remain uncertain: the changes in policy contrasts are −0.191 h [−2.651,2.435] and −0.096 h [−1.607,1.457]. Thus the amplified community cost is not accompanied by a demonstrated increase in average logistics benefit. Balanced and HospFirst population advantages remain small; their changes in population contrasts are +0.059 h [−0.022,0.141] and −0.010 h [−0.068,0.049].

![Figure 4. Two separate targeted contrasts. Panels A–B vary Class B influence in mixed A/B tracts, retaining resolved mass and fixed decisions; λ=1 is baseline. Panels C–D double only stored DS4 task durations, with original weights and sequences. The tests are not combined into a factorial experiment. Curves connect evaluated conditions and do not imply interpolation evidence. Paired intervals for the duration contrast appear in Table 3.](Figures/Figure_4_Targeted_contrasts.png)

Figure 4. Two separate targeted contrasts. Panels A–B vary Class B influence in mixed A/B tracts, retaining resolved mass and fixed decisions; λ=1 is baseline. Panels C–D double only stored DS4 task durations, with original weights and sequences. The tests are not combined into a factorial experiment. Curves connect evaluated conditions and do not imply interpolation evidence. Paired intervals for the duration contrast appear in Table 3.



Table 3. Change in the strategy-minus-Hospital-first contrast when DS4 durations are doubled.

| Metric | Balanced | HospFirst | Efficiency |
|---|---|---|---|
| Population-normalized burden (h) | +0.059 [−0.022, +0.141] | −0.010 [−0.068, +0.049] | +11.169 [+9.303, +12.880] |
| Q4 burden (h) | +0.032 [−0.044, +0.112] | −0.005 [−0.069, +0.065] | +16.303 [+14.317, +18.168] |
| Hospital-tract burden (h) | +0.070 [−0.018, +0.157] | −0.022 [−0.081, +0.037] | +8.097 [+6.199, +9.867] |
| Makespan (h) | −0.109 [−0.287, +0.073] | −0.092 [−0.262, +0.075] | −0.191 [−2.651, +2.435] |
| Total travel (crew-hours) | −0.411 [−1.566, +0.735] | +0.191 [−1.411, +1.815] | −0.096 [−1.607, +1.457] |

Entries are paired differences-in-differences in hours, with 95% bootstrap intervals. Positive indicates that the strategy’s relative cost increases under longer DS4 actions; it is not the total duration-condition effect.



Under the mean-effect tract classification, Efficiency's worsened population share increases to 93.33%, covering 763 tracts. However, its average realization-specific worsened share is 75.33%, compared with 76.57% under baseline durations. The apparent contrast reflects different averaging and classification operations, not conflicting datasets. The more severe condition increases the mean magnitude and persistence of burden for many tracts without requiring the worsened share to increase in each individual realization.

## 4 Discussion

### 4.1 What the sequence comparisons establish

The principal result is a separation of decision criteria. Modest reductions in overall burden can have different group consequences; improvement for the highest-vulnerability quartile can increase the absolute gap when its baseline modeled burden is already lower; and lower Gini can coincide with higher burdens in every quartile. These observations are more informative than a single strategy ranking. They also show why T80, makespan, and a vulnerability-weighted aggregate should not be treated as interchangeable measures of community benefit.

Hospital-first and the two weighted-priority sequences are close in overall population burden. The small paired differences do not support claims of large policy superiority, nor do intervals spanning zero demonstrate equivalence. The HospFirst result is a specific distributional contrast, not an estimate of the causal effect of prioritizing hospitals. Its coefficients differ from the other policies in several respects, its ordering resembles Hospital-first, and hospital-tract burdens differ little. The study does not isolate a vulnerability-priority intervention or optimize fairness.

The interpretation of Efficiency is similarly bounded. A good score under its own static completion surrogate does not guarantee low source-connected community burden. Expected-workload decoding need not equal expected realized decoding: crew release, subsequent travel origins, and maximum completion are nonlinear in task durations. Moreover, an asset's completion may yield no immediate service benefit until another path or source becomes usable. The observed objective mismatch is therefore a comparison between distinct modeled quantities, not proof that optimization generally fails or that a particular social objective is undesirable.

### 4.2 What the targeted comparisons add

The A/B contrast addresses uncertainty in relative candidate influence while holding decisions fixed. Its stability in population-effect direction is useful, but limited: the group-level magnitudes and one signed gap depend on the weighting assumption. It does not validate named-system connectivity, true load shares, or omission of distribution-station damage. Recomputing priorities and searching anew under another mapping would answer a different question about policy design, which was not attempted.

The DS4 contrast shows that a restoration assumption can alter relative community costs rather than merely stretching all recovery times. Stored task events for the two weighted-priority sequences show that doubling severe-damage durations changes crew assignments for roughly 220 tasks per realization, among an average of about 300 tasks, and increases mean arrival by approximately 32 h. This is evidence of changed event logistics, not a uniform rescaling of old trajectories. It does not establish that the doubled duration scenario is more realistic.

Saved interface integrals also permit accounting for modeled burden changes. For example, three upstream interfaces account for approximately 2.375, 2.363, and 2.027 h of Efficiency's baseline excess population burden; their contributions increase under longer DS4 tasks (Supplement S4). Such a decomposition identifies where a model's weighted deficit accumulates. It cannot, without adequate event evidence, establish that those stations' own repair order caused the differences, and it does not explain real neighborhood outcomes causally. We therefore avoid attributing results to unverified hospital geography, social mechanisms, or electrical bottlenecks.

### 4.3 Scope and limitations

First, source-connected functionality is only a proxy for upstream availability. Connectivity may be informative when other electrical constraints are nonbinding, but their nonbinding status is not established here. Generation adequacy, capacity, protection, voltage, switching, and load shedding can change both levels and relative policy performance. Applying the same proxy to all policies does not eliminate that possibility. No comparison to historical restoration milestones is used as tract-level validation.

Second, official candidate relationships improve the evidential basis over unrestricted distance allocation, yet equal weights and named-system attachments remain assumptions. Class A includes damage to its identified network asset; Class B omits separate downstream damage. The network and GIS sources span different epochs. Fifty-five tracts contain some unresolved candidate mass, and the twelve fully unresolved tracts are not a random sample that can safely be discarded in claims about the whole population. Population-weighted normalized burden describes the represented portion of partially identifiable tracts; it does not impute their unrepresented supply.

Third, the 302-asset task domain and the SCE outcome domain are not coextensive utility systems. Cross-owner crews are pooled, routes are static, and the 57-crew budget and on-site durations are uncalibrated scenarios. Roads remain usable; material shortages, mobilization, work shifts, task specialization, and distribution repairs are absent. This study compares sequences under one resource budget and cannot quantify the causal benefit of adding crews or recommend actual utility dispatch arrangements.

Fourth, the fixed hazard field, adopted fragility, independent conditional draws, and 32 existing realizations constrain inference. The two targeted contrasts do not constitute a full uncertainty analysis. Candidate correction was followed by reevaluation on the same sample, not a held-out test. Sequence selection remained ex ante with respect to the community objective, but the evidence should still be described as a limited paired comparison. No policy was further tuned to preserve a favorable ranking.

Finally, burden inequality is one distributional description, not a complete concept of equity. NRI-derived tract vulnerability does not identify individual need, and modeled time deficits do not measure hardship, health outcomes, access to backup power, or procedural justice. The four policy points do not trace a Pareto frontier. Stronger claims about equitable optimization or actual electricity recovery would require different objectives and additional physical and social evidence.

## 5 Conclusion

Under the stated Los Angeles network and candidate-service conditions, fixed restoration sequences redistribute modeled community burden in ways not summarized by system completion or a single inequality statistic. Two weighted-priority sequences offer only small population-burden reductions relative to Hospital-first, while their group effects differ. The hospital-dominant sequence benefits Q4 while slightly increasing Q1 burden. An efficiency-oriented search sequence produces lower relative inequality but greater absolute burden in every quartile, without a clear mean makespan advantage.

The limited candidate-influence contrast preserves overall effect directions but changes some group relationships. Longer relative DS4 durations amplify Efficiency's additional community burden. These results support reporting absolute group levels, paired tract effects, and logistics costs together. They support a conditional study of how fixed recovery decisions allocate burden, not a claim to have found optimal equitable policies or predicted observed Los Angeles outages.

## Data and code availability

The repository retains the original results and the corrected comparison, including frozen sequence identities, the 32 shared physical vectors, realization-level metrics, tract burdens, and targeted-contrast evidence. The scientific results used here correspond to commit 87110dad035ddb6eb694235330cd2547d9ba5588 of https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale. Supplement S5 identifies the analysis files and dataset provenance. Third-party GIS and source data retain their providers' terms. The manuscript figures are generated from saved results; no new search or simulation was conducted for manuscript preparation.

## Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Declaration of AI-assisted work

ChatGPT and Codex assisted with code preparation, result presentation, literature checking, and drafting and organization of the revision. AI-generated text was not treated as scientific evidence; the reported findings are grounded in retained model outputs and the cited sources. Responsibility for verifying the methods, evidence, references, and final submitted text rests with the authors.

## References

Çağnan, Z., Davidson, R. A., and Guikema, S. D. (2006). Post-earthquake restoration planning for Los Angeles electric power. Earthquake Spectra, 22(3), 589–608. https://doi.org/10.1193/1.2222400

California Energy Commission (CEC). (n.d.). California electric substations, electric transmission lines, and electric load-serving entities [GIS datasets]. https://gis.data.ca.gov/

California Geological Survey (CGS). (n.d.). Map Sheet 48, retained CA_pt01_GM_maps.csv, PGA-2pc50 field [ground-motion data; exact grid-release year undetermined in retained records]. https://www.conservation.ca.gov/cgs/publications/ms48

California Health and Human Services Agency. (n.d.). Licensed and Certified Healthcare Facility Listing [retained hospital extract; snapshot date undetermined, facility status dates include 2026; Table S6]. https://data.chhs.ca.gov/dataset/licensed-healthcare-facility-listing

Cavdaroglu, B., Hammel, E., Mitchell, J. E., Sharkey, T. C., and Wallace, W. A. (2013). Integrating restoration and scheduling decisions for disrupted interdependent infrastructure systems. Annals of Operations Research, 203, 279–294. https://doi.org/10.1007/s10479-011-0959-3

Cheng, B., Nozick, L., Dobson, I., Davidson, R., Obiang, D., Dias, J., and Granados, M. (2024). Quantifying the earthquake risk to the electric power transmission system in Los Angeles at the census tract level. IEEE Access, 12, 126019–126032. https://doi.org/10.1109/ACCESS.2024.3408797

Federal Emergency Management Agency (FEMA). (2013). Multi-hazard loss estimation methodology: Earthquake model, Hazus-MH 2.1 technical manual. U.S. Department of Homeland Security.

Federal Emergency Management Agency (FEMA). (2023). National Risk Index, version 1.19.0, March 2023, California census-tract table and SOVI_SCORE field [dataset and data dictionary]. https://www.fema.gov/about/openfema/data-sets/national-risk-index-data

Homeland Infrastructure Foundation-Level Data (HIFLD). (n.d.). Electric substations [dataset]. https://catalog.data.gov/dataset/electric-substations

Jiang, L., Yu, D., Xu, R., Tang, T., and Wang, G. (2025). Uncertainty-aware predict-then-optimize framework for equitable post-disaster power restoration. Proceedings of IJCAI-25, 9719–9727. https://doi.org/10.24963/ijcai.2025/1080

Lin, Y., Wang, J., and Yue, M. (2022). Equity-based grid resilience: How do we get there? The Electricity Journal, 35(5), 107135. https://doi.org/10.1016/j.tej.2022.107135

Logan, T. M., and Guikema, S. D. (2020). Reframing resilience: Equitable access to essential services. Risk Analysis, 40(8), 1538–1553. https://doi.org/10.1111/risa.13492

OpenStreetMap contributors. (n.d.). OpenStreetMap [road-network dataset]. https://www.openstreetmap.org/copyright

Southern California Edison (SCE). (2026). Distribution circuits, service territory, and substations [planning GIS snapshot retained 14 September 2026]. https://drpep.sce.com/arcgis_server/rest/services/Hosted/Distribution_circuits/FeatureServer/0 ; https://drpep.sce.com/arcgis_server/rest/services/Hosted/ICA_Layer/FeatureServer

Toplu-Tutay, G., Hasenbein, J. J., and Kutanoglu, E. (2024). Impact of power outages depends on who loses it: Equity-informed grid resilience planning via stochastic optimization. Socio-Economic Planning Sciences, 95, 102036. https://doi.org/10.1016/j.seps.2024.102036

U.S. Census Bureau. (n.d.). Census tract boundaries and population data [retained derivatives; exact boundary release and population estimate year/original table undetermined; Table S6]. https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html ; https://api.census.gov/data.html

Xu, N., Guikema, S. D., Davidson, R. A., Nozick, L. K., Çağnan, Z., and Vaziri, K. (2007). Optimizing scheduling of post-earthquake electric power restoration tasks. Earthquake Engineering & Structural Dynamics, 36(2), 265–284. https://doi.org/10.1002/eqe.623
