"""Fixed-cohort, fixed-k construct/weight sensitivity; no formal-file writes."""
import os
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
 os.environ.setdefault(key,'1')
from pathlib import Path
import json,hashlib,time,sys,ast,itertools,platform
import numpy as np,pandas as pd,scipy,sklearn
from sklearn.preprocessing import StandardScaler,PolynomialFeatures
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score,silhouette_score,pairwise_distances,r2_score
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LinearRegression
from scipy.optimize import linear_sum_assignment
from scipy.stats import pearsonr,spearmanr
from threadpoolctl import threadpool_limits

HERE=Path(__file__).resolve().parent
WT=HERE if HERE.name!='built_env_validity_controlled_audit_20261010' else HERE.parents[3]
WT=Path('\\\\?\\'+str(WT)) if not str(WT).startswith('\\\\?\\') else WT
ROOT=WT/'docs/data_research/built_environment_20261009'
OUT=ROOT/'built_env_validity_controlled_audit_20261010'
BASE=ROOT/'final_feature_validation_20261010'; SP=ROOT/'spatial_k4_validation_20261010'
SEEDS=list(range(42,62));PARENT='5f49471ac707c001baefa1fa860aa77971dd62c5'
PARAMS=dict(n_clusters=4,n_init=100,max_iter=500,tol=1e-4,algorithm='lloyd')
PHYS=['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share']
GRID=['Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI']
BUDGETS={'equal':dict(recovery_service=.2,grid=.2,physical=.2,social=.2,loss_exposure=.2),
 'inherited':dict(recovery_service=2/11,grid=4/11,physical=2/11,social=1/11,loss_exposure=2/11)}
DESCRIPTORS=['B_480_hr','T80','Init_Supply','SOVI_SCORE',*PHYS,'land_use_classified_land_coverage','all_use2014_age_coverage','NRI_BUILDVALUE','ALR_NPCTL','EAL_SCORE',*GRID,'Pop_Density','residential_pre1970_housing_share']
UNRESOLVED=['06037189703','06037301601','06037301602','06037404600']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def ahash(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def jdump(name,value):
 (OUT/name).parent.mkdir(parents=True,exist_ok=True)
 (OUT/name).write_bytes(json.dumps(value,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x),allow_nan=False).encode())
def save(name,data):
 if not isinstance(data,pd.DataFrame):data=pd.DataFrame(data)
 (OUT/name).write_bytes(data.to_csv(index=False,lineterminator='\n',float_format='%.15g').encode())
def read(path):return pd.read_csv(path,dtype={'tract_id':str}).set_index('tract_id')
def inputs():
 master=read(BASE/'FINAL_CANDIDATE_FEATURE_MATRIX.csv');d=master.loc[master.primary_complete_case].copy()
 assert len(master)==2291 and len(d)==2287 and master.index.is_unique
 assert all(x.isdigit() and len(x)==11 for x in master.index)
 assert set(master.index.difference(d.index))==set(UNRESOLVED)
 assert master.loc[UNRESOLVED,PHYS].isna().all().all()
 assert d.index.equals(read(BASE/'COMPLETE_CASE_FEATURE_MATRIX.csv').index)
 blocks=read(BASE/'TRACT_SPATIAL_BLOCKS.csv').loc[d.index]
 blocks['block_id']=blocks.block.map(lambda s:':'.join(map(str,ast.literal_eval(s))))
 old=pd.read_csv(SP/'SPATIAL_K4_RUNS.csv');sets={}
 for seed,g in old.groupby('seed'):
  assert g.removed_blocks.nunique()==1
  removed=sorted(g.removed_blocks.iloc[0].split(';'));mask=~blocks.block_id.isin(removed)
  assert mask.sum()==g.n_training.iloc[0]
  sets[int(seed)]={'removed_blocks':removed,'n_training':int(mask.sum()),'n_heldout':int((~mask).sum())}
 assert sorted(sets)==SEEDS
 return master,d,blocks,sets
def specs():
 s=[]
 def add(name,phys=PHYS,budget='equal',risk='D',mode='redistribute',source=None,spatial_source=None,family='physical'):
  s.append(dict(name=name,physical=list(phys),budget=budget,risk=risk,physical_weight_mode=mode,saved_full_source=source,saved_spatial_source=spatial_source,family=family))
 add('BE0',source='D__equal_five_domains',spatial_source='D',family='reference')
 add('D_INHERITED',budget='inherited',source='D__inherited',family='weights')
 for budget,src in [('equal','equal_five_domains'),('inherited','inherited')]:
  add('EAL_'+budget.upper(),budget=budget,risk='EAL',source='EAL__'+src,spatial_source='EAL' if budget=='equal' else None,family='risk_exposure')
  add('ALR_ONLY_'+budget.upper(),budget=budget,risk='ALR',family='risk_exposure')
  add('BE1_'+budget.upper(),phys=PHYS[:2],budget=budget,source='D_no_age__'+src,family='age')
  add('BE7_ACS_'+budget.upper(),phys=PHYS[:2]+['residential_pre1970_housing_share'],budget=budget,source='D_ACS_age__'+src,family='age')
 combos={2:[PHYS[0],PHYS[2]],3:PHYS[1:],4:PHYS[:1],5:PHYS[1:2],6:PHYS[2:]}
 for n,cols in combos.items():add(f'BE{n}_EQUAL',phys=cols)
 for n,cols in {1:PHYS[:2],**combos}.items():add(f'BE{n}_FIXED_COORD',phys=cols,mode='fixed_coordinate',family='deletion_weight_control')
 for budget in ['equal','inherited']:
  for side in ['lower','upper']:
   add(f'BE8_{side.upper()}_{budget.upper()}',phys=PHYS[:2]+[f'age_{side}_bound'],budget=budget,source=f'D_age_{side}_bound__inherited' if budget=='inherited' else None,family='age_missingness')
  for target in ['transport','dominant']:
   add(f'SCAG_{target.upper()}_{budget.upper()}',phys=[f'entropy_missing_to_{target}',*PHYS[1:]],budget=budget,source=f'D_entropy_{target}__inherited' if budget=='inherited' else None,family='land_coverage')
 assert len(s)==29
 return s
def design(d,s,mask=None):
 domains={'recovery_service':['B_480_hr','Init_Supply'],'grid':GRID,'physical':s['physical'],'social':['SOVI_SCORE'],'loss_exposure':{'D':['log1p_NRI_BUILDVALUE','ALR_NPCTL'],'ALR':['ALR_NPCTL'],'EAL':['EAL_SCORE']}[s['risk']]}
 cols=[c for v in domains.values() for c in v];budget=BUDGETS[s['budget']]
 factors=np.array([np.sqrt(budget[k]/(3 if k=='physical' and s['physical_weight_mode']=='fixed_coordinate' else len(v))) for k,v in domains.items() for c in v])
 raw=d[cols];assert raw.notna().all().all() and np.isfinite(raw).all().all()
 sc=StandardScaler()
 if mask is None:z=sc.fit_transform(raw)
 else:sc.fit(raw.loc[mask]);z=sc.transform(raw)
 return z*factors,cols,domains,sc,factors
def mapping(y,p,mask):
 tab=np.zeros((4,4),int)
 np.add.at(tab,(y[mask],p[mask]),1)
 rows,cols=linear_sum_assignment(-tab)
 mp={int(a):int(b) for a,b in zip(rows,cols) if tab[a].sum()>0}
 aligned=np.full(len(p),-1,int)
 for a,b in mp.items():aligned[p==b]=a
 return mp,aligned,tab
def declare():
 master,d,blocks,sets=inputs();sp=specs();sources=[]
 for path in [BASE/'FINAL_CANDIDATE_FEATURE_MATRIX.csv',BASE/'COMPLETE_CASE_FEATURE_MATRIX.csv',BASE/'TRACT_SPATIAL_BLOCKS.csv',BASE/'CONTROLLED_EXPERIMENT_SPECIFICATION.json',BASE/'CONTROLLED_CLUSTERING_COMPARISON.csv',SP/'INPUT_AND_BASELINE_QA.json',SP/'SPATIAL_K4_RUNS.csv',ROOT/'physical_feature_gate_20261010/NEXT_STAGE7_GATE.md',ROOT/'manuscript_reconciliation_20261010/MANUSCRIPT_RECONCILIATION_DECISION.md',ROOT/'manuscript_integration_preview_20261010/STAGE7_CANDIDATE_FREEZE.json']:
  assert not path.read_bytes().startswith(b'version https://git-lfs')
  sources.append({'file':str(path.relative_to(WT)).replace('\\','/'),'sha256':sha(path),'source_commit':PARENT})
 for s in sp:
  for ext in ['npz','json']:
   if s['saved_full_source']:
    p=BASE/'run_records'/f"{s['saved_full_source']}.{ext}";sources.append({'file':str(p.relative_to(WT)).replace('\\','/'),'sha256':sha(p),'source_commit':'50df10481815f3dd94c46dc9443f93cfdb1c5014'})
  x,cols,dom,sc,w=design(d,s);s['matrix_sha256']=ahash(x);s['feature_columns']=cols;s['coordinate_factors']=w.tolist();s['domains']=dom
 newfull=sum(s['saved_full_source'] is None for s in sp)*20
 newspatial=sum(s['saved_spatial_source'] is None for s in sp)*20
 assert newfull+newspatial==880
 jdump('CONTROLLED_COMPARISON_SPECIFICATION.json',dict(parent=PARENT,models=sp,seeds=SEEDS,k=4,KMeans=PARAMS,new_full_fits=newfull,new_spatial_fits=newspatial,maximum_new_fits=880,saved_full_reused=580-newfull,saved_spatial_reused=580-newspatial,cohort_n=2287,master_n=2291,unresolved=UNRESOLVED,sample_sha256=hashlib.sha256('\n'.join(d.index).encode()).hexdigest(),spatial_deletions=sets,unique_spatial_sets=len({tuple(v['removed_blocks']) for v in sets.values()}),versions={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scikit_learn':sklearn.__version__,'scipy':scipy.__version__},aliases={'SCAG_PROPORTIONAL_EQUAL':'BE0','SCAG_PROPORTIONAL_INHERITED':'D_INHERITED'},fit_limit_applies_to_this_audit=True,full_cohort_not_resampled=True,thresholds_chosen_after_results=False,k_search=False))
 save('SOURCE_HASHES.csv',pd.DataFrame(sources).drop_duplicates('file'))
 save('TRACT_COHORT_AND_SPATIAL_CASES.csv',pd.DataFrame({'tract_id':master.index,'complete_case':master.primary_complete_case,'block_id':blocks.block_id.reindex(master.index),'status':np.where(master.primary_complete_case,'COMPLETE_CASE','UNCLASSIFIED_GEOMETRY')}))
 assert np.allclose(d.entropy_missing_proportional,d.land_use_entropy,atol=1e-13,rtol=0)
 jdump('PROPORTIONAL_ALLOCATION_IDENTITY.json',{'mathematical_identity':True,'max_source_serialization_difference':float((d.entropy_missing_proportional-d.land_use_entropy).abs().max()),'alias_reuses_baseline_not_independent_replication':True})
 print('PREDECLARED',len(sp),'models;',newfull,'new full fits;',newspatial,'new spatial fits; 280 existing runs reused',flush=True)
 return sp
def fit():
 master,d,blocks,sets=inputs();sp=declare();(OUT/'run_records').mkdir(exist_ok=True)
 start=time.perf_counter();new=0;old=0;cache=0
 with threadpool_limits(limits=1):
  for s in sp:
   cp=OUT/'run_records'/f"{s['name']}.npz";mpath=cp.with_suffix('.json')
   signature=hashlib.sha256(json.dumps(s,sort_keys=True).encode()).hexdigest()
   if cp.exists() and mpath.exists():
    meta=json.loads(mpath.read_text());assert meta['signature']==signature and meta['payload_sha256']==sha(cp);cache+=40;print('CACHE',s['name'],flush=True);continue
   x,cols,domains,sc,w=design(d,s);arrays={'tract_ids':np.asarray(d.index,dtype=str),'feature_columns':np.asarray(cols,dtype=str),'coordinate_factors':w,'full_scaler_mean':sc.mean_,'full_scaler_scale':sc.scale_,'full_scaler_var':sc.var_}
   rows=[]
   if s['saved_full_source']:
    src=BASE/'run_records'/f"{s['saved_full_source']}.npz";sm=json.loads(src.with_suffix('.json').read_text());assert sm['matrix_sha256']==ahash(x) and sm['n_init']==100
    full=np.load(src);source_rows={r['seed']:r for r in sm['rows'] if r['k']==4}
   for seed in SEEDS:
    t=time.perf_counter()
    if s['saved_full_source']:
     y=full[f's{seed}_k4'];centers=np.array([x[y==i].mean(axis=0) for i in range(4)])
     r={**source_rows[seed],'origin':'SAVED_FULL_REUSED','center_kind':'saved-label means; original algorithm centers unavailable','source_file':str(src.relative_to(WT)).replace('\\','/')};old+=1
    else:
     km=KMeans(**PARAMS,random_state=seed).fit(x);y=km.labels_;centers=km.cluster_centers_
     r={'inertia':float(km.inertia_),'iterations':int(km.n_iter_),'elapsed_s':time.perf_counter()-t,'origin':'NEW_FULL_FIT','center_kind':'actual KMeans centers'};new+=1
    arrays[f'full_s{seed}']=y;arrays[f'full_centers_s{seed}']=centers;rows.append({'scope':'full','seed':seed,**r})
    mask=~blocks.block_id.isin(sets[seed]['removed_blocks']);arrays[f'train_s{seed}']=mask.to_numpy()
    xs,_,_,ss,_=design(d,s,mask)
    t=time.perf_counter()
    if s['saved_spatial_source']:
     src=SP/'run_records'/f"{s['saved_spatial_source']}_s{seed}.npz";prev=np.load(src);sm=json.loads(src.with_suffix('.json').read_text());assert sm['spec']['source_matrix_sha256']==ahash(x)
     assert np.array_equal(prev['tract_ids'],arrays['tract_ids']) and np.array_equal(prev['train_mask'],mask)
     assert np.array_equal(prev['baseline_labels'],y) and np.array_equal(prev['coordinate_factors'],w)
     assert np.array_equal(prev['scaler_mean'],ss.mean_) and np.array_equal(prev['scaler_scale'],ss.scale_)
     pred=prev['raw_prediction'];cc=prev['cluster_centers'];r={'inertia':sm['inertia'],'iterations':sm['iterations'],'elapsed_s':sm['fit_elapsed_s'],'origin':'SAVED_SPATIAL_REUSED','source_file':str(src.relative_to(WT)).replace('\\','/')};old+=1
    else:
     km=KMeans(**PARAMS,random_state=seed).fit(xs[mask]);pred=km.predict(xs);cc=km.cluster_centers_
     r={'inertia':float(km.inertia_),'iterations':int(km.n_iter_),'elapsed_s':time.perf_counter()-t,'origin':'NEW_SPATIAL_FIT'};new+=1
    arrays[f'spatial_s{seed}']=pred;arrays[f'spatial_centers_s{seed}']=cc
    arrays[f'spatial_mean_s{seed}']=ss.mean_;arrays[f'spatial_scale_s{seed}']=ss.scale_;arrays[f'spatial_var_s{seed}']=ss.var_
    rows.append({'scope':'spatial','seed':seed,**r})
   np.savez_compressed(cp,**arrays);jdump('run_records/'+mpath.name,{'signature':signature,'spec':s,'rows':rows,'payload_sha256':sha(cp)})
   print('COMPLETE',s['name'],'new',new,'reused',old,'elapsed',round(time.perf_counter()-start,1),flush=True)
 assert new<=880
 record=dict(new_fits_this_invocation=new,reused_saved_runs=old,reused_current_checkpoints=cache,unique_model_runs=1160,maximum_new_fits=880,elapsed_s=time.perf_counter()-start,simulation_runs=0,GA_runs=0,GIS_extractions=0,k_searches=0)
 # Preserve the original audit execution rather than replacing its accounting on resume.
 jdump('FIT_LAST_RESUME.json' if (OUT/'FIT_EXECUTION_RECORD.json').exists() else 'FIT_EXECUTION_RECORD.json',record)
def class_metrics(y,p,mask):
 mp,a,tab=mapping(y,p,mask);rows=[]
 for i in range(4):
  own=y==i;pred=p==mp[i] if i in mp else np.zeros(len(y),bool)
  inter=int((own&pred).sum());union=int((own|pred).sum());n=int(own.sum());pn=int(pred.sum())
  rows.append({'reference_class':i+1,'predicted_raw_class':mp.get(i,-2)+1,'training_support':bool((own&mask).any()),'baseline_n':n,'predicted_n':pn,'intersection':inter,'union':union,'retention':inter/n if n else np.nan,'purity':inter/pn if pn else np.nan,'jaccard':inter/union if union else np.nan,'training_baseline_n':int((own&mask).sum())})
 return rows,a,tab,mp
def analyze_runs():
 master,d,blocks,sets=inputs();sp=specs();ref=np.load(BASE/'run_records/D__equal_five_domains.npz');ref42=ref['s42_k4'];target=ref42==np.flatnonzero(np.bincount(ref42)==34)[0]
 desc=d[DESCRIPTORS];std=desc.std(ddof=0);outfull=[];outsp=[];cls=[];profiles=[];contrib=[];small=[];changes=[];cont=[];within=[];shifts=[]
 commonx,_,_,_,_=design(d,specs()[0])
 with threadpool_limits(limits=1):
  for s in sp:
   z=np.load(OUT/'run_records'/f"{s['name']}.npz");meta=json.loads((OUT/'run_records'/f"{s['name']}.json").read_text());x,cols,dom,sc,w=design(d,s);domain_by={c:k for k,v in dom.items() for c in v};dist=pairwise_distances(x)
   own42=z['full_s42']
   for sa,sb in itertools.combinations(SEEDS,2):within.append({'model':s['name'],'seed_a':sa,'seed_b':sb,'ARI':adjusted_rand_score(z[f'full_s{sa}'],z[f'full_s{sb}'])})
   for seed in SEEDS:
    y=z[f'full_s{seed}'];p=z[f'spatial_s{seed}'];mask=z[f'train_s{seed}'];base=ref[f's{seed}_k4'];mf,aligned,tab,mp=class_metrics(base,y,np.ones(len(d),bool));ms,pa,sp_tab,sp_mp=class_metrics(y,p,mask)
    for scope,table in [('reference_vs_full',tab),('spatial_training_match',sp_tab)]:
     for i,j in itertools.product(range(4),repeat=2):cont.append({'model':s['name'],'seed':seed,'scope':scope,'reference_class':i+1,'prediction_raw_class':j+1,'n':int(table[i,j])})
    for r in mf:cls.append({'model':s['name'],'seed':seed,'scope':'BE0_same_seed_vs_model',**r})
    for r in ms:cls.append({'model':s['name'],'seed':seed,'scope':'model_same_seed_vs_spatial',**r})
    for scope,scope_mask in [('training',mask),('heldout',~mask)]:
     for i in range(4):
      own=(y==i)&scope_mask;pred=(p==sp_mp[i])&scope_mask if i in sp_mp else np.zeros(len(y),bool)
      inter=int((own&pred).sum());n=int(own.sum());pn=int(pred.sum());union=n+pn-inter
      cls.append({'model':s['name'],'seed':seed,'scope':'model_same_seed_vs_spatial__'+scope,'reference_class':i+1,'predicted_raw_class':sp_mp.get(i,-2)+1,'training_support':bool(((y==i)&mask).any()),'baseline_n':n,'predicted_n':pn,'intersection':inter,'union':union,'retention':inter/n if n else np.nan,'purity':inter/pn if pn else np.nan,'jaccard':inter/union if union else np.nan,'training_baseline_n':int(((y==i)&mask).sum())})
     for i,j in itertools.product(range(4),repeat=2):cont.append({'model':s['name'],'seed':seed,'scope':'spatial_'+scope+'_raw','reference_class':i+1,'prediction_raw_class':j+1,'n':int(((y==i)&(p==j)&scope_mask).sum())})
    for scope,yy,qq,mpp in [('feature_change_vs_BE0',base,y,mp),('spatial_vs_own_baseline',y,p,sp_mp)]:
     for i,j in mpp.items():
      shift=commonx[qq==j].mean(axis=0)-commonx[yy==i].mean(axis=0)
      shifts.append({'model':s['name'],'seed':seed,'scope':scope,'reference_class':i+1,'weighted_center_shift':float(np.linalg.norm(shift)),'coordinate_system':'common full-cohort BE0 standardized and weighted coordinates; descriptive center shift, not probability'})
    changed=aligned!=base
    r=next(r for r in meta['rows'] if r['seed']==seed and r['scope']=='full')
    budget=s['budget'];physicalbudget=sum(w[cols.index(c)]**2 for c in dom['physical'])
    outfull.append({'model':s['name'],'family':s['family'],'seed':seed,'k':4,'n':len(d),'budget':budget,'physical_weight_mode':s['physical_weight_mode'],'physical_domain_budget':physicalbudget,'total_squared_weight':float((w*w).sum()),'physical_coordinates':';'.join(s['physical']),'risk_representation':s['risk'],'ARI_vs_BE0_same_seed':adjusted_rand_score(base,y),'ARI_vs_frozen_BE0_seed42':adjusted_rand_score(ref42,y),'aligned_reassigned_n':int(changed.sum()),'aligned_reassigned_fraction':float(changed.mean()),'class_sizes':';'.join(map(str,np.bincount(y,minlength=4))),'minimum_cluster_size':int(np.bincount(y).min()),'silhouette':silhouette_score(dist,y,metric='precomputed'),'inertia':r['inertia'],'iterations':r['iterations'],'origin':r['origin']})
    a,aa,tt,mmm=class_metrics(own42,y,np.ones(len(d),bool))
    s42map={raw:di for di,raw in mmm.items()}
    outsp.append({'model':s['name'],'seed':seed,'reference':'same-model same-seed full-cohort labels','training_n':int(mask.sum()),'heldout_n':int((~mask).sum()),'removed_blocks':';'.join(sets[seed]['removed_blocks']),'ARI_all':adjusted_rand_score(y,p),'ARI_training':adjusted_rand_score(y[mask],p[mask]),'ARI_heldout':adjusted_rand_score(y[~mask],p[~mask]),'aligned_reassigned_n':int((pa!=y).sum()),'minimum_purity':float(np.nanmin([r['purity'] for r in ms])),'minimum_jaccard':float(np.nanmin([r['jaccard'] for r in ms]))})
    for scope,q,support in [('full',y,np.ones(len(d),bool)),('spatial',p,mask)]:
     counts=np.bincount(q[target],minlength=4);matched=int(counts.argmax()) if scope=='full' else sp_mp.get(int(np.bincount(y[target],minlength=4).argmax()))
     sel=q==matched if matched is not None else np.zeros(len(q),bool);inter=int((sel&target).sum());pn=int(sel.sum())
     small.append({'model':s['name'],'seed':seed,'scope':scope,'target':'saved D seed42 34 members','target_n':int(target.sum()),'training_target_n':int((target&support).sum()),'matched_raw_class':matched+1 if matched is not None else np.nan,'predicted_n':pn,'intersection':inter,'retention':inter/34,'purity':inter/pn if pn else np.nan,'jaccard':inter/(34+pn-inter) if pn else np.nan,'target_destinations':json.dumps(counts.tolist()),'incoming_other_n':pn-inter})
    for r in mf:
     i=r['reference_class']-1;j=mp[i];old=desc.loc[base==i];cur=desc.loc[y==j]
     for col in DESCRIPTORS:
      profiles.append({'model':s['name'],'seed':seed,'scope':'feature_change_vs_BE0','reference_class':i+1,'feature':col,'baseline_mean':old[col].mean(),'mean':cur[col].mean(),'median':cur[col].median(),'p10':cur[col].quantile(.1),'p90':cur[col].quantile(.9),'mean_change':cur[col].mean()-old[col].mean(),'mean_change_full_cohort_SD':(cur[col].mean()-old[col].mean())/std[col]})
    for r in ms:
     i=r['reference_class']-1;j=sp_mp.get(i);display=s42map.get(i,-1)+1
     if j is None:continue
     old=desc.loc[y==i];ret=desc.loc[(y==i)&mask];cur=desc.loc[p==j];traincur=desc.loc[(p==j)&mask]
     for col in DESCRIPTORS:
      profiles.append({'model':s['name'],'seed':seed,'scope':'spatial_vs_own_baseline','reference_class':i+1,'model_seed42_display_class':display,'feature':col,'baseline_mean':old[col].mean(),'retained_original_mean':ret[col].mean(),'mean':cur[col].mean(),'median':cur[col].median(),'p10':cur[col].quantile(.1),'p90':cur[col].quantile(.9),'mean_change':cur[col].mean()-old[col].mean(),'mean_change_full_cohort_SD':(cur[col].mean()-old[col].mean())/std[col],'deleted_member_shift':ret[col].mean()-old[col].mean(),'reclassification_shift_training':traincur[col].mean()-ret[col].mean()})
    means=np.array([x[y==i].mean(axis=0) for i in range(4)]);centered=x-x.mean(axis=0);resid=x-means[y]
    total=(centered*centered).sum(axis=0);withinss=(resid*resid).sum(axis=0);between=total-withinss
    for ix,c in enumerate(cols):contrib.append({'model':s['name'],'seed':seed,'feature':c,'domain':domain_by[c],'coordinate_squared_weight':float(w[ix]**2),'total_SS':total[ix],'within_SS':withinss[ix],'between_SS':between[ix],'total_distance_fraction':total[ix]/total.sum(),'within_distance_fraction':withinss[ix]/withinss.sum(),'between_class_fraction':between[ix]/between.sum(),'variance_explained_by_partition':between[ix]/total[ix]})
    if seed==42:
     for ix,id in enumerate(d.index):changes.append({'tract_id':id,'model':s['name'],'BE0_raw_class':int(ref42[ix])+1,'model_raw_class':int(y[ix])+1,'aligned_BE0_class':int(aligned[ix])+1,'changed':bool(changed[ix]),'SCAG_coverage':d.land_use_classified_land_coverage.iloc[ix],'age_coverage':d.all_use2014_age_coverage.iloc[ix]})
   print('SUMMARIZED',s['name'],flush=True)
 save('BUILT_ENV_ABLATION_RESULTS.csv',outfull);save('BUILT_ENV_SPATIAL_SENSITIVITY.csv',outsp);save('CLASS_MEMBERSHIP_STABILITY.csv',cls);save('RAW_CLUSTER_CROSSTABS.csv',cont);save('CLASS_PROFILE_CHANGES.csv',profiles);save('CLUSTER_DISTANCE_CONTRIBUTIONS.csv',contrib);save('SMALL_34_GROUP_SENSITIVITY.csv',small);save('SEED42_TRACT_REASSIGNMENTS.csv',changes);save('WITHIN_MODEL_SEED_AGREEMENT.csv',within);save('CLASS_CENTER_SHIFTS.csv',shifts)
def partial(x,y,c,rank=False):
 if rank:x=pd.Series(x).rank().to_numpy();y=pd.Series(y).rank().to_numpy();c=pd.DataFrame(c).rank().to_numpy()
 z=np.column_stack([np.ones(len(x)),c]);a=x-z@np.linalg.lstsq(z,x,rcond=None)[0];b=y-z@np.linalg.lstsq(z,y,rcond=None)[0]
 return pearsonr(a,b).statistic
def redundancy():
 master,d,blocks,sets=inputs();rows=[];pairbins=[]
 secondary=['Pop_Density','log1p_Pop_Density','building_count_density','NRI_BUILDVALUE','log1p_NRI_BUILDVALUE','SOVI_SCORE','impervious_land_fraction','residential_pre1970_housing_share','housing_5plus_share','ALR_NPCTL','EAL_SCORE']
 strata={'current_2287':d,'legacy_2276_current_values':d.loc[d.legacy2276_complete_case], 'SCAG_coverage_below_70pct':d.loc[d.land_use_classified_land_coverage<.7],'SCAG_coverage_70_to_85pct':d.loc[d.land_use_classified_land_coverage.between(.7,.85,inclusive='left')],'SCAG_coverage_85pct_plus':d.loc[d.land_use_classified_land_coverage>=.85],'age_coverage_below_90pct':d.loc[d.all_use2014_age_coverage<.9],'age_coverage_90pct_plus':d.loc[d.all_use2014_age_coverage>=.9]}
 for scope,frame in strata.items():
  pairs=list(itertools.combinations(PHYS,2))
  if scope=='current_2287':pairs+=list(itertools.product(PHYS,secondary))+list(itertools.combinations(['log1p_NRI_BUILDVALUE','ALR_NPCTL','EAL_SCORE','SOVI_SCORE'],2))+[('NRI_BUILDVALUE','ALR_NPCTL'),('NRI_BUILDVALUE','EAL_SCORE')]
  for a,b in pairs:
   sub=frame[[a,b]].dropna()
   for metric,fn in [('Pearson',pearsonr),('Spearman',spearmanr)]:
    rows.append({'scope':scope,'measure':metric,'feature':a,'other_feature':b,'n':len(sub),'value':fn(sub[a],sub[b]).statistic,'interpretation':'descriptive association; spatial dependence; no independent-tract significance test'})
 for cols,scope in [(PHYS,'physical_3'),(['SOVI_SCORE','log1p_NRI_BUILDVALUE','ALR_NPCTL'],'D_risk_social'),(['SOVI_SCORE','ALR_NPCTL'],'ALR_only_social'),(['SOVI_SCORE','EAL_SCORE'],'EAL_social')]:
  frame=d[cols].dropna();z=StandardScaler().fit_transform(frame)
  for ix,c in enumerate(cols):
   cov=np.delete(z,ix,axis=1);lm=LinearRegression().fit(cov,z[:,ix]);r2=lm.score(cov,z[:,ix]);rows.append({'scope':scope,'measure':'VIF','feature':c,'other_feature':';'.join(x for x in cols if x!=c),'n':len(z),'value':1/(1-r2),'joint_explained_fraction':r2})
 for a,b in itertools.combinations(PHYS,2):
  controls=[c for c in PHYS if c not in [a,b]]
  for metric,rank in [('partial_Pearson',False),('partial_Spearman',True)]:rows.append({'scope':'physical_3','measure':metric,'feature':a,'other_feature':b,'controls':';'.join(controls),'n':len(d),'value':partial(d[a].to_numpy(),d[b].to_numpy(),d[controls].to_numpy(),rank)})
 for a,b in itertools.combinations(['log1p_NRI_BUILDVALUE','ALR_NPCTL','EAL_SCORE'],2):
  controls=['SOVI_SCORE','log1p_Pop_Density']
  for metric,rank in [('partial_Pearson',False),('partial_Spearman',True)]:rows.append({'scope':'risk_exposure','measure':metric,'feature':a,'other_feature':b,'controls':';'.join(controls),'n':len(d),'value':partial(d[a].to_numpy(),d[b].to_numpy(),d[controls].to_numpy(),rank)})
 for target in PHYS:
  for predictors in [[c for c in PHYS if c!=target],['log1p_Pop_Density','log1p_NRI_BUILDVALUE','SOVI_SCORE']]:
   sub=d[[target,*predictors]].dropna();r2=LinearRegression().fit(sub[predictors],sub[target]).score(sub[predictors],sub[target]);rows.append({'scope':'current_2287','measure':'joint_linear_explained_fraction','feature':target,'other_feature':';'.join(predictors),'n':len(sub),'value':r2})
 for a,b in itertools.permutations(PHYS,2):
  for degree in [1,2,3]:
   pred=np.full(len(d),np.nan)
   for train,test in GroupKFold(n_splits=5).split(d,groups=blocks.block_id):
    pf=PolynomialFeatures(degree=degree,include_bias=False);tr=pf.fit_transform(d[[a]].iloc[train]);te=pf.transform(d[[a]].iloc[test]);lm=LinearRegression().fit(tr,d[b].iloc[train]);pred[test]=lm.predict(te)
   rows.append({'scope':'spatial_5fold_block_prediction','measure':f'polynomial_degree_{degree}_out_of_fold_R2','feature':b,'other_feature':a,'n':len(d),'value':r2_score(d[b],pred),'interpretation':'descriptive nonlinear predictive overlap, not causal or source validation'})
  bins=pd.qcut(d[a],10,duplicates='drop')
  for g,sub in d.groupby(bins,observed=True):pairbins.append({'x':a,'y':b,'n':len(sub),'x_median':sub[a].median(),'y_median':sub[b].median(),'y_p10':sub[b].quantile(.1),'y_p90':sub[b].quantile(.9)})
 old=read(ROOT/'local_joint_feature_extraction_20261009/TRACT_FEATURE_CANDIDATES.csv');old=old.loc[old.index.intersection(master.index)]
 oldcols=old[['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share']].dropna()
 for a,b in itertools.combinations(PHYS,2):
  sub=oldcols[[a,b]];rows.append({'scope':'original_pilot_actual_values','measure':'Pearson','feature':a,'other_feature':b,'n':len(sub),'value':pearsonr(sub[a],sub[b]).statistic})
 z=StandardScaler().fit_transform(oldcols)
 for ix,c in enumerate(PHYS):
  lm=LinearRegression().fit(np.delete(z,ix,axis=1),z[:,ix]);r2=lm.score(np.delete(z,ix,axis=1),z[:,ix]);rows.append({'scope':'original_pilot_actual_values','measure':'VIF','feature':c,'n':len(z),'value':1/(1-r2)})
 save('BUILT_ENV_REDUNDANCY_METRICS.csv',rows);save('NONLINEAR_BINNED_RELATIONSHIPS.csv',pairbins)
 print('REDUNDANCY COMPLETE',len(rows),'metrics',flush=True)
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 if '--declare' in sys.argv:declare()
 if '--fit' in sys.argv:fit()
 if '--analyze' in sys.argv:analyze_runs();redundancy()
 if '--redundancy' in sys.argv:redundancy()
