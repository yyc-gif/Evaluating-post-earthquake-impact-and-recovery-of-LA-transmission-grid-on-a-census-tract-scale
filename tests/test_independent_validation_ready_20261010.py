"""Pure guard tests; no physical model loading or Monte Carlo draws."""
from pathlib import Path

import numpy as np
import pytest

from la_grid.diagnostics import independent_validation_20261010 as v


def test_no_authorization_refuses_execution(tmp_path):
    with pytest.raises(PermissionError):
        v.execute(None,tmp_path/'should-not-exist')
    assert not (tmp_path/'should-not-exist').exists()


def test_physical_pair_hash_is_station_ordered_and_duration_sensitive():
    ids = ['a','b']
    ds = np.array([1,2],dtype=np.int64)
    duration = np.array([1.,2.])
    assert v.physical_hash(ids,ds,duration)!=v.physical_hash(ids,ds,duration+.001)
    assert v.physical_hash(ids,ds,duration)!=v.physical_hash(ids[::-1],ds,duration)
    assert v.physical_hash(ids,ds,duration)==v.physical_hash(ids,ds.astype('>i8'),duration.astype('>f8'))


def test_overlap_never_redraws():
    ids,ds,duration = ['a'],np.array([1]),np.array([2.])
    h = v.physical_hash(ids,ds,duration)
    with pytest.raises(ValueError,match='STOP_FOR_REVIEW'):
        v.check_overlap(ids,ds,duration,{h},set())
    with pytest.raises(ValueError,match='STOP_FOR_REVIEW'):
        v.check_overlap(ids,ds,duration,set(),{h})


def test_long_path_is_idempotent(tmp_path):
    assert v.long_path(v.long_path(tmp_path))==v.long_path(tmp_path)


def test_archive_refuses_protected_and_unrelated_paths(tmp_path):
    protected = tmp_path/'protected'
    protected.mkdir()
    freeze = {'protected_revision_checkout':str(protected)}
    with pytest.raises(ValueError):
        v.check_archive_path(protected/'new',freeze)
    with pytest.raises(ValueError):
        v.check_archive_path(tmp_path,freeze)
    unrelated = tmp_path/'unrelated'
    unrelated.mkdir()
    (unrelated/'keep.txt').write_text('keep',encoding='utf-8')
    with pytest.raises(ValueError):
        v.check_archive_path(unrelated,freeze)
