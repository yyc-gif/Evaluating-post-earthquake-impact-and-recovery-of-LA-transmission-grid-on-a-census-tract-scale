"""Measurement QA, descriptive summaries and evidence-bounded decision support."""
from controlled_audit import *
def measurement_qa():
 master,d,blocks,sets=inputs()
 details={
 'land_use_entropy':('SCAG 2019 ALU 2019.1','2019 parcel classifications','-sum(p log p)/log(11); p=exclusive classified category area / all classified area','classified parcel land only','land_use_classified_land_coverage','land-use mixture; not total-land composition or density','Unclassified land and public ROW not known; stacked/conflicting geometries resolved by existing union overlay; no invented category','KEEP as precisely named classified-parcel mix'),
 'building_footprint_coverage':('LARIAC6 2020 release','cumulative imagery, predominantly 2008; mixed acquisition years','union building footprint area clipped to tract land / validated tract land area','all observed outline uses','building_footprint_coverage','ground-building coverage; not building count, floor area, or occupancy','Roof outline / historical imagery / undocumented detection limit; not a new 2020 census of buildings','KEEP as ground-building coverage'),
 'all_use2014_pre1970_area_share':('LARIAC4 original 2014 outlines; assessor-associated YearBuilt1','2014 inventory and valid associated construction years','union pre-1970 valid-age footprint area / union valid-age footprint area','observed valid-age stock of 2014, all available uses','all_use2014_age_coverage','historical observed building-age composition; not complete current stock or independently validated fragility','Nonrandom age missingness by use; government missingness; 2014-2020 transfer is not representative; vintage caveat essential','DECISION_IN_MEMO'),
 'residential_pre1970_housing_share':('ACS B25034 2022 5-year','2018-2022 residential unit estimates','estimated pre-1970 housing units / estimated all housing units','residential housing units','residential_pre1970_housing_share','residential age composition; not all-use area-weighted building age','Survey estimate with MOE; nonresidential uses excluded; replacement changes construct','SENSITIVITY ONLY'),
 'building_count_density':('LARIAC6 2020 release','mixed earlier imagery','centroid-assigned building count / Census ALAND in km2','observed outlines','building_count_density','number intensity, not footprint size or floor area','Tract assignment by centroid; count sensitive to building segmentation and detection','DESCRIPTION ONLY'),
 'impervious_land_fraction':('ESRI AnnualNLCD2022 Collection1.0 pilot','2022 pilot','existing numerical impervious fraction','pilot raster support','impervious_valid_coverage_fraction','surface impermeability; includes roads and other non-building surfaces','Direct USGS source/version correspondence not verified; cannot upgrade pilot to authoritative input','NOT ADMITTED AS PRIMARY'),
 'log1p_NRI_BUILDVALUE':('FEMA NRI v1.19 March 2023','Hazus 6.0/2020 geography; 2022-dollar stock convention','log1p(BUILDVALUE)','total modeled building economic stock','log1p_NRI_BUILDVALUE','economic stock, not household income or annual loss','Shared economic exposure sources with EAL; total stock varies with tract scale','CONSTRUCT CHOICE IN MEMO'),
 'ALR_NPCTL':('FEMA NRI v1.19 March 2023','archived multi-hazard historical loss model','published national composite expected-annual-loss-rate percentile','exposure-normalized loss propensity, EAL-weighted components','ALR_NPCTL','multi-hazard loss-rate propensity; not pure PGA, simple EAL/stock or SOVI-adjusted percentile','Locally earthquake-dominated; different hazards contribute unequally; geographic percentiles not interval loss units','CONSTRUCT CHOICE IN MEMO'),
 'EAL_SCORE':('FEMA NRI v1.19 March 2023','archived multi-hazard historical loss model','national percentile of monetized total expected annual loss','building, population-equivalent and agriculture losses','EAL_SCORE','combined exposure and expected loss, not pure hazard','Replacing stock+rate removes independently interpretable stock coordinate; social geography need not be independent','SENSITIVITY ALTERNATIVE')}
 rows=[]
 for col,(source,vintage,definition,domain,coverage,means,limits,decision) in details.items():
  v=master[col];cv=d[coverage]
  rows.append(dict(feature=col,source=source,vintage=vintage,numerator_denominator=definition,measurement_domain=domain,defined_residential_n=int(v.notna().sum()),residential_n=2291,missing_n=int(v.isna().sum()),common_cohort_n=2287,common_cohort_valid_n=int(d[col].notna().sum()),minimum=float(d[col].min()),p10=float(d[col].quantile(.1)),median=float(d[col].median()),p90=float(d[col].quantile(.9)),maximum=float(d[col].max()),coverage_or_comparator_field=coverage,median_coverage_or_comparator=float(cv.median()),measurement_meaning=means,limitations=limits,recommendation_scope=decision))
 save('BUILT_ENV_MEASUREMENT_QA.csv',rows)
 pooled=pd.read_csv(BASE/'BUILDING_AGE_POOLED_USE_MISSINGNESS.csv');save('AGE_USE_MISSINGNESS_REUSED.csv',pooled)
 sourceextra=[]
 for path in [ROOT/'local_joint_feature_extraction_20261009/TRACT_FEATURE_CANDIDATES.csv',ROOT/'local_joint_feature_extraction_20261009/BUILDING_AGE_COMPLETENESS_AND_SENSITIVITY.md',ROOT/'local_joint_feature_extraction_20261009/BUILT_ENVIRONMENT_SOURCE_AND_GEOMETRY_AUDIT.md',BASE/'FINAL_FEATURE_DEFINITIONS_AND_QA.csv',BASE/'BUILDING_AGE_POOLED_USE_MISSINGNESS.csv',BASE/'SCAG_ENTROPY_SENSITIVITY.csv',BASE/'BUILDING_AGE_SENSITIVITY.csv']:
  sourceextra.append({'file':str(path.relative_to(WT)).replace('\\','/'),'sha256':sha(path),'source_commit':PARENT})
 prev=pd.read_csv(OUT/'SOURCE_HASHES.csv');save('SOURCE_HASHES.csv',pd.concat([prev,pd.DataFrame(sourceextra)]).drop_duplicates('file'))
 jdump('MEASUREMENT_LIMITATIONS_FACTS.json',{'classified_land_coverage_median_2287':float(d.land_use_classified_land_coverage.median()),'age2014_valid_area_coverage_median_2287':float(d.all_use2014_age_coverage.median()),'strict2020_age_transfer_coverage_median_2287':float(d.all_use_age_coverage.median()),'age_bound_width_median_2287':float((d.age_upper_bound-d.age_lower_bound).median()),'impervious_source_status_counts':master.impervious_source_status.value_counts(dropna=False).to_dict(),'legacy_sample_n':int(d.legacy2276_complete_case.sum()),'newly_admitted_geometry_rows':d.index[~d.legacy2276_complete_case].tolist(),'primary_sources_not_redownloaded':True})
def summaries():
 r=pd.read_csv(OUT/'BUILT_ENV_ABLATION_RESULTS.csv');s=pd.read_csv(OUT/'BUILT_ENV_SPATIAL_SENSITIVITY.csv');m=pd.read_csv(OUT/'SMALL_34_GROUP_SENSITIVITY.csv');w=pd.read_csv(OUT/'WITHIN_MODEL_SEED_AGREEMENT.csv')
 ref42=np.load(BASE/'run_records/D__equal_five_domains.npz')['s42_k4']
 frozen_counts={}
 for model,g in r.groupby('model',sort=False):
  z=np.load(OUT/'run_records'/f'{model}.npz')
  for seed in SEEDS:
   _,aligned,_=mapping(ref42,z[f'full_s{seed}'],np.ones(len(ref42),bool));frozen_counts[(model,seed)]=int((ref42!=aligned).sum())
 r['aligned_reassigned_vs_frozen_BE0_seed42_n']=[frozen_counts[(a,b)] for a,b in zip(r.model,r.seed)]
 r['reassignment_reference']='same-model seed counterpart in BE0; separate frozen-seed42 count also provided'
 save('BUILT_ENV_ABLATION_RESULTS.csv',r)
 rows=[]
 for name,g in r.groupby('model',sort=False):
  sp=s.loc[s.model.eq(name)];sf=m.loc[m.model.eq(name)&m.scope.eq('full')];ss=m.loc[m.model.eq(name)&m.scope.eq('spatial')];se=w.loc[w.model.eq(name)]
  rows.append({'model':name,'family':g.family.iloc[0],'weight_mode':g.physical_weight_mode.iloc[0],'budget':g.budget.iloc[0],'physical_budget':g.physical_domain_budget.iloc[0],'n_seeds':len(g),'ARI_BE0_median':g.ARI_vs_frozen_BE0_seed42.median(),'ARI_BE0_min':g.ARI_vs_frozen_BE0_seed42.min(),'ARI_BE0_same_seed_median':g.ARI_vs_BE0_same_seed.median(),'reassigned_median':g.aligned_reassigned_n.median(),'reassigned_frozen_seed42_median':g.aligned_reassigned_vs_frozen_BE0_seed42_n.median(),'reassigned_min':g.aligned_reassigned_n.min(),'reassigned_max':g.aligned_reassigned_n.max(),'spatial_ARI_median':sp.ARI_all.median(),'spatial_ARI_p05':sp.ARI_all.quantile(.05),'spatial_ARI_min':sp.ARI_all.min(),'seed_pair_ARI_median':se.ARI.median(),'seed_pair_ARI_min':se.ARI.min(),'min_cluster_size_min':g.minimum_cluster_size.min(),'D34_full_retention_min':sf.retention.min(),'D34_full_purity_min':sf.purity.min(),'D34_spatial_retention_min':ss.retention.min(),'D34_spatial_purity_min':ss.purity.min(),'D34_spatial_prediction_max':ss.predicted_n.max(),'silhouette_median':g.silhouette.median()})
 save('CONTROLLED_MODEL_SUMMARY.csv',rows)
 # Paired cases describe specification effects, not independent stochastic/geographic samples.
 pairs=[]
 for name in r.model.unique():
  if name=='BE0':continue
  for metric,frame,col in [('reference_reassignment',r,'aligned_reassigned_n'),('spatial_ARI',s,'ARI_all')]:
   a=frame.loc[frame.model.eq(name)].set_index('seed')[col];b=frame.loc[frame.model.eq('BE0')].set_index('seed')[col];v=a-b
   pairs.append({'model':name,'reference':'BE0, same prescribed seed/deletion case','measure':metric,'n_prescribed_cases':len(v),'mean_change':v.mean(),'median_change':v.median(),'p05_change':v.quantile(.05),'p95_change':v.quantile(.95),'minimum_change':v.min(),'maximum_change':v.max(),'interval_definition':'empirical spread of 20 fixed cases, not CI; only 17 distinct spatial deletion sets'})
 save('PAIRED_CASE_SPECIFICATION_EFFECTS.csv',pairs)
 profiles=pd.read_csv(OUT/'CLASS_PROFILE_CHANGES.csv');p=profiles.loc[profiles.scope.eq('spatial_vs_own_baseline')];rev=[]
 for model,g in p.groupby('model',sort=False):
  for a,b in itertools.combinations(range(1,5),2):
   for col in DESCRIPTORS:
    ga=g.loc[(g.model_seed42_display_class==a)&(g.feature==col)].set_index('seed');gb=g.loc[(g.model_seed42_display_class==b)&(g.feature==col)].set_index('seed');ix=ga.index.intersection(gb.index)
    if len(ix)!=20:continue
    before=ga.loc[ix,'baseline_mean']-gb.loc[ix,'baseline_mean'];after=ga.loc[ix,'mean']-gb.loc[ix,'mean']
    rev.append({'model':model,'model_seed42_class_a':a,'model_seed42_class_b':b,'feature':col,'n_cases':len(ix),'reversal_n':int((np.sign(before)!=np.sign(after)).sum()),'baseline_raw_difference_median':before.median(),'predicted_raw_difference_median':after.median(),'baseline_raw_difference_min':before.min(),'baseline_raw_difference_max':before.max()})
 save('SPATIAL_PROFILE_DIRECTION_REVERSALS.csv',rev)
 for split,fields in [('RISK_EXPOSURE',r.family.isin(['reference','risk_exposure','weights'])),('BUILDING_AGE',r.family.isin(['reference','age','age_missingness'])),('SCAG_EQUAL_DOMAIN',r.family.isin(['reference','land_coverage']))]:save(split+'_CONTROLLED_COMPARISON.csv',r.loc[fields])
 # Coverage-associated reassignments: coverage bands predetermined, never used to choose models.
 z=pd.read_csv(OUT/'SEED42_TRACT_REASSIGNMENTS.csv',dtype={'tract_id':str});cov=[]
 for name,g in z.groupby('model',sort=False):
  for label,mask in [('SCAG_below70',g.SCAG_coverage<.7),('SCAG_70to85',g.SCAG_coverage.between(.7,.85,inclusive='left')),('SCAG_85plus',g.SCAG_coverage>=.85),('age_below90',g.age_coverage<.9),('age_90plus',g.age_coverage>=.9)]:
   sub=g.loc[mask];cov.append({'model':name,'coverage_stratum':label,'n':len(sub),'reassigned_n':sub.changed.sum(),'reassigned_fraction':sub.changed.mean()})
 save('COVERAGE_STRATIFIED_REASSIGNMENT.csv',cov)
 print(pd.DataFrame(rows)[['model','ARI_BE0_median','reassigned_median','spatial_ARI_median','spatial_ARI_min','D34_spatial_purity_min']].to_string(index=False),flush=True)
def controlled_contrasts():
 _,d,_,_=inputs();sp=specs();archives={s['name']:np.load(OUT/'run_records'/f"{s['name']}.npz") for s in sp};rows=[];prof=[];weights=[];redis=[]
 for s in sp:
  ref='BE0' if s['budget']=='equal' else 'D_INHERITED';rz=archives[ref];z=archives[s['name']]
  ref42=rz['full_s42']
  for seed in SEEDS:
   y,p=rz[f'full_s{seed}'],z[f'full_s{seed}'];mp,aligned,tab=mapping(y,p,np.ones(len(d),bool));dm,_,_=mapping(ref42,y,np.ones(len(d),bool));display={raw:di for di,raw in dm.items()}
   spatial=archives[s['name']][f'spatial_s{seed}'];spref=archives[ref][f'spatial_s{seed}'];own_full=archives[s['name']][f'full_s{seed}']
   rows.append({'model':s['name'],'reference_model':ref,'seed':seed,'budget':s['budget'],'ARI_vs_same_weight_reference':adjusted_rand_score(y,p),'aligned_reassigned_n':int((aligned!=y).sum()),'aligned_reassigned_fraction':float((aligned!=y).mean()),'spatial_ARI_difference_vs_same_weight_reference':adjusted_rand_score(own_full,spatial)-adjusted_rand_score(y,spref),'definition':'OFAT feature/coordinate-content effect within declared weight scheme; redistribution mode separately identified'})
   if s['budget']=='inherited':
    for i,j in mp.items():
     for col in DESCRIPTORS:prof.append({'model':s['name'],'reference_model':ref,'seed':seed,'reference_raw_class':i+1,'reference_display_seed42_class':display.get(i,-1)+1,'feature':col,'reference_mean':d.loc[y==i,col].mean(),'model_mean':d.loc[p==j,col].mean(),'mean_change':d.loc[p==j,col].mean()-d.loc[y==i,col].mean()})
 for a,b in [('BE0','D_INHERITED'),('EAL_EQUAL','EAL_INHERITED'),('ALR_ONLY_EQUAL','ALR_ONLY_INHERITED'),('BE1_EQUAL','BE1_INHERITED'),('BE7_ACS_EQUAL','BE7_ACS_INHERITED'),('BE8_LOWER_EQUAL','BE8_LOWER_INHERITED'),('BE8_UPPER_EQUAL','BE8_UPPER_INHERITED'),('SCAG_TRANSPORT_EQUAL','SCAG_TRANSPORT_INHERITED'),('SCAG_DOMINANT_EQUAL','SCAG_DOMINANT_INHERITED')]:
  for seed in SEEDS:
   y,p=archives[a][f'full_s{seed}'],archives[b][f'full_s{seed}'];mp,aligned,tab=mapping(y,p,np.ones(len(d),bool));weights.append({'equal_domain_model':a,'inherited_domain_model':b,'seed':seed,'ARI':adjusted_rand_score(y,p),'aligned_reassigned_n':int((aligned!=y).sum()),'definition':'same feature content, k, cohort and seed; only parent-domain budgets differ'})
 for i in range(1,7):
  a,b=f'BE{i}_EQUAL',f'BE{i}_FIXED_COORD'
  for seed in SEEDS:
   y,p=archives[a][f'full_s{seed}'],archives[b][f'full_s{seed}'];mp,aligned,tab=mapping(y,p,np.ones(len(d),bool));redis.append({'redistributed_model':a,'fixed_coordinate_model':b,'seed':seed,'ARI':adjusted_rand_score(y,p),'aligned_reassigned_n':int((aligned!=y).sum()),'definition':'same retained physical coordinates; only survivors weighting differs, nonphysical coordinates unchanged'})
 save('WITHIN_WEIGHT_SPECIFICATION_EFFECTS.csv',rows);save('WITHIN_WEIGHT_PROFILE_CHANGES.csv',prof);save('WEIGHT_SCHEME_EFFECTS.csv',weights);save('PHYSICAL_REDISTRIBUTION_EFFECTS.csv',redis)
 profile=pd.read_csv(OUT/'CLASS_PROFILE_CHANGES.csv');rr=np.load(BASE/'run_records/D__equal_five_domains.npz');maps={}
 for seed in SEEDS:
  mp,_,_=mapping(rr['s42_k4'],rr[f's{seed}_k4'],np.ones(len(d),bool));maps[seed]={b+1:a+1 for a,b in mp.items()}
 profile['reference_display_seed42_class']=[maps[int(seed)][int(cid)] if scope=='feature_change_vs_BE0' else disp for seed,cid,scope,disp in zip(profile.seed,profile.reference_class,profile.scope,profile.model_seed42_display_class)]
 save('CLASS_PROFILE_CHANGES.csv',profile)
if __name__=='__main__':measurement_qa();summaries();controlled_contrasts()
