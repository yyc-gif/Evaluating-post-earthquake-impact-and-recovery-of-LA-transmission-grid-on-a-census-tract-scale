"""Additional summaries using saved labels only; no fitting or model selection."""
from weight_path import *

def main():
 _,d,blocks,cases=inputs();models=json.loads((OUT/'PREDECLARED_RUN_SPECIFICATION.json').read_text())['models']
 z={m['name']:np.load(OUT/'run_records'/f"{m['name']}.npz") for m in models};allmask=np.ones(len(d),bool)
 allpairs=[]
 for a,b in itertools.combinations(models,2):
  for seed in SEEDS:
   ya=z[a['name']][f'full_s{seed}'];yb=z[b['name']][f'full_s{seed}'];mp,aligned,tab=align(ya,yb,allmask)
   allpairs.append(dict(model_a=a['name'],model_b=b['name'],seed=seed,ARI=adjusted_rand_score(ya,yb),aligned_reassigned_n=int((aligned!=ya).sum())))
 save('ALL_SPECIFICATION_PAIRWISE_ARI.csv',allpairs)
 f=pd.read_csv(OUT/'WEIGHT_PATH_RESULTS.csv');p=pd.read_csv(OUT/'CLASS_PROFILES_ORIGINAL_UNITS.csv');s=pd.read_csv(OUT/'WEIGHT_PATH_SPATIAL_STABILITY.csv');m=pd.read_csv(OUT/'MINORITY_34_GROUP_AUDIT.csv');c=pd.read_csv(OUT/'DOMAIN_DISTANCE_CONTRIBUTIONS.csv');i=pd.read_csv(OUT/'CLASS_INTERPRETATION_ROBUSTNESS.csv');pairs=pd.read_csv(OUT/'WEIGHT_PATH_PAIRWISE_COMPARISONS.csv')
 steps=[]
 for (be,la,lb),g in pairs.loc[pairs.neighbor].groupby(['be','lambda_a','lambda_b']):
  steps.append(dict(be=be,lambda_a=la,lambda_b=lb,n_seeds=len(g),ARI_median=g.ARI.median(),ARI_min=g.ARI.min(),ARI_max=g.ARI.max(),reassigned_median=g.reassigned_n.median(),reassigned_min=g.reassigned_n.min(),reassigned_max=g.reassigned_n.max(),split_entropy_median=g.weighted_row_split_entropy.median()))
 save('NEIGHBOR_WEIGHT_STEP_SUMMARY.csv',steps)
 findings=[]
 for (model,scope),g in i.groupby(['model','scope']):
  large=g.loc[g.finding=='large_group_recovery_SOVI_contrast']
  findings.append(dict(model=model,scope=scope,finding='large_reference_group_service_loss_and_SOVI_directions',n_tested=len(large),supporting_n=int(large.supports_joint_direction.eq(True).sum()),contradicting_n=int((~large.supports_joint_direction.eq(True)).sum()),definition='matched highest-vs-lowest loss BE0 seed42 large groups; B difference>0 and SOVI difference<0'))
  for feature,sub in g.loc[g.finding=='physical_profile_pair_direction'].groupby('feature'):
   findings.append(dict(model=model,scope=scope,finding=feature+'_pairwise_class_mean_sign',n_tested=len(sub),supporting_n=int(sub.supports_direction.eq(True).sum()),contradicting_n=int((~sub.supports_direction.eq(True)).sum()),definition='all six original-unit reference class-pair mean signs, across20 seeds; direction only, not effect significance'))
 save('CLASS_INTERPRETATION_SUPPORT_COUNTS.csv',findings)
 drift=[]
 for model in f.model.unique():
  for scope in ['full','spatial']:
   for feature in PROFILE:
    gp=p.loc[(p.model==model)&(p.scope==scope)&(p.feature==feature)]
    for cls,g in gp.groupby('BE0_seed42_class'):
     drift.append(dict(model=model,scope=scope,reference_class=int(cls),feature=feature,raw_mean_change_median=g.raw_mean_change.median(),raw_mean_change_min=g.raw_mean_change.min(),raw_mean_change_max=g.raw_mean_change.max(),standardized_center_change_median=g.standardized_mean_change.median(),standardized_center_change_min=g.standardized_mean_change.min(),standardized_center_change_max=g.standardized_mean_change.max()))
 save('PROFILE_CENTER_SHIFT_SUMMARY.csv',drift)
 # Counts and population in actual original-unit profile rows, one row per class/run.
 counts=p.loc[p.feature=='B_480_hr',['model','be','lambda_value','seed','scope','BE0_seed42_class','raw_class','n','population']].copy()
 save('CLASS_COUNTS_AND_POPULATION.csv',counts)
 # Four seed42 reference classes' geographic footprint changes.
 geog=pd.read_csv(OUT/'CLASS_GEOGRAPHIC_BLOCK_DISTRIBUTION.csv');geo=[]
 for (model,scope,cid),gp in geog.groupby(['model','scope','BE0_seed42_class']):
  raw=gp.loc[gp.seed==42].set_index('block_id').n
  original=geog.loc[(geog.model=='BE0_L000')&(geog.scope=='full')&(geog.seed==42)&(geog.BE0_seed42_class==cid)].set_index('block_id').n
  ix=raw.index.union(original.index);a=raw.reindex(ix,fill_value=0);b=original.reindex(ix,fill_value=0)
  geo.append(dict(model=model,scope=scope,reference_class=cid,represented_blocks=int((a>0).sum()),original_represented_blocks=int((b>0).sum()),block_distribution_total_variation=float(.5*abs(a/a.sum()-b/b.sum()).sum()),definition='seed42 empirical20-km block-count probability profiles; not physical area or causal shift'))
 save('GEOGRAPHIC_CLASS_DISTRIBUTION_CHANGES.csv',geo)
 # Compare nominal budget against TSS and BSS; inspect within-class variation explicitly.
 rows=[]
 for (model,domain),g in c.groupby(['model','domain']):
  per=g.groupby('seed').agg(TSS=('total_SS','sum'),BSS=('between_SS','sum'),WSS=('within_SS','sum'),between_fraction=('between_fraction','sum'))
  rows.append(dict(model=model,domain=domain,nominal_domain_weight=g.loc[g.seed==42].nominal_coordinate_weight.sum(),between_fraction_mean=per.between_fraction.mean(),domain_variance_explained_mean=(per.BSS/per.TSS).mean(),within_domain_fraction_mean=(per.WSS/per.TSS).mean()))
 save('DOMAIN_SEPARATION_SUMMARY.csv',rows)
 # Explicit endpoint changes by class: retention, purity, split/merge structure.
 end=[];ct=[]
 for be in ['BE0','BE1']:
  for seed in SEEDS:
   a=z[name(be,0.)][f'full_s{seed}'];b=z[name(be,1.)][f'full_s{seed}'];rr,_,_,tab=class_rows(a,b,allmask,dict(be=be,seed=seed,comparison='equal_to_inherited'))
   end+=rr
   for ii,jj in itertools.product(range(4),repeat=2):ct.append(dict(be=be,seed=seed,reference_class=ii,prediction_class=jj,n=int(tab[ii,jj]),row_fraction=float(tab[ii,jj]/tab[ii].sum()),column_fraction=float(tab[ii,jj]/tab[:,jj].sum())))
 save('ENDPOINT_CLASS_CHANGES.csv',end);save('ENDPOINT_RAW_CROSSTABS.csv',ct)
 # Minority split trace independent of Hungarian assignment: always record the dominant destination.
 target=z['BE0_L000']['full_s42'];target=target==np.flatnonzero(np.bincount(target)==34)[0];dominant=[]
 for model in z:
  for seed in SEEDS:
   for scope in ['full','spatial']:
    labels=z[model][f'{scope}_s{seed}'];tab=np.bincount(labels[target],minlength=4);j=int(tab.argmax());pred=labels==j;inter=int(tab[j]);pn=int(pred.sum())
    dominant.append(dict(model=model,seed=seed,scope=scope,dominant_destination=j,intersection=inter,target_n=34,predicted_n=pn,retention=inter/34,purity=inter/pn,jaccard=inter/(34+pn-inter),target_training_n=int((target&z[model][f'train_s{seed}']).sum()),matching='dominant destination describes original membership; not a replacement for training-only spatial label matching'))
 save('MINORITY_DOMINANT_DESTINATION_TRACE.csv',dominant)
 impact=[]
 for be in ['BE0','BE1']:
  for seed in SEEDS:
   a=z[name(be,0.)][f'full_s{seed}'];b=z[name(be,1.)][f'full_s{seed}'];_,al,_=align(a,b,allmask)
   impact.append(dict(be=be,seed=seed,ARI_all=adjusted_rand_score(a,b),ARI_excluding_original34=adjusted_rand_score(a[~target],b[~target]),reassigned_original34_n=int(((al!=a)&target).sum()),reassigned_other2253_n=int(((al!=a)&~target).sum()),definition='exclude original34 only from descriptive comparison; fitted partitions remain unchanged'))
 save('MINORITY_VS_LARGE_PARTITION_CHANGE.csv',impact)
 print(pd.DataFrame(steps).to_string(index=False))
 print(pd.DataFrame(findings).query("finding=='large_reference_group_service_loss_and_SOVI_directions'").to_string(index=False))
if __name__=='__main__':main()
