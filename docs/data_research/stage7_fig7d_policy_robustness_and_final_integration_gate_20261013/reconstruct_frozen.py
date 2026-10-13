"""Linear projection of archived integrals, not service or schedule regeneration."""
from scipy import sparse
from common import *


def main():
    sources = Sources()
    prior_qa = json.loads(lp(OUT / 'inputs/POLICY_ENSEMBLE_QA.json').read_text())
    archives = pd.read_csv(sources.source(MP + 'SOURCE_HASH_VERIFICATION.csv'))
    source_hashes = archives.set_index('source_file').sha256.to_dict()
    physical_rel = 'Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_2pc50.npz'
    phy_path = sources.source(physical_rel)
    assert sha(phy_path) == prior_qa['physical_input_npz_sha256']
    phy_manifest_path = sources.source('Formal_Experiment_20260923/Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv')
    phy = pd.read_csv(phy_manifest_path).query("scenario == '2pc50' and split == 'evaluation'").sort_values('realization_id')
    with np.load(phy_path) as arrays:
        station_ids = arrays['station_ids'].astype(str)
        ds, durations = arrays['evaluation_ds'], arrays['evaluation_duration']
    assert ds.shape == durations.shape == (92, 1000)
    for m, row in enumerate(phy.itertuples()):
        raw = ('\n'.join(station_ids) + '\n').encode() + ds[:, m].astype('<i8').tobytes() + durations[:, m].astype('<f8').tobytes()
        assert hashlib.sha256(raw).hexdigest() == row.physical_input_hash
        assert row.realization_id == f'2pc50__evaluation_{m:04d}'
    z = np.load(lp(OUT / 'inputs/FROZEN_STATION_INTEGRALS_AND_MAPPING.npz'))
    np.testing.assert_array_equal(z['station_ids'].astype(str), station_ids)
    np.testing.assert_array_equal(z['realization_ids'], phy.realization_id.to_numpy(str))
    np.testing.assert_array_equal(z['physical_hashes'], phy.physical_input_hash.to_numpy(str))
    ids = pd.Index(z['tract_ids'].astype(str), name='tract_id')
    assert len(ids) == 2315 and ids.is_unique and ids.str.fullmatch(r'\d{11}').all()
    w = sparse.csr_matrix((z['mapping_data'], z['mapping_indices'], z['mapping_indptr']), shape=tuple(z['mapping_shape']))
    mass = np.asarray(w.sum(axis=1)).ravel()
    np.testing.assert_allclose(mass, 1, atol=1e-12, rtol=0)
    mapping_path = sources.source('Data/JULY_UTILITY_CONSTRAINED_92.csv')
    assert sha(mapping_path) == prior_qa['mapping_sha256']
    mapping = pd.read_csv(mapping_path, dtype={'tract_id': str, 'substation_id': str})
    direct_w = sparse.csr_matrix((mapping.weight, (ids.get_indexer(mapping.tract_id), pd.Index(station_ids).get_indexer(mapping.substation_id))), shape=w.shape)
    assert (w != direct_w).nnz == 0
    full = frame('inputs/VERIFIED_DESCRIPTORS_2315.csv', 'tract_id').reindex(ids)
    assert full.Population.sum() == 9066522 and full.Population.gt(0).sum() == 2299
    policies = z['policies'].astype(str).tolist()
    means, deltas, burden = {}, {}, {}
    qa_records = []
    for p in ['unconstrained', *PRIMARY]:
        index = policies.index(p)
        old = next(record for record in prior_qa['policies'] if record['policy'] == p)
        prefix = 'Formal_Experiment_20260923/' + ('Equity_Amendment/Offline/' if p == 'vulnerability-first' else 'Formal_Offline_Evaluation/') + '2pc50__C57_D1__' + p
        meta = json.loads(sources.archive(prefix + '__EVALUATION.json', source_hashes[prefix + '__EVALUATION.json']).read_text())
        assert meta['identity'] == old['identity'] and meta['realization_count'] == 1000
        assert meta['identity']['H_eval_hr'] == 480 and meta['identity']['resource_case'] == 'C57_D1'
        assert 'M1_UTILITY_003' in meta['identity']['mapping_cases'] and 'G1_BASELINE_050' in meta['identity']['gate_cases']
        integral_path = sources.archive(prefix + '__INTEGRALS.npz', old['integral_sha256'])
        with np.load(integral_path) as raw:
            np.testing.assert_array_equal(raw['station_ids'].astype(str), station_ids)
            np.testing.assert_array_equal(raw['physical_hashes'], z['physical_hashes'])
            np.testing.assert_array_equal(raw['G1_BASELINE_050__L_total'], z['station_loss'][index])
            projected = (w @ raw['G1_BASELINE_050__L_total'].T).T / mass
            observed = raw['M1_UTILITY_003__normalized_burden_hr']
            np.testing.assert_allclose(projected, observed, rtol=0, atol=1e-10)
            max_projection_error = float(np.max(np.abs(projected - observed)))
        assert projected.shape == (1000, 2315) and np.isfinite(projected).all()
        assert projected.min() >= 0 and projected.max() <= 480
        summary = pd.read_parquet(sources.archive(prefix + '__SUMMARY.parquet', old['summary_sha256']))
        summary = summary.query("mapping == 'M1_UTILITY_003' and gate == 'G1_BASELINE_050' and comparison_domain == 'mapping_native_domain'").sort_values('realization_id')
        np.testing.assert_array_equal(summary.realization_id, phy.realization_id)
        pop_error = np.max(np.abs(projected @ full.Population.to_numpy() / full.Population.sum() - summary.population_weighted_normalized_burden_hr))
        assert pop_error < 1e-10
        burden[p] = projected
        means[p] = projected.mean(0)
        if p != 'unconstrained':
            deltas[p] = (projected - burden['unconstrained']).mean(0)
            np.testing.assert_allclose(means[p], means['unconstrained'] + deltas[p], atol=1e-10, rtol=0)
        qa_records.append(dict(policy=p, realization_count=1000, integral_sha256=sha(integral_path),
                               max_projection_error_hr=max_projection_error, max_population_summary_error_hr=pop_error,
                               physical_hashes_match=True, frozen_mapping_match=True, gate='G1_BASELINE_050'))
        print('Frozen source arrays verified:', p, flush=True)
    mean_delta5 = np.stack([deltas[p] for p in PRIMARY]).mean(0)
    direct_mean5 = np.stack([means[p] for p in PRIMARY]).mean(0)
    sum_identity = means['unconstrained'] + mean_delta5
    np.testing.assert_allclose(direct_mean5, sum_identity, rtol=0, atol=1e-10)
    paired_direct = np.mean(np.mean(np.stack([burden[p] for p in PRIMARY]), axis=0), axis=0)
    np.testing.assert_allclose(direct_mean5, paired_direct, rtol=0, atol=1e-10)
    table = full[['Population', 'frozen_SOVI_quartile']].copy()
    for p in ['unconstrained', *PRIMARY]:
        table['B_' + p] = means[p]
    table['MeanTotal5'] = sum_identity
    table['MeanTotal4_no_Vulnerability'] = np.stack([means[p] for p in PRIMARY[:-1]]).mean(0)
    table['MeanDelta5'] = mean_delta5
    table['MeanDelta4_no_Vulnerability'] = np.stack([deltas[p] for p in PRIMARY[:-1]]).mean(0)
    save('FROZEN_POLICY_TRACT_MEANS_2315.csv', table.reset_index())
    identity = pd.DataFrame(dict(tract_id=ids, eligible_positive_population=full.Population.to_numpy() > 0,
                                B_Unconstrained=means['unconstrained'], MeanDelta5=mean_delta5,
                                mean_of_five_frozen_policy_B=direct_mean5, B_U_plus_MeanDelta=sum_identity,
                                direct_vs_identity_error_hr=direct_mean5 - sum_identity,
                                realization_order_error_hr=paired_direct - direct_mean5))
    save('FROZEN_FIVE_POLICY_TOTAL_DEFICIT_IDENTITY_QA.csv', identity)
    d = eligible()
    subset = table.reindex(d.index)
    np.testing.assert_allclose(d.B_Unconstrained, subset['B_unconstrained'], atol=1e-10, rtol=0)
    np.testing.assert_allclose(d.MeanDelta, subset.MeanDelta5, atol=1e-10, rtol=0)
    prior = frame('inputs/MULTIPOLICY_RQ2_TRACT_VALUES.csv').query("policy_set == 'main5'").set_index('tract_id').reindex(ids)
    np.testing.assert_allclose(prior.MeanTotalBurden, table.MeanTotal5, atol=1e-10, rtol=0)
    events = frame('inputs/FROZEN_EVENT_VERIFICATION.csv')
    for p in ['unconstrained', *PRIMARY]:
        ep = events.loc[events.policy.eq(p)].sort_values('realization_id')
        np.testing.assert_array_equal(ep.realization_id, phy.realization_id)
        np.testing.assert_array_equal(ep.physical_hash, phy.physical_input_hash)
    save('FROZEN_POLICY_SOURCE_PAIRING_QA.csv', qa_records)
    save('SOURCE_HASH_VERIFICATION_RECONSTRUCTION.csv', sources.records)
    save('PHYSICAL_REALIZATION_IDENTITY.csv', phy)
    dump('FROZEN_SOURCE_IDENTITY_QA.json', dict(status='PASS', source_arrays_reverified=True,
         cohort_count=2299, full_domain_count=2315, population=9066522, policies=PRIMARY,
         physical_realizations=1000, identity_max_error_hr=np.max(np.abs(direct_mean5 - sum_identity)),
         projection_max_error_hr=max(r['max_projection_error_hr'] for r in qa_records),
         all_source_events_previously_verified=True, original_event_files_not_reread_this_round=True,
         clean_clone_reproduction='Core arithmetic uses archived compact station-integral/mapping snapshot; original integral/summary source re-audit needs manifest-bound local archive.',
         no_new_trajectory_or_schedule=True, no_simulation=True))


if __name__ == '__main__':
    main()
