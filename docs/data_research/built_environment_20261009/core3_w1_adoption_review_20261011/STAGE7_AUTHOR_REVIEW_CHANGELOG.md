# Stage 7 author review change ledger

Source S19 SHA256 `a61472ed6918f505dfd0c26b88ce24f9d184f6dca076194b5032014142acd253`. Separate review copy only. Existing scientific results and the original file are unchanged.

## P0002

review metadata

Original: Resubmission reconstruction from the retained July 23, 2026 manuscript. Coauthor review draft; all numerical findings below are from the frozen September 2026 formal experiment unless explicitly identified as external evidence.

Proposed: Author review copy proposing the conditional CORE3/W1 Stage 7 reference. Other sections, numerical results and existing figures retain the author-confirmed S19 working draft. This copy does not promote the new classification to the formal analysis.

## P0009

replace Stage7 clause only

Original: Three questions organize the study. First, how do station damage and source-path connectivity propagate to spatially different tract service deficits? Second, how do scarce crews, travel, task duration, and fixed repair priorities alter system and community recovery under identical physical realizations? Third, where do long recovery burdens coincide with vulnerability, built-environment exposure, risk, and modeled grid dependency, and who benefits or loses when restoration priority changes? The network is an abstraction and tract assignments are dependency proxies. These boundaries motivate the external candidate benchmark, mapping and gate contrasts, and explicit loss decomposition rather than claims of feeder-level validation or delivered electricity.

Proposed: Three questions organize the study. First, how do station damage and source-path connectivity propagate to spatially different tract service deficits? Second, how do scarce crews, travel, task duration, and fixed repair priorities alter system and community recovery under identical physical realizations? Third, where do long recovery burdens coincide with vulnerability, physical built environment, economic stock, multi-hazard loss propensity, and modeled grid dependency, and who benefits or loses when restoration priority changes? The network is an abstraction and tract assignments are dependency proxies. These boundaries motivate the external candidate benchmark, mapping and gate contrasts, and explicit loss decomposition rather than claims of feeder-level validation or delivered electricity.

## P0023

replace Stage7 clause only

Original: The fixed NRI-derived SOVI_SCORE quartiles label Q1 lowest and Q4 highest vulnerability. For each sequence and physical realization we calculate absolute population-weighted normalized burden in each quartile, signed Q4−Q1 gap, its absolute value, population-weighted tract burden Gini, and paired tract differences relative to a named rule. Improved, near-zero, and worsened tracts use a predeclared ±1 h practical threshold on paired mean effects; unresolved tracts remain separate. This threshold is not statistical significance. Bootstrap and direction-frequency comparisons resample physical realizations, not tracts. The retained Stage 7 PCA/K-means and hotspot screening examine co-occurrence among recovery, vulnerability, built environment, risk, and grid-dependency attributes. They are descriptive typologies and do not establish causal mechanisms.

Proposed: The fixed NRI-derived SOVI_SCORE quartiles label Q1 lowest and Q4 highest vulnerability. For each sequence and physical realization we calculate absolute population-weighted normalized burden in each quartile, signed Q4−Q1 gap, its absolute value, population-weighted tract burden Gini, and paired tract differences relative to a named rule. Improved, near-zero, and worsened tracts use a predeclared ±1 h practical threshold on paired mean effects; unresolved tracts remain separate. This threshold is not statistical significance. Bootstrap and direction-frequency comparisons resample physical realizations, not tracts. The joint CORE3/W1 community classification is descriptive and conditional on its feature definitions, fixed four-class partition and declared domain weights.

## P0040

replace Stage7 clause only

Original: The Q4 targeting tradeoff depends on resources. At C29, vulnerability-first lowers Q4 burden by 6.385 h relative to hospital-first, but adds 1.710 h to population burden, 6.255 h to T80, and 15.268 h to absolute group separation. At C86/C114, policy differences approach zero. Under the three historical hazards, Q4 gains relative to hospital-first are only 0.004–0.015 h; the larger 2pc50 effect cannot be generalized to every hazard. The Stage 7 descriptive typology retains recovery, vulnerability, built environment, risk, and dependency variables. Its 2,291 analyzed tracts form five clusters in the formal log-transformed specification; 24 tracts are excluded from the clustering input rather than silently assigned. Cluster membership is sensitive to raw versus log-tailed exposure features (adjusted Rand index 0.484), although the top-ten slow-vulnerable hotspot overlap is complete. These clusters screen co-occurring tract attributes; they do not attribute individual recovery times causally to vulnerability or housing.

Proposed: The Q4 targeting tradeoff depends on resources. At C29, vulnerability-first lowers Q4 burden by 6.385 h relative to hospital-first, but adds 1.710 h to population burden, 6.255 h to T80, and 15.268 h to absolute group separation. At C86/C114, policy differences approach zero. Under the three historical hazards, Q4 gains relative to hospital-first are only 0.004–0.015 h; the larger 2pc50 effect cannot be generalized to every hazard. 

## P0047

replace Stage7 clause only

Original: The positive repair-duration parameters and pooled C57 crews are scenarios rather than observed earthquake staffing or calibrated task times. Historical earthquake fields are hazard contexts, not validation against historical restoration milestones. The distributional results are normalized modeled service deficits, not resident hours without electricity. The vulnerability-first policy tests one transparent Q4-targeted decision and does not isolate a complete efficiency–equity frontier. Cluster and hotspot outputs are descriptive screening. These boundaries are material to application: a future operational study would need utility feeder/customer links, switching and demand, crew records, and observed outages before recommending a specific field dispatch order.

Proposed: The positive repair-duration parameters and pooled C57 crews are scenarios rather than observed earthquake staffing or calibrated task times. Historical earthquake fields are hazard contexts, not validation against historical restoration milestones. The distributional results are normalized modeled service deficits, not resident hours without electricity. The vulnerability-first policy tests one transparent Q4-targeted decision and does not isolate a complete efficiency–equity frontier. CORE3/W1 class descriptions are conditional on the chosen specification and geographic support; historical hotspot ranks are not transferred to the new partition. These boundaries are material to application: a future operational study would need utility feeder/customer links, switching and demand, crew records, and observed outages before recommending a specific field dispatch order.

## after P0023, inserted methods1

insert targeted Stage7 paragraph

Original: (new material)

Proposed: We characterized communities using a joint descriptive classification of recovery and initial modeled service, grid dependency, built environment, social vulnerability, and economic stock and multi-hazard expected-loss propensity. The recovery coordinate B is the tract mean normalized cumulative modeled service deficit over 0–480 h, averaged over the existing 1,000 2pc50 realizations under C57/D1 and the direct-community sequence, production utility-compatible mapping and baseline source-connectivity gate. Init_Supply is the saved initial modeled service measure. B summarizes the full evaluation horizon; T80 is the first exact completion-event crossing of 0.8 by the mean tract service trajectory, not the mean of realization-specific crossing times; it is retained only for description and is not a clustering coordinate. Recovery and initial service are inputs to this classification, so their between-class differences do not independently validate it.

## after P0023, inserted methods2

insert targeted Stage7 paragraph

Original: (new material)

Proposed: The twelve coordinates were B, Init_Supply, mapping-weighted Grid_Degree, Grid_Impact, Grid_Betweenness and Redundancy_HHI; EMC2022 total built-land fraction, ACS 2022 five-year share of housing units in structures with five or more units, SCAG2020 classified-parcel land-use entropy; FEMA SOVI_SCORE; log1p(BUILDVALUE); and ALR_NPCTL. Grid_Impact is the dependency-weighted network λ2-impact descriptor. These grid measures describe modeled dependency, not delivered electricity or electrical capacity. EMC uses Sentinel-2 observations from 2022 in the JRC EMC-BUILT R2025A product. ACS describes housing units over 2018–2022, not building counts. SCAG entropy describes the classified parcel land in the 2020 inventory, including carried-forward 2019 classifications; it does not represent all tract land. FEMA NRI v1.19 (March 2023) supplies social vulnerability, monetary building stock and the unadjusted composite annualized loss-rate percentile. ALR is multi-hazard expected-loss propensity, not pure hazard intensity. Building age and population density are not primary coordinates.

## after P0023, inserted methods3

insert targeted Stage7 paragraph

Original: (new material)

Proposed: We standardized each coordinate using the saved full-cohort StandardScaler mean and population standard deviation, then multiplied it by sqrt(w/q), where w is its domain's squared-distance budget and q its number of coordinates. W1 assigns 0.20 each to recovery/service, grid, physical and social domains, and 0.10 each to stock and ALR. Thus stock and loss propensity share a 0.20 parent budget while remaining separate measurements. Coordinates share their own domain budget equally. This convention expresses a declared conceptual balance, not empirically optimal weights. We used the previously selected four-class K-means solution (seed 42, n_init=100, max_iter=500, tol=10⁻⁴, Lloyd algorithm; scikit-learn 1.5.1), without PCA reduction. Of the 2,291 residential tracts, 2,287 have complete inputs; four unresolved geometry records remain unclassified without imputation. The other 24 tracts in the 2,315-tract electricity-model domain are outside this residential typology cohort.

## after P0023, inserted methods4

insert targeted Stage7 paragraph

Original: (new material)

Proposed: We assessed optimization sensitivity using the twenty saved seeds 42–61 and specification sensitivity using four registered alternative weight conventions. Geographic sensitivity used twenty registered 20-km spatial-block deletion cases representing seventeen unique deletion sets. Each saved spatial fit estimated its scaler and centroids on retained training tracts and predicted the complete cohort. Class alignment used maximum training-set overlap only; held-out labels were not used to select the mapping. We report raw contingency tables, ARI, retention, purity and Jaccard. These perturbations test sample sensitivity and are not independent geographic validation. Class identifiers C1–C4 refer only to this specification.

## after P0040, inserted results1

insert targeted Stage7 paragraph

Original: (new material)

Proposed: Under CORE3/W1, the 2,287 classified tracts formed groups of 650 (C1), 802 (C2), 801 (C3) and 34 (C4), containing 2,441,616, 3,143,470, 3,327,909 and 124,158 mapped residents, respectively (temporary Figures 7–8 and Table 4). Tract-mean cumulative modeled service loss was 36.25, 35.21, 31.09 and 23.60 h. Mean SOVI_SCORE was 31.14, 84.16, 77.51 and 67.99. C1 therefore combined lower social vulnerability with greater modeled service loss than C2 and C3 within this specification; this co-occurrence does not imply that vulnerability causes recovery differences.

## after P0040, inserted results2

insert targeted Stage7 paragraph

Original: (new material)

Proposed: C2 had larger mean built-land fraction (0.331), five-or-more-unit housing share (0.506) and classified-land entropy (0.453) than C3 (0.301, 0.214 and 0.301). C1 had the greatest median monetary building stock ($667.14 million), compared with $484.27 million for C2, $350.34 million for C3 and $389.58 million for C4. Median ALR percentiles were 79.24, 89.04, 75.19 and 69.55. These quantities characterize different physical and economic dimensions; their alignment is conditional on the selected weights. Median classified-land coverage was 0.764, 0.748, 0.750 and 0.715, respectively, and entropy excludes unclassified land. All means here weight tracts equally; Table 4 separately identifies population-weighted service loss.

## after P0040, inserted results3

insert targeted Stage7 paragraph

Original: (new material)

Proposed: The twenty optimization seeds gave a median pairwise ARI of 1.0000 and minimum 0.9987 (190 seed pairs). Registered W1 spatial deletions gave median ARI 0.8792, minimum 0.6929, and at most 255 reassigned tracts after training-based alignment. C1's greater mean loss than C3 was retained in all 20 W1 spatial cases and all 80 full-cohort W2–W5 comparisons. Some class rankings did not persist: the C2–C3 mean service-loss and SOVI ordering reversed in all 20 full-cohort stock-emphasis W5 comparisons. Median same-seed reassignment relative to W1 was 12.33%, 34.50%, 5.99% and 23.87% for W2–W5. Consequently the four classes are a conditional descriptive partition, not a stable universal taxonomy.

## after P0040, inserted results4

insert targeted Stage7 paragraph

Original: (new material)

Proposed: C4's initial modeled service mean was 0.01815 (1.815%), higher than the other class means but far from continuously available service. Under a deletion leaving only four original C4 members in training, the W1 matched prediction retained all 34 original members but expanded to 92 tracts, with 36.96% purity and Jaccard overlap. Retention therefore did not establish membership specificity. We retain C4 as a specification-dependent subgroup and do not assign it a stable resilience archetype or a class-based intervention priority. The four unresolved residential tracts, containing 12,390 mapped residents, remain unclassified.

## after P0047, inserted discussion1

insert targeted Stage7 paragraph

Original: (new material)

Proposed: The joint classification describes where modeled recovery, physical form, vulnerability and economic loss propensity co-occur. Its strongest W1 contrasts support tract-group descriptions; they do not isolate a built-environment effect or independently validate recovery, which is itself an input. Social and recovery/service coordinates accounted for median shares of 39.98% and 29.15% of weighted between-class separation across the twenty W1 fits; physical, ALR, stock and grid shares were 11.07%, 11.44%, 5.99% and 2.38%. These observed contributions differ from the nominal distance budgets. Weak between-class grid separation does not establish that grid dependency is irrelevant or redundant.

## after P0047, inserted discussion2

insert targeted Stage7 paragraph

Original: (new material)

Proposed: Interpretation remains conditional on fixed k=4 and the W1 conceptual hierarchy. Reasonable alternative weights change substantial membership and some recovery and vulnerability rankings, while sparse spatial support reduces the specificity of the 34-tract subgroup. Geographic deletions are dependent perturbations of this study population. EMC cell resolution and boundary support, ACS sampling uncertainty, SCAG partial classified-land coverage and carried-forward records, and FEMA vintage and loss construction limit the physical and economic descriptions. ALR represents multi-hazard loss propensity, whose regional composition is strongly earthquake-dominated; it is not a tract shaking variable. Four unresolved residential geometry records remain unclassified. The previous five-class names, age/density interpretations, PCA presentation and hotspot-by-class recommendations do not transfer to CORE3/W1. Existing restoration-policy and SOVI-quartile comparisons remain separate analyses.

## new Table4 after Stage7 results

insert table; existing Table1–3 unchanged

Original: (new material)

Proposed: Temporary Table 4. Original-unit CORE3/W1 class profiles (fixed k=4, seed 42, 2,287 classified residential tracts). Entries are unweighted tract means [medians] unless otherwise stated. Population is the sum of saved mapping populations; population-weighted service loss is identified separately. Log stock is the fitted coordinate; original monetary stock is also reported. T80 and measurement coverage are descriptive, not additional clustering inputs. B is mean normalized modeled service loss over 0–480 h for the saved 2pc50/C57/D1 direct-community trajectories. Four unresolved residential tracts are reported separately and receive no class. No intervals in this table represent confidence intervals. T80 summaries are across tract mean-trajectory crossing times, not across realization-specific T80 values.

## new temporary Figure7 at figure-section end

insert preview; existing six images unchanged

Original: (new material)

Proposed: Temporary Figure 7. CORE3/W1 residential tract membership. The saved four-class seed-42 partition classifies 2,287 of 2,291 residential tracts using twelve standardized coordinates and W1 squared-distance budgets. Gray denotes the four geometry-unresolved residential tracts; white denotes the 24 tracts outside the residential cohort, not necessarily tracts without residents. Boundaries are the archived study tract polygons, not utility service territories. CORE3 combines 2022 EMC built surface, ACS 2018–2022 housing structure and SCAG2020 classified-parcel composition; these measurements are not fully contemporaneous. Class membership is descriptive and specification-dependent.

## new temporary Figure8 at figure-section end

insert preview; existing six images unchanged

Original: (new material)

Proposed: Temporary Figure 8. CORE3/W1 joint profiles. Cells show unweighted tract-mean standardized coordinates relative to the 2,287-tract reference scaler, solely for visual comparability. Numeric annotations show the actual z values; color saturates outside ±2.5. The clustering itself uses W1 domain weights, not this unweighted color scale. Columns show the saved four classes (seed 42). Table 4 reports original-unit means and medians. B and initial modeled service are classification inputs, so their class differences are not independent validation or causal effects. EMC2022, ACS 2018–2022, SCAG2020 and FEMA v1.19 have distinct observation scopes and restrictions.

Existing source paragraphs not listed above, original Tables1–3, Figures1–6, styles, references, equations, headers/footers and all original media remain byte-identical. New page flow reflects only targeted inserted Stage7 content. The old BE0 review is not the layout/template authority.
