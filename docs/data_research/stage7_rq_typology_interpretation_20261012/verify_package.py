"""Final isolated scope and artifact checks; no scientific calculation."""
import json
import py_compile
from common import *

REQUIRED=['K3_K4_K5_SCIENTIFIC_COMPARISON.md','CLUSTER_ORIGINAL_UNIT_PROFILES.csv',
    'CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv','THIRTYFOUR_TRACT_IDENTITY_AND_STABILITY.csv',
    'THIRTYFOUR_TRACT_STATION_DEPENDENCY.csv','THIRTYFOUR_TRACT_SOURCE_CONNECTIVITY_AUDIT.md',
    'INIT_SUPPLY_SCALING_AND_ABLATION.md','SEVEN_VS_EIGHT_INTERPRETABILITY.md','K_SELECTION_AUTHOR_DECISION.md']


def main():
    for name in REQUIRED:assert lp(OUT/name).is_file()
    for path in OUT.glob('*.py'):py_compile.compile(str(lp(path)),doraise=True)
    qa=json.loads(lp(OUT/'INDEPENDENT_QA_RESULTS.json').read_text());assert qa['status']=='PASS'
    visual=json.loads(lp(OUT/'VISUAL_QA.json').read_text());assert visual['all_eight_pages_visually_inspected']
    rendered=json.loads(lp(OUT/'PDF_RENDER_AND_BOUNDS_QA.json').read_text())
    assert len(rendered)==8 and len(set(row['pdf'] for row in rendered))==6
    for row in rendered:assert sha(OUT/'figures'/row['pdf'])==row['pdf_sha256']
    assert visual['PDF_hashes']=={p.name:sha(p) for p in (OUT/'figures').glob('*.pdf')}
    s=sources();protected=preserve(s);assert len(protected)==950
    before=json.loads(lp(OUT/'STARTING_STATUS_AND_PRESERVATION.json').read_text())
    assert git('status','--porcelain',cwd=SOURCE_ROOT).decode().splitlines()==before['unrelated_source_status']
    changed=git('diff','--name-only',AUTH).decode().splitlines()
    assert all(p.startswith(OUT.relative_to(ROOT).as_posix()+'/') for p in changed)
    manifests={}
    skip={'DERIVED_FILE_HASHES.json','FINAL_PACKAGE_QA.json','REMOTE_DELIVERY_VERIFICATION.json'}
    for path in OUT.rglob('*'):
        rel=path.relative_to(OUT)
        if not path.is_file() or any(p in ['__pycache__','pdf_review'] for p in rel.parts) or path.name in skip:continue
        manifests[rel.as_posix()]=dict(sha256=sha(path),bytes=lp(path).stat().st_size)
    dump('DERIVED_FILE_HASHES.json',manifests)
    dump('FINAL_PACKAGE_QA.json',dict(status='PASS',required_deliverables=len(REQUIRED),
        scientific_baseline_commit=AUTH,diagnostic_branch=git('branch','--show-current').decode().strip(),
        six_PDFs_eight_pages_reviewed=True,all_scripts_compile=True,source_archive_limit_documented=True,
        protected_scientific_files_unchanged=950,only_isolated_package_changes=True,new_model_fits=0,
        new_physical_simulations=0,formal_stage7_promotion=False,manifest_files=len(manifests)))
    print('PASS: package scope, six PDFs, independent QA, compilation and preservation.')


if __name__=='__main__':main()
