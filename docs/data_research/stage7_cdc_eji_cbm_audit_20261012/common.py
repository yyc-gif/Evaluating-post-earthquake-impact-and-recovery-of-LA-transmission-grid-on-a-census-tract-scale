"""Source-bound CDC CBM diagnostics; never write outside this package."""
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
AUTH = '022f3f9a8a1fb3e454de05559311f1763a2ebb3b'
MH = 'docs/data_research/stage7_multihazard_rq3_audit_20261012/'
MP = 'docs/data_research/stage7_multi_policy_typology_20261012/'
SOURCE_ROOT = Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT', r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
P2 = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained', 'MeanDelta', 'SOVI_SCORE', 'log1p_Population']
WARN = 'AUTHOR REVIEW - NOT FORMAL STAGE 7'


def lp(p):
    p = str(Path(p).resolve())
    return Path('\\\\?\\' + p) if sys.platform == 'win32' and not p.startswith('\\\\?\\') else Path(p)


def sha(p):
    h = hashlib.sha256()
    with lp(p).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', '-c', 'filter.lfs.process=', '-c', 'filter.lfs.required=false', *args], cwd=cwd)


def clean(v):
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray)):
        return [clean(x) for x in v]
    if isinstance(v, np.generic):
        v = v.item()
    return None if isinstance(v, float) and not np.isfinite(v) else v


def dump(name, v):
    p = lp(OUT / name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(clean(v), indent=2, allow_nan=False) + '\n', encoding='utf-8')


def save(name, v):
    pd.DataFrame(v).to_csv(lp(OUT / name), index=False, float_format='%.17g', lineterminator='\n')


def md(name, text):
    lp(OUT / name).write_text(text.strip() + '\n', encoding='utf-8')


def sources():
    rel = 'docs/data_research/stage7_rq_driven_variable_audit_20261011/audit.py'
    path = next(p for p in [ROOT / rel, ROOT.parent / '_rq11' / rel, SOURCE_ROOT / rel] if lp(p).exists())
    assert lp(path).read_bytes().replace(b'\r\n', b'\n') == git('show', AUTH + ':' + rel)
    spec = importlib.util.spec_from_file_location('frozen_reader', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = ROOT
    return mod.Sources(SOURCE_ROOT, [ROOT] + [ROOT.parent / p for p in ['_mh12', '_mp12', '_pk12', '_ti12', '_rv11', '_rq11', '_le11', '_ca10', '_ad11']])


def frozen(s, rel):
    return pd.read_csv(s.source(rel, AUTH), dtype={'tract_id': str, 'GEOID': str, 'TRACTFIPS': str})


def dataset(s):
    full = frozen(s, MH + 'FROZEN_P2_AND_COHORT.csv').set_index('tract_id').sort_index()
    assert len(full) == 2315 and full.index.is_unique and full.index.str.fullmatch(r'\d{11}').all()
    d = full.loc[full.Population.gt(0)].copy()
    assert len(d) == 2299 and int(d.additional_zero_housing_positive_population.sum()) == 8
    assert np.isfinite(d[P2]).all().all()
    return full, d


def describe(v):
    valid = pd.to_numeric(v, errors='coerce').replace(-999, np.nan).dropna()
    return dict(n=len(valid), missing_or_sentinel=len(v)-len(valid), min=valid.min(), max=valid.max(),
                mean=valid.mean(), sd=valid.std(ddof=0), median=valid.median(),
                p10=valid.quantile(.1), p25=valid.quantile(.25), p75=valid.quantile(.75), p90=valid.quantile(.9),
                zero_count=int(valid.eq(0).sum()), unique_values=valid.nunique())
