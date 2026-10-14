"""Run default and forced canonical replay; preserve a real-byte stability record."""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT=Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE=ROOT/'docs/reproducibility/figure7_candidateA_approved_integration_20261013'
sys.path.append(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages')
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

checkpoint=ROOT/'docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/BUILD_CHECKPOINT.json'
expected=json.load(open(u.lp(checkpoint)))
commands=[]
for args in [[],['--rebuild'],['--rebuild'],[]]:
    code=("import sys,runpy;sys.path.append(r'C:\\Users\\yinch\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\Lib\\site-packages');"
          "sys.path.insert(0,r'src/la_grid/plotting');sys.argv=['build_current_suite_k3.py','--portable']+"+repr(args)+";"
          "runpy.run_path(r'src/la_grid/plotting/build_current_suite_k3.py',run_name='__main__')")
    env=os.environ.copy();env['GIT_OPTIONAL_LOCKS']='0'
    result=subprocess.run([sys.executable,'-c',code],cwd=str(ROOT),env=env,text=True,capture_output=True)
    commands.append({'command':'python src/la_grid/plotting/build_current_suite_k3.py --portable '+' '.join(args),
        'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    print(result.stdout,flush=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    actual=json.load(open(u.lp(checkpoint)))
    if len(commands)==1:
        expected=actual
    assert expected==actual,'Forced build did not reproduce exact output bytes'
    assert all(u.sha(ROOT/path)==h for path,h in expected['output_hashes'].items())
u.dump(HERE/'BUILD_IDEMPOTENCE_QA.json',{'default_replays':2,'forced_rebuilds':2,
    'all_canonical_output_hashes_identical':True,'checks':commands,
    'output_hashes':expected['output_hashes'],'generator_sha256':expected['generator_sha256'],
    'layout_module_sha256':expected['layout_module_sha256']})
print('Default replay and two forced source builds are byte-identical.',flush=True)
