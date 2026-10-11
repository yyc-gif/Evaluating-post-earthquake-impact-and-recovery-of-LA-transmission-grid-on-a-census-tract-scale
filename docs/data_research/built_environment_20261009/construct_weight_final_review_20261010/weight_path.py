"""Predeclared fixed-k construct/weight audit. Writes only this diagnostic package."""
import os
for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import ast,hashlib,itertools,json,platform,subprocess,sys,time
import numpy as np,pandas as pd,scipy,sklearn
from scipy.optimize import linear_sum_assignment
from scipy.stats import pearsonr,spearmanr
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score
from sklearn.linear_model import LinearRegression
from threadpoolctl import threadpool_limits
HERE=Path(__file__).resolve().parent
WT=HERE.parents[3]
if not str(WT).startswith('\\\\?\\'):WT=Path('\\\\?\\'+str(WT))
ROOT=WT/'docs/data_research/built_environment_20261009'
OUT=ROOT/'construct_weight_final_review_20261010'
AUD=ROOT/'built_env_validity_controlled_audit_20261010'
BASE=ROOT/'final_feature_validation_20261010'
PARENT='13d2b8978a74246873e76c6c860ab9604100de8b'
SEEDS=list(range(42,62));LAMBDAS=[0.,.25,.5,.75,1.]
DOMAINS=['recovery_service','grid','physical','social','loss_exposure']
EQ=np.full(5,.2);INH=np.array([2,4,2,1,2])/11
PARAMS=dict(n_clusters=4,n_init=100,max_iter=500,tol=1e-4,algorithm='lloyd')
PHYS=['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share']
GRID=['Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI']
PROFILE=['B_480_hr','T80','Init_Supply','SOVI_SCORE',*PHYS,'land_use_classified_land_coverage','all_use2014_age_coverage','NRI_BUILDVALUE','log1p_NRI_BUILDVALUE','ALR_NPCTL','EAL_SCORE',*GRID,'Pop_Density']
EXCLUDED=['06037189703','06037301601','06037301602','06037404600']
ORIGINAL=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def ahash(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def dump(n,x):(OUT/n).write_bytes(json.dumps(x,indent=2,allow_nan=False,default=lambda v:v.item() if isinstance(v,np.generic) else str(v)).encode())
def save(n,x):
 if not isinstance(x,pd.DataFrame):x=pd.DataFrame(x)
 (OUT/n).write_bytes(x.to_csv(index=False,lineterminator='\n',float_format='%.15g').encode())
def inputs():
 master=pd.read_csv(BASE/'FINAL_CANDIDATE_FEATURE_MATRIX.csv',dtype={'tract_id':str}).set_index('tract_id')
 d=master.loc[master.primary_complete_case].copy()
 assert len(master)==2291 and len(d)==2287 and d.index.is_unique
 assert set(master.index.difference(d.index))==set(EXCLUDED)
 assert master.loc[EXCLUDED,PHYS].isna().all().all()
 assert all(len(t)==11 and t.isdigit() for t in master.index)
 cc=pd.read_csv(BASE/'COMPLETE_CASE_FEATURE_MATRIX.csv',dtype={'tract_id':str}).tract_id
 assert np.array_equal(d.index,cc)
 blocks=pd.read_csv(BASE/'TRACT_SPATIAL_BLOCKS.csv',dtype={'tract_id':str}).set_index('tract_id').loc[d.index]
 blocks['block_id']=blocks.block.map(lambda t:':'.join(map(str,ast.literal_eval(t))))
 spec=json.loads((AUD/'CONTROLLED_COMPARISON_SPECIFICATION.json').read_text())
 cases={int(k):v for k,v in spec['spatial_deletions'].items()}
 assert sorted(cases)==SEEDS
 return master,d,blocks,cases
def name(be,lam):return f'{be}_L{round(lam*100):03d}'
def design(d,be,lam,mask=None):
 dom={'recovery_service':['B_480_hr','Init_Supply'],'grid':GRID,'physical':PHYS if be=='BE0' else PHYS[:2],'social':['SOVI_SCORE'],'loss_exposure':['log1p_NRI_BUILDVALUE','ALR_NPCTL']}
 cols=[c for v in dom.values() for c in v];weights=(1-lam)*EQ+lam*INH
 factors=np.array([np.sqrt(weights[i]/len(v)) for i,v in enumerate(dom.values()) for _ in v])
 raw=d[cols];assert np.isfinite(raw.to_numpy()).all()
 scaler=StandardScaler().fit(raw if mask is None else raw.loc[mask])
 return scaler.transform(raw)*factors,cols,dom,scaler,factors,weights
def align(y,p,mask):
 tab=np.zeros((4,4),int);np.add.at(tab,(y[mask],p[mask]),1)
 rr,cc=linear_sum_assignment(-tab);mp={int(a):int(b) for a,b in zip(rr,cc) if tab[a].sum()}
 a=np.full(len(p),-1,int)
 for r,c in mp.items():a[p==c]=r
 return mp,a,tab
def preservation(n):
 old=json.loads((AUD/'PRESERVATION_BEFORE.json').read_text());current={k:sha(ORIGINAL/k) for k in old['protected_files']}
 assert current==old['protected_files']
 index=subprocess.check_output(['git','-C',str(ORIGINAL),'ls-files','--stage','-z'])
 h=hashlib.sha256(index).hexdigest();assert h==old['logical_index_sha256']
 head=subprocess.check_output(['git','-C',str(ORIGINAL),'rev-parse','HEAD'],text=True).strip();assert head==old['current_head']
 count=len(subprocess.check_output(['git','-C',str(ORIGINAL),'diff','--cached','--name-only','-z']).split(b'\0'))-1;assert count==862
 dump(n,dict(protected_files=950,protected_payload_changes=0,original_head=head,staged_items=count,logical_index_sha256=h,original_index_unchanged=True))
def declare():
 master,d,blocks,cases=inputs();models=[]
 for be,lam in itertools.product(['BE0','BE1'],LAMBDAS):
  x,cols,dom,sc,f,w=design(d,be,lam)
  endpoint={('BE0',0.):'BE0',('BE0',1.):'D_INHERITED',('BE1',0.):'BE1_EQUAL',('BE1',1.):'BE1_INHERITED'}.get((be,lam))
  models.append(dict(name=name(be,lam),be=be,lambda_value=lam,endpoint_source=endpoint,domains=dom,features=cols,domain_weights=dict(zip(DOMAINS,w.tolist())),coordinate_factors=f.tolist(),matrix_sha256=ahash(x)))
 spec=dict(parent=PARENT,models=models,seeds=SEEDS,KMeans=PARAMS,cohort_n=2287,master_n=2291,excluded=EXCLUDED,sample_sha256=hashlib.sha256('\n'.join(d.index).encode()).hexdigest(),spatial_deletions=cases,distinct_deletion_sets=len({tuple(v['removed_blocks']) for v in cases.values()}),maximum_new_fits=240,reused_endpoint_runs=160,k_search=False,post_result_weight_selection=False,versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__))
 dump('PREDECLARED_RUN_SPECIFICATION.json',spec)
 # Criteria separate source/construct validity from optimizer/specification/spatial evidence.
 (OUT/'PREDECLARED_DECISION_RULE.md').write_bytes(b'''# Decision rule established before intermediate fits

Measurement: a high observed coverage or low VIF does not establish contemporary validity. Historical age can support a precisely historical descriptive construct; it cannot support contemporary all-use age, seismic fragility or causal recovery effects. ACS residential age is a different quantity.
Construct: the study concerns joint electricity recovery/community characteristics, not prediction of building damage. Age need not be primary merely because it is nonredundant. Choose its role from measurement meaning and the intended temporal scope, not partition preservation.
Weights: equal-domain weighting expresses equal conceptual budgets; inherited weighting favors the four-coordinate grid domain and gives social vulnerability 1/11. No interpolation point is selected for favorable empirical scores.
Numerical: report all 190 seed-pair ARIs per specification without a retrospective pass threshold.
Specification: report neighboring and endpoint transitions, raw contingencies, profiles and coordinate contributions. Abrupt or gradual refers to the observed four prescribed steps; no untested change point is inferred.
Spatial: use only the registered 20 seed/deletion cases (17 geographic sets), refit scalers on retained tracts and align labels from training overlap only. Report lower tails, purity and merging, not ARI as accuracy. No acceptance cutoff is chosen after observing results.
Interpretation checks: reference seed42 BE0 labels identify the highest-service-loss and lowest-service-loss large groups (each at least 10 percent of the cohort). Test their original-unit loss and SOVI contrast directions in 200 full and 200 spatial configurations, after specified overlap alignment. This 10-percent rule defines the descriptive large-group comparison; it is not a model-admission threshold. Enumerate all six class-pair physical-profile signs as well. Count cases descriptively, not as independent geographic replications. Recovery is an input and cannot validate the classes independently.
Minority group: identify the saved 34-member set by membership. Report retention, purity, Jaccard, destination distributions and training support separately. Matching does not guarantee the same scientific meaning.
Final: if meaningful continuous relationships survive but the four-class taxonomy depends strongly on reasonable weights, recommend a conditional/exploratory typology rather than unique stable archetypes. No automatic promotion follows any numerical result.
''')
 evidence=[]
 for n in ['BUILT_ENV_REDUNDANCY_DECISION.md','BUILT_ENV_ABLATION_RESULTS.csv','BUILT_ENV_SPATIAL_SENSITIVITY.csv','CLUSTER_DISTANCE_CONTRIBUTIONS.csv','WEIGHT_SCHEME_EFFECTS.csv','WITHIN_WEIGHT_SPECIFICATION_EFFECTS.csv','PHYSICAL_REDISTRIBUTION_EFFECTS.csv','CLASS_MEMBERSHIP_STABILITY.csv','SMALL_34_GROUP_SENSITIVITY.csv','MANUSCRIPT_IMPLICATIONS.md']:
  p=AUD/n
  if p.suffix=='.csv':
   frame=pd.read_csv(p);evidence.append(dict(file=n,sha256=sha(p),rows=len(frame),columns=';'.join(frame.columns),actual_payload=True))
  else:
   text=p.read_text(encoding='utf-8');evidence.append(dict(file=n,sha256=sha(p),rows=len(text.splitlines()),columns='full text read',actual_payload=True))
 save('EXISTING_EVIDENCE_AUDIT.csv',evidence)
 for m in models:
  if not m['endpoint_source']:continue
  p=AUD/'run_records'/f"{m['endpoint_source']}.npz";z=np.load(p);meta=json.loads(p.with_suffix('.json').read_text())
  assert meta['payload_sha256']==sha(p) and meta['spec']['matrix_sha256']==m['matrix_sha256']
  assert np.array_equal(z['tract_ids'],d.index) and np.array_equal(z['coordinate_factors'],m['coordinate_factors'])
  for seed in SEEDS:
   mask=~blocks.block_id.isin(cases[seed]['removed_blocks']);xs,_,_,ss,_,_=design(d,m['be'],m['lambda_value'],mask)
   assert np.array_equal(z[f'train_s{seed}'],mask) and np.array_equal(z[f'spatial_mean_s{seed}'],ss.mean_) and np.array_equal(z[f'spatial_scale_s{seed}'],ss.scale_)
  assert {r['seed'] for r in meta['rows'] if r['scope']=='full'}==set(SEEDS)
 preservation('PRESERVATION_BEFORE.json')
 print('PREDECLARED: 240 maximum new fits; 160 exact endpoint runs to reuse',flush=True)
def fit():
 spec=json.loads((OUT/'PREDECLARED_RUN_SPECIFICATION.json').read_text());_,d,blocks,cases=inputs();(OUT/'run_records').mkdir(exist_ok=True)
 started=time.perf_counter();new=reused=cached=0
 with threadpool_limits(limits=1):
  for m in spec['models']:
   cp=OUT/'run_records'/f"{m['name']}.npz";mpath=cp.with_suffix('.json');sig=hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()
   if cp.exists():
    meta=json.loads(mpath.read_text());assert meta['signature']==sig and meta['payload_sha256']==sha(cp);cached+=40;continue
   if m['endpoint_source']:
    src=AUD/'run_records'/f"{m['endpoint_source']}.npz";data=src.read_bytes();cp.write_bytes(data);old=json.loads(src.with_suffix('.json').read_text())
    rows=[dict(r,origin='EXACT_ENDPOINT_REUSE',original_origin=r['origin']) for r in old['rows']];reused+=40
    meta=dict(signature=sig,spec=m,rows=rows,payload_sha256=sha(cp),source_archive_sha256=sha(src),original_full_center_kind='see endpoint source; saved-label means where original fitted centers unavailable')
   else:
    x,cols,dom,sc,f,w=design(d,m['be'],m['lambda_value']);arrays=dict(tract_ids=np.asarray(d.index,dtype=str),feature_columns=np.asarray(cols,dtype=str),coordinate_factors=f,full_scaler_mean=sc.mean_,full_scaler_scale=sc.scale_,full_scaler_var=sc.var_);rows=[]
    for seed in SEEDS:
     t=time.perf_counter();km=KMeans(**PARAMS,random_state=seed).fit(x);new+=1
     arrays[f'full_s{seed}']=km.labels_;arrays[f'full_centers_s{seed}']=km.cluster_centers_
     rows.append(dict(scope='full',seed=seed,origin='NEW_INTERMEDIATE_FIT',inertia=km.inertia_,iterations=km.n_iter_,elapsed_s=time.perf_counter()-t,center_kind='actual KMeans centers'))
     mask=~blocks.block_id.isin(cases[seed]['removed_blocks']);xs,_,_,ss,_,_=design(d,m['be'],m['lambda_value'],mask)
     t=time.perf_counter();km=KMeans(**PARAMS,random_state=seed).fit(xs[mask]);new+=1
     arrays[f'train_s{seed}']=mask.to_numpy();arrays[f'spatial_s{seed}']=km.predict(xs);arrays[f'spatial_centers_s{seed}']=km.cluster_centers_
     arrays[f'spatial_mean_s{seed}']=ss.mean_;arrays[f'spatial_scale_s{seed}']=ss.scale_;arrays[f'spatial_var_s{seed}']=ss.var_
     rows.append(dict(scope='spatial',seed=seed,origin='NEW_INTERMEDIATE_FIT',inertia=km.inertia_,iterations=km.n_iter_,elapsed_s=time.perf_counter()-t,center_kind='actual KMeans centers'))
    np.savez_compressed(cp,**arrays);meta=dict(signature=sig,spec=m,rows=rows,payload_sha256=sha(cp))
   dump('run_records/'+mpath.name,meta)
   print('COMPLETE',m['name'],'new',new,'reused',reused,'seconds',round(time.perf_counter()-started,1),flush=True)
 assert new<=240
 dump('FIT_EXECUTION_RECORD.json' if not (OUT/'FIT_EXECUTION_RECORD.json').exists() else 'FIT_RESUME_RECORD.json',dict(new_fits=new,reused_endpoint_runs=reused,cached_runs=cached,maximum_new_fits=240,total_unique_runs=400,elapsed_s=time.perf_counter()-started,k_searches=0,simulations=0,GA_runs=0,GIS_extractions=0))
def class_rows(y,p,mask,context,domain='all'):
 mp,a,tab=align(y,p,mask);rows=[]
 for i in range(4):
  own=y==i;pred=p==mp[i] if i in mp else np.zeros(len(p),bool);inter=int((own&pred).sum());n=int(own.sum());pn=int(pred.sum())
  destinations=np.bincount(p[own],minlength=4);origin=np.bincount(y[pred],minlength=4)
  rows.append(dict(context,reference_class=i,prediction_class=mp.get(i,-1),baseline_n=n,predicted_n=pn,training_support_n=int((own&mask).sum()),intersection=inter,union=n+pn-inter,retention=inter/n,purity=inter/pn if pn else np.nan,jaccard=inter/(n+pn-inter),largest_destination_fraction=float(destinations.max()/n),destinations=json.dumps(destinations.tolist()),origins=json.dumps(origin.tolist())))
 return rows,a,mp,tab
def analyze():
 _,d,blocks,cases=inputs();models=json.loads((OUT/'PREDECLARED_RUN_SPECIFICATION.json').read_text())['models'];archives={m['name']:np.load(OUT/'run_records'/f"{m['name']}.npz") for m in models}
 ref=archives['BE0_L000']['full_s42'];targetclass=int(np.flatnonzero(np.bincount(ref)==34)[0]);target=ref==targetclass
 large=[i for i in range(4) if (ref==i).sum()>=.1*len(d)];means={i:d.loc[ref==i,'B_480_hr'].mean() for i in large};hi=max(means,key=means.get);lo=min(means,key=means.get)
 full=[];spatial=[];classes=[];profiles=[];cts=[];contrib=[];pairs=[];seedpairs=[];minor=[];interp=[];geog=[];predrows=[]
 std=d[PROFILE].std(ddof=0);allmask=np.ones(len(d),bool)
 for m in models:
  z=archives[m['name']];x,cols,dom,sc,f,w=design(d,m['be'],m['lambda_value']);dmap={c:k for k,v in dom.items() for c in v}
  total=((x-x.mean(axis=0))**2).sum(axis=0)
  for sa,sb in itertools.combinations(SEEDS,2):seedpairs.append(dict(model=m['name'],be=m['be'],lambda_value=m['lambda_value'],seed_a=sa,seed_b=sb,ARI=adjusted_rand_score(z[f'full_s{sa}'],z[f'full_s{sb}'])))
  for seed in SEEDS:
   y=z[f'full_s{seed}'];p=z[f'spatial_s{seed}'];mask=z[f'train_s{seed}'];refseed=archives['BE0_L000'][f'full_s{seed}'];ctx=dict(model=m['name'],be=m['be'],lambda_value=m['lambda_value'],seed=seed)
   rr,ra,rmp,tab=class_rows(ref,y,allmask,dict(ctx,comparison='BE0_seed42_to_full'));classes+=rr
   ss,pa,smp,stab=class_rows(y,p,mask,dict(ctx,comparison='own_full_to_spatial'));classes+=ss
   _,raseed,_,_=class_rows(refseed,y,allmask,ctx)
   full.append(dict(ctx,ARI_vs_BE0_seed42=adjusted_rand_score(ref,y),ARI_vs_BE0_same_seed=adjusted_rand_score(refseed,y),reassigned_vs_BE0_same_seed_n=int((raseed!=refseed).sum()),reassigned_vs_BE0_seed42_n=int((ra!=ref).sum()),class_sizes=json.dumps(np.bincount(y,minlength=4).tolist())))
   spatial.append(dict(ctx,ARI_all=adjusted_rand_score(y,p),ARI_training=adjusted_rand_score(y[mask],p[mask]),ARI_heldout=adjusted_rand_score(y[~mask],p[~mask]),n_training=int(mask.sum()),n_heldout=int((~mask).sum()),removed_blocks=';'.join(cases[seed]['removed_blocks']),class_sizes=json.dumps(np.bincount(p,minlength=4).tolist()),minimum_retention=min(r['retention'] for r in ss),minimum_purity=min(r['purity'] for r in ss if np.isfinite(r['purity'])),minimum_jaccard=min(r['jaccard'] for r in ss)))
   for context,t in [('BE0_seed42_full',tab),('spatial_training_match',stab),('spatial_all',np.array([[int(((y==i)&(p==j)).sum()) for j in range(4)] for i in range(4)]))]:
    for i,j in itertools.product(range(4),repeat=2):cts.append(dict(ctx,comparison=context,reference_class=i,prediction_class=j,n=int(t[i,j])))
   for scope,labels,mp in [('full',y,rmp),('spatial',p,{a:smp[b] for a,b in rmp.items() if b in smp})]:
    byref={}
    for a,b in mp.items():
     selection=labels==b;byref[a]=d.loc[selection,PROFILE].mean()
     for feature in PROFILE:
      v=d.loc[selection,feature];before=d.loc[ref==a,feature];kept=d.loc[(ref==a)&mask,feature]
      profiles.append(dict(ctx,scope=scope,BE0_seed42_class=a,raw_class=b,n=int(selection.sum()),population=float(d.loc[selection,'formal_population'].sum()),feature=feature,mean=v.mean(),median=v.median(),p10=v.quantile(.1),p90=v.quantile(.9),baseline_mean=before.mean(),raw_mean_change=v.mean()-before.mean(),standardized_mean_change=(v.mean()-before.mean())/std[feature],fixed_reference_retained_mean=kept.mean(),fixed_reference_deletion_mean_change=kept.mean()-before.mean(),reclassified_vs_retained_mean_change=v.mean()-kept.mean()))
     for block,g in blocks.groupby('block_id'):geog.append(dict(ctx,scope=scope,BE0_seed42_class=a,block_id=block,n=int(selection[d.index.get_indexer(g.index)].sum()),population=float(d.loc[g.index[selection[d.index.get_indexer(g.index)]],'formal_population'].sum())))
    if hi in byref and lo in byref:
     bv=byref[hi].B_480_hr-byref[lo].B_480_hr;sv=byref[hi].SOVI_SCORE-byref[lo].SOVI_SCORE
     interp.append(dict(ctx,scope=scope,finding='large_group_recovery_SOVI_contrast',reference_class_a=hi,reference_class_b=lo,loss_difference_hr=bv,SOVI_difference=sv,supports_loss_direction=bv>0,supports_SOVI_direction=sv<0,supports_joint_direction=(bv>0 and sv<0)))
    for a,b in itertools.combinations(sorted(byref),2):
     for feature in PHYS:
      original=d.loc[ref==a,feature].mean()-d.loc[ref==b,feature].mean();current=byref[a][feature]-byref[b][feature]
      interp.append(dict(ctx,scope=scope,finding='physical_profile_pair_direction',feature=feature,reference_class_a=a,reference_class_b=b,reference_difference=original,current_difference=current,standardized_current_difference=current/std[feature],supports_direction=np.sign(original)==np.sign(current)))
    tc=mp.get(targetclass,-1);sel=labels==tc if tc>=0 else np.zeros(len(d),bool);inter=int((target&sel).sum());pn=int(sel.sum());train_target=int((target&mask).sum())
    minor.append(dict(ctx,scope=scope,reference_target_n=34,reference_target_training_n=train_target,matched_raw_class=tc,predicted_n=pn,intersection=inter,retention=inter/34,purity=inter/pn if pn else np.nan,jaccard=inter/(34+pn-inter),original_target_destination_counts=json.dumps(np.bincount(labels[target],minlength=4).tolist()),matching_rule='BE0 seed42 full overlap then own-full spatial training-overlap map; heldout never used for spatial map'))
   between=np.array([sum((y==i).sum()*(x[y==i,j].mean()-x[:,j].mean())**2 for i in range(4)) for j in range(len(cols))])
   for j,c in enumerate(cols):contrib.append(dict(ctx,feature=c,domain=dmap[c],nominal_coordinate_weight=f[j]**2,total_SS=total[j],between_SS=between[j],within_SS=total[j]-between[j],between_fraction=between[j]/between.sum(),within_fraction=(total[j]-between[j])/(total-between).sum(),partition_R2=between[j]/total[j],denominator='sum over all weighted standardized coordinates; unweighted tracts'))
   if seed==42:
    for i,t in enumerate(d.index):predrows.append(dict(model=m['name'],be=m['be'],lambda_value=m['lambda_value'],tract_id=t,block_id=blocks.block_id.iloc[i],full_raw_class=int(y[i]),full_BE0_seed42_display=int(ra[i]),spatial_raw_class=int(p[i]),training=bool(mask[i])))
 # All weight pairs and neighbor contingency tables, matched within the same seed.
 for be in ['BE0','BE1']:
  for la,lb in itertools.combinations(LAMBDAS,2):
   for seed in SEEDS:
    a=archives[name(be,la)][f'full_s{seed}'];b=archives[name(be,lb)][f'full_s{seed}'];mp,al,tab=align(a,b,allmask)
    fractions=tab/tab.sum(axis=1,keepdims=True);entropy=-np.where(fractions>0,fractions*np.log(np.maximum(fractions,1e-300)),0).sum(axis=1)/np.log(4)
    pairs.append(dict(be=be,lambda_a=la,lambda_b=lb,seed=seed,neighbor=(lb-la==.25),ARI=adjusted_rand_score(a,b),reassigned_n=int((al!=a).sum()),reassigned_fraction=float((al!=a).mean()),weighted_row_split_entropy=float(np.average(entropy,weights=tab.sum(axis=1))),reference_class_max_destination_fractions=json.dumps(fractions.max(axis=1).tolist())))
    if lb-la==.25:
     for i,j in itertools.product(range(4),repeat=2):cts.append(dict(be=be,seed=seed,lambda_a=la,lambda_b=lb,comparison='neighbor_weight_full',reference_class=i,prediction_class=j,n=int(tab[i,j]),row_fraction=float(fractions[i,j]),column_fraction=float(tab[i,j]/tab[:,j].sum())))
 age=[]
 for lam,seed in itertools.product(LAMBDAS,SEEDS):
  a=archives[name('BE0',lam)][f'full_s{seed}'];b=archives[name('BE1',lam)][f'full_s{seed}'];mp,al,tab=align(a,b,allmask)
  for i,j in mp.items():
   for c in PROFILE:
    age.append(dict(lambda_value=lam,seed=seed,BE0_raw_class=i,BE1_matched_raw_class=j,feature=c,BE0_mean=d.loc[a==i,c].mean(),BE1_mean=d.loc[b==j,c].mean(),raw_mean_change=d.loc[b==j,c].mean()-d.loc[a==i,c].mean(),BE0_n=int((a==i).sum()),BE1_n=int((b==j).sum()),ARI=adjusted_rand_score(a,b),aligned_reassigned_n=int((al!=a).sum()),interpretation='age deletion and redistribution within same parent domain; fixed-coordinate control exists in parent audit'))
 save('WEIGHT_PATH_RESULTS.csv',full);save('WEIGHT_PATH_PAIRWISE_COMPARISONS.csv',pairs);save('WEIGHT_PATH_SPATIAL_STABILITY.csv',spatial)
 save('BE0_BE1_CONSTRUCT_COMPARISON.csv',age);save('CLASS_MEMBERSHIP_AND_MATCHING.csv',classes);save('RAW_CLASS_TRANSITIONS.csv',cts)
 save('CLASS_PROFILES_ORIGINAL_UNITS.csv',profiles);save('DOMAIN_DISTANCE_CONTRIBUTIONS.csv',contrib);save('CLASS_INTERPRETATION_ROBUSTNESS.csv',interp)
 save('MINORITY_34_GROUP_AUDIT.csv',minor);save('CLASS_GEOGRAPHIC_BLOCK_DISTRIBUTION.csv',geog);save('SEED42_TRACT_WEIGHT_PATH.csv',predrows);save('NUMERICAL_SEED_STABILITY.csv',seedpairs)
 # Independent verification of source decomposition and diagnosis of low grid separation.
 old=pd.read_csv(AUD/'CLUSTER_DISTANCE_CONTRIBUTIONS.csv');now=pd.DataFrame(contrib);check=now.loc[now.model=='BE0_L000'].merge(old.loc[old.model=='BE0'],on=['seed','feature','domain'])
 err=float((check.between_fraction-check.between_class_fraction).abs().max());assert err<1e-12
 dump('BETWEEN_CLASS_DECOMPOSITION_VERIFICATION.json',dict(max_source_absolute_error=err,definition='TSS=sum_i ||x_i-xbar||2; BSS=sum_c n_c||xbar_c-xbar||2; WSS=TSS-BSS; domain contribution=BSS_domain/BSS_all',BE0_mean_domain_contributions=now.loc[now.model=='BE0_L000'].groupby('domain').between_fraction.sum().div(20).to_dict(),small_group_raw_label_seed42=targetclass,large_group_reference_labels=dict(high_loss=hi,low_loss=lo)))
 grid=[]
 coords=design(d,'BE0',0.)[1];rawz=StandardScaler().fit_transform(d[coords]);others=[i for i,c in enumerate(coords) if c not in GRID]
 for c in GRID:
  vals=d[c].to_numpy();cor=[(o,pearsonr(vals,d[o])[0]) for o in coords if o not in GRID]
  reg=LinearRegression().fit(rawz[:,others],vals);top=max(cor,key=lambda t:abs(t[1]))
  grid.append(dict(feature=c,R2_from_other_domains_in_sample=reg.score(rawz[:,others],vals),largest_absolute_other_domain_correlation=abs(top[1]),strongest_other_feature=top[0],interpretation='linear descriptive association, not independent validation or causal redundancy'))
 save('GRID_DOMAIN_LOW_SEPARATION_DIAGNOSTICS.csv',grid)
 cont=[];B=d.B_480_hr;S=d.SOVI_SCORE
 for stat,fun in [('Pearson',pearsonr),('Spearman',spearmanr)]:cont.append(dict(measure=stat,n=len(d),value=fun(B,S)[0],definition='unweighted common tract cohort, cluster-independent descriptive relationship'))
 b=B>=B.quantile(.75);s=S>=S.quantile(.75)
 cont.append(dict(measure='upper_quartile_overlap',n=len(d),high_loss_n=int(b.sum()),high_SOVI_n=int(s.sum()),intersection=int((b&s).sum()),high_loss_not_high_SOVI_n=int((b&~s).sum()),high_SOVI_not_high_loss_n=int((s&~b).sum()),definition='sample 75th percentile with >= ties; descriptive only, not an acceptance threshold'))
 save('CONTINUOUS_RECOVERY_SOVI_EVIDENCE.csv',cont)
 summary=[]
 ff=pd.DataFrame(full);ss=pd.DataFrame(spatial);mm=pd.DataFrame(minor);ns=pd.DataFrame(seedpairs);cc=pd.DataFrame(contrib)
 for m in models:
  n=m['name'];f0=ff.loc[ff.model==n];s0=ss.loc[ss.model==n];mt=mm.loc[(mm.model==n)&(mm.scope=='spatial')];nu=ns.loc[ns.model==n];c0=cc.loc[cc.model==n]
  summary.append(dict(model=n,be=m['be'],lambda_value=m['lambda_value'],ARI_ref_median=f0.ARI_vs_BE0_same_seed.median(),reassigned_ref_median=f0.reassigned_vs_BE0_same_seed_n.median(),seed_ARI_median=nu.ARI.median(),seed_ARI_min=nu.ARI.min(),spatial_ARI_median=s0.ARI_all.median(),spatial_ARI_p05=s0.ARI_all.quantile(.05),spatial_ARI_min=s0.ARI_all.min(),target34_purity_min=mt.purity.min(),target34_retention_min=mt.retention.min(),target34_predicted_n_max=mt.predicted_n.max(),**{k+'_between_fraction':float(c0.loc[c0.domain==k].between_fraction.sum()/20) for k in DOMAINS}))
 save('MODEL_SUMMARY.csv',summary)
 print(pd.DataFrame(summary).to_string(index=False),flush=True)
 print('source decomposition max absolute error',err,flush=True)
if __name__=='__main__':
 if '--declare' in sys.argv:declare()
 if '--fit' in sys.argv:fit()
 if '--analyze' in sys.argv:analyze()
 if '--preserve' in sys.argv:preservation('PRESERVATION_AFTER.json')
