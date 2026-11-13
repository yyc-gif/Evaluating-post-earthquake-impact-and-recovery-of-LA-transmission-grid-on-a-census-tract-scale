"""Verify actual remote artwork payloads, reusing exact parent-object evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
BASE='a6847bda22a49b13ba0ef2fa309dfb9cdb994909'
PREFIX='results/submission_artwork/IJDRS_five_figure/'
REPOSITORY='yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit',default='HEAD')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--download-all',action='store_true',help='Re-download unchanged parent objects too.')
    args=parser.parse_args();commit=git('rev-parse',args.commit)
    parent=json.loads(git('show',BASE+':results/publication_artwork_20261111/qa/REMOTE_DELIVERY.json'))
    known={r['sha256']:r for r in parent['files'] if r['actual_payload_downloaded']}
    records=json.loads(git('lfs','ls-files','--json',commit))['files']
    groups={}
    for row in records:
        if row['name'].startswith(PREFIX):groups.setdefault(row['oid'],[]).append(row)
    rows=[]
    for oid,files in groups.items():
        first=files[0];path=first['name'];local=ROOT/path
        assert hashlib.sha256(local.read_bytes()).hexdigest()==oid
        url=f'https://media.githubusercontent.com/media/{REPOSITORY}/{commit}/'+urllib.parse.quote(path)
        inherited=oid in known and not args.download_all
        for attempt in range(3):
            try:
                if inherited:
                    assert known[oid]['bytes']==local.stat().st_size
                    with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=180) as response:
                        assert response.status==200
                        length=response.headers.get('Content-Length')
                        if length:assert int(length)==local.stat().st_size
                    size=local.stat().st_size
                else:
                    checksum=hashlib.sha256();size=0;magic=b''
                    with urllib.request.urlopen(url,timeout=180) as response:
                        assert response.status==200
                        for block in iter(lambda:response.read(1024*1024),b''):
                            if not magic:magic=block[:64]
                            checksum.update(block);size+=len(block)
                    assert checksum.hexdigest()==oid and size==local.stat().st_size
                    expected={'.pdf':b'%PDF','.png':b'\x89PNG','.tif':b'II*\x00'}
                    assert magic.startswith(expected[local.suffix.lower()])
                break
            except Exception:
                if attempt==2:raise
                time.sleep(3*(attempt+1))
        for row in files:
            if row['name']==path:continue
            alternate=f'https://media.githubusercontent.com/media/{REPOSITORY}/{commit}/'+urllib.parse.quote(row['name'])
            with urllib.request.urlopen(urllib.request.Request(alternate,method='HEAD'),timeout=180) as response:
                assert response.status==200
        rows.append(dict(paths=[r['name'] for r in files],sha256=oid,bytes=size,url=url,
            actual_payload_downloaded_now=not inherited,
            inherited_complete_payload_proof=known[oid]['url'] if inherited else None,
            all_named_paths_available=True))
        print(f'Verified {len(rows)}/{len(groups)}: {path}'+(' (exact parent LFS object; HEAD checked)' if inherited else ' (full payload downloaded)'),flush=True)
    assert groups
    report=dict(commit=commit,parent_evidence_commit=BASE,unique_lfs_objects=len(rows),
        named_artifact_paths=sum(len(r['paths']) for r in rows),
        fully_downloaded_now=sum(r['actual_payload_downloaded_now'] for r in rows),
        downloaded_bytes_now=sum(r['bytes'] for r in rows if r['actual_payload_downloaded_now']),
        inherited_verified_payloads=sum(not r['actual_payload_downloaded_now'] for r in rows),files=rows)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
