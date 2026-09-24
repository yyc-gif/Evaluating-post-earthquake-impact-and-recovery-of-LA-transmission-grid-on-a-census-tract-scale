from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from r1_formal_archive import inspect_formal_archive, retain_formal_trajectory


@dataclass
class Trace:
    f: pd.DataFrame
    F: pd.DataFrame
    C: pd.DataFrame
    e: pd.DataFrame
    L_self: pd.DataFrame
    L_threshold: pd.DataFrame
    L_source: pd.DataFrame
    L_total: pd.DataFrame


def fixture():
    ids = [str(300000 + i) for i in range(92)]
    f = pd.DataFrame(np.ones((2, 92)), index=[0.0, 480.0], columns=ids)
    zeros = f * 0.0
    trace = Trace(f, f, f, f, zeros, zeros, zeros, zeros)
    identity = dict(
        matrix_id="JULY92_REVIEWER_REVISION_FINAL_V1",
        executable_code_commit_sha="abc", hazard="2pc50",
        realization_id="2pc50__evaluation_0000", split="evaluation",
        strategy="hospital-first", resource_scenario="C57_D1",
        DS_hash="ds", duration_hash="duration", physical_sample_hash="physical",
        graph_hash="graph", source_set_hash="source",
        mapping_method_id="M1_UTILITY_003", crew_roster_hash="crew",
        directed_travel_hash="travel", event_horizon_hr=480.0,
    )
    return trace, pd.DataFrame(columns=["task_id", "completion_hr"]), identity


def test_archive_write_and_verified_resume(tmp_path: Path):
    trace, events, identity = fixture()
    assert inspect_formal_archive(tmp_path, identity=identity, stem="one") is None
    assert retain_formal_trajectory(tmp_path, trace=trace, task_events=events, identity=identity, stem="one") == "written"
    assert inspect_formal_archive(tmp_path, identity=identity, stem="one")["event_count"] == 0
    assert retain_formal_trajectory(tmp_path, trace=trace, task_events=events, identity=identity, stem="one") == "reused"
    changed = dict(identity, duration_hash="different")
    with pytest.raises(ValueError, match="identity changed"):
        inspect_formal_archive(tmp_path, identity=changed, stem="one")
    with pytest.raises(ValueError, match="identity changed"):
        retain_formal_trajectory(tmp_path, trace=trace, task_events=events, identity=changed, stem="one")


def test_archive_detects_partial_or_mutated_files(tmp_path: Path):
    trace, events, identity = fixture()
    retain_formal_trajectory(tmp_path, trace=trace, task_events=events, identity=identity, stem="one")
    (tmp_path / "one__TASK_EVENTS.csv").unlink()
    with pytest.raises(ValueError, match="Partial"):
        inspect_formal_archive(tmp_path, identity=identity, stem="one")
    (tmp_path / "one__TASK_EVENTS.csv").write_text("task_id,completion_hr\n", encoding="utf-8")
    (tmp_path / "one.npz").write_bytes(b"damaged")
    with pytest.raises(ValueError, match="contents changed"):
        inspect_formal_archive(tmp_path, identity=identity, stem="one")
