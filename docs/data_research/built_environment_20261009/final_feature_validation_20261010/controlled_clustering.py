"""Predeclared controlled comparisons; original Stage 7 labels are never inputs."""
import os,time,json,hashlib,itertools
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1');os.environ.setdefault('LOKY_MAX_CPU_COUNT','1')
import numpy as np,pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score,silhouette_score,pairwise_distances
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr,pearsonr
from threadpoolctl import threadpool_limits
from validate_stage7 import ROOT,OUT,read,save,dump,sha
SEEDS=list(range(42,62));KS=list(range(2,9));NINIT=100
BUDGETS={'inherited':{'recovery_service':2/11,'grid':4/11,'physical':2/11,'social':1/11,'loss_exposure':2/11},'equal_five_domains':{k:.2 for k in ['recovery_service','grid','physical','social','loss_exposure']}}
GRID=['Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI']
def variants():
 v=[]
 for budget in BUDGETS:
  for name,changes in [('D',{}),('EAL',{'loss':'EAL'}),('D_T80',{'recovery':'T80'}),('D_logB',{'recovery':'log1p_B_480_hr'}),('D_ACS_age',{'age':'residential_pre1970_housing_share'}),('D_no_age',{'age':None})]:
   s=dict(name=name+'__'+budget,budget=budget,loss='D',recovery='B_480_hr',age='all_use2014_pre1970_area_share',entropy='land_use_entropy',sample='complete');s.update(changes);v.append(s)
 # Independent OFAT measurement/sample diagnostics, not a gigantic factorial.
 for name,c in [('entropy_transport',{'entropy':'entropy_missing_to_transport'}),('entropy_dominant',{'entropy':'entropy_missing_to_dominant'}),('entropy_proportional',{'entropy':'entropy_missing_proportional'}),('age_lower_bound',{'age':'age_lower_bound'}),('age_upper_bound',{'age':'age_upper_bound'}),('pop_density',{'population':True}),('legacy2276',{'sample':'legacy'}),('lowcoverage',{'sample':'coverage_top75'})]:
  s=dict(name='D_'+name+'__inherited',budget='inherited',loss='D',recovery='B_480_hr',age='all_use2014_pre1970_area_share',entropy='land_use_entropy',sample='complete');s.update(c);v.append(s)
 return v
def spec_domains(s):
 physical=[s['entropy'],'building_footprint_coverage']+([s['age']] if s['age'] else [])
 domains={'recovery_service':[s['recovery'],'Init_Supply'],'grid':GRID,'physical':physical,'social':['SOVI_SCORE'],'loss_exposure':['log1p_NRI_BUILDVALUE','ALR_NPCTL'] if s['loss']=='D' else ['EAL_SCORE']}
 budget=dict(BUDGETS[s['budget']])
 if s.get('population'):
  # Split the original exposure budget between demographic and economic/loss domains.
  budget['demographic_exposure']=budget['loss_exposure']/2;budget['loss_exposure']/=2;domains['demographic_exposure']=['log1p_Pop_Density']
 return domains,budget
def design(frame,s):
 domains,budget=spec_domains(s);cols=[c for block in domains.values() for c in block];data=frame[cols];assert data.notna().all().all()
 scaler=StandardScaler();z=scaler.fit_transform(data);factors=[];weights=[]
 for domain,fields in domains.items():
  for c in fields:
   factor=np.sqrt(budget[domain]/len(fields));factors.append(factor);weights.append({'model':s['name'],'domain':domain,'feature':c,'domain_budget':budget[domain],'coordinate_squared_weight':factor**2,'n':len(frame)})
 return z*np.array(factors),cols,domains,scaler,np.asarray(factors),weights
def select_k(inertias):
 # Deterministic normalized maximum distance from endpoint chord, k2..8.
 y=np.asarray(inertias);y=(y-y.min())/(y.max()-y.min());x=np.linspace(0,1,len(y));distance=((1-x)-y)/np.sqrt(2);return KS[int(np.argmax(distance))]
def fit_one(matrix,k,seed,dist):
 km=KMeans(n_clusters=k,n_init=NINIT,max_iter=500,tol=1e-4,algorithm='lloyd',random_state=seed);start=time.perf_counter();labels=km.fit_predict(matrix)
 return labels,km,{'inertia':float(km.inertia_),'silhouette':float(silhouette_score(dist,labels,metric='precomputed')),'minimum_cluster_size':int(np.bincount(labels).min()),'maximum_cluster_size':int(np.bincount(labels).max()),'cluster_sizes':';'.join(str(x) for x in np.bincount(labels)),'iterations':int(km.n_iter_),'elapsed_s':time.perf_counter()-start}
def precompute(spec):
 frame=read('FINAL_CANDIDATE_FEATURE_MATRIX.csv',OUT);sub=frame.loc[frame.primary_complete_case].copy()
 if spec['sample']=='legacy':sub=sub.loc[sub.legacy2276_complete_case]
 if spec['sample']=='coverage_top75':sub=sub.loc[sub.land_use_classified_land_coverage.ge(sub.land_use_classified_land_coverage.quantile(.25))]
 matrix,cols,domains,scaler,factors,weights=design(sub,spec);mh=hashlib.sha256(np.ascontiguousarray(matrix).tobytes()).hexdigest();samplehash=hashlib.sha256('\n'.join(sub.index).encode()).hexdigest();cp=OUT/'run_records'/(spec['name']+'.npz');meta=cp.with_suffix('.json')
 if cp.exists() and meta.exists():
  m=json.loads(meta.read_text());assert m['matrix_sha256']==mh and m['n_init']==NINIT;return spec['name']+' REUSED_COMPLETE_CHECKPOINT'
 rows=[];labs={};start=time.time()
 with threadpool_limits(limits=1):
  dist=pairwise_distances(matrix,metric='euclidean')
  for seed in SEEDS:
   rr=[]
   for k in KS:
    labels,km,metrics=fit_one(matrix,k,seed,dist);labs[(seed,k)]=labels
    rr.append({'model':spec['name'],'seed':seed,'k':k,'n':len(sub),'n_init':NINIT,'sample_sha256':samplehash,'matrix_sha256':mh,**metrics})
   selected=select_k([r['inertia'] for r in rr])
   for row in rr:row['selected_k']=selected;row['selected_run']=row['k']==selected;row['fixed_k5']=row['k']==5
   rows+=rr
 np.savez_compressed(cp,**{f's{s}_k{k}':l for (s,k),l in labs.items()});meta.write_text(json.dumps({'matrix_sha256':mh,'n_init':NINIT,'rows':rows}),encoding='utf-8')
 return spec['name']+' COMPLETE '+str(round(time.time()-start,1))+'s'
def run():
 frame=read('FINAL_CANDIDATE_FEATURE_MATRIX.csv',OUT);d=frame.loc[frame.primary_complete_case].copy();specs=variants();checkpoint=OUT/'run_records';checkpoint.mkdir(exist_ok=True)
 dump('CONTROLLED_EXPERIMENT_SPECIFICATION.json',{'status':'EXPLORATORY_NOT_FORMAL_REPLACEMENT','planned_models':specs,'seeds':SEEDS,'n_init':NINIT,'k_sweep':KS,'k_selection':'per-seed maximum distance below normalized k2..k8 inertia endpoint chord; silhouette is reported, never selection criterion','budget_definitions':BUDGETS,'distance':'z score within cohort then sqrt(domain budget/number of coordinates) weighting, squared Euclidean','physical_budget':'Three distinct physical subconstructs share fixed physical budget; equal five parent domains keeps risk/exposure definition comparable. It does not mean nine constructs each receive equal weight.','no_age':'Physical budget redistributed over remaining entropy and footprint coordinates; not removed from entire domain','pop_density':'Separate demographic domain allocated half existing loss/exposure budget, total remains one; not a second primary physical-density input','samples':'paired feature comparisons use identical complete cohort; legacy/coverage subset comparisons explicitly change sample and evaluate ARI on common tracts','formal_labels_used':False,'PCA':'none; direct weighted-coordinate KMeans, exploratory method distinct from stored formal Stage7 PCA','spatial':'20km EPSG3310 centroid blocks; 20 block deletions, 10% occupied blocks per deletion, original full-data predictions compared on entire complete-case set','bootstrap':'none; seed variability is optimization variability, not sampling CI'})
 from concurrent.futures import ProcessPoolExecutor,as_completed
 with ProcessPoolExecutor(max_workers=6) as pool:
  for future in as_completed([pool.submit(precompute,s) for s in specs]):print('MODEL_BATCH',future.result(),flush=True)
 allrows=[];labelstore={};allweights=[];domains_by={};model_frames={};matrices={};start=time.time()
 with threadpool_limits(limits=1):
  for spec in specs:
   name=spec['name'];sub=d
   if spec['sample']=='legacy':sub=d.loc[d.legacy2276_complete_case]
   if spec['sample']=='coverage_top75':sub=d.loc[d.land_use_classified_land_coverage.ge(d.land_use_classified_land_coverage.quantile(.25))]
   matrix,cols,domains,scaler,factors,weights=design(sub,spec);allweights.extend(weights);domains_by[name]=(cols,domains);model_frames[name]=sub;matrices[name]=matrix
   samplehash=hashlib.sha256('\n'.join(sub.index).encode()).hexdigest();mh=hashlib.sha256(np.ascontiguousarray(matrix).tobytes()).hexdigest();cp=checkpoint/(name+'.npz');meta=checkpoint/(name+'.json')
   if cp.exists() and meta.exists():
    m=json.loads(meta.read_text());assert m['matrix_sha256']==mh and m['n_init']==NINIT;rows=m['rows'];z=np.load(cp);labs={(int(k.split('_')[0][1:]),int(k.split('_')[1][1:])):z[k] for k in z.files}
   else:
    dist=pairwise_distances(matrix,metric='euclidean');rows=[];labs={}
    for seed in SEEDS:
     rr=[]
     for k in KS:
      labels,km,metrics=fit_one(matrix,k,seed,dist);labs[(seed,k)]=labels
      rr.append({'model':name,'seed':seed,'k':k,'n':len(sub),'n_init':NINIT,'sample_sha256':samplehash,'matrix_sha256':mh,**metrics})
     selected=select_k([r['inertia'] for r in rr])
     for row in rr:row['selected_k']=selected;row['selected_run']=row['k']==selected;row['fixed_k5']=row['k']==5
     rows+=rr
     if seed in [42,46,51,56,61]:print('CLUSTER',name,'seed',seed,'selected',selected,'elapsed',round(time.time()-start,1),flush=True)
    np.savez_compressed(cp,**{f's{s}_k{k}':l for (s,k),l in labs.items()});meta.write_text(json.dumps({'matrix_sha256':mh,'n_init':NINIT,'rows':rows}),encoding='utf-8')
   allrows+=rows
   for (seed,k),labels in labs.items():labelstore[(name,seed,k)]=pd.Series(labels,index=sub.index)
 result=pd.DataFrame(allrows);save('CONTROLLED_CLUSTERING_COMPARISON.csv',result);save('CLUSTER_DOMAIN_WEIGHTS.csv',pd.DataFrame(allweights))
 stability=[];pairs=[];profiles=[];domainrows=[];labelout=pd.DataFrame(index=d.index)
 for spec in specs:
  name=spec['name'];sub=model_frames[name];cols,domains=domains_by[name];matrix=matrices[name]
  for role in ['fixed_k5','selected_run']:
   rr=result.loc[result.model.eq(name)&result[role]]
   for a,b in itertools.combinations(SEEDS,2):
    ka=int(rr.loc[rr.seed.eq(a),'k'].iloc[0]);kb=int(rr.loc[rr.seed.eq(b),'k'].iloc[0]);ari=adjusted_rand_score(labelstore[(name,a,ka)],labelstore[(name,b,kb)]);pairs.append({'model':name,'role':role,'seed_a':a,'seed_b':b,'k_a':ka,'k_b':kb,'ari':ari})
   pv=pd.DataFrame(pairs);v=pv.loc[pv.model.eq(name)&pv.role.eq(role),'ari'];stability.append({'record_type':'OPTIMIZATION_SEED_STABILITY','model':name,'role':role,'n':len(sub),'seeds':20,'pair_count':190,'ari_median':v.median(),'ari_min':v.min(),'ari_p05':v.quantile(.05),'silhouette_mean':rr.silhouette.mean(),'silhouette_sd':rr.silhouette.std(),'minimum_cluster_size':rr.minimum_cluster_size.min(),'selected_k_counts':rr.k.value_counts().sort_index().to_json()})
   k=int(rr.loc[rr.seed.eq(42),'k'].iloc[0]);labels=labelstore[(name,42,k)];labelout[name+'__'+role]=labels+1
   for cluster in range(k):
    idx=labels.index[labels.eq(cluster)]
    for field in ['B_480_hr','T80','Init_Supply']+GRID+['land_use_entropy','land_use_classified_land_coverage','building_footprint_coverage','all_use2014_pre1970_area_share','all_use2014_age_coverage','residential_pre1970_housing_share','SOVI_SCORE','log1p_NRI_BUILDVALUE','ALR_NPCTL','EAL_SCORE','Pop_Density','housing_5plus_share']:
     values=sub.loc[idx,field];profiles.append({'record_type':'DESCRIPTIVE_PROFILE','model':name,'role':role,'seed':42,'k':k,'cluster_id':cluster+1,'n_cluster':len(idx),'feature':field,'observed_n':values.notna().sum(),'mean':values.mean(),'median':values.median(),'p05':values.quantile(.05),'p95':values.quantile(.95),'label_semantics':'arbitrary exploratory ID, no old formal label assignment'})
   center=np.vstack([matrix[labels.eq(i)].mean(axis=0) for i in range(k)]);between=matrix.shape[0]*0.;within=(matrix-center[labels.to_numpy()])**2
   total=(matrix-matrix.mean(axis=0))**2;between_by=total.sum(axis=0)-within.sum(axis=0)
   for domain,fields in domains.items():
    ix=[cols.index(c) for c in fields];b=between_by[ix].sum();w=within[:,ix].sum();domainrows.append({'model':name,'role':role,'seed':42,'k':k,'domain':domain,'between_sumsquares':b,'within_sumsquares':w,'domain_explained_fraction':b/(b+w),'between_share_all_domains':b/between_by.sum(),'meaning':'geometric separation in defined domain, not causal information'})
 between=[]
 for spec in specs:
  name=spec['name'];reference='D__'+spec['budget']
  if name==reference:continue
  for seed in SEEDS:
   for role in ['fixed_k5','selected_run']:
    ka=5 if role=='fixed_k5' else int(result.loc[result.model.eq(name)&result.seed.eq(seed)&result.selected_run,'k'].iloc[0]);kb=5 if role=='fixed_k5' else int(result.loc[result.model.eq(reference)&result.seed.eq(seed)&result.selected_run,'k'].iloc[0]);a=labelstore[(name,seed,ka)];b=labelstore[(reference,seed,kb)];idx=a.index.intersection(b.index)
    between.append({'model':name,'reference_model':reference,'seed':seed,'role':role,'k_model':ka,'k_reference':kb,'n_common':len(idx),'ari':adjusted_rand_score(a.loc[idx],b.loc[idx]),'sample_change':len(a)!=len(b),'comparison':'same seed, same common tract IDs; descriptive partition sensitivity'})
 for seed in SEEDS:
  for name in ['D','EAL','D_T80','D_logB','D_ACS_age','D_no_age']:
   a=labelstore[(name+'__inherited',seed,5)];b=labelstore[(name+'__equal_five_domains',seed,5)];between.append({'model':name+'__equal_five_domains','reference_model':name+'__inherited','seed':seed,'role':'fixed_k5_domain_budget','k_model':5,'k_reference':5,'n_common':len(a),'ari':adjusted_rand_score(a,b),'sample_change':False,'comparison':'domain budget sensitivity'})
 save('CLUSTER_BETWEEN_MODEL_ARI.csv',pd.DataFrame(between));save('CLUSTER_WITHIN_MODEL_PAIRWISE_ARI.csv',pd.DataFrame(pairs));save('CLUSTER_DOMAIN_CONTRIBUTIONS.csv',pd.DataFrame(domainrows));save('CLUSTER_STABILITY_AND_PROFILES.csv',pd.concat([pd.DataFrame(stability),pd.DataFrame(profiles)],ignore_index=True));save('EXPLORATORY_LABELS_SEED42.csv',labelout,index=True)
 # Contiguous geographic block deletions preserve shared exposures better than iid tract sampling.
 import geopandas as gpd
 geo=gpd.read_file(ROOT/'Data/LA_Tracts_With_Population.shp');geo['tract_id']=geo.GEOID.astype(str);geo=geo.set_index('tract_id').loc[d.index].to_crs(3310);cent=geo.geometry.centroid;blocks=pd.Series([(int(x//20000),int(y//20000)) for x,y in zip(cent.x,cent.y)],index=d.index);unique=sorted(set(blocks));sp=[];base_spec=specs[0]
 with threadpool_limits(limits=1):
  for seed in SEEDS:
   rng=np.random.default_rng(seed);choice=rng.choice(len(unique),max(1,int(np.ceil(.1*len(unique)))),replace=False);removed={unique[i] for i in choice};train=d.loc[~blocks.isin(removed)];mat,cols,domains,scaler,factors,_=design(train,base_spec);km=KMeans(n_clusters=5,n_init=NINIT,random_state=seed,max_iter=500,tol=1e-4).fit(mat);pred=km.predict(scaler.transform(d[cols])*factors);reference=labelstore[('D__inherited',seed,5)];ari=adjusted_rand_score(reference,pred)
   sp.append({'seed':seed,'n_training':len(train),'n_heldout':len(d)-len(train),'occupied_blocks':len(unique),'removed_blocks':';'.join(f'{x}:{y}' for x,y in sorted(removed)),'full_prediction_ARI':ari,'training_ARI':adjusted_rand_score(reference.loc[train.index],pred[d.index.isin(train.index)]),'heldout_ARI':adjusted_rand_score(reference.loc[d.index.difference(train.index,sort=False)],pred[~d.index.isin(train.index)]),'method':'20km spatial-block delete10percent, scaler refit on retained tracts, predict full cohort','meaning':'partition sensitivity to spatial sample perturbation, not independent validation'})
 save('SPATIAL_BLOCK_STABILITY.csv',pd.DataFrame(sp));save('TRACT_SPATIAL_BLOCKS.csv',pd.DataFrame({'tract_id':d.index,'block':[str(x) for x in blocks],'centroid_x_3310':cent.x.to_numpy(),'centroid_y_3310':cent.y.to_numpy()}))
 dump('CLUSTER_EXECUTION_QA.json',{'models':len(specs),'n_fit_records':len(result),'seeds':20,'n_init':100,'k_range':KS,'base_sample_n':len(d),'spatial_replicates':len(sp),'seconds':time.time()-start,'formal_files_written':0,'versions':{'numpy':np.__version__,'pandas':pd.__version__,'sklearn':__import__('sklearn').__version__},'duplicate_experiments':'each observed model/seed/k is unique; entropy proportional is an explicitly same-definition sensitivity, not independent replication'})
 print('COMPLETE_CONTROLLED_CLUSTERING',len(result),'seconds',round(time.time()-start,1),flush=True)
if __name__=='__main__':run()
