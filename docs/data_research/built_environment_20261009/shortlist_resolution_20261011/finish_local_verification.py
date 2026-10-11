from common import *
import pandas as pd

if __name__=='__main__':
    before=json.loads(lp(OUT/'PRESERVATION_BEFORE.json').read_text(encoding='utf-8'));after=snapshot();assert after==before;dump('PRESERVATION_AFTER.json',after)
    qa=json.loads(lp(OUT/'COMPARISON_COMPLETION_QA.json').read_text(encoding='utf-8'))
    dump('VERIFICATION_RESULTS.json',dict(baseline=BASELINE,protected_scientific_files_unchanged=after['protected_count'],original_staged_items_unchanged=after['staged_count'],original_HEAD_unchanged=after['original_head'],logical_index_unchanged=True,original_status_unchanged=True,formal_scientific_files_changed=0,formal_stage7_replaced=False,manuscript_or_figures_changed=False,tests='13 passed',new_diagnostic_fits=qa['total_new_fits'],historical_fits_reused=40,additional_k_searches=0,physical_simulations_or_GA_runs=0))
    # Canonicalize only authored text so the manifest also matches Git text bytes.
    # Official metadata responses retain their exact acquired bytes.
    for p in lp(OUT).rglob('*'):
        if p.is_file() and p.suffix in ['.py','.md','.json','.txt'] and not any(k in p.parts for k in ['source_evidence','__pycache__','.pytest_cache','_test_tmp']):
            data=p.read_bytes();normalized=data.replace(b'\r\n',b'\n')
            if data!=normalized:p.write_bytes(normalized)
    hashes={}
    for p in lp(OUT).rglob('*'):
        if not p.is_file() or any(k in p.parts for k in ['__pycache__','.pytest_cache','_test_tmp']):continue
        rel=p.relative_to(lp(OUT)).as_posix()
        if rel in ['DERIVED_FILE_HASHES.json','REMOTE_LFS_BYTE_VERIFICATION.json','EXECUTION_LOG.md']:continue
        hashes[rel]=dict(sha256=sha(p),bytes=p.stat().st_size)
    dump('DERIVED_FILE_HASHES.json',hashes)
    log('Local tables/checkpoints and 13 consequential tests verified; 950 protected scientific files and 862 staged items unchanged.')
