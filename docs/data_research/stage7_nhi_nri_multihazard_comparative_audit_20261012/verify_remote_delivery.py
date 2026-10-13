"""Remote HEAD and streamed actual Git LFS bytes, not merely pointer presence."""
import time
from urllib.parse import quote
import requests
from common import *

REPO='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'


def main():
    branch=git('branch','--show-current').decode().strip();commit=git('rev-parse','HEAD').decode().strip()
    remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0];assert remote==commit
    prefix=OUT.relative_to(ROOT).as_posix();paths=git('ls-tree','-r','--name-only',commit,'--',prefix).decode().splitlines()
    manifest=json.loads(lp(OUT/'DERIVED_FILE_HASHES.json').read_text())['files']
    for rel,item in manifest.items():assert prefix+'/'+rel in paths and sha(OUT/rel)==item['sha256'],rel
    records=[];texts=0
    for rel in paths:
        blob=git('show',commit+':'+rel);local=lp(ROOT/rel)
        if not blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            assert local.read_bytes()==blob or local.read_bytes().replace(b'\r\n',b'\n')==blob;texts+=1;continue
        fields=dict(line.split(' ',1) for line in blob.decode().splitlines());oid=fields['oid'].split(':')[1];size=int(fields['size'])
        assert sha(local)==oid and local.stat().st_size==size
        url='https://media.githubusercontent.com/media/'+REPO+'/'+commit+'/'+quote(rel,safe='/')
        for attempt in range(3):
            try:
                h=hashlib.sha256();count=0
                with requests.get(url,stream=True,timeout=(20,240)) as response:
                    response.raise_for_status()
                    for chunk in response.iter_content(1048576):h.update(chunk);count+=len(chunk)
                assert h.hexdigest()==oid and count==size
                records.append(dict(file=rel,sha256=oid,bytes=count,actual_payload_verified=True));break
            except Exception:
                if attempt==2:raise
                time.sleep(3*(attempt+1))
        print('ActualLFSbytes PASS',len(records),rel.rsplit('/',1)[-1],flush=True)
    dump('REMOTE_DELIVERY_VERIFICATION.json',dict(review_status=WARN,branch=branch,verified_payload_commit=commit,remote_HEAD_at_verification=remote,git_text_files_verified=texts,actual_LFS_files=len(records),actual_LFS_bytes=sum(x['bytes'] for x in records),all_actual_payload_bytes_verified=True,records=records))
    print('REMOTE DELIVERY PASS',commit,len(records),flush=True)


if __name__=='__main__':main()
