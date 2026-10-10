# Stage 7 next gate — construct-driven physical inputs, recovery and risk (2026-10-10)

**Purpose:** make the next Stage7 experiment a coherent joint recovery–initial-supply–grid–built-environment–social–natural-hazard-loss typology, not a density-only map or a cluster-label-driven selection exercise. This diagnostic is exploratory; original formal files, clusters and figures remain unchanged.

Starting evidence:
- Author's FEMA audit: commit 65f388f9710566ffa845808bd7b10503de4da608, `nri_eal_redundancy_audit_20261009/`.
- Independently source-checked local extraction: `local_joint_feature_extraction_20261009/`, two matrices (2315 full, 2291 residential), 1081 tract-paired correlations, physical geometry QA and matched 1000-realization B.
- Supplemental new analysis: `physical_feature_gate_20261010/results/FEATURE_GATE_SUMMARY.json`, from exact saved LFS SHA-256 input identities and new correlations. No old cluster labels used to select features.

## Recovery and initial-service choice

- **Proposed main recovery coordinate:** `B_480_hr`, the tract-normalized modelled service deficit integrated over 0–480 h, from the exact same frozen 1000 evaluation realizations, 2pc50/C57_D1/direct-community/M1/G1.
- **Mandatory initial-service coordinate:** `Init_Supply`; retain it separate. 1529/2291 values are zero, so inspect potential leverage of rare nonzero cases, but do not delete the coordinate.
- **Required recovery sensitivity:** replace B by T80, never include both simultaneously. Within same 2291 tracts, B versus T80 r=0.912150 (Spearman 0.929190); B versus Init_Supply r=-0.252442; T80 versus Init_Supply r=-0.108296.
- Raw B skewness is only 0.478, so raw standardized B is a defensible primary interpretation in equivalent complete-service-loss hours; compare log1p B as a preprocessing sensitivity, not automatic replacement. AUC_480 = 1−B/480 and cannot be another independent coordinate.

## Physical built-environment candidates: now empirically distinguishable

Three candidate constructs, actual Pearson r on n=2276 complete polygon-area tracts:

| Pair | Pearson r | Spearman rho |
|---|---:|---:|
| 2019 SCAG land-use entropy vs LARIAC footprint coverage | **−0.1183** | −0.1139 |
| SCAG entropy vs original 2014 all-use pre-1970 age-area share | −0.3096 | −0.3826 |
| LARIAC footprint coverage vs 2014 all-use age share | **0.0572** | −0.0241 |
| Footprint coverage vs log population density | 0.7425 | 0.7211 |
| Footprint coverage vs log building-count density | 0.3562 | 0.3008 |
| 2014 all-use age vs ACS housing-unit age | 0.7802 | 0.7615 |
| 5+ housing-unit share vs footprint coverage | 0.5864 | 0.5587 |

The three-feature built-environment VIF maximum is **1.1185**. Full provisional joint input VIF max is **2.3219** for SOVI+EAL and **2.3434** for SOVI+BuildingValue+ALR. These are independent of previous cluster separability. They support *provisional* distinct physical measures, not a conclusion that survey/geometry uncertainty is solved.

**Preferred provisional physical variables:**
1. `land_use_entropy`: SCAG 2019 historical classified-parcel **land-use mix**, normalized across eleven classes. NOT an all-land entropy measurement where classified coverage is incomplete.
2. `building_footprint_coverage`: LARIAC6 2020 release physical building roof footprint union / tract land area; not population or floor-space density. Also report building-count density as a diagnostic alternative.
3. `all_use2014_pre1970_area_share`: ORIGINAL LARIAC4 2014 all-use valid-age building-footprint area share; not strict2014→2020 transfer, whose median area coverage is only 4.35% of residential tracts. Do not rename the 2014 variable as 2020 age or claim independently verified YearBuilt.

Do not put 5+ residential share or ACS residential age simultaneously into the main model on top of these three. Retain them as *diagnostics/sensitivity alternatives*. Population density describes demographic exposure and belongs outside physical built-environment domain if independently required.

## Urgent quality gates before formal 2291-row final model

**Geometry:** 18 full-domain tracts, including 15 residential members, have Census ALAND vs landmask discrepancy greater than 0.5%; polygon-dependent candidate values are correctly withheld. Resolve individual geometry/water definitions before publishing a full 2291-label model. Do not set these missing values to zero. A scientifically labeled 2276-row complete-case **exploratory** fit is acceptable for diagnosing performance but is not a silent full-domain replacement.

**SCAG coverage:** median classified parcel land coverage is **75.11%** (n=2291). In the landmask-pass group, only **1830/2276** meet 70% classified coverage, **193/2276** meet 85%, **66/2276** meet 90%. A blanket 85% screen would discard over 90% of tracts and is unacceptable as the main cohort. Evaluate entropy sensitivity to plausible missing-area allocation and class mix, including the possibility that missing public ROW behaves differently from mapped land parcels. The primary entropy must be named precisely as **classified-parcel entropy**, with classified coverage reported separately. Do not silently treat missing area as a known land-use type.

**Age:** original2014 median observed valid-age footprint area coverage **95.25%** in residential study tracts. Government building YearBuilt coverage is poor (~4.29% of county records); age missingness is not random by use. Require missing-age sensitivity bounds, time-vintage discussion, and replace/omit age in controlled sensitivity. Compare original2014 age vs ACS 2018–22 residential age, and do not use sparse strict2020 linkage as a main input.

**LARIAC 2020 vintage:** source is cumulative building outlines with much imagery from 2008, not a clean all-2020 survey. State the source-year distribution and limits; do not infer number of floors from building height.

## Risk/social/economic choice

SOVI_SCORE remains mandatory. Do not replace overall all-hazard risk with earthquake-only scores/PGA.

- **Leading interpretation-sensitive candidate D:** separate `SOVI_SCORE`, `log1p(NRI_BUILDVALUE)` and `ALR_NPCTL`. It distinguishes economic stock and normalized multi-hazard expected-loss rate, without mechanically inserting SOVI through FEMA's RISK Community Risk Factor.
- **Compact candidate B:** `SOVI_SCORE` and `EAL_SCORE`. EAL conflates expected loss and exposure, omitting a separate building-stock coordinate. Its direct SOVI correlation is −0.044 and joint built+grid+service VIF remains modest.
- Both FEMA multi-hazard loss metrics are strongly earthquake-dominated locally (98.1563% annual monetized EAL from earthquakes). Do not describe either as balanced natural-hazard diversity or a pure physical hazard occurrence index.
- Additional 20-seed / high-n_init tests show B's original seed instability was largely an initialization artifact; neither B nor D can be chosen on old low-n_init stability alone. The two feature definitions produce scientifically different partitions.

## Next controlled experiment once quality gates are addressed

Construct two identically aligned matrices, D vs B, on full validated 2291 tracts if possible; otherwise publish an explicitly scoped 2276-row provisional sensitivity with 15-missing-row boundary and a plan to restore them. Each contains one recovery input (B_480), mandatory Init_Supply, unchanged four grid features, validated physical-domain indicators (SCAG classified entropy, union footprint, original2014 all-use age), mandatory SOVI; risk/economic set differs by B vs D only. Do not silently include Population Density as an additional full-weight physical-density variable. A separate demographic-exposure sensitivity can add it with a prespecified budget.

Use raw-versus-log recovery sensitivity; k=2..8 plus fixed k5 for comparability, multiple explicit **predeclared domain-weight schemes**, >=20 seeds, n_init>=100 and assess independent-run seed consistency, class size, minimum class, and spatial-block sensitivity/cluster profiles. Do not select feature definitions or domain weights to match old labels or maximize silhouette alone. Compare B-vs-T80 while holding other choices fixed. Do not let risk set B have greater *domain* weight just because it has fewer coordinates.

Only after this model/quality evaluation and author approval should new Stage7 files, maps, figures, and manuscript claims replace originals; record all data hashes, sample membership and exclusion accounting.

Sources and scripts for the gate are committed separately on analysis/stage7-physical-feature-gate-20261010; previous author audit branch and scientific manuscript branch stay unchanged.
