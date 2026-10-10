"""Scoped separate research branch, unchanged original index; remote LFS read-back."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import quote
import os,json,subprocess,hashlib,requests
from spatial_k4 import ROOT,OUT,PARENT,git,sha,dump
BRANCH='analysis/stage7-k4-spatial-validation-20261010'
REPO='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'
def call(*args,env=None):return subprocess.check_output(['git','-C',str(ROOT),*args],env=env)
def objects(ref):
 out={}
 for row in call('ls-tree','-r','-z',ref).split(b'\0'):
  if row:
   meta,p=row.split(b'\t',1);out[p.decode()]=meta.split()[-1]
 return out
def publish():
 base=json.loads((OUT/'PRESERVATION_BASELINE.json').read_text());check=json.loads((OUT/'PRESERVATION_FINAL_QA.json').read_text());tests=json.loads((OUT/'TEST_RESULTS.json').read_text());assert check['scientific_files_changed']==0 and tests['passed']==9 and tests['returncode']==0
 original=(OUT/'original_state/index.bin').read_bytes();assert git('ls-files','--stage','-z')==original and git('rev-parse','HEAD').decode().strip()==base['head']
 prefix=OUT.relative_to(ROOT).as_posix()+'/'
 paths=[p.decode() for p in git('ls-files','--others','--exclude-standard','-z','--',prefix).split(b'\0') if p];assert paths and all(p.startswith(prefix) for p in paths)
 required=['INPUT_AND_BASELINE_QA.json','SPATIAL_K4_RUNS.csv','SPATIAL_K4_TRACT_PREDICTIONS.csv','SPATIAL_K4_CLUSTER_MATCHING.csv','SPATIAL_K4_PROFILE_STABILITY.csv','SMALL_CLUSTER_34_AUDIT.csv','SPATIAL_K4_MODEL_SUMMARY.json','STAGE7_K4_DECISION_NOTE.md']
 assert all(prefix+n in paths for n in required),'Required delivery file ignored or missing'
 assert len([p for p in paths if '/run_records/' in p and p.endswith('.npz')])==40 and len([p for p in paths if '/run_records/' in p and p.endswith('.json')])==40
 assert not any('/original_state/' in p or '/publish_state/' in p for p in paths)
 state=OUT/'publish_state';state.mkdir(exist_ok=True);env=dict(os.environ,GIT_INDEX_FILE=str(state/'index'));subprocess.run(['git','-C',str(ROOT),'read-tree',PARENT],env=env,check=True)
 spec=state/'paths.bin';spec.write_bytes(b'\0'.join(p.encode() for p in paths)+b'\0');subprocess.run(['git','-C',str(ROOT),'add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],env=env,check=True)
 subprocess.run(['git','-C',str(ROOT),'diff','--cached','--check',PARENT],env=env,check=True);tree=call('write-tree',env=env).decode().strip();before=objects(PARENT);after=objects(tree);changes=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)];assert all(p.startswith(prefix) for p in changes) and not any(p in before for p in changes)
 lfs=[]
 for p in changes:
  blob=call('show',tree+':'+p)
  if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
   lines=blob.decode().splitlines();oid=lines[1].split(':')[-1];size=int(lines[2].split()[1]);assert sha(ROOT/p)==oid and (ROOT/p).stat().st_size==size
   subprocess.run(['git','-C',str(ROOT),'lfs','pointer','--check','--strict','--stdin'],input=blob,capture_output=True,check=True);lfs.append(dict(path=p,sha256=oid,bytes=size))
 (state/'LFS_POINTER_VERIFICATION.json').write_text(json.dumps(lfs,indent=2)+'\n',encoding='utf-8')
 exists=subprocess.run(['git','-C',str(ROOT),'rev-parse','--verify','refs/heads/'+BRANCH],capture_output=True);assert exists.returncode!=0,'Existing branch must be inspected, not overwritten'
 msg=state/'message.txt';msg.write_text('analysis: validate fixed-k4 Stage7 spatial stability\n\nReuse saved equal-domain D/EAL k4 baselines and the prescribed20 spatial deletions. Add40 perturbation fits, train-only class matching, minority-group/profile audits and saved model parameters. Preserve formal Stage7, physical results, manuscripts, figures and existing staging.\n',encoding='utf-8')
 commit=call('commit-tree',tree,'-p',PARENT,'-F',str(msg),env=env).decode().strip();subprocess.run(['git','-C',str(ROOT),'update-ref','refs/heads/'+BRANCH,commit,'0'*40],check=True)
 (state/'commit.txt').write_text(commit+'\n');print('COMMIT',commit,'FILES',len(changes),'LFS',len(lfs),flush=True)
 subprocess.run(['git','-C',str(ROOT),'lfs','fsck','--objects',PARENT+'..'+commit],check=True)
 subprocess.run(['git','-C',str(ROOT),'push','origin',BRANCH],check=True)
 remote=call('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0];assert remote==commit
 def fetch(rec):
  url='https://media.githubusercontent.com/media/'+REPO+'/'+commit+'/'+quote(rec['path'],safe='/');response=requests.get(url,timeout=(15,90));response.raise_for_status();assert len(response.content)==rec['bytes'] and hashlib.sha256(response.content).hexdigest()==rec['sha256'];assert not response.content.startswith(b'version https://git-lfs.github.com/spec/v1');return {**rec,'remote_actual_bytes_verified':True}
 verified=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for future in as_completed([pool.submit(fetch,rec) for rec in lfs]):verified.append(future.result());print('REMOTE_LFS_BYTES',len(verified),'/',len(lfs),flush=True)
 assert git('ls-files','--stage','-z')==original and git('rev-parse','HEAD').decode().strip()==base['head'] and all(sha(ROOT/p)==h for p,h in base['protected_files'].items())
 result=dict(branch=BRANCH,remote_HEAD=remote,parent=PARENT,new_files=len(changes),new_lfs_objects=len(lfs),all_new_lfs_actual_bytes_sha256_verified=True,objects=verified,original_index_and_HEAD_unchanged=True,protected_files_changed=0)
 (state/'REMOTE_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('REMOTE_VERIFIED',remote,'LFS_ACTUAL_BYTES',len(lfs),flush=True)
if __name__=='__main__':publish()
