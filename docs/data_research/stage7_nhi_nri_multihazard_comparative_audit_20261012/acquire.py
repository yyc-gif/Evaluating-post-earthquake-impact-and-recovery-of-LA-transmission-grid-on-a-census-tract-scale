"""Original official/peer-reviewed payloads, queries and explicit acquisition failures."""
from datetime import datetime, timezone
import requests
from common import *

BASE = 'https://services2.arcgis.com/IsDCghZ73NgoYoz5/ArcGIS/rest/services/Hazards_Index_Sum/FeatureServer'
URLS = {
    'COLUMBIA_OFFICIAL': 'https://ncdp.columbia.edu/us-natural-hazards-index/',
    'COLUMBIA_SERVICE': BASE + '?f=pjson',
    'COLUMBIA_LAYER77': BASE + '/77?f=pjson',
    'COLUMBIA_APP_ITEM': 'https://www.arcgis.com/sharing/rest/content/items/fda2d684cd3f4ed5b802818a298d1b1a?f=pjson',
    'COLUMBIA_APP_DATA': 'https://www.arcgis.com/sharing/rest/content/items/fda2d684cd3f4ed5b802818a298d1b1a/data?f=pjson',
    'WILLIAMS_PMC': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11980775/',
    'WILLIAMS_XML': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11980775/fullTextXML',
    'WILLIAMS_MDPI_XML': 'https://www.mdpi.com/2071-1050/16/23/10778/xml',
    'CENSUS_RELATION_PAGE': 'https://www.census.gov/geographies/reference-files/2020/geo/relationship-files.html',
    'CENSUS_RELATION_CA': 'https://www2.census.gov/geo/docs/maps-data/data/rel2020/tract/tab20_tract20_tract10_st06.txt',
    'CENSUS_RELATION_EXPLANATION': 'https://www2.census.gov/geo/pdfs/maps-data/data/rel2020/tract/explanation_tab20_tract20_tract10.pdf',
    'CENSUS_TIGER2020_CATALOG': 'https://www2.census.gov/geo/tiger/TIGER2020/TRACT/',
    'CENSUS_TIGER2020_CA': 'https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_06_tract.zip',
    'CENSUS_TIGER2010_LA': 'https://www2.census.gov/geo/tiger/TIGER2010/TRACT/2010/tl_2010_06037_tract10.zip',
    'WILLIAMS_OA_METADATA': 'https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC11980775',
    'FEMA_V119_TRACTS_ARCHIVE_TRIAL': 'https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload/Archive/v119_0/NRI_Table_CensusTracts.zip',
    'FEMA_V119_COUNTIES_ARCHIVE_TRIAL': 'https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload/Archive/v119_0/NRI_Table_Counties.zip',
    'USFS_RPS_DEFINITION': 'https://wildfirerisk.org/download/',
    'USFS_RPS_2020_METHOD': 'https://wildfirerisk.org/wp-content/uploads/2020/06/WRC-LANDFIRE-2020-05-28.pdf',
    'WILLIAMS_PUBLISHED_PDF_CDN_TRIAL': 'https://mdpi-res.com/d_attachment/sustainability/sustainability-16-10778/article_deploy/sustainability-16-10778.pdf',
}


class Acquisition:
    def __init__(self):
        self.path = OUT / 'OFFICIAL_SOURCE_ACQUISITION_AND_HASHES.json'
        self.records = json.loads(lp(self.path).read_text())['records'] if lp(self.path).exists() else []
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'LA-grid academic multi-hazard source audit'

    def flush(self):
        dump(self.path.name, dict(review_status=WARN, records=self.records))

    def fetch(self, name, url, params=None, suffix=None):
        existing = next((r for r in self.records if r['name'] == name), None)
        if existing:
            if name=='CENSUS_TIGER2020_CATALOG':
                existing['status']='UNRESOLVED_WAF_RESPONSE'
                self.flush()
            if existing.get('status') == 'ACQUIRED':
                path = OUT / existing['file']
                assert sha(path) == existing['sha256']
                return lp(path)
            return None
        record = dict(review_status=WARN, name=name, requested_url=url, query_parameters=params,
            client_review_date='2026-10-12', retrieval_UTC=datetime.now(timezone.utc).isoformat())
        try:
            with self.session.get(url, params=params, stream=True, timeout=(20, 120)) as response:
                content = response.content
                record.update(final_url=response.url, http_status=response.status_code,
                    content_type=response.headers.get('Content-Type'), bytes=len(content))
                ext = suffix or ('.pdf' if content.startswith(b'%PDF') else '.zip' if content.startswith(b'PK\x03\x04') else '.json' if 'json' in response.headers.get('Content-Type', '') else '.xml' if name.endswith('XML') else '.txt' if name.startswith('CENSUS_RELATION_CA') else '.html')
                path = dest('sources/' + name + ext)
                path.write_bytes(content)
                valid = response.ok
                if ext == '.pdf':
                    valid = valid and content.startswith(b'%PDF')
                if ext == '.zip' or name.endswith('ARCHIVE_TRIAL'):
                    valid = valid and content.startswith(b'PK\x03\x04')
                if ext == '.json':
                    try:
                        valid = valid and 'error' not in json.loads(content)
                    except ValueError:
                        valid = False
                if name == 'CENSUS_TIGER2020_CATALOG' and len(content) < 1000:
                    valid = False
                if b'reCAPTCHA' in content or b'_Incapsula_Resource' in content or b'Request Rejected' in content:
                    valid = False
                record.update(file='sources/' + path.name, sha256=sha(path), status='ACQUIRED' if valid else 'UNRESOLVED_RESPONSE')
                return path if valid else None
        except Exception as error:
            record.update(status='ACQUISITION_FAILED', error=str(error))
            return None
        finally:
            self.records.append(record)
            self.flush()
            print(name, record['status'], record.get('bytes', 0), flush=True)


def main():
    a = Acquisition()
    for name, url in URLS.items():
        a.fetch(name, url)
    layer = next((r for r in a.records if r['name'] == 'COLUMBIA_LAYER77' and r['status'] == 'ACQUIRED'), None)
    if layer:
        data = json.loads(lp(OUT / layer['file']).read_bytes())
        print('NHI layer:', data.get('name'), data.get('geometryType'), data.get('maxRecordCount'), flush=True)
        print('NHI field count:', len(data.get('fields', [])), flush=True)
    service = next((r for r in a.records if r['name'] == 'COLUMBIA_SERVICE' and r['status'] == 'ACQUIRED'), None)
    if service:
        item = json.loads(lp(OUT / service['file']).read_bytes()).get('serviceItemId')
        if item:
            for tail, suffix in [('', 'METADATA'), ('/data', 'DATA')]:
                a.fetch('COLUMBIA_SERVICE_ITEM_' + suffix, 'https://www.arcgis.com/sharing/rest/content/items/' + item + tail, {'f': 'pjson'})
    app = a.fetch('COLUMBIA_APP_DATA', URLS['COLUMBIA_APP_DATA'])
    if app:
        config = json.loads(app.read_bytes())
        for key, value in config.get('dataSources', {}).items():
            if value.get('type') == 'WEB_MAP' and value.get('itemId'):
                a.fetch('COLUMBIA_WEBMAP_' + key, 'https://www.arcgis.com/sharing/rest/content/items/' + value['itemId'] + '/data', {'f': 'pjson'}, '.json')
            if 'NHI_Documentation_Table' in value.get('url', ''):
                url = value['url']
                root = a.fetch(value['sourceLabel'].replace(' ', '_') + '_SERVICE', url, {'f': 'pjson'}, '.json')
                if root:
                    info = json.loads(root.read_bytes())
                    for table in info.get('tables', []) + info.get('layers', []):
                        stem = value['sourceLabel'].replace(' ', '_') + '_' + str(table['id'])
                        a.fetch(stem + '_SCHEMA', url + '/' + str(table['id']), {'f': 'pjson'}, '.json')
                        a.fetch(stem + '_RECORDS', url + '/' + str(table['id']) + '/query',
                            {'f': 'json', 'where': '1=1', 'outFields': '*', 'returnGeometry': 'false'}, '.json')
    if layer:
        query = BASE + '/77/query'
        ids = a.fetch('COLUMBIA_LA_OBJECT_IDS', query, {'f': 'json', 'where': "STCOFIPS='06037'", 'returnIdsOnly': 'true'}, '.json')
        count = a.fetch('COLUMBIA_LA_COUNT', query, {'f': 'json', 'where': "STCOFIPS='06037'", 'returnCountOnly': 'true'}, '.json')
        if ids and count:
            identifiers = sorted(json.loads(ids.read_bytes())['objectIds'])
            assert len(identifiers) == json.loads(count.read_bytes())['count']
            for start in range(0, len(identifiers), 100):
                a.fetch('COLUMBIA_LA_GEOJSON_B100_' + str(start), query,
                    {'f': 'geojson', 'objectIds': ','.join(map(str, identifiers[start:start+100])),
                     'outFields': '*', 'returnGeometry': 'true', 'outSR': '4326'}, '.json')
            dump('ARCGIS_PAGINATION_REGISTRATION.json', dict(review_status=WARN, layer=BASE + '/77',
                where="STCOFIPS='06037'", expected_records=len(identifiers), batch_size=100,
                rule='Count and complete OID inventory first; explicit sorted OID batches; no offset truncation accepted',
                object_ids=identifiers, outFields='*', returnGeometry=True, outSR=4326, geometry_simplification_requested=False))


if __name__ == '__main__':
    main()
