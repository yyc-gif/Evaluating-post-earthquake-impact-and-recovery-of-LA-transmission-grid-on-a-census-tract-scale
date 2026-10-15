"""Method checks independent of the full physical archive."""
import numpy as np
from analyze import align, grouping, grouped_prediction
from extract_outcomes import first_threshold, overlap_deficit
from common import inputs


def test_exact_step_windows_and_partition():
    t = np.array([0., 10., 30., 480.])
    service = np.array([[0., .5, 1., 1.]])
    assert overlap_deficit(t, service, 0, 24)[0] == 17
    assert overlap_deficit(t, service, 24, 72)[0] == 3
    assert overlap_deficit(t, service, 72, 480)[0] == 0
    assert overlap_deficit(t, service, 0, 480)[0] == 20


def test_unreached_is_nan_not_horizon():
    t = np.array([0., 5., 480.])
    service = np.array([[0., .8, 1.], [0., .3, .7]])
    times = first_threshold(t, service)
    assert times[0] == 5 and np.isnan(times[1])


def test_hungarian_alignment_is_label_invariant():
    ref = np.array([0,0,1,1,2,2])
    pred = np.array([2,2,0,0,1,1])
    np.testing.assert_array_equal(align(ref, pred, 3), ref)


def test_quantile_ties_are_not_artificially_split():
    x = np.array([0., 0., 0., 0., 1.])
    labels, cuts = grouping(x, x, 4)
    assert len(cuts) < 3 and len(set(labels[:4])) == 1


def test_frozen_memberships_and_positive_cohort():
    a, f, refs = inputs()
    assert len(f) == 2299 and f.Population.sum() == 9066522
    assert np.bincount(refs[3]).tolist() == [1235,428,636]
    assert np.bincount(refs[4]).tolist() == [37,1217,429,616]
    assert f.additional_zero_housing_positive_population.sum() == 8


def test_outcome_prediction_uses_training_groups_only():
    labels = np.array([0,0,1,1])
    y = np.array([[2.],[4.],[10.],[14.]])
    np.testing.assert_array_equal(grouped_prediction(labels,np.array([1,0]),y),[[12.],[3.]])


def test_test_outlier_does_not_move_training_cuts():
    train = np.arange(9.)
    _, cuts = grouping(train,np.array([-1e8,1e8]),3)
    np.testing.assert_array_equal(cuts,np.quantile(train,[1/3,2/3]))
