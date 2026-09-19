"""Offline paired inference and mapping evaluation; never invokes scientific kernels."""
from pathlib import Path
import hashlib
import io
import json
import zipfile
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
REVIEW=OUT.parent
R26=REVIEW/'26_GA_Reproducibility_and_Revised_Paired_Pilot_20260919'
R10=REVIEW/'10_SCE_ServiceLayer_Architecture_20260914'
STRATEGIES=('Hospital-first','GA-Balanced','GA-HospFirst','GA-Efficiency')
CONDITIONS=('corrected_baseline','AB_lambda_0.5','AB_lambda_2','DS4x2')
BOOT=np.random.default_rng(20260919).integers(0,32,size=(10000,32))

def read(path,**kw):
    return pd.read_csv(path,float_precision='round_trip',**kw)

def write(df,name):
    df.to_csv(OUT/name,index=False,float_format='%.17g',lineterminator='\n')

def wm(x,w):
    ok=np.isfinite(x)&(w>0)
    return float(np.average(x[ok],weights=w[ok])) if ok.any() else np.nan

def gini(x,w):
    ok=np.isfinite(x)&(w>0);x=x[ok];w=w[ok]
    if not len(x):return np.nan
    if np.allclose(x,0):return 0.
    order=np.argsort(x,kind='stable');x=x[order];w=w[order]
    p=np.r_[0,np.cumsum(w)/w.sum()];v=np.r_[0,np.cumsum(x*w)/np.dot(x,w)]
    return float(1-np.sum((v[1:]+v[:-1])*np.diff(p)))

def ci(x):
    x=np.asarray(x,float)
    assert len(x)==32 and np.isfinite(x).all()
    lo,hi=np.quantile(x[BOOT].mean(axis=1),[.025,.975])
    return dict(mean_paired_difference=float(x.mean()),median_paired_difference=float(np.median(x)),sd_paired_difference=float(x.std(ddof=1)),fraction_delta_lt_0=float((x<0).mean()),ci95_low=float(lo),ci95_high=float(hi),paired_n=32)

def plot_findings(distributions,effects):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors={'Hospital-first':'#2b4c7e','GA-Balanced':'#b76a22','GA-HospFirst':'#248778','GA-Efficiency':'#ad4471'}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,2,figsize=(12,8.5),layout='constrained')
    d=distributions[distributions.condition=='corrected_baseline']
    for s in STRATEGIES:
        vals=[d[(d.strategy==s)&(d.metric==f'Q{k}_burden_hr')]['mean'].iloc[0] for k in range(1,5)]
        axs[0,0].plot(range(1,5),vals,'o-',label=s,color=colors[s])
    axs[0,0].set(title='A  Absolute burden, corrected baseline',xticks=range(1,5),xticklabels=['Q1','Q2','Q3','Q4'],ylabel='Population-weighted tract burden (h)',xlabel='Fixed NRI SOVI quartile')
    axs[0,0].legend(fontsize=8)
    e=effects[(effects.contrast=='strategy_minus_HF')&(effects.metric=='population_normalized_burden_hr')]
    for off,cond,label in [(-.13,'corrected_baseline','Baseline durations'),(.13,'DS4x2','DS4 durations doubled')]:
        for j,s in enumerate(STRATEGIES[1:]):
            row=e[(e.condition==cond)&(e.strategy==s)].iloc[0]
            axs[0,1].errorbar(j+off,row.mean_paired_difference,yerr=[[row.mean_paired_difference-row.ci95_low],[row.ci95_high-row.mean_paired_difference]],fmt='o' if off<0 else 's',color=colors[s],capsize=3,label=label if j==0 else None)
    axs[0,1].axhline(0,color='gray',lw=.7);axs[0,1].set(title='B  Population burden relative to Hospital-first',xticks=range(3),xticklabels=['Balanced','HospFirst','Efficiency'],ylabel='Paired difference (h); 95% bootstrap CI');axs[0,1].legend(fontsize=8)
    for s in STRATEGIES[1:]:
        rows=[effects[(effects.contrast=='strategy_minus_HF')&(effects.condition==c)&(effects.strategy==s)&(effects.metric=='Q4_burden_hr')].iloc[0] for c in ['AB_lambda_0.5','corrected_baseline','AB_lambda_2']]
        axs[1,0].plot([0,1,2],[r.mean_paired_difference for r in rows],'o-',color=colors[s],label=s)
    axs[1,0].axhline(0,color='gray',lw=.7);axs[1,0].set(title='C  Q4 effect under fixed-decision A/B weights',xticks=[0,1,2],xticklabels=['0.5','1 (original W1)','2'],xlabel='Relative Class B influence lambda',ylabel='Q4 burden relative to Hospital-first (h)')
    for s in STRATEGIES:
        g=d[(d.strategy==s)&(d.metric=='burden_gini')]['mean'].iloc[0]
        b=d[(d.strategy==s)&(d.metric=='population_normalized_burden_hr')]['mean'].iloc[0]
        axs[1,1].scatter(b,g,color=colors[s],s=65,label=s,edgecolors='white')
    axs[1,1].set(title='D  Four policy points, not an optimal frontier',xlabel='Mean population-normalized burden (h)',ylabel='Mean population-weighted burden Gini')
    axs[1,1].legend(fontsize=8)
    fig.suptitle('Conditional D302 / C57 decision comparisons: 32 paired realizations',fontsize=13)
    fig.savefig(OUT/'TARGETED_SCIENTIFIC_FINDINGS.png',dpi=300)
    fig.savefig(OUT/'TARGETED_SCIENTIFIC_FINDINGS.pdf')
    plt.close(fig)

def main():
    manifest=json.loads((OUT/'STRENGTHENING_INPUT_MANIFEST.json').read_text())
    journal=[json.loads(x) for x in (OUT/'EXECUTION_JOURNAL.jsonl').read_text().splitlines()]
    assert any(x['status']=='all_science_complete' for x in journal),'Science is still incomplete'
    assert sum(x['status']=='checkpoint_saved' for x in journal)==192
    assert sum(x['status']=='invariants_passed' for x in journal)==192
    src=np.load(R26/'REVISED_PAIRED_PILOT_EVIDENCE.npz',allow_pickle=True)
    ids=list(map(str,src['tract_ids'])); full=list(map(str,src['full_r1_ids']))
    domain=list(map(str,src['domain_ids']));services=list(map(str,src['service_ids']))
    pop=src['tract_population'];quart=src['tract_sovi_quartile'].astype(str);hospital=src['tract_hospital']
    metadata=read(R10/'SERVICE_LAYER_COVERAGE_QA.csv',dtype={'tract_id':str}).set_index('tract_id').loc[ids]
    oldtract=read(R26/'TRACT_BURDEN_BY_REALIZATION.csv',dtype={'tract_id':str})
    oldsummary=read(R26/'REALIZATION_STRATEGY_SUMMARY.csv')
    R=oldtract[(oldtract.realization_id==0)&(oldtract.strategy=='Hospital-first')].set_index('tract_id').loc[ids].resolved_mass.to_numpy()
    assert (R==0).sum()==12
    N=src['normalized_tract_burden_hr'].copy()
    B=np.nan_to_num(N,nan=0)*R[None,None,:]
    # Columns of C aggregate official A/B service weights onto upstream targets.
    att=pd.read_csv(R10/'SERVICE_UPSTREAM_ATTACHMENT_LEDGER.csv',dtype=str,keep_default_na=False).set_index('service_node_id').loc[services]
    # Preserve Round26 parser semantics for W; numerical residuals are recorded.
    W=pd.read_csv(R10/'SCE_TRACT_SERVICE_W1.csv',dtype={'tract_id':str}).set_index('tract_id').loc[ids,services].to_numpy()
    targets=sorted(set(att.selected_upstream_R1_id)-{''})
    C=np.column_stack([W[:,att.selected_upstream_R1_id.to_numpy()==i].sum(axis=1) for i in targets])
    merge_pair=['300829','303005'];kept=[i for i in targets if i!=merge_pair[1]]
    assert np.array_equal(C[:,targets.index(merge_pair[0])],C[:,targets.index(merge_pair[1])])
    basis=C[:,[targets.index(i) for i in kept]]
    assert np.linalg.matrix_rank(basis)==116
    labels=[i if i!=merge_pair[0] else '300829+303005_unseparated' for i in kept]
    integrals=np.full((2,32,4,116),np.nan)
    reconstructed=np.linalg.lstsq(basis,B.transpose(2,0,1).reshape(817,-1),rcond=None)[0].reshape(116,32,4).transpose(1,2,0)
    max_reconstruct=float(np.max(abs(np.einsum('ri,nsi->nsr',basis,reconstructed)-B)))
    assert max_reconstruct<1e-8
    integrals[0]=reconstructed
    physical_B=np.full((2,32,4,817),np.nan);physical_B[0]=B
    physical_R=np.full((2,32,4,817),np.nan);physical_R[0]=R
    summaries=[]; event_frames=[];mechanism=[]
    reuse=oldsummary[oldsummary.strategy.isin(['Hospital-first','GA-Efficiency'])].copy()
    reuse['condition']='corrected_baseline';reuse['result_source']='retained_R26_exact_inputs_sequence'
    summaries.extend(reuse.to_dict('records'))
    runtime_ties=[]
    archive=OUT/'SCIENTIFIC_RUN_CHECKPOINTS.zip'
    with zipfile.ZipFile(archive) as z:
        for scenario in ['baseline','DS4x2']:
            sk=0 if scenario=='baseline' else 1
            selection=STRATEGIES[1:3] if sk==0 else STRATEGIES
            for rid in range(32):
                for strategy in selection:
                    si=STRATEGIES.index(strategy); key=f'{scenario}/r{rid:02d}/{strategy}'
                    e=np.load(io.BytesIO(z.read(key+'/evidence.npz')))
                    events=read(io.BytesIO(z.read(key+'/task_events.csv')),dtype={'task_id':str,'previous_task_id':str})
                    assert list(e['tract_ids'])==ids and list(e['full_r1_ids'])==full
                    assert np.array_equal(e['damage'],src['physical_damage_states'][rid])
                    expected_duration=src['physical_duration_hr'][rid].copy()
                    if sk:expected_duration[e['damage']==4]*=2
                    assert np.array_equal(e['duration'],expected_duration)
                    lower=e['lower'];resolved=e['resolved_mass'];times=e['times']
                    assert np.allclose(resolved,R,atol=1e-12,rtol=0)
                    burden=np.sum(np.clip(resolved[None,:]-lower[:-1],0,None)*np.diff(times)[:,None],axis=0)
                    physical_B[sk,rid,si]=burden;physical_R[sk,rid,si]=resolved
                    ints=e['network_deficit_integrals']
                    values=np.array([ints[full.index(i)] for i in kept])
                    values[kept.index(merge_pair[0])]+=ints[full.index(merge_pair[1])]
                    integrals[sk,rid,si]=values
                    assert np.allclose(basis@values,burden,atol=1e-8,rtol=0),'Saved interface integrals differ from production tract burden'
                    available=lower@pop/np.dot(pop,resolved)
                    metrics={f'population_resolved_T{int(p*100)}_hr':float(times[np.flatnonzero(available>=p-1e-12)[0]]) if (available>=p-1e-12).any() else np.nan for p in [.5,.8,.9]}
                    row=dict(condition='corrected_baseline' if sk==0 else 'DS4x2',realization_id=rid,strategy=strategy,result_source='new_full_scientific_chain',task_count=len(events),makespan_hr=float(events.completion_hr.max()),total_travel_hr=float(events.travel_hr.sum()),total_on_site_work_hr=float(e['duration'].sum()),**metrics)
                    vector=manifest['physical_vectors'][rid]
                    row.update(damage_vector_hash=vector['damage_hash'],duration_vector_hash=vector['baseline_duration_hash' if sk==0 else 'DS4x2_duration_hash'],**{f'DS{k}_count':int((e['damage']==k).sum()) for k in range(5)})
                    summaries.append(row)
                    events.insert(0,'strategy',strategy);events.insert(0,'realization_id',rid);events.insert(0,'condition',row['condition']);event_frames.append(events)
        # Inspect paired new-run logistics changes without reconstructing absent old events.
    all_events=pd.concat(event_frames,ignore_index=True)
    all_events.to_csv(OUT/'NEW_RUN_TASK_EVENTS.csv.gz',index=False,float_format='%.17g',compression='gzip')
    summary=pd.DataFrame(summaries).set_index(['condition','realization_id','strategy'])
    for s in STRATEGIES[1:3]:
        baseline=all_events[(all_events.condition=='corrected_baseline')&(all_events.strategy==s)]
        doubled=all_events[(all_events.condition=='DS4x2')&(all_events.strategy==s)]
        joined=baseline.merge(doubled,on=['realization_id','task_id'],suffixes=('_baseline','_DS4x2'),validate='one_to_one')
        for rid,g in joined.groupby('realization_id'):
            mechanism.append(dict(strategy=s,realization_id=rid,paired_tasks=len(g),crew_assignment_changes=int((g.crew_index_baseline!=g.crew_index_DS4x2).sum()),previous_task_changes=int((g.previous_task_id_baseline.fillna('BASE')!=g.previous_task_id_DS4x2.fillna('BASE')).sum()),mean_arrival_change_hr=float((g.arrival_hr_DS4x2-g.arrival_hr_baseline).mean()),mean_completion_change_hr=float((g.completion_hr_DS4x2-g.completion_hr_baseline).mean())))
    write(pd.DataFrame(mechanism),'PAIRED_LOGISTICS_MECHANISM.csv')

    # Offline weight conditions: C and total R unchanged, no trajectory reconstruction.
    bclass=att.attachment_class.str.startswith('B').to_numpy();ab=~att.attachment_class.str.startswith('C').to_numpy()
    condition_B={'corrected_baseline':physical_B[0],'DS4x2':physical_B[1]}
    matrices={'corrected_baseline':basis,'DS4x2':basis}
    for lam,name in [(.5,'AB_lambda_0.5'),(2.,'AB_lambda_2')]:
        mixed=(W[:,ab&~bclass].sum(axis=1)>0)&(W[:,bclass].sum(axis=1)>0)
        altered=W.copy();altered[np.ix_(mixed,bclass)]*=lam
        mass=altered[:,ab].sum(axis=1)
        factor=np.divide(R,mass,out=np.ones_like(R),where=mass>0)
        altered[np.ix_(mixed,ab)]*=factor[mixed,None]
        assert np.array_equal(altered[~mixed],W[~mixed])
        assert np.array_equal(altered[:,~ab],W[:,~ab])
        assert np.allclose(altered[:,ab].sum(axis=1),R,atol=1e-12,rtol=0)
        D=np.column_stack([altered[:,att.selected_upstream_R1_id.to_numpy()==i].sum(axis=1) for i in kept])
        matrices[name]=D
        condition_B[name]=np.einsum('ri,nsi->nsr',D,integrals[0])
    # lambda=1 equals existing W, not a new reweighting or a separate science run.
    lambda1_error=float(np.max(abs(np.einsum('ri,nsi->nsr',basis,integrals[0])-physical_B[0])))
    assert lambda1_error<1e-8

    N_all={};metric_rows=[];groups=[]
    known_pop=float(pop[R>0].sum());candidate_pop=float(np.dot(pop,R))
    for condition in CONDITIONS:
        value=condition_B[condition]
        normalized=np.divide(value,R[None,None,:],out=np.full_like(value,np.nan),where=R[None,None,:]>0)
        if condition=='corrected_baseline':
            normalized[:,0]=src['normalized_tract_burden_hr'][:,0]
            normalized[:,3]=src['normalized_tract_burden_hr'][:,3]
        assert np.isnan(normalized[:,:,R==0]).all()
        N_all[condition]=normalized
        for rid in range(32):
            for si,strategy in enumerate(STRATEGIES):
                n=normalized[rid,si]
                q={f'Q{k}_burden_hr':wm(n[quart==f'Q{k}'],pop[quart==f'Q{k}']) for k in range(1,5)}
                row=dict(condition=condition,realization_id=rid,strategy=strategy,population_normalized_burden_hr=wm(n,pop),population_resolved_mass_burden_hr=float(np.dot(pop,value[rid,si])/candidate_pop),hospital_mean_normalized_burden_hr=float(np.nanmean(n[hospital])),burden_gini=gini(n,pop),**q)
                row['Q4_minus_Q1_burden_gap_hr']=q['Q4_burden_hr']-q['Q1_burden_hr'];row['absolute_Q4_minus_Q1_burden_gap_hr']=abs(row['Q4_minus_Q1_burden_gap_hr'])
                row.update(population_denominator=known_pop,population_resolved_mass_denominator=candidate_pop,unresolved_tracts=int((R==0).sum()),unresolved_population=float(pop[R==0].sum()))
                if condition in ['corrected_baseline','DS4x2']:
                    extra=summary.loc[(condition,rid,strategy)].to_dict()
                    # These integral metrics are rebuilt consistently; only trajectories/logistics come from extra.
                    row.update({k:v for k,v in extra.items() if k not in row})
                    if condition=='corrected_baseline' and strategy in ('Hospital-first','GA-Efficiency'):
                        for k in list(row):
                            if k in extra and isinstance(extra[k],(int,float,np.number)) and np.isfinite(extra[k]):
                                if k in ['population_normalized_burden_hr','hospital_mean_normalized_burden_hr','burden_gini','Q1_burden_hr','Q2_burden_hr','Q3_burden_hr','Q4_burden_hr','Q4_minus_Q1_burden_gap_hr','absolute_Q4_minus_Q1_burden_gap_hr']:
                                    assert abs(row[k]-extra[k])<1e-9
                                    row[k]=extra[k]
                metric_rows.append(row)
                for group_type,labels_array in [('SOVI_quartile',quart),('attachment_tier',metadata.attachment_tier.to_numpy())]:
                    for group in sorted(set(labels_array)):
                        mask=labels_array==group
                        groups.append(dict(condition=condition,realization_id=rid,strategy=strategy,group_type=group_type,group=group,population=float(pop[mask].sum()),identified_population=float(pop[mask&(R>0)].sum()),mean_normalized_burden_hr=wm(n[mask],pop[mask])))
    metrics=pd.DataFrame(metric_rows)
    write(metrics,'REALIZATION_STRATEGY_METRICS.csv')
    write(pd.DataFrame(groups),'GROUP_ABSOLUTE_BURDEN.csv')
    measures=['population_normalized_burden_hr','population_resolved_mass_burden_hr','hospital_mean_normalized_burden_hr','Q1_burden_hr','Q2_burden_hr','Q3_burden_hr','Q4_burden_hr','Q4_minus_Q1_burden_gap_hr','absolute_Q4_minus_Q1_burden_gap_hr','burden_gini','population_resolved_T50_hr','population_resolved_T80_hr','population_resolved_T90_hr','makespan_hr','total_travel_hr']
    effects=[];distributions=[];ranks=[]
    for condition in CONDITIONS:
        m=metrics[metrics.condition==condition]
        for measure in measures:
            frame=m.pivot(index='realization_id',columns='strategy',values=measure).reindex(index=range(32),columns=STRATEGIES)
            if frame.isna().all().all():continue
            assert np.isfinite(frame.to_numpy()).all(),(condition,measure)
            for s in STRATEGIES:
                x=frame[s].to_numpy()
                distributions.append(dict(condition=condition,strategy=s,metric=measure,mean=x.mean(),sd=x.std(ddof=1),median=np.median(x),q25=np.quantile(x,.25),q75=np.quantile(x,.75)))
            for s in STRATEGIES[1:]:
                effects.append(dict(contrast='strategy_minus_HF',condition=condition,strategy=s,metric=measure,**ci(frame[s]-frame['Hospital-first'])))
            best=frame.to_numpy().min(axis=1,keepdims=True);ties=frame.to_numpy()==best
            for j,s in enumerate(STRATEGIES):
                ranks.append(dict(condition=condition,metric=measure,strategy=s,lowest_frequency=float((ties/ties.sum(axis=1,keepdims=True))[:,j].mean())))
    for condition in CONDITIONS[1:]:
        for measure in measures:
            a=metrics[metrics.condition=='corrected_baseline'].pivot(index='realization_id',columns='strategy',values=measure).reindex(index=range(32),columns=STRATEGIES)
            b=metrics[metrics.condition==condition].pivot(index='realization_id',columns='strategy',values=measure).reindex(index=range(32),columns=STRATEGIES)
            if b.isna().all().all():continue
            for s in STRATEGIES:
                effects.append(dict(contrast='condition_minus_baseline_within_strategy',condition=condition,strategy=s,metric=measure,**ci(b[s]-a[s])))
            for s in STRATEGIES[1:]:
                effects.append(dict(contrast='change_in_strategy_minus_HF',condition=condition,strategy=s,metric=measure,**ci((b[s]-b['Hospital-first'])-(a[s]-a['Hospital-first']))))
    # Selection correction comparisons use the same 32 physical samples, not independent groups.
    for measure in measures:
        if measure not in oldsummary:continue
        a=oldsummary.pivot(index='realization_id',columns='strategy',values=measure).reindex(index=range(32),columns=STRATEGIES)
        b=metrics[metrics.condition=='corrected_baseline'].pivot(index='realization_id',columns='strategy',values=measure).reindex(index=range(32),columns=STRATEGIES)
        for s in STRATEGIES:
            effects.append(dict(contrast='candidate_correction_minus_R26',condition='corrected_baseline',strategy=s,metric=measure,**ci(b[s]-a[s])))
    write(pd.DataFrame(effects),'PAIRED_EFFECTS.csv')
    write(pd.DataFrame(distributions),'METRIC_DISTRIBUTIONS.csv')
    write(pd.DataFrame(ranks),'METRIC_RANK_FREQUENCIES.csv')

    tract_effects=[];classifications=[]
    for condition in CONDITIONS:
        values=N_all[condition]
        for si,s in enumerate(STRATEGIES[1:],1):
            delta=values[:,si]-values[:,0]
            mean=np.full(817,np.nan);median=np.full(817,np.nan);direction=np.full(817,np.nan)
            mean[R>0]=delta[:,R>0].mean(axis=0);median[R>0]=np.median(delta[:,R>0],axis=0);direction[R>0]=(delta[:,R>0]<0).mean(axis=0)
            classes=np.where(R==0,'unresolved',np.where(mean< -1,'improved',np.where(mean>1,'worsened','near_zero')))
            for r,tid in enumerate(ids):
                tract_effects.append(dict(condition=condition,strategy=s,tract_id=tid,population=pop[r],resolved_mass=R[r],sovi_quartile=quart[r],attachment_tier=metadata.attachment_tier.iloc[r],mean_paired_delta_normalized_burden_hr=mean[r],median_paired_delta_normalized_burden_hr=median[r],fraction_realizations_delta_lt_0=direction[r],classification=classes[r],practical_threshold_hr=1.0))
            arrays=[('classification_of_32_realization_mean',None,classes)]+[('single_realization_classification',rid,np.where(R==0,'unresolved',np.where(delta[rid]< -1,'improved',np.where(delta[rid]>1,'worsened','near_zero')))) for rid in range(32)]
            for statistic,rid,cls in arrays:
                for group in ['ALL','Q1','Q2','Q3','Q4']:
                    gm=np.ones(817,bool) if group=='ALL' else quart==group
                    for category in ['improved','near_zero','worsened','unresolved']:
                        mask=gm&(cls==category)
                        classifications.append(dict(condition=condition,strategy=s,statistic=statistic,realization_id=rid,group=group,classification=category,tract_count=int(mask.sum()),population=float(pop[mask].sum()),pct_all_group_population=float(100*pop[mask].sum()/pop[gm].sum()),pct_identifiable_group_population=float(100*pop[mask].sum()/pop[gm&(R>0)].sum()) if category!='unresolved' else np.nan))
    write(pd.DataFrame(tract_effects),'TRACT_PAIRED_EFFECTS.csv')
    write(pd.DataFrame(classifications),'WINNER_LOSER_POPULATION.csv')

    contribution=[]
    for condition in CONDITIONS:
        ints=integrals[1 if condition=='DS4x2' else 0]
        for group in ['ALL','Q1','Q2','Q3','Q4']:
            gm=np.ones(817,bool) if group=='ALL' else quart==group
            weights=np.divide(pop,R,out=np.zeros_like(pop),where=R>0)*gm/pop[gm&(R>0)].sum()
            coefficients=weights@matrices[condition]
            for si,s in enumerate(STRATEGIES[1:],1):
                parts=(ints[:,si]-ints[:,0])*coefficients[None,:]
                for j,label in enumerate(labels):
                    contribution.append(dict(condition=condition,strategy=s,group=group,upstream_interface=label,mean_population_normalized_burden_difference_contribution_hr=float(parts[:,j].mean()),interpretation='integrated model accounting; not real-world causal mechanism'))
    write(pd.DataFrame(contribution),'INTERFACE_INTEGRATED_CONTRIBUTIONS.csv')
    np.savez_compressed(OUT/'TARGETED_SCIENTIFIC_EVIDENCE.npz',conditions=np.array(CONDITIONS),strategies=np.array(STRATEGIES),tract_ids=np.array(ids),population=pop,resolved_mass=R,sovi_quartile=quart,hospital_tract=hospital,normalized_burden=np.array([N_all[c] for c in CONDITIONS]),mass_burden=np.array([condition_B[c] for c in CONDITIONS]),upstream_identifiable_labels=np.array(labels),integrated_upstream_deficits=integrals,domain_ids=np.array(domain),stored_DS=src['physical_damage_states'],baseline_stored_durations=src['physical_duration_hr'],DS4x2_durations=np.where(src['physical_damage_states']==4,src['physical_duration_hr']*2,src['physical_duration_hr']))
    for name,h in manifest['original_R26_artifact_hashes'].items():assert hashlib.sha256((R26/name).read_bytes()).hexdigest()==h
    for name,path in manifest['input_paths'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==manifest['input_hashes'][name]
    results=dict(new_scientific_chains=192,reused_scientific_chains=64,new_GA_searches=0,new_physical_draws=0,pre_scientific_validation_failures=sum(r['status']=='pre_scientific_validation_failed' for r in journal),scientific_call_attempts=sum(r['status']=='started' for r in journal),bootstrap_unit='paired realization across all strategies and conditions',bootstrap_seed=20260919,resamples=10000,population_total=float(pop.sum()),identifiable_population=known_pop,resolved_candidate_population=candidate_pop,unresolved_population=float(pop[R==0].sum()),reconstruction_error_hr=max_reconstruct,lambda1_identity_error_hr=lambda1_error,unseparated_pair=merge_pair,original_inputs_unchanged=True)
    (OUT/'RESULTS_PROVENANCE.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))
    print(pd.DataFrame(distributions).pivot_table(index=['condition','strategy'],columns='metric',values='mean').to_string())
    plot_findings(pd.DataFrame(distributions),pd.DataFrame(effects))

if __name__=='__main__':main()
