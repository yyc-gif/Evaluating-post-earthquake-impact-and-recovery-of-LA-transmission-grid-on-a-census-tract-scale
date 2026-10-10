import numpy as np
import pytest
import pandas as pd

from la_grid.diagnostics.ga_research_mechanism_20261009 import influences
from la_grid.diagnostics.ga_research_report_20261009 import contrast, convergence_summary


def test_interaction_is_within_seed_difference_in_differences():
    data = {s: {"a": {"planning_loss_hr": 10+s},
                "b": {"planning_loss_hr": 11+s},
                "c": {"planning_loss_hr": 12+s},
                "d": {"planning_loss_hr": 15+s}} for s in range(5)}
    result = contrast(data, {"a": 1, "b": -1, "c": -1, "d": 1}, "interaction", 3)
    assert result["n"] == 5
    assert result["mean_delta_hr"] == 2
    assert result["simultaneous95_low_hr"] == result["simultaneous95_high_hr"] == 2


def test_influential_sample_omissions_preserve_mean_objective():
    values = np.r_[-1., np.full(63, .01)]
    report = influences(values)
    assert report["better_samples"] == 1 and report["worse_samples"] == 63
    assert report["mean_delta_hr"] == pytest.approx(values.mean())
    assert report["leave_one_out"][0]["leave_one_out_mean_delta_hr"] == pytest.approx(.01)
    assert report["leave_one_out"][0]["ranking_reversed"]
    assert report["exhaustive_omissions"][0]["ga_better_count"] == 1
    assert report["exhaustive_omissions"][1]["subsets"] == 2016
    assert report["exhaustive_omissions"][1]["ga_better_count"] == 63
    assert report["exhaustive_omissions"][2]["subsets"] == 41664
    assert report["exhaustive_omissions"][2]["ga_better_count"] == 1953


@pytest.mark.parametrize("values", [np.zeros(63), np.r_[np.nan,np.zeros(63)]])
def test_invalid_planning_sample_domain_rejected(values):
    with pytest.raises(AssertionError):
        influences(values)


def test_checkpoints_are_paired_within_search_not_independent_observations():
    data = pd.DataFrame([dict(batch="x", configuration="a", seed=seed,
        evaluations=budget, best_loss_hr=value) for seed, values in
        ((0, (10., 9., 8.)), (1, (12., 12., 11.)))
        for budget, value in zip((50, 100, 500), values)])
    rows = convergence_summary(data)
    assert len(rows) == 2 and all(r["seeds"] == 2 for r in rows)
    assert rows[0]["mean_within_seed_gain_hr"] == .5
    assert rows[0]["seeds_with_strict_gain"] == 1
    assert rows[1]["mean_within_seed_gain_hr"] == 1.


def test_nonmonotone_best_so_far_rejected():
    data = pd.DataFrame([dict(batch="x", configuration="a", seed=0,
        evaluations=budget, best_loss_hr=value) for budget, value in ((50, 9.), (100, 10.))])
    with pytest.raises(AssertionError):
        convergence_summary(data)
