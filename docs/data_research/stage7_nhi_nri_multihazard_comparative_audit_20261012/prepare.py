"""Preserve frozen scientific authority; no simulation, scheduling or formal edits."""
from common import *


def main():
    assert git('rev-parse', 'HEAD').decode().strip() == AUTH or git('merge-base', '--is-ancestor', AUTH, 'HEAD') == b''
    s = reader()
    previous = json.loads(lp(s.source(EH + 'STARTING_STATE_AND_PROTECTION.json', AUTH)).read_text())
    for rel, digest in previous['protected_files'].items():
        assert sha(SOURCE_ROOT / rel) == digest, rel
    assert len(previous['protected_files']) == 950
    state = OUT / 'STARTING_STATE_AND_PROTECTION.json'
    if not lp(state).exists():
        status = git('status', '--porcelain', cwd=SOURCE_ROOT)
        dump(state.name, dict(review_status=WARN, authority=AUTH,
            branch=git('branch', '--show-current').decode().strip(), starting_status=git('status', '--porcelain').decode(),
            protected_files=previous['protected_files'], authoritative_git_blobs=tree(),
            original_status_sha256=hashlib.sha256(status).hexdigest(), original_status_lines=len(status.splitlines()),
            original_staged_diff_sha256=hashlib.sha256(git('diff', '--cached', '--binary', cwd=SOURCE_ROOT)).hexdigest()))
    d = read(s, EH + 'VERIFIED_EIGHT_VARIABLE_COHORT.csv', 'tract_id')
    assert len(d) == 2299 and d.index.is_unique and d.index.str.fullmatch(r'\d{11}').all()
    assert d.Population.gt(0).all() and d.Population.sum() == 9066522
    assert d.additional_zero_housing_positive_population.sum() == 8
    save('FROZEN_COHORT_AND_COMPARATORS.csv', d.reset_index())
    save('EXCLUDED_ZERO_POPULATION_GEOIDS.csv', read(s, EH + 'EXCLUDED_ZERO_POPULATION_GEOIDS.csv'))
    nri = s.source('Data/NRI_Table_CensusTracts_California.csv', AUTH)
    dest('sources/FEMA_NRI_v119_CA_FROZEN.csv').write_bytes(lp(nri).read_bytes())
    for old, new in [('REUSED_MAIN_FIT_ARRAYS.npz', 'FROZEN_COMPARATOR_FIT_ARRAYS.npz'),
                     ('REUSED_WEIGHTED_MATRICES.npz', 'FROZEN_COMPARATOR_WEIGHTED_MATRICES.npz'),
                     ('EIGHT_VARIABLE_K_EVIDENCE.csv', 'FROZEN_COMPARATOR_K_EVIDENCE.csv')]:
        p = s.source(EH + old, AUTH)
        dest(new).write_bytes(lp(p).read_bytes()) if new.endswith('.npz') else save(new, read(s, EH + old))
    candidates = [p for p in tree() if p.startswith(BE + 'sources/') and p.lower().endswith('.pdf')]
    for rel in candidates:
        src = s.source(rel, AUTH)
        dest('sources/ARCHIVED_' + Path(rel).name).write_bytes(lp(src).read_bytes())
    dump('REGISTERED_ANALYSIS.json', dict(review_status=WARN, authority=AUTH, cohort=2299, full_service_domain=2315,
        population=9066522, retained_zero_housing=8, excluded_zero_population=16,
        objective='Earthquake-inclusive natural-hazard coordinate; Columbia NHI versus published FEMA NCV method; CBM comparator only',
        frozen_setup=['2pc50', 'C57_D1', 'M1_UTILITY_003', 'G1_BASELINE_050', '480 hours', '1000 physical evaluations'],
        first_seven=P2, squared_distance_budgets=BUDGET, kmeans=PARAMS, seeds=SEEDS, K=list(range(1, 9)),
        source_gate='No new fitted hazard matrix unless full-cohort source/geography and construct semantics are defensible',
        Columbia_transfer='Official 2010-to-2020 relation plus equal-area geometry. Dominant-area ordinal classification and fractional-area composition, never physical intensity.',
        FEMA_method='Published Williams 2024 hazard set/formula first; tract-scale and normalization adaptations explicitly separate',
        no_imputation=True, no_formal_promotion=True, no_physical_or_restoration_regeneration=True))
    save('SOURCE_HASH_VERIFICATION_PREPARE.csv', s.records)
    print('Frozen cohort 2299; population 9066522; counties', sorted(set(d.index.str[:5])), flush=True)
    print('Archived FEMA PDFs:', candidates, flush=True)


if __name__ == '__main__':
    main()
