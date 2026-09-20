# Responses to the editor and reviewers

Manuscript originally submitted as IJDRR-D-26-02276

Revised title: Distributional consequences of postearthquake restoration sequences under uncertain task workloads in Los Angeles

## Response to the editorial decision and overall revision

The original decision was rejection with a separate transfer offer, not an invitation to revise at IJDRR. We have prepared a substantially rewritten manuscript for resubmission and address all original comments below. Section numbers refer to the accompanying clean revised manuscript; S1–S5 refer to its supplementary material. The original manuscript, results, and correspondence remain preserved.

The revised study is a conditional restoration-decision comparison with two targeted assumption contrasts. It no longer claims a new GA methodology, validated delivered-power prediction, or equity-optimal planning. The outcome domain is 817 strictly classified SCE tracts, linked through official candidate evidence to a regional 302-asset task domain. Fifty-seven crews form a pooled resource scenario. Damage and positive task durations vary across 32 stored physical realizations, paired across all policies. Completion releases a crew and restores raw asset functionality; source connectivity remains a separate condition.

We corrected candidate retention for Balanced and HospFirst by recovering deterministic initializers that reached the highest recorded scores under their original ex-ante objectives. We did not launch new GA searches or select candidates using community outcomes. Efficiency retains its finite-budget search sequence. These changes alter the old ranking narrative: the two recovered sequences offer small population-burden reductions relative to Hospital-first, rather than the former large disadvantages. A lower Gini for Efficiency still accompanies higher absolute burdens in every vulnerability quartile. Two limited contrasts preserve overall effect directions under A/B candidate-influence changes but reveal group sensitivity, and show that longer severe-damage durations amplify Efficiency's community cost.

The rewritten manuscript presents these results as distributional consequences of fixed modeled decisions. It does not equate small differences with meaningful superiority, intervals including zero with equivalence, or lower inequality with social welfare improvement. The following replies distinguish actual new evidence from issues addressed by narrowing scope.

## Reviewer 1

### Overall assessment

> This manuscript develops a census-tract-level framework for post-earthquake power-service recovery in Los Angeles County by integrating substation damage, network connectivity, restoration logistics, and social vulnerability. The study is relevant to IJDRR and provides a useful attempt to link infrastructure recovery with community-level impacts. However, several key assumptions and the model validation require further clarification to support the robustness of the conclusions.

Response: We retained the connection between infrastructure restoration and community consequences but narrowed what that connection can support. The title, abstract, research questions, methods, and conclusions now consistently describe a conditional service-access comparison. The original IDW outcome mapping has been replaced by official SCE candidate relationships with explicit unresolved mass. The simulation uses realization-specific task eligibility and stored positive durations rather than mean-duration scheduling followed by another repair clock. We added absolute vulnerability-group burdens, tract-level paired effects, Gini, and two focused assumption contrasts. These strengthen specific comparisons while leaving power-flow and actual feeder/outage validation outside the study. Locations: Abstract; Sections 1.2, 2.1–2.7, 3, 4.3, and 5; Tables 1–3; Figures 1–4.

### Comment 1

> The census-tract service availability is derived from an IDW-based dependency matrix using tract centroids, network distances, and an assumed cutoff. However, this mapping is not supported by actual utility service territories, feeder connections, or outage records. Since the subsequent population-weighted recovery, hospital prioritization, and vulnerability hotspot results all depend directly on this matrix, the authors should provide stronger validation or robustness analysis for the tract-substation mapping, beyond varying only the weight cutoff. The limitations of interpreting this proxy as actual electricity-service dependency should also be more clearly stated.

Response: We replaced the primary IDW dependency with an independently evidenced candidate set from official SCE circuit/tract intersections and substation records. The 817 strictly classified SCE tracts have 196 candidates: 113 physical-identity attachments, 71 named-system upstream proxies, and twelve unresolved candidates. Equal baseline weights represent candidate uncertainty, not customer-load shares. No nearest filling or missing-mass renormalization is used.

We then evaluated the same fixed policies at relative Class B influences 0.5, 1, and 2, preserving the official candidates, attachments, Class C mass, and each tract's total resolved mass. Population-burden effect directions persist, but group relationships are not invariant: Efficiency's own mean signed Q4−Q1 gap changes from +0.495 to −3.540 h across the endpoints. This is limited evaluation robustness, not proof of feeder wiring or actual service shares. It also does not establish that Class B facilities' own distribution damage can be ignored. Locations: Sections 2.1–2.2, 2.7, 3.3, and 4.2–4.3; Figure 4; Supplement S1.1 and S4.1. Evidence: PAIRED_EFFECTS.csv, condition AB_lambda_0.5/AB_lambda_2; group and tract effect tables.

### Comment 2

> The reduced network is explicitly stated not to be an electrical power-flow equivalent, while service availability is determined mainly by whether a substation remains connected to an active source. This ignores power balance, transmission capacity, line loading, generation availability, voltage constraints, and load shedding. The authors should clarify under what conditions source connectivity can reasonably serve as a proxy for electricity availability and avoid interpreting the modeled S_r (t) as equivalent to actual delivered power unless additional validation is provided.

Response: This issue is addressed explicitly through scope limitation, not claimed physical validation. Section 2.4 defines effective state as raw functionality retained only in functional components containing an active reference source. This can be an upstream-availability proxy when unmodeled electrical constraints are nonbinding, but we have not established that condition for the real system. The manuscript no longer calls the result actual delivered electricity or observed customer outage. Section 4.3 states that omitted capacity, power balance, generation adequacy, voltage, protection, switching, and load shedding can affect relative policy comparisons; using a common proxy does not remove this risk. We added no invented capacity inputs or power-flow model. Locations: Abstract; Sections 2.1, 2.4, 4.3, and 5. Remaining limitation: conclusions are conditional on the frozen reference source-connectivity representation.

### Comment 3

> Damage states and restoration durations are generated through Monte Carlo simulation, but the scheduling stage subsequently uses the Monte Carlo mean restoration duration as a representative value for each substation. It is unclear how the scenario-specific repair-task set is determined when damage itself varies across realizations, and how uncertainty in damage and repair duration propagates into the reported strategy rankings.

Response: We replaced mean-duration task selection with DS>0 eligibility in each physical realization. One positive realized duration is stored for each damaged task and reused across all four policies. The queue is the full ex-ante sequence with DS0 removed; duration affects completion and later crew release but not priority order. Completion restores raw functionality directly, without a second continuous CDF. Thirty-two damage/duration pairs, not 128 independent physical samples, underlie the baseline comparison.

Paired intervals and ranking frequencies now quantify realization variation. Balanced is lowest in population burden in 68.75% of baseline realizations; Hospital-first in 6.25%, HospFirst in 25%, and Efficiency in none. The DS4-only duration contrast changes the Efficiency–HF population-burden difference by +11.169 h [9.303,12.880], demonstrating model-assumption sensitivity beyond within-distribution randomness. Locations: Sections 2.3–2.7, 3.1, and 3.3; Tables 2–3; Supplement S1.3/S3. Evidence: REALIZATION_STRATEGY_METRICS.csv and PAIRED_EFFECTS.csv. Remaining limitation: 32 existing samples under a fixed PGA field are not independent validation or comprehensive seismic uncertainty.

### Comment 4

> The comparison with historical restoration records provides a useful contextual check on the overall recovery timescale, but it should not be interpreted as a validation of the tract-level recovery model. In particular, the framework does not explicitly represent distribution feeders, customer-level switching, or utility emergency operations, and discrepancies remain across different recovery milestones. The authors should therefore more clearly frame the model as a scenario-based tool for comparing alternative restoration strategies rather than as a predictive representation of actual post-earthquake power restoration.

Response: We agree that historical restoration milestones cannot validate the tract model. The rewritten manuscript no longer uses historical curves as validation and consistently names the durations uncalibrated scenario-based on-site restoration actions. Travel is separate; mobilization, material wait, permanent reconstruction, distribution feeders, and emergency operating procedures are not represented. The DS4×2 contrast asks whether the same fixed decisions change performance under relatively longer severe-damage actions; it does not establish a more realistic duration. Efficiency's population excess increases from 15.076 to 26.245 h, whereas the two weighted-priority advantages remain small. Locations: Sections 2.3, 2.7, 3.3, and 4.3; Table 3. This is a focused assumption comparison plus scope clarification, not predictive restoration validation.

### Comment 5

> The current SVI-weighted recovery measure is essentially a population-and-SVI-weighted average service trajectory. An earlier SVI-weighted T_80 does not necessarily imply a more equitable restoration outcome, nor does it directly quantify inequality among communities. Indeed, the manuscript finds that SVI-weighted T_80 is often slightly earlier than population-weighted T_80. The authors should either introduce more explicit distributional-equity measures—such as recovery gaps between vulnerability groups or inequality measures—or moderate the claims regarding social equity. Similarly, the K-means typologies and top-10 composite hotspot score should be described primarily as descriptive screening tools rather than evidence of causal relationships between social vulnerability and delayed recovery.

Response: We removed the claim that SVI-weighted T80 establishes equity and removed clustering and composite hotspot analysis from the revised scientific argument. The vulnerability variable is correctly named NRI-derived SOVI_SCORE. We now report population-weighted normalized burden for fixed Q1–Q4 groups, signed and absolute Q4−Q1 gaps, population-weighted Gini, and tract-level paired changes. Absolute levels accompany the inequality statistics.

Efficiency illustrates why this matters: its lower Gini (0.1765 versus 0.2187) accompanies higher mean burden in all four groups, with Q4 +21.526 h relative to HF. Conversely, Balanced improves all four means but widens the absolute gap because Q4 already has lower modeled baseline burden. Twelve completely unresolved tracts retain NA outcomes rather than zero or near-zero classification. Locations: Sections 2.6, 3.2, and 4.1/4.3; Figures 2–3; Supplement S3. Remaining limitation: distributional metrics do not establish causal equity or constitute equity optimization.

### Comment 6

> The GA formulation requires more information on implementation and reproducibility, including population size, number of generations, crossover/mutation settings, stopping criteria, repeated runs, and convergence. The weighting choices in Table 2, particularly the hospital weight of 20, also require justification.

Response: The manuscript and supplement now disclose population size 100, 100 fixed generations, ordered crossover probability 0.8, inversion mutation probability 0.2, tournament size three, seeds 42–51 for each objective, and the 504 h surrogate horizon. Figure S1 shows the retained generation-best records and seed variability. We do not claim proven convergence or global optimality. Weight 20 is explicitly a hospital-dominant policy-design coefficient, not empirical calibration.

Candidate provenance also required correction. The original output retained the best final-generation member, although 28/30 histories contained a higher earlier score. Balanced/HospFirst deterministic priority initializers are reconstructible and attain their recorded maxima. We now use these candidates, not presumed unsaved intermediate sequences. An independent best-so-far archive/incumbent comparison prevents returning a known worse candidate without changing search replacement or RNG. No new GA was run. Locations: Section 2.5; Supplement S2, Table S3 and Figure S1. Remaining limitation: unknown intermediate chromosomes are not recovered and initialization gains are not attributed to genetic evolution.

### Comment 7

> The manuscript should explain more clearly why the relatively simple Hospital-first rule outperforms GA-HospitalFirst. If the GA is presented as an optimization benchmark, this result deserves further discussion regarding the difference between the GA fitness function and the reported T_80/AUC objectives.

Response: We no longer retain the old explanation that HF simply outperforms GA-HospitalFirst. Under the identical HospFirst surrogate and expected-workload decoder, the restored candidate scores 0.916459946176 and HF 0.916319981609. Corrected physical reevaluation gives population burden −0.166 h [−0.257,−0.064] relative to HF, but hospital-tract burden −0.022 h [−0.104,0.066] and T80 −0.197 h [−0.735,0.204]. The overall advantage is small and neither hospital advantage nor equivalence is established.

We separate candidate-retention quality from the mismatch between an additive completion surrogate and source-gated community outcomes. Efficiency remains an example of higher own-objective fitness with higher community burden; scores are never compared across different objectives. Locations: Sections 2.5, 3.1, and 4.1; Table 2; Supplement Table S3. We did not alter the objective to make a comparator win, and removed the superseded HF-superiority narrative.

## Reviewer 2

### Overall assessment

> This manuscript presents a set of steps using separate well-known methods taken to investigate contributing elements to disparities in post-earthquake power service restoration on a case study of Los Angeles. Specifically, it "combines established hazard, fragility, network-dependency, repair-logistic, and vulnerability-assessment components into a transparent workflow for evaluating earthquake-specific power-service recovery and community-level recovery disparities."

> The majority of the manuscript reads like an encyclopedia or dictionary of well-known methods. The manuscript is very long and very dull to read. The introduction is one short paragraph in length. The manuscript then immediately dives into a review of the literature without clear understanding of the manuscript's goals and motivation. The manuscript's contribution appears to be the study of factors in power service restoration that affect tract-level disparities in Los Angeles.

> The manuscript has some nice elements, but its methodological contributions are unclear despite many pages spent on methodologies and its findings are not particularly poignant or especially insightful. The application to Los Angeles sounds very interesting, as this city is very large, but the network is substantively reduced in size through assumptions designed to create a more aggregated and smaller problem instance, making it much less interesting. Moreover, the findings focus on the proposed methods and their effectiveness rather than on providing deeper understanding of or implications for disparities, how policies/regulations/strategies post-disaster can inadvertently create disparities, or how to avoid creating them.

> A number of additional comments/concerns follow that I hope will be helpful to the authors.

Response: We rewrote the full paper around a decision question rather than a catalogue of methods. A substantive Introduction now motivates why system completion, absolute community burden, and relative inequality can conflict. Section 1.1 gives a focused literature comparison and Section 1.2 states three questions that the retained experiments answer. Conventional implementation details have moved to the supplement; internal software interfaces and verification counts are not presented as contributions.

The Results follow three findings: modest aggregate differences with distinct group consequences; the non-equivalence of improving Q4, reducing overall burden, and shrinking gaps; and targeted assumptions that preserve some overall directions but alter group relationships or amplify costs. The model uses a larger retained inventory and a clearly separated task/outcome domain, without claiming a full electrical model. Locations: Title, Abstract, Sections 1–5, Tables 1–3, Figures 1–4. We have narrowed the interpretation to conditional distributional consequences, not proposed-method performance or optimized equitable planning.

### Comment 1

> I recommend separating out the literature review into its own section and writing a proper introduction to motivate the paper.

Response: The Introduction is now a substantive motivation followed by a distinct related-research subsection and explicit research questions. It explains the practical distinction between finishing repairs and allocating burdens during recovery before introducing the model. Section 1.1 discusses established logistics, service-access, power-flow, and equity-optimization work; Section 1.2 defines the conditional questions this study can answer. The revision does not merely move the old encyclopedic review intact. Remaining scope is stated at the start rather than deferred entirely to limitations. Locations: Sections 1, 1.1, and 1.2.

### Comment 2

> The literature review does not elucidate what gaps exist in the literature that this manuscript will fill. Why is this manuscript important to publish given the existence of these earlier works? What haven't they done that will be done in this manuscript?

Response: We rewrote the contribution around the comparison evidence that readers can use. Los Angeles restoration studies establish the importance of inspection, repair scheduling, and resource bottlenecks (Çağnan et al., 2006; Xu et al., 2007). Access-based resilience and multidimensional equity research motivate examining community consequences beyond system completion (Logan and Guikema, 2020; Lin et al., 2022). Cheng et al. (2024) assess Los Angeles census-tract seismic risk with DC load flow; Toplu-Tutay et al. (2024) explicitly incorporate equity in hardening optimization; Jiang et al. (2025) study restoration optimization under repair uncertainty. These are substantive precedents, rather than components whose assembly alone establishes a gap.

Our complementary question is how the same fixed restoration decisions are evaluated by cumulative population burden, absolute vulnerability-group burdens, and relative inequality under shared damage and workloads, and which comparisons depend on the two stated assumptions. The final Introduction paragraph now states this positive contribution: quantify small aggregate differences with different group consequences; identify who bears additional absolute burden when inequality falls; and distinguish overall directions that persist in the targeted contrasts from group judgments that remain assumption-dependent. Results provide concrete evidence: Balanced improves all four group means while widening the absolute high–low gap; Efficiency lowers Gini while increasing all four means; and the two contrasts retain overall directions but change group relationships or amplify community costs. Locations: Sections 1.1–1.2, especially the final contribution paragraph; Sections 3.1–3.3; Figures 2–4. We removed the defensive sentence about a contribution not resting on component assembly and consolidated repeated qualifications. The contribution remains conditional comparison evidence, not first-ever equity analysis, an improved optimization algorithm, or physical validation.

### Comment 3

> I also recommend moving most of the methods into appendices, as they do not appear to be novel, they are not well connected and they are taking away from what might be the real content of the manuscript.

Response: Main Methods retain only the domains, candidate mapping, realization information set, event dispatch, source proxy, sequence provenance, burden estimands, and paired design needed to interpret the findings. Fragility parameter tables, RNG details, search diagnostics, probability cleanup, and integral-reconstruction details appear in S1–S5. The updated Table 1 summarizes adopted assumptions and their limits. Internal adapter/exporter contracts, hash checks, round-trip counts, percolation, and clustering are absent from the scientific methods narrative. Locations: Section 2 and Supplement S1–S5. The conventional scheduler and GA are no longer claimed as methodological innovations.

### Comment 4

> The 3 questions on page 6 that guide the study are useful; however, the answers given for them at the end of the manuscript do not offer much we couldn't already guess from merely stating the questions. I expected much deeper and clearer findings with respect to these questions.

Response: We replaced the old questions with comparisons whose answers are quantitatively developed. The two weighted-priority sequences reduce mean population burden by only 0.295/0.166 h, yet HospFirst shifts burden from Q4 toward Q1. Efficiency's smaller Gini accompanies worse means in every group. The A/B contrast preserves overall directions while changing one signed group-gap relationship; DS4×2 increases Efficiency's excess population burden by a paired 11.169 h. These distinguish criteria and identify an assumption-dependent cost rather than merely ranking methods. Locations: Section 1.2 and Results 3.1–3.3; Figures 2–4; Conclusion. The answers remain conditional, not universal rules about hospital priority or real communities.

### Comment 5

> Table 1 is excellent.

Response: We retained the useful purpose of Table 1 as a concise parameter/source guide and rebuilt it around the actual final study. It now separates the fixed hazard field, 302 task assets, 57 pooled crews, event-completion durations, official candidates, unresolved mass, four fixed sequences, paired sample design, and the two executed contrasts. Removed rows include the old IDW cutoff, continuous recovery clock, and clustering settings. The table labels which entries are scenario assumptions rather than calibrated quantities. Location: Table 1 in Section 2.1.

### Comment 6

> Why identify the most critical substations? Does this align with the main goals of the paper?

Response: We removed identifying the most critical substations as a separate aim and removed centrality-based priority comparisons from the revised analysis. No top-ten criticality or hotspot ranking is rebuilt. Supplement S4.2 retains only a limited integral decomposition where it helps account for the reported policy burden contrast. It explicitly does not infer that the corresponding facilities are real-world critical nodes or that their own completion times alone caused the change. Locations: Sections 1.2 and 4.2; Supplement S4.2. This keeps the focus on distributional consequences of decisions rather than asset-ranking methodology.

### Comment 7

> I had difficultly following the normalized percolation curve discussion. Why does it need to be normalized? What is a redundantly meshed network? I'm not familiar with the idea of meshing.

Response: The normalized percolation curve and its meshing discussion have been removed because they are not needed to answer the revised research questions. We have not reconstructed them for this response. The network description now states only the relevant adjacency, task-component, and functional source-connectivity semantics, with the limits of electrical interpretation. Locations: Sections 2.1 and 2.4. There is consequently no new percolation normalization claim or unexplained redundantly-meshed terminology.

### Comment 8

> Minor type page 19, "Second, time sequence helps" should be sequencing and "Third, path validity mandates [the or that the] crew…"

Response: The affected legacy prose was replaced by a clear event-scheduling description rather than retained with isolated typographical edits. Section 2.4 now states that the next fixed-list task is assigned to the earliest available crew, travel uses the origin or previous task in the correct direction, and completion determines the next release. We checked terminology for sequencing and crew travel throughout the revised text. Location: Section 2.4, second and third paragraphs.

### Comment 9

> The use of a black-box genetic algorithm is very uninteresting. Why trust the GA? Why the GA? Where are the details of the GA or was it just a library?

Response: GA is now described as a transparent finite-budget search comparator, not the contribution or a black-box source of optimal policies. The surrogate, expected workload, search operators, budget, seeds, initializers, incumbent comparison, and historical output-retention issue are disclosed. Two adopted candidates actually come from deterministic initialization and are named accordingly; only Efficiency retains the selected search sequence. No claim is made that GA is necessary or superior to other methods. Locations: Section 2.5; Supplement S2, Table S3 and Figure S1. The retained search adds a comparator with a different surrogate emphasis, but the scientific contribution is the resulting conditional burden comparison. Remaining limitation: neither convergence to a global optimum nor algorithmic superiority is established.

### Comment 10

> Maybe the composite SVI score is the point of this paper and that portion of the paper could be the main focus?

Response: We considered refocusing on a composite vulnerability score but did not adopt it. The vulnerability measure is an existing NRI-derived score, not a new contribution, and an ad hoc composite hotspot would distract from the decision question. Instead we use fixed vulnerability quartiles to show absolute modeled burdens and paired changes, with a signed gap and Gini as complementary descriptions. The old clustering and composite hotspot analysis are removed. Locations: Sections 1.2, 2.6, 3.2, and 4.3. We acknowledge that tract vulnerability does not measure individual hardship or establish causal social effects.

### Comment 11

> The final LA network had 92 nodes with 318 edges. How large was the original network?

Response: The retained historical candidate-facility table contains 486 records. The old model had 92 nodes and 318 edges, but the historical rule selecting those 92 from the 486 could not be recovered. We now state that gap directly; replacing the old model does not recover or justify its original reduction. The 486 records were a facility candidate table, not a documented complete original electrical graph, so we cannot give a defensible complete-network size for that historical starting point.

The revised results instead use the documented inventory chain: 4,260 upstream database records → 3,374 SUBSTATION records → 2,775 IN SERVICE records → 2,548 with valid coordinates and original maximum voltage at least 34.5 kV → 310 covered by the fixed study-area polygon. The polygon is the union of 2,315 retained tract geometries; ownership and largest-component membership do not select the inventory. The predeclared boundary-source exception added no records. The 4,260 count is a database inventory, not the node count of the complete Los Angeles electrical system. Of the 310 retained records, 306 have identified network states and the 302-asset main component defines the task domain; the eight excluded task records and their reasons remain listed explicitly.

We also added how the line geometry becomes facility adjacency. Physical line-graph paths are blocked by intervening registered station nodes or projection anchors. The retained facility graph has 310 nodes and 1,040 undirected edges; its largest component has 302 assets, including all 117 resolved SCE upstream attachment targets. These geometric rules do not validate electrical switching or capacity. Locations: Methods 2.1 gives the selection overview and current graph scale; Supplement S1.1 gives the historical gap, full selection chain, intermediate-station rule, and component sizes; Table S6 identifies retained data vintages and unresolved dates. Evidence: the existing PROVENANCE_DECISION.md and R1_310_LOCAL_CLOSURE_REPORT.md. No network was rebuilt and no scientific result was changed for this clarification.

### Comment 12

> Many of the observations from the results are obvious. What is interesting that was found?

Response: The revised findings emphasize conflicts among decision criteria rather than familiar statements that order matters. In this model, Balanced improves all four group means yet increases the absolute high–low gap; Efficiency lowers Gini while worsening every group mean; and severe-damage duration changes increase its relative community cost without a corresponding clear increase in average logistics benefit. Mapping influence leaves overall effect directions intact but alters group-level relationships. Locations: Results 3.2–3.3 and Discussion 4.1–4.2; Figures 2 and 4. These are documented conditional examples, not claims that such relations universally hold.

### Comment 13

> I found the logistics-aware strategy section difficult to follow. Logistics-aware or logistics-constrained makes me think that the effects of limited resources will be modeled, but this aspect is not well explained. It's also not novel.

Response: Resource constraints are now stated concretely: 57 initially available pooled crews at eleven origin proxies, one task per crew at a time, no preemption, and release at completion. The earliest-release rule and directed travel determine which crew is next available, while the next task remains the next item in the fixed queue. C57 is a scenario resource budget, not verified utility staffing, and there is no utility-specific task restriction. Results report makespan and total travel beside community burden. Locations: Sections 2.4, 3.1, and 4.3; Tables 1–3; Supplement S1.3. This explains how logistics constrain the comparison, without claiming a novel scheduling method or an unperformed crew-number sensitivity.

### Comment 14

> Key: It was difficult to find findings within the solutions related to the main thing that the paper needs to show - the tradeoffs of using an "equity-informed, targeted restoration planning" approach. How much better would the outcomes have been in terms of reducing disparities if such a plan were used and at what cost and to whom? This may be buried in the results, but I struggled to find it.

Response: We now directly report who has lower or higher burden and the measured logistics differences, while narrowing the equity-planning claim. Under the ±1 h classification of 32-realization mean effects, Balanced improves 110 tracts containing 13.02% of the study population and worsens nine containing 1.10%; HospFirst improves 61 containing 7.37% and worsens three containing 0.33%. All these worsened tracts are in Q1. Efficiency worsens 663 tracts containing 80.07%, despite lower Gini. The twelve unresolved tracts remain separate. Realization-first population shares are also shown and are not confused with these mean-effect classifications.

The four sequences are not an isolated equity intervention or an optimized frontier. We therefore removed claims of the benefits of an equity-optimal plan. Locations: Sections 2.6, 3.2–3.3, and 4.1/4.3; Figures 2–4; Supplement Table S5. Remaining limitation: this answers distributional consequences of fixed policy bundles, not the optimal cost of reducing inequity.

### Comment 15

> Also a main finding is, "Overall, restoration-related assumptions primarily control the absolute duration of recovery, whereas topology-related assumptions mainly rest the robustness of service-propagation and tract-mapping boundaries." This is the final statement of the findings, yet I'm not sure what it really means or why the reader is concerned with these items. These are methods used in the study that are not necessarily well-adopted (or if they are, making that point would be very useful).

Response: We removed the quoted generalization. The new evidence shows why it was too broad: doubling only severe-damage task durations changes relative policy costs, increasing Efficiency's excess population burden by 11.169 h, rather than merely controlling a common absolute time scale. Conversely, A/B candidate weighting has small overall effects but changes some group relationships. These are the two actual tested contrasts; no conclusion about generic topology-related assumptions or all restoration assumptions is drawn. Locations: Section 3.3, Discussion 4.2, and Conclusion; Figure 4 and Table 3. This connects assumptions to decision consequences instead of judging the methods in the abstract.

### Comment 16

> Overall, the conclusions section is helpful for identifying what the authors see as the final outcomes and seems to be quite inclusive. However, it also opens more questions, as most of the findings are specific to the methods that are suggested (e.g. the source-gated topology concentrates network vulnerability vs…). These were never findings that the reader was interested in, but rather a means to some deeper insight that the authors are offering. That is, the findings seem to come down to judgements about the pros and cons of offered methods that the manuscript applies rather than findings related to the overall point of the paper, which is never really made, but seems to be something related to how decisions affect different tracts disproportionately.

Response: The title, abstract, research questions, Results, and Conclusion now center on how restoration sequences redistribute modeled burdens. We report population and group levels, paired tract effects, uncertainty, and logistics costs, rather than presenting interface tests or method rankings as findings. The three main conclusions are small overall differences with different distributional effects; the non-equivalence of Q4 improvement, lower total burden, and equalization; and assumption-dependent amplification or group sensitivity. Locations: Abstract; Sections 1.2, 3, 4.1–4.3, and 5; Figures 2–4.

We also state what these findings do not imply: no real-community causal attribution, delivered-power validation, fairness optimization, or Pareto frontier. The contribution is a conditional decision comparison with measured distributional consequences, and the remaining physical, data, and social limitations are explicit rather than treated as resolved by software reproducibility.
