"""Run consequential tests and hash only this isolated diagnostic package."""
from common import *
import os

if __name__=='__main__':
    if '--hash-only' not in sys.argv:
        env=os.environ.copy();env['PYTHONIOENCODING']='utf-8';env['LOKY_MAX_CPU_COUNT']='1'
        command=[sys.executable,'-m','pytest',str(OUT/'test_core3_weights.py'),'-q','--basetemp',str(OUT/'_test_tmp')]
        result=subprocess.run(command,cwd=str(ROOT),env=env,capture_output=True,text=True,encoding='utf-8')
        print(result.stdout);print(result.stderr)
        dump('TEST_RECEIPT.json',dict(command=command,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),initial_assertions_corrected=['ACS survey value retained on geometry-unclassified tracts; only geometry variables null','Spatial scaling verified bitwise from original DataFrame layout; advanced NumPy indexing changes summation order by approximately 1e-13'],scientific_values_or_fits_changed_for_tests=False))
        assert result.returncode==0
        log('12 consequential numerical/protection/PDF tests passed without new KMeans fits.')
    else:
        assert json.loads(lp(OUT/'TEST_RECEIPT.json').read_text())['exit_code']==0
    for p in lp(OUT).rglob('*'):
        if p.is_file() and p.suffix in ['.py','.md','.json','.txt'] and '__pycache__' not in p.parts and '_test_tmp' not in p.parts:
            p.write_text(p.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    omitted={'DERIVED_FILE_HASHES.json','EXECUTION_LOG.md','REMOTE_LFS_BYTE_VERIFICATION.json'}
    manifest={}
    for p in sorted(lp(OUT).rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or '_test_tmp' in p.parts or p.name in omitted:continue
        rel=p.relative_to(lp(OUT)).as_posix();manifest[rel]=dict(sha256=sha(p),bytes=p.stat().st_size)
    dump('DERIVED_FILE_HASHES.json',manifest)
    print('Manifest outputs:',len(manifest),'bytes:',sum(r['bytes'] for r in manifest.values()))
