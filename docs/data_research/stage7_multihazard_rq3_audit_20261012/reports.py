"""Author decision reports from audited values, not from fitted cluster quality."""
from common import *


def table(df):return df.to_markdown(index=False,floatfmt='.4g')


def main():
    read=lambda n:pd.read_csv(lp(OUT/n),dtype={'tract_id':str})
    status=json.loads(lp(OUT/'PHYSICAL_COMPOSITE_ADMISSION_DECISION.json').read_text())
    reg=read('PHYSICAL_HAZARD_MEASUREMENT_REGISTER.csv')
    missing=read('TRACT_OVERLAY_AND_MISSINGNESS_QA.csv');nri=json.loads(lp(OUT/'FEMA_NUMERICAL_COMPOSITION_QA.json').read_text())
    info=read('CONDITIONAL_LINEAR_VIF_AND_NONLINEAR_AUDIT.csv');loss=read('HAZARD_EXPECTED_LOSS_CONTRIBUTIONS.csv')
    full=read('FROZEN_P2_AND_COHORT.csv');d=full.loc[full.Population.gt(0)]
    physical=read('PHYSICAL_HAZARD_TRACT_VALUES.csv');point=read('POINT_VERSUS_POLYGON_COMPARISONS.csv')
    weights=dict(P2=dict(zip(P2,[1/9,1/9,1/9,1/6,1/6,1/6,1/6])),
        conditional_eight_equal_RQ3=dict(zip(P2+['H_physical_screening'],[1/9,1/9,1/9,1/6,1/6,1/9,1/9,1/9])),
        conditional_eight_preserve_SOVI=dict(zip(P2+['H_physical_screening'],[1/9,1/9,1/9,1/6,1/6,1/6,1/12,1/12])))
    assert all(np.isclose(sum(w.values()),1) for w in weights.values())
    dump('MULTIHAZARD_CANDIDATE_DEFINITIONS_AND_WEIGHTS.json',dict(squared_distance_budgets=weights,
        preregistration='CONDITIONAL_ANALYSIS_REGISTRATION.json, created before source overlays and any proposed fits',
        Euclidean_application='sqrt(budget)*cohort-standardized coordinate; no matrix fitted in this audit',
        H_candidate='NOT CONSTRUCTED / NOT ADMITTED',
        weighting_confound='Adding H also reallocates RQ3 budgets; not a pure isolated feature-addition effect',
        composite_and_hazard_leaveout='NOT EXECUTED: source/construct gate failed; EAL leave-out is separate Family E diagnostic',
        K_status='No new fits; existing P2 policy/K findings unchanged and open to author decision'))
    source_rows=[
        ['CGS MS48','2025 / NSHM2023 / Vs30July2022','g, PGA-2pc50, original0.01-degree grid','2294full-land supports;2299centroid estimates','https://www.conservation.ca.gov/cgs/Pages/Publications/MS48.aspx'],
        ['CAL FIRE SRA + LRA','SRAeffective2024-04-01;LRA2025state recommendation','Moderate/High/VeryHigh and NonWildland; EPSG4326 snapshot ->3310area','2200fully classified tract lands;99partial,61tracts intersect FRA','https://data.ca.gov/@cal-fire/fire-hazard-severity-zone-viewer1'],
        ['FEMA NFHL','Current service snapshot; field/query metadata retained','SFHA, A-family, coastal V,0.2%bands; unknown D','2088known full-land supports;211partial/unknown,203withD','https://www.fema.gov/flood-maps/national-flood-hazard-layer'],
        ['CDC/ATSDR EJI raw heat','2024release;2018-2022reference','E_NEHD days/year above tract-specific95th percentile;2010->2020crosswalk','2299values;13national upstreaminterpolations withouttract IDs','https://www.atsdr.cdc.gov/place-health/php/eji/eji-indicators-climate-burden-module.html'],
        ['FEMA NRI','v1.19 / Mar-23','2020tracts; AFREQ,EXP_AREA,EAL,ALR inspected','All2299matched;ratings and nulls retained','https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf'],
        ['CGS MS58 landslide','2011;metadata revision2018','Relative deep-seated susceptibility, not event probability','Source screened;no new complete raster overlay performed','https://maps.conservation.ca.gov/cgs/metadata/MS58.html'],
        ['NWS strong wind','Regionalsource description;NRIv1.19fieldscreen','SantaAna physical relevance;NRI49kmfrequency not local intensity','No independent tract-scale wind-intensity field admitted','https://www.weather.gov/safety/wind-mountain-valley']]
    save('OFFICIAL_SOURCE_AND_HAZARD_COVERAGE_INVENTORY.csv',pd.DataFrame(source_rows,columns=['source','vintage','measurement','coverage_or_limit','official_URL']))
    md('OFFICIAL_SOURCES_AND_HAZARD_COVERAGE.md',f'''# Official sources and coverage

{WARN}

{table(pd.DataFrame(source_rows,columns=['Source','Reference','Measurement','Coverage/limit','Official URL']))}

Exact official query URLs, parameters, response hashes, bytes and recorded client access date are in OFFICIAL_SOURCE_ACQUISITION.json. CAL FIRE SRA/LRA feature counts163/298, responsibility267; NFHLzones4416 and availability10. Return-ID-only queries and bounded chunks prove no transfer-limit truncation. Combined geometries contain the exact fetched features, not AI illustrations. Source geometries remain unchanged on disk; make_valid is explicitly logged for overlay working copies. Original CRS/query metadata and equal-area EPSG3310 calculations are recorded.

CAL FIRE LRA classifications are state recommendations, not proof of each local ordinance's adoption. SRA and LRA are not assumed to cover Federal Responsibility Areas. NonWildland (-3) is an explicit provider class, not a zero-fire-probability claim. NFHL availability footprints are not proof of determinate hazard-zone information; D and missing polygons remain unknown. A-family includes inland and potentially non-wave coastal flooding; V/VE is wave-coastal, so A is not simply renamed riverine.

NFHL0.01/0.002annual-chance designations and NRI RFLD/CFLD AFREQ have distinct definitions. NRI coastal frequency can combine fixed flood probabilities and high-tide recurrence; raw AFREQs from different hazards are never summed. Historical heat is not the CDPHfuture2040-2060/2080-2099 climate projection. No future climate variable enters this audit. EJI overall/social/health indices are not used, only E_NEHD and its published rank for source QA.

CDCtechnicaldocumentation pp93-94 identifies annual2018-2022extreme days, tract-specific95th-percentile thresholds and2010->2020crosswalking. It discloses13national neighbor-interpolated tracts but does not name them; the raw service lacks F_NEHD. We cannot independently establish whether any of those13are in this cohort, nor infer native within-tract temperature/population resolution from the service geometry. No new interpolation is performed. This remains a source limitation, not a claim of missing numeric values.

Landslide and strong wind are regionally relevant, not excluded for low expected loss. CGSMS58 measures slope/rock-strength deep-landslide susceptibility, not all landslide modes or a triggering-event probability. NRI LNDS includes minimum-frequency assumptions; SWND originates on49-km support. These sources are screened and retained descriptively, not forced into an already incomplete four-hazard coordinate. Tsunami and drought are relevant coastal/water-stress contexts but not conflated with riverine/coastal inundation or household electricity dependence.

Attribution remains with each original agency. Government/OSM/third-party data are not relicensed as original project code. Users should consult the original provider's current terms of use. The cached TIGER2020area-water source and existing MS48extraction are manifest/hash-bound; their current network bytes were not re-downloaded in this round. No prospective claims of a universal or synchronized-year hazard field are made.
''')
    md('ALL_18_FEMA_SCREENING.md',f'''# All18FEMA hazards screened

{WARN}

ALL_18_HAZARD_INVENTORY.csv records scientific screening and native frequency support for every category, not only earthquakes. ALL_18_HAZARD_FIELD_QA.csv records every AFREQ/EXP_AREA/EALT/EALS/ALR field's existence, finite/null/zero/negative values and distribution. ALL_18_HAZARD_APPLICABILITY_RATINGS.csv preserves source-defined applicability separately.

{table(loss[['hazard','valid_tracts','positive_EAL_tracts','pooled_share']])}

Avalanche, hurricane, ice storm and volcanic activity have no numeric EALT in this cohort's archived release. Their exact ratings are preserved, not imputed. Release-specific NotApplicable does not establish universal physical impossibility or account for events after the source's temporal reference. Cold-waveEAL is numeric zero, a different state from null applicability. Agriculture-only drought EAL does not measure all drought effects on residents. Positive historical earthquake-service burden is not a direct measurement of broader wind/fire/flood/heat exposure.

Version-specific evidence uses the March2023document, not the current v1.20 technical PDF. Table6(PDFp63,printed5-4) explains distinctevents, eventdays and nohistoricaleventcount for modeledhazards. PDFp44(printed3-6) distinguishes NotApplicable, InsufficientData and noEAL. Frequency/exposure excerpts and exact PDF are retained. All18hazards are measured on the same2299IDs; no score-driven hazard selection occurs.
''')
    md('TRACT_OVERLAY_AND_MISSINGNESS_QA.md',f'''# Full cohort retained; incomplete measurements not filled

{WARN}

Full frozen domain2315; positive frozenpopulation2299; excluded zero-population16(exact IDs in EXCLUDED_ZERO_POPULATION_GEOIDS.csv). All eight positive-population zero-housing tracts remain. Full2315P2source descriptors are retained; no service or distributional calculation changes. No CORE3geometry exclusions are inherited.

Complete polygon measurements: PGA2294; wildfire2200; known flood2088; historicalheat2299. Their common complete-case intersection is **2032**, used only for explicitly labeled information diagnostics, NOT a revised clustering cohort. **267** eligible tracts lack at least one complete polygon measurement. All missing fields and GEOIDs are exported. The current complete-case subset cannot silently replace the approved2299cohort.

Land geometry is recomputed for all2315tracts from frozen polygon bytes minus TIGER2020area-water. No geometries disappear. Validity, area partition residuals and source hashes are recorded. Polygon coverage fraction within1e-6of full land is the numerical overlay-completeness criterion, not a hazard threshold. PGA retains the prior documented99%grid-support rule and flags5partialcoastal supports rather than renormalizing them into a complete measurement.

{table(point[['comparison','n','Pearson','Spearman','area_positive_point_zero']])}

Point/PGA estimates broadly agree with supported areameans but do not restore missing polygon support. On comparable fire records206tracts have positive high-class area while the geometric centroid is outside that class; the corresponding flood count is400. Neither centroid nor Census internalpoint is population geography. Reported populations in high-exposure *tracts* are representation counts, not people located in the exposed polygon. No household/building spatial distributions are fabricated.

Three of the eight special-use tracts have incomplete flood support and two have incompletefireclassification; some overlap. They stay in all source/missingness tables and are not dropped for convenience.
''')
    md('INCREMENTAL_INFORMATION_AND_CONSTRUCT_DECISION.md',f'''# Incremental information is not admission by itself

{WARN}

{table(info.loc[info.target.isin(['tract_seismic_PGA','Wildfire_high_land_fraction','Flood_SFHA_land_fraction_complete','Historical_heat_days_2018_2022']),['target','n_common_complete_cases','all_other_core_conditional_linear_R2','VIF','fivefold_nonlinear_predictive_R2','fivefold_15km_block_nonlinear_R2','P2_only_R2_on_common_cohort']])}

Full pairwise-count and common2032cohort Pearson/Spearman matrices are exported. Common-cohort conditional linearR2/VIF and fixed ExtraTrees diagnostics quantify predictive overlap, not causality or independent validation. RandomCV can exploit spatial shared patterns;15kmblockCV is reported separately. No parameters are tuned to make a candidate eligible. Missingness can affect these comparisons: fulleligible and completecase counts are never conflated.

Wildfire and flood have low pairwise linear association with each other(r=-0.0029on2032tracts), and historicalheat has weak marginal association with SOVI(r=-0.0625on2299). Thus non-earthquake context is demonstrably not identical to SOVI, Population or PGA. PGA/heat nevertheless have shared geography and meaningful overlap with existing recovery inputs: earthquake-PGA versus B_Unconstrained Pearson0.4433(n2294), heat versus B_Unconstrained -0.4164(n2299), heat versus MeanDelta0.3715. These are empirical frozen-model associations, not causal heat effects on earthquake restoration.

Known-flood SFHA area is extremely concentrated: its highest1%accountsfor75.71%of standardized variance; zmax14.44. This is a physical-area distribution and requires sensitivity awareness, not clipping or automatic rejection for poor cluster quality. It does not justify inserting a forced equal-rank composite. Original-unit distributions, exactzero fractions and standardized leverage are reported separately.

No multi-hazardHcoordinate is constructed. Ordinal long-term fireseverity, designfloodzone fractions, probabilisticPGA and relative-threshold historicalheat are not a common probability/time horizon. A transparent relative screening index could be defined with author-approved semantics, but normalization alone does not establish a coherent construct; incomplete federal/fire and undeterminedflood geography cannot be interpreted as zero. The predeclared equal-hazard percentilerank option was conditional and is not executed. No exact H-specific influence/leave-hazard-out clustering is claimed because there is no admitted Hcoordinate.

FamilyEprovides a separate actual contribution diagnostic: earthquake pooled share {nri['earthquake_pooled_share']:.6%}, wildfire {loss.loc[loss.hazard.eq('Wildfire'),'pooled_share'].iloc[0]:.6%}, tornado {loss.loc[loss.hazard.eq('Tornado'),'pooled_share'].iloc[0]:.6%}; remaining contributions are exported. EAL leave-one-hazard-out shows the loss-based composition's sensitivity and is explicitly not a physical-composite normalization experiment. ALR_NPCTL reduces stock scaling but retains expected-loss weights; neither EAL nor ALR is promoted as a substitute Hmeasurement. RISK_SCORE remains excluded.
''')
    md('SEVEN_VERSUS_EIGHT_CONDITIONAL_COMPARISON.md',f'''# Conditional comparison stops at the admission gate

{WARN}

P2's seven frozen coordinates and one-third RQ budgets remain untouched. Two eight-coordinate RQ3alternatives were preregistered before source extraction: equal1/9each, or SOVI1/6and Population/H1/12each. Every value is a squared-distance budget, whose square root would multiply cohort-standardized values. Neither budget is asserted statistically optimal.

The physical candidate fails complete2299source support and has unresolved aggregation semantics. Therefore **zero new K-means fits** are performed. No Elbow, Silhouette, ARI, spatial or policy-set cluster stability is fabricated for an inadmissible feature. Existing P2results remain prior diagnostics, not validation of a hypothetical eight-variable model. K remains open and no variable/weight/Kdecision is promoted.

To proceed, authors would first need to declare the intended environmental-context construct and physical support, resolve/quantify incomplete federal/fire and Dflood geography without adding cohort exclusions/imputations, verify historicalheat upstream limitations, and justify a component normalization/temporal interpretation. Then the registered K2-8/K1baseline, seeds42-46,n_init50,Lloyd500,tol1e-4comparison could proceed. Changes to weights would be acknowledged separately from feature addition. This task does not grant formal Stage7replacement.
''')
    md('FINAL_MULTIHAZARD_AUTHOR_DECISION.md',f'''# Final scientific recommendation

{WARN}

1. **Reliable non-earthquake context exists, with explicit limits.** Historical heat has 2,299 official 2018-2022 values (11.8-25.2 days/year). Fire severity has 2,200 complete land classifications; known flood zones have 2,088. SFHA intersects 486 eligible tracts; 40 intersect coastal V/VE wave zones. These are geographic overlap counts, not exposed-population totals. All 18 NRI hazards were screened, including wind, landslide, drought and tsunami; complete independent physical layers are not admitted for every hazard.
2. **Do not combine them into one main clustering coordinate now.** Five PGA supports, 99 fire classifications and 211 flood supports are incomplete. The common 2,032-tract information subset is not the approved 2,299-tract cohort. Mixed severity, probability and relative-threshold heat measurements need an explicit screening meaning, not just numerical normalization. No missing values are filled, no observations are trimmed, and no geometry exclusions are inherited.
3. **They add genuine information, but not a complete validated composite.** Fire and flood area have Pearson r=-0.0029 on the common cohort. Heat has weak marginal association with SOVI (r=-0.0625) and log population (r=-0.0170). Conditional and nonlinear diagnostics show both shared geography/recovery information, especially for PGA and heat, and distinct environmental attributes. Low VIF does not resolve source gaps or establish construct validity.
4. **EAL is earthquake dominated.** The independently recomputed current-cohort earthquake share is {nri['earthquake_pooled_share']:.6%} of pooled expected annual loss. EAL_SCORE is therefore not balanced multi-hazard physical exposure here. ALR_NPCTL is a loss-based comparator; RISK_SCORE embeds vulnerability/resilience and is not a physical-exposure measure.
5. **Recommendation: retain separate contextual maps and descriptors.** Preserve the existing seven-variable P2 candidate for review, without declaring it universally selected. Describe wildfire, flood and historical heat independently of earthquake-conditioned restoration. Adding context maps does not simulate compound events, non-earthquake station failures or multi-hazard electrical-system performance.
6. **No eight-variable K or stability result can honestly be reported.** Admission failed before fitting: zero new K-means models were run. There is no evidence that any K or membership structure survives hazard addition. Author decisions remain: the intended screening construct and spatial/temporal support, how source gaps could be resolved without changing the 2,299 identities or imputing missing values, and whether to authorize a later conditional comparison. No final variable set, weights, K or formal Stage 7 replacement is promoted.

Important limitations: current NFHL and 2024/2025 fire classifications differ in temporal reference from the frozen earthquake simulation. CDC's 13 national upstream interpolation identities remain unresolved. Spatial-block predictive diagnostics do not validate resident-level exposure. Existing MeanDelta values and Vulnerability-first/SOVI procedural dependence are unchanged. The 950 protected scientific files, 1,570 prior diagnostic Git blob identities, unrelated staged work and frozen outputs are independently checked before delivery.
''')
    md('README.md',f'''# Multi-hazard RQ3 audit

{WARN}

Starting authority `{AUTH}`. Begin with [the decision](FINAL_MULTIHAZARD_AUTHOR_DECISION.md) and [coverage audit](TRACT_OVERLAY_AND_MISSINGNESS_QA.md).

No new clustering or physical simulations; no formal Stage7promotion. The approved2299positivepopulationIDs and all eight additionalzero-housingtracts are retained. LossfamiliesE/L are not substitutes for physicalfamilyH.

Reproduce numerical post-processing from retained new-package CSVs: `python information_audit.py`, `python reports.py`, `python figures.py`, `python verify_independent.py`. Run from this package directory or use its full script path. Source-stage reproduction uses `audit_fema.py`, `audit_physical.py --phase base` and `--phase flood`; it needs GitLFS-delivered frozen inputs/priorPGA extraction and the retained official geometry/heat snapshots. `common.py` resolves a fullclone first; local sparseworktrees use declared fallback sources.

`acquire_physical_sources.py --phase metadata|heat|geometry` is optional live reacquisition, not exact historicalsnapshot reconstruction. Providerlayers can change. Rawrequestchunkresponses are local-only caches; canonicalcombinedFeatureCollections, exactqueryIDQA, metadata and requesthashrecords are retained. CachedTIGER2020waterbytes are copied from prior officialacquisition; their sourceURL/hash and nofreshdownload limitation are explicit. No manifest-bound realizationarchive is required to reproduce this package's CSV-based informationaudit; the prior P2physical provenance remains in its original package.

Reviewplots are vectorPDFs plus600dpipreviews, rendered and checked at publication dimensions. They use Matplotlib/GeoPandas, not generatedimages or illustrativephysicalmechanisms. Source PDFs are copied official documents, not created finalplotdeliverables. Requirements used: Python3.12.3, NumPy,Pandas,SciPy,scikit-learn,GeoPandas,Shapely,Matplotlib,PyMuPDF,requests,tabulate; exact versions are recorded in INDEPENDENT_QA.json.
''')
    print('Decision reports generated; no clustering authorized by admission',flush=True)


if __name__=='__main__':main()
