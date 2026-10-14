"""Record the entire scientific figure-suite regression run, not a selected subset."""
from pathlib import Path
import importlib.metadata
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE=ROOT/'docs/reproducibility/figure7_candidateA_approved_integration_20261013'
sys.path.append(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages')
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

command=[sys.executable,'-m','pytest','tests/test_current_figure_suite_integration.py','-q',
         '--basetemp=C:/Windows/Temp/fa13_pytest','--junitxml='+u.lp(HERE/'PYTEST_RESULTS.xml')]
run=subprocess.run(command,cwd=str(ROOT),capture_output=True,text=True)
print(run.stdout,flush=True)
syntax=subprocess.run([sys.executable,'-m','compileall','-q','src/la_grid/plotting/build_current_suite_k3.py',
    'src/la_grid/plotting/figure7_candidate_a.py','tests/test_current_figure_suite_integration.py'],
    cwd=str(ROOT),capture_output=True,text=True)
tree=ET.parse(u.lp(HERE/'PYTEST_RESULTS.xml'))
cases=tree.findall('.//testcase')
failed=[c.attrib['name'] for c in cases if c.find('failure') is not None or c.find('error') is not None]
u.dump(HERE/'TEST_RESULTS.json',{'command':command,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,
    'tests':len(cases),'failures':failed,'test_names':[c.attrib['name'] for c in cases],
    'original_suite_tests_retained':19,'carried_forward_S10_tests':3,'new_Candidate_A_tests':4,
    'compileall_exit_code':syntax.returncode,'compileall_stderr':syntax.stderr,'python':platform.python_version(),
    'versions':{name:importlib.metadata.version(name) for name in ['numpy','pandas','matplotlib','PyMuPDF','Pillow','pytest']},
    'generator_sha256':u.sha(ROOT/'src/la_grid/plotting/build_current_suite_k3.py'),
    'layout_module_sha256':u.sha(ROOT/'src/la_grid/plotting/figure7_candidate_a.py')})
assert run.returncode==syntax.returncode==0 and len(cases)==26 and not failed
