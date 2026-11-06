import numpy as np
import pytest

from la_grid.diagnostics.ga_impact_event_mechanism_20261106 import (
    event_loss_components,
    sequence_hash,
    source_connected,
)


def test_source_unlock_is_attributed_to_other_station_dependency_mass():
    adjacency = [{1}, {0, 2}, {1}]
    sources = {0}
    before_f = np.array([1.0, 0.0, 1.0])
    after_f = np.array([1.0, 1.0, 1.0])
    before_F = before_f >= 0.5
    after_F = after_f >= 0.5
    before_C = source_connected(before_f, adjacency, sources)
    after_C = source_connected(after_f, adjacency, sources)

    result = event_loss_components(
        before_f, before_F, before_C, after_f, after_F, after_C,
        event_stations=[1], station_mass=np.array([10.0, 20.0, 30.0]),
        total_population=60.0, time_hr=100.0, horizon_hr=480.0,
    )

    assert before_C.tolist() == [True, False, False]
    assert after_C.tolist() == [True, True, True]
    assert result["direct_source_loss_delta_hr"] == pytest.approx(0.0)
    assert result["external_source_loss_delta_hr"] == pytest.approx(-190.0)
    assert result["unlocked_station_count"] == 1
    assert result["unlocked_dependency_mass_person_equiv"] == pytest.approx(30.0)
    assert result["unlocked_effective_service_mass_person_equiv"] == pytest.approx(30.0)


def test_sequence_hash_is_order_sensitive_and_newline_terminated():
    assert sequence_hash(["a", "b"]) != sequence_hash(["b", "a"])
    assert len(sequence_hash(["station"])) == 64
