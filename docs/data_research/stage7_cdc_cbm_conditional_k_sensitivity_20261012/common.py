"""Frozen-source readers; write only inside this isolated review package."""
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
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
AUTH = '896d75d527325d8ea3ac408357cf4be7747e441e'
CB = 'docs/data_research/stage7_cdc_eji_cbm_audit_20261012/'
MP = 'docs/data_research/stage7_multi_policy_typology_20261012/'
MH = 'docs/data_research/stage7_multihazard_rq3_audit_20261012/'
TI = 'docs/data_research/stage7_rq_typology_interpretation_20261012/'
SOURCE_ROOT = Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT', r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
WARN = 'EXPLORATORY AUTHOR REVIEW \u2014 NOT FORMAL STAGE 7'
P2 = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained', 'MeanDelta', 'SOVI_SCORE', 'log1p_Population']
CODES = ['NEHD','SMOKE','BURN','CFLD','DRGT','RFLD','HRCN','SWND','TRND']
REMOVALS = {'no_riverine':['RFLD'], 'no_burn':['BURN'], 'no_heat':['NEHD'], 'no_wildfire':['SMOKE','BURN']}
BUDGETS = {'P2':[1/9,1/9,1/9,1/6,1/6,1/6,1/6],
           'H1':[1/9,1/9,1/9,1/6,1/6,1/9,1/9,1/9],
           'H2':[1/9,1/9,1/9,1/6,1/6,1/6,1/12,1/12]}
PARAMS = dict(init='k-means++', n_init=50, algorithm='lloyd', max_iter=500, tol=1e-4)
SEEDS = list(range(42,47))
KS = list(range(2,9))


def lp(p):
    s = str(Path(p).resolve())
    return Path('\\\\?\\'+s) if sys.platform=='win32' and not s.startswith('\\\\?\\') else Path(s)


def sha(p):
    h = hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git','-c','core.longpaths=true','-c','filter.lfs.process=','-c','filter.lfs.required=false',*args], cwd=cwd)


def clean(v):
    if isinstance(v,dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)): return [clean(x) for x in v]
    if isinstance(v,np.generic): v=v.item()
    return None if isinstance(v,float) and not np.isfinite(v) else v


def dump(name,v):
    p=lp(OUT/name); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n',encoding='utf-8')


def save(name,v):
    pd.DataFrame(v).to_csv(lp(OUT/name),index=False,float_format='%.17g',lineterminator='\n')


def md(name,text):
    lp(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')


def frame(name):
    return pd.read_csv(lp(OUT/name),dtype={'tract_id':str},float_precision='round_trip').set_index('tract_id')


def sources():
    rel='docs/data_research/stage7_rq_driven_variable_audit_20261011/audit.py'
    p=next(p for p in [ROOT/rel,ROOT.parent/'_rq11'/rel,SOURCE_ROOT/rel] if lp(p).exists())
    assert lp(p).read_bytes().replace(b'\r\n',b'\n')==git('show',AUTH+':'+rel)
    spec=importlib.util.spec_from_file_location('frozen_reader',p)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.ROOT=ROOT
    return mod.Sources(SOURCE_ROOT,[ROOT]+[ROOT.parent/p for p in ['_cb12','_mh12','_mp12','_pk12','_ti12','_rv11','_rq11','_le11','_ca10','_ad11']])


def frozen(s,rel,key='tract_id'):
    return pd.read_csv(s.source(rel,AUTH),dtype={key:str,'GEOID':str,'GEOID_2020':str,'GEOID_20':str}).set_index(key)


def cols(spec): return P2+([] if spec=='P2' else ['RPL_CBM'])


def matrix(d,spec,reference=None):
    a=d[cols(spec)].to_numpy(float)
    r=a if reference is None else reference[cols(spec)].to_numpy(float)
    mu,sd=r.mean(0),r.std(0)
    assert np.isfinite(a).all() and (sd>0).all()
    return (a-mu)/sd*np.sqrt(BUDGETS[spec]),mu,sd


def canon(lab,d):
    order=sorted(np.unique(lab),key=lambda c:(d.loc[lab==c,'MeanTotalBurden'].mean(),d.loc[lab==c,'Population'].mean()))
    m={c:i for i,c in enumerate(order)}
    return np.array([m[c] for c in lab],dtype=np.int16)


def match(a,b,pop):
    k=max(a.max(),b.max())+1; tab=np.zeros((k,k),int); np.add.at(tab,(a,b),1)
    i,j=linear_sum_assignment(-tab); mapping=dict(zip(j,i)); aligned=np.array([mapping[c] for c in b])
    changed=aligned!=a
    return dict(ARI=adjusted_rand_score(a,b),reassigned_tracts=int(changed.sum()),
                reassigned_population=int(pop[changed].sum()),reassigned_population_share=pop[changed].sum()/pop.sum()),aligned,tab


def prior_blobs(commit=AUTH):
    paths=git('ls-tree','-r','--name-only',commit,'--','docs/data_research').decode().splitlines()
    p=subprocess.run(['git','-c','core.longpaths=true','cat-file','--batch'],input=('\n'.join(commit+':'+p for p in paths)+'\n').encode(),stdout=subprocess.PIPE,cwd=ROOT,check=True)
    stream=io.BytesIO(p.stdout); result={}
    for path in paths:
        header=stream.readline().decode().split(); assert header[1]=='blob'
        blob=stream.read(int(header[2])); assert stream.read(1)==b'\n'
        result[path]=hashlib.sha256(blob).hexdigest()
    return result
