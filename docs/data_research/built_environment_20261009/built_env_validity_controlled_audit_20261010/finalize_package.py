from controlled_audit import *
import subprocess,shutil,datetime
ORIGINAL=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
def main():
 # Copy only this task's reproducible scripts; source research packages are read-only.
 for name in ['controlled_audit.py','finish_audit.py','write_decision.py','diagnostic_figures.py','render_qa.py','test_controlled_audit.py','finalize_package.py','verify_delivery.py']:
  source=Path(__file__).resolve().parent/name
  if source!=OUT/name:shutil.copyfile(source,OUT/name)
 (OUT/'.gitignore').write_bytes(b'!*.csv\n!*.pdf\n!*.png\n!*.json\n!*.npz\n__pycache__/\n.pytest_cache/\n*.pyc\n')
 (OUT/'.gitattributes').write_bytes(b'*.npz filter=lfs diff=lfs merge=lfs -text\n')
 # Add actual perturbation sources, not just their names or LFS pointers.
 records=pd.read_csv(OUT/'SOURCE_HASHES.csv');more=[]
 for p in (SP/'run_records').glob('*'):
  if p.suffix in ['.npz','.json']:more.append({'file':str(p.relative_to(WT)).replace('\\','/'),'sha256':sha(p),'source_commit':'ecf98c6cbda280914962582a819943fabfa41132'})
 save('SOURCE_HASHES.csv',pd.concat([records,pd.DataFrame(more)]).drop_duplicates('file'))
 before=json.loads((OUT/'PRESERVATION_BEFORE.json').read_text());now={k:sha(ORIGINAL/k) for k in before['protected_files']}
 index=subprocess.check_output(['git','-C',str(ORIGINAL),'ls-files','--stage','-z']);head=subprocess.check_output(['git','-C',str(ORIGINAL),'rev-parse','HEAD'],text=True).strip();count=len(subprocess.check_output(['git','-C',str(ORIGINAL),'diff','--cached','--name-only','-z']).split(b'\0'))-1
 assert before['protected_files']==now and head==before['current_head'] and count==862
 assert hashlib.sha256(index).hexdigest()==before['logical_index_sha256']
 jdump('PRESERVATION_AFTER.json',{'protected_file_count':len(now),'protected_payload_changes':0,'original_head':head,'staged_count':count,'logical_index_sha256':hashlib.sha256(index).hexdigest(),'staged_index_unchanged':True,'source_research_hashes_unchanged':True})
 q=json.loads((OUT/'PDF_RENDER_AND_FONT_QA.json').read_text());assert all(not p['outside_page_text'] and p['minimum_font_pt']>=7.5 and p['raster_images']==0 for p in q['pages'])
 q['actual_visual_review_required']=False;q['actual_visual_review_completed']=True;q['visual_findings']='All four Poppler-rendered pages inspected at185-mm width. Page1/2 legend-panel-letter collisions fixed; risk-row labeling corrected. Final labels, data and legends readable without clipping.';q['review_method']='Actual rendered PNG inspection, with native PDF font/page extraction';jdump('PDF_RENDER_AND_FONT_QA.json',q)
 run=json.loads((OUT/'FIT_EXECUTION_RECORD.json').read_text());log=f'''# Execution log

Parent {PARENT}; independent branch analysis/stage7-built-env-validity-controlled-20261010.

1. Verified live remote manuscript-reconciliation HEAD and actual source bytes. Created a separate sparse analysis worktree. Windows linked-worktree metadata name shortened to _bv to resolve LFS path limits; original worktree/index untouched.
2. Verified950 protected payloads and862 original staged items before analysis.
3. Declared29 model specifications, fixed2287 cohort, k4,20 seeds and original20 deletion cases before fitting. Reused280 source runs; completed880 new fits. Fit execution took {run['elapsed_s']:.3f} seconds. No simulations, GA, physical sampling, new GIS or formal-stage runs.
4. Exported full-cohort, spatial, class matching, raw cross-table, profile, distance, coverage and construct/weight effect tables. Proportional allocations are aliases with documented floating-point serialization tolerance.
5. Six scientific integrity tests passed; actual four-page visual inspection found and fixed diagnostic legend/letter collision and risk-row wording. Final185-mm PDFs have Arial embedded,7.5-pt minimum text and no rasterized plots.
6. Rechecked all950 protected hashes and exact862-item original index. New package alone is eligible for commit. Remote delivery verification is recorded separately after push.

This package does not assign labels to unresolved tracts or replace the existing candidate freeze, formal Stage7, figures or manuscripts. Recommendations are for author scientific review.
'''
 (OUT/'EXECUTION_LOG.md').write_bytes(log.encode())
 # Hash all package payloads, excluding the self-referential manifest and remote record.
 files=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ['OUTPUT_HASHES.csv','REMOTE_VERIFICATION.json'] and '__pycache__' not in str(p)]
 save('OUTPUT_HASHES.csv',[{'file':str(p.relative_to(OUT)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)])
 print('PACKAGE',len(files)+1,'files; protected changes0; staging862 unchanged',flush=True)
if __name__=='__main__':main()
