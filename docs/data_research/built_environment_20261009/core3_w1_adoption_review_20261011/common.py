"""Isolated read-only scientific sources; writes only this adoption package."""
from pathlib import Path
import hashlib,json,subprocess,datetime
BASELINE='adb3cb49ced687730beff7ebf88f9c5e161062ed'
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
PREFIX='docs/data_research/built_environment_20261009/'
W='core3_weight_decision_20261011/'
R='shortlist_resolution_review_20261011/'
M='manuscript_reconciliation_20261010/'
B='manuscript_integration_preview_20261010/'
ORIGINAL=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
COLS=['B_480_hr','Init_Supply','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','emc2022_total_built_land_fraction','housing_5plus_share','scag2020_classified_land_entropy','SOVI_SCORE','log1p_BUILDVALUE','ALR_NPCTL']
DOMAINS={'Recovery':COLS[:2],'Grid':COLS[2:6],'Physical':COLS[6:9],'Social':COLS[9:10],'Stock':COLS[10:11],'ALR':COLS[11:12]}
UNRESOLVED=['06037189703','06037301601','06037301602','06037404600']
SEEDS=list(range(42,62))
PALETTE={'C1':'#0072B2','C2':'#E69F00','C3':'#009E73','C4':'#D55E00'}

def lp(p):
    s=str(p);return Path(s if s.startswith('\\\\?\\') else '\\\\?\\'+str(Path(p).absolute()))
def sha(p):
    h=hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def git(*a,cwd=ROOT):return subprocess.check_output(['git',*a],cwd=str(cwd).removeprefix('\\\\?\\'))
def clean(v):
    import numpy as np
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    if isinstance(v,np.ndarray):return clean(v.tolist())
    if isinstance(v,np.generic):v=v.item()
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
def dump(n,v):lp(OUT/n).write_text(json.dumps(clean(v),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def text(n,t):lp(OUT/n).write_text(t.strip()+'\n',encoding='utf-8',newline='\n')
def log(t):
    print(t,flush=True)
    with lp(OUT/'EXECUTION_LOG.md').open('a',encoding='utf-8',newline='\n') as f:f.write(f'- {datetime.datetime.now(datetime.timezone.utc).isoformat()}: {t}\n')
def record(p,h,commit,role):
    file=lp(OUT/'INPUT_HASHES.json');d=json.loads(file.read_text()) if file.exists() else {}
    d[role]={'path':str(p),'sha256':h,'bytes':lp(p).stat().st_size,'commit':commit};dump('INPUT_HASHES.json',d)
def source(rel,commit=BASELINE):
    blob=git('show',commit+':'+rel)
    expected=blob.decode().split('oid sha256:')[1].splitlines()[0] if blob.startswith(b'version https://git-lfs.github.com/spec/v1') else hashlib.sha256(blob).hexdigest()
    for root in [ROOT,ROOT.parent/'_w311',ROOT.parent/'_ms7',ROOT.parent/'_sr11',ROOT.parent/'_cs11',ORIGINAL]:
        p=lp(root/rel)
        if p.exists() and sha(p)==expected:record(p,expected,commit,rel);return p
    raise FileNotFoundError('Actual verified source bytes missing: '+rel)
def src(rel):return source(PREFIX+rel)
def read(rel):
    import pandas as pd
    return pd.read_csv(src(rel),dtype={'tract_id':str})
def save(n,v):
    import pandas as pd
    (v if isinstance(v,pd.DataFrame) else pd.DataFrame(v)).to_csv(lp(OUT/n),index=False,float_format='%.17g',na_rep='',lineterminator='\n')
def snapshot():
    prior=json.loads(src(W+'PRESERVATION_BEFORE.json').read_text())
    files={p:sha(ORIGINAL/p) if lp(ORIGINAL/p).exists() else None for p in prior['protected_files']}
    return dict(original_HEAD=git('rev-parse','HEAD',cwd=ORIGINAL).decode().strip(),protected_files=files,protected_count=len(files),index_sha256=hashlib.sha256(git('ls-files','--stage','-z',cwd=ORIGINAL)).hexdigest(),status_sha256=hashlib.sha256(git('status','--porcelain=v1','-z',cwd=ORIGINAL)).hexdigest(),staged_count=len([p for p in git('diff','--cached','--name-only','-z',cwd=ORIGINAL).split(b'\0') if p]))
def match(a,b,mask,na=4,nb=4):
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    table=np.zeros((na,nb),int);np.add.at(table,(a[mask],b[mask]),1)
    i,j=linear_sum_assignment(-table);mp={int(y):int(x) for x,y in zip(i,j)}
    return np.array([mp.get(int(x),-1) for x in b]),mp,table
