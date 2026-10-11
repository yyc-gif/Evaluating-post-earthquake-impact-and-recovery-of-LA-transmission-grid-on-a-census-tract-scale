# CORE3 W1 scientific adoption decision

**ADOPT_AS_CONDITIONAL_STAGE7_REFERENCE.** Use a concise descriptive Stage 7 account in the main manuscript, with the full profiles, weight comparisons and geographic sensitivity in the supplementary material. This is a review recommendation, not formal promotion. Do not call the partition a universal, independently validated, predictive or causal community taxonomy.

## 1 Reproducibility

The archived input matrix was independently reconstructed from the actual source bytes in exact GEOID order. All twelve coordinates, the saved scaler, weighted matrix, seed-42 labels and actual saved estimator centers agree. Nearest-center evaluation reproduces every saved label without fitting. The complete sample is 2,287, the residential master 2,291, and the electricity-model universe 2,315. Four geometry-unresolved records remain null. Their 12,390 mapped residents are distinct from the 16,979 residents of the 24 outside-cohort tracts. Formal CSV identifiers serialized without their leading zero were restored deterministically to eleven digits solely for comparison; no original table was edited. See INDEPENDENT_SCIENTIFIC_QA.json and FORMAL_GEOID_SERIALIZATION_AUDIT.json.

## 2 Constructs and weights

CORE3 distinguishes built-surface coverage, housing-unit configuration and classified-parcel composition. It does not measure the entire built environment. W1 is defensible as a transparent equal-five-parent convention: recovery, grid, physical, social and economic stock/loss each receive 0.20; stock and ALR split the economic parent equally. Distinct measurement meanings do not require separate equal parent budgets. No data-driven optimality is claimed. Scores retain their published scales before standardization; only monetary stock is log1p transformed. ALR is unadjusted multi-hazard loss propensity, not pure hazard. The feature-selection and weighting gates are closed.

## 3 Supported original-unit descriptions

C1/C2/C3/C4 contain 650/802/801/34 tracts. Mean B is 36.2488/35.2091/31.0927/23.6011 h; mean SOVI is 31.1408/84.1608/77.5061/67.9862. C1 combines relatively lower SOVI with greater B than C2 and C3 under W1. C2 has greater built coverage, 5+ housing share, entropy and ALR than C3 under W1. C1 has the largest median monetary stock ($667.1411 million). All twelve-coordinate raw profiles, medians and measurement coverage are in CORE3_W1_VERIFIED_PROFILES.csv and CORE3_W1_PROFILE_TABLE.csv. Tract-weighted values and population-weighted B are explicitly separate. C4's initial service is 1.8153%, not uninterrupted service or a universally resilient class.

## 4 Stability and failures

The 190 W1 seed pairs have median ARI 1.0000 and minimum 0.998737625. Twenty spatial cases (seventeen unique deletion sets) have median ARI 0.879221778, fifth percentile 0.715234632 and minimum 0.692932771, with at most 255 reassignments. These are registered sample perturbations, not independent geographic validation. No post-result acceptance threshold is introduced.

Direction support is counted against W1 seed42 after explicit overlap alignment. C1>B(C3) persists in 20/20 W1 spatial cases and 80/80 W2–W5 complete-cohort cases; C1's lower SOVI than C2 and C3 persists in the same sets. Yet W3 geographic cases reverse each of these SOVI comparisons in 2/20 cases. C2>B(C3) and C2>SOVI(C3) persist in 20/20 W1 spatial cases, but both reverse in 20/20 complete-cohort W5 cases (and in 15/20 and 17/20 W5 geographic cases). Minor W1 rankings also reverse: C1 versus C3 HHI reverses in 4/20 spatial cases; their initial-service and 5+ housing directions each reverse in 1/20. Support for a direction is not membership stability, magnitude equivalence or statistical significance. CORE3_W1_CLAIM_STABILITY.csv provides all 720 pair/feature/family summaries, with exact N=20 and per-case evidence.

Median same-seed reassignment relative to W1 is W2 12.3306%, W3 34.4993%, W4 5.9904%, W5 23.8741%. The nominal W1 grid budget is 20%, whereas its median observed BSS share is 2.3821%; social and recovery shares are 39.9791% and 29.1452%. BSS/TSS and within-class spread distinguish modest grid mean separation from lack of relevant dependency information. These results do not demonstrate that grid measurements are irrelevant or redundant.

## 5 Minority specificity

The exact 34-GEOID set is verified, not inferred from a historical class number. In the adverse seed54 deletion, four original members remain in training; all 34 remain in the W1 matched full prediction, which expands to 92 and absorbs 58. Retention=100%, purity=Jaccard=36.9565%. The failure is loss of specificity despite training support, not disappearance of tracts. W2/W3/W5 can yield zero original-member retention in the training-aligned counterpart, while those same original tracts are predicted in other destination classes. Full raw contingency and destination counts are retained. Do not name this group a stable archetype or justify intervention by its membership.

## 6 Conditional use versus stable taxonomy

The candidate is sufficiently documented and reproducible for an explicitly conditional exploratory main-text characterization. The evidence is insufficient for a stable community taxonomy. Optimization consistency does not resolve model-definition sensitivity. W1 is the reference convention, not a uniquely correct geographical partition. The current gate supports the separate S19 review copy, not replacement of formal Stage 7.

## 7 Withdrawn previous findings

Withdraw the original five-class names and the BE0 counts 850/34/651/752 as descriptions of CORE3/W1. On 2,287 common GEOIDs, formal5 versus CORE3 ARI is 0.201656240; BE0 versus CORE3 is 0.655022087. These partitions are scientifically different. Withdraw age/density-based class mechanisms, old PCA/loading descriptions as the new model specification, old hotspot-by-cluster ranks and class-dependent funding/dispatch recommendations. Original PCA was diagnostic/visualization after clustering in standardized coordinates; the new solution uses no PCA. Historical hotspot scores used rank-percentiles of T80, ACS pre1970, composite NRI risk and SOVI. Those inputs are not the current primary specification and their ranks are not transferred. Preserve historical records as provenance, not current claims.

## 8 Independent findings retained

Retain the established restoration-policy, fixed SOVI quartile and source-gated service analyses independently of clustering. S19 Figures 1–6 and Tables 1–3 are not Stage 7 figures and are not replaced. KEEP in the ledger means unaffected by this Stage 7 change; it is not revalidation of all numerical content or the unrelated GA narrative. Between-class B/initial-service differences are descriptive because those variables enter the clustering.

## 9 Remaining uncertainty and integration boundary

Fixed k=4 and W1 remain conceptual/specification choices, not proof of uniquely valid classes. Geographic support is dependent and sparse for the minority class. EMC resolution, ACS variance, SCAG partial coverage/carry-forward classifications and FEMA vintage/construction constrain meaning. Four geometry records remain unresolved. No new source acquisition, k/weight search, fitting, PCA or physical computation is required or authorized by this decision. Main text should present the conditional large-class descriptions and immediately disclose sensitivity; detailed alternatives and the minority specificity failure belong in the supplementary material. The exact numbering is proposed only and requires author approval together with adoption.
