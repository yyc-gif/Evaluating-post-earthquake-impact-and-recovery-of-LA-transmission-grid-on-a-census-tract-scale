"""Final package, scope, provenance and artifact gates."""
import py_compile
import fitz
from common import *

REQUIRED=['MULTIPOLICY_FEATURE_DEFINITIONS.md','POLICY_ENSEMBLE_SOURCE_AND_PAIRING_QA.md','MULTIPOLICY_RQ2_TRACT_VALUES.csv',
    'POLICY_VARIABILITY_INFORMATION_AUDIT.csv','VULNERABILITY_FIRST_CIRCULARITY_AUDIT.md',
    'LEAVE_ONE_POLICY_OUT_FEATURE_SENSITIVITY.csv','FEATURE_SPECIFICATIONS_AND_WEIGHTS.json',
    'A_VS_P2_VS_P3_CLUSTERING_RESULTS.csv','ELBOW_AND_SILHOUETTE_COMPARISON.csv',
    'POLICY_SET_CLUSTER_STABILITY.csv','CLUSTER_ORIGINAL_UNIT_PROFILES.csv','INIT_SUPPLY_MULTIPOLICY_SENSITIVITY.md',
    'MULTIPOLICY_METHODS_AND_REVIEWER_RATIONALE.md','FINAL_P2_P3_AUTHOR_DECISION.md']


def main():
    for name in REQUIRED: assert lp(OUT/name).is_file() and lp(OUT/name).stat().st_size>0
    for p in lp(OUT).glob('*.py'): py_compile.compile(str(p),doraise=True)
    for name in ['INDEPENDENT_QA_RESULTS.json','CLEAN_CLONE_CORE_ARITHMETIC_QA.json','REGISTERED_FIT_COMPLETION.json']:
        assert json.loads(lp(OUT/name).read_text())['status']=='PASS'
    render=json.loads(lp(OUT/'PDF_RENDER_QA.json').read_text())
    visual=json.loads(lp(OUT/'VISUAL_REVIEW_QA.json').read_text())
    assert visual['status']=='PASS' and len(render['pages'])==len(visual['pages'])==10
    for record in render['pages']:
        assert sha(OUT/record['pdf'])==record['pdf_sha256']
        assert any(v['pdf']==record['pdf'] and v['page']==record['page'] and v['pdf_sha256']==record['pdf_sha256'] for v in visual['pages'])
    pdfs=list(lp(OUT).glob('*.pdf'));assert len(pdfs)==7
    for p in pdfs:
        with fitz.open(p) as doc:
            for page in doc:
                assert 'AUTHOR REVIEW' in page.get_text() and 'NOT FORMAL STAGE 7' in page.get_text()
    start=json.loads(lp(OUT/'STARTING_STATUS_AND_PRESERVATION.json').read_text());s=sources()
    assert {p:sha(SOURCE_ROOT/p) for p in start['protected_files']}==start['protected_files']
    assert {p:sha(s.source(p,AUTH)) for p in start['prior_package_files']}==start['prior_package_files']
    assert git('status','--porcelain',cwd=SOURCE_ROOT).decode()==start['unrelated_source_status']
    prefix=OUT.relative_to(ROOT).as_posix()
    changes=set(git('diff','--name-only',AUTH).decode().splitlines()) | set(git('ls-files','--others','--exclude-standard').decode().splitlines())
    assert all(p.startswith(prefix+'/') for p in changes),changes
    git('diff','--check')
    exclusions={'DERIVED_FILE_HASHES.json','FINAL_PACKAGE_QA.json','REMOTE_DELIVERY_VERIFICATION.json'}
    manifest={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in lp(OUT).iterdir() if p.is_file() and p.name not in exclusions}
    for name in manifest:
        result=subprocess.run(['git','check-ignore','-q',prefix+'/'+name],cwd=ROOT)
        assert result.returncode==1,('Deliverable ignored by Git',name)
    dump('DERIVED_FILE_HASHES.json',manifest)
    dump('FINAL_PACKAGE_QA.json',dict(status='PASS',required_outputs=len(REQUIRED),vector_PDFs=7,publication_pages_visually_reviewed=10,
        syntax_checks=True,git_diff_check=True,all_changes_confined_to_new_package=True,
        protected_scientific_files_unchanged=len(start['protected_files']),prior_package_files_unchanged=len(start['prior_package_files']),
        all_source_and_derived_hashes_recorded=True,no_formal_promotion=True,no_physical_simulation=True))
    print('Final package QA PASS',flush=True)


if __name__=='__main__':main()
