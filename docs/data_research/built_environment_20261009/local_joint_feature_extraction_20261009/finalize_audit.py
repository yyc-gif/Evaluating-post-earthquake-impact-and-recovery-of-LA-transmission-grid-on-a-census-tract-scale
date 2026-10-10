"""Write source-bounded reports and verify preservation after feature extraction."""
from pathlib import Path
import json,hashlib,time,subprocess
import pandas as pd,numpy as np
from source_audit import ROOT,OUT,sha,dump,git
from extract_scag import CLASSES
def load(n):return json.loads((OUT/n).read_text(encoding='utf-8-sig'))
def text(n,s):(OUT/n).write_text(s.rstrip()+'\n',encoding='utf-8')
def run():
 f=pd.read_csv(OUT/'TRACT_FEATURE_CANDIDATES.csv',dtype={'tract_id':str}).set_index('tract_id')
 res=pd.read_csv(OUT/'RESIDENTIAL_2291_FEATURE_MATRIX.csv',dtype={'tract_id':str}).set_index('tract_id')
 sc=load('SCAG_GEOMETRY_QA.json');la=load('LARIAC2020_GEOMETRY_QA.json');age=load('BUILDING_AGE_QA.json');age4=load('BUILDING_AGE_2014_QA.json');pga=load('TRACT_SEISMIC_HAZARD_QA.json');height=load('LARIAC2020_HEIGHT_QA.json');assembly=load('FEATURE_ASSEMBLY_QA.json')
 sources=[
 ('SCAG2019','https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0','ALU2019.1, updated February2021'),
 ('LARIAC6','https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_%282020%29/FeatureServer/0','2020 release; mixed source capture dates'),
 ('LARIAC4','https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1','2014 outlines; associated assessor Roll_Year retained'),
 ('CGS MS48','https://www.conservation.ca.gov/cgs/Pages/Publications/MS48.aspx','2025 MS48 / USGS NSHM2023 / Vs30 July2022'),
 ('TIGER water','https://www2.census.gov/geo/tiger/TIGER2020/AREAWATER/tl_2020_06037_areawater.zip','2020 county area-water polygons')]
 s='# Built-environment source and geometry audit\n\nScientific baseline: 031d2c675f8e7d58035d27448be040b809ced086. All outputs here are measurements/candidate diagnostics; no variable selection or clustering was performed.\n\n'
 s+='| source | official location | version |\n|---|---|---|\n'+''.join(f'| {n} | {url} | {v} |\n' for n,url,v in sources)
 s+='\n## Domain and land denominator\n\nThe original 2,315 GEOID11 universe and exact 2,291 residential membership are preserved. Study polygons are transformed to EPSG3310. Land is polygon area minus unioned TIGER2020 county water; Census ALAND is an independent check. Eighteen tracts differ by more than 0.5%; candidate polygon-dependent shares, entropy and primary PGA are withheld there, while raw measured diagnostics and discrepancy values remain. land_mask_area_check_pass means area agreement within0.5%, not independent spatial validation of the water mask. The maximum discrepancy is44.84%; this is an unresolved land-area definition/geometry discrepancy, not a proven absence of water. Building counts and housing-unit densities use Census ALAND directly.\n\n'
 s+=f"## SCAG2019\n\nAll {sc['raw_records']:,} LA records and {sc['stack_gt1_records']:,} STACK>1 records were acquired, with exact OBJECTID reconciliation across 1,204 response chunks. Actual equal-area intersections allocate parcels spanning tracts; GEOID20 is never assumed to be a tract key. {sc['exact_normalized_geometry_duplicate_records']:,} duplicate geometries are counted once. Same-geometry conflicting classes and different-geometry cross-class overlaps are withheld as ambiguous area; STACK>1 is not a blanket deletion rule. {sc['invalid_repaired']:,} invalid geometries were repaired and {sc['missing_geometry']:,} missing geometries retained in the QA count.\n\n"
 s+=f"Classified land coverage quantiles: {sc['classified_coverage_quantiles']}. Total ambiguous overlap is {sc['ambiguous_overlap_total_m2']/1e6:.3f} km² and parcel gaps {sc['parcel_gaps_total_m2']/1e6:.3f} km². Unknown LU codes, geometry gaps, SCAG water and overlap are separately reported. Broad-code allocation is explicit in SCAG_SOURCE_CODE_MAPPING.csv. Mixed-use records remain mixed-use rather than guessed residential/commercial fractions.\n\n"
 s+='Entropy = -sum(p_i ln p_i)/ln(11), with p_i exclusive class area divided by all exclusive classified land. It covers all eleven prespecified land categories, including agriculture/vacant/protected land, and excludes unknown/water/ambiguous area. It is not entropy of parcel counts or only developed land. Classification coverage and ambiguity must accompany interpretation. Boundary lines/points have zero area and are removed before overlays; any failed numerical overlay uses a recorded 0.1-mm precision repair, not blanket geometry quantization.\n\n'
 s+=f"## LARIAC6 urban form\n\nThe official GDB contains {la['raw_records']:,} records: {la['code_counts']}. Only actual Building outlines enter the footprint/count measures. {la['duplicate_geometry_removed']} exact-geometry duplicates are removed; distinct outlines with repeated BLD_ID remain. {la['invalid_repaired']} invalid geometries are repaired. Unioned footprint coverage is clipped to tract land; {la['total_overlap_removed_m2']:.3f} m² of overlap is removed. Count assignment uses the outline centroid, with the lowest GEOID for an exact boundary tie; crossing outlines are not multiply counted.\n\n"
 s+='AREA is ft² in the native EPSG6424 feet geometry, confirmed by near-one source-area/native-geometry ratios. Official County LARIAC dictionary specifies HEIGHT in feet; the inherited LARIAC6 schema is converted by 0.3048 to metres. Median heights use centroid-assigned observed buildings; area-weighted heights use clipped outline area. Two conflicting duplicate heights are excluded locally, not all height observations. Missing/nonpositive heights remain undefined. Heights do not establish stories; footprint is roof projection, not floor area. No arbitrary small-building cutoff is added, and a minimum detectable footprint is not documented. The 2020 release contains substantial earlier imagery, including 2008; it is not a complete new 2020 survey.\n\n'
 s+='## Age and inventory boundary\n\nBUILDING_AGE_COMPLETENESS_AND_SENSITIVITY.md separates original2014 age measurements from strict 2014-to-2020 linkage. R2D_BRAILS_INVENTORY_AUDIT.md finds school portfolios only, not a representative all-use county inventory. No NSI/BRAILS school attribute is propagated to county buildings.\n\n'
 s+='## Pure hazard and pilot imperviousness\n\nThe original CGS PGA CSV is byte-identical to the official MS48 download. Its station interpolation reproduces all 92 frozen inputs within 2.22e-16 g. Primary tract PGA is an area-weighted piecewise-constant 0.01-degree cell representation of the same geographical PGA field, not a mapping-weighted station value. Units are g. Five tracts have less than99% grid support and primary PGA is withheld; partial-area and centroid-IDW diagnostic values remain. TIGER land-mask discrepancies are additionally flagged/withheld. FEMA total/earthquake risk remains diagnostic and is not admitted as pure hazard.\n\nImpervious fraction is the existing numeric ESRI AnnualNLCD2022 Collection1.0 pilot. Direct USGS source/version correspondence is not verified; this remains a pilot candidate, not an authoritative USGS measurement.\n\n'
 s+='Original source archives and full SCAG response geometries remain locally available. Completed temporary overlay caches were hash-recorded and removed to recover disk space; see REMOVED_TEMPORARY_CACHE_MANIFEST.csv. SOURCE_CACHE_MANIFEST.csv records their exact hashes; metadata, acquisition logs and scripts are committed. Large raw archives are not uploaded or used as a substitute for validated tract data.\n'
 text('BUILT_ENVIRONMENT_SOURCE_AND_GEOMETRY_AUDIT.md',s)
 orig=pd.read_csv(OUT/'BUILDING_AGE_2014_ORIGINAL_TRACTS.csv');linked=pd.read_csv(OUT/'BUILDING_AGE_ALL_USE_TRACTS.csv')
 s=f"""# Building-age completeness and sensitivity

Two distinct measurements are supplied; neither is a silently imputed all-building age.

| scope | source | valid-age coverage median | tracts with defined pre1970 share |
|---|---|---:|---:|
| Original 2014 outlines | associated assessor YearBuilt1 on LARIAC4 | {orig.all_use2014_age_coverage.median():.6f} | {orig.all_use2014_pre1970_area_share.notna().sum()} |
| Strict linkage to 2020 outlines | unique BLD_ID and geometric IoU>=0.90 | {linked.all_use_age_coverage.median():.6f} | {linked.all_use_pre1970_area_share.notna().sum()} |

The original2014 statistic uses unioned observed footprints clipped to tract land. Its numerator is pre1970 area and denominator is valid-age area. Coverage divides valid-age area by all 2014 outline area. It spans actual available uses and is explicitly a2014 candidate; it is not evidence of the construction-age distribution of all 2020 buildings.

Strict2020 transfer accepts {age['unique_id_and_IoU_accepted']:,} county outlines and rejects {age['unique_id_geometry_mismatch']:,} same-ID geometry mismatches. This conservative linked statistic has very low coverage and must not be described as representative all-use building age. A deterministic20,000-record convenience audit found median centroid displacement about1.25m despite near-identical outline areas, explaining sensitivity to geometry overlap. It does not prove the cause of the displacement or authorize coordinate correction. No transfer tolerance was relaxed and no government years were filled.

Years must be finite integer1800–2014 and not exceed the recorded assessor Roll_Year where present. YearBuilt1 is an associated assessor attribute, not independent validation of actual construction year. Conflicting duplicate geometry attributes are withheld. Residential-only statistics are separate. County record-level validity by use is in LARIAC4_COUNTYWIDE_AGE_BY_USE.csv; high county validity does not certify tract coverage or individual years.

For either scope, lower bound = known pre1970 area / all area; upper bound = (known pre1970 area + missing-age area) / all area. These are missing-age sensitivity bounds, not probabilistic confidence intervals or imputations. Width directly reveals insufficient information. The strict2020 and original2014 measures must not be pooled as if their footprints/vintages matched.

Government validity is approximately4.29%, industrial85.22%, institutional92.57%, commercial94.04%, residential98.86% at county record level. Observed tract-use area coverage and missing area are exported. ACS housing age is an independent residential-unit estimate with MOE, not a general non-residential age measure.
"""
 text('BUILDING_AGE_COMPLETENESS_AND_SENSITIVITY.md',s)
 # Definitions are data-dependent listings, not recommendations.
 coverage=pd.read_csv(OUT/'FEATURE_COVERAGE_QA.csv')
 defs=[]
 for k in coverage.feature:
  unit='dimensionless';definition='Candidate/source field; see source and QA reports.'
  if k=='B_480_hr':unit='h';definition='Mean over1000 realizations of integral0..480 of normalized tract service deficit, unchanged M1/G1 mapping mass.'
  elif k=='T80':unit='h';definition='First saved completion-event crossing0.8 by mean tract service trajectory, not mean realization T80.'
  elif k=='Init_Supply':definition='Frozen mean initial normalized source-connected tract service availability.'
  elif k.endswith('_area_share'):definition='Class/known-age area divided by specified land or observed valid-age area; consult scope/coverage fields.'
  elif k.endswith('_age_coverage'):definition='Observed valid-age outline area / all outline area for the named vintage/linkage scope.'
  elif k=='land_use_entropy':definition='-sum(p ln p)/ln11 on exclusive classified land area, unknown/water/ambiguous excluded.'
  elif k=='building_footprint_coverage':definition='Union area of actual building roof outlines clipped to tract land / tract land area.'
  elif k=='building_count_density':unit='buildings per km2';definition='Unique-geometry buildings assigned once by centroid / CensusALAND km2.'
  elif k.startswith('building_height_'):unit='m';definition='Positive observed source HEIGHT converted from feet; median centroid buildings or clipped-area weighted mean.'
  elif k=='housing_units_per_km2':unit='housing units per km2';definition='ACS2022 housing total / CensusALAND km2.'
  elif k=='NRI_BUILDVALUE':unit='USD, original FEMA exposure value';definition='Original FEMA NRI building exposure value, not measured seismic hazard.'
  elif k=='Grid_Degree':unit='mapping-weighted neighbor count';definition='Frozen mapping-weighted station degree, not a station count per tract.'
  elif k=='SOVI_SCORE':unit='original FEMA NRI social-vulnerability score';definition='Preserved formal social-vulnerability score; not income quartile.'
  elif k=='Pop_Density':unit='persons per square mile';definition='Exact original CDC E_TOTPOP/AREA_SQMI, not replaced with a different Census population convention.'
  elif k=='tract_seismic_PGA':unit='g';definition='Land-area weighted0.01degree MS48 PGA-2pc50 field, grid>=99% and landmask check required.'
  elif k.startswith('housing_') or k.startswith('residential_pre'):definition='ACS2022 five-year residential unit composition/age estimate; undefined when denominatorzero; MOE retained.'
  elif k=='impervious_land_fraction':definition='Numeric ESRI annualNLCD2022 C1.0 pilot; independentUSGS source/version unverified.'
  elif k.startswith('Grid_'):definition='Frozen mapping-weighted source station topology metric.'
  elif k=='Redundancy_HHI':definition='Sum of squared normalized positive tract dependency weights.'
  defs.append({'feature':k,'units':unit,'definition':definition,'reliability':coverage.set_index('feature').loc[k,'reliability'],'source_and_vintage':coverage.set_index('feature').loc[k,'source_and_vintage'],'final_indicator_selected':False})
 pd.DataFrame(defs).to_csv(OUT/'FEATURE_DEFINITIONS.csv',index=False)
 text('REMAINING_BLOCKERS.md',"""# Remaining qualifications before feature selection

- Strict2014-to2020 age transfer is sparse (median valid-age area4.4%); it is not representative countywide age. The additional original2014 measure provides a separately dated observed candidate, not a cure for2020 linkage.
- Eighteen tract land-mask areas disagree with CensusALAND by>0.5%. Primary polygon-dependent candidates are withheld there; diagnostic values remain. Resolve the land/water definition before using those tracts for affected physical-area measures.
- Five tract PGA supports are below99%; partial support is not extrapolated.
- Imperviousness remains an ESRI pilot with unverified directUSGS/version linkage.
- R2D/BRAILS inventories discovered are school portfolios, not a representative all-use structural census. Countywide structure/occupancy predictions were not generated or guessed.
- Roof outlines do not measure floor area or stories; minimum detectable footprint is undocumented.2014/2020 releases contain older imagery and age vintages differ.
- SCAG mixed-use allocation and ambiguous overlaps are not resolved by fabricated fractions. Classified-area coverage is part of every entropy/share interpretation.
- Descriptive correlations/VIF do not select final variables, establish causality or account for spatially independent observations. No final clustering or manuscript claim is inserted.
""")
 text('EXECUTION_LOG.md',"""# Execution log

1. Inspected checkout HEAD/branch, remote refs, staged changes, LFS and runtime. Baseline031d2c6; exploratory reference d5d51c6. Preserved862 pre-existing staged additions and unrelated untracked work. New work confined to this directory.
2. Snapshotted original212 protected files plus priorGA protection (950 unique paths); retained index/status bytes and input hashes.
3. Searched Windows sources, GIS caches and CE294 archives. PriorD drive absent; actualR2D installation onC. Found884-school inventories; no suitable complete local SCAG/LARIAC geometry cache.
4. Retrieved official SCAG2019 LA records and official LARIAC6/4 GDB archives. Retained exact response/chunk/source hashes and acquisition logs. No AI/image inventory generation.
5. Verified and recovered formalB from savedINTEGRALS and1000 archived trajectories. Initial tract-order check caught an incorrect sorted-order assumption; corrected to saved original tract order. Exact saved mapping/station-integral reproduction now passes. Stage7T80/Init reproduce numerically.
6. Computed observed LARIAC union footprints, centroid counts and height. A first all-county geometry accumulation exhausted memory; switched to compressed pertract caches. Conflictingduplicate heights were localized to two outlines and other valid height observations restored.
7. Computed strict 2014-to-2020 age transfer, full linkage and tract-use completeness. A final QA path-variable shadowing error occurred after output completion; recoveredQA from retained records and correctedscript. Added original2014 tract-age measurements to avoid conflating sparse2020 transfer with source-year evidence; no transfer threshold was relaxed.
8. SCAGblank LU codes became explicitly unclassified. Area overlay failed on mixed-dimensional boundary intersections; stripped nonareal components and resumed from retained geometry cache. Exceptional numerical repairs are recorded. No indiscriminateSTACK deletion or tractprefix assignment.
9. OfficialCGS source ZIP matches local originalPGA bytes. Reproduced92 stationPGA values and extracted tractgeographic gridarea means. No risk/fragility replacement.
10. Preserved raw Windows inventory discovery after auto-review rejected destructive overwrite; wrote a separate relevance filter.
11. Assembled all 2,315 and exact 2,291 matrices with nulls/coverageflags; descriptive correlations, VIF, and conditional redundancy use explicit matchedtractN and hash. No feature selection or clustering.
12. Disk pressure interrupted the additional2014 extraction. Automatic review rejected bulk cache cleanup; after confirming no active extractor, only completed LARIAC6/SCAG temporary caches were hash-recorded and removed. Original sources, verified outputs and failed partial caches remain. The original2014 extraction resumed with a fresh cache and explicit missing-geometry handling.
13. A resumed age-union process exited1 without an explanatory traceback. Complete cached geometries were retained. Metadata-only cache recovery, progress/partial checkpoints and an independent original-source count/area reconciliation closed that integrity gate; the exitcause is undetermined, not silently called a source-data success.
14. Repeated full/subset polygon unions were replaced by exact union areas of disjoint positive-overlap components. All overlaps still use GEOS union. An independent40-tract/160-subset comparison agrees within1.9e-9m2. This changes computational work, not area definitions. Earlier partial rows were retained locally for direct value comparison.
15. Focused tests, post-extraction protected/input/index hash verification and scoped alternate-index branch publishing are recorded in QA/test/publish files. Physical damage, repair schedules, GA, mapping, trajectories, storedclusters, figures and manuscript are not modified.
""")
 text('README.md',f'''# Joint tract feature extraction for author review

Scientific baseline: 031d2c675f8e7d58035d27448be040b809ced086. Analysis reference: d5d51c6ad1659c82c3b6717ab14a31f3e5cd78c7. These are candidate measurements and descriptive redundancy evidence; no final variable selection or clustering was performed.

- TRACT_FEATURE_CANDIDATES.csv: all 2,315 tracts with GEOID11, nulls and source/coverage flags.
- RESIDENTIAL_2291_FEATURE_MATRIX.csv: the exact saved 2,291 residential members.
- FEATURE_CORRELATION_MATRIX.csv: 1,081 Pearson/Spearman comparisons, each with actual N, missingness and a hash of its matched tract set. Log alternatives are diagnostic.
- FEATURE_VIF.csv and FEATURE_CONDITIONAL_REDUNDANCY.csv: explicit complete-case samples, controls and composition constraints; no indicator is selected.
- FEATURE_COVERAGE_QA.csv and FEATURE_DEFINITIONS.csv: source, vintage, units, completeness and reliability.
- RECOVERY_METRIC_QA.md: exact B/T80/initial-service definitions, horizon and reconstruction checks.
- BUILT_ENVIRONMENT_SOURCE_AND_GEOMETRY_AUDIT.md, BUILDING_AGE_COMPLETENESS_AND_SENSITIVITY.md and R2D_BRAILS_INVENTORY_AUDIT.md: actual source scope and limitations.
- INPUT_SOURCE_HASHES.json, SOURCE_CACHE_MANIFEST.csv, REMOVED_TEMPORARY_CACHE_MANIFEST.csv and PRESERVATION_FINAL_QA.json: traceability and preservation.

| dataset | actual completion status |
|---|---|
| B/T80/initial service | Same 1,000 saved formal realizations; all 2,315 values verified |
| SCAG 2019 | All 2,406,373 LA records processed; median classified land coverage 75.1%; ambiguous area and gaps retained |
| LARIAC 2020 | Observed union footprints, centroid counts and positive heights extracted; release contains earlier imagery |
| Original 2014 building age | Separately dated all-use candidate; median valid-age area coverage 95.2%, not complete all-building age |
| Age transferred to 2020 | Strict ID/geometry linkage; median valid-age area coverage 4.4%; unsuitable for a complete all-use interpretation |
| R2D/BRAILS | 884-record school portfolios only; not a representative county structural inventory |
| Pure tract PGA | Original official geographical field verified; 2,294 primary values after support/land-mask checks, partial diagnostics retained |
| Imperviousness | Existing numeric pilot retained; direct USGS source/version correspondence unverified |

B is mean normalized service deficit integrated over 0-480 h. T80 crosses 0.8 on the mean service trajectory, not the mean of realization T80. On the exact residential subset, B/T80 Pearson = 0.912150 and Spearman = 0.929190. AUC_480 = 1 - B/480 is an exact complement. None of these findings selects an outcome or transform.

Use the installed Anaconda Python. Scripts resolve repository paths from this directory. Original scientific files are read only. This extraction uses original sources, not new damage, scheduling, GA or clustering.

For a fresh source extraction, the order is source_audit.py probe; acquire_sources.py; acquire_scag.py; extract_gis.py land; extract_gis.py lariac; extract_height.py; extract_age.py; extract_age2014_original.py; audit_age2014_cache_complete.py; audit_union_area_equivalence.py; extract_hazard.py; extract_scag.py; extract_recovery.py; assemble_features.py; finalize_audit.py. audit_r2d.py documents local inventories. Reuse existing sources rather than downloading again. When reusing the complete 2014 geometry cache, invoke extract_age2014_original.py --resume-cache. The source snapshot intentionally records entry-state protection; do not overwrite it after starting work. publish_research_branch.py is for this task's scoped branch, not a general-purpose publishing command.

Large original archives and SCAG response geometries remain local with hashes. Completed temporary overlay caches were removed after hash recording to recover disk space; they can be reconstructed from retained original sources. Partial checkpoint tables remain local and are not proposed data products. The branch contains validated tables, scripts, metadata and audits.

See REMAINING_BLOCKERS.md before feature selection. Undefined housing age is null; government building ages are not imputed. No existing figure, manuscript, stored cluster, formal GA result or restoration archive was changed.
''')
 unionqa=load('UNION_AREA_EQUIVALENCE_QA.json');assert unionqa['all_sampled_areas_match_direct_GEOS'],'Union area equivalence failed'
 cacheqa=load('BUILDING_AGE_2014_CACHE_QA.json');assert cacheqa['all_expected_source_intersections_match'],'Original2014 source cache incomplete'
 # Retain all local source hash identities, without uploading bulk archives.
 rows=[]
 for p in sorted((OUT/'sources').rglob('*')):
  if p.is_file():
   status='SOURCE_OR_METADATA_RETAINED'
   if any(name in p.parts for name in ['age2014_tract_clips','age2014_tract_clips_v2','scag_tract_geometries']):status='PARTIAL_DERIVED_CACHE_NOT_ADMITTED'
   elif 'age2014_tract_clips_v3' in p.parts:status='VERIFIED_COMPLETE_DERIVED_CACHE'
   elif 'scag_la_chunks' in p.parts:status='VERIFIED_COMPLETE_SOURCE_RESPONSE'
   elif 'age_linkage' in p.parts:status='VERIFIED_RECORD_LINKAGE_DIAGNOSTIC'
   elif p.name in ['CGS_GM_VIEWER.html','SCAG_PORTAL_ITEM.json']:status='FAILED_HTTP_RESPONSE_NOT_USED_AS_AUTHORITY'
   rows.append({'local_relative_path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'source_cache_status':status,'retention':'local retained source/cache; acquisition URL in logs or official source audit'})
 pd.DataFrame(rows).to_csv(OUT/'SOURCE_CACHE_MANIFEST.csv',index=False)
 baseline=load('PRESERVATION_BASELINE.json');changed=[k for k,v in baseline['protected_files'].items() if sha(ROOT/k)!=v];inputs=load('INPUT_SOURCE_HASHES.json');changed_inputs=[k for k,v in inputs.items() if sha(ROOT/k)!=v['sha256']];idx=git('ls-files','--stage','-z')
 assert not changed and not changed_inputs
 assert idx==(OUT/'ORIGINAL_STAGING.bin').read_bytes()
 dump('PRESERVATION_FINAL_QA.json',{'scientific_baseline':baseline['head'],'protected_files_checked':len(baseline['protected_files']),'original_protected_count':212,'protected_file_hash_changes':changed,'formal_input_files_checked':len(inputs),'formal_input_hash_changes':changed_inputs,'original_staging_sha256':hashlib.sha256(idx).hexdigest(),'original_staging_unchanged':True,'preexisting_staged_files':baseline['staged_count'],'scientific_files_changed':0,'new_final_clustering':False,'existing_artwork_changed':False})
 print('FINAL_REPORTS_COMPLETE',len(rows),'SOURCEHASHES',len(inputs),'PROTECTED',len(baseline['protected_files']),flush=True)
if __name__=='__main__':run()
