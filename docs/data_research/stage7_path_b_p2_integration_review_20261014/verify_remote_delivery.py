"""Verify remote commit and actual bytes downloaded into a new LFS store."""
from pathlib import Path
import os
import re
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).parent))
import analyze_path_b as a


def main():
    branch='review/stage7-path-b-p2-figure7-20261013'
    head=a.u.git('rev-parse','HEAD').decode().strip()
    assert a.u.git('ls-remote','origin','refs/heads/'+branch).decode().split()[0]==head
    prefixes=['docs/data_research/stage7_path_b_p2_integration_review_20261014/',
              'docs/reproducibility/figure_suite_concise_captions_20261013/']
    selected=[p for p in a.u.git('ls-tree','-r','--name-only',head).decode().splitlines() if
              any(p.startswith(v) for v in prefixes) or p=='results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf']
    records=[]
    for p in selected:
        blob=a.u.git('show',head+':'+p)
        m=re.search(rb'^version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize (\d+)',blob)
        if m:records.append(dict(path=p,oid=m[1].decode(),size=int(m[2])))
    cache=a.ROOT/'build'/('path_b_remote_LFS_'+str(time.time_ns()))
    assert not cache.exists();cache.mkdir(parents=True)
    patterns=[p+'**' for p in prefixes]+['results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf']
    r=subprocess.run(['git','-C',str(a.ROOT),'-c','lfs.storage='+str(cache),'lfs','fetch',
        '--include='+','.join(patterns),'--exclude=','origin',head],text=True,capture_output=True,
        env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
    a.u.write(a.HERE/'REMOTE_LFS_FETCH_OUTPUT.txt',r.stdout+r.stderr)
    assert r.returncode==0,r.stdout+r.stderr
    objects={}
    for row in records:
        oid=row['oid'];p=cache/'objects'/oid[:2]/oid[2:4]/oid
        assert Path(a.u.lp(p)).stat().st_size==row['size']
        assert a.u.sha(p)==oid==a.u.sha(a.ROOT/row['path'])
        objects[oid]=row['size']
    assert a.u.git('ls-remote','origin','refs/heads/'+branch).decode().split()[0]==head
    a.dump('REMOTE_DELIVERY_VERIFICATION.json',dict(status='PASS_ACTUAL_REMOTE_LFS_BYTES',
        artifact_commit=head,remote_branch=branch,remote_HEAD_matches=True,empty_cache_before_fetch=True,
        paths_verified=len(records),unique_objects=len(objects),bytes_downloaded=sum(objects.values()),
        actual_payloads=records,no_merge_or_force_push=True))
    print(head,len(records),'paths;',sum(objects.values()),'actual downloaded bytes')


if __name__=='__main__':main()
