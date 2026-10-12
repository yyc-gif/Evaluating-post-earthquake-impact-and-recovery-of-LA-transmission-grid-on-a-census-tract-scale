"""Read-only frozen inputs and isolated diagnostic output helpers."""
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
AUTH = '66d16d61b13c05785f58795ef9d13ba82ece472e'
PREVIOUS = 'docs/data_research/stage7_rq_driven_7v8_sensitivity_20261011/'
INTERPRETATION = 'docs/data_research/stage7_rq_typology_interpretation_20261012/'
AUDIT = 'docs/data_research/stage7_rq_driven_variable_audit_20261011/'
FORMAL = 'Formal_Experiment_20260923/'
SOURCE_ROOT = Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT', r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
POLICIES = ['impact-first', 'hospital-first', 'degree-first', 'betweenness-first', 'vulnerability-first', 'random']
FEATURES = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_480_hr', 'Delta_B_logistics', 'SOVI_SCORE', 'log1p_Population']
SEEDS = [42, 43, 44, 45, 46]
KS = list(range(2, 9))


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
    path = ROOT / AUDIT / 'audit.py'
    assert lp(path).read_bytes().replace(b'\r\n', b'\n') == git('show', AUTH + ':' + AUDIT + 'audit.py')
    spec = importlib.util.spec_from_file_location('source_reader_only', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    caches = [ROOT.parent / p for p in ['_ti12', '_rv11', '_rq11', '_ms7', '_ad11', '_le11']]
    return module.Sources(SOURCE_ROOT, caches)


def clean(v):
    if isinstance(v, dict): return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray)): return [clean(x) for x in v]
    if isinstance(v, np.generic): v = v.item()
    if isinstance(v, float) and not np.isfinite(v): return None
    return v


def dump(name, value):
    lp(OUT / name).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n', encoding='utf-8')


def save(name, data):
    pd.DataFrame(data).to_csv(lp(OUT / name), index=False, float_format='%.17g', lineterminator='\n')


def md(name, text):
    lp(OUT / name).write_text(text.strip() + '\n', encoding='utf-8')


def frame(name):
    return pd.read_csv(lp(OUT / name), dtype={'tract_id': str, 'substation_id': str})


def frozen(s, rel, key='tract_id'):
    return pd.read_csv(s.source(rel, AUTH), dtype={key: str}).set_index(key)


def preserve(s):
    prior = json.loads(s.source(PREVIOUS + 'PRESERVATION_AFTER.json', AUTH).read_text())
    current = {p: sha(SOURCE_ROOT / p) for p in prior['protected_files']}
    assert current == prior['protected_files']
    return current


def data():
    return frame('VERIFIED_FIXED_FEATURES_2315.csv').set_index('tract_id').sort_index()


def weights(spec):
    return np.array([1/9]*3 + [1/6]*4) if spec == 'A' else np.full(6, 1/6)


def columns(spec):
    return FEATURES if spec == 'A' else FEATURES[1:]


def canon(labels, d):
    order = sorted(np.unique(labels), key=lambda c: (d.loc[labels == c, 'B_480_hr'].mean(), d.loc[labels == c, 'Population'].mean()))
    return np.array([{c: i for i, c in enumerate(order)}[v] for v in labels], dtype=np.int16)


def matrix(d, spec, reference=None):
    x = d[columns(spec)].to_numpy(float)
    ref = x if reference is None else reference[columns(spec)].to_numpy(float)
    mu, sd = ref.mean(0), ref.std(0)
    assert np.isfinite(x).all() and (sd > 0).all()
    return (x - mu) / sd * np.sqrt(weights(spec)), mu, sd
