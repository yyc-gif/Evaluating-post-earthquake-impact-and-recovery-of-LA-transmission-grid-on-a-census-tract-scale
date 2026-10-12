"""Read immutable scientific authorities; write only this diagnostic package."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
AUTH = '81c3452e29abc109f50564d39035c06225e3ea84'
SOURCE_ROOT = Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT', r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
MP = 'docs/data_research/stage7_multi_policy_typology_20261012/'
BE = 'docs/data_research/built_environment_20261009/'
WARN = 'AUTHOR REVIEW - NOT FORMAL STAGE 7'
P2 = ['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','log1p_Population']


def lp(p):
    p = str(Path(p).resolve())
    return Path('\\\\?\\'+p) if sys.platform == 'win32' and not p.startswith('\\\\?\\') else Path(p)


def sha(p):
    h = hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def git(*args,cwd=ROOT):
    return subprocess.check_output(['git','-c','core.longpaths=true','-c','filter.lfs.process=','-c','filter.lfs.required=false',*args],cwd=cwd)


def clean(v):
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,np.generic):v=v.item()
    return None if isinstance(v,float) and not np.isfinite(v) else v


def dump(name,v):
    p=lp(OUT/name);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n',encoding='utf-8')


def save(name,v):
    pd.DataFrame(v).to_csv(lp(OUT/name),index=False,float_format='%.17g',lineterminator='\n')


def sources():
    rel='docs/data_research/stage7_rq_driven_variable_audit_20261011/audit.py'
    candidates=[ROOT/rel,ROOT.parent/'_rq11'/rel,SOURCE_ROOT/rel]
    path=next(p for p in candidates if lp(p).exists())
    assert lp(path).read_bytes().replace(b'\r\n',b'\n')==git('show',AUTH+':'+rel)
    spec=importlib.util.spec_from_file_location('frozen_reader',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.ROOT=ROOT
    return mod.Sources(SOURCE_ROOT,[ROOT]+[ROOT.parent/p for p in ['_mp12','_pk12','_ti12','_rv11','_rq11','_le11','_ca10','_ad11']])


def frozen(s,rel,**kwargs):
    return pd.read_csv(s.source(rel,AUTH),dtype={'tract_id':str,'TRACTFIPS':str},**kwargs)


def dataset(s):
    d=frozen(s,MP+'VERIFIED_DESCRIPTORS_2315.csv').set_index('tract_id').sort_index()
    v=frozen(s,MP+'MULTIPOLICY_RQ2_TRACT_VALUES.csv').query("policy_set=='main5'").set_index('tract_id')
    d[['B_Unconstrained','MeanDelta','PolicySD']]=v[['B_Unconstrained','MeanDelta','PolicySD']].reindex(d.index)
    assert len(d)==2315 and d.index.is_unique and d.index.str.fullmatch(r'\d{11}').all()
    positive=d.loc[d.Population.gt(0)].copy()
    assert len(positive)==2299 and np.isfinite(positive[P2]).all().all()
    return d,positive


def md(name,text):
    lp(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')
