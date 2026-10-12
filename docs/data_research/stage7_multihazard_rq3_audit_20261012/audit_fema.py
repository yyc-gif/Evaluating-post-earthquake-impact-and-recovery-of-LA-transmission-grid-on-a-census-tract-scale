"""Version-specific screening of all 18 hazards, with nulls preserved."""
import shutil
import fitz
from common import *

# Occurrence bases and native supports are transcribed from v1.19 Table 6 (PDF p63).
HAZARDS = [
 ('AVLN','Avalanche','events/year','county','Regional mountain possibility, not an urban-wide exposure layer'),
 ('CFLD','Coastal flooding','modeled events/year, mixed probability bands and high-tide recurrence','coastal polygons','Coastal relevance; NFHL V/A distinctions require care'),
 ('CWAV','Cold wave','event-days/year','block / forecast zones','Regional weather context, not interchangeable with heat'),
 ('DRGT','Drought','event-days/year','tract','Regional drought relevant; NRI EAL is agriculture-only'),
 ('ERQK','Earthquake','probability/year','probabilistic grid','Primary earthquake context; independent MS48 PGA preferred'),
 ('HAIL','Hail','events/year','49-km fishnet','Coarse occurrence support; retain screening only'),
 ('HWAV','Heat wave','event-days/year','block / forecast zones','Use historical CDC extreme-heat days as independent context'),
 ('HRCN','Hurricane','events/year','49-km fishnet','Applicability determined by source, not infer from absent losses'),
 ('ISTM','Ice storm','event-days/year','49-km fishnet','Coarse and low regional salience; screen actual values'),
 ('LNDS','Landslide','events/year','tract / susceptibility map','Hillside relevance; NRI includes susceptibility/minimum-frequency assumptions'),
 ('LTNG','Lightning','events/year','4-km source raster','Coarse physical occurrence screening; no separate tract overlay admitted'),
 ('RFLD','Riverine flooding','event-days/year','county historical occurrence','NFHL physical probability bands are not NRI event-day frequency'),
 ('SWND','Strong wind','events/year','49-km fishnet','Regionally relevant; coarse source frequency is not tract wind intensity'),
 ('TRND','Tornado','events/year','49-km fishnet by subtype','Retain as screening; do not infer zero probability from no historical records'),
 ('TSUN','Tsunami','events/year','tract','Coastal relevance; no new complete independent inundation overlay in this audit'),
 ('VLCN','Volcanic activity','events/year','block','Source applicability must be distinguished from measured zero'),
 ('WFIR','Wildfire','annual burn probability','probabilistic raster','CAL FIRE severity classification preferred for independent regional context'),
 ('WNTW','Winter weather','event-days/year','block / forecast zones','Screen actual fields; coarse and not the prioritized environmental construct')]


def describe(x):
    x=pd.to_numeric(x,errors='raise');valid=x.dropna()
    out=dict(n=len(x),valid_count=len(valid),missing_count=int(x.isna().sum()),negative_count=int(x.lt(0).sum()),
        zero_count=int(x.eq(0).sum()),positive_count=int(x.gt(0).sum()),unique_valid=valid.nunique())
    out.update({name:valid.quantile(q) for name,q in [('P10',.1),('P25',.25),('median',.5),('P75',.75),('P90',.9)]})
    out.update(mean=valid.mean(),std=valid.std(),minimum=valid.min(),maximum=valid.max(),
        zero_fraction_all=int(x.eq(0).sum())/len(x),upper_1pct_count=int(valid.gt(valid.quantile(.99)).sum()))
    return out


def main():
    s=sources();full,d=dataset(s)
    n=frozen(s,'Data/NRI_Table_CensusTracts_California.csv').set_index('TRACTFIPS')
    assert n.index.is_unique and n.index.str.fullmatch(r'\d{11}').all() and n.NRI_VER.eq('Mar-23').all()
    n=n.reindex(d.index);assert n.NRI_VER.notna().all()
    sovi_residual=(n.SOVI_SCORE-d.SOVI_SCORE).abs().max()
    assert np.allclose(n.SOVI_SCORE,d.SOVI_SCORE,rtol=0,atol=5e-9)
    save('FEMA_V119_MATCHED_2299_SOURCE_ROWS.csv',n.reset_index().rename(columns={'TRACTFIPS':'tract_id'}))
    rows=[];inventory=[];ratings=[];contrib=[]
    total=n.EAL_VALT.sum()
    for prefix,name,units,support,decision in HAZARDS:
        inventory.append(dict(prefix=prefix,hazard=name,AFREQ_units=units,AFREQ_original_support=support,
            v119_occurrence_reference='Table 6, PDF p63; hazard chapter '+str(6+len(inventory)),
            EXP_AREA_units='km2 of source-defined exposed area; not population fraction',
            EALT_units='2022 USD/year, building + monetized population + agriculture where applicable',
            ALR_units='consequence-specific annual-loss fraction; NPCTL national percentile',
            AFREQ_valid_count=n[prefix+'_AFREQ'].notna().sum(),
            EALT_valid_count=n[prefix+'_EALT'].notna().sum(),regional_screen=decision,
            recommendation='SCREENING_ONLY; prioritize independently documented physical layers'))
        for suffix in ['EVNTS','AFREQ','EXP_AREA','EALT','EALS','ALRB','ALRP','ALRA','ALR_NPCTL']:
            c=prefix+'_'+suffix
            rows.append(dict(hazard=name,field=c,field_exists=c in n,**(describe(n[c]) if c in n else {})))
        for rating,count in n[prefix+'_EALR'].value_counts(dropna=False).items():
            ratings.append(dict(prefix=prefix,hazard=name,EAL_rating=rating,count=count))
        values=n[prefix+'_EALT'];share=values/n.EAL_VALT.where(n.EAL_VALT.gt(0))
        contrib.append(dict(prefix=prefix,hazard=name,pooled_EAL=values.sum(min_count=1),
            pooled_share=values.sum(min_count=1)/total,valid_tracts=values.notna().sum(),
            positive_EAL_tracts=values.gt(0).sum(),median_tract_share=share.median(),P90_tract_share=share.quantile(.9)))
    save('ALL_18_HAZARD_INVENTORY.csv',inventory);save('ALL_18_HAZARD_FIELD_QA.csv',rows)
    save('ALL_18_HAZARD_APPLICABILITY_RATINGS.csv',ratings);save('HAZARD_EXPECTED_LOSS_CONTRIBUTIONS.csv',contrib)
    hazard_cols=[p+'_EALT' for p,*_ in HAZARDS]
    residual=n[hazard_cols].sum(axis=1,min_count=1)-n.EAL_VALT
    components=n[['EAL_VALB','EAL_VALPE','EAL_VALA']].sum(axis=1,min_count=1)-n.EAL_VALT
    assert np.allclose(residual,0,atol=1e-6) and np.allclose(components,0,atol=1e-6)
    qa=dict(cohort=2299,source_rows=9106,release='Mar-23 / v1.19',exact_11_digit_IDs=True,
        earthquake_pooled_share=n.ERQK_EALT.sum()/total,max_SOVI_export_precision_residual=float(sovi_residual),
        max_hazard_sum_residual_USD=float(residual.abs().max()),
        max_consequence_sum_residual_USD=float(components.abs().max()),
        no_nulls_imputed=True,not_applicable_preserved=True,
        EAL_total=total,earthquake_median_tract_share=(n.ERQK_EALT/n.EAL_VALT).median())
    dump('FEMA_NUMERICAL_COMPOSITION_QA.json',qa)
    p=s.source(BE+'nri_eal_redundancy_audit_20261009/sources/FEMA_V119_TECHNICAL_DOCUMENTATION.pdf',AUTH)
    dest=lp(OUT/'sources/FEMA_V119_TECHNICAL_DOCUMENTATION.pdf');shutil.copyfile(p,dest)
    doc=fitz.open(p);evidence=[]
    for i,page in enumerate(doc):
        t=page.get_text()
        if any(x in t.lower() for x in ['annualized frequency','not applicable','period of record','exposure area']):
            evidence.append(dict(pdf_page=i+1,text=t))
    dump('sources/FEMA_V119_RELEVANT_PAGE_TEXT.json',evidence)
    save('SCIENTIFIC_INPUT_HASHES_FEMA.csv',s.records)
    md('FEMA_RISK_LOSS_AND_EXPOSURE_CONSTRUCTS.md',f'''# Measurement families: do not substitute one for another

{WARN}

The exact California archive contains 9,106 2020-tract records, all NRI_VER=Mar-23.
The current analysis matches all 2,299 positive frozen-population GEOIDs. No FEMA population replaces formal population.

**H physical exposure:** MS48 probabilistic PGA, CAL FIRE severity classes, NFHL probability-zone area, historical CDC extreme-heat days are distinct source-defined environmental measurements. None is electricity-outage damage.

**L loss propensity:** ALR_NPCTL nationally ranks an EAL-weighted combination of consequence-specific loss-rate percentiles. ALRB/ALRP/ALRA refer to building/population/agriculture rates; missing or zero-exposure denominators are not measured zero loss propensity. These retain modeled frequency and loss-ratio assumptions; they are not intensity or balanced physical exposure. See v1.19 PDF pp93-95 (printed 5-34 to 5-36).

**E expected loss:** EAL_VALT is modeled annual building + monetized population + agriculture loss (2022 USD/year); EAL_SCORE is its national percentile. On this cohort earthquake contributes **{qa['earthquake_pooled_share']:.6%}** of pooled EAL; median within-tract earthquake share is {qa['earthquake_median_tract_share']:.6%}. This updates, rather than inherits, the older residential 98.1563% calculation. Null hazard contributions remain null; the available-component sum matches the published total within {qa['max_hazard_sum_residual_USD']:.3g} USD.

**Adjusted risk:** RISK_VALUE=EAL_VALT*CRF_VALUE; CRF embeds SOVI/resilience. RISK_SCORE and ALR_VRA_NPCTL are excluded as primary physical hazard coordinates. Statistical correlation is separate from this procedural dependence.

v1.19 p44 (printed 3-6): Not Applicable, Insufficient Data and No Expected Annual Losses have different meanings. The archive's exact ratings and nulls are retained. A zero EAL can arise from zero exposure or frequency; it is not proof of physical safety. Historical EVNTS can be zero while minimum modeled AFREQ is positive (e.g. landslide). Table 6 (PDF p63) confirms mixed events, event-days and probability supports; raw AFREQs are never summed. EXP_AREA is source-defined exposure geography, not exposed resident population.

Official FEMA v1.19 technical documentation, March 2023, preserved by Ohio Emergency Management: https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf . The exact previously verified PDF and evidence pages are copied, not replaced by a newer technical release.
''')
    print(json.dumps(clean(qa)),flush=True)


if __name__=='__main__':main()
