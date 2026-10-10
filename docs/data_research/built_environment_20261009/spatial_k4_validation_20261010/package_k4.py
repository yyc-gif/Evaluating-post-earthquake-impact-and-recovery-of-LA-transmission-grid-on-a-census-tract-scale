"""Copy only new analysis scripts and run tests on the delivered copies."""
from pathlib import Path
import shutil,subprocess,json,hashlib
from spatial_k4 import OUT,dump,sha
def package():
 here=Path(__file__).parent
 for name in ['spatial_k4.py','finish_k4.py','test_spatial_k4.py','publish_k4.py','package_k4.py']:shutil.copyfile(here/name,OUT/name)
 result=subprocess.run([r'C:\Users\yinch\anaconda3\python.exe','-m','pytest',str(OUT/'test_spatial_k4.py'),'-q','-p','no:cacheprovider'],capture_output=True,text=True,encoding='utf-8')
 (OUT/'TEST_OUTPUT.txt').write_text(result.stdout+result.stderr,encoding='utf-8',newline='\n');assert result.returncode==0 and '9 passed' in result.stdout
 dump('TEST_RESULTS.json',dict(returncode=result.returncode,passed=9,test_source='delivered test_spatial_k4.py',checks='saved-model prediction/inertia reconstruction; unchanged inputs/baselines; domain budgets; training-only optimal matching; no-support handling; raw cross-tables/ARI; profile decomposition; small-group and GEOID accounting; protected files/index',extra_KMeans_fits=0))
 manifest=[dict(file=p.relative_to(OUT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in OUT.rglob('*') if p.is_file() and not any(part in ['original_state','publish_state','__pycache__','.pytest_cache'] for part in p.relative_to(OUT).parts) and p.name!='DELIVERY_FILE_MANIFEST.json']
 dump('DELIVERY_FILE_MANIFEST.json',dict(files=manifest,all_analysis_files_in_requested_directory=True,formal_files_written=0))
 print(result.stdout.strip());print('PACKAGED',len(manifest)+1,'files',flush=True)
if __name__=='__main__':package()
