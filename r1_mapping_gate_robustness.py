"""Offline paired mapping/gate evaluation. Consumes saved raw event states only."""
from pathlib import Path
import numpy as np
import pandas as pd
from r1_mapping import generate_mapping, load_mapping, threshold_weights, ROOT, BASELINE_PATH
from r1_source_gate import evaluate_source_gate
from r1_distributional_metrics import summarize_distribution, classify_tract_effects, paired_realization_summary

GATE_CASES={'G0_NO_GATE':('no_gate',.5),'G1_BASELINE_050':('source_gate',.5),
            'G2_RELAXED_005':('source_gate',.05),'G3_STRICT_075':('source_gate',.75)}


def candidate_supported(baseline, candidates):
    """Literal restriction of cutoff July weights. Zero overlap remains unresolved."""
    if not candidates.index.is_unique or not candidates.columns.is_unique:
        raise ValueError('Duplicate candidate identities')
    if not set(candidates.index).issubset(baseline.index) or set(candidates.columns)!=set(baseline.columns):
        raise ValueError('Candidate/mapping identity mismatch')
    b=baseline.reindex(index=candidates.index,columns=candidates.columns)
    restricted=b.where(candidates,0.)
    den=restricted.sum(axis=1)
    return restricted.div(den.where(den>0,1),axis=0)


def read_candidates(station_ids):
    x=pd.read_csv(ROOT/'Revision_Mapping_Gate/SCE_CANDIDATES_FROZEN.csv',dtype={'tract_id':str})
    x=x[x.utility_domain.eq('SCE') & x.represented_direct_count.gt(0)]
    if len(x)!=337:raise ValueError('Expected exactly 337 external subset tracts')
    c=pd.DataFrame(False,index=x.tract_id,columns=station_ids)
    for row in x.itertuples():
        ids=str(row.represented_direct_ids).split(';')
        if not set(ids).issubset(c.columns):raise ValueError('External ID outside July92')
        c.loc[row.tract_id,ids]=True
    return c


def mapping_cases():
    m0,raw0=generate_mapping(utility_constrained=False)
    m1,raw1=generate_mapping(utility_constrained=True)
    c=read_candidates(m0.columns)
    return {'M0_JULY_003':m0,'M1_UTILITY_003':m1,'M0_JULY_NO_CUTOFF':raw0,
            'M0_JULY_001':threshold_weights(raw0,.01),'M1_UTILITY_NO_CUTOFF':raw1,
            'M1_UTILITY_001':threshold_weights(raw1,.01),'M3_SCE_SUPPORTED':candidate_supported(m0,c)},c


def event_integral(values, times):
    """Right-continuous post-event states: left rectangles, not trapezoids."""
    times=np.asarray(times,float)
    if len(times)<2 or not np.isfinite(times).all() or times[0]!=0 or np.any(np.diff(times)<=0):
        raise ValueError('Event grid must start at zero and end after zero')
    return np.sum(np.asarray(values)[:-1]*np.diff(times)[:,None],axis=0)


def evaluate_mapping(trace, weights, population, quartile, hospital_tracts):
    if weights.index.has_duplicates or set(weights.columns)!=set(trace.f.columns):
        raise ValueError('Mapping/trajectory identity mismatch')
    w=weights.reindex(columns=trace.f.columns).to_numpy(float)
    if not np.isfinite(w).all() or (w<0).any() or (w.sum(axis=1)>1+1e-12).any():
        raise ValueError('Mapping mass must be finite nonnegative and <=1')
    known=trace.f.notna().iloc[0].to_numpy();resolved=w[:,known].sum(axis=1)
    available=trace.e.fillna(0).to_numpy() @ w.T
    rows={'resolved_mass':resolved,'status':np.where(resolved>1e-15,'resolved','unresolved')}
    for name in ['L_self','L_threshold','L_source','L_total']:
        mapped=getattr(trace,name).fillna(0).to_numpy() @ w.T
        rows[name+'_mass_hr']=event_integral(mapped,trace.f.index)
    rows['restoration_burden_mass_hr']=rows['L_total_mass_hr'].copy()
    rows['normalized_burden_hr']=np.divide(rows['L_total_mass_hr'],resolved,out=np.full(len(resolved),np.nan),where=resolved>1e-15)
    b=pd.DataFrame(rows,index=weights.index)
    b.loc[b.status.eq('unresolved'),[c for c in b if c.endswith('_hr')]]=np.nan
    np.testing.assert_allclose(b.L_self_mass_hr+b.L_threshold_mass_hr+b.L_source_mass_hr,b.L_total_mass_hr,rtol=0,atol=1e-10,equal_nan=True)
    summary=summarize_distribution(b,population,quartile)
    pop=population.reindex(b.index).to_numpy(float);mass_denom=float(pop@resolved)
    curve=(available@pop)/mass_denom if mass_denom>0 else np.full(len(available),np.nan)
    for target,label in [(.5,'T50'),(.8,'T80')]:
        idx=np.flatnonzero(curve>=target)
        summary['population_'+label+'_hr']=float(trace.f.index[idx[0]]) if len(idx) else np.nan
    hospitals=b.index.isin(hospital_tracts)&b.status.eq('resolved').to_numpy()
    summary['hospital_mean_normalized_burden_hr']=float(b.loc[hospitals,'normalized_burden_hr'].mean())
    summary['represented_population']=float(pop[resolved>1e-15].sum())
    summary['population_times_resolved_mass']=mass_denom
    summary['unresolved_population']=float(pop[resolved<=1e-15].sum())
    summary['horizon_hr']=float(trace.f.index[-1])
    for name in ['L_self','L_threshold','L_source','L_total']:
        value=float(np.nansum(pop*b[name+'_mass_hr'].to_numpy()))/mass_denom if mass_denom>0 else np.nan
        summary[name+'_population_mass_weighted_hr']=value
    total=summary['L_total_population_mass_weighted_hr']
    for name in ['L_self','L_threshold','L_source']:
        summary[name+'_fraction']=summary[name+'_population_mass_weighted_hr']/total if total>0 else np.nan
    return summary,b


def evaluate_saved_trajectory(raw,graph,source_ids,mappings,population,quartile,hospital_tracts,*,realization_id,strategy_id):
    """No scheduler or sampling dependency. Same raw object for every evaluation view."""
    original=raw.copy(deep=True);summaries=[];tracts=[];traces={}
    for gate,(mode,threshold) in GATE_CASES.items():
        trace=evaluate_source_gate(raw,graph,source_ids,mode=mode,threshold=threshold);traces[gate]=trace
        for name,w in mappings.items():
            summary,b=evaluate_mapping(trace,w,population,quartile,hospital_tracts)
            keys=dict(realization_id=str(realization_id),strategy_id=str(strategy_id),mapping=name,gate=gate,comparison_domain='mapping_native_domain')
            summaries.append(dict(**keys,**summary.to_dict()));tracts.append(b.rename_axis('tract_id').reset_index().assign(**keys))
        # M3 cannot give an 817- or 2315-tract result. Compare on identical positive
        # supported rows, while retaining all 337 rows (including 17 NA) above.
        if 'M3_SCE_SUPPORTED' in mappings:
            common=mappings['M3_SCE_SUPPORTED'].index[mappings['M3_SCE_SUPPORTED'].sum(axis=1)>0]
            for name in ['M0_JULY_003','M1_UTILITY_003','M3_SCE_SUPPORTED']:
                summary,_=evaluate_mapping(trace,mappings[name].loc[common],population,quartile,hospital_tracts)
                summaries.append(dict(realization_id=str(realization_id),strategy_id=str(strategy_id),mapping=name,gate=gate,comparison_domain='SCE_common_positive_support',**summary.to_dict()))
    pd.testing.assert_frame_equal(raw,original)
    return pd.DataFrame(summaries),pd.concat(tracts,ignore_index=True),traces


def paired_effects(summaries, metric, *, reference_strategy, bootstrap_resamples=10000):
    out=[]
    for keys,g in summaries.groupby(['mapping','gate','comparison_domain']):
        if g.duplicated(['realization_id','strategy_id']).any():raise ValueError('Duplicate paired key')
        pivot=g.pivot(index='realization_id',columns='strategy_id',values=metric)
        if pivot.isna().any().any():
            # Preserve not-reached/unknown metrics; paired helper reports available n.
            pass
        q=paired_realization_summary(pivot,reference_strategy,bootstrap_resamples=bootstrap_resamples)
        out.append(q.reset_index().assign(mapping=keys[0],gate=keys[1],comparison_domain=keys[2],metric=metric))
    return pd.concat(out,ignore_index=True)


def tract_effects(tracts, population, quartile, *, reference_strategy):
    """Both mean-paired classifications and per-realization classifications."""
    result=[]
    for (m,g),group in tracts.groupby(['mapping','gate']):
        p=group.pivot(index=['realization_id','tract_id'],columns='strategy_id',values='normalized_burden_hr')
        for strategy in p.columns:
            if strategy==reference_strategy:continue
            delta=p[strategy]-p[reference_strategy]
            valid=delta.notna().groupby(level='tract_id').sum()
            direction=(delta.lt(0)&delta.notna()).groupby(level='tract_id').sum()/valid.replace(0,np.nan)
            for scope,series in [('per_realization',delta),('mean_paired_effect',delta.groupby(level='tract_id').mean())]:
                # Explicit NA retains unresolved; direction denominator is valid paired realizations.
                z=pd.DataFrame({'delta_burden_hr':series});z['classification']='near-zero'
                z.loc[series < -1,'classification']='improved';z.loc[series > 1,'classification']='worsened';z.loc[series.isna(),'classification']='unresolved'
                z=z.reset_index();z['population']=z.tract_id.map(population);z['quartile']=z.tract_id.map(quartile)
                z['paired_valid_n']=z.tract_id.map(valid)
                z['paired_probability_delta_below_zero']=z.tract_id.map(direction)
                z=z.assign(mapping=m,gate=g,strategy=strategy,reference=reference_strategy,classification_scope=scope)
                result.append(z)
    return pd.concat(result,ignore_index=True)

def classification_population_summary(effects):
    """Mean-effect classification and average per-realization classification differ.

    Population fractions use every tract in the stated mapping domain, including
    unresolved. No tract is silently removed from the denominator.
    """
    keys=['mapping','gate','strategy','reference','classification_scope']
    records=[]
    for identity,g in effects.groupby(keys):
        scopes=[('all',g)]+[(str(q),z) for q,z in g.groupby('quartile',dropna=False)]
        for quartile,z in scopes:
            units=list(z.groupby('realization_id')) if identity[-1]=='per_realization' else [('mean',z)]
            for unit,x in units:
                denominator=float(x.population.sum())
                for label in ['improved','near-zero','worsened','unresolved']:
                    chosen=x[x.classification.eq(label)]
                    records.append(dict(zip(keys,identity),quartile=quartile,unit=unit,classification=label,tract_count=len(chosen),population=float(chosen.population.sum()),domain_population=denominator,population_fraction=float(chosen.population.sum())/denominator if denominator>0 else np.nan))
    out=pd.DataFrame(records)
    group=keys+['quartile','classification']
    return out.groupby(group,dropna=False)[['tract_count','population','domain_population','population_fraction']].mean().reset_index()

def paired_assumption_effects(summaries,metric,*,reference_mapping='M1_UTILITY_003',reference_gate='G1_BASELINE_050',bootstrap_resamples=10000):
    """Same strategy/realization, varying evaluation assumptions only.

    Native M3 is excluded from full-domain comparisons. M3 contrasts use the
    explicit common-positive subset summaries, with the same population denominator.
    """
    result=[]
    for (strategy,domain),g in summaries.groupby(['strategy_id','comparison_domain']):
        if domain=='mapping_native_domain':g=g[~g.mapping.eq('M3_SCE_SUPPORTED')]
        x=g.assign(case=g.mapping+'|'+g.gate)
        pivot=x.pivot(index='realization_id',columns='case',values=metric)
        ref=reference_mapping+'|'+reference_gate
        if ref not in pivot:continue
        q=paired_realization_summary(pivot,ref,bootstrap_resamples=bootstrap_resamples)
        result.append(q.reset_index().rename(columns={'strategy':'evaluation_case'}).assign(strategy_id=strategy,comparison_domain=domain,metric=metric,reference_case=ref))
    return pd.concat(result,ignore_index=True)
