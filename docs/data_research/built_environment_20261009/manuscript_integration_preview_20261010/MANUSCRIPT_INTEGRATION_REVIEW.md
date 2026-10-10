# Manuscript integration review

This directory is an isolated author-review preview. It does not replace formal Stage 7, manuscript material, figures or hotspot results.

## Files ready for author review

- STAGE7_CANDIDATE_FREEZE.json and STAGE7_CANDIDATE_PARAMETERS.npz: source commits/hashes, exact tract order, labels, transformations, domain factors and reconstructed preprocessing. No new KMeans fit. Original scaler/algorithm centers were not serialized; label-member centers are explicitly identified as reconstructed, reproduce every original assignment and reproduce the selected run's inertia within tolerance.
- STAGE7_CANDIDATE_LABELS_2291.csv: exact 2,287 saved seed-42 labels and four UNCLASSIFIED_GEOMETRY records; no predicted or imputed labels.
- STAGE7_CLUSTER_PROFILES.csv, STAGE7_PROFILE_TABLES.md and UNCLASSIFIED_TRACT_CHARACTERISTICS.csv: raw-unit statistics, explicit population summaries and all four excluded tracts.
- STAGE7_OLD_NEW_CROSSWALK.csv and OLD_INTERPRETATION_DISPOSITION.md: common-domain contingency, ARI and interpretation changes, including the old manuscript/source-label semantic discrepancy.
- Three vector PDFs and 600-dpi PNGs, with captions in FIGURE_CAPTIONS.md: map, joint profiles and spatial stability/small-class expansion.
- Four section drafts: Methods, Results, Supplementary and Discussion/Limitations. The existing manuscript was read, not edited. New dataset bibliographic entries remain an editorial reference-manager check.
- Reproducible scripts, SOURCE_HASH_VERIFICATION.csv, OUTPUT_HASHES.csv, tests, VISUAL_QA.json and preservation checks.

## Claims supported with qualifications

The large-class contrast of modeled service loss versus social vulnerability, older observed buildings versus more mixed classified land use, and the relatively higher-initial-service 34-tract class can enter integration review as descriptive joint patterns. Optimizer seed agreement and broad spatial partition agreement are supported. Neither establishes causal effects, universal validation or an invariant taxonomy.

The C2 geographic boundary/profile is sensitive when only four members remain in spatial training; all original members survive but purity falls substantially. Fine C1/C4 grid rankings reverse in 12/20 cases. SCAG coverage, older imagery, partial 2014 age coverage and earthquake-dominated multi-hazard loss must remain visible. Old class names and old hotspot narratives must be rewritten or excluded from this candidate integration.

## Remaining scientific adoption gates

No missing numerical evidence blocks delivery of this preview: labels, source hashes, model matrix and raw profiles reproduce. Scientific qualifications remain substantive, especially the complete-case exclusion of four residential geometries and sparse-support contamination of the 34-tract group. The author must accept these limited descriptions before any formal replacement. Equal-domain missing-land/age-bound perturbations were not newly fitted; existing inherited-weight sensitivities cannot be called direct validation of the primary specification. No new hotspot score or intervention-response model is part of this preview. A future hotspot update requires a separate approved definition.

No formal Stage 7 labels, PCA, scientific source arrays, manuscript, existing figures, schedules, physical samples or GA results were modified. This round stops at the integration preview.
