# Independent Stage 7 built-environment re-clustering — 2026-10-09

**Status: exploratory results executed and verified, NOT a replacement for formal Stage 7.**

Starting snapshot: commit 031d2c675f8e7d58035d27448be040b809ced086. Work is isolated to analysis/stage7-pre-event-reclustering-20261009. The main reviewer branch, previous cluster labels, protected scientific results, restoration simulations, and figures are unchanged.

## Corrected research logic

First specify built-environment indicators from construct meaning, time/geographic compatibility, independent data checks and redundancy. Then do clustering. Only after fixing clustering results can one compare recovery outcomes. **Never select input measures for their ability to reproduce old cluster labels.** Old Stage 7 put T80 and Init_Supply in the clustering matrix; including those when inferring how ex-ante community types relate to restoration is circular.

### Built environment — audited residential-physical core

1. **Pre_1970_Ratio**: ACS B25034, share of all housing units built before 1970. Housing stock age, NOT seismic fragility.
2. **housing_5plus_share**: ACS B25024, (006+007+008+009)/001; fraction of all housing units in structures with at least 5 units, NOT a count of buildings, number of floors or their strength.
3. **housing_units_per_km2**: all housing units / (Census tract ALAND in m² / 1e6). Gross tract-land housing-unit density, NOT population density, building footprint, floor area or EPA density per unprotected land area.

This three-input physical housing-stock cluster is called **housing_three_measure**. It is the direct answer to the currently *verified* physical residential form. It does NOT claim to capture the entire built environment.

### Other physical components

- **Impervious fraction** from 2022 Annual NLCD measures artificial surface including roads, rooftops and parking. Numerically extracted in all 2,315 study tracts, but the retained Esri mirror is beta/non-production with unresolved source/build provenance; it is not approved against original USGS authoritative raster. The four-input **housing_plus_impervious_pilot** is conditional **only**. Do not publish its cluster outputs as validated production measurements.
- **Land-use mixture (SCAG)** would be conceptually useful but was not admitted: compatible historical land-use polygons, overlapping/stacked geometries, classification and tract-level valid-area checks remain unresolved. EPA activity entropy is not a drop-in equivalent without crosswalking original employment/housing counts.
- **Street design, accessibility, non-residential form** are further built-environment domains; not all have validated inputs in this snapshot. Do not claim a comprehensive urban-form measurement based on only three housing descriptors.

### Different scientific target: multi-domain pre-event community/grid clustering

The nine-feature **primary_equal_domain** (an internal script label, not a claim that the model is a pure built-environment analysis) includes three housing variables, four pre-event electrical topology features (Grid_Degree, Grid_Impact, Grid_Betweenness, Redundancy_HHI), and social/economic context (SOVI_SCORE, NRI_BUILDVALUE). Its three domains have equal total weight. It is a community/grid typology, NOT a housing-physical type. A parallel equal-per-coordinate analysis and a population-density substitution are explicit sensitivity models. NRI_RISK_SCORE is excluded from the base nine coordinates and evaluated separately both as a tenth input within the social domain and as a separately weighted fourth domain. These changes are not conflated.

**All** re-clustered models hold out T80 and Init_Supply from clustering/k-selection. Those may only be evaluated afterward; causal claims cannot be made by comparing means.

## Independent source QA, not an assertion from old summaries

The independent source_qa.py actually reads retained original Census B25024/B25034 2018–2022 California 80-replicate ZIPs and recomputes point ratios plus covariance-aware SDR 90% MOEs. It verifies archived hashes. Original Census tract ALAND is re-read from the original DBF and compared with the zonal extraction ALAND (2,315 records).

- Reconstructed all **2,291** residential ratios.
- Maximum discrepancies versus archived rows: 5+ ratio **1.11e-16**, 5+ MOE90 **9.71e-17**, housing-age share **1.11e-16**.
- **211** tract MOEs above 10 percentage points; **158** survey boundary-model cases; median 90% MOE **6.7482 percentage points**.
- Maximum Census tract land-area mismatch **0 m²** over 2,315 records.
- Reproducing the previous 11-feature k=5 clustering recovers **all old labels exactly in ARI terms (ARI=1.000)**.
- The source of the NLCD raster itself was **not independently certified against USGS**; matching bytes, computation and the archived manifest are not that certificate.

## Clustering protocol

Use the original 2,291 residential-typology tract universe. Scale all features by StandardScaler; apply log1p to housing_units_per_km2 and NRI_BUILDVALUE when present, avoiding population-density proxy in the primary housing model. Euclidean K-means, random seed 42, k=2–8, choose highest silhouette subject to every group containing >=2% of tracts; n_init=20 for k search and n_init=30 for final. Twelve random 80%-sample refits provide *conditional* algorithmic stability, not model-specification validity. The nine-feature model's domain blocks use total squared-distance weight 1/3 each; check coordinate-equal alternative. PCA is a descriptive diagnostic and not the K-means input compression. Old cluster labels do not enter new feature design, k choice or optimization.

## Results (actual successful GitHub Actions run)

| Model and meaning | k | Silhouette | Median 80% refit ARI |
| --- | ---: | ---: | ---: |
| Housing age + 5+ | 2 | 0.48462 | 0.99474 |
| **Housing age + 5+ + housing unit density** | **2** | **0.42275** | **0.99468** |
| Physical housing + experimental impervious | 3 | 0.38463 | 0.96738 |
| Nine-feature community/grid, domain-equal | 2 | 0.19488 | 0.86541 |
| Same nine features, coordinate-equal | 2 | 0.17580 | 0.97986 |
| Population-density instead of housing-unit density | 2 | 0.20552 | 0.97129 |
| NRI risk added inside social domain | 2 | 0.16273 | 0.98078 |
| NRI risk as separate fourth domain | 2 | 0.20001 | 0.95294 |
| Nine-feature community/grid + experimental impervious | 2 | 0.20429 | 0.98165 |

**Three-feature physically grounded housing types, tract-equal means:**

| Newly calculated label | n | Pre-1970 share | Units in 5+ structures | Units/km² | Held-out mean T80 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 740 | 47.69% | 69.48% | 4008.62 | 45.89 h |
| 2 | 1551 | 69.80% | 16.82% | 1279.89 | 44.37 h |

This is a housing **age, configuration and concentration** difference; no structure fragility inference is made.

**Pilot four-feature (physical plus impervious) types — NOT publication source approved:**

| Pilot label | n | Pre-1970 | Units in 5+ | Units/km² | Impervious cover | Held-out T80 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1336 | 73.13% | 18.88% | 1465.34 | 63.63% | 44.09 h |
| 2 | 701 | 47.19% | 70.74% | 4103.77 | 72.44% | 45.89 h |
| 3 | 254 | 50.29% | 10.61% | 460.85 | 35.80% | 46.10 h |

Physical-three versus physical-four experimental labels ARI **0.6720**. A physically motivated impervious variable changes the partition in a meaningful way, which is why its official provenance cannot be skipped.

**Model-specification risk:** the nine-feature domain-equal versus the *same nine variables* coordinate-equal has ARI **0.02182**, even though both select k=2 and each shows high within-specification refit stability. Nine-feature domain-equal versus physical-three ARI **0.00211**. These are not the same scientific clustering question. The multi-domain silhouette 0.195 is modest. It is not defensible to call that partition frozen or a natural five-class refinement.

Held-out T80 differences are a descriptive scenario-specific observation only; no significance, spatial/Monte Carlo uncertainty, causal relationship, or between-scenario generalization is established. Silhouette values from distinct feature spaces should not be used to choose the preferred **scientific construct**.

## Deliverables and open scientific gates

- Source code: **recluster.py**, **source_qa.py**, and .github/workflows/stage7-pre-event-typology.yml.
- Independently audited source output: **results/SOURCE_QA.json**, **results/SUMMARY.json** (full input hashes, exact feature/block specifications, k/stability/ARI comparisons).
- Per-cluster physical, nine-feature and held-out recovery profiles: **results/MODEL_PROFILES.json**, **results/cluster_profiles_with_heldout_outcomes.csv**.
- Actual new GEOID-to-cluster assignments: **results/new_cluster_assignments.csv** (separate model namespace), k diagnostics, model ARI comparisons, per-model resampling stability files, PCA, ACS screening, and input audit. CSVs require Git LFS to download true bytes.
- Still necessary before *formal* Stage 7 replacement: authoritative original USGS NLCD version and independent raster QA; adequate land-use mix and accessibility geometry if pursuing a comprehensive built-environment construct; propagate ACS sampling uncertainty through new labels; test spatial autocorrelation/outliers and sensitivity to objectively defensible model weights; validate external scenario stability and held-out outcome uncertainty; explicitly choose whether the manuscript examines residential physical urban form or multidimensional community/grid contexts.

**Only a new analysis branch and newly added files were committed.** No existing original 212 protected files, old formal Stage 7 outputs, main figures, GA, or earthquake simulations were altered.
