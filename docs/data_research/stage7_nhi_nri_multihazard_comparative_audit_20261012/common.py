"""Commit-bound inputs and package-only outputs for the two-track hazard audit."""
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
AUTH = '8ce85454e9db1b6991c311b1ebec1948e5bf1fe0'
EH = 'docs/data_research/stage7_final_eighth_hazard_coordinate_20261012/'
CK = 'docs/data_research/stage7_cdc_cbm_conditional_k_sensitivity_20261012/'
MH = 'docs/data_research/stage7_multihazard_rq3_audit_20261012/'
MP = 'docs/data_research/stage7_multi_policy_typology_20261012/'
BE = 'docs/data_research/built_environment_20261009/nri_eal_redundancy_audit_20261009/'
SOURCE_ROOT = Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT', r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
WARN = 'EXPLORATORY MULTI-HAZARD INDEX AUDIT \u2014 NOT FORMAL STAGE 7'
P2 = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained', 'MeanDelta', 'SOVI_SCORE', 'log1p_Population']
BUDGET = np.array([1/9, 1/9, 1/9, 1/6, 1/6, 1/6, 1/12, 1/12])
PARAMS = dict(init='k-means++', n_init=50, algorithm='lloyd', max_iter=500, tol=1e-4)
SEEDS = [42, 43, 44, 45, 46]
ID_COLUMNS = ['tract_id','GEOID','GEOID_TRACT_10','GEOID_TRACT_20','source_2010_GEOID',
              'dominant_2010_GEOID','geometric_total_area_dominant_2010_GEOID','dominant_source',
              'FIPS','TRACTFIPS','STCOFIPS']


def lp(path):
    value = str(Path(path).resolve())
    return Path('\\\\?\\' + value) if sys.platform == 'win32' and not value.startswith('\\\\?\\') else Path(value)


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', '-c', 'filter.lfs.process=', '-c', 'filter.lfs.required=false', *args], cwd=cwd)


def sha(path):
    h = hashlib.sha256()
    with lp(path).open('rb') as file:
        for chunk in iter(lambda: file.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def dest(name):
    path = OUT / name
    assert path.resolve().is_relative_to(OUT)
    lp(path).parent.mkdir(parents=True, exist_ok=True)
    return lp(path)


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    return None if isinstance(value, float) and not np.isfinite(value) else value


def dump(name, value):
    dest(name).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def save(name, value):
    d = pd.DataFrame(value).copy()
    if 'review_status' not in d:
        d.insert(0, 'review_status', WARN)
    d.to_csv(dest(name), index=False, float_format='%.17g', lineterminator='\n')


def md(name, text):
    dest(name).write_text('> ' + WARN + '\n\n' + text.strip() + '\n', encoding='utf-8', newline='\n')


def reader():
    rel = 'docs/data_research/stage7_rq_driven_variable_audit_20261011/audit.py'
    candidates = [ROOT / rel, ROOT.parent / '_rq11' / rel, SOURCE_ROOT / rel]
    p = next((lp(p) for p in candidates if lp(p).exists()), None)
    if p is None:
        # Rehydrate the exact committed reader if a disposable prior worktree is absent.
        p = dest('support/commit_bound_sources_reader.py')
        p.write_bytes(git('show', AUTH + ':' + rel))
        dest('support/AUDIT_SPECIFICATION.json').write_bytes(git('show', AUTH + ':docs/data_research/stage7_rq_driven_variable_audit_20261011/AUDIT_SPECIFICATION.json'))
    assert p.read_bytes().replace(b'\r\n', b'\n') == git('show', AUTH + ':' + rel)
    spec = importlib.util.spec_from_file_location('commit_bound_reader', p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    caches = [ROOT] + [ROOT.parent / name for name in ['_eh12', '_ck12', '_cb12', '_mh12', '_mp12', '_pk12', '_ti12', '_rv11', '_rq11']]
    return module.Sources(SOURCE_ROOT, caches)


def read(s, rel, key=None):
    d = pd.read_csv(s.source(rel, AUTH), dtype={'tract_id': str, 'GEOID': str, 'STCOFIPS': str, 'TRACTFIPS': str}, float_precision='round_trip')
    return d.set_index(key) if key else d


def frame(name, key=None):
    d = pd.read_csv(lp(OUT / name), dtype={c:str for c in ID_COLUMNS}, float_precision='round_trip')
    return d.set_index(key) if key else d


def tree(commit=AUTH):
    return {line.split('\t', 1)[1]: line.split('\t', 1)[0].split()[2] for line in git('ls-tree', '-r', commit).decode().splitlines()}


def weighted(d, hazard):
    x = np.column_stack([d[P2].to_numpy(float), np.asarray(hazard, float)])
    assert np.isfinite(x).all() and (x.std(0) > 0).all()
    return (x - x.mean(0)) / x.std(0) * np.sqrt(BUDGET)
