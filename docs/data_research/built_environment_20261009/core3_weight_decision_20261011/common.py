"""Isolated CORE3 weight diagnostics; hash-verified reads, no parent edits."""
from pathlib import Path
import hashlib,json,subprocess,datetime,sys
BASELINE='22e77dd2cfd6adaee5a1be6bb2feeb34da27eeb2'
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
PREFIX='docs/data_research/built_environment_20261009/'
REVIEW='shortlist_resolution_review_20261011/'
ORIGINAL=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
UNRESOLVED=['06037189703','06037301601','06037301602','06037404600']
SEEDS=list(range(42,62))
DOMAIN_COLUMNS={'Recovery':['B_480_hr','Init_Supply'],'Grid':['Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI'],'Physical':['emc2022_total_built_land_fraction','housing_5plus_share','scag2020_classified_land_entropy'],'Social':['SOVI_SCORE'],'Stock':['log1p_BUILDVALUE'],'ALR':['ALR_NPCTL']}
COLS=[c for columns in DOMAIN_COLUMNS.values() for c in columns]
WEIGHTS={'W1':[.2,.2,.2,.2,.1,.1],'W2':[1/6]*6,'W3':[2/11,4/11,2/11,1/11,1/11,1/11],'W4':[.2,.2,.2,.2,.05,.15],'W5':[.2,.2,.2,.2,.15,.05]}
PARAMS=dict(n_clusters=4,n_init=100,max_iter=500,tol=1e-4,algorithm='lloyd')

def lp(p):
    s=str(p);return Path(s if s.startswith('\\\\?\\') else '\\\\?\\'+str(Path(p).absolute()))
def sha(p):
    h=hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def git(*args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=str(cwd).removeprefix('\\\\?\\'))
def clean(v):
    import numpy as np
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    if isinstance(v,np.ndarray):return clean(v.tolist())
    if isinstance(v,np.generic):v=v.item()
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
def dump(n,v):lp(OUT/n).write_text(json.dumps(clean(v),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def textfile(n,t):lp(OUT/n).write_text(t.strip()+'\n',encoding='utf-8',newline='\n')
def log(s):
    print(s,flush=True)
    with lp(OUT/'EXECUTION_LOG.md').open('a',encoding='utf-8',newline='\n') as f:f.write(f'- {datetime.datetime.now(datetime.timezone.utc).isoformat()}: {s}\n')
def source(rel):
    path=PREFIX+rel;blob=git('show',BASELINE+':'+path)
    expected=blob.decode().split('oid sha256:')[1].splitlines()[0] if blob.startswith(b'version https://git-lfs.github.com/spec/v1') else hashlib.sha256(blob).hexdigest()
    for root in [ROOT,ROOT.parent/'_sr11',ROOT.parent/'_cs11',ROOT.parent/'_ca10',ORIGINAL]:
        p=lp(root/path)
        if p.exists() and sha(p)==expected:
            old=lp(OUT/'INPUT_HASHES.json');d=json.loads(old.read_text()) if old.exists() else {}
            d[path]=dict(path=str(p),sha256=expected,bytes=p.stat().st_size,commit=BASELINE);dump('INPUT_HASHES.json',d);return p
    raise FileNotFoundError('Actual baseline bytes unavailable: '+path)
def frame(rel):
    import pandas as pd
    f=pd.read_csv(source(rel),dtype={'tract_id':str})
    if 'tract_id' in f:
        assert f.tract_id.str.fullmatch(r'\d{11}').all() and f.tract_id.is_unique;f=f.set_index('tract_id')
    return f
def save(n,v,index=False):
    import pandas as pd
    (v if isinstance(v,pd.DataFrame) else pd.DataFrame(v)).to_csv(lp(OUT/n),index=index,na_rep='',float_format='%.17g',lineterminator='\n')
def factors(scheme):
    import numpy as np
    w=dict(zip(DOMAIN_COLUMNS,WEIGHTS[scheme]));return np.array([np.sqrt(w[k]/len(cols)) for k,cols in DOMAIN_COLUMNS.items() for _ in cols])
def hashids(ids):return hashlib.sha256('\n'.join(ids).encode()).hexdigest()
def snapshot():
    prior=json.loads(source(REVIEW+'PRESERVATION_BEFORE.json').read_text())
    files={p:sha(ORIGINAL/p) if lp(ORIGINAL/p).exists() else None for p in prior['protected_files']}
    return dict(original_HEAD=git('rev-parse','HEAD',cwd=ORIGINAL).decode().strip(),original_branch=git('branch','--show-current',cwd=ORIGINAL).decode().strip(),protected_count=len(files),protected_files=files,staged_count=len([p for p in git('diff','--cached','--name-only','-z',cwd=ORIGINAL).split(b'\0') if p]),index_sha256=hashlib.sha256(git('ls-files','--stage','-z',cwd=ORIGINAL)).hexdigest(),status_sha256=hashlib.sha256(git('status','--porcelain=v1','-z',cwd=ORIGINAL)).hexdigest())

def inputs():
    import numpy as np,pandas as pd,ast
    spec=json.loads(source(REVIEW+'CONTROLLED_SHORTLIST_SPECIFICATION.json').read_text())
    old=frame('final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv');ids=spec['primary_GEOID_order']
    master=frame('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_RESIDENTIAL_2291.csv')
    for c in ['B_480_hr','Init_Supply',*DOMAIN_COLUMNS['Grid'],'SOVI_SCORE','ALR_NPCTL']:
        assert np.allclose(master.loc[ids,c],old.loc[ids,c],atol=1e-11,rtol=1e-12);master.loc[ids,c]=old.loc[ids,c]
    master.loc[ids,'log1p_BUILDVALUE']=old.loc[ids,'log1p_NRI_BUILDVALUE']
    data=master.loc[ids].copy();assert len(master)==2291 and len(data)==2287 and data[COLS].notna().all().all()
    assert set(master.index)-set(ids)==set(UNRESOLVED)
    blocks=frame('final_feature_validation_20261010/TRACT_SPATIAL_BLOCKS.csv').loc[ids]
    blocks['block_id']=blocks.block.map(lambda s:':'.join(map(str,ast.literal_eval(s))))
    cases={int(k):v for k,v in spec['spatial_cases'].items()};assert set(cases)==set(SEEDS)
    assert len(set(tuple(sorted(v)) for v in cases.values()))==17
    assert spec['KMeans']==PARAMS and spec['seeds']==SEEDS
    return master,data,blocks,cases,spec
