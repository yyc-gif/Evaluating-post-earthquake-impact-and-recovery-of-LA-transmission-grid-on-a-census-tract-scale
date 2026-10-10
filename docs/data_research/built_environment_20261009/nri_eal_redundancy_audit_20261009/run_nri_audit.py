"""Read-only FEMA v1.19 redundancy and controlled typology sensitivity."""
from pathlib import Path
import os,json,hashlib,itertools,subprocess,time,sys,platform
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
import numpy as np
import pandas as pd
from scipy.stats import pearsonr,spearmanr,rankdata,skew
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score,silhouette_score,pairwise_distances
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
STAGE=ROOT/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized'
LOCAL=ROOT/'docs/data_research/built_environment_20261009/local_joint_feature_extraction_20261009'
BASE='031d2c675f8e7d58035d27448be040b809ced086'
FEMA_FIELDS=['RISK_SCORE','RISK_VALUE','EAL_SCORE','EAL_VALT','EAL_VALB','EAL_VALP','EAL_VALPE','EAL_VALA','SOVI_SCORE','RESL_SCORE','RESL_VALUE','BUILDVALUE','POPULATION','AGRIVALUE','CRF_VALUE','ALR_VALB','ALR_VALP','ALR_VALA','ALR_NPCTL','ALR_VRA_NPCTL']
COMMON=['T80','Init_Supply','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','Pre_1970_Ratio','Pop_Density']
SETS={'A':['NRI_BUILDVALUE','NRI_RISK_SCORE'],'B':['EAL_SCORE'],'C':['NRI_BUILDVALUE','EAL_SCORE'],'D':['NRI_BUILDVALUE','ALR_NPCTL'],'B_value':['EAL_VALT'],'C_value':['NRI_BUILDVALUE','EAL_VALT']}
DOMAIN={'recovery':['T80','Init_Supply'],'grid':['Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI'],'built':['Pre_1970_Ratio','Pop_Density'],'social':['SOVI_SCORE']}
BUDGETS={'original_domain_totals':{'recovery':2/11,'grid':4/11,'built':2/11,'social':1/11,'loss_exposure':2/11},'equal_domains':{k:.2 for k in ['recovery','grid','built','social','loss_exposure']}}
SEEDS=[42,43,44,45,46]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(n,x):(OUT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def csv(n,d):d.to_csv(OUT/n,index=False,float_format='%.15g')
def git(*a):return subprocess.check_output(['git','-C',str(ROOT),*a])
def ids_hash(ids):return hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()
def correlation(x,y):
 if len(x)<3 or np.ptp(x)<=1e-12 or np.ptp(y)<=1e-12:return np.nan,np.nan,'UNDEFINED_CONSTANT_OR_INSUFFICIENT'
 return float(pearsonr(x,y).statistic),float(spearmanr(x,y).statistic),'ESTIMATED'
def load_data():
 paths=[ROOT/'Data/NRI_Table_CensusTracts_California.csv',STAGE/'clusters_labels_final.csv',ROOT/'src/la_grid/core/C257H_Project_Main.py',LOCAL/'TRACT_FEATURE_CANDIDATES.csv',LOCAL/'FEATURE_COVERAGE_QA.csv',LOCAL/'FEATURE_ASSEMBLY_QA.json']
 dump('SOURCE_HASHES.json',{p.relative_to(ROOT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths})
 saved=pd.read_csv(paths[1],dtype={'tract_id':str});saved.tract_id=saved.tract_id.str.zfill(11);assert len(saved)==2291 and saved.tract_id.is_unique
 nri=pd.read_csv(paths[0],dtype={'TRACTFIPS':str},low_memory=False);assert nri.NRI_VER.eq('Mar-23').all() and nri.TRACTFIPS.is_unique and nri.TRACTFIPS.str.len().eq(11).all()
 raw=nri.set_index('TRACTFIPS').reindex(saved.tract_id);assert raw.NRI_VER.notna().all();raw.index.name='tract_id'
 d=saved.set_index('tract_id').copy();qa=[]
 for source,dest in [('RISK_SCORE','NRI_RISK_SCORE'),('BUILDVALUE','NRI_BUILDVALUE'),('SOVI_SCORE','SOVI_SCORE')]:
  error=float((raw[source]-d[dest]).abs().max());assert np.allclose(raw[source],d[dest],atol=1e-7,rtol=1e-12)
  qa.append({'source':source,'saved':dest,'n':2291,'max_abs_error':error})
 for c in FEMA_FIELDS:
  if c not in d:d[c]=pd.to_numeric(raw[c],errors='coerce')
 for c in [x for x in raw if x.endswith(('_RATNG','_SPCTL','_EALT','_EALB','_EALPE','_EALA'))]:d[c]=raw[c]
 candidate=pd.read_csv(paths[3],dtype={'tract_id':str}).set_index('tract_id');assert len(candidate)==2315 and (candidate.index.str.len()==11).all()
 fields=pd.read_csv(paths[4]).feature.tolist()
 extras={c:candidate.reindex(d.index)[c] for c in fields if c not in d}
 d=pd.concat([d,pd.DataFrame(extras,index=d.index)],axis=1)
 identities={c:float((d[c]-saved.set_index('tract_id')[c]).abs().max()) for c in COMMON+['SOVI_SCORE','NRI_BUILDVALUE','NRI_RISK_SCORE']};assert all(v==0 for v in identities.values())
 hazards=[c for c in raw if c.endswith('_EALT')];assert len(hazards)==18
 comparisons={'component_total':(raw.EAL_VALT-raw.EAL_VALB-raw.EAL_VALPE-raw.EAL_VALA).abs(),'VSL_11_6_million':(raw.EAL_VALPE-raw.EAL_VALP*11600000).abs(),'risk_times_CRF':(raw.RISK_VALUE-raw.EAL_VALT*raw.CRF_VALUE).abs(),'building_loss_rate':(raw.ALR_VALB-raw.EAL_VALB/raw.BUILDVALUE).abs(),'population_loss_rate':(raw.ALR_VALP-raw.EAL_VALP/raw.POPULATION).abs(),'agriculture_loss_rate':(raw.ALR_VALA-raw.EAL_VALA/raw.AGRIVALUE.replace(0,np.nan)).abs(),'18_hazard_total':(raw.EAL_VALT-raw[hazards].sum(axis=1,min_count=1)).abs()}
 formula=[]
 for k,e in comparisons.items():formula.append({'identity':k,'n_comparable':int(e.notna().sum()),'max_abs_error':float(e.max()),'pass_rounding_tolerance':bool(e.max()<1e-5)})
 assert all(x['pass_rounding_tolerance'] for x in formula)
 csv('SAVED_STAGE7_SOURCE_REPRODUCTION.csv',pd.DataFrame(qa));csv('EAL_NUMERICAL_COMPOSITION_QA.csv',pd.DataFrame(formula))
 applicability=[];keep=[]
 for value in hazards:
  prefix=value.removesuffix('_EALT');rating=prefix+'_EALR';keep.extend([value,rating]);counts=raw[rating].fillna('NULL_RATING').value_counts().to_dict()
  applicability.append({'hazard':prefix,'source_value_field':value,'source_rating_field':rating,'value_valid_n':int(raw[value].notna().sum()),'value_null_n':int(raw[value].isna().sum()),'value_zero_n':int(raw[value].eq(0).sum()),'rating_counts_json':json.dumps(counts,sort_keys=True),'nulls_replaced_with_zero':False})
 csv('HAZARD_APPLICABILITY_AUDIT.csv',pd.DataFrame(applicability));csv('FEMA_HAZARD_APPLICABILITY_AND_VALUES.csv',raw[keep].reset_index())
 dump('INPUT_IDENTITY_QA.json',{'nri_release':'Mar-23','fema_rows':len(nri),'residential_rows':2291,'matched_nri_rows':2291,'unmatched_tracts':[],'duplicate_ids':0,'residential_tract_set_sha256':ids_hash(d.index),'frozen_common_input_max_errors':identities,'all_hazard_fields':hazards,'cluster_labels_used_only_for_diagnostic_ARI':True,'recovery_input':'T80','recovery_selection_unresolved':True})
 csv('MATCHED_FEMA_STAGE7_FEATURES.csv',d.reset_index())
 return d,fields

def statistics(d,physical):
 core=list(dict.fromkeys(FEMA_FIELDS+['NRI_BUILDVALUE','NRI_RISK_SCORE','Pop_Density','Pre_1970_Ratio']+physical))
 money=['EAL_VALT','EAL_VALB','EAL_VALPE','EAL_VALA','RISK_VALUE','NRI_BUILDVALUE','BUILDVALUE','AGRIVALUE']
 transforms=money+['Pop_Density','building_count_density','housing_units_per_km2','building_height_area_weighted_m']
 qa=[]
 for c in core:
  a=pd.to_numeric(d[c],errors='coerce');valid=a.dropna();qa.append({'field':c,'n':len(a),'valid_n':len(valid),'missing':int(a.isna().sum()),'zero_n':int(a.eq(0).sum()),'negative_n':int(a.lt(0).sum()),'minimum':valid.min(),'p01':valid.quantile(.01),'median':valid.median(),'p99':valid.quantile(.99),'maximum':valid.max(),'skewness':skew(valid,bias=False) if valid.nunique()>1 else np.nan,'units_transform': 'published scale'})
  if c in transforms:
   d=d.copy();d['log1p_'+c]=np.log1p(a.where(a>=0));qa.append({'field':'log1p_'+c,'n':len(a),'valid_n':int(d['log1p_'+c].notna().sum()),'missing':int(d['log1p_'+c].isna().sum()),'zero_n':int(d['log1p_'+c].eq(0).sum()),'negative_n':0,'minimum':d['log1p_'+c].min(),'p01':d['log1p_'+c].quantile(.01),'median':d['log1p_'+c].median(),'p99':d['log1p_'+c].quantile(.99),'maximum':d['log1p_'+c].max(),'skewness':skew(d['log1p_'+c].dropna(),bias=False) if d['log1p_'+c].nunique()>1 else np.nan,'units_transform':'natural log(1 + nonnegative published value); zero retained; negative/missing null'})
 csv('FIELD_COVERAGE_AND_DISTRIBUTION.csv',pd.DataFrame(qa))
 targets=['SOVI_SCORE','EAL_SCORE','EAL_VALT','log1p_EAL_VALT','NRI_RISK_SCORE','NRI_BUILDVALUE','log1p_NRI_BUILDVALUE','ALR_NPCTL','ALR_VRA_NPCTL','EAL_VALB','EAL_VALPE','EAL_VALA','log1p_EAL_VALB','log1p_EAL_VALPE','log1p_EAL_VALA']
 features=list(dict.fromkeys(core+['log1p_'+c for c in transforms]))
 pairs=sorted(set(tuple(sorted((a,b))) for a in targets for b in features if a!=b))
 rows=[]
 for a,b in pairs:
  sub=d[[a,b]].dropna();r,rho,status=correlation(sub[a].to_numpy(),sub[b].to_numpy());rows.append({'field_a':a,'field_b':b,'n':len(sub),'missing_from_2291':2291-len(sub),'pearson_r':r,'spearman_rho':rho,'status':status,'matched_tract_sha256':ids_hash(sub.index),'sample':'exact saved residential membership; pairwise complete cases','note':'partial 2020-age coverage or numeric impervious pilot retains its source limitations' if any(w in a+b for w in ['all_use_pre1970','impervious']) else ''})
 csv('NRI_EAL_SOVI_BUILDVALUE_CORRELATIONS.csv',pd.DataFrame(rows))
 # Paired resampling quantifies difference in overlap with the mandatory social score.
 rng=np.random.default_rng(20261009);x=d.SOVI_SCORE.to_numpy();a=d.NRI_RISK_SCORE.to_numpy();b=d.EAL_SCORE.to_numpy();boot=[]
 for _ in range(2000):
  idx=rng.integers(0,len(d),len(d));r1,s1,_=correlation(x[idx],a[idx]);r2,s2,_=correlation(x[idx],b[idx]);boot.append([r2-r1,abs(r2)-abs(r1),s2-s1,abs(s2)-abs(s1)])
 out=[]
 r1,s1,_=correlation(x,a);r2,s2,_=correlation(x,b)
 for i,name,value in [(0,'Pearson EAL minus RISK',r2-r1),(1,'Pearson absolute-overlap difference',abs(r2)-abs(r1)),(2,'Spearman EAL minus RISK',s2-s1),(3,'Spearman absolute-overlap difference',abs(s2)-abs(s1))]:
  ci=np.quantile(np.array(boot)[:,i],[.025,.975]);out.append({'comparison':name,'estimate':value,'ci_low':ci[0],'ci_high':ci[1],'resamples':2000,'definition':'descriptive IID-tract paired percentile bootstrap; not spatially adjusted; same tract resampled across measures'})
 csv('SOCIAL_OVERLAP_PAIRED_BOOTSTRAP.csv',pd.DataFrame(out))
 comp=d[['EAL_VALT','EAL_VALB','EAL_VALP','EAL_VALPE','EAL_VALA','BUILDVALUE','POPULATION','AGRIVALUE','ALR_VALB','ALR_VALP','ALR_VALA','ALR_NPCTL','ALR_VRA_NPCTL']].copy()
 for k,label in [('EAL_VALB','building'),('EAL_VALPE','population_equivalent'),('EAL_VALA','agriculture')]:comp[label+'_loss_share']=comp[k]/comp.EAL_VALT
 hazards=[c for c in d if c.endswith('_EALT')]
 for c in hazards:comp[c]=d[c];comp[c+'_share']=d[c]/d.EAL_VALT
 csv('EAL_BUILDING_POPULATION_AGRICULTURE_COMPONENTS.csv',comp.reset_index())
 cr=[]
 for c in ['building_loss_share','population_equivalent_loss_share','agriculture_loss_share']+[h+'_share' for h in hazards]:
  cr.append({'component':c,'valid_n':int(comp[c].notna().sum()),'zero_n':int(comp[c].eq(0).sum()),'tract_mean_share':comp[c].mean(),'tract_median_share':comp[c].median(),'p10_share':comp[c].quantile(.1),'p90_share':comp[c].quantile(.9),'pooled_loss_share':float(comp[c].mul(comp.EAL_VALT).sum(min_count=1)/comp.EAL_VALT.sum()),'note':'hazard N/A remains null; sum of present hazard values reconciles composite; not a single-event hazard measure'})
 csv('EAL_COMPONENT_AND_HAZARD_SUMMARY.csv',pd.DataFrame(cr))
 return d

def residual(v,c):
 design=np.column_stack([np.ones(len(v)),c]);return v-design@np.linalg.lstsq(design,v,rcond=None)[0]
def design(d,set_name,transform):
 cols=COMMON+['SOVI_SCORE']+SETS[set_name];f=d[cols].copy()
 if transform=='log_exposures':
  for c in ['NRI_BUILDVALUE','Pop_Density','EAL_VALT']:
   if c in f:assert f[c].ge(0).all();f[c]=np.log1p(f[c])
 return f

def redundancy(d):
 rows=[];models=[]
 for name in SETS:
  for transform in ['raw','log_exposures']:
   f=design(d,name,transform)
   for scope,cols in [('nri_coordinates',['SOVI_SCORE']+SETS[name]),('complete_stage7',f.columns.tolist())]:
    z=StandardScaler().fit_transform(f[cols]);sv=np.linalg.svd(z,compute_uv=False);condition=float(sv[0]/sv[-1]);rank=int(np.linalg.matrix_rank(z))
    vifs=[]
    for i,c in enumerate(cols):
     err=residual(z[:,i],np.delete(z,i,axis=1));r2=1-np.sum(err**2)/np.sum(z[:,i]**2);vif=1/max(1-r2,1e-15);vifs.append(vif)
     rows.append({'analysis':'VIF','feature_set':name,'transform':transform,'scope':scope,'feature_a':c,'feature_b':'all simultaneous other coordinates','controls':' | '.join(x for x in cols if x!=c),'n':len(f),'pearson_partial':np.nan,'spearman_partial':np.nan,'r2':r2,'incremental_r2':np.nan,'value':vif,'condition_number_standardized':condition,'design_rank':rank,'matched_tract_sha256':ids_hash(f.index),'interpretation':'collinearity; not causality'})
    models.append({'feature_set':name,'transform':transform,'scope':scope,'coordinates':' | '.join(cols),'n':len(f),'coordinate_count':len(cols),'condition_number_standardized':condition,'max_vif':max(vifs),'min_vif':min(vifs),'missing_records':0,'recovery_input':'T80 unchanged','economic_coordinate':'multi-hazard expected loss integrates exposed stock and population-equivalent loss' if name.startswith('B') else 'building stock explicitly retained','mechanical_social_overlap':'yes via RISK CRF' if name=='A' else 'no CRF in EAL or unadjusted ALR; statistical socioeconomic association remains','status':'exploratory only; built-environment/recovery choices unresolved'})
 controls=['SOVI_SCORE','log1p_NRI_BUILDVALUE','log1p_Pop_Density']
 targets=['EAL_SCORE','EAL_VALT','log1p_EAL_VALT','ALR_NPCTL','ALR_VRA_NPCTL','NRI_RISK_SCORE']
 for target in targets:
  sub=d[[target]+controls].dropna();z=StandardScaler().fit_transform(sub);err=residual(z[:,0],z[:,1:]);r2=1-(err@err)/(z[:,0]@z[:,0]);rows.append({'analysis':'EXPLAINED_FRACTION','feature_set':'conditional','transform':'published score / named log values','scope':'cross-domain','feature_a':target,'feature_b':'controls jointly','controls':' | '.join(controls),'n':len(sub),'r2':r2,'value':r2,'incremental_r2':np.nan,'matched_tract_sha256':ids_hash(sub.index),'interpretation':'descriptive linear explained fraction; not causal share'})
  for control in controls:
   others=[c for c in controls if c!=control];rz=residual(z[:,0],z[:,[sub.columns.get_loc(c) for c in others]]);xres=residual(z[:,sub.columns.get_loc(control)],z[:,[sub.columns.get_loc(c) for c in others]]);p,_s,_=correlation(rz,xres)
   ranked=sub.apply(lambda v:rankdata(v)).to_numpy();rr=residual(ranked[:,0],ranked[:,[sub.columns.get_loc(c) for c in others]]);xr=residual(ranked[:,sub.columns.get_loc(control)],ranked[:,[sub.columns.get_loc(c) for c in others]]);rankpartial=pearsonr(rr,xr).statistic
   reduced=residual(z[:,0],z[:,[sub.columns.get_loc(c) for c in others]]);increment=(reduced@reduced-err@err)/(z[:,0]@z[:,0])
   rows.append({'analysis':'PARTIAL_CORRELATION','feature_set':'conditional','transform':'published score / named log values','scope':'cross-domain','feature_a':target,'feature_b':control,'controls':' | '.join(others),'n':len(sub),'pearson_partial':p,'spearman_partial':rankpartial,'r2':np.nan,'value':np.nan,'incremental_r2':increment,'matched_tract_sha256':ids_hash(sub.index),'interpretation':'rank-residual Pearson for partial Spearman; conditional association, not causality'})
 # Information lost by removing a stock coordinate, even when loss has lower overlap with social vulnerability.
 for target in ['NRI_BUILDVALUE','log1p_NRI_BUILDVALUE']:
  for predictors in [['EAL_SCORE'],['log1p_EAL_VALT'],['EAL_SCORE','SOVI_SCORE','log1p_Pop_Density'],['ALR_NPCTL','SOVI_SCORE','log1p_Pop_Density']]:
   sub=d[[target]+predictors].dropna();z=StandardScaler().fit_transform(sub);err=residual(z[:,0],z[:,1:]);r2=1-(err@err)/(z[:,0]@z[:,0]);rows.append({'analysis':'STOCK_INFORMATION_RECONSTRUCTION','feature_set':'conditional','scope':'cross-domain','feature_a':target,'feature_b':'joint predictors','controls':' | '.join(predictors),'n':len(sub),'r2':r2,'value':r2,'incremental_r2':np.nan,'matched_tract_sha256':ids_hash(sub.index),'interpretation':'in-sample linear stock information retained; no out-of-sample accuracy claim'})
 for target in ['EAL_SCORE','ALR_NPCTL','log1p_EAL_VALT']:
  for other in ['NRI_RISK_SCORE','Pre_1970_Ratio','building_footprint_coverage','building_count_density','all_use2014_pre1970_area_share','land_use_entropy']:
   sub=d[[target,other]+controls].dropna();values=sub.to_numpy();rx=residual(values[:,0],values[:,2:]);ry=residual(values[:,1],values[:,2:]);p,_s,status=correlation(rx,ry);ranks=sub.apply(lambda v:rankdata(v)).to_numpy();rr=residual(ranks[:,0],ranks[:,2:]);rs=residual(ranks[:,1],ranks[:,2:]);rp=pearsonr(rr,rs).statistic if np.ptp(rr)>1e-12 and np.ptp(rs)>1e-12 else np.nan
   rows.append({'analysis':'PARTIAL_CROSS_DOMAIN','feature_set':'conditional','transform':'published score / named log values','scope':'cross-domain','feature_a':target,'feature_b':other,'controls':' | '.join(controls),'n':len(sub),'pearson_partial':p,'spearman_partial':rp,'r2':np.nan,'value':np.nan,'incremental_r2':np.nan,'matched_tract_sha256':ids_hash(sub.index),'interpretation':'controls are held on identical complete-case tract set; association, not causality'})
 csv('PARTIAL_CORRELATIONS_AND_VIF.csv',pd.DataFrame(rows));csv('FOUR_FEATURE_SET_COMPARISON.csv',pd.DataFrame(models))
 return pd.DataFrame(rows)

def elbow(inertias):
 ks=np.arange(1,len(inertias)+1);p1=np.array([ks[0],inertias[0]]);p2=np.array([ks[-1],inertias[-1]]);u=p2-p1
 points=np.column_stack([ks,inertias]);v=p1-points;dist=np.abs(u[0]*v[:,1]-u[1]*v[:,0])/np.linalg.norm(u)
 return int(ks[np.argmax(dist)])

def clustering(d):
 rows=[];krows=[];domainrows=[];weights=[];stability=[];store={};labelout=pd.DataFrame({'tract_id':d.index});base_labels=d.cluster.to_numpy()
 for budget_name,budget in BUDGETS.items():
  for transform in ['raw','log_exposures']:
   for name in SETS:
    start=time.perf_counter();cpu_start=time.process_time();f=design(d,name,transform);cols=f.columns.tolist();domains=dict(DOMAIN,loss_exposure=SETS[name]);z=StandardScaler().fit_transform(f);matrix=z.copy()
    for domain,features in domains.items():
     factor=np.sqrt(budget[domain]/len(features));indices=[cols.index(c) for c in features];matrix[:,indices]*=factor
     for c in features:weights.append({'feature_set':name,'transform':transform,'budget':budget_name,'domain':domain,'feature':c,'domain_weight':budget[domain],'coordinate_squared_weight':budget[domain]/len(features),'domain_coordinate_count':len(features),'n':len(d),'observed_coordinate_variance':float(np.var(matrix[:,cols.index(c)]))})
    assert np.allclose(np.sum(np.var(matrix,axis=0)),1,atol=1e-12)
    distances=pairwise_distances(matrix,metric='euclidean');np.fill_diagonal(distances,0)
    sweep={};inertias=[]
    for k in range(1,11):
     model=KMeans(n_clusters=k,random_state=42,n_init=10,max_iter=300,tol=1e-4,algorithm='lloyd');labs=model.fit_predict(matrix);sweep[k]=(model,labs);inertias.append(float(model.inertia_))
     krows.append({'feature_set':name,'transform':transform,'budget':budget_name,'seed':42,'k':k,'inertia':model.inertia_,'silhouette':silhouette_score(distances,labs,metric='precomputed') if k>1 else np.nan,'selection_rule':'same k=1..10 maximum perpendicular-distance elbow as formal Stage7; not silhouette maximization'})
    selected=elbow(inertias);models_to_run=sorted(set([5,selected]));namekey=(budget_name,transform,name)
    for k in models_to_run:
     for seed in SEEDS:
      if seed==42:model,labs=sweep[k]
      else:
       model=KMeans(n_clusters=k,random_state=seed,n_init=10,max_iter=300,tol=1e-4,algorithm='lloyd');labs=model.fit_predict(matrix)
      reference=store.get((budget_name,transform,'A',k,seed));aris=adjusted_rand_score(labs,reference) if reference is not None else np.nan
      role='fixed_5_and_selected' if k==5==selected else 'fixed_5' if k==5 else 'selected_elbow'
      key=f'{name}__{transform}__{budget_name}__k{k}__s{seed}';labelout=labelout.copy();labelout[key]=labs+1
      rows.append({'feature_set':name,'transform':transform,'budget':budget_name,'seed':seed,'k':k,'elbow_selected_k':selected,'run_role':role,'n':len(d),'silhouette':float(silhouette_score(distances,labs,metric='precomputed')),'minimum_cluster_size':int(np.bincount(labs).min()),'maximum_cluster_size':int(np.bincount(labs).max()),'inertia':float(model.inertia_),'iterations':int(model.n_iter_),'ari_vs_original_saved_labels':adjusted_rand_score(base_labels,labs),'ari_vs_A_same_seed_k_budget_transform':aris,'matched_tract_sha256':ids_hash(d.index),'scientific_status':'exploratory; not selection or promotion'})
      # Between-cluster squared distance is an interpretable contribution in the explicitly weighted metric.
      centroid=model.cluster_centers_[labs];between=(centroid-matrix.mean(axis=0))**2;within=(matrix-centroid)**2
      for domain,features in domains.items():
       indices=[cols.index(c) for c in features];b=float(between[:,indices].sum());w=float(within[:,indices].sum());domainrows.append({'feature_set':name,'transform':transform,'budget':budget_name,'seed':seed,'k':k,'domain':domain,'prespecified_weight':budget[domain],'total_sumsquares':float((matrix[:,indices]**2).sum()),'between_sumsquares':b,'within_sumsquares':w,'between_fraction_all_domains':b/float(between.sum()),'domain_explained_fraction':b/(b+w),'interpretation':'geometric cluster contribution, not causal contribution or external validation'})
      store[(budget_name,transform,name,k,seed)]=labs
     for a,b in itertools.combinations(SEEDS,2):stability.append({'feature_set':name,'transform':transform,'budget':budget_name,'k':k,'seed_a':a,'seed_b':b,'ari':adjusted_rand_score(store[(budget_name,transform,name,k,a)],store[(budget_name,transform,name,k,b)]),'comparison':'independent-seed stability; same full tract matrix'})
    print('CLUSTER',budget_name,transform,name,'selected_k',selected,'seconds',round(time.perf_counter()-start,2),flush=True)
    krows[-1]['model_wall_seconds']=time.perf_counter()-start;krows[-1]['model_cpu_seconds']=time.process_time()-cpu_start
    csv('CONTROLLED_CLUSTERING_SENSITIVITY.csv',pd.DataFrame(rows));csv('CLUSTER_K_SELECTION_DIAGNOSTICS.csv',pd.DataFrame(krows))
 result=pd.DataFrame(rows);assert result.n.eq(2291).all()
 csv('CLUSTER_DOMAIN_WEIGHTS.csv',pd.DataFrame(weights));csv('CLUSTER_DOMAIN_CONTRIBUTIONS.csv',pd.DataFrame(domainrows));csv('CLUSTER_SEED_STABILITY.csv',pd.DataFrame(stability));csv('EXPLORATORY_CLUSTER_LABELS.csv',labelout)
 summary=result.groupby(['feature_set','transform','budget','k','run_role'],as_index=False).agg(seeds=('seed','count'),silhouette_mean=('silhouette','mean'),silhouette_sd=('silhouette','std'),minimum_cluster_size=('minimum_cluster_size','min'),ari_saved_mean=('ari_vs_original_saved_labels','mean'),ari_vs_A_mean=('ari_vs_A_same_seed_k_budget_transform','mean'))
 csv('CONTROLLED_CLUSTERING_SUMMARY.csv',summary)
 replay=result[(result.feature_set=='A')&(result['transform']=='log_exposures')&(result.budget=='original_domain_totals')&(result.seed==42)&(result.k==5)].iloc[0]
 assert replay.ari_vs_original_saved_labels>.999999,'Original benchmark could not reproduce archived labels'
 consistency=[]
 for name in SETS:
  for seed in SEEDS:
   for budget in BUDGETS:
    a=store[(budget,'raw',name,5,seed)];b=store[(budget,'log_exposures',name,5,seed)];consistency.append({'feature_set':name,'seed':seed,'comparison':'raw vs log inputs','fixed_setting':budget,'ari':adjusted_rand_score(a,b)})
   for transform in ['raw','log_exposures']:
    a=store[('original_domain_totals',transform,name,5,seed)];b=store[('equal_domains',transform,name,5,seed)];consistency.append({'feature_set':name,'seed':seed,'comparison':'original-domain totals vs equal domains','fixed_setting':transform,'ari':adjusted_rand_score(a,b)})
 csv('CONTENT_VS_WEIGHT_TRANSFORM_SENSITIVITY.csv',pd.DataFrame(consistency))
 dump('CLUSTER_RUN_SPECIFICATION.json',{'sets':SETS,'common_frozen_columns':COMMON,'mandatory_social':'SOVI_SCORE','recovery':'T80 unchanged; B selection not made here','built_environment':'formal Pre_1970_Ratio and Pop_Density unchanged; new physical-form metrics only correlated','domain_budgets':BUDGETS,'distance':'weighted squared Euclidean; standardized coordinate multiplied by sqrt(domain budget / coordinate count)','seeds':SEEDS,'n_init':10,'k_sweep':list(range(1,11)),'selection_rule':'maximum perpendicular distance to line from k1 inertia to k10 inertia; seed42','compare_k':'fixed5 and separately selected elbow k; reuse identical fit if selected5','bootstrap_for_clustering':'none','silhouette':'exact all2291 precomputed Euclidean distances','old_labels':'ARI diagnostic only; no choice uses labels','original_benchmark_ARI':float(replay.ari_vs_original_saved_labels),'sklearn_version':__import__('sklearn').__version__})
 return result

def verify_preservation():
 baseline=json.loads((OUT/'PRESERVATION_BASELINE.json').read_text(encoding='utf-8'));changed=[p for p,h in baseline['protected_files'].items() if sha(ROOT/p)!=h]
 inputs=json.loads((OUT/'SOURCE_HASHES.json').read_text(encoding='utf-8'));inputchanged=[p for p,h in inputs.items() if sha(ROOT/p)!=h['sha256']]
 formal=json.loads((LOCAL/'INPUT_SOURCE_HASHES.json').read_text(encoding='utf-8'));formalchanged=[p for p,h in formal.items() if sha(ROOT/p)!=h['sha256']]
 idx=git('ls-files','--stage','-z');assert idx==(OUT/'ORIGINAL_STAGING.bin').read_bytes() and not changed and not inputchanged and not formalchanged
 dump('PRESERVATION_FINAL_QA.json',{'head_unchanged':git('rev-parse','HEAD').decode().strip()==BASE,'protected_files_checked':len(baseline['protected_files']),'original_212_protected_unchanged':True,'protected_hash_changes':changed,'used_source_hash_changes':inputchanged,'formal_input_files_checked':len(formal),'formal_input_hash_changes':formalchanged,'original_index_unchanged':True,'original_staged_count':baseline['staged_count'],'scientific_files_changed':0,'formal_clusters_manuscript_figures_modified':False,'land_use_urban_density_building_age_sources_modified':False})

def main():
 start=time.perf_counter()
 with threadpool_limits(limits=1):
  d,physical=load_data();d=statistics(d,physical);redundancy(d);clustering(d)
 verify_preservation()
 dump('EXECUTION_RUNTIME.json',{'wall_seconds':time.perf_counter()-start,'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':__import__('scipy').__version__,'sklearn':__import__('sklearn').__version__,'threads':1})
 print('AUDIT_CALCULATIONS_COMPLETE',flush=True)
if __name__=='__main__':main()
