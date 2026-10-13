"""Focused primary-source evidence; unchanged response bytes and explicit failures."""
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from common import *

URLS={
 'CDC_CBM':'https://www.atsdr.cdc.gov/place-health/php/eji/eji-indicators-climate-burden-module.html',
 'NOAA_NCEI':'https://www.ncei.noaa.gov/news/billion-dollar-disasters-mapping-vulnerabilities-census-tract-level-data',
 'NASA_NDH':'https://data.nasa.gov/dataset/global-multihazard-frequency-and-distribution',
 'SEDAC_DOWNLOAD':'https://sedac.ciesin.columbia.edu/data/set/ndh-multihazard-frequency-distribution/data-download',
 'NASA_CMR_COLLECTION':'https://cmr.earthdata.nasa.gov/search/collections.json?concept_id=C179001784-SEDAC',
 'NASA_CMR_GRANULE':'https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C179001784-SEDAC&page_size=100',
 'SEDAC_ZIP':'https://sedac.ciesin.columbia.edu/downloads/data/ndh/ndh-multihazard-frequency-distribution/gdmhz.zip',
 'CALIFORNIA_VCP':'https://lci.ca.gov/climate/icarp/vulnerable-communities/',
 'CALIFORNIA_VCP_CODE':'https://api.github.com/repos/Climate-Services-LCI/vulnerable-communities-platform/contents/',
 'OEHHA_CES':'https://oehha.ca.gov/calenviroscreen/model-scoring',
 'USGS_LANDSLIDE':'https://www.usgs.gov/tools/us-landslide-inventory-and-susceptibility-map',
 'USGS_MULTIFRAMEWORK':'https://www.usgs.gov/publications/multi-hazard-risk-analysis-us-department-interior-integration-expert-elicitation',
 'PRISM_ARTICLE':'https://pmc.ncbi.nlm.nih.gov/articles/PMC11152088/',
 'NaHRSI_ARTICLE':'https://pmc.ncbi.nlm.nih.gov/articles/PMC7007161/',
 'PRISM_XML':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11152088/fullTextXML',
 'NaHRSI_XML':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7007161/fullTextXML',
 'NASA_CMR_KEYWORD':'https://cmr.earthdata.nasa.gov/search/collections.json?keyword=Global%20Multihazard%20Frequency%20and%20Distribution&page_size=20',
 'NASA_CURRENT_GRANULES':'https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C3550190541-ESDIS&page_size=100',
 'NASA_CURRENT_METADATA':'https://cmr.earthdata.nasa.gov/search/concepts/C3550190541-ESDIS.umm_json',
 'NASA_NDH_MIGRATED_ZIP':'https://data.earthdata.nasa.gov/nasa-earth/human-dimensions/sedac-root/downloads/data/ndh/ndh-multihazard-frequency-distribution/gdmhz.zip',
 'EPA_PRISM_CATALOG':'https://catalog.data.gov/dataset/prism-scaled-dataset',
 'EPA_PRISM_WORKBOOK':'https://pasteur.epa.gov/uploads/10.23719/1519307/Buck_PRISM%20Scaled%20ScienceHub.xlsx',
 'EPA_PRISM_DICTIONARY':'https://pasteur.epa.gov/uploads/10.23719/1519307/documents/PRISM%20Scaled%20ScienceHub%20Metadata.xlsx',
 'EPA_PRISM_TRACT_XML':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8318127/fullTextXML',
}


def main():
    rows=[];session=requests.Session()
    session.headers.update({'User-Agent':'LA-grid scientific source audit; Python requests'})
    def get(name,url):
        record=dict(review_status=WARN,name=name,requested_url=url,client_review_date='2026-10-12',
                    actual_retrieval_UTC=datetime.now(timezone.utc).isoformat())
        try:
            with session.get(url,timeout=(15,40),stream=True) as response:
                content=b''
                for block in response.iter_content(262144):
                    content+=block
                    if len(content)>20000000: raise ValueError('Focused search 20 MB response limit')
                suffix='.xlsx' if content.startswith(b'PK\x03\x04') and 'PRISM' in name else '.zip' if content.startswith(b'PK\x03\x04') else '.json' if 'json' in response.headers.get('Content-Type','') else '.xml' if name.endswith('XML') else '.html'
                path=destination('sources/'+name+suffix);path.write_bytes(content)
                good=response.ok
                if name.endswith('ZIP'): good=good and suffix=='.zip'
                if name.endswith('ARTICLE'): good=good and b'reCAPTCHA' not in content and b'Checking your browser' not in content
                if b'_Incapsula_Resource' in content: good=False
                record.update(http_status=response.status_code,final_url=response.url,bytes=len(content),sha256=sha(path),
                    archived_file=path.name,status='ACQUIRED' if good else 'UNRESOLVED_RESPONSE',content_type=response.headers.get('Content-Type'))
                return content if good else None
        except Exception as e:
            record.update(status='ACQUISITION_FAILED',error=str(e))
            return None
        finally:
            rows.append(record);dump('OFFICIAL_SOURCE_ACQUISITION.json',dict(review_status=WARN,records=rows))
            print(name,record.get('status'),record.get('bytes',0),flush=True)
    old_path=lp(OUT/'OFFICIAL_SOURCE_ACQUISITION.json')
    old=json.loads(old_path.read_text())['records'] if old_path.exists() else []
    rows.extend(r for r in old if r['name'] not in URLS)
    for name,url in URLS.items():
        previous=next((r for r in old if r['name']==name),None)
        if previous:
            if name=='OEHHA_CES': previous['status']='UNRESOLVED_WAF_RESPONSE'
            rows.append(previous)
        else: get(name,url)
    granule=next((r for r in rows if r['name']=='NASA_CURRENT_GRANULES' and r['status']=='ACQUIRED'),None)
    if granule:
        obj=json.loads(lp(OUT/'sources'/granule['archived_file']).read_bytes())
        links=[l for g in obj.get('feed',{}).get('entry',[]) for l in g.get('links',[]) if l.get('rel','').endswith('/data#') and not l.get('inherited')]
        dump('NASA_NDH_OFFICIAL_DOWNLOAD_LINKS.json',dict(review_status=WARN,links=links))
        if not any(r['name']=='SEDAC_ZIP' and r['status']=='ACQUIRED' for r in rows):
            for i,link in enumerate(links[:2]):
                url=link.get('href','')
                name='NASA_NDH_ALTERNATE_'+str(i)
                if urlparse(url).scheme=='https' and not any(r['name']==name for r in rows): get(name,url)
    save('OFFICIAL_SOURCE_ACQUISITION.csv',rows)
    dump('OFFICIAL_SOURCE_ACQUISITION.json',dict(review_status=WARN,records=rows))
    earlier=[]
    for name,url in [('NASA_NDH_ALTERNATE_0.html','https://data.earthdata.nasa.gov/nasa-earth/human-dimensions/sedac-root/downloads/data/ndh/ndh-multihazard-frequency-distribution/gdmhz.zip'),
                     ('NASA_NDH_ALTERNATE_1.html','https://doi.org/10.7927/H45718Z5')]:
        path=lp(OUT/'sources'/name)
        if path.exists():
            earlier.append(dict(file=name,sha256=sha(path),bytes=path.stat().st_size,registered_candidate_url=url,
                original_complete_retrieval_record_available=False,
                use='Preserved earlier same-task response only; not an acquired raster or independently admitted measurement',
                limitation='Initial complete attempt row was not retained during link-filter correction. Do not infer retrieval time or response status from this attachment. Migrated ZIP was separately fetched and fully recorded.'))
    dump('EARLIER_SOURCE_RESPONSE_ATTACHMENTS.json',dict(review_status=WARN,attachments=earlier))


if __name__=='__main__': main()
