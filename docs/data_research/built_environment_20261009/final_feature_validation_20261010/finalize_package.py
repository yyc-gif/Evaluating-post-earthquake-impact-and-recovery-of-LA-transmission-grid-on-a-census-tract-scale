"""Finalize scoped run evidence and file manifest after actual tests."""
from pathlib import Path
import shutil,json,subprocess,sys
import pandas as pd
from validate_stage7 import ROOT,OUT,sha,dump
HERE=Path(__file__).resolve().parent
def main():
 for p in HERE.glob('*.py'):
  dest=OUT/p.name
  if p.resolve()!=dest.resolve():shutil.copyfile(p,dest)
 # Normalize authored text only. Official source snapshots retain their exact bytes.
 for p in OUT.rglob('*'):
  if not p.is_file() or any(x in p.relative_to(OUT).parts for x in ['sources','checkpoints','original_state','publish_state','__pycache__','.pytest_cache']):continue
  if p.suffix in ['.py','.md','.json','.txt'] or p.name in ['.gitignore','.gitattributes']:
   lines=p.read_text(encoding='utf-8').splitlines();p.write_text('\n'.join(x.rstrip() for x in lines)+'\n',encoding='utf-8',newline='\n')
 # Run the delivered test file, not merely its scratch copy.
 command=[sys.executable,'-m','pytest',str(OUT/'test_final_validation.py'),'-q'];done=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',cwd=ROOT);(OUT/'TEST_RESULTS.txt').write_text(done.stdout+done.stderr,encoding='utf-8',newline='\n');assert done.returncode==0,done.stdout+done.stderr
 print(done.stdout,flush=True);dump('VERIFICATION_RESULTS.json',{'focused_tests_passed':8,'test_returncode':done.returncode,'test_file':'test_final_validation.py','checks':'exact tract identities/nulls; corrected mask and union arithmetic; entropy scenario bounds; age bounds; original1000-realization B and AUC; run/weight accounting; independent silhouette and ARI; spatial/profile accounting'})
 q=json.loads((OUT/'CLUSTER_EXECUTION_QA.json').read_text());q['spatial_replicates_per_model']=20;q['spatial_total_fits']=80;q['seconds_definition']='Elapsed postprocessing and20 initial spatial fits in resumed invocation; per-run elapsed times retain original worker timings. This value is not total historical batch wall time.';dump('CLUSTER_EXECUTION_QA.json',q)
 records=pd.read_csv(OUT/'CONTROLLED_CLUSTERING_COMPARISON.csv');save=pd.DataFrame([{'model':name,'recorded_fit_wall_seconds_sum':g.elapsed_s.sum(),'n_distinct_model_seed_k_fits':len(g),'timing_note':'sum of fit timings across parallel workers, not elapsed batch wall time'} for name,g in records.groupby('model')]);save.to_csv(OUT/'COMPUTATION_RECORD_ACCOUNTING.csv',index=False)
 (OUT/'EXECUTION_LOG.md').write_text('''# Execution log — 2026-10-10

- Read the complete attached task and pinned source branches. Inspected the existing manuscript checkout: HEAD031d2c675f8e7d58035d27448be040b809ced086, 862 prior staged paths. Saved the unchanged index and protection inventory without switching or cleaning that checkout.
- Fetched/read independent gatebd913b91c9c73d0b92fa327c28660d74197b6259, which inherits FEMA audit65f388f9710566ffa845808bd7b10503de4da608. Reused existing SCAG/LARIAC/recovery sources.
- Retrieved exactly18 official2020 tract boundary records for water-definition comparison. Independently remeasured projected and geodesic polygons and cached water overlays. Disposed4 corrected,8 explained source-definition/version cases,6 unresolved (4 residential).
- Re-scanned all2,406,373 existing compressed SCAG records for the four corrected local polygons; obtained4,300 relevant unique geometries. Read only spatial subsets of local LARIAC2014/2020 geodatabases. No large data source was downloaded again. Existing extraction files stayed byte-identical.
- Calculated classified entropy, three hypothetical missing-area scenarios, unconstrained entropy allocation bounds, rank shifts, observed2014 age bounds and by-use missingness. Produced2291-row null-preserving matrix,2287 current complete cases, and2276 legacy comparison.
- Predeclared20 model configurations,20 seeds42–61, n_init100, every k2–8. Saved2800 unique fit observations, full labels and numerical definitions. Completed paired spatial block sensitivity for D/EAL under both parent-domain budgets,20 deletion sets each (80 fits).
- Six bounded workers were used for independent fits. A first purely administrative snapshot attempt assumed .git was a directory; corrected it to Git's linked-worktree index path before any index mutation. One output filename exceeded Windows path length; shortened that diagnostic model's filename and completed only its unsaved fit batch. The other19 complete model checkpoints were reused. A loky core-discovery warning was resolved by explicitly declaring the single-core worker budget. No scientific model or random physical inputs changed.
- Ran eight independent numerical tests on the delivered scripts. Verified950 protected file hashes and2008 frozen numerical/GIS/trajectory source hashes. Logical original index, original branch and original HEAD remain unchanged.
- Publication uses a separate analysis branch and alternate index, never broad staging of the manuscript checkout. Remote HEAD and newly added LFS objects are checked after push.

Reproduction is documented in README.md. Scientific readiness remains provisional: four residential river-mask cases, incomplete classified land and nonrandom age missingness are unresolved. Seed stability does not remove construct/weight/spatial sensitivity.
''',encoding='utf-8',newline='\n')
 files=[]
 for p in sorted(OUT.rglob('*')):
  if not p.is_file() or p.name=='DELIVERY_FILE_MANIFEST.csv' or any(x in p.relative_to(OUT).parts for x in ['checkpoints','original_state','publish_state','__pycache__','.pytest_cache']):continue
  files.append({'file':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'status':'NEW_EXPLORATORY_ANALYSIS_ONLY'})
 pd.DataFrame(files).to_csv(OUT/'DELIVERY_FILE_MANIFEST.csv',index=False);print('DELIVERY_MANIFEST',len(files),flush=True)
if __name__=='__main__':main()
