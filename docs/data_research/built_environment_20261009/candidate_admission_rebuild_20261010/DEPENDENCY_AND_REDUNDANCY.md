# Source and mathematical dependency audit

SCAG2019 raw LU19 + geometry → broad exclusive classes → area fractions → normalized entropy. Fractions and entropy summarize the same composition. Residential/nonresidential classified fractions are complementary; eleven fractions have a unit-sum constraint. They are alternatives or descriptors, not twelve independent inputs.

LARIAC6 CODE/geometry → exact normalized geometry dedup → whole centroid counts and areas → count density, mean/median/IQR/CV. The same raw polygons → clipped union → union coverage. Height feet → positive/nonconflicting meters → valid-height area weighted mean and volume proxy.

Assessor2022 unique AIN + parcel point + positive SQFTmain + actual YearBuilt → observed-main-area age share and valid-age support. EffectiveYearBuilt is a different coordinate. Main area/land has no certified FAR interpretation. Condominium/shared point and building-line issues remain limitations rather than guessed deduplication.

JRC2022 total/NRES surface TIFF → fractional pixel-land intersections → total/NRES land fraction → NRES/total ratio. The ratio and both factors do not add three independent constructs. JRC2018 ANBH is a separate historical height product; it is not multiplied by2022 EMC and relabeled a synchronized measured volume.

ACS B25024 estimate +80 replicates → housing composition ratios/MOEs. B25034 → residential unit-age ratio. Housing configuration fractions share a denominator, and5+ and10+ are nested. Detached+attached=single-unit. These are one measurement family, not seven separate physical constructs.

FEMA exposure + annual event frequency + historic loss ratio → component EAL → total monetary EAL → national EAL_SCORE rank. Component exposure-normalized rates → rate percentile combination → ALR_NPCTL. Community adjustment introduces SOVI/resilience into RISK and ALR_VRA. BUILDVALUE is one underlying economic exposure, not the same construct as expected loss.

## Exact identities and their limits

For the SAME disjoint polygon list and boundary convention: coverage=count_density*mean_area/1e6; volume/land=coverage*area-weighted height. FAR additionally requires actual measured floors, absent here. Our centroid sums are not a disjoint clipped union. The computed centroid sum identity is exact, but union coverage is NOT substituted for it. With incomplete positive-height support the actual identity is centroid_sum_fraction * valid_height_area_fraction * mean_valid_height. See ALGEBRAIC_DEPENDENCY_QA.json for numerical residuals. Median area and IQR are not mean area, so the product identity cannot use them.

## Actual common-sample comparisons

LARIAC union versus JRC2022 total coverage: N=2287, Pearson=0.949244, Spearman=0.930706.
LARIAC height versus historical ANBH: N=2287, Pearson=0.785588, Spearman=0.716169.
Assessor2022 actual-year share versus LARIAC2014 age: N=2286, Pearson=0.941531, Spearman=0.943500.
These compare differently dated/support-defined measurements; correlation does not establish agreement or exchangeability. LARIAC2014 construction-year attributes may share the assessor source lineage with the2022 roll, so their high correlation is not independent validation of construction year. It must not be presented as two independent age observations. Common-sample exclusions are listed by GEOID. Full and residential scopes and source-coverage/multiline strata are included in the CSV, with actual matched N and GEOID-set SHA. Diagnostics never select a feature because it correlates with recovery.

SAME_CONSTRUCT_AND_RISK_VIF.csv reports collinearity under simultaneous diagnostic input sets. It does not admit features, assign weights or imply causation. NONLINEAR_MEASUREMENT_DIAGNOSTICS.csv supplies prespecified log1p pair comparisons. Count/size versus clipped-union differences are retained in BOUNDARY_AND_SEGMENTATION_DIAGNOSTICS.csv. None substitutes for an independent physical-building segmentation census.


Follow-up measurement evidence: PENDING_DATA_COMPLETION_AUDIT.md and the three source-specific QA notes. EPA values are spatially allocated estimates, SCAG2020 is measured classified parcel land, and Assessor gross FAR remains unmeasured. No automatic feature substitution or weight change is adopted.
