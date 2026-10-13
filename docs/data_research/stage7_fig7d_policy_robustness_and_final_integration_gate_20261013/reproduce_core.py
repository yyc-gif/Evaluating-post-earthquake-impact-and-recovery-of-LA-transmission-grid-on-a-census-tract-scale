"""Clean-clone core arithmetic from compact inputs, with a short Windows entrypoint."""
import math
from scipy import sparse
from common import *


def main():
    d = eligible()
    z = np.load(lp(OUT / 'inputs/FROZEN_STATION_INTEGRALS_AND_MAPPING.npz'))
    ids = pd.Index(z['tract_ids'].astype(str))
    w = sparse.csr_matrix((z['mapping_data'], z['mapping_indices'], z['mapping_indptr']), shape=tuple(z['mapping_shape']))
    mass = np.asarray(w.sum(1)).ravel()
    order = ids.get_indexer(d.index)
    policies = z['policies'].astype(str).tolist()
    loss = z['station_loss']
    means = {}
    for p in ['unconstrained', *PRIMARY]:
        array = loss[policies.index(p)]
        # Reduce samples with compensated summation, then project. This order
        # differs from the source reconstruction's per-realization projection.
        station_mean = np.array([math.fsum(array[:, i]) / 1000 for i in range(92)])
        means[p] = (w @ station_mean / mass)[order]
    direct_five = np.array([math.fsum(means[p][i] for p in PRIMARY) / 5 for i in range(len(d))])
    frozen = frame('FROZEN_POLICY_TRACT_MEANS_2315.csv', 'tract_id').reindex(d.index)
    assert np.max(np.abs(direct_five - frozen.MeanTotal5.to_numpy())) < 1e-10
    high = direct_five >= FIXED_P75
    q4 = d.frozen_SOVI_quartile.eq('Q4').to_numpy()
    joint = high & q4
    assert high.sum() == 575 and joint.sum() == 94
    assert math.fsum(d.Population.to_numpy()[joint]) == 350799
    assert set(d.index[joint]) == set(frame('VERIFIED_ORIGINAL_94_GEOIDS.csv', 'tract_id').index)
    print('CLEAN_CLONE_CORE_PASS:2299/575/94/350799;maximum error', np.max(np.abs(direct_five - frozen.MeanTotal5.to_numpy())), flush=True)


if __name__ == '__main__':
    main()
