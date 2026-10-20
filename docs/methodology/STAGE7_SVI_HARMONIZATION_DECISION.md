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

The initial rerun had 2,292 tracts, but a source-level follow-up found that
description incomplete. Every tract has a retained ACS 2022 B25034 record.
Exactly 23 have **zero total housing units**, so their pre-1970 housing
*ratio* is mathematically undefined (0/0), rather than a missing ACS row.
Seven of these have positive CDC population and 100% of those residents in
group quarters. One additional tract has 15 housing units but zero formal
population. The 2020-based formal population and CDC 2022 `E_TOTPOP` differ
for some tracts; both values are retained rather than silently interchanged.

The corrected Stage 7-only rerun uses a clearly defined residential
typology domain: positive formal population and positive housing-unit count.
It has 2,291 tracts, the same count as July Stage 7. July excluded the same
24 tracts earlier in its CDC-SVI loading step; that exclusion incidentally
removed all 23 undefined housing ratios. The revised run does not rely on
CDC SVI availability to define this domain. `SOVI_SCORE` and frozen service
metrics cover **all 2,315 tracts** in
`stage7_full_domain_tract_status.csv`, with an explicit status for each tract.
The 24 outside the residential typology are documented in
`stage7_typology_noneligible_tracts.csv`: 23 zero-housing tracts and one
zero-population tract. No housing ratio was imputed or set to zero, and the
23 group-quarters/nonresidential tracts are not represented as ordinary
residential built-environment clusters.
The seven positive-CDC-population group-quarters tracts still carry 16,932
formal mapped residents and formal 2pc50 T80 values of 40.41–54.68 hours.
They remain in the full-domain service and distributional calculations and
in the explicit status table; only the residential-housing PCA/K-means
classification is inapplicable to them.

Only Stage 7 PCA, K-means, cluster profiles, and hotspot ranks were
recomputed. The previous Stage 7 outputs remain in Git history; Stage 1–6,
formal service trajectories, fixed Q1–Q4 groups, and Q4 targeting did not
change.
The exact Stage 7-only rerun entry is
`python run_stage7_sovi_harmonization.py --refresh-existing-stage7-only`;
refreshing an existing result requires that explicit flag.

The protected July worktree at `182686868cffe962739804f6bc0ccecaed73d601`
was read without modification: its `stage7_svi_excluded_tracts.csv` has 24
rows and its final Stage 7 cluster table has 2,291 rows. On the *same* 2,291
tracts and unchanged formal T80, replacing the old CDC-theme mean with FEMA
`SOVI_SCORE` changes the descriptive typology: adjusted Rand index between
old and harmonized cluster assignments is 0.743, and six of the previous ten
highlighted hotspots remain in the new top ten. This is a substantive
Stage 7 result change, not a relabeling; figures and claims that use the old
clusters/hotspots must not be presented as harmonized output.
The existing Revised Suite Stage 7 figure panels were made before this
harmonization; its README now marks them stale. The suite builder has been
pointed at the harmonized Stage 7 tables for its next plotting-only refresh.

This is a code/data decision record, not a manuscript edit.
