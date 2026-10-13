"""Predeclared descriptive policy/threshold/spatial comparisons of frozen tracts."""
from scipy import sparse, stats
from scipy.spatial import cKDTree
from common import *

COMPARATORS = {
    'Five_policy_mean': 'MeanTotal5',
    'Four_policy_no_Vulnerability': 'MeanTotal4_no_Vulnerability',
    'Impact_first': 'B_impact-first',
    'Hospital_first': 'B_hospital-first',
    'Degree_first': 'B_degree-first',
    'Betweenness_first': 'B_betweenness-first',
    'Vulnerability_first': 'B_vulnerability-first',
    'Unconstrained': 'B_unconstrained',
    'MeanDelta_five': 'MeanDelta5',
    'MeanDelta_four': 'MeanDelta4_no_Vulnerability',
}


def safe_ratio(a, b):
    return float(a / b) if b > 0 else np.nan


def effects(data, high):
    q4 = data.frozen_SOVI_quartile.eq('Q4').to_numpy()
    high = np.asarray(high, dtype=bool)
    population = data.Population.to_numpy(float)
    a, b, c, e = [(q4 & high), (q4 & ~high), (~q4 & high), (~q4 & ~high)]
    cells = [a, b, c, e]
    count = np.array([cell.sum() for cell in cells], dtype=float)
    people = np.array([population[cell].sum() for cell in cells])
    values = dict(n=len(data), n_Q4=int(q4.sum()), n_nonQ4=int((~q4).sum()),
                  n_high=int(high.sum()), n_joint=int(a.sum()), population=float(population.sum()),
                  population_joint=float(people[0]), population_Q4=float(population[q4].sum()),
                  population_nonQ4=float(population[~q4].sum()), population_high=float(population[high].sum()))
    for name, weights in [('tract', count), ('resident', people)]:
        p4 = safe_ratio(weights[0], weights[0] + weights[1])
        pn = safe_ratio(weights[2], weights[2] + weights[3])
        expected = safe_ratio((weights[0] + weights[1]) * (weights[0] + weights[2]), weights.sum())
        values.update({name + '_Q4_prevalence': p4, name + '_nonQ4_prevalence': pn,
                       name + '_prevalence_difference_pp': (p4 - pn) * 100,
                       name + '_prevalence_ratio': safe_ratio(p4, pn),
                       name + '_odds_ratio': safe_ratio(weights[0] * weights[3], weights[1] * weights[2]),
                       name + '_expected_joint_under_marginal_independence': expected,
                       name + '_observed_joint': weights[0],
                       name + '_observed_to_expected': safe_ratio(weights[0], expected)})
    return values, [(label, cell) for label, cell in zip(['Q4_high', 'Q4_not_high', 'nonQ4_high', 'nonQ4_not_high'], cells)]


def weighted_quantile(values, weights, q):
    order = np.argsort(values, kind='stable')
    x, w = np.asarray(values)[order], np.asarray(weights)[order]
    return float(x[np.searchsorted(np.cumsum(w), q * w.sum(), side='left')])


def profile(values, population):
    values, population = np.asarray(values, dtype=float), np.asarray(population, dtype=float)
    return dict(n=len(values), population=population.sum(), mean_hr=values.mean(), median_hr=np.median(values),
                P10_hr=np.quantile(values, .1), P90_hr=np.quantile(values, .9), min_hr=values.min(), max_hr=values.max(),
                resident_weighted_mean_hr=np.average(values, weights=population),
                resident_weighted_P10_hr=weighted_quantile(values, population, .1),
                resident_weighted_median_hr=weighted_quantile(values, population, .5),
                resident_weighted_P90_hr=weighted_quantile(values, population, .9))


def jaccard(a, b):
    return safe_ratio(np.logical_and(a, b).sum(), np.logical_or(a, b).sum())


def main():
    d = eligible()
    frozen = frame('FROZEN_POLICY_TRACT_MEANS_2315.csv', 'tract_id').reindex(d.index)
    for field in COMPARATORS.values():
        assert np.isfinite(frozen[field]).all()
        d[field] = frozen[field]
    for k in [3, 4]:
        membership = frame('inputs/K' + str(k) + '_CLUSTER_MEMBERSHIP.csv', 'tract_id').reindex(d.index)
        d['K' + str(k) + '_class'] = membership.candidate_display_cluster.to_numpy(int)
    assert d.K3_class.value_counts().sort_index().to_list() == [1242, 475, 582]
    descriptors = frame('inputs/VERIFIED_DESCRIPTORS_2315.csv', 'tract_id').reindex(d.index)
    d[['utm_x_m', 'utm_y_m', 'INTPTLAT', 'INTPTLON']] = descriptors[['utm_x_m', 'utm_y_m', 'INTPTLAT', 'INTPTLON']]
    assert np.isfinite(d[['utm_x_m', 'utm_y_m']]).all().all()
    base = d.MeanTotal5.to_numpy()
    q4 = d.frozen_SOVI_quartile.eq('Q4').to_numpy()
    base_cut = np.quantile(base, .75, method='linear')
    assert abs(base_cut - FIXED_P75) < 1e-10
    base_high = base >= FIXED_P75
    base_joint = base_high & q4
    old = frame('inputs/ORIGINAL_COOCCURRENCE_TABLE.csv', 'tract_id').reindex(d.index)
    old94 = frame('inputs/ORIGINAL_COOCCURRENCE_TRACTS.csv', 'tract_id')
    assert set(d.index[base_joint]) == set(old94.index) and base_joint.sum() == 94
    assert d.Population.to_numpy()[base_joint].sum() == 350799
    assert q4.sum() == 579 and base_high.sum() == 575
    d['Figure7D_original_high'] = base_high
    d['Figure7D_original_joint'] = base_joint
    save('VERIFIED_ORIGINAL_94_GEOIDS.csv', d.loc[base_joint, ['Population', 'frozen_SOVI_quartile', 'MeanTotal5', 'K3_class', 'K4_class']].reset_index())
    save('VERIFIED_COOCCURRENCE_TRACT_VALUES.csv', d.reset_index())
    effects_rows, cells_rows, thresholds, rounding, transitions, continuous, membership_rows = [], [], [], [], [], [], []
    base_rank = stats.rankdata(base, method='average')
    for name, field in COMPARATORS.items():
        values = d[field].to_numpy()
        kind = 'additional_constraint_deficit' if name.startswith('MeanDelta') else 'total_service_deficit'
        rank = stats.rankdata(values, method='average')
        continuous.append(dict(comparator=name, metric_kind=kind, Pearson_SOVI=stats.pearsonr(d.SOVI_SCORE, values).statistic,
                               Spearman_SOVI=stats.spearmanr(d.SOVI_SCORE, values).statistic,
                               Pearson_vs_five=stats.pearsonr(base, values).statistic,
                               Spearman_vs_five=stats.spearmanr(base, values).statistic,
                               absolute_rank_change_median=np.median(np.abs(rank - base_rank)),
                               absolute_rank_change_P90=np.quantile(np.abs(rank - base_rank), .9)))
        for percentile in [.70, .75, .80]:
            for protocol in ['F', 'R']:
                cutoff = (FIXED_P75 if percentile == .75 else np.quantile(base, percentile)) if protocol == 'F' else np.quantile(values, percentile)
                high = values >= cutoff
                eff, cells = effects(d, high)
                common = dict(comparator=name, field=field, metric_kind=kind, protocol=protocol,
                              percentile=int(100 * percentile), cutoff_hr=cutoff, inclusivity='>=', quantile_method='linear',
                              total_cutoff_applied_to_increment=(kind == 'additional_constraint_deficit' and protocol == 'F'))
                eff.update(common)
                eff.update(dict(high_Jaccard_vs_original=jaccard(high, base_high),
                                joint_Jaccard_vs_original=jaccard(high & q4, base_joint),
                                entering_joint=int((high & q4 & ~base_joint).sum()),
                                exiting_joint=int((base_joint & ~(high & q4)).sum()),
                                direction_Q4='lower' if eff['tract_prevalence_difference_pp'] < 0 else 'higher' if eff['tract_prevalence_difference_pp'] > 0 else 'equal',
                                near_cutoff_0p25hr_n=int((np.abs(values - cutoff) <= .25).sum()),
                                near_cutoff_1hr_n=int((np.abs(values - cutoff) <= 1).sum())))
                effects_rows.append(eff)
                if percentile == .75:
                    for i, tid in enumerate(d.index):
                        membership_rows.append(dict(tract_id=tid, comparator=name, protocol=protocol, cutoff_hr=cutoff,
                            burden_hr=values[i], Population=d.Population.iloc[i], frozen_Q4=bool(q4[i]), selected_high=bool(high[i]),
                            selected_joint=bool(high[i] and q4[i]), rank_change_vs_five=rank[i]-base_rank[i],
                            burden_change_vs_five_hr=values[i]-base[i], original_high=bool(base_high[i]), original_joint=bool(base_joint[i]),
                            INTPTLAT=d.INTPTLAT.iloc[i], INTPTLON=d.INTPTLON.iloc[i]))
                    thresholds.append({**common, **{k: eff[k] for k in ['n_high', 'n_joint', 'population_joint', 'tract_prevalence_ratio', 'tract_prevalence_difference_pp', 'high_Jaccard_vs_original', 'joint_Jaccard_vs_original']}})
                    for label, mask in cells:
                        cells_rows.append(dict(**common, cell=label, n_tracts=int(mask.sum()), frozen_population=float(d.Population.to_numpy()[mask].sum())))
                    if name == 'Four_policy_no_Vulnerability':
                        for i, tid in enumerate(d.index):
                            changed = high[i] != base_high[i]
                            transitions.append(dict(tract_id=tid, protocol=protocol, cutoff_hr=cutoff, Population=d.Population.iloc[i],
                                                    frozen_Q4=bool(q4[i]), five_B_hr=base[i], four_B_hr=values[i],
                                                    four_minus_five_B_hr=values[i] - base[i], original_high=bool(base_high[i]), comparator_high=bool(high[i]),
                                                    original_joint=bool(base_joint[i]), comparator_joint=bool(q4[i] and high[i]), changed_high=bool(changed),
                                                    rank_change=rank[i] - base_rank[i],
                                                    original_distance_to_cutoff_hr=base[i] - FIXED_P75,
                                                    within_1hr_of_original_boundary=bool(abs(base[i] - FIXED_P75) <= 1),
                                                    K3_class=int(d.K3_class.iloc[i]), INTPTLAT=d.INTPTLAT.iloc[i], INTPTLON=d.INTPTLON.iloc[i]))
        for method in ['linear', 'lower', 'higher', 'midpoint', 'nearest']:
            cutoff = np.quantile(values, .75, method=method)
            for operator in ['>=', '>']:
                selected = values >= cutoff if operator == '>=' else values > cutoff
                rounding.append(dict(comparator=name, quantile_method=method, operator=operator, cutoff_hr=cutoff,
                                     exact_ties_n=int((values == cutoff).sum()), n_high=int(selected.sum()), n_joint=int((selected & q4).sum()),
                                     population_joint=float(d.Population.to_numpy()[selected & q4].sum())))
        for digits in [3, 6, 12]:
            rounded = np.round(values, digits) >= round(float(np.quantile(values, .75)), digits)
            rounding.append(dict(comparator=name, quantile_method='linear_rounded_' + str(digits), operator='>=',
                                 cutoff_hr=round(float(np.quantile(values, .75)), digits), n_high=int(rounded.sum()),
                                 n_joint=int((rounded & q4).sum()), population_joint=float(d.Population.to_numpy()[rounded & q4].sum())))
    effects_frame = pd.DataFrame(effects_rows)
    save('Q4_HIGH_DEFICIT_CONTINGENCY_TABLES.csv', cells_rows)
    save('Q4_VS_NONQ4_EFFECT_SIZES.csv', effects_frame.loc[effects_frame.percentile.eq(75)])
    save('FIXED_VS_RECOMPUTED_P75_THRESHOLDS.csv', thresholds)
    save('THRESHOLD_P70_P75_P80_SENSITIVITY.csv', effects_frame)
    save('INDIVIDUAL_POLICY_COOCCURRENCE.csv', effects_frame.loc[effects_frame.percentile.eq(75) & effects_frame.comparator.str.endswith('_first')])
    save('FIVE_VS_FOUR_POLICY_COMPARISON.csv', transitions)
    save('PERCENTILE_TIE_AND_ROUNDING_QA.csv', rounding)
    save('POLICY_SELECTION_MEMBERSHIP_BY_TRACT.csv', membership_rows)
    save('CONTINUOUS_SOVI_AND_POLICY_ASSOCIATIONS.csv', continuous)
    quartile_rows, differences = [], []
    for name, field in COMPARATORS.items():
        summaries = {}
        for quartile in ['Q1', 'Q2', 'Q3', 'Q4']:
            group = d.loc[d.frozen_SOVI_quartile.eq(quartile)]
            row = profile(group[field], group.Population)
            summaries[quartile] = row
            row.update(comparator=name, quartile=quartile, full_cohort_R_P75_cutoff_hr=np.quantile(d[field], .75),
                       n_above_full_cohort_R_P75=int(group[field].ge(np.quantile(d[field], .75)).sum()))
            quartile_rows.append(row)
        differences.append(dict(comparator=name, Q4_minus_Q1_mean_hr=summaries['Q4']['mean_hr'] - summaries['Q1']['mean_hr'],
                                Q4_minus_Q1_median_hr=summaries['Q4']['median_hr'] - summaries['Q1']['median_hr'],
                                Q4_minus_Q1_resident_weighted_mean_hr=summaries['Q4']['resident_weighted_mean_hr'] - summaries['Q1']['resident_weighted_mean_hr']))
    save('VULNERABILITY_QUARTILE_BURDEN_PROFILES.csv', quartile_rows)
    save('Q4_Q1_BURDEN_DECOMPOSITION.csv', differences)
    context = []
    for quartile in ['Q1', 'Q2', 'Q3', 'Q4']:
        group = d.loc[d.frozen_SOVI_quartile.eq(quartile)]
        for field in ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'Population', 'FEMA_NCV14_CA_v119']:
            context.append(dict(quartile=quartile, field=field, n=len(group), mean=group[field].mean(),
                                median=group[field].median(), P10=group[field].quantile(.1), P90=group[field].quantile(.9)))
    save('QUARTILE_NETWORK_AND_POPULATION_CONTEXT.csv', context)
    spatial_rows, standardized_rows, moran_rows = [], [], []
    coords = d[['utm_x_m', 'utm_y_m']].to_numpy()
    for size in [5000, 10000]:
        cells = np.floor(coords / size).astype(int)
        d['block_' + str(size)] = [f'{x}_{y}' for x, y in cells]
    x, y = coords[:, 0], coords[:, 1]
    bx = np.clip(np.floor(3 * (x - x.min()) / (x.max() - x.min())).astype(int), 0, 2)
    by = np.clip(np.floor(4 * (y - y.min()) / (y.max() - y.min())).astype(int), 0, 3)
    d['broad_region'] = [f'X{xx + 1}_Y{yy + 1}' for xx, yy in zip(bx, by)]
    spatial_comparators = ['Five_policy_mean', 'Four_policy_no_Vulnerability', 'Impact_first', 'Vulnerability_first', 'Unconstrained', 'MeanDelta_five']
    for grouping in ['K3_class', 'K4_class', 'block_5000', 'block_10000', 'broad_region']:
        for name in spatial_comparators:
            field = COMPARATORS[name]
            full_cutoff = np.quantile(d[field], .75)
            for label, group in d.groupby(grouping, sort=True):
                high = group[field].ge(full_cutoff)
                eff, _ = effects(group, high)
                spatial_rows.append(dict(comparator=name, grouping=grouping, group=str(label), test='within_group_full_comparator_R_cutoff', cutoff_hr=full_cutoff, **eff))
                if grouping.startswith('block_') or grouping == 'broad_region':
                    remain = d.loc[d[grouping].ne(label)]
                    if len(remain) == 0:
                        continue
                    for protocol in ['F_original_numeric', 'R_full_comparator_cutoff', 'R_recomputed_remaining']:
                        cut = FIXED_P75 if protocol == 'F_original_numeric' else full_cutoff if protocol == 'R_full_comparator_cutoff' else np.quantile(remain[field], .75)
                        out, _ = effects(remain, remain[field].ge(cut))
                        spatial_rows.append(dict(comparator=name, grouping=grouping, group=str(label), test='leave_group_out_' + protocol,
                                                 excluded_n=len(group), excluded_population=group.Population.sum(), cutoff_hr=cut, **out))
            if grouping.startswith('block_'):
                usable = []
                for label, group in d.groupby(grouping):
                    q = group.frozen_SOVI_quartile.eq('Q4')
                    if q.sum() >= 5 and (~q).sum() >= 5:
                        eff, _ = effects(group, group[field].ge(full_cutoff))
                        usable.append(dict(label=label, **eff))
                for weighting in ['tract', 'resident']:
                    count_field = 'n' if weighting == 'tract' else 'population'
                    weights = np.array([r[count_field] for r in usable], dtype=float)
                    p4 = np.average([r[weighting + '_Q4_prevalence'] for r in usable], weights=weights)
                    pn = np.average([r[weighting + '_nonQ4_prevalence'] for r in usable], weights=weights)
                    standardized_rows.append(dict(comparator=name, grouping=grouping, weighting=weighting,
                                                  common_support_blocks=len(usable), common_support_tracts=sum(r['n'] for r in usable),
                                                  common_support_population=sum(r['population'] for r in usable),
                                                  min_group_tract_count=5, standardized_Q4_prevalence=p4, standardized_nonQ4_prevalence=pn,
                                                  standardized_difference_pp=100 * (p4 - pn), standardized_prevalence_ratio=safe_ratio(p4, pn)))
    neighbors = cKDTree(coords).query(coords, k=9)[1][:, 1:]
    row = np.repeat(np.arange(len(d)), 8)
    adjacency = sparse.csr_matrix((np.ones(len(row)), (row, neighbors.ravel())), shape=(len(d), len(d)))
    adjacency = adjacency.maximum(adjacency.T)
    weights = sparse.diags(1 / np.asarray(adjacency.sum(1)).ravel()) @ adjacency
    for name, values in [('SOVI_SCORE', d.SOVI_SCORE), ('Frozen_Q4', q4.astype(float)), ('High_five_P75', base_high.astype(float)),
                         *[(name, d[COMPARATORS[name]]) for name in spatial_comparators]]:
        z = np.asarray(values, dtype=float) - np.mean(values)
        moran = len(d) / weights.sum() * float(z @ (weights @ z)) / float(z @ z)
        moran_rows.append(dict(measure=name, Moran_I=moran, n=len(d), graph='symmetrized_8NN_TIGER_internal_points_UTM',
                               row_standardized=True, p_value_not_calculated=True, inference='descriptive_only'))
    save('SPATIAL_AND_K3_STRATIFIED_CHECKS.csv', spatial_rows)
    save('SPATIAL_COMMON_SUPPORT_STANDARDIZATION.csv', standardized_rows)
    save('SPATIAL_DEPENDENCE_DIAGNOSTICS.csv', moran_rows)
    save('SPATIAL_BLOCK_ASSIGNMENTS.csv', d[['utm_x_m', 'utm_y_m', 'block_5000', 'block_10000', 'broad_region', 'K3_class', 'K4_class']].reset_index())
    dump('SPATIAL_DESIGN_AND_INFERENCE_LIMITS.json', dict(internal_points='Frozen TIGER 2020 INTPT projected UTM coordinates; no geometry exclusions.',
         block_sizes_m=[5000, 10000], origin='Fixed national UTM grid origin (0,0), floor(x/size),floor(y/size)',
         broad_regions='3 east-west by 4 south-north equal-width bins of cohort point extent; fixed before outcome summaries',
         graph='8 nearest distinct tract internal points, symmetrized and row-standardized',
         joint_standardization='Same all-tract/resident block weights for Q4 and non-Q4, only blocks with >=5 tracts of each; descriptive, not a causal adjustment.',
         no_IID_pvalues=True, no_spatial_significance_claim=True,
         no_permutation_reason='Fixed deterministic modeled census domain, strong nonexchangeable network/mapping and policy dependence. No validated spatial null or independent replicated regions.',
         temporary_leaveout_only=True, main_cohort_unchanged=True))
    dump('ORIGINAL_94_REPRODUCTION_QA.json', dict(status='PASS', original_94_exact_GEOIDs=True, population_joint=350799,
         Q4=579, high=575, joint=94, fixed_cutoff_hr=FIXED_P75, independently_recalculated_cutoff_hr=base_cut,
         cutoff_difference_hr=base_cut - FIXED_P75, original_policy_mean_identity_error_hr=np.max(np.abs(base - (d.B_Unconstrained + d.MeanDelta))),
         threshold_quantile_method='NumPy linear (Hyndman-Fan type 7)', operator='>=', reference_population=9066522,
         flags_not_recomputed=True, no_new_Kmeans=True))
    print(effects_frame.loc[effects_frame.percentile.eq(75) & effects_frame.protocol.eq('R'), ['comparator', 'cutoff_hr', 'n_high', 'n_joint', 'population_joint', 'tract_prevalence_difference_pp', 'tract_prevalence_ratio']].to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
