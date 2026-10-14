"""Record preservation and byte-stable current-builder replay."""
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
sys.path.append(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages')
import consolidate_current_figure_suite as u

u.ROOT = ROOT
QA = ROOT / 'docs/reproducibility/figure_suite_concise_captions_20261013'
before = json.load(open(u.lp(QA / 'PRESERVATION_BEFORE.json')))
after = u.protected_snapshot(before)
assert before == after
u.dump(QA / 'PRESERVATION_AFTER.json', after)
checkpoint = json.load(open(u.lp(QA / 'BUILD_CHECKPOINT.json')))
code = "import sys,runpy;sys.path.insert(0,'src/la_grid/plotting');sys.path.append(" + repr(
    r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages') + ");sys.argv=['build_current_suite_k3.py','--portable'];runpy.run_path('src/la_grid/plotting/build_current_suite_k3.py',run_name='__main__')"
r = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True)
if r.returncode:
    raise RuntimeError(r.stderr)
assert all(u.sha(ROOT / p) == h for p, h in checkpoint['output_hashes'].items())
suite = ET.parse(u.lp(QA / 'pytest.xml')).getroot().find('testsuite')
u.dump(QA / 'FINAL_QA.json', dict(tests=int(suite.attrib['tests']), failures=int(suite.attrib['failures']),
       errors=int(suite.attrib['errors']), protected_files=950, original_index_and_status_unchanged=True,
       builder_replay=r.stdout.strip(), output_hashes_unchanged=True,
       packet_sha256=u.sha(ROOT / 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf')))
print(r.stdout.strip(), '950 protected files and original index/status unchanged.')
