"""Read-only review of the saved 50df104 feature-validation results. NO refitting."""
from pathlib import Path
import hashlib, json, subprocess
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, silhouette_score

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / 'docs/data_research/built_environment_20261009/final_feature_validation_20261010'
OUT = Path(__file__).resolve().parent
BASE = '50df10481815f3dd94c46dc9443f93cfdb1c5014'
FILES = ['FINAL_CANDIDATE_FEATURE_MATRIX.csv', 'CONTROLLED_CLUSTERING_COMPARISON.csv',
         'SPATIAL_BLOCK_STABILITY.csv', 'CLUSTER_DOMAIN_CONTRIBUTIONS.csv',
         'EXPLORATORY_LABELS_SEED42.csv', 'CLUSTER_BETWEEN_MODEL_ARI.csv',
         'CANDIDATE_VIF.csv']
GRID = ['Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI']


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [clean(v) for v in x]
    if isinstance(x, np.ndarray): return clean(x.tolist())
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (float,np.floating)): return float(x) if np.isfinite(x) else None
    if isinstance(x, (np.bool_,)): return bool(x)
    return x


def main():
    tables, hashes = {}, {}
    for name in FILES:
        path = SRC / name
        pointer = subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()], cwd=ROOT).decode()
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if pointer.startswith('version https://git-lfs.github.com/spec/v1'):
            expected = next(line.split(':',1)[1] for line in pointer.splitlines() if line.startswith('oid sha256:'))
            size = int(next(line.split()[1] for line in pointer.splitlines() if line.startswith('size ')))
            assert digest == expected and len(data) == size, name
        hashes[name] = {'sha256':digest, 'bytes':len(data)}
        tables[name] = pd.read_csv(path, dtype={'tract_id':str}, low_memory=False)
    full = tables['FINAL_CANDIDATE_FEATURE_MATRIX.csv'].set_index('tract_id')
    full.index = full.index.str.zfill(11)
    assert len(full)==2291 and full.index.is_unique
    mask = full.primary_complete_case.astype(str).str.lower().eq('true')
    frame = full.loc[mask].copy()
    assert len(frame)==2287
    labels = tables['EXPLORATORY_LABELS_SEED42.csv'].set_index('tract_id')
    labels.index = labels.index.str.zfill(11)
    labels = labels.reindex(frame.index)
    runs = tables['CONTROLLED_CLUSTERING_COMPARISON.csv']
    selected = runs.loc[runs.selected_run.astype(str).str.lower().eq('true')]
    assert len(runs)==2800 and len(selected)==400
    spatial = tables['SPATIAL_BLOCK_STABILITY.csv']
    domain = tables['CLUSTER_DOMAIN_CONTRIBUTIONS.csv']
    checks, profiles, selections, space = [], {}, {}, {}
    main_models = ['D__inherited','EAL__inherited','D__equal_five_domains','EAL__equal_five_domains']
    show = ['B_480_hr','T80','Init_Supply','SOVI_SCORE','land_use_entropy',
            'land_use_classified_land_coverage','building_footprint_coverage',
            'all_use2014_pre1970_area_share','all_use2014_age_coverage',
            'NRI_BUILDVALUE','log1p_NRI_BUILDVALUE','ALR_NPCTL','EAL_SCORE','Pop_Density'] + GRID
    for model in main_models:
        subset = selected.loc[selected.model.eq(model)]
        selections[model] = {'selected_k_counts': subset.k.value_counts().sort_index().to_dict(),
            'selected_silhouette_mean':subset.silhouette.mean(),
            'k_sweep': runs.loc[runs.model.eq(model)].groupby('k')[['inertia','silhouette','minimum_cluster_size']].mean().reset_index().to_dict('records')}
        for role in ['fixed_k5','selected_run']:
            row = runs.loc[runs.model.eq(model)&runs.seed.eq(42)&runs[role].astype(str).str.lower().eq('true')].iloc[0]
            y = labels[model+'__'+role].astype(int)
            groups = {'recovery_service':['B_480_hr','Init_Supply'],'grid':GRID,
                      'physical':['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share'],
                      'social':['SOVI_SCORE'],
                      'loss_exposure':['log1p_NRI_BUILDVALUE','ALR_NPCTL'] if model.startswith('D__') else ['EAL_SCORE']}
            budget = {'recovery_service':2/11,'grid':4/11,'physical':2/11,'social':1/11,'loss_exposure':2/11}
            if 'equal_five_domains' in model: budget={k:.2 for k in groups}
            cols = [col for group in groups.values() for col in group]
            x = frame[cols].to_numpy(float)
            assert np.isfinite(x).all()
            x = (x-x.mean(axis=0))/x.std(axis=0)
            weights = np.array([np.sqrt(budget[g]/len(members)) for g,members in groups.items() for col in members])
            x *= weights
            centers = {v:x[y.to_numpy()==v].mean(axis=0) for v in sorted(y.unique())}
            inertia = float(sum(np.sum((x[y.to_numpy()==v]-centers[v])**2) for v in centers))
            sil = float(silhouette_score(x,y.to_numpy()))
            assert abs(sil-row.silhouette)<1e-8, (model,role,sil,row.silhouette)
            assert abs(inertia-row.inertia)<1e-4, (model,role,inertia,row.inertia)
            checks.append({'model':model,'role':role,'k':int(row.k),'silhouette_error':sil-row.silhouette,'inertia_error':inertia-row.inertia})
            key = model+'__'+role
            records=[]
            for cluster in sorted(y.unique()):
                d = frame.loc[y.eq(cluster)]
                records.append({'cluster':int(cluster),'n':len(d),
                    'initial_zero_fraction':float(d.Init_Supply.eq(0).mean()),
                    'means':{c:float(d[c].mean()) for c in show if c in d},
                    'medians':{c:float(d[c].median()) for c in show if c in d},
                    'recovery_p10_p90':[float(d.B_480_hr.quantile(.1)),float(d.B_480_hr.quantile(.9))]})
            profiles[key] = records
        s = spatial.loc[spatial.model.eq(model)]
        assert len(s)==20
        space[model] = {'n':len(s),'full_median':s.full_prediction_ARI.median(),
            'full_min':s.full_prediction_ARI.min(),'training_median':s.training_ARI.median(),
            'heldout_median':s.heldout_ARI.median(),'heldout_min':s.heldout_ARI.min(),
            'training_n_min':s.n_training.min(),'training_n_max':s.n_training.max(),
            'worst_three':s.nsmallest(3,'full_prediction_ARI')[['seed','n_training','n_heldout','full_prediction_ARI','training_ARI','heldout_ARI','removed_blocks']].to_dict('records')}
    matches = []
    ref = labels['D__inherited__fixed_k5'].astype(int)
    for model in ['D__equal_five_domains','EAL__inherited','D_T80__inherited',
                  'D_entropy_transport__inherited','D_entropy_dominant__inherited',
                  'D_age_lower_bound__inherited','D_age_upper_bound__inherited','D_ACS_age__inherited']:
        y = labels[model+'__fixed_k5'].astype(int)
        cross = pd.crosstab(ref,y)
        r,c = linear_sum_assignment(-cross.to_numpy())
        counts = cross.to_numpy()[r,c]
        per = [{'reference_cluster':int(cross.index[i]),'matched_cluster':int(cross.columns[j]),
                'reference_n':int(cross.iloc[i,:].sum()),'matched_n':int(cross.iloc[:,j].sum()),
                'intersection':int(cross.iloc[i,j]),
                'jaccard':float(cross.iloc[i,j]/(cross.iloc[i,:].sum()+cross.iloc[:,j].sum()-cross.iloc[i,j]))}
               for i,j in zip(r,c)]
        matches.append({'model':model,'reference':'D__inherited','seed':42,
            'ARI':float(adjusted_rand_score(ref,y)),'optimal_matched_fraction':float(counts.sum()/len(y)),
            'cluster_matching':per})
    excluded = full.loc[~mask]
    missing = {'tract_ids':excluded.index.tolist(),'tract_fraction':len(excluded)/len(full),
               'available_values':excluded[[c for c in show if c in excluded]].reset_index().to_dict('records')}
    if 'formal_population' in full:
        missing['population_fraction']=float(excluded.formal_population.sum()/full.formal_population.sum())
        missing['excluded_population']=float(excluded.formal_population.sum())
    report={'source_commit':BASE,'source_hashes':hashes,'independent_saved_label_metric_checks':checks,
            'new_kmeans_fits':0,'original_scientific_files_modified':False,
            'selected_k':selections,'spatial_fixed_k5':space,'profiles':profiles,
            'between_model_cluster_matching_seed42':matches,'missing':missing,
            'domain_contributions':domain.loc[domain.model.isin(main_models)].to_dict('records')}
    (OUT/'SAVED_RESULTS_REVIEW.json').write_text(json.dumps(clean(report),indent=2,allow_nan=False)+'\n')
    text=['# Independent review of stored Stage7 results','',
          'Input commit: '+BASE+'. No clustering was rerun. Seven hydrated LFS inputs were checked against their commit-specific SHA256 and byte length. Eight stored-label silhouette/inertia pairs were independently recalculated.',
          '', '## Sample and selected k',
          'The candidate universe has 2291 rows; 2287 are complete. Four original tract identities remain unclassified.']
    for model, item in selections.items():
        text.append('- '+model+': selected k over 20 seeds '+str(item['selected_k_counts'])+'.')
    text.extend(['','## Spatial sensitivity (fixed k=5 only)'])
    for model,item in space.items():
        text.append('- '+model+': median full-cohort ARI %.6f, minimum %.6f; median heldout-only ARI %.6f.'%(item['full_median'],item['full_min'],item['heldout_median']))
    text.extend(['','## Interpretation limits',
       'All reported spatial perturbations were fitted at k=5. They do not directly validate whichever k was selected by the elbow. Feature-choice sensitivity is distinct from missing-data sensitivity; whole-partition ARI is not a percentage of preserved labels. Quantile/mean profiles use seed42 labels and describe the saved model, not a causal effect. Complete-case inference must report the four unclassified tracts and their population coverage.'])
    (OUT/'SAVED_RESULTS_REVIEW.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(clean({'checks':checks,'selected_k':{m:x['selected_k_counts'] for m,x in selections.items()},
        'spatial':space,'excluded':missing}),indent=2,allow_nan=False))

if __name__=='__main__': main()
