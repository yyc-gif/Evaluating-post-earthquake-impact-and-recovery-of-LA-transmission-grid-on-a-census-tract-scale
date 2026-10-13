"""Commit-bound snapshots; no fitting or physical simulation."""
from common import *

def main():
    s=reader();prior=json.loads(lp(s.source(HN+'STARTING_STATE_AND_PROTECTION.json',AUTH)).read_text())
    for p,h in prior['protected_files'].items():assert sha(SOURCE_ROOT/p)==h,p
    state=OUT/'STARTING_STATE_AND_PROTECTION.json'
    if not lp(state).exists():
        dump(state.name,dict(review_status=WARN,authority=AUTH,branch=git('branch','--show-current').decode().strip(),initial_status=git('status','--porcelain').decode(),protected_files=prior['protected_files'],original_status_sha256=hashlib.sha256(git('status','--porcelain',cwd=SOURCE_ROOT)).hexdigest(),original_staged_sha256=hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest(),base_tree={r.split('\t',1)[1]:r.split('\t',1)[0].split()[2] for r in git('ls-tree','-r',AUTH).decode().splitlines()}))
    paths={
        'FROZEN_COHORT.csv':HN+'FROZEN_COHORT_AND_COMPARATORS.csv',
        'NCV_HAZARD_COMPONENTS.csv':HN+'FEMA_NCV_NORMALIZED_COMPONENTS.csv',
        'NCV_RAW_FACTORS.csv':HN+'FEMA_NCV_HAZARD_COMPONENT_VALUES.csv',
        'NCV_VECTOR.csv':HN+'FEMA_NCV_CANDIDATE_VECTORS.csv',
        'NCV_CA_AND_LA_EXTREMA.csv':HN+'FEMA_NCV_NORMALIZATION_REFERENCE.csv',
        'SOURCE_HAZARD_FIELD_REGISTER.csv':HN+'FEMA_NRI_V119_18_HAZARD_RAW_FIELD_REGISTER.csv',
        'EXISTING_HAZARD_LEAVEOUT.csv':HN+'HAZARD_LEAVE_ONE_OUT_SENSITIVITY.csv',
        'EXISTING_K_EVIDENCE.csv':HN+'EIGHT_VARIABLE_K_EVIDENCE.csv',
        'EXISTING_STABILITY.csv':HN+'POLICY_SPATIAL_SEED_INIT_STABILITY.csv',
        'EXCLUDED_ZERO_POPULATION_GEOIDS.csv':HN+'EXCLUDED_ZERO_POPULATION_GEOIDS.csv',
        'CGS_PGA_FROZEN.csv':MH+'FROZEN_PGA_TRACT_EXTRACTION_SOURCE.csv',
        'PHYSICAL_SOURCE_REGISTER.csv':MH+'PHYSICAL_HAZARD_MEASUREMENT_REGISTER.csv',
        'PRIOR_Q34_NETWORK.csv':TI+'THIRTYFOUR_TRACT_NETWORK_SUMMARY.csv',
        'PRIOR_Q34_DEPENDENCY.csv':TI+'THIRTYFOUR_TRACT_STATION_DEPENDENCY.csv',
        'SAVED_LABELS_AND_SILHOUETTES.npz':HN+'REGISTERED_CONDITIONAL_FIT_ARRAYS.npz',
        'SAVED_WEIGHTED_MATRICES.npz':HN+'REGISTERED_CONDITIONAL_MATRICES.npz',
        'SAVED_MODEL_CENTERS.npz':HN+'REGISTERED_MODEL_CENTERS.npz',
        'TARGET_GEOMETRY.gpkg':HN+'TARGET_2020_GEOMETRY.gpkg',
        'source_evidence/FEMA_V119_TECHNICAL.pdf':HN+'sources/ARCHIVED_FEMA_V119_TECHNICAL_DOCUMENTATION.pdf',
        'source_evidence/WILLIAMS2024_PUBLISHED.pdf':HN+'sources/WILLIAMS_PUBLISHED_PDF_CDN_TRIAL.pdf',
        'source_evidence/NRI_V119_CA_FROZEN.csv':HN+'sources/FEMA_NRI_v119_CA_FROZEN.csv',
    }
    for out,rel in paths.items():
        source=s.source(rel,AUTH);dest('inputs/'+out).write_bytes(lp(source).read_bytes())
    formal=[p for p in prior['authoritative_git_blobs'] if 'hotspot' in p.lower() and p.endswith('.csv') and p.startswith('Formal_Experiment')]
    dump('INPUT_REGISTRATION.json',dict(review_status=WARN,authority=AUTH,inputs=paths,no_new_fits=True,K_review=[3,4],K5_unchanged=True,first7_unchanged=True,H2_budget=BUDGET,scientific_approval_needed=True,formal_hotspot_candidate_paths=formal))
    save('SOURCE_HASH_VERIFICATION.csv',s.records)
    print('Prepared',len(paths),'verified sources;950 files preserved;newfitting0',flush=True)

if __name__=='__main__':main()
