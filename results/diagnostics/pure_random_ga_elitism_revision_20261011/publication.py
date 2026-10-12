"""Reuse established remote-byte verification, with scoped source provenance."""
import argparse
import hashlib
from types import SimpleNamespace
import study as s


def manifest():
    files={}
    for p in s.a.lp(s.OUT).rglob('*'):
        if not p.is_file() or any(x in p.parts for x in ('runtime','__pycache__','.pytest_cache')):continue
        if p.name in ('OUTPUT_HASH_MANIFEST.json','REMOTE_PUBLICATION_VERIFIED.json','REMOTE_SOURCE_VERIFIED.json'):continue
        files[str(p.relative_to(s.a.lp(s.OUT))).replace('\\','/')]=dict(sha256=s.a.sha(p),size=p.stat().st_size)
    s.save('OUTPUT_HASH_MANIFEST.json',dict(files=files,total_bytes=sum(v['size'] for v in files.values()),
        source_runtime_sha256=s.a.sha(s.SOURCE),source_git_blob_sha256=hashlib.sha256(s.git('show','HEAD:src/la_grid/diagnostics/ga_variant_engine.py')).hexdigest(),
        windows_extended_length_enumeration=True))
    print('MANIFEST',len(files),sum(v['size'] for v in files.values()),flush=True)


def remote():
    head=s.git('rev-parse','HEAD').decode().strip()
    prefix=str(s.OUT.relative_to(s.ROOT)).replace('\\','/')
    tree=set(s.git('ls-tree','-r','--name-only',head,'--',prefix).decode().splitlines())
    manifest=s.a.read(s.OUT/'OUTPUT_HASH_MANIFEST.json')
    for name,row in manifest['files'].items():
        assert prefix+'/'+name in tree,'Manifest payload omitted from commit: '+name
        assert s.a.sha(s.OUT/name)==row['sha256'],name
    path=s.BASE/'results/diagnostics/ga_random_initialization_isolation_20261011/publish.py'
    m=s.module('existing_remote_payload_verifier',path)
    m.s=SimpleNamespace(ROOT=s.ROOT,OUT=s.OUT,BRANCH=s.BRANCH,lp=s.a.lp,digest=s.a.sha,
        git=s.git,save=lambda p,v:s.save(str(p.relative_to(s.OUT)),v))
    m.remote()
    head=s.git('rev-parse','HEAD').decode().strip()
    blob=s.git('show',head+':src/la_grid/diagnostics/ga_variant_engine.py')
    actual=s.a.lp(s.SOURCE).read_bytes()
    assert blob==actual.replace(b'\r\n',b'\n')
    s.save('REMOTE_SOURCE_VERIFIED.json',dict(status='PASS',remote_commit=head,
        source_path='src/la_grid/diagnostics/ga_variant_engine.py',
        normalized_git_blob_sha256=hashlib.sha256(blob).hexdigest(),
        frozen_windows_runtime_sha256=hashlib.sha256(actual).hexdigest(),
        normalization='Only CRLF to LF in Git, unchanged executed runtime bytes',
        reused_remote_verifier_sha256=s.a.sha(path)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['manifest','remote']);args=p.parse_args()
    {'manifest':manifest,'remote':remote}[args.phase]()
