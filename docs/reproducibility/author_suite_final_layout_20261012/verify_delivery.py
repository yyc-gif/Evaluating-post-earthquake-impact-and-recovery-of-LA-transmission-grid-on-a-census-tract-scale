"""Verify actual remote LFS data and the single current GitHub directory."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,re,runpy,subprocess
import requests

ROOT=Path(__file__).resolve().parents[3]
QA=Path(__file__).parent
BASE='37e71b3e15b0f4e1be3a651344e3f9e6475dc24b'
BRANCH='review/official-figure-suite-final-s05-20261012'
REPO='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'
verify=runpy.run_path(str(QA.parent/'official_figure_suite_review_20261012/verify_delivery.py'))['verify']


def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])


if __name__=='__main__':
    commit=git('rev-parse','HEAD').decode().strip()
    remote=git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
    assert commit==remote
    integration=json.loads((QA/'INTEGRATION_QA.json').read_text(encoding='utf-8'))
    active=integration['active_figures'];numbered=['results/figure_review/'+s+'.'+e for s in active for e in ['pdf','png']]
    directories=[]
    for folder in ['Main','Supplement']:
        response=requests.get(f'https://api.github.com/repos/{REPO}/contents/results/figure_review/{folder}',params={'ref':commit},timeout=(20,60))
        response.raise_for_status();files={e['name'] for e in response.json() if e['type']=='file' and e['name'].endswith(('.pdf','.png'))}
        required={Path(s).name+'.'+ext for s in active if s.startswith(folder+'/') for ext in ['pdf','png']}
        assert files==required,(folder,files^required)
        if folder=='Supplement':assert not any(s.startswith(('FigS02.','FigS12.','FigS13.')) for s in files)
        directories.append({'directory':folder,'exact_current_files':len(files),'all_present_no_placeholder':True})
    changed=git('diff','--name-only','--diff-filter=ACMRT',BASE,commit).decode().splitlines()
    all_changes=git('diff','--name-only',BASE,commit).decode().splitlines()
    allowed=('results/figure_review/','results/figures/','docs/reproducibility/author_suite_final_layout_20261012/',
             'src/la_grid/plotting/finish_author_figure_suite_20261012.py','tests/test_current_figure_suite_integration.py')
    assert all(p.startswith(allowed) for p in all_changes)
    scope=set(numbered+changed+[r['mirror_file'] for r in integration['figures']])
    objects={}
    for rel in sorted(scope):
        blob=git('show',commit+':'+rel);m=re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)',blob)
        if m:
            oid,size=m[1].decode(),int(m[2]);obj=objects.setdefault(oid,{'bytes':size,'paths':[]})
            assert obj['bytes']==size;obj['paths'].append(rel)
    rows=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs=[pool.submit(verify,(oid,r['bytes'],r['paths']),commit) for oid,r in objects.items()]
        for done in as_completed(jobs):
            rows.append(done.result())
            if len(rows)%10==0:print(f'{len(rows)}/{len(objects)} remote LFS payloads verified',flush=True)
    report={'branch':BRANCH,'verified_payload_commit':commit,'remote_HEAD_at_verification':remote,
            'numbered_files':len(numbered),'github_directories':directories,'unique_LFS_payloads':len(rows),
            'actual_bytes_downloaded':sum(r['bytes'] for r in rows),'all_actual_remote_bytes_verified':True,
            'scope_is_figure_only':True,'files':sorted(rows,key=lambda r:r['paths'][0])}
    (QA/'REMOTE_DELIVERY_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'}),flush=True)
