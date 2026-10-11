"""Summarize completed measurements and remaining floor-area evidence gaps."""
from common import *
import pandas as pd, numpy as np
from write_reports import write, table

def main():
 f=pd.read_csv(OUT/'CANDIDATE_VALUES_2315.csv',dtype={'tract_id':str}).set_index('tract_id')
 r=pd.read_csv(OUT/'CANDIDATE_REGISTER.csv').set_index('candidate_id')
 residential=pd.read_csv(OUT/'CANDIDATE_VALUES_RESIDENTIAL_2291.csv',dtype={'tract_id':str}).set_index('tract_id')
 e=json.loads((OUT/'EPA_ACTIVITY_CROSSWALK_QA.json').read_text(encoding='utf-8'))
 s=json.loads((OUT/'SCAG2020_GEOMETRY_AND_COVERAGE_QA.json').read_text(encoding='utf-8'))
 a=json.loads((OUT/'ASSESSOR_FLOOR_AREA_AND_OWNERSHIP_QA.json').read_text(encoding='utf-8'))
 p=pd.read_csv(OUT/'ASSESSOR2022_PARCEL_GEOMETRY_IDENTITY_SAMPLE.csv')
 rows=[]
 for key,cov in [('assessor2022_gross_floor_area_ratio',''),('epa_household_job_activity_mix','epa_donor_land_coverage'),('scag2020_classified_land_entropy','scag2020_classified_land_coverage')]:
  rows.append({'candidate':key,'disposition':r.loc[key,'disposition'],
    'valid_full_2315':int(f[key].notna().sum()),'valid_residential_2291':int(residential[key].notna().sum()),
    'median_residential_coverage':float(residential[cov].median()) if cov else 'not certified',
    'scope_or_gap':r.loc[key,'admission_condition_or_exclusion_reason']})
 summary=pd.DataFrame(rows);summary.to_csv(OUT/'PENDING_DATA_COMPLETION_SUMMARY.csv',index=False)
 write('PENDING_DATA_COMPLETION_AUDIT.md',f'''# Three pending measurements: actual follow-up results

Starting analysis commit: `561283f50f110e0897650857241880d19d904c67`. Output remains on `analysis/stage7-candidate-admission-rebuild-20261010`.

{table(summary)}

SCAG2020 and EPA now have actual numeric tract outputs, qualified as CONDITIONAL. Assessor gross FAR remains PENDING_DATA after a completed evidence audit; a raw Main Square Footage sum is not substituted. Admission is not final feature selection. No clustering, weights, formal scientific outputs, manuscript or figures were changed.

The 2,315 full-domain and 2,291 residential GEOID masters retain exact membership and order. Four unresolved target land masks stay null for the new geometry-dependent values. Non-geometric Assessor diagnostics remain available. Read EPA_ACTIVITY_GEOGRAPHIC_CONVERSION.md, SCAG2020_MEASUREMENT_QA.md and ASSESSOR_FLOOR_AREA_AND_DUPLICATE_ATTRIBUTION.md for source-specific qualifications.
''')
 write('EPA_ACTIVITY_GEOGRAPHIC_CONVERSION.md',f'''# EPA activity counts converted to study tracts

Official polygon layer: https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer/7
Method definition: https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1014W9I.TXT

The actual SLD v3 layer describes 2018 Census block-group polygons. Its misleadingly named GEOID20 alias refers to 2018 block-group identifiers, not 2020 boundaries. Household counts use ACS 2014–2018 and jobs use 2017 LODES. Cached source rows: {e['cached_source_records']:,}; returned polygon donors: {e['donors']:,}. The {e['source_records_without_donor_polygon']} missing source records all have zero households and zero jobs; their identifiers and counts are retained in EPA_SOURCE_RECORDS_WITHOUT_DONOR_POLYGON.csv. No positive activity counts were dropped. {e['source_GE0ID10_vs_2018_ID_changes']} donor IDs differ from their older GEOID10 identifiers. Numeric counts on every returned donor match the retained source exactly; max differences: {e['source_numeric_match_max_differences']}.

For donor j and target tract t, w_jt = area(donor land intersect target tract) / area(whole donor land). Land removes the retained 2020 Census water polygons. Source and target vintages therefore remain distinct. Allocate household and each of five job-category counts with w_jt, aggregate counts by target GEOID, then calculate -sum(p log p)/log(number of positive activity categories). A single occupied category has entropy zero; zero total activity is undefined. A fixed-log(6) expression is retained only as a definition diagnostic. Source D2A_EPHHM is reproduced on donors with at least two positive categories; max absolute error {e['source_entropy_reproduction_max_difference']:.3g}.

This is uniform-within-donor-land count estimation, not observed target-tract activity. No entropy averaging, GEOID-prefix matching, unsupported-area renormalization or target-count imputation occurs. The actual crosswalk has {e['crosswalk_rows']:,} intersections; {e['split_donors']:,} donors span multiple target tracts. Donor activity allocated outside the county target universe remains an explicit residual. Count conservation is checked for each category using all county target tracts plus outside-target residuals, before selecting the study universe; it is not a claim that all county activity falls within the 2,315 study tracts.

Any positive intersection counts as a split, including tiny cross-vintage boundary slivers. Only {e['donors_with_at_least_two_one_percent_intersections']:,} donors have two intersections each at least 1% of donor land; that threshold describes slivers only and changes no weights. Source donor-land summed area exceeds its union by {e['donor_land_overlap_m2']:,.3f} m² ({100*e['donor_land_overlap_m2']/e['donor_land_sum_m2']:.6f}% of summed donor land). The service polygons therefore are not a perfectly disjoint cadastral truth. Coverage uses union donor land intersecting the identical target land mask, not summed whole-tract donor intersections divided by another mask. EPA_TARGET_LAND_SUPPORT_DIAGNOSTICS.csv retains those support differences. Count conservation confirms arithmetic, not geographic allocation accuracy.

Actual county source counts: {e['county_source_totals']}.
Target plus outside totals: {e['county_target_plus_outside_totals']}.
Study valid entropy: {e['full_valid']:,}/2,315; residential: {e['residential_valid']:,}/2,291.
Continuous donor-land coverage quantiles: {e['target_land_coverage_quantiles']}.
Fraction of allocated activity originating in split donors: {e['split_activity_fraction_quantiles']}.

Disposition: CONDITIONAL. This measures household/job activity composition, not parcel land-use composition. Survey error, job geocoding, within-donor nonuniformity, historical vintages and boundary changes are not quantified by geometric coverage. Coverage is not accuracy. The four unresolved land masks remain null; no universal coverage threshold or clustering-derived admission rule was invented. Source payload and crosswalk hashes are retained for reproduction.
''')
 write('SCAG2020_MEASUREMENT_QA.md',f'''# SCAG 2020 numeric land-use overlay

Official ALU20 service: https://rdp.scag.ca.gov/mapping/rest/services/Housing/2020_Annual_Land_Use/MapServer/0

{s['raw_records']:,} LA parcel records were acquired once, with complete queried OBJECTID identity and byte hashes for all chunks. ALU20 is the 2020 classified snapshot; later contextual fields/service updates do not date the land-use observation. SCAG2020_SOURCE_CODE_MAPPING.csv records the official ALU20 code descriptions and the same eleven broad classes used for the qualified 2019 comparison. Mixed-use records remain an explicit class rather than an invented disaggregation. Unknown/blank codes remain unclassified. Missing observed dictionary codes: {s['dictionary_missing_codes']}.

Normalized identical geometries: {s['exact_geometry_duplicates']:,} repeat records; {s['different_ALU20_duplicates']:,} have differing detailed codes. Identical geometries within one broad class count once; broad-class conflicts are withheld. The {s['stack_gt1_records']:,} STACK>1 rows were not indiscriminately deleted. Nonidentical geometries are retained, unioned within classes, and cross-class overlap is withheld from competing classes. {s['invalid_repaired']:,} invalid source geometries were repaired; failed overlay precision repairs are individually recorded in SCAG2020_GEOMETRY_AND_COVERAGE_QA.json.

Actual EPSG3310 intersections use study tract polygons and the independently retained land mask; GEOID20 block codes are not tract membership assignments. Entropy is -sum(p_i log p_i)/log(11), where p_i uses exclusive classified parcel land. Tract-land shares, classified shares, unknown area, ambiguous area, mapped water and parcel gaps accompany it. These diagnostic areas may overlap and must not be summed as an exclusive missingness partition. Coverage quantiles: {s['classified_coverage_quantiles']}. Ambiguous land area across the study: {s['ambiguous_land_area_m2']:,.3f} m². Parcel gaps relative to the whole target tract polygon: {s['parcel_gap_area_m2']:,.3f} m²; this gap denominator includes water and is explicitly distinct from classified-land coverage.

Entropy values: {int(f.scag2020_classified_land_entropy.notna().sum()):,}/2,315 and {int(residential.scag2020_classified_land_entropy.notna().sum()):,}/2,291 residential. Four unresolved land masks remain null. Exclusive classified areas cannot exceed tract land; shares and entropy are recomputed and tested. Geometry coverage is not classification accuracy.

Disposition: CONDITIONAL for a historical classified-land composition measure. The actual 2020 extraction closes the previous numeric-overlay gap. It does not certify full-land composition, synchronize 2020 to 2022, or authorize automatic replacement of SCAG2019. The same-GEOID 2019/2020 comparison is supplied without choosing a version by old labels or recovery correlation.
''')
 write('ASSESSOR_FLOOR_AREA_AND_DUPLICATE_ATTRIBUTION.md',f'''# Assessor 2022 floor-area semantics and identity audit

All {a['county_assignment_records']:,} assigned assessment records reuse the previously acquired single RollYear2022 cache; {a['unique_AIN']:,} AINs are unique. Only nonpersonal assessment attributes are used. Same-coordinate groups with positive main area: {a['shared_coordinate_groups']:,}; repeated nonidentity attributes flag {a['same_nonidentity_attribute_repeat_records']:,} records. Multi-building-data-line records: {a['multiline_records']:,}; condo-coded records: {a['condo_records']:,}.

Per-tract diagnostics retain actual positive Main Square Footage, shared-point/condo/multiline/repeated-attribute area fractions, and the explicitly restricted single-line, noncondo, nonshared-point area subset. The amount that a naive coordinate collapse would remove is reported as a warning diagnostic, not a valid lower bound or deduplication method. No assessment records were deleted from the existing measurement.

Same-year parcel geometry verification selected the 20 largest shared condo-coordinate groups and 20 other shared condo groups with fixed seed20261010. This is a bounded identity probe, not a representative countywide validation sample. {a['parcel_geometry_sample_groups']} groups were checked; {a['sample_shared_geometry_groups']} groups have fewer unique normalized cadastral geometries than returned AIN identities. Returned assessment identities: {int(p.unique_returned_ain.sum()):,}; returned parcel rows: {int(p.returned_parcel_rows.sum()):,}; roll years: {sorted(set(';'.join(p.roll_years.astype(str)).split(';')))}. A shared cadastral footprint does not identify a shared physical building or establish whether unit/common areas are duplicated. Missing returned AINs remain visible in the sample table.

The inspected official dictionary labels SQFTmain as Main Square Footage and totBuildingDataLines as building-data-line count. It does not certify the floor-area inclusion/exclusion convention, independently identify every structure, or resolve condo ownership/common-area accounting. AIN identifies an assessment parcel/account, not necessarily one physical building. The public HD22 housing layer lacks certified all-use gross-floor-area fields; the inspected XREF and 2022 parcel layer provide assessment/cadastral identities rather than the missing structure-area inventory. Targeted public catalog searches are retained; absence from these inspected endpoints is not proof that no appropriate dataset exists elsewhere.

Remaining required evidence:
{chr(10).join('- '+x for x in a['missing_required_evidence'])}

Disposition: PENDING_DATA. `assessor2022_gross_floor_area_ratio` remains null on all 2,315 tracts. Existing Main Square Footage/land stays DESCRIPTIVE_ONLY. The restricted subset is diagnostic, not countywide FAR. Shared coordinates, identical area/age attributes or parcel geometries cannot justify building-level deduplication. No floor counts are inferred from heights and no missing exempt/government values are replaced.
''')
 # Extend the source access ledger with the exact bytes newly used this round.
 ledger=pd.read_csv(OUT/'SOURCE_ACCESS_AND_VERSION_AUDIT.csv')
 new=[]
 source_urls={
  'SCAG2020_layer_current.json':'https://rdp.scag.ca.gov/mapping/rest/services/Housing/2020_Annual_Land_Use/MapServer/0?f=pjson',
  'EPA_SLD_actual_polygon_metadata.json':'https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer/7?f=pjson',
  'Assessor2022_parcels_metadata.json':'https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcels_2022Roll/FeatureServer/0?f=pjson',
  'Assessor_HD22_actual_layer_metadata.json':'https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/ResidentialParcels_LACounty_010924download_allCB20_HD22_attributes/FeatureServer/1?f=pjson',
  'Assessor_XREF_metadata.json':'https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_XREF/FeatureServer/0?f=pjson',
  'Assessor_public_catalog_search.json':'https://www.arcgis.com/sharing/rest/search?f=json&num=100&q=orgid%3ARmCCgQtiZLDCtblq%20AND%20%28assessor%20OR%20building%29',
  'Assessor_floor_search.json':'https://www.arcgis.com/sharing/rest/search?f=json&num=100&q=orgid%3ARmCCgQtiZLDCtblq%20AND%20%28%22floor%20area%22%20OR%20%22building%20data%22%20OR%20%22square%20footage%22%29'}
 for name in ['SCAG2020_layer_current.json','EPA_SLD_actual_polygon_metadata.json','Assessor2022_parcels_metadata.json','Assessor_HD22_actual_layer_metadata.json','Assessor_XREF_metadata.json','Assessor_public_catalog_search.json','Assessor_floor_search.json']:
  file=OUT/'source_evidence'/name
  new.append({'source_id':'PENDING_COMPLETION:'+name,'official_url':source_urls[name],
    'access_result':'ACTUAL_PUBLIC_METADATA; numeric status in candidate-specific QA',
    'original_bytes_sha256':sha(file),'payload_bytes':file.stat().st_size})
 ledger=pd.concat([ledger.loc[~ledger.source_id.str.startswith('PENDING_COMPLETION:',na=False)],pd.DataFrame(new)],ignore_index=True)
 ledger.to_csv(OUT/'SOURCE_ACCESS_AND_VERSION_AUDIT.csv',index=False)
 for name in ['CANDIDATE_DEFINITIONS.md','DEPENDENCY_AND_REDUNDANCY.md','ADMITTED_SHORTLIST_AND_REPLACEMENTS.md','README.md']:
  text=(OUT/name).read_text(encoding='utf-8')
  if 'Follow-up measurement evidence:' not in text:
   text+='\n\nFollow-up measurement evidence: PENDING_DATA_COMPLETION_AUDIT.md and the three source-specific QA notes. EPA values are spatially allocated estimates, SCAG2020 is measured classified parcel land, and Assessor gross FAR remains unmeasured. No automatic feature substitution or weight change is adopted.\n'
  write(name,text)
 dump('PENDING_COMPLETION_DERIVED_HASHES.json',{name:sha(OUT/name) for name in ['CANDIDATE_REGISTER.csv','CANDIDATE_VALUES_2315.csv','CANDIDATE_VALUES_RESIDENTIAL_2291.csv','EPA_TRACT_ACTIVITY_MIX.csv','EPA_DONOR_TO_TRACT_CROSSWALK.csv','SCAG2020_TRACT_LAND_USE.csv','ASSESSOR2022_FLOOR_IDENTITY_DIAGNOSTICS.csv']})
 log('Three-source follow-up QA and admission decisions written; gross FAR remains pending.')

if __name__=='__main__':main()
