# Full cohort retained; incomplete measurements not filled

AUTHOR REVIEW - NOT FORMAL STAGE 7

Full frozen domain2315; positive frozenpopulation2299; excluded zero-population16(exact IDs in EXCLUDED_ZERO_POPULATION_GEOIDS.csv). All eight positive-population zero-housing tracts remain. Full2315P2source descriptors are retained; no service or distributional calculation changes. No CORE3geometry exclusions are inherited.

Complete polygon measurements: PGA2294; wildfire2200; known flood2088; historicalheat2299. Their common complete-case intersection is **2032**, used only for explicitly labeled information diagnostics, NOT a revised clustering cohort. **267** eligible tracts lack at least one complete polygon measurement. All missing fields and GEOIDs are exported. The current complete-case subset cannot silently replace the approved2299cohort.

Land geometry is recomputed for all2315tracts from frozen polygon bytes minus TIGER2020area-water. No geometries disappear. Validity, area partition residuals and source hashes are recorded. Polygon coverage fraction within1e-6of full land is the numerical overlay-completeness criterion, not a hazard threshold. PGA retains the prior documented99%grid-support rule and flags5partialcoastal supports rather than renormalizing them into a complete measurement.

| comparison                                        |    n |   Pearson |   Spearman |   area_positive_point_zero |
|:--------------------------------------------------|-----:|----------:|-----------:|---------------------------:|
| PGA polygon versus centroid                       | 2294 |    0.9981 |     0.9971 |                          0 |
| Wildfire high-area versus centroid classification | 2200 |    0.9309 |     0.7519 |                        206 |
| Flood SFHA-area versus centroid intersection      | 2088 |    0.6301 |     0.2888 |                        400 |

Point/PGA estimates broadly agree with supported areameans but do not restore missing polygon support. On comparable fire records206tracts have positive high-class area while the geometric centroid is outside that class; the corresponding flood count is400. Neither centroid nor Census internalpoint is population geography. Reported populations in high-exposure *tracts* are representation counts, not people located in the exposed polygon. No household/building spatial distributions are fabricated.

Three of the eight special-use tracts have incomplete flood support and two have incompletefireclassification; some overlap. They stay in all source/missingness tables and are not dropped for convenience.
