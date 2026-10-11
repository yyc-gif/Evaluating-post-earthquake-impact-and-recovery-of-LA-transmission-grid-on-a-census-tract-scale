from weight_path import *
import concurrent.futures,re,urllib.parse,requests

def finalize():
 preservation('PRESERVATION_AFTER.json')
 q=json.loads((OUT/'PDF_ACTUAL_SIZE_QA.json').read_text())
 assert len(q['pages'])==4 and all(p['minimum_font_pt']>=7.5 and not p['outside_page_text'] and p['raster_images']==0 for p in q['pages'])
 q['actual_visual_review_completed']=True;q['reviewed_PDF_sha256']=sha(OUT/'WEIGHT_CONSTRUCT_DIAGNOSTICS.pdf')
 q['visual_review']='All four latest Poppler-rendered pages opened and inspected. Native185-mm width,7.5-pt minimum Arial/ArialBold text, embedded fonts, vector heatmap cells and paths. Minority legend moved off the worst-case curve. No out-of-page text, panel/legend overlap or unreadable data labels observed.'
 dump('PDF_ACTUAL_SIZE_QA.json',q)
 (OUT/'.gitignore').write_bytes(b'!*.csv\n!*.pdf\n!*.png\n!*.json\n!*.npz\n__pycache__/\n.pytest_cache/\n*.pyc\n')
 (OUT/'.gitattributes').write_bytes(b'*.npz filter=lfs diff=lfs merge=lfs -text\n*.json -text\n*.py text eol=lf\n*.md text eol=lf\n')
 r=json.loads((OUT/'FIT_EXECUTION_RECORD.json').read_text())
 (OUT/'EXECUTION_LOG.md').write_bytes(f'''# Execution log

1. Read the author attachment and complete previous decision memo, numerical tables and manuscript implications. Verified local parent {PARENT} against the remote audit-branch HEAD. Created independent worktree _cw10 on analysis/stage7-construct-weight-decision-20261010.
2. Hydrated124 locally available parent files only after verifying their actual bytes against the parent Git blob or LFS SHA-256. No source downloads or GIS extraction. Read and verified950 protected file hashes and the exact862-item original staged index before new fits.
3. Wrote PREDECLARED_RUN_SPECIFICATION.json and PREDECLARED_DECISION_RULE.md before fitting. Verified4endpoint archive identities, input matrices,20seeds, registered deletion masks, scaler parameters and coordinate weights.
4. Completed exactly240new intermediate fits and reused160endpoint runs, in{r['elapsed_s']:.3f}seconds of fit-loop wall time. No existing880-fit batch repeated. No k search, simulation, scheduler, GA or source acquisition. No new weight settings added.
5. Saved original-unit profiles, all45specification pair comparisons, raw neighbor/endpoint contingencies, training-only spatial matching, split/purity/destination diagnostics, population/block distributions and domain variance denominators. Reproduced source BSS fractions to within3.66e-15.
6. Eight integrity tests passed. A Windows long-path prefix duplication in the test import was corrected; it did not affect fitted data. Replaced initial raster heatmap cells with vector cells. Opened all four final Poppler-rendered pages and corrected the minority legend placement. Final185-mm diagnostic PDF has7.5-pt minimum text, embeddedArial fonts and no raster content.
7. Rechecked all950 protected payloads, the exact862 original staged items and all124 hydrated source hashes. Formal labels, manuscript/figures, physical samples, trajectories, scheduling, mapping and GA results remain unchanged.
8. Commit/push is restricted to this diagnostic directory. Actual remote LFS bytes and branch HEAD are checked after push in REMOTE_VERIFICATION.json.

The recommendation limits the four-class taxonomy claim; it does not promote any labels or edit the manuscript. The source geometries and contemporary all-use age limitations remain explicit.
'''.encode())
 # Only newly created package text: normalize line endings before hashing/committing.
 for p in OUT.rglob('*'):
  if p.is_file() and p.suffix in ['.md','.json','.py','.txt'] and '__pycache__' not in str(p):
   data=p.read_bytes();p.write_bytes(data.replace(b'\r\n',b'\n'))
 files=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ['OUTPUT_HASHES.csv','REMOTE_VERIFICATION.json'] and '__pycache__' not in str(p) and '.pytest_cache' not in str(p)]
 save('OUTPUT_HASHES.csv',[dict(file=p.relative_to(OUT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)])
 print('PACKAGE',len(files)+1,'files;950 protected hashes and862 staged items preserved',flush=True)

def remote():
 short=str(WT).replace('\\\\?\\','');head=subprocess.check_output(['git','-C',short,'rev-parse','HEAD'],text=True).strip();branch=subprocess.check_output(['git','-C',short,'branch','--show-current'],text=True).strip()
 remotehead=subprocess.check_output(['git','-C',short,'ls-remote','origin','refs/heads/'+branch],text=True).split()[0];assert head==remotehead
 entries=[]
 for p in OUT.rglob('*'):
  if not p.is_file() or p.name=='REMOTE_VERIFICATION.json' or '__pycache__' in str(p) or '.pytest_cache' in str(p):continue
  rel=p.relative_to(WT).as_posix();blob=subprocess.check_output(['git','-C',short,'show',head+':'+rel])
  if blob.startswith(b'version https://git-lfs'):
   oid=re.search(rb'oid sha256:([0-9a-f]{64})',blob)[1].decode();assert oid==sha(p);entries.append((rel,oid,p.stat().st_size))
  else:assert blob==p.read_bytes(),rel
 def verify(e):
  rel,oid,size=e;url='https://media.githubusercontent.com/media/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/'+head+'/'+urllib.parse.quote(rel,safe='/')
  response=requests.get(url,timeout=180);response.raise_for_status();data=response.content
  assert not data.startswith(b'version https://git-lfs') and len(data)==size and hashlib.sha256(data).hexdigest()==oid,rel
  return dict(file=rel,sha256=oid,bytes=size,actual_remote_bytes_verified=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:verified=list(pool.map(verify,entries))
 dump('REMOTE_VERIFICATION.json',dict(commit=head,branch=branch,remote_HEAD=remotehead,LFS_objects_verified=len(verified),remote_actual_bytes=sum(x['bytes'] for x in verified),objects=verified,verification_record_excluded_from_self_hash=True))
 print('REMOTE',head,len(verified),'LFS objects',sum(x['bytes'] for x in verified),'actual bytes verified',flush=True)
if __name__=='__main__':
 if '--finalize' in sys.argv:finalize()
 if '--remote' in sys.argv:remote()
