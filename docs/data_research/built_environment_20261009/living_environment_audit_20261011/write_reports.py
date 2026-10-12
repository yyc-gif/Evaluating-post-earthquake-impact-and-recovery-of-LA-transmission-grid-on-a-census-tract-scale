"""Write source-bounded measurement conclusions from completed audit tables."""
from common import *
import pandas as pd,platform,importlib.metadata
from audit_values import CANDIDATES,CONTEXT

LABELS=dict(canopy_2022_fraction='2022 published urban tree canopy',parks_all_published_fraction='2022 published Access to All Parks',parks_good_published_fraction='2022 published Access to Good Parks',electric_heating_share='ACS 2022 electric principal heating share',housing_5plus_share='ACS 2022 units in structures with 5+ units')
URLS={
 'canopy':'https://services1.arcgis.com/gGHDlz6USftL5Pau/ArcGIS/rest/services/Statistics_by_Census_Tract_wCalES4/FeatureServer/0',
 'raster':'https://tiles.arcgis.com/tiles/gGHDlz6USftL5Pau/arcgis/rest/services/UrbanTreeCanopy_CA2022/MapServer',
 'parks':'https://la.myneighborhooddata.org/2023/03/parks-access/',
 'heating':'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/B25040_06.csv.zip',
 'housing':'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/B25024_06.csv.zip',
 'vre':'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/documentation/5-year/2018-2022_Variance_Replicate_Table_Documentation.pdf',
 'svi':'https://www.atsdr.cdc.gov/place-health/media/pdfs/2024/08/SVI2020Documentation_08.05.22.pdf'}

def tab(df):return df.to_markdown(index=False,floatfmt='.4f')
def run():
    f=pd.read_csv(lp(OUT/'LIVING_ENVIRONMENT_VALUES_2315.csv'),dtype={'tract_id':str},float_precision='round_trip').set_index('tract_id');ref=f.loc[f.reference2287]
    d=pd.read_csv(lp(OUT/'CANDIDATE_DISTRIBUTIONS.csv'));q=d.loc[d.cohort.eq('reference2287')&d.candidate.isin(CANDIDATES)].copy()
    corr=pd.read_csv(lp(OUT/'CANDIDATE_REDUNDANCY.csv'));coverage=pd.read_csv(lp(OUT/'SOURCE_MATCH_AND_COVERAGE.csv'))
    u=pd.read_csv(lp(OUT/'ACS_UNCERTAINTY_AUDIT.csv'),dtype={'tract_id':str});ur=u.loc[u.reference2287]
    geo=json.loads(lp(OUT/'CANOPY_GEOGRAPHY_INTERPRETATION_QA.json').read_text());park=json.loads(lp(OUT/'PARKS_NUMERICAL_QA.json').read_text())
    stats=[]
    for c,g in ur.groupby('candidate'):
        stats.append(dict(candidate=c,n=len(g),median_MOE90_pp=100*g.MOE90.median(),P90_MOE90_pp=100*g.MOE90.quantile(.9),MOE90_gt_5pp_n=int(g.MOE90_gt_5pp.sum()),MOE90_gt_10pp_n=int(g.MOE90_gt_10pp.sum()),MOE90_gt_10pp_percent=100*g.MOE90_gt_10pp.mean(),CV_gt_30percent_n=int(g.CV_gt_30pct.sum()),undefined_CV_zero_estimate_n=int(g.CV.isna().sum()),boundary_variance_n=int(g.boundary_model.sum()),denominator_CI90_includes_zero_n=int(g.denominator_CI90_includes_zero.sum()),zero_replicate_denominator_n=int(g.undefined_replicate_denominator_count.gt(0).sum())))
    us=pd.DataFrame(stats);save('ACS_UNCERTAINTY_SUMMARY.csv',us)
    roles={
      'CANOPY_LA_0.geojson':'published numeric canopy + source geometry', 'CANOPY_LA_1000.geojson':'published numeric canopy + source geometry', 'CANOPY_LA_2000.geojson':'published numeric canopy + source geometry',
      'PARKS_DOWNLOAD_0.payload':'published numeric park proximity', 'B25040_06.csv.zip':'official numeric heating estimates, MOEs,80 replicates', 'CDC_SVI2020_CALIFORNIA.csv':'official numeric SVI2020 raw component diagnostic', 'CENSUS2020_URBAN_LA.geojson':'official 2020 urban-area support geometry; not canopy pixels',
      'CANOPY_VIEWER.json':'excluded: old2012 viewer, not2022 canopy', 'CANOPY_VIEWER_DATA.json':'excluded: old2012 viewer, not2022 canopy', 'CANOPY_URBAN_SERVICE.json':'excluded: related UFIA urban service, not established2022 support',
      'CANOPY_URBAN_LAYER.json':'failed ArcGIS layer route', 'ACS_B25040_LA.json':'semantic failure:200 Missing Key HTML; not numeric estimates', 'CDC_SVI2020_CA.csv':'404 failed old CDC route', 'CDC_SVI2020_CA_VALID.csv':'semantic failure:200 app-shell HTML; not CSV', 'PARKS_API_METADATA.payload':'404 failed metadata route', 'CANOPY_RASTER_ITEM_DATA.json':'empty optional item data; not numerical raster'}
    acq=json.loads(lp(OUT/'ACQUISITION_RECORDS.json').read_text());rows=[]
    for name in sorted({r['file'] for r in acq}):
        r=[x for x in acq if x['file']==name][-1];p=lp(OUT/'sources'/name)
        rows.append(dict(file='sources/'+name,role=roles.get(name,'metadata/documentation/discovery only'),url=r['url'],query=json.dumps(r.get('params'),sort_keys=True),acquisition_utc=r['utc'],HTTP_status=r.get('status_code'),transport_success=r.get('success'),bytes=p.stat().st_size if p.exists() else 0,sha256=sha(p) if p.exists() else '',numeric_measurement_used=name in ['CANOPY_LA_0.geojson','CANOPY_LA_1000.geojson','CANOPY_LA_2000.geojson','PARKS_DOWNLOAD_0.payload','B25040_06.csv.zip','CDC_SVI2020_CALIFORNIA.csv']))
    ar=json.loads(lp(OUT/'ARCHIVED_LAND_REUSE.json').read_text());rows.append(dict(file='sources/ARCHIVED_STUDY_LAND.gpkg',role='verified cached2020 tract land masks; four unresolved excluded from land comparisons',url='archived local derivative; exact archived record in ARCHIVED_LAND_REUSE.json',bytes=ar['bytes'],sha256=ar['sha256'],numeric_measurement_used=False))
    save('SOURCE_URLS_AND_CHECKSUMS.csv',rows)
    admission=[
      ('housing_5plus_share','ADMIT','eligible primary coordinate for residential configuration','all housing units; 5+ structure units','verified existing80-VRE method; related to SOVI10+units and population density; not building count or all-use physical form'),
      ('electric_heating_share','ADMIT','sensitivity coordinate for principal residential heating dependence','occupied housing units using electricity as main heating fuel','strong sampling uncertainty; specific use of electricity, not general dependence; moderate housing overlap'),
      ('canopy_2022_fraction','CONDITIONAL','ecological canopy sensitivity/description; no unqualified primary replacement','published urban-canopy analysis area, mostly close to tract land; exact partial-area rule unresolved','whole-area greenness not resident shade; residual land geometry differences and partial urban support'),
      ('parks_all_published_fraction','CONDITIONAL','published descriptive proximity until spatial apportionment verified','published 2020 population denominator; numerator spatial apportionment unresolved','cannot verify resident weighting versus tract overlay; geometric half-mile is not pedestrian network'),
      ('parks_good_published_fraction','DESCRIPTIVE_ONLY','separate published condition-qualified description','same unresolved proximity allocation plus park-condition filter','rating criteria, assessor objectivity and vintage not established; not an objective primary living-environment coordinate')]
    aa=pd.DataFrame([dict(candidate=c,measurement_status=s,recommended_role=r,construct=x,qualification=y) for c,s,r,x,y in admission]);save('CANDIDATE_ADMISSION.csv',aa)
    inp=json.loads(lp(OUT/'INPUT_HASHES.json').read_text());prefix=PREFIX
    def ih(rel):return inp[prefix+rel]['sha256']
    text('DATA_AVAILABILITY_AND_PROVENANCE.md',f'''
# Living-environment measurements: availability and provenance

This package audits measurements only. CORE3/W1 is an archived reference and is not an approved final feature set. No clustering, weight selection, recovery computation, manuscript editing or promotion was performed. The isolated branch is analysis/stage7-living-environment-audit-20261011, based on {BASELINE}.

## Exact cohorts and inherited inputs

The unchanged model universe contains 2,315 GEOIDs, the residential master 2,291, and the complete archived reference 2,287. Every comparison joins on an11-digit string GEOID. Ordered memberships are in COHORT_IDENTITIES.npz and BASELINE_IDENTITY_QA.json. The four geometry-unresolved residential records remain in the master and have their published non-geometric values preserved: {', '.join(UNRESOLVED)}. Their old geometry exclusion status is not removed and no class labels are assigned. New published canopy values for them do not validate their existing physical land masks.

Reused parent values and source SHA-256:

- candidate_admission_rebuild_20261010/CANDIDATE_VALUES_2315.csv: {ih('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_2315.csv')}. Housing configuration, EMC2022, frozen SOVI and original population/density remain numerically unchanged.
- final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv: {ih('final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv')}. Used only for residential and complete-reference identities; cluster labels and recovery outcomes were not read for admission.
- validation/sources/B25024_06.csv.zip: {ih('validation/sources/B25024_06.csv.zip')}; official cached2022 ACS California tract VRE, not downloaded again.
- validation/ACS_TRACT_VALIDATION.csv: {ih('validation/ACS_TRACT_VALIDATION.csv')}; original housing estimates, boundary rules and MOEs reproduced within 1e-13.

Full original and new source byte hashes, URLs, request parameters and timestamps are in INPUT_HASHES.json, SOURCE_URLS_AND_CHECKSUMS.csv and ACQUISITION_RECORDS.json. HTTP success is recorded separately from numerical validity. Software versions are in SOFTWARE_VERSIONS.json.

## A. Published2022 urban tree canopy

[USFS/CALFIRE tract layer]({URLS['canopy']}) supplies FIPS, PctCan22, CanoAcr22, AREA22 and PctCan18. Its2,486 LA records have unique11-digit GEOIDs. The [2022 raster service]({URLS['raster']}) and official CALFIRE launch material identify0.6-m2022 NAIP imagery and a deep convolutional model, analyzed for2020 Census urban areas. Publication/update dates in2025 are not observation years. The related2012 viewer and a different UFIA urban-area service were investigated but excluded. Field aliases contain inconsistencies; field identities and actual arithmetic, rather than an alias alone, define the values.

The exported value is PctCan22/100. Numerically CanoAcr22/AREA22 =0.00024711 (the source's approximate acre-per-m2 conversion), so AREA22 is canopy-class area, not the total tract denominator. Inferring the analysis denominator as AREA22/(PctCan22/100) agrees closely with source polygon area in most records, but {geo['source_analysis_fraction_lt_0_99_n']} of 2,287 reference records have a ratio below0.99. This is a diagnostic, not a new admission cutoff. The exact urban clipping/zone rule and LA-specific classification error are not supplied by the inspected metadata. Census 2020 urban geometry provides a support check, not proof of every denominator; observed edge discrepancies remain in CANOPY_ANALYSIS_SUPPORT_AUDIT.csv. No canopy pixels were reclassified or substituted.

Comparing source polygons with original whole-tract geometry gives {geo['whole_tract_IoU_lt_0_9_n']} reference records below0.90 IoU. Much of this comparison includes water in the frozen polygon. Reusing the exact previously validated land-mask bytes reduces that count to {geo['land_IoU_lt_0_9_n']}; land IoU median = {geo['land_IoU_quantiles']['0.5']:.6f}, minimum = {geo['land_IoU_quantiles']['0.0']:.6f}. Residual differences are explicitly retained, not labeled automatically as new-vintage boundary changes. CANOPY_GEOGRAPHIC_SUPPORT_FLAGS.csv gives exact GEOIDs, geometry overlap, displacement and population. No geometry, mapping or existing environmental measurement changed.

All 2,291 residential GEOIDs have published canopy values. The two absent full-domain records are06037980020 and06037980026, outside the residential cohort. Urban-analysis/whole-tract canopy remains an ecological area measurement. It does not identify where residents live, shade along pedestrian routes, or personal shade exposure. Large unoccupied areas and partial urban coverage can change its denominator and interpretation.

## B. Published parks proximity

[USC NDSC2022 Parks Access]({URLS['parks']}) has a working download link. The actual CSV contains 2,498 unique LA2020 tract identities, year2022, population denominator, fractional all/good access counts and corresponding percentages. geoid20 lost one leading zero in its serialized numeric form; restoration to11 digits reproduces the complete GEOID field exactly. The population denominator matches the canopy layer's2020 Census population exactly on 2,313/2,313 comparable model records. This is not the frozen restoration weighting population, which remains untouched.

Published percentages reproduce100*access_count/denom_total_pop within {max(park['published_percentage_vs_count_ratio_max_difference_pp'].values()):.8f} percentage points. Tiny float-storage overshoots above100 are retained and flagged (all parks:{park['all_rounding_overshoot_n']}; good parks:{park['good_rounding_overshoot_n']} full-domain records), rather than silently clipped. Five zero-population full-domain tracts have undefined proportions; all residential/reference tracts have usable published values.

The documentation calls the result a percentage of residents within half a mile, but describes only park buffers overlaid on tracts. Neither the download nor retrieved county reports specify block/population-surface weighting or an exact area-based allocation formula. Fractional counts and a population denominator cannot distinguish genuine population weighting from tract population multiplied by a buffered-area fraction. Consequently the exported variable is named published_fraction, not verified resident access. No substitute park-access calculation was constructed. A geometric half-mile buffer is not half-mile pedestrian-network accessibility. Good Parks additionally depends on condition ratings whose rule, date and objectivity are not established for this download; it remains separate and descriptive.

## C/D. ACS heating and housing configuration

Both represent2018-2022 ACS 5-year estimates on 2020 tract geography, not a single2022 census of buildings. Electric heating = B25040_004E/B25040_001E, electricity as principal heating fuel divided by occupied housing units. Housing5+ = sum(B25024_006E...009E)/B25024_001E, units in5+unit structures divided by all housing units. Their denominators differ; neither is a fraction of physical buildings.

The Census point-estimate API redirected to Missing Key HTML despite HTTP200. Its bytes are recorded as a failed numerical route. The official [B25040 VRE archive]({URLS['heating']}) was successfully retrieved and contains original ESTIMATE/MOE fields and80 corresponding variance replicates. The [official 2022 VRE documentation]({URLS['vre']}) supports covariance-aware derived-ratio uncertainty. Existing housing VRE estimates were independently reproduced and retained.

For valid ratio p=N/D, SDR variance = (4/80)*sum_r(p_r-p)^2, with the same indexed numerator/denominator replicates. Undefined replicate denominators follow the official rule p_r=0. For p=0, p=1 or zero replicate SE, official boundary variance is used: p*=min(0.5,2.3*AW/D), SE=sqrt[p_ast*(1-p_ast)*AW/D], with archived California average weight AW=16. MOE90=1.645*SE. Display confidence bounds are truncated to[0,1] only for presentation; raw estimates, SE and MOE remain unchanged. No approximation that ignores ratio covariance replaces the original housing method.

{tab(us)}

Five-/ten-percentage-point MOE and30% CV flags are transparent diagnostic thresholds, not exclusion gates. No high-MOE observation is deleted. CV is undefined when p=0; such cases remain in the master. Full-domain zero denominators produce24 undefined heating and23 undefined housing fractions, mostly special nonresidential9800 tracts, with every exact GEOID in MISSING_INVALID_GEOIDS.csv. No null was replaced by zero.

Heating measures dependence on electricity for principal residential heating only. It is not total electricity dependence, cooling prevalence, backup-power availability, current demand or an outage consequence. Housing5+ describes residential unit configuration, not comprehensive built environment.

## Shared sources and SOVI components

Frozen FEMA v1.19 SOVI remains unchanged. Its CDC 2020 source includes housing/transportation information. [CDC 2020 dictionary]({URLS['svi']}) defines EP_MUNIT=(DP04_0012E+DP04_0013E)/E_HU*100, the10+unit share from 2016-2020 ACS. The5+measure uses a nested housing category and an overlapping later survey period. This is conceptual and source overlap, not an exact algebraic duplicate across releases.

The current official CDC public download API provided actual California 2020 data after the old static URL failed. Only raw housing/transportation components are used diagnostically. California RPL rankings are state percentiles and are not substituted for frozen national SOVI. Component uncertainty is not estimated by treating the two releases as independent samples. The80 ACS replicate correlations are measurement-sensitivity results, not80 independent tract cohorts or a confidence interval for spatially dependent tract correlations.

## Failures and unresolved evidence

- Census B25040 point API: HTTP200 Missing Key HTML; replaced by official VRE numerical file without bypassing authentication.
- Old CDC static route:404; another route returned HTML; neither was parsed as data. Official public webapi supplied actual CSV.
- USC guessed dataset metadata endpoint:404. Primary numeric download works, but spatial apportionment and Good Parks rating details remain unresolved.
- Optional ArcGIS item/data was empty; unrelated old services were not numerical substitutes.
- Canopy partial-area definition, residual land geometry differences and local classification uncertainty remain qualified. Count/coverage is not validation accuracy.

No source acquisition failure was converted into a fabricated measurement. The audit is complete as a measurement decision package; the specific unresolved definitions prevent unconditional admission of park proximity and canopy as resident-level primary coordinates.
''')
    q['candidate']=q.candidate.map(LABELS)
    for col in ['minimum','P10','P25','median','P75','P90','maximum','mean','standard_deviation','zero_fraction']:q[col]*=100
    text('LIVING_ENVIRONMENT_CONSTRUCT_DECISION.md',f'''
# Living-environment construct decision

## Decision

Housing5+ is a defensible residential-configuration measurement. Electric principal heating is a defensible but use-specific measurement best retained as a sensitivity coordinate at present. Published canopy can describe ecological urban greenness conditionally; it does not yet establish resident shade exposure. All Parks remains conditional because the spatial allocation statistic is not verified. Good Parks is descriptive only. None is promoted into Stage7, and no new formal feature set is selected.

{tab(aa)}

Two verified measurements are preferable to forcing three. A subsequent author-approved model could examine housing configuration and specific electric-heating dependence as distinct constructs, with their survey uncertainty and shared-source overlap disclosed. This audit does not prescribe their joint weights or require using both. Canopy and parks should not automatically replace the archived land-use or built-surface coordinates: they measure greenness and proximity, not those physical constructs. The current CORE3/W1 partition has no default approval status.

## Actual reference distributions

All five published indicators have2,287/2,287 values on the archived reference. Percent and percentage-point units below; exact fractions are in the CSV. Statistics are unweighted across tracts, not across residents. Published parks endpoint roundoff is retained.

{tab(q[['candidate','minimum','P10','P25','median','P75','P90','maximum','mean','standard_deviation','zero_fraction']])}

All Parks has a ceiling-heavy distribution (median 97.36%, P75100%); Good Parks has36.29% exact zeros. These describe the published measurements, not evidence that almost all residents have equivalent pedestrian access. Tree canopy has no exact zeros on the reference and a right tail. Extreme GEOIDs and their density/population are exported, not removed as inconvenient observations.

## Statistical versus construct redundancy

On identical2,287 GEOIDs, electric heating versus housing5+ has Pearson r=0.6320 and Spearman rho=0.6012. Controlling housing5+, EMC, log1p density and SOVI leaves59.80% of heating variance unexplained (conditional VIF1.67). This permits distinct heating interpretation but is not proof of independent information or a reason to call it general electricity dependence.

Housing5+ correlates with log density at r=0.4971/rho=0.5476 and SOVI at r=0.2008/rho=0.2855. More directly, housing5+ correlates with CDC 2020 EP_MUNIT at r=0.9476/rho=0.9518. Thus the modest aggregate SOVI correlation must not hide nested housing content and shared ACS source dependence. Heating and housing have different denominators and neither is an exact deterministic function of the other.

Canopy correlates negatively with EMC(r=-0.5531), log density(-0.3986) and SOVI(-0.5280). Conditional on the inherited housing/context measurements,56.99% of canopy variance remains. This is ecological overlap, not causal protection from outages or proof of resident shade. Boundary/analysis-support and low-density sensitivity rows preserve the exact subset GEOIDs and N; no subset replaces the main measurements.

Weak All Parks/Good Parks marginal correlations with inherited variables cannot resolve their definition problems. Good access is nested in all access, with r=0.3995, and both share park geometry, denominator and spatial allocation. Condition filtering adds a different, potentially subjective construct. Derived published percent and access_count/denominator are the same quantity, never separate primary inputs. The two canopy area units are conversions of the same canopy class, not independent indicators.

## Precision sensitivity

Electric heating has568/2,287(24.84%) records with MOE90>10 percentage points; housing5+ has211/2,287(9.23%). Median MOEs are8.48 and6.75 points. Both estimates remain in the data. Across the80 corresponding raw variance replicates, heating/housing Pearson values range0.6120-0.6309; that is a sensitivity range, not a confidence interval or independent replication. Boundary cases require the extra official variance rule, so raw replicate ranges do not summarize every source of sampling uncertainty.

Filtering both MOEs to<=5 points would leave only 76 tracts and substantially change the observed relationship (Pearson0.9399, Spearman0.3831). This demonstrates selection sensitivity, not superiority of a filtered model. No such deletion is recommended. Formal survey MOEs do not quantify canopy classification error, uncertain park allocation or shared-source systematic biases.

## Remaining blockers and scope

For canopy, {geo['land_IoU_lt_0_9_n']} reference tracts have land IoU<0.90 and {geo['source_analysis_fraction_lt_0_99_n']} have source analysis area<99% of source polygon. These are diagnostic flags, not retrospectively optimized acceptance thresholds. The exact canopy zone rule and actual residential location support remain unresolved. For parks, the downloaded population fields and buffer narrative still do not establish population weighting. Good Parks rating lineage/objectivity remains unverified.

No correlation with recovery outcomes, existing labels, silhouette, ARI or class separation was used. Statistical association, common source, conceptual overlap and algebraic duplication are recorded separately. No causal assertion, final clustering choice, weight decision or manuscript claim follows from this audit.
''')
    text('README.md','''
# Stage7 living-environment measurement audit

Start with LIVING_ENVIRONMENT_CONSTRUCT_DECISION.md, DATA_AVAILABILITY_AND_PROVENANCE.md and CANDIDATE_ADMISSION.csv. CORE3/W1 is an archived reference, not an approved final feature set.

Values are in LIVING_ENVIRONMENT_VALUES_2315.csv, LIVING_ENVIRONMENT_VALUES_RESIDENTIAL_2291.csv and LIVING_ENVIRONMENT_VALUES_REFERENCE_2287.csv. Fractions, original survey counts, uncertainty and continuous geometry/support flags are retained. Four unresolved geometry IDs remain in the residential master; no labels or missing physical variables are imputed.

Required coverage/distribution/uncertainty/redundancy tables are present with exact comparison GEOID sets. Figures are under figures/, with native185-mm vector PDFs,600-dpi page PNGs and rendered native-width previews. These are measurement diagnostics, not replacements for manuscript figures.

Reproduction using the recorded Python environment: verify_sources.py (checks/replays ledger only when requested), audit_values.py (reads original source byte identities and already acquired measurements), finish_measurement_checks.py (reuses cached land-mask bytes), write_reports.py, render_figures.py, then pytest test_measurements.py. No new source request is needed for cached reproduction. audit_values.py repeats only tract-level measurement/support arithmetic; it never reruns restoration, scheduling, mapping, GA or clustering. Original cached inputs are resolved by exact Git/LFS hashes; INPUT_HASHES.json records actual local byte locations. Source downloads are snapshot data, not promises that a live URL always returns identical bytes.

Run pytest with a workspace-local --basetemp. See TEST_RESULTS.txt, NUMERICAL_AND_RENDER_QA.json, PRESERVATION_BEFORE/AFTER.json and REMOTE_DELIVERY_VERIFICATION.json. Only this new package is committed; the original checkout/index,950 protected scientific files and prior audit packages remain unchanged.
''')
    dump('SOFTWARE_VERSIONS.json',dict(Python=platform.python_version(),**{k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy','geopandas','shapely','pyproj','matplotlib','PyMuPDF','requests','pytest']}))
    log('Source, uncertainty and construct decisions written from actual tables; no formal feature selection or promotion.')
if __name__=='__main__':run()
