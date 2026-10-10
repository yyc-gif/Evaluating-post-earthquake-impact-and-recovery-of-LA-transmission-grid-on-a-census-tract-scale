"""Publish scoped Task A-C evidence and verify remote commit/LFS payloads."""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import subprocess

import requests

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_actionable_delay_20261010 import OUT, START, BRANCH, read, sha


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--push',action='store_true',required=True)
    p.parse_args()
    assert subprocess.check_output(['git','branch','--show-current'],cwd=REPO_ROOT,text=True).strip()==BRANCH
    assert read(OUT/'PRESERVATION_VERIFIED.json')['status']=='PASS'
    assert read(OUT/'RESTRICTED_CERTIFICATES_QA.json')['status']=='PASS'
    assert read(OUT/'EXACT_SIX_SLOT_RESULTS.json')['enumerated_assignments']==86400
    assert read(OUT/'CANDIDATE_PRODUCTION_INFLUENCE.json')['status']=='ALL_PRODUCTION_PARITY_PASS'
    for name,digest in read(OUT/'EVIDENCE_HASHES.json').items():
        assert sha(OUT/name)==digest,name
    changed=subprocess.check_output(['git','diff','--name-only',START,'HEAD'],cwd=REPO_ROOT,text=True).splitlines()
    assert all(name.startswith(('results/diagnostics/ga_actionable_delay_six_slot_20261010/',
        'src/la_grid/diagnostics/ga_actionable_delay_', 'tests/test_actionable_delay_',
        'docs/reviewer/OPTIMIZATION_ACTIONABLE_DELAY_')) for name in changed),changed
    credential=subprocess.run(['git','credential','fill'],cwd=REPO_ROOT.parent,
        input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True)
    fields=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    encoded=base64.b64encode((fields['username']+':'+fields['password']).encode()).decode()
    env=os.environ.copy()
    env.update(GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
        GIT_CONFIG_VALUE_0='Authorization: Basic '+encoded,GIT_CONFIG_KEY_1='credential.helper',
        GIT_CONFIG_VALUE_1='',GIT_TERMINAL_PROMPT='0')
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+BRANCH],cwd=REPO_ROOT,env=env,check=True)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO_ROOT,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+BRANCH],cwd=REPO_ROOT,env=env,text=True).split()[0]
    assert head==remote
    subprocess.run(['git','lfs','push','--dry-run','origin',BRANCH],cwd=REPO_ROOT,env=env,check=True)
    names=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD',
        'results/diagnostics/ga_actionable_delay_six_slot_20261010'],cwd=REPO_ROOT,text=True).splitlines()
    objects={}
    for name in names:
        pointer=subprocess.check_output(['git','show','HEAD:'+name],cwd=REPO_ROOT)
        if pointer.startswith(b'version https://git-lfs.github.com/spec/v1'):
            row=dict(line.split(' ',1) for line in pointer.decode().splitlines())
            objects[row['oid'][7:]]=int(row['size'])
    endpoint='https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git/info/lfs/objects/batch'
    requests_list=[{'oid':oid,'size':size} for oid,size in objects.items()]
    payloads=[]
    for start in range(0,len(requests_list),40):
        response=requests.post(endpoint,auth=(fields['username'],fields['password']),
            headers={'Accept':'application/vnd.git-lfs+json','Content-Type':'application/vnd.git-lfs+json'},
            json={'operation':'download','transfers':['basic'],'ref':{'name':'refs/heads/'+BRANCH},
                'objects':requests_list[start:start+40]},timeout=90)
        response.raise_for_status()
        payloads.extend(response.json()['objects'])
    assert {o['oid'] for o in payloads}==set(objects)
    for obj in payloads:
        assert 'error' not in obj,obj
        action=obj['actions']['download']
        payload=requests.get(action['href'],headers=action.get('header',{}),timeout=180)
        payload.raise_for_status()
        assert len(payload.content)==objects[obj['oid']]
        assert hashlib.sha256(payload.content).hexdigest()==obj['oid']
    print('REMOTE_LFS_PAYLOADS_VERIFIED',len(objects),flush=True)
    print('REMOTE_HEAD_VERIFIED',head,BRANCH,flush=True)


if __name__=='__main__':
    main()
