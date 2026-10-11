from pathlib import Path
import hashlib, json, subprocess, datetime

BASELINE = '94faefd30273dec8318197de443f2f992fa29e5c'
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
CA = ROOT.parent / '_ca10'
ORIGINAL = Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
REL = 'docs/data_research/built_environment_20261009/'
UNRESOLVED = ['06037189703','06037301601','06037301602','06037404600']

def lp(p):
    s=str(p)
    return Path(s if s.startswith('\\\\?\\') else '\\\\?\\'+str(Path(p).absolute()))

def sha(p):
    h=hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''): h.update(b)
    return h.hexdigest()

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git',*args],cwd=str(cwd).removeprefix('\\\\?\\'))

def clean(v):
    import numpy as np
    if isinstance(v, dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    if isinstance(v,np.ndarray): return clean(v.tolist())
    if isinstance(v,np.generic): v=v.item()
    if isinstance(v,float) and not np.isfinite(v): return None
    return v

def dump(name,obj):
    lp(OUT/name).write_text(json.dumps(clean(obj),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def log(message):
    print(message,flush=True)
    with lp(OUT/'EXECUTION_LOG.md').open('a',encoding='utf-8') as f:
        f.write(f'- {datetime.datetime.now(datetime.timezone.utc).isoformat()}: {message}\n')

def source(relative):
    rel=REL+relative
    blob=git('show',BASELINE+':'+rel)
    expected=blob.decode().split('oid sha256:')[1].splitlines()[0] if blob.startswith(b'version https://git-lfs.github.com/spec/v1') else hashlib.sha256(blob).hexdigest()
    for root in [ROOT,CA,ORIGINAL,ROOT.parent/'_cw10',ROOT.parent/'_stage7_be_validity_20261010']:
        p=lp(root/rel)
        if p.exists() and sha(p)==expected:
            rp=lp(OUT/'INPUT_HASHES.json')
            rows=json.loads(rp.read_text(encoding='utf-8')) if rp.exists() else {}
            rows[rel]=dict(path=str(p),sha256=expected,bytes=p.stat().st_size,commit=BASELINE)
            dump('INPUT_HASHES.json',rows)
            return p
    raise FileNotFoundError('No actual hash-verified payload: '+rel)

def frame(relative):
    import pandas as pd
    f=pd.read_csv(source(relative),dtype={'tract_id':str})
    if 'tract_id' in f:
        assert f.tract_id.str.fullmatch(r'\d{11}').all() and f.tract_id.is_unique
        f=f.set_index('tract_id')
    return f

def save(name,rows,index=False):
    import pandas as pd
    f=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    f.to_csv(lp(OUT/name),index=index,float_format='%.15g',lineterminator='\n',na_rep='')

def snapshot():
    prior=json.loads(source('candidate_admission_rebuild_20261010/PENDING_COMPLETION_PROTECTION_AFTER.json').read_text(encoding='utf-8'))
    result={k:sha(ORIGINAL/k) if lp(ORIGINAL/k).exists() else None for k in prior['protected_files']}
    index=git('ls-files','--stage','-z',cwd=ORIGINAL)
    status=git('status','--porcelain=v1','-z',cwd=ORIGINAL)
    return dict(original_head=git('rev-parse','HEAD',cwd=ORIGINAL).decode().strip(),original_branch=git('branch','--show-current',cwd=ORIGINAL).decode().strip(),logical_index_sha256=hashlib.sha256(index).hexdigest(),status_sha256=hashlib.sha256(status).hexdigest(),staged_count=len([x for x in git('diff','--cached','--name-only','-z',cwd=ORIGINAL).split(b'\0') if x]),protected_count=len(result),protected_files=result)

if __name__=='__main__':
    assert git('rev-parse','HEAD').decode().strip()==BASELINE
    assert git('status','--porcelain').decode().strip() in ['', '?? docs/data_research/built_environment_20261009/shortlist_resolution_20261011/']
    if not lp(OUT/'PRESERVATION_BEFORE.json').exists(): dump('PRESERVATION_BEFORE.json',snapshot())
    log('Isolated shortlist worktree initialized from '+BASELINE)
