# Stage 7 social-vulnerability harmonization decision (before code change)

The current official CDC/ATSDR 2022 California tract CSV was downloaded from
`https://svi.cdc.gov/Documents/Data/2022/csv/states/California.csv` on
2026-09-26 UTC. Its SHA-256 is
`9dacb6fdaef432e9f8d81a1083a6db44b98e8ab1d3c1bf68d7aadd62b9f0578a`;
it is byte-identical to `Data/California.csv`. In the fixed 2,315-tract domain,
24 official `RPL_THEMES` values are unavailable: 17 zero-population tracts and
7 positive-population tracts with unavailable underlying fields. No values
will be imputed and the frozen Q1–Q4 assignments will not change. CDC 2022
cannot provide complete 2,315-tract coverage without imputation.

## Proposed patch diff, before execution

- Keep CDC `E_TOTPOP / AREA_SQMI` solely as the existing population-density
  source. Stop using CDC `RPL_THEME1`–`RPL_THEME4` as the Stage 7 social feature.
- Load `SOVI_SCORE` by tract FIPS from
  `Data/LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv`, the complete FEMA
  NRI v1.19 score (March 2023 release, derived from CDC/ATSDR SVI 2020)
  already used by formal Q1–Q4 and Q4 targeting. Require one
  finite score for every study tract; do not fill missing scores.
- Replace local-derived `SVI_Composite = mean(RPL_THEME1..4)` with
  `SOVI_SCORE` in the PCA/K-means feature list, hotspot vulnerability component,
  and Stage 7 exported table. `SVI_Composite` will not be represented as
  official CDC overall SVI.
- Preserve frozen Stage 1–6 inputs and create a separate Stage 7-only output
  directory. No Monte Carlo damage, schedules, GA, or restoration trajectory
  will be recomputed.

## Expected affected outputs

Stage 7 tract feature table, PCA loadings/scores/scree, K-means diagnostics,
cluster assignments/profiles/map, hotspot rankings/map, and any Stage 7 plots
that read those outputs. Stage 1–6 outputs, frozen trajectories, Q1–Q4 groups,
and the Q4-targeted sequence are unchanged.

## Stage 7-only execution result

The rerun completed with 2,292 tracts in
`Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/`.
`SOVI_SCORE` itself covers all 2,315 tracts. The remaining 23 omissions have
an unavailable ACS pre-1970 housing ratio (zero denominator or unmatched
housing information), documented in `stage7_housing_excluded_tracts.csv`.
These were excluded only from the multivariate Stage 7 typology; no housing
values were imputed. The previous Stage 7 outputs are preserved.

This is a code/data decision record, not a manuscript edit.
