"""Commit-bound sources and package-scoped outputs; no formal science writes."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
AUTH = '5eeaa02ca4dec99f27a6ee3eb470a441007e6f6b'
CK = 'docs/data_research/stage7_cdc_cbm_conditional_k_sensitivity_20261012/'
CB = 'docs/data_research/stage7_cdc_eji_cbm_audit_20261012/'
MH = 'docs/data_research/stage7_multihazard_rq3_audit_20261012/'
MP = 'docs/data_research/stage7_multi_policy_typology_20261012/'
SOURCE_ROOT = Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT', r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
WARN = 'EXPLORATORY EIGHT-VARIABLE AUTHOR REVIEW \u2014 NOT FORMAL STAGE 7'
CODES = ['NEHD','SMOKE','BURN','CFLD','DRGT','RFLD','HRCN','SWND','TRND']
P2 = ['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','log1p_Population']
BUDGETS = {'P2': [1/9,1/9,1/9,1/6,1/6,1/6,1/6],
           'H1': [1/9,1/9,1/9,1/6,1/6,1/9,1/9,1/9],
           'H2': [1/9,1/9,1/9,1/6,1/6,1/6,1/12,1/12]}
PARAMS = dict(init='k-means++',n_init=50,algorithm='lloyd',max_iter=500,tol=1e-4)


def lp(path):
    value = str(Path(path).resolve())
    return Path('\\\\?\\'+value) if sys.platform == 'win32' and not value.startswith('\\\\?\\') else Path(value)


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git','-c','core.longpaths=true','-c','filter.lfs.process=','-c','filter.lfs.required=false',*args],cwd=cwd)


def sha(path):
    h = hashlib.sha256()
    with lp(path).open('rb') as f:
        for part in iter(lambda:f.read(1048576),b''): h.update(part)
    return h.hexdigest()


def destination(name):
    path = OUT / name
    assert path.resolve().is_relative_to(OUT)
    lp(path).parent.mkdir(parents=True,exist_ok=True)
    return lp(path)


def clean(v):
    if isinstance(v,dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)): return [clean(x) for x in v]
    if isinstance(v,np.generic): v=v.item()
    return None if isinstance(v,float) and not np.isfinite(v) else v


def dump(name,v):
    destination(name).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n',encoding='utf-8')


def save(name,v):
    d=pd.DataFrame(v).copy()
    if 'review_status' not in d: d.insert(0,'review_status',WARN)
    d.to_csv(destination(name),index=False,float_format='%.17g',lineterminator='\n')


def md(name,v):
    destination(name).write_text('> '+WARN+'\n\n'+v.strip()+'\n',encoding='utf-8')


def source_reader():
    rel='docs/data_research/stage7_rq_driven_variable_audit_20261011/audit.py'
    candidates=[ROOT/rel,ROOT.parent/'_rq11'/rel,SOURCE_ROOT/rel]
    p=next(lp(p) for p in candidates if lp(p).exists())
    assert p.read_bytes().replace(b'\r\n',b'\n')==git('show',AUTH+':'+rel)
    spec=importlib.util.spec_from_file_location('commit_bound_reader',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT
    return m.Sources(SOURCE_ROOT,[ROOT]+[ROOT.parent/w for w in ['_ck12','_cb12','_mh12','_mp12','_pk12','_ti12','_rv11','_rq11']])


def read(s,rel,key=None):
    d=pd.read_csv(s.source(rel,AUTH),dtype={'tract_id':str,'GEOID':str,'GEOID_2020':str},float_precision='round_trip')
    return d.set_index(key) if key else d


def frame(name,key=None):
    d=pd.read_csv(lp(OUT/name),dtype={'tract_id':str},float_precision='round_trip')
    return d.set_index(key) if key else d


def prior_blobs():
    result={}
    lines=git('ls-tree','-r',AUTH,'--','docs/data_research').decode().splitlines()
    for line in lines:
        meta,path=line.split('\t',1)
        result[path]=meta.split()[2]
    return result


def matrix(d,sp):
    cols=P2+([] if sp=='P2' else ['RPL_CBM'])
    a=d[cols].to_numpy(float)
    return (a-a.mean(0))/a.std(0)*np.sqrt(BUDGETS[sp])
