from pathlib import Path
from html.parser import HTMLParser
import requests
import json
ROOT=Path(__file__).resolve().parent
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            url=dict(attrs).get('href','')
            if '2022' in url and ('csv' in url or 'Appendix' in url):
                print(url)

Links().feed((ROOT/'sources/variance_tables.html').read_text(encoding='utf8'))
base='https://dmsdata.cr.usgs.gov/geoserver/mrlc_Fractional-Impervious-Surface-Native_conus_year_data/wcs'
prefix='mrlc_Fractional-Impervious-Surface-Native_conus_year_data'
name='Fractional-Impervious-Surface-Native_conus_year_data'
params=[('service','WCS'),('version','2.0.1'),('request','GetCoverage'),('coverageId',prefix+'__'+name),('format','image/tiff'),('subset','X(-2000505,-1997505)'),('subset','Y(1460505,1463505)')]
log=[]
for label,extra in [('slice',[('subset','time("2022-01-01T00:00:00.000Z")')]),
                    ('interval',[('subset','time("2022-01-01T00:00:00.000Z","2022-01-01T00:00:00.000Z")')]),
                    ('full_axis',[('subset','http://www.opengis.net/def/axis/OGC/0/time("2022-01-01T00:00:00.000Z")')]),
                    ('time_kvp',[('time','2022-01-01T00:00:00.000Z')])]:
    r=requests.get(base,params=params+extra,timeout=60)
    item={'label':label,'url':r.url,'status':r.status_code,'type':r.headers.get('Content-Type'),'bytes':len(r.content),'tiff':r.content[:2] in (b'II',b'MM'),'retrieved':'2026-10-09'}
    if not item['tiff']:item['error']=r.text[:2000]
    (ROOT/f'sources/probe_{label}.bin').write_bytes(r.content)
    log.append(item); print(json.dumps(item),flush=True)
(ROOT/'sources/variance_tables_2022.html').write_bytes(requests.get('https://www.census.gov/programs-surveys/acs/data/variance-tables.2022.html',timeout=60).content)
Links().feed((ROOT/'sources/variance_tables_2022.html').read_text(encoding='utf8'))
params1={'service':'WCS','version':'1.0.0','request':'GetCoverage','coverage':prefix+':'+name,'format':'GeoTIFF',
         'bbox':'-2000505,1460505,-1997505,1463505','crs':'EPSG:5070','resx':30,'resy':30,'time':'2022-01-01T00:00:00.000Z'}
r=requests.get(base,params=params1,timeout=60)
item={'label':'wcs1','url':r.url,'status':r.status_code,'type':r.headers.get('Content-Type'),'bytes':len(r.content),'tiff':r.content[:2] in (b'II',b'MM')}
if not item['tiff']:item['error']=r.text[:2000]
(ROOT/'sources/probe_wcs1.bin').write_bytes(r.content)
log.append(item);print(json.dumps(item),flush=True)
(ROOT/'NLCD_PROBE_LOG.json').write_text(json.dumps(log,indent=2),encoding='utf8')
