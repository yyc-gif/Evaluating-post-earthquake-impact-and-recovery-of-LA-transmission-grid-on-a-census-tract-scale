"""Independent CSV/Decimal ranking, SciPy distances and preservation checks."""
import csv
from decimal import Decimal
import math
import py_compile
import zipfile
from importlib.metadata import version
import fitz
from PIL import Image
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits
from common import *


def independent_silhouette(dist,lab):
    n=len(lab); classes=np.unique(lab); mean=np.empty((n,len(classes)))
    for c in classes:
        mask=lab==c; mean[:,c]=dist[:,mask].sum(axis=1)/mask.sum()
    counts=np.bincount(lab); own=mean[np.arange(n),lab]*counts[lab]/np.maximum(counts[lab]-1,1)
    mean[np.arange(n),lab]=np.inf; other=mean.min(axis=1)
    ans=(other-own)/np.maximum(own,other); ans[counts[lab]==1]=0
    return ans


def main():
    s=sources(); d=frame('VERIFIED_COHORT_AND_DESCRIPTORS.csv')
    assert len(d)==2299 and d.index.is_unique and d.index.str.fullmatch(r'\d{11}').all()
    assert (d.Population>0).all() and d.Population.sum()==9066522
    assert d.additional_zero_housing_positive_population.sum()==8
    full=frozen(s,CB+'FROZEN_P2_AND_COHORT.csv').sort_index()
    np.testing.assert_array_equal(d.Population,full.loc[d.index,'Population'])
    np.testing.assert_array_equal(d.frozen_SOVI_quartile,full.loc[d.index,'frozen_SOVI_quartile'])
    assert set(frame('EXCLUDED_ZERO_POPULATION_GEOIDS.csv').index)==set(full.index[full.Population.eq(0)])
    # Decimal rather than pandas float summation: exact ties in published four-decimal EPLs.
    scores=[]; published=[]; ids=[]; removed={name:[] for name in REMOVALS}; total=0; matched={}; sumerror=0
    with zipfile.ZipFile(s.source(CB+'sources/EJI_2024_United_States_CSV.zip',AUTH)) as z:
        with z.open('EJI_2024_United_States.csv') as f:
            reader=csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''))
            assert [c for c in CODES if 'F_'+c not in reader.fieldnames]==['NEHD','SMOKE','BURN']
            for row in reader:
                total+=1; rank=float(row['RPL_CBM'])
                if row['GEOID'] in d.index: matched[row['GEOID']]=row
                if not 0<=rank<=1: continue
                decimal=[Decimal(row['EPL_'+c]) for c in CODES]
                assert all(v>=0 for v in decimal)
                ticks=[int(v*10000) for v in decimal]
                assert all(Decimal(t)/10000==v for t,v in zip(ticks,decimal))
                scores.append(float(row['SPL_CBM']));published.append(rank);ids.append(row['GEOID'])
                sumerror=max(sumerror,abs(float(sum(decimal))-float(row['SPL_CBM'])))
                for name,drop in REMOVALS.items(): removed[name].append(sum(t for t,c in zip(ticks,CODES) if c not in drop))
    assert total==85188 and len(scores)==83509 and len(matched)==2299 and sumerror<1e-12
    r=np.searchsorted(np.sort(scores),scores,side='left')/(len(scores)-1)
    err=np.max(np.abs(r-published));assert err<=.0000501
    saved=frame('NATIONAL_COMPONENT_REMOVAL_TRACT_RANKS.csv');rank_errors=[]
    for name,a in removed.items():
        rank=np.searchsorted(np.sort(a),a,side='left')/(len(a)-1)
        expected=pd.Series(rank,index=ids).reindex(d.index)
        diff=np.max(np.abs(expected-saved[name]));assert diff<1e-15;rank_errors.append(diff)
    for id,row in matched.items():
        assert row['GEOID_2020']==id and int(row['F_HRCN'])==1
        assert math.isclose(float(row['RPL_CBM']),d.loc[id,'RPL_CBM'],abs_tol=2e-16,rel_tol=0)
    assert sum(float(row['E_BURN'])==0 for row in matched.values())==2251
    arrays=np.load(lp(OUT/'REGISTERED_FIT_ARRAYS.npz')); matrices=np.load(lp(OUT/'VERIFIED_WEIGHTED_MATRICES.npz'))
    np.testing.assert_array_equal(arrays['tract_ids'],d.index);np.testing.assert_array_equal(matrices['tract_ids'],d.index)
    fit=pd.read_csv(lp(OUT/'P2_VS_P2_CBM_K_DIAGNOSTICS.csv')).set_index(['specification','condition','k','seed'])
    con=pd.read_csv(lp(OUT/'DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv'))
    compare=pd.read_csv(lp(OUT/'P2_VS_P2_CBM_MEMBERSHIP_COMPARISONS.csv'))
    index={key:i for i,key in enumerate(arrays['keys'])}; max_inertia_error=0; max_sil_error=0; cache={}; tested=0
    for key,pos in index.items():
        sp,tail=key.split('__',1);condition=tail.rsplit('__k',1)[0];k=int(key.rsplit('__k',1)[1].split('__')[0]);seed=int(key.rsplit('__s',1)[1])
        x=matrices[sp+'__'+condition];lab=arrays['labels'][pos];sil=arrays['silhouette'][pos]
        assert lab.shape==(2299,) and set(lab)==set(range(k))
        centers=np.stack([x[lab==c].mean(0) for c in range(k)])
        inertia=np.sum((x-centers[lab])**2)
        delta=abs(inertia-fit.loc[(sp,condition,k,seed),'WCSS']); assert delta<1e-9;max_inertia_error=max(max_inertia_error,delta)
        if k>1 and seed==42:
            cond=sp+'__'+condition
            if cond not in cache:
                cache={cond:cdist(x,x,metric='euclidean')}
            independent=independent_silhouette(cache[cond],lab)
            difference=np.max(np.abs(independent-sil));assert difference<1e-10;max_sil_error=max(max_sil_error,difference);tested+=1
        if condition=='published':
            weights=np.array(BUDGETS[sp]);raw=d[cols(sp)].to_numpy()
            expected=(raw-raw.mean(0))/raw.std(0)*np.sqrt(weights)
            np.testing.assert_array_equal(expected,x)
            assert abs(weights.sum()-1)<1e-15 and abs(((x-x.mean(0))**2).sum()-2299)<1e-8
            for a,b in [(0,3),(3,5),(5,len(weights))]:assert abs(weights[a:b].sum()-1/3)<1e-15
            if seed==42:
                part=con.loc[con.specification.eq(sp)&con.condition.eq(condition)&con.k.eq(k)&con.seed.eq(seed)]
                assert abs(part.within_SS.sum()-inertia)<1e-8
                assert abs(part.total_SS.sum()-2299)<1e-8
    for _,row in compare.iterrows():
        sp=row.specification;k=int(row.k);seed=int(row.seed)
        a=arrays['labels'][index[f'{sp}__published__k{k}__s{seed}']]
        other=f'{row.alternative}__published' if row.comparison=='feature_specification' else sp+'__'+row.alternative
        b=arrays['labels'][index[f'{other}__k{k}__s{seed}']]
        assert abs(adjusted_rand_score(a,b)-row.ARI)<1e-12
        value,_,_=match(a,b,d.Population.to_numpy())
        assert value['reassigned_tracts']==row.reassigned_tracts and value['reassigned_population']==row.reassigned_population
    old=np.load(s.source(MP+'REGISTERED_FIT_ARRAYS.npz',AUTH)); oi={key:i for i,key in enumerate(old['keys'])}
    reused=0
    for key,pos in index.items():
        if not key.startswith('P2__'): continue
        equivalent=key.replace('P2__published__','P2__main5__cohort__').replace('P2__policy_','P2__')
        np.testing.assert_array_equal(arrays['labels'][pos],old['labels'][oi[equivalent]]);reused+=1
    assert reused==124
    repeats=[]
    for sp,k in [('H1',3),('H2',5)]:
        x=matrices[sp+'__published'];model=KMeans(n_clusters=k,random_state=42,**PARAMS).fit(x)
        expected=canon(model.labels_,d); savedlabel=arrays['labels'][index[f'{sp}__published__k{k}__s42']]
        np.testing.assert_array_equal(expected,savedlabel);repeats.append(f'{sp}/K{k}/seed42')
    al=pd.read_csv(lp(OUT/'RQ3_ADDITION_VS_REALLOCATION_ALGEBRA.csv'))
    assert np.max(np.abs(al.old_seven_budget_BSS+al.climate_added_BSS+al.reallocation_SOVI_BSS+al.reallocation_population_BSS-al.new_total_BSS))<1e-10
    start=json.loads(lp(OUT/'STARTING_STATE_AND_PROTECTION.json').read_text())
    for path,digest in start['protected_files'].items(): assert sha(SOURCE_ROOT/path)==digest,path
    assert git('status','--porcelain',cwd=SOURCE_ROOT).decode()==start['source_status']
    assert hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest()==start['source_staged_diff_sha256']
    assert prior_blobs()==start['prior_git_blobs']
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    changed=git('diff','--name-only',AUTH).decode().splitlines();assert all(p.startswith(prefix) for p in changed)
    graphics=[]
    for path in sorted(lp(OUT/'figures').glob('*.pdf')):
        doc=fitz.open(path);assert len(doc)==1 and not doc[0].get_images()
        page=doc[0];text=page.get_text();assert 'EXPLORATORY AUTHOR REVIEW' in text and 'NOT FORMAL STAGE 7' in text
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    b=fitz.Rect(span['bbox']);assert b.x0>=-.5 and b.y0>=-.5 and b.x1<=page.rect.width+.5 and b.y1<=page.rect.height+.5,(path.name,span)
        with Image.open(path.with_suffix('.png')) as im:
            assert min(im.info['dpi'])>=599
            assert all(abs(a-b)<=1 for a,b in zip(im.size,[round(page.rect.width/72*600),round(page.rect.height/72*600)]))
            pixels=im.size
        assert path.with_name(path.stem+'_publication_review.png').exists()
        graphics.append(dict(file=path.name,pages=1,vector_without_image_objects=True,all_text_within_page=True,
            pixels=pixels,dpi=600,visual_review='Every native publication-size render inspected in task'))
    assert len(graphics)==8
    for script in lp(OUT).glob('*.py'):
        py_compile.compile(str(script),cfile=str(lp(OUT/'tmp'/f'{script.stem}.pyc')),doraise=True)
    qa=dict(label=WARN,status='PASS_WITH_UNRESOLVED_CDC_SOURCE_QUALITY',authority=AUTH,cohort=2299,domain=2315,
        national_valid=83509,independent_Decimal_sum_error=sumerror,official_rank_rounding_error=err,
        exact_component_rank_max_error=max(rank_errors),saved_fits=len(index),full_cohort_silhouette_independent_seed42_fits=tested,
        maximum_independent_silhouette_error=max_sil_error,maximum_inertia_error=max_inertia_error,P2_labels_unchanged=reused,
        exact_repeated_fits=repeats,protected_files_unchanged=950,prior_diagnostic_git_blobs_unchanged=len(start['prior_git_blobs']),
        original_dirty_and_staged_state_unchanged=True,physical_models_rerun=False,formal_promotion=False,
        source_quality_gate_passed=False,graphics=graphics,
        versions={p:version(p) for p in ['numpy','pandas','scipy','scikit-learn','geopandas','matplotlib','PyMuPDF']})
    dump('INDEPENDENT_QA.json',qa);save('SOURCE_HASH_VERIFICATION_INDEPENDENT.csv',s.records)
    hashes={}
    for path in sorted(lp(OUT).rglob('*')):
        rel=path.relative_to(lp(OUT)).as_posix()
        if path.is_file() and not any(p in rel.split('/') for p in ['tmp','__pycache__']) and rel not in ['DERIVED_FILE_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json']:
            hashes[rel]=dict(sha256=sha(path),bytes=path.stat().st_size)
    dump('DERIVED_FILE_HASHES.json',hashes)
    print('INDEPENDENT QA PASS',json.dumps(clean({k:v for k,v in qa.items() if k not in ['graphics','versions']})),flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=1): main()
