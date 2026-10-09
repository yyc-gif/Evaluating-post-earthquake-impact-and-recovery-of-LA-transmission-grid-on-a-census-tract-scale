# Stage 7 Built-Environment Recommendation

Date: 2026-10-09; latest verified HEAD `b1030f839d522fed4af21e424472e3f8b076797b`. Scientific inputs are unchanged from initial snapshot `73ef343f21e998eb9c9ccf7797d1aa0119d15c04`.

## Decision: A Is Strongest for the Current Manuscript

**Keep housing age as a descriptive development-history variable and use additional built-environment indicators to describe the existing clusters.** Do not reinterpret pre-1970 units as calibrated fragility, and do not automatically replace the saved typology. The audit demonstrates one usable new descriptor, identifies a strong second source with remaining extraction work, and finds meaningful land-use provenance/geometry limitations. It does not supply evidence that a replacement clustering is scientifically superior.

The current matrix mixes recovery outcomes, grid/mapping descriptors, social vulnerability, economic stock and composite natural-hazard risk. The manuscript should call this a **multidimensional recovery/community typology**, not a built-environment-only classification. NRI_RISK_SCORE is not a substitute for urban form; NRI_BUILDVALUE is not seismic capacity or building morphology. Their presence in the frozen model is disclosed, not silently corrected in this audit.

## Recommended Indicators: Two, With a Conditional Third

1. **Housing units in structures with 5+ units / total housing units (ACS 2022 B25024).** Ready for uncertainty-aware descriptive reporting: 2,291/2,291 residential tracts have a defined value, and totals agree with existing B25034. Label it residential configuration, not apartment-building counts, height or vulnerability. Retain uncertainty flags, especially the 27 tracts with share MOE above 20 percentage points.
2. **Area-weighted mean impervious fraction, Annual NLCD 2022, pinned Collection 1.2.** A complementary measure of constructed-surface intensity, including roads and parking. It is pending actual GeoTIFF acquisition, encoding/water-mask decisions and 2,315-tract coverage QA. Do not place invented values or a claim of complete coverage in the manuscript now. [Official USGS product documentation](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-land-cover-annual-nlcd-collection-1-fractional-impervious).
3. **Optional: SCAG area-based existing-land-use entropy.** Admit only after obtaining the intended historical release, resolving stacked/overlapping parcel footprints, fixing classes and denominators, and publishing per-tract classified-area coverage. The inspected v2019.1 source includes substantial LU16 carry-forward and a STACK dictionary/data discrepancy. EPA v3 activity mix is a clearly labeled fallback after an appropriate geographic/count crosswalk, not an extra fourth indicator. [SCAG historical service metadata](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0), [EPA technical guide](https://www.epa.gov/system/files/documents/2023-10/epa_sld_3.0_technicaldocumentationuserguide_may2021_0.pdf).

Do not prioritize intersection density or occupancy without showing that they add a distinct descriptive question not already represented by road access, population density or the social/housing composite.

## Options and Implicit Weight

| Option | Interpretability | Effect on clustering weight | Assessment |
| --- | --- | --- | --- |
| A: keep age; additional variables only describe saved clusters | Separates original model construction from new physical interpretation; retains development history | No change to current distances, PCA, labels or hotspot ranks | Recommended now |
| B: replace age with broader form variables | Changes the meaning of the typology and removes historical-development information; age is not empirically interchangeable with configuration | One-for-one replacement preserves coordinate count but changes construct; replacing one age coordinate with two form coordinates raises that domain's nominal weight | Not justified by this audit alone |
| C: add selected indicators in an exploratory alternative model | Can test whether a broader urban-form block changes interpretation, but is a distinct model rather than a cosmetic update | Adding standardized coordinates gives their domain additional influence unless block weighting is explicitly redesigned | Suitable only as a future, separately authorized sensitivity study |

Current standardization gives every nonconstant coordinate unit marginal variance. With 11 coordinates, age occupies nominally 1/11 (9.1%) of coordinates; including population density as urban context gives 2/11 (18.2%). Adding configuration and imperviousness while keeping age produces 13 coordinates: direct built-environment descriptors become 3/13 (23.1%), or 4/13 (30.8%) including density. Adding land-use entropy as well gives 4/14 (28.6%), or 5/14 (35.7%) including density. These are **coordinate-count diagnostics**, not measured causal importance, PCA explained variance or guaranteed shares of every pairwise distance. Correlation can reinforce the same urbanization direction rather than providing independent information.

A future C should prespecify domain membership and, if warranted, a block-level distance such as a fixed block budget divided across its coordinates. That is a scientific modeling decision, not an automatic helper refactor. Compare interpretable profiles, stability and geographic behavior, not merely the maximum silhouette. Do not include both EPA and SCAG mix, or three composition shares plus their own entropy, as separate independent form variables.

## Admission Gates Before Any Model Revision

1. Freeze the target population: keep the 2,315 full-domain accounting and 2,291 residential-typology subset explicit. Do not assign residential housing form to zero-housing tracts by filling missing shares with zero.
2. Preserve provenance: source observation year, release/version, exact fields/formulas, boundary vintage, original URLs, download hash and code/class mapping.
3. Publish actual valid-indicator coverage, including raster valid-area and parcel classified-area denominators; source extent alone is insufficient.
4. Declare ACS uncertainty handling and zero-activity/one-category entropy conventions before comparing clusters. Keep low-denominator sensitivities separate from the frozen population.
5. Measure redundancy jointly on the same IDs after remaining indicators exist. Do not invent correlations for NLCD or SCAG from expected urban patterns.
6. For a future alternative model, distinguish pre-event descriptors from event outcomes; explicitly decide whether composite NRI risk and aggregate building value belong in that question. Keeping both risk and SOVI can partly duplicate social context, and removing either would require a separately reviewed model revision.
7. Obtain separate approval before any PCA/K-means, hotspot-ranking, restoration or figure rerun. A good data source is not authorization to alter results.

## Suggested Manuscript Interpretation

The existing recovery/community typology can be supplemented by housing-unit configuration and, after spatial QA, constructed-surface intensity. These variables describe pre-event urban development and land cover; they are not additional estimates of earthquake damage, loss, seismic resistance or electricity demand. The housing-age term describes the historical residential stock rather than a fragility model. Land-use diversity remains conditional on geographically and temporally compatible classifications.

The actual pilot confirms complete **defined B25024 coverage only within the 2,291 residential tracts**, not complete coverage of every proposed indicator. Existing-label configuration profiles are informative but overlap substantially and do not validate natural cluster boundaries.

## Work Completed and Left Open

Completed: current eleven-feature audit; official definition/vintage review; ACS extraction and approximate MOE QA; correlations in actual feature transforms; uncertainty sensitivity; unchanged-label profiles; EPA source retrieval and relationship feasibility; SCAG source/category/QA distributions; source manifests and preservation checks.

Open: NLCD numeric extraction and fractional zonal means; verified SCAG historical geometry/class mapping and overlays; a genuine EPA 2019-to-2020 count-allocation crosswalk; measured correlations involving those uncomputed indicators. No scientific rerun is part of this deliverable.
