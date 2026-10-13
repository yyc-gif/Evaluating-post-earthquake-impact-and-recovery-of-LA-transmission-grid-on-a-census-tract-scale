"""Run actual canonical CLI replays and verify production-byte idempotence."""
from pathlib import Path
import ast
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import reportlab

ROOT = Path(__file__).resolve().parents[3]
ROOT = Path(str(ROOT).removeprefix('\\\\?\\'))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

checkpoint = ROOT / 'docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/BUILD_CHECKPOINT.json'
paths = json.load(open(u.lp(checkpoint), encoding='utf-8'))['output_hashes']
paths = [*paths, str(checkpoint.relative_to(ROOT)).replace('\\', '/')]
baseline = {p: u.sha(ROOT / p) for p in paths}
records = []
for flags in [['--portable'], ['--portable', '--rebuild'], ['--portable']]:
    # Only append the pure-Python dependency directory; retain the active scientific runtime first.
    bootstrap = ('import sys,runpy;sys.path.append(' + repr(str(Path(reportlab.__file__).parent.parent)) + ');'
        'sys.path.insert(0,' + repr(str(ROOT / 'src/la_grid/plotting')) + ');sys.argv=["build_current_suite_k3.py",' +
        ','.join(repr(f) for f in flags) + '];runpy.run_path("src/la_grid/plotting/build_current_suite_k3.py",run_name="__main__")')
    run = subprocess.run([sys.executable, '-c', bootstrap], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    after = {p: u.sha(ROOT / p) for p in paths}
    assert after == baseline, 'Canonical replay changed production bytes: ' + str([p for p in paths if after[p] != baseline[p]])
    records.append({'entrypoint': 'python src/la_grid/plotting/build_current_suite_k3.py ' + ' '.join(flags),
                    'exit_code': run.returncode, 'stdout': run.stdout.strip(), 'stderr': run.stderr,
                    'all_production_and_checkpoint_bytes_identical': True})
u.dump(HERE / 'BUILD_IDEMPOTENCE_RESULTS.json', {'replays': records, 'checked_file_count': len(paths), 'sha256': baseline})

old = ast.parse(u.payload('8f2dcb3b9762137b9f2686609c34480334f5d44e', 'tests/test_current_figure_suite_integration.py').decode())
new = ast.parse(open(u.lp(ROOT / 'tests/test_current_figure_suite_integration.py'), encoding='utf-8').read())
functions = lambda tree: {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')}
old_tests, new_tests = functions(old), functions(new)
assert len(old_tests) == 19 and len(new_tests) == 22
assert all(new_tests[name] == body for name, body in old_tests.items())
tree = ET.parse(u.lp(HERE / 'TEST_RESULTS.xml'))
suites = list(tree.getroot().iter('testsuite'))
assert sum(int(s.get('tests', 0)) for s in suites) == 22
assert not any(int(s.get('failures', 0)) + int(s.get('errors', 0)) + int(s.get('skipped', 0)) for s in suites)
u.dump(HERE / 'TEST_RESULTS.json', {'tests': 22, 'passed': 22, 'failures': 0, 'errors': 0, 'skipped': 0,
    'original_19_test_function_ASTs_unchanged': True, 'new_regression_tests': sorted(set(new_tests) - set(old_tests)),
    'command': 'python -m pytest tests/test_current_figure_suite_integration.py -q --basetemp=_qa_tmp --junitxml=docs/reproducibility/figure_suite_s10_crossref_fix_20261013/TEST_RESULTS.xml'})
print('Three CLI replays including forced caption rebuild: all bytes stable. Original 19 tests unchanged; 22 passed.')
