"""Mechanical JSON compaction only; assert exact parsed geometry identity."""
from common import *
import zipfile


def main():
    records=[]
    for p in lp(OUT/'sources').glob('*_COMPLETE.geojson'):
        before=sha(p);data=json.loads(p.read_text());old=p.stat().st_size
        payload=json.dumps(data,separators=(',',':'),allow_nan=False)+'\n'
        assert json.loads(payload)==data
        p.write_text(payload,encoding='utf-8')
        records.append(dict(file='sources/'+p.name,before_sha256=before,after_sha256=sha(p),
            before_bytes=old,after_bytes=p.stat().st_size,parsed_feature_identity=True,
            operation='Whitespace-only JSON serialization; coordinates/attributes/order unchanged'))
    save('SNAPSHOT_SERIALIZATION_QA.csv',records)
    lookup={Path(v['file']).stem.replace('_COMPLETE',''):v['after_sha256'] for v in records}
    for phase in ['BASE','FLOOD']:
        path=lp(OUT/('SOURCE_GEOMETRY_QA_'+phase+'.csv'));q=pd.read_csv(path)
        q['source_sha256']=q.layer.map(lookup);assert q.source_sha256.notna().all()
        save(path.name,q)
    archive=lp(OUT/'sources/PHYSICAL_SOURCE_SNAPSHOTS.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(lp(OUT/'sources').glob('*_COMPLETE.geojson')):
            item=zipfile.ZipInfo(p.name,date_time=(2026,10,12,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(item,p.read_bytes(),compresslevel=9)
    with zipfile.ZipFile(archive) as z:
        for row in records:
            assert hashlib.sha256(z.read(Path(row['file']).name)).hexdigest()==row['after_sha256']
    dump('sources/PHYSICAL_SNAPSHOT_ARCHIVE_QA.json',dict(sha256=sha(archive),bytes=archive.stat().st_size,
        members=records,all_uncompressed_payload_hashes_verified=True))


if __name__=='__main__':main()
