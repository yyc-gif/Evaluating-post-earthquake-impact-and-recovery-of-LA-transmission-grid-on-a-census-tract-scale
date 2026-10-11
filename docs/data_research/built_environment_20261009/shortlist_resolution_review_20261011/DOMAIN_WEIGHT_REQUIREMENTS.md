# Domain Weight Requirements

Measurement selection is closed for the preferred comparison: CORE3 comprises EMC2022 occupancy, ACS five-plus residential unit configuration and SCAG2020 classified-parcel diversity. Certified FAR is ineligible; age/height/EPA remain qualified alternatives or supplementary descriptors. Neither correlations nor the fitted partition determine their scientific definitions.

## Exact Remaining Decision

Define the conceptual hierarchy and its total squared-distance budgets before any next weight study:

1. Do coverage, residential configuration and classified land-use diversity share a single physical-domain budget, or are they three explicitly weighted physical constructs? The recommended starting hierarchy is one physical parent with three named subconstructs, avoiding an automatic gain in physical weight from adding columns.
2. Do monetary building stock and normalized multi-hazard loss propensity share one exposure/loss parent, or become separate stock and loss domains? They remain separate measurements in either hierarchy. Equal weights over six parents would change their joint representation; that would be a normative modeling choice, not an algebraic correction.
3. What total budgets represent recovery/initial service, grid dependency and mandatory SOVI relative to the physical and economic/loss components? Equal historical 20% budgets are not established by feature admission.
4. If an optional hardening or vertical-form extension is later selected, which existing budget supplies its weight? Adding a column must not silently grant a new domain additional total influence.

There is no evidence here that mathematically identifies a unique optimal scientific weight. Recommended hierarchy and numerical weight authorization are distinct. Any subsequent sensitivity must hold CORE3, the nonphysical definitions and common GEOIDs fixed, preregister a small substantive budget comparison, and not search for attractive groups or old-label retention.

## Weights Actually Used Here

For a domain with budget w and q standardized coordinates, each squared-distance coordinate weight is w/q. The transformed coordinate is z * sqrt(w/q). Euclidean distances then have the intended domain budget; scaling by w/q instead would square the intended coefficient.

| Domain | Coordinates | Benchmark total | Per coordinate |
| --- | --- | --- | --- |
| Recovery/service | B_480_hr, Init_Supply | 0.20 | 0.10 |
| Grid dependence | Grid_Degree, Grid_Impact, Grid_Betweenness, Redundancy_HHI | 0.20 | 0.05 |
| Physical CORE2 | EMC, ACS five-plus | 0.20 | 0.10 |
| Physical CORE3 and three-coordinate substitutes | EMC/coverage, ACS configuration, SCAG entropy | 0.20 | 0.0666666667 |
| Physical four-coordinate age/hardening/height extensions | Core physical variables plus extension | 0.20 | 0.05 |
| Social | SOVI_SCORE | 0.20 | 0.20 |
| Monetary stock/loss propensity | log1p(BUILDVALUE), ALR_NPCTL | 0.20 | 0.10 |

Only one physical row applies to each model. Adding the third physical measurement reduces each existing physical coordinate from 0.10 to 0.0666666667, a one-third reduction. Adding the fourth reduces 0.0666666667 to 0.05, a one-quarter reduction. The model comparisons therefore include both a new coordinate and an explicit within-domain redistribution; they are not pure feature effects at fixed coordinate weights.

`DOMAIN_COORDINATE_CONTRIBUTIONS.csv` separates specified coefficients from observed between-class sums of squares. The latter describe the fitted separation and cannot be interpreted as causal contributions, a measurement quality score, or a chosen domain budget. No second weight scheme, k sweep or weight optimization was performed. Formal Stage7 weights and results remain unchanged.
