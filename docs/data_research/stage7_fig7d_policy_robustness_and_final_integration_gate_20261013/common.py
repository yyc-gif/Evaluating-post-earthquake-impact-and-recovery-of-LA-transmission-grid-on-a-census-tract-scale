"""Frozen input verification and package-only outputs; no simulation or fitting."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
AUTH = '0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
PRIOR = 'docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/'
MP = 'docs/data_research/stage7_multi_policy_typology_20261012/'
PK = 'docs/data_research/stage7_policy_reference_and_k_selection_20261012/'
SOURCE_ROOT = Path(os.environ.get('LA_GRID_FROZEN_SOURCE_ROOT', r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'))
WARN = 'AUTHOR REVIEW - NOT FORMAL STAGE 7'
PRIMARY = ['impact-first', 'hospital-first', 'degree-first', 'betweenness-first', 'vulnerability-first']
FIXED_P75 = 38.38135467381475
FEATURES = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained', 'MeanDelta', 'SOVI_SCORE', 'log1p_Population', 'FEMA_NCV14_CA_v119']
BUDGET = np.array([1/9, 1/9, 1/9, 1/6, 1/6, 1/6, 1/12, 1/12])


def lp(path):
    text = str(Path(path).resolve())
    return Path('\\\\?\\' + text) if sys.platform == 'win32' and not text.startswith('\\\\?\\') else Path(text)


def sha(path):
    h = hashlib.sha256()
    with lp(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', '-c', 'filter.lfs.process=', '-c', 'filter.lfs.required=false', *args], cwd=cwd)


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


def md(name, text):
    dest(name).write_text('> ' + WARN + '\n\n' + text.strip() + '\n', encoding='utf-8', newline='\n')


def save(name, rows):
    frame = pd.DataFrame(rows).copy()
    if 'review_status' not in frame:
        frame.insert(0, 'review_status', WARN)
    frame.to_csv(dest(name), index=False, float_format='%.17g', lineterminator='\n')


def frame(name, key=None):
    data = pd.read_csv(lp(OUT / name), dtype={'tract_id': str, 'GEOID': str, 'substation_id': str}, float_precision='round_trip')
    return data.set_index(key) if key else data


class Sources:
    def __init__(self):
        self.records = []
        self.resolved = {}

    def source(self, rel, commit=AUTH):
        key = (commit, rel)
        if key in self.resolved:
            return self.resolved[key]
        blob = git('show', commit + ':' + rel)
        lfs = blob.startswith(b'version https://git-lfs.github.com/spec/v1')
        digest = blob.decode().split('oid sha256:')[1].splitlines()[0] if lfs else hashlib.sha256(blob).hexdigest()
        common = Path(git('rev-parse', '--git-common-dir').decode().strip())
        if not common.is_absolute():
            common = ROOT / common
        roots = [SOURCE_ROOT, ROOT, *(ROOT.parent / n for n in ['_sf12', '_mp12', '_pk12', '_hn12', '_ti12'])]
        candidates = [*(p / rel for p in roots), common / 'lfs/objects' / digest[:2] / digest[2:4] / digest]
        for path in candidates:
            if not lp(path).is_file():
                continue
            actual = sha(path)
            equivalent = not lfs and lp(path).read_bytes().replace(b'\r\n', b'\n') == blob
            if actual == digest or equivalent:
                self.records.append(dict(source_file=rel, commit=commit, committed_sha256=digest, actual_sha256=actual,
                                         bytes=lp(path).stat().st_size, LFS=lfs, CRLF_equivalent_only=actual != digest))
                self.resolved[key] = lp(path)
                return lp(path)
        if not lfs:
            path = dest('tmp/committed_blobs/' + digest + Path(rel).suffix)
            path.write_bytes(blob)
            self.records.append(dict(source_file=rel, commit=commit, committed_sha256=digest, actual_sha256=sha(path),
                                     bytes=len(blob), LFS=False, materialized_exact_committed_text=True))
            self.resolved[key] = path
            return path
        raise FileNotFoundError('Missing exact frozen source: ' + commit + ':' + rel)

    def archive(self, rel, expected):
        path = lp(SOURCE_ROOT / rel)
        assert sha(path) == expected, rel
        self.records.append(dict(source_file=rel, commit='', actual_sha256=expected, bytes=path.stat().st_size,
                                 external_manifest_bound=True))
        return path


def eligible():
    data = frame('inputs/EIGHT_VARIABLE_FROZEN_TABLE.csv', 'tract_id').sort_index()
    assert len(data) == 2299 and data.index.is_unique and data.index.str.fullmatch(r'\d{11}').all()
    assert (data.Population > 0).all() and data.Population.sum() == 9066522
    return data


def profiles_table(data):
    return pd.DataFrame(data).to_markdown(index=False, floatfmt='.6g')
