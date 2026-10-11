# Assessor 2022 floor-area semantics and identity audit

All 2,413,687 assigned assessment records reuse the previously acquired single RollYear2022 cache; 2,413,687 AINs are unique. Only nonpersonal assessment attributes are used. Same-coordinate groups with positive main area: 20,789; repeated nonidentity attributes flag 291,567 records. Multi-building-data-line records: 157,429; condo-coded records: 315,122.

Per-tract diagnostics retain actual positive Main Square Footage, shared-point/condo/multiline/repeated-attribute area fractions, and the explicitly restricted single-line, noncondo, nonshared-point area subset. The amount that a naive coordinate collapse would remove is reported as a warning diagnostic, not a valid lower bound or deduplication method. No assessment records were deleted from the existing measurement.

Same-year parcel geometry verification selected the 20 largest shared condo-coordinate groups and 20 other shared condo groups with fixed seed20261010. This is a bounded identity probe, not a representative countywide validation sample. 40 groups were checked; 40 groups have fewer unique normalized cadastral geometries than returned AIN identities. Returned assessment identities: 8,430; returned parcel rows: 8,430; roll years: ['2022']. A shared cadastral footprint does not identify a shared physical building or establish whether unit/common areas are duplicated. Missing returned AINs remain visible in the sample table.

The inspected official dictionary labels SQFTmain as Main Square Footage and totBuildingDataLines as building-data-line count. It does not certify the floor-area inclusion/exclusion convention, independently identify every structure, or resolve condo ownership/common-area accounting. AIN identifies an assessment parcel/account, not necessarily one physical building. The public HD22 housing layer lacks certified all-use gross-floor-area fields; the inspected XREF and 2022 parcel layer provide assessment/cadastral identities rather than the missing structure-area inventory. Targeted public catalog searches are retained; absence from these inspected endpoints is not proof that no appropriate dataset exists elsewhere.

Remaining required evidence:
- 2022 structure/building-line identifiers and areas
- certified gross-floor-area inclusion/exclusion convention
- unit versus shared/common building-area accounting
- complete government/exempt stock coverage

Disposition: PENDING_DATA. `assessor2022_gross_floor_area_ratio` remains null on all 2,315 tracts. Existing Main Square Footage/land stays DESCRIPTIVE_ONLY. The restricted subset is diagnostic, not countywide FAR. Shared coordinates, identical area/age attributes or parcel geometries cannot justify building-level deduplication. No floor counts are inferred from heights and no missing exempt/government values are replaced.
