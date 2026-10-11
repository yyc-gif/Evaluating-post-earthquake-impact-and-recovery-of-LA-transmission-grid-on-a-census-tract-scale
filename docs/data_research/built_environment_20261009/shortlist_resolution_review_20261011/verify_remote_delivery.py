"""Download every newly uploaded LFS payload and verify actual bytes."""
from common import *
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import quote
import requests,time

REPO='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'

def verify(item,commit):
    rel,oid,size=item;url='https://media.githubusercontent.com/media/'+REPO+'/'+commit+'/'+quote(rel,safe='/');error=None
    for attempt in range(3):
        try:
            r=requests.get(url,stream=True,timeout=(15,90));r.raise_for_status();h=hashlib.sha256();n=0
            for b in r.iter_content(1024*1024):h.update(b);n+=len(b)
            assert h.hexdigest()==oid and n==size,(rel,n,h.hexdigest(),oid)
            return dict(file=rel,sha256=oid,bytes=n,url=url,actual_bytes_verified=True)
        except Exception as e:error=str(e);time.sleep(2**attempt)
    raise RuntimeError(rel+': '+error)

if __name__=='__main__':
    branch=git('branch','--show-current').decode().strip();commit=git('rev-parse','HEAD').decode().strip();remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0];assert remote==commit
    prefix=OUT.relative_to(ROOT).as_posix();paths=git('ls-tree','-r','--name-only',commit,'--',prefix).decode().splitlines();items=[]
    for rel in paths:
        blob=git('show',commit+':'+rel)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            lines=blob.decode().splitlines();oid=lines[1].split(':')[-1];size=int(lines[2].split()[1]);assert sha(ROOT/rel)==oid and lp(ROOT/rel).stat().st_size==size;items.append((rel,oid,size))
    records=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(verify,i,commit) for i in items]
        for future in as_completed(futures):records.append(future.result())
    records.sort(key=lambda x:x['file']);dump('REMOTE_LFS_BYTE_VERIFICATION.json',dict(branch=branch,verified_payload_commit=commit,remote_HEAD_at_verification=remote,files=len(records),total_actual_bytes=sum(x['bytes'] for x in records),all_actual_bytes_verified=True,records=records))
    log(f'Remote HEAD={commit}; {len(records)} actual LFS payloads, {sum(x["bytes"] for x in records)} bytes verified.')
