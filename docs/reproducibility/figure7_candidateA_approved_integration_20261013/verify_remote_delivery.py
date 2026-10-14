"""Verify remote refs and real LFS bytes in an independent initially empty cache."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT=Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE=ROOT/'docs/reproducibility/figure7_candidateA_approved_integration_20261013'
sys.path.append(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages')
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

BRANCH='review/official-figure7-candidateA-approved-20261013'
REFS={
    'review/official-figure-suite-ncv14-h2-k3-d3-20261013':'8f2dcb3b9762137b9f2686609c34480334f5d44e',
    'review/figure7-scientific-layout-author-review-20261013':'aa55131cc5455aca9e1a6dead98e8f0eb8944217',
    'review/figure-suite-s10-crossreference-fix-20261013':'7795638a73ac533d544971c20db13cf6662d13d3'}


def source_heads():
    data=u.git('ls-remote','origin',*['refs/heads/'+r for r in REFS]).decode()
    actual={line.split()[1].removeprefix('refs/heads/'):line.split()[0] for line in data.splitlines()}
    assert actual==REFS,('Source branches changed; inspect rather than reset',actual)
    u.dump(HERE/'REMOTE_SOURCE_HEADS_VERIFIED.json',{'checked_UTC':datetime.now(timezone.utc).isoformat(),
        'remote':'origin','branch_HEADs':actual,'all_pinned_source_HEADs_match':True})


def delivery():
    head=u.git('rev-parse','HEAD').decode().strip()
    remote=u.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
    assert head==remote
    checkpoint=json.load(open(u.lp(HERE/'BUILD_CHECKPOINT.json')))
    required=list(checkpoint['output_hashes'])
    required += [str(p.relative_to(ROOT)).replace('\\','/') for p in HERE.iterdir() if p.suffix in ['.csv','.png']]
    payloads={}
    paths=[]
    source_groups={}
    for rel in required:
        blob=u.git('show',head+':'+rel)
        match=re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)',blob)
        if not match:continue
        oid=match[1].decode();size=int(match[2]);paths.append(rel)
        assert u.sha(ROOT/rel)==oid
        record=payloads.setdefault(oid,{'oid':oid,'bytes':size,'paths':[]})
        assert record['bytes']==size
        record['paths'].append(rel)
    sources=json.load(open(u.lp(HERE/'SOURCE_AUTHORITY_AND_HASHES.json')))['sources']
    for r in sources.values():
        if not r['lfs_oid']:continue
        oid=r['lfs_oid']
        record=payloads.setdefault(oid,{'oid':oid,'bytes':r['bytes'],'paths':[]})
        assert record['bytes']==r['bytes'] and oid==r['sha256']
        record.setdefault('pinned_source_references',[]).append({'commit':r['commit'],'path':r['path']})
        source_groups.setdefault(r['commit'],[]).append(r['path'])
    # tempfile.mkdtemp is independent of the existing shared repository LFS cache.
    cache=Path(tempfile.mkdtemp(prefix='fa13_remote_lfs_'))
    assert not list(cache.iterdir())
    command=['git','-C',str(ROOT),'-c','lfs.storage='+cache.as_posix(),'lfs','fetch',
        '--include='+','.join(paths),'--exclude=','origin',head]
    run=subprocess.run(command,text=True,capture_output=True)
    print(run.stdout,flush=True)
    if run.returncode:raise RuntimeError(run.stderr)
    source_fetches=[]
    for commit,rels in source_groups.items():
        command=['git','-C',str(ROOT),'-c','lfs.storage='+cache.as_posix(),'lfs','fetch',
            '--include='+','.join(rels),'--exclude=','origin',commit]
        fetched=subprocess.run(command,text=True,capture_output=True)
        if fetched.returncode:raise RuntimeError(fetched.stderr)
        source_fetches.append({'commit':commit,'paths':rels,'stdout':fetched.stdout,'stderr':fetched.stderr})
    for oid,r in payloads.items():
        downloaded=cache/'objects'/oid[:2]/oid[2:4]/oid
        assert downloaded.is_file() and downloaded.stat().st_size==r['bytes']
        assert u.sha(downloaded)==oid
        r['actual_download_SHA256']=u.sha(downloaded)
        r['verified_from_independent_remote_download']=True
    again=u.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
    assert again==head
    u.dump(HERE/'REMOTE_DELIVERY_VERIFICATION.json',{'checked_UTC':datetime.now(timezone.utc).isoformat(),
        'verified_artifact_commit':head,'remote_HEAD':remote,'branch':BRANCH,
        'isolated_cache_initially_empty':True,'cache_path':str(cache),
        'unique_real_LFS_payloads':len(payloads),'payload_bytes':sum(r['bytes'] for r in payloads.values()),
        'required_LFS_paths':len(paths),'all_actual_remote_payload_bytes_verified':True,
        'fetch_stdout':run.stdout,'fetch_stderr':run.stderr,'source_fetches':source_fetches,'payloads':list(payloads.values()),
        'source_or_scientific_branch_merged':False,'force_push_used':False})
    print('Remote HEAD and',len(payloads),'actual LFS payloads independently verified.',flush=True)


if __name__=='__main__':
    source_heads() if '--sources' in sys.argv else delivery()
