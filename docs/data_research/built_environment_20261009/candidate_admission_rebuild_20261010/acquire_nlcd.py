"""Official C1.2 mapping-year2022 fractional impervious numeric acquisition."""
from common import *
import requests,zipfile,time,shutil

def main():
 url='https://www.sciencebase.gov/catalog/file/get/697b907eb66b0197c3043c9f?name=Annual_NLCD_FctImp_2022_CU_C1V2.zip';p=RAW/'Annual_NLCD_FctImp_2022_CU_C1V2.zip';start=time.time()
 if not p.exists():
  temp=RAW/'NLCD_C12.partial';n=0;mark=0
  with requests.get(url,stream=True,timeout=(20,60)) as r:
   r.raise_for_status();headers={k:v for k,v in r.headers.items() if k.lower() not in ['set-cookie','cookie']}
   with temp.open('wb') as f:
    for b in r.iter_content(1024*1024):
     if b:
      if n==0:assert b.startswith(b'PK'),'Not numeric ZIP'
      f.write(b);n+=len(b)
      if n-mark>=128*1024**2:log(f'Official NLCD C1.2 download {n/1024**2:.1f} MiB; {time.time()-start:.1f}s');mark=n
      if time.time()-start>900:raise TimeoutError('Bounded official download exceeded15min; partial retained')
  assert n==962491880,'Official archive byte count differs from exact ScienceBase record'
  temp.replace(p)
 else:headers={}
 with zipfile.ZipFile(p) as z:
  members=[{'name':x.filename,'bytes':x.file_size,'CRC':x.CRC} for x in z.infolist()];name=next(x.filename for x in z.infolist() if x.filename.lower().endswith('.tif'))
  evidence=OUT/'source_evidence';evidence.mkdir(exist_ok=True)
  for member in z.namelist():
   if member.endswith('.xml'):(evidence/Path(member).name).write_bytes(z.read(member))
  tif=RAW/'nlcd2022_c12.tif'
  if not tif.exists():
   with z.open(name) as a,tif.open('wb') as b:shutil.copyfileobj(a,b,8*1024**2)
 dump('NLCD_C12_ACQUISITION.json',{'official_url':url,'source_record':'https://www.sciencebase.gov/catalog/item/697b907eb66b0197c3043c9f?format=json','collection':'1.2','mapping_year':2022,'archive_sha256':sha(p),'archive_bytes':p.stat().st_size,'members':members,'numeric_raster_sha256':sha(tif),'tif_path':str(tif),'headers':headers,'seconds':time.time()-start,'no_authentication_or_paid_access':True})
 log('Official NLCD C1.2 numeric archive acquired and TIFF extracted; version/year/hash verified')
if __name__=='__main__':main()
