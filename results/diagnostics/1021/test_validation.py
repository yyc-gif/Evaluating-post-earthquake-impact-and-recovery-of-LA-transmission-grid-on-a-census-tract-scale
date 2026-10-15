"""Small independent method checks; these are not substantive tract experiments."""
import numpy as np
from sklearn.metrics import adjusted_rand_score
from validate import best_jaccard, gap_select, pair_strength, rng


def test_prediction_strength_pair_count_not_ari():
    a = np.array([0, 0, 0, 0, 1, 1, 1])
    b = np.array([0, 0, 1, 1, 1, 1, 1])
    strength, rows = pair_strength(a, b)
    assert rows[0]["agreeing_pairs"] == 2 and rows[0]["all_pairs"] == 6
    assert strength == 1/3 and rows[1]["strength"] == 1
    assert strength != adjusted_rand_score(a, b)


def test_prediction_singleton_is_undefined():
    score, rows = pair_strength(np.array([0, 0, 1]), np.array([0, 0, 1]))
    assert np.isnan(score) and rows[1]["all_pairs"] == 0


def test_prediction_label_invariance():
    a = np.array([0, 0, 1, 1])
    b = np.array([9, 9, 8, 8])
    assert pair_strength(a, b)[0] == 1


def test_gap_uses_smallest_one_se_and_includes_k1():
    assert gap_select(np.array([1, 1.04, 1.4]), np.array([.01, .1, .02])) == 1
    assert gap_select(np.array([1, 2, 3]), np.array([.01]*3)) is None


def test_bootstrap_jaccard_is_max_per_cluster():
    rows = best_jaccard(np.array([0, 0, 1, 1]), np.array([4, 4, 4, 5]))
    assert rows[0]["jaccard"] == 2/3
    assert rows[1]["jaccard"] == .5
    assert rows[1]["matched_cluster"] == 5


def test_pairwise_squared_distance_equals_wcss():
    x = np.array([[0., 1.], [2., 3.], [4., 5.]])
    pair_sum = sum(np.sum((a-b)**2) for a in x for b in x)
    assert pair_sum/(2*len(x)) == np.sum((x-x.mean(0))**2)


def test_random_streams_reproducible_and_independent():
    assert np.array_equal(rng(10, 3).random(9), rng(10, 3).random(9))
    assert not np.array_equal(rng(10, 3).random(9), rng(11, 3).random(9))


def test_pca_rotation_preserves_distances():
    x = np.array([[0., 1.], [3., 5.], [-2., 4.], [0., 0.]])
    u = np.linalg.svd(x-x.mean(0), full_matrices=False)[2].T
    z = (x-x.mean(0)) @ u
    np.testing.assert_allclose(np.sum((x[0]-x[1])**2), np.sum((z[0]-z[1])**2))
