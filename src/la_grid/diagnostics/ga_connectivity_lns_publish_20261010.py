"""Scoped diagnostic publication with ephemeral host credentials and verification."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
import subprocess
import requests

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_connectivity_lns_local_20261010 import OUT

BRANCH = 'diagnostics/noncontiguous-connectivity-lns-local-20261010'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--push', action='store_true', required=True)
    a = p.parse_args()
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO_ROOT, text=True).strip() == BRANCH
    status = json.loads((OUT / 'PRESERVATION_VERIFIED.json').read_text())
    assert status['status'] == 'PASS'
    assert json.loads((OUT / 'CONFIRMATION_EXECUTION.json').read_text())['count'] == 100
    changed = subprocess.check_output(['git', 'diff', '--name-only', '79ac982', 'HEAD'], cwd=REPO_ROOT, text=True).splitlines()
    prefixes = ('results/diagnostics/ga_noncontiguous_connectivity_lns_20261010/',
        'src/la_grid/diagnostics/ga_connectivity_lns_', 'src/la_grid/diagnostics/ga_noncontiguous_setup_',
        'tests/test_connectivity_lns_', 'docs/reviewer/OPTIMIZATION_NONCONTIGUOUS_LNS_')
    assert all(name.startswith(prefixes) for name in changed), changed
    credential = subprocess.run(['git', 'credential', 'fill'], cwd=REPO_ROOT.parent,
        input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True, check=True)
    fields = dict(line.split('=', 1) for line in credential.stdout.splitlines() if '=' in line)
    encoded = base64.b64encode((fields['username'] + ':' + fields['password']).encode()).decode()
    env = os.environ.copy()
    env.update(GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
        GIT_CONFIG_VALUE_0='Authorization: Basic ' + encoded,
        GIT_CONFIG_KEY_1='credential.helper', GIT_CONFIG_VALUE_1='', GIT_TERMINAL_PROMPT='0')
    subprocess.run(['git', 'push', 'origin', 'HEAD:refs/heads/' + BRANCH], cwd=REPO_ROOT, env=env, check=True)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO_ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/' + BRANCH],
        cwd=REPO_ROOT, env=env, text=True).split()[0]
    assert head == remote
    subprocess.run(['git', 'lfs', 'push', '--dry-run', 'origin', BRANCH], cwd=REPO_ROOT, env=env, check=True)
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'HEAD',
        'results/diagnostics/ga_noncontiguous_connectivity_lns_20261010'], cwd=REPO_ROOT, text=True).splitlines()
    objects = {}
    for name in names:
        if not name.endswith(('.csv', '.zip')):
            continue
        pointer = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=REPO_ROOT)
        assert pointer.startswith(b'version https://git-lfs.github.com/spec/v1'), name
        row = dict(line.split(' ', 1) for line in pointer.decode().splitlines())
        objects[row['oid'][7:]] = int(row['size'])
    endpoint = 'https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git/info/lfs/objects/batch'
    response = requests.post(endpoint, auth=(fields['username'], fields['password']),
        headers={'Accept': 'application/vnd.git-lfs+json', 'Content-Type': 'application/vnd.git-lfs+json'},
        json={'operation': 'download', 'transfers': ['basic'],
            'ref': {'name': 'refs/heads/' + BRANCH},
            'objects': [{'oid': oid, 'size': size} for oid, size in objects.items()]}, timeout=90)
    response.raise_for_status()
    remote_objects = response.json()['objects']
    assert {o['oid'] for o in remote_objects} == set(objects)
    for o in remote_objects:
        assert 'error' not in o, o
        action = o['actions']['download']
        payload = requests.get(action['href'], headers=action.get('header', {}), timeout=90)
        payload.raise_for_status()
        assert len(payload.content) == objects[o['oid']]
        assert hashlib.sha256(payload.content).hexdigest() == o['oid']
    print('REMOTE_LFS_PAYLOADS_VERIFIED', len(remote_objects), flush=True)
    print('REMOTE_HEAD_VERIFIED', head, BRANCH, flush=True)


if __name__ == '__main__':
    main()
