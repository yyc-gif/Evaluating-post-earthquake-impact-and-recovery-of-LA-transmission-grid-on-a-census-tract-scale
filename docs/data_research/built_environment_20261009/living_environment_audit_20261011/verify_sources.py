"""Verify cached payloads. Optional reacquisition replays exact logged public requests."""
from common import *
import argparse
def run(reacquire=False):
    records=json.loads(lp(OUT/'ACQUISITION_RECORDS.json').read_text());last={r['file']:r for r in records}
    if reacquire:
        from acquire import get
        for r in last.values():
            if r.get('success') and r.get('bytes',0)>0:get(r['file'],r['url'],r.get('params'))
    checks=[]
    for name,r in last.items():
        p=lp(OUT/'sources'/name);ok=p.exists() and sha(p)==r.get('sha256')
        checks.append(dict(file=name,bytes=p.stat().st_size if p.exists() else 0,sha256=sha(p) if p.exists() else '',recorded_sha256=r.get('sha256'),identity_ok=ok,transport_success=r.get('success'),HTTP_status=r.get('status_code')))
        assert ok,'Source byte identity failed: '+name
    for rel,r in json.loads(lp(OUT/'INPUT_HASHES.json').read_text()).items():assert sha(r['path'])==r['sha256'],rel
    assert sha(OUT/'sources/ARCHIVED_STUDY_LAND.gpkg')==json.loads(lp(OUT/'ARCHIVED_LAND_REUSE.json').read_text())['sha256']
    dump('SOURCE_BYTE_VERIFICATION.json',dict(source_files=checks,inherited_input_bytes_verified=True))
    log('Verified all cached payload bytes, including documented failed responses; failed responses are not admitted measurements.')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--reacquire-missing',action='store_true');run(a.parse_args().reacquire_missing)
