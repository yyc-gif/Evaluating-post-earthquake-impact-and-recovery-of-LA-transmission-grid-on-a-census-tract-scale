# CBM flags and zero semantics
AUTHOR REVIEW - NOT FORMAL STAGE 7

The official dictionary defines:0=provider true zero in the source measure;1=source null updated to zero;2=positive estimate whose percentile is zero;9=other values. -999/null means unavailable, not zero. F=0 is a recorded/model-defined zero in a particular period/support, not proof of zero future hazard. F=9 may include modeled FEMA minimum frequency, not exclusively observed events. No user-generated zero substitution or imputation occurs.

| indicator   | quality_state                         |   tract_count |   resident_population | flag_field_available   |
|:------------|:--------------------------------------|--------------:|----------------------:|:-----------------------|
| NEHD        | POSITIVE_PUBLISHED_ESTIMATE_NO_FLAG   |          2299 |               9066522 | False                  |
| SMOKE       | POSITIVE_PUBLISHED_ESTIMATE_NO_FLAG   |          2299 |               9066522 | False                  |
| BURN        | POSITIVE_PUBLISHED_ESTIMATE_NO_FLAG   |            48 |                174249 | False                  |
| BURN        | ZERO_NO_PUBLISHED_FLAG_UNRESOLVED     |          2251 |               8892273 | False                  |
| CFLD        | POSITIVE_ESTIMATE_WITH_ZERO_RANK      |            17 |                 68639 | True                   |
| CFLD        | PROVIDER_CONFIRMED_RECORD_PERIOD_ZERO |          2207 |               8707881 | True                   |
| CFLD        | PROVIDER_OTHER_VALID_ESTIMATE         |            75 |                290002 | True                   |
| DRGT        | PROVIDER_OTHER_VALID_ESTIMATE         |          2299 |               9066522 | True                   |
| RFLD        | PROVIDER_CONFIRMED_RECORD_PERIOD_ZERO |          1860 |               7337445 | True                   |
| RFLD        | PROVIDER_OTHER_VALID_ESTIMATE         |           439 |               1729077 | True                   |
| HRCN        | SOURCE_NULL_OR_EXCLUDED_SET_ZERO      |          2299 |               9066522 | True                   |
| SWND        | PROVIDER_OTHER_VALID_ESTIMATE         |          2299 |               9066522 | True                   |
| TRND        | POSITIVE_ESTIMATE_WITH_ZERO_RANK      |            13 |                 63705 | True                   |
| TRND        | PROVIDER_CONFIRMED_RECORD_PERIOD_ZERO |          2285 |               8998003 | True                   |
| TRND        | PROVIDER_OTHER_VALID_ESTIMATE         |             1 |                  4814 | True                   |

All 2,299 tracts (9,066,522 frozen residents) have hurricane F=1. The frozen NRI frequency records are null here, and CDC assigns source-null zeros; the flag alone does not distinguish geography exclusion from another missing-source cause. These are not measured hurricane-free observations. This coordinate is locally constant and contributes no local score variance; omitting it changes national calibration but essentially not LA rank order. Its presence alone is not proof the CDC index is invalid.

The more consequential unresolved gate is absence of three published flags: heat/smoke positive estimates cannot be linked to documented processing exceptions, and2,251 burned-area zeros (8,892,273 residents) have no released flag separating actual no-intersection from source-null/excluded states. These are *unresolved zeros*, not a claim that2,251 values are missing. No count of provider structural zeros versus generic missing can be established where F=1 combines them.

CDC documents13 interpolated national heat records but gives no IDs or heat flag in the downloaded table. Their study membership is unknowable from the release. Crosswalk affects all heat values; smoke/burn use polygon intersections, and NRI hurricane/riverine may use minimum annual frequency. `CBM_2299_BY_NINE_INDICATOR_QUALITY.csv` preserves all20,691 tract-indicator records. The wide matrix and per-tract counts identify unresolved processing without silently dropping tracts.

There is no flag-free composite subgroup in this cohort because all hurricane flags are1. Thus flagged-versus-unflagged full-composite comparison is not estimable. Burn-zero/positive subgroup summaries are not missing-versus-observed strata. Source flags are not uncertainty confidence intervals.
