"""Verify frozen sources and cohort membership before exploratory fitting.

Usage: python prepare.py --source-root PATH --cache-root PATH [--cache-root PATH]
No scientific model module is imported or executed.
"""
import argparse
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import wkt

from common import COMMIT, NRI_AUDIT, OUT, PRIOR, ROOT, SPEC, cohorts, distribution, dump, git, lp, save, sha, snapshot, source_verifier


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--cache-root', action='append', default=[])
    args = parser.parse_args()
    sources = source_verifier(args.source_root, args.cache_root)
    source_status = git('status', '--porcelain=v1', cwd=args.source_root).decode()
    dump('STARTING_GIT_AND_ENVIRONMENT.json', dict(
        starting_commit=git('rev-parse', 'HEAD').decode().strip(),
        diagnostic_branch=git('branch', '--show-current').decode().strip(),
        diagnostic_status=git('status', '--porcelain=v1').decode().splitlines(),
        source_worktree_head=git('rev-parse', 'HEAD', cwd=args.source_root).decode().strip(),
        unrelated_source_status=source_status.splitlines(), python=sys.version, platform=platform.platform(),
        source_root=args.source_root, cache_roots=args.cache_root,
        preregistration_sha256=sha(OUT / 'FEATURE_SPECIFICATIONS_AND_WEIGHTS.json')))
    dump('PRESERVATION_BEFORE.json', snapshot(args.source_root, sources))
    previous_paths = git('ls-tree', '-r', '--name-only', COMMIT, '--', PRIOR).decode().splitlines()
    dump('PRIOR_AUDIT_IMMUTABILITY_BEFORE.json', {p: sha(sources.source(p, COMMIT)) for p in previous_paths})
    d = sources.frame(PRIOR + 'TRACT_CANDIDATE_VALUES_2315.csv', commit=COMMIT).sort_index()
    population = sources.frame('Data/Tracts_Within_Expanded_Area.csv', key='GEOID', commit=COMMIT)
    formal = sources.frame('provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv', commit=COMMIT)
    assert len(d) == len(population) == len(formal) == 2315 and set(d.index) == set(population.index) == set(formal.index)
    assert np.array_equal(d.Population, population.population.reindex(d.index))
    assert np.array_equal(d.Population, formal.population.reindex(d.index))
    assert np.array_equal(d.Population, d.formal_population) and d.Population.ge(0).all()
    nri_fields = ['TRACTFIPS', 'BUILDVALUE', 'SOVI_SCORE', 'POPULATION', 'NRI_VER', 'AREA',
                  'EAL_SCORE', 'EAL_VALT', 'EAL_VALB', 'ALR_NPCTL', 'ALR_VALB']
    nri = sources.frame('Data/NRI_Table_CensusTracts_California.csv', key='TRACTFIPS', columns=nri_fields, commit=COMMIT)
    assert set(d.index).issubset(nri.index) and nri.NRI_VER.eq('Mar-23').all()
    n = nri.reindex(d.index)
    sovi_error = float(np.max(abs(d.SOVI_SCORE - n.SOVI_SCORE)))
    assert sovi_error < 1e-8  # Preserve frozen scores, including their decimal representation.
    for c in ['BUILDVALUE', 'EAL_SCORE', 'EAL_VALT', 'EAL_VALB', 'ALR_NPCTL', 'ALR_VALB', 'AREA']:
        d[c] = n[c]
    d['NRI_POPULATION'] = n.POPULATION
    d['log1p_BUILDVALUE'] = np.log1p(d.BUILDVALUE)
    assert np.isfinite(d[['BUILDVALUE', 'log1p_BUILDVALUE']]).all().all() and d.BUILDVALUE.ge(0).all()
    assert np.allclose(d.log1p_Population, np.log1p(d.Population), rtol=0, atol=1e-14)
    # Official TIGER internal points require no housing ratio or polygon-area admission.
    for c in ['INTPTLAT', 'INTPTLON']:
        d[c] = pd.to_numeric(population[c].reindex(d.index), errors='raise')
    assert np.isfinite(d[['INTPTLAT', 'INTPTLON']]).all().all()
    assert d.INTPTLAT.between(32, 36).all() and d.INTPTLON.between(-120, -116).all()
    xy = Transformer.from_crs(4326, 32611, always_xy=True).transform(d.INTPTLON, d.INTPTLAT)
    d['utm_x_m'], d['utm_y_m'] = xy
    geometry = population.wkt_geom.reindex(d.index).map(wkt.loads)
    d['source_polygon_valid'] = geometry.map(lambda g: g.is_valid and not g.is_empty)
    d['positive_population_member'] = d.Population.gt(0)
    d['additional_zero_housing_positive_population'] = d.Population.gt(0) & d.housing_total.eq(0)
    cdc = sources.frame('Data/California.csv', key='FIPS', columns=['FIPS', 'E_TOTPOP', 'E_GROUPQ', 'EP_GROUPQ'], commit=COMMIT)
    for c in ['E_TOTPOP', 'E_GROUPQ', 'EP_GROUPQ']:
        d['CDC2022_' + c] = cdc[c].reindex(d.index).replace(-999, np.nan)
    assert d.residential_member.eq(d.Population.gt(0) & d.housing_total.gt(0)).all()
    features = list(SPEC['specifications']['B'])
    assert np.isfinite(d[features]).all().all(), 'No missing-feature imputation is permitted'
    assert not d.T80_unreached.any()
    assert np.allclose(d.B_480_hr, d.B_unconstrained+d.Delta_B_logistics, atol=1e-12)
    # Recheck original paired integrals; reuse trajectories, never reapply a gate.
    prior_pairing = json.loads(sources.source(PRIOR + 'RECOVERY_PAIRING_QA.json', COMMIT).read_text())
    saved_hashes = pd.read_csv(sources.source(PRIOR + 'SOURCE_HASH_VERIFICATION.csv', COMMIT))
    arrays, identities = {}, {}
    for policy in ['impact-first', 'unconstrained']:
        rel = 'Formal_Experiment_20260923/Formal_Offline_Evaluation/2pc50__C57_D1__' + policy
        meta_path = rel + '__EVALUATION.json'
        expected = saved_hashes.set_index('source_file').loc[meta_path, 'sha256']
        meta = json.loads(sources.archive(meta_path, expected).read_text())
        identities[policy] = meta['identity']
        assert meta['identity'] == prior_pairing['identities'][policy]
        assert meta['identity']['H_eval_hr'] == SPEC['authority']['horizon_hr']
        assert meta['identity']['resource_case'] == SPEC['authority']['resources']
        assert meta['identity']['hazard'] == SPEC['authority']['hazard']
        with np.load(sources.archive(rel+'__INTEGRALS.npz', meta['integral_sha256']), allow_pickle=False) as z:
            arrays[policy] = {k: z[k].copy() for k in ['physical_hashes', 'M1_UTILITY_003__normalized_burden_hr']}
    for key in ['physical_hashes_sha256', 'matrix_sha256', 'mapping_cases', 'gate_cases', 'resource_case', 'H_eval_hr', 'hazard']:
        assert identities['impact-first'][key] == identities['unconstrained'][key]
    assert np.array_equal(arrays['impact-first']['physical_hashes'], arrays['unconstrained']['physical_hashes'])
    assert len(arrays['impact-first']['physical_hashes']) == 1000
    manifest = pd.read_csv(sources.source('Formal_Experiment_20260923/Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv', COMMIT))
    manifest = manifest[(manifest.scenario=='2pc50') & (manifest.split=='evaluation')].sort_values('realization_id')
    assert np.array_equal(arrays['impact-first']['physical_hashes'], manifest.physical_input_hash.to_numpy())
    mapping = pd.read_csv(sources.source('Data/JULY_UTILITY_CONSTRAINED_92.csv', COMMIT), dtype={'tract_id': str, 'substation_id': str})
    tract_order = population.index.tolist()  # Frozen integral column order is the source table order.
    assert set(tract_order) == set(mapping.tract_id.unique()) == set(d.index)
    b = arrays['impact-first']['M1_UTILITY_003__normalized_burden_hr']
    u = arrays['unconstrained']['M1_UTILITY_003__normalized_burden_hr']
    assert b.shape == u.shape == (1000, 2315)
    expected_b = d.B_480_hr.reindex(tract_order).to_numpy()
    expected_delta = d.Delta_B_logistics.reindex(tract_order).to_numpy()
    assert np.allclose(b.mean(0), expected_b, rtol=0, atol=1e-10)
    assert np.allclose((b-u).mean(0), expected_delta, rtol=0, atol=1e-10)
    dump('FROZEN_RECOVERY_SOURCE_RECHECK.json', dict(identities=identities, paired_1000_ids_equal=True,
        frozen_integral_tract_order=tract_order,
        B_max_error=np.max(abs(b.mean(0)-expected_b)), Delta_max_error=np.max(abs((b-u).mean(0)-expected_delta)),
        all_original_reference_checks=sources.source(PRIOR+'INDEPENDENT_VERIFICATION.json', COMMIT).as_posix(),
        ordered_physical_manifest_ids_verified=True,
        reapplication_of_source_gate=False, any_physical_simulation=False))
    for name in ['PROPOSED_FEATURE_AND_WEIGHT_DECISION.md', 'RQ3_ROUTE_A_SOCIAL_AND_POPULATION_AUDIT.md',
                 'RQ2_2PC50_HAZARD_AND_POLICY_PROVENANCE.md', 'HAZARD_SOURCE_QA.json', 'GRID_DEFINITION_QA.json']:
        sources.source(PRIOR + name, COMMIT)
    for rel in [NRI_AUDIT+'NRI_EAL_DECISION.md', NRI_AUDIT+'FEMA_FIELD_DEFINITIONS_AND_COMPOSITION.md',
                NRI_AUDIT+'sources/FEMA_V119_PAGE_TEXT.json', NRI_AUDIT+'sources/FEMA_V119_TECHNICAL_DOCUMENTATION.pdf',
                'docs/methodology/STAGE7_SVI_HARMONIZATION_DECISION.md']:
        sources.source(rel, COMMIT)
    pages = json.loads(sources.source(NRI_AUDIT+'sources/FEMA_V119_PAGE_TEXT.json', COMMIT).read_text())
    excerpts = {k: v for k, v in pages.items() if 'Hazus 6.0' in v and ('2022' in v or 'building' in v.lower())}
    assert excerpts
    dump('BUILDVALUE_V119_SOURCE_PASSAGES.json', {'source': NRI_AUDIT+'sources/FEMA_V119_PAGE_TEXT.json', 'pages': excerpts,
        'web_access_attempt': '2026-10-11 official Ohio-retained FEMA PDF web fetch rejected for 23MB size; exact archived page text used'})
    save('TRACT_FEATURES_VERIFIED_2315.csv', d.reset_index())
    ledger = d[['Population', 'housing_total', 'positive_population_member', 'residential_member',
                'historical_CORE3_member', 'additional_zero_housing_positive_population', 'source_polygon_valid']].copy()
    ledger['exclusion_reason_primary'] = np.where(d.Population.eq(0), 'zero frozen formal population', 'included')
    ledger['missing_primary_features'] = d[features].isna().sum(axis=1)
    save('TRACT_COHORT_AND_EXCLUSIONS.csv', ledger.reset_index())
    save('ADDITIONAL_POSITIVE_POPULATION_TRACTS.csv', d[d.additional_zero_housing_positive_population].reset_index())
    dist = []
    for cohort, sub in cohorts(d).items():
        for c in [*features, 'Population', 'BUILDVALUE', 'Pop_Density', 'T80', 'EAL_SCORE', 'EAL_VALT', 'ALR_NPCTL']:
            dist.append(dict(cohort=cohort, variable=c, **distribution(sub[c])))
        dist.append(dict(cohort=cohort, variable='Init_Supply_NONZERO_ONLY', **distribution(sub.loc[sub.Init_Supply.gt(0), 'Init_Supply'])))
    save('FEATURE_ORIGINAL_UNIT_DISTRIBUTIONS.csv', dist)
    save('SOURCE_HASH_VERIFICATION.csv', sources.records)
    dump('COHORT_SOURCE_QA.json', dict(full_domain=len(d), positive_population=int(d.Population.gt(0).sum()),
        zero_population=int(d.Population.eq(0).sum()), residential=int(d.residential_member.sum()),
        additional_positive_population_tracts=int(d.additional_zero_housing_positive_population.sum()),
        additional_population=int(d.loc[d.additional_zero_housing_positive_population,'Population'].sum()),
        excluded_zero_population_GEOIDs=d.index[d.Population.eq(0)].tolist(),
        extra_GEOIDs=d.index[d.additional_zero_housing_positive_population].tolist(),
        all_feature_values_complete=True, NRI_source_rows=len(nri), NRI_version='Mar-23',
        BUILDVALUE_units='2022 USD; total building exposure stock, Hazus 6.0',
        SOVI_frozen_vs_full_NRI_max_decimal_error=sovi_error,
        upstream_formal_population_release_resolved=False, official_internal_points_complete=True,
        source_polygon_invalid_count=int((~d.source_polygon_valid).sum()),
        no_old_geometry_exclusions_applied=True, frozen_quartiles_unchanged=True))
    print(json.dumps({'prepared': True, 'cohorts': {k: len(v) for k,v in cohorts(d).items()}, 'protected': 950}), flush=True)


if __name__ == '__main__':
    main()
