"""Evidence-bounded eight-coordinate recommendation; draft only, never promotion."""
from common import *


def main():
    s=source_reader();d=frame('VERIFIED_EIGHT_VARIABLE_COHORT.csv','tract_id')
    k=frame('EIGHT_VARIABLE_K_EVIDENCE.csv');h=k.loc[k.specification.eq('H2')].set_index('k')
    info=frame('EIGHTH_COORDINATE_INCREMENTAL_INFORMATION.csv').set_index('variable').loc['RPL_CBM']
    effective=json.loads(lp(OUT/'EFFECTIVE_LOCAL_HAZARD_CONTENT.json').read_text())
    prism=json.loads(lp(OUT/'EPA_PRISM_SOURCE_AND_COVERAGE_QA.json').read_text())
    physical=json.loads(lp(s.source(MH+'PHYSICAL_COMPOSITE_ADMISSION_DECISION.json',AUTH)).read_text())
    acq=json.loads(lp(OUT/'OFFICIAL_SOURCE_ACQUISITION.json').read_text())['records']
    source_table='\n'.join(f"| {r['name']} | {r['status']} | {r.get('http_status','-')} | [{r['requested_url']}]({r['requested_url']}) |" for r in acq)
    md('EIGHTH_COORDINATE_SOURCE_SEARCH.md',f'''# Focused source search

Authority: `{AUTH}`. Review date: 2026-10-12 (America/Los_Angeles); acquisition records also preserve actual UTC timestamps.
The design objective is eight variables; P2 is only the seven-variable ablation.
Search was restricted to a coherent hazard-only or standalone climate measure. No variables were ranked by desired cluster labels.

The strongest **verified full-cohort** choice remains CDC EJI 2024 `RPL_CBM`. This is a bounded finding, not proof that no better product exists.

- NASA/SEDAC's 2005 Global Multihazard Frequency and Distribution is a genuine alternative: sum of six single-hazard deciles on a 2.5-arcminute grid. Its modern catalog was found at `C3550190541-ESDIS`; the old `C179001784-SEDAC` returns an empty catalog. The migrated actual ZIP redirects to NASA Earthdata authentication and returns HTTP 401 in the fully recorded final attempt; no raster was obtained. The DOI landing page is not a data payload. Coverage, NoData/zero distinctions, local component contributions and population/GDP ancillary-field separation remain unverified. Metadata alone cannot admit it. No false 2,299 coverage claim is made. It also omits wildfire and heat and uses early source periods; age alone is not its exclusion reason. This access limitation does not establish that the product is intrinsically scientifically unsuitable.
- EPA PRISM Scaled Dataset, DOI `10.23719/1519307`, was actually acquired with its field dictionary. `Hazard_Exp=1+Proport_Exp` exactly in all {prism['national_records']:,} records; the latter is land-area proportional exposure, not property loss. Only {prism['identifier_matches']:,}/2,299 IDs match, with {prism['unmatched']} missing ({prism['unmatched_population']:,} frozen residents); only {prism['retained_special_use_matches']}/8 special-use positive-population IDs match. Even matching IDs do not verify unchanged 2015/2020 boundaries. The workbook does not expose individual hazard flags, and the published PRISM approach also treats technological hazards; a natural-only aggregate cannot be certified from this table. No crosswalk/imputation is used.
- NOAA NCEI's combined disaster-risk viewer builds on FEMA NRI. The source distinguishes hazard, exposure, vulnerability and resilience. Separate hazard layers are not automatically an independently verified multi-hazard scalar. No unknown combined-map formula was invented, and social layers were not assumed to contaminate every separately displayed field.
- FEMA NRI annualized-frequency fields can exclude asset/social adjustments, but different hazards have different event/event-day/probability units and minimum-frequency/support rules. No official universal frequency-sum score was verified. Its Risk and EAL scores mix different constructs and are not admissible replacements.
- California VCP publishes separate climate-hazard and social-vulnerability data. Its combined vulnerability output intersects both; no ready-made full-cohort hazard-only scalar was verified. CalEnviroScreen's overall product includes population characteristics; its pollution-only component is not a selected-natural-hazard index. Current live versions were not substituted into frozen 2024 data.
- USGS/CGS physical products are defensible individual layers, but neither a landslide layer nor a seismic scenario alone meets the multiple-hazard objective. The previous four-layer physical proposal has only {physical['joint_complete_physical_n']} complete tracts; no 267-tract exclusion or missing-to-zero fill is allowed.
- Peer-reviewed PRISM and NaHRSI were considered. NaHRSI includes governance/societal/built/natural-system resilience at county scale; no county value is broadcast as tract physical hazard. PRISM's natural-only exposure interpretation is promising but full-cohort source support fails here.

## Acquisition ledger

Original response bytes, workbook and dictionary are in `sources/`, with actual SHA256, final URLs and timestamps in `OFFICIAL_SOURCE_ACQUISITION.json` and `.csv`. Original bytes are unedited; the review label is in the ledger. Error responses are archived and explicitly distinguished from data. Two earlier same-task NASA response attachments have incomplete original attempt histories, explicitly recorded in `EARLIER_SOURCE_RESPONSE_ATTACHMENTS.json`; neither is an admitted raster measurement, and the migrated ZIP's final authentication response was separately acquired with complete provenance. Web-tool cached primary-source pages also informed construct screening where live full-text retrieval was blocked; those are not claimed to be hashed complete publications. No provider was contacted.

| Source | Result | HTTP | Original URL |
|---|---|---:|---|
{source_table}

Detailed formulas/limitations are in `HAZARD_ONLY_CANDIDATE_COMPARISON.csv`. All unsupported formulas or coverage are explicitly unresolved. No alternative K-means matrix was fabricated.
''')
    candidates=[
      dict(candidate='CDC EJI 2024 standalone RPL_CBM',formula='National minimum percentile rank of sum of nine published indicator percentile ranks; sum then rank; not equal domain weights',hazards='Heat; wildfire smoke/burned area; coastal/riverine flood; drought; hurricane; strong wind; tornado',geography='2020 census tract',valid_2299=2299,missing_2299=0,direct_social_adjustment=False,direct_asset_adjustment=False,population_in_score=False,
           zero_semantics='F_NEHD/SMOKE/BURN absent; burn-zero and hurricane source-zero limitations disclosed',decision='LEADING_QUALIFIED_EIGHTH_COORDINATE',source='https://www.atsdr.cdc.gov/place-health/php/eji/eji-indicators-climate-burden-module.html',incremental_information='Full-cohort conditional R2/VIF/CV verified'),
      dict(candidate='NASA SEDAC Global Multihazard Frequency and Distribution v1',formula='Sum of single-hazard decile values; no verified payload-level formula/mask details',hazards='Cyclone; drought; earthquake; flood; landslide; volcano',geography='2.5 arcminute global grid (~4 km)',valid_2299=None,missing_2299=None,direct_social_adjustment='Not in stated hazard sum; ancillary population/GDP fields require payload separation',direct_asset_adjustment='Not in stated sum; not certified from absent payload',population_in_score='Unresolved masking/ancillary usage',zero_semantics='Actual NoData and zero semantics unverified; migrated ZIP Earthdata authentication HTTP401',decision='NOT_ADMITTED_SOURCE_PAYLOAD_UNAVAILABLE',source='https://doi.org/10.7927/H45718Z5',incremental_information='Cannot calculate without actual raster; not represented by a proxy'),
      dict(candidate='EPA PRISM Scaled Proport_Exp / Hazard_Exp',formula='Hazard_Exp=1+Proport_Exp (verified all rows); proportional land area coinciding with multi-hazard layer; exact component aggregation unresolved',hazards='2015 PRISM historical/proximity hazards; natural-only subset not exposed in workbook; methodology also has technological sources',geography='2015 census tract; same GEOID not same-boundary proof',valid_2299=prism['identifier_matches'],missing_2299=prism['unmatched'],direct_social_adjustment='Not directly in these exposure fields',direct_asset_adjustment='No; separate Prop_Val/risk fields not used',population_in_score=False,zero_semantics='Aggregate table lacks per-hazard observed-zero vs missing flags',decision='NOT_ADMITTED_INCOMPLETE_AND_GEOGRAPHY_UNVERIFIED',source='https://doi.org/10.23719/1519307',incremental_information='Descriptive incomplete-cohort associations only; no comparison fit'),
      dict(candidate='NOAA NCEI combined hazard/risk viewer',formula='No source-verified independent hazard-only composite formula obtained; combines selectable FEMA-based outputs',hazards='Weather/climate disaster families',geography='Tract/county; contemporary identity not verified',valid_2299=None,missing_2299=None,direct_social_adjustment='Combined risk can include vulnerability/resilience; separate layers need exact selector audit',direct_asset_adjustment='FEMA EAL-based fields embed consequences/exposure',population_in_score='Depends on chosen field; not certified',zero_semantics='Underlying NRI support/minimum-frequency rules',decision='NOT_ADMITTED_NO_VERIFIED_HAZARD_ONLY_SCALAR',source='https://www.ncei.noaa.gov/news/billion-dollar-disasters-mapping-vulnerabilities-census-tract-level-data',incremental_information='No matrix constructed'),
      dict(candidate='FEMA NRI v1.19 annualized frequency component fields',formula='Recorded events or event-days / record length, or probabilistic annual occurrence; not one common-unit composite',hazards='18 separately documented natural hazards',geography='Tract with hazard-specific source support',valid_2299=None,missing_2299=None,direct_social_adjustment=False,direct_asset_adjustment=False,population_in_score=False,zero_semantics='Hazard-specific excluded/null/physical-zero and minimum-frequency rules; no blanket zero fill',decision='COMPONENTS_ONLY_NO_EXISTING_COHERENT_SCALAR',source='https://hazards.fema.gov/nri/data-resources',incremental_information='Full index not constructed to fill required slot'),
      dict(candidate='California VCP combined vulnerability / standalone hazard layers',formula='Combined vulnerability intersects climate hazard and social vulnerability; separate scalar across hazard layers not verified',hazards='Heat; wildfire; flood; sea-level rise; drought',geography='California tract/blockgroup; five separate hazard families',valid_2299=None,missing_2299=None,direct_social_adjustment='Yes combined product; no automatically in separate hazard layers',direct_asset_adjustment='Not established for unspecified selector',population_in_score='Not established for unspecified selector',zero_semantics='Per-layer rules; no complete aggregate obtained',decision='INDIVIDUAL_LAYERS_NOT_VERIFIED_REPLACEMENT',source='https://lci.ca.gov/climate/icarp/vulnerable-communities/',incremental_information='No unregistered layer averaging'),
      dict(candidate='CalEnviroScreen overall / pollution burden',formula='Overall pollution burden times population characteristics; pollution-only component represents pollutants/environmental effects',hazards='Primarily pollution not selected natural-hazard frequency/intensity',geography='California census tracts',valid_2299=None,missing_2299=None,direct_social_adjustment='Yes overall; not directly in standalone pollution burden',direct_asset_adjustment='Not the relevant gate',population_in_score='Population characteristics in overall score',zero_semantics='Indicator-specific data gaps',decision='EXCLUDE_CONSTRUCT_MISMATCH',source='https://oehha.ca.gov/calenviroscreen/model-scoring',incremental_information='Not compared to frozen community inputs'),
      dict(candidate='USGS/CGS individual physical hazards / audited four-layer proposal',formula='Separate seismic PGA, fire severity area, SFHA area, historical heat; no approved full-cohort normalization/composite',hazards='Earthquake; fire; flood; heat (or individual landslide layer)',geography='Audited tract summaries with source-support masks',valid_2299=physical['joint_complete_physical_n'],missing_2299=2299-physical['joint_complete_physical_n'],direct_social_adjustment=False,direct_asset_adjustment=False,population_in_score=False,zero_semantics='Explicit missing support, not zero',decision='NOT_ADMITTED_INCOMPLETE_PHYSICAL_COMPOSITE',source='https://www.usgs.gov/tools/us-landslide-inventory-and-susceptibility-map',incremental_information='Prior physical support audit retained; no composite/fit'),
      dict(candidate='EPA NaHRSI / USGS multiobjective risk framework',formula='Resilience/governance/system or asset/planning-preference framework, not verified tract hazard-only scalar',hazards='Multiple natural hazards plus resilience/organizational exposure',geography='County or organizational assets, not verified 2020 tract index',valid_2299=None,missing_2299=None,direct_social_adjustment='Yes resilience framework; USGS framework context-specific',direct_asset_adjustment='Framework-specific',population_in_score='Framework-specific',zero_semantics='No source-certified tract field',decision='EXCLUDE_SCALE_AND_CONSTRUCT_MISMATCH',source='https://pmc.ncbi.nlm.nih.gov/articles/PMC7007161/',incremental_information='Not used as fitted coordinate'),
    ]
    save('HAZARD_ONLY_CANDIDATE_COMPARISON.csv',candidates)
    md('CDC_CBM_VS_ALTERNATIVES.md',f'''# Decision on the eighth coordinate

**Use official CDC EJI 2024 standalone `RPL_CBM` as the qualified eighth coordinate.**
Retain the published-as-is H2 values and budgets; seven-variable P2 is the ablation, not the intended primary model.

The search found two credible hazard-only exposure alternatives, not just contaminated risk scores. NASA NDH includes seismic and nonseismic hazards but its actual raster was unavailable after migrated official metadata/link retrieval. EPA PRISM exposure was acquired and tested, but {prism['unmatched']} current cohort IDs are absent and matched IDs are not boundary-verified. Neither can honestly displace the complete CDC published ranking in this task. The previous physical composite is incomplete for 267 tracts. No missing or new crosswalk values are invented.

CBM is **selected climate-hazard burden**, not comprehensive natural-hazard risk or modeled multi-hazard restoration. Seismic context is already explicit in earthquake-conditioned RQ1/RQ2. Direct demographic, SOVI, asset and resilience adjustment is absent from the standalone CBM formula; statistical/geographic independence is not implied. Combined `RPL_EJI_CBM`, FEMA Risk/EAL and asset fields are excluded.

All 2,299 published CBM ranks are valid, but rank completeness is not complete physical-observation support. F_NEHD/F_SMOKE/F_BURN are unavailable; 2,251 burned-area zeros are unresolved; 13 national heat interpolations are unidentified; all study hurricane flags indicate source-null/excluded-to-zero; drought unit wording conflicts with source values. **Published-as-is experimental use is author-authorized, not clean physical-hazard certification.**

Local content is unbalanced: riverine support explains {effective['riverine_binary_published_rank_R2']:.2%} of rank variance. Heat, wildfire and coastal-flood content still contribute and vary within riverine strata; `RPL_CBM` is not literally a flood-only binary. It must not be described as nine equally informative local hazards. See the exact hazard participation diagnostics and leaveout ranks/labels.
''')
    ktable=h.loc[[3,4,5],['mean_silhouette','seed_min_ARI','geographic_min_ARI','policy_LOO_min_ARI','policy_LOO_mean_ARI','smallest_seed42_class']].to_markdown()
    md('SEVEN_VS_EIGHT_ABLATION.md',f'''# Seven-versus-eight ablation

The primary design candidate is H2-CBM; P2 is the seven-variable ablation. H1 is weighting sensitivity.
Main fits K1-8/seeds42-46, four geographic quadrants and policy perturbations are reused exactly at `{AUTH}`. No unrestricted search or primary refit occurred.

H2 preserves SOVI's 1/6 budget, halves population's budget from 1/6 to 1/12, and adds CBM at 1/12. Consequently P2-to-H2 is **not pure feature addition**. Exact fixed-pair distance algebra separates added hazard and removed population contributions. Average contributions cancel because both are standardized, not because individual distances/memberships are unchanged. The fixed-partition BSS decomposition is separately retained.

H2-to-P2 mean ARI is about 0.906 at K3 and 0.934 at K4; Hungarian-displayed reassigned population is about 2.37% and 1.66%. At K5 the P2 seed solutions themselves compete, so larger changes are not solely a CBM effect. H1 alters SOVI as well as population budgets and changes more assignments at K3/4. Cross-space Silhouette is not a common out-of-sample physical-quality score.

## H2 quantitative evidence

{ktable}

K4 is the **leading detailed author-review candidate**, not a promoted final selection: it is the K1-8 chord-bend candidate and nearly ties K5 mean Silhouette while being more seed-consistent and less subdivided. K3 is the defensible parsimonious alternative, with stronger worst-case geographic agreement but a mixed logistics group whose seed42 mean silhouette is only about 0.004 (47.8% negative). K5 adds a 219-tract high-spectral-impact subtype at seed42, a real structural interpretation, but mean silhouette improves only {h.loc[5,'mean_silhouette']-h.loc[4,'mean_silhouette']:.6f}; it does not produce a clear new climate-context community class. Policy robustness is mixed, not categorically better for K4: K5 has higher average LOO agreement but a slightly lower worst case. No composite ranking score is used.

The H2 Elbow is smooth, not sharp. K1-6 and K1-7 chord bends support K3; K1-8 supports K4. Mean Silhouette peaks at K5, with overlapping K4/5 seed ranges. K2 is too coarse for the distinct burden/constraint patterns; K6-8 lose much Silhouette and can isolate very-low-population classes. No K is selected because of the number of RQs.

K4/5 retain 38 tracts containing all 34 frozen STATION Q-linked tracts. Their mean Init is about 1.731%, not strong resilience; Init supplies about 80.1% of their centroid separation. The registered minus-Init sensitivity redistributes RQ1 weights and dissolves this rare class. It is a source-proxy/model-initial-condition exception, not an institutional-tract artifact: this 38-class contains no <=100-resident or zero-housing tract. Separate fixed-budget algebra preserves the deletion/reallocation distinction.
''')
    md('EIGHT_VARIABLE_METHODS_DRAFT.md',f'''# Proposed methods wording - not inserted into the manuscript

A tract-level author-review typology was constructed for the 2,299 study tracts with positive frozen formal population. Three domains describe earthquake-conditioned initial disruption and network dependency (initial modeled service, spectral grid impact and dependency HHI), restoration behavior (unconstrained full-service-deficit hours and the equally weighted mean constrained-minus-unconstrained increment across five predefined priorities), and community context (FEMA NRI v1.19 SOVI, log-transformed frozen population and CDC/ATSDR EJI 2024 standalone Climate Burden Module rank). The five policies are a finite descriptive comparison set, not probabilities of future policy adoption or a physically executed average schedule.

The CDC `RPL_CBM` coordinate ranks selected heat, wildfire and extreme-event indicators nationally; it excludes earthquakes and contains no direct SOVI/demographic, asset-value or community-resilience factor. It contextualizes frozen post-earthquake service recovery and does not simulate climate-induced station failure, actual delivered power or causal hazard interactions. Complete published ranks do not certify complete original physical observations; unresolved source-zero and flag limitations are disclosed with component-removal sensitivity.

Each RQ receives one-third of the squared-distance budget. In H2, the three RQ1 coordinates each receive 1/9; the two RQ2 coordinates each receive 1/6; SOVI receives 1/6 and log population/CBM each receive 1/12. Cohort mean/population-SD standardization is followed by multiplication by square-root budgets. Tracts are equally weighted in K-means, with resident coverage reported separately. These are construct-based design weights, not statistically optimized weights or guaranteed realized separation.

K1-8 inertia and full-cohort K2-8 silhouette were assessed with fixed seeds42-46, n_init50, Lloyd, max_iter500 and tolerance1e-4. Geographic and policy-set perturbations, original-unit profiles, rare initial-state sensitivity, and a seven-variable ablation were considered alongside Elbow/Silhouette. K4 is proposed for detailed author review, with K3/K5 alternatives retained. No formal Stage7 replacement has occurred.
''')
    profiles=frame('EIGHT_VARIABLE_CLUSTER_PROFILES.csv')
    p=profiles.loc[profiles.specification.eq('H2')&profiles.condition.eq('published')&profiles.k.eq(4)].copy()
    # Key only by model-specific class, not floating population_share (source serializations differ below display precision).
    table=p.pivot(index='cluster',columns='variable',values='mean')
    counts=p.drop_duplicates('cluster').set_index('cluster')[['n_tracts','population','population_share']]
    table=counts.join(table[['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','Population','Published_RPL_CBM']])
    table.index=table.index+1;table.index.name='H2_K4_display_class'
    save('H2_K4_ORIGINAL_UNIT_CLASS_MEANS.csv',table.reset_index())
    md('FINAL_EIGHT_VARIABLE_AUTHOR_DECISION.md',f'''# Final eight-variable author-review decision

**RECOMMENDED EIGHTH VARIABLE: CDC/ATSDR EJI 2024 standalone `RPL_CBM`.**

**Recommended specification: H2-CBM, eight coordinates, equal three-RQ budgets. Provisional detailed review resolution: K4; K3 parsimonious and K5 network-detail alternatives remain defensible. No formal promotion.**

## 1. Scientific definition, coverage and alternative search

Use the official nationally ranked sum of nine selected climate-indicator percentiles exactly as published. Hazards are heat; wildfire smoke and burned area; coastal/riverine flooding; drought; hurricane; strong winds; tornado. Earthquakes are excluded but already condition the frozen recovery model. Label the coordinate **selected climate-hazard burden**, not all-natural-hazard risk, expected loss, actual outage exposure or economic damage.

All 2,299 positive-population tracts have finite 0-1 ranks, including all eight zero-housing tracts; only the 16 frozen zero-population tracts remain outside clustering. Frozen population totals 9,066,522. The complete 2,315-tract service domain is untouched.

No independently verified alternative improves both construct and full-cohort support here. NASA NDH is a serious seismic/nonseismic hazard-decile alternative, but its migrated payload requires Earthdata authentication (verified HTTP401), so local support and zero rules are unresolved in this task. EPA PRISM's actual exposure table matches only {prism['identifier_matches']:,} IDs and misses {prism['unmatched']} ({prism['unmatched_population']:,} residents); current boundary identity is also unverified. The prior physical composite covers only {physical['joint_complete_physical_n']} tracts jointly. No missing values are invented or additional tracts removed. This is a bounded source-search conclusion, not a universal claim of best available hazard measurement.

## 2. What actually determines the local hazard coordinate?

Riverine percentile covariance supplies 69.25% of local published sum-score variance; the binary split between positive and zero published riverine-frequency values explains {effective['riverine_binary_published_rank_R2']:.2%} of published rank variance. This binary split does not certify physical absence of flooding. Heat contributes about 12.21%, burned area 8.53%, coastal flooding 8.11%, smoke 1.78%; several other hazards contribute almost no local variation. Positive-covariance participation ratio is {effective['positive_covariance_indicator_participation_ratio']:.3f} at indicator level and {effective['hazard_family_positive_covariance_participation_ratio']:.3f} after grouping smoke/burn and the two flood measures into hazard families. These are descriptive concentration measures, **not counts of independent physical hazards**. Negative/shared covariance is explicitly retained in the source table.

The coordinate is strongly flood-influenced, not nine balanced local hazards, but is not solely one binary field: within-riverine-stratum climate variation and all-indicator/domain leaveouts are reported. Four previously verified major-removal fits are reused; six remaining individual removals and the Extreme Events domain receive narrowly registered H2 K3/4/5 seed42 comparisons. Removing a locally constant hurricane indicator can still change national rerank spacing; any resulting membership change is national calibration/geometry, not local hurricane information.

## 3. Incremental information and weighting

CBM has conditional linear R2={info.conditional_linear_R2:.4f}, VIF={info.VIF:.4f}; fixed random-fivefold nonlinear R2={info.nonlinear_random5fold_R2:.4f} and spatial-block R2={info.nonlinear_spatial15km_5fold_R2:.4f}. Pairwise associations are modest, but this is not causal independence or source-quality validation. It adds a distinct climate-context construct while contributing only about 1.4-2.1% of H2 K3-5 observed between-class separation. Small contribution is not a license to tune its weight upwards.

Keep H2 squared-distance budgets: RQ1 each1/9, RQ2 each1/6, SOVI1/6, log population1/12, CBM1/12. Square roots multiply standardized values. H1 remains sensitivity only. Fixed-distance and fixed-partition algebra separates hazard addition from population-budget reduction; reassignment cannot be attributed entirely to hazard information. Equal domains are defensible declared design budgets, not optimized, not equally realized separation. No weight revision is required to achieve the author's eight-variable design.

## 4. K evidence and action

{ktable}

Mean Silhouette favors K5 ({h.loc[5,'mean_silhouette']:.6f}); K4 ({h.loc[4,'mean_silhouette']:.6f}) is nearly tied, with overlapping seed ranges. Smooth endpoint-sensitive chord bends favor K3 on K1-6/7 and K4 on K1-8. Thus neither statistic establishes a universal optimum. K4 is the proposed **detailed author-review** resolution because it reconciles the full-range bend, near-maximal silhouette, very high seed consistency and interpretable explicit initial-state exception without K5's additional structural split. Geographic/policy agreement remains moderate; K4 is not certified geographically optimal. K3 better supports a simpler regional three-pattern account and has stronger worst-case geographic agreement; K5 adds a meaningful high-spectral-impact subgroup if finer network differentiation is the desired resolution. These trade-offs are explicit author decisions, not three-RQ counting.

H2-to-P2 ARI is approximately0.906 (K3) and0.934 (K4); about2.37% and1.66% resident population is reassigned after display alignment. H2 K4 is seed-stable (minimumARI {h.loc[4,'seed_min_ARI']:.3f}) but geographically moderate (minimum {h.loc[4,'geographic_min_ARI']:.3f}) and policy-set sensitive (LOO minimum {h.loc[4,'policy_LOO_min_ARI']:.3f}, mean {h.loc[4,'policy_LOO_mean_ARI']:.3f}). H2 K5 has somewhat better average policy LOO agreement, not a uniformly worse robustness result. No claims of policy-neutral types are made.

## 5. Original-unit H2 K4 profiles (seed42)

{table.to_markdown(floatfmt='.4f')}

Display IDs are H2/K4-specific, not formal Stage7 IDs; clusters are ordered by mean frozen total burden. Full distributions, counts, original quartile composition and hospital incidence are separate CSVs. Clustering-input profiles are descriptive, not independent validation.

- C1:38 tracts,1.51% residents, elevated relative initial service (~1.731% absolute), lower baseline deficit but high constraint increment. All34 frozen Q-linked tracts are present. Its separation is about80.1% Init; no zero-housing or <=100-resident tract is in this small class. This is a retained Core-source proxy/initial-condition exception, **not electrical resilience**.
- C2:1,228 tracts,55.81% residents, low spectral grid impact and constraint increment, near-regional baseline deficit, SOVI mean78.19 versus cohort mean reported in the profile CSV, and lower local CBM. High SOVI does not mechanically produce high modeled recovery burden.
- C3:440 tracts,19.36% residents, relatively large constraint increment (~6.82 deficit hours) and lower unconstrained burden (~28.37h); SOVI49.41 and CBM0.357. This is a logistics-sensitive pattern, not a quantified causal travel-delay class.
- C4:593 tracts,23.33% residents, larger unconstrained burden (~37.51h), spectral impact (~0.327) and moderate constraint increment (~4.07h), SOVI55.28/CBM0.342. HHI varies less among these class means; no need to force an extreme in every coordinate.

Reference percentile ranges and exact means/medians/P10/P90 are supplied, avoiding unsupported high/low narrative labels. K5 splits an additional high-spectral-impact class (219 tracts,8.39% residents), not a new independent multi-hazard impact mechanism.

## 6. Remaining scientific limitations and approvals

The standalone formula lacks direct social/asset/resilience adjustment, but source-quality gate remains unresolved: missing F_NEHD/F_SMOKE/F_BURN;2,251 burned-area zeros of uncertain physical/source-null provenance;13 unidentified national heat interpolations;hurricane source-null-to-zero;drought units discrepancy. Removing burned area has small membership effects but does not certify those zeros. Mixed source periods, nationally tied ranks and riverine support can dominate local climate geography. Independent CAL FIRE/NFHL comparison is partial and construct-dependent; the archived CDC heat measure is same-source, not independent validation.

Vulnerability-first uses frozen Q4 in the ensemble's priority construction. Prior evidence shows procedural SOVI dependence despite modest marginal correlations; these RQ domains are not independent causal mechanisms. Geographic tests use four coarse leave-out quadrants and seed42; policy perturbations use seed42. No formal uncertainty intervals or clean-clone raw-archive reproducibility are inferred from these diagnostics. Full physical-source preservation needs the manifest-bound local archive absent from clean Git clones; published matrices and fits can be independently verified from committed LFS payloads.

Author must approve: (1) the **climate-hazard context**, not comprehensive hazard-risk, interpretation; (2) published-as-is source-limit acceptance; (3)H2 domain/internal budgets; (4)K4 detailed review versus K3 parsimonious/K5 structural-detail resolution; (5) separate formal Stage7 promotion. The seven-variable P2 is now ablation only. No model, frozen simulation, quartile, manuscript or numbered figure changed, and no CDC/provider email was sent.
''')
    md('README.md',f'''# Eight-variable author-review candidate

Primary: H2-CBM with official `RPL_CBM`; P2 is ablation. Provisional detailed review K4, with K3/K5 evidence retained. No formal promotion.

Entry report: `FINAL_EIGHT_VARIABLE_AUTHOR_DECISION.md`. Source search: `EIGHTH_COORDINATE_SOURCE_SEARCH.md`. CSV tables have the review-status column; numerical NPZ arrays are identified by the labeled registration and hash ledger. Original fetched bytes retain their original content with labeled provenance ledger.

## Reproduction (Python3.12)

From this package: `python prepare.py`, `python acquire_search_sources.py`, `python analyze.py`, `python reports.py`, `python figures.py`, `python verify_independent.py`.
All writes are package-scoped. Source payloads must match `{AUTH}` and need Git LFS. `prepare.py`/preservation checks additionally require the manifest-bound original frozen archive at `LA_GRID_FROZEN_SOURCE_ROOT` (see `common.py`). No frozen damage/schedule/recovery calculation runs. Prior fit labels/matrices are reused; only narrowly registered researcher component leaveouts are fitted. Source fetches use original URLs, preserve hashes and log access failures; if official sources move, retain the archived bytes rather than silently replace them.

`verify_remote_delivery.py` runs after push and hashes actual remote LFS bytes. The final proof is a separate provenance-only commit. Figure rebuilding uses commit-bound prior geometry and does not regenerate model results; no old four-tract geometry exclusions apply.

Registered component fits retain `tol=1e-4`. Returned model-center inertia and final-membership centroid WCSS are separately stored where early tolerance stopping produces a small difference; labels, parameters and initializations are not adjusted to remove it.

Main tables: candidate comparison, incremental information, K evidence, full original-unit profiles, hazard component sensitivity, geographic/policy stability. Source quality remains unresolved; numerical QA is not scientific certification.
''')
    save('SOURCE_HASH_VERIFICATION_REPORTS.csv',s.records)
    print('Eight-variable decision written; H2-CBM recommended, K4 provisional review only',flush=True)


if __name__=='__main__': main()
