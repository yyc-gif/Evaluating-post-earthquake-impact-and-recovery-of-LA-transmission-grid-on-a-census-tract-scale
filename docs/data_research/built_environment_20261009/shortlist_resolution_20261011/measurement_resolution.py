"""Resolve measurements on explicit common GEOIDs; never use cluster outcomes."""
from common import *
import itertools, gzip, zipfile, time
import numpy as np, pandas as pd
from scipy import stats
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

S='candidate_admission_rebuild_20261010/'
PHYSICAL=['emc2022_total_built_land_fraction','building_footprint_coverage','housing_5plus_share','housing_detached_share','land_use_entropy','scag2020_classified_land_entropy','assessor2022_actual_pre1970_main_area_share','all_use2014_pre1970_area_share','acs_residential_pre1970_share','nlcd_c12_2022_impervious_fraction','outline_height_area_weighted_centroid_m','jrc_anbh_positive_surface_mean_m','epa_household_job_activity_mix']
PAIRS=[('building_footprint_coverage','emc2022_total_built_land_fraction','coverage'),('land_use_entropy','scag2020_classified_land_entropy','land_use'),('housing_5plus_share','housing_detached_share','housing_contrast_not_same_quantity'),('all_use2014_pre1970_area_share','assessor2022_actual_pre1970_main_area_share','age_different_denominator'),('acs_residential_pre1970_share','assessor2022_actual_pre1970_main_area_share','age_different_population'),('outline_height_area_weighted_centroid_m','jrc_anbh_positive_surface_mean_m','height_different_support')]

def ids_sha(ids):return hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest()

def partial(a,b,controls):
    z=np.column_stack([np.ones(len(a)),controls]);ra=a-z@np.linalg.lstsq(z,a,rcond=None)[0];rb=b-z@np.linalg.lstsq(z,b,rcond=None)[0]
    return stats.pearsonr(ra,rb).statistic

def entropy(a):
    a=np.asarray(a,float);s=a.sum(axis=1);p=np.divide(a,s[:,None],out=np.zeros_like(a),where=s[:,None]>0);n=(a>0).sum(axis=1)
    h=-(np.where(p>0,p*np.log(np.maximum(p,1e-300)),0)).sum(axis=1)/np.log(np.maximum(n,2));h[s<=0]=np.nan;return h

def epa_sensitivity(d):
    x=pd.read_csv(source(S+'EPA_DONOR_TO_TRACT_CROSSWALK.csv'),dtype={'donor_geoid10':str,'tract_id':str});dq=pd.read_csv(source(S+'EPA_DONOR_ALLOCATION_QA.csv'),dtype={'donor_geoid10':str})
    x.donor_geoid10=x.donor_geoid10.str.zfill(12);dq.donor_geoid10=dq.donor_geoid10.str.zfill(12)
    src=pd.read_csv(source('pilot/EPA_SLD_V3_LA_BG_SOURCE.csv'),dtype={'GEOID10':str});src.GEOID10=src.GEOID10.str.zfill(12);src=src.set_index('GEOID10')
    counts=['HH','E5_Ret','E5_Off','E5_Ind','E5_Svc','E5_Ent'];cross=x[['donor_geoid10','tract_id','allocation_fraction']].copy()
    outside=dq[['donor_geoid10','outside_target_fraction']].rename(columns={'outside_target_fraction':'allocation_fraction'});outside['tract_id']='OUTSIDE';cross=pd.concat([cross,outside.loc[outside.allocation_fraction.gt(0)]],ignore_index=True)
    # Round-off correction is confined to hypothetical alternatives. Baseline uses saved weights.
    weights=cross.allocation_fraction.to_numpy();key=cross.donor_geoid10;idx=key.map({v:i for i,v in enumerate(dq.donor_geoid10)}).to_numpy();n=len(dq)
    raw=src.loc[key,counts].to_numpy(float);results=[];summaries=[]
    scenarios={'uniform_land':(1,1),'less_concentrated':(.5,.5),'more_concentrated':(2,2),'households_concentrated_jobs_diffuse':(2,.5),'households_diffuse_jobs_concentrated':(.5,2)}
    for name,(hh,jobs) in scenarios.items():
        ww=[]
        for power in [hh]+[jobs]*5:
            w=weights.copy() if name=='uniform_land' else weights**power
            if name!='uniform_land': w=w/np.bincount(idx,weights=w,minlength=n)[idx]
            ww.append(w)
        ww=np.array(ww).T;allocated=raw*ww
        if name!='uniform_land': assert np.allclose(allocated.sum(axis=0),src.loc[dq.donor_geoid10,counts].sum().to_numpy(),rtol=1e-10,atol=1e-6)
        agg=pd.DataFrame(allocated,columns=counts).assign(tract_id=cross.tract_id).groupby('tract_id')[counts].sum().reindex(d.index)
        h=pd.Series(entropy(agg),index=d.index);h.loc[d.geometry_status.eq('UNRESOLVED_GEOMETRY')]=np.nan
        if name=='uniform_land': assert np.allclose(h,d.epa_household_job_activity_mix,equal_nan=True,atol=1e-10)
        delta=h-d.epa_household_job_activity_mix;valid=delta.dropna()
        summaries.append(dict(scenario=name,n=len(valid),allocation_assumption='household area exponent '+str(hh)+', job area exponent '+str(jobs),mean_change=valid.mean(),median_change=valid.median(),mean_absolute_change=valid.abs().mean(),p90_absolute_change=valid.abs().quantile(.9),maximum_absolute_change=valid.abs().max(),n_absolute_change_gt_005=int(valid.abs().gt(.05).sum()),count_conservation_error_max=float(np.max(np.abs(allocated.sum(axis=0)-src.loc[dq.donor_geoid10,counts].sum().to_numpy()))),meaning='assumption stress test, neither allocation accuracy nor a confidence interval'))
        results.append(pd.DataFrame({'tract_id':d.index,'scenario':name,'activity_mix':h.to_numpy(),'difference_from_uniform_land':delta.to_numpy()}))
    save('EPA_ALLOCATION_SENSITIVITY.csv',pd.concat(results,ignore_index=True));save('EPA_ALLOCATION_SENSITIVITY_SUMMARY.csv',summaries)

def acs_replicates(d):
    reps=[f'Var_Rep{i}' for i in range(1,81)];p=source('validation/sources/B25024_06.csv.zip')
    with zipfile.ZipFile(p) as z:f=pd.read_csv(z.open(z.namelist()[0]),dtype={'GEOID':str})
    f=f.loc[f.GEOID.str.startswith('1400000US06037',na=False)].copy();f['tract_id']=f.GEOID.str[-11:]
    rows={k:f.loc[f.ORDER.eq(k)].set_index('tract_id').reindex(d.index) for k in [1,2,6,7,8,9]}
    den=rows[1][reps].to_numpy(float);out={}
    for name,orders in [('housing_detached_share',[2]),('housing_5plus_share',[6,7,8,9])]:
        num=sum(rows[k][reps].to_numpy(float) for k in orders);rep=np.divide(num,den,out=np.full_like(num,np.nan),where=den>0);point=d[name].to_numpy();se=np.sqrt(4/80*np.nansum((rep-point[:,None])**2,axis=1))
        regular=~d[name+'_boundary_model'].astype(bool).to_numpy();assert np.allclose(1.645*se[regular],d[name+'_moe90'].to_numpy()[regular],rtol=1e-7,atol=1e-10)
        out[name]=rep
    np.savez_compressed(lp(OUT/'ACS_CONFIGURATION_REPLICATES.npz'),tract_ids=d.index.to_numpy(dtype='U11'),**out)
    rows=[]
    for name,rep in out.items():
        moe=d[name+'_moe90'];rows.append(dict(feature=name,n=len(d),replicates=80,point_sd=d[name].std(),moe90_median=moe.median(),moe90_p90=moe.quantile(.9),moe90_max=moe.max(),boundary_model_n=int(d[name+'_boundary_model'].sum()),zero_rep_denominator_tract_n=int(d[name+'_zero_replicate_denominators'].gt(0).sum()),SOVI_pearson=stats.pearsonr(d[name],d.SOVI_SCORE).statistic,SOVI_spearman=stats.spearmanr(d[name],d.SOVI_SCORE).statistic,replicate_SOVI_pearson_min=min(stats.pearsonr(rep[:,i],d.SOVI_SCORE).statistic for i in range(80)),replicate_SOVI_pearson_max=max(stats.pearsonr(rep[:,i],d.SOVI_SCORE).statistic for i in range(80)),no_precision_exclusion=True))
    save('ACS_CONFIGURATION_UNCERTAINTY.csv',rows)

def assessor_restrictions(d):
    qa=json.loads(source(S+'ASSESSOR_ASSIGNED_CACHE_QA.json').read_text(encoding='utf-8'));p=lp(CA/REL/S/'raw_cache/assessor2022_assigned_nonpersonal.pkl');assert sha(p)==qa['cache_sha256'];a=pd.read_pickle(p)
    assert len(a)==qa['rows'] and a.AIN.is_unique and set(a.RollYear.astype(str))=={'2022'}
    a=a.loc[a.tract_id.isin(d.index)].copy();area=pd.to_numeric(a.SQFTmain,errors='coerce').clip(lower=0).fillna(0);year=pd.to_numeric(a.YearBuilt,errors='coerce');valid=year.between(1700,2022);pre=valid&year.lt(1970);shared=a.groupby(['CENTER_LAT','CENTER_LON']).AIN.transform('size').gt(1)
    sets={'all_recorded':np.ones(len(a),bool),'single_line':a.totBuildingDataLines.eq(1),'noncondo':a.UseType.ne('CND'),'single_line_noncondo_nonshared':a.totBuildingDataLines.eq(1)&a.UseType.ne('CND')&~shared,'taxable_only':a.isTaxableParcel.eq('Y'),'government_recorded':a.ParcelClassification.eq('Public (non-taxable government-owned)')}
    results=[]
    for name,mask in sets.items():
        f=pd.DataFrame({'tract_id':a.tract_id,'area':area*mask,'valid':area*valid*mask,'pre':area*pre*mask,'records':mask.astype(int)}).groupby('tract_id').sum().reindex(d.index)
        h=f.pre/f.valid;cov=f.valid/f.area;support=f.area/area.groupby(a.tract_id).sum().reindex(d.index)
        if name=='all_recorded':assert np.allclose(h,d.assessor2022_actual_pre1970_main_area_share,equal_nan=True,atol=1e-10)
        results.append(pd.DataFrame({'tract_id':d.index,'restriction':name,'pre1970_observed_main_area_share':h.to_numpy(),'valid_age_coverage':cov.to_numpy(),'recorded_area_retained_fraction':support.to_numpy(),'records':f.records.to_numpy(),'difference_from_all_recorded':(h-d.assessor2022_actual_pre1970_main_area_share).to_numpy()}))
    save('ASSESSOR_AGE_SUPPORT_SENSITIVITY.csv',pd.concat(results,ignore_index=True))
    log('Assessor restrictions calculated without asserting building deduplication.')

def scag_provenance():
    """Read cached numeric attributes only. No overlay or download is repeated."""
    manifest=pd.read_csv(source(S+'SCAG2020_CHUNK_HASHES.csv'));by={};byclass={};start=time.time()
    for rec in manifest.itertuples():
        p=lp(CA/REL/S/f'raw_cache/scag2020_chunks/{rec.chunk:04d}.json.gz');assert sha(p)==rec.gzip_sha256
        raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==rec.response_sha256
        for f in json.loads(raw)['features']:
            a=f['attributes'];name=str(a.get('ALU20_SRC'));acre=float(a.get('ACRES') or 0);v=by.setdefault(name,[0,0.]);v[0]+=1;v[1]+=acre
            key=(name,str(a.get('ALU20')));v=byclass.setdefault(key,[0,0.]);v[0]+=1;v[1]+=acre
    assert sum(v[0] for v in by.values())==2093407
    rows=[dict(source_origin=k,records=v[0],reported_parcel_acres_sum=v[1],record_fraction=v[0]/2093407,reported_acres_fraction=v[1]/sum(x[1] for x in by.values()),area_scope='county source ACRES; not deduplicated tract-land intersections') for k,v in by.items()]
    save('SCAG2020_RECORD_LINEAGE.csv',rows);save('SCAG2020_SOURCE_CODE_LINEAGE.csv',[dict(source_origin=k[0],ALU20=k[1],records=v[0],reported_parcel_acres_sum=v[1]) for k,v in byclass.items()]);log(f'SCAG cached record lineage audit {time.time()-start:.1f}s; no GIS overlay repeated.')

def main():
    master=frame(S+'CANDIDATE_VALUES_RESIDENTIAL_2291.csv');base=frame('final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv');ids=base.index[base.primary_complete_case];d=master.reindex(ids);assert len(d)==2287
    common=d[PHYSICAL].notna().all(axis=1);controls=['SOVI_SCORE','log1p_BUILDVALUE'];cc=d.loc[common];assert len(cc)==2286
    source_rows=[];reg=frame(S+'CANDIDATE_REGISTER.csv')
    for c in PHYSICAL:
        v=master[c];r=reg.loc[reg.candidate_id.eq(c)].iloc[0].to_dict();r.update(feature=c,master_n=2291,valid_master_n=int(v.notna().sum()),reference_n=2287,valid_reference_n=int(d[c].notna().sum()),common_n=len(cc),minimum=v.min(),p10=v.quantile(.1),median=v.median(),p90=v.quantile(.9),maximum=v.max());source_rows.append(r)
    save('SHORTLIST_MEASUREMENT_QA.csv',source_rows)
    excluded=[]
    for tid in master.index:
        reason=[c for c in PHYSICAL if pd.isna(master.at[tid,c])]
        if reason:excluded.append(dict(tract_id=tid,in_primary2287=tid in ids,missing=';'.join(reason),population=master.at[tid,'formal_population'],B_480_hr=master.at[tid,'B_480_hr'],SOVI_SCORE=master.at[tid,'SOVI_SCORE']))
    save('COMMON_SAMPLE_EXCLUSIONS.csv',excluded)
    rows=[]
    for a,b in itertools.combinations(PHYSICAL+['SOVI_SCORE','log1p_BUILDVALUE','ALR_NPCTL','Pop_Density_per_km2'],2):
        subset=cc[[a,b]+[c for c in controls if c not in [a,b]]].dropna();x=subset[a].to_numpy();y=subset[b].to_numpy();control=[c for c in controls if c not in [a,b]]
        cv=KFold(5,shuffle=True,random_state=20261011);est=make_pipeline(SplineTransformer(n_knots=5,degree=3),Ridge(alpha=1));pred=cross_val_predict(est,x[:,None],y,cv=cv)
        rows.append(dict(feature_a=a,feature_b=b,n=len(subset),GEOID_sha256=ids_sha(subset.index),pearson=stats.pearsonr(x,y).statistic,spearman=stats.spearmanr(x,y).statistic,nonlinear_5fold_spline_R2=r2_score(y,pred),partial_pearson=partial(x,y,subset[control].to_numpy()),controls=';'.join(control),interpretation='overlap diagnostics; not an admission score'))
    save('CANDIDATE_SOURCE_COMPARISON.csv',rows)
    diffrows=[];summary=[]
    for a,b,kind in PAIRS:
        delta=cc[b]-cc[a]
        for tid,v in delta.items():diffrows.append(dict(tract_id=tid,family=kind,source_a=a,source_b=b,value_a=cc.at[tid,a],value_b=cc.at[tid,b],difference_b_minus_a=v))
        summary.append(dict(family=kind,source_a=a,source_b=b,n=len(cc),GEOID_sha256=ids_sha(cc.index),pearson=stats.pearsonr(cc[a],cc[b]).statistic,spearman=stats.spearmanr(cc[a],cc[b]).statistic,mean_difference=delta.mean(),median_difference=delta.median(),mean_absolute_difference=delta.abs().mean(),p90_absolute_difference=delta.abs().quantile(.9),maximum_absolute_difference=delta.abs().max(),units='m' if 'height' in kind else 'fraction',equal_construct=kind in ['coverage','land_use']))
    save('SAME_CONSTRUCT_SOURCE_SUBSTITUTIONS.csv',summary);save('PAIRED_MEASUREMENT_DIFFERENCES.csv',diffrows)
    qa_fields=['tract_id']+PHYSICAL+['B_480_hr','Init_Supply','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','SOVI_SCORE','log1p_BUILDVALUE','NRI_BUILDVALUE','ALR_NPCTL','formal_population','T80','land_use_classified_land_coverage','scag2020_classified_land_coverage','all_use2014_age_coverage','assessor2022_actual_age_main_area_coverage','jrc_total_valid_land_coverage','outline_valid_height_area_fraction_centroid','nlcd_c12_valid_land_coverage','housing_5plus_share_moe90','housing_detached_share_moe90']
    mat=master.reset_index()[qa_fields];mat['primary2287']=mat.tract_id.isin(ids);mat['common2286']=mat.tract_id.isin(cc.index);save('SHORTLIST_FEATURE_MATRIX.csv',mat)
    dump('MEASUREMENT_COHORT_QA.json',dict(master_n=2291,reference_n=2287,common_n=len(cc),common_GEOID_sha256=ids_sha(cc.index),reference_GEOID_sha256=ids_sha(ids),excluded_from_reference=[i for i in ids if i not in cc.index],no_imputation=True,physical_variables_admitted_by_cluster_outcomes=False))
    acs_replicates(d);epa_sensitivity(master);assessor_restrictions(master);scag_provenance()
    log('Measurement gate numerical evidence completed before new clustering fits.')

if __name__=='__main__':main()
