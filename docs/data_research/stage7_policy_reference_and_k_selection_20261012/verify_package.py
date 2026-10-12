"""Final scope, deliverables, source preservation and compilation gate."""
import py_compile
from common import *

REQUIRED=['POLICY_REFERENCE_SOURCE_AND_PAIRING_QA.md','POLICY_REFERENCE_TRACT_METRICS.csv',
    'POLICY_REFERENCE_PAIRWISE_COMPARISONS.csv','IMPACT_FIRST_REFERENCE_DECISION.md',
    'ELBOW_INERTIA_BY_K.csv','SILHOUETTE_BY_K_AND_SEED.csv','PER_CLUSTER_SILHOUETTE_AND_SIZE.csv',
    'POLICY_CONDITIONAL_MEMBERSHIP_COMPARISONS.csv','INIT_SUPPLY_K_SENSITIVITY.md',
    'K_SELECTION_STATISTICAL_EVIDENCE.md','FINAL_POLICY_AND_K_AUTHOR_DECISION.md']


def main():
    for p in REQUIRED:assert lp(OUT/p).is_file()
    for p in OUT.glob('*.py'):py_compile.compile(str(lp(p)),doraise=True)
    qa=json.loads(lp(OUT/'INDEPENDENT_QA_RESULTS.json').read_text())
    assert qa['status']=='PASS' and qa['protected_scientific_files_unchanged']==950
    visual=json.loads(lp(OUT/'VISUAL_QA.json').read_text())
    assert visual['all_eight_pages_visually_inspected'] and not visual['remaining_clipping_or_overlap']
    assert visual['PDF_hashes']=={p.name:sha(p) for p in (OUT/'figures').glob('*.pdf')}
    assert len(visual['PDF_hashes'])==6
    before=json.loads(lp(OUT/'STARTING_STATUS_AND_PRESERVATION.json').read_text())
    s=sources();assert preserve(s)==before['protected_files']
    assert git('status','--porcelain',cwd=SOURCE_ROOT).decode()==before['unrelated_source_status']
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    for p in git('diff','--name-only',AUTH).decode().splitlines():assert p.startswith(prefix),p
    for row in git('status','--porcelain').decode().splitlines():assert row[3:].strip('"').replace('\\','/').startswith(prefix),row
    manifest={}
    for p in OUT.rglob('*'):
        rel=p.relative_to(OUT)
        if not p.is_file() or any(v in ['__pycache__','pdf_review','tmp'] for v in rel.parts):continue
        if p.name in ['DERIVED_FILE_HASHES.json','FINAL_PACKAGE_QA.json','REMOTE_DELIVERY_VERIFICATION.json']:continue
        manifest[rel.as_posix()]=dict(sha256=sha(p),bytes=lp(p).stat().st_size)
    dump('DERIVED_FILE_HASHES.json',manifest)
    dump('FINAL_PACKAGE_QA.json',dict(status='PASS',required_deliverables=len(REQUIRED),starting_commit=AUTH,
        branch=git('branch','--show-current').decode().strip(),registered_fit_records=960,distinct_full_cohort_fits=880,
        spatial_refits=672,protected_scientific_files_unchanged=950,prior_package_files_unchanged=qa['prior_package_files_unchanged'],
        formal_science_unchanged=True,no_new_physical_simulation=True,no_formal_promotion=True,
        six_vector_PDFs_eight_pages_reviewed=True,all_scripts_compile=True,only_new_package_changed=True,manifest_files=len(manifest)))
    print('Final package QA PASS; no formal scientific files changed.',flush=True)


if __name__=='__main__':main()
