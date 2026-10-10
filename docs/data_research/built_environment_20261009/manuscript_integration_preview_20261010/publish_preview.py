"""Publish only the integration preview via a separate index; verify LFS bytes."""
import argparse,hashlib,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import quote
import pandas as pd
import requests

BRANCH='analysis/stage7-manuscript-integration-preview-20261010'
PARENT='ecf98c6cbda280914962582a819943fabfa41132'
REPOSITORY='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda:stream.read(2**20),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--state',type=Path,required=True);a=ap.parse_args()
    repo=a.repo.resolve();state=a.state.resolve();state.mkdir(exist_ok=True)
    out=repo/'docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010'
    def call(*args,env=None):return subprocess.check_output(['git','-C',str(repo),*args],env=env)
    base=json.loads((out/'PRESERVATION_BASELINE.json').read_text());qa=json.loads((out/'PRESERVATION_FINAL_QA.json').read_text())
    assert qa['scientific_files_changed_count']==0 and qa['original_862_staged_items_preserved']
    assert hashlib.sha256(call('ls-files','--stage','-z')).hexdigest()==base['logical_index_sha256']
    assert call('rev-parse','HEAD').decode().strip()==base['original_head']
    check=subprocess.run(['git','-C',str(repo),'rev-parse','--verify','refs/heads/'+BRANCH],capture_output=True)
    assert check.returncode!=0,'Inspect existing branch before any update; never overwrite it.'
    manifest=pd.read_csv(out/'OUTPUT_HASHES.csv')
    for _,r in manifest.iterrows():assert sha(out/r.file)==r.sha256
    prefix=out.relative_to(repo).as_posix()+'/'
    paths=[prefix+n for n in manifest.file]+[prefix+'OUTPUT_HASHES.csv']
    required=['STAGE7_CANDIDATE_FREEZE.json','STAGE7_CANDIDATE_LABELS_2291.csv','STAGE7_CLUSTER_PROFILES.csv','STAGE7_OLD_NEW_CROSSWALK.csv',
              'STAGE7_METHODS_DRAFT.md','STAGE7_RESULTS_DRAFT.md','STAGE7_SUPPLEMENTARY_DRAFT.md','STAGE7_DISCUSSION_LIMITATIONS_DRAFT.md','MANUSCRIPT_INTEGRATION_REVIEW.md']
    required += [n+ext for n in ['FIG_STAGE7_TYPOLOGY_MAP','FIG_STAGE7_CLUSTER_PROFILE','FIG_STAGE7_SPATIAL_ROBUSTNESS'] for ext in ['.pdf','.png']]
    assert all(prefix+n in paths for n in required) and len(paths)==len(set(paths))
    env=dict(os.environ,GIT_INDEX_FILE=str(state/'index'))
    subprocess.run(['git','-C',str(repo),'read-tree',PARENT],env=env,check=True)
    pathspec=state/'paths.bin';pathspec.write_bytes(b'\0'.join(p.encode() for p in paths)+b'\0')
    subprocess.run(['git','-C',str(repo),'add','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul'],env=env,check=True)
    whitespace=subprocess.run(['git','-C',str(repo),'diff','--cached','--check',PARENT],env=env,capture_output=True)
    if whitespace.returncode:
        print(whitespace.stdout.decode(errors='replace')[:1600]);raise RuntimeError('Scoped cached diff check failed')
    tree=call('write-tree',env=env).decode().strip()
    changes=call('diff-tree','--no-commit-id','--name-only','-r',PARENT,tree).decode().splitlines()
    assert sorted(paths)==sorted(changes) and all(p.startswith(prefix) for p in changes)
    assert all(not call('ls-tree',PARENT,'--',p).strip() for p in changes)
    lfs=[]
    for path in changes:
        blob=call('show',tree+':'+path)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            lines=blob.decode().splitlines();oid=lines[1].split(':')[-1];size=int(lines[2].split()[1])
            assert sha(repo/path)==oid and (repo/path).stat().st_size==size
            subprocess.run(['git','-C',str(repo),'lfs','pointer','--check','--strict','--stdin'],input=blob,capture_output=True,check=True)
            lfs.append({'file':path,'sha256':oid,'bytes':size})
        else:
            assert (repo/path).read_bytes().replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')
    msg=state/'message.txt';msg.write_text('analysis: freeze Stage7 candidate and manuscript integration preview\n\nReuse exact D equal-domain k4 seed42 labels; add raw-unit profiles, old/new crosswalk, actual-checked vector artwork and qualified section drafts. Preserve four unresolved tracts, formal science, manuscript, figures and original staging. No new clustering or simulation; no promotion.\n',encoding='utf-8')
    commit=call('commit-tree',tree,'-p',PARENT,'-F',str(msg),env=env).decode().strip()
    subprocess.run(['git','-C',str(repo),'update-ref','refs/heads/'+BRANCH,commit,'0'*40],check=True)
    (state/'commit.txt').write_text(commit+'\n');(state/'LFS_POINTERS.json').write_text(json.dumps(lfs,indent=2)+'\n')
    print('COMMIT',commit,'FILES',len(changes),'LFS',len(lfs),flush=True)
    subprocess.run(['git','-C',str(repo),'lfs','fsck','--objects',PARENT+'..'+commit],check=True)
    subprocess.run(['git','-C',str(repo),'push','origin',BRANCH],check=True)
    remote=call('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0];assert remote==commit
    def fetch(rec):
        url='https://media.githubusercontent.com/media/'+REPOSITORY+'/'+commit+'/'+quote(rec['file'],safe='/')
        response=requests.get(url,timeout=(15,90));response.raise_for_status()
        assert not response.content.startswith(b'version https://git-lfs.github.com/spec/v1')
        assert len(response.content)==rec['bytes'] and hashlib.sha256(response.content).hexdigest()==rec['sha256']
        return {**rec,'remote_actual_bytes_verified':True}
    verified=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(fetch,r) for r in lfs]):
            verified.append(future.result());print('REMOTE_BYTES',len(verified),'/',len(lfs),flush=True)
    assert hashlib.sha256(call('ls-files','--stage','-z')).hexdigest()==base['logical_index_sha256']
    assert call('rev-parse','HEAD').decode().strip()==base['original_head']
    assert all(sha(repo/p)==h for p,h in base['protected_files'].items())
    result={'branch':BRANCH,'remote_HEAD':remote,'parent':PARENT,'new_files':len(changes),'new_LFS_objects':len(lfs),
            'all_remote_LFS_payload_SHA256_verified':True,'objects':verified,'original_index_and_HEAD_preserved':True,'scientific_files_changed':0}
    (state/'REMOTE_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('VERIFIED_REMOTE_HEAD',remote,flush=True)

if __name__=='__main__':main()
