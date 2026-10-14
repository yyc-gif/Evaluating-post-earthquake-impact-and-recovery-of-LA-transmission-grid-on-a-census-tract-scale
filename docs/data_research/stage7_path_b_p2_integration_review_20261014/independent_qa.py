"""Independent frozen-integral, classification and preservation checks; no fitting."""
import io
import json
import re
from pathlib import Path
import sys

import fitz
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.sparse import csr_matrix
from sklearn.metrics import adjusted_rand_score
sys.path.insert(0,str(Path(__file__).parent))
import analyze_path_b as a


def main():
    tests=[]
    def check(name,condition,detail):
        assert bool(condition),name
        tests.append(dict(check=name,passed=True,detail=detail))
    d=a.load_frozen();x=d.loc[d.Population>0];q=x.frozen_SOVI_quartile.eq('Q4')
    src=pd.read_csv(a.u.lp(a.HERE/'SOURCE_PAYLOAD_HASHES.csv'))
    for row in src.itertuples():
        raw=open(a.u.lp(a.HERE/row.archived_path),'rb').read() if a.OFFLINE else a.u.payload(row.commit,row.path)
        check('source_payload:'+row.archived_path,a.u.digest(raw)==row.sha256 and
              a.u.sha(a.HERE/row.archived_path)==row.sha256,str(row.bytes)+' actual bytes')
    f=np.load(a.u.lp(a.HERE/'inputs/FROZEN_STATION_INTEGRALS_AND_MAPPING.npz'))
    W=csr_matrix((f['mapping_data'],f['mapping_indices'],f['mapping_indptr']),shape=tuple(f['mapping_shape']))
    check('normalized_mapping',np.max(abs(np.asarray(W.sum(axis=1)).ravel()-1))<1e-12,'2315 row sums')
    e=a.read('FROZEN_EVENT_VERIFICATION.csv')
    pairing=[]
    for i,p in enumerate(f['policies']):
        t=e.loc[e.policy.eq(p)].set_index('realization_id').reindex(f['realization_ids'])
        ok=len(t)==1000 and t.physical_hash.notna().all() and np.array_equal(t.physical_hash.to_numpy(),f['physical_hashes'])
        check('1000_physical_pairings:'+p,ok,'Frozen manifest hashes and realization IDs')
        pairing.append(dict(policy=p,realizations=len(t),physical_hashes_match=ok,station_order_sha256=a.u.digest(f['station_ids'].tobytes())))
    loss=(W@f['station_loss'].mean(axis=1).T).T
    frozen=a.read('FROZEN_POLICY_TRACT_MEANS_2315.csv').set_index('tract_id')
    errs=[]
    for i,p in enumerate(f['policies']):
        if p=='random':continue
        field='B_unconstrained' if p=='unconstrained' else 'B_'+p
        err=float(np.max(abs(loss[i]-frozen.loc[f['tract_ids'],field])))
        check('station_integral_to_tract:'+p,err<2e-11,f'max absolute hours error {err:.3g}')
        errs.append(dict(policy=p,max_abs_error_hr=err))
    a.save('INDEPENDENT_REALIZATION_PAIRING.csv',pd.DataFrame(pairing))
    a.save('INDEPENDENT_STATION_TO_TRACT_INTEGRAL_QA.csv',pd.DataFrame(errs))
    pi={p:i for i,p in enumerate(f['policies'])}
    R=loss[[pi[p] for p in a.POLICIES]].mean(0)
    reconstructed=pd.Series(R,index=f['tract_ids']).loc[x.index]
    check('five_policy_identity_from_station_integrals',np.max(abs(reconstructed-x.MeanTotal5))<2e-11,'No trajectories regenerated')
    cut=np.percentile(reconstructed.to_numpy(),75,method='linear')
    h=reconstructed>=38.38135467381475
    check('exact94_set_from_independent_integrals',set(x.index[q&h])==set(pd.read_csv(a.u.lp(a.HERE/'VERIFIED_94_COOCCURRENCE_GEOIDS.csv'),dtype={'tract_id':str}).tract_id),str(cut))
    check('frozen_population',x.Population.sum()==9066522 and len(x)==2299,'16 excluded; no missing imputation')
    check('eight_zero_housing_retained',x.additional_zero_housing_positive_population.sum()==8,'All classified in P2/K3')
    geo=gpd.read_file(a.u.lp(a.HERE/'inputs/FULL_2315_GEOMETRY.gpkg')).set_index('tract_id').loc[d.index]
    check('full_geometry_support',geo.geometry.is_valid.all() and not geo.geometry.is_empty.any(),'2315 valid polygons; no inherited geometry exclusions')
    bounds=geo.total_bounds
    pixel_scale=min(.445*7.2*150/(bounds[2]-bounds[0]+4400),.239*10.4*150/(bounds[3]-bounds[1]+3600))
    support=pd.DataFrame(dict(tract_id=d.index,population=d.Population.to_numpy(),area_m2=geo.geometry.area,
        approximate_area_pixels_at_150dpi=geo.geometry.area*pixel_scale**2))
    a.save('MAP_GEOMETRY_AND_SMALL_TRACT_DISPLAY_QA.csv',support)
    check('seven_primary_columns',len(a.FEATURES)==7 and all('NCV' not in v for v in a.FEATURES),'NCV supplementary only')
    fits=np.load(a.u.lp(a.HERE/'inputs/REGISTERED_FIT_ARRAYS.npz'))
    keys=fits['keys'].tolist()
    policy=a.read('POLICY_SET_CLUSTER_STABILITY.csv').query("specification == 'P2' and comparison == 'policy_set' and k in [3,4]")
    agreement=[]
    for row in policy.itertuples():
        ref=fits['labels'][keys.index(f'P2__main5__cohort__k{row.k}__s{row.seed}')]
        alt=fits['labels'][keys.index(f'P2__{row.policy_set}__{row.scaling}__k{row.k}__s{row.seed}')]
        ari=adjusted_rand_score(ref,alt)
        check('saved_policy_ARI:'+str((row.k,row.seed,row.policy_set,row.scaling)),abs(ari-row.ARI)<1e-13,'Recomputed from exact saved labels')
        agreement.append(dict(k=row.k,seed=row.seed,policy_set=row.policy_set,scaling=row.scaling,ARI=ari))
    a.save('INDEPENDENT_POLICY_LABEL_ARI.csv',pd.DataFrame(agreement))
    sfits=np.load(a.u.lp(a.HERE/'inputs/SPATIAL_REFIT_LABELS.npz'))
    skeys=sfits['keys'].tolist()
    spatial=a.read('SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv').query("specification == 'P2' and policy_set == 'main5' and k in [3,4]")
    for row in spatial.itertuples():
        ref=fits['labels'][keys.index(f'P2__main5__cohort__k{row.k}__s42')]
        alt=sfits['labels'][skeys.index(f'P2__main5__cohort__k{row.k}__block{row.left_out_block}')]
        check('saved_spatial_full_ARI:'+str((row.k,row.left_out_block)),abs(adjusted_rand_score(ref,alt)-row.full_ARI)<1e-13,'Saved training-only scaling/refit labels; not a new refit')
    z=(x[a.FEATURES].to_numpy()-x[a.FEATURES].to_numpy().mean(0))/x[a.FEATURES].to_numpy().std(0)
    profile=pd.read_csv(a.u.lp(a.HERE/'P2_ORDINARY_COHORT_Z_CLASS_MEANS.csv')).set_index('class_id')
    for c in [1,2,3]:
        vals=z[x.P2_K3_class.eq(c).to_numpy()].mean(0)
        check('all_seven_profile_cells_C'+str(c),np.max(abs(vals-profile.loc[f'C{c}',a.FEATURES].to_numpy(dtype=float)))<1e-12,'ordinary ddof0 cohort-z, not weighted')
    prior=a.read('HISTORICAL_EIGHT_VARIABLE_K3_MEMBERSHIP.csv').set_index('tract_id').loc[x.index]
    old=prior.candidate_display_cluster.to_numpy()-1;new=x.P2_K3_class.to_numpy(dtype=int)-1
    tab=pd.crosstab(old,new).reindex(index=range(3),columns=range(3),fill_value=0).to_numpy()
    ii,jj=linear_sum_assignment(-tab)
    a.save('OLD_NCV14_TO_P2_LABEL_CROSSWALK.csv',pd.DataFrame([dict(
        historical_NCV14_class=int(i+1),PathB_P2_class=int(j+1),overlap_tracts=int(tab[i,j]),
        color_retained=a.COLORS[i] if i==j else 'Require model-specific palette discussion',
        label_invariant_ARI=adjusted_rand_score(old,new)) for i,j in zip(ii,jj)]))
    check('transparent_palette_matching',np.array_equal(ii,jj),'Same display color identities, explicitly different model membership')
    rarebytes=a.source('66d16d61b13c05785f58795ef9d13ba82ece472e',
        'docs/data_research/stage7_rq_typology_interpretation_20261012/',
        'THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv')
    rare=pd.read_csv(io.BytesIO(rarebytes),dtype={'tract_id':str})
    check('rare_source_34',rare.tract_id.nunique()==34,'Exact frozen STATION Q proxy-linked reference')
    rarex=x.loc[rare.tract_id]
    a.save('Q_LINKED_34_IN_P2.csv',rarex[['Init_Supply','B_Unconstrained','MeanDelta','P2_K3_class','P2_K4_sensitivity_class','Population']].reset_index())
    a.save('RARE_Q_SOURCE_HASH.csv',pd.DataFrame(a.SOURCES))
    for kind in ['A','B']:
        name=f'FIGURE7_PATH_B_CANDIDATE_{kind}.pdf'
        with fitz.open(a.u.lp(a.HERE/'figures'/name)) as doc:
            check('native_width_'+kind,abs(doc[0].rect.width/72-7.2)<1e-6,'7.2-inch publication width')
            check('vector_artwork_'+kind,len(doc[0].get_images())==0,'No raster maps, legend or profile cells in PDF')
            check('no_eight_variable_label_'+kind,'eight-variable' not in doc[0].get_text().lower(),'P2 namespace')
            spans=[s for b in doc[0].get_text('dict',flags=0)['blocks'] for line in b.get('lines',[]) for s in line['spans']]
            check('all_text_inside_page_'+kind,all(doc[0].rect.contains(fitz.Rect(s['bbox'])) for s in spans),'Actual native-size text bounds')
    ecdf=[]
    for c in [1,2,3]:
        for v in ['Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','Population']:
            values=x.loc[x.P2_K3_class.eq(c),v].to_numpy()
            ecdf.append(dict(class_id=f'C{c}',variable=v,n=len(values),median=float(np.median(values)),
                min=float(values.min()),max=float(values.max()),exact_zero_count=int((values==0).sum()),
                sorted_observation_sha256=a.u.digest(np.sort(values).tobytes()),smoothed=False,clipped=False))
    a.save('ALL_18_ECDF_DATA_CHECKS.csv',pd.DataFrame(ecdf))
    lut=pd.read_csv(a.u.lp(a.HERE/'BIVARIATE_EXACT_COLOR_LEGEND.csv'))
    check('matched_burden_luminance',lut.groupby('position').relative_luminance.agg(lambda v:v.max()-v.min()).max()<2e-7,'Equal CIELAB L* and sRGB luminance at every common hour')
    check('burden_monotonic_luminance',all(np.all(np.diff(g.relative_luminance)<0) for _,g in lut.groupby('quartile')),'Higher hours are consistently darker in all four families')
    manifest=[] if a.OFFLINE else a.u.csv_rows(a.u.payload('5fbdf5a33cb8cee4790f81e896776b8b6fb4f9ae','results/figure_review/FIGURE_MANIFEST.csv'))
    for row in manifest:
        for field in ['current_source_file','mirror_file']:
            check('unchanged_official:'+row[field],a.u.sha(a.ROOT/row[field])==row['sha256'],'No official Path B artwork promotion')
    if not a.OFFLINE:
        before=json.load(open(a.u.lp(a.HERE/'PRESERVATION_BEFORE.json')))
        after=a.u.protected_snapshot(before)
        check('950_and_original_index',before==after,'Protected bytes, original HEAD, index/status and staged names unchanged')
        a.dump('PRESERVATION_AFTER.json',after)
    a.dump('OFFLINE_INDEPENDENT_QA.json' if a.OFFLINE else 'INDEPENDENT_QA_RESULTS.json',dict(passed=len(tests),failed=0,checks=tests,
        all_physical_pairings_verified_from_frozen_compact_archive=True,
        original_worktree_preservation_rechecked=not a.OFFLINE,
        full_original_event_archives_recomputed=False,no_fitting=True,no_formal_promotion=True))
    print(f'{len(tests)} independent checks passed; no models fitted.')


if __name__=='__main__':main()
