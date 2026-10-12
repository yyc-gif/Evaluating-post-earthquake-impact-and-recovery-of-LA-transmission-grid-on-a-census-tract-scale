"""Final package completeness, scientific assertions and reproducibility checks."""
import argparse
import compileall
import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import OUT, ROOT, SPEC, dump, frame, git, lp, sha

ANALYSIS_CSVS=[
    'BUILDVALUE_INCREMENTAL_INFORMATION.csv','SAME_COHORT_ASSOCIATION_MATRIX.csv','CONDITIONAL_R2_AND_VIF.csv',
    'BUILDVALUE_EXTREME_AND_TAIL_SENSITIVITY.csv','INIT_SUPPLY_DISTANCE_LEVERAGE.csv',
    'REGISTERED_EXPLORATORY_CLUSTERING.csv','CLUSTER_PROFILE_DISTRIBUTIONS.csv','DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv',
    'CLUSTER_SIZE_POPULATION_AND_EXTREMES.csv','COHORT_STANDARDIZATION_AND_WEIGHTS.csv',
    'CLUSTER_MEMBERSHIPS_POSITIVE_POPULATION.csv','CLUSTER_MEMBERSHIPS_RESIDENTIAL.csv',
    'CLUSTER_MEMBERSHIP_COMPARISONS.csv','CLUSTER_MEMBERSHIP_TRANSITIONS.csv','COHORT_SENSITIVITY.csv',
    'SPATIAL_SUPPORT_AND_BLOCKS.csv','SPATIAL_AND_SEED_STABILITY.csv','STRESS_TEST_MEMBERSHIPS.csv']


def checks():
    for name in ANALYSIS_CSVS:
        assert lp(OUT/name).is_file(),name
    qa=json.loads(lp(OUT/'INDEPENDENT_QA_RESULTS.json').read_text())
    assert qa['status']=='PASS' and qa['protected_scientific_files_unchanged']==950
    spec_hash=sha(OUT/'FEATURE_SPECIFICATIONS_AND_WEIGHTS.json')
    execution=json.loads(lp(OUT/'ANALYSIS_EXECUTION.json').read_text())
    assert spec_hash==execution['preregistration_sha256']
    assert sha(OUT/'TRACT_FEATURES_VERIFIED_2315.csv')==execution['input_sha256']
    registered=frame('REGISTERED_EXPLORATORY_CLUSTERING.csv')
    assert len(registered)==200 and not registered[['cohort','specification','k','seed']].duplicated().any()
    assert set(registered.k)=={3,4,5,6} and set(registered.seed)=={42,43,44,45,46}
    assert registered.n_init.eq(50).all()
    contributions=frame('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv')
    domains=contributions[contributions.kind=='domain']
    assert np.allclose(domains.squared_distance_budget,1/3)
    assert np.allclose(domains.total_SS/domains.groupby(['cohort','specification','k','seed']).total_SS.transform('sum'),1/3)
    assert np.allclose(domains.total_SS,domains.between_SS+domains.within_SS,rtol=0,atol=1e-9)
    stability=frame('SPATIAL_AND_SEED_STABILITY.csv')
    assert stability.kind.eq('seed_pair').sum()==400
    assert stability.kind.eq('asset_P99_leaveout').sum()==40
    assert stability.kind.eq('spatial_leave_quadrant_out').sum()==80
    assert len(frame('STRESS_TEST_MEMBERSHIPS.csv'))==275720
    cohort=frame('TRACT_COHORT_AND_EXCLUSIONS.csv')
    assert len(cohort)==2315 and cohort.tract_id.is_unique
    assert cohort.positive_population_member.sum()==2299 and cohort.residential_member.sum()==2291
    assert cohort.missing_primary_features.eq(0).all()
    assert len(frame('ADDITIONAL_POSITIVE_POPULATION_TRACTS.csv'))==8
    assert not frame('TRACT_FEATURES_VERIFIED_2315.csv').T80_unreached.any()
    pdfqa=json.loads(lp(OUT/'PDF_RENDER_AND_BOUNDARY_QA.json').read_text())
    assert len(pdfqa['figures'])==5 and pdfqa['visual_review_status']=='PASS_ALL_FIVE_PDFS_AT_PUBLICATION_SIZE'
    for f in pdfqa['figures']:
        assert sha(OUT/f['file'])==f['sha256'] and f['text_within_page_bounds']
    assert compileall.compile_dir(str(lp(OUT)),quiet=1)
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    changes=git('diff','--name-only',SPEC['starting_commit'],'HEAD').decode().splitlines()
    assert all(p.startswith(prefix) for p in changes),changes
    dump('FINAL_PACKAGE_QA.json',dict(status='PASS',registered_fits=200,stress_fits=120,
        all_required_tables_present=True,all_tract_IDs_and_weights_verified=True,
        all_five_PDFs_visually_inspected=True,syntax_check=True,formal_promotion=False,
        protected_scientific_files=950,changes_confined_to_package=True))


def manifest():
    result={}
    for p in lp(OUT).rglob('*'):
        rel=p.relative_to(lp(OUT)).as_posix()
        if not p.is_file() or any(v in rel.split('/') for v in ['__pycache__','.pytest_cache','test_tmp']):continue
        if rel in ['DERIVED_FILE_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json']:continue
        result[rel]=dict(sha256=sha(p),bytes=p.stat().st_size)
    dump('DERIVED_FILE_HASHES.json',result)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--capture-replay',action='store_true')
    parser.add_argument('--verify-replay',action='store_true')
    args=parser.parse_args()
    if args.capture_replay:
        dump('NUMERICAL_REPLAY_BASELINE_HASHES.json',{p:sha(OUT/p) for p in ANALYSIS_CSVS})
    elif args.verify_replay:
        expected=json.loads(lp(OUT/'NUMERICAL_REPLAY_BASELINE_HASHES.json').read_text())
        actual={p:sha(OUT/p) for p in ANALYSIS_CSVS}
        assert actual==expected,'Numerical CSV bytes changed on replay'
        dump('NUMERICAL_REPLAY_VERIFICATION.json',dict(status='PASS',files=len(actual),
            all_numerical_CSV_bytes_identical=True,sha256=actual))
    else:
        checks()
        manifest()
    print('Package verification command completed',flush=True)


if __name__=='__main__':main()
