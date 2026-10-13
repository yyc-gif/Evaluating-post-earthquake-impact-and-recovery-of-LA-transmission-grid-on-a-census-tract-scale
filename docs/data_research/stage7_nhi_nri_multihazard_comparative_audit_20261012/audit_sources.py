"""NHI reconstruction/geography and frozen FEMA source-factor calculations only."""
from html.parser import HTMLParser
import re
import xml.etree.ElementTree as ET

import fitz
import geopandas as gpd
from scipy.stats import spearmanr
from shapely import make_valid
from shapely.geometry import shape
from shapely.ops import unary_union
from acquire import Acquisition
from common import *

NHI = ['wind', 'tor', 'hail', 'cfh', 'wf', 'tsu', 'hi', 'vol', 'ls', 'eq', 'ww', 'hu', 'dr', 'fl']
NAMES = ['Damaging wind', 'Tornado', 'Hail', 'Coastal flood', 'Wildfire', 'Tsunami', 'Extreme heat', 'Volcano', 'Landslide', 'Earthquake', 'Winter storms', 'Hurricane', 'Drought', 'Floods']
HAZARDS = ['AVLN', 'CFLD', 'CWAV', 'DRGT', 'ERQK', 'HAIL', 'HWAV', 'HRCN', 'ISTM', 'LNDS', 'LTNG', 'RFLD', 'SWND', 'TRND', 'TSUN', 'VLCN', 'WFIR', 'WNTW']
HAZARD_NAMES = ['Avalanche', 'Coastal flooding', 'Cold wave', 'Drought', 'Earthquake', 'Hail', 'Heat wave', 'Hurricane', 'Ice storm', 'Landslide', 'Lightning', 'Riverine flooding', 'Strong wind', 'Tornado', 'Tsunami', 'Volcanic activity', 'Wildfire', 'Winter weather']


class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def htmltext(text):
    parser = HTMLText(); parser.feed(text)
    return ' '.join(' '.join(parser.parts).split())


def source_path(acq, name):
    rec = next(r for r in acq.records if r['name'] == name)
    assert rec['status'] == 'ACQUIRED', (name, rec['status'])
    path = lp(OUT / rec['file']); assert sha(path) == rec['sha256']
    return path


def stats(values):
    x = pd.Series(values).dropna()
    return dict(valid=len(x), missing=int(pd.Series(values).isna().sum()), zero=int(x.eq(0).sum()),
        distinct=x.nunique(), distinct_round6=x.round(6).nunique(), min=x.min(), p10=x.quantile(.1),
        median=x.median(), p90=x.quantile(.9), max=x.max(), mean=x.mean(), sd=x.std(ddof=0))


def normalize(x):
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else x * np.nan


def main():
    a = Acquisition(); d = frame('FROZEN_COHORT_AND_COMPARATORS.csv', 'tract_id')
    app = json.loads(source_path(a, 'COLUMBIA_APP_DATA').read_bytes())
    docs = htmltext(app['widgets']['widget_217']['config']['text'])
    md('COLUMBIA_OFFICIAL_APP_METHOD_TEXT.md', docs)
    tables = {}
    for i in [1, 2]:
        obj = json.loads(source_path(a, f'NHI_Documentation_Table{i}_0_RECORDS').read_bytes())
        assert not obj.get('exceededTransferLimit', False)
        table = pd.DataFrame([x['attributes'] for x in obj['features']])
        assert len(table) == 14
        tables[i] = table
        save(f'COLUMBIA_OFFICIAL_DOCUMENTATION_TABLE{i}.csv', table)
    schema = json.loads(source_path(a, 'COLUMBIA_LAYER77').read_bytes())
    save('COLUMBIA_FIELD_SCHEMA.csv', schema['fields'])
    webmap = json.loads(source_path(a, 'COLUMBIA_WEBMAP_1ddc2479ea4b4fe491fd776843c73cf6').read_bytes())
    linked = [layer.get('url', '') for layer in webmap.get('operationalLayers', [])]
    assert any('hazards_index_sum/featureserver/77' in url.lower() for url in linked)

    inventory = json.loads(source_path(a, 'COLUMBIA_LA_OBJECT_IDS').read_bytes())['objectIds']
    features = []
    for r in a.records:
        if r['name'].startswith('COLUMBIA_LA_GEOJSON_B100_'):
            assert r['status'] == 'ACQUIRED'
            obj = json.loads(lp(OUT / r['file']).read_bytes())
            assert obj['type'] == 'FeatureCollection' and not obj.get('exceededTransferLimit', False)
            features.extend(obj['features'])
    raw = gpd.GeoDataFrame.from_features(features, crs='EPSG:4326')
    assert len(raw) == len(inventory) == 2343 and set(raw.OBJECTID_1) == set(inventory)
    assert raw.FIPS.is_unique and raw.FIPS.str.fullmatch(r'\d{11}').all()
    raw = raw.set_index('FIPS')
    for h in NHI:
        raw[h + '_hazcat5'] = pd.to_numeric(raw[h + '_hazcat5'])
    scores = raw[[h + '_hazcat5' for h in NHI]]
    reconstructed = scores.sum(axis=1, min_count=1)
    assert np.max(np.abs(reconstructed - raw.hazsum5)) == 0
    quality = []
    for h, name in zip(NHI, NAMES):
        cat, val = raw[h + '_hazcat5'], raw[h + '_val']
        quality.append(dict(hazard=h, name=name, **stats(cat), raw_missing=int(val.isna().sum()), raw_zero=int(val.eq(0).sum()),
            class_null=int(cat.isna().sum()), class_zero=int(cat.eq(0).sum()), class_valid1to5=int(cat.between(1, 5).sum()),
            labels=json.dumps(raw[h + '_haz5'].value_counts(dropna=False).to_dict()),
            original_sum_reconstruction_rule='Official NULL contributes zero arithmetically; original raw NULL is retained and never declared physical zero',
            structural_zero_status='Explicit raw 0/category0 in tsunami footprint only; other NULLs unresolved no-hazard versus missing source',
            source_units='Ordinal five-level class; not physical intensity'))
    save('COLUMBIA_NHI_14_HAZARD_COMPONENT_QA.csv', quality)
    save('COLUMBIA_SOURCE_ATTRIBUTE_RECORDS.csv', raw.drop(columns='geometry').reset_index().rename(columns={'FIPS': 'source_2010_GEOID'}))

    # Actual official 2010 and 2020 geometries, not an identifier-only join.
    old = gpd.read_file('zip://' + str(source_path(a, 'CENSUS_TIGER2010_LA'))).set_index('GEOID10')
    new = gpd.read_file('zip://' + str(source_path(a, 'CENSUS_TIGER2020_CA'))).set_index('GEOID')
    target = new.loc[d.index].to_crs(3310)
    old = old.to_crs(3310)
    raw_geo = raw.to_crs(3310)
    assert set(raw.index).issubset(old.index)
    missing_old=old.loc[sorted(set(old.index)-set(raw.index)),['ALAND10','AWATER10']].reset_index()
    save('COLUMBIA_UNCOVERED_OFFICIAL_2010_TRACTS.csv',missing_old)
    assert missing_old.ALAND10.eq(0).all()
    validation = []
    for name, g in [('TIGER2010', old), ('TIGER2020', target), ('Columbia2010', raw_geo)]:
        invalid = ~g.geometry.is_valid
        if invalid.any():
            g.loc[invalid, 'geometry'] = g.loc[invalid, 'geometry'].map(make_valid)
        validation.append(dict(source=name, crs='EPSG:3310 equal-area meters', records=len(g),
            original_invalid=int(invalid.sum()), valid_after=int(g.geometry.is_valid.sum()), geometry_repair='make_valid only where originally invalid; no buffers or area clipping'))
    save('GEOMETRY_VALIDATION.csv', validation)
    target.to_file(dest('TARGET_2020_GEOMETRY.gpkg'), layer='tracts', driver='GPKG')
    raw_geo[['geometry']].to_file(dest('COLUMBIA_2010_GEOMETRY.gpkg'), layer='tracts', driver='GPKG')
    rel = pd.read_csv(source_path(a, 'CENSUS_RELATION_CA'), sep='|', dtype=str)
    oldkey = 'GEOID_TRACT_10'; newkey = 'GEOID_TRACT_20'
    assert oldkey in rel and newkey in rel
    for c in [x for x in rel.columns if 'AREALAND' in x or 'AREAWATER' in x]:
        rel[c] = pd.to_numeric(rel[c])
    counts_old = rel.groupby(oldkey)[newkey].nunique()
    counts_new = rel.groupby(newkey)[oldkey].nunique()
    relation_rows = rel.loc[rel[newkey].isin(d.index)].copy()
    save('OFFICIAL_RELATION_STUDY_ROWS.csv', relation_rows)
    pair_source = []
    geo_rows = []
    transfer_rows = []
    composition = []
    for tract in d.index:
        tg = target.loc[tract, 'geometry']; area = tg.area
        hits = raw_geo.sindex.query(tg, predicate='intersects')
        parts = []
        for pos in hits:
            source = raw_geo.index[pos]; intersection = tg.intersection(raw_geo.geometry.iloc[pos]); ar = intersection.area
            if ar <= 1e-8:
                continue
            parts.append((source, ar, intersection))
            pair_source.append(dict(tract_id=tract, source_2010_GEOID=source, overlap_m2=ar, target_area_m2=area, fraction_of_target=ar/area))
        assert parts
        parts.sort(key=lambda v: (-v[1], v[0]))
        union = unary_union([v[2] for v in parts]).area
        geometric_dominant, biggest, _ = parts[0]
        same_geometry_fraction = tg.intersection(old.loc[tract, 'geometry']).area / tg.union(old.loc[tract, 'geometry']).area if tract in old.index else np.nan
        links = rel.loc[rel[newkey].eq(tract)]
        land_parts=[(row[oldkey],float(row.AREALAND_PART)) for _,row in links.iterrows() if float(row.AREALAND_PART)>0]
        land_parts.sort(key=lambda v:(-v[1],v[0]))
        dominant, dominant_land=land_parts[0]
        land_total=float(target.loc[tract,'ALAND'])
        land_supported=sum(ar for src,ar in land_parts if src in raw.index)
        assert dominant in raw.index
        service_old_jaccard = raw_geo.loc[dominant, 'geometry'].intersection(old.loc[dominant, 'geometry']).area / raw_geo.loc[dominant, 'geometry'].union(old.loc[dominant, 'geometry']).area
        donors = links[oldkey].tolist()
        relation_type = 'many_to_many' if len(donors)>1 and any(counts_old[t]>1 for t in donors) else 'many_to_one' if len(donors)>1 else 'one_to_many' if counts_old[donors[0]]>1 else 'one_to_one'
        census_total_area = float(target.loc[tract, 'ALAND'] + target.loc[tract, 'AWATER'])
        census_overlap = float(links.AREALAND_PART.sum() + links.AREAWATER_PART.sum())
        geo_rows.append(dict(tract_id=tract, Population=int(d.loc[tract,'Population']), exact_GEOID_match=tract in raw.index,
            relation_type=relation_type, official_donor_count=len(donors), service_intersecting_source_count=len(parts),
            dominant_2010_GEOID=dominant, dominant_source_fraction=dominant_land/land_total, geometric_covered_fraction=union/area,
            geometric_total_area_dominant_2010_GEOID=geometric_dominant,geometric_dominant_fraction=biggest/area,
            official_land_supported_fraction=land_supported/land_total,
            summed_overlap_fraction=sum(v[1] for v in parts)/area, partition_overlap_excess=(sum(v[1] for v in parts)-union)/area,
            same_GEOID_TIGER_Jaccard=same_geometry_fraction, unchanged_same_ID_at_99_9pct=(same_geometry_fraction>=.999),
            Columbia_vs_TIGER2010_dominant_Jaccard=service_old_jaccard,
            official_relation_partition_fraction=census_overlap/census_total_area,
            area_m2=area, official_ALAND_m2=float(target.loc[tract,'ALAND']), official_AWATER_m2=float(target.loc[tract,'AWATER']),
            support_geographic='Documented 2010 source transfer; not a native 2020 observation',
            retained_zero_housing=bool(d.loc[tract,'additional_zero_housing_positive_population'])))
        values = dict(tract_id=tract, Columbia_published_sum_dominant_source=float(raw.loc[dominant,'hazsum5']),
            Columbia_ordinal_area_average=sum(raw.loc[src,'hazsum5']*ar for src,ar in land_parts if src in raw.index)/land_supported if land_supported>=land_total-1 else np.nan,
            dominant_source=dominant, dominant_source_fraction=dominant_land/land_total)
        for h in NHI:
            valid_area, null_area = 0., 0.
            bins = {}
            for src, ar in land_parts:
                if src not in raw.index:
                    bins['UNKNOWN_SOURCE_GEOGRAPHY']=bins.get('UNKNOWN_SOURCE_GEOGRAPHY',0)+ar
                    null_area+=ar
                    continue
                cat = raw.loc[src,h+'_hazcat5']
                key = 'UNKNOWN' if pd.isna(cat) else str(int(cat))
                bins[key] = bins.get(key,0) + ar
                null_area += ar if pd.isna(cat) else 0
                valid_area += ar if not pd.isna(cat) else 0
            values[h+'_dominant_source_category'] = raw.loc[dominant,h+'_hazcat5']
            values[h+'_unknown_area_fraction'] = null_area/land_total
            for key, ar in bins.items():
                composition.append(dict(tract_id=tract,hazard=h,source_category=key,fraction_of_target_area=ar/land_total,
                    interpretation='Official relationship-file LAND-area ordinal composition; UNKNOWN is not category zero; no population weighting'))
        transfer_rows.append(values)
    geo = pd.DataFrame(geo_rows).set_index('tract_id')
    transfers = pd.DataFrame(transfer_rows).set_index('tract_id')
    save('COLUMBIA_NHI_2010_TO_2020_GEOGRAPHY_QA.csv', geo.reset_index())
    save('COLUMBIA_GEOMETRIC_OVERLAP_PAIRS.csv', pair_source)
    save('COLUMBIA_NHI_TARGET_CLASS_COMPOSITION.csv', composition)
    save('COLUMBIA_NHI_TRANSFERRED_VALUES.csv', transfers.reset_index())
    save('COLUMBIA_SOURCE_COVERAGE_BY_TARGET.csv', pd.DataFrame({'tract_id':d.index,
        'hazards_with_no_source_null_area':[(transfers.loc[t,[h+'_unknown_area_fraction' for h in NHI]] <= 1e-9).sum() for t in d.index],
        'hazards_unknown_on_dominant_source':[raw.loc[transfers.loc[t,'dominant_source'],[h+'_hazcat5' for h in NHI]].isna().sum() for t in d.index]}))

    # FEMA source-factor QA. Missing values remain missing; no physical-zero claims.
    n = pd.read_csv(lp(OUT/'sources/FEMA_NRI_v119_CA_FROZEN.csv'), dtype={'TRACTFIPS':str,'STCOFIPS':str}, float_precision='round_trip').set_index('TRACTFIPS')
    assert len(n)==9106 and n.index.is_unique and set(n.NRI_VER)=={'Mar-23'}
    study=n.loc[d.index]
    pdf=fitz.open(lp(OUT/'sources/ARCHIVED_FEMA_V119_TECHNICAL_DOCUMENTATION.pdf'))
    pages={str(i+1):page.get_text() for i,page in enumerate(pdf)}
    dump('FEMA_V119_EXTRACTED_PAGE_TEXT.json',dict(review_status=WARN,pages=pages,source_sha256=sha(OUT/'sources/ARCHIVED_FEMA_V119_TECHNICAL_DOCUMENTATION.pdf')))
    raw_ncv={}; register=[]; wide=pd.DataFrame(index=d.index)
    for i,(h,name) in enumerate(zip(HAZARDS,HAZARD_NAMES)):
        freq=n[h+'_AFREQ']; exposure=n[h+'_EXP_AREA']; fraction=exposure/n.AREA
        good=freq.notna()&exposure.notna()&n.AREA.gt(0)&freq.ge(0)&exposure.ge(0)&fraction.le(1+1e-9)
        x=(freq*fraction).where(good)
        raw_ncv[h]=x
        wide[h+'_AFREQ']=study[h+'_AFREQ'];wide[h+'_EXP_AREA_sqmi']=study[h+'_EXP_AREA'];wide[h+'_area_fraction']=fraction.reindex(d.index);wide[h+'_NCV_raw']=x.reindex(d.index)
        original=pages[str(394+i)]
        start=original.index('Annualized Frequency Data')
        source_text=' '.join(original[start:original.index('HLR Data Source')].split())
        study_good=good.reindex(d.index)
        afreq=study[h+'_AFREQ'];area_frac=fraction.reindex(d.index)
        occurrence='event-days/year' if h in ['CWAV','DRGT','HWAV','ISTM','RFLD','WNTW'] else 'modeled annualized surrogate, published numerical scale' if h=='ERQK' else 'annual burn probability' if h=='WFIR' else 'events/year or modeled events/year'
        register.append(dict(hazard=h,name=name,AFREQ_field=h+'_AFREQ',EXP_AREA_field=h+'_EXP_AREA',AREA_field='AREA',
            AFREQ_units=occurrence,area_units='square miles; same frozen source AREA denominator',NCV_units='Native frequency times geographic-area proportion; min-max later creates dimensionless screening coordinate',
            source_version='March 2023 v1.19; NRI_VER=Mar-23; 2020 geography',documentation_pdf_page=394+i,source_period_and_extent=source_text,
            matched_tracts=len(study),**{'AFREQ_'+k:v for k,v in stats(afreq).items()},**{'area_fraction_'+k:v for k,v in stats(area_frac).items()},
            NCV_valid_study=int(study_good.sum()),NCV_valid_CA=int(good.sum()),area_fraction_gt1=int((area_frac>1+1e-9).sum()),
            minimum_frequency_note='LNDS tract default 0.01 (PDF235); RFLD county default 0.01 (PDF260) where susceptible and no event history; other rules as exact PDF. Defaults are modeled values, not observed physical occurrence.',
            geographic_dependence='County frequency inherited for positive RFLD susceptibility; others block/fishnet or modeled source aggregates; see exact sections',
            direct_social_asset_loss_fields_used=False,unknown_imputed=False,
            full_study_input_support=bool(study_good.all()),study_frequency_constant=afreq.dropna().nunique()==1))
    save('FEMA_NRI_V119_18_HAZARD_RAW_FIELD_REGISTER.csv',register)
    save('FEMA_NCV_HAZARD_COMPONENT_VALUES.csv',wide.reset_index())
    complete=[h for h in HAZARDS if raw_ncv[h].reindex(d.index).notna().all()]
    omitted=[h for h in HAZARDS if h not in complete]
    assert len(complete)==14 and omitted==['AVLN','HRCN','ISTM','VLCN']
    # Pre-fit extension registry is based only on source completeness, never fitted labels.
    dump('FEMA_NCV_ADAPTATION_REGISTRATION.json',dict(review_status=WARN,
        candidate='FEMA_NCV14_CA_v119',hazards=complete,omitted_hazards=omitted,
        selection_rule='Retain each of 18 release hazards only if all frozen 2299 tracts have nonnegative AFREQ, valid impacted/total area and compatible fraction. Four all-null fields omitted, never zero-filled.',
        method='Williams 2024 factor AFREQ*(EXP_AREA/AREA), per-hazard min-max, equal sum, final min-max',
        exact_paper_nine_hazard_replication=False,paper_nine_set_unresolved=True,
        main_normalization='California-wide 9106 frozen records; each hazard uses its actual valid source records',
        final_sum_CA_complete14_reference_count=int(pd.DataFrame({h:raw_ncv[h] for h in complete}).notna().all(axis=1).sum()),
        sensitivities=['Los Angeles cohort-only min-max explicitly labeled regional','leave each retained hazard out','omit locally invariant CWAV only','source-defined zero masking diagnostics, not fitted imputation'],
        reference_population_replaced=False,clustering_not_yet_run=True,
        qualified_native_geography=True,all_original_physical_measurements_certified=False))
    ncvs=pd.DataFrame({h:raw_ncv[h] for h in complete})
    ca_norm=pd.DataFrame({h:normalize(ncvs[h]) for h in complete})
    # A zero-range locally constant hazard has no LA-only distance information.
    la=ncvs.loc[d.index]
    varying=[h for h in complete if la[h].max()>la[h].min()]
    la_norm=pd.DataFrame({h:normalize(la[h]) for h in varying})
    ca_sum=ca_norm.loc[d.index].sum(1,min_count=len(complete))
    # Final CA sum reference uses only complete actual 14-component rows, not NA-to-zero sums.
    ca_all_sum=ca_norm.sum(1,min_count=len(complete))
    final_ca=(ca_sum-ca_all_sum.min())/(ca_all_sum.max()-ca_all_sum.min())
    final_la=normalize(la_norm.sum(1,min_count=len(varying)))
    candidate=pd.DataFrame({'FEMA_NCV14_CA_v119':final_ca,'FEMA_NCV13_LA_v119_regional_sensitivity':final_la},index=d.index)
    assert candidate.notna().all().all()
    save('FEMA_NCV_CANDIDATE_VECTORS.csv',candidate.reset_index())
    save('FEMA_NCV_NORMALIZED_COMPONENTS.csv',ca_norm.loc[d.index].reset_index())
    normalization=[]
    for h in complete:
        normalization.append(dict(hazard=h,CA_valid=int(ncvs[h].notna().sum()),CA_min=ncvs[h].min(),CA_max=ncvs[h].max(),
            LA_min=la[h].min(),LA_max=la[h].max(),LA_constant=h not in varying,CA_reference_is_national=False))
    save('FEMA_NCV_NORMALIZATION_REFERENCE.csv',normalization)
    final=pd.concat([candidate,transfers[['Columbia_published_sum_dominant_source','Columbia_ordinal_area_average']],d[['RPL_CBM']]],axis=1)
    save('CANDIDATE_TRACT_VALUES.csv',final.reset_index())
    dump('SOURCE_RECONSTRUCTION_QA.json',dict(review_status=WARN,Columbia_original_records=len(raw),
        published_sum_max_error=float((reconstructed-raw.hazsum5).abs().max()),Columbia_exact2020_ID_matches=int(geo.exact_GEOID_match.sum()),
        minimum_geometry_coverage=geo.geometric_covered_fraction.min(),maximum_partition_overlap=geo.partition_overlap_excess.max(),
        FEMA_version='Mar-23',FEMA_CA_records=9106,FEMA_full_match=2299,FEMA_complete_source_hazards=complete,
        original_nine_hazard_aggregate_exactly_replicated=False,national_NCV_normalization_verified=False,
        no_hazard_null_zero_imputation=True,no_new_clustering_in_this_script=True))
    print('NHI/FEMA source audit complete; Columbia nulls remain unresolved; 14 FEMA components are calculable without imputation',flush=True)


if __name__=='__main__':
    main()
