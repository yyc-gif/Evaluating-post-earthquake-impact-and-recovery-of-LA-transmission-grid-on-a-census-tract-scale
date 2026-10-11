from common import *
import requests, concurrent.futures, zipfile

def download(item):
 name,url=item;p=RAW/name
 if not p.exists():
  r=requests.get(url,timeout=(20,180));r.raise_for_status();p.write_bytes(r.content)
 else:r=None
 with zipfile.ZipFile(p) as z: members=[{'name':i.filename,'bytes':i.file_size} for i in z.infolist()]
 return {'source':'JRC EMC-BUILT 2022 R2025A','name':name,'url':url,'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'members':members,'resolution_m':100}

if __name__=='__main__':
 items=[]
 for kind in ['S','S_NRES']:
  root=f'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/EMC_BUILT_GLOBE_R2025A/EMC_BUILT_{kind}_GLOBE_R2025A/EMC_BUILT_{kind}_E2022_GLOBE_R2025A_54009_100/V1-0/tiles/'
  for tile in ['R5_C8','R6_C8']:
   name=f'EMC_BUILT_{kind}_E2022_GLOBE_R2025A_54009_100_V1_0_{tile}.zip';items.append((name,root+name))
 for tile in ['R5_C8','R6_C8']:
  name=f'GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100_V1_0_{tile}.zip'
  items.append((name,'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_H_GLOBE_R2023A/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100/V1-0/tiles/'+name))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:records=list(ex.map(download,items))
 for r in records:
  if r['name'].startswith('GHS'):
   r['source']='JRC GHS-BUILT-H ANBH R2023A';r['observation_support']='2018 Sentinel-2; SRTM2000; AW3D30 2006-2011';r['unit']='m'
  else:r['observation_support']='2022 Sentinel-2';r['unit']='m2 per100m pixel'
 u='https://human-settlement.emergency.copernicus.eu/documents/EMC-BUILT_R2025.pdf';p=RAW/'EMC-BUILT_R2025.pdf'
 if not p.exists():r=requests.get(u,timeout=60);r.raise_for_status();p.write_bytes(r.content)
 records.append({'source':'JRC product guide','url':u,'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
 dump('JRC_ACQUISITION.json',records);log('Downloaded and verified four official EMC 100-m tiles covering the study; total and nonresidential surface')
