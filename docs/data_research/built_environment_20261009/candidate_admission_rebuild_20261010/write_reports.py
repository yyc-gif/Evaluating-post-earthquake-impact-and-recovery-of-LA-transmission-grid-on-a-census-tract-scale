"""Assemble actual source evidence, definitions and decisions from computed tables."""
from common import *
from build_admission import SOURCES,SCAG,idhash
import pandas as pd,numpy as np,shutil,itertools

def write(name,text):(OUT/name).write_text(text.strip()+'\n',encoding='utf8')
def table(frame):
 cols=list(frame.columns);lines=['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
 for row in frame.itertuples(index=False,name=None):lines.append('| '+' | '.join(str(x).replace('|','/').replace('\n',' ') for x in row)+' |')
 return '\n'.join(lines)

def source_audit():
 records=[];evidence=OUT/'source_evidence';evidence.mkdir(exist_ok=True)
 license_info={'EMC':'CC BY4.0; scientific product, local accuracy not established','ANBH':'CC BY4.0; historical image/DEM support','ASSESSOR':'public Query/Extract endpoint; County informational disclaimer; no claim of unrestricted raw-record redistribution','SCAG':'public service; SCAG disclaimer, not jurisdictional certification','ACS':'US Census public statistics; sampling uncertainty retained','NLCD':'USGS public scientific data; requester-pays route not used','EPA':'EPA public SLD; historic LODES/ACS source dates'}
 for name,(url,vintage,resolution,qa) in SOURCES.items():
  if name=='CONCEPT':continue
  records.append({'source_id':name,'official_url':url,'access_result':'NEW_NUMERIC_ACQUIRED' if name in ['EMC','ANBH','ASSESSOR','NLCD'] else ('NEW_NUMERIC_OVERLAY_VERIFIED' if name=='SCAG2020' else ('VERIFIED_DONOR_GEOMETRY_AND_ESTIMATED_TRACT_COUNTS' if name=='EPA' else 'VERIFIED_CACHE_REUSED')),'observation_or_support_year':vintage,'inventory_roll_or_release_year':'2022 single roll' if name=='ASSESSOR' else vintage,'resolution_fields':resolution,'license_or_access_note':license_info.get(name,'see exact archived source terms'),'original_bytes_sha256':'see acquisition/reuse manifest below','numeric_scope':qa})
 probes=json.loads((OUT/'OFFICIAL_SOURCE_PROBES.json').read_text(encoding='utf8'))
 probes+=json.loads((OUT/'SCAG_ALTERNATIVE_VERSION_CHECK.json').read_text(encoding='utf8'))
 for rec in probes:
  records.append({'source_id':rec.get('source'),'official_url':rec.get('url'),'access_result':f"HTTP {rec.get('status',rec.get('http_status','ERROR'))}; metadata/description only",'original_bytes_sha256':rec.get('sha256'),'payload_bytes':rec.get('bytes'),'observation_or_support_year':'not inferred from web page date'})
 for rec in json.loads((OUT/'JRC_ACQUISITION.json').read_text(encoding='utf8')):records.append({'source_id':rec['source'],'official_url':rec['url'],'access_result':'ACTUAL_NUMERIC_ZIP' if rec.get('name') else 'OFFICIAL_PRODUCT_GUIDE','original_bytes_sha256':rec['sha256'],'payload_bytes':rec['bytes'],'observation_or_support_year':rec.get('observation_support','product documentation')})
 nlcd=json.loads((OUT/'NLCD_C12_ACQUISITION.json').read_text(encoding='utf8'));records.append({'source_id':'USGS Annual NLCD C1.2 2022','official_url':nlcd['official_url'],'access_result':'ACTUAL_NUMERIC_ZIP_PUBLIC_LEGACY_ROUTE','original_bytes_sha256':nlcd['archive_sha256'],'payload_bytes':nlcd['archive_bytes'],'observation_or_support_year':'2022 mapping year, C1.2 2026 release'})
 for name in ['NLCD_WCS_NEW_PROBES.json','NLCD_PUBLIC_API_DOWNLOAD.json','NLCD_DOWNLOAD_PROBE.json']:
  z=json.loads((OUT/name).read_text(encoding='utf8'));z=z if isinstance(z,list) else [z]
  for rec in z:records.append({'source_id':'NLCD C1.2 access attempt','official_url':rec.get('url',rec.get('request_url')),'access_result':str(rec.get('response_start',rec.get('error',rec.get('status'))))[:900],'original_bytes_sha256':rec.get('sha256',rec.get('byte_sha256')),'payload_bytes':rec.get('bytes'),'numeric_scope':'No valid C1.2 GeoTIFF obtained; not marked usable'})
 reused=json.loads((OUT/'REUSED_SOURCE_HASHES.json').read_text(encoding='utf8'))
 for name,rec in reused.items():records.append({'source_id':name,'official_url':'source commits and archived acquisition logs','access_result':'ACTUAL_PAYLOAD_SHA_EQUALS_BASELINE','original_bytes_sha256':rec['sha256'],'source_commit':rec['source_commit'],'payload_bytes':rec['bytes']})
 # Retain public metadata and exact failed response bytes; bulk county data remain local cache.
 manifest=[]
 for p in RAW.rglob('*'):
  if not p.is_file() or 'assessor2022' in p.parts and 'assessor2022_v2' not in p.parts:continue
  if p.suffix in ['.zip','.tif','.gpkg','.gz'] or p.stat().st_size<200000:
   h=nlcd['numeric_raster_sha256'] if str(p)==nlcd['tif_path'] else sha(p);manifest.append({'file':str(p.relative_to(RAW)),'bytes':p.stat().st_size,'sha256':h,'retention':'LOCAL_CACHE_ONLY'})
   if p.stat().st_size<200000 and p.suffix in ['.json','.xml','.txt'] and p.parent==RAW:
    dest=evidence/p.name;shutil.copyfile(p,dest);assert sha(dest)==h;manifest[-1]['retention']='COMMITTED_PUBLIC_METADATA_OR_ACCESS_RESPONSE'
 # Actual county caches and geometry identity reused without another county download.
 for name in ['LARIAC6_Buildings_2020.gdb.zip','LARIAC4_BUILDINGS_2014.zip','study_tract_land_3310.gpkg','tl_2020_06037_areawater.zip']:
  p=RESEARCH/'local_joint_feature_extraction_20261009/sources'/name;manifest.append({'file':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'retention':'VERIFIED_PREEXISTING_CACHE_NOT_REDUPLICATED'})
 pd.DataFrame(records).to_csv(OUT/'SOURCE_ACCESS_AND_VERSION_AUDIT.csv',index=False);pd.DataFrame(manifest).to_csv(OUT/'RAW_SOURCE_BYTE_MANIFEST.csv',index=False)
 shutil.copyfile(source('local_joint_feature_extraction_20261009/SCAG_SOURCE_CODE_MAPPING.csv'),OUT/'SCAG_SOURCE_CODE_MAPPING.csv')
 # Method records reused, not just their old statistics.
 for name in ['SCAG_GEOMETRY_QA.json','LARIAC2020_HEIGHT_QA.json','BUILDING_AGE_2014_QA.json','BUILDING_AGE_2014_BY_USE_COVERAGE.csv']:
  shutil.copyfile(source('local_joint_feature_extraction_20261009/'+name),evidence/name)

def reports():
 r=pd.read_csv(OUT/'CANDIDATE_REGISTER.csv').fillna('');f=pd.read_csv(OUT/'CANDIDATE_VALUES_RESIDENTIAL_2291.csv',dtype={'tract_id':str}).set_index('tract_id');allf=pd.read_csv(OUT/'CANDIDATE_VALUES_2315.csv',dtype={'tract_id':str}).set_index('tract_id');pair=pd.read_csv(OUT/'DEPENDENCY_AND_REDUNDANCY.csv')
 def corr(a,b):
  x=pair.loc[pair.scope.eq('residential2291')&(((pair.x==a)&(pair.y==b))|((pair.x==b)&(pair.y==a)))].iloc[0];return f"N={int(x.N)}, Pearson={x.pearson_r:.6f}, Spearman={x.spearman_r:.6f}"
 def med(c):return f'{f[c].median():.6f}'
 def n(c):return str(f[c].notna().sum())
 counts=r.disposition.value_counts().to_dict();definitions=['# Candidate definitions and measurement boundaries','Candidate registration is broader than model admission. No saved cluster label, silhouette or recovery correlation was used to admit a measurement. ADMIT does not mean independent or finally selected.','## Denominators and time','The full study universe has 2,315 GEOIDs and the residential master has 2,291. Four unresolved land masks are null for geometry-based variables. ACS and assessor parcel-point attributes remain available where their own support is valid. A common analysis subset is explicitly identified per comparison, never assumed to be the old 2,287 cases.','SCAG entropy uses 11 exclusive classes of classified land, including open/undeveloped categories. Area shares with tract-land denominators are retained alongside classified-land shares. Water, parcel gaps, ambiguous cross-class overlaps and unknowns remain separate. The actual LU19 cache and class map are reused; STACK>1 is not indiscriminately dropped. The official 2020 ALU20 alternative now has actual county numeric records and an exclusive tract-land overlay using the same eleven-class convention. It is CONDITIONAL on classified-land coverage and historical snapshot support; it does not automatically replace 2019.1. The Housing catalog contains 2019 and 2020 ALU services, not a verified 2022 parcel release.','LARIAC union coverage clips to source-qualified tract land. Whole-outline count/size/height diagnostics use centroid assignment and Census ALAND; they are not clipped footprint fragments. Parcel ages use assessment points. These boundary/denominator conventions must not be mixed in algebraic identities.','EMC values are modeled built surface m2 within 100m equal-area cells supported by 2022 Sentinel-2. Fractional cell/land intersections aggregate actual numeric TIFF values. NoData and valid unbuilt zero differ. NRES is a binary modeled non-residential surface, not an 11-class land-use survey.','ANBH is positive-cell net height at100m, with 2018 Sentinel-2 and older SRTM2000/AW3D30 2006-2011. The tract average weights positive cells by land intersection, not building footprint. Neither 2023 release nor current website year is observation year.','Assessor actual year and effective year are kept separate. Valid actual years1700-2022 are an explicit plausibility rule, not an independent validation. SQFTmain is Main Square Footage in the exact current official dictionary; it has not been established as complete gross floor area. AIN deduplication does not resolve shared condominium buildings or multiple building data lines. The follow-up audits shared coordinates, repeated attributes, restricted main-area support and a bounded 2022 cadastral geometry sample; none supplies a certified physical-building identity or gross-floor-area accounting rule. Year/missing-area coverage is observed assessment stock, not complete county all-use coverage.','ACS structure/age denominators are housing units, including vacant units. B25024 5+ =orders6,7,8,9 over1; detached=2 over1, attached=3 over1. B25034 pre1970=orders8-11 over1. SE=sqrt((4/80)*sum((replicate ratio-full estimate ratio)^2)); Census published boundary model uses average weight16 and p*=min(0.5,2.3*16/N); 90% MOE=1.645SE. Zero unit denominators are undefined, never0. Replicate zero-denominator and boundary flags are retained. Exact earlier corrected ratios/MOEs are reused, detached/attached use the same80-replicate calculation.','## Candidate-by-candidate definitions']
 for row in r.to_dict('records'):
  definitions.extend([f"### {row['candidate_id']} — {row['disposition']}",f"Construct: {row['construct']}. Formula: `{row['definition']}`. Units: {row['unit'] or 'not measured'}. Source: [{row['primary_source']}]({row['source_url']})" if row['source_url'] else f"Construct: {row['construct']}. Formula: {row['definition']}.",f"Time/support: {row['vintage']}. Spatial support: {row['resolution']}. Use: {row['research_use']}. Alternative: {row['alternative_to'] or 'none designated'}.",f"Admission: {row['admission_condition_or_exclusion_reason']}"])
 write('CANDIDATE_DEFINITIONS.md','\n\n'.join(definitions))
 dep=f'''# Source and mathematical dependency audit

SCAG2019 raw LU19 + geometry → broad exclusive classes → area fractions → normalized entropy. Fractions and entropy summarize the same composition. Residential/nonresidential classified fractions are complementary; eleven fractions have a unit-sum constraint. They are alternatives or descriptors, not twelve independent inputs.

LARIAC6 CODE/geometry → exact normalized geometry dedup → whole centroid counts and areas → count density, mean/median/IQR/CV. The same raw polygons → clipped union → union coverage. Height feet → positive/nonconflicting meters → valid-height area weighted mean and volume proxy.

Assessor2022 unique AIN + parcel point + positive SQFTmain + actual YearBuilt → observed-main-area age share and valid-age support. EffectiveYearBuilt is a different coordinate. Main area/land has no certified FAR interpretation. Condominium/shared point and building-line issues remain limitations rather than guessed deduplication.

JRC2022 total/NRES surface TIFF → fractional pixel-land intersections → total/NRES land fraction → NRES/total ratio. The ratio and both factors do not add three independent constructs. JRC2018 ANBH is a separate historical height product; it is not multiplied by2022 EMC and relabeled a synchronized measured volume.

ACS B25024 estimate +80 replicates → housing composition ratios/MOEs. B25034 → residential unit-age ratio. Housing configuration fractions share a denominator, and5+ and10+ are nested. Detached+attached=single-unit. These are one measurement family, not seven separate physical constructs.

FEMA exposure + annual event frequency + historic loss ratio → component EAL → total monetary EAL → national EAL_SCORE rank. Component exposure-normalized rates → rate percentile combination → ALR_NPCTL. Community adjustment introduces SOVI/resilience into RISK and ALR_VRA. BUILDVALUE is one underlying economic exposure, not the same construct as expected loss.

## Exact identities and their limits

For the SAME disjoint polygon list and boundary convention: coverage=count_density*mean_area/1e6; volume/land=coverage*area-weighted height. FAR additionally requires actual measured floors, absent here. Our centroid sums are not a disjoint clipped union. The computed centroid sum identity is exact, but union coverage is NOT substituted for it. With incomplete positive-height support the actual identity is centroid_sum_fraction * valid_height_area_fraction * mean_valid_height. See ALGEBRAIC_DEPENDENCY_QA.json for numerical residuals. Median area and IQR are not mean area, so the product identity cannot use them.

## Actual common-sample comparisons

LARIAC union versus JRC2022 total coverage: {corr('building_footprint_coverage','emc2022_total_built_land_fraction')}.
LARIAC height versus historical ANBH: {corr('outline_height_area_weighted_centroid_m','jrc_anbh_positive_surface_mean_m')}.
Assessor2022 actual-year share versus LARIAC2014 age: {corr('assessor2022_actual_pre1970_main_area_share','all_use2014_pre1970_area_share')}.
These compare differently dated/support-defined measurements; correlation does not establish agreement or exchangeability. LARIAC2014 construction-year attributes may share the assessor source lineage with the2022 roll, so their high correlation is not independent validation of construction year. It must not be presented as two independent age observations. Common-sample exclusions are listed by GEOID. Full and residential scopes and source-coverage/multiline strata are included in the CSV, with actual matched N and GEOID-set SHA. Diagnostics never select a feature because it correlates with recovery.

SAME_CONSTRUCT_AND_RISK_VIF.csv reports collinearity under simultaneous diagnostic input sets. It does not admit features, assign weights or imply causation. NONLINEAR_MEASUREMENT_DIAGNOSTICS.csv supplies prespecified log1p pair comparisons. Count/size versus clipped-union differences are retained in BOUNDARY_AND_SEGMENTATION_DIAGNOSTICS.csv. None substitutes for an independent physical-building segmentation census.
''';write('DEPENDENCY_AND_REDUNDANCY.md',dep)
 risk=f'''# Risk/exposure candidate admission

All fields come from the SAME archived NRI v1.19 Mar-23 California table and exact2315/2291 GEOIDs. BUILDVALUE and SOVI reproduce prior saved values. Scores remain published0-100 percentile scales; standardization below is only for VIF, not a new clustering model.

| Construct | Candidate representation | Meaning and limitation |
| --- | --- | --- |
| Asset scale | BUILDVALUE; raw or log1p | Building monetary stock; not building form and not expected loss. |
| Exposure-bearing expected losses | EAL_SCORE OR EAL_VALT/log1p(EAL_VALT) | Multi-hazard annual building+population-equivalent+agriculture loss; rank versus monetary level, never independent duplicate coordinates. |
| Exposure-normalized loss propensity | ALR_NPCTL | Official unadjusted composite rate percentile; not pure hazard and not totalEAL/BUILDVALUE. |
| Consequence-specific rate | ALR_VALB or ALR_VALP | Building or population component only; cannot represent all consequences. |

EAL_h = exposure_h * annual_frequency_h * historic_loss_ratio_h, summed over applicable hazards. EAL_VALT=EAL_VALB+EAL_VALPE+EAL_VALA; EAL_VALPE=11,600,000 * EAL_VALP in this dollar framework. ALR_VALB=EAL_VALB/BUILDVALUE, ALR_VALP=EAL_VALP/POPULATION, ALR_VALA=EAL_VALA/AGRIVALUE where each denominator is positive. ALR_NPCTL combines national component rate percentiles with EAL weighting per v1.19 methodology. It is not the percentile of an invented total-loss/building-value ratio. The source combines all relevant hazards even where earthquake contributions dominate regionally.

RISK_SCORE ranks EAL multiplied by a community factor using social vulnerability/resilience; ALR_VRA_NPCTL is also community-adjusted. With mandatory independent SOVI, RISK is descriptive and ALR_VRA is rejected for proposed primary coordinates. Agricultural zero exposure is undefined, not a manufactured0 rate. Low marginal correlation does not prove socioeconomic independence.

## Actual diagnostic evidence

BUILDVALUE–EAL_SCORE: {corr('BUILDVALUE','EAL_SCORE')}.
BUILDVALUE–ALR_NPCTL: {corr('BUILDVALUE','ALR_NPCTL')}.
SOVI–EAL_SCORE: {corr('SOVI_SCORE','EAL_SCORE')}.
Full pairwise raw/log monetary comparisons, component values/rates, same-sample VIF and partial-control diagnostics are supplied. VIF does not establish causal or construct equivalence.

## Candidate designs for author decision (no weights assigned)

1. Separate stock and propensity: log1p(BUILDVALUE)+ALR_NPCTL. Preferred when both amount of assets and exposure-normalized multi-hazard loss propensity are research coordinates. This is a construct reason; D has no automatic admission privilege.
2. Propensity only: ALR_NPCTL. Removes explicit asset scale; appropriate only if economic stock is intentionally not a separate coordinate. Not an equivalent smaller version of design1.
3. Combined expected-loss/exposure: EAL_SCORE, alternatively log1p(EAL_VALT). Integrates expected annual consequences and asset/population/agriculture exposure; omits a separately identifiable asset-stock coordinate. Do not combine the score and value as two constructs.
4. Building-only or population-only rate alternatives are conditional consequence-specific sensitivity, not an all-hazard all-consequence replacement without changing the declared construct.

SOVI and Init_Supply remain mandatory. No domain20% weighting, no five-domain acceptance, no new hazard variable or new composite score is adopted.
''';write('RISK_EXPOSURE_CANDIDATE_ADMISSION.md',risk)
 short=f'''# Admitted shortlist and replacements

The63/64-row registry is a measurement pool, not an instruction to fit every coordinate. Current dispositions: {counts}. Prior BE0/BE1/D are reference calculations only. No candidate was preferred for retaining previous clusters.

## Small proposed measurement sets

**Definition-qualified core:** `emc2022_total_built_land_fraction` + one ACS residential-configuration summary (`housing_5plus_share`, or `housing_detached_share` as a same-family alternative). These capture ground coverage and residential unit configuration separately. EMC has2,311 full-domain/2,287 residential valid geometric measurements; ACS has2,292/2,291 valid positive-housing denominators. Valid zeros are preserved. This core has no claim of comprehensive all-use morphology.

**Preferred expanded, explicitly conditional set:** add `land_use_entropy` for classified-land composition, then `assessor2022_actual_pre1970_main_area_share` for observed2022 assessment-stock age. This four-construct proposal is not forced to three coordinates. SCAG coverage median={med('land_use_classified_land_coverage')}; entropy represents classified land only. Assessor age is available on{n('assessor2022_actual_pre1970_main_area_share')} residential tracts, valid-year main-area coverage median={med('assessor2022_actual_age_main_area_coverage')}. Do not call it complete area-weighted all-building construction age. If that conditional age construct is not scientifically acceptable, OMIT age from the initial candidate set rather than imply a complete measure exists. Retain three age alternatives for a prespecified measurement comparison.

**Ground-hardening candidate:** `nlcd_c12_2022_impervious_fraction` is admitted from the official2022 C1.2 numeric product. It measures buildings AND roads/other hard surfaces. Choose it instead of building-only coverage only if the declared coordinate is whole-surface hardening; do not treat the two as identical or automatically stack both. Their common-sample overlap is reported.

**Optional vertical-form extension:** `outline_height_area_weighted_centroid_m`, conditional on mixed historical LARIAC support and continuous valid-height coverage. This measures a distinct vertical coordinate and is not a prerequisite for every model. Historical ANBH is the independent-source alternative; its positive-cell weighting and older source dates are explicit. Outline median area or CV can be tested as size/segmentation alternatives ONLY if building-size structure is an intended coordinate. Do not add count density, mean area and their coverage product as independent evidence.

## Same-construct alternative designs

| Proposed measurement | Alternative | Why one may replace the other; required restriction |
| --- | --- | --- |
| EMC2022 total coverage | LARIAC clipped-union coverage |2022 remotely modeled surface versus older mixed-image vector rooflines; compare exactly same GEOIDs, do not co-include coverage duplicates.|
| SCAG classified entropy | SCAG residential classified share |diversity versus composition direction; same raw classes, not independent evidence. EPA activity mix is now a conditional historical household/job-count allocation on actual 2018 SLD polygons, followed by tract-level entropy; it measures a different construct. SCAG2020 entropy is a conditional temporal alternative with the same eleven-class convention.|
| Assessor2022 actual-year main-area share | LARIAC2014 historical valid-age footprint share |different time, assessed support and denominator; conditional alternatives, not equivalent measurements.|
| All-use age candidate | ACS2022 housing-unit pre1970 share |residential unit age only; cannot be relabeled all-use age.|
| LARIAC weighted height | ANBH2018 positive-cell land mean |historic vector rooflines versus historic modeled net-height cells; denominator/date differences retained.|
| ACS5+ housing share | detached share |same residential composition family; do not include its full partition merely to add coordinates.|
| log1pBUILDVALUE+ALR_NPCTL | ALR_NPCTL only or EAL_SCORE |separate stock/propensity versus propensity alone or combined exposure-bearing expected losses; scientific coordinate choice, not performance ranking.|

## Excluded/held measurements and their destination

{table(r.loc[r.disposition.isin(['REJECT','PENDING_DATA','DESCRIPTIVE_ONLY']),['candidate_id','disposition','admission_condition_or_exclusion_reason']])}

## Remaining genuine gaps

Official Annual NLCD2022 C1.2 was acquired through the public legacy ScienceBase route after manager/API/WCS failures. Its numeric TIFF and continuous valid-land coverage were checked and it is admitted as ground hardening; the C1.0 pilot stays descriptive. Same-geometry C1.2 versus C1.0 differences are reported in NLCD_OFFICIAL_AND_PILOT_COMPARISON.csv. Ground hardening includes roads and is not building footprint coverage. EPA tract activity mix now has an explicit actual-donor land-intersection crosswalk, numeric identity and conservation checks, with uniform within-donor activity allocation declared as estimation. SCAG2020 now has actual numeric overlay, duplicate/conflict treatment and continuous coverage QA. Both are CONDITIONAL, rather than complete synchronized 2022 measurements. Certified2022 all-use gross FAR remains PENDING_DATA: the inspected Main Square Footage dictionary, shared parcel identities and public building-line fields do not establish gross-floor-area inclusion, unit/common-area attribution or exempt-stock completeness. These are missing evidence, not zero measurements. No complete contemporaneous all-use age census is claimed.
''';write('ADMITTED_SHORTLIST_AND_REPLACEMENTS.md',short.replace('The63/64-row',f'The{len(r)}-row'))
 write('NEXT_STAGE_WEIGHT_PREREGISTRATION.md','''# Next-stage preregistration — not executed

Admission and alternative-source decisions must be reviewed before any model comparison. This document neither accepts five domains nor sets a20% weight. Mandatory SOVI, Init_Supply, the previously saved recovery coordinate and four grid descriptors remain fixed. No new labels, PCA, K selection or clustering were calculated here.

Before fitting, select a scientific coordinate set from the core/conditional shortlist and state which construct each coordinate measures. Compare same-construct sources ONE AT A TIME on a common GEOID subset: EMC vs LARIAC coverage; classified entropy vs residential composition direction; assessment-stock actual age vs historical valid-age footprint age vs residential housing-unit age/no-age; vector height vs historical net-height. Publish exact subset exclusions and continuous coverage profiles before comparing partitions. Pending source candidates cannot enter.

Risk/exposure comparisons are separate: stock+unadjusted loss propensity, loss propensity only, combined exposure-bearing EAL score (with value/log-value as an expression alternative). Describe information deliberately omitted; do not preserve a domain weight merely because a previous model used it.

Only after construct approval, preregister any inherited/equal-domain weight comparison with a scientific distance-budget rationale, fixed common sample/k/initialization/spatial-deletion protocol and declared primary stability summaries. No intermediate weight may be chosen from best silhouette, old-label agreement or outcome correlation. This task does not authorize that experiment, and gives no numerical new weight vector.
''')
 prereg=OUT/'NEXT_STAGE_WEIGHT_PREREGISTRATION.md'
 with prereg.open('a',encoding='utf8') as h:h.write('\n## Bounded later comparison settings (not executed)\n\nUse existing k=4, seeds42-61, n_init100, max_iter500, tol1e-4, Lloyd for comparability; reuse the existing20 spatial deletion sets, never redraw to improve stability. Define common cohorts by explicit GEOID intersection for each same-construct substitution and publish exclusions before fitting. The core is EMC coverage plus one ACS structure coordinate, with separately approved classified-land composition/observed-stock age extensions. Preserve the recovery/service/grid/SOVI inputs. Risk alternatives are stock+ALR, ALR only, or EAL score with non-target measurements fixed. Before execution, author approval of construct grouping and numerical distance budgets is required; no new vector is specified or selected here. Report definition changes, budget changes and spatial membership/profile stability separately, never choose by best silhouette.\n')
 # Every actual column/candidate has a traceable parent; identity controls and boundary differences.
 edges=[]
 for row in r.to_dict('records'):edges.append({'source':row['primary_source'],'raw_fields':{'SCAG':'LU19 + parcel geometry','SCAG2020':'ALU20 + actual parcel geometry','EPA':'HH + five job counts + actual 2018 SLD polygons + 2020 water/tract intersections','LARIAC6':'CODE + geometry + HEIGHT feet','LARIAC4':'YearBuilt1 + historical geometry','ASSESSOR':'AIN + RollYear + point + SQFTmain + actual/effective year','ACS':'B25024/B25034 estimate +80 variance replicates','EMC':'built surface m2/cell','ANBH':'net modeled height m/cell','FEMA':'archived published fields'}.get(row['primary_source'],''),'aggregation':row['definition'],'candidate':row['candidate_id'],'shared_denominator':row['coverage_column'],'disposition':row['disposition']})
 pd.DataFrame(edges).to_csv(OUT/'SOURCE_TO_CANDIDATE_DEPENDENCIES.csv',index=False)
 d=f[['building_footprint_coverage','outline_area_fraction_centroid_sum','outline_count_per_km2_centroid','outline_area_mean_m2','outline_area_median_m2','outline_area_cv','outline_multipart_count','outline_centroid_count']].copy();d['centroid_area_sum_minus_clipped_union_fraction']=d.outline_area_fraction_centroid_sum-d.building_footprint_coverage;d['multipart_geometry_fraction']=d.outline_multipart_count/d.outline_centroid_count.replace(0,np.nan);d.to_csv(OUT/'BOUNDARY_AND_SEGMENTATION_DIAGNOSTICS.csv',float_format='%.15g')
 # Partial overlap is measurement-only, controlling retained social/population and economic stock.
 partial=[]
 for a,b,control in [('EAL_SCORE','ALR_NPCTL',['SOVI_SCORE','log1p_BUILDVALUE','Pop_Density_per_km2']),('EAL_SCORE','SOVI_SCORE',['log1p_BUILDVALUE','Pop_Density_per_km2']),('emc2022_total_built_land_fraction','housing_5plus_share',['Pop_Density_per_km2','SOVI_SCORE'])]:
  d=f[[a,b]+control].dropna();z=np.column_stack([np.ones(len(d)),d[control].to_numpy()]);x=d[a]-z@np.linalg.lstsq(z,d[a],rcond=None)[0];y=d[b]-z@np.linalg.lstsq(z,d[b],rcond=None)[0];partial.append({'x':a,'y':b,'controls':';'.join(control),'N':len(d),'GEOID_set_sha256':idhash(d.index),'partial_Pearson_r':np.corrcoef(x,y)[0,1],'interpretation':'measurement overlap, not causal independence or admission rule'})
 pd.DataFrame(partial).to_csv(OUT/'PARTIAL_MEASUREMENT_REDUNDANCY.csv',index=False)
 write('README.md',f'''# Stage7 candidate admission rebuild

Baseline `{BASELINE}`. Branch `analysis/stage7-candidate-admission-rebuild-20261010`. Start with CANDIDATE_REGISTER.csv, then ADMITTED_SHORTLIST_AND_REPLACEMENTS.md. Numeric values are in full2315/residential2291 matrices; every disposition has a measurement/construct reason. Definitions, continuous coverage QA, common-sample statistics, source versions and raw-byte hashes are separate and traceable.

New extraction: single-year2022 Assessor nonpersonal parcel fields, actual2022 EMC total/NRES TIFFs, official NLCD C1.2 2022 fractional impervious TIFF, historical ANBH TIFFs, and cached LARIAC size/height. Correct ACS80-replicate statistics and verified SCAG/LARIAC/FEMA caches are reused. Four unresolved land geometries remain null without suppressing valid ACS/assessment-point values. Raw caches are retained locally and ignored by Git; public metadata/access responses and download hashes are committed. No county file was redownloaded when its verified cache existed. The follow-up downloads previously absent SCAG2020 county payloads and EPA donor polygons, while reusing all Assessor2022 numeric chunks and the validated tract/water support.

Reproduction reuses the delivered GEOID master tables; the follow-up does not create a new tract universe. Reproduction order: probe_sources.py; acquire_assessor.py; acquire_jrc.py; measure_rasters.py; measure_vectors.py outlines/assessor; acquire_nlcd.py; measure_nlcd.py; audit_raw_attributes.py; acquire_scag2020.py; measure_scag2020.py; audit_assessor_floor_ownership.py; measure_epa_activity.py; build_admission.py; write_reports.py; complete_pending_reports.py; pytest test_admission.py. Use the original scientific Python/GIS versions recorded in EXECUTION_ENVIRONMENT.json. rasterio1.3.10 is isolated under worktree _vendor; no original environment was upgraded. common.py contains the original payload cache locations and verifies cached analysis sources against the audited commit. Acquire scripts skip existing payloads and expose exact query fields, roll filter, count/ID completeness and download URLs. No KMeans/PCA/simulation/scheduler/GA entrypoint is imported.

Follow-up completed: conditional EPA tract activity mix from actual donor geometry and transferred counts; conditional SCAG2020 exclusive parcel-land entropy. Pending: certified gross FAR/building-line attribution, gross-area convention and condo/common-area/exempt-stock accounting. See PENDING_DATA_COMPLETION_AUDIT.md for actual values and limits. Official NLCD C1.2 numerical acquisition and verification are complete; the retained study GeoTIFF is in source_evidence with its official parent hash and XML. They do not block delivery of the acquired candidate pool; they block claims of comprehensive current-year all-use measurement.
''')
 if (OUT/'NLCD_PIXEL_AND_TRACT_IDENTITY_QA.json').exists():
  note='\nOfficial C1.2 versus retained C1.0 numeric identity: same native30m grid, 6,916,982 common valid pixels, zero value/mask differences, and zero differences in all2,311 same-geometry tract means. Release provenance remains separate; no duplicate measurement is added. See NLCD_PIXEL_AND_TRACT_IDENTITY_QA.json.\n'
  for name in ['CANDIDATE_DEFINITIONS.md','ADMITTED_SHORTLIST_AND_REPLACEMENTS.md','README.md']:
   with (OUT/name).open('a',encoding='utf8') as h:h.write(note)
 log('Definitions, source evidence, measurement shortlist and no-execution next-stage preregistration written')

if __name__=='__main__':source_audit();reports()
