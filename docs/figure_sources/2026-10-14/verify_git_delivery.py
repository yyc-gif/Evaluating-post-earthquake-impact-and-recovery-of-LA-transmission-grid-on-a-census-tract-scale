"""Scoped review-package delivery and fresh remote-LFS-byte verification."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import pandas as pd

import build_local_review as review

u = review.a.u
OUT = review.OUT
ROOT = review.ROOT
BASE = review.AUTHORITY
BRANCH = 'review/stage7-path-b-p2-figure7-20261013'
PREFIX = 'local_elsevier_review_outputs/'


def included(p):
    rel = p.relative_to(OUT)
    return (p.is_file() and '__pycache__' not in rel.parts
            and not any(part in ['qa', 'qa_final'] for part in rel.parts)
            and p.suffix != '.pyc' and p.name != 'FILE_SHA256_MANIFEST.csv')


def preservation():
    before = review.read_json(OUT / 'PRESERVATION_BEFORE.json')
    for name, expected in before['tracked_materialized_file_hashes'].items():
        if name != '.gitattributes':
            assert u.sha(ROOT / name) == expected, name
    assert u.protected_snapshot(before['protected_original_worktree']) == before['protected_original_worktree']
    assert u.git('branch', '--show-current').decode().strip() == BRANCH
    changed = u.git('diff', BASE, '--name-only').decode().splitlines()
    assert all(p == '.gitattributes' or p.startswith(PREFIX) for p in changed), changed
    return dict(original_tracked_files_unchanged_except_scoped_lfs_attributes=True,
                protected_original_scientific_files_unchanged=950,
                original_worktree_and_index_unchanged=True,
                active_17_numbered_artwork_pairs_unchanged=True,
                no_merge_or_formal_promotion=True)


def prepare():
    old = pd.read_csv(u.lp(OUT / 'FILE_SHA256_MANIFEST.csv'))
    editable = {'README.md', 'FINAL_LOCAL_REVIEW_REPORT.md'}
    for row in old.itertuples():
        path = OUT / row.path
        if row.path not in editable:
            assert u.sha(path) == row.sha256, row.path
    proof = preservation()
    proof.update(baseline_commit=BASE, delivery_branch=BRANCH,
                 author_authorized_commit_push=True,
                 original_review_artifact_hashes_verified=True)
    review.dump('GIT_DELIVERY_PRESERVATION_QA.json', proof)
    refresh_manifest()
    print('PASS: review artifact hashes, original artwork and 950 protected files unchanged.')


def refresh_manifest():
    rows = [dict(path=str(p.relative_to(OUT)).replace('\\', '/'), bytes=p.stat().st_size,
                 sha256=u.sha(p)) for p in sorted(OUT.rglob('*')) if included(p)]
    u.write_csv(OUT / 'FILE_SHA256_MANIFEST.csv', rows)


def remote(no_write=False):
    preservation()
    head = u.git('rev-parse', 'HEAD').decode().strip()
    remote_head = lambda: u.git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0]
    assert remote_head() == head
    paths = u.git('diff', '--name-only', BASE, head).decode().splitlines()
    assert all(p == '.gitattributes' or p.startswith(PREFIX) for p in paths)
    records = []
    for path in paths:
        raw = u.git('show', head + ':' + path)
        match = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize (\d+)\n', raw)
        if match:
            records.append(dict(path=path, oid=match[1].decode(), size=int(match[2])))
    assert records
    cache = ROOT / 'build' / ('elsevier_remote_' + str(time.time_ns()))
    assert not cache.exists()
    cache.mkdir(parents=True)
    command = ['git', '-C', str(ROOT), '-c', 'lfs.storage=' + str(cache), 'lfs', 'fetch',
               '--include=' + ','.join(r['path'] for r in records), '--exclude=', 'origin', head]
    result = subprocess.run(command, capture_output=True, text=True,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    assert result.returncode == 0, result.stdout + result.stderr
    unique = {}
    for row in records:
        oid = row['oid']
        path = cache / 'objects' / oid[:2] / oid[2:4] / oid
        assert Path(u.lp(path)).stat().st_size == row['size']
        assert u.sha(path) == oid == u.sha(ROOT / row['path'])
        unique[oid] = row['size']
    assert remote_head() == head
    data = dict(status='PASS_ACTUAL_REMOTE_LFS_BYTES', artifact_commit=head, remote_branch=BRANCH,
                remote_HEAD_matches=True, fresh_empty_store=True, paths_verified=len(records),
                unique_objects=len(unique), bytes_downloaded=sum(unique.values()),
                payloads=records, no_merge_or_force_push=True)
    if not no_write:
        review.dump('GIT_REMOTE_DELIVERY_VERIFICATION.json', data)
        refresh_manifest()
    print(json.dumps({k: v for k, v in data.items() if k != 'payloads'}))


if __name__ == '__main__':
    if sys.argv[1] == 'prepare':
        prepare()
    else:
        assert sys.argv[1] == 'remote'
        remote('--no-write' in sys.argv)
