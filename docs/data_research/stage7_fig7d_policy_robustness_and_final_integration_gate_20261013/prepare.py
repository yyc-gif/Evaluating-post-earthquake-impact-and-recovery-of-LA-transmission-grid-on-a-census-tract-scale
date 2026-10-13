"""Record preservation and copy exact commit-bound scientific inputs."""
from common import *


def main():
    sources = Sources()
    protection = json.loads(sources.source(PRIOR + 'STARTING_STATE_AND_PROTECTION.json').read_text())
    for rel, digest in protection['protected_files'].items():
        assert sha(SOURCE_ROOT / rel) == digest, rel
    if not lp(OUT / 'STARTING_STATE_AND_PROTECTION.json').exists():
        dump('STARTING_STATE_AND_PROTECTION.json', dict(authority=AUTH,
             branch=git('branch', '--show-current').decode().strip(), initial_status=git('status', '--porcelain').decode(),
             source_head=git('rev-parse', 'HEAD', cwd=SOURCE_ROOT).decode().strip(),
             original_status_sha256=hashlib.sha256(git('status', '--porcelain', cwd=SOURCE_ROOT)).hexdigest(),
             original_staged_sha256=hashlib.sha256(git('diff', '--cached', '--binary', cwd=SOURCE_ROOT)).hexdigest(),
             protected_files=protection['protected_files'],
             base_tree={r.split('\t', 1)[1]: r.split('\t', 1)[0].split()[2] for r in git('ls-tree', '-r', AUTH).decode().splitlines()}))
    copies = {
        'EIGHT_VARIABLE_FROZEN_TABLE.csv': PRIOR + 'candidate/EIGHT_VARIABLE_FROZEN_TABLE.csv',
        'K3_CLUSTER_MEMBERSHIP.csv': PRIOR + 'candidate/K3_CLUSTER_MEMBERSHIP.csv',
        'K4_CLUSTER_MEMBERSHIP.csv': PRIOR + 'candidate/K4_CLUSTER_MEMBERSHIP.csv',
        'CLASS_ID_REGISTRY.csv': PRIOR + 'candidate/CLASS_ID_REGISTRY.csv',
        'FULL_2315_COHORT_STATUS.csv': PRIOR + 'candidate/FULL_2315_COHORT_STATUS.csv',
        'FULL_2315_GEOMETRY.gpkg': PRIOR + 'candidate/FULL_2315_GEOMETRY.gpkg',
        'FROZEN_PREPROCESSING_AND_LABELS.npz': PRIOR + 'candidate/FROZEN_PREPROCESSING_AND_LABELS.npz',
        'FROZEN_CANDIDATE_SPECIFICATION.json': PRIOR + 'candidate/FROZEN_CANDIDATE_SPECIFICATION.json',
        'ORIGINAL_UNIT_PROFILES.csv': PRIOR + 'K3_K4_ORIGINAL_UNIT_PROFILES.csv',
        'QUARTILE_POPULATION_HOSPITAL.csv': PRIOR + 'K3_K4_QUARTILE_POPULATION_HOSPITAL.csv',
        'ORIGINAL_COOCCURRENCE_TABLE.csv': PRIOR + 'candidate/PROPOSED_DESCRIPTIVE_COOCCURRENCE_TABLE.csv',
        'ORIGINAL_COOCCURRENCE_TRACTS.csv': PRIOR + 'candidate/PROPOSED_COOCCURRENCE_TRACTS.csv',
        'ORIGINAL_COOCCURRENCE_DEFINITION.json': PRIOR + 'candidate/PROPOSED_COOCCURRENCE_DEFINITION.json',
        'EXISTING_K_EVIDENCE.csv': PRIOR + 'inputs/EXISTING_K_EVIDENCE.csv',
        'EXISTING_STABILITY.csv': PRIOR + 'inputs/EXISTING_STABILITY.csv',
        'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz': MP + 'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz',
        'POLICY_ENSEMBLE_QA.json': MP + 'POLICY_ENSEMBLE_QA.json',
        'FROZEN_EVENT_VERIFICATION.csv': MP + 'FROZEN_EVENT_VERIFICATION.csv',
        'VERIFIED_DESCRIPTORS_2315.csv': MP + 'VERIFIED_DESCRIPTORS_2315.csv',
        'MULTIPOLICY_RQ2_TRACT_VALUES.csv': MP + 'MULTIPOLICY_RQ2_TRACT_VALUES.csv',
        'POLICY_REFERENCE_TRACT_METRICS.csv': PK + 'POLICY_REFERENCE_TRACT_METRICS.csv',
        'METHODS_PRIOR.md': PRIOR + 'candidate/METHODS_REPLACEMENT_DRAFT.md',
        'RESULTS_PRIOR.md': PRIOR + 'candidate/RESULTS_REPLACEMENT_DRAFT.md',
        'CAPTIONS_PRIOR.md': PRIOR + 'candidate/FIGURE7_AND_S9_CAPTIONS_DRAFT.md',
        'SUPPLEMENTARY_PRIOR.md': PRIOR + 'candidate/SUPPLEMENTARY_NOTES_DRAFT.md',
        'FORMAL_CAPTIONS_BASELINE.md': PRIOR + 'CURRENT_FORMAL_FIGURE7_AND_S9_BASELINE.md',
        'Figure7_previous.pdf': PRIOR + 'figures/Figure7_candidate.pdf',
        'FigureS9_previous.pdf': PRIOR + 'figures/FigureS9_candidate.pdf',
        'Figure7_previous.png': PRIOR + 'figures/Figure7_candidate.png',
        'PRIOR_FIGURE_BUILDER.py': PRIOR + 'figures.py',
    }
    for target, rel in copies.items():
        dest('inputs/' + target).write_bytes(sources.source(rel).read_bytes())
    full = frame('inputs/FULL_2315_COHORT_STATUS.csv', 'tract_id')
    descriptors = frame('inputs/VERIFIED_DESCRIPTORS_2315.csv', 'tract_id')
    assert set(full.index) == set(descriptors.index) and len(full) == 2315
    assert descriptors.Population.gt(0).sum() == 2299 and descriptors.Population.sum() == 9066522
    assert descriptors.loc[descriptors.Population.gt(0), 'additional_zero_housing_positive_population'].sum() == 8
    paths = git('ls-tree', '-r', '--name-only', AUTH).decode().splitlines()
    legacy = [p for p in paths if p.startswith('Formal_Experiment') and p.endswith('.csv') and 'hotspot' in p.lower()]
    dump('INPUT_REGISTRATION.json', dict(authority=AUTH, copies=copies, legacy_hotspot_paths=legacy,
         reference_hazard='2pc50', resource='C57_D1', mapping='M1_UTILITY_003', gate='G1_BASELINE_050',
         horizon_hr=480, realizations=1000, new_fits=0, new_simulations=0))
    save('SOURCE_HASH_VERIFICATION.csv', sources.records)
    print('Prepared', len(copies), 'sources;950 actual protected files verified;no fitting/simulation', flush=True)


if __name__ == '__main__':
    main()
