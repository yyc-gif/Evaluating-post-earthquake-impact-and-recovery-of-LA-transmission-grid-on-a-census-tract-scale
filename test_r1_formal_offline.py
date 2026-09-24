import numpy as np
import pandas as pd

from r1_formal_offline import PreparedMapping, evaluate_exact_event_arrays, weighted_gini_exact
from r1_mapping_gate_robustness import evaluate_mapping
from r1_source_gate import GateTrace
from r1_distributional_metrics import population_weighted_gini


def test_exact_station_integral_matches_retained_tract_evaluator():
    ids = [str(300000 + i) for i in range(92)]
    t = np.array([0.0, 2.0, 7.0])
    f = np.ones((3, 92))
    f[0, 0] = 0.5
    f[0:2, 1] = 0.0
    f[1, 0] = 1.0
    z = np.zeros_like(f)
    F = np.ones_like(f)
    C = np.ones_like(f)
    data = dict(f=f, F=F, C=C, e=f, L_self=1-f,
                L_threshold=z, L_source=z, L_total=1-f)
    trace = GateTrace(**{name: pd.DataFrame(value, index=t, columns=ids)
                         for name, value in data.items()},
                      threshold=.5, source_ids=(), mode="source_gate")
    weights = pd.DataFrame(0.0, index=["r1", "r2", "r3"], columns=ids)
    weights.loc["r1", ids[0]] = .6
    weights.loc["r1", ids[1]] = .4
    weights.loc["r2", ids[1]] = 1.0
    population = pd.Series([100., 200., 50.], index=weights.index)
    quartile = pd.Series(["Q1", "Q4", "Q2"], index=weights.index)
    hospitals = {"r1"}
    prepared = PreparedMapping.from_frame("synthetic", weights, ids,
                                          population, quartile, hospitals)
    fast, tract, _ = evaluate_exact_event_arrays(
        mapping=prepared, event_time_hr=t,
        **{name: data[name] for name in
           ("f", "e", "L_self", "L_threshold", "L_source", "L_total")})
    retained, rows = evaluate_mapping(trace, weights, population, quartile, hospitals)
    for name, value in retained.items():
        if name in fast and isinstance(value, (int, float, np.number)):
            assert np.isclose(value, fast[name], rtol=0, atol=1e-12, equal_nan=True), name
    assert np.allclose(rows.normalized_burden_hr.to_numpy(),
                       tract["normalized_burden_hr"], rtol=0, atol=1e-12,
                       equal_nan=True)
    assert tract["status"].tolist() == ["resolved", "resolved", "unresolved"]


def test_weighted_gini_fast_form_matches_retained_pairwise_definition():
    values = np.array([0.0, 3.0, 10.0, np.nan, 4.0])
    population = np.array([40.0, 20.0, 15.0, 50.0, 25.0])
    expected = population_weighted_gini(
        pd.Series(values), pd.Series(population))
    assert np.isclose(weighted_gini_exact(values, population), expected,
                      rtol=0, atol=1e-15)
