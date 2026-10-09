# Built-Environment Feature Redundancy

Audit: 2026-10-09; latest verified HEAD `b1030f839d522fed4af21e424472e3f8b076797b`. The audited scientific inputs are unchanged from the initial preservation snapshot at `73ef343f21e998eb9c9ccf7797d1aa0119d15c04`. Analysis uses the 2,291 saved residential rows for `2pc50`, not an alternative clustering run or a four-scenario average.

## Current Eleven Features

The actual matrix is established jointly from `src/la_grid/core/C257H_Project_Main.py` (feature selection around lines 5641-5652, transforms around 5686-5717 and fit around 6025-6073) and the saved harmonized labels/PCA loading names. Only Pop_Density and NRI_BUILDVALUE receive log1p before standardization. K-means fits all standardized coordinates; PCA is diagnostic and does not remove correlated dimensions from that distance.

| Feature | Primary construct | Interpretation boundary |
| --- | --- | --- |
| T80 | Recovery outcome | Simulation-derived time to service threshold; not pre-event urban form |
| Init_Supply | Initial event service outcome | Scenario-dependent service level; not an intrinsic building characteristic |
| Grid_Degree | Network topology | Tract dependency-weighted station degree; not local building or street density |
| Grid_Impact | Network topology | Dependency-weighted station impact metric; not earthquake building damage |
| Grid_Betweenness | Network topology | Dependency-weighted graph centrality; shares structural information with degree |
| Redundancy_HHI | Mapping concentration | Sum of squared normalized station-dependency shares; higher values mean more concentration, not measured MW/capacity or a guaranteed supply-redundancy count |
| Pre_1970_Ratio | Descriptive built stock | Share of housing units built before 1970; age/development history, not a calibrated fragility function |
| Pop_Density | Urban-demographic intensity | Persons per area; partly urban context but not impervious cover or physical building volume |
| NRI_RISK_SCORE | Composite natural-hazard/community risk | Hazard-loss, social vulnerability and resilience information; not a pure physical built-environment variable |
| NRI_BUILDVALUE | Economic asset quantity | Aggregate building dollar value; not morphology, construction type, seismic capacity or observed electric demand |
| SOVI_SCORE | Social vulnerability | FEMA v1.19 national social-vulnerability percentile based on CDC/ATSDR SVI; not a building-form index |

Thus the matrix contains two event outcomes, four network/mapping variables, one direct housing-age descriptor, one urban-demographic density measure, one composite hazard/community-risk score, one economic asset quantity and one social composite. It should not be described as eleven independent physical built-environment dimensions.

## Why the NRI Fields Need Distinct Labels

The local input has `NRI_VER=Mar-23`. Its matching **FEMA March 2023 technical documentation**, sections 3.1-3.2 and 4.1-4.3, describes risk value as Expected Annual Loss multiplied by a Community Risk Factor derived from social vulnerability and community resilience. EAL itself includes exposure, annualized hazard frequency and historic loss ratios across natural hazards. RISK_SCORE is a national relative percentile of the risk value, not earthquake probability, PGA or a direct multiplication of displayed percentile scores. Including it alongside SOVI_SCORE introduces some social information twice even if the empirical correlation is modest. The current online FEMA technical PDF has subsequently changed; it is not silently substituted for the frozen Mar-23 release. [FEMA-authored March 2023 documentation preserved by Ohio EMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf), printed pages 3-1 to 4-5 (PDF pages 39-50).

The same release's exposure documentation identifies building values from Hazus 6.0, with 2022 valuations of the 2020 Census inventory. `BUILDVALUE` is the total building-dollar quantity, not the hazard-specific building loss estimate; economic asset stock and exposure-scaled consequences are different from physical form. The citation establishes its economic provenance, not permission to introduce Hazus building-loss estimates here. It cannot resolve footprint, apartment configuration, height, material, condition, seismic resistance or demand. Log-transforming it reduces skew but does not change that meaning. [Same historical FEMA documentation, section 5.3.2, printed page 5-9 / PDF page 68](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf).

CDC/ATSDR SVI includes housing with **10+ units**, mobile homes, crowding and no-vehicle households in its housing/transportation theme. A new 5+ unit share is not identical to SOVI_SCORE, but partially reintroduces one of its component constructs; the years also differ. The observed pairwise correlation with the final composite does not eliminate this conceptual duplication. [CDC/ATSDR source-variable comparison, 2020 column](https://atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html).

## Actual Correlations

Pearson uses the actual clustering transforms, before standardization (positive affine standardization does not change r). Spearman uses ranked values; log1p does not change rank ordering. Every listed pair has n=2,291, with no imputation. Full raw and transformed pairwise tables are retained in `pilot/FEATURE_PAIRWISE_CORRELATIONS.csv`. These are descriptive associations of spatially dependent tracts, not independence tests or causal findings.

| Existing pair | Pearson r in transformed space | Spearman rho |
| --- | ---: | ---: |
| NRI_RISK_SCORE - log1p(NRI_BUILDVALUE) | 0.611 | 0.624 |
| log1p(Pop_Density) - log1p(NRI_BUILDVALUE) | -0.498 | -0.573 |
| Grid_Degree - Grid_Betweenness | 0.469 | 0.579 |
| log1p(Pop_Density) - SOVI_SCORE | 0.483 | 0.511 |
| NRI_RISK_SCORE - SOVI_SCORE | 0.380 | 0.353 |
| T80 - Grid_Degree | -0.387 | -0.447 |

No existing pair exceeds abs(r)=0.8 in Pearson or Spearman. That screening threshold is not a universal redundancy criterion: NRI's embedded social component, related graph metrics and simulation-derived outcomes can still duplicate constructs or be dependent by design. The stronger rank association between T80 and Grid_Impact (rho=0.563, Pearson r=0.172) also shows why a Pearson-only screen is insufficient.

| New 5+ housing-unit share versus existing feature | Pearson r | Spearman rho |
| --- | ---: | ---: |
| T80 | 0.178 | 0.221 |
| Init_Supply | 0.013 | -0.072 |
| Grid_Degree | -0.102 | -0.058 |
| Grid_Impact | 0.155 | 0.250 |
| Grid_Betweenness | 0.185 | 0.159 |
| Redundancy_HHI | -0.097 | -0.099 |
| Pre_1970_Ratio | -0.449 | -0.468 |
| log1p(Pop_Density) | 0.493 | 0.546 |
| NRI_RISK_SCORE | 0.206 | 0.229 |
| log1p(NRI_BUILDVALUE) | -0.037 | -0.051 |
| SOVI_SCORE | 0.200 | 0.285 |

Configuration adds information beyond housing age, but age, configuration and population density are not orthogonal. The weak relationship with building value is particularly important: a dollar quantity is not an adequate substitute for this physical descriptor.

The pilot uncertainty sensitivity excludes observations only for a **separate descriptive check**, not the scientific results. Requiring at least 100 housing units gives n=2,280: r(age)=-0.455 and r(log-density)=0.534. Requiring share MOE <=0.20 gives n=2,264: r(age)=-0.456 and r(log-density)=0.538. The configuration/density relationship persists and strengthens slightly; no arbitrary cutoff is adopted for clustering. See `pilot/B25024_RELIABILITY_SENSITIVITY.csv`.

## Existing-Label Description, Not Validation

| Saved cluster | n | Mean 5+ share | Median 5+ share |
| --- | ---: | ---: | ---: |
| 1 | 910 | 40.25% | 33.85% |
| 2 | 183 | 47.35% | 42.86% |
| 3 | 619 | 27.56% | 21.68% |
| 4 | 545 | 25.82% | 14.43% |
| 5 | 34 | 31.86% | 32.67% |

These tract-unweighted profiles use untouched existing labels. Wide within-cluster ranges overlap; this is a useful extra description, not proof that clusters are natural building-form classes, statistically distinct populations or more valid than before. Cluster 5 is small. Means are not pooled housing-unit shares; pooled counts and their MOEs would require a separately defined aggregation.

## Candidate Redundancy and Weighting

- Impervious fraction measures surface construction rather than people or housing age. Its associations remain unmeasured because no numeric raster was extracted; do not label it independent on intuition alone.
- SCAG land-use entropy measures area composition; EPA entropy measures household/job activity. They address the same broad mix domain by different measurements and should be alternatives, not simultaneously counted as two independent physical dimensions.
- Residential/commercial/industrial shares are compositional. Do not add all shares plus their entropy as unrelated coordinates; the shares sum to one and entropy is derived from them. A future model must choose an interpretable representation and consider compositional geometry/zero handling.
- Intersection density could add street grain but overlaps road-access and population/urbanization context. Occupancy describes utilization and shares social/housing context; neither has a demonstrated incremental benefit here.
- PCA does not automatically fix construct over-weighting, particularly because current K-means fits the full standardized matrix. Correlation pruning alone also cannot turn the composite NRI risk score into physical urban form.

Retain existing results. Use these findings to predefine blocks and alternative-model questions before any separately authorized rerun, rather than optimizing variable selection to a desired silhouette or hotspot map.
