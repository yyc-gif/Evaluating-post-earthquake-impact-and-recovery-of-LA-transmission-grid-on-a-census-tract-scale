"""Scope-check diagnostic commits and verify streamed remote LFS payloads."""
from __future__ import annotations
import base64
import hashlib
import os
import subprocess
import time

import requests

from la_grid.diagnostics.standalone_ils_20261010 import R, OUT, read, save, sha, preservation


PREFIX = 'results/diagnostics/standalone_ils_final_method_20261010/'
ALLOWED = (PREFIX, 'src/la_grid/diagnostics/standalone_ils_', 'tests/test_standalone_ils_')
START = '62f0c2be4f1e37f25e3db8d0d042cd5d0cfcfd3f'
BRANCH = 'diagnostics/standalone-ils-final-method-decision-20261010'


def git(*args, env=None):
    return subprocess.check_output(['git', *args], cwd=R, env=env)


def publish():
    qa = read(OUT / 'REPRODUCIBILITY_AND_PRESERVATION_QA.json')
    assert qa['status'] == 'PASS'
    assert preservation() == read(OUT / 'PRESERVATION_BASELINE.json')
    assert git('branch', '--show-current').decode().strip() == BRANCH
    changed = git('diff', '--name-only', START, 'HEAD').decode().splitlines()
    assert changed and all(n.startswith(ALLOWED) for n in changed), changed
    unrelated = git('status', '--porcelain').decode().splitlines()
    scoped = [line for line in unrelated if line[3:].strip('"').startswith(ALLOWED)]
    assert not scoped, scoped
    for name, expected in qa['required_deliverable_sha256'].items():
        blob = git('show', 'HEAD:'+PREFIX+name)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            fields = dict(line.split(' ',1) for line in blob.decode().splitlines())
            assert fields['oid'] == 'sha256:'+expected
        else:
            assert hashlib.sha256(blob).hexdigest() == expected
    for name, expected in qa['scoped_source_sha256'].items():
        repository_path = name.replace('\\', '/')
        assert hashlib.sha256(git('show','HEAD:'+repository_path)).hexdigest() == expected, name
    credential = subprocess.run(['git','credential','fill'], cwd=R.parent,
        input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True, check=True)
    fields = dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    encoded = base64.b64encode((fields['username']+':'+fields['password']).encode()).decode()
    env = os.environ.copy()
    env.update(GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
        GIT_CONFIG_VALUE_0='Authorization: Basic '+encoded, GIT_CONFIG_KEY_1='credential.helper',
        GIT_CONFIG_VALUE_1='', GIT_TERMINAL_PROMPT='0')
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+BRANCH], cwd=R, env=env, check=True)
    head = git('rev-parse','HEAD').decode().strip()
    remote = git('ls-remote','origin','refs/heads/'+BRANCH, env=env).decode().split()[0]
    assert remote == head
    names = git('ls-tree','-r','--name-only','HEAD',PREFIX).decode().splitlines()
    objects = {}
    for name in names:
        blob = git('show','HEAD:'+name)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            row = dict(line.split(' ',1) for line in blob.decode().splitlines())
            oid, size = row['oid'][7:], int(row['size'])
            assert sha(R/name) == oid
            objects.setdefault(oid,dict(bytes=size,paths=[]))['paths'].append(name)
    endpoint = 'https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git/info/lfs/objects/batch'
    wanted = [dict(oid=oid,size=r['bytes']) for oid,r in objects.items()]
    received, tick = [], time.perf_counter()
    for start in range(0,len(wanted),40):
        response = requests.post(endpoint, auth=(fields['username'],fields['password']),
            headers={'Accept':'application/vnd.git-lfs+json','Content-Type':'application/vnd.git-lfs+json'},
            json=dict(operation='download',transfers=['basic'],ref={'name':'refs/heads/'+BRANCH},
                      objects=wanted[start:start+40]), timeout=90)
        response.raise_for_status()
        received.extend(response.json()['objects'])
    assert {o['oid'] for o in received} == set(objects)
    for obj in received:
        assert 'error' not in obj
        action, digest, size = obj['actions']['download'], hashlib.sha256(), 0
        with requests.get(action['href'], headers=action.get('header',{}), stream=True, timeout=180) as response:
            response.raise_for_status()
            for block in response.iter_content(2**20):
                digest.update(block)
                size += len(block)
        assert size == objects[obj['oid']]['bytes'] and digest.hexdigest() == obj['oid']
        objects[obj['oid']]['downloaded_sha256'] = digest.hexdigest()
        print('REMOTE_LFS_DOWNLOADED_VERIFIED',obj['oid'],size,flush=True)
    assert preservation() == read(OUT / 'PRESERVATION_BASELINE.json')
    save(OUT / 'REMOTE_PUBLICATION_VERIFIED.json',dict(status='PASS', data_commit=head, branch=BRANCH,
        remote_head_verified=True, remote_lfs_payloads=objects,
        downloaded_bytes=sum(r['bytes'] for r in objects.values()),
        download_verification_wall_seconds=time.perf_counter()-tick, protected950_preserved=True,
        unrelated_worktree_status_preserved=unrelated, receipt_commit_must_be_pushed_separately=True))
    print('REMOTE_HEAD_VERIFIED',head,BRANCH,flush=True)


if __name__ == '__main__':
    publish()
