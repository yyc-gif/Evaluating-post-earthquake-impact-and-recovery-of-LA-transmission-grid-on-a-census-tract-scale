"""Verify final branch and actual remote LFS bytes in a new empty store."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
BASE='937fa2b1ab9953d8411a08fbbd0400cf3b52bd8f'
BRANCH='publication/p2-seven-variable'


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))


def sha(path):
    value=str(path.resolve())
    if os.name=='nt' and not value.startswith('\\\\?\\'):value='\\\\?\\'+value
    h=hashlib.sha256()
    with open(value,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    head=git('rev-parse','HEAD').decode().strip()
    remote=lambda:git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
    assert remote()==head
    paths=git('diff','--name-only',BASE,head).decode().splitlines()
    records=[]
    for path in paths:
        if not (ROOT/path).is_file():continue
        blob=git('show',head+':'+path)
        m=re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize (\d+)\n',blob)
        if m:records.append(dict(path=path,oid=m[1].decode(),size=int(m[2])))
    assert records
    cache=ROOT/'build'/('remote_p2_'+str(time.time_ns()))
    assert not cache.exists()
    cache.mkdir(parents=True)
    result=subprocess.run(['git','-C',str(ROOT),'-c','lfs.storage='+str(cache),'lfs','fetch',
        '--include='+','.join(r['path'] for r in records),'--exclude=','origin',head],
        text=True,capture_output=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
    assert result.returncode==0,result.stdout+result.stderr
    for row in records:
        oid=row['oid'];path=cache/'objects'/oid[:2]/oid[2:4]/oid
        assert sha(path)==oid==sha(ROOT/row['path'])
    assert remote()==head
    report=dict(status='PASS_ACTUAL_REMOTE_LFS_BYTES',artifact_commit=head,branch=BRANCH,
        remote_HEAD_matches=True,fresh_empty_store=True,paths_verified=len(records),
        bytes_downloaded=sum({r['oid']:r['size'] for r in records}.values()),payloads=records,
        no_simulation_or_fitting=True)
    if '--no-write' not in sys.argv:
        (HERE/'REMOTE_DELIVERY_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k!='payloads'}))


if __name__=='__main__':main()
