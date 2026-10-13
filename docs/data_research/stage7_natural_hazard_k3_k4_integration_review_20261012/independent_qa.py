"""Source/candidate/formal-preservation verification, with zero new fitting."""
import ast
import importlib.metadata
import platform
from datetime import datetime,timezone
import fitz
from PIL import Image
from scipy.spatial.distance import cdist
from scipy.stats import rankdata
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
from common import *


def main():
    checks=[]
    def check(name,detail):checks.append(dict(name=name,status='PASS',detail=detail));print('PASS',name,flush=True)
    s=reader();d=frame('inputs/FROZEN_COHORT.csv','tract_id');old=read(s,HN+'FROZEN_COHORT_AND_COMPARATORS.csv','tract_id')
    assert d.index.is_unique and d.index.str.fullmatch(r'\d{11}').all() and len(d)==2299
    assert d.Population.gt(0).all() and d.Population.sum()==9066522 and d.additional_zero_housing_positive_population.sum()==8
    np.testing.assert_array_equal(d[FEATURES[:7]].to_numpy(),old[FEATURES[:7]].to_numpy());np.testing.assert_array_equal(d.frozen_SOVI_quartile,old.frozen_SOVI_quartile)
    full=frame('candidate/FULL_2315_COHORT_STATUS.csv','tract_id');assert len(full)==2315 and full.index.is_unique
    excluded=frame('inputs/EXCLUDED_ZERO_POPULATION_GEOIDS.csv','tract_id');assert len(excluded)==16 and excluded.Population.eq(0).all()
    assert set(full.index[~full.clustering_eligible])==set(excluded.index)
    assert full.loc[excluded.index,['K3_candidate_cluster','K4_candidate_cluster']].isna().all().all()
    np.testing.assert_array_equal(full.loc[d.index,'Frozen_Formal_Population'],d.Population)
    check('cohort_source_quartile_identity','2299+16=2315;9066522people;eight zero-housing retained;no missing population imputation')
    n=frame('inputs/source_evidence/NRI_V119_CA_FROZEN.csv','TRACTFIPS');assert len(n)==9106 and set(n.NRI_VER)=={'Mar-23'}
    nc=frame('inputs/NCV_HAZARD_COMPONENTS.csv','tract_id');hazards=[c for c in nc if c!='review_status'];assert len(hazards)==14
    raw=frame('inputs/NCV_RAW_FACTORS.csv','tract_id');norm={}
    for h in hazards:
        fraction=n[h+'_EXP_AREA']/n.AREA
        q=(n[h+'_AFREQ']*fraction).where(n[h+'_AFREQ'].ge(0)&n[h+'_EXP_AREA'].ge(0)&n.AREA.gt(0)&fraction.le(1+1e-9))
        z=(q-q.min())/(q.max()-q.min());norm[h]=z
        np.testing.assert_allclose(q.loc[d.index],raw[h+'_NCV_raw'],rtol=0,atol=1e-12)
        np.testing.assert_allclose(z.loc[d.index],nc[h],rtol=0,atol=1e-13)
    sumscore=pd.DataFrame(norm).sum(1,min_count=14);v=(sumscore-sumscore.min())/(sumscore.max()-sumscore.min())
    candidate=frame('candidate/EIGHT_VARIABLE_FROZEN_TABLE.csv','tract_id')
    np.testing.assert_allclose(v.loc[d.index],candidate.FEMA_NCV14_CA_v119,atol=1e-13,rtol=0)
    for h in ['AVLN','HRCN','ISTM','VLCN']:assert n.loc[d.index,h+'_AFREQ'].isna().all()
    check('NCV14_raw_formula_and_reference','All14 recomputed from original9106CA rows;noNULLs changed to0;original sourceSHA verified')
    comparisons=frame('EARTHQUAKE_NRI_CGS_SPATIAL_RANK_COMPARISON.csv');q=frame('EARTHQUAKE_MATCHED_TRACT_VALUES.csv','tract_id')
    for row in comparisons.itertuples():
        values=q[[row.a,row.b]].dropna();r=np.corrcoef(rankdata(values[row.a]),rankdata(values[row.b]))[0,1]
        assert len(values)==row.n and abs(r-row.Spearman)<1e-12
    assert q.CGS_PGA_land_mean_g.isna().sum()==5
    check('independent_CGS_rank_and_missingness','Independent average-rank correlation;2294valid polygon comparisons;5 remain missing;no cohort shrinkage')
    snap=np.load(lp(OUT/'candidate/FROZEN_PREPROCESSING_AND_LABELS.npz'));mat=np.load(lp(OUT/'inputs/SAVED_WEIGHTED_MATRICES.npz'));source=np.load(lp(OUT/'inputs/SAVED_LABELS_AND_SILHOUETTES.npz'));centers=np.load(lp(OUT/'inputs/SAVED_MODEL_CENTERS.npz'));ix={k:i for i,k in enumerate(source['keys'])}
    np.testing.assert_array_equal(snap['weighted_matrix'],mat['main']);np.testing.assert_allclose((snap['raw']-snap['cohort_mean'])/snap['population_SD']*np.sqrt(snap['budgets']),snap['weighted_matrix'],atol=1e-14,rtol=0)
    assert abs(snap['budgets'][:3].sum()-1/3)<1e-15 and abs(snap['budgets'][3:5].sum()-1/3)<1e-15 and abs(snap['budgets'][5:].sum()-1/3)<1e-15
    fitchecks=[]
    for condition in ['main','minus_Init']:
        x=mat[condition];distance=cdist(x,x)
        for k in [3,4]:
            key=f'NCV14__{condition}__k{k}__s42';label=source['labels'][ix[key]]
            np.testing.assert_array_equal(cdist(x,centers[key],'sqeuclidean').argmin(1),label)
            a=np.zeros(len(d));b=np.full(len(d),np.inf)
            for c in range(k):
                mask=label==c;count=mask.sum();total=distance[:,mask].sum(1)
                a[mask]=total[mask]/(count-1);b[~mask]=np.minimum(b[~mask],total[~mask]/count)
            sil=(b-a)/np.maximum(a,b)
            np.testing.assert_allclose(sil,source['silhouette'][ix[key]],atol=2e-7,rtol=0)
            if condition=='main':
                np.testing.assert_array_equal(snap['K'+str(k)+'_labels'],label)
                membership=frame(f'candidate/K{k}_CLUSTER_MEMBERSHIP.csv','tract_id');np.testing.assert_array_equal(membership.saved_model_class,label);np.testing.assert_array_equal(membership.candidate_display_cluster,label+1)
            fitchecks.append(dict(key=key,silhouette=sil.mean(),negative_fraction=np.mean(sil<0),independent_inertia=np.square(x-centers[key][label]).sum(),no_refit=True))
    check('saved_preprocessing_labels_distance_silhouette','Four saved K3/K4 main/ablation models;source-label exact;SciPy silhouettes;no new fit')
    transition=frame('K3_TO_K4_EXACT_MEMBERSHIP.csv');lab3=snap['K3_labels'];lab4=snap['K4_labels']
    for row in transition.itertuples():
        mask=(lab3==row.K3_model_class)&(lab4==row.K4_model_class)
        assert mask.sum()==row.n_tracts and d.loc[mask,'Population'].sum()==row.population
    assert ((lab4==0)&(lab3!=1)).sum()==0 and (lab4==0).sum()==38
    trace=frame('Q38_ALL_STATION_DEPENDENCY_AND_CONTRIBUTION.csv');qa=np.load(lp(OUT/'inputs/FROZEN_Q38_WEIGHT_AND_INITIAL_SOURCE.npz'))
    np.testing.assert_allclose((qa['weights']*qa['station_effective_initial_mean']).sum(1),qa['expected_tract_initial'],atol=1e-14,rtol=0)
    qid=int(np.flatnonzero(qa['station_ids']=='308581')[0]);assert (qa['weights'][:,qid]>0).sum()==34
    extra=frame('K4_38_TRACT_EXACT_IDENTITY.csv','tract_id').reindex(qa['tract_ids']).prior_Q34_member.eq(False).to_numpy()
    assert extra.sum()==4 and qa['weights'][extra,qid].sum()==0
    assert len(qa['realization_ids'])==len(set(qa['realization_ids']))==len(qa['physical_hashes'])==1000
    check('K3_parent_K4_exception_Q38_source_trace','All38 come fromK3parent;34Qdependencies;4additionalHAYNES/ALAMITOS;1000 frozenidentity hashes;no source propagation')
    context=frame('candidate/PROPOSED_DESCRIPTIVE_COOCCURRENCE_TABLE.csv','tract_id');definition=json.loads(lp(OUT/'candidate/PROPOSED_COOCCURRENCE_DEFINITION.json').read_text())
    cutoff=np.quantile(d.MeanTotalBurden,.75);joint=d.frozen_SOVI_quartile.eq('Q4')&d.MeanTotalBurden.ge(cutoff)
    np.testing.assert_array_equal(context.proposed_Q4_high_burden_cooccurrence,joint)
    assert cutoff==definition['cutoff_equivalent_deficit_hours'] and joint.sum()==94 and d.loc[joint,'Population'].sum()==350799
    assert definition['author_approval_required'] and definition['no_weighted_score']
    check('proposed_screen_no_hidden_formal_hotspot_change','94tracts/350799people;frozenQ4;explicitP75 rule;authorapprovalrequired;notoldweightedscore')
    figure_checks=[]
    manifest=json.loads(lp(OUT/'FIGURE_MANIFEST.json').read_text())
    for r in manifest['figures']:
        with fitz.open(str(lp(OUT/r['pdf']))) as doc:
            page=doc[r['page']-1];assert 'NOT FORMAL STAGE 7' in page.get_text()
            assert not page.get_images(), 'Candidate page must preserve vector marks/text'
            assert abs(page.rect.width-7.2*72)<.1
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    for span in line['spans']:assert page.rect.contains(fitz.Rect(span['bbox'])),(r['pdf'],span['text'])
        with Image.open(lp(OUT/r['PNG'])) as image:
            assert image.width>=4300 and abs(image.info['dpi'][0]-600)<.1
            figure_checks.append(dict(pdf=r['pdf'],page=r['page'],PNG_pixels=image.size,text_inside_page=True))
    check('candidate_artwork_bounds_dimensions','5PDFs/6pages;7.2inch width;600dpi previews;formal path writes0')
    for path in lp(OUT).glob('*.py'):
        code=path.read_text(encoding='utf-8');tree=ast.parse(code)
        assert not any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ['KMeans','run_pipeline'] for node in ast.walk(tree))
    state=json.loads(lp(OUT/'STARTING_STATE_AND_PROTECTION.json').read_text());current={r.split('\t',1)[1]:r.split('\t',1)[0].split()[2] for r in git('ls-tree','-r','HEAD').decode().splitlines()}
    assert all(current.get(p)==oid for p,oid in state['base_tree'].items())
    for p,h in state['protected_files'].items():assert sha(SOURCE_ROOT/p)==h,p
    assert len(state['protected_files'])==950
    assert hashlib.sha256(git('status','--porcelain',cwd=SOURCE_ROOT)).hexdigest()==state['original_status_sha256']
    assert hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest()==state['original_staged_sha256']
    check('950_scientific_files_original_staging_prior_assets_preserved','950actualSHA256;allpriorGitblobs;originalstatus/stagedbytes;candidate-onlypaths')
    visual=json.loads(lp(OUT/'VISUAL_INSPECTION.json').read_text())
    for rec in visual['pages']:assert sha(OUT/rec['pdf'])==rec['PDF_sha256']
    dump('INDEPENDENT_NUMERICAL_AND_PRESERVATION_QA.json',dict(review_status=WARN,all_checks_passed=True,checks=checks,fit_checks=fitchecks,figure_checks=figure_checks,completed_UTC=datetime.now(timezone.utc).isoformat(),review_completed_client_date='2026-10-13',python=platform.python_version(),versions={name:importlib.metadata.version(name) for name in ['numpy','pandas','scipy','scikit-learn','geopandas','shapely','matplotlib','PyMuPDF','Pillow']},new_Kmeans_fits=0,physical_simulations=0,formal_promotion=False))
    save('SOURCE_HASH_VERIFICATION_INDEPENDENT.csv',s.records)
    hashes={}
    for p in lp(OUT).rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(lp(OUT)).as_posix()
        if rel.startswith('tmp/') or '__pycache__' in Path(rel).parts or rel in ['DERIVED_FILE_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json']:continue
        hashes[rel]=dict(sha256=sha(p),bytes=p.stat().st_size)
    dump('DERIVED_FILE_HASHES.json',dict(review_status=WARN,files=hashes))
    print('INDEPENDENT QA COMPLETE',len(checks),'checks',len(hashes),'hashes',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=1):main()
