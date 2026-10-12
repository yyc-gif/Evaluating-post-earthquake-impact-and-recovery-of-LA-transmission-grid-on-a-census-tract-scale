"""Phase I: verify frozen pairing and derive metrics; no models are executed."""
from itertools import combinations
import hashlib
import json
import platform

from scipy import sparse
from scipy.stats import spearmanr, pearsonr

from common import *


def prefixes(policy):
    base = FORMAL + ('Equity_Amendment/Offline/' if policy == 'vulnerability-first' else 'Formal_Offline_Evaluation/')
    events = FORMAL + ('Equity_Amendment/T/2pc50/C57_D1/' if policy == 'vulnerability-first' else f'Formal_Trajectories/2pc50/C57_D1/{policy}/')
    return base + f'2pc50__C57_D1__{policy}', events


def main():
    s = sources()
    assert git('merge-base', AUTH, 'HEAD').decode().strip() == AUTH
    dump('STARTING_STATUS_AND_PRESERVATION.json', dict(commit=AUTH,
        branch=git('branch', '--show-current').decode().strip(), worktree_status=git('status', '--porcelain').decode(),
        source_head=git('rev-parse', 'HEAD', cwd=SOURCE_ROOT).decode().strip(),
        unrelated_source_status=git('status', '--porcelain', cwd=SOURCE_ROOT).decode(),
        protected_files=preserve(s), python=platform.python_version()))
    fixed = frozen(s, PREVIOUS + 'TRACT_FEATURES_VERIFIED_2315.csv').sort_index()
    population_source = frozen(s, 'Data/Tracts_Within_Expanded_Area.csv', 'GEOID').population
    fixed = fixed.reindex(population_source.index)
    fixed.index.name = 'tract_id'
    population = population_source.reindex(fixed.index)
    np.testing.assert_array_equal(population.to_numpy(), fixed.Population.to_numpy())
    assert len(fixed) == 2315 and fixed.index.str.fullmatch(r'\d{11}').all()
    positive = fixed.Population.gt(0)
    assert positive.sum() == 2299 and (~positive).sum() == 16
    save('EXCLUDED_ZERO_POPULATION_GEOIDS.csv', fixed.loc[~positive, ['Population']].reset_index())
    retained = FEATURES + ['Population', 'B_unconstrained', 'frozen_SOVI_quartile', 'INTPTLAT', 'INTPTLON',
        'utm_x_m', 'utm_y_m', 'hospital_tract', 'residential_member', 'additional_zero_housing_positive_population']
    save('VERIFIED_FIXED_FEATURES_2315.csv', fixed[retained].reset_index())
    physical = pd.read_csv(s.source(FORMAL + 'Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv', AUTH))
    physical = physical.query("scenario == '2pc50' and split == 'evaluation'").sort_values('realization_id')
    with np.load(s.source(FORMAL + 'Stage 1 Output_expanded/physical_inputs_2pc50.npz', AUTH), allow_pickle=False) as z:
        stations, ds, durations = z['station_ids'].astype(str), z['evaluation_ds'], z['evaluation_duration']
    assert ds.shape == durations.shape == (92, 1000)
    for i, row in enumerate(physical.itertuples()):
        h = hashlib.sha256(('\n'.join(stations) + '\n').encode() + ds[:, i].astype('<i8').tobytes() + durations[:, i].astype('<f8').tobytes()).hexdigest()
        assert h == row.physical_input_hash
        assert row.realization_id == f'2pc50__evaluation_{i:04d}'
    mapping = pd.read_csv(s.source('Data/JULY_UTILITY_CONSTRAINED_92.csv', AUTH), dtype={'tract_id': str, 'substation_id': str})
    # Archived tract integrals follow the original tract-table order, not GEOID sort.
    order = list(population_source.index)
    assert set(order) == set(mapping.tract_id.unique())
    w = sparse.csr_matrix((mapping.weight, (pd.Index(order).get_indexer(mapping.tract_id), pd.Index(stations).get_indexer(mapping.substation_id))), shape=(2315, 92))
    mass = np.asarray(w.sum(1)).ravel()
    np.testing.assert_allclose(mass, 1, atol=1e-12)
    rows, qa, archive_rows, burdens, initial = [], [], [], {}, None
    pair_identities = {}
    initial_authority = np.load(s.source(INTERPRETATION + 'FROZEN_INITIAL_STATION_STATES.npz', AUTH), allow_pickle=False)
    initial_e = initial_authority['e']
    for policy in ['unconstrained', *POLICIES]:
        prefix, events = prefixes(policy)
        meta = json.loads(s.archive(prefix + '__EVALUATION.json').read_text())
        ident = meta['identity']
        assert ident['hazard'] == '2pc50' and ident['resource_case'] == 'C57_D1' and ident['H_eval_hr'] == 480
        assert 'M1_UTILITY_003' in ident['mapping_cases'] and 'G1_BASELINE_050' in ident['gate_cases']
        assert meta['realization_count'] == 1000
        with np.load(s.archive(prefix + '__INTEGRALS.npz', meta['integral_sha256']), allow_pickle=False) as z:
            np.testing.assert_array_equal(z['station_ids'].astype(str), stations)
            np.testing.assert_array_equal(z['physical_hashes'], physical.physical_input_hash.to_numpy())
            b = z['M1_UTILITY_003__normalized_burden_hr'].copy()
            loss = z['G1_BASELINE_050__L_total'].copy()
        assert b.shape == (1000, 2315) and np.isfinite(b).all() and b.min() >= 0 and b.max() <= 480
        projection_error = np.max(np.abs(b - (w @ loss.T).T / mass))
        assert projection_error < 1e-10
        summary = pd.read_parquet(s.archive(prefix + '__SUMMARY.parquet', meta['summary_sha256']))
        selected = summary.query("mapping == 'M1_UTILITY_003' and gate == 'G1_BASELINE_050' and comparison_domain == 'mapping_native_domain'").sort_values('realization_id')
        np.testing.assert_array_equal(selected.realization_id, physical.realization_id)
        summary_error = np.max(np.abs(b @ fixed.Population.to_numpy() / fixed.Population.sum() - selected.population_weighted_normalized_burden_hr))
        assert summary_error < 1e-10 and (selected.horizon_hr == 480).all()
        max_error = 0
        for i, row in enumerate(physical.itertuples()):
            stem = events + row.realization_id
            mp = lp(SOURCE_ROOT / (stem + '.json'))
            record = json.loads(mp.read_text())
            ri = record['identity']
            for key, expected in [('realization_id', row.realization_id), ('physical_sample_hash', row.physical_input_hash), ('DS_hash', row.DS_hash), ('duration_hash', row.duration_hash), ('hazard', '2pc50'), ('resource_scenario', 'C57_D1'), ('event_horizon_hr', 480), ('mapping_method_id', 'M1_UTILITY_003'), ('split', 'evaluation'), ('strategy', policy)]:
                assert ri[key] == expected, (policy, i, key)
            keys = ['physical_sample_hash', 'DS_hash', 'duration_hash', 'graph_hash', 'source_set_hash', 'crew_roster_hash', 'directed_travel_hash', 'matrix_id', 'event_horizon_hr', 'mapping_method_id']
            shared = {key: ri[key] for key in keys}
            if policy == 'unconstrained': pair_identities[row.realization_id] = shared
            else: assert shared == pair_identities[row.realization_id], (policy, i)
            npz = lp(SOURCE_ROOT / (stem + '.npz'))
            assert sha(npz) == record['npz_sha256']
            with np.load(npz, allow_pickle=False) as z:
                t, e = z['event_time_hr'], z['e']
                np.testing.assert_array_equal(z['station_ids'].astype(str), stations)
                np.testing.assert_array_equal(e[0], initial_e[i])
                assert t[0] == 0 and t[-1] == 480 and (np.diff(t) > 0).all()
                assert np.isfinite(e).all() and e.min() >= 0 and e.max() <= 1 + 1e-12
                error = np.max(np.abs(((1 - e[:-1]) * np.diff(t)[:, None]).sum(0) - loss[i]))
                assert error < 1e-10
                max_error = max(max_error, error)
            archive_rows.append(dict(policy=policy, realization_id=row.realization_id, physical_hash=row.physical_input_hash,
                manifest_sha256=sha(mp), npz_sha256=record['npz_sha256'], archive_relative_path=stem + '.npz', integration_error_hr=error))
        burdens[policy] = b
        initial = (w @ initial_e.mean(0)) / mass
        qa.append(dict(policy=policy, realizations=1000, integral_sha256=meta['integral_sha256'], summary_sha256=meta['summary_sha256'],
            projection_max_error_hr=projection_error, exact_event_max_error_hr=max_error, population_summary_max_error_hr=summary_error,
            population_burden_hr=float(selected.population_weighted_normalized_burden_hr.mean()),
            Q4_burden_hr=float(selected.burden_Q4_hr.mean()), hospital_burden_hr=float(selected.hospital_mean_normalized_burden_hr.mean()),
            identity=ident, local_archive_required=True))
        print('paired and verified frozen policy', policy, flush=True)
    np.testing.assert_allclose(initial, fixed.Init_Supply, rtol=0, atol=1e-12)
    prefix, _ = prefixes('direct-community')
    direct_meta = json.loads(s.archive(prefix + '__EVALUATION.json').read_text())
    assert direct_meta['integral_sha256'] == qa[1]['integral_sha256']
    s.archive(prefix + '__INTEGRALS.npz', direct_meta['integral_sha256'])
    uncon = burdens['unconstrained']
    identity_error = 0
    for policy, b in burdens.items():
        delta = (b - uncon).mean(0)
        identity_error = max(identity_error, np.max(np.abs(b.mean(0) - uncon.mean(0) - delta)))
        for i, tract in enumerate(order):
            row = fixed.loc[tract]
            rows.append(dict(tract_id=tract, policy=policy, eligible_positive_population=bool(positive.iloc[i]), Population=row.Population,
                frozen_SOVI_quartile=row.frozen_SOVI_quartile, B_480_hr=b[:, i].mean(), B_unconstrained=uncon[:, i].mean(), Delta_B_logistics=delta[i]))
    metrics = pd.DataFrame(rows)
    baseline = metrics.query("policy == 'impact-first'").set_index('tract_id')
    for variable in ['B_480_hr', 'Delta_B_logistics', 'B_unconstrained']:
        np.testing.assert_allclose(baseline[variable], fixed[variable], rtol=0, atol=1e-10)
    save('POLICY_REFERENCE_TRACT_METRICS.csv', metrics)
    save('FROZEN_POLICY_EVENT_VERIFICATION.csv', archive_rows)
    stat_rows, comparisons, changes = [], [], []
    pos = metrics.loc[metrics.eligible_positive_population]
    for policy, part in pos.groupby('policy', sort=False):
        for v in ['B_480_hr', 'Delta_B_logistics']:
            x = part[v]
            stat_rows.append(dict(policy=policy, variable=v, n=len(x), mean=x.mean(), sd=x.std(ddof=0), minimum=x.min(), p10=x.quantile(.1), p25=x.quantile(.25), median=x.median(), p75=x.quantile(.75), p90=x.quantile(.9), maximum=x.max(), population_weighted_mean=np.average(x, weights=part.Population)))
    for a, b in combinations(POLICIES, 2):
        aa = pos.query('policy == @a').set_index('tract_id')
        bb = pos.query('policy == @b').set_index('tract_id').reindex(aa.index)
        for v in ['B_480_hr', 'Delta_B_logistics']:
            difference = bb[v] - aa[v]
            ranks = bb[v].rank(method='average', pct=True) - aa[v].rank(method='average', pct=True)
            comparisons.append(dict(policy_a=a, policy_b=b, variable=v, pearson=pearsonr(aa[v], bb[v]).statistic,
                spearman=spearmanr(aa[v], bb[v]).statistic, mean_difference_hr=difference.mean(), median_abs_difference_hr=difference.abs().median(),
                p90_abs_difference_hr=difference.abs().quantile(.9), max_abs_difference_hr=difference.abs().max(),
                abs_gt_1hr_tracts=int(difference.abs().gt(1).sum()), abs_gt_1hr_population=aa.loc[difference.abs().gt(1),'Population'].sum(),
                abs_gt_5hr_tracts=int(difference.abs().gt(5).sum()), abs_gt_5hr_population=aa.loc[difference.abs().gt(5),'Population'].sum(),
                p90_abs_rank_percentile_change=ranks.abs().quantile(.9)))
            if a == 'impact-first':
                for tract in aa.index:
                    changes.append(dict(tract_id=tract, alternative_policy=b, variable=v, alternative_minus_impact_hr=difference.loc[tract],
                        rank_percentile_change=ranks.loc[tract], Population=aa.loc[tract,'Population'],
                        INTPTLAT=fixed.loc[tract,'INTPTLAT'], INTPTLON=fixed.loc[tract,'INTPTLON']))
    save('POLICY_REFERENCE_DISTRIBUTIONS.csv', stat_rows)
    save('POLICY_REFERENCE_PAIRWISE_COMPARISONS.csv', comparisons)
    save('IMPACT_FIRST_TRACT_POLICY_DIFFERENCES.csv', changes)
    dump('POLICY_PAIRING_QA.json', dict(status='PASS', policies=qa, identity_max_error_hr=identity_error,
        study_tracts=2315, clustering_tracts=2299, population=fixed.Population.sum(),
        physical_hashes_sha256=hashlib.sha256(('\n'.join(physical.physical_input_hash)+'\n').encode()).hexdigest(),
        direct_community_impact_integral_bytes_identical=True, no_new_physical_simulation=True,
        external_dependency='Manifest-bound Formal_Trajectories and Equity_Amendment archives are not assumed available in a clean Git clone.'))
    save('SOURCE_HASH_VERIFICATION.csv', s.records)
    md('POLICY_REFERENCE_SOURCE_AND_PAIRING_QA.md', '''# Policy reference source and pairing QA
AUTHOR REVIEW - NOT FORMAL STAGE 7

All six scheduled policies plus Unconstrained have complete frozen station event arrays and tract integrals. Each contains the same 1,000 evaluation realization IDs, 92 stations, 2,315 tract IDs in the original tract-table order (not GEOID sort), damage/duration hashes, graph/source/travel/crew identities, M1_UTILITY_003 mapping, C57_D1 resources, and 480 h horizon. Analysis aligns by exact GEOID and then sorts. Vulnerability-first comes from Equity_Amendment/Offline and Equity_Amendment/T, not from the original policy folder. Its executable commit differs, but every physical/configuration identity is matched.

B is the mean integral of normalized service deficit in hours (not divided by 480). Delta is the mean realization-paired constrained-minus-Unconstrained integral, including finite crews, dispatch and travel jointly. Exact step-event integration of archived e agrees with archived G1_BASELINE_050 station integrals, and W projection agrees with archived tract values. Population-weighted checks use all 2,315 study tracts, including the 16 with zero population. Clustering alone excludes those 16. Detailed maximum errors are in POLICY_PAIRING_QA.json.

Direct-community and Impact-first integral files have identical SHA256; they are not independent policies. Initial station/tract availability is unchanged across all policies. No gates, trajectories, damage, schedules or physical realizations were recomputed. The event payloads are local manifest-bound archive dependencies; the derived metric table is included here for clean-clone numerical diagnostics. Reproducing the full archive audit requires those original archives, not fabricated aggregate-to-spatial reconstruction.

Frozen population is unchanged; its upstream Census-vintage provenance remains as bounded by the prior audit. SOVI is frozen FEMA NRI v1.19; quartiles are inherited, never recomputed. 2pc50 is the probabilistic 2%-in-50-year ground-motion field, not a unique earthquake rupture or community risk index.
''')
    md('IMPACT_FIRST_REFERENCE_DECISION.md', '''# Phase I: registered policy-reference decision
AUTHOR REVIEW - NOT FORMAL STAGE 7

Impact-first was the preceding audit's declared population-impact-oriented operational benchmark and was identical to the archived direct-community reference. It was not selected by a completed policy-robust typology study. It remains a legitimate conditional benchmark, not a universal or neutral restoration model. Spectral Grid_Impact is distinct from its population-impact repair-order score.

All six policies pass pairing and are retained for Phase II. No policy is selected from aggregate loss alone. The generated distributions and paired differences quantify how much the operational premise matters; final membership evidence is assessed after these pre-fit checks. Hospital-first asks a critical-service question; structure-first policies ask network-priority questions. Vulnerability-first deliberately targets frozen Q4 and must not be used to claim independent discovery of vulnerability-associated recovery. No synthetic average-policy trajectory is created.
''')
    print('Phase I PASS; no clustering has been fitted.', flush=True)


if __name__ == '__main__': main()
