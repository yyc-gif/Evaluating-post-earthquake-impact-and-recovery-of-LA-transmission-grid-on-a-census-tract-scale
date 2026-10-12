"""Source-bounded interpretation of the completed registered diagnostics."""
import json
from importlib.metadata import version

import numpy as np
import pandas as pd

from common import COMMIT, OUT, SPEC, cohorts, dump, frame, lp, save, sha, source_verifier


def write(name,text):
    lp(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')


def table(d,cols=None):
    return d[cols].to_markdown(index=False,floatfmt='.4f') if cols else d.to_markdown(index=False,floatfmt='.4f')


def supplementary_diagnostics(d):
    coordinate_rows=[]
    for cohort,sub in cohorts(d).items():
        membership=frame('CLUSTER_MEMBERSHIPS_'+cohort.upper()+'.csv').set_index('tract_id')
        for spec,budgets in SPEC['specifications'].items():
            columns=list(budgets)
            z=(sub[columns]-sub[columns].mean())/sub[columns].std(ddof=0)
            for k in SPEC['k_values']:
                for seed in SPEC['seeds']:
                    labels=membership[f'{spec}__k{k}__s{seed}']
                    for label in range(k):
                        part=z.loc[labels.eq(label)]
                        separation=len(part)*part.mean().pow(2)*pd.Series(budgets)
                        for c in columns:
                            coordinate_rows.append(dict(cohort=cohort,specification=spec,k=k,seed=seed,
                                diagnostic_cluster=label,n_tracts=len(part),coordinate=c,
                                between_SS=separation[c],fraction_of_cluster_centroid_separation=separation[c]/separation.sum()))
    save('CLUSTER_LEVEL_COORDINATE_SEPARATION.csv',coordinate_rows)
    small=frame('CLUSTER_SIZE_POPULATION_AND_EXTREMES.csv')
    small=small.loc[small.n_tracts.le(50)]
    save('SMALL_CLUSTER_CASE_REGISTER.csv',small)
    positive=cohorts(d)['positive_population']
    tail=positive.loc[positive.BUILDVALUE.ge(positive.BUILDVALUE.quantile(.99))].copy()
    tail['Census_9800_special_land_use_code']=tail.index.str[5:9].astype(int).isin(range(9800,9900))
    save('HIGH_ASSET_TRACT_REGISTER.csv',tail.reset_index())
    spatial=frame('SPATIAL_SUPPORT_AND_BLOCKS.csv').set_index('tract_id')
    q=positive.join(spatial[['block']])
    spatial_rows=[]
    for block,part in q.groupby('block'):
        top=part.index.isin(tail.index)
        spatial_rows.append(dict(block=block,n_tracts=len(part),population_share=part.Population.sum()/positive.Population.sum(),
            asset_share=part.BUILDVALUE.sum()/positive.BUILDVALUE.sum(),asset_P99_tracts=int(top.sum()),
            asset_P99_dollar_share_of_tail=part.loc[top,'BUILDVALUE'].sum()/tail.BUILDVALUE.sum(),
            median_BUILDVALUE=part.BUILDVALUE.median(),mean_SOVI=part.SOVI_SCORE.mean()))
    save('BUILDVALUE_SPATIAL_CONCENTRATION.csv',spatial_rows)
    # Read the fixed W only to describe rare groups' dependency, not to simulate services.
    context=json.loads(lp(OUT/'STARTING_GIT_AND_ENVIRONMENT.json').read_text())
    sources=source_verifier(context['source_root'],context['cache_roots'])
    mapping=pd.read_csv(sources.source('Data/JULY_UTILITY_CONSTRAINED_92.csv',COMMIT),dtype={'tract_id':str,'substation_id':str})
    membership=frame('CLUSTER_MEMBERSHIPS_POSITIVE_POPULATION.csv').set_index('tract_id')
    mapping_rows=[]
    for r in small[(small.cohort=='positive_population')&(small.seed==42)].itertuples():
        ids=membership.index[membership[f'{r.specification}__k{r.k}__s42'].eq(r.diagnostic_cluster)]
        selected=mapping[mapping.tract_id.isin(ids)]
        for station,part in selected.groupby('substation_id'):
            mapping_rows.append(dict(specification=r.specification,k=r.k,diagnostic_cluster=r.diagnostic_cluster,
                n_tracts=len(ids),substation_id=station,mean_dependency_weight=part.weight.sum()/len(ids),
                dependent_tract_count=part.tract_id.nunique()))
    save('SMALL_CLUSTER_DEPENDENCY_PROFILES.csv',mapping_rows)


def main():
    d=frame('TRACT_FEATURES_VERIFIED_2315.csv').set_index('tract_id')
    qa=json.loads(lp(OUT/'COHORT_SOURCE_QA.json').read_text())
    supplementary_diagnostics(d)
    positive=cohorts(d)['positive_population']
    extra=frame('ADDITIONAL_POSITIVE_POPULATION_TRACTS.csv')
    stats=frame('FEATURE_ORIGINAL_UNIT_DISTRIBUTIONS.csv')
    stats=stats[stats.cohort=='positive_population'].set_index('variable')
    info=frame('BUILDVALUE_INCREMENTAL_INFORMATION.csv')
    primary_info=info[info.cohort=='positive_population']
    condition=primary_info[primary_info.kind=='conditional_all_other_primary'].iloc[0]
    associations=primary_info[primary_info.kind=='pairwise']
    leverage=frame('INIT_SUPPLY_DISTANCE_LEVERAGE.csv')
    lev=leverage[(leverage.cohort=='positive_population')&(leverage.subset=='Init_P99')].iloc[0]
    contributions=frame('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv')
    cont=contributions[(contributions.cohort=='positive_population')&(contributions.k==4)&(contributions.seed==42)]
    clusters=frame('CLUSTER_SIZE_POPULATION_AND_EXTREMES.csv')
    shown=clusters[(clusters.cohort=='positive_population')&(clusters.k==4)&(clusters.seed==42)]
    comparisons=frame('CLUSTER_MEMBERSHIP_COMPARISONS.csv')
    comparisons=comparisons[comparisons.cohort=='positive_population']
    k4=comparisons[comparisons.k==4].groupby(['specification_a','specification_b']).agg(ARI_median=('ARI','median'),changed_median=('changed_count','median')).reset_index()
    stability=frame('SPATIAL_AND_SEED_STABILITY.csv')
    stable_summary=stability[stability.cohort=='positive_population'].groupby(['specification','k','kind']).ARI.agg(['min','median','max']).reset_index()
    cohort=frame('COHORT_SENSITIVITY.csv').groupby(['specification','k']).ARI.agg(['min','median','max']).reset_index()
    tiny=frame('SMALL_CLUSTER_CASE_REGISTER.csv')
    tiny=tiny[(tiny.cohort=='positive_population')&(tiny.seed==42)]
    separation=frame('CLUSTER_LEVEL_COORDINATE_SEPARATION.csv')
    separation=separation[(separation.cohort=='positive_population')&(separation.specification=='A')&
        (separation.k==4)&(separation.seed==42)&(separation.diagnostic_cluster==0)]
    init_fraction=separation.set_index('coordinate').loc['Init_Supply','fraction_of_cluster_centroid_separation']
    source_url='https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf'
    census_url='https://www2.census.gov/geo/pdfs/partnerships/psap/G-650.pdf'
    write('POSITIVE_POPULATION_COHORT_AUDIT.md',f'''
# Positive-population cohort audit

**AUTHOR REVIEW - NOT FORMAL STAGE 7.** Eligibility is independently derived from the frozen formal population: `Population > 0`. Full domain: **{qa['full_domain']}**; positive-population primary: **{qa['positive_population']}**; excluded zero population: **{qa['zero_population']}**. The secondary residential rule additionally requires archived `housing_total > 0`, giving **{qa['residential']}**. The eight added tracts contain **{qa['additional_population']:,} frozen residents** ({qa['additional_population']/positive.Population.sum():.3%} of full positive population). All eight proposed coordinates are complete; no imputation, generic complete-case deletion, old CORE3 geometry exclusion or population substitution.

## Exact exclusions

{', '.join(qa['excluded_zero_population_GEOIDs'])}.

Every eleven-digit identity and reason is retained in `TRACT_COHORT_AND_EXCLUSIONS.csv`. The old four CORE3 geometry exclusions are all retained. The full 2,315 service/distributional domain and existing vulnerability quartiles are untouched.

## Added tracts, in actual units

{table(extra,['tract_id','Population','housing_total','BUILDVALUE','Init_Supply','B_480_hr','CDC2022_E_TOTPOP','CDC2022_EP_GROUPQ'])}

Seven have CDC 2022 group-quarters share 100%; 06037980023 has zero CDC 2022 population and unavailable group-quarters share, but **47 frozen formal residents**. CDC missing marker -999 is retained as missing, never zero. The CDC values are descriptive source evidence, not replacements for formal population or a complete authentication of institution types. The exact named institutions have not been verified, so no prison/university/hospital label is invented.

Five added records belong to the 9800-series special-land-use numbering range. The [Census tract reference]({census_url}) defines this range for special uses with little or no population/housing; it does not identify the precise local use. The added population count therefore improves represented scope, while log population has genuine low-end leverage: minimum cohort-standardized log population is about -13.11.

## Cohort sensitivity is k-dependent

{table(cohort)}

At k=4, common-tract ARI is about 0.95 for A and 0.98 for B (median over five matched seeds). At k=6, A falls to about 0.47 and is also seed-sensitive. A and A-minus-Init at seed42/k6 isolate **12 low-population tracts**, five from the added cohort, with median population 43.5. They are valid observations but a tiny exposure-defined class, not proof of a new universal community type. B halves the population budget and does not form that 12-tract cluster in these registered fits. This comparison changes features and budgets together.

Representation improves without an added-only cluster at k3-5. It is **not** valid to claim the eight records never influence clustering or that k6 is universally robust. Keep all positive-population records and disclose these sensitivities instead of deleting them to improve the fit.

## Spatial support

All 2,315 frozen TIGER internal points are finite, and all archived WKT polygons are nonempty/valid. Spatial perturbations use those internal points on a common UTM11N support; no area/land mask or old built-environment geometry admission is needed. A leave-quadrant-out fit tests geographic training composition, not polygon uncertainty or formal prediction validation.
''')
    bv=stats.loc['BUILDVALUE']
    write('POPULATION_AND_BUILDVALUE_SOURCE_QA.md',f'''
# Frozen population and building-asset source QA

**AUTHOR REVIEW - NOT FORMAL STAGE 7.** Baseline commit: `{COMMIT}`. Actual Git LFS source bytes, not pointer text, are checked in `SOURCE_HASH_VERIFICATION.csv` and the independent source record.

## Population authority

`Data/Tracts_Within_Expanded_Area.csv::population` matches the formal metadata and prior audit on all 2,315 exact GEOIDs. It is the only population used for eligibility and `log1p(Population)`. The existing harmonization report calls it 2020-based, but its direct upstream Census release/batch remains **unresolved**. Frozen numerical identity is verified; external vintage is not newly authenticated. NRI/Hazus population and CDC 2022 population are not substituted. Density remains the existing CDC 2022 `E_TOTPOP / AREA_SQMI` (persons/square mile), a different denominator/vintage and descriptive only.

## Exact BUILDVALUE identity and units

`Data/NRI_Table_CensusTracts_California.csv::BUILDVALUE`, NRI v1.19, March 2023 (`NRI_VER=Mar-23`, 9,106 archived California rows), exactly joins every study GEOID. It is **total building exposure stock in 2022 USD**, using **Hazus 6.0 2022 valuations on 2020 Census support**. The archived version-specific FEMA Technical Documentation, printed p.5-9 (PDF index68), states this lineage; [official FEMA document retained by Ohio EMA]({source_url}). The verified local PDF and page text are used because a current web fetch rejected the 23MB PDF. Current v1.20 documentation was not substituted.

This field is not electricity-interruption damage, actual power demand, household income, earthquake damage or another social-vulnerability measure. A larger stock can occur in special-use or employment tracts and can coexist with high SOVI. It is not evidence that residents are wealthy. All NRI values are retained exactly; the frozen SOVI representation differs from full NRI decimals by at most {qa['SOVI_frozen_vs_full_NRI_max_decimal_error']:.3g}, explicitly tolerated below 1e-8 without changing scores or quartiles.

## Distribution and coverage, positive-population cohort

BUILDVALUE valid={int(bv.n)}, missing={int(bv.missing)}, zero={int(bv.zero_count)}. Minimum=${bv.minimum:,.0f}; P10=${bv.p10:,.0f}; P25=${bv.p25:,.0f}; median=${bv['median']:,.0f}; P75=${bv.p75:,.0f}; P90=${bv.p90:,.0f}; maximum=${bv.maximum:,.0f}. Mean=${bv['mean']:,.0f}; population SD=${bv.sd:,.0f}; skewness={bv.skewness:.3f}. Full original and transformed distributions are in `FEATURE_ORIGINAL_UNIT_DISTRIBUTIONS.csv`.

`log1p(BUILDVALUE)` is ln(1 + stock measured in USD), then cohort-standardized, not a locally re-ranked NRI percentile. The highest 23 stocks account for about 6.58% of assets but 1.09% of frozen population. `HIGH_ASSET_TRACT_REGISTER.csv` preserves exact locations/types; two largest are 06037980016 and 06037980035, each above $9 billion. Their SOVI scores are about 73.21 and 83.21: high stock does not imply low vulnerability. Tract-specific land-use identities are not inferred from monetary values alone.

The eight added records span ${extra.BUILDVALUE.min():,.0f} to ${extra.BUILDVALUE.max():,.0f}; zero housing units are not zero economic stock. `BUILDVALUE_SPATIAL_CONCENTRATION.csv` reports the same official-point quadrants, not an unverified neighborhood aggregation.

## Incremental information, not automatic admission

{table(associations,['predictor','pearson','spearman','linear_R2','spline_random_tract_CV_R2'])}

Conditioning on all seven A coordinates, log stock has linear R2={condition.linear_R2:.4f}, VIF={condition.VIF:.4f}, additive-spline five-fold random-tract CV R2={condition.spline_random_tract_CV_R2:.4f}. Thus the added coordinate is not a mechanical duplicate. Nonlinear diagnostics and MI are descriptive; neither establishes causality or spatially independent prediction.

EAL_SCORE, EAL_VALT and ALR_NPCTL appear only in construct diagnostics. EAL mixes hazard, stock and annual modeled consequences; ALR is a distinct normalized loss-propensity construct. The strong stock/EAL association does not turn stock into a power-interruption loss estimate. None of these, nor RISK_SCORE, enters any registered primary fit. No geographic or economic loss validation is claimed.
''')
    init=stats.loc['Init_Supply']
    write('INIT_SUPPLY_ZERO_INFLUENCE.md',f'''
# Initial-supply sensitivity

**AUTHOR REVIEW - NOT FORMAL STAGE 7.** The coordinate is the frozen 2pc50 mean modeled initial tract service state after the existing gate, not observed customer supply and not a new gate calculation.

Exact zeros: **{int(init.zero_count)}/{len(positive)} ({init.zero_fraction:.3%})**. Near-zero absolute <=1e-8 count is the same. Full-cohort median is zero; P75={init.p75:.8f}; P90={init.p90:.8f}; maximum={init.maximum:.8f} (2.45%). Nonzero-only quantiles and moments are retained separately in `FEATURE_ORIGINAL_UNIT_DISTRIBUTIONS.csv`. No zeros are changed, jittered or imputed.

The standardized range is **-0.23671 to 9.73336**. The top 1%, **23 tracts**, contributes **{lev.fraction_of_Init_total_SS:.2%}** of initial-service SS and **{lev.fraction_of_entire_A_total_SS:.2%}** of all A standardized weighted total SS. All nonzero records contribute about 96.26% of this coordinate's SS. Its overall distance budget nevertheless stays 1/9; tail leverage is not an unlimited increase in total budget.

## Rare-state cluster

A/B/B-equal-RQ3 at k4-6 repeatedly retain **34 tracts** with mean initial service **0.018153** and mean B **23.601 h**. At A/k4/seed42, the initial coordinate accounts for **{init_fraction:.2%}** of that cluster centroid's distance from the global centroid; it contributes **22.42%** of all between-cluster SS. All 23 Init-P99 tracts are in this group. None of the eight added zero-housing records is in it, and none is an asset-P99 observation. It is not an institutional/asset-tail artifact.

This is a real difference in the frozen modeled state and is associated with lower cumulative service deficit. But isolating the group is strongly amplified by z scaling. It cannot be called independent confirmation of superior electrical connectivity, a real-life outage class or a robust universal community type. The input-profile relation to B is shared frozen model evidence, not independent validation. `SMALL_CLUSTER_DEPENDENCY_PROFILES.csv` describes fixed W contributions without interpreting them as capacity or rerunning any physics.

## Registered ablation

{table(k4)}

At k4, A versus A-minus-Init median ARI is about 0.18, while B versus B-minus-Init is about 0.66. The 34-tract class disappears in the ablations, but this also raises each remaining RQ1 coordinate from 1/9 to 1/6. Differences therefore cannot be attributed to a pure removal alone. A-minus-Init/k4 assigns roughly 57.8% of separation to grid impact/HHI and only 4.1% to RQ3; dropping Init does not automatically produce a better balanced community typology.

## Recommendation

**Retain Init conditionally in the registered seven/eight-variable reference** if initial disruption is an intended RQ1 construct, and show the minus-Init comparison prominently. Do not drop it simply because its original range is small, or retain it merely because the resulting rare group is seed-stable. There is no scientifically justified transformed/trimmed replacement evaluated here. Author approval is needed on whether a rare favorable initial-service regime deserves its own community type, versus being a descriptive initial-condition indicator. This audit does not choose or promote a formal answer.
''')
    write('SEVEN_VS_EIGHT_VARIABLE_DECISION.md',f'''
# Seven versus eight variables: scientific decision for author review

**AUTHOR REVIEW - NOT FORMAL STAGE 7. No formal specification or k is promoted.** Starting authority `{COMMIT}`. All comparisons hold 2pc50, Impact-first, C57_D1, M1_UTILITY_003, G1_BASELINE_050, 480 h and 1,000 existing realizations fixed. DeltaB is matched Impact-first minus Unconstrained, never a new travel-only or damage simulation. Spectral Grid_Impact is not the population-impact restoration-policy score.

## A. Does BUILDVALUE add useful economic exposure?

**Yes as a separately declared building-asset stock construct; no clear evidence that it should automatically replace A as the primary community-recovery specification.** Log assets has Pearson correlation 0.3602 with log population and -0.3160 with SOVI; all-seven conditional R2={condition.linear_R2:.4f}, VIF={condition.VIF:.4f}. Economic stock is not numerically redundant, and the source is clean, complete and version-specific. It broadens construct coverage beyond people, but its relevance depends on whether RQ3 explicitly concerns assets as well as residents.

At k4/seed42, B separates groups with much greater SOVI/stock contrast: one large group's mean SOVI is 81.46 and median stock $406.6m, another's 38.67 and $619.8m. A has SOVI 77.92/$437.4m versus 49.52/$512.4m. These are input-based descriptions, not independent validation or household wealth/outage-loss findings. B's log-stock coordinate accounts for only 1.95% of separation, while SOVI rises from 10.90% in A to 22.54% in B. The reorganization is not simply an extreme-stock class.

A versus B median ARI at k3/4/5/6 is about 0.874/0.601/0.801/0.480. This is substantively different, not a cosmetic extra column. The change includes both adding assets and splitting population's exposure budget from 1/6 to 1/12. Equal-RQ3 B also reduces SOVI to 1/9 and materially changes k4 membership (B agreement about 0.50). Neither comparison identifies a pure asset-addition causal effect.

Asset-P99 leaveout training then prediction of all tracts yields B ARI 0.966-0.987 across k3-6, and B-minus-Init 0.982-0.989. The highest values are not creating a new tiny asset-only cluster under the registered log budgets. This robustness check is not permission to remove assets or records from the source.

## B. Should Init_Supply remain?

It carries a distinct initial-state RQ1 meaning but is **highly influential and conditional**, not an innocuous coordinate. Zero fraction 66.68%; maximum z 9.73; top 23 records supply 62.48% of its SS. A/B have the same modeled favorable 34-tract group at k4-6, mean initial service 1.8153%, mean deficit 23.601 h. This reflects frozen model differences, with substantial scaling leverage. The minus-Init ablations reorganize the wider typology and reallocate RQ1 weights. Retaining it is defensible only if isolating that rare modeled state serves the stated typology purpose; otherwise authors may choose a separately justified descriptive role. No replacement transform or automatic omission is approved.

## C. Does the 2,299 cohort improve representation?

**Yes.** It adds 16,979 valid frozen residents without feature missingness, and old geometry exclusions are unnecessary. The eight records do not form an added-only group at k3-5. At k6, A and A-minus-Init can isolate 12 special-use low-population tracts, five added, with median 43.5 residents. These are valid exposure extremes, not corrupted rows, but a tiny class is conditional on resolution/weight choices. A's cohort ARI at k6 about 0.47 and seed-pair median about 0.65 warn against a robust k6 claim. Excluding legitimate residents would hide this scope sensitivity. Keep all 2,315 in original service/distributional calculations.

## D. Are the weights defensible?

**As a transparent normative RQ balance, yes; as statistically optimal or guaranteeing equal observed separation, no.** Each domain is exactly 1/3 of total weighted standardized SS and budgets are applied by square roots. Full pairwise/conditional statistics do not show mathematical duplication of the eight proposed coordinates. Shared W/trajectories create mechanistic dependence, distinct from algebraic duplicates.

{table(cont[cont.kind=='domain'],['specification','domain','squared_distance_budget','fraction_of_between'])}

At k4/seed42, RQ3 separation is 13.87% for A, 25.04% for B, 4.07% for A-minus-Init and 23.99% for B-minus-Init. Equal-RQ3 B has only 6.28%. A priori equal input budgets do not equalize how many clusters each construct defines. No evidence licenses outcome-optimized reweighting here. **The proposal needs explicit author acceptance, not automatic numerical revision**; if RQ3 population/vulnerability must be strongly visible, these differences require substantive discussion before choosing a primary fit.

## E. Which candidate is clearest?

**No unconditional winner is established. Keep A as the parsimonious registered reference and B as the economic-exposure extension for review.** A is closest to the prior source-audited RQs without adding an asset-consequence claim; B supplies a defensible distinct stock dimension and often a clearer social/asset contrast. A-minus-Init is not automatically preferred: its k4 solution is highly structural with little RQ3 separation. B-minus-Init also has pronounced spatial k4 sensitivity. The choice depends on the intended role of rare initial states and whether economic asset stock is explicitly within RQ3. Authors must decide these construct priorities before any promotion; do not declare a universally best specification or select k from these profiles.

## Registered evidence and limitations

200 primary/cohort/ablation/weight fits: k3-6, seeds42-46, n_init50, max_iter500, tol1e-4, Lloyd. Seed42/k4 is a predeclared display only. 120 additional tail/spatial stress fits are separate. No silhouette optimization, old label matching, or preferred manuscript narrative is used. Diagnostic D labels are sorted by mean deficit then population, never formal IDs. Input profiles are not independent validation.

{table(stable_summary[stable_summary.k==4])}

Random initialization stability is high at k4 but spatial leave-quadrant-out agreement can be much lower (B-minus-Init k4 as low as~0.24; A-minus-Init~0.25). Internal points give complete common geographic support, but quadrant tests alter training composition and refit scalers; they are not a prediction-validation study or a comprehensive spatial-error model. Within-cluster distributions, profiles and membership comparisons for **every** registered condition are preserved, not only the displayed example.

Remaining limits: direct upstream Census batch for formal population unresolved; NRI stock is 2022 dollars, not observed outage damages; full source event/integral archives are manifest-bound locally but not all Git-tracked; the fixed 2pc50 field is a probabilistic benchmark, not a unique coherent rupture; independent external electricity/customer restoration outcomes are not used as typology validation. Frozen Q1-Q4, hospital-linked outcomes, Gini/gaps, formal curves and formal Stage7 remain unchanged.

## Required author decisions

1. Is economic building stock explicitly part of RQ3, or a descriptive companion to the population/vulnerability typology?
2. Is the rare 34-tract modeled initial-service state a meaningful intended type, or should Init be descriptive with the ablation as a candidate?
3. Accept the all-positive-population scope and disclose special-use low-population leverage, rather than hiding it through residential admission.
4. Accept normative domain budgets and observed unequal separation; any future change requires a new declared comparison, not tuning to preferred labels.
5. Resolve the upstream frozen Census population release without replacing values. No author-approved formal model or k is established here.
''')
    write('README.md','''
# Registered Stage 7 seven/eight-variable exploration

**AUTHOR REVIEW - NOT FORMAL STAGE 7.** Only this isolated package is new. No formal model, parameter, trajectory, manuscript, original figure or previous audit is changed. Author decides the candidate; this is not a new official typology.

Start with `SEVEN_VS_EIGHT_VARIABLE_DECISION.md`, then the cohort, source and initial-service reports. `FEATURE_SPECIFICATIONS_AND_WEIGHTS.json` was written before fitting and fixes both cohorts, all budgets, k3-6, five seeds, n_init50 and the separate tail/spatial stress tests. The eight-variable extension and initial ablations also reallocate internal domain budgets; differences are not pure coordinate-addition/removal effects.

## Reproduction

Python 3.12; versions recorded in `ANALYSIS_EXECUTION.json` and `requirements-diagnostics.txt`. Set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS and MKL_NUM_THREADS to 1 for the registered replay. Run inside this package:

```text
python prepare.py --source-root <frozen-research-worktree> --cache-root <verified-data-worktree>
python analyze.py
python verify_independently.py
python write_reports.py
python make_plots.py
python verify_package.py
```

After `make_plots.py`, inspect all five PDF pages using the publication-size review renders. Only after this visual inspection, set `visual_review_status` in `PDF_RENDER_AND_BOUNDARY_QA.json` to `PASS_ALL_FIVE_PDFS_AT_PUBLICATION_SIZE` before the final package check. This is a manual visual-QA attestation, not an automatic claim. The heatmap color scale is clipped at +/-2 standard deviations for display only; cell annotations retain the actual, unclipped means.

For a deterministic numerical replay, run `python verify_package.py --capture-replay`, rerun `python analyze.py`, then run `python verify_package.py --verify-replay`. The archived replay comparison checks 18 numerical CSVs byte-for-byte; PDF metadata timestamps and elapsed-time records are not expected to be byte-identical.

For a Git/LFS clone containing this and the prior audit, `analyze.py` reproduces statistical diagnostics and exploratory fits directly from `TRACT_FEATURES_VERIFIED_2315.csv`. Source-level `prepare.py` and independent archive rechecks additionally require the original manifest-bound local frozen integral archives, which are not all published in Git. Do not substitute new trajectories. The pinned prior audit's source verifier is reused only for byte verification; no scientific model module is imported.

## Outputs

- `TRACT_COHORT_AND_EXCLUSIONS.csv`: all 2,315 exact identities and explicit admission reasons.
- `CLUSTER_MEMBERSHIPS_*.csv`: all 100 registered diagnostic label columns per cohort.
- `REGISTERED_EXPLORATORY_CLUSTERING.csv`: 200 fit records, no selected winner.
- `CLUSTER_PROFILE_DISTRIBUTIONS.csv`: actual/transformed units, moments, percentiles, extrema for every fit/cluster.
- `DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv`: declared squared-distance budgets and empirical total/within/between SS.
- `CLUSTER_LEVEL_COORDINATE_SEPARATION.csv`: coordinate shares of each cluster centroid's separation.
- `CLUSTER_MEMBERSHIP_COMPARISONS.csv`, transitions and `COHORT_SENSITIVITY.csv`: label-invariant and matched-label comparisons, never selection targets.
- `SPATIAL_AND_SEED_STABILITY.csv`: 400 seed-pair rows plus 120 tail/spatial stress comparisons. `STRESS_TEST_MEMBERSHIPS.csv` preserves all predictions and heldout flags.
- `BUILDVALUE_INCREMENTAL_INFORMATION.csv`, association/VIF files, distributions and source hashes: construct and source audit.
- `INDEPENDENT_QA_RESULTS.json`: independent source projections, 10 full replays, 200 distance checks, 950 protected-file preservation and prior-audit immutability.
- `figures/`: five Matplotlib PDF/PNG diagnostic figures with actual-size review renders; no AI-generated artwork. All k4 illustrations are predeclared display examples, not a chosen formal k.

`B_480_hr` is mean normalized full-service-deficit hours over 480 h under fixed Impact-first/C57_D1/M1/G1 and 1,000 existing realizations. DeltaB is paired constrained-minus-Unconstrained deficit. T80 is descriptive; no mean trajectory is unreached here. BUILDVALUE is 2022 USD building stock, not outage damage. Original vulnerability quartiles and group-level strategy outcomes remain authoritative.
''')
    packages=['numpy','pandas','scipy','scikit-learn','matplotlib','pyproj','shapely','PyMuPDF','tabulate','requests']
    write('requirements-diagnostics.txt','\n'.join(p+'=='+version(p) for p in packages))
    dump('REPORT_SOURCE_AND_DECISION_RECORD.json',dict(
        source_figures_are_diagnostic_only=True,author_approval_required=True,
        BUILDVALUE_conditional_not_automatic_primary=True,Init_conditional_retention=True,
        all_positive_population_recommended=True,no_k_selected=True,no_formal_promotion=True,
        census_special_use_definition_url=census_url,FEMA_v119_definition_url=source_url,
        initial_34_cluster_initial_coordinate_separation_fraction=init_fraction))
    print('Reports and supplementary diagnostic tables written',flush=True)


if __name__=='__main__':main()
