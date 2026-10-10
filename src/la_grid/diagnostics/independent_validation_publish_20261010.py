"""Scoped diagnostic publication with remote HEAD and downloaded LFS verification."""
from __future__ import annotations

import base64
import hashlib
import os
import subprocess

import requests

from la_grid.diagnostics.independent_validation_20261010 import (
    R, OUT, START, BRANCH, read, sha, verify_freeze, snapshot,
)


def main():
    verify_freeze()
    assert read(OUT/'VALIDATION_DRY_RUN_QA.json')['status']=='PASS'
    assert read(OUT/'READINESS_RECEIPT.json')['new_validation_samples_generated']==0
    freeze = read(OUT/'FINAL_VALIDATION_FREEZE_RECEIPT.json')
    from pathlib import Path
    assert snapshot(Path(freeze['protected_revision_checkout']))==read(OUT/'PRESERVATION_BASELINE.json')
    assert subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()==BRANCH
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=R)
    changed = subprocess.check_output(['git','diff','--name-only',START,'HEAD'],cwd=R,text=True).splitlines()
    allowed = ('results/diagnostics/independent_validation_ready_20261010/',
        'src/la_grid/diagnostics/independent_validation_', 'tests/test_independent_validation_',
        'docs/reviewer/INDEPENDENT_VALIDATION_READINESS_')
    assert all(n.startswith(allowed) or n=='src/la_grid/diagnostics/.gitattributes' for n in changed),changed
    # Existing Git credential helper supplies a transient header; never log/store credentials.
    credential = subprocess.run(['git','credential','fill'],cwd=R.parent,
        input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True)
    fields = dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    encoded = base64.b64encode((fields['username']+':'+fields['password']).encode()).decode()
    env = os.environ.copy()
    env.update(GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
        GIT_CONFIG_VALUE_0='Authorization: Basic '+encoded,GIT_CONFIG_KEY_1='credential.helper',
        GIT_CONFIG_VALUE_1='',GIT_TERMINAL_PROMPT='0')
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+BRANCH],cwd=R,env=env,check=True)
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
    remote = subprocess.check_output(['git','ls-remote','origin','refs/heads/'+BRANCH],cwd=R,env=env,text=True).split()[0]
    assert head==remote
    subprocess.run(['git','lfs','push','--dry-run','origin',BRANCH],cwd=R,env=env,check=True)
    names = subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD',
        'results/diagnostics/independent_validation_ready_20261010'],cwd=R,text=True).splitlines()
    objects = {}
    for name in names:
        blob = subprocess.check_output(['git','show','HEAD:'+name],cwd=R)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            row = dict(line.split(' ',1) for line in blob.decode().splitlines())
            objects[row['oid'][7:]] = int(row['size'])
    endpoint = 'https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git/info/lfs/objects/batch'
    wanted = [{'oid':oid,'size':size} for oid,size in objects.items()]
    received = []
    for start in range(0,len(wanted),40):
        response = requests.post(endpoint,auth=(fields['username'],fields['password']),
            headers={'Accept':'application/vnd.git-lfs+json','Content-Type':'application/vnd.git-lfs+json'},
            json={'operation':'download','transfers':['basic'],'ref':{'name':'refs/heads/'+BRANCH},
                'objects':wanted[start:start+40]},timeout=90)
        response.raise_for_status()
        received.extend(response.json()['objects'])
    assert {o['oid'] for o in received}==set(objects)
    for obj in received:
        assert 'error' not in obj,obj
        action = obj['actions']['download']
        response = requests.get(action['href'],headers=action.get('header',{}),timeout=180)
        response.raise_for_status()
        assert len(response.content)==objects[obj['oid']]
        assert hashlib.sha256(response.content).hexdigest()==obj['oid']
    print('REMOTE_LFS_DOWNLOADED_AND_VERIFIED',len(objects),flush=True)
    print('REMOTE_HEAD_VERIFIED',head,BRANCH,flush=True)
    print('PRESERVATION_VERIFIED',len(snapshot(Path(freeze['protected_revision_checkout']))['files_sha256']),flush=True)


if __name__=='__main__':
    main()
