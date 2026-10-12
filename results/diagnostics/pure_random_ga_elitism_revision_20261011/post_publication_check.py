"""Read-only final checks, explicitly recording a late external path exception."""
import hashlib
from pathlib import Path
import study as s


def main():
    before=s.a.read(s.OUT/'PRESERVATION_BASELINE.json')
    revision=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
    current=s.a.snapshot(revision)
    for name,value in current.items():assert value==before[name],name
    assert len(current['files_sha256'])==950
    staged=len([x for x in s.a.git('diff','--cached','--name-only','-z',cwd=revision).split(b'\0') if x])
    assert staged==before['staged_count']==862
    checks={
        'index_sha256':hashlib.sha256(s.a.git('ls-files','--stage','-z',cwd=revision)).hexdigest(),
        'revision_status_sha256':hashlib.sha256(s.a.git('status','--porcelain=v1','-z',cwd=revision)).hexdigest(),
    }
    for name,value in checks.items():assert value==before[name],name
    for name,expected in before['source_checkout_state'].items():
        folder=Path(name)
        actual=dict(head=s.a.git('rev-parse','HEAD',cwd=folder).decode().strip(),
            index=hashlib.sha256(s.a.git('ls-files','--stage','-z',cwd=folder)).hexdigest(),
            status=hashlib.sha256(s.a.git('status','--porcelain=v1','-z',cwd=folder)).hexdigest())
        assert actual==expected,name
    missing=[]
    for name,digest in before['protected_external_sha256'].items():
        if not s.a.lp(name).exists():missing.append(dict(path=name,baseline_sha256=digest))
        else:assert s.a.sha(name)==digest,name
    manuscript=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_manuscript_rebuild\LA_Grid_Manuscript_Resubmission_Rebuild.docx')
    assert len(missing)==1 and missing[0]['path']==str(manuscript)
    backup=Path(r'C:\2025-2026 Fall\Local_Recovery_Snapshot_20260925\Private_Backup_Small\private-la-grid-research\manuscripts\LA_Grid_Manuscript_Resubmission_Rebuild.docx')
    assert s.a.sha(backup)==missing[0]['baseline_sha256']
    for field,args in (
        ('parameter_evidence_head',('rev-parse','HEAD')),
        ('parameter_evidence_index',('ls-files','--stage','-z')),
        ('parameter_evidence_status',('status','--porcelain=v1','-z'))):
        data=s.a.git(*args,cwd=s.PRIOR)
        value=data.decode().strip() if field.endswith('head') else hashlib.sha256(data).hexdigest()
        assert value==before[field],field
    prior_manifest=s.PRIOR/'results/diagnostics/pure_random_ga_parameter_consistency_20261011/OUTPUT_HASH_MANIFEST.json'
    assert s.a.sha(prior_manifest)==before['parameter_evidence_hash_manifest']
    old=s.a.read(prior_manifest)
    for name,row in old['files'].items():assert s.a.sha(prior_manifest.parent/name)==row['sha256'],name
    manifest=s.a.read(s.OUT/'OUTPUT_HASH_MANIFEST.json')
    for name,row in manifest['files'].items():assert s.a.sha(s.OUT/name)==row['sha256'],name
    s.save('FINAL_POST_PUBLICATION_CHECK.json',dict(
        status='PASS_SCIENTIFIC_STATE_WITH_EXTERNAL_MANUSCRIPT_PATH_EXCEPTION',
        scientific_hashes_verified=950,original_staged_items=staged,
        original_branch_head_index_status_unchanged=True,previous_source_checkout_states_unchanged=True,
        earlier_strict_full_preservation_qa='PASS before the late external manuscript path disappearance',
        current_strict_full_preservation_cannot_pass=True,external_missing_paths=missing,
        exact_baseline_manuscript_backup=dict(path=str(backup),sha256=s.a.sha(backup)),
        backup_not_declared_current_authority=True,manuscript_restored_or_modified=False,
        disappearance_cause='Unconfirmed; no task action targeted this external directory',
        cleanup_scope_receipt='REDUNDANT_RUNTIME_CLEANUP_QA.json',
        manifest_files_verified=len(manifest['files']),prior_package_payloads_verified=len(old['files']),
        actual_remote_lfs_receipt='REMOTE_PUBLICATION_VERIFIED.json',
        new_physical_samples=0,formal_strategy_modified=False))
    print('FINAL_SCIENTIFIC_STATE_PASS_EXTERNAL_PATH_EXCEPTION',staged,flush=True)


if __name__=='__main__':main()
