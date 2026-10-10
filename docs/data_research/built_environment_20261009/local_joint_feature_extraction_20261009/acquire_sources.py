"""Acquire official source snapshots with size and disk checks; never run a model."""
from pathlib import Path
import requests,json,zipfile,io,struct,shutil,time,re,hashlib
from html.parser import HTMLParser
class Links(HTMLParser):
 def __init__(self):super().__init__();self.href=None;self.items=[]
 def handle_starttag(self,tag,attrs):
  if tag=="a":self.href=dict(attrs).get("href")
 def handle_data(self,data):
  if self.href and "Ground Motion datafiles" in data:self.items.append(self.href)
 def handle_endtag(self,tag):
  if tag=="a":self.href=None
from source_audit import ROOT,OUT,sha,dump
S=OUT/'sources';S.mkdir(exist_ok=True)
L6='https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip'
def download(url,path,limit=600_000_000):
 if path.exists():return {'file':str(path),'bytes':path.stat().st_size,'sha256':sha(path),'reused':True}
 q=requests.get(url,stream=True,timeout=(20,60));q.raise_for_status();size=int(q.headers.get('Content-Length',0));assert size<=limit
 assert shutil.disk_usage(S).free>size+700_000_000
 n=0;t=time.time()
 with path.open('wb') as f:
  for block in q.iter_content(2**20):
   n+=len(block);assert n<=limit;f.write(block)
   if n%(50*2**20)<2**20:print('DOWNLOAD',path.name,n,round(time.time()-t,1),flush=True)
 return {'url':url,'file':str(path),'bytes':n,'sha256':sha(path),'headers':dict(q.headers),'seconds':time.time()-t}
def run():
 log={}
 q=requests.get('https://www.conservation.ca.gov/cgs/Pages/Publications/MS48.aspx',timeout=45);q.raise_for_status();(S/'CGS_MS48_PAGE.html').write_text(q.text,encoding='utf-8');parser=Links();parser.feed(q.text);links=parser.items;print('CGS_LINKS',links,flush=True)
 if len(links)==1:
  from urllib.parse import urljoin
  u=urljoin(q.url,links[0]);log['CGS']=download(u,S/'CGS_OFFICIAL_MS48_datafiles.zip',120_000_000)
  with zipfile.ZipFile(S/'CGS_OFFICIAL_MS48_datafiles.zip') as z:
   names=z.namelist();log['CGS']['zip_members']=[{'file':i.filename,'bytes':i.file_size} for i in z.infolist()]
   for name in names:
    if name.endswith('CA_pt01_GM_maps.csv'):
     b=z.read(name);local=ROOT/'Data/MS_048_CA_pt01_MMI_GM_datafiles/CA_pt01_GM_maps.csv';log['CGS']['grid_official_sha256']=hashlib.sha256(b).hexdigest();log['CGS']['grid_local_sha256']=sha(local);log['CGS']['exact_match']=log['CGS']['grid_official_sha256']==sha(local)
     (S/'CGS_OFFICIAL_GRID_HEADER.txt').write_text(b.splitlines()[0].decode('utf-8'),encoding='utf-8');print('CGS_MATCH',log['CGS']['exact_match'],flush=True)
 log['LARIAC4']=download('https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC4/LARIAC4_BUILDINGS_2014.zip',S/'LARIAC4_BUILDINGS_2014.zip')
 log['LARIAC6']=download(L6,S/'LARIAC6_Buildings_2020.gdb.zip')
 with zipfile.ZipFile(S/'LARIAC6_Buildings_2020.gdb.zip') as z:
  log['LARIAC6']['uncompressed_bytes']=sum(i.file_size for i in z.infolist());log['LARIAC6']['zip_members']=[{'file':i.filename,'bytes':i.file_size} for i in z.infolist()];print('LARIAC6_UNCOMPRESSED',log['LARIAC6']['uncompressed_bytes'],flush=True)
 dump('ACQUISITION_LOG.json',log)
if __name__=='__main__':run()
