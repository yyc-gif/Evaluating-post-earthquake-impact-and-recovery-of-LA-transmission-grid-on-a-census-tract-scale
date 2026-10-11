from controlled_audit import *
import subprocess,concurrent.futures,requests,urllib.parse,re
def test_and_manifest():
 result=subprocess.run([sys.executable,'-m','pytest',str(OUT/'test_controlled_audit.py'),'-q'],cwd=str(WT),capture_output=True,text=True)
 (OUT/'TEST_RESULTS.txt').write_bytes((result.stdout+result.stderr).encode());assert result.returncode==0,result.stdout+result.stderr
 print(result.stdout,flush=True)
def remote():
 shortwt=str(WT).replace('\\\\?\\','');head=subprocess.check_output(['git','-C',shortwt,'rev-parse','HEAD'],text=True).strip();branch=subprocess.check_output(['git','-C',shortwt,'branch','--show-current'],text=True).strip()
 remotehead=subprocess.check_output(['git','-C',shortwt,'ls-remote','origin',f'refs/heads/{branch}'],text=True).split()[0];assert remotehead==head
 rel=str(OUT.relative_to(WT)).replace('\\','/');entries=[]
 for p in OUT.rglob('*'):
  if not p.is_file() or p.name=='REMOTE_VERIFICATION.json' or '__pycache__' in str(p):continue
  path=str(p.relative_to(WT)).replace('\\','/');blob=subprocess.check_output(['git','-C',shortwt,'show',f'{head}:{path}'])
  if blob.startswith(b'version https://git-lfs'):
   oid=re.search(rb'oid sha256:([0-9a-f]{64})',blob)[1].decode();assert sha(p)==oid
   entries.append((path,oid,p.stat().st_size))
 def verify(e):
  path,expected,size=e;url='https://media.githubusercontent.com/media/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/'+head+'/'+urllib.parse.quote(path,safe='/')
  response=requests.get(url,timeout=180);response.raise_for_status();data=response.content
  assert not data.startswith(b'version https://git-lfs') and len(data)==size and hashlib.sha256(data).hexdigest()==expected,path
  return {'file':path,'sha256':expected,'bytes':size,'remote_actual_data_verified':True}
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  verified=list(pool.map(verify,entries))
 jdump('REMOTE_VERIFICATION.json',{'commit':head,'branch':branch,'remote_HEAD':remotehead,'new_LFS_objects_verified':len(verified),'actual_remote_LFS_bytes_verified':sum(r['bytes'] for r in verified),'objects':verified,'verification_record_excluded_from_self_hash':True})
 print('VERIFIED REMOTE',head,len(verified),'LFS objects',sum(r['bytes'] for r in verified),'actual bytes',flush=True)
if __name__=='__main__':
 if '--test' in sys.argv:test_and_manifest()
 if '--remote' in sys.argv:remote()
