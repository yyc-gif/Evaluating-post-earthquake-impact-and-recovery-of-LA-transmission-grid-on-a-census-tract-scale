import requests, concurrent.futures, re, json
from common import RAW,dump,log,sha

URLS={
 'JRC_EMC_total_directory':'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/EMC_BUILT_GLOBE_R2025A/EMC_BUILT_S_GLOBE_R2025A/',
 'JRC_EMC_nres_directory':'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/EMC_BUILT_GLOBE_R2025A/EMC_BUILT_S_NRES_GLOBE_R2025A/',
 'JRC_EMC_product':'https://human-settlement.emergency.copernicus.eu/emc_built_s.php',
 'USGS_NLCD_C12':'https://www.usgs.gov/centers/eros/science/usgs-eros-archive-land-cover-annual-nlcd-collection-12-fractional-impervious',
 'MRLC_services':'https://www.mrlc.gov/data-services-page',
 'Assessor_item':'https://www.arcgis.com/sharing/rest/content/items/70d93266f45a4080a97b285a471493cd?f=json',
 'Assessor_dictionary':'https://www.arcgis.com/sharing/rest/content/items/70d93266f45a4080a97b285a471493cd/info/metadata/metadata.xml',
 'JRC_height_product':'https://human-settlement.emergency.copernicus.eu/ghs_buH2023.php',
 'EPA_SLD':'https://www.epa.gov/smartgrowth/smart-location-mapping',
 'SCAG_service':'https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0?f=pjson',
}
def fetch(item):
 name,url=item
 try:
  r=requests.get(url,timeout=60);r.raise_for_status()
  f=RAW/(name+'.txt');f.write_bytes(r.content)
  links=re.findall(r'(?:href|src)=[\"\x27]([^\"\x27]+)',r.text)
  rec={'source':name,'url':url,'final_url':r.url,'status':r.status_code,'bytes':len(r.content),'sha256':sha(f),'file':str(f),'links':links}
  if name=='Assessor_item': rec['metadata']=r.json()
  return rec
 except Exception as e:return {'source':name,'url':url,'error':str(e)}
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: records=list(ex.map(fetch,URLS.items()))
 dump('OFFICIAL_SOURCE_PROBES.json',records)
 for r in records:
  print(r['source'],r.get('error',r.get('bytes')))
  print('\n'.join(x for x in r.get('links',[]) if any(z in x.lower() for z in ['ftp','tif','zip','s3','sciencebase','download','wcs','pdf'])))
  if 'metadata' in r: print(json.dumps({k:r['metadata'].get(k) for k in ['url','title','licenseInfo','description']})[:6500])
