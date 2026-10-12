"""Transparent source admission and author-facing interpretation; no promotion."""
import fitz
from common import *
from audit_cdc import CODES, EPL


def frame(name):
    return pd.read_csv(lp(OUT/name),dtype={'tract_id':str,'GEOID':str})


def table(d, cols=None):
    return d[cols].to_markdown(index=False,floatfmt='.5g') if cols else d.to_markdown(index=False,floatfmt='.5g')


def main():
    full=frame('FROZEN_P2_AND_COHORT.csv').set_index('tract_id')
    d=full.loc[full.Population.gt(0)]
    cdc=frame('CDC_2024_MATCHED_ORIGINAL_VALUES.csv').set_index('tract_id').reindex(d.index)
    rankqa=json.loads(lp(OUT/'CBM_RANK_RECONSTRUCTION_QA.json').read_text())
    verify=[]
    for label in ['RAW','MAP']:
        service=frame('CDC_'+label+'_LA_QUERY_VALUES.csv').set_index('GEOID').reindex(d.index)
        assert service.index.equals(d.index)
        fields=[c for c in cdc if c in service and (c in ['RPL_CBM','SPL_CBM','RPL_EJI_CBM'] or c in EPL or c.startswith('F_'))]
        errors={c:float((cdc[c]-service[c]).abs().max()) for c in fields}
        assert all(v<1e-12 for v in errors.values())
        verify.append(dict(source=label,complete_study_matches=service.RPL_CBM.notna().sum(),checked_fields=fields,
                           maximum_absolute_error=max(errors.values()),exact_flag_and_rank_agreement=True))
    dump('BULK_RAW_AND_MAP_COMPARISON_QA.json',verify)
    special=d.loc[d.additional_zero_housing_positive_population].join(cdc[['E_TOTPOP','RPL_CBM','E_BURN','E_RFLD']])
    save('SPECIAL_USE_TRACT_SOURCE_QA.csv',special.reset_index())
    high=d.join(cdc[['RPL_CBM','E_NEHD','E_BURN','E_RFLD','F_HRCN']]).nlargest(230,'RPL_CBM')
    save('HIGH_CBM_TRACT_GEOGRAPHY.csv',high.reset_index())
    contribution=frame('CBM_DOMAIN_AND_INDICATOR_CONTRIBUTIONS.csv')
    comps=frame('CBM_P2_SAME_COHORT_ASSOCIATIONS.csv').query("variable_b=='RPL_CBM'")
    nonlinear=frame('CBM_VS_P2_REDUNDANCY_AND_INFORMATION.csv').query("target=='RPL_CBM'").iloc[0]
    physical=frame('CBM_VS_OFFICIAL_PHYSICAL_HAZARDS.csv')
    counts=frame('CBM_FLAGGED_TRACT_AND_POPULATION_COUNTS.csv')
    admission=dict(status='NOT_ADMITTED_PENDING_SOURCE_QUALITY_CLARIFICATION',formal_promotion=False,
        exact_positive_population_cohort=2299,valid_published_ranks=2299,original_cohort_exclusions_only=16,
        direct_demographic_or_asset_adjustment=False,new_Kmeans_fits=0,
        reasons=['F_NEHD, F_SMOKE and F_BURN absent from national and state bulk tables, dictionary and raw service despite flag-setting technical text',
                 '2251 published burned-area zeros cannot be separated into original physical zeros versus null/ranking exclusions from available flags',
                 '13 nationwide heat interpolations have no released tract-ID marker; study membership not identifiable',
                 'Hurricane F=1 source-null/excluded zero for all 2299, not an observed hazard-free state; constant locally, affects national calibration',
                 'LA local summed-score variance strongly dominated by riverine-frequency rank; broad national climate definition is not balanced local hazard information'],
        nonfailure_findings=['Standalone CBM has no direct social/demographic/resilience/building-value adjustment',
                             'National rank formula and all cohort ranks reproducible',
                             'Conditional overlap with seven P2 features low; not rejected for linear duplication',
                             'Local flood association consistent with independently mapped NFHL on its documented complete coverage'],
        recommendation='Retain P2 as existing candidate and CBM/independent hazard maps as contextual descriptors; K unresolved',
        reopening_conditions=['CDC supplies omitted three flags or source-level evidence resolving their zero/null semantics',
                              'Interpolation IDs and drought-unit wording clarified; burned-area source archive and used period already distinguished',
                              'Author explicitly accepts selected-climate national rank with locally flood/heat-dominated variation as an RQ3 environmental-context construct'])
    dump('CBM_FEATURE_ADMISSION_DECISION.json',admission)
    md('CDC_2024_SOURCE_AND_VERSION_QA.md',f'''# CDC EJI 2024 source and version QA
{WARN}

Authority: `{AUTH}`. Official portal JavaScript and its geography JSON supplied the actual bulk filenames. Both national and California 2024 CSV ZIPs were downloaded successfully; no guessed third-party table substituted. Archives contain original CSV and matching CSV/XLSX dictionaries. National table: {rankqa['national_rows']:,} rows; California: {rankqa['california_rows']:,}. Both have unique GEOIDs. California numeric values and both dictionaries match the national release exactly.

Original payload URLs, UTC retrieval timestamps, server last-modified labels and SHA256/byte counts are in `OFFICIAL_SOURCE_ACQUISITION.json`. Archive member hashes are separate. The environment's task date is recorded separately from actual client UTC time; neither is the data vintage. Original ZIPs are immutable. The dictionary CSV uses Windows-1252 encoding; its original bytes are retained.

Official raw and CBM map services were queried for all 2,495 LA county records. Map's first broad query was transfer-limited; a long object-ID URL returned HTTP404. Both are retained in acquisition evidence, not mistaken for complete data. Final short, ID-bound queries retrieved exactly all expected records. Raw/bulk/map CBM fields agree on all2,299 approved tract IDs.

Dictionary/header use `GEOID_2020`, rather than the technical changelog's `GEOID_20` shorthand. It equals GEOID for all matched LA records. Connecticut's 2022 county-code exception is not applicable. Boundaries are 2020 TIGER/Line. CDC `E_TOTPOP` is ACS2018-2022 and differs from frozen population for {rankqa['cdc_population_differs']:,} study tracts. It is not substituted. One frozen-positive tract,06037980023 (47 frozen residents), has CDC population0 but valid climate rank; it remains eligible. All eight positive-population zero-housing tracts remain.

Published ranks exist for all2299; this is rank coverage, not proof of complete physical observation. Full source dictionaries expose six extreme-events flags, but no F_NEHD/F_SMOKE/F_BURN. Technical processing describes flags for all three; this upstream discrepancy remains unresolved.

The bulk raw NRI frequency fields numerically match the frozen v1.19 coastal/drought/riverine/wind frequencies to four-decimal export precision; hurricane source nulls match F=1. This is numerical association, not proof of an explicitly documented CDC NRI release identifier. Tornado uses CDC Tracking1986-2024 and does not match NRIv1.19; no substitution made.

The burned-area dictionary refers to the MTBS source archive (1984-2022), whereas technical processing uses 2013-2022 only and wildfire polygons over 1,000 acres. This is an archive-versus-analysis distinction, not a contradiction. Smaller fires and prescribed burns are not measured by this indicator. The drought technical text says event-weeks, whereas values match NRI event-days/year. Frozen FEMA v1.19 documentation p143 (printed 9-4) explicitly converts weeks to seven event-days. No values or published rank have been corrected by this audit. Indicator-level provider URLs and technical PDF page references are in the source register.
''')
    md('CBM_FLAG_AND_ZERO_SEMANTICS.md',f'''# CBM flags and zero semantics
{WARN}

The official dictionary defines:0=provider true zero in the source measure;1=source null updated to zero;2=positive estimate whose percentile is zero;9=other values. -999/null means unavailable, not zero. F=0 is a recorded/model-defined zero in a particular period/support, not proof of zero future hazard. F=9 may include modeled FEMA minimum frequency, not exclusively observed events. No user-generated zero substitution or imputation occurs.

{table(counts,['indicator','quality_state','tract_count','resident_population','flag_field_available'])}

All 2,299 tracts (9,066,522 frozen residents) have hurricane F=1. The frozen NRI frequency records are null here, and CDC assigns source-null zeros; the flag alone does not distinguish geography exclusion from another missing-source cause. These are not measured hurricane-free observations. This coordinate is locally constant and contributes no local score variance; omitting it changes national calibration but essentially not LA rank order. Its presence alone is not proof the CDC index is invalid.

The more consequential unresolved gate is absence of three published flags: heat/smoke positive estimates cannot be linked to documented processing exceptions, and2,251 burned-area zeros (8,892,273 residents) have no released flag separating actual no-intersection from source-null/excluded states. These are *unresolved zeros*, not a claim that2,251 values are missing. No count of provider structural zeros versus generic missing can be established where F=1 combines them.

CDC documents13 interpolated national heat records but gives no IDs or heat flag in the downloaded table. Their study membership is unknowable from the release. Crosswalk affects all heat values; smoke/burn use polygon intersections, and NRI hurricane/riverine may use minimum annual frequency. `CBM_2299_BY_NINE_INDICATOR_QUALITY.csv` preserves all20,691 tract-indicator records. The wide matrix and per-tract counts identify unresolved processing without silently dropping tracts.

There is no flag-free composite subgroup in this cohort because all hurricane flags are1. Thus flagged-versus-unflagged full-composite comparison is not estimable. Burn-zero/positive subgroup summaries are not missing-versus-observed strata. Source flags are not uncertainty confidence intervals.
''')
    md('CBM_RANK_RECONSTRUCTION_QA.md',f'''# Official rank reconstruction
{WARN}

`SPL_CBM = EPL_NEHD + EPL_BURN + EPL_SMOKE + EPL_CFLD + EPL_DRGT + EPL_HRCN + EPL_RFLD + EPL_SWND + EPL_TRND`.

`RPL_CBM` nationally ranks SPL_CBM; not a mean of three equally weighted domain ranks. Heat contributes1/9, Wildfire2/9 and Extreme Events6/9 of declared indicator-count weight before final national ranking. Domain ranks are separately national ranks of their own component sums. `RPL_EJI_CBM` nationally ranks the sum of RPL_EBM, RPL_HVM, RPL_SVM and RPL_CBM, so it is excluded from the intended RQ3 construct. RPL_EJI, RPL_SER and RPL_SVM are also not standalone climate ranks.

For {rankqa['national_valid_CBM']:,} nationally valid records, nine-percentile sum error is {rankqa['max_nine_EPL_sum_error']:.3g}. Independent minimum-rank/(N-1) national reconstruction differs by at most {rankqa['national_min_rank_max_error']:.8g}, within four-decimal export rounding. National Spearman agreement={rankqa['national_min_rank_Spearman']:.12g}. SQL versus Excel rounding and ties are acknowledged; not claimed byte-identical to unrounded CDC processing.

{table(contribution,['component','type','unique_values','zero_count','Pearson','Spearman','covariance_share_of_local_SPL_variance','incremental_linear_R2_for_published_rank'])}

Covariance shares sum to1 over indicators and separately over domains; they are decomposition of *local SPL score* variance including shared geographic covariance, not causal percentages of climate damage or nominal CDC weights. Riverine rank has only two values (0 and0.8605),439 positive-ranked and1,860 zero-ranked tracts. It accounts for69.248% of local score variance and Pearson0.918 with final rank. Heat contributes12.215%, wildfire combined10.310%, coastal8.106%; other indicators contribute almost no local variation. Heat Spearman0.621 remains important to ordering within the low-flood group. CBM is not literally single-component, but is not locally balanced across nine hazards.

Drought rank lies0.9467-0.9868 with only seven values. Strong wind is low/low-variance; hurricane is constant0; tornado rank is positive in only one tract, with13 other positive estimates assigned percentile0. Raw positive measurements can therefore have no effective variation in the index.

National leave-one-indicator/domain reranks are labeled researcher diagnostics, never CDC official alternatives. Omitting hurricane leaves top230 LA membership unchanged (local Spearman effectively1) while shifting national percentile calibration. Omitting riverine retains53.48% of top230, and omitting heat51.74%; both matter in different ways. Large absolute national-rank shifts after deleting a nearly constant local component do not establish local-information dominance.
''')
    md('CBM_FEATURE_ADMISSION_DECISION.md',f'''# Feature admission decision
{WARN}

**Not admitted to the primary eight-coordinate matrix at this stage. No K-means fits are performed.**

Pass: official standalone environmental/climate rank, no direct demographic/SOVI/resilience/asset-value terms; exact2,299-ID coverage; unchanged cohort/population; full national summation/rank reconstruction; limited P2 predictive overlap.

Unresolved mandatory source-quality gate: three technical flag fields absent from complete bulk data and raw service;2,251 burned-area zeros cannot be separated by their origin;13 national heat interpolation IDs unavailable. All hurricane source-null zeros are disclosed, not reclassified physical zeros. No subgroup is dropped. Source date/unit wording discrepancies are explicitly retained.

Construct caution: most LA score variance reflects one binary riverine-frequency rank with heat providing finer ordering. An established national multi-climate measure does not imply nine balanced independent hazards locally. This does not invalidate CDC's intended screening product; it limits use as a full-cohort physical-hazard coordinate without accepting these source semantics.

Recommendation: retain P2 as the existing seven-variable candidate and use standalone CBM/domain maps alongside independently acquired physical layers with their documented denominators. P2 is not promoted and K remains open. No conditional K-result file or stability claims are fabricated. H1/H2 allocations remain registered proposals; the distance-budget CSV is algebra only.

To reopen: obtain omitted flags/source-zero definitions and interpolated IDs from CDC (or documented source-level evidence), clarify drought-unit wording, then obtain explicit author approval for the *selected-climate contextual rank*, not all-hazard risk or electrical failure predictor. The burned-area archive/analysis-period distinction and large-fire filter are already documented. Only then run the registered full-cohort H1/H2 comparison.
''')
    md('RQ3_CBM_METHODS_AND_REVIEWER_RATIONALE.md',f'''# Proposed methods and reviewer rationale
{WARN}

## Current admissible contextual description (not inserted in manuscript)
The standalone CDC/ATSDR EJI2024 Climate Burden Module was examined as a contextual comparator. It nationally ranks the sum of nine indicator percentiles spanning heat, wildfire and selected extreme events. Unlike the combined EJI-plus-climate ranking or FEMA's social-adjusted RISK_SCORE, this standalone module has no direct social-demographic, resilience or asset-value adjustment. It excludes earthquake. Official data were joined to the unchanged2,299 positive-frozen-population cohort; component flags, national rank composition and source coverage were audited before consideration as a clustering input. Unresolved omitted quality flags and locally concentrated indicator variation precluded admitting it to the primary matrix in this audit.

## Reviewer explanation
An existing module is methodologically preferable to inventing a new ad-hoc multi-hazard score, but provider publication and complete percentile coverage are not sufficient admission tests. Unlike earthquake-dominated pooled EAL, CBM contains several non-earthquake climate measurements, but in LA riverine-frequency and heat ranks dominate its variation. Source-excluded zeros are not observed absence of hazards. Physical NFHL/CAL FIRE/PGA measures and relative CDC ranks have different spatial supports, time windows and meanings. Same-source heat agreement is a reproducibility check, not independent validation.

If a future approved extension uses RPL_CBM, it must be described as *post-earthquake modeled recovery with selected-climate environmental context*. It is not an all-natural-hazards risk index, multi-hazard electrical recovery simulation, joint climate-earthquake probability or causal outage-loss estimate. Future comparison changes both RQ3 coordinate inclusion and budgets: H1 thirds withinRQ3, H2 preserves SOVI while splitting population/context. Algebra can isolate budget contributions, but no present clustering results exist.
''')
    md('FINAL_CBM_AUTHOR_DECISION.md',f'''# CDC climate module: author decision
{WARN}

## Recommendation
**Keep the seven-variable P2 candidate; use standalone CBM and domain maps as climate-context descriptors. Do not add an eighth coordinate yet. K remains undecided.**

1. **Direct social adjustment? No.** Official standalone RPL_CBM sums nine climate indicator percentiles and nationally ranks the sum. It contains no direct household, social vulnerability, resilience or building-value factors. RPL_EJI_CBM does contain the other EJI modules and is not eligible. This is arithmetic separation, not proof of geographic/statistical independence.
2. **Coverage? 2,299/2,299 valid published ranks, all exact eleven-digit 2020 GEOIDs.** The full 2,315 study domain, 16 zero-population exclusions and eight special-use tracts remain unchanged. CDC's own ACS population is not substituted; tract 06037980023 has CDC population zero but frozen population 47 and remains.
3. **Source-null/flags? All 2,299 have hurricane F=1 (9,066,522 residents).** That is source-null/excluded-to-zero, not observed absence; the cause is not separately coded. It is locally constant and not the variation driver. F_NEHD/F_SMOKE/F_BURN are absent even in both bulk archives/dictionary and raw service. The 2,251 burned-area zeros lack released zero/null discrimination; this is unresolved, not a claim they are all missing. The 13 national heat interpolation IDs are unavailable.
4. **Local components? Primarily riverine frequency plus heat.** Riverine rank contributes 69.248% of local SPL variance and correlates 0.918 with CBM. Heat contributes 12.215%, wildfire 10.310%, coastal 8.106%. Hurricane is constant; drought/strong-wind/tornado rank variation contributes almost nothing. These are local covariance shares, not official weights or causal contributions. National multi-indicator coverage does not imply locally balanced nine-hazard information.
5. **Meaningful multi-hazard information? Some, but limited.** Heat strongly affects fine rank order; wildfire/coastal identify subsets. No new synthesized physical index is created. Complete ranks do not cure source-support gaps by themselves.
6. **Incremental information? Yes statistically, not established as mandatory construct.**

{table(comps,['variable_a','Pearson','Spearman'])}

Seven-feature conditional linear R2 = {nonlinear.conditional_linear_R2:.5f}, VIF = {nonlinear.VIF:.5f}; fixed random-fold nonlinear R2 = {nonlinear.random5fold_nonlinear_R2:.5f}, 15-km-block R2 = {nonlinear.spatial15km_5fold_nonlinear_R2:.5f}. Thus non-admission is not based on linear duplication. Predictive overlap is not causality or full independence.

7. **Physical geographic correspondence? Partial support, not intensity validation.**

{table(physical,['CDC_variable','physical_variable','n','Pearson','Spearman'])}

Riverine frequency aligns with mapped SFHA support on 2,088 complete NFHL tracts (Spearman 0.944); historical burn versus CAL FIRE severity is weaker (0.278 on 2,200). Heat exactly matches the prior *same CDC source*, not independently acquired temperature evidence. Coastal V fractions are lower-bound intersections on partial mapped support, not full hazard certainty. Earthquake PGA is not a CBM input. Polygon area is not exposed resident count.

8. **Admission? Not yet: unresolved mandatory source flags/zero semantics and local construct concentration.** No tracts are dropped or imputed to force eligibility.
9. **K/silhouette/ARI effects? Not evaluated.** Admission stopped before any new fit; no eight-coordinate Elbow/Silhouette/stability claim. H1/H2 budgets are predeclared, not fitted or optimized. Existing rare STATION Q group is untouched and is not reinterpreted by this audit.
10. **Manuscript choice? P2 plus standalone context maps is the defensible current candidate.** Formal Stage7, manuscript, numbered figures, physical realizations and schedules are unchanged. Author must approve any later measurement admission, policy set, budget and K. CDC clarification of omitted flags and source processing is the specific missing evidence.

## Reproduction and limitations
Original national/state archives, dictionaries, raw/map query payloads and SHA256s are retained. Independent QA verifies ranks, identities, arithmetic, associations, preservation and repeatability. All 950 protected files and previous diagnostic objects are checked. No MC, GA, repair, service-trajectory or K-means computation is authorized or run. Manifest-bound local frozen source/archive dependencies remain required for source-level baseline reconstruction where absent from Git; saved verified P2/physical CSVs support this diagnostic's core calculations. Six vector review figures have 600 dpi previews and publication-size renders. Remote delivery is verified separately using real LFS bytes, not pointers.
''')
    md('README.md',f'''# Standalone CDC EJI2024 climate-burden audit
{WARN}

Start `{AUTH}`. This package is isolated diagnostics, not formal Stage7. Read `FINAL_CBM_AUTHOR_DECISION.md` first. No new clustering fits: source-quality admission is unresolved.

Reproduction (Python3.12; repository dependencies plus requests/PyMuPDF/tabulate):
1. `python initialize.py` only at the starting authority in a clean isolated worktree; records hashes and source dirty state.
2. `python acquire.py --phase metadata`, `--phase discovery`, `--phase bulk`, `--phase query` (network only if archived snapshots absent).
3. `python audit_cdc.py`
4. `python information_audit.py`
5. `python reports.py`
6. `python figures.py`
7. `python verify_independent.py`

Run scripts from this package or pass their absolute path. Source resolver first uses clean-clone tracked files, then declared local frozen worktree fallbacks. Set LA_GRID_FROZEN_SOURCE_ROOT when full frozen local archives are needed. No formal-source outputs are overwritten. If a source is absent, resolution fails rather than inventing records. Git LFS pull is required for original ZIPs, tables and figures. Original source download failures/transfer-limit recoveries are documented. Review figure renders are for publication-size QA.

Policy/hazard/physical source inputs remain frozen:2pc50,C57_D1,M1_UTILITY_003,G1_BASELINE_050,480h,1,000 matched realizations; P2 MeanDelta is the equal descriptive mean of Impact/Hospital/Degree/Betweenness/Vulnerability-first increments, not a future-policy probability. Existing SOVI groups remain unchanged. Contacting CDC for missing flags is proposed, not performed.
''')
    print('SOURCE QA and ADMISSION: NOT ADMITTED; new fits=0',flush=True)


if __name__=='__main__':
    main()
