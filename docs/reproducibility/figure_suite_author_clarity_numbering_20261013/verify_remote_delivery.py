"""Download actual current LFS payloads into a new, empty object store."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import time

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

QA = ROOT / 'docs/reproducibility/figure_suite_author_clarity_numbering_20261013'
BRANCH = 'review/figure-suite-author-clarity-numbering-20261013'


def main():
    env = os.environ.copy()
    env['GIT_OPTIONAL_LOCKS'] = '0'
    def git(*args):
        return subprocess.check_output(['git', '-C', str(ROOT), *args], env=env)
    head = git('rev-parse', 'HEAD').decode().strip()
    remote = git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0]
    assert head == remote
    patterns = ['results/figure_review/Main/*', 'results/figure_review/Supplement/*',
                'results/figure_review/Page_Previews/*', 'results/figure_review/ALL*.pdf',
                'results/figure_review/FIGURE_MANIFEST.csv', 'results/figures/*',
                'docs/reproducibility/figure_suite_author_clarity_numbering_20261013/*',
                'docs/reproducibility/figure_suite_author_clarity_numbering_20261013/source_control_inputs/*']
    paths = git('ls-tree', '-r', '--name-only', head).decode().splitlines()
    import fnmatch
    selected = [p for p in paths if any(fnmatch.fnmatchcase(p, pat) for pat in patterns)]
    payloads = []
    for path in selected:
        blob = git('show', head + ':' + path)
        m = re.search(rb'^version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize (\d+)', blob)
        if m:
            payloads.append(dict(path=path, oid=m[1].decode(), size=int(m[2])))
    cache = ROOT / 'build' / ('lfs_real_byte_delivery_' + str(time.time_ns()))
    assert not cache.exists()
    cache.mkdir(parents=True)
    fetch = subprocess.run(['git', '-C', str(ROOT), '-c', 'lfs.storage=' + str(cache),
                            'lfs', 'fetch', '--include=' + ','.join(patterns), '--exclude=',
                            'origin', head], env=env, text=True, capture_output=True)
    u.write(QA / 'REMOTE_LFS_FETCH_OUTPUT.txt', fetch.stdout + fetch.stderr)
    assert fetch.returncode == 0, fetch.stdout + fetch.stderr
    objects = {}
    for row in payloads:
        oid = row['oid']
        path = cache / 'objects' / oid[:2] / oid[2:4] / oid
        assert Path(u.lp(path)).stat().st_size == row['size']
        assert u.sha(path) == oid == u.sha(ROOT / row['path'])
        objects[oid] = row['size']
    assert git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0] == head
    u.dump(QA / 'REMOTE_DELIVERY_VERIFICATION.json', dict(
        status='PASS_ACTUAL_REMOTE_PAYLOAD_BYTES', artifact_commit=head,
        remote_branch=BRANCH, remote_HEAD_matches=True, empty_cache_before_fetch=True,
        independent_storage=str(cache), paths_verified=len(payloads),
        unique_LFS_objects=len(objects), unique_payload_bytes=sum(objects.values()),
        payloads=payloads, no_merge_or_force_push=True))
    print('Verified remote HEAD:', head)
    print('Actual remote LFS:', len(objects), 'objects;', sum(objects.values()), 'bytes')


if __name__ == '__main__':
    main()
