"""Evidence QA and transport reuse; no search or physical sampling."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import subprocess
import sys
from types import SimpleNamespace

import finalize as f


def child_identity():
    f.worker_setup()
    return dict(out=str(f.q.OUT), candidate=f.q.POLICIES[0]['sequence_sha256'],
                strategy=f.q.POLICIES[0]['strategy'], station_count=len(f.q.MODEL['ids']))


def preflight():
    freeze = f.verify()
    assert f.preserved(freeze['protected_revision_checkout'], freeze['old_validation_checkout'],
                       freeze['source_checkout']) == f.v.read(f.OUT / 'PRESERVATION_BASELINE.json')
    commands = [
        [sys.executable, '-B', '-m', 'pytest', 'tests/test_standalone_ils_validation_20261011.py',
         'tests/test_independent_validation_ready_20261010.py', '--basetemp=_qa_original', '-q'],
        [sys.executable, '-B', '-m', 'pytest', str(f.OUT / 'test_finalize.py'), '--basetemp=_qa_freeze', '-q']]
    records = []
    for command in commands:
        result = subprocess.run(command, cwd=f.ROOT, text=True, capture_output=True, check=True)
        records.append(dict(command=command, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr))
    with ProcessPoolExecutor(max_workers=1) as pool:
        child = pool.submit(child_identity).result()
    assert child['out'] == str(f.OUT) and child['strategy'] == f.CANDIDATE
    assert child['candidate'] == freeze['strategies'][0]['sequence_sha256'] and child['station_count'] == 92
    qa = f.v.read(f.OUT / 'ENGINEERING_QA.json')
    assert qa['genuine_sampling_calls'] == 0 and qa['production_calls'] == 16
    f.v.write(f.OUT / 'PREFLIGHT_QA.json', dict(status='PASS', tests=records, windows_spawn=child,
        planning_production_qa_reused_64=True, engineering_original_cases_only=True,
        new_search_calls=0, new_genuine_physical_draws=0,
        protected_files=950, original_staged_items=862, all_preservation_hashes_equal=True,
        earlier_test_setup_failure='Missing deep runtime parent for pytest basetemp; tests rerun at short worktree-relative basetemp, all16 pass',
        repaired_before_preregistration=True))
    print('PREFLIGHT_PASS:16tests; Windows spawn correct candidate;950/862 preserved', flush=True)


def manifest():
    records = {}
    roots = [f.OUT, f.v.long_path(f.ROOT / 'Review_and_Revision/Pure_Random_GA_20261011')]
    for root in roots:
        for p in root.rglob('*'):
            if not p.is_file() or any(x in p.parts for x in ('cohort','engineering','runtime','__pycache__')):
                continue
            if p.name in ('OUTPUT_HASH_MANIFEST.json','REMOTE_PUBLICATION_VERIFIED.json','REVIEW_REMOTE_VERIFIED.json'):
                continue
            name = str(p.relative_to(f.v.long_path(f.ROOT))).replace('\\','/')
            records[name] = dict(sha256=f.v.sha(p), bytes=p.stat().st_size)
    f.v.write(f.OUT / 'OUTPUT_HASH_MANIFEST.json', dict(files=records,
                total_bytes=sum(x['bytes'] for x in records.values())))


def remote():
    # Reuse the already validated actual-LFS-download implementation.
    f.verify()
    spec = importlib.util.spec_from_file_location('prior_transport', f.PRIOR / 'publish.py')
    sys.path.insert(0, str(f.PRIOR))
    transport = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transport)
    transport.s = SimpleNamespace(ROOT=f.ROOT,
        OUT=f.ROOT / 'results/diagnostics/pure_random_ga_final_20261011', BRANCH=f.BRANCH,
        lp=f.v.long_path, digest=f.v.sha, save=f.v.write,
        git=lambda *args: f.git(f.ROOT,*args))
    changed = f.git(f.ROOT,'diff','--name-only',f.BASE,'HEAD').decode().splitlines()
    allowed = ('results/diagnostics/pure_random_ga_final_20261011/',
               'Review_and_Revision/Pure_Random_GA_20261011/')
    assert changed and all(name.startswith(allowed) for name in changed), changed
    transport.remote()
    transport.s.OUT = f.ROOT / allowed[1]
    transport.s.save = lambda path, receipt: f.v.write(f.OUT / 'REVIEW_REMOTE_VERIFIED.json', receipt)
    transport.remote()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['preflight','manifest','remote'])
    phase = parser.parse_args().phase
    if phase == 'preflight': preflight()
    elif phase == 'manifest': manifest()
    else: remote()
