"""Verify current directory listings and actual remote LFS bytes after push."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import re
import runpy
import subprocess
import requests

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).parent
BASE = 'f010a4b42ebb7b160ab78556405bdb5c8e8a3ef6'
BRANCH = 'review/official-figure-suite-final-s05-20261012'
REPO = 'yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'
verify = runpy.run_path(str(QA.parent/'official_figure_suite_review_20261012/verify_delivery.py'))['verify']


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])


if __name__ == '__main__':
    commit = git('rev-parse','HEAD').decode().strip()
    remote = git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
    assert commit == remote
    expected = [f'Main/Fig{i:02d}' for i in range(1,8)] + [f'Supplement/FigS{i:02d}' for i in [1,*range(3,14)]]
    numbered = ['results/figure_review/'+s+'.'+ext for s in expected for ext in ['pdf','png']]
    listing = []
    for folder in ['Main','Supplement']:
        r = requests.get(f'https://api.github.com/repos/{REPO}/contents/results/figure_review/{folder}',
                         params={'ref':BRANCH},timeout=(20,60))
        r.raise_for_status()
        names = {e['name'] for e in r.json() if e['type']=='file'}
        required = {Path(s).name+'.'+ext for s in expected if s.startswith(folder+'/') for ext in ['pdf','png']}
        assert required <= names
        listing.append({'directory':folder,'required_files':len(required),'all_present_on_GitHub':True})
    changed = git('diff','--name-only',BASE,commit).decode().splitlines()
    allowed = ('results/figure_review/','results/figures/',
               'docs/reproducibility/s05_plain_figure_labels_20261012/',
               'src/la_grid/plotting/simplify_s05_figure_text_20261012.py',
               'tests/test_current_figure_suite_integration.py')
    assert all(p.startswith(allowed) for p in changed)
    integration = json.loads((QA/'INTEGRATION_QA.json').read_text(encoding='utf-8'))
    scope = set(numbered+changed+[r['mirror_file'] for r in integration['figures']])
    objects = {}
    for rel in sorted(scope):
        blob = git('show',commit+':'+rel)
        m = re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)',blob)
        if m:
            oid, size = m[1].decode(), int(m[2])
            obj = objects.setdefault(oid,{'bytes':size,'paths':[]})
            assert obj['bytes'] == size
            obj['paths'].append(rel)
        else:
            # Canonical Git bytes verify the non-LFS scope without line-ending ambiguity.
            assert blob == git('show',remote+':'+rel)
    records = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(verify,(oid,r['bytes'],r['paths']),commit) for oid,r in objects.items()]
        for done in as_completed(jobs):
            records.append(done.result())
            if len(records)%10 == 0:
                print(f'{len(records)}/{len(objects)} actual remote LFS objects verified',flush=True)
    report = {'branch':BRANCH,'verified_payload_commit':commit,'remote_HEAD_at_verification':remote,
              'numbered_files':38,'github_directory_listing':listing,
              'unique_LFS_payloads':len(records),'actual_bytes_downloaded':sum(r['bytes'] for r in records),
              'all_actual_remote_bytes_verified':True,'scope_is_figure_only':True,
              'files':sorted(records,key=lambda r:r['paths'][0])}
    (QA/'REMOTE_DELIVERY_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'}),flush=True)
