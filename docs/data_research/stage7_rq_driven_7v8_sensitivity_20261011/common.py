"""Bounded diagnostic I/O; reuse the committed source-byte verifier only."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PRIOR = 'docs/data_research/stage7_rq_driven_variable_audit_20261011/'
NRI_AUDIT = 'docs/data_research/built_environment_20261009/nri_eal_redundancy_audit_20261009/'
SPEC = json.loads((OUT / 'FEATURE_SPECIFICATIONS_AND_WEIGHTS.json').read_text())
COMMIT = SPEC['starting_commit']


def lp(path):
    value = str(Path(path).resolve())
    return Path('\\\\?\\' + value) if sys.platform == 'win32' and not value.startswith('\\\\?\\') else Path(value)


def sha(path):
    h = hashlib.sha256()
    with lp(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, np.ndarray)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def dump(name, value):
    lp(OUT / name).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n', encoding='utf-8')


def save(name, frame):
    pd.DataFrame(frame).to_csv(lp(OUT / name), index=False, float_format='%.17g', lineterminator='\n')


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', '-c',
                                    'filter.lfs.process=', '-c', 'filter.lfs.required=false', *args], cwd=cwd)


def frame(name):
    d = pd.read_csv(lp(OUT / name), dtype={'tract_id': str})
    if 'tract_id' in d:
        assert d.tract_id.str.fullmatch(r'\d{11}').all()
    return d


def source_verifier(source_root, caches):
    file = ROOT / PRIOR / 'audit.py'
    blob = git('show', COMMIT + ':' + PRIOR + 'audit.py')
    assert lp(file).read_bytes().replace(b'\r\n', b'\n') == blob
    spec = importlib.util.spec_from_file_location('prior_source_verification', file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Sources(source_root, caches)


def snapshot(source_root, sources):
    old = json.loads(sources.source(PRIOR + 'PRESERVATION_AFTER.json', COMMIT).read_text())
    protected = {rel: sha(Path(source_root) / rel) for rel in old['protected_files']}
    assert protected == old['protected_files'], 'Protected scientific files differ from prior authority'
    return {'protected_count': len(protected), 'protected_files': protected}


def distribution(values):
    a = pd.Series(values).dropna().astype(float)
    return dict(n=len(a), missing=len(values)-len(a), minimum=a.min(), p01=a.quantile(.01),
                p10=a.quantile(.1), p25=a.quantile(.25), median=a.median(), p75=a.quantile(.75),
                p90=a.quantile(.9), p99=a.quantile(.99), maximum=a.max(), mean=a.mean(),
                sd=a.std(ddof=0), zero_count=int(a.eq(0).sum()), zero_fraction=a.eq(0).mean(),
                near_zero_le_1e_8_count=int(a.abs().le(1e-8).sum()),
                skewness=a.skew(), upper_p99_count=int(a.ge(a.quantile(.99)).sum()))


def cohorts(d):
    return {'positive_population': d.loc[d.Population.gt(0)].copy(),
            'residential': d.loc[d.Population.gt(0) & d.housing_total.gt(0)].copy()}
