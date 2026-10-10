# Independent review of stored Stage7 results

Input commit: 50df10481815f3dd94c46dc9443f93cfdb1c5014. No clustering was rerun. Seven hydrated LFS inputs were checked against their commit-specific SHA256 and byte length. Eight saved-label silhouettes were independently reproduced. Within sums of squares were recomputed after recentering saved labels, with small tolerance-stop differences recorded rather than represented as exact source discrepancies.

## Sample and selected k
The candidate universe has 2291 rows; 2287 are complete. Four original tract identities remain unclassified.
- D__inherited: selected k over 20 seeds {5: 20}.
- EAL__inherited: selected k over 20 seeds {5: 20}.
- D__equal_five_domains: selected k over 20 seeds {4: 20}.
- EAL__equal_five_domains: selected k over 20 seeds {4: 20}.

## Spatial sensitivity (fixed k=5 only)
- D__inherited: median full-cohort ARI 0.759060, minimum 0.300447; median heldout-only ARI 0.783226.
- EAL__inherited: median full-cohort ARI 0.864528, minimum 0.738042; median heldout-only ARI 0.906639.
- D__equal_five_domains: median full-cohort ARI 0.941676, minimum 0.562588; median heldout-only ARI 0.906583.
- EAL__equal_five_domains: median full-cohort ARI 0.836548, minimum 0.536919; median heldout-only ARI 0.846828.

## Interpretation limits
All reported spatial perturbations were fitted at k=5. They do not directly validate whichever k was selected by the elbow. Feature-choice sensitivity differs from missing-data sensitivity; whole-partition ARI is not a percentage of preserved labels. Profiles use seed42 labels and describe the saved joint typology, not a causal effect. Report the four unclassified tracts and their population coverage.
