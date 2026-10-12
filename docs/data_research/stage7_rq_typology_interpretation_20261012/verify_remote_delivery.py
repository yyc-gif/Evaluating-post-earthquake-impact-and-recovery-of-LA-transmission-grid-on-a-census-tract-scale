"""Verify pushed HEAD, committed bytes and actual remote LFS payloads."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import time
from urllib.parse import quote
import requests
from common import OUT,ROOT,dump,git,lp,sha

REPO='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'


def payload(item):
    rel,oid,size,commit=item
    url='https://media.githubusercontent.com/media/'+REPO+'/'+commit+'/'+quote(rel,safe='/')
    for attempt in range(3):
        try:
            h=hashlib.sha256();n=0
            with requests.get(url,stream=True,timeout=(15,120)) as response:
                response.raise_for_status()
                for b in response.iter_content(1048576):h.update(b);n+=len(b)
            assert h.hexdigest()==oid and n==size,(rel,n,h.hexdigest())
            return dict(file=rel,sha256=oid,bytes=n,actual_payload_bytes_verified=True)
        except Exception:
            if attempt==2:raise
            time.sleep(2**attempt)


def main():
    branch=git('branch','--show-current').decode().strip();commit=git('rev-parse','HEAD').decode().strip()
    remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0]
    assert remote==commit
    prefix=OUT.relative_to(ROOT).as_posix()
    paths=git('ls-tree','-r','--name-only',commit,'--',prefix).decode().splitlines()
    manifest=json.loads(lp(OUT/'DERIVED_FILE_HASHES.json').read_text())
    for name,item in manifest.items():
        assert prefix+'/'+name in paths and sha(OUT/name)==item['sha256']
    lfs=[];text_count=0
    for rel in paths:
        blob=git('show',commit+':'+rel)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            fields=dict(v.split(' ',1) for v in blob.decode().splitlines());oid=fields['oid'].split(':')[1];size=int(fields['size'])
            assert sha(ROOT/rel)==oid and lp(ROOT/rel).stat().st_size==size
            lfs.append((rel,oid,size,commit))
        else:
            assert lp(ROOT/rel).read_bytes().replace(b'\r\n',b'\n')==blob
            text_count+=1
    with ThreadPoolExecutor(max_workers=4) as executor:records=list(executor.map(payload,lfs))
    dump('REMOTE_DELIVERY_VERIFICATION.json',dict(branch=branch,verified_payload_commit=commit,
        remote_HEAD_at_verification=remote,files=len(records),total_actual_LFS_bytes=sum(v['bytes'] for v in records),
        git_text_files_verified=text_count,all_actual_payload_bytes_verified=True,records=sorted(records,key=lambda v:v['file'])))
    print(json.dumps(dict(verified_remote_commit=remote,actual_LFS_payloads=len(records),all_verified=True)),flush=True)


if __name__=='__main__':main()
