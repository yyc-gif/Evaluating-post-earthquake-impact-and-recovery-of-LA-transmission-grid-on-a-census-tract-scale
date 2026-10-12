"""Freeze cohort, scientific protection and the conditional analysis gate."""
from common import *


def main():
    assert git('rev-parse','HEAD').decode().strip()==AUTH
    s=sources();full,d=dataset(s)
    start=json.loads(lp(s.source(MP+'STARTING_STATUS_AND_PRESERVATION.json',AUTH)).read_text())
    protected={p:sha(SOURCE_ROOT/p) for p in start['protected_files']}
    assert protected==start['protected_files']
    prior=git('ls-tree','-r','--name-only',AUTH,'--','docs/data_research').decode().splitlines()
    dump('STARTING_STATE_AND_PROTECTION.json',dict(starting_commit=AUTH,branch=git('branch','--show-current').decode().strip(),
        new_worktree_status=git('status','--porcelain').decode(),protected_files=protected,
        source_status=git('status','--porcelain',cwd=SOURCE_ROOT).decode(),
        source_staged_diff_sha256=hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest(),
        prior_package_git_blob_manifest={p:hashlib.sha256(git('show',AUTH+':'+p)).hexdigest() for p in prior}))
    save('FROZEN_P2_AND_COHORT.csv',full.reset_index())
    save('EXCLUDED_ZERO_POPULATION_GEOIDS.csv',full.loc[full.Population.eq(0),['Population']].reset_index())
    save('SCIENTIFIC_INPUT_HASHES.csv',s.records)
    dump('CONDITIONAL_ANALYSIS_REGISTRATION.json',dict(starting_commit=AUTH,cohort_rule='Frozen population > 0; no imputation or geometry exclusions',
        physical_simulation='Forbidden',admission_before_clustering=True,
        minimum_physical_coverage=['earthquake','wildfire','flood','historical_or_current_reference_heat'],
        admission='Every component needs documented meaning, interpretable common support, full cohort values and missingness separated from zero; no forced composite',
        possible_composite='Equal hazard-contribution mean of declared cohort percentile ranks, only if a coherent relative background-screening construct passes the gate; not loss or joint probability',
        conditional_RQ3_budgets={'equal_coordinates':[1/9,1/9,1/9], 'preserve_social_split_context':[1/6,1/12,1/12]},
        budget_order=['SOVI_SCORE','log1p_Population','admissible_physical_screening_score'],
        fitting_if_admitted=dict(K=list(range(2,9)),K1_inertia=True,seeds=list(range(42,47)),n_init=50,init='k-means++',algorithm='lloyd',max_iter=500,tol=1e-4),
        prohibition='No hazard definition or weights may be chosen by cluster quality; if admission fails, no new fits'))
    print('Source protection and cohort registration complete',flush=True)


if __name__=='__main__':main()
