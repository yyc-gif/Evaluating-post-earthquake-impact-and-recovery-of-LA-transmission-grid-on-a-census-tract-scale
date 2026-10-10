"""Fixed k=4 spatial deletions only; baseline labels are read, never refitted."""
from pathlib import Path
import os,json,hashlib,subprocess,ast,time,sys,platform,itertools
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
os.environ.setdefault('LOKY_MAX_CPU_COUNT','1')
import numpy as np
import pandas as pd
import scipy,sklearn
from scipy.optimize import linear_sum_assignment
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
ROOT=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
BASE=ROOT/'docs/data_research/built_environment_20261009/final_feature_validation_20261010'
OUT=ROOT/'docs/data_research/built_environment_20261009/spatial_k4_validation_20261010'
PARENT='50df10481815f3dd94c46dc9443f93cfdb1c5014'
SEEDS=list(range(42,62))
MODELS=['D','EAL']
DOMAINS={'recovery_service':['B_480_hr','Init_Supply'],'grid':['Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI'],'physical':['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share'],'social':['SOVI_SCORE'],'loss_exposure':['log1p_NRI_BUILDVALUE','ALR_NPCTL']}
PROFILES=['B_480_hr','Init_Supply','SOVI_SCORE','land_use_entropy','land_use_classified_land_coverage','building_footprint_coverage','all_use2014_pre1970_area_share','all_use2014_age_coverage','NRI_BUILDVALUE','log1p_NRI_BUILDVALUE','ALR_NPCTL','EAL_SCORE']+DOMAINS['grid']+['T80','Pop_Density','housing_5plus_share']
UNRESOLVED=['06037189703','06037301601','06037301602','06037404600']
PARAMS=dict(n_clusters=4,n_init=100,max_iter=500,tol=1e-4,algorithm='lloyd')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*args,env=None):return subprocess.check_output(['git','-C',str(ROOT),*args],env=env)
def clean(v):
 if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [clean(x) for x in v]
 if isinstance(v,np.generic):v=v.item()
 if isinstance(v,float) and not np.isfinite(v):return None
 return v
def dump(n,v): (OUT/n).write_text(json.dumps(clean(v),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def save(n,rows):pd.DataFrame(rows).to_csv(OUT/n,index=False,float_format='%.15g',lineterminator='\n',na_rep='')
def frame(n):
 f=pd.read_csv(BASE/n,dtype={'tract_id':str})
 assert f.tract_id.str.fullmatch(r'\d{11}').all() and f.tract_id.is_unique
 return f.set_index('tract_id')
def source_identity(p):
 data=p.read_bytes();assert not data.startswith(b'version https://git-lfs.github.com/spec/v1')
 rel=p.relative_to(ROOT).as_posix();blob=git('show',PARENT+':'+rel)
 if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
  lines=blob.decode().splitlines();assert sha(p)==lines[1].split(':')[-1] and len(data)==int(lines[2].split()[1]);kind='LFS_ACTUAL_BYTES'
 else:assert blob==data;kind='GIT_BLOB_EXACT'
 return dict(file=rel,sha256=sha(p),bytes=len(data),commit=PARENT,verified_as=kind)
def model_spec(model):
 dom={k:list(v) for k,v in DOMAINS.items()}
 if model=='EAL':dom['loss_exposure']=['EAL_SCORE']
 cols=[c for v in dom.values() for c in v];factors=np.array([np.sqrt(.2/len(v)) for v in dom.values() for c in v])
 return dom,cols,factors
def initialize():
 OUT.mkdir(exist_ok=True);(OUT/'run_records').mkdir(exist_ok=True);(OUT/'original_state').mkdir(exist_ok=True)
 (OUT/'.gitignore').write_text('original_state/\npublish_state/\n__pycache__/\n.pytest_cache/\n!SMALL_CLUSTER_34_AUDIT.csv\n',encoding='utf-8',newline='\n')
 (OUT/'.gitattributes').write_text('*.md text eol=lf\n*.py text eol=lf\n*.json text eol=lf\n*.txt text eol=lf\n',encoding='utf-8',newline='\n')
 state=OUT/'original_state'
 if not (OUT/'PRESERVATION_BASELINE.json').exists():
  (state/'index.bin').write_bytes(git('ls-files','--stage','-z'))
  (state/'status.bin').write_bytes(git('status','--porcelain=v1','-z'))
  prior=json.loads((BASE/'PRESERVATION_BASELINE.json').read_text())
  assert all(sha(ROOT/p)==v for p,v in prior['protected_files'].items())
  source=json.loads((BASE/'INPUT_HASHES.json').read_text())
  dump('PRESERVATION_BASELINE.json',dict(head=git('rev-parse','HEAD').decode().strip(),branch=git('branch','--show-current').decode().strip(),protected_files=prior['protected_files'],source_hash_record=source,staged_count=len(git('diff','--cached','--name-only').splitlines())))
 names=['STAGE7_FEATURE_DECISION_PACKET.md','FEATURE_MATRIX_QA.json','CONTROLLED_EXPERIMENT_SPECIFICATION.json','controlled_clustering.py','summarize_and_verify.py','FINAL_CANDIDATE_FEATURE_MATRIX.csv','COMPLETE_CASE_FEATURE_MATRIX.csv','CONTROLLED_CLUSTERING_COMPARISON.csv','SPATIAL_BLOCK_STABILITY.csv','TRACT_SPATIAL_BLOCKS.csv','CLUSTER_EXECUTION_QA.json']
 names += [f'run_records/{m}__equal_five_domains.{ext}' for m in MODELS for ext in ['npz','json']]
 records=[source_identity(BASE/n) for n in names]
 f=frame('FINAL_CANDIDATE_FEATURE_MATRIX.csv');d=f.loc[f.primary_complete_case].copy();cc=frame('COMPLETE_CASE_FEATURE_MATRIX.csv')
 assert len(f)==2291 and len(d)==2287 and d.index.equals(cc.index)
 assert list(f.index[~f.primary_complete_case])==UNRESOLVED
 assert f.loc[UNRESOLVED,['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share']].isna().all().all()
 blocks=frame('TRACT_SPATIAL_BLOCKS.csv').reindex(d.index);assert blocks.notna().all().all()
 blocks['block_id']=blocks.block.map(lambda s:':'.join(map(str,ast.literal_eval(s))))
 sp=pd.read_csv(BASE/'SPATIAL_BLOCK_STABILITY.csv');sets={}
 for seed,g in sp.groupby('seed'):
  assert g.removed_blocks.nunique()==1 and g.n_training.nunique()==1 and g.n_heldout.nunique()==1
  removed=sorted(g.removed_blocks.iloc[0].split(';'));mask=~blocks.block_id.isin(removed)
  assert mask.sum()==g.n_training.iloc[0] and (~mask).sum()==g.n_heldout.iloc[0]
  sets[int(seed)]=dict(removed_blocks=removed,n_training=int(mask.sum()),n_heldout=int((~mask).sum()))
 assert sorted(sets)==SEEDS and blocks.block_id.nunique()==15
 comparison=pd.read_csv(BASE/'CONTROLLED_CLUSTERING_COMPARISON.csv');baselines={};checks=[]
 for model in MODELS:
  dom,cols,w=model_spec(model);scaler=StandardScaler().fit(d[cols]);x=scaler.transform(d[cols])*w
  mh=hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest();sh=hashlib.sha256('\n'.join(d.index).encode()).hexdigest()
  meta=json.loads((BASE/f'run_records/{model}__equal_five_domains.json').read_text());assert meta['matrix_sha256']==mh
  z=np.load(BASE/f'run_records/{model}__equal_five_domains.npz');labs={}
  for seed in SEEDS:
   row=comparison.loc[comparison.model.eq(model+'__equal_five_domains')&comparison.seed.eq(seed)&comparison.k.eq(4)].iloc[0]
   assert row.matrix_sha256==mh and row.sample_sha256==sh and row.selected_k==4 and row.n_init==100
   y=z[f's{seed}_k4'];assert len(y)==2287 and np.array_equal(np.unique(y),np.arange(4));labs[seed]=y
   center=np.vstack([x[y==c].mean(axis=0) for c in range(4)]);inertia=((x-center[y])**2).sum();assert inertia<=row.inertia+1e-8
   # At tolerance stopping sklearn may reassign labels without recomputing centers.
   # Original centers were not saved; label means are descriptive centers only.
   checks.append(dict(model=model,seed=seed,k=4,n=2287,matrix_sha256=mh,sample_sha256=sh,saved_algorithm_inertia=float(row.inertia),label_mean_center_inertia=float(inertia),saved_minus_label_mean_inertia=float(row.inertia-inertia),baseline_sizes=np.bincount(y).tolist(),full_sample_KMeans_refit=False,baseline_margin_definition='distances to saved-label member means in full baseline weighted coordinates; original algorithm centers unavailable'))
  baselines[model]=(labs,scaler,w,x,mh,sh,cols,dom)
 oldversions=json.loads((BASE/'CLUSTER_EXECUTION_QA.json').read_text())['versions']
 versions=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,platform=platform.platform())
 assert all(versions[k]==v for k,v in oldversions.items())
 small=np.flatnonzero(np.bincount(baselines['D'][0][42])==34);assert len(small)==1
 small_ids=d.index[baselines['D'][0][42]==small[0]].tolist()
 dump('INPUT_AND_BASELINE_QA.json',dict(status='VERIFIED_ACTUAL_BYTES',baseline_commit=PARENT,source_files=records,residential_n=2291,complete_n=2287,complete_sample_sha256=checks[0]['sample_sha256'],unresolved_residential=UNRESOLVED,unresolved_values_and_labels_not_imputed=True,geoids_joined_explicitly=True,full_baseline_labels_reused=checks,spatial_deletion_sets=sets,unique_geographic_deletion_sets=len({tuple(v['removed_blocks']) for v in sets.values()}),versions=versions,original_versions=oldversions,baseline_matrix_reconstructed_only_for_identity_and_distance_checks=True,small_D_seed42_raw_label=int(small[0]),small_D_seed42_members=small_ids,models=MODELS,k=4,total_allowed_new_fits=40,KMeans=PARAMS,no_k_search=True,no_new_sources=True,domain_budget={k:.2 for k in DOMAINS}))
 return f,d,blocks,sets,baselines
def fit_runs(d,blocks,sets,baselines):
 new=0;reuse=0;start=time.perf_counter()
 with threadpool_limits(limits=1):
  for model in MODELS:
   labs,fullsc,w,x,mh,sh,cols,dom=baselines[model]
   for seed in SEEDS:
    cp=OUT/f'run_records/{model}_s{seed}.npz';mp=cp.with_suffix('.json');spec=dict(model=model,seed=seed,baseline_commit=PARENT,source_matrix_sha256=mh,sample_sha256=sh,removed_blocks=sets[seed]['removed_blocks'],feature_columns=cols,coordinate_factors=w.tolist(),domains=dom,KMeans={**PARAMS,'random_state':seed})
    mask=~blocks.block_id.isin(sets[seed]['removed_blocks']);training_ids=d.index[mask].tolist();spec['training_sample_sha256']=hashlib.sha256('\n'.join(training_ids).encode()).hexdigest();spec['input_files']={r['file']:r['sha256'] for r in json.loads((OUT/'INPUT_AND_BASELINE_QA.json').read_text())['source_files']}
    if cp.exists() and mp.exists():
     old=json.loads(mp.read_text());assert old['spec']==spec;z=np.load(cp);assert z['tract_ids'].tolist()==d.index.tolist() and z['train_mask'].tolist()==mask.tolist();reuse+=1;print('REUSED',model,seed,flush=True);continue
    sc=StandardScaler().fit(d.loc[mask,cols]);trainx=sc.transform(d.loc[mask,cols])*w;clock=time.perf_counter();km=KMeans(**PARAMS,random_state=seed).fit(trainx);new+=1
    fullx=sc.transform(d[cols])*w;pred=km.predict(fullx)
    np.savez_compressed(cp,tract_ids=np.array(d.index,dtype=str),train_mask=mask.to_numpy(),raw_prediction=pred,scaler_mean=sc.mean_,scaler_scale=sc.scale_,scaler_var=sc.var_,coordinate_factors=w,cluster_centers=km.cluster_centers_,feature_columns=np.array(cols,dtype=str),baseline_labels=labs[seed])
    record={'spec':spec,'inertia':float(km.inertia_),'iterations':int(km.n_iter_),'fit_elapsed_s':time.perf_counter()-clock,'n_training':int(mask.sum()),'n_heldout':int((~mask).sum()),'training_sizes':np.bincount(pred[mask],minlength=4).tolist(),'full_prediction_sizes':np.bincount(pred,minlength=4).tolist(),'versions':json.loads((OUT/'INPUT_AND_BASELINE_QA.json').read_text())['versions']}
    mp.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n');print('FIT',new,'/40',model,seed,'train',mask.sum(),'seconds',round(record['fit_elapsed_s'],2),flush=True)
 assert new+reuse==40
 dump('FIT_EXECUTION_RECORD.json',dict(new_fits_this_invocation=new,reused_complete_checkpoints=reuse,total_unique_fits=40,full_sample_baseline_refits=0,k_search_fits=0,elapsed_s=time.perf_counter()-start))
def mapping(y,p,mask):
 table=np.zeros((4,4),dtype=int);np.add.at(table,(y[mask],p[mask]),1)
 supported=np.flatnonzero(table.sum(axis=1)>0);r,c=linear_sum_assignment(-table[supported]);m={int(supported[i]):int(j) for i,j in zip(r,c)}
 return m,table
def stats(v):
 return dict(observed_n=int(v.notna().sum()),mean=v.mean(),median=v.median(),p10=v.quantile(.1),p90=v.quantile(.9),zero_fraction=(v.dropna()==0).mean())
def summarize(d,blocks,sets,baselines):
 runs=[];matching=[];cross=[];predictions=[];profiles=[];smallrows=[];reversals=[];centers=[];baseline_profiles=[]
 q=json.loads((OUT/'INPUT_AND_BASELINE_QA.json').read_text());smallset=set(q['small_D_seed42_members']);rawstd=d[PROFILES].std(ddof=0);rawmeans=d[PROFILES].mean()
 for model in MODELS:
  labs,fullsc,w,fullx,mh,sh,cols,dom=baselines[model];display=labs[42];smid=int(np.argmin(np.bincount(display)));smset=set(d.index[display==smid]);displaycounts=np.bincount(display)
  for cid in range(4):
   for field in PROFILES:baseline_profiles.append(dict(model=model,display_seed=42,display_cluster=cid+1,n_members=int(displaycounts[cid]),feature=field,**stats(d.loc[display==cid,field])))
  for seed in SEEDS:
   z=np.load(OUT/f'run_records/{model}_s{seed}.npz');meta=json.loads((OUT/f'run_records/{model}_s{seed}.json').read_text());ids=pd.Index(z['tract_ids']);assert ids.equals(d.index)
   y=z['baseline_labels'];p=z['raw_prediction'];mask=z['train_mask'];mp,traincross=mapping(y,p,mask)
   inv={v:k for k,v in mp.items()};aligned=np.array([inv.get(int(a),-1) for a in p]);displaymap,_=mapping(display,y,np.ones(len(y),dtype=bool));seedtodisplay={v:k for k,v in displaymap.items()}
   dist=((fullx[:,None,:]-np.vstack([fullx[y==c].mean(axis=0) for c in range(4)])[None,:,:])**2).sum(axis=2);ordered=np.sort(dist,axis=1);margin=(ordered[:,1]-ordered[:,0])/np.maximum(ordered[:,1],np.finfo(float).tiny);changed=aligned!=y
   runs.append(dict(model=model,seed=seed,k=4,n_training=int(mask.sum()),n_heldout=int((~mask).sum()),removed_blocks=';'.join(sets[seed]['removed_blocks']),full_ARI=adjusted_rand_score(y,p),training_ARI=adjusted_rand_score(y[mask],p[mask]),heldout_ARI=adjusted_rand_score(y[~mask],p[~mask]),inertia=meta['inertia'],iterations=meta['iterations'],fit_elapsed_s=meta['fit_elapsed_s'],training_cluster_sizes=';'.join(map(str,meta['training_sizes'])),full_cluster_sizes=';'.join(map(str,meta['full_prediction_sizes'])),no_training_support_baseline_classes=';'.join(str(i+1) for i in range(4) if i not in mp),aligned_changed_n=int(changed.sum()),aligned_changed_fraction=float(changed.mean()),baseline_margin_median_changed=float(np.median(margin[changed])) if changed.any() else np.nan,baseline_margin_median_unchanged=float(np.median(margin[~changed])) if (~changed).any() else np.nan,changed_n_in_lowest_margin_quartile=int((changed&(margin<=np.quantile(margin,.25))).sum()),changed_n_in_highest_margin_quartile=int((changed&(margin>=np.quantile(margin,.75))).sum())))
   for i,key in enumerate(d.index):predictions.append(dict(model=model,seed=seed,tract_id=key,block_id=blocks.loc[key,'block_id'],training_member=bool(mask[i]),baseline_seed_cluster=int(y[i])+1,baseline_display_seed42_cluster=seedtodisplay[int(y[i])]+1,raw_prediction_cluster=int(p[i])+1,aligned_baseline_seed_cluster=int(aligned[i])+1 if aligned[i]>=0 else None,aligned_display_seed42_cluster=seedtodisplay[int(aligned[i])]+1 if aligned[i]>=0 else None,changed_relative_to_own_seed_baseline=bool(changed[i]),baseline_distance_margin=float(margin[i]),D34_member=key in smallset,model_seed42_smallest_group_member=key in smset))
   for scope,scope_mask in [('training',mask),('heldout',~mask),('full',np.ones(len(y),dtype=bool))]:
    ct=np.zeros((4,4),int);np.add.at(ct,(y[scope_mask],p[scope_mask]),1)
    for a,b in itertools.product(range(4),repeat=2):cross.append(dict(model=model,seed=seed,scope=scope,baseline_seed_cluster=a+1,prediction_raw_cluster=b+1,n=int(ct[a,b]),row_fraction=ct[a,b]/ct[a].sum() if ct[a].sum() else np.nan,column_fraction=ct[a,b]/ct[:,b].sum() if ct[:,b].sum() else np.nan,training_selected_match=mp.get(a)==b))
    for a in range(4):
     base=(y==a)&scope_mask;bm=int(base.sum());b=mp.get(a);pr=(p==b)&scope_mask if b is not None else np.zeros(len(y),bool);pn=int(pr.sum());inter=int((base&pr).sum());union=bm+pn-inter
     flows=[(int(ct[a,j]),j) for j in range(4) if j!=b];flow=max(flows) if flows else (0,-1);inflows=[(int(ct[i,b]),i) for i in range(4) if i!=a] if b is not None else [];incoming=max(inflows) if inflows else (0,-1)
     matching.append(dict(model=model,seed=seed,scope=scope,baseline_seed_cluster=a+1,display_seed42_cluster=seedtodisplay[a]+1,matched_prediction_raw_cluster=b+1 if b is not None else None,training_baseline_n=int(((y==a)&mask).sum()),training_support='SUPPORTED' if b is not None else 'NO_TRAINING_SUPPORT',baseline_n=bm,predicted_n=pn if b is not None else None,intersection=inter if b is not None else None,union=union if b is not None else None,retention=inter/bm if bm and b is not None else np.nan,purity=inter/pn if pn and b is not None else np.nan,jaccard=inter/union if union and b is not None else np.nan,major_outflow_prediction_raw_cluster=flow[1]+1 if flow[0] else None,major_outflow_n=flow[0],major_inflow_baseline_seed_cluster=incoming[1]+1 if incoming[0] else None,major_inflow_n=incoming[0],positive_destination_count=int((ct[a]>0).sum()),positive_source_count=int((ct[:,b]>0).sum()) if b is not None else None,majority_of_baseline_outside_match=(inter<bm/2) if bm and b is not None else None,majority_of_prediction_from_other_classes=(inter<pn/2) if pn and b is not None else None))
   for a in range(4):
    b=mp.get(a);orig=(y==a);fixed=orig&mask;fullpred=p==b if b is not None else np.zeros(len(y),bool);trainpred=fullpred&mask
    for field in PROFILES:
     base=stats(d.loc[orig,field]);fixedstat=stats(d.loc[fixed,field]);fullstat=stats(d.loc[fullpred,field]) if b is not None else stats(d.loc[np.zeros(len(y),bool),field]);trstat=stats(d.loc[trainpred,field])
     for group,st in [('fixed_original_members_retained_training',fixedstat),('reclassified_matched_full_population',fullstat),('reclassified_matched_training_population',trstat)]:
      change=st['mean']-base['mean'];profiles.append(dict(model=model,seed=seed,baseline_seed_cluster=a+1,display_seed42_cluster=seedtodisplay[a]+1,training_support='SUPPORTED' if b is not None else 'NO_TRAINING_SUPPORT',profile_population=group,feature=field,baseline_n=int(orig.sum()),profile_n=int(fixed.sum()) if group.startswith('fixed') else int(fullpred.sum()) if group.endswith('full_population') else int(trainpred.sum()),baseline_mean=base['mean'],baseline_median=base['median'],baseline_p10=base['p10'],baseline_p90=base['p90'],baseline_zero_fraction=base['zero_fraction'],**st,mean_change_raw_units=change,mean_change_standardized_full_cohort=change/rawstd[field] if rawstd[field]>0 else np.nan,fixed_members_deletion_mean_change=fixedstat['mean']-base['mean'],training_reclassification_mean_change=trstat['mean']-fixedstat['mean']))
    if b is not None:
     basecenter=fullx[orig].mean(axis=0);postcenter=fullx[fullpred].mean(axis=0);fixedcenter=fullx[fixed].mean(axis=0)
     centers.append(dict(model=model,seed=seed,baseline_seed_cluster=a+1,display_seed42_cluster=seedtodisplay[a]+1,full_membership_weighted_center_shift=float(np.linalg.norm(postcenter-basecenter)),fixed_member_deletion_weighted_center_shift=float(np.linalg.norm(fixedcenter-basecenter)),standardization='full baseline StandardScaler and fixed sqrt-domain weights; excludes changing train-scaler coordinate system'))
   for a,c in itertools.combinations(range(4),2):
    if a not in mp or c not in mp:continue
    for field in PROFILES:
     before=d.loc[y==a,field].mean()-d.loc[y==c,field].mean();after=d.loc[p==mp[a],field].mean()-d.loc[p==mp[c],field].mean()
     da,dc=seedtodisplay[a]+1,seedtodisplay[c]+1
     if da>dc:da,dc=dc,da;before,after=-before,-after
     reversals.append(dict(model=model,seed=seed,display_class_a=da,display_class_b=dc,feature=field,baseline_mean_difference=before,post_mean_difference=after,baseline_difference_standardized=before/rawstd[field],post_difference_standardized=after/rawstd[field],direction_reversed=bool(before*after<0),both_supported=True))
   for target,targetids in [('D_SEED42_34',smallset),('MODEL_SEED42_SMALLEST',smset)]:
    member=d.index.isin(targetids);basecount=np.bincount(y[member],minlength=4);a=int(np.argmax(basecount));b=mp.get(a);pr=p==b if b is not None else np.zeros(len(y),bool);inter=int((member&pr).sum());pn=int(pr.sum());bc={block:int((member&(blocks.block_id.to_numpy()==block)).sum()) for block in sets[seed]['removed_blocks']}
    smallrows.append(dict(model=model,seed=seed,target=target,reference_seed42_model='D' if target=='D_SEED42_34' else model,target_original_n=int(member.sum()),own_seed_dominant_baseline_cluster=a+1,own_seed_target_in_dominant_class=int(basecount[a]),training_target_n=int((member&mask).sum()),heldout_target_n=int((member&~mask).sum()),dominant_baseline_training_n=int(((y==a)&mask).sum()),training_support='SUPPORTED' if b is not None else 'NO_TRAINING_SUPPORT',matched_raw_prediction_cluster=b+1 if b is not None else None,prediction_n=pn if b is not None else None,original_members_in_match=inter if b is not None else None,original_member_retention=inter/member.sum() if b is not None else np.nan,prediction_target_purity=inter/pn if pn and b is not None else np.nan,new_other_members=pn-inter if b is not None else None,original_members_by_raw_prediction=json.dumps({str(j+1):int(((p==j)&member).sum()) for j in range(4)}),removed_blocks=';'.join(sets[seed]['removed_blocks']),target_members_removed_by_block=json.dumps(bc),majority_of_target_merged_elsewhere=(inter<member.sum()/2) if b is not None else None))
 save('SPATIAL_K4_RUNS.csv',runs);save('SPATIAL_K4_TRACT_PREDICTIONS.csv',predictions);save('SPATIAL_K4_CLUSTER_MATCHING.csv',matching);save('SPATIAL_K4_CROSSTABS.csv',cross);save('SPATIAL_K4_PROFILE_STABILITY.csv',profiles);save('SMALL_CLUSTER_34_AUDIT.csv',smallrows);save('SPATIAL_K4_CENTER_SHIFTS.csv',centers);save('SPATIAL_K4_PROFILE_DIRECTION_COMPARISONS.csv',reversals);save('BASELINE_SEED42_PROFILES.csv',baseline_profiles)
 overlap=len(smallset&set(d.index[baselines['EAL'][0][42]==np.argmin(np.bincount(baselines['EAL'][0][42]))]))
 dump('SMALL_GROUP_BASELINE_IDENTITY.json',dict(D_seed42_sizes=np.bincount(baselines['D'][0][42]).tolist(),EAL_seed42_sizes=np.bincount(baselines['EAL'][0][42]).tolist(),D34_members=sorted(smallset),EAL_smallest_members=sorted(set(d.index[baselines['EAL'][0][42]==np.argmin(np.bincount(baselines['EAL'][0][42]))])),intersection_D34_EAL_smallest=overlap))
 print('SUMMARIZED',len(runs),'fits',len(predictions),'tract predictions',flush=True)
def run():
 f,d,blocks,sets,baselines=initialize();fit_runs(d,blocks,sets,baselines);summarize(d,blocks,sets,baselines)
if __name__=='__main__':run()
