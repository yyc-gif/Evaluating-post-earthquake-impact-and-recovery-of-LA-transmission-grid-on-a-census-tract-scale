# Revised Stage 7 Recommendation

## Current Choice: B

**For manuscript interpretation now: housing age + 5+ housing-unit configuration, with uncertainty-aware cluster profiles.** Keep the original labels and all numerical scientific outputs unchanged. Retain the impervious results as a clearly labeled validation pilot; do not yet insert them as final manuscript measurements. This is more defensible than the earlier provisional A, not because imperviousness lacks a physical interpretation, but because its production-source gate did not pass.

| Candidate | Classification | Pass evidence | Open/fail evidence | Permitted scope |
| --- | --- | --- | --- | --- |
| Existing pre-1970 housing share | READY for development-history description | Same ACS vintage/denominator; all saved ratios reproduced; cluster distributions and replicate uncertainty audited | Housing age does not establish strength or retrofit status; small denominators need flags | Retain descriptive age, no fragility inference |
| 5+ housing-unit share | READY for cluster-level description | 2,291 defined ratios; numerator/denominator/source matches; covariance-aware VRE; <=10 pp and precision diagnostics preserve main contrasts; moderate rather than extreme redundancy | 211 tracts >10 pp; harsh 5-pp screening substantially selects the population; C5 only 34 tracts; some contrasts small | One configuration descriptor, full distributions/MOEs and sensitivity; not individual-tract ranking |
| 10+ housing share | EXCLUDE as an additional indicator | Valid extraction | r=0.956/rho=0.963 with 5+; overlaps housing term in social vulnerability | Diagnostic only |
| One-unit share | EXCLUDE as an additional indicator | Valid extraction | r=-0.943/rho=-0.945 with 5+; composition repeats same axis | Diagnostic only |
| Annual NLCD impervious fraction | CONDITIONAL | Actual numeric extraction; 2,315/2,315 geometry/valid means; exact boundaries/water; independent and repeat QA; distinct descriptive information | Mirror beta/non-production notice, item/catalog version mismatch, no original USGS reference-file verification | Pilot only until authoritative version/source gate closes |
| SCAG land-use entropy | EXCLUDE from this manuscript addition | Physical concept and source candidates documented | Historical release, overlap/STACK semantics, fixed classes and unique-area tract coverage unverified; no valid entropy or incremental-information result | No extraction/admission merely to add another variable |

READY is purpose-specific, not blanket approval for reclustering, seismic modeling, individual estimates or fine-scale causal inference. These are operational admission criteria for this audit, not universal thresholds selected before seeing the data.

## Explicit Gates

1. Matching: exact unique saved GEOIDs; all numerator/denominator inputs verified; undefined denominators left missing. Passed ACS; passed the NLCD **pilot**.
2. Precision: genuine survey covariance or defensible approximation disclosed; mean differences, spread, low-count flags and screening selection examined. Passed for uncertainty-aware aggregate configuration descriptions; **failed** the claim that a universal 5-pp filtered sample preserves all groups.
3. Distinctness: meaningful physical interpretation, no near-compositional duplicate, measured correlations/conditional redundancy. Passed for 5+; numerically promising for imperviousness, without claiming independence from all original variables.
4. Raster methods: single numeric band, correct year/version, actual equal-area CRS, explicit water/NoData, exact boundary weighting, complete valid area and repeat/independent QA. Extraction checks passed on the retained mirror snapshot.
5. Production provenance: authoritative original release/build verified and archived, source restrictions addressed, no misleading collection label. **Open for NLCD**. Close it using the reference path and change audit described in `NLCD_EXTRACTION_AND_VERIFICATION.md`.
6. Parcel entropy: authoritative compatible historical geometry, non-overlapping areas, documented fixed categories/unknown/mixed-use treatment, actual coverage and additional value. **Not passed for SCAG**. The earlier v2019.1 service has 2,406,373 LA records but record count is not coverage; 23.87% carry forward LU16 and 336,496 have STACK >1. Current 2024 geometry is not an automatic substitute for ACS-2022 context. [Historical SCAG metadata](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0), [current LA service](https://maps.scag.ca.gov/scaggis/rest/services/LDX/Existinglanduse_poly_LA/MapServer).

## Alternatives and Weight

- **A:** scientifically promising once the NLCD production gate closes. Adds residential configuration and constructed-surface intensity to historical development; no SCAG addition without separate evidence. At present it is not fully justified as a final manuscript data choice.
- **B:** recommended now. Configuration complements rather than replaces age, while limiting redundant housing descriptors. It is supported by actual matched data and uncertainty checks.
- **C:** unnecessarily discards a validated descriptive source, but remains preferable to inserting unverified impervious/entropy values or treating configuration as precise for every tract.

These are **description-only** options. None changes the existing eleven-feature distance metric or its mathematical weights. Descriptive emphasis may shift, so discuss domains transparently. Adding two configuration coordinates or promoting descriptions into new standardized clustering coordinates would implicitly reweight physical form and requires a separate model-design decision, not this audit.

Completed: original-feature audit refresh; ACS covariance-aware extraction/uncertainty; all specified screening/weighting/composition checks; numeric NLCD pilot; geometry/water/boundary/repeat QA; effect-size/correlation/conditional-information tables. Open: authoritative NLCD reference/build validation and mapping-error characterization; compatible SCAG geometry/entropy if later pursued. Existing cluster assignments are held unchanged for this task, **not declared scientifically final**.
