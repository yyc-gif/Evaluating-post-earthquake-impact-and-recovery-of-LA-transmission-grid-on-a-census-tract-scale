"""Publish only this isolated extraction with an alternate Git index."""
from pathlib import Path
import os,json,subprocess,hashlib
from source_audit import ROOT,OUT,git,sha,dump
BASE='031d2c675f8e7d58035d27448be040b809ced086';BRANCH='analysis/stage7-local-joint-features-20261009';state=OUT/'publish_state';state.mkdir(exist_ok=True)
def cmd(*args,env=None):return subprocess.check_output(['git','-C',str(ROOT),*args],env=env)
def objects(ref):
 out={}
 for item in cmd('ls-tree','-r','-z',ref).split(b'\0'):
  if item:
   head,path=item.split(b'\t',1);out[path.decode()]=head.split()[-1]
 return out
def main():
 assert cmd('rev-parse','HEAD').decode().strip()==BASE
 original=(OUT/'ORIGINAL_STAGING.bin').read_bytes();assert cmd('ls-files','--stage','-z')==original
 q=json.loads((OUT/'PRESERVATION_FINAL_QA.json').read_text(encoding='utf-8'));assert q['scientific_files_changed']==0 and q['original_staging_unchanged']
 # A scoped prospective file list respects the new local ignore file.
 untracked=cmd('ls-files','--others','--exclude-standard','-z','--',OUT.relative_to(ROOT).as_posix())
 paths=[s.decode() for s in untracked.split(b'\0') if s]
 assert paths and all(s.startswith(OUT.relative_to(ROOT).as_posix()+'/') for s in paths)
 assert not any(s.endswith(('.zip','.gpkg','.bin')) or 'scag_la_chunks/' in s or 'publish_state/' in s for s in paths)
 source=objects(BASE);index=state/'index';env=dict(os.environ,GIT_INDEX_FILE=str(index));subprocess.run(['git','-C',str(ROOT),'read-tree',BASE],env=env,check=True)
 spec=state/'paths.bin';spec.write_bytes(b'\0'.join(s.encode() for s in paths)+b'\0')
 subprocess.run(['git','-C',str(ROOT),'add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],env=env,check=True)
 check=subprocess.run(['git','-C',str(ROOT),'diff','--cached','--check',BASE],env=env,capture_output=True,text=True,encoding="utf-8",errors="replace");assert check.returncode==0,check.stdout+check.stderr
 changed=cmd('diff','--cached','--name-only',BASE,env=env).decode().splitlines();assert set(changed)==set(paths)
 tree=cmd('write-tree',env=env).decode().strip();proposed=objects(tree)
 protected=json.loads((OUT/'PRESERVATION_BASELINE.json').read_text(encoding='utf-8'))['protected_files'];assert all(source.get(s)==proposed.get(s) for s in protected)
 outside=[s for s in set(source)|set(proposed) if source.get(s)!=proposed.get(s) and s not in paths];assert not outside
 # Verify every new LFS pointer identifies the exact local content.
 lfs=[]
 for s in paths:
  blob=cmd('show',tree+':'+s)
  if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
   lines=blob.decode().splitlines();oid=lines[1].removeprefix('oid sha256:');size=int(lines[2].removeprefix('size '))
   assert sha(ROOT/s)==oid and (ROOT/s).stat().st_size==size
   subprocess.run(['git','-C',str(ROOT),'lfs','pointer','--check','--strict','--stdin'],input=blob,check=True,capture_output=True)
   lfs.append({'path':s,'sha256':oid,'bytes':size})
  elif s.startswith(OUT.relative_to(ROOT).as_posix()+'/sources/'):
   assert blob==(ROOT/s).read_bytes(),'Raw source snapshot bytes changed in Git'
 (state/'LFS_POINTER_VERIFICATION.json').write_text(json.dumps(lfs,indent=2)+'\n')
 message=state/'message.txt';message.write_text('analysis: align count-density provenance and verification\n\nKeep the candidate matrix unchanged and retain geometry-denominator diagnostics; preserve all formal scientific files.\n',encoding='utf-8')
 prior=subprocess.run(['git','-C',str(ROOT),'rev-parse','--verify','refs/heads/'+BRANCH],capture_output=True)
 parent=prior.stdout.decode().strip() if prior.returncode==0 else BASE
 if parent!=BASE:
  previous=objects(parent)
  assert not [k for k in set(source)|set(previous) if source.get(k)!=previous.get(k) and not k.startswith(OUT.relative_to(ROOT).as_posix()+'/')],'Existing research branch has unrelated changes'
 commit=cmd('commit-tree',tree,'-p',parent,'-F',str(message),env=env).decode().strip()
 assert cmd('ls-files','--stage','-z')==original
 # Only create a new branch; never replace an existing ref.
 subprocess.run(['git','-C',str(ROOT),'update-ref','refs/heads/'+BRANCH,commit,parent if prior.returncode==0 else '0'*40],check=True)
 (state/'commit.txt').write_text(commit+'\n')
 print('COMMIT',commit,'FILES',len(paths),'LFS',len(lfs),'ORIGINAL_INDEX_UNCHANGED',flush=True)
 subprocess.run(['git','-C',str(ROOT),'lfs','fsck','--objects',BASE+'..'+commit],check=True)
 subprocess.run(['git','-C',str(ROOT),'push','origin',BRANCH],check=True)
 remote=cmd('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0];assert remote==commit
 assert cmd('ls-files','--stage','-z')==original and cmd('rev-parse','HEAD').decode().strip()==BASE
 (state/'REMOTE_VERIFICATION.json').write_text(json.dumps({'branch':BRANCH,'local_commit':commit,'remote_commit':remote,'original_branch_and_index_unchanged':True,'new_lfs_pointers_verified':len(lfs),'published_file_count':len(paths)},indent=2)+'\n')
 print('REMOTE_VERIFIED',remote,flush=True)
if __name__=='__main__':main()
