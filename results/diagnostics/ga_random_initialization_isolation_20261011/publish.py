"""Lossless per-run evidence bundles and actual remote LFS byte verification."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from pathlib import Path
import subprocess
import time
from urllib.parse import quote
import zipfile
import study as s


def package():
    manifest=[]
    for folder in s.lp(s.OUT/'runs').iterdir():
        if not folder.is_dir():continue
        target=s.lp(s.OUT/'raw_evidence'/(folder.name+'.zip'))
        target.parent.mkdir(parents=True,exist_ok=True)
        unique={};records=[]
        files=sorted([p for p in folder.iterdir() if p.suffix in ['.npz','.gz']])
        for p in files:
            h=s.digest(p);entry=unique.setdefault(h,'objects/'+h)
            records.append(dict(path=p.name,sha256=h,size=p.stat().st_size,entry=entry))
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
            for h,entry in unique.items():
                source=next(p for p,r in zip(files,records) if r['sha256']==h)
                z.write(source,entry)
            import json
            z.writestr('PATH_HASH_MANIFEST.json',json.dumps(records,indent=2)+'\n')
        with zipfile.ZipFile(target) as z:
            for row in records:
                h=hashlib.sha256();size=0
                with z.open(row['entry']) as f:
                    for block in iter(lambda:f.read(2**20),b''):h.update(block);size+=len(block)
                assert h.hexdigest()==row['sha256'] and size==row['size']
        manifest.append(dict(run=folder.name,zip_path=str(target.relative_to(s.lp(s.OUT))).replace('\\','/'),
            zip_sha256=s.digest(target),zip_bytes=target.stat().st_size,all_raw_bytes_verified=True,
            files=records,distinct_raw_objects=len(unique)))
        print('PACKAGED',folder.name,target.stat().st_size,flush=True)
    s.save(s.OUT/'RAW_SEARCH_EVIDENCE_MANIFEST.json',dict(status='PASS',runs=manifest,
        duplicate_checkpoint_payloads='Stored once by SHA256 within each bundle; all logical paths preserved in PATH_HASH_MANIFEST.json',
        lossless=True,total_bundle_bytes=sum(r['zip_bytes'] for r in manifest)))
    output_manifest()


def output_manifest():
    files={}
    for p in s.lp(s.OUT).rglob('*'):
        if not p.is_file() or 'runtime' in p.parts:continue
        if 'runs' in p.parts and p.suffix in ['.npz','.gz']:continue
        if p.name in ['OUTPUT_HASH_MANIFEST.json','REMOTE_PUBLICATION_VERIFIED.json']:continue
        files[str(p.relative_to(s.lp(s.OUT))).replace('\\','/')]=dict(sha256=s.digest(p),size=p.stat().st_size)
    s.save(s.OUT/'OUTPUT_HASH_MANIFEST.json',dict(files=files,total_bytes=sum(v['size'] for v in files.values())))


def remote():
    import requests
    sha=s.git('rev-parse','HEAD').decode().strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+s.BRANCH],cwd=s.ROOT,text=True).split()[0]
    assert remote==sha
    names=s.git('ls-tree','-r','--name-only',sha,'--',str(s.OUT.relative_to(s.ROOT)).replace('\\','/')).decode().splitlines()
    lfs=[];ordinary=[]
    for name in names:
        blob=s.git('show',sha+':'+name)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            f=dict(x.split(' ',1) for x in blob.decode().splitlines())
            lfs.append(dict(path=name,oid=f['oid'][7:],size=int(f['size'])))
        else:
            assert hashlib.sha256(blob).hexdigest()==s.digest(s.ROOT/name)
            ordinary.append(dict(path=name,sha256=hashlib.sha256(blob).hexdigest(),size=len(blob)))
    tick=time.perf_counter();dest=s.lp(s.OUT/'runtime'/'remote_payloads');dest.mkdir(parents=True,exist_ok=True)
    repo='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'
    def verify(row):
        url=f'https://media.githubusercontent.com/media/{repo}/{sha}/'+quote(row['path'],safe='/')
        target=dest/row['oid'];h=hashlib.sha256();count=0
        with requests.get(url,stream=True,timeout=(30,600)) as r:
            r.raise_for_status()
            with target.open('wb') as f:
                for block in r.iter_content(2**20):
                    if block:h.update(block);count+=len(block);f.write(block)
        assert h.hexdigest()==row['oid'] and count==row['size'],row['path']
        print('REMOTE_LFS_PASS',row['path'],count,flush=True)
        return dict(**row,downloaded_sha256=h.hexdigest(),downloaded_bytes=count,verified=True,url=url)
    verified=[]
    # Identical objects can be represented by several paths; download each unique object once.
    unique={r['oid']:r for r in lfs}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(verify,r) for r in unique.values()]):verified.append(f.result())
    s.save(s.OUT/'REMOTE_PUBLICATION_VERIFIED.json',dict(status='PASS',remote_head=sha,
        branch=s.BRANCH,git_non_lfs_tree_verified=ordinary,unique_lfs_objects=len(verified),
        lfs_paths=len(lfs),actual_download_bytes=sum(r['downloaded_bytes'] for r in verified),
        actual_remote_lfs_objects=verified,wall_seconds=time.perf_counter()-tick,
        receipt_commit='This receipt is committed after the verified payload commit; the final remoteHEAD is checked separately.'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['package','manifest','remote']);a=p.parse_args()
    if a.phase=='package':package()
    elif a.phase=='manifest':output_manifest()
    else:remote()
