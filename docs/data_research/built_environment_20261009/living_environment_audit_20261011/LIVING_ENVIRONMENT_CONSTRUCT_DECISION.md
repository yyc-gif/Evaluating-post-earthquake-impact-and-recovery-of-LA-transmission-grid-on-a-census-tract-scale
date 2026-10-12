# Living-environment construct decision

## Decision

Housing5+ is a defensible residential-configuration measurement. Electric principal heating is a defensible but use-specific measurement best retained as a sensitivity coordinate at present. Published canopy can describe ecological urban greenness conditionally; it does not yet establish resident shade exposure. All Parks remains conditional because the spatial allocation statistic is not verified. Good Parks is descriptive only. None is promoted into Stage7, and no new formal feature set is selected.

| candidate                     | measurement_status   | recommended_role                                                              | construct                                                                                            | qualification                                                                                                               |
|:------------------------------|:---------------------|:------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------|
| housing_5plus_share           | ADMIT                | eligible primary coordinate for residential configuration                     | all housing units; 5+ structure units                                                                | verified existing80-VRE method; related to SOVI10+units and population density; not building count or all-use physical form |
| electric_heating_share        | ADMIT                | sensitivity coordinate for principal residential heating dependence           | occupied housing units using electricity as main heating fuel                                        | strong sampling uncertainty; specific use of electricity, not general dependence; moderate housing overlap                  |
| canopy_2022_fraction          | CONDITIONAL          | ecological canopy sensitivity/description; no unqualified primary replacement | published urban-canopy analysis area, mostly close to tract land; exact partial-area rule unresolved | whole-area greenness not resident shade; residual land geometry differences and partial urban support                       |
| parks_all_published_fraction  | CONDITIONAL          | published descriptive proximity until spatial apportionment verified          | published 2020 population denominator; numerator spatial apportionment unresolved                    | cannot verify resident weighting versus tract overlay; geometric half-mile is not pedestrian network                        |
| parks_good_published_fraction | DESCRIPTIVE_ONLY     | separate published condition-qualified description                            | same unresolved proximity allocation plus park-condition filter                                      | rating criteria, assessor objectivity and vintage not established; not an objective primary living-environment coordinate   |

Two verified measurements are preferable to forcing three. A subsequent author-approved model could examine housing configuration and specific electric-heating dependence as distinct constructs, with their survey uncertainty and shared-source overlap disclosed. This audit does not prescribe their joint weights or require using both. Canopy and parks should not automatically replace the archived land-use or built-surface coordinates: they measure greenness and proximity, not those physical constructs. The current CORE3/W1 partition has no default approval status.

## Actual reference distributions

All five published indicators have2,287/2,287 values on the archived reference. Percent and percentage-point units below; exact fractions are in the CSV. Statistics are unweighted across tracts, not across residents. Published parks endpoint roundoff is retained.

| candidate                                  |   minimum |     P10 |     P25 |   median |      P75 |      P90 |   maximum |    mean |   standard_deviation |   zero_fraction |
|:-------------------------------------------|----------:|--------:|--------:|---------:|---------:|---------:|----------:|--------:|---------------------:|----------------:|
| 2022 published urban tree canopy           |    0.5900 |  5.4942 |  7.4462 |  10.4696 |  15.2328 |  21.4667 |   46.2387 | 12.4524 |               7.3293 |          0.0000 |
| 2022 published Access to All Parks         |    0.0000 | 30.5239 | 70.7137 |  97.3618 | 100.0000 | 100.0000 |  100.0000 | 80.4965 |              28.8480 |          2.7110 |
| 2022 published Access to Good Parks        |    0.0000 |  0.0000 |  0.0000 |  19.6138 |  78.4909 |  99.9105 |  100.0000 | 37.3105 |              39.8610 |         36.2921 |
| ACS 2022 electric principal heating share  |    0.0000 | 13.2654 | 18.6047 |  26.0914 |  35.0632 |  45.6687 |  100.0000 | 28.1602 |              13.4087 |          0.1312 |
| ACS 2022 units in structures with 5+ units |    0.0000 |  1.3935 |  8.6910 |  25.4593 |  55.0344 |  81.2626 |  100.0000 | 33.8219 |              29.3792 |          6.6900 |

All Parks has a ceiling-heavy distribution (median 97.36%, P75100%); Good Parks has36.29% exact zeros. These describe the published measurements, not evidence that almost all residents have equivalent pedestrian access. Tree canopy has no exact zeros on the reference and a right tail. Extreme GEOIDs and their density/population are exported, not removed as inconvenient observations.

## Statistical versus construct redundancy

On identical2,287 GEOIDs, electric heating versus housing5+ has Pearson r=0.6320 and Spearman rho=0.6012. Controlling housing5+, EMC, log1p density and SOVI leaves59.80% of heating variance unexplained (conditional VIF1.67). This permits distinct heating interpretation but is not proof of independent information or a reason to call it general electricity dependence.

Housing5+ correlates with log density at r=0.4971/rho=0.5476 and SOVI at r=0.2008/rho=0.2855. More directly, housing5+ correlates with CDC 2020 EP_MUNIT at r=0.9476/rho=0.9518. Thus the modest aggregate SOVI correlation must not hide nested housing content and shared ACS source dependence. Heating and housing have different denominators and neither is an exact deterministic function of the other.

Canopy correlates negatively with EMC(r=-0.5531), log density(-0.3986) and SOVI(-0.5280). Conditional on the inherited housing/context measurements,56.99% of canopy variance remains. This is ecological overlap, not causal protection from outages or proof of resident shade. Boundary/analysis-support and low-density sensitivity rows preserve the exact subset GEOIDs and N; no subset replaces the main measurements.

Weak All Parks/Good Parks marginal correlations with inherited variables cannot resolve their definition problems. Good access is nested in all access, with r=0.3995, and both share park geometry, denominator and spatial allocation. Condition filtering adds a different, potentially subjective construct. Derived published percent and access_count/denominator are the same quantity, never separate primary inputs. The two canopy area units are conversions of the same canopy class, not independent indicators.

## Precision sensitivity

Electric heating has568/2,287(24.84%) records with MOE90>10 percentage points; housing5+ has211/2,287(9.23%). Median MOEs are8.48 and6.75 points. Both estimates remain in the data. Across the80 corresponding raw variance replicates, heating/housing Pearson values range0.6120-0.6309; that is a sensitivity range, not a confidence interval or independent replication. Boundary cases require the extra official variance rule, so raw replicate ranges do not summarize every source of sampling uncertainty.

Filtering both MOEs to<=5 points would leave only 76 tracts and substantially change the observed relationship (Pearson0.9399, Spearman0.3831). This demonstrates selection sensitivity, not superiority of a filtered model. No such deletion is recommended. Formal survey MOEs do not quantify canopy classification error, uncertain park allocation or shared-source systematic biases.

## Remaining blockers and scope

For canopy, 21 reference tracts have land IoU<0.90 and 22 have source analysis area<99% of source polygon. These are diagnostic flags, not retrospectively optimized acceptance thresholds. The exact canopy zone rule and actual residential location support remain unresolved. For parks, the downloaded population fields and buffer narrative still do not establish population weighting. Good Parks rating lineage/objectivity remains unverified.

No correlation with recovery outcomes, existing labels, silhouette, ARI or class separation was used. Statistical association, common source, conceptual overlap and algebraic duplication are recorded separately. No causal assertion, final clustering choice, weight decision or manuscript claim follows from this audit.
