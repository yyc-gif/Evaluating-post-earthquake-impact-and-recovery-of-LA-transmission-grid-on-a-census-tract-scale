"""Original bulk table, exact GEOID join, nine-indicator flags and national ranks."""
import zipfile
import re
from scipy.stats import pearsonr, spearmanr
from common import *

INDICATORS = [
    ('NEHD', 'Extreme heat days', 'Heat', '2018-2022', 'days/year above tract-specific 95th temperature percentile',
     'CDC Tracking', '2010 tract estimate crosswalked to 2020; native temperature-grid resolution not established',
     '13 national records neighbor-interpolated by CDC; identities absent; no published F_NEHD'),
    ('SMOKE', 'Wildfire smoke', 'Wildfire', '2013-2022', 'medium/heavy smoky days/year',
     'NOAA OSPO Hazard Mapping System', 'Daily smoke polygons intersected with 2020 tracts; any intersection counts a day',
     'Light smoke excluded; no published F_SMOKE; smoke cover is not ground-level dose'),
    ('BURN', 'Wildfire proximity', 'Wildfire', '2013-2022 used; source archive 1984-2022',
     'mean annual percentage of tract area burned; percentage interpretation from technical processing',
     'USGS EROS / USDA GTAC Monitoring Trends in Burn Severity', 'Annual MTBS wildfire polygons over 1000 acres intersected with tracts',
     'Prescribed burns and smaller fires excluded; no published F_BURN; archive and analysis periods differ by design'),
    ('CFLD', 'Coastal flooding frequency', 'Extreme Events', '1996-2019', 'modeled events/year',
     'FEMA NRI', 'NRI tract annualized frequency; underlying coastal modeling footprint, not tract flood-zone area',
     'F=1 source-excluded/null rather than observed zero; do not equate to NFHL probability'),
    ('DRGT', 'Drought frequency', 'Extreme Events', '2000-2021', 'NRI event-days/year; CDC technical text calls event-weeks',
     'FEMA NRI / US Drought Monitor', 'Weekly extreme/exceptional drought polygons; NRI converts week counts to event-days',
     'Units discrepancy: values match v1.19 event-day frequency, not event-weeks; published values unchanged'),
    ('RFLD', 'Riverine flooding frequency', 'Extreme Events', '1996-2019', 'event-days/year',
     'FEMA NRI', 'NRI county occurrence assigned to supported tract geography; includes minimum annual frequency',
     'FEMA minimum annual frequency may be modeled despite no historical event; not a NFHL area fraction'),
    ('HRCN', 'Hurricane frequency', 'Extreme Events', '1851-2020', 'events/year',
     'FEMA NRI', 'NRI historic hurricane wind-track exposure geography; minimum annual frequency within supported footprint',
     'All study F_HRCN=1; absent NRI records represented as published zero; not observed hurricane-free condition'),
    ('SWND', 'Strong winds frequency', 'Extreme Events', '1986-2019', 'events/year',
     'FEMA NRI', 'NRI 49-by-49-km source fishnet occurrence assigned to tracts',
     'Not measured tract wind speed, local Santa Ana severity, or station wind fragility'),
    ('TRND', 'Tornado frequency', 'Extreme Events', '1986-2024 as documented by CDC', 'events/year',
     'CDC Tracking', 'CDC tract annualized frequency; underlying spatial support not independently established',
     'Do not silently substitute NRI v1.19 tornado frequency or vintage')]
CODES = [x[0] for x in INDICATORS]
EPL = ['EPL_' + c for c in CODES]
DOMAINS = {'Heat': ['NEHD'], 'Wildfire': ['SMOKE', 'BURN'],
           'Extreme Events': ['CFLD', 'DRGT', 'RFLD', 'HRCN', 'SWND', 'TRND']}
TECHNICAL_PAGES = {'NEHD':'93-94','SMOKE':'95-96','BURN':'97-98','CFLD':'99',
                   'DRGT':'100-101','RFLD':'101-102','HRCN':'103-104','SWND':'106-107','TRND':'105-106'}


def read_bulk(label):
    path = lp(OUT / 'sources' / f'EJI_2024_{label}_CSV.zip')
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return pd.read_csv(z.open(f'EJI_2024_{label}.csv'), dtype={'GEOID': str, 'GEOID_2020': str})


def safe_assoc(a, b):
    f = pd.DataFrame({'a': a, 'b': b}).replace(-999, np.nan).dropna()
    return dict(n=len(f), Pearson=pearsonr(f.a, f.b).statistic if f.a.nunique()>1 and f.b.nunique()>1 else np.nan,
                Spearman=spearmanr(f.a, f.b).statistic if f.a.nunique()>1 and f.b.nunique()>1 else np.nan)


def main():
    s = sources()
    full, d = dataset(s)
    national = read_bulk('United_States')
    ca = read_bulk('California')
    assert national.GEOID.is_unique and ca.GEOID.is_unique
    assert ca.GEOID.str.fullmatch(r'\d{11}').all()
    national = national.set_index('GEOID')
    ca = ca.set_index('GEOID')
    n = ca.reindex(d.index)
    assert n.index.equals(d.index) and n.GEOID_2020.eq(n.index).all()
    numeric = ca.select_dtypes('number').columns
    assert np.allclose(ca[numeric], national.reindex(ca.index)[numeric], equal_nan=True, atol=0, rtol=0)
    with zipfile.ZipFile(lp(OUT/'sources/EJI_2024_United_States_CSV.zip')) as z:
        dictionary_bytes = z.read('EJI_DATADICTIONARY_2024.csv')
        with zipfile.ZipFile(lp(OUT/'sources/EJI_2024_California_CSV.zip')) as cz:
            assert dictionary_bytes == cz.read('EJI_DATADICTIONARY_2024.csv')
        lp(OUT/'sources/EJI_DATADICTIONARY_2024_ORIGINAL.csv').write_bytes(dictionary_bytes)
        dictionary = pd.read_csv(z.open('EJI_DATADICTIONARY_2024.csv'), encoding='cp1252', header=1)
        dictionary.columns = ['field','2022_field','definition','module','domain','source','calculation','notes']
        cbm_fields = dictionary.field.astype(str).str.contains('CBM|NEHD|BURN|SMOKE|CFLD|DRGT|RFLD|HRCN|SWND|TRND|GEOID|TOTPOP')
        save('CDC_CBM_FIELD_DICTIONARY.csv', dictionary.loc[cbm_fields])
        dump('OFFICIAL_ARCHIVE_MEMBER_HASHES.json', {x.filename: dict(bytes=x.file_size, sha256=hashlib.sha256(z.read(x.filename)).hexdigest()) for x in z.infolist()})
    save('CDC_2024_MATCHED_ORIGINAL_VALUES.csv', n.reset_index())
    cov = d[['Population','additional_zero_housing_positive_population']].copy()
    cov['CDC_GEOID_2020'] = n.GEOID_2020
    cov['exact_match'] = n.GEOID_2020.eq(d.index)
    cov['published_RPL_CBM'] = n.RPL_CBM
    cov['rank_null'] = n.RPL_CBM.isna()
    cov['rank_sentinel'] = n.RPL_CBM.eq(-999)
    cov['rank_valid_0_1'] = n.RPL_CBM.between(0,1)
    cov['CDC_2018_2022_ACS_Population'] = n.E_TOTPOP
    cov['CDC_population_zero'] = n.E_TOTPOP.eq(0)
    cov['CDC_population_sentinel_or_null'] = n.E_TOTPOP.isna() | n.E_TOTPOP.lt(0)
    cov['population_difference_CDC_minus_frozen'] = n.E_TOTPOP - d.Population
    save('CBM_2299_GEOID_COVERAGE.csv', cov.reset_index())
    records = []
    flags = []
    register = []
    for code, name, domain, period, units, provider, support, limitation in INDICATORS:
        e, p, f = 'E_'+code, 'EPL_'+code, 'F_'+code
        flag = n[f] if f in n else pd.Series(np.nan, index=n.index)
        states = []
        for key in d.index:
            raw, rank, flag_value = n.loc[key,e], n.loc[key,p], flag.loc[key]
            if pd.isna(raw) or raw == -999 or pd.isna(rank) or rank == -999:
                status = 'UNAVAILABLE_RAW_OR_RANK'
            elif flag_value == 1:
                status = 'SOURCE_NULL_OR_EXCLUDED_SET_ZERO'
            elif flag_value == 0:
                status = 'PROVIDER_CONFIRMED_RECORD_PERIOD_ZERO'
            elif flag_value == 2:
                status = 'POSITIVE_ESTIMATE_WITH_ZERO_RANK'
            elif flag_value == 9:
                status = 'PROVIDER_OTHER_VALID_ESTIMATE'
            elif f not in n and raw == 0:
                status = 'ZERO_NO_PUBLISHED_FLAG_UNRESOLVED'
            elif f not in n and raw > 0:
                status = 'POSITIVE_PUBLISHED_ESTIMATE_NO_FLAG'
            else:
                status = 'UNKNOWN_FLAG_OR_INVALID_VALUE'
            states.append(status)
            records.append(dict(tract_id=key, indicator=code, domain=domain, Population=d.loc[key,'Population'],
                           raw_value=raw, official_indicator_rank=rank, flag_field=f if f in n else 'NOT_PUBLISHED',
                           flag_value=flag_value, quality_state=status,
                           special_source_processing=code in ['NEHD','BURN','SMOKE','RFLD','HRCN'],
                           unresolved_processing_identity=code=='NEHD',
                           additional_zero_housing_positive_population=d.loc[key,'additional_zero_housing_positive_population']))
        states = pd.Series(states, index=d.index)
        for state in sorted(states.unique()):
            idx = states.index[states.eq(state)]
            flags.append(dict(indicator=code, quality_state=state, tract_count=len(idx), resident_population=d.loc[idx,'Population'].sum(),
                              flag_field_available=f in n))
        for value in sorted(flag.dropna().unique()):
            assert value in [0,1,2,9,-999]
        register.append(dict(indicator=code, name=name, domain=domain, raw_field=e, percentile_field=p,
                         flag_field=f if f in n else 'Absent from official bulk CSV, dictionary and raw service',
                         reference_period=period, units=units, source_agency_and_dataset=provider,
                         original_source_url='; '.join(re.findall(r'https?://[^\s\\]+',str(dictionary.set_index('field').loc[e,'source']))),
                         CDC_technical_PDF_pages=TECHNICAL_PAGES[code],
                         spatial_support_and_crosswalk=support, applicable_geography='CONUS; study uses exact 2020 LA tract IDs',
                         zero_definition='F=0: provider confirms zero in record/measure, not absence of future hazard; unflagged zero unresolved',
                         missing_definition='F=1: source null/excluded, sometimes raw zero; -999/null unavailable; never relabeled observed zero',
                         NRI_minimum_frequency=code in ['RFLD','HRCN'], official_rank_role='One of nine equally summed EPL ranks; domains not equally weighted',
                         scientific_limitation=limitation, **describe(n[e])))
    q = pd.DataFrame(records)
    save('CBM_2299_BY_NINE_INDICATOR_QUALITY.csv', q)
    q.pivot(index='tract_id', columns='indicator', values='quality_state').reset_index().to_csv(lp(OUT/'CBM_INDICATOR_QUALITY_MATRIX.csv'),index=False)
    save('CBM_FLAGGED_TRACT_AND_POPULATION_COUNTS.csv', flags)
    save('CBM_NINE_INDICATOR_SOURCE_REGISTER.csv', register)
    totals = d[['Population','additional_zero_housing_positive_population']].copy()
    masks = dict(published_numeric=q.raw_value.ge(0), provider_confirmed_record_zero=q.quality_state.eq('PROVIDER_CONFIRMED_RECORD_PERIOD_ZERO'),
                 source_null_or_excluded=q.quality_state.eq('SOURCE_NULL_OR_EXCLUDED_SET_ZERO'),
                 unresolved_zero=q.quality_state.str.contains('UNRESOLVED|UNKNOWN|UNAVAILABLE'),
                 unavailable_quality_flag=q.flag_field.eq('NOT_PUBLISHED'),
                 source_processing=q.special_source_processing)
    for name, mask in masks.items():
        totals[name+'_indicator_count'] = q.assign(value=mask.astype(int)).groupby('tract_id').value.sum().reindex(d.index)
    save('CBM_TRACT_QUALITY_COUNTS.csv', totals.reset_index())
    # Check the exact summation and the national rank, retaining SQL/rounding tolerances.
    sums = national[EPL].replace(-999,np.nan).sum(axis=1,min_count=9)
    valid = national.SPL_CBM.ge(0) & national.RPL_CBM.between(0,1) & sums.notna()
    sum_error = (sums.loc[valid] - national.loc[valid,'SPL_CBM']).abs()
    rank = (national.loc[valid,'SPL_CBM'].rank(method='min')-1)/(valid.sum()-1)
    rank_error = (rank-national.loc[valid,'RPL_CBM']).abs()
    # Provider SQL and rounded components are not asserted byte-equivalent to Excel.
    diagnostics = dict(national_rows=len(national), california_rows=len(ca), national_valid_CBM=int(valid.sum()),
                       cohort_valid_CBM=int(n.RPL_CBM.between(0,1).sum()), duplicate_ids=int(national.index.duplicated().sum()),
                       max_nine_EPL_sum_error=float(sum_error.max()), median_sum_error=float(sum_error.median()),
                       national_min_rank_max_error=float(rank_error.max()), national_min_rank_median_error=float(rank_error.median()),
                       national_min_rank_Spearman=spearmanr(rank,national.loc[valid,'RPL_CBM']).statistic,
                       national_min_rank_pearson=pearsonr(rank,national.loc[valid,'RPL_CBM']).statistic,
                       rank_tolerance=.0000501, sum_tolerance=1e-12, rank_match_within_tolerance=bool(rank_error.max()<=.0000501),
                       sum_match_within_tolerance=bool(sum_error.max()<=1e-12),
                       missing_quality_fields=[f'F_{c}' for c in CODES if f'F_{c}' not in n],
                       frozen_population_unchanged=True, cdc_population_differs=int(n.E_TOTPOP.ne(d.Population).sum()),
                       cdc_population_zero_on_frozen_positive=int(n.E_TOTPOP.eq(0).sum()),
                       source_null_flag1_tracts=int(totals.source_null_or_excluded_indicator_count.gt(0).sum()),
                       unresolved_zero_tracts=int(totals.unresolved_zero_indicator_count.gt(0).sum()))
    for domain, codes in DOMAINS.items():
        k = ['Heat','Wildfire','Extreme Events'].index(domain)+1
        err = (n[['EPL_'+c for c in codes]].sum(axis=1)-n[f'SPL_CBM_DOM{k}']).abs().max()
        diagnostics[domain+'_domain_sum_max_error'] = err
    dump('CBM_RANK_RECONSTRUCTION_QA.json', diagnostics)
    # Compare retained NRI source frequencies without assuming that a field name proves version identity.
    nri = frozen(s, MH+'FEMA_V119_MATCHED_2299_SOURCE_ROWS.csv').set_index('tract_id').reindex(d.index)
    checks = []
    for c in ['CFLD','DRGT','RFLD','HRCN','SWND','TRND']:
        pair = pd.DataFrame({'CDC':n['E_'+c], 'NRI':nri[c+'_AFREQ']}).dropna()
        checks.append(dict(indicator=c, paired_n=len(pair), source_null_n=int(nri[c+'_AFREQ'].isna().sum()),
                           max_abs_difference=(pair.CDC-pair.NRI).abs().max(), **safe_assoc(pair.CDC,pair.NRI),
                           note='CDC raw table four-decimal export versus NRI v1.19; equivalence only assessed numerically'))
    save('CDC_VS_FROZEN_NRI_AFREQ_SOURCE_CHECK.csv',checks)
    save('SCIENTIFIC_INPUT_HASHES_CDC.csv',s.records)
    print(json.dumps(clean(diagnostics),indent=2),flush=True)


if __name__ == '__main__':
    main()
