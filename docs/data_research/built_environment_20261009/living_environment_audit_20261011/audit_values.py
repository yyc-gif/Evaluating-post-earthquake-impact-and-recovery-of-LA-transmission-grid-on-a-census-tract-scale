"""Exact-GEOID measurement audit. No cluster labels, fitting, weights or recovery outcomes used."""
from common import *
import pandas as pd,zipfile,itertools,geopandas as gpd,shapely
from scipy import stats

CANDIDATES=['canopy_2022_fraction','parks_all_published_fraction','parks_good_published_fraction','electric_heating_share','housing_5plus_share']
CONTEXT=['emc2022_total_built_land_fraction','log1p_population_density_per_km2','SOVI_SCORE']
REPS=[f'Var_Rep{i}' for i in range(1,81)]
SCIENCE='031d2c675f8e7d58035d27448be040b809ced086'

def archived_boundaries():
    paths=[source('Data/LA_Tracts_With_Population.'+e,SCIENCE) for e in ['shp','shx','dbf','prj','cpg']]
    g=gpd.read_file(paths[0]);key=next(c for c in ['GEOID','tract_id','GEOID20','TRACTFIPS'] if c in g)
    g['tract_id']=g[key].astype(str).str.zfill(11)
    assert g.tract_id.str.fullmatch(r'\d{11}').all() and not g.tract_id.duplicated().any()
    return g.set_index('tract_id').to_crs(3310)

def ratio_uncertainty(n,d,nr,dr,aw=16):
    valid=(d>0)&(n>=0)&(n<=d)
    p=np.divide(n,d,out=np.full(len(d),np.nan),where=valid)
    # Official 2022 VRE guidance: undefined replicate denominator -> zero replicate ratio.
    r=np.divide(nr,dr,out=np.zeros_like(nr,dtype=float),where=dr!=0)
    se=np.sqrt((4/80)*np.square(r-p[:,None]).sum(axis=1))
    boundary=valid&((p==0)|(p==1)|(se==0))
    pstar=np.minimum(.5,np.divide(2.3*aw,d,out=np.full(len(d),np.nan),where=d>0))
    bse=np.sqrt(pstar*(1-pstar)*np.divide(aw,d,out=np.full(len(d),np.nan),where=d>0))
    se=np.where(boundary,bse,se)
    return p,r,se,boundary

def vre(path,ids,orders):
    with zipfile.ZipFile(path) as z:f=pd.read_csv(z.open(z.namelist()[0]),dtype={'GEOID':str})
    f=f.loc[f.GEOID.str.startswith('1400000US06037',na=False)].copy();f['tract_id']=f.GEOID.str[-11:]
    den=f.loc[f.ORDER.eq(1)].set_index('tract_id').reindex(ids)
    num=f.loc[f.ORDER.isin(orders)].groupby('tract_id')[['ESTIMATE','MOE']+REPS].sum(min_count=1).reindex(ids)
    assert not den.index.duplicated().any()
    p,r,se,b=ratio_uncertainty(num.ESTIMATE.to_numpy(),den.ESTIMATE.to_numpy(),num[REPS].to_numpy(),den[REPS].to_numpy())
    return den,num,p,r,se,b

def assemble():
    parent=frame('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_2315.csv')
    residential=frame('final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv')
    reference_ids=residential.index[residential.primary_complete_case.astype(bool)]
    assert len(parent)==2315 and len(residential)==2291 and len(reference_ids)==2287
    assert set(residential.index)==set(parent.index[parent.residential_member.astype(bool)])
    assert set(residential.index.difference(reference_ids))==set(UNRESOLVED)
    assert parent.index.str.fullmatch(r'\d{11}').all() and not parent.index.duplicated().any()
    keep=['formal_population','residential_member','Pop_Density','Pop_Density_per_km2','SOVI_SCORE','emc2022_total_built_land_fraction','housing_5plus_share','housing_5plus_share_moe90']
    f=parent[keep].copy();f['reference2287']=f.index.isin(reference_ids);f['core3_geometry_unresolved']=f.index.isin(UNRESOLVED)
    f['log1p_population_density_per_km2']=np.log1p(f.Pop_Density_per_km2.where(f.Pop_Density_per_km2>=0))
    np.savez_compressed(lp(OUT/'COHORT_IDENTITIES.npz'),model_ids=parent.index.to_numpy(dtype='U11'),residential_ids=residential.index.to_numpy(dtype='U11'),reference_ids=reference_ids.to_numpy(dtype='U11'))
    dump('BASELINE_IDENTITY_QA.json',dict(baseline=BASELINE,model_n=2315,residential_n=2291,reference_n=2287,model_order_sha256=idhash(parent.index),residential_order_sha256=idhash(residential.index),reference_order_sha256=idhash(reference_ids),unclassified_geometry_ids=UNRESOLVED,source_columns_preserved=keep,cluster_labels_used=False,recovery_outcomes_used=False))
    return f,reference_ids

def canopy(f,g):
    features=[]
    for offset in ['0','1000','2000']:features+=json.loads(lp(OUT/'sources'/('CANOPY_LA_'+offset+'.geojson')).read_text(encoding='utf-8'))['features']
    a=gpd.GeoDataFrame.from_features(features,crs=4326).to_crs(3310).set_index('FIPS')
    assert len(a)==json.loads(lp(OUT/'sources/CANOPY_LA_COUNT.json').read_text(encoding='utf-8'))['count']
    assert a.index.str.fullmatch(r'\d{11}').all() and not a.index.duplicated().any()
    assert a.index.equals(pd.Index(a.FIPS_1.to_numpy()))
    a['canopy_2022_fraction']=a.PctCan22/100
    a['implied_analysis_area_m2']=a.AREA22/a.canopy_2022_fraction
    a['implied_analysis_to_source_tract_area']=a.implied_analysis_area_m2/a.Shape__Area
    a['CanoAcr22_per_AREA22']=a.CanoAcr22/a.AREA22
    for c in ['canopy_2022_fraction','PctCan22','CanoAcr22','AREA22','PctCan18','Shape__Area','POPULATION_2020','implied_analysis_area_m2','implied_analysis_to_source_tract_area']:
        f[c if c=='canopy_2022_fraction' else 'canopy_'+c]=a[c].reindex(f.index)
    f['canopy_2022_valid']=f.canopy_2022_fraction.between(0,1)&(f.canopy_AREA22>=0)
    f['canopy_source_match']=f.index.isin(a.index)
    save('CANOPY_LA_PUBLISHED_VALUES.csv',a.drop(columns='geometry').reset_index())
    m=g.reindex(f.index);a=a.reindex(f.index)
    valid=m.geometry.notna()&a.geometry.notna()&m.geometry.is_valid&a.geometry.is_valid
    rows=[]
    for tract in f.index:
        row=dict(tract_id=tract,source_match=bool(f.loc[tract,'canopy_source_match']),frozen_geometry_valid=bool(m.loc[tract].geometry.is_valid),source_geometry_valid=bool(a.loc[tract].geometry.is_valid) if a.loc[tract].geometry is not None else False)
        if valid.loc[tract]:
            x=m.loc[tract].geometry;y=a.loc[tract].geometry;intersection=x.intersection(y).area;union=x.union(y).area
            row.update(frozen_area_m2=x.area,source_geometry_area_m2=y.area,intersection_m2=intersection,geometry_IoU=intersection/union,relative_symmetric_difference=(union-intersection)/x.area,centroid_distance_m=x.centroid.distance(y.centroid),source_stored_shape_area_m2=a.loc[tract,'Shape__Area'],implied_canopy_analysis_area_m2=a.loc[tract,'implied_analysis_area_m2'])
        rows.append(row)
    compare=pd.DataFrame(rows);save('CANOPY_GEOMETRY_COMPARISON.csv',compare)
    urban=json.loads(lp(OUT/'sources/CENSUS2020_URBAN_LA.geojson').read_text(encoding='utf-8'))
    assert urban.get('type')=='FeatureCollection' and not urban.get('exceededTransferLimit',False)
    u=gpd.GeoDataFrame.from_features(urban['features'],crs=4326).to_crs(3310)
    original_valid=u.geometry.is_valid.to_numpy();before_area=u.geometry.area.to_numpy()
    u.geometry=shapely.make_valid(u.geometry.to_numpy())
    assert u.geometry.is_valid.all()
    save('URBAN_SUPPORT_GEOMETRY_QA.csv',pd.DataFrame(dict(GEOID=u.GEOID,NAME=u.NAME,original_valid=original_valid,original_area_m2=before_area,analysis_repaired_area_m2=u.geometry.area,relative_area_change=(u.geometry.area-before_area)/np.maximum(before_area,1),operation='make_valid only for support intersection; cached official geometry unchanged')))
    union=shapely.union_all(u.geometry.to_numpy())
    intersections=shapely.intersection(m.geometry.to_numpy(),union)
    f['census2020_urban_area_fraction']=shapely.area(intersections)/m.geometry.area.to_numpy()
    f['canopy_implied_analysis_to_frozen_tract_area']=f.canopy_implied_analysis_area_m2/m.geometry.area
    f['canopy_implied_area_vs_census2020_urban_relative_error']=(f.canopy_implied_analysis_area_m2-shapely.area(intersections))/np.maximum(shapely.area(intersections),1)
    # This is denominator/source-support verification, not extraction of new canopy pixels.
    save('CANOPY_ANALYSIS_SUPPORT_AUDIT.csv',f[['canopy_PctCan22','canopy_AREA22','canopy_CanoAcr22','canopy_Shape__Area','canopy_implied_analysis_area_m2','canopy_implied_analysis_to_source_tract_area','canopy_implied_analysis_to_frozen_tract_area','census2020_urban_area_fraction','canopy_implied_area_vs_census2020_urban_relative_error','formal_population','Pop_Density_per_km2','residential_member','reference2287']].reset_index())
    dump('CANOPY_NUMERICAL_QA.json',dict(county_rows=len(features),duplicate_FIPS=0,source_FIPS_join_identity=True,percentage_invalid_n=int((~pd.Series([z['properties']['PctCan22'] for z in features]).between(0,100)).sum()),acres_per_area_m2_median=float(f.canopy_CanoAcr22.div(f.canopy_AREA22).median()),published_vs_full_tract_percent_max_difference=float((f.canopy_PctCan22-100*f.canopy_AREA22/f.canopy_Shape__Area).abs().max()),boundary_IoU=compare.geometry_IoU.describe(percentiles=[.01,.1,.5,.9]).to_dict(),census2020_urban_features=len(u),implied_denominator_is_inference=True,denominator_confirmed_by_support_intersection=False))
    log('Canopy source and geometry checks completed')

def parks(f):
    p=pd.read_csv(lp(OUT/'sources/PARKS_DOWNLOAD_0.payload'),dtype={'geoid':str,'geoid20':str})
    p['tract_id']=p.geoid.str.extract(r'(\d{11})$')[0];assert p.tract_id.str.fullmatch(r'\d{11}').all() and not p.tract_id.duplicated().any()
    assert (p.geoid20.str.zfill(11)==p.tract_id).all() and set(p.year)=={2022}
    p=p.set_index('tract_id');f['parks_source_match']=f.index.isin(p.index)
    for c in p.columns:f['parks_'+c]=p[c].reindex(f.index)
    errors={}
    for key,pct,num in [('all','park_access_pct','park_access_count'),('good','good_park_access_pct','good_park_access_count')]:
        raw=f['parks_'+pct];fraction=raw/100
        # Keep tiny float32 overshoots exactly; flag rather than silently clamp.
        f['parks_'+key+'_published_fraction']=fraction.where(raw.between(-1e-3,100+1e-3)&(f.parks_denom_total_pop>0))
        f['parks_'+key+'_rounding_overshoot']=((raw<0)|(raw>100))&raw.between(-1e-3,100+1e-3)
        f['parks_'+key+'_invalid']=~raw.between(-1e-3,100+1e-3)|(f.parks_denom_total_pop<=0)
        errors[key]=float((raw-100*f['parks_'+num]/f.parks_denom_total_pop).abs().max())
    save('PARKS_LA_PUBLISHED_VALUES.csv',p.reset_index())
    same=f.parks_denom_total_pop.notna()&f.canopy_POPULATION_2020.notna()
    dump('PARKS_NUMERICAL_QA.json',dict(county_rows=len(p),duplicate_GEOID=0,published_years=[2022],id_reproduction=True,published_percentage_vs_count_ratio_max_difference_pp=errors,all_rounding_overshoot_n=int(f.parks_all_rounding_overshoot.sum()),good_rounding_overshoot_n=int(f.parks_good_rounding_overshoot.sum()),good_exceeds_all_n=int((f.parks_good_published_fraction>f.parks_all_published_fraction+1e-5).sum()),denominator_comparison_with_source_Census2020_population_n=int(same.sum()),denominator_exact_Census2020_population_agreement_n=int((f.loc[same,'parks_denom_total_pop']==f.loc[same,'canopy_POPULATION_2020']).sum()),population_weighting_verified=False,area_weighting_verified=False,method_issue='Population-denominator/count fields reproduce the ratio but do not establish spatial allocation. Published prose states residents; method only specifies buffer/tract overlay. No population-surface/block apportionment or pure area formula supplied.',network_accessibility_verified=False))

def acs(f):
    weight=pd.read_csv(src('validation/sources/VRE_AVERAGE_WEIGHT_2022.csv'));aw=float(weight.loc[weight.FIPS_STATE_CODE.eq('6'),'AVERAGE_WEIGHT'].iloc[0]);assert aw==16
    hd,hn,hp,hr,hse,hb=vre(src('validation/sources/B25024_06.csv.zip'),f.index,[6,7,8,9])
    old=frame('validation/ACS_TRACT_VALIDATION.csv').reindex(f.index)
    assert np.allclose(hp,f.housing_5plus_share,equal_nan=True,atol=1e-13)
    assert np.allclose(hp,old.housing_5plus_share,equal_nan=True,atol=1e-13)
    assert np.allclose(1.645*hse,f.housing_5plus_share_moe90,equal_nan=True,atol=1e-13)
    assert np.array_equal(hb,old.housing_5plus_share_boundary_model)
    ed,en,ep,er,ese,eb=vre(lp(OUT/'sources/B25040_06.csv.zip'),f.index,[4])
    f['electric_heating_share']=ep;f['electric_heating_share_moe90']=1.645*ese
    f['electric_heating_occupied_units']=ed.ESTIMATE;f['electric_heating_occupied_units_moe90']=ed.MOE
    f['electric_heating_units']=en.ESTIMATE;f['electric_heating_units_moe90']=en.MOE
    f['electric_heating_boundary_model']=eb;f['electric_heating_denominator_CI90_includes_zero']=ed.ESTIMATE<=ed.MOE
    f['electric_heating_zero_replicate_denominators']=(ed[REPS].to_numpy()==0).sum(axis=1)
    f['electric_heating_source_match']=ed.ESTIMATE.notna()
    f['housing_total']=hd.ESTIMATE;f['housing_total_moe90']=hd.MOE
    f['housing_5plus_share_boundary_model']=hb;f['housing_5plus_denominator_CI90_includes_zero']=hd.ESTIMATE<=hd.MOE
    f['housing_5plus_zero_replicate_denominators']=(hd[REPS].to_numpy()==0).sum(axis=1)
    rows=[]
    for name,den,num,p,r,se,b in [('electric_heating_share',ed,en,ep,er,ese,eb),('housing_5plus_share',hd,hn,hp,hr,hse,hb)]:
        cv=np.divide(se,p,out=np.full(len(p),np.nan),where=p>0)
        for i,tract in enumerate(f.index):
            rows.append(dict(tract_id=tract,candidate=name,residential_member=bool(f.loc[tract,'residential_member']),reference2287=bool(f.loc[tract,'reference2287']),point_estimate=p[i],numerator=num.ESTIMATE.iloc[i],denominator=den.ESTIMATE.iloc[i],denominator_MOE90=den.MOE.iloc[i],denominator_CI90_includes_zero=bool(den.ESTIMATE.iloc[i]<=den.MOE.iloc[i]),standard_error=se[i],MOE90=1.645*se[i],CI90_low_display=max(0,p[i]-1.645*se[i]) if np.isfinite(p[i]) else np.nan,CI90_high_display=min(1,p[i]+1.645*se[i]) if np.isfinite(p[i]) else np.nan,CV=cv[i],MOE90_gt_5pp=bool(1.645*se[i]>.05),MOE90_gt_10pp=bool(1.645*se[i]>.10),CV_gt_30pct=bool(cv[i]>.30),boundary_model=bool(b[i]),undefined_replicate_denominator_count=int((den[REPS].iloc[i]==0).sum()),method='80 VRE, SDR factor 4/80; zero replicate denominators set to zero; official boundary variance with CA average weight16',valid_estimate=bool(np.isfinite(p[i])),precision_exclusion=False))
    save('ACS_UNCERTAINTY_AUDIT.csv',rows)
    np.savez_compressed(lp(OUT/'ACS_PAIRED_VARIANCE_REPLICATES.npz'),tract_ids=f.index.to_numpy(dtype='U11'),heating_ratio_replicates=er,housing5plus_ratio_replicates=hr,heating_point=ep,housing5plus_point=hp,heating_SE=ese,housing5plus_SE=hse,heating_boundary=eb,housing5plus_boundary=hb)
    dump('ACS_NUMERICAL_QA.json',dict(VRE_year=2022,period='2018-2022',replicates=80,SDR_variance_factor=.05,CA_average_weight=aw,housing_point_max_absolute_reproduction_error=float(np.nanmax(abs(hp-f.housing_5plus_share))),housing_MOE90_max_absolute_reproduction_error=float(np.nanmax(abs(1.645*hse-f.housing_5plus_share_moe90))),stored_housing_method_preserved=True,electric_heating_numerator_order=4,electric_heating_denominator_order=1,electric_heating_negative_estimate_n=int(((ed.ESTIMATE<0)|(en.ESTIMATE<0)).sum()),electric_heating_zero_denominator_n=int(ed.ESTIMATE.eq(0).sum()),electric_heating_num_exceeds_den_n=int((en.ESTIMATE>ed.ESTIMATE).sum()),electric_heating_negative_replicate_denominators_n=int((ed[REPS]<0).sum().sum()),Census_API_data_unavailable=True,estimates_and_original_MOEs_retrieved_from_official_VRE_archive=True,interpretation='Principal heating fuel among occupied housing units, not all electricity dependence, air-conditioning, heating season losses or backup power'))
    log('Covariance-aware ACS uncertainty completed; verified housing measurements preserved')

def svi_components(f):
    path=lp(OUT/'sources/CDC_SVI2020_CALIFORNIA.csv')
    if not path.exists():return
    s=pd.read_csv(path,dtype={'FIPS':str});s=s.loc[s.FIPS.str.startswith('06037')].set_index('FIPS')
    assert not s.index.duplicated().any()
    cols=['EP_MUNIT','EP_MOBILE','EP_CROWD','EP_NOVEH','EP_GROUPQ','RPL_THEME4','RPL_THEMES']
    for c in cols:
        if c in s:f['SVI2020_CA_'+c]=s[c].where(s[c]>=0).reindex(f.index)
    dump('SVI_COMPONENT_SCOPE_QA.json',dict(county_rows=len(s),source='CDC/ATSDR SVI2020 California file via official webapi',ACS_period='2016-2020',raw_EP_components_are_percentages=True,state_RPL_percentiles_not_equivalent_to_frozen_national_SOVI=True,aggregate_SOVI_unchanged=True,component_coordinates_not_admitted=True,mechanical_overlap='SVI2020 EP_MUNIT = (DP04_0012E + DP04_0013E) / E_HU *100: 10+ units from 2016-2020 ACS DP04. Housing5plus uses B25024 orders6-9 /order1, 2018-2022 ACS. Nested housing configuration constructs and overlapping survey years, not identical coordinates.'))

def distributions(f):
    rows=[];extreme=[];missing=[];coverage=[]
    for cohort,mask in [('reference2287',f.reference2287),('residential2291',f.residential_member),('model2315',np.ones(len(f),bool))]:
        for c in CANDIDATES+CONTEXT:
            x=f.loc[mask,c];v=x.dropna();qs=v.quantile([.1,.25,.5,.75,.9])
            rows.append(dict(cohort=cohort,candidate=c,cohort_n=len(x),valid_n=len(v),missing_n=int(x.isna().sum()),minimum=v.min(),P10=qs.loc[.1],P25=qs.loc[.25],median=qs.loc[.5],P75=qs.loc[.75],P90=qs.loc[.9],maximum=v.max(),mean=v.mean(),standard_deviation=v.std(ddof=1),zero_fraction=float(v.eq(0).mean()),skewness=v.skew(),units='percentile score0-100' if c=='SOVI_SCORE' else ('log1p persons/km2' if c.startswith('log1p_') else 'fraction')))
            bad=x[x.isna()].index
            for tract in bad:missing.append(dict(cohort=cohort,candidate=c,tract_id=tract,reason='undefined denominator' if c in ['electric_heating_share','housing_5plus_share'] else 'source/measurement unavailable',geometry_unresolved=bool(f.loc[tract,'core3_geometry_unresolved']),formal_population=f.loc[tract,'formal_population'],Pop_Density_per_km2=f.loc[tract,'Pop_Density_per_km2']))
            for tail,z in [('low',v.nsmallest(10)),('high',v.nlargest(10))]:
                for tract,value in z.items():extreme.append(dict(cohort=cohort,candidate=c,tail=tail,tract_id=tract,value=value,formal_population=f.loc[tract,'formal_population'],Pop_Density_per_km2=f.loc[tract,'Pop_Density_per_km2'],canopy_analysis_support=f.loc[tract,'canopy_implied_analysis_to_frozen_tract_area']))
            coverage.append(dict(cohort=cohort,candidate=c,cohort_n=len(x),valid_n=len(v),valid_percent=100*len(v)/len(x),missing_n=len(bad),missing_GEOIDs=';'.join(bad),successful_GEOID_matches=int(f.loc[mask,'canopy_source_match'].sum()) if c.startswith('canopy_') else (int(f.loc[mask,'parks_source_match'].sum()) if c.startswith('parks_') else (int(f.loc[mask,'electric_heating_source_match'].sum()) if c=='electric_heating_share' else (int(f.loc[mask,'housing_total'].notna().sum()) if c=='housing_5plus_share' else len(v)))),invalid_or_undefined_count=len(bad),validity_does_not_certify_interpretation=True))
    save('CANDIDATE_DISTRIBUTIONS.csv',rows);save('SOURCE_MATCH_AND_COVERAGE.csv',coverage)
    save('MISSING_INVALID_GEOIDS.csv',pd.DataFrame(missing,columns=['cohort','candidate','tract_id','reason','geometry_unresolved','formal_population','Pop_Density_per_km2']))
    save('EXTREME_OBSERVATIONS.csv',extreme)

def corr(x,y):
    if len(x)<3 or np.std(x)==0 or np.std(y)==0:return np.nan,np.nan
    return float(stats.pearsonr(x,y).statistic),float(stats.spearmanr(x,y).statistic)
def residual(y,X):
    A=np.c_[np.ones(len(X)),X];return y-A@np.linalg.lstsq(A,y,rcond=None)[0]

def redundancy(f):
    ref=f.loc[f.reference2287].copy();cols=CANDIDATES+CONTEXT
    common=ref[cols].dropna().index;rows=[];sets={}
    def add(kind,a,b,d,controls=None):
        pr,sr=corr(d[a],d[b]);key=idhash(d.index);sets[key]=d.index.tolist()
        row=dict(kind=kind,candidate_a=a,candidate_b=b,n=len(d),GEOID_order_sha256=key,Pearson=pr,Spearman=sr,controls=';'.join(controls or []),interval='none; descriptive tract statistics')
        if controls:
            row['partial_Pearson']=corr(residual(d[a].to_numpy(),d[controls].to_numpy()),residual(d[b].to_numpy(),d[controls].to_numpy()))[0]
            ranked=d[[a,b]+controls].rank();row['partial_Spearman_rank_residual']=corr(residual(ranked[a].to_numpy(),ranked[controls].to_numpy()),residual(ranked[b].to_numpy(),ranked[controls].to_numpy()))[0]
        rows.append(row)
    for a,b in itertools.combinations(cols,2):
        d=ref[[a,b]].dropna();add('pairwise_reference',a,b,d)
        add('identical_all_indicator_complete_subset',a,b,ref.loc[common,cols])
        controls=[c for c in ['housing_5plus_share']+CONTEXT if c not in [a,b]]
        if a in CANDIDATES and b in CANDIDATES:add('conditional_on_existing_measurements',a,b,ref[[a,b]+controls].dropna(),controls)
    for c in CANDIDATES:
        controls=[x for x in ['housing_5plus_share']+CONTEXT if x!=c];d=ref[[c]+controls].dropna();y=d[c].to_numpy();e=residual(y,d[controls].to_numpy());r2=1-np.var(e)/np.var(y);key=idhash(d.index);sets[key]=d.index.tolist()
        rows.append(dict(kind='residual_variance_existing_controls',candidate_a=c,candidate_b='',n=len(d),GEOID_order_sha256=key,controls=';'.join(controls),OLS_explained_fraction=r2,residual_variance_fraction=1-r2,VIF_if_simultaneous=1/(1-r2)))
    for setname,variables in [('all_published_measures',cols),('omit_condition_rated_good_parks',[c for c in cols if c!='parks_good_published_fraction'])]:
        d=ref[variables].dropna();Z=(d-d.mean())/d.std(ddof=0);key=idhash(d.index);sets[key]=d.index.tolist()
        for c in variables:
            e=residual(Z[c].to_numpy(),Z.drop(columns=c).to_numpy());r2=1-np.var(e)
            rows.append(dict(kind='simultaneous_VIF_'+setname,candidate_a=c,candidate_b='',n=len(d),GEOID_order_sha256=key,controls=';'.join(x for x in variables if x!=c),VIF_if_simultaneous=1/(1-r2),OLS_explained_fraction=r2,standardized_condition_number=np.linalg.cond(Z.to_numpy())))
    svi=[c for c in ref if c.startswith('SVI2020_CA_EP_')]
    for a in ['housing_5plus_share','SOVI_SCORE','log1p_population_density_per_km2']:
        for b in svi:add('SVI_housing_transportation_component_audit',a,b,ref[[a,b]].dropna())
    npz=np.load(lp(OUT/'ACS_PAIRED_VARIANCE_REPLICATES.npz'));ix=np.flatnonzero(f.reference2287.to_numpy());rep=[]
    for j in range(80):
        d=ref.copy();d['housing_5plus_share']=npz['housing5plus_ratio_replicates'][ix,j];d['electric_heating_share']=npz['heating_ratio_replicates'][ix,j]
        for a,b in itertools.combinations(cols,2):
            if a not in ['housing_5plus_share','electric_heating_share'] and b not in ['housing_5plus_share','electric_heating_share']:continue
            v=d[[a,b]].dropna();pr,sr=corr(v[a],v[b]);rep.append(dict(replicate=j+1,candidate_a=a,candidate_b=b,n=len(v),Pearson=pr,Spearman=sr,meaning='corresponding official survey replicates, not independent datasets; boundary variance not fully represented by raw replicate ratios'))
    save('ACS_REPLICATE_CORRELATION_SENSITIVITY.csv',rep)
    for tag,mask in [('both_ACS_MOE90_le_5pp',(ref.housing_5plus_share_moe90<=.05)&(ref.electric_heating_share_moe90<=.05)),('both_ACS_MOE90_le_10pp',(ref.housing_5plus_share_moe90<=.10)&(ref.electric_heating_share_moe90<=.10)),('canopy_implied_support_ge_99pct',ref.canopy_implied_analysis_to_frozen_tract_area>=.99),('exclude_lowest_density_quartile',ref.Pop_Density_per_km2>ref.Pop_Density_per_km2.quantile(.25))]:
        for a,b in itertools.combinations(cols,2):add('measurement_support_sensitivity_'+tag,a,b,ref.loc[mask,[a,b]].dropna())
    save('CANDIDATE_REDUNDANCY.csv',rows);dump('COMPARISON_GEOID_SETS.json',sets)
    log('Distributions, exact-sample correlations, survey sensitivity and conditional redundancy completed')

if __name__=='__main__':
    f,ids=assemble();g=archived_boundaries();assert set(f.index)<=set(g.index);g=g.loc[f.index]
    canopy(f,g);parks(f);acs(f);svi_components(f)
    save('LIVING_ENVIRONMENT_VALUES_2315.csv',f.reset_index());save('LIVING_ENVIRONMENT_VALUES_RESIDENTIAL_2291.csv',f.loc[f.residential_member].reset_index());save('LIVING_ENVIRONMENT_VALUES_REFERENCE_2287.csv',f.loc[ids].reset_index())
    distributions(f);redundancy(f)
