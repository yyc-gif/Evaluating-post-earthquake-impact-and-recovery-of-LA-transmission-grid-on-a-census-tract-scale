"""Prospective validation guards; physical sampler is replaced by test fixtures."""
import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from la_grid.diagnostics import standalone_ils_validation_20261011 as q


def test_draw_is_saved_once_then_reused_without_sampler(tmp_path,monkeypatch):
    monkeypatch.setattr(q,'OUT',tmp_path)
    q.v.write(tmp_path/'EXECUTION_FREEZE.json',dict(sampling_namespace='engineering-only'))
    ids=[str(i) for i in range(92)]
    model=dict(ids=ids,devices=pd.DataFrame(dict(pga_2pc50=np.ones(92))),cfg=None)
    calls=[]
    def damage(*args):
        calls.append('damage');return np.ones((92,1),dtype=np.int64)
    def repair(ds,rng,cfg):
        calls.append('repair');return np.ones_like(ds),np.full((92,1),2.)
    monkeypatch.setattr(q.v.core,'sample_damage_states',damage)
    monkeypatch.setattr(q.v.core,'damage_to_functionality_and_repair',repair)
    first=q.draw_once(model,tmp_path/'physical/0000',0,set(),set())
    second=q.draw_once(model,tmp_path/'physical/0000',0,set(),set())
    assert first==second and calls==['damage','repair']
    assert first['entropy']==[2026110100,0]
    with pytest.raises(ValueError,match='STOP_FOR_REVIEW'):
        q.draw_once(model,tmp_path/'physical/0000',0,{first['physical_sha256']},set())
    assert calls==['damage','repair']


def test_uncommitted_draw_never_resamples(tmp_path,monkeypatch):
    monkeypatch.setattr(q,'OUT',tmp_path)
    q.v.write(tmp_path/'EXECUTION_FREEZE.json',dict(sampling_namespace='engineering-only'))
    folder=tmp_path/'physical';folder.mkdir();q.v.write(folder/'DRAW_STARTED.json',{})
    with pytest.raises(RuntimeError,match='never redraw'):
        q.draw_once(dict(ids=['x']),folder,0,set(),set())


def test_missing_authorization_refuses_before_sampling(tmp_path,monkeypatch):
    monkeypatch.setattr(q,'OUT',tmp_path)
    q.v.write(tmp_path/'EXECUTION_FREEZE.json',{})
    with pytest.raises(FileNotFoundError):
        q.verify()
    assert not (tmp_path/'cohort').exists()


def test_hash_and_namespace_depend_on_station_order_and_durations():
    ids=['a','b'];ds=np.array([1,2]);dur=np.array([3.,4.])
    h=q.v.physical_hash(ids,ds,dur)
    assert h!=q.v.physical_hash(ids[::-1],ds,dur)
    assert h!=q.v.physical_hash(ids,ds,dur+.001)
    assert not np.array_equal(np.random.default_rng(np.random.SeedSequence([2026110100,0])).random(5),
                              np.random.default_rng(np.random.SeedSequence([202610091,3,2,0])).random(5))
