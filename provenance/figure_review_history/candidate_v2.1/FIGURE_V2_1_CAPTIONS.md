# Figure v2.1 draft captions

## Fig01_Revised_Analytical_Framework

Revised analytical framework. Fixed earthquake scenarios provide station-level PGA inputs for damage-state sampling. Modeled station service is combined with the production source-reachability gate and utility-compatible tract dependency. Frozen restoration policies operate on damaged tasks with realized durations, directed travel, and crew dispatch. Downstream evaluation reports recovery, burden, distributional outcomes, descriptive typology, and bounded robustness checks. The production source gate is a reachability representation; it does not model power flow, generation adequacy, capacity, or delivered MW.

## Fig02_System_Network_Mapping_and_Public_Site_Check

Study system, utility-compatible tract dependency, and public-site agreement. (A) Physical CEC network context and (B) the retained model graph (92 stations, 318 edges, 14 Core sources); both geographic source panels are preserved from the existing authority. (C) Frozen utility-domain eligibility for all 2,315 study tracts: SCE (817) and LADWP (848) domains use utility-matched candidate pools; other/ambiguous tracts (650) retain the July general candidate pool. The separate M0-to-revised dependency-weight shift remains in the mapping-robustness evidence. (D) Any-, top-1-, and top-3-candidate agreement with public-site evidence for the 337 directly comparable tracts contrasts the distance-based general-pool baseline with revised utility-compatible eligibility. The 337-row direct-site set differs from the earlier 342-tract crosswalk (316 shared; 26 old-only and 21 current-only); denominators are not pooled. Public-site agreement is supporting evidence, not accuracy, feeder validation, or service-territory ground truth.

## Fig03_Hazard_Service_Loss_and_Unconstrained_Baseline

Hazard context and Unconstrained baseline chain. (A) Distribution across 92 stations of station-specific mean damage state, each mean derived from 1,000 frozen realizations; boxes summarize station heterogeneity, not Monte Carlo uncertainty. (B) Empirical tract distribution of mean initial modeled service for each hazard. (C) Unconstrained integrated burden decomposition into local physical damage, functionality-threshold loss, and source-path loss; all component values use the accepted C57_D1 summary row for the no-scheduling Unconstrained reference and the common 0–480 h integral. This is not a restoration-policy comparison. (D, left) 2pc50 population-weighted T80 across 1,000 Unconstrained realizations; unreached outcomes are not assigned the 480 h horizon. (D, right) Mean tract T80 among reached tracts; unreached/missing values remain gray. Historical hazards and 2pc50 use different adopted fragility parameter sets, so cross-hazard differences are not pure PGA sensitivity.

## Fig04_All_Policy_Recovery_and_Outcomes

Recovery and outcomes for all eight distinct scheduled policies plus the Unconstrained reference under 2pc50, C57_D1. Panel A displays mean population service availability over 0–120 h; panels B summarize outcomes integrated/evaluated over the full 0–480 h horizon. Dots are realization means and whiskers show the 5th–95th realization range (n=1,000), not confidence intervals. Impact-first, Degree-first, Hospital-first, and Vulnerability-first receive stronger visual emphasis; Centrality-first, Betweenness-first, Closeness-first, and Random remain displayed as lower-emphasis comparators. Unconstrained is the black reference. Direct-community is omitted because its frozen sequence is the same as Impact-first. Source-path-related burden is a modeled loss component, not delivered electricity.

## Fig05_Distributional_Outcomes_and_Reference_Sensitivity

Distributional outcomes and matched-reference sensitivity under 2pc50, C57_D1. (A) Absolute Q1–Q4 service burden for Impact-first, Hospital-first, Degree-first, and Vulnerability-first; whiskers are 5th–95th realization ranges, not confidence intervals. Q1 and Q4 denote the lowest- and highest-social-vulnerability quartiles. (B) Mean aggregate population-weighted service burden versus mean Q4 burden for all eight distinct scheduled policies and Unconstrained; points are summary estimates and no two-dimensional uncertainty is encoded in this panel. (C) For each physical realization, the Vulnerability-first outcome is differenced from Impact-first, Hospital-first, or Degree-first. Hour-valued outcomes use the labeled hour axis; population-weighted Gini change uses a separate unitless axis. Gini is 0 under equal tract burden and increases with inequality. Whiskers are 5th–95th paired-realization ranges. (D) Tract-level mean burden change, Vulnerability-first minus Impact-first, over the same physical realizations. Negative values indicate lower mean burden under Vulnerability-first; the map does not show statistical significance or the per-realization count of people helped.

## Fig06_Two_Level_Crew_Resource_Contrast

Two-level crew-resource contrast for 2pc50 with the frozen D1 repair-duration case. The figure compares the accepted 29-crew and 57-crew cases for Impact-first, Hospital-first, Degree-first, and Vulnerability-first on population-weighted service burden, highest-vulnerability-quartile burden, absolute high–low vulnerability burden difference, and hospital-linked tract service burden. Dots are means and whiskers are 5th–95th realization ranges (n=1,000 per policy/case), not confidence intervals. This is a comparison of two tested crew conditions, not a continuous response curve or a result for unshown resource levels.

## Fig07_Community_Typology_and_Hotspots

Harmonized Stage 7 community typology and hotspot screening for 2pc50. (A) Cluster means for selected variables expressed as z-scores across the five cluster means. (B) The residential typology includes 2,291 of 2,315 study tracts; the 24 tracts outside the residential typology are hatched gray and are not assigned a cluster. Cluster colors use the official Stage 7 cluster-ID palette, shared with FigS09. (C) The official combined slow-vulnerable score is a screening indicator, not a repair priority, intervention ranking, or independent causal validation.

## FigS05_GA_Reproducibility

Frozen five-seed Genetic Algorithm (GA) planning evidence for 2pc50. (A) Generation-mean candidate objective for each seed and the frozen Impact-first incumbent/best-so-far reference. Candidate means vary by generation; the best candidate attained by each seed does not exceed the incumbent. (B) Best generation candidate by seed compared with the incumbent; no seed improved it. (C) The retained sequence is Impact-first; Direct-community is sequence-equivalent, not an additional scheduled policy. This finite five-seed search does not establish global optimality and did not use evaluation realizations to choose a strategy.

## FigS09_Stage7_Diagnostics

Frozen Stage 7 support diagnostics for the harmonized 2pc50 residential typology. (A) PCA scores for 2,291 eligible tracts colored by the same official cluster-ID palette used in Fig07. (B) Explained variance by component. (C) Loadings in the accepted log1p-exposure, standardized feature space. (D) Frozen k-means inertia (left scale) and silhouette coefficient (right scale) across candidate cluster counts. These panels document dimensionality-reduction and clustering support; they do not turn clusters or hotspots into repair strategies.

## Candidate_Supplement_Cross_Hazard_Policy_Robustness

Cross-hazard policy contrasts from frozen accepted summaries. Each cell is the mean paired difference between one scheduled policy and the Unconstrained reference within the same hazard-specific 1,000 physical realizations; the source CSV records 5th–95th paired-realization ranges. Negative burden differences indicate lower burden relative to Unconstrained; negative T80 differences indicate earlier population recovery. Each panel has its own symmetric color scale centered at zero. The four hazard scenarios use different fragility parameter sets for historical hazards versus 2pc50, so the panels are scenario contrasts, not pure PGA sensitivity. Direct-community is omitted as Impact-first sequence-equivalent.

## Candidate_Supplement_Crew_Resource_Contrasts

Frozen discrete crew-count comparisons under 2pc50 and D1 for all eight distinct scheduled policies. Panels show population-weighted burden, highest-vulnerability-quartile burden, absolute high–low vulnerability burden difference, and hospital-linked tract service burden. Dots are realization means and whiskers are 5th–95th realization ranges (n=1,000 per policy/case), not confidence intervals. The tested categories are 29, 57, 86, and 114 crews; connecting values or trends between these categories are not inferred. Direct-community is omitted because its sequence equals Impact-first; Unconstrained has no scheduled crew case.

## Candidate_Supplement_Repair_Duration_Contrasts

Frozen discrete repair-duration comparisons under 2pc50 and C57 for all eight distinct scheduled policies. Panels show population-weighted burden, highest-vulnerability-quartile burden, absolute high–low vulnerability burden difference, and hospital-linked tract service burden. Dots are realization means and whiskers are 5th–95th realization ranges (n=1,000 per policy/case), not confidence intervals. The accepted tested multipliers are D0.75, D1, D1.25, and D1.50; categories are discrete scenarios and no interpolation is implied. Direct-community is omitted because its sequence equals Impact-first; Unconstrained has no scheduled repair-duration case.
