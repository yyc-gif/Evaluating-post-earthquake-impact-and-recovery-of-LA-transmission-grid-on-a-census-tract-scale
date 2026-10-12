"""Verify this package's remote commit and actual LFS bytes after pushing."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import time
from urllib.parse import quote

import requests

from audit import OUT, ROOT, dump, git, longpath, sha

REPO='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'


def download_verified(item):
    rel,oid,size,commit=item
    url='https://media.githubusercontent.com/media/'+REPO+'/'+commit+'/'+quote(rel,safe='/')
    for attempt in range(3):
        try:
            h=hashlib.sha256()
            n=0
            with requests.get(url,stream=True,timeout=(15,90)) as response:
                response.raise_for_status()
                for block in response.iter_content(1048576):
                    h.update(block)
                    n+=len(block)
            assert h.hexdigest()==oid and n==size,(rel,n,h.hexdigest(),oid)
            return dict(file=rel,sha256=oid,bytes=n,actual_payload_bytes_verified=True)
        except Exception:
            if attempt==2:
                raise
            time.sleep(2**attempt)


def main():
    branch=git('branch','--show-current').decode().strip()
    commit=git('rev-parse','HEAD').decode().strip()
    remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0]
    assert remote==commit
    prefix=OUT.relative_to(ROOT).as_posix()
    paths=git('ls-tree','-r','--name-only',commit,'--',prefix).decode().splitlines()
    assert paths and all(p.startswith(prefix+'/') for p in paths)
    manifest=json.loads((OUT/'DERIVED_FILE_HASHES.json').read_text())
    for name,item in manifest.items():
        assert prefix+'/'+name in paths,'Required package asset not committed: '+name
        assert sha(OUT/name)==item['sha256']
        assert longpath(OUT/name).stat().st_size==item['bytes']
    lfs=[]
    text_count=0
    for rel in paths:
        blob=git('show',commit+':'+rel)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            fields=dict(line.split(' ',1) for line in blob.decode().splitlines())
            oid=fields['oid'].split(':')[1]
            size=int(fields['size'])
            assert sha(ROOT/rel)==oid and longpath(ROOT/rel).stat().st_size==size
            lfs.append((rel,oid,size,commit))
        else:
            assert longpath(ROOT/rel).read_bytes().replace(b'\r\n',b'\n')==blob,rel
            text_count+=1
    with ThreadPoolExecutor(max_workers=4) as executor:
        records=list(executor.map(download_verified,lfs))
    records.sort(key=lambda row:row['file'])
    dump('REMOTE_DELIVERY_VERIFICATION.json',dict(branch=branch,verified_payload_commit=commit,
         remote_HEAD_at_verification=remote,files=len(records),
         total_actual_LFS_bytes=sum(r['bytes'] for r in records),git_text_files_verified=text_count,
         all_actual_payload_bytes_verified=True,records=records))
    print(json.dumps(dict(remote_commit=remote,lfs_payloads=len(records),git_text_files=text_count,
                          all_actual_bytes_verified=True)),flush=True)


if __name__=='__main__':
    main()
