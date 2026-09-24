import numpy as np
import pandas as pd

from r1_formal_schedule import FormalScheduleDecoder
from r1_realization_scheduling import execute_realization_schedule


def test_compiled_decode_matches_production_scheduler():
    ids = [str(300000 + i) for i in range(92)]
    base = pd.DataFrame(np.full((2, 92), 0.25), index=["depot-A", "depot-B"], columns=ids)
    base.loc["depot-B", ids[1]] = 0.5
    task = pd.DataFrame(np.full((92, 92), 1.0), index=ids, columns=ids)
    np.fill_diagonal(task.values, 0.0)
    task.loc[ids[0], ids[2]] = 0.125
    task.loc[ids[2], ids[0]] = 9.0
    context = {"ids": ids, "base": base, "task": task}
    decoder = FormalScheduleDecoder(context)
    sequence = ids.copy()
    ds = pd.Series(0, index=ids, dtype="int64")
    ds.iloc[[0, 1, 2, 3]] = [1, 2, 3, 4]
    duration = pd.Series(0.0, index=ids)
    duration.iloc[[0, 1, 2, 3]] = [1.0, 2.0, 3.0, 4.0]
    crew_origins = ["depot-A", "depot-B"]
    expected, _, clocks, queue = execute_realization_schedule(
        full_priority_sequence=sequence, damage_state=ds,
        realized_duration_hr=duration, crew_origin_ids=crew_origins,
        base_to_task_hr=base, task_to_task_hr=task,
    )
    got = decoder.decode(order=decoder.order(sequence), damage=ds.to_numpy(),
                         duration=duration.to_numpy(), origins=decoder.origins(crew_origins))
    completion, arrival, travel, crew, prior, dispatch, final_clocks = got
    lookup = {station: i for i, station in enumerate(ids)}
    assert queue == tuple(ids[:4])
    for row in expected.itertuples():
        i = lookup[row.task_id]
        assert completion[i] == row.completion_hr
        assert arrival[i] == row.arrival_hr
        assert travel[i] == row.travel_hr
        assert crew[i] == row.crew_index
        assert prior[i] == (-1 if row.previous_task_id is None else lookup[row.previous_task_id])
        assert dispatch[i] == row.dispatch_rank - 1
    assert np.array_equal(final_clocks, clocks)
    assert np.isnan(completion[4:]).all()
