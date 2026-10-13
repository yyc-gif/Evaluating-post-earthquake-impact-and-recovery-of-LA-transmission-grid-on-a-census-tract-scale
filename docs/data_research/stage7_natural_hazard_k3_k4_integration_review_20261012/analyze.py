"""Final source/interpretation checks using saved fits; no K-means fitting."""
from itertools import combinations
import fitz
import geopandas as gpd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score
from common import *


def stats(x):
    x=pd.Series(x);valid=x.dropna()
    return dict(n=len(x),valid=len(valid),missing=int(x.isna().sum()),zero=int(valid.eq(0).sum()),unique=valid.nunique(),unique_round6=valid.round(6).nunique(),minimum=valid.min(),p10=valid.quantile(.1),median=valid.median(),p90=valid.quantile(.9),maximum=valid.max(),mean=valid.mean(),sd=valid.std(ddof=0),CV=valid.std(ddof=0)/abs(valid.mean()) if valid.mean()!=0 else np.nan)


def aligned(a,b):
    ct=pd.crosstab(a,b);ri,ci=linear_sum_assignment(-ct.to_numpy());mapping={ct.columns[c]:ct.index[r] for r,c in zip(ri,ci)}
    return np.array([mapping.get(v,-1) for v in b]),ct


def main():
    s=reader();d=frame('inputs/FROZEN_COHORT.csv','tract_id')
    h=frame('inputs/NCV_VECTOR.csv','tract_id').reindex(d.index);d['FEMA_NCV14_CA_v119']=h.FEMA_NCV14_CA_v119
    n=frame('inputs/source_evidence/NRI_V119_CA_FROZEN.csv','TRACTFIPS');study=n.loc[d.index]
    raw=frame('inputs/NCV_RAW_FACTORS.csv','tract_id').reindex(d.index)
    nc=frame('inputs/NCV_HAZARD_COMPONENTS.csv','tract_id').reindex(d.index)
    hazards=[c for c in nc if c!='review_status'];assert len(hazards)==14
    p=frame('inputs/CGS_PGA_FROZEN.csv','tract_id').reindex(d.index)
    measurements=pd.DataFrame({'ERQK_AFREQ':raw.ERQK_AFREQ,'ERQK_EXP_AREA_sqmi':raw.ERQK_EXP_AREA_sqmi,'ERQK_area_fraction':raw.ERQK_area_fraction,'ERQK_frequency_area_factor':raw.ERQK_NCV_raw,'ERQK_CA_normalized':nc.ERQK,'CGS_PGA_land_mean_g':p.tract_seismic_PGA,'CGS_PGA_centroid_diagnostic_g':p.PGA_centroid_IDW_g})
    corr=[]
    for a,b in combinations(measurements,2):
        pair=measurements[[a,b]].dropna()
        corr.append(dict(a=a,b=b,n=len(pair),population=int(d.loc[pair.index,'Population'].sum()),Pearson=pair[a].corr(pair[b]),Spearman=pair[a].corr(pair[b],method='spearman'),top5pct_overlap=len(set(pair[a].nlargest(int(np.ceil(.05*len(pair)))).index)&set(pair[b].nlargest(int(np.ceil(.05*len(pair)))).index))/int(np.ceil(.05*len(pair)))))
    save('EARTHQUAKE_NRI_CGS_SPATIAL_RANK_COMPARISON.csv',corr)
    save('EARTHQUAKE_COMPONENT_DISTRIBUTIONS.csv',[dict(variable=c,**stats(measurements[c])) for c in measurements])
    save('EARTHQUAKE_MATCHED_TRACT_VALUES.csv',measurements.join(d[['Population']]).reset_index())
    save('CGS_PARTIAL_SUPPORT_NOT_IMPUTED.csv',p.loc[p.tract_seismic_PGA.isna()].join(d[['Population']]).reset_index())
    # Documentary statements stay separate from observations of the released table.
    doc=fitz.open(str(lp(OUT/'inputs/source_evidence/FEMA_V119_TECHNICAL.pdf')))
    pages=[151,152,153,154,155,163,164,165,166,167,168,177,178,179,180,181,184,185,186,271,272,273,274,275,276,398,399,400,407]
    dump('FEMA_TARGETED_DOCUMENTARY_EVIDENCE.json',dict(review_status=WARN,source_sha256=sha(OUT/'inputs/source_evidence/FEMA_V119_TECHNICAL.pdf'),PDF_page_text={str(i):doc[i-1].get_text() for i in pages},discrepancies=['StrongWind section18.1.1 says1986-2019/34y; sections18.6 and18.6.1 print70y','Earthquake proxy units/released exposed-area construction not revalidated against raw USGS raster','Exposure area is release-defined, not independently regenerated physical susceptibility geometry']))
    weather=[]
    for code,period,description in [('HAIL',34.,'NOAA/NWS SPC;1986-2019;80-km reporting buffer,49-km fishnet,national count scaling'),('SWND',34.,'NOAA/NWS SPC;1986-2019 in source section;AFREQ section prints70y;80-km buffer,49-km fishnet,national count scaling'),('HWAV',16.9,'NWS warning-day polygons viaIEM;2005-2022;forecast-zone boundaries,5% block-intersection rule')]:
        af=study[code+'_AFREQ'];events=study[code+'_EVNTS'];fraction=study[code+'_EXP_AREA']/study.AREA
        for kind,value in [('AFREQ',af),('geographic_fraction',fraction),('raw_factor',raw[code+'_NCV_raw']),('CA_normalized',nc[code])]:
            weather.append(dict(hazard=code,measurement=kind,source=description,**stats(value),dominant_rounded_value_fraction=value.round(6).value_counts(normalize=True).iloc[0],recorded_zero_not_missing=True,explicit_MAF_in_acquired_hazard_section=False))
        ratio=(events/af).where(af.gt(0))
        weather.append(dict(hazard=code,measurement='EVNTS_divided_by_AFREQ_diagnostic',source=description,**stats(ratio),reference_period_from_source_section=period,n_near34=int(np.isclose(ratio,34,rtol=0,atol=1e-5).sum()),n_near70=int(np.isclose(ratio,70,rtol=0,atol=1e-5).sum()),warning='Tract event count and area-weighted AFREQ need not use identical aggregation; ratio alone is not provider code reconstruction'))
    save('WEATHER_SOURCE_SCALE_AND_DEFAULT_AUDIT.csv',weather)
    weatherpairs=[]
    for a,b in combinations(['HWAV','HAIL','SWND'],2):
        for suffix,label in [('_AFREQ','released_frequency'),('_NCV_raw','frequency_area')]:
            x=study[a+suffix] if suffix=='_AFREQ' else raw[a+suffix];y=study[b+suffix] if suffix=='_AFREQ' else raw[b+suffix]
            weatherpairs.append(dict(a=a,b=b,measurement=label,Pearson=x.corr(y),Spearman=x.corr(y,method='spearman'),shared_provider=True,shared_generation_pipeline=a in ['HAIL','SWND'] and b in ['HAIL','SWND']))
    save('WEATHER_PAIRWISE_DEPENDENCE.csv',weatherpairs)
    attribution=[];total=nc[hazards].sum(1);variance=total.var(ddof=0)
    ext=frame('inputs/NCV_CA_AND_LA_EXTREMA.csv').set_index('hazard')
    for code in hazards:
        value=nc[code];diff=ext.loc[code,'CA_max']-ext.loc[code,'CA_min'];la_range=ext.loc[code,'LA_max']-ext.loc[code,'LA_min']
        attribution.append(dict(hazard=code,nominal_sum_coefficient=1.,source_factor_CA_range=diff,local_range_fraction_of_CA_range=la_range/diff,local_normalized_mean=value.mean(),local_normalized_sd=value.std(ddof=0),signed_covariance_share=((value-value.mean())*(total-total.mean())).mean()/variance,mean_share_in_sum=value.mean()/total.mean(),native_zero_count=int(raw[code+'_NCV_raw'].eq(0).sum()),source_unknown_count=int(raw[code+'_NCV_raw'].isna().sum())))
    save('HAZARD_SET_AND_NORMALIZATION_EFFECTIVE_INFLUENCE.csv',attribution)
    # A uniform frequency-unit conversion cancels exactly under hazard-level min-max.
    linear=[]
    for code in ['SWND','HAIL','ERQK']:
        q=n[code+'_AFREQ']*n[code+'_EXP_AREA']/n.AREA
        q=q.where(n[code+'_AFREQ'].ge(0)&n[code+'_EXP_AREA'].ge(0)&n.AREA.gt(0)&(n[code+'_EXP_AREA']/n.AREA).le(1+1e-9))
        scale=70/34 if code=='SWND' else 100.
        a=(q-q.min())/(q.max()-q.min());z=q*scale;b=(z-z.min())/(z.max()-z.min())
        linear.append(dict(hazard=code,diagnostic_uniform_multiplier=scale,maximum_normalized_error=(a-b).abs().max(),reinterpretation_of_original_units=False,meaning='Constant source-unit/period scale changes do not change per-hazard min-max ranks; spatial or inconsistent source processing still matters'))
    save('UNIFORM_SOURCE_SCALE_CANCELLATION_QA.csv',linear)
    fits=np.load(lp(OUT/'inputs/SAVED_LABELS_AND_SILHOUETTES.npz'));ix={k:i for i,k in enumerate(fits['keys'])};mats=np.load(lp(OUT/'inputs/SAVED_WEIGHTED_MATRICES.npz'))
    a=fits['labels'][ix['NCV14__main__k3__s42']];b=fits['labels'][ix['NCV14__main__k4__s42']]
    transition=[]
    for c in range(3):
        for e in range(4):
            mask=(a==c)&(b==e);transition.append(dict(K3_model_class=c,K4_model_class=e,n_tracts=int(mask.sum()),population=int(d.loc[mask,'Population'].sum()),share_of_K3_class=mask.sum()/np.sum(a==c)))
    save('K3_TO_K4_EXACT_MEMBERSHIP.csv',transition)
    profiles=[];groups=[];members=[];contrast=[]
    for condition in ['main','minus_Init']:
        for k in [3,4]:
            label=fits['labels'][ix[f'NCV14__{condition}__k{k}__s42']]
            for c in range(k):
                mask=label==c;pop=d.loc[mask,'Population'];q=d.loc[mask,'frozen_SOVI_quartile'].value_counts()
                groups.append(dict(condition=condition,k=k,model_class=c,proposed_display_ID=c+1,n_tracts=int(mask.sum()),population=int(pop.sum()),population_share=pop.sum()/d.Population.sum(),hospital_tracts=int(d.loc[mask,'hospital_tract'].sum()),hospital_fraction=d.loc[mask,'hospital_tract'].mean(),positive_zero_housing=int(d.loc[mask,'additional_zero_housing_positive_population'].sum()),population100_or_less=int(pop.le(100).sum()),**{name+'_n':int(q.get(name,0)) for name in ['Q1','Q2','Q3','Q4']}))
                for field in FEATURES+['Population','MeanTotalBurden','T80','hospital_tract']:
                    z=d.loc[mask,field];profiles.append(dict(condition=condition,k=k,model_class=c,variable=field,**stats(z),cohort_mean=d[field].mean(),cohort_median=d[field].median(),fitted_input=field in FEATURES and not(condition=='minus_Init' and field=='Init_Supply')))
            base=a if k==3 else b
            matched,ct=aligned(base,label)
            if condition=='minus_Init':
                for c in range(k):
                    for e in range(k):
                        mask=(base==c)&(label==e);members.append(dict(k=k,main_model_class=c,minus_Init_model_class=e,n_tracts=int(mask.sum()),population=int(d.loc[mask,'Population'].sum())))
                contrast.append(dict(k=k,comparison='main versus registered minus-Init',ARI=adjusted_rand_score(base,label),n_reassigned=int(np.sum(base!=matched)),reassigned_population=int(d.Population.to_numpy()[base!=matched].sum()),scientific_change='Deletes initial-state coordinate',numerical_change='RQ1 impact/HHI budgets rise from1/9 to1/6; no isolated new fit'))
    save('K3_K4_ORIGINAL_UNIT_PROFILES.csv',profiles);save('K3_K4_QUARTILE_POPULATION_HOSPITAL.csv',groups);save('INIT_ABLATION_CLASS_TRANSITIONS.csv',members);save('K3_K4_INIT_ABLATION_SUMMARY.csv',contrast)
    rare=d.loc[b==0].copy();assert len(rare)==38
    prior34=frame('inputs/PRIOR_Q34_NETWORK.csv','tract_id');rare['prior_Q34_member']=rare.index.isin(prior34.index)
    assert rare.prior_Q34_member.sum()==34
    save('K4_38_TRACT_EXACT_IDENTITY.csv',rare.reset_index())
    comparison_groups={'K4_38_initial_exception':b==0,'K3_475_parent':a==1,'K3_parent_without_exception':(a==1)&(b!=0),'K4_441_neighbor':b==2}
    descriptors=[]
    for name,mask in comparison_groups.items():
        for field in FEATURES+['Population','MeanTotalBurden','T80','hospital_tract']:
            descriptors.append(dict(group=name,variable=field,**stats(d.loc[mask,field])))
    save('K3_PARENT_AND_K4_RARE_GROUP_CONTRAST.csv',descriptors)
    leverage=[];x=mats['main']
    for k,label in [(3,a),(4,b)]:
        means=np.stack([x[label==c].mean(0) for c in range(k)]);overall=x.mean(0)
        between=np.array([np.sum(label==c)*(means[c]-overall)**2 for c in range(k)]).sum(0)
        for c in range(k):
            sq=(means[c]-overall)**2
            for j,f in enumerate(FEATURES):leverage.append(dict(k=k,model_class=c,variable=f,centroid_squared_share=sq[j]/sq.sum(),overall_between_share=between[j]/between.sum(),declared_budget=BUDGET[j]))
    save('K3_K4_DISTANCE_AND_DOMAIN_LEVERAGE.csv',leverage)
    # Frozen prior Q network evidence is descriptive trace, not a new source-adequacy experiment.
    dep=frame('inputs/PRIOR_Q34_DEPENDENCY.csv')
    station=dep.groupby(['substation_id','name']).agg(tract_count=('tract_id','nunique'),sum_initial_contribution=('initial_service_contribution','sum'),sum_dependency=('normalized_weight','sum'),mean_effective_initial=('mean_effective_initial','mean'),mean_source_connection_fraction=('source_connected_fraction','mean')).reset_index()
    station['share_of_Q34_initial_contribution']=station.sum_initial_contribution/station.sum_initial_contribution.sum()
    save('Q34_FROZEN_STATION_CONTRIBUTION_TRACE.csv',station)
    from scipy.sparse import csr_matrix
    physical=np.load(lp(s.source('docs/data_research/stage7_multi_policy_typology_20261012/FROZEN_STATION_INTEGRALS_AND_MAPPING.npz',AUTH)))
    mapping=csr_matrix((physical['mapping_data'],physical['mapping_indices'],physical['mapping_indptr']),shape=tuple(physical['mapping_shape']))
    rows=pd.Index(physical['tract_ids']).get_indexer(rare.index);assert np.all(rows>=0)
    weights=mapping[rows].toarray();initial=physical['initial_station_e_mean'];ids=physical['station_ids']
    contribution=weights*initial
    np.testing.assert_allclose(contribution.sum(1),rare.Init_Supply,atol=1e-14,rtol=0)
    source_trace=[]
    for i,tract in enumerate(rare.index):
        for j in np.flatnonzero(weights[i]>0):
            source_trace.append(dict(tract_id=tract,substation_id=str(ids[j]),dependency_weight=weights[i,j],frozen_effective_station_initial_mean=initial[j],initial_tract_contribution=contribution[i,j],fraction_of_initial_service=contribution[i,j]/rare.loc[tract,'Init_Supply'],prior_Q34_member=bool(rare.loc[tract,'prior_Q34_member'])))
    save('Q38_ALL_STATION_DEPENDENCY_AND_CONTRIBUTION.csv',source_trace)
    station_metadata=read(s,TI+'STATION_INITIAL_STATE_AND_DAMAGE_SUMMARY.csv')
    station_metadata['substation_id']=station_metadata.substation_id.astype(str)
    enriched=pd.DataFrame(source_trace);enriched['substation_id']=enriched.substation_id.astype(str)
    enriched=enriched.merge(station_metadata[['substation_id','name','is_Core','source_type']],on='substation_id',how='left',validate='many_to_one')
    assert enriched.name.notna().all()
    save('Q38_ALL_STATION_DEPENDENCY_AND_CONTRIBUTION.csv',enriched)
    save('Q38_ADDITIONAL_FOUR_SOURCE_TRACE.csv',enriched.loc[~enriched.prior_Q34_member&enriched.initial_tract_contribution.gt(0)])
    np.savez_compressed(dest('inputs/FROZEN_Q38_WEIGHT_AND_INITIAL_SOURCE.npz'),tract_ids=rare.index.to_numpy(dtype='U11'),station_ids=ids,weights=weights,station_effective_initial_mean=initial,expected_tract_initial=rare.Init_Supply.to_numpy(),realization_ids=physical['realization_ids'],physical_hashes=physical['physical_hashes'])
    # New candidate maps need the whole study domain, but only positive-population members are fitted.
    excluded=frame('inputs/EXCLUDED_ZERO_POPULATION_GEOIDS.csv');allids=pd.Index(list(d.index)+list(excluded.tract_id))
    assert len(allids)==2315 and allids.is_unique
    geometry=gpd.read_file('zip://'+str(lp(s.source(HN+'sources/CENSUS_TIGER2020_CA.zip',AUTH)))).set_index('GEOID').reindex(allids).to_crs(3310)
    assert geometry.geometry.notna().all();geometry.geometry=geometry.geometry.make_valid();geometry.index.name='tract_id'
    geometry[['geometry']].to_file(dest('candidate/FULL_2315_GEOMETRY.gpkg'),driver='GPKG')
    old=read(s,'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv','tract_id')
    save('inputs/FORMAL_OLD_STAGE7.csv',old.reset_index())
    text=lp(s.source('results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md',AUTH)).read_text(encoding='utf-8')
    selected=[t for t in text.split('## ') if t.startswith('Figure 7.') or t.startswith('Supplementary Figure S9.')]
    md('CURRENT_FORMAL_FIGURE7_AND_S9_BASELINE.md','\n\n'.join('## '+t for t in selected))
    q_idx=int(np.flatnonzero(ids=='308581')[0])
    dump('ANALYSIS_COMPLETION_AND_PHASE_GATES.json',dict(review_status=WARN,source_audit_complete=True,source_status='QUALIFIED_SOURCE_SCREENING_ONLY; native released factors,not physically independent full hazard validation',CGS_polygon_valid=int(p.tract_seismic_PGA.notna().sum()),CGS_unimputed_missing=int(p.tract_seismic_PGA.isna().sum()),no_new_fits=True,physical_realizations_regenerated=0,K3_K4_ARI=adjusted_rand_score(a,b),K3_parent475=int((a==1).sum()),K4_rare38=int((b==0).sum()),priorQ34=34,Q38_positive_Q_dependency=int((weights[:,q_idx]>0).sum()),Q38_initial_service_Q_share=contribution[:,q_idx].sum()/contribution.sum(),source_neutrality_claimed=False,stage3_allowed_as_author_review_only=True))
    save('SOURCE_HASH_VERIFICATION_ANALYSIS.csv',s.records)
    print('Analysis complete;source gate qualified;no new fits;K3/K4 ARI',adjusted_rand_score(a,b),flush=True)

if __name__=='__main__':main()
