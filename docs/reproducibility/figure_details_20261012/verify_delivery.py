"""Verify remote branch, numbered files, mirrors and downloaded LFS bytes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
import hashlib
import json
import re
import subprocess
import time
import requests

ROOT = Path(__file__).resolve().parents[3]
BRANCH = 'revision/reviewer-driven-core-rebuild-v2'
REPO = 'yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args]).decode()


def verify(item, commit):
    oid, size, paths = item
    url = f'https://media.githubusercontent.com/media/{REPO}/{commit}/' + quote(paths[0], safe='/')
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, timeout=(20, 90)) as r:
                r.raise_for_status()
                h = hashlib.sha256()
                n = 0
                for b in r.iter_content(1048576):
                    h.update(b)
                    n += len(b)
            assert h.hexdigest() == oid and n == size
            return {'sha256': oid, 'bytes': n, 'paths': paths, 'actual_remote_bytes_verified': True}
        except Exception as e:
            error = str(e)
            time.sleep(2**attempt)
    raise RuntimeError(f'{paths[0]}: {error}')


if __name__ == '__main__':
    commit = git('rev-parse', 'HEAD').strip()
    remote = git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0]
    assert commit == remote
    expected = [f'Main/Fig{i:02d}' for i in range(1, 8)] + [f'Supplement/FigS{i:02d}' for i in [1, *range(3, 14)]]
    numbered = ['results/figure_review/' + s + '.' + ext for s in expected for ext in ['pdf', 'png']]
    tree = git('ls-tree', '-r', '--name-only', commit).splitlines()
    assert set(numbered) <= set(tree)
    github_directories = []
    for folder in ['Main', 'Supplement']:
        response = requests.get(f'https://api.github.com/repos/{REPO}/contents/results/figure_review/{folder}',
                                params={'ref': BRANCH}, timeout=(20, 60))
        response.raise_for_status()
        names = {r['name'] for r in response.json() if r['type'] == 'file'}
        required = {Path(s).name + '.' + ext for s in expected if s.startswith(folder + '/') for ext in ['pdf', 'png']}
        assert required <= names, (folder, required - names)
        github_directories.append({'directory': folder, 'required_files': len(required), 'all_present_on_GitHub': True})
    changed = git('diff', '--name-only', '9b98e2cd571a43ab632a8d3a68c7cdd03d2d84d4', commit).splitlines()
    allowed = ('results/figure_review/', 'results/figures/', 'docs/reproducibility/figure_details_20261012/',
               'src/la_grid/plotting/apply_author_figure_details_20261012.py', 'tests/test_current_figure_suite_integration.py')
    assert all(p.startswith(allowed) for p in changed), changed
    scope = set(numbered + changed)
    # Verify exact mirror pointers, including retained ones.
    integration = json.load(open(Path(__file__).parent / 'INTEGRATION_QA.json', encoding='utf-8'))
    scope.update(r['mirror_file'] for r in integration['figures'])
    objects = {}
    normal = []
    for rel in sorted(scope):
        blob = subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{commit}:{rel}'])
        m = re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)', blob)
        if m:
            oid, size = m.group(1).decode(), int(m.group(2))
            obj = objects.setdefault(oid, {'bytes': size, 'paths': []})
            assert obj['bytes'] == size
            obj['paths'].append(rel)
        else:
            normal.append({'path': rel, 'git_blob_sha256': hashlib.sha256(blob).hexdigest()})
    records = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(verify, (oid, r['bytes'], r['paths']), commit) for oid, r in objects.items()]
        for future in as_completed(futures):
            records.append(future.result())
            if len(records) % 10 == 0:
                print(f'{len(records)}/{len(objects)} actual remote LFS payloads verified', flush=True)
    report = {'branch': BRANCH, 'verified_payload_commit': commit, 'remote_HEAD_at_verification': remote,
              'numbered_figures': len(expected), 'numbered_files': len(numbered),
              'unique_LFS_payloads': len(records), 'LFS_paths': sum(len(r['paths']) for r in records),
              'actual_bytes_downloaded': sum(r['bytes'] for r in records),
              'all_actual_remote_bytes_verified': True, 'protected_science_commit_diff_unchanged': True,
              'github_directory_listing': github_directories,
              'files': sorted(records, key=lambda r: r['paths'][0]), 'git_text_records': normal}
    (Path(__file__).parent / 'REMOTE_DELIVERY_VERIFICATION.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ['files', 'git_text_records']}), flush=True)
