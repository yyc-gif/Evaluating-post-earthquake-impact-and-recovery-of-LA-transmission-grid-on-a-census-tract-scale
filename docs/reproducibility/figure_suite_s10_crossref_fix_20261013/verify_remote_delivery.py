"""Verify remote HEAD and download changed actual LFS bytes into a fresh cache."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import uuid

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

BASE = '8f2dcb3b9762137b9f2686609c34480334f5d44e'
branch = u.git('branch', '--show-current').decode().strip()
head = u.git('rev-parse', 'HEAD').decode().strip()
remote = u.git('ls-remote', 'origin', 'refs/heads/' + branch).decode().split()[0]
assert branch == 'review/figure-suite-s10-crossreference-fix-20261013' and head == remote
proof = HERE / 'REMOTE_DELIVERY_VERIFICATION.json'
if '--verify-final' in sys.argv:
    record = json.load(open(u.lp(proof), encoding='utf-8'))
    for item in record['verified_actual_payloads']:
        pointer = u.git('show', head + ':' + item['path'])
        assert ('oid sha256:' + item['sha256']).encode() in pointer
        assert u.sha(Path(record['fresh_empty_cache']) / item['cache_relative_path']) == item['sha256']
    print('Final remote HEAD:', remote, '; all downloaded LFS bytes still match final commit.')
    sys.exit(0)
paths = u.git('diff', '--name-only', BASE, head).decode().splitlines()
payloads = []
for path in paths:
    pointer = u.git('show', head + ':' + path)
    match = re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)', pointer)
    if match:
        payloads.append({'path': path, 'sha256': match[1].decode(), 'size': int(match[2])})
assert any(p['path'] == 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf' for p in payloads)
cache = ROOT.parent / ('_s10_remote_' + uuid.uuid4().hex[:12])
assert not cache.exists()
cache.mkdir()
assert not list(cache.iterdir())
env = os.environ.copy()
env['GIT_OPTIONAL_LOCKS'] = '0'
command = ['git', '-C', str(ROOT), '-c', 'lfs.storage=' + cache.as_posix(), 'lfs', 'fetch',
           'origin', head, '--include=' + ','.join(p['path'] for p in payloads), '--exclude=']
subprocess.run(command, check=True, env=env)
for item in payloads:
    h = item['sha256']
    relative = 'objects/' + h[:2] + '/' + h[2:4] + '/' + h
    path = cache / relative
    assert os.path.getsize(u.lp(path)) == item['size'] and u.sha(path) == h
    assert u.sha(ROOT / item['path']) == h
    item['cache_relative_path'] = relative
u.dump(proof, {'publication_commit': head, 'verified_remote_HEAD': remote, 'branch': branch,
    'fresh_empty_cache': cache.as_posix(), 'download_from_remote_not_existing_common_store': True,
    'verified_actual_payloads': payloads, 'payload_count': len(payloads),
    'total_payload_bytes': sum(p['size'] for p in payloads), 'pointer_only_verification': False})
print('Remote HEAD and actual changed LFS payloads PASS:', len(payloads), 'files;', sum(p['size'] for p in payloads), 'bytes.')
