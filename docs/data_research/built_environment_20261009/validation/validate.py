"""Existing-label descriptive audit, not a clustering or simulation entry point."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile
import itertools
import subprocess
import platform
import numpy as np
import pandas as pd
from scipy import stats

ROOT=Path(__file__).resolve().parent
STAGE7=Path('Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized')
AUDIT=Path('docs/data_research/built_environment_20261009')
REPS=[f'Var_Rep{i}' for i in range(1,81)]
FEATURES=['T80','Init_Supply','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','Pre_1970_Ratio','Pop_Density','NRI_RISK_SCORE','NRI_BUILDVALUE','SOVI_SCORE']
GROUPS={'housing_5plus_share':('B25024',[6,7,8,9]),
        'housing_10plus_share':('B25024',[7,8,9]),
        'housing_single_unit_share':('B25024',[2,3]),
        'housing_2to4_share':('B25024',[4,5]),
        'housing_mobile_other_share':('B25024',[10,11]),
        'Pre_1970_Ratio':('B25034',[8,9,10,11])}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

def dump(name,value):
    (ROOT/name).write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf8')

def read_ids(path):
    f=pd.read_csv(path,dtype={'tract_id':str})
    f['tract_id']=f.tract_id.str.zfill(11)
    assert f.tract_id.str.fullmatch(r'06037\d{6}').all() and not f.tract_id.duplicated().any()
    return f

def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])

def preserve(repo,verify=False):
    baseline=json.loads((repo/AUDIT/'PRESERVATION_BASELINE.json').read_text())
    current={p:sha(repo/p) for p in baseline['protected_files']}
    assert current==baseline['protected_files'], 'Protected-file change detected'
    staged=hashlib.sha256(git(repo,'diff','--cached','--raw','-z')).hexdigest()
    originals={p.relative_to(repo).as_posix():sha(p) for p in (repo/AUDIT).rglob('*') if p.is_file() and 'validation' not in p.relative_to(repo/AUDIT).parts}
    result={'head':git(repo,'rev-parse','HEAD').decode().strip(),'branch':git(repo,'branch','--show-current').decode().strip(),
            'protected_count':len(current),'protected_unchanged':True,'staged_diff_raw_sha256':staged,'original_audit_files':originals}
    assert result['branch']=='revision/reviewer-driven-core-rebuild-v2'
    if verify:
        previous=json.loads((ROOT/'VALIDATION_PRESERVATION_BASELINE.json').read_text())
        assert staged==previous['staged_diff_raw_sha256'], 'Unrelated staged changes changed'
        assert originals==previous['original_audit_files'], 'Original audit changed'
    else:
        assert result['head'].startswith('dab9761')
    dump('VALIDATION_PRESERVATION_VERIFIED.json' if verify else 'VALIDATION_PRESERVATION_BASELINE.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='original_audit_files'}),flush=True)

def vre(table):
    archive=ROOT/f'sources/{table}_06.csv.zip'
    with zipfile.ZipFile(archive) as z:
        frame=pd.read_csv(z.open(z.namelist()[0]),dtype={'GEOID':str})
    frame=frame.loc[frame.GEOID.str.startswith('1400000US06037',na=False)].copy()
    frame['tract_id']=frame.GEOID.str[-11:]
    frame['ORDER']=frame.ORDER.astype(int)
    assert len(frame)==2498*11 and not frame.duplicated(['tract_id','ORDER']).any()
    assert frame[['ESTIMATE','MOE']+REPS].notna().all().all()
    frame.to_csv(ROOT/f'sources/{table}_VRE_LA.csv',index=False)
    return frame

def ratio(n,d):
    return np.divide(n,d,out=np.zeros_like(n,dtype=float),where=d!=0)

def acs(repo):
    full=read_ids(repo/STAGE7/'stage7_full_domain_tract_status.csv')
    labels=read_ids(repo/STAGE7/'clusters_labels_final.csv')
    assert (len(full),len(labels))==(2315,2291)
    data={t:vre(t) for t in ['B25024','B25034']}
    pilot=read_ids(repo/AUDIT/'BUILT_ENVIRONMENT_TRACT_COVERAGE.csv').set_index('tract_id').loc[full.tract_id]
    denominators={t:f.loc[f.ORDER.eq(1)].set_index('tract_id').loc[full.tract_id] for t,f in data.items()}
    assert np.array_equal(denominators['B25024'].ESTIMATE,denominators['B25034'].ESTIMATE)
    for order in range(1,12):
        source=data['B25024'].loc[data['B25024'].ORDER.eq(order)].set_index('tract_id').loc[full.tract_id]
        for kind,col in [('E','ESTIMATE'),('M','MOE')]:
            assert np.array_equal(source[col],pilot[f'B25024_{order:03d}{kind}'])
    out=full[['tract_id','Housing_Units_Total']].copy().set_index('tract_id')
    D=denominators['B25024'].ESTIMATE.to_numpy()
    out['housing_total']=D
    assert np.array_equal(D,out.Housing_Units_Total) and np.array_equal(D,pilot.B25024_001E)
    weight=pd.read_csv(ROOT/'sources/VRE_AVERAGE_WEIGHT_2022.csv',dtype={'FIPS_STATE_CODE':str})
    aw=float(weight.loc[weight.FIPS_STATE_CODE.eq('6'),'AVERAGE_WEIGHT'].iloc[0]); assert aw==16
    out['denominator_ci90_includes_zero']=D<=denominators['B25024'].MOE.to_numpy()
    matrices={}
    for name,(table,orders) in GROUPS.items():
        frame=data[table]; denom=denominators[table]
        num=frame.loc[frame.ORDER.isin(orders)].groupby('tract_id')[['ESTIMATE','MOE']+REPS].sum().loc[full.tract_id]
        numerator=num.ESTIMATE.to_numpy(); denominator=denom.ESTIMATE.to_numpy()
        p=np.divide(numerator,denominator,out=np.full(len(out),np.nan),where=denominator>0)
        rep=ratio(num[REPS].to_numpy(),denom[REPS].to_numpy())
        se=np.sqrt(.05*np.square(rep-p[:,None]).sum(axis=1))
        boundary=(p==0)|(p==1)|(se==0)
        pstar=np.minimum(.5,ratio(np.full(len(out),2.3*aw),denominator))
        boundary_se=np.sqrt(pstar*(1-pstar)*ratio(np.full(len(out),aw),denominator))
        se=np.where(boundary,boundary_se,se)
        out[name]=p
        out[name+'_moe90']=1.645*se
        out[name+'_boundary_model']=boundary & (denominator>0)
        out[name+'_zero_replicate_denominators']=(denom[REPS].to_numpy()==0).sum(axis=1)
        out[name+'_ci90_low']=np.maximum(0,p-1.645*se)
        out[name+'_ci90_high']=np.minimum(1,p+1.645*se)
        matrices[name]={'point':p,'rep':rep,'se':se,'boundary':boundary,'numerator':numerator,
                        'num_rep':num[REPS].to_numpy(),'denominator':denominator,'den_rep':denom[REPS].to_numpy()}
        if table=='B25024':
            assert np.array_equal(numerator, frame.loc[frame.ORDER.isin(orders)].groupby('tract_id').ESTIMATE.sum().loc[full.tract_id])
    assert np.allclose(out.housing_5plus_share,pilot.housing_5plus_share,equal_nan=True)
    assert np.allclose(out.loc[labels.tract_id,'Pre_1970_Ratio'],labels.Pre_1970_Ratio,atol=1e-12)
    # Reproduce the original subset-proportion approximation, preserving its identity.
    frame=data['B25024']; order_m=frame.loc[frame.ORDER.isin([6,7,8,9])].assign(M2=lambda x:x.MOE**2).groupby('tract_id').M2.sum().loc[full.tract_id].to_numpy()
    p=out.housing_5plus_share.to_numpy(); md=denominators['B25024'].MOE.to_numpy()
    minus=order_m-p*p*md*md; fallback=minus<0
    approx=np.sqrt(np.where(fallback,order_m+p*p*md*md,minus))/np.where(D>0,D,np.nan)
    assert np.allclose(approx,pilot.housing_5plus_share_moe90,equal_nan=True)
    out['housing_5plus_share_approx_moe90']=approx
    out['approx_plus_ratio_fallback']=fallback
    out['cluster']=out.index.map(labels.set_index('tract_id').cluster)
    out['residential_member']=out.cluster.notna()
    out['acs_status']=np.where(D>0,'valid_estimate','zero_housing_denominator')
    out['dominant_configuration']=None
    valid=out.housing_total.gt(0)
    out.loc[valid,'dominant_configuration']=out.loc[valid,['housing_single_unit_share','housing_2to4_share','housing_5plus_share','housing_mobile_other_share']].idxmax(axis=1)
    out.to_csv(ROOT/'ACS_TRACT_VALIDATION.csv',index=True)
    for name,m in matrices.items():
        np.savez_compressed(ROOT/f'_{name}_replicates.npz',tract_id=out.index.to_numpy(dtype=str),**m)
    eligible=out.loc[out.residential_member]
    summary={'study_n':2315,'residential_n':2291,'record_matches':2315,'zero_denominators':int((D==0).sum()),
             'valid_study_estimates':int((D>0).sum()),'valid_residential_estimates':int(eligible.housing_5plus_share.notna().sum()),
             'all_b25024_b25034_totals_equal':True,'age_and_configuration_point_values_reproduced':True,
             'approx_gt10pp':int(eligible.housing_5plus_share_approx_moe90.gt(.10).sum()),
             'vre_gt10pp':int(eligible.housing_5plus_share_moe90.gt(.10).sum()),
             'vre_gt5pp':int(eligible.housing_5plus_share_moe90.gt(.05).sum()),
             'vre_moe90_median_pp':float(eligible.housing_5plus_share_moe90.median()*100),
             'vre_moe90_p90_pp':float(eligible.housing_5plus_share_moe90.quantile(.9)*100),
             'boundary_model_n':int(eligible.housing_5plus_share_boundary_model.sum()),
             'denominator_ci_includes_zero_n':int(eligible.denominator_ci90_includes_zero.sum()),
             'undefined_replicate_denominators_n':int(eligible.housing_5plus_share_zero_replicate_denominators.gt(0).sum()),
             'california_average_weight':aw,'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__}
    dump('ACS_VERIFICATION.json',summary);print(json.dumps(summary),flush=True)

def eta(values,clusters):
    values=np.asarray(values); clusters=np.asarray(clusters); grand=values.mean()
    den=np.square(values-grand).sum()
    return float(sum((clusters==c).sum()*(values[clusters==c].mean()-grand)**2 for c in np.unique(clusters))/den) if den else 0.

def weighted_diag(y,se):
    w=1/np.square(se); fixed=np.dot(w,y)/w.sum()
    q=np.dot(w,np.square(y-fixed)); c=w.sum()-np.dot(w,w)/w.sum()
    tau2=max(0.,(q-(len(y)-1))/c)
    w=1/(np.square(se)+tau2); w=w/w.sum()
    return {'precision_random_effects_mean':float(np.dot(w,y)),'tau2':float(tau2),
            'kish_effective_n':float(1/np.dot(w,w)),'largest_weight':float(w.max())}

def comparisons(repo):
    ac=read_ids(ROOT/'ACS_TRACT_VALIDATION.csv').set_index('tract_id')
    d=read_ids(repo/STAGE7/'clusters_labels_final.csv').set_index('tract_id')
    d=d.join(ac.drop(columns=['cluster','Pre_1970_Ratio']))
    if (ROOT/'NLCD_TRACT_EXTRACTION.csv').exists():
        d=d.join(read_ids(ROOT/'NLCD_TRACT_EXTRACTION.csv').set_index('tract_id'))
    names=['Pre_1970_Ratio','housing_5plus_share','housing_10plus_share','housing_single_unit_share']
    if 'impervious_land_fraction' in d:names+=['impervious_land_fraction']
    tables=[]; pairs=[]; bias=[]; effects=[]; precision=[]
    repdata={n:dict(np.load(ROOT/f'_{n}_replicates.npz',allow_pickle=False)) for n in names if n in GROUPS}
    for n,m in repdata.items():
        positions=pd.Series(np.arange(len(m['tract_id'])),index=m['tract_id']).loc[d.index].to_numpy()
        repdata[n]={k:v[positions] for k,v in m.items() if k!='tract_id'}
    masks={'all':np.ones(len(d),bool),'vre_moe_le10pp':d.housing_5plus_share_moe90.le(.10).to_numpy(),
           'vre_moe_le5pp':d.housing_5plus_share_moe90.le(.05).to_numpy(),
           'approx_moe_le10pp':d.housing_5plus_share_approx_moe90.le(.10).to_numpy(),
           'approx_moe_le5pp':d.housing_5plus_share_approx_moe90.le(.05).to_numpy(),
           'housing_total_ge100':d.housing_total.ge(100).to_numpy()}
    for screen,mask in masks.items():
        for name in names:
            grouprep={}
            for cluster in sorted(d.cluster.unique()):
                ix=mask & d.cluster.eq(cluster).to_numpy(); y=d.loc[ix,name].to_numpy(); original=d.loc[d.cluster.eq(cluster),name]
                assert len(y)>1
                row={'screen':screen,'indicator':name,'cluster':int(cluster),'n_original':len(original),'n':len(y),
                     'retention_fraction':len(y)/len(original),'mean':float(y.mean()),'median':float(np.median(y)),
                     'p10':float(np.quantile(y,.1)),'p25':float(np.quantile(y,.25)),'p75':float(np.quantile(y,.75)),
                     'p90':float(np.quantile(y,.9)),'sd':float(y.std(ddof=1)), 'mean_change_from_all':float(y.mean()-original.mean())}
                if name in repdata:
                    m=repdata[name]; rp=m['rep'][ix].mean(axis=0); sdrse=float(np.sqrt(.05*np.square(rp-y.mean()).sum()))
                    supplement=float(m['se'][ix&m['boundary']].sum()/len(y))
                    moe=1.645*(sdrse+supplement)
                    row.update(mean_sdr_se=sdrse,boundary_se_triangle_supplement=supplement,mean_moe90_augmented=moe,
                               mean_ci90_low=max(0.,y.mean()-moe),mean_ci90_high=min(1.,y.mean()+moe),
                               tract_moe90_median=float(d.loc[ix,name+'_moe90'].median()),tract_moe90_p90=float(d.loc[ix,name+'_moe90'].quantile(.9)),
                               tract_gt10pp=int(d.loc[ix,name+'_moe90'].gt(.10).sum()),tract_gt5pp=int(d.loc[ix,name+'_moe90'].gt(.05).sum()))
                    pooled=m['numerator'][ix].sum()/m['denominator'][ix].sum()
                    pooledrep=ratio(m['num_rep'][ix].sum(axis=0),m['den_rep'][ix].sum(axis=0))
                    pooledmoe=1.645*np.sqrt(.05*np.square(pooledrep-pooled).sum())
                    row.update(housing_unit_weighted_share=float(pooled),housing_unit_weighted_moe90=float(pooledmoe))
                    grouprep[cluster]=(rp,supplement)
                    if screen=='all':
                        precision.append(dict(cluster=int(cluster),indicator=name,n=len(y),**weighted_diag(y,m['se'][ix])))
                else:
                    row.update(coverage_min=float(d.loc[ix,'valid_coverage_fraction'].min()),valid_area_m2=float(d.loc[ix,'valid_area_m2'].sum()))
                tables.append(row)
            effects.append({'screen':screen,'indicator':name,'n':int(mask.sum()),'eta_squared':eta(d.loc[mask,name],d.loc[mask,'cluster'])})
            for a,b in itertools.combinations(sorted(d.cluster.unique()),2):
                xa=d.loc[mask & d.cluster.eq(a).to_numpy(),name].to_numpy(); xb=d.loc[mask & d.cluster.eq(b).to_numpy(),name].to_numpy()
                diff=xa.mean()-xb.mean(); df=len(xa)+len(xb)-2
                pooledsd=np.sqrt(((len(xa)-1)*xa.var(ddof=1)+(len(xb)-1)*xb.var(ddof=1))/df)
                g=(1-3/(4*df-1))*diff/pooledsd if pooledsd else np.nan
                u=stats.mannwhitneyu(xa,xb,method='asymptotic').statistic
                row={'screen':screen,'indicator':name,'cluster_a':int(a),'cluster_b':int(b),'n_a':len(xa),'n_b':len(xb),
                     'mean_difference':float(diff),'hedges_g':float(g),'cliffs_delta':float(2*u/(len(xa)*len(xb))-1)}
                if name in repdata:
                    ra,sa=grouprep[a];rb,sb=grouprep[b]
                    moe=1.645*(np.sqrt(.05*np.square(ra-rb-diff).sum())+sa+sb)
                    row.update(difference_moe90_augmented=float(moe),difference_ci90_low=float(diff-moe),difference_ci90_high=float(diff+moe),
                               ci90_excludes_zero=bool(abs(diff)>moe))
                pairs.append(row)
        for cluster in sorted(d.cluster.unique()):
            ix=d.cluster.eq(cluster).to_numpy(); keep=ix&mask; lose=ix&~mask
            row={'screen':screen,'group_type':'cluster','group':str(cluster),'n_original':int(ix.sum()),'n_retained':int(keep.sum()),'n_removed':int(lose.sum()),
                 'retention_fraction':float(keep.sum()/ix.sum())}
            for var in ['housing_5plus_share','Pre_1970_Ratio','Pop_Density','SOVI_SCORE','housing_total']:
                row[var+'_retained_mean']=float(d.loc[keep,var].mean())
                row[var+'_removed_mean']=float(d.loc[lose,var].mean()) if lose.any() else None
            bias.append(row)
        for configuration in d.dominant_configuration.unique():
            ix=d.dominant_configuration.eq(configuration).to_numpy()
            bias.append({'screen':screen,'group_type':'dominant_configuration','group':configuration,'n_original':int(ix.sum()),
                         'n_retained':int((ix&mask).sum()),'n_removed':int((ix&~mask).sum()),'retention_fraction':float((ix&mask).sum()/ix.sum())})
    for filename,rows in [('CLUSTER_COMPARISONS.csv',tables),('CLUSTER_PAIRWISE_EFFECTS.csv',pairs),('CLUSTER_EFFECT_SIZES.csv',effects),
                          ('ACS_SCREENING_BIAS.csv',bias),('ACS_PRECISION_WEIGHTING.csv',precision)]:pd.DataFrame(rows).to_csv(ROOT/filename,index=False)
    transformed=d[FEATURES].copy(); transformed['Pop_Density']=np.log1p(transformed.Pop_Density); transformed['NRI_BUILDVALUE']=np.log1p(transformed.NRI_BUILDVALUE)
    candidates=[n for n in names if n!='Pre_1970_Ratio']
    allvars=transformed.join(d[candidates]); cor=[]
    for a,b in itertools.combinations(allvars.columns,2):
        if a not in candidates and b not in candidates:continue
        x=allvars[a].to_numpy();y=allvars[b].to_numpy()
        cor.append({'variable_a':a,'variable_b':b,'n':len(x),'pearson_r':float(stats.pearsonr(x,y).statistic),'spearman_rho':float(stats.spearmanr(x,y).statistic)})
    pd.DataFrame(cor).to_csv(ROOT/'INDICATOR_CORRELATIONS.csv',index=False)
    sensitivity=[]
    for screen,mask in masks.items():
        for name in candidates:
            for control in ['Pre_1970_Ratio','Pop_Density','SOVI_SCORE']:
                x=allvars.loc[mask,name];y=allvars.loc[mask,control]
                sensitivity.append({'screen':screen,'indicator':name,'control':control,'n':len(x),
                                    'pearson_r':float(stats.pearsonr(x,y).statistic),'spearman_rho':float(stats.spearmanr(x,y).statistic)})
    pd.DataFrame(sensitivity).to_csv(ROOT/'INDICATOR_CORRELATION_SENSITIVITY.csv',index=False)
    incremental=[]
    controlsets={'age_density':['Pre_1970_Ratio','Pop_Density'],
                 'age_density_social':['Pre_1970_Ratio','Pop_Density','SOVI_SCORE'],
                 'all_existing_features':FEATURES}
    if 'impervious_land_fraction' in d:controlsets['age_density_social_configuration']=['Pre_1970_Ratio','Pop_Density','SOVI_SCORE','housing_5plus_share']
    for name in candidates:
        for label,controls in controlsets.items():
            if name in controls:continue
            X=allvars[controls].to_numpy();X=(X-X.mean(axis=0))/X.std(axis=0)
            X=np.column_stack([np.ones(len(X)),X]);y=d[name].to_numpy();coef=np.linalg.lstsq(X,y,rcond=None)[0];resid=y-X@coef
            r2=1-np.dot(resid,resid)/np.square(y-y.mean()).sum()
            incremental.append({'indicator':name,'controls':label,'n':len(y),'ols_r_squared':float(r2),'residual_fraction':float(1-r2),
                                'conditional_vif':float(1/(1-r2)),'residual_cluster_eta_squared':eta(resid,d.cluster),'design_condition_number':float(np.linalg.cond(X))})
    pd.DataFrame(incremental).to_csv(ROOT/'INDICATOR_INCREMENTAL_INFORMATION.csv',index=False)
    d.to_csv(ROOT/'RESIDENTIAL_VALIDATION_MATRIX.csv',index=True)
    coverage=ac.reset_index().merge(read_ids(ROOT/'NLCD_TRACT_EXTRACTION.csv'),on='tract_id',validate='one_to_one') if (ROOT/'NLCD_TRACT_EXTRACTION.csv').exists() else ac.reset_index().assign(nlcd_status='not_extracted')
    coverage.to_csv(ROOT/'BUILT_ENVIRONMENT_TRACT_COVERAGE.csv',index=False)
    summary=pd.DataFrame(tables);eff=pd.DataFrame(effects)
    print(summary.loc[(summary.screen=='all')&summary.indicator.isin(['housing_5plus_share','impervious_land_fraction']),['indicator','cluster','n','mean','median','mean_moe90_augmented']].to_string(index=False),flush=True)
    print(eff.loc[eff.screen.eq('all')].to_string(index=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--phase',choices=['baseline','verify','acs','compare'],required=True);a=p.parse_args()
    if a.phase in ['baseline','verify']:preserve(a.repo,a.phase=='verify')
    elif a.phase=='acs':acs(a.repo)
    else:comparisons(a.repo)
