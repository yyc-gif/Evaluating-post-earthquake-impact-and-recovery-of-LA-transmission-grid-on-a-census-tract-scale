"""Recover frozen P2 fits and audit Path B. No model fitting or simulation."""
from pathlib import Path
import hashlib
import io
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr
from sklearn.metrics import adjusted_rand_score, silhouette_samples

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE = ROOT / 'docs/data_research/stage7_path_b_p2_integration_review_20261014'
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
sys.path.append(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages')
import consolidate_current_figure_suite as u
u.ROOT = ROOT

MP = '81c3452e29abc109f50564d39035c06225e3ea84'
FD = '05a78645b17bf8de04326e54181f9db432d7186c'
SF = '0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
HN = '49cc153c3f4d7a8c29cf94baf090dbfc0be4d068'
MPD = 'docs/data_research/stage7_multi_policy_typology_20261012/'
FDD = 'docs/data_research/stage7_fig7d_policy_robustness_and_final_integration_gate_20261013/'
SFD = 'docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/'
HND = 'docs/data_research/stage7_nhi_nri_multihazard_comparative_audit_20261012/'
FEATURES = ['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained',
            'MeanDelta','SOVI_SCORE','log1p_Population']
BUDGET = np.array([1/9,1/9,1/9,1/6,1/6,1/6,1/6])
COLORS = ['#147f98','#d07734','#7a5899']
POLICIES = ['impact-first','hospital-first','degree-first','betweenness-first','vulnerability-first']
SOURCES = []
OFFLINE = '--archived-inputs' in sys.argv


def source(commit, directory, name, target=None):
    p = HERE / 'inputs' / (target or name)
    if OFFLINE:
        records=[]
        for registry in ['SOURCE_PAYLOAD_HASHES.csv','RARE_Q_SOURCE_HASH.csv']:
            manifest=HERE/registry
            if Path(u.lp(manifest)).exists():
                records.extend(pd.read_csv(u.lp(manifest)).to_dict('records'))
        record=next(r for r in records if r['commit']==commit and r['path']==directory+name)
        raw=open(u.lp(p),'rb').read()
        assert u.digest(raw)==record['sha256'] and len(raw)==record['bytes']
        SOURCES.append(record)
        return raw
    method='Git blob or SHA-verified shared LFS payload'
    try:
        raw = u.payload(commit, directory + name)
    except FileNotFoundError:
        # The retained interpretation checkout has real bytes absent from shared LFS cache.
        if commit!='66d16d61b13c05785f58795ef9d13ba82ece472e':raise
        pointer=u.git('show',f'{commit}:{directory+name}')
        oid=re.search(rb'oid sha256:([0-9a-f]{64})',pointer).group(1).decode()
        raw=open(u.lp(ROOT.parent/'_ti12'/directory/name),'rb').read()
        assert u.digest(raw)==oid
        method='Retained interpretation worktree payload, exact Git LFS OID verified'
    u.write(p, raw)
    SOURCES.append(dict(commit=commit, path=directory+name, archived_path=str(p.relative_to(HERE)).replace('\\','/'),
                        bytes=len(raw), sha256=u.digest(raw), actual_payload_verified=True,acquisition=method))
    return raw


def read(name):
    return pd.read_csv(u.lp(HERE / 'inputs' / name), dtype={'tract_id':str},float_precision='round_trip')


def save(name, frame):
    u.write(HERE / name, frame.to_csv(index=False, float_format='%.17g', lineterminator='\n'))


def dump(name, obj):
    u.dump(HERE / name, obj)


def load_frozen():
    d = pd.read_csv(u.lp(HERE / 'FROZEN_P2_TRACT_TABLE_2315.csv'),dtype={'tract_id':str},float_precision='round_trip')
    return d.set_index('tract_id').sort_index()


def main():
    before_path=HERE/'PRESERVATION_BEFORE.json'
    if not OFFLINE and not Path(u.lp(before_path)).exists():
        ref=json.load(open(u.lp(ROOT/'docs/reproducibility/figure_suite_concise_captions_20261013/PRESERVATION_BEFORE.json')))
        dump('PRESERVATION_BEFORE.json',u.protected_snapshot(ref))
    if not OFFLINE and not Path(u.lp(HERE/'STARTING_REVIEW_STATE.json')).exists():
        dump('STARTING_REVIEW_STATE.json',dict(branch=u.git('branch','--show-current').decode().strip(),
            HEAD=u.git('rev-parse','HEAD').decode().strip(),status=u.git('status','--porcelain=v1').decode(),
            scientific_scope='Review package only; no K-means fits, physical calculation or formal promotion'))
    source(MP,'docs/methodology/','STAGE7_SVI_HARMONIZATION_DECISION.md')
    source(MP,'docs/data_research/stage7_rq_driven_variable_audit_20261011/','GRID_DEFINITION_QA.json')
    for n in ['VERIFIED_DESCRIPTORS_2315.csv','MULTIPOLICY_RQ2_TRACT_VALUES.csv','REGISTERED_FIT_ARRAYS.npz',
              'VERIFIED_WEIGHTED_MATRICES.npz','SPATIAL_REFIT_LABELS.npz','COHORT_STANDARDIZATION_AND_WEIGHTS.csv',
              'A_VS_P2_VS_P3_CLUSTERING_RESULTS.csv','SEED_STABILITY.csv','SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv',
              'POLICY_SET_CLUSTER_STABILITY.csv','PER_CLUSTER_SILHOUETTE_AND_SIZE.csv',
              'RARE_Q_GROUP_MEMBERSHIP_AUDIT.csv','INIT_ALGEBRAIC_DISTANCE_DIAGNOSTICS.csv',
              'POLICY_ENSEMBLE_QA.json','REGISTERED_ANALYSIS.json','FROZEN_EVENT_VERIFICATION.csv',
              'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz','VULNERABILITY_FIRST_CIRCULARITY_AUDIT.md']:
        source(MP,MPD,n)
    for n in ['FROZEN_POLICY_TRACT_MEANS_2315.csv','VERIFIED_ORIGINAL_94_GEOIDS.csv',
              'Q4_VS_NONQ4_EFFECT_SIZES.csv','FIXED_VS_RECOMPUTED_P75_THRESHOLDS.csv',
              'THRESHOLD_P70_P75_P80_SENSITIVITY.csv','SPATIAL_COMMON_SUPPORT_STANDARDIZATION.csv',
              'SPATIAL_DEPENDENCE_DIAGNOSTICS.csv','SPATIAL_BLOCK_ASSIGNMENTS.csv',
              'FROZEN_SOURCE_IDENTITY_QA.json','FROZEN_POLICY_SOURCE_PAIRING_QA.csv',
              'FROZEN_FIVE_POLICY_TOTAL_DEFICIT_IDENTITY_QA.csv','PHYSICAL_REALIZATION_IDENTITY.csv',
              'FORMAL_PROMOTION_PATH_REGISTRY.csv','FORMAL_DEPENDENCY_MATCHES.csv',
              'MANUSCRIPT_AUTHORITY_PATH_AUDIT.csv']:
        source(FD,FDD,n)
    source(FD,FDD,'inputs/FULL_2315_GEOMETRY.gpkg','FULL_2315_GEOMETRY.gpkg')
    for n in ['NCV_VECTOR.csv','NCV_HAZARD_COMPONENTS.csv','NCV_CA_AND_LA_EXTREMA.csv','SOURCE_HAZARD_FIELD_REGISTER.csv']:
        source(SF,SFD+'inputs/',n)
    for n in ['01_NATURAL_HAZARD_FINAL_DEFINITION_AND_EVIDENCE.md',
              'EARTHQUAKE_NRI_CGS_SPATIAL_RANK_COMPARISON.csv',
              'WEATHER_SOURCE_SCALE_AND_DEFAULT_AUDIT.csv','WEATHER_PAIRWISE_DEPENDENCE.csv',
              'HAZARD_SET_AND_NORMALIZATION_EFFECTIVE_INFLUENCE.csv']:
        source(SF,SFD,n)
    for n in ['WILLIAMS_2024_NCV_METHOD_REPLICATION.md','FEMA_NCV_TRACT_SCALE_ADAPTATION_AND_LIMITATIONS.md',
              'FEMA_NCV_EFFECTIVE_HAZARD_CONTRIBUTIONS.csv','HAZARD_LEAVE_ONE_OUT_RANK_SENSITIVITY.csv']:
        source(HN,HND,n)
    source(SF,SFD,'candidate/K3_CLUSTER_MEMBERSHIP.csv','HISTORICAL_EIGHT_VARIABLE_K3_MEMBERSHIP.csv')
    save('SOURCE_PAYLOAD_HASHES.csv',pd.DataFrame(SOURCES))

    d=read('VERIFIED_DESCRIPTORS_2315.csv').set_index('tract_id').sort_index()
    r=read('MULTIPOLICY_RQ2_TRACT_VALUES.csv').query("policy_set == 'main5'").set_index('tract_id').sort_index()
    p=read('FROZEN_POLICY_TRACT_MEANS_2315.csv').set_index('tract_id').sort_index()
    assert d.index.is_unique and len(d)==2315 and d.index.equals(r.index) and d.index.equals(p.index)
    assert all(len(x)==11 and x.isdigit() for x in d.index)
    for c in ['Population','frozen_SOVI_quartile']:
        assert (d[c]==p[c]).all()
    d['B_Unconstrained']=r['B_Unconstrained']
    d['MeanDelta']=r['MeanDelta']
    d['MeanTotal5']=d['B_Unconstrained']+d['MeanDelta']
    pol=p[['B_'+x for x in POLICIES]].to_numpy()
    identity=np.max(np.abs(pol.mean(1)-d.MeanTotal5))
    assert identity<1e-11
    assert np.max(np.abs(d.B_Unconstrained-p.B_unconstrained))<1e-12
    assert np.max(np.abs(d.MeanDelta-p.MeanDelta5))<1e-12
    assert np.max(np.abs(np.log1p(d.Population)-d.log1p_Population))<1e-14
    ncv=read('NCV_VECTOR.csv').set_index('tract_id')
    assert ncv.index.is_unique and d.index[d.Population>0].isin(ncv.index).all()
    d['FEMA_NCV14_CA_v119']=ncv.FEMA_NCV14_CA_v119
    eligible=d.Population>0
    x=d.loc[eligible,FEATURES].copy()
    assert len(x)==2299 and np.isfinite(x.to_numpy()).all()
    assert d.loc[eligible,'Population'].sum()==9066522 and (~eligible).sum()==16
    assert d.loc[eligible,'additional_zero_housing_positive_population'].sum()==8
    assert d.loc[eligible,'frozen_SOVI_quartile'].eq('Q4').sum()==579
    arrays=np.load(u.lp(HERE/'inputs/REGISTERED_FIT_ARRAYS.npz'),allow_pickle=False)
    assert np.array_equal(x.index.to_numpy(),arrays['tract_ids'])
    keys=arrays['keys'].tolist()
    weighted=np.load(u.lp(HERE/'inputs/VERIFIED_WEIGHTED_MATRICES.npz'))
    z=(x-x.mean())/x.std(ddof=0)
    w=z.to_numpy()*np.sqrt(BUDGET)
    assert np.max(np.abs(w-weighted['P2__main5__cohort']))<2e-13, np.max(np.abs(w-weighted['P2__main5__cohort']))
    standard=pd.DataFrame(dict(variable=FEATURES,cohort_mean=x.mean(),population_SD=x.std(ddof=0),
                              squared_distance_budget=BUDGET,coordinate_multiplier=np.sqrt(BUDGET)))
    save('P2_STANDARDIZER_AND_WEIGHTS.csv',standard)
    save('P2_COHORT_ELIGIBILITY_2315.csv',d[['Population','residential_member',
        'additional_zero_housing_positive_population','frozen_SOVI_quartile']].assign(
        eligible=eligible,exclusion_reason=np.where(eligible,'','Frozen formal population equals zero')).reset_index())
    profiles=[];poprows=[];contributions=[];fitqa=[];silrows=[];members=[]
    y3=None;y4=None
    for k in [3,4]:
        key=f'P2__main5__cohort__k{k}__s42'
        j=keys.index(key);y=arrays['labels'][j]
        if k==3:y3=y.copy()
        else:y4=y.copy()
        s=silhouette_samples(w,y,metric='euclidean')
        assert np.max(np.abs(s-arrays['silhouette'][j]))<2e-12
        inertia=0
        for c in range(k):
            m=y==c;g=d.loc[x.index[m]]
            centroid=w[m].mean(0)
            inertia+=float(np.sum((w[m]-centroid)**2))
            for variable in FEATURES+['Population','MeanTotal5','FEMA_NCV14_CA_v119','T80']:
                v=g[variable].dropna()
                profiles.append(dict(model=f'P2_K{k}',class_id=f'C{c+1}',variable=variable,n=len(v),
                    mean=v.mean(),median=v.median(),P10=v.quantile(.1),P90=v.quantile(.9),
                    min=v.min(),max=v.max(),sd=v.std(ddof=0)))
            row=dict(model=f'P2_K{k}',class_id=f'C{c+1}',tracts=int(m.sum()),population=int(g.Population.sum()),
                population_share=g.Population.sum()/9066522,hospital_linked_tracts=int(g.hospital_tract.sum()),
                zero_housing_positive_tracts=int(g.additional_zero_housing_positive_population.sum()),
                median_latitude=g.INTPTLAT.median(),median_longitude=g.INTPTLON.median(),
                median_tract_population=g.Population.median())
            for q in ['Q1','Q2','Q3','Q4']:row[q]=int(g.frozen_SOVI_quartile.eq(q).sum())
            poprows.append(row)
            silrows.append(dict(model=f'P2_K{k}',class_id=f'C{c+1}',tracts=int(m.sum()),
                mean=s[m].mean(),median=np.median(s[m]),P10=np.quantile(s[m],.1),P90=np.quantile(s[m],.9),
                negative_fraction=np.mean(s[m]<0)))
            for f,bc in zip(FEATURES,m.sum()*centroid**2):
                contributions.append(dict(model=f'P2_K{k}',class_id=f'C{c+1}',coordinate=f,
                    domain='RQ1' if f in FEATURES[:3] else 'RQ2' if f in FEATURES[3:5] else 'RQ3',
                    between_class_sum_squares=float(bc)))
        fitqa.append(dict(model=f'P2_K{k}',key=key,mean_silhouette=float(s.mean()),WCSS=inertia,
                         saved_label_sha256=hashlib.sha256(y.tobytes()).hexdigest(),refitted=False))
        members.extend(dict(tract_id=t,model=f'P2_K{k}',saved_label=int(c),class_id=f'C{c+1}',
                            namespace=f'PathB_P2_K{k}_C{c+1}') for t,c in zip(x.index,y))
    assert np.bincount(y3).tolist()==[1235,428,636]
    assert np.bincount(y4).tolist()==[37,1217,429,616]
    d['P2_K3_class']=pd.Series(y3+1,index=x.index).reindex(d.index).astype('Int64')
    d['P2_K4_sensitivity_class']=pd.Series(y4+1,index=x.index).reindex(d.index).astype('Int64')
    save('P2_FROZEN_MEMBERSHIPS.csv',pd.DataFrame(members))
    save('CLUSTER_ORIGINAL_UNIT_PROFILES.csv',pd.DataFrame(profiles))
    save('CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv',pd.DataFrame(poprows))
    save('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv',pd.DataFrame(contributions))
    save('PER_CLASS_SILHOUETTE.csv',pd.DataFrame(silrows))
    save('RECOMPUTED_SAVED_FIT_QA.csv',pd.DataFrame(fitqa))
    fit=read('A_VS_P2_VS_P3_CLUSTERING_RESULTS.csv')
    fit=fit.query("specification == 'P2' and policy_set == 'main5' and scaling == 'cohort'")
    save('P2_REGISTERED_K_EVIDENCE.csv',fit)
    for name,query in [('SEED_STABILITY.csv',"specification == 'P2' and policy_set == 'main5'"),
                       ('SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv',"specification == 'P2' and policy_set == 'main5'"),
                       ('POLICY_SET_CLUSTER_STABILITY.csv',"specification == 'P2'")]:
        save('P2_'+name,read(name).query(query))
    membership_qa=[]
    for k,y in [(3,y3),(4,y4)]:
        for s in range(42,47):
            a=arrays['labels'][keys.index(f'P2-minus-Init__main5__cohort__k{k}__s{s}')]
            membership_qa.append(dict(k=k,seed=s,comparison='registered minus-Init with RQ1 redistribution',
                                     ARI=adjusted_rand_score(y,a)))
    save('P2_INIT_ABLATION_AGREEMENT.csv',pd.DataFrame(membership_qa))
    old=read('HISTORICAL_EIGHT_VARIABLE_K3_MEMBERSHIP.csv')
    dump('HISTORICAL_LABEL_COLUMNS.json',old.columns.tolist())
    # Explicit model namespaces prevent a shared palette from implying shared members.
    dump('P2_CLASS_ID_REGISTRY.json',dict(model='PathB_P2_K3',saved_labels='zero-based source; display adds one',
         classes=[dict(class_id=f'C{i+1}',color=COLORS[i],tracts=int((y3==i).sum()),
                      population=int(d.loc[x.index[y3==i],'Population'].sum())) for i in range(3)],
         old_NCV14_memberships_used=False))

    r5=d.loc[eligible,'MeanTotal5'];q4=d.loc[eligible,'frozen_SOVI_quartile'].eq('Q4')
    threshold=float(r5.quantile(.75,interpolation='linear'));high=r5>=threshold;joint=q4&high
    assert abs(threshold-38.38135467381475)<2e-12
    assert joint.sum()==94 and d.loc[r5.index[joint],'Population'].sum()==350799 and high.sum()==575
    old94=read('VERIFIED_ORIGINAL_94_GEOIDS.csv')
    assert set(old94.tract_id)==set(r5.index[joint])
    d['Q4_and_high_mean_total5']=pd.Series(joint,index=x.index).reindex(d.index,fill_value=False).astype(bool)
    save('VERIFIED_94_COOCCURRENCE_GEOIDS.csv',d.loc[r5.index[joint],['Population','MeanTotal5','frozen_SOVI_quartile','P2_K3_class']].reset_index())
    cont=[]
    for a in [True,False]:
        for b in [True,False]:
            mask=(q4==a)&(high==b)
            cont.append(dict(Q4=a,high_deficit=b,tracts=int(mask.sum()),population=int(d.loc[x.index[mask],'Population'].sum())))
    save('INDEPENDENT_COOCCURRENCE_CONTINGENCY.csv',pd.DataFrame(cont))
    effect=[]
    comparators={'five_policy_total':r5,'four_policy_total':p.loc[x.index,'MeanTotal4_no_Vulnerability'],
                 'Unconstrained':d.loc[x.index,'B_Unconstrained'],'MeanDelta5':d.loc[x.index,'MeanDelta']}
    comparators.update({c:p.loc[x.index,'B_'+c] for c in POLICIES})
    for name,v in comparators.items():
        for protocol,cut in [('fixed_five_P75',threshold),('within_comparator_P75',float(v.quantile(.75)))]:
            h=v>=cut;qa=(q4&h).sum()/q4.sum();na=(~q4&h).sum()/(~q4).sum()
            wp=d.loc[x.index,'Population']
            effect.append(dict(comparator=name,protocol=protocol,threshold=cut,high_tracts=int(h.sum()),
                Q4_intersection=int((q4&h).sum()),joint_population=int(wp[q4&h].sum()),
                Q4_prevalence=qa,nonQ4_prevalence=na,difference_pp=100*(qa-na),prevalence_ratio=qa/na if na else np.nan,
                resident_Q4_prevalence=wp[q4&h].sum()/wp[q4].sum(),
                resident_nonQ4_prevalence=wp[~q4&h].sum()/wp[~q4].sum(),
                jaccard_high_with_five=(h&high).sum()/(h|high).sum(),
                Spearman_with_five=spearmanr(v,r5).statistic))
    save('POLICY_CONDITIONED_MAP_CONTEXT.csv',pd.DataFrame(effect))
    strat=[]
    for c in [1,2,3]:
        mask=d.loc[x.index,'P2_K3_class'].eq(c).to_numpy()
        for q in ['Q1','Q2','Q3','Q4']:
            m=mask&d.loc[x.index,'frozen_SOVI_quartile'].eq(q).to_numpy()
            strat.append(dict(P2_K3_class=c,quartile=q,tracts=int(m.sum()),
                population=int(d.loc[x.index[m],'Population'].sum()),mean_total5=float(r5[m].mean()),
                high_deficit_tracts=int(high[m].sum())))
    save('P2_STRATIFIED_COOCCURRENCE.csv',pd.DataFrame(strat))

    info=x.assign(NCV14=d.loc[x.index,'FEMA_NCV14_CA_v119'])
    corr=[]
    for f in FEATURES:
        corr.append(dict(variable=f,Pearson=float(info[f].corr(info.NCV14)),
                         Spearman=float(info[f].corr(info.NCV14,method='spearman'))))
    predictors=np.column_stack([np.ones(len(x)),z])
    ncvz=(info.NCV14-info.NCV14.mean())/info.NCV14.std(ddof=0)
    resid=ncvz-predictors@np.linalg.lstsq(predictors,ncvz,rcond=None)[0]
    r2=1-float(np.sum(resid**2)/np.sum(ncvz**2))
    save('NCV14_VS_P2_INFORMATION.csv',pd.DataFrame(corr).assign(
        conditional_linear_R2_all_seven=r2,VIF_all_seven=1/(1-r2)))
    save('NCV14_P2_CLASS_DISTRIBUTIONS.csv',pd.DataFrame(profiles).query("model == 'P2_K3' and variable == 'FEMA_NCV14_CA_v119'"))
    within=float(sum(np.sum((info.NCV14.to_numpy()[y3==c]-info.NCV14.to_numpy()[y3==c].mean())**2) for c in range(3)))
    ncv_eta=1-within/float(np.sum((info.NCV14-info.NCV14.mean())**2))
    save('FROZEN_P2_TRACT_TABLE_2315.csv',d.reset_index())
    save('P2_ORDINARY_COHORT_Z_CLASS_MEANS.csv',pd.DataFrame(
        [dict(class_id=f'C{c+1}',**z.loc[x.index[y3==c]].mean().to_dict()) for c in range(3)]))
    dump('FEATURE_SPECIFICATION.json',dict(primary='P2',features=FEATURES,squared_distance_budgets=BUDGET.tolist(),
        preprocessing='Cohort mean and population SD (ddof=0), multiply by sqrt(budget)',
        fitting='Previously registered fits only; no refitting in this package',main_text_candidate='saved P2/K3/seed42',
        sensitivity='saved P2/K4; different model-specific IDs',NCV14='Supplementary context only, never fitted',
        policies=POLICIES,cohort_rule='Frozen formal Population > 0',source_commit=MP,
        frozen_setup=['2pc50','C57_D1','M1_UTILITY_003','G1_BASELINE_050','480 h','1000 matched realizations']))
    dump('NUMERICAL_QA.json',dict(tracts=2315,eligible=2299,zero_population_excluded=16,zero_housing_positive_included=8,
        population=9066522,K3_counts=np.bincount(y3).tolist(),K4_counts=np.bincount(y4).tolist(),
        five_policy_identity_max_abs_error=float(identity),weighted_matrix_max_abs_error=float(np.max(np.abs(w-weighted['P2__main5__cohort']))),
        threshold_P75=threshold,high_deficit_tracts=575,Q4_tracts=579,joint_tracts=94,joint_population=350799,
        Init_zero_count=int(x.Init_Supply.eq(0).sum()),Init_max=float(x.Init_Supply.max()),
        NCV14_conditional_linear_R2=r2,NCV14_between_P2_K3_fraction=ncv_eta,all_fit_labels_reused=True,
        uncertainty='Pairing authority is the frozen audit and compact integrals. External full event archives are not re-simulated; see original manifest dependencies.'))
    print(json.dumps(json.load(open(u.lp(HERE/'NUMERICAL_QA.json'))),indent=2))
    if OFFLINE:
        dump('OFFLINE_REPRODUCTION_QA.json',dict(compact_inputs_hash_verified=True,no_original_worktree_required=True,
             original_worktree_preservation_rechecked=False,full_external_trajectory_archives_reconstructed=False))


if __name__=='__main__':main()
