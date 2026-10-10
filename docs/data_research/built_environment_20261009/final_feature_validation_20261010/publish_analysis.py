"""Scoped separate-branch publication using an isolated index; no checkout."""
from pathlib import Path
import os,json,hashlib,subprocess
from validate_stage7 import ROOT,OUT,BASE,PARENT,SCIENCE,git,sha,dump
BRANCH='analysis/stage7-final-feature-validation-20261010'
def call(*args,env=None):return subprocess.check_output(['git','-C',str(ROOT),*args],env=env)
def objects(ref):
 d={}
 for row in call('ls-tree','-r','-z',ref).split(b'\0'):
  if row:
   meta,p=row.split(b'\t',1);d[p.decode()]=meta.split()[-1]
 return d
def publish():
 baseline=json.loads((OUT/'PRESERVATION_BASELINE.json').read_text());q=json.loads((OUT/'PRESERVATION_FINAL_QA.json').read_text());tests=json.loads((OUT/'VERIFICATION_RESULTS.json').read_text());assert q['scientific_files_changed']==0 and tests['focused_tests_passed']==8
 original=(OUT/'original_state/index.bin').read_bytes();assert git('ls-files','--stage','-z')==original and git('rev-parse','HEAD').decode().strip()==SCIENCE
 parent=objects(PARENT);formal=objects(SCIENCE);bprefix=BASE.relative_to(ROOT).as_posix()+'/'
 inherited_extra={'.github/workflows/stage7-physical-feature-gate.yml'}
 assert not [p for p in set(parent)|set(formal) if parent.get(p)!=formal.get(p) and not p.startswith(bprefix) and p not in inherited_extra]
 assert all(p not in formal for p in inherited_extra)
 prefix=OUT.relative_to(ROOT).as_posix()+'/';paths=[p.decode() for p in git('ls-files','--others','--exclude-standard','-z','--',prefix).split(b'\0') if p]
 assert paths and all(p.startswith(prefix) for p in paths) and not any('/original_state/' in p or '/checkpoints/' in p or '/publish_state/' in p for p in paths)
 for n in ['LANDMASK_18_TRACT_RESOLUTION.csv','SCAG_ENTROPY_SENSITIVITY.csv','BUILDING_AGE_SENSITIVITY.csv','FINAL_CANDIDATE_FEATURE_MATRIX.csv','CONTROLLED_CLUSTERING_COMPARISON.csv','CLUSTER_STABILITY_AND_PROFILES.csv','STAGE7_FEATURE_DECISION_PACKET.md','validate_stage7.py','controlled_clustering.py','test_final_validation.py']:assert prefix+n in paths,n
 records=[p for p in paths if '/run_records/' in p and p.endswith('.npz')];assert len(records)==20
 state=OUT/'publish_state';state.mkdir(exist_ok=True);env=dict(os.environ,GIT_INDEX_FILE=str(state/'index'));subprocess.run(['git','-C',str(ROOT),'read-tree',PARENT],env=env,check=True)
 spec=state/'paths.bin';spec.write_bytes(b'\0'.join(p.encode() for p in paths)+b'\0');subprocess.run(['git','-C',str(ROOT),'add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],env=env,check=True)
 subprocess.run(['git','-C',str(ROOT),'diff','--cached','--check',PARENT],env=env,check=True);tree=call('write-tree',env=env).decode().strip();proposed=objects(tree);assert not [p for p in set(parent)|set(proposed) if parent.get(p)!=proposed.get(p) and not p.startswith(prefix)]
 lfs=[]
 for p in paths:
  blob=call('show',tree+':'+p)
  if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
   lines=blob.decode().splitlines();oid=lines[1].removeprefix('oid sha256:');size=int(lines[2].removeprefix('size '));assert sha(ROOT/p)==oid and (ROOT/p).stat().st_size==size
   subprocess.run(['git','-C',str(ROOT),'lfs','pointer','--check','--strict','--stdin'],input=blob,capture_output=True,check=True);lfs.append({'path':p,'sha256':oid,'bytes':size})
  elif '/sources/' in p:assert blob==(ROOT/p).read_bytes()
 (state/'LFS_POINTER_VERIFICATION.json').write_text(json.dumps(lfs,indent=2)+'\n',encoding='utf-8');message=state/'message.txt';message.write_text('analysis: validate Stage7 features and controlled joint clustering\n\nResolve individual landmask cases, quantify entropy and age uncertainty, and compare candidate constructs with20 seeds and fixed domain budgets. Exploratory only; retain formal Stage7, physical data, GA, manuscripts, figures and prior staging.\n',encoding='utf-8')
 exists=subprocess.run(['git','-C',str(ROOT),'rev-parse','--verify','refs/heads/'+BRANCH],capture_output=True);assert exists.returncode!=0,'Existing branch requires inspection; do not overwrite'
 commit=call('commit-tree',tree,'-p',PARENT,'-F',str(message),env=env).decode().strip();assert git('ls-files','--stage','-z')==original;subprocess.run(['git','-C',str(ROOT),'update-ref','refs/heads/'+BRANCH,commit,'0'*40],check=True);(state/'commit.txt').write_text(commit+'\n')
 print('COMMIT',commit,'FILES',len(paths),'LFS',len(lfs),flush=True);subprocess.run(['git','-C',str(ROOT),'lfs','fsck','--objects',PARENT+'..'+commit],check=True);subprocess.run(['git','-C',str(ROOT),'push','origin',BRANCH],check=True)
 remote=call('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0];assert remote==commit and git('ls-files','--stage','-z')==original and git('rev-parse','HEAD').decode().strip()==SCIENCE
 (state/'REMOTE_VERIFICATION.json').write_text(json.dumps({'branch':BRANCH,'remote_HEAD':remote,'local_commit':commit,'parent':PARENT,'original_checkout_unchanged':True,'new_files':len(paths),'new_lfs':len(lfs)},indent=2)+'\n',encoding='utf-8');print('REMOTE_VERIFIED',remote,flush=True)
if __name__=='__main__':publish()
