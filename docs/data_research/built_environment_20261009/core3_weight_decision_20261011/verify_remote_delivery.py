"""Verify committed outputs and download actual LFS payload bytes after push."""
from common import *
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
import requests, time

REPO='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'

def verify(item,commit):
    rel,oid,size=item
    url='https://media.githubusercontent.com/media/'+REPO+'/'+commit+'/'+quote(rel,safe='/')
    error=None
    for attempt in range(3):
        try:
            with requests.get(url,stream=True,timeout=(15,90)) as response:
                response.raise_for_status();h=hashlib.sha256();n=0
                for block in response.iter_content(1048576):h.update(block);n+=len(block)
            assert h.hexdigest()==oid and n==size,(rel,n,h.hexdigest(),oid)
            return dict(file=rel,sha256=oid,bytes=n,url=url,actual_bytes_verified=True)
        except Exception as e:error=str(e);time.sleep(2**attempt)
    raise RuntimeError(rel+': '+error)

if __name__=='__main__':
    branch=git('branch','--show-current').decode().strip();commit=git('rev-parse','HEAD').decode().strip()
    remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0];assert remote==commit
    prefix=OUT.relative_to(ROOT).as_posix()
    paths=git('ls-tree','-r','--name-only',commit,'--',prefix).decode().splitlines()
    manifest=json.loads(lp(OUT/'DERIVED_FILE_HASHES.json').read_text(encoding='utf-8'))
    assert all(prefix+'/'+rel in paths for rel in manifest), 'Manifest output missing from commit'
    items=[];text_verified=0
    for rel in paths:
        blob=git('show',commit+':'+rel)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            lines=blob.decode().splitlines();oid=lines[1].split(':')[-1];size=int(lines[2].split()[1])
            assert sha(ROOT/rel)==oid and lp(ROOT/rel).stat().st_size==size;items.append((rel,oid,size))
        else:
            assert hashlib.sha256(blob).hexdigest()==sha(ROOT/rel),rel
            text_verified+=1
    for rel,r in manifest.items():assert sha(OUT/rel)==r['sha256'] and lp(OUT/rel).stat().st_size==r['bytes'],rel
    records=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(verify,i,commit) for i in items]):records.append(future.result())
    records.sort(key=lambda x:x['file'])
    dump('REMOTE_LFS_BYTE_VERIFICATION.json',dict(branch=branch,verified_payload_commit=commit,remote_HEAD_at_verification=remote,files=len(records),total_actual_bytes=sum(x['bytes'] for x in records),git_text_files_verified=text_verified,all_actual_bytes_verified=True,records=records))
    log(f'Remote HEAD={commit}; {len(records)} actual LFS payloads and {text_verified} Git text files verified.')
