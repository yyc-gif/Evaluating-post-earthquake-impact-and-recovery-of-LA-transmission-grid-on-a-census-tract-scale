"""Publish only the new validated FEMA audit, preserving the original index."""
from pathlib import Path
import os,json,subprocess,hashlib
from run_nri_audit import ROOT,OUT,BASE,git,sha,dump
PARENT='e90186e62103b2dfe1d8bb7e09c07cae15476497'
BRANCH='analysis/stage7-nri-eal-redundancy-20261009'
def cmd(*args,env=None):return subprocess.check_output(['git','-C',str(ROOT),*args],env=env)
def tree_objects(ref):
 result={}
 for record in cmd('ls-tree','-r','-z',ref).split(b'\0'):
  if record:
   meta,path=record.split(b'\t',1);result[path.decode()]=meta.split()[-1]
 return result

def main():
 assert cmd('rev-parse','HEAD').decode().strip()==BASE
 original=(OUT/'ORIGINAL_STAGING.bin').read_bytes();assert cmd('ls-files','--stage','-z')==original
 q=json.loads((OUT/'PRESERVATION_FINAL_QA.json').read_text(encoding='utf-8'));assert q['scientific_files_changed']==0 and q['original_index_unchanged']
 tests=json.loads((OUT/'VERIFICATION_RESULTS.json').read_text(encoding='utf-8'));assert tests['focused_tests_passed']==8
 state=OUT/'publish_state';state.mkdir(exist_ok=True);prefix=OUT.relative_to(ROOT).as_posix()+'/'
 paths=[s.decode() for s in cmd('ls-files','--others','--exclude-standard','-z','--',prefix).split(b'\0') if s]
 assert paths and all(s.startswith(prefix) for s in paths) and not any('publish_state/' in s or s.endswith('.bin') for s in paths)
 # Inherit the earlier separately reviewed feature extraction, unchanged, so its exact read-only inputs are available on this branch.
 source=tree_objects(PARENT);baseline=tree_objects(BASE);assert not [s for s in set(source)|set(baseline) if source.get(s)!=baseline.get(s) and not s.startswith('docs/data_research/built_environment_20261009/local_joint_feature_extraction_20261009/')]
 env=dict(os.environ,GIT_INDEX_FILE=str(state/'index'));subprocess.run(['git','-C',str(ROOT),'read-tree',PARENT],env=env,check=True)
 spec=state/'paths.bin';spec.write_bytes(b'\0'.join(s.encode() for s in paths)+b'\0');subprocess.run(['git','-C',str(ROOT),'add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],env=env,check=True)
 subprocess.run(['git','-C',str(ROOT),'diff','--cached','--check',PARENT],env=env,check=True)
 tree=cmd('write-tree',env=env).decode().strip();proposed=tree_objects(tree);assert not [s for s in set(source)|set(proposed) if source.get(s)!=proposed.get(s) and not s.startswith(prefix)]
 lfs=[]
 for s in paths:
  blob=cmd('show',tree+':'+s)
  if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
   lines=blob.decode().splitlines();oid=lines[1].removeprefix('oid sha256:');size=int(lines[2].removeprefix('size '));assert sha(ROOT/s)==oid and (ROOT/s).stat().st_size==size
   subprocess.run(['git','-C',str(ROOT),'lfs','pointer','--check','--strict','--stdin'],input=blob,check=True,capture_output=True);lfs.append({'path':s,'sha256':oid,'bytes':size})
  elif s.startswith(prefix+'sources/'):assert blob==(ROOT/s).read_bytes()
 (state/'LFS_POINTER_VERIFICATION.json').write_text(json.dumps(lfs,indent=2)+'\n',encoding='utf-8')
 prior=subprocess.run(['git','-C',str(ROOT),'rev-parse','--verify','refs/heads/'+BRANCH],capture_output=True);assert prior.returncode!=0,'Branch already exists; inspect rather than overwrite it'
 message=state/'message.txt';message.write_text('analysis: audit multi-hazard EAL, exposure and social redundancy\n\nControlled exploratory Stage7 comparisons only; preserve formal results, existing figures, physical-form sources and original staging.\n',encoding='utf-8')
 commit=cmd('commit-tree',tree,'-p',PARENT,'-F',str(message),env=env).decode().strip();assert cmd('ls-files','--stage','-z')==original
 subprocess.run(['git','-C',str(ROOT),'update-ref','refs/heads/'+BRANCH,commit,'0'*40],check=True);(state/'commit.txt').write_text(commit+'\n')
 print('COMMIT',commit,'NEW_FILES',len(paths),'NEW_LFS',len(lfs),flush=True)
 subprocess.run(['git','-C',str(ROOT),'lfs','fsck','--objects',PARENT+'..'+commit],check=True);subprocess.run(['git','-C',str(ROOT),'push','origin',BRANCH],check=True)
 remote=cmd('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0];assert remote==commit and cmd('ls-files','--stage','-z')==original and cmd('rev-parse','HEAD').decode().strip()==BASE
 (state/'REMOTE_VERIFICATION.json').write_text(json.dumps({'branch':BRANCH,'parent_feature_extraction':PARENT,'local_commit':commit,'remote_commit':remote,'original_branch_and_index_unchanged':True,'new_lfs_pointers_verified':len(lfs),'new_published_file_count':len(paths)},indent=2)+'\n',encoding='utf-8');print('REMOTE_VERIFIED',remote,flush=True)
if __name__=='__main__':main()
