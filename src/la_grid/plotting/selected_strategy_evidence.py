"""Read-only outcome/reference tables and network-community evidence."""
import json
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from pathlib import Path
from la_grid.plotting import selected_strategy_artwork as a
from la_grid.plotting.selected_strategy_panels import all_summary,MARK
R=a.ROOT;OUT=R/'results/diagnostics/selected_strategy_20261008'
METRICS={'population_weighted_normalized_burden_hr':'All-tract service loss (h)','population_resolved_mass_weighted_burden_hr':'Population-dependency-weighted service loss (h)','population_T80_hr':'Population T80 (h)','hospital_mean_normalized_burden_hr':'Hospital-tract service loss (h)','burden_gini':'Population-weighted Gini','signed_Q4_minus_Q1_hr':'Signed Q4-Q1 service-loss difference (h)','absolute_Q4_minus_Q1_hr':'High-low vulnerability service-loss gap (h)','L_self_population_mass_weighted_hr':'Substation-damage service loss (h)','L_threshold_population_mass_weighted_hr':'Functionality-threshold service loss (h)','L_source_population_mass_weighted_hr':'Source-path service loss (h)'}
METRICS.update({f'burden_Q{i}_hr':f'Q{i} tract service loss (h)' for i in range(1,5)})

def tables(d):
    absolute=[];contrasts=[]
    for (hazard,case),q in d.groupby(['hazard','resource_scenario']):
        for k,p in q.groupby('strategy_id'):
            assert len(p)==1000 and not p.realization_id.duplicated().any()
            for f,label in METRICS.items():
                if f not in p:continue
                v=p[f].dropna().to_numpy()
                absolute.append(dict(hazard=hazard,resource_condition=case,policy=k,source_field=f,metric=label,n=len(v),mean=v.mean(),median=np.median(v),p05=np.quantile(v,.05),p95=np.quantile(v,.95),interval='5th-95th realization range'))
        for ref in ['hospital-first','impact-first','random','unconstrained']:
            base=q[q.strategy_id.eq(ref)].set_index('realization_id')
            if base.empty:continue
            for k in a.SELECTED:
                p=q[q.strategy_id.eq(k)].set_index('realization_id')
                if p.empty or k==ref:continue
                assert set(p.index)==set(base.index)
                for f,label in METRICS.items():
                    if f not in p:continue
                    v=(p[f]-base[f]).dropna().to_numpy()
                    contrasts.append(dict(hazard=hazard,resource_condition=case,policy=k,reference=ref,source_field=f,metric=label,n=len(v),mean=v.mean(),median=np.median(v),p05=np.quantile(v,.05),p95=np.quantile(v,.95),interval='5th-95th realization-difference range'))
    pd.DataFrame(absolute).to_csv(OUT/'ABSOLUTE_OUTCOMES.csv',index=False)
    effects=pd.DataFrame(contrasts);effects.to_csv(OUT/'NAMED_REFERENCE_EFFECTS.csv',index=False)
    return effects

def saved_station_curves():
    path=OUT/'STATION_FUNCTIONALITY_CURVES.csv'
    if path.exists():return pd.read_csv(path)
    grid=np.arange(0,121);rows=[]
    for k in ['degree-first','betweenness-first','impact-first','hospital-first']:
        folder=R/'Formal_Experiment_20260923/Formal_Trajectories/2pc50/C57_D1'/k
        files=sorted(folder.glob('*.npz'));assert len(files)==1000
        sums=np.zeros((len(grid),3))
        for file in files:
            with np.load(file) as z:
                ix=np.clip(np.searchsorted(z['event_time_hr'],grid,side='right')-1,0,len(z['event_time_hr'])-1)
                sums+=np.column_stack([z['f'][ix].mean(axis=1),(z['f'][ix]*z['F'][ix]).mean(axis=1),z['e'][ix].mean(axis=1)])
        for t,v in zip(grid,sums/1000):rows.append(dict(policy=k,time_hr=t,raw_functionality=v[0],threshold_eligible_functionality=v[1],source_connected_effective_functionality=v[2]))
        print('Read saved station curves',k,flush=True)
    pd.DataFrame(rows).to_csv(path,index=False);return pd.DataFrame(rows)

def mechanism(effects):
    weights=pd.read_csv(R/'Data/JULY_UTILITY_CONSTRAINED_92.csv',dtype={'tract_id':str});assert np.max(abs(weights.groupby('tract_id').weight.sum().to_numpy()-1))<1e-12
    curves=saved_station_curves();fig,axes=plt.subplots(2,2,figsize=(185/25.4,175/25.4))
    fig.subplots_adjust(left=.16,right=.97,bottom=.13,top=.88,wspace=.35,hspace=.65)
    keys=['impact-first','hospital-first','degree-first','betweenness-first']
    fig.legend(handles=[a.Line2D([0],[0],color=a.common.COLORS[k],lw=1.2,label=a.common.LABEL[k]) for k in keys],loc='upper center',ncol=4,frameon=False,columnspacing=1.2)
    for ax,f,title in zip(axes.flat[:2],['raw_functionality','source_connected_effective_functionality'],['A. Station functionality','B. Source-connected station functionality']):
        for k in keys:
            q=curves[curves.policy.eq(k)];ax.plot(q.time_hr,q[f],color=a.common.COLORS[k],lw=1.2)
        ax.set_xlim(0,120);ax.set_ylim(-.025,1.04);ax.set_xlabel('Time after earthquake (h)');ax.set_ylabel('Mean station functionality');ax.set_title(title,fontsize=9.5)
    d=effects[effects.hazard.eq('2pc50')&effects.resource_condition.eq('C57_D1')]
    for ax,fields,title in [(axes[1,0],['L_self_population_mass_weighted_hr','L_threshold_population_mass_weighted_hr','L_source_population_mass_weighted_hr'],'C. Sources of community service loss'),(axes[1,1],['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr'],'D. Community-outcome changes')]:
        for j,(k,ref) in enumerate([(k,ref) for k in ['degree-first','betweenness-first'] for ref in ['hospital-first','impact-first']]):
            for i,f in enumerate(fields):
                row=d[d.policy.eq(k)&d.reference.eq(ref)&d.source_field.eq(f)].iloc[0]
                ax.errorbar(row['mean'],i+(j-1.5)*.13,xerr=[[row['mean']-row.p05],[row.p95-row['mean']]],fmt='o' if ref=='hospital-first' else 's',ms=3,color=a.common.COLORS[k],lw=.65,capsize=1)
        labels=['Substation\ndamage','Functionality\nthreshold','Source path'] if ax is axes[1,0] else ['All tracts','Q4 tracts','Hospital-linked\ntracts']
        ax.set_yticks(range(3),labels);ax.set_ylim(2.5,-.5);ax.axvline(0,color='#404040',lw=.6);ax.set_xlabel('Change from reference (h)');ax.set_title(title,fontsize=9.5)
    for ax in axes.flat:ax.grid(color='#e6e6e6',lw=.4);ax.spines[['top','right']].set_visible(False)
    fig.text(.5,.025,'Circles: relative to Hospital-first; squares: relative to Impact-first',ha='center',fontsize=7.5)
    result=a.export_figure(fig,'Additional_Evidence/Network_Station_Community_Tradeoffs')
    caption=('Network, station and community restoration trade-offs under 2pc50, reference crew availability and repair duration. A/B are station-equal-weight means across 1,000 realizations, read from saved event arrays: raw f and source-connected e=fFC. The threshold-eligible fF progression is also recorded in the source CSV. C uses population-dependency-weighted component integrals: substation damage 1-f, functionality threshold f(1-F), and source-path loss fF(1-C). D uses the existing all-tract population-weighted, Q4 population-weighted and hospital-linked equal-tract mean loss estimands. Loss integrals cover 0-480 h; curves display 0-120 h. Circles compare Degree/Betweenness with Hospital-first; squares compare them with Impact-first on the same physical realizations. Intervals are 5th-95th realization-difference ranges, not confidence intervals. Degree-first reduces source-path loss relative to Hospital-first by approximately 1.647 h while increasing all-tract loss by 1.401 h; the saved production weights resolve unit tract mass, so the additional substation-damage and threshold losses outweigh the reduced source-path component. Faster station/source-connected recovery need not minimize community loss. These quantities are not delivered MW or a full-network electrical-capacity validation. Sources: saved Formal_Trajectories, PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet and NAMED_REFERENCE_EFFECTS.csv.\n')
    (a.REVIEW/'Additional_Evidence/Network_Station_Community_Tradeoffs.md').write_text(caption,encoding='utf-8')
    return result

def station_guidance():
    from la_grid.diagnostics.ga_search_budget_sensitivity import identity
    formal=R/'Formal_Experiment_20260923';seq=json.loads((formal/'Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50'];seq['vulnerability-first']=json.loads((formal/'Equity_Amendment/VULNERABILITY_FIRST_SEQUENCE.json').read_text())['ordered_station_ids']
    w=pd.read_csv(R/'Data/JULY_UTILITY_CONSTRAINED_92.csv',dtype={'tract_id':str,'substation_id':str});meta=pd.read_csv(R/'provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv',dtype={'tract_id':str}).set_index('tract_id');w=w.join(meta[['SOVI_quartile','hospital_tract']],on='tract_id')
    metrics=pd.read_csv(formal/'Stage 2 Output_expanded/impact_centrality_substations.csv',dtype={'substation_id':str}).set_index('substation_id');rows=[]
    for k in a.SELECTED:
        folder=(formal/'Equity_Amendment/T/2pc50/C57_D1') if k=='vulnerability-first' else formal/'Formal_Trajectories/2pc50/C57_D1'/k
        tables=[pd.read_csv(p,dtype={'task_id':str}) for p in sorted(folder.glob('*__TASK_EVENTS.csv'))];assert len(tables)==1000
        event=pd.concat(tables).groupby('task_id');priority={s:i+1 for i,s in enumerate(seq[k])}
        for s,rank in priority.items():
            dep=w[w.substation_id.eq(s)];p=dep.population*dep.weight;events=event.get_group(s) if s in event.groups else None
            rows.append(dict(policy=k,station_id=s,fixed_priority_rank=rank,degree=float(metrics.loc[s,'degree']),betweenness=float(metrics.loc[s,'betweenness_centrality']),mapped_population_dependency=float(p.sum()),Q4_mapped_population_dependency=float(p[dep.SOVI_quartile.eq('Q4')].sum()),hospital_linked_tract_count=int(dep[dep.hospital_tract&dep.weight.gt(0)].tract_id.nunique()),damaged_realization_count=0 if events is None else len(events),mean_effective_dispatch_rank=np.nan if events is None else events.dispatch_rank.mean(),mean_completion_hr=np.nan if events is None else events.completion_hr.mean(),mean_travel_hr=np.nan if events is None else events.travel_hr.mean(),sequence_sha256=identity(seq[k])))
    guide=pd.DataFrame(rows);names=pd.read_csv(R/'Data/working_area_substations_with_fragility.csv',dtype={'ID':str})[['ID','NAME','Owner']].rename(columns={'ID':'station_id','NAME':'station_name','Owner':'station_owner'});guide=guide.merge(names,on='station_id',validate='many_to_one');guide.to_csv(OUT/'STATION_PRIORITY_AND_EXECUTION.csv',index=False)
    (OUT/'REFERENCE_AND_STATION_GUIDANCE.md').write_text('Hospital-first is the predeclared critical-service reference; Impact-first is the direct population-loss incumbent; Random is one frozen random priority order, not a new random order per realization; Unconstrained is an idealized reference without crew competition. Degree and Betweenness are compared with both Impact and Hospital. Named-reference effects align physical realization IDs. Fixed station rank is not an effective damaged-task rank or completion order: DS0 tasks are omitted and earliest-release crews include directed travel. The table links fixed rank, saved task dispatch/completion, mapped population/Q4/hospital dependency and saved network centrality. It does not estimate the causal benefit of repairing an individual station early, nor unmeasured MW capacity.\n',encoding='utf-8')

def main():
    OUT.mkdir(parents=True,exist_ok=True);d=all_summary();effects=tables(d);result=mechanism(effects);station_guidance()
    p=a.TEMP/'artwork_records.json';p.write_text(json.dumps(json.loads(p.read_text())+[result],indent=2));print('Completed read-only strategy evidence',flush=True)
if __name__=='__main__':main()
