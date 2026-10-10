"""Freeze saved Stage 7 labels and derive review tables/artwork; never fit KMeans.

Usage: python build_preview.py --repo PATH
All writes are confined to the requested manuscript integration preview directory.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, platform, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score

REL = Path('docs/data_research/built_environment_20261009')
OUT_NAME = 'manuscript_integration_preview_20261010'
COMMITS = dict(features='50df10481815f3dd94c46dc9443f93cfdb1c5014',
               spatial='ecf98c6cbda280914962582a819943fabfa41132',
               fema='65f388f9710566ffa845808bd7b10503de4da608',
               formal='031d2c675f8e7d58035d27448be040b809ced086')
DOMAINS = {
    'Recovery and initial service': ['B_480_hr', 'Init_Supply'],
    'Grid dependency': ['Grid_Degree', 'Grid_Impact', 'Grid_Betweenness', 'Redundancy_HHI'],
    'Built environment': ['land_use_entropy', 'building_footprint_coverage', 'all_use2014_pre1970_area_share'],
    'Social vulnerability': ['SOVI_SCORE'],
    'Economic stock and multi-hazard loss': ['log1p_NRI_BUILDVALUE', 'ALR_NPCTL'],
}
UNCLASSIFIED = ['06037189703', '06037301601', '06037301602', '06037404600']
FIELDS = ['B_480_hr', 'T80', 'Init_Supply', 'SOVI_SCORE', 'land_use_entropy',
          'land_use_classified_land_coverage', 'building_footprint_coverage',
          'all_use2014_pre1970_area_share', 'all_use2014_age_coverage', 'NRI_BUILDVALUE',
          'ALR_NPCTL', 'EAL_SCORE', 'Grid_Degree', 'Grid_Impact', 'Grid_Betweenness',
          'Redundancy_HHI', 'Pop_Density', 'Pop_Density_per_km2',
          'residential_pre1970_housing_share', 'housing_5plus_share']

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''): h.update(block)
    return h.hexdigest()

def dump(path, obj):
    Path(path).write_bytes((json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8'))

def read(path):
    d = pd.read_csv(path, dtype={'tract_id': str})
    if 'tract_id' in d:
        d['tract_id'] = d.tract_id.str.zfill(11)
        assert d.tract_id.str.fullmatch(r'\d{11}').all() and d.tract_id.is_unique
    return d

def git(repo, *args):
    return subprocess.check_output(['git','-C',str(repo),*args])

def verify_source(repo, rel, commit):
    p = repo/rel; data = p.read_bytes()
    assert not data.startswith(b'version https://git-lfs.github.com/spec/v1')
    blob = git(repo,'show',f'{commit}:{Path(rel).as_posix()}')
    if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
        oid = next(x.split(b'sha256:')[1] for x in blob.splitlines() if x.startswith(b'oid ')).decode()
        assert hashlib.sha256(data).hexdigest() == oid, rel
        method = 'actual payload SHA-256 equals commit LFS OID'
    else:
        assert data.replace(b'\r\n',b'\n') == blob.replace(b'\r\n',b'\n'), rel
        method = 'Git source bytes equal (text CRLF normalized only)'
    return {'file':Path(rel).as_posix(),'source_commit':commit,'sha256':sha(p),'bytes':len(data),'verification':method}

def preserve(repo, spatial, out):
    old = json.loads((spatial/'PRESERVATION_BASELINE.json').read_text())
    protected = old['protected_files']
    mismatches = [p for p,h in protected.items() if not (repo/p).exists() or sha(repo/p)!=h]
    assert not mismatches, mismatches
    staged = git(repo,'ls-files','--stage','-z')
    staged_changes = git(repo,'diff','--cached','--name-only','-z').split(b'\0')
    info = {'original_head':git(repo,'rev-parse','HEAD').decode().strip(),
            'original_branch':git(repo,'branch','--show-current').decode().strip(),
            'original_staged_change_count':sum(bool(x) for x in staged_changes),
            'logical_index_sha256':hashlib.sha256(staged).hexdigest(),
            'protected_files':protected,'protected_count':len(protected),'mismatches':mismatches}
    baseline = out/'PRESERVATION_BASELINE.json'
    if baseline.exists():
        prior=json.loads(baseline.read_text()); assert prior['logical_index_sha256']==info['logical_index_sha256']; assert prior['protected_files']==protected
    else: dump(baseline,info)
    return info

def main():
    args=argparse.ArgumentParser();args.add_argument('--repo',type=Path,required=True);args=args.parse_args()
    repo=args.repo.resolve();base=repo/REL;f=base/'final_feature_validation_20261010';s=base/'spatial_k4_validation_20261010'
    out=base/OUT_NAME;out.mkdir(exist_ok=True)
    preservation=preserve(repo,s,out)
    sources=[]
    for folder, key in [(f,'features'),(s,'spatial')]:
        # Verify the actual authoritative package, including every saved model record.
        for p in sorted(folder.rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts: continue
            rel=p.relative_to(repo)
            if git(repo,'ls-tree',COMMITS[key],'--',rel.as_posix()).strip():
                sources.append(verify_source(repo,rel,COMMITS[key]))
    for rel,key in [(REL/'local_joint_feature_extraction_20261009/TRACT_FEATURE_CANDIDATES.csv','features'),
                    (REL/'nri_eal_redundancy_audit_20261009/FEMA_FIELD_DEFINITIONS_AND_COMPOSITION.md','fema'),
                    (REL/'nri_eal_redundancy_audit_20261009/NRI_EAL_DECISION.md','fema'),
                    (Path('Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv'),'formal'),
                    (Path('provenance/legacy_outputs/Submission_Package/Manuscript_IJDRR.docx'),'formal'),
                    (Path('src/la_grid/plotting/Project_Visualizer.py'),'formal')]:
        sources.append(verify_source(repo,rel,COMMITS[key]))
    for p in sorted((repo/'Data').glob('LA_Tracts_With_Population.*')):
        if git(repo,'ls-tree',COMMITS['formal'],'--',p.relative_to(repo).as_posix()).strip():
            sources.append(verify_source(repo,p.relative_to(repo),COMMITS['formal']))
    pd.DataFrame(sources).to_csv(out/'SOURCE_HASH_VERIFICATION.csv',index=False)
    master=read(f/'FINAL_CANDIDATE_FEATURE_MATRIX.csv'); complete=read(f/'COMPLETE_CASE_FEATURE_MATRIX.csv')
    assert len(master)==2291 and len(complete)==2287
    assert set(master.tract_id)-set(complete.tract_id)==set(UNCLASSIFIED)
    assert complete.tract_id.tolist()==master.loc[master.primary_complete_case,'tract_id'].tolist()
    columns=sum(DOMAINS.values(),[]);raw=complete[columns].to_numpy(dtype=float)
    assert np.isfinite(raw).all()
    # Recover the original deterministic preprocessing only, not a new cluster fit.
    scaler=StandardScaler().fit(complete[columns])
    factors=np.array([np.sqrt(.2/len(v)) for v in DOMAINS.values() for _ in v])
    matrix=scaler.transform(complete[columns])*factors
    meta=json.loads((f/'run_records/D__equal_five_domains.json').read_text())
    mh=hashlib.sha256(np.ascontiguousarray(matrix).tobytes()).hexdigest()
    sampleh=hashlib.sha256('\n'.join(complete.tract_id).encode()).hexdigest()
    assert mh==meta['matrix_sha256'];assert sampleh==meta['rows'][0]['sample_sha256']
    labels=np.load(f/'run_records/D__equal_five_domains.npz')['s42_k4']
    assert np.bincount(labels).tolist()==[850,34,651,752]
    record=next(r for r in meta['rows'] if r['seed']==42 and r['k']==4)
    centers=np.array([matrix[labels==c].mean(axis=0) for c in range(4)])
    inertia=float(np.square(matrix-centers[labels]).sum())
    nearest=np.square(matrix[:,None,:]-centers[None,:,:]).sum(axis=2).argmin(axis=1)
    assert np.isclose(inertia,record['inertia'],rtol=0,atol=1e-8)
    assert np.array_equal(nearest,labels)
    mapping={i:f'C{i+1}' for i in range(4)}
    ids=complete.tract_id.tolist(); complete['candidate_cluster']=[mapping[int(i)] for i in labels]
    lab=master[['tract_id','primary_complete_case','missing_primary_fields']].copy()
    lab=lab.merge(complete[['tract_id','candidate_cluster']],on='tract_id',how='left',validate='one_to_one',sort=False)
    lab['source_raw_cluster']=lab.tract_id.map(dict(zip(ids,labels))).astype('Int64')
    lab['classification_status']=np.where(lab.candidate_cluster.notna(),'CLASSIFIED','UNCLASSIFIED_GEOMETRY')
    lab.to_csv(out/'STAGE7_CANDIDATE_LABELS_2291.csv',index=False)
    complete.to_csv(out/'CLASSIFIED_FEATURE_VALUES_2287.csv',index=False)
    unknown=master.loc[~master.tract_id.isin(ids),['tract_id','formal_population']+FIELDS+['missing_primary_fields']].copy()
    unknown['classification_status']='UNCLASSIFIED_GEOMETRY';unknown.to_csv(out/'UNCLASSIFIED_TRACT_CHARACTERISTICS.csv',index=False)
    np.savez_compressed(out/'STAGE7_CANDIDATE_PARAMETERS.npz',tract_id=np.array(ids),labels=labels,
                        feature_names=np.array(columns),scaler_mean=scaler.mean_,scaler_std=scaler.scale_,
                        scaler_variance=scaler.var_,coordinate_factors=factors,label_mean_centers=centers,
                        weighted_standardized_matrix=matrix)
    rows=[];long=[];pop=complete.formal_population.sum()
    for c,d in complete.groupby('candidate_cluster',sort=True):
        r={'candidate_cluster':c,'n_tracts':len(d),'tract_share':len(d)/len(complete),
           'population_sum':d.formal_population.sum(),'population_share':d.formal_population.sum()/pop,
           'primary_profile_weighting':'equal weight per tract; population only for explicitly named fields'}
        for col in FIELDS:
            v=d[col].dropna();r[col+'_n_observed']=len(v)
            for stat,value in [('mean',v.mean()),('median',v.median()),('p10',v.quantile(.1)),('p90',v.quantile(.9)),('zero_fraction',v.eq(0).mean())]:
                r[col+'_'+stat]=value
                long.append({'candidate_cluster':c,'feature':col,'statistic':stat,'value':value,'n_observed':len(v),'weighting':'tract'})
        r['B_480_hr_population_weighted_mean']=np.average(d.B_480_hr,weights=d.formal_population)
        rows.append(r)
    profiles=pd.DataFrame(rows);profiles.to_csv(out/'STAGE7_CLUSTER_PROFILES.csv',index=False)
    pd.DataFrame(long).to_csv(out/'STAGE7_CLUSTER_PROFILES_LONG.csv',index=False)
    old=read(repo/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv')
    assert set(old.tract_id)==set(master.tract_id)
    joined=complete[['tract_id','candidate_cluster']].merge(old[['tract_id','cluster']],on='tract_id',validate='one_to_one')
    assert joined.tract_id.tolist()==ids
    ari=float(adjusted_rand_score(joined.cluster,joined.candidate_cluster))
    cross=[]
    for oldc in sorted(old.cluster.unique()):
        oldn=(joined.cluster==oldc).sum();oldfull=(old.cluster==oldc).sum()
        for newc in sorted(complete.candidate_cluster.unique()):
            newn=(joined.candidate_cluster==newc).sum();n=((joined.cluster==oldc)&(joined.candidate_cluster==newc)).sum()
            cross.append({'original_cluster':int(oldc),'candidate_cluster':newc,'n_intersection':int(n),
                          'original_n_common_domain':int(oldn),'original_n_full_2291':int(oldfull),
                          'original_n_unclassified_candidate':int(oldfull-oldn),'candidate_n':int(newn),
                          'fraction_of_original':n/oldn,'fraction_of_candidate':n/newn,'common_n':len(joined),'ARI':ari})
    pd.DataFrame(cross).to_csv(out/'STAGE7_OLD_NEW_CROSSWALK.csv',index=False)
    # Summarize only already saved partitions, preserving fixed-k/reference distinctions.
    experiments=read(f/'CONTROLLED_CLUSTERING_COMPARISON.csv');sens=[]
    specs=json.loads((f/'CONTROLLED_EXPERIMENT_SPECIFICATION.json').read_text())['planned_models']
    for spec in specs:
        name=spec['name']
        if spec['sample']!='complete':continue
        saved=np.load(f/'run_records'/f'{name}.npz')
        reference='D__equal_five_domains' if spec['budget']=='equal_five_domains' else 'D__inherited'
        ref=np.load(f/'run_records'/f'{reference}.npz')
        for k in [4,5]:
            vals=[adjusted_rand_score(ref[f's{seed}_k{k}'],saved[f's{seed}_k{k}']) for seed in range(42,62)]
            selected=experiments[(experiments.model==name)&experiments.selected_run].k.value_counts().to_dict()
            sens.append({'model':name,'reference':reference,'fixed_k':k,'n':2287,'seeds':20,
                         'ARI_median':np.median(vals),'ARI_min':min(vals),'ARI_max':max(vals),
                         'selected_k_counts':json.dumps({int(a):int(b) for a,b in selected.items()},sort_keys=True)})
    pd.DataFrame(sens).to_csv(out/'SAVED_SENSITIVITY_SUMMARY.csv',index=False)
    optimization=[]
    for name in ['D__equal_five_domains','EAL__equal_five_domains']:
        z=np.load(f/'run_records'/f'{name}.npz')
        vals=[adjusted_rand_score(z[f's{a}_k4'],z[f's{b}_k4']) for a,b in itertools.combinations(range(42,62),2)]
        optimization.append({'model':name,'saved_seed_count':20,'pair_count':len(vals),'pairwise_ARI_median':float(np.median(vals)),'pairwise_ARI_min':float(min(vals))})
    dump(out/'OPTIMIZATION_STABILITY_SUMMARY.json',optimization)
    definitions=read(f/'FINAL_FEATURE_DEFINITIONS_AND_QA.csv')
    definitions.to_csv(out/'VALIDATED_FEATURE_DEFINITIONS.csv',index=False)
    freeze={'candidate':'descriptive joint community typology; not formal Stage 7 replacement',
            'source_commits':COMMITS,'source_verification':'SOURCE_HASH_VERIFICATION.csv',
            'original_label_file':str((f/'run_records/D__equal_five_domains.npz').relative_to(repo)),
            'original_label_array':'s42_k4','original_saved_label_sha256':hashlib.sha256(labels.tobytes()).hexdigest(),
            'tract_order':ids,'tract_order_sha256':sampleh,'matrix_sha256':mh,
            'residential_master_n':2291,'classified_n':2287,'unclassified_geoids':UNCLASSIFIED,
            'unclassified_treatment':'null labels and physical inputs; UNCLASSIFIED_GEOMETRY; no imputation or predictions',
            'old_to_new_id_mapping':{str(k):v for k,v in mapping.items()},
            'identifier_rule':'source integer 0..3 becomes C1..C4; no scientific ranking or silent reordering',
            'domains':{k:{'features':v,'squared_distance_weight':.2} for k,v in DOMAINS.items()},
            'standardization':{'population':'2287 complete cases, exact saved order','mean':scaler.mean_.tolist(),
                               'std_ddof0':scaler.scale_.tolist(),'variance_ddof0':scaler.var_.tolist()},
            'coordinate_order':columns,'coordinate_factors':factors.tolist(),
            'coordinate_squared_distance_weights':np.square(factors).tolist(),
            'transformations':{'NRI_BUILDVALUE':'natural log1p; 2022 USD before transformation','B_480_hr':'raw hours',
                               'FEMA_scores':'published national percentile scales unchanged before z standardization'},
            'KMeans_original_run':{'k':4,'seed':42,'n_init':100,'max_iter':500,'tol':1e-4,'algorithm':'lloyd',
                                   'sklearn_version':'1.5.1','iterations':int(record['iterations']),'inertia':record['inertia']},
            'preprocessing_recovery':'Original saved scaler/centers were not serialized. Deterministic StandardScaler statistics reconstructed from exact source inputs; weighted matrix byte hash equals original. No KMeans fit.',
            'centers_provenance':'Means of saved-label members in weighted coordinates, explicitly reconstructed, not original serialized algorithm centers. Nearest-center assignments reproduce every saved label and inertia agrees within 1e-8.',
            'weighted_label_mean_centers':centers.tolist(),'nearest_center_label_mismatches':int((nearest!=labels).sum()),
            'descriptive_not_primary':['T80','Pop_Density','housing_5plus_share','EAL_SCORE','residential_pre1970_housing_share'],
            'runtime':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__},
            'original_to_candidate_ARI':ari,'protected_file_count':preservation['protected_count'],
            'new_KMeans_fits':0,'new_simulations':0,'formal_files_written':0}
    dump(out/'STAGE7_CANDIDATE_FREEZE.json',freeze)
    (out/'.gitignore').write_text('!*.csv\n!*.json\n!*.npz\n',encoding='utf-8')
    (out/'.gitattributes').write_text('*.npz filter=lfs diff=lfs merge=lfs -text\n',encoding='utf-8')
    print(json.dumps({'output':str(out),'n':len(complete),'old_new_ARI':ari,'population':int(pop),
                      'unknown_population':int(unknown.formal_population.sum()),'counts':np.bincount(labels).tolist()},indent=2))
    print(profiles[['candidate_cluster','population_sum','B_480_hr_mean','T80_mean','Init_Supply_mean','SOVI_SCORE_mean','ALR_NPCTL_median']].to_string(index=False))

if __name__=='__main__':main()
