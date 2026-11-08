import pandas as pd
import pytest

from la_grid.diagnostics.c1_mechanism_actionability import (
    classify_damage_state_batch,
    summarize_event_damage_states,
)


def test_damage_state_batches_preserve_simultaneous_repair_grouping():
    assert classify_damage_state_batch("1") == "DS1"
    assert classify_damage_state_batch("2;4") == "DS2_4"
    assert classify_damage_state_batch("1;3") == "mixed_DS1_and_DS2_4"
    with pytest.raises(ValueError):
        classify_damage_state_batch("0;2")


def test_event_summary_uses_realization_means_not_event_rows_as_replicates():
    events = pd.DataFrame([
        {"policy": "impact-first", "realization_id": "r0", "damage_states": "1",
         "newly_source_connected_other_count": 1,
         "newly_source_connected_other_dependency_mass_people": 10.0,
         "indirect_service_gain_person_equiv": 20.0},
        {"policy": "impact-first", "realization_id": "r0", "damage_states": "1",
         "newly_source_connected_other_count": 0,
         "newly_source_connected_other_dependency_mass_people": 0.0,
         "indirect_service_gain_person_equiv": 0.0},
        {"policy": "impact-first", "realization_id": "r1", "damage_states": "1",
         "newly_source_connected_other_count": 0,
         "newly_source_connected_other_dependency_mass_people": 0.0,
         "indirect_service_gain_person_equiv": 0.0},
    ])

    result = summarize_event_damage_states(events, bootstrap_reps=100)[0]
    assert result["event_batches"] == 3
    assert result["realizations_with_events"] == 2
    assert result["external_unlock_batch_fraction"] == pytest.approx(0.25)
    assert result["indirect_gain_person_equiv_per_event"] == pytest.approx(5.0)
    assert result["external_unlock_batch_fraction_bootstrap_95ci"][0] <= 0.25
    assert result["external_unlock_batch_fraction_bootstrap_95ci"][1] >= 0.25
