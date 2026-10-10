# Supplementary Methods and Results draft

## Three distinct kinds of stability

Optimization stability repeats the same feature specification on the same full cohort with seeds 42-61. At k=4, median pairwise ARI across the 190 seed pairs was 0.9958 for D (minimum 0.9797) and 0.9860 for EAL (minimum 0.9600). Seed pairs are dependent summaries, not 190 independent experiments or sampling-confidence intervals. This does not resolve uncertainty in feature meaning or geographic sampling.

Specification comparisons use existing saved labels only. The full controlled study had 20 model specifications, 20 seeds and seven k values (2,800 recorded fits). This preview performs no additional cluster fitting. SAVED_SENSITIVITY_SUMMARY.csv reports fixed-k=4 and fixed-k=5 comparisons separately, with their actual reference and selected-k counts. Results at k=5 do not substitute for validation of the chosen k=4 candidate.

## Loss/exposure construct and recovery metric

Replacing separate log building stock and ALR with EAL_SCORE under the same 0.2 domain budget gives median fixed-k4 ARI 0.6286 against D. Both specifications select k=4 in all 20 seeds, but the larger classes differ. The seed-42 34-member subgroup is identical in both models. D preserves stock and multi-hazard loss propensity as separately interpretable coordinates; EAL combines expected loss and exposure. Better ARI or silhouette is not the scientific reason for selecting either representation.

Substituting T80 for raw B, with initial service and all other domains held constant, gives median k4 ARI 0.9111. On the same 2,287 tracts, B-T80 Pearson correlation is 0.9119 and Spearman correlation is 0.9292. They describe related recovery information but different estimands: an integrated deficit versus an 80% crossing of the mean trajectory. We use B because cumulative service loss is the study's substantive recovery quantity, not because it maximizes clustering performance. Replacing raw B by log1p(B) gives median k4 ARI 0.9755; it is a transformation sensitivity, not authorization to change the primary raw-hour input.

## Building age and domain weights

Replacing all-use 2014 observed-age share with the ACS residential pre-1970 housing share gives median fixed-k4 ARI 0.9148; omitting age gives 0.8445. Both age alternatives select k=5 in all 20 seeds, unlike the primary equal-domain D k=4. They change the physical construct and selected resolution. Omitting age redistributes the unchanged physical-domain budget across entropy and footprint coverage rather than reducing that entire domain's importance.

Inherited domain budgets were recovery/initial service 2/11, grid 4/11, built environment 2/11, social 1/11 and loss/exposure 2/11. Equal-five-domain weighting assigns 0.2 to each domain. At fixed k=4, median ARI between D under these two budgets is 0.2123 (range 0.2033-0.3398). Inherited D selects k=5 in all 20 seeds. The weighting decision therefore changes representation as well as selected resolution and must be stated rather than treated as a neutral preprocessing detail.

## Incomplete land classification and age observations

Existing SCAG missing-land scenarios allocate unclassified area to transportation, to the dominant class, or proportionally to classified categories. These are deliberately different measurement assumptions, not new observed land use. Under the inherited budget at fixed k=5, median ARI relative to inherited D is 0.8183, 0.8863 and 1.0000, respectively. Proportional allocation leaves entropy unchanged and is not an independent replication. Corresponding fixed-k4 records are available, but this sensitivity family uses inherited weights and is not a direct equal-domain-primary robustness test.

Age lower/upper bounds treat missing observed-age footprint area as entirely post-1970 or pre-1970. Under inherited weights at fixed k=5 their median ARIs are 0.8978 and 0.9511. These bound incomplete age observations and do not validate missing government-building years. No new equal-domain missing-land/age-bound factorial comparison was run, so that scope remains a limitation.

## Fixed-k4 geographic perturbations

Each model used the same 20 predefined spatial cases, with 17 unique geographic deletion sets, not IID tract bootstrap. The 20-km blocks were defined in EPSG:3310 from the original centroid positions. Two of 15 occupied blocks were deleted per case; training size ranged from 1,753 to 2,270 and held-out size from 17 to 534. Scaling and centroids were estimated only on training tracts in the earlier spatial study. Labels were aligned by one-to-one training overlap and that mapping was carried unchanged to the full and held-out cohorts. Statistical references were each seed's own saved full-cohort labels; display IDs were aligned within each model to its seed-42 partition and do not identify identical communities across D and EAL.

Member retention is intersection/baseline membership; purity is intersection/predicted membership; Jaccard is intersection/union. In seed 54's small-class case all 34 original members remain, but 58 other tracts join under D and 56 under EAL. This gives retention 1 and purity/Jaccard 34/92 or 34/90. No case lacked all training support; sparse support must not be described as zero support. Class-level summaries, raw contingency tables and feature shifts accompany the prior validation package. The combined profile is descriptive and cannot validate causal effects of variables also used to construct the partition.
