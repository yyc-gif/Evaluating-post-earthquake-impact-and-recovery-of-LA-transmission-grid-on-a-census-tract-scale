"""Distributional recovery metrics for paired tract trajectories.

This module evaluates already-produced tract service trajectories. It does not
alter damage, topology, mapping, scheduling, source gating, or strategies.
"""
from typing import Sequence
import numpy as np
import pandas as pd


def assign_fixed_vulnerability_quartiles(vulnerability:pd.Series)->pd.Series:
    """Assign stable Q1..Q4 once using value then tract-ID tie breaking."""
    v=pd.to_numeric(vulnerability,errors='coerce')
    if v.empty or v.isna().any() or not np.isfinite(v.to_numpy()).all(): raise ValueError('Vulnerability must be complete and finite.')
    ids=pd.Index(v.index.astype(str)); order=pd.DataFrame({'id':ids,'value':v.to_numpy()}).sort_values(['value','id'],kind='mergesort')
    n=len(order); labels=np.minimum((np.arange(n)*4)//n+1,4); result=pd.Series(index=order.id,data=['Q'+str(x) for x in labels],name='vulnerability_quartile')
    return result.reindex(ids)


def compute_tract_burden(known_available:pd.DataFrame,resolved_mass:pd.Series|None=None, *, interpolation:str='linear')->pd.DataFrame:
    """Integrate represented service deficit; all-unresolved tracts remain NA.

    `known_available` is service mass supported by represented candidates, not
    a missing-filled availability fraction. `resolved_mass` is the tract mass
    that can be represented by the mapping. The normalized result has hours as
    units: integral(resolved-known)/resolved.
    """
    if interpolation not in {'linear','previous'}: raise ValueError('Unknown trajectory interpolation.')
    if not isinstance(known_available,pd.DataFrame) or known_available.empty: raise ValueError('known_available must be a nonempty DataFrame.')
    times=pd.to_numeric(pd.Index(known_available.index),errors='raise').to_numpy(float)
    if not np.isfinite(times).all() or np.any(np.diff(times)<=0): raise ValueError('Trajectory time must be finite and strictly increasing.')
    cols=pd.Index(known_available.columns.astype(str)); values=known_available.copy(); values.columns=cols
    if resolved_mass is None:
        rm=pd.Series([0. if values[c].isna().all() else 1. for c in cols],index=cols,dtype=float)
    else:
        rm=pd.to_numeric(resolved_mass,errors='raise'); rm.index=rm.index.astype(str); rm=rm.reindex(cols)
    if rm.isna().any() or not np.isfinite(rm.to_numpy()).all() or (rm<0).any() or (rm>1+1e-12).any(): raise ValueError('resolved_mass must cover all tracts and lie in [0,1].')
    rows=[]
    for tract in cols:
        mass=float(rm.loc[tract]); series=pd.to_numeric(values[tract],errors='coerce')
        if mass<=1e-15:
            if series.notna().any(): raise ValueError(f'Unresolved tract {tract} must remain semantic NA.')
            rows.append({'tract_id':tract,'resolved_mass':0.,'restoration_burden_mass_hr':np.nan,'normalized_burden_hr':np.nan,'status':'unresolved'}); continue
        x=series.to_numpy(float)
        if not np.isfinite(x).all(): raise ValueError(f'Resolved tract {tract} contains missing service values.')
        if (x<-1e-12).any() or (x>mass+1e-12).any(): raise ValueError(f'Tract {tract} service lies outside [0,resolved_mass].')
        deficit=np.clip(mass-x,0.,None)
        burden=float(np.sum(deficit[:-1]*np.diff(times)) if interpolation=='previous' else np.sum((deficit[:-1]+deficit[1:])*.5*np.diff(times)))
        rows.append({'tract_id':tract,'resolved_mass':mass,'restoration_burden_mass_hr':burden,'normalized_burden_hr':burden/mass,'status':'resolved'})
    return pd.DataFrame(rows).set_index('tract_id')


def population_weighted_gini(values:pd.Series,population:pd.Series)->float:
    """Population-weighted Gini of finite tract burden values."""
    x=pd.to_numeric(values,errors='coerce'); w=pd.to_numeric(population,errors='coerce').reindex(x.index); keep=x.notna()&w.notna()&(w>0)
    x=x[keep].to_numpy(float); w=w[keep].to_numpy(float)
    if not len(x): return float('nan')
    if not np.isfinite(x).all() or not np.isfinite(w).all() or (x<0).any(): raise ValueError('Gini inputs must be finite and nonnegative.')
    mean=float(np.sum(w*x)/np.sum(w))
    if mean==0:return 0.
    return float(np.sum((w[:,None]*w[None,:])*np.abs(x[:,None]-x[None,:]))/(2*np.sum(w)**2*mean))


def summarize_distribution(burden:pd.DataFrame,population:pd.Series,quartile:pd.Series)->pd.Series:
    """Return absolute group burdens, two population denominators, gaps and Gini."""
    pop=pd.to_numeric(population,errors='raise'); pop.index=pop.index.astype(str); pop=pop.reindex(burden.index)
    q=quartile.copy(); q.index=q.index.astype(str); q=q.reindex(burden.index)
    if pop.isna().any() or (pop<0).any() or q.isna().any(): raise ValueError('Population/quartile coverage is incomplete.')
    resolved=burden.status.eq('resolved'); norm=burden.normalized_burden_hr
    out={}
    denom=float(pop[resolved].sum()); out['population_weighted_normalized_burden_hr']=float((pop[resolved]*norm[resolved]).sum()/denom) if denom>0 else np.nan
    mass_weight=pop*burden.resolved_mass; denom_mass=float(mass_weight[resolved].sum()); out['population_resolved_mass_weighted_burden_hr']=float((pop[resolved]*burden.restoration_burden_mass_hr[resolved]).sum()/denom_mass) if denom_mass>0 else np.nan
    for label in ['Q1','Q2','Q3','Q4']:
        use=resolved&q.eq(label); d=float(pop[use].sum()); out[f'burden_{label}_hr']=float((pop[use]*norm[use]).sum()/d) if d>0 else np.nan
    out['signed_Q4_minus_Q1_hr']=out['burden_Q4_hr']-out['burden_Q1_hr']; out['absolute_Q4_minus_Q1_hr']=abs(out['signed_Q4_minus_Q1_hr'])
    out['burden_gini']=population_weighted_gini(norm[resolved],pop[resolved]); out['resolved_tract_count']=int(resolved.sum()); out['unresolved_tract_count']=int((~resolved).sum())
    return pd.Series(out)


def classify_tract_effects(candidate:pd.Series,reference:pd.Series,*,practical_threshold_hr:float=1.)->pd.DataFrame:
    """Classify candidate-reference burden; threshold is practical, not inferential."""
    if practical_threshold_hr<0: raise ValueError('Threshold must be nonnegative.')
    ids=pd.Index(sorted(set(candidate.index.astype(str))|set(reference.index.astype(str))))
    a=candidate.copy();a.index=a.index.astype(str);b=reference.copy();b.index=b.index.astype(str);delta=a.reindex(ids)-b.reindex(ids)
    label=pd.Series('near-zero',index=ids,dtype=object);label[delta<-practical_threshold_hr]='improved';label[delta>practical_threshold_hr]='worsened';label[delta.isna()]='unresolved'
    return pd.DataFrame({'delta_burden_hr':delta,'classification':label},index=ids)


def paired_realization_summary(metric_by_strategy:pd.DataFrame,reference_strategy:str,*,bootstrap_resamples:int=10000,bootstrap_seed:int=42)->pd.DataFrame:
    """Summarize paired differences using realizations as the resampling unit."""
    if reference_strategy not in metric_by_strategy: raise KeyError(reference_strategy)
    if bootstrap_resamples<=0: raise ValueError('bootstrap_resamples must be positive.')
    ref=pd.to_numeric(metric_by_strategy[reference_strategy],errors='coerce');rng=np.random.default_rng(bootstrap_seed);rows=[]
    for strategy in metric_by_strategy.columns:
        if strategy==reference_strategy:continue
        delta=(pd.to_numeric(metric_by_strategy[strategy],errors='coerce')-ref).dropna().to_numpy(float);n=len(delta)
        if not n: rows.append({'strategy':strategy,'n_realizations':0,'paired_mean_difference':np.nan,'paired_median_difference':np.nan,'fraction_delta_below_zero':np.nan,'bootstrap_ci_low':np.nan,'bootstrap_ci_high':np.nan});continue
        samples=rng.choice(delta,size=(bootstrap_resamples,n),replace=True).mean(axis=1);low,high=np.quantile(samples,[.025,.975])
        rows.append({'strategy':strategy,'n_realizations':n,'paired_mean_difference':float(delta.mean()),'paired_median_difference':float(np.median(delta)),'fraction_delta_below_zero':float(np.mean(delta<0)),'bootstrap_ci_low':float(low),'bootstrap_ci_high':float(high)})
    return pd.DataFrame(rows).set_index('strategy')

