"""Read verified archived bytes; write only the living-environment diagnostic package."""
from pathlib import Path
import hashlib,json,subprocess,datetime
import numpy as np
BASELINE='e4497dcf2182535ef1eda9612ca45c43704c1a6f'
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
PREFIX='docs/data_research/built_environment_20261009/'
ORIGINAL=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
UNRESOLVED=['06037189703','06037301601','06037301602','06037404600']
def lp(p):
    s=str(p);return Path(s if s.startswith('\\\\?\\') else '\\\\?\\'+str(Path(p).absolute()))
def sha(p):
    h=hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def git(*a,cwd=ROOT):return subprocess.check_output(['git',*a],cwd=str(cwd).removeprefix('\\\\?\\'))
def clean(v):
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    if isinstance(v,np.ndarray):return clean(v.tolist())
    if isinstance(v,np.generic):v=v.item()
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
def dump(n,v):
    p=lp(OUT/n);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(clean(v),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def text(n,t):lp(OUT/n).write_text(t.strip()+'\n',encoding='utf-8',newline='\n')
def log(t):
    print(t,flush=True)
    with lp(OUT/'EXECUTION_LOG.md').open('a',encoding='utf-8',newline='\n') as f:f.write(f'- {datetime.datetime.now(datetime.timezone.utc).isoformat()}: {t}\n')
def source(rel,commit=BASELINE):
    blob=git('show',commit+':'+rel)
    expected=blob.decode().split('oid sha256:')[1].splitlines()[0] if blob.startswith(b'version https://git-lfs.github.com/spec/v1') else hashlib.sha256(blob).hexdigest()
    for root in [ROOT]+[ROOT.parent/x for x in ['_ad11','_w311','_sr11','_cs11','_ca10','_ms7']]+[ORIGINAL]:
        p=lp(root/rel)
        if p.exists() and sha(p)==expected:
            q=lp(OUT/'INPUT_HASHES.json');d=json.loads(q.read_text(encoding='utf-8')) if q.exists() else {}
            d[rel]=dict(path=str(p),sha256=expected,bytes=p.stat().st_size,commit=commit);dump('INPUT_HASHES.json',d);return p
    raise FileNotFoundError('No verified actual bytes available: '+rel)
def src(rel):return source(PREFIX+rel)
def frame(rel):
    import pandas as pd
    return pd.read_csv(src(rel),dtype={'tract_id':str}).set_index('tract_id')
def save(n,v):
    import pandas as pd
    (v if isinstance(v,pd.DataFrame) else pd.DataFrame(v)).to_csv(lp(OUT/n),index=False,float_format='%.17g',na_rep='',lineterminator='\n')
def idhash(ids):return hashlib.sha256(('\n'.join(map(str,ids))+'\n').encode()).hexdigest()
def snapshot():
    protected=json.loads(src('core3_w1_adoption_review_20261011/PRESERVATION_BEFORE.json').read_text(encoding='utf-8'))['protected_files']
    return dict(original_HEAD=git('rev-parse','HEAD',cwd=ORIGINAL).decode().strip(),protected_files={p:sha(ORIGINAL/p) for p in protected},protected_count=len(protected),index_sha256=hashlib.sha256(git('ls-files','--stage','-z',cwd=ORIGINAL)).hexdigest(),status_sha256=hashlib.sha256(git('status','--porcelain=v1','-z',cwd=ORIGINAL)).hexdigest(),staged_count=len([p for p in git('diff','--cached','--name-only','-z',cwd=ORIGINAL).split(b'\0') if p]))
