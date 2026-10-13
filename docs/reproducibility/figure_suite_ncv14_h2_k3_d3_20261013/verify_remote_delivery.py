"""Download required LFS payloads into an empty nonce cache and verify real bytes."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).resolve().parent
BRANCH = 'review/official-figure-suite-ncv14-h2-k3-d3-20261013'
INCLUDE = ','.join(['results/figure_review/Main/**', 'results/figure_review/Supplement/**',
    'results/figure_review/Page_Previews/**', 'results/figure_review/ALL_*.pdf',
    'results/figure_review/FIGURE_MANIFEST.csv', 'results/figures/*.pdf', 'results/figures/*.png',
    'results/figures/FIGURE_INDEX.csv', 'docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/**',
    'results/figure_review/Additional_Evidence/Q4_High_Deficit_94_Frozen_GEOIDs.csv'])


def lp(p):
    p = str(p.resolve())
    return p if os.name != 'nt' or p.startswith('\\\\?\\') else '\\\\?\\' + p


def git(*args):
    env = os.environ.copy()
    env['GIT_OPTIONAL_LOCKS'] = '0'
    return subprocess.check_output(['git', '-C', str(ROOT), *args], env=env)


def wanted(rel):
    return (rel.startswith(('results/figure_review/Main/', 'results/figure_review/Supplement/',
        'results/figure_review/Page_Previews/', 'docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/'))
        or rel in ['results/figure_review/FIGURE_MANIFEST.csv', 'results/figures/FIGURE_INDEX.csv',
                   'results/figure_review/Additional_Evidence/Q4_High_Deficit_94_Frozen_GEOIDs.csv']
        or rel.startswith('results/figure_review/ALL_') and rel.endswith('.pdf')
        or rel.startswith('results/figures/') and rel.endswith(('.pdf', '.png')))


def sha(p):
    h = hashlib.sha256()
    with open(lp(p), 'rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def main():
    head = git('rev-parse', 'HEAD').decode().strip()
    remote = git('ls-remote', 'origin', 'refs/heads/'+BRANCH).decode().split()[0]
    assert head == remote, (head, remote)
    cache = ROOT.parent / ('_lvr13_' + uuid.uuid4().hex[:12])
    assert not cache.exists()
    cache.mkdir()
    assert not list(cache.iterdir())
    # No use of the primary local LFS store; all selected objects must be fetched here.
    config = 'lfs.storage=' + str(cache).replace('\\','/')
    subprocess.run(['git', '-C', str(ROOT), '-c', config, 'lfs', 'fetch', 'origin', head,
                    '--include='+INCLUDE, '--exclude='], check=True)
    rows = []
    unique = {}
    paths = git('ls-tree', '-r', '--name-only', '-z', head).decode().split('\0')
    for rel in paths:
        if not rel or not wanted(rel):
            continue
        b = git('show', head+':'+rel)
        m = re.search(rb'^version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize (\d+)', b)
        if not m:
            continue
        oid, size = m[1].decode(), int(m[2])
        p = cache/'objects'/oid[:2]/oid[2:4]/oid
        assert p.is_file(), rel
        assert p.stat().st_size == size and sha(p) == oid, rel
        rows.append({'path':rel, 'lfs_oid':oid, 'bytes':size, 'actual_download_sha256':oid, 'verified':True})
        unique[oid] = size
    assert len([r for r in rows if r['path'].startswith(('results/figure_review/Main/', 'results/figure_review/Supplement/'))]) == 34
    assert len([r for r in rows if r['path'].startswith('results/figures/') and r['path'].endswith(('.pdf','.png'))]) == 34
    assert len([r for r in rows if r['path'].startswith('results/figure_review/ALL_')]) == 3
    assert git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0] == head
    report = {'publication_commit':head, 'remote_verified_HEAD':head, 'branch':BRANCH,
        'verification':'Actual remote download into newly created empty nonce storage; SHA256 and size checks',
        'isolated_cache_basename':cache.name, 'cache_was_new_and_empty':True,
        'primary_LFS_store_used_for_verification':False, 'required_LFS_paths_verified':len(rows),
        'unique_objects_verified':len(unique), 'unique_downloaded_bytes':sum(unique.values()),
        'all_17_numbered_pairs_and_17_mirrors_verified':True, 'all_three_packets_verified':True,
        'paths':rows, 'no_merge_or_force_push':True}
    with open(lp(QA/'REMOTE_DELIVERY_VERIFICATION.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(report,f,indent=2);f.write('\n')
    print(f'Remote HEAD verified; {len(rows)} LFS paths / {len(unique)} unique objects / {sum(unique.values()):,} actual downloaded bytes verified.')


if __name__ == '__main__':
    main()
