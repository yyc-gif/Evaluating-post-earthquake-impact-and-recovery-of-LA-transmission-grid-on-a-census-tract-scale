"""Download changed LFS payloads into an empty store and verify actual bytes."""
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))
import review_publication_gate as gate
a = gate.a


def main():
    branch = 'review/stage7-path-b-p2-figure7-20261013'
    head = a.u.git('rev-parse', 'HEAD').decode().strip()
    assert a.u.git('ls-remote', 'origin', 'refs/heads/' + branch).decode().split()[0] == head
    start = gate.read_json(gate.HERE / 'STARTING_STATE.json')['HEAD']
    paths = a.u.git('diff', '--name-only', start, head).decode().splitlines()
    records = []
    for path in paths:
        blob = a.u.git('show', head + ':' + path)
        m = re.search(rb'^version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize (\d+)', blob)
        if m:
            records.append(dict(path=path, oid=m[1].decode(), size=int(m[2])))
    assert records
    cache = a.ROOT / 'build' / ('publication_gate_remote_' + str(time.time_ns()))
    assert not cache.exists()
    cache.mkdir(parents=True)
    r = subprocess.run(['git', '-C', str(a.ROOT), '-c', 'lfs.storage=' + str(cache), 'lfs', 'fetch',
                        '--include=' + ','.join(r['path'] for r in records), '--exclude=', 'origin', head],
                       text=True, capture_output=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    gate.write('REMOTE_LFS_FETCH_OUTPUT.txt', r.stdout + r.stderr)
    assert r.returncode == 0, r.stdout + r.stderr
    objects = {}
    for row in records:
        oid = row['oid']
        payload = cache / 'objects' / oid[:2] / oid[2:4] / oid
        assert Path(a.u.lp(payload)).stat().st_size == row['size']
        assert a.u.sha(payload) == oid == a.u.sha(a.ROOT / row['path'])
        objects[oid] = row['size']
    assert a.u.git('ls-remote', 'origin', 'refs/heads/' + branch).decode().split()[0] == head
    gate.dump('REMOTE_DELIVERY_VERIFICATION.json', dict(
        status='PASS_ACTUAL_REMOTE_LFS_BYTES', artifact_commit=head, remote_branch=branch,
        remote_HEAD_matches=True, fresh_empty_store=True, paths_verified=len(records),
        unique_objects=len(objects), bytes_downloaded=sum(objects.values()), actual_payloads=records,
        no_merge_or_force_push=True))
    print(head, len(records), 'LFS paths;', sum(objects.values()), 'downloaded bytes hash-verified.')


if __name__ == '__main__':
    main()
