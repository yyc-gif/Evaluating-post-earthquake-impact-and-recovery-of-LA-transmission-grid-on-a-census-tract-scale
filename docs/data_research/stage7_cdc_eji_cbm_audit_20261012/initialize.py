"""Record preservation and conditional fit protocol before source analysis."""
from common import *


def main():
    assert git('rev-parse', 'HEAD').decode().strip() == AUTH
    assert not git('status', '--porcelain', '--untracked-files=no').decode().strip()
    s = sources()
    full, d = dataset(s)
    old = json.loads(lp(s.source(MH + 'STARTING_STATE_AND_PROTECTION.json', AUTH)).read_text())
    protected = {p: sha(SOURCE_ROOT / p) for p in old['protected_files']}
    assert protected == old['protected_files'] and len(protected) == 950
    prior = git('ls-tree', '-r', '--name-only', AUTH, '--', 'docs/data_research').decode().splitlines()
    dump('STARTING_STATE_AND_PROTECTION.json', dict(starting_commit=AUTH,
         branch=git('branch', '--show-current').decode().strip(), status=git('status', '--porcelain').decode(),
         protected_files=protected, source_status=git('status', '--porcelain', cwd=SOURCE_ROOT).decode(),
         source_staged_diff_sha256=hashlib.sha256(git('diff', '--cached', '--binary', cwd=SOURCE_ROOT)).hexdigest(),
         prior_git_blobs={p: hashlib.sha256(git('show', AUTH + ':' + p)).hexdigest() for p in prior}))
    save('FROZEN_P2_AND_COHORT.csv', full.reset_index())
    save('EXCLUDED_ZERO_POPULATION_GEOIDS.csv', full.loc[full.Population.eq(0), ['Population']].reset_index())
    save('SCIENTIFIC_INPUT_HASHES_INITIAL.csv', s.records)
    dump('CONDITIONAL_ANALYSIS_REGISTRATION.json', dict(
         cohort='2299 frozen positive-population tracts; no missing-to-zero or additional exclusions',
         candidate='Official CDC EJI 2024 RPL_CBM; never RPL_EJI_CBM',
         admission='Documented standalone construct, full matched valid ranks, interpretable component provenance and flags; unresolved quality blocks fitting',
         diagnostics='Published rank unchanged; any leave-out/local rank is researcher diagnostic, not CDC official',
         nonlinear=dict(model='ExtraTrees', trees=150, min_samples_leaf=20, seed=42, random_folds=5, spatial_block_m=15000, tuning=False),
         fitting_if_admitted=dict(K=list(range(2, 9)), K1_inertia=True, seeds=list(range(42, 47)), n_init=50,
                                  init='k-means++', algorithm='lloyd', max_iter=500, tol=1e-4),
         squared_distance_budgets=dict(P2=[1/9,1/9,1/9,1/6,1/6,1/6,1/6],
                                       H1=[1/9,1/9,1/9,1/6,1/6,1/9,1/9,1/9],
                                       H2=[1/9,1/9,1/9,1/6,1/6,1/6,1/12,1/12]),
         prohibition='No physical, MC, recovery, scheduling or formal Stage 7 changes'))
    print('Registered conditional protocol and verified 950 protected files', flush=True)


if __name__ == '__main__':
    main()
