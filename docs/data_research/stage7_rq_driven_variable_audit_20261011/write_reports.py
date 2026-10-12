"""Build interpretation tables from the completed audit, without model fitting."""
import json

import numpy as np
import pandas as pd

from audit import OUT, PRIMARY, longpath, save

BE = 'docs/data_research/built_environment_20261009/'
FORMAL = 'Formal_Experiment_20260923/'


def read(name):
    return pd.read_csv(longpath(OUT / name))


def record(name):
    return json.loads((OUT / name).read_text())


def write(name, text):
    longpath(OUT / name).write_text(text.strip() + '\n', encoding='utf-8')


def main():
    f = pd.read_csv(longpath(OUT / 'TRACT_CANDIDATE_VALUES_2315.csv'), dtype={'tract_id': str}).set_index('tract_id')
    r = f.loc[f.residential_member].copy()
    cond = read('CONDITIONAL_EXPLAINED_VARIANCE_AND_VIF.csv')
    pairs = read('CROSS_DOMAIN_INFORMATION_AUDIT.csv')
    svi = read('SVI_COMPOSITE_SOURCE_COMPARISON.csv')
    cq, hq, rq = record('COHORT_QA.json'), record('HAZARD_SOURCE_QA.json'), record('RECOVERY_PAIRING_QA.json')
    original = record('ORIGINAL_COMMENT_SOURCE_RECORD.json')
    definitions = [
        ('RQ1','Init_Supply','PRIMARY','Mean frozen 2pc50 source-gated tract service availability at t=0: mean_m sum_j W_rj e_mj(0), divided by resolved mapping mass.','fraction [0,1]; retain raw fraction; future standardization only',FORMAL+'Formal_Trajectories/2pc50/C57_D1/direct-community/; '+BE+'local_joint_feature_extraction_20261009/RECOVERY_B_T80_INIT_COMPARISON.csv','frozen 20260923 experiment; 2pc50 CGS MS48 2025','model-generated','Initial modeled disruption, not duration or physical delivered load.','1529/2291 exact zeros; low positive range; standardized tails need explicit author review, not automatic removal.'),
        ('RQ1','Grid_Impact','PRIMARY','sum_j p_rj max(0,(lambda2_base-lambda2_after_removing_j)/lambda2_base); p_rj=W_rj/sum_j W_rj. Station measure is spectral impact_centrality.','dimensionless; raw; proposed later standardization',FORMAL+'Stage 2 Output_expanded/impact_centrality_substations.csv; Data/JULY_UTILITY_CONSTRAINED_92.csv','frozen physical/reduced graph and July utility mapping','model-generated','Dependency-weighted spectral network criticality. NOT impact_population repair-policy value.','Node removal uses the initial largest connected component; static structural proxy, not capacity or electrical flow; 33.4% exact zeros.'),
        ('RQ1','Redundancy_HHI','PRIMARY','sum_j p_rj^2 for normalized positive tract-substation dependency weights.','dimensionless (0,1]; raw', 'Data/JULY_UTILITY_CONSTRAINED_92.csv','frozen July M1_UTILITY_003 mapping','model-generated','Dependency concentration; larger means less diversified dependency.','Not a count of independent electrical paths, nor proof of feasible backup supply.'),
        ('RQ1','Grid_Degree','CONDITIONAL','sum_j p_rj d_j, with d_j the actual stored station graph degree.','dependency-weighted degree; raw',FORMAL+'Stage 2 Output_expanded/impact_centrality_substations.csv; Data/JULY_UTILITY_CONSTRAINED_92.csv','frozen graph/mapping','model-generated','Local adjacency differs from spectral removal criticality.','Not rejected as collinear: assess as a structural alternative or split the same structural budget if jointly retained; do not select by correlation with burden.'),
        ('RQ1','Grid_Betweenness','CONDITIONAL','sum_j p_rj b_j, with b_j the stored normalized station betweenness_centrality.','dimensionless; raw',FORMAL+'Stage 2 Output_expanded/impact_centrality_substations.csv; Data/JULY_UTILITY_CONSTRAINED_92.csv','frozen graph/mapping','model-generated','Shortest-path brokerage differs from spectral vulnerability.','Not rejected as collinear; another structural descriptor is an author construct choice, not an extra independent domain.'),
        ('RQ2','B_480_hr','PRIMARY','mean_m integral_0^480 [1 - sum_j W_rj e_mj(t)/sum_j W_rj] dt under fixed impact-first, C57_D1, M1_UTILITY_003, G1_BASELINE_050.','equivalent full-service-deficit hours [0,480]; raw hours, NOT B/480',FORMAL+'Formal_Offline_Evaluation/2pc50__C57_D1__impact-first__INTEGRALS.npz','frozen 1000 evaluation realizations; C57; duration multiplier 1','model-generated','Whole-trajectory cumulative normalized deficit under a declared constrained policy.','Policy-conditional, not inherent tract damage; e(t) is a service proxy. Bulk archive is locally manifest-verified but not currently Git-tracked.'),
        ('RQ2','Delta_B_logistics','PRIMARY','mean_m (B_r,m,impact-first - B_r,m,unconstrained), paired by exact physical sample ID with the same M1/G1 and 480-hour horizon.','additional normalized service-deficit hours; raw hours',FORMAL+'Formal_Offline_Evaluation/2pc50__C57_D1__impact-first__INTEGRALS.npz; corresponding unconstrained archive','same frozen 1000 realizations/C57_D1 context','model-generated','Incremental service loss attributable to this fixed constrained policy versus matched Unconstrained.','Contains queue, travel and sequence effects together; not an isolated causal travel effect. Do not jointly retain B_constrained, B_unconstrained and Delta.'),
        ('RQ2','T80','DESCRIPTIVE_ONLY','Earliest exact frozen event time at which the mean tract availability trajectory reaches 0.80; not mean realization-specific crossing time. Unreached remains censored/NA.','hours; milestone; 0 unreached here; never substitute 480',FORMAL+'Formal_Trajectories/2pc50/C57_D1/direct-community/; '+BE+'local_joint_feature_extraction_20261009/RECOVERY_B_T80_INIT_COMPARISON.csv','same frozen 2pc50/C57_D1/M1/G1 reference','model-generated','An interpretable recovery milestone, complementary presentation to cumulative deficit.','Very high empirical shared trajectory information with B; do not double-count it as another equal primary coordinate.'),
        ('RQ2','B_unconstrained','DESCRIPTIVE_ONLY','mean_m integral_0^480 (1-A_r,m,unconstrained(t)/mapping_mass_r) dt.','normalized service-deficit hours',FORMAL+'Formal_Offline_Evaluation/2pc50__C57_D1__unconstrained__INTEGRALS.npz','matched frozen 1000 evaluation realizations','model-generated','Physical restoration reference without dispatch constraints, used to define Delta.','Arithmetic identity with B and Delta; not a third independent recovery measurement.'),
        ('RQ3','SOVI_SCORE','PRIMARY','FEMA NRI v1.19 Mar-23 SOVI_SCORE: nationally percentile-based composite social vulnerability derived from CDC/ATSDR SVI 2020, preserved from the formal source.','score [0,100]; raw; not local re-ranking','Data/NRI_Table_CensusTracts_California.csv; Data/LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv','March 2023 NRI v1.19; underlying CDC/ATSDR SVI 2020','external measurement','One established relative social-vulnerability composite coherent with frozen vulnerability groups and policy.','Relative score, not absolute interruption loss. Q1-Q4 remain original frozen groups; do not replace with freshly cut residential quartiles.'),
        ('RQ3','log1p_Population','PRIMARY','Natural log(1+P_r), where P_r is the exact population used in frozen formal tract weights.','natural log of 1 + persons; proposed exposure coordinate','Data/Tracts_Within_Expanded_Area.csv; provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv','documented as 2020-based formal population; direct upstream Census release/batch unresolved','external frozen measurement','Magnitude of exposed population; distinct from vulnerability and service duration.','Computational identity is verified for 2315/2315. Upstream population release metadata requires author resolution before publication of a new typology; no replacement made.'),
        ('RQ3','Population','DESCRIPTIVE_ONLY','P_r: exact frozen formal tract population.','persons; no transformation', 'Data/Tracts_Within_Expanded_Area.csv','same frozen population; upstream release metadata unresolved','external frozen measurement','Exposure and population-weighted reporting denominator.','Deterministically equivalent to its log transform; never retain both as independent coordinates.'),
        ('RQ3','log1p_Pop_Density','DESCRIPTIVE_ONLY','Natural log(1 + stored Pop_Density), where stored density is CDC 2022 E_TOTPOP / AREA_SQMI.','natural log of 1 + persons/square mile; diagnostic only','Data/California.csv; frozen candidate source','CDC SVI 2022 / ACS 2018-2022; not frozen population vintage','external measurement','Population concentration rather than total exposed population.','Uses a different population source and area denominator. A km2 conversion before log1p is a different transform; no silent replacement by formal-population density.'),
        ('RQ3','CDC2022_RPL_THEMES','CONDITIONAL','Official CDC/ATSDR 2022 California overall RPL_THEMES, with -999 invalid values kept missing.','state-relative percentile [0,1]; alternative only','Data/California.csv','CDC/ATSDR SVI 2022; ACS 2018-2022','external measurement','Established alternative overall SVI, not an additional coordinate.','Changes ranking and Q4 membership; would change the vulnerability-targeting estimand. 24 full-domain missing values; no zero fill.'),
        ('RQ3','CDC2022_local_theme_mean','EXCLUDE','Historical local arithmetic mean of four available CDC 2022 RPL_THEME1 through RPL_THEME4 values.','mean theme percentile [0,1]; reconstructed for comparison only','Data/California.csv; '+FORMAL+'Stage 7 Output_expanded/clusters_labels_final.csv (SVI_Composite only)','historical Stage 7 local construction on CDC 2022 data','locally constructed diagnostic','Explains the historical source discrepancy only.','NOT official CDC overall SVI; neither a new official index nor a Route A candidate.'),
        ('RQ3','electric_heating_share','CONDITIONAL','ACS B25040_004E / B25040_001E: electricity as principal residential heating fuel among occupied housing units.','fraction [0,1]; ACS estimate; VRE-based 90% MOE retained',BE+'living_environment_audit_20261011/LIVING_ENVIRONMENT_VALUES_2315.csv; '+BE+'living_environment_audit_20261011/sources/B25040_06.csv.zip','ACS 2018-2022 five-year, 2020 tract geography; diagnostic commit f321517','external measurement','Narrow residential electric-heating reliance; not general medical or all-season electricity dependence.','Complete residential coverage and some independent information, but substantial MOE and no weather, backup or space-cooling measurement. Optional targeted sensitivity, not primary third coordinate.'),
        ('RQ3','housing_5plus_share','DESCRIPTIVE_ONLY','ACS housing units in structures with five or more units / total housing units, used only as heating context.','fraction [0,1]',BE+'candidate_admission_rebuild_20261010/CANDIDATE_VALUES_2315.csv','ACS 2018-2022 five-year / B25024','external measurement','Housing composition explains part of heating reliance.','Housing composition overlaps SVI components; is not itself verified electricity-interruption sensitivity.'),
        ('RQ3','hospital_tract','DESCRIPTIVE_ONLY','Frozen indicator of a hospital-linked census tract used by service-priority calculations.','binary 0/1','provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv','frozen formal critical-service linkage; original facility vintage not reauthenticated here','external frozen linkage','Location-linked critical-service reporting, not resident medical dependence.','Hospital location does not measure all residents or facility backup power. Keep Hospital-linked mean burden downstream.'),
    ]
    rows = []
    for domain, name, decision, definition, units, source, vintage, generated, interpretation, limitation in definitions:
        x = r[name].astype(float)
        valid = x[np.isfinite(x)]
        q = valid.quantile([.10,.25,.50,.75,.90])
        sd = valid.std(ddof=1)
        assoc = r[[name, *[c for c in PRIMARY if c != name]]].corr(method='spearman')[name].drop(name)
        relations = '; '.join(f'{c}: Spearman={v:.4f}' for c,v in assoc.items())
        rows.append(dict(RQ_domain=domain,variable_name=name,exact_scientific_definition=definition,
                         units_and_transformation=units,source_file=source,data_vintage=vintage,
                         measurement_type=generated,statistics_cohort='2291 residential; individual available values; pairwise audits use complete same cohort',
                         valid_tract_count=len(valid),valid_full_domain_count=int(np.isfinite(f[name]).sum()),
                         missing_values=int(x.isna().sum()),invalid_values=int((x.notna()&~np.isfinite(x)).sum()),
                         full_domain_missing_values=int(f[name].isna().sum()),P10=q.loc[.10],P25=q.loc[.25],median=q.loc[.50],P75=q.loc[.75],P90=q.loc[.90],
                         mean=valid.mean(),standard_deviation=sd,minimum=valid.min(),maximum=valid.max(),
                         zero_fraction=valid.eq(0).mean(),near_zero_fraction=(valid.abs()<=1e-8).mean(),
                         extreme_value_fraction=(np.abs((valid-valid.mean())/sd)>3).mean() if sd>0 else 0,
                         extreme_definition='absolute unweighted z > 3; descriptive flag, NOT exclusion; near-zero abs <= 1e-8',
                         relationship_to_existing_variables=relations,independent_interpretation=interpretation,
                         scientific_limitation=limitation,recommendation=decision))
    rejected = [
        ('RQ3','CDC_four_theme_coordinates','EXCLUDE','Four CDC percentile themes as separate coordinates would count social vulnerability four times in Route A.','Individual thematic components are not extra independent vulnerability domains.'),
        ('RQ3','elderly_or_disability_share','EXCLUDE','Nested CDC SVI component measurements; no separately validated electricity-dependent resident needs variable admitted.','Different labels do not establish independence from the selected composite.'),
        ('RQ3','resident_electricity_dependent_medical_need','CONDITIONAL','No documented reasonably complete tract measure with denominator and backup-power context found in the retained inventory.','Evidence gap; not zero need. No values fabricated or inferred from hospital locations.'),
        ('RQ3','building_value_or_general_built_environment','EXCLUDE','Stock value, vegetation, parks, building form and land-use entropy are not admitted in this RQ-driven specification.','No independently declared electricity-interruption construct; previous built-environment QA is not feature eligibility.'),
        ('RQ1','NRI_RISK_SCORE_or_ALR_NPCTL_as_2pc50_hazard','EXCLUDE','NRI integrated risk and multi-hazard annualized-loss-rate percentile are not the fixed 2pc50 ground-motion exceedance benchmark.','Integrated community risk or multi-hazard loss cannot be relabeled as pure scenario-specific PGA.'),
        ('RQ3','Population_times_B','EXCLUDE','P_r times cumulative normalized deficit is person-hours, deterministically constructed from two existing coordinates.','Use for aggregate exposure-weighted reporting if declared, not an additional independent distance coordinate.'),
        ('RQ2','AUC_480','EXCLUDE','For the same mean normalized trajectory AUC_480 = 1 - B_480_hr/480.','Exact mathematical duplicate of B.'),
        ('RQ3','Q4_mean_Q4_minus_Q1_Gini_Hospital_linked_mean','DESCRIPTIVE_ONLY','Strategy-level distributional evaluation metrics, not tract-level measurements.','Wrong observational level for tract clustering; retain as downstream evaluation.'),
    ]
    for domain,name,decision,definition,limitation in rejected:
        row={c:np.nan for c in rows[0]}
        row.update(RQ_domain=domain,variable_name=name,exact_scientific_definition=definition,
                   units_and_transformation='not an admitted tract coordinate',source_file='existing source inventory / construct review only',
                   data_vintage='not a new measurement',measurement_type='construct-only screening',
                   statistics_cohort='not materialized for clustering; numeric statistics intentionally not applicable',
                   relationship_to_existing_variables=definition,independent_interpretation='No additional admitted construct',
                   scientific_limitation=limitation,recommendation=decision)
        rows.append(row)
    save('THREE_RQ_CANDIDATE_REGISTER.csv',rows)
    domains={row['variable_name']:row['RQ_domain'] for row in rows}
    pairs['RQ_domain_a']=pairs.variable_a.map(domains)
    pairs['RQ_domain_b']=pairs.variable_b.map(domains)
    def relationship(row):
        names={row.variable_a,row.variable_b}
        if names=={'Population','log1p_Population'}:
            return 'MATHEMATICAL_IDENTITY_TRANSFORM', 'log1p invertible; never two independent coordinates'
        if names <= {'B_480_hr','B_unconstrained','Delta_B_logistics','T80'}:
            return 'SHARED_TRAJECTORY_CONSTRUCT', 'B_c=B_u+Delta is a triplet identity, not a pairwise identity; T80 shares trajectories'
        if names <= {'SOVI_SCORE','CDC2022_RPL_THEMES','CDC2022_local_theme_mean'}:
            return 'SHARED_SOURCE_OR_COMPOSITE_ALTERNATIVE', 'Overall SVI and local theme mean are alternatives, not additional social dimensions'
        if 'Init_Supply' in names and names & {'B_480_hr','T80','Delta_B_logistics','B_unconstrained'}:
            return 'SHARED_PHYSICAL_SERVICE_PROCESS', 'Initial state and subsequent burden share physical samples and mapping; not a mathematical identity'
        if names & {'SOVI_SCORE','CDC2022_RPL_THEMES','CDC2022_local_theme_mean'} and names & {'electric_heating_share','housing_5plus_share','log1p_Pop_Density'}:
            return 'RELATED_CENSUS_COMPONENT_CONSTRUCTS', 'Census composition/source lineage can overlap; sources/vintages and exact measures differ'
        if row.RQ_domain_a=='RQ1' and row.RQ_domain_b=='RQ1':
            return 'SHARED_MAPPING_DIFFERENT_NETWORK_CONSTRUCTS', 'Same W projection; structural and dependency constructs remain scientifically distinguishable'
        return 'EMPIRICAL_ASSOCIATION_NOT_IDENTITY', 'Association does not establish causality or independent construct validity; interpret mechanism and sources'
    annotated=pairs.apply(relationship,axis=1)
    pairs['relationship_class']=[v[0] for v in annotated]
    pairs['interpretation_note']=[v[1] for v in annotated]
    save('CROSS_DOMAIN_INFORMATION_AUDIT.csv',pairs)
    primary_cond=cond[cond.block=='primary_three_RQ']
    heat_cond=cond[(cond.block=='RQ3_heating_context')&(cond.target=='electric_heating_share')].iloc[0]
    heating=r.electric_heating_share_moe90
    high_moe=int((heating>.10).sum())
    def pearson(a,b):
        return float(r[a].corr(r[b]))
    def table(columns):
        return r[columns].corr(method='spearman').round(4).to_markdown()
    write('RQ3_ROUTE_A_SOCIAL_AND_POPULATION_AUDIT.md',f"""
# Route A: social vulnerability and population exposure

Status: candidate evidence only; no formal Stage 7 replacement, regrouping or clustering. Statistics below use the same {len(r)} residential GEOIDs unless a source comparison explicitly says otherwise.

## Composite source identity and harmonization

Use **FEMA NRI v1.19 March 2023 `SOVI_SCORE`**, not NRI total risk or an older HVRI SoVI release. All 2,315 source rows match exact eleven-digit GEOIDs and `NRI_VER=Mar-23`; all values match the frozen candidate source and score helper (helper decimal tolerance 1e-5). The authoritative existing [harmonization decision](../../methodology/STAGE7_SVI_HARMONIZATION_DECISION.md) and [source review](../../reviewer/SOCIAL_VULNERABILITY_MEASURE_REVIEW.md) document CDC/ATSDR **SVI 2020** lineage and a **national percentile-based 0-100 scale**. These are source vintages, not earthquake dates. FEMA v1.19 documentation: [provider version record](https://www.fema.gov/sites/default/files/documents/fema_national-risk-index-data-version-and-update-documentation.pdf). The score is relative social vulnerability, not a probability of outage or absolute welfare loss.

CDC 2022 California official `RPL_THEMES` is a **state-relative 0-1 overall percentile**, using ACS 2018-2022. It is distinct from the historical local arithmetic mean of `RPL_THEME1` through `RPL_THEME4`. Ranking and combining underlying variables and then ranking an overall score is not equivalent to averaging four percentile themes. [Official CDC 2022 documentation](https://www.atsdr.cdc.gov/place-health/media/pdfs/2024/10/SVI2022Documentation.pdf). The local mean is reproduced solely to audit the discrepancy; neither it nor four separate theme coordinates is recommended for Route A.

`SVI_COMPOSITE_SOURCE_COMPARISON.csv` independently reproduces the earlier harmonization associations and membership comparisons. SOVI versus CDC official overall: Pearson 0.9468, Spearman 0.9480; versus local theme mean: 0.9255 and 0.9292. Similarity is high, but ranking is not identical. Median absolute percentile-rank displacement is 0.0543 and 0.0633, respectively; P95 is 0.1880 and 0.2217.

On the 2,291 common valid source rows, replacing the **actual frozen** Q4 by newly cut CDC overall Q4 gives overlap 466, entrants 106, departures 111, Jaccard 0.6823. Replacing it by the local mean gives overlap 450, entrants 122, departures 127, Jaccard 0.6438. These are diagnostic comparisons, NOT applied group changes. All original full-domain groups (Q1=579, Q2=580, Q3=577, Q4=579) and the Vulnerability-first strategy remain unchanged. Freshly cutting even FEMA quartiles does not exactly reproduce the frozen original membership; do not silently recut it.

## Population exposure, not another vulnerability index

`Population` is copied from `Data/Tracts_Within_Expanded_Area.csv` and agrees with formal evaluation metadata and prior frozen candidate population on **2,315/2,315** rows. The harmonization record describes it as 2020-based; a direct upstream Census release/batch record was not recovered in this audit. Exact computational provenance is clean; that remaining external-vintage documentation must be resolved by the authors, not guessed. No CDC 2022 population, canopy-layer population or NRI population replaced the frozen values. NRI `POPULATION` is not interchangeable (only 7/2,315 exact matches in an exploratory check).

Propose `log1p(Population)` for scale compression of exposed people. Total population measures exposed magnitude; density measures spatial concentration and has an area denominator; population-weighted aggregate loss is a downstream weighted summary; `Population * B` is person-hours constructed from existing exposure and duration. The latter is not a new independent coordinate. Do not retain raw Population and its log transform together.

Residential Pearson correlation of log population with SOVI is {pearson('log1p_Population','SOVI_SCORE'):.4f}. Controlling the other six proposed coordinates gives linear R-squared 0.0655, VIF 1.0701 and additive-spline cross-validated R-squared 0.0639. Exposure magnitude is not mechanically duplicated by the vulnerability score. Population density remains a descriptive diagnostic, with a separate CDC denominator/vintage. No outcome-correlated variable selection is performed.

## Possible third coordinate: electricity heating

The prior independently sourced [living-environment audit](../built_environment_20261009/living_environment_audit_20261011/) supplies ACS B25040 electricity-as-principal-heating-fuel share, ACS **2018-2022 five-year**, 2020 tract support. This is occupied housing units, not residents or all buildings. Source: [official Census 80-replicate B25040 archive](https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/B25040_06.csv.zip). Estimates and MOEs were validated there against official source cells; that diagnostic package is separately pinned to commit f321517.

All 2,291 residential records are valid. With SOVI, log population, log density and 5+ housing-unit share as controls, heating has linear R-squared {heat_cond.conditional_linear_R2:.4f}, VIF {heat_cond.VIF:.4f}, and additive-spline CV R-squared {heat_cond.additive_spline_cv_R2:.4f}. Thus it is **not simply a statistical duplicate**. Its Pearson association with 5+ housing share is {pearson('electric_heating_share','housing_5plus_share'):.4f}. Housing-unit composition overlaps the composite's housing-related components; statistical residual variation alone does not establish a new community-dependence construct.

Uncertainty is material: median share MOE90={heating.median():.4f}; P90={heating.quantile(.9):.4f}; **{high_moe}/2291 ({high_moe/len(r):.2%})** exceed 0.10 (ten percentage points). The prior MOE uses correlated numerator/denominator 80-replicate ratio variance, including documented Census boundary fallback, not independent MOE division. These are survey estimates, not observed post-event household electricity needs.

Recommendation: **CONDITIONAL** for a specifically declared residential-heating interruption sensitivity experiment, not a third primary Route A coordinate. Temperature, alternative fuels, backup supply, cooling and medically necessary loads are absent. Completeness does not cure limited construct scope or large uncertainty. No reasonably complete verified tract-level medical electricity-dependence measure was found. Hospital location is not resident dependence; age/disability shares are already component-related to SVI; stock value or general built environment is not interruption loss. Keep RQ3 at **two coordinates** rather than manufacture a weak third.

## Original comment record

An original local `CommentsLAGrid.docx` was inspected read-only; SHA256 `{original['sha256']}`; location and exact quote are in `ORIGINAL_COMMENT_SOURCE_RECORD.json`. The relevant readable comment is:

> {original['original_comment']}

This asks for clear K-means variables and purpose. No explicit recommendation to average the four SVI theme percentiles was located in readable main-document text, and no comments XML was present. The record is the locally supplied reviewer file; author metadata does not independently authenticate attribution. **Do not attribute an SVI aggregation recommendation to Marta from this evidence.** Embedded-image-only content, if any, is not evidence of a new recommendation. No comment document is republished here.

Q4 mean burden, Q4-Q1 gap, Gini and Hospital-linked mean burden remain downstream strategy-evaluation metrics, not tract clustering coordinates.
""")
    write('RQ2_2PC50_HAZARD_AND_POLICY_PROVENANCE.md',f"""
# RQ2: frozen 2pc50 hazard and fixed restoration policy

## Hazard reference

Actual source is `Data/MS_048_CA_pt01_MMI_GM_datafiles/CA_pt01_GM_maps.csv`, CGS **MS48 (2025)**, based on **USGS NSHM 2023**, with July 2022 Vs30. The provider describes a 0.01-degree California grid; this exact file has {hq['rows']:,} rows and a `PGA-2pc50` column in g. [Official CGS MS48 publication and download page](https://www.conservation.ca.gov/cgs/Pages/Publications/MS48.aspx). Original payload SHA256: `{hq['source_sha256']}`. Prior official-download byte equality is preserved in the acquisition record; this audit checks the local payload and archived source check, not a new interpolation.

Frozen station CSV `PGA_2pc50` matches the archived source reconstruction for **92/92 stations**: min {hq['station_min_g']:.6f} g, median {hq['station_median_g']:.6f} g, max {hq['station_max_g']:.6f} g; maximum archived reconstruction error {hq['frozen_check_max_error_g']:.3g} g. `FROZEN_STATION_PGA_VERIFICATION.csv` retains each station ID and both values. No PGA/damage sample was regenerated or replaced.

`2pc50` means **2% probability of ground-motion exceedance in 50 years**, not 2% of stations in a damage state. Under the Poisson return-period convention, -50/log(0.98) = {hq['mean_return_interval_yr']:.2f} years. A common regional probabilistic ground-motion level is a defensible benchmark for comparing tract dependencies and restoration policies under the same declared shaking reference. It is not a unique physically specified rupture, a spatially sampled coherent earthquake-event field, or a combined population/asset/social-vulnerability risk index. The frozen damage realizations are conditional on this fixed hazard field and the existing fragility assumptions; this audit does not certify spatial ground-motion correlation.

Do not call this **ASCE 41-17 BSE-2E**: that is 5% exceedance in 50 years, subject to BSE-2N; BSE-2N is based on ASCE 7 risk-targeted MCER. [FEMA P-2018, Section 3.3](https://www.fema.gov/sites/default/files/2020-08/fema_seismic-eval-older-concrete-buildings_p-2018.pdf) corroborates the distinction. In this session the indexed primary-source passage was accessible but opening the full FEMA PDF failed; no full-PDF reread is claimed. The source/data interpretation as 2pc50 is consistent. **Calling it BSE-2E, a unique earthquake, or integrated community risk would be a substantive terminology mismatch** requiring later author correction, not silent scientific change here.

## Policy and physical reference

The hazard reference and policy reference are separate decisions. Fix **Impact-first (`impact-first`, the population-impact repair policy)** as constrained reference for this candidate audit; do not confuse its policy score with spectral `Grid_Impact`. Resources: **C57_D1, 57 crews, duration multiplier 1**, existing crew origins/travel, all physical samples held fixed. Mapping: **M1_UTILITY_003**, frozen `JULY_UTILITY_CONSTRAINED_92.csv`; gate: **G1_BASELINE_050**; horizon: **480 h**. Compare to matched **Unconstrained** only. This is not a declaration that Impact-first is scientifically optimal.

The two `INTEGRALS.npz` sources in `Formal_Experiment_20260923/Formal_Offline_Evaluation/` contain 1,000 evaluation realizations; `PHYSICAL_SAMPLE_MANIFEST.csv` and `physical_inputs_2pc50.npz` give fixed station order, physical IDs, DS/duration hashes. Archives contain multiple mapping/gate cases: only the named M1/G1 arrays are used. `RECOVERY_PAIRING_QA.json` and `INDEPENDENT_VERIFICATION.json` verify common graph/source/mapping/physical/crew/travel identities and horizon, rather than inferring equality from filenames.

For tract r and realization m, define A_r,m(t)=sum_j W_rj e_mj(t), mass_r=sum_j W_rj. Then B_r,m=integral_0^480 [1-A_r,m(t)/mass_r] dt. The fixed M1 mass is one for every tract. `B_480_hr` is mean_m B_r,m in **equivalent full-service-deficit hours**; its normalized proportion is B/480, not a separate coordinate. `Delta_B_logistics` is mean_m (B_r,m,Impact - B_r,m,Unconstrained), exactly paired by physical ID. It incorporates dispatch queuing, travel and sequence jointly; it does not isolate travel causally. Archive integral versus W-projected station integral agrees within {max(rq['normalized_integral_max_errors_hr'].values()):.3g} h.

## Legacy direct-community identity

The frozen direct-community reference and Impact-first are **numerically identical in this applicable formal case**: the integral files have identical bytes; all 1,000 event payloads match independently; the recorded incumbent sequence is Impact-first with no improvement. This supports using the named fixed policy to clarify provenance. It does not prove all direct-community searches, resources or scenarios would be identical, or that an independent optimized policy was evaluated here.

## T80 and redundant recovery measures

T80 is the **first exact frozen event at which the mean tract availability reaches 0.80**, not an average of realization-specific T80. The audit reconstructs the mean event trajectory from saved monotone e(t), without applying a new gate or simulating recovery. Reconstruction error is {rq['T80_max_error']:.3g} h. All 2,315 mean trajectories cross before 480 h; mean-trajectory unreached count=0; terminal realization-tract pairs below 0.80=0. `T80_CENSORING_AND_ENDPOINTS.csv` gives every GEOID. No unreached time was filled with 480. In any future data with unreached cases, use a censoring flag and actual endpoint; do not silently fill, drop or treat horizon as a crossing.

Residential B-T80 Pearson={pearson('B_480_hr','T80'):.4f}, Spearman={r.B_480_hr.corr(r.T80,method='spearman'):.4f}; B-Delta Pearson={pearson('B_480_hr','Delta_B_logistics'):.4f}. `RQ2_RECOVERY_METRIC_REDUNDANCY.csv` and conditional diagnostics show strong shared recovery information for B and T80, while Delta distinguishes the fixed constraint increment. Proposed primary RQ2: **B and Delta**. T80 is descriptive. The exact identity B_constrained=B_unconstrained+Delta makes that three-coordinate triplet inadmissible (VIF infinite); AUC=1-B/480 is also an exact duplicate.

## Source availability limitation

Tracked input identities, physical manifests and prior source checks are available through Git/LFS. The bulk offline integral and per-realization event archive files used here are **not currently Git-tracked**; they were read from the authoritative local frozen research archive and verified against manifests. Independent verification checked 3,000 event payloads across all three policies. Reproduction of that source-level verification needs access to the same manifest-bound archive in addition to a clean clone. No bulk archive is copied or newly published here. The package retains derived tract metrics, source hashes and checks so its statistical diagnostics are inspectable, but does **not** claim clean-clone access to every frozen trajectory.
""")
    gridc=cond[cond.block=='RQ1_all']
    write('PROPOSED_FEATURE_AND_WEIGHT_DECISION.md',f"""
# Proposed RQ-driven measurements and domain budgets

**Decision status: author-review proposal only.** No new K-means, PCA, k selection, outcome-optimized weights, fitted weighted matrix, formal typology promotion or manuscript/figure edit. Prior five-domain CORE3/W1 stability does not validate this new construct specification.

## Research questions and selected constructs

RQ1 asks how hazard/network dependency produces disruption. Proposed coordinates: **Init_Supply** (initial service state), **Grid_Impact** (spectral structural criticality), **Redundancy_HHI** (dependency concentration). RQ2 asks about restoration under resources/logistics; under fixed 2pc50 and Impact-first propose **B_480_hr** (cumulative deficit) and **Delta_B_logistics** (matched constrained-minus-Unconstrained increment). RQ3 asks how burdens distribute across vulnerability and places; Route A proposes **SOVI_SCORE** and **log1p(Population)**. The latter is numerically frozen and reproducible; direct population source-vintage documentation remains an author action, not a reason to substitute a new population. These seven candidate coordinates measure distinct declared constructs, not every available graph or census statistic.

The existing framework figure `results/figure_review/Main/Fig01.pdf` and its three-question `provenance/figure_review_history/candidate_v2.1_layout/STORY_EVIDENCE_MATRIX.md` were source/hash checked, not regenerated. This audit uses the three RQs as construct organization, not current cluster narratives as an eligibility rule.

## RQ1 structural alternatives are not statistically rejected

{gridc[['target','conditional_linear_R2','VIF','additive_spline_cv_R2']].round(4).to_markdown(index=False)}

Impact-Degree Pearson={pearson('Grid_Impact','Grid_Degree'):.4f}; Impact-Betweenness={pearson('Grid_Impact','Grid_Betweenness'):.4f}; Degree-Betweenness={pearson('Grid_Degree','Grid_Betweenness'):.4f}. Degree and Betweenness have complementary empirical structural information; **they are CONDITIONAL, not EXCLUDE for multicollinearity**. One primary spectral coordinate is a parsimonious construct choice. Authors may declare local adjacency or brokerage as additional measurements, but must split the same structural-importance budget and justify the added construct. Do not select them because they explain B well or recreate preferred clusters.

All four graph descriptors were independently reprojected from stored station metrics and exact normalized W; maximum errors are in `GRID_DEFINITION_QA.json`. Spectral Grid_Impact is not the repair policy's population-impact score. The stored degree is used as defined in the frozen graph, not relabeled as a power capacity. HHI is tract dependency concentration, not independent electrical-path redundancy.

Init_Supply has {int(r.Init_Supply.eq(0).sum())}/{len(r)} exact zeros ({r.Init_Supply.eq(0).mean():.2%}) and max {r.Init_Supply.max():.6f}. Grid_Impact has {int(r.Grid_Impact.eq(0).sum())} exact zeros ({r.Grid_Impact.eq(0).mean():.2%}). Zero and near-zero distributions are in the register. This severe 2pc50 initial-state sparsity limits resolution and can accentuate standardized tails; no values are clipped, imputed, excluded or rescaled into a new fitted matrix here. Tiny floating-point excursions are reported with numeric tolerance, not edited away.

## Joint information audit

All primary and extended proposed/diagnostic pairwise matrices use the **same 2,291 residential tract IDs**, in exact sorted order. Pearson, Spearman, bidirectional nearest-neighbor mutual information, directional five-fold additive-spline R-squared, conditional linear explained variance and VIF are retained. Pairwise files classify mathematical transform identities, shared trajectories/composite sources, shared mapping and empirical associations. The extended matrix intentionally includes inadmissible alternatives and the recovery arithmetic triplet for diagnosis only; its infinite VIFs are expected, not an estimable model.

For the seven primary coordinates, linear conditional R-squared ranges {primary_cond.conditional_linear_R2.min():.4f}-{primary_cond.conditional_linear_R2.max():.4f}, VIF {primary_cond.VIF.min():.4f}-{primary_cond.VIF.max():.4f}. They are not linearly interchangeable. Nonlinear information can still be substantial (e.g. Init_Supply spline CV R-squared {primary_cond.loc[primary_cond.target=='Init_Supply','additive_spline_cv_R2'].iloc[0]:.4f}); shared W and fixed event trajectories provide real mechanistic dependence. Random tract CV does not establish spatially independent generalization, and MI with many ties/zeros is descriptive. No p-value, VIF cutoff or correlation threshold is used as an automatic feature admission rule.

Mathematical duplication (B_c=B_u+Delta; AUC=1-B/480; Population/log transform) is different from composite-source overlap (SVI alternatives), empirical correlation (B versus T80), or a physical/mechanistic relation (dependency, initial loss and later recovery). None alone proves causal mediation. No cluster labels, ARI, silhouette, selected k or manuscript profile was used.

## Cohorts and explicit exclusions

Full modeled domain=2,315; prior residential cohort=2,291; historical CORE3 reference=2,287. Proposed primary statistics use residential 2,291 for continuity, **not** historical CORE3 geometry admission. Regained four: {', '.join(cq['regained_residential_GEOIDs'])}. None has missing primary coordinates. All seven are actually complete on the full 2,315 domain, so retaining the residential restriction is an explicit scientific scope decision, not a data-quality necessity.

The 24 residential exclusions are individually listed in `TRACT_COHORT_AND_MISSINGNESS.csv`: 23 zero housing-unit records and one zero frozen-population record. The study-wide model retains them. Old geometry discrepancies do not require exclusion for these non-geometry-dependent measures. No zero imputation or generic complete-case deletion occurred. Authors must confirm **residential 2,291 versus full-domain 2,315** before future clustering; this audit does not silently promote either.

## Proposed squared-distance budget, not a fitted matrix

After author approval of measurements and cohort, a future analysis could standardize the selected coordinates on that fixed cohort and use squared distance sum_v a_v (z_rv-z_sv)^2. A coordinate's multiplier would be sqrt(a_v); the table below is a normative domain-balance proposal, **not statistically optimal**, not fitted and not applied.

| Domain | Construct | Proposed coordinate | Squared-distance budget a_v |
|---|---|---|---:|
| RQ1 | Initial modeled state | Init_Supply | 1/9 |
| RQ1 | Structural criticality | Grid_Impact | 1/9 |
| RQ1 | Dependency concentration | Redundancy_HHI | 1/9 |
| RQ2 | Cumulative deficit | B_480_hr | 1/6 |
| RQ2 | Fixed constraint increment | Delta_B_logistics | 1/6 |
| RQ3 | Composite vulnerability | SOVI_SCORE | 1/6 |
| RQ3 | Population exposure scale | log1p(Population) | 1/6 |

Each domain totals **1/3**, total 1. If Degree/Betweenness is additionally justified within structural importance, split that construct's 1/9 among retained structural measurements; do not increase RQ1's total. If a third genuinely independent RQ3 construct is later admitted, explicitly revise within-domain construct budgets rather than append equal global weight. Heating is not presently primary. Do not include B_unconstrained or T80 as extra recovery coordinates, four SVI themes as four social coordinates, or Population*B as another exposure coordinate.

## Required author decisions and remaining limitations

1. Approve the fixed 2pc50 hazard benchmark separately from fixed Impact-first C57_D1 policy/M1/G1 reference; no independent optimized direct-community benefit is claimed.
2. Confirm residential versus full-domain typology scope; do not inherit the old four geometry exclusions.
3. Resolve the upstream Census release/batch for frozen formal population without replacing the values. The current 2020-based claim is documented but not independently authenticated to an original release in this task.
4. Decide whether adjacency/brokerage adds a declared structural construct; the data do not require their deletion as redundant.
5. Decide whether electric heating merits a narrow, uncertainty-aware separate sensitivity analysis. No complete broadly valid third electricity-dependence coordinate was admitted.
6. Approve any later standardization/domain-budget implementation and treatment of initial-state sparsity. No automatic trimming or weighting occurs here.
7. Make the manifest-bound bulk trajectory archive available if source-level clean-clone replication is required; current Git does not contain all those bulk payloads.

The proposal is scientifically interpretable but not an author-approved new typology. Qualifying variables as numerically clean does not make incomplete external release metadata resolved, service proxies actual outage observations, or static graph analysis electrical power-flow feasibility.
""")
    write('README.md',"""
# Final three-RQ Stage 7 variable audit (2026-10-11)

Isolated diagnostic package. No scientific baseline, formal Stage 7 output, manuscript, figure, sample, schedule or previous diagnostic is modified. No clustering/weighted feature matrix is fitted. Primary decisions remain proposals for author approval.

## Start here

- `PROPOSED_FEATURE_AND_WEIGHT_DECISION.md`: concise feature/construct/cohort/budget decision and unresolved actions.
- `THREE_RQ_CANDIDATE_REGISTER.csv`: definitions, provenance, coverage, same-residential-cohort distributions, zeros/extremes and dispositions.
- `RQ3_ROUTE_A_SOCIAL_AND_POPULATION_AUDIT.md`: single SVI, population and optional heating evidence.
- `RQ2_2PC50_HAZARD_AND_POLICY_PROVENANCE.md`: original PGA, exact metric/policy/sample/censoring identity.
- `RQ1_GRID_METRIC_REDUNDANCY.csv`, `RQ2_RECOVERY_METRIC_REDUNDANCY.csv`, `CROSS_DOMAIN_INFORMATION_AUDIT.csv`: pairwise linear/rank/nonlinear evidence.
- `CONDITIONAL_EXPLAINED_VARIANCE_AND_VIF.csv`: conditional explained variance and VIF; identity blocks intentionally singular.
- `TRACT_COHORT_AND_MISSINGNESS.csv`, `MISSING_VALUE_LEDGER.csv`: every exact GEOID and exclusion/missing reason; no hidden four-geometry filter.
- `SVI_COMPOSITE_SOURCE_COMPARISON.csv`: earlier harmonization results reproduced, frozen Q groups not changed.
- `SOURCE_HASH_VERIFICATION.csv`, `FROZEN_REALIZATION_VERIFICATION.csv`, `INDEPENDENT_THREE_POLICY_ARCHIVE_VERIFICATION.csv`: actual payload provenance, not LFS pointer-only checks.
- `PRESERVATION_BEFORE.json` and `PRESERVATION_AFTER.json`: identical protected universe of 950 prior files.

## Reproduction

Python 3.12.3; isolated statistical dependencies are pinned in `requirements-audit.txt`, not installed or changed automatically. Get Git LFS payloads. Main Git baseline and separate heating-package commit are fixed in `AUDIT_SPECIFICATION.json`. Worktree checkout can be sparse; `--cache-root` searches additional actual-source checkouts or the shared LFS object store and admits only committed hashes (text CRLF-only equivalence explicitly recorded).

From this directory:

```powershell
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python audit.py --source-root 'PATH_TO_AUTHORITATIVE_FROZEN_ARCHIVE' --cache-root 'PATH_TO_HEATING_COMMIT_CHECKOUT' --comments 'PATH_TO_ORIGINAL_COMMENTS_DOCX'
python write_reports.py
python verify_independently.py --source-root 'PATH_TO_AUTHORITATIVE_FROZEN_ARCHIVE'
python validate_package.py
```

Audit.py performs source metric reconstruction and regression diagnostics only, not model simulation. Original comments are optional for numerical reconstruction; report generation expects the retained source quote record if that optional file is not accessible. The source archive must include the frozen offline integral arrays and 1,000 existing event records per policy. Those bulk files are not all Git-tracked: a clean clone alone cannot reproduce their source-level verification. Existing package CSVs allow independent numerical/association tests without that archive. No new raw medical-need data or current-year population is invented.

Independent verification uses separate archive integration/identity code, checks all 3,000 event payloads and reproduces conditional linear R-squared separately. `validate_package.py` runs package-only compileall (Windows extended paths where needed), pytest and a changed-path scope check, then records the commands and derived payload hashes. The tests check cohort identity, missingness, exact recovery identities, source comparisons, censoring semantics, no clustering imports and protected hashes. The source comments document is not copied into this package.

Distributions use valid individual values on the declared 2,291 residential cohort; primary and extended correlation matrices both use the same complete 2,291 GEOIDs. Zero/near-zero fraction and |z|>3 flags are descriptive only. Non-estimable construct-level exclusions have blank numeric statistics rather than invented zero values. An infinite VIF in the deliberately included arithmetic identity block is expected, not a model defect. Source qualification and construct admission are different decisions.
""")
    write('PRIMARY_SOURCE_DOCUMENTATION.md',"""
# Source documentation and access boundaries

Actual input bytes, Git/LFS payload identities and source commits are listed in `SOURCE_HASH_VERIFICATION.csv`. Records explicitly distinguish actual committed bytes, Git text CRLF-only equivalence, frozen local archive/manifest checks and local metadata not tracked by Git. No LFS pointer is accepted as a numeric source.

| Source | Primary provider record | Verification and limitation |
|---|---|---|
| CGS MS48 ground motion | https://www.conservation.ca.gov/cgs/Pages/Publications/MS48.aspx | Official page inspected in this task. Archived official download equality, original grid bytes and 92 frozen station values checked. No new PGA interpolation. |
| FEMA NRI v1.19 March 2023 | https://www.fema.gov/sites/default/files/documents/fema_national-risk-index-data-version-and-update-documentation.pdf | Actual Mar-23 source rows and existing source/harmonization reports verified. Live full-PDF fetch was unavailable in this task; source vintage/CDC lineage use the previously inspected official documentation, not a claimed new PDF reread. |
| CDC/ATSDR SVI 2022 | https://www.atsdr.cdc.gov/place-health/media/pdfs/2024/10/SVI2022Documentation.pdf | Official documentation opened; California table actual rows checked, -999 retained as missing, overall and local theme mean distinguished. |
| ACS B25040 2018-2022 | https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/B25040_06.csv.zip | Actual official numeric archive payload hash verified at f321517; prior estimate/replicate/MOE numerical QA reused. Prior API HTTP-200 Missing Key HTML was not a numeric measurement source. |
| ACS variance replicates | https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/documentation/5-year/2018-2022_Variance_Replicate_Table_Documentation.pdf | Actual provider document bytes verified; prior correlated ratio-MOE computation used, not independent numerator/denominator MOE propagation. |
| ASCE 41-17 BSE-2E distinction | https://www.fema.gov/sites/default/files/2020-08/fema_seismic-eval-older-concrete-buildings_p-2018.pdf | FEMA P-2018 indexed Section 3.3 primary-source passage accessible; full PDF open failed. This distinction is documentation evidence, not a new building-code calculation. |
| Frozen formal population | Data/Tracts_Within_Expanded_Area.csv and frozen formal metadata | Actual bytes and values agree on all 2315 GEOIDs. Existing decision calls them 2020-based, but direct original Census release/batch was not authenticated. Do not claim that gap resolved, or substitute NRI/CDC/new Census values. |

The source-age differences (SVI2020, ACS2018-2022, CGS2025/NSHM2023, frozen population) are recorded, not harmonized by changing data. A common tract identifier does not imply common measurement year. Original reviewer comments were read from a local document and quoted with its SHA256; no manuscript/comment file is republished. Current access restrictions and archive availability are distinct from numerical missingness.
""")
    assert set(PRIMARY)==set(row['variable_name'] for row in rows if row['recommendation']=='PRIMARY')
    print('REPORTS_COMPLETE',len(rows),'candidate rows; primary=7; no fitted weighted matrix')


if __name__=='__main__':
    main()
