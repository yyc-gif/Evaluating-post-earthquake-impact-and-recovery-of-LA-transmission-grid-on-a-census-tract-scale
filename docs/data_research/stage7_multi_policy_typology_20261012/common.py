"""Frozen readers and outputs confined to this diagnostic package."""
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
AUTH = '739420417412228f9302051d154f11ba3d5cde84'
AUDIT = 'docs/data_research/stage7_rq_driven_variable_audit_20261011/'
PREVIOUS = 'docs/data_research/stage7_rq_driven_7v8_sensitivity_20261011/'
INTERPRETATION = 'docs/data_research/stage7_rq_typology_interpretation_20261012/'
POLICY_AUDIT = 'docs/data_research/stage7_policy_reference_and_k_selection_20261012/'
FORMAL = 'Formal_Experiment_20260923/'
SOURCE_ROOT = Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT', r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
PRIMARY = ['impact-first', 'hospital-first', 'degree-first', 'betweenness-first', 'vulnerability-first']
POLICIES = ['unconstrained', *PRIMARY, 'random']
SETS = {'main5': PRIMARY, **{'without_' + p: [q for q in PRIMARY if q != p] for p in PRIMARY}, 'plus_random': [*PRIMARY, 'random']}
RQ1 = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI']
RQ3 = ['SOVI_SCORE', 'log1p_Population']
COLS = {'A': RQ1 + ['B_480_hr', 'Delta_B_logistics'] + RQ3,
        'P2': RQ1 + ['B_Unconstrained', 'MeanDelta'] + RQ3,
        'P3': RQ1 + ['B_Unconstrained', 'MeanDelta', 'PolicySD'] + RQ3}
SEEDS = list(range(42, 47))
KS = list(range(2, 9))
PARAMS = dict(init='k-means++', n_init=50, algorithm='lloyd', max_iter=500, tol=1e-4)


def lp(p):
    s = str(Path(p).resolve())
    return Path('\\\\?\\' + s) if sys.platform == 'win32' and not s.startswith('\\\\?\\') else Path(s)


def sha(p):
    h = hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', '-c', 'filter.lfs.process=', '-c', 'filter.lfs.required=false', *args], cwd=cwd)


def sources():
    p = ROOT / AUDIT / 'audit.py'
    assert lp(p).read_bytes().replace(b'\r\n', b'\n') == git('show', AUTH + ':' + AUDIT + 'audit.py')
    spec = importlib.util.spec_from_file_location('frozen_source_reader', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Sources(SOURCE_ROOT, [ROOT.parent / p for p in ['_pk12','_ti12','_rv11','_rq11','_ms7','_ad11','_le11']])


def clean(v):
    if isinstance(v, dict): return {str(k): clean(x) for k,x in v.items()}
    if isinstance(v, (list,tuple,np.ndarray)): return [clean(x) for x in v]
    if isinstance(v, np.generic): v = v.item()
    return None if isinstance(v,float) and not np.isfinite(v) else v


def dump(name, v):
    lp(OUT/name).write_text(json.dumps(clean(v), indent=2, allow_nan=False)+'\n', encoding='utf-8')


def save(name, rows):
    pd.DataFrame(rows).to_csv(lp(OUT/name), index=False, float_format='%.17g', lineterminator='\n')


def md(name, text):
    lp(OUT/name).write_text(text.strip()+'\n', encoding='utf-8')


def frame(name):
    return pd.read_csv(lp(OUT/name), dtype={'tract_id': str, 'substation_id': str})


def frozen(s, rel, key='tract_id'):
    return pd.read_csv(s.source(rel, AUTH), dtype={key: str}).set_index(key)


def columns(spec):
    return COLS[spec.replace('-minus-Init','')][int(spec.endswith('-minus-Init')):]


def weights(spec):
    c = columns(spec)
    n1 = sum(v in RQ1 for v in c)
    n2 = len(c) - n1 - 2
    return np.array([1/(3*n1) if v in RQ1 else 1/6 if v in RQ3 else 1/(3*n2) for v in c])


def matrix(d, spec, reference=None):
    x = d[columns(spec)].to_numpy(float)
    ref = x if reference is None else reference[columns(spec)].to_numpy(float)
    mu, sd = ref.mean(0), ref.std(0)
    assert np.isfinite(x).all() and (sd > 0).all()
    return (x-mu)/sd*np.sqrt(weights(spec)), mu, sd


def dataset(policy_set='main5'):
    d = frame('VERIFIED_DESCRIPTORS_2315.csv').set_index('tract_id').sort_index()
    v = frame('MULTIPOLICY_RQ2_TRACT_VALUES.csv').query('policy_set == @policy_set').set_index('tract_id')
    d[['B_Unconstrained','MeanDelta','PolicySD','MeanTotalBurden','MeanWithinRealizationPolicySD']] = v[['B_Unconstrained','MeanDelta','PolicySD','MeanTotalBurden','MeanWithinRealizationPolicySD']].reindex(d.index)
    return d.loc[d.Population.gt(0)]


def canon(lab, d, spec):
    burden = 'B_480_hr' if spec.startswith('A') else 'MeanTotalBurden'
    order = sorted(np.unique(lab), key=lambda c: (d.loc[lab==c,burden].mean(), d.loc[lab==c,'Population'].mean()))
    remap = {v:i for i,v in enumerate(order)}
    return np.array([remap[v] for v in lab], dtype=np.int16)


def key(spec, policy_set, scaling, k, seed):
    return f'{spec}__{policy_set}__{scaling}__k{k}__s{seed}'
