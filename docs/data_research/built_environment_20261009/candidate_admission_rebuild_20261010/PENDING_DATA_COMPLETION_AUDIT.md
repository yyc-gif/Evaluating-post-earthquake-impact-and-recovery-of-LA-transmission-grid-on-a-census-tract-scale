# Three pending measurements: actual follow-up results

Starting analysis commit: `561283f50f110e0897650857241880d19d904c67`. Output remains on `analysis/stage7-candidate-admission-rebuild-20261010`.

| candidate | disposition | valid_full_2315 | valid_residential_2291 | median_residential_coverage | scope_or_gap |
| --- | --- | --- | --- | --- | --- |
| assessor2022_gross_floor_area_ratio | PENDING_DATA | 0 | 0 | not certified | Cached 2022 unique-AIN records and bounded same-year parcel geometry samples audited. Main Square Footage does not certify gross floor area. Missing structure/building-line area IDs, condo unit/common-area accounting, gross-area inclusion convention and exempt/government coverage. Shared coordinates, parcel geometry or identical attributes do not justify building deduplication. No certified FAR produced. |
| epa_household_job_activity_mix | CONDITIONAL | 2311 | 2287 | 0.999653854482142 | Historical household/job activity, not parcel land use. Actual 2018 SLD donor polygons are overlaid on 2020 tract/water support. Uniform within-donor land allocation estimates counts; boundary/vintage and source errors remain. Missing donor records and outside-target counts are explicitly audited. No source entropy averaging, prefix allocation or uncovered-area renormalization. |
| scag2020_classified_land_entropy | CONDITIONAL | 2311 | 2287 | 0.751271678181665 | Actual 2020 ALU20 parcel geometry and coded domain verified. Same-geometry same-class duplicates collapsed; conflicting classifications and cross-class overlap withheld; nonidentical stacked geometries retained. Classified land only, continuous gap/unknown/conflict/water coverage retained. Temporal alternative, no automatic replacement of 2019.1. |

SCAG2020 and EPA now have actual numeric tract outputs, qualified as CONDITIONAL. Assessor gross FAR remains PENDING_DATA after a completed evidence audit; a raw Main Square Footage sum is not substituted. Admission is not final feature selection. No clustering, weights, formal scientific outputs, manuscript or figures were changed.

The 2,315 full-domain and 2,291 residential GEOID masters retain exact membership and order. Four unresolved target land masks stay null for the new geometry-dependent values. Non-geometric Assessor diagnostics remain available. Read EPA_ACTIVITY_GEOGRAPHIC_CONVERSION.md, SCAG2020_MEASUREMENT_QA.md and ASSESSOR_FLOOR_AREA_AND_DUPLICATE_ATTRIBUTION.md for source-specific qualifications.
