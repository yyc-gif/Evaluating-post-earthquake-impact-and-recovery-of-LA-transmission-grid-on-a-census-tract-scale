"""Acquire exact official payloads and discover documented download endpoints."""
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import time
from urllib.parse import urljoin
import requests
from common import *

S = OUT / 'sources'
RECORDS = []


def fetch(name, url, params=None):
    p = lp(S / name)
    p.parent.mkdir(parents=True, exist_ok=True)
    previous = next((r for r in RECORDS if r['name'] == name and r['status'] == 'ACQUIRED'), None)
    if p.exists() and previous:
        assert sha(p) == previous['sha256'] and previous['url'] == url and previous['params'] == (params or {})
        return p
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=(20, 240))
            r.raise_for_status()
            if params and params.get('f') in ['json', 'pjson'] and 'error' in r.json():
                raise ValueError(r.json()['error'])
            p.write_bytes(r.content)
            RECORDS.append(dict(name=name, url=url, params=params or {}, resolved_url=r.url,
                                retrieved_utc=datetime.now(timezone.utc).isoformat(), environment_date='2026-10-12',
                                sha256=sha(p), bytes=p.stat().st_size, last_modified=r.headers.get('Last-Modified'), status='ACQUIRED'))
            dump('OFFICIAL_SOURCE_ACQUISITION.json', RECORDS)
            return p
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                RECORDS.append(dict(name=name, url=url, params=params or {}, status='UNAVAILABLE', error=str(e)))
                dump('OFFICIAL_SOURCE_ACQUISITION.json', RECORDS)
                raise


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ['href', 'src']:
            if key in a:
                self.links.append(a[key])


def main():
    global RECORDS
    if lp(OUT / 'OFFICIAL_SOURCE_ACQUISITION.json').exists():
        RECORDS = json.loads(lp(OUT / 'OFFICIAL_SOURCE_ACQUISITION.json').read_text())
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', default='metadata', choices=['metadata', 'discovery', 'bulk', 'query'])
    args = parser.parse_args()
    if args.phase == 'metadata':
        urls = dict(
            CDC_DOWNLOAD_PAGE='https://www.atsdr.cdc.gov/place-health/php/eji/eji-data-download.html',
            CDC_DOWNLOAD_PORTAL='https://eji.cdc.gov/dfe/eji_data_download_dfe.html',
            CDC_INDICATORS='https://www.atsdr.cdc.gov/place-health/php/eji/eji-indicators-climate-burden-module.html',
            CDC_TECHNICAL='https://atsdr.cdc.gov/place-health/media/pdfs/2024/10/EJI_2024_Technical_Documentation.pdf')
        for name, url in urls.items():
            try:
                suffix = '.pdf' if name == 'CDC_TECHNICAL' else '.html'
                p = fetch(name + suffix, url)
                if suffix == '.html':
                    links = Links()
                    links.feed(p.read_text(encoding='utf-8', errors='replace'))
                    dump('sources/' + name + '_LINKS.json', [urljoin(url, x) for x in links.links])
                    print(name, [x for x in links.links if any(v in x.lower() for v in ['csv', 'zip', 'dictionary', 'assets/', 'download'])], flush=True)
            except Exception as e:
                print(name, 'UNAVAILABLE', str(e), flush=True)
    if args.phase == 'discovery':
        p = fetch('CDC_DOWNLOAD_APP.js', 'https://eji.cdc.gov/dfe/assets/app-de5b659f.js')
        import re
        txt = p.read_text(encoding='utf-8')
        for term in ['zip', 'csv', 'dictionary', '2024', 'https', 'download', '.json']:
            print(term, [txt[max(0,m.start()-100):m.end()+180] for m in list(re.finditer(re.escape(term), txt, re.I))[-20:]], flush=True)
        fetch('CDC_DOWNLOAD_STATES.json', 'https://eji.cdc.gov/dfe/content/json/states.json')
    if args.phase == 'bulk':
        states = json.loads(lp(S / 'CDC_DOWNLOAD_STATES.json').read_text())
        print('Official geography options', states, flush=True)
        for label in ['United States', 'California']:
            if not any(x['name'] == label for x in states['states']):
                continue
            filename = f'EJI_2024_{label.replace(" ", "_")}_CSV.zip'
            try:
                p = fetch(filename, 'https://eji.cdc.gov/Documents/Data/2024/2024_CSV/' + filename)
                import zipfile
                with zipfile.ZipFile(p) as z:
                    print(filename, [(x.filename, x.file_size) for x in z.infolist()], flush=True)
            except Exception as e:
                print('BULK_UNAVAILABLE', label, str(e), flush=True)
    if args.phase == 'query':
        for label, url in [('RAW', 'https://onemap.cdc.gov/onemapservices/rest/services/EJI/EJI_2024_Data_Service/MapServer/0'),
                           ('MAP', 'https://onemap.cdc.gov/onemapservices/rest/services/EJI/ClimateBurdenModule_2024/MapServer/0')]:
            meta = json.loads(lp(S / ('CDC_RAW_METADATA.json' if label=='RAW' else 'CDC_CBM_MAP_METADATA.json')).read_text())
            names = [x['name'] for x in meta['fields']]
            fields = [x for x in names if x.startswith(('F_', 'E_', 'EPL_', 'RPL_', 'SPL_')) or x in ['GEOID','GEOID_2020']]
            if label=='MAP':
                fields=[x for x in fields if 'CBM' in x or x=='GEOID' or any(x.endswith('_'+c) for c in ['NEHD','BURN','SMOKE','CFLD','DRGT','HRCN','RFLD','SWND','TRND'])]
            where = "STATEFP='06' AND COUNTYFP='037'" if 'STATEFP' in names else "GEOID LIKE '06037%'"
            p = fetch('CDC_'+label+('_LA_CBM_QUERY.json' if label=='MAP' else '_LA_QUERY.json'), url+'/query', dict(f='json', where=where,
                      outFields=','.join(fields),returnGeometry='false',orderByFields='GEOID',resultRecordCount=10000))
            j = json.loads(p.read_text())
            expected = json.loads(fetch('CDC_'+label+'_LA_COUNT.json',url+'/query',dict(f='json',where=where,returnCountOnly='true')).read_text())['count']
            rows=[x['attributes'] for x in j['features']]
            limited=bool(j.get('exceededTransferLimit',False))
            if limited:
                ids=json.loads(fetch('CDC_'+label+'_LA_IDS.json',url+'/query',dict(f='json',where=where,returnIdsOnly='true')).read_text())
                oid=ids['objectIdFieldName']
                expected_ids=sorted(ids['objectIds'])
                assert len(expected_ids)==expected
                rows=[]
                for i in range(0,len(expected_ids),100):
                    part=json.loads(fetch(f'CDC_{label}_LA_SMALLPART_{i//100:02d}.json',url+'/query',dict(f='json',
                        objectIds=','.join(map(str,expected_ids[i:i+100])),outFields=','.join([oid]+fields),returnGeometry='false')).read_text())
                    assert not part.get('exceededTransferLimit',False)
                    rows.extend(x['attributes'] for x in part['features'])
                assert sorted(x[oid] for x in rows)==expected_ids
            assert len(rows)==expected and len(set(x['GEOID'] for x in rows))==expected
            save('CDC_'+label+'_LA_QUERY_VALUES.csv',rows)
            dump('sources/CDC_'+label+'_QUERY_COMPLETENESS_QA.json',dict(expected_n=expected,actual_n=len(rows),
                 original_query_transfer_limited=limited,complete_ID_bound_queries_used=limited,geoids_unique=True))
            print(label, expected, 'county records acquired',flush=True)
        for name, url in [('CDC_RAW', 'https://onemap.cdc.gov/onemapservices/rest/services/EJI/EJI_2024_Data_Service/MapServer/0'),
                          ('CDC_CBM_MAP', 'https://onemap.cdc.gov/onemapservices/rest/services/EJI/ClimateBurdenModule_2024/MapServer/0')]:
            try:
                p = fetch(name + '_METADATA.json', url, {'f': 'pjson'})
                j = json.loads(p.read_text())
                print(name, [(v['name'], v.get('alias')) for v in j['fields'] if any(w in v['name'] for w in ['CBM', 'F_', 'NEHD', 'WFIR', 'CFLD', 'DRGT', 'RFLD', 'HRCN', 'SWND', 'TRND', 'GEOID'])], flush=True)
            except Exception as e:
                print(name, 'UNAVAILABLE', str(e), flush=True)


if __name__ == '__main__':
    main()
