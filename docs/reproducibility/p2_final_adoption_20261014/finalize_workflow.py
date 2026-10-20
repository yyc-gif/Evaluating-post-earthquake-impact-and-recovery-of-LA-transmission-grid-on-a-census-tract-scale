"""Refresh only current workflow-routing metadata for the adopted P2 version."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[3]
BASE='937fa2b1ab9953d8411a08fbbd0400cf3b52bd8f'


def source(rel):
    return json.loads(subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':'+rel]))


def write(rel,obj):
    (ROOT/rel).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def main():
    ca=source('FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json')
    ca['checked_out_branch']='2026-10-14'
    current=ca['current_code_files']
    for name in ['src/la_grid/revision/current_stage7.py','src/la_grid/plotting/build_current_suite_p2.py',
                 'src/la_grid/plotting/build_current_figures.py',
                 'src/la_grid/plotting/figure_presentation.py',
                 'src/la_grid/plotting/consolidate_current_figure_suite.py',
                 'src/la_grid/plotting/short_current_captions_20261013.py']:
        if not any(r['path']==name for r in current):
            current.append(dict(path=name,sha256='',tracked_in_current_git=True))
    tracked=set(subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z']).decode().split('\0'))
    retired=[r for r in current if r['path'] not in tracked]
    ca['retired_code_available_at']=dict(commit='aecc9adadd04edc4c5f64de64f79ed4c34c1f69c', paths=[r['path'] for r in retired])
    current[:]=[r for r in current if r['path'] in tracked]
    for row in current:
        path=ROOT/row['path']
        if path.is_file():
            row['sha256']=hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    write('FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json',ca)
    matrix=source('FINAL_REVISION_RUN_SEQUENCE/FINAL_REVISION_RUN_MATRIX.json')
    old=matrix['accepted_post_freeze_additions'].pop('final_stage7_sovi_harmonization')
    matrix['accepted_post_freeze_additions']['historical_stage7_sovi_harmonization']=old
    matrix['accepted_post_freeze_additions']['adopted_stage7_P2']=dict(
        authority='results/stage7/2026-10-14',selector='config/current_stage7.json',
        variables=7,primary_K=3,sensitivity_K=4,author_adoption_date='2026-10-14')
    matrix['stage_authorities']['08']='results/stage7/2026-10-14'
    write('FINAL_REVISION_RUN_SEQUENCE/FINAL_REVISION_RUN_MATRIX.json',matrix)
    hashes=json.loads((ROOT/'results/stage7/2026-10-14/ARTIFACT_HASHES.json').read_text())
    write('FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/STAGE8_OUTPUT_HASHES.json',hashes)
    import sys
    sys.path.insert(0,str(ROOT/'src'))
    from la_grid.revision.current_stage7 import verify_current_stage7,verify_current_figures
    prior=source('FINAL_REVISION_RUN_SEQUENCE/FINAL_RUN_MANIFEST.json')
    write('FINAL_REVISION_RUN_SEQUENCE/FINAL_RUN_MANIFEST.json',dict(
        status='PASS_P2_ADOPTION_FROZEN_REUSE_ONLY',stage7_version='2026-10-14',
        scientific_computation_performed=False,full_workflow_revalidated=False,
        stage7_current_verification=verify_current_stage7(ROOT),
        figures_current_verification=verify_current_figures(ROOT),
        prior_full_validation=dict(source_commit=BASE,path='FINAL_REVISION_RUN_SEQUENCE/FINAL_RUN_MANIFEST.json',
                                   status=prior.get('status')),
        limitation='The original manifest-bound physical archives were not rerun or newly clean-room certified.'))
    print('Current workflow code/routing registry updated; frozen experiment design unchanged.')


if __name__=='__main__':main()
