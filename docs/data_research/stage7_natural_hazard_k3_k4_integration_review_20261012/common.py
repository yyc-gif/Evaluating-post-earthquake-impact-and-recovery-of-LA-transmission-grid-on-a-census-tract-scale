"""AUTHOR REVIEW ONLY: frozen sources and package-contained candidate outputs."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
AUTH='49cc153c3f4d7a8c29cf94baf090dbfc0be4d068'
HN='docs/data_research/stage7_nhi_nri_multihazard_comparative_audit_20261012/'
MH='docs/data_research/stage7_multihazard_rq3_audit_20261012/'
TI='docs/data_research/stage7_rq_typology_interpretation_20261012/'
BE='docs/data_research/built_environment_20261009/'
SOURCE_ROOT=Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT',r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
WARN='AUTHOR REVIEW CANDIDATE - NOT FORMAL STAGE 7'
FEATURES=['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','log1p_Population','FEMA_NCV14_CA_v119']
BUDGET=np.array([1/9,1/9,1/9,1/6,1/6,1/6,1/12,1/12])

def lp(p):
    p=str(Path(p).resolve())
    return Path('\\\\?\\'+p) if sys.platform=='win32' and not p.startswith('\\\\?\\') else Path(p)

def git(*a,cwd=ROOT):
    return subprocess.check_output(['git','-c','core.longpaths=true','-c','filter.lfs.process=','-c','filter.lfs.required=false',*a],cwd=cwd)

def sha(p):
    h=hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def dest(name):
    p=OUT/name;assert p.resolve().is_relative_to(OUT)
    lp(p).parent.mkdir(parents=True,exist_ok=True);return lp(p)

def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple,np.ndarray)):return [clean(v) for v in x]
    if isinstance(x,np.generic):x=x.item()
    return None if isinstance(x,float) and not np.isfinite(x) else x

def dump(name,x):dest(name).write_text(json.dumps(clean(x),indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def md(name,x):dest(name).write_text('> '+WARN+'\n\n'+x.strip()+'\n',encoding='utf-8',newline='\n')
def save(name,x):
    x=pd.DataFrame(x).copy()
    if 'review_status' not in x:x.insert(0,'review_status',WARN)
    x.to_csv(dest(name),index=False,float_format='%.17g',lineterminator='\n')

def frame(name,key=None):
    x=pd.read_csv(lp(OUT/name),dtype={'tract_id':str,'GEOID':str,'TRACTFIPS':str,'station_id':str},float_precision='round_trip')
    return x.set_index(key) if key else x

def reader():
    rel='docs/data_research/stage7_rq_driven_variable_audit_20261011/audit.py'
    p=dest('support/commit_bound_reader.py');p.write_bytes(git('show',AUTH+':'+rel))
    dest('support/AUDIT_SPECIFICATION.json').write_bytes(git('show',AUTH+':docs/data_research/stage7_rq_driven_variable_audit_20261011/AUDIT_SPECIFICATION.json'))
    spec=importlib.util.spec_from_file_location('frozen_reader',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.ROOT=ROOT
    return mod.Sources(SOURCE_ROOT,[ROOT,*(ROOT.parent/n for n in ['_hn12','_mh12','_eh12','_ti12','_mp12','_pk12','_ck12','_cb12'])])

def read(s,rel,key=None):
    x=pd.read_csv(s.source(rel,AUTH),dtype={'tract_id':str,'GEOID':str,'TRACTFIPS':str,'station_id':str},float_precision='round_trip')
    return x.set_index(key) if key else x

def table(x):return pd.DataFrame(x).to_markdown(index=False,floatfmt='.6g')
