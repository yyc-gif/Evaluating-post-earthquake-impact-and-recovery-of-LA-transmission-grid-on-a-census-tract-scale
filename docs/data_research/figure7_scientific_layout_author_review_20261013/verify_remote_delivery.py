"""Download actual review-package LFS bytes from the isolated remote branch."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import uuid

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE = Path(str(Path(__file__).resolve().parent).removeprefix('\\\\?\\'))
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

BASE = '8f2dcb3b9762137b9f2686609c34480334f5d44e'
branch = u.git('branch', '--show-current').decode().strip()
head = u.git('rev-parse', 'HEAD').decode().strip()
remote = u.git('ls-remote', 'origin', 'refs/heads/' + branch).decode().split()[0]
assert branch == 'review/figure7-scientific-layout-author-review-20261013' and head == remote
proof = HERE / 'REMOTE_DELIVERY_VERIFICATION.json'
if '--verify-final' in sys.argv:
    record = json.load(open(u.lp(proof), encoding='utf-8'))
    for item in record['verified_actual_payloads']:
        assert ('oid sha256:' + item['sha256']).encode() in u.git('show', head + ':' + item['path'])
        assert u.sha(Path(record['fresh_empty_cache']) / item['cache_relative_path']) == item['sha256']
    print('Final remote HEAD:', remote, '; downloaded actual LFS bytes match the final review package.')
    sys.exit(0)
paths = u.git('diff', '--name-only', BASE, head).decode().splitlines()
prefix = str(HERE.relative_to(ROOT)).replace('\\', '/') + '/'
assert all(path.startswith(prefix) for path in paths), 'Change outside isolated package'
payloads = []
for path in paths:
    blob = u.git('show', head + ':' + path)
    match = re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)', blob)
    if match:
        payloads.append({'path': path, 'sha256': match[1].decode(), 'size': int(match[2])})
    else:
        assert u.digest(blob) == u.sha(ROOT / path), 'Committed non-LFS bytes differ: ' + path
cache = ROOT.parent / ('_fl_remote_' + uuid.uuid4().hex[:12])
assert not cache.exists()
cache.mkdir()
env = os.environ.copy(); env['GIT_OPTIONAL_LOCKS'] = '0'
subprocess.run(['git', '-C', str(ROOT), '-c', 'lfs.storage=' + cache.as_posix(), 'lfs', 'fetch',
    'origin', head, '--include=' + ','.join(p['path'] for p in payloads), '--exclude='], check=True, env=env)
for item in payloads:
    h = item['sha256']; relative = 'objects/' + h[:2] + '/' + h[2:4] + '/' + h
    assert os.path.getsize(u.lp(cache / relative)) == item['size'] and u.sha(cache / relative) == h
    assert u.sha(ROOT / item['path']) == h
    item['cache_relative_path'] = relative
u.dump(proof, {'review_artifact_commit': head, 'verified_remote_HEAD': remote, 'branch': branch,
    'fresh_empty_cache': cache.as_posix(), 'all_changed_paths_inside_review_package': True,
    'non_LFS_committed_bytes_also_checked': True, 'verified_actual_payloads': payloads,
    'payload_count': len(payloads), 'total_payload_bytes': sum(p['size'] for p in payloads),
    'downloaded_from_remote': True, 'pointer_only_verification': False})
print('Remote delivery PASS:', len(payloads), 'actual LFS files,', sum(p['size'] for p in payloads), 'bytes.')
