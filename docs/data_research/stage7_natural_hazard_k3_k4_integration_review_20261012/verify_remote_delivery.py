"""Verify requested isolated branch and stream every actual LFS payload."""
import time
from urllib.parse import quote
import requests
from common import *

REPO='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'

def main():
    branch=git('branch','--show-current').decode().strip();commit=git('rev-parse','HEAD').decode().strip()
    remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0];assert commit==remote
    prefix=OUT.relative_to(ROOT).as_posix();paths=git('ls-tree','-r','--name-only',commit,'--',prefix).decode().splitlines()
    manifest=json.loads(lp(OUT/'DERIVED_FILE_HASHES.json').read_text())['files']
    for rel,item in manifest.items():assert prefix+'/'+rel in paths and sha(OUT/rel)==item['sha256'],rel
    results=[];texts=0
    for rel in paths:
        blob=git('show',commit+':'+rel);path=lp(ROOT/rel)
        if not blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            assert path.read_bytes()==blob or path.read_bytes().replace(b'\r\n',b'\n')==blob;texts+=1;continue
        fields=dict(row.split(' ',1) for row in blob.decode().splitlines());digest=fields['oid'].split(':')[1];size=int(fields['size'])
        assert sha(path)==digest and path.stat().st_size==size
        url='https://media.githubusercontent.com/media/'+REPO+'/'+commit+'/'+quote(rel,safe='/')
        for attempt in range(3):
            try:
                h=hashlib.sha256();count=0
                with requests.get(url,stream=True,timeout=(20,240)) as response:
                    response.raise_for_status()
                    for part in response.iter_content(1048576):h.update(part);count+=len(part)
                assert h.hexdigest()==digest and count==size
                results.append(dict(file=rel,sha256=digest,bytes=count,actual_payload_verified=True));break
            except Exception:
                if attempt==2:raise
                time.sleep(3*(attempt+1))
        print('ActualLFSbytes PASS',len(results),rel.rsplit('/',1)[-1],flush=True)
    dump('REMOTE_DELIVERY_VERIFICATION.json',dict(review_status=WARN,branch=branch,verified_payload_commit=commit,remote_HEAD_at_verification=remote,git_text_files_verified=texts,actual_LFS_files=len(results),actual_LFS_bytes=sum(r['bytes'] for r in results),all_actual_payload_bytes_verified=True,records=results))
    print('REMOTE DELIVERY PASS',commit,len(results),flush=True)

if __name__=='__main__':main()
