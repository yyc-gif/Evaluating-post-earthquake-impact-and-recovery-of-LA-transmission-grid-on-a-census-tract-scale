"""Isolated, source-verified interpretation I/O. No scientific model execution."""
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
AUTH = 'b2ed86401ad7ac98ed7a7bef5c83ddd08e4f23dc'
PREVIOUS = 'docs/data_research/stage7_rq_driven_7v8_sensitivity_20261011/'
AUDIT = 'docs/data_research/stage7_rq_driven_variable_audit_20261011/'
FORMAL = 'Formal_Experiment_20260923/'
SOURCE_ROOT = Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT', r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
CACHES = [ROOT.parent / p for p in ['_rv11', '_rq11', '_ms7', '_ad11', '_le11']]
SPECS = ['A', 'B', 'A-minus-Init', 'B-minus-Init']
KS = [3, 4, 5]
SEEDS = [42, 43, 44, 45, 46]


def lp(p):
    s = str(Path(p).resolve())
    return Path('\\\\?\\' + s) if sys.platform == 'win32' and not s.startswith('\\\\?\\') else Path(s)


def sha(p):
    h = hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', '-c', 'filter.lfs.process=',
                                   '-c', 'filter.lfs.required=false', *args], cwd=cwd)


def sources():
    path = ROOT / AUDIT / 'audit.py'
    blob = git('show', AUTH + ':' + AUDIT + 'audit.py')
    assert lp(path).read_bytes().replace(b'\r\n', b'\n') == blob
    spec = importlib.util.spec_from_file_location('verified_source_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Sources(SOURCE_ROOT, CACHES)


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


def frame(name):
    return pd.read_csv(lp(OUT / name), dtype={'tract_id': str, 'substation_id': str})


def frozen(s, rel, key='tract_id'):
    return pd.read_csv(s.source(rel, AUTH), dtype={key: str}).set_index(key)


def preserve(s):
    prior = json.loads(s.source(PREVIOUS + 'PRESERVATION_AFTER.json', AUTH).read_text())
    current = {p: sha(SOURCE_ROOT / p) for p in prior['protected_files']}
    assert current == prior['protected_files']
    return current


def inputs(s):
    d = frozen(s, PREVIOUS + 'TRACT_FEATURES_VERIFIED_2315.csv').sort_index()
    d = d.loc[d.Population.gt(0)]
    assert len(d) == 2299 and d.index.str.fullmatch(r'\d{11}').all()
    labels = frozen(s, PREVIOUS + 'CLUSTER_MEMBERSHIPS_POSITIVE_POPULATION.csv').reindex(d.index)
    spec = json.loads(s.source(PREVIOUS + 'FEATURE_SPECIFICATIONS_AND_WEIGHTS.json', AUTH).read_text())
    return d, labels, spec
