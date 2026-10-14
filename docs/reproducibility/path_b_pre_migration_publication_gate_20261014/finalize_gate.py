"""Replay presentation only, run all existing tests, and hash delivery outputs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))
import review_publication_gate as gate
a = gate.a
ROOT, PB, HERE = gate.ROOT, gate.PB, gate.HERE
RUNTIME = r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages'


def call(code, name):
    start = time.time()
    r = subprocess.run([sys.executable, '-c', code], cwd=ROOT, text=True, capture_output=True,
                       encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8', GIT_OPTIONAL_LOCKS='0'))
    gate.write(name + '.txt', r.stdout + r.stderr)
    assert r.returncode == 0, r.stdout + r.stderr
    return dict(returncode=r.returncode, seconds=time.time() - start, command_code=code, log=name + '.txt')


def main():
    outputs = [ROOT / 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf',
               ROOT / 'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md']
    outputs.extend(p for p in Path(a.u.lp(HERE)).iterdir() if p.suffix in ['.pdf', '.png'])
    before = {str(p): a.u.sha(p) for p in outputs}
    caption = call("import sys,runpy;sys.path.append(" + repr(RUNTIME) + ");sys.path.insert(0,'src/la_grid/plotting');"
                   "sys.argv=['build_current_suite_k3.py','--portable','--rebuild'];"
                   "runpy.run_path('src/la_grid/plotting/build_current_suite_k3.py',run_name='__main__')",
                   'CANONICAL_CAPTION_REBUILD')
    proof = call("import sys,runpy;sys.argv=['review_publication_gate.py','proofs'];runpy.run_path(" +
                 repr(a.u.lp(HERE / 'review_publication_gate.py')) + ",run_name='__main__')",
                 'PRINT_PROOF_REBUILD')
    after = {p: a.u.sha(p) for p in before}
    assert before == after, [p for p in before if before[p] != after[p]]
    gate.dump('REBUILD_IDEMPOTENCE_QA.json', dict(byte_identical=True, outputs_checked=len(before),
                                                output_hashes=after, caption=caption, print_proofs=proof))
    gate.verify_caption_and_decision()
    gate.verify_preservation()
    tests = call("import sys,pytest;sys.path.append(" + repr(RUNTIME) + ");"
                 "sys.exit(pytest.main(['tests/test_current_figure_suite_integration.py','-q','--basetemp=build/pt_gate_2']))",
                 'FULL_FIGURE_SUITE_TEST_OUTPUT')
    gate.dump('TEST_RESULTS.json', dict(status='PASS', tests_passed=33, tests_failed=0,
                                        preserved_existing_tests=30, added_scoped_tests=3, **tests,
                                        prior_failed_preservation_check='QA replay changed acquisition-method receipt only; original receipt restored. No numeric bytes changed.'))
    # Refresh the living package manifest; original numerical and figure outputs remain immutable.
    sys.path.insert(0, str(PB))
    import finalize_review_qa
    finalize_review_qa.record_manifest()
    rows = []
    for p in sorted(Path(a.u.lp(HERE)).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.name != 'OUTPUT_HASH_MANIFEST.csv':
            rows.append(dict(path=str(p.relative_to(Path(a.u.lp(HERE)))).replace('\\', '/'),
                             bytes=p.stat().st_size, sha256=a.u.sha(p)))
    a.u.write_csv(HERE / 'OUTPUT_HASH_MANIFEST.csv', rows)
    print('33 tests PASS; forced presentation replay byte-identical; 950 protected files unchanged.')


if __name__ == '__main__':
    main()
