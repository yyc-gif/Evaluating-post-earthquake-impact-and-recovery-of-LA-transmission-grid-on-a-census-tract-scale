"""Verify the pushed package using actual remote LFS payload bytes."""
from common import *
import requests,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import quote
REPO='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'
def verify(item,commit):
    rel,oid,size=item;url='https://media.githubusercontent.com/media/'+REPO+'/'+commit+'/'+quote(rel,safe='/')
    for attempt in range(3):
        try:
            with requests.get(url,stream=True,timeout=(15,90)) as response:
                response.raise_for_status();h=hashlib.sha256();n=0
                for b in response.iter_content(1048576):h.update(b);n+=len(b)
            assert h.hexdigest()==oid and n==size
            return {'file':rel,'sha256':oid,'bytes':n,'actual_remote_bytes_verified':True,'url':url}
        except Exception as exc:
            error=str(exc);time.sleep(2**attempt)
    raise RuntimeError(rel+': '+error)
if __name__=='__main__':
    branch=git('branch','--show-current').decode().strip();commit=git('rev-parse','HEAD').decode().strip()
    remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0];assert remote==commit
    prefix=PKG.relative_to(ROOT).as_posix();paths=git('ls-tree','-r','--name-only',commit,'--',prefix).decode().splitlines()
    manifest=json.load(open(lp(PKG/'OUTPUT_HASHES.json'),encoding='utf-8'))
    assert all(prefix+'/'+rel in paths for rel in manifest)
    for rel,r in manifest.items():assert sha(PKG/rel)==r['sha256'],rel
    items=[];normal=0
    for rel in paths:
        blob=git('show',commit+':'+rel)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            lines=blob.decode().splitlines();oid=lines[1].split(':')[-1];size=int(lines[2].split()[1])
            assert sha(ROOT/rel)==oid;items.append((rel,oid,size))
        else:assert hashlib.sha256(blob).hexdigest()==sha(ROOT/rel);normal+=1
    records=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(verify,item,commit) for item in items]):
            records.append(future.result())
            if len(records)%10==0:print(f'{len(records)}/{len(items)} remote payloads verified',flush=True)
    dump('REMOTE_DELIVERY_VERIFICATION.json',{'branch':branch,'verified_payload_commit':commit,'remote_HEAD_at_verification':remote,
        'LFS_files':len(records),'actual_bytes_downloaded':sum(r['bytes'] for r in records),
        'git_text_files_verified':normal,'all_actual_remote_bytes_verified':True,
        'files':sorted(records,key=lambda r:r['file'])})
    print('Remote verified:',commit,'actual LFS files:',len(records),'bytes:',sum(r['bytes'] for r in records),flush=True)
