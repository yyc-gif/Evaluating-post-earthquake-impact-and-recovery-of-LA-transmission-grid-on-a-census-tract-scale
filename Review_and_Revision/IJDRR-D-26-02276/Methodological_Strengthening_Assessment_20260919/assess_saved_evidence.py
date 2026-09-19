"""Read-only analysis of frozen R26; no GA, physical sampling, or pipeline execution."""
from pathlib import Path
import ast
import hashlib
import json
import math
import heapq
from dataclasses import dataclass
from typing import Sequence
import numpy as np
import pandas as pd

ROOT = Path('R:/Review_and_Revision/IJDRR-D-26-02276')
OUT = Path(__file__).resolve().parent
R26 = ROOT / '26_GA_Reproducibility_and_Revised_Paired_Pilot_20260919'
R23 = ROOT / '23_R1_310_Scheduling_Input_Readiness_20260916'
R10 = ROOT / '10_SCE_ServiceLayer_Architecture_20260914'
def read(path):
    return pd.read_csv(path, dtype={'tract_id':str, 'R1_station_id':str,'station_id':str,'yard_id':str},float_precision='round_trip')
def write(df,name):
    df.to_csv(OUT/name,index=False,float_format='%.17g',lineterminator='\n')
def wm(v,w):
    v=np.asarray(v,float);w=np.asarray(w,float);ok=np.isfinite(v)&np.isfinite(w)&(w>0)
    return float(np.average(v[ok],weights=w[ok])) if ok.any() else np.nan
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source_files=list(R26.glob('*')); before={p.name:sha(p) for p in source_files if p.is_file()}

# Extract only the frozen surrogate definitions: never import/execute the runner main.
tree=ast.parse((R26/'run_revised_paired_pilot.py').read_text(encoding='utf-8'))
allowed={'SurrogateResult','SurrogateDecoder','expand_c57'}
ns=globals().copy();ns['TMAX_HR']=504.0
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in allowed],type_ignores=[]),'<frozen_surrogate_only>','exec'),ns)
prob=read(R26/'D302_2PC50_DAMAGE_PROBABILITIES.csv');ids=prob.R1_station_id.tolist()
priority=read(R23/'R1_ARCHB_PRIORITY_COMPONENTS.csv').set_index('R1_station_id').loc[ids]
base=read(R23/'R1_BASE_TO_TASK_TRAVEL_HR.csv').set_index('yard_id').loc[:,ids]
task=read(R23/'R1_TASK_TO_TASK_TRAVEL_HR.csv').set_index('R1_station_id').loc[ids,ids]
crew=ns['expand_c57'](read(R23/'R1_CREW_SCENARIO_ROSTERS.csv'))
origin=np.array([base.index.get_loc(x) for x in crew.origin_key])
means=np.array([0,1.027623931339495,6.16574358803697,12.017751356168503,36.05325406850551])
work=prob[[f'P_DS{k}' for k in range(5)]].to_numpy()@means
policies={'GA-Balanced':(1,3,1,.5),'GA-HospFirst':(1,20,1,.1),'GA-Efficiency':(1,1,1,2)}
seq=read(R26/'GA_CANONICAL_SEQUENCES.csv');index={x:i for i,x in enumerate(ids)}
stored={s:tuple(index[x] for x in g.sort_values('rank').R1_station_id) for s,g in seq.groupby('strategy')}
rows=[]
for policy,(wp,wh,ws,wmk) in policies.items():
    score=(wp*priority.population_priority_score+wh*priority.hospital_priority_score+ws*priority.sovi_priority_score).to_numpy()/(wp+wh+ws)
    decoder=ns['SurrogateDecoder'](base.to_numpy(),task.to_numpy(),origin,work,score,wmk)
    candidates={**stored,'initial_priority_desc':tuple(np.argsort(-score,kind='stable')),'initial_workload_asc':tuple(np.argsort(work,kind='stable'))}
    for name,order in candidates.items():
        r=decoder.evaluate(order)
        rows.append(dict(objective=policy,sequence=name,fitness=r.fitness,completion_benefit=r.completion_benefit,makespan_hr=r.makespan_hr,makespan_penalty=r.makespan_penalty,sequence_sha256=hashlib.sha256(('\n'.join(ids[i] for i in order)+'\n').encode()).hexdigest()))
rescore=pd.DataFrame(rows);write(rescore,'GA_SAVED_SEQUENCE_RESCORING.csv')
curves=read(R26/'GA_CONVERGENCE_BY_SEED.csv'); hist=[]
for (policy,seed),g in curves.groupby(['policy','seed']):
    g=g.sort_values('generation');best=g.loc[g.generation_best_fitness.idxmax()];last=g.iloc[-1]
    hist.append(dict(policy=policy,seed=seed,initial_best=g.iloc[0].generation_best_fitness,highest_recorded_fitness=best.generation_best_fitness,highest_generation=int(best.generation),last_generation_best=last.generation_best_fitness,recorded_minus_returned=best.generation_best_fitness-last.generation_best_fitness,strictly_better_recorded=bool(best.generation_best_fitness>last.generation_best_fitness),earlier_sequence_saved=False))
history=pd.DataFrame(hist);write(history,'GA_RECORDED_VERSUS_RETURNED.csv')

# Only five clipped probability rows; distinguish finite crossing from roundoff.
cross=[]
for row in prob.loc[prob.stage1_clip_applied].itertuples():
    exc=np.array([0.5*math.erfc(-math.log(row.PGA_2pc50_g/getattr(row,f'mu_DS{k}'))/getattr(row,f'beta_DS{k}')/math.sqrt(2)) for k in range(1,5)])
    raw=np.r_[1-exc[0],exc[:-1]-exc[1:],exc[-1]]
    fixed=np.array([getattr(row,f'P_DS{k}') for k in range(5)])
    cross.append(dict(R1_station_id=row.R1_station_id,station_name=row.station_name,PGA=row.PGA_2pc50_g,negative_mass=float(-np.minimum(raw,0).sum()),max_abs_change=float(np.max(abs(fixed-raw))),L1_change=float(abs(fixed-raw).sum()),expected_DS_change=float((fixed-raw)@np.arange(5)),expected_work_hr_change=float((fixed-raw)@means),**{f'raw_DS{k}':raw[k] for k in range(5)},**{f'fixed_DS{k}':fixed[k] for k in range(5)}))
cross=pd.DataFrame(cross);write(cross,'FIVE_STATION_PROBABILITY_CROSSINGS.csv')

tract=read(R26/'TRACT_BURDEN_BY_REALIZATION.csv');summary=read(R26/'REALIZATION_STRATEGY_SUMMARY.csv')
metadata=read(R10/'SERVICE_LAYER_COVERAGE_QA.csv');mcols=['tract_id','attachment_tier','direct_identity_mass','named_system_proxy_mass','unresolved_attachment_mass']
tract=tract.merge(metadata[mcols],on='tract_id',validate='many_to_one')
# Fully unresolved must not become near_zero/zero direction probability.
old=read(R26/'PAIRWISE_STRATEGY_EFFECTS.csv');correct=old.copy();bad=correct.resolved_mass<=0
correct.loc[bad,'classification']='unresolved'
for c in ['mean_paired_delta_burden_hr','median_paired_delta_burden_hr','fraction_realizations_delta_lt_0']:
    correct.loc[bad,c]=np.nan
correct=correct.merge(metadata[mcols],on='tract_id',validate='many_to_one')
write(correct,'CORRECTED_TRACT_PAIRED_EFFECTS.csv')
pop=metadata.population.sum();knownpop=metadata.loc[metadata.architecture_B_static_state_coverage>0,'population'].sum()
winners=[]
for (s,c),b in correct.groupby(['strategy','classification']):
    winners.append(dict(statistic='classification_of_32_realization_mean',strategy=s,classification=c,tract_count=len(b),population=b.population.sum(),pct_all_817_population=100*b.population.sum()/pop,pct_identifiable_805_population=np.nan if c=='unresolved' else 100*b.population.sum()/knownpop,mean_effect_hr=wm(b.mean_paired_delta_burden_hr,b.population)))
ref=tract.loc[tract.strategy=='Hospital-first',['realization_id','tract_id','normalized_burden_hr']].rename(columns={'normalized_burden_hr':'reference_burden'})
paired=tract.loc[tract.strategy!='Hospital-first'].merge(ref,on=['realization_id','tract_id'],validate='many_to_one')
paired['delta']=paired.normalized_burden_hr-paired.reference_burden
paired['class']=np.select([paired.resolved_mass<=0,paired.delta< -1,paired.delta>1],['unresolved','improved','worsened'],default='near_zero')
for (rid,s,c),b in paired.groupby(['realization_id','strategy','class']):
    winners.append(dict(statistic='single_realization_classification',realization_id=rid,strategy=s,classification=c,tract_count=len(b),population=b.population.sum(),pct_all_817_population=100*b.population.sum()/pop,pct_identifiable_805_population=np.nan if c=='unresolved' else 100*b.population.sum()/knownpop,mean_effect_hr=wm(b.delta,b.population)))
write(pd.DataFrame(winners),'CORRECTED_WINNERS_AND_DENOMINATORS.csv')

# Same tract evidence, distinct scientifically meaningful weighting/denominators.
metrics=[]
for (rid,s),b in tract.groupby(['realization_id','strategy']):
    metrics.append(dict(realization_id=rid,strategy=s,person_weighted_normalized_hr=wm(b.normalized_burden_hr,b.population),candidate_mass_weighted_hr=float(np.dot(b.population,b.restoration_burden_mass_hr)/np.dot(b.population,b.resolved_mass)),population_denominator=knownpop,population_resolved_mass_denominator=float(np.dot(b.population,b.resolved_mass))))
metric=pd.DataFrame(metrics);write(metric,'ALTERNATIVE_BURDEN_DENOMINATORS.csv')
groups=[]
for groupcol in ['sovi_quartile','attachment_tier']:
    for (rid,s,g),b in tract.groupby(['realization_id','strategy',groupcol]):
        groups.append(dict(group_type=groupcol,group=g,realization_id=rid,strategy=s,tract_count=len(b),population=b.population.sum(),identified_population=b.loc[b.resolved_mass>0,'population'].sum(),person_weighted_normalized_hr=wm(b.normalized_burden_hr,b.population),candidate_mass_weighted_hr=float(np.dot(b.population,b.restoration_burden_mass_hr)/np.dot(b.population,b.resolved_mass)) if np.dot(b.population,b.resolved_mass)>0 else np.nan))
groups=pd.DataFrame(groups);write(groups,'GROUP_ABSOLUTE_AND_PAIRED_BURDEN.csv')
groupref=groups[groups.strategy=='Hospital-first'][['group_type','group','realization_id','person_weighted_normalized_hr']].rename(columns={'person_weighted_normalized_hr':'reference_hr'})
groups=groups.merge(groupref,on=['group_type','group','realization_id']);groups['paired_delta_hr']=groups.person_weighted_normalized_hr-groups.reference_hr
write(groups,'GROUP_ABSOLUTE_AND_PAIRED_BURDEN.csv')
# Static A/B exposure by vulnerability, including fully unresolved communities.
q=tract[['tract_id','sovi_quartile']].drop_duplicates();meta=metadata.merge(q,on='tract_id',validate='one_to_one')
exposure=[]
for name,b in [('ALL',meta)]+list(meta.groupby('sovi_quartile'))+list(meta.groupby('attachment_tier')):
    exposure.append(dict(group=str(name),tract_count=len(b),population=b.population.sum(),A_candidate_mass=np.dot(b.population,b.direct_identity_mass),B_candidate_mass=np.dot(b.population,b.named_system_proxy_mass),C_candidate_mass=np.dot(b.population,b.unresolved_attachment_mass),A_fraction=wm(b.direct_identity_mass,b.population),B_fraction=wm(b.named_system_proxy_mass,b.population),C_fraction=wm(b.unresolved_attachment_mass,b.population),tracts_with_B=int((b.named_system_proxy_mass>0).sum()),population_in_B_affected_tracts=b.loc[b.named_system_proxy_mass>0,'population'].sum(),mixed_A_B_tracts=int(((b.direct_identity_mass>0)&(b.named_system_proxy_mass>0)).sum())))
write(pd.DataFrame(exposure),'MAPPING_EXPOSURE_BY_GROUP.csv')
# Linear information retained in tract integrals: distinguish identifiable integrated
# upstream contributions from absent event-time trajectories. No new states inferred.
att=pd.read_csv(R10/'SERVICE_UPSTREAM_ATTACHMENT_LEDGER.csv',dtype=str,keep_default_na=False)
w=read(R10/'SCE_TRACT_SERVICE_W1.csv').set_index('tract_id').loc[metadata.tract_id]
targets=sorted(set(att.selected_upstream_R1_id)-{''})
C=np.column_stack([w[att.loc[att.selected_upstream_R1_id==i,'service_node_id'].tolist()].sum(axis=1) for i in targets])
u,s,v=np.linalg.svd(C,full_matrices=False)
null=v[-1]
# The one null direction only exchanges these indistinguishable A targets.
assert np.linalg.matrix_rank(C)==116
null_ids=[i for i,x in zip(targets,null) if abs(x)>1e-5]
assert null_ids==['300829','303005']
assert np.array_equal(C[:,targets.index(null_ids[0])],C[:,targets.index(null_ids[1])])
kept=[i for i in targets if i!=null_ids[1]]
basis=C[:,[targets.index(i) for i in kept]]
labels=[i if i!=null_ids[0] else '300829+303005_unseparated' for i in kept]
keys=pd.MultiIndex.from_product([range(32),['Hospital-first','GA-Balanced','GA-HospFirst','GA-Efficiency']],names=['realization_id','strategy'])
Y=tract.pivot(index='tract_id',columns=['realization_id','strategy'],values='restoration_burden_mass_hr').reindex(index=metadata.tract_id,columns=keys).to_numpy()
integrals=np.linalg.lstsq(basis,Y,rcond=None)[0]
residual=float(np.max(abs(basis@integrals-Y)))
assert residual<1e-8
R=metadata.architecture_B_static_state_coverage.to_numpy(float)
popweights=np.divide(metadata.population.to_numpy(float),R,out=np.zeros(len(R)),where=R>0)/knownpop
coef=popweights@basis
contribution=integrals.reshape(116,32,4)*coef[:,None,None]
con=[]
for si,strategy in enumerate(['GA-Balanced','GA-HospFirst','GA-Efficiency'],start=1):
    delta=(contribution[:,:,si]-contribution[:,:,0]).mean(axis=1)
    for label,d in zip(labels,delta):
        con.append(dict(strategy=strategy,upstream_group=label,mean_population_burden_difference_contribution_hr=d,interpretation='linear accounting attribution, not task-timing or real-world causal attribution'))
write(pd.DataFrame(con),'IDENTIFIABLE_INTEGRATED_UPSTREAM_CONTRIBUTIONS.csv')
W=w[att.service_node_id].to_numpy();ab=~att.attachment_class.str.startswith('C').to_numpy();bm=att.attachment_class.str.startswith('B').to_numpy()
nullchecks={}
for lam in [.5,2.]:
    Z=W.copy();Z[:,bm]*=lam
    denom=Z[:,ab].sum(axis=1);Z[:,ab]*=np.divide(R,denom,out=np.ones(len(R)),where=denom>0)[:,None]
    colpos={j:k for k,j in enumerate(att.service_node_id)}
    D=np.column_stack([Z[:,[colpos[j] for j in att.loc[att.selected_upstream_R1_id==i,'service_node_id']]].sum(axis=1) for i in targets])
    nullchecks[str(lam)]=float(np.max(abs(D@null)))
linear_information=dict(target_count=117,rank=116,unseparated_A_pair=null_ids,combined_basis_condition_number=float(np.linalg.cond(basis)),max_integral_reconstruction_error=residual,B_weight_tilt_null_projection=nullchecks,meaning='B/A weight tilt burden is identifiable offline; individual pair integrals and event-time trajectories are not; no tilted outcomes computed this round')
with np.load(R26/'REVISED_PAIRED_PILOT_EVIDENCE.npz',allow_pickle=True) as z:
    archive={k:dict(shape=list(z[k].shape),dtype=str(z[k].dtype)) for k in z.files}
    ds=z['physical_damage_states'];dur=z['physical_duration_hr']
    by_ds={str(k):dict(task_count=int((ds==k).sum()),hours=float(dur[ds==k].sum())) for k in range(5)}
findings=dict(baseline_commit='1d1015ff2d636bb36385267ce5a52df7ac28aefc',source_files_unchanged=all(sha(R26/n)==v for n,v in before.items()),original_hashes=before,GA_runs_with_better_earlier_fitness=int(history.strictly_better_recorded.sum()),probability_negative_mass_max=float(cross.negative_mass.max()),sum_negative_probability_mass=float(cross.negative_mass.sum()),original_fully_unresolved_effect_rows=int(bad.sum()),total_population=int(pop),identifiable_population=int(knownpop),evidence_contents=archive,stored_work_by_DS=by_ds,linear_information=linear_information,executions=dict(GA=0,physical_pipeline=0,unique_surrogate_sequence_objective_pairs=len(rescore)))
(OUT/'ASSESSMENT_CALCULATION_PROVENANCE.json').write_text(json.dumps(findings,indent=2),encoding='utf-8')
print(json.dumps(findings,indent=2))
print('\nRESCORE\n',rescore.to_string(index=False))
print('\nHISTORY\n',history.to_string(index=False))
print('\nCROSSINGS\n',cross.to_string(index=False))
print('\nGROUP MEANS\n',groups.groupby(['group_type','group','strategy'])[['person_weighted_normalized_hr','paired_delta_hr']].mean().to_string())
print('\nEXPOSURE\n',pd.DataFrame(exposure).to_string(index=False))
print('\nBURDEN DEFINITIONS\n',metric.groupby('strategy').mean(numeric_only=True).to_string())
