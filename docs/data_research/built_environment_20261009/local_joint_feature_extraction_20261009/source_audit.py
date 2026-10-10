"""Read-only local source, Git-preservation and bounded live-source audit."""
from pathlib import Path
import json,os,subprocess,hashlib,time,requests,shutil,sys
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
BASE='031d2c675f8e7d58035d27448be040b809ced086'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(n,x):(OUT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git','-C',str(ROOT),*a])
def snapshot():
 assert git('rev-parse','HEAD').decode().strip()==BASE
 idx=git('ls-files','--stage','-z');status=git('status','--porcelain=v1','-z')
 (OUT/'ORIGINAL_STAGING.bin').write_bytes(idx)
 (OUT/'ORIGINAL_STATUS.bin').write_bytes(status)
 p=json.loads((ROOT/'docs/data_research/built_environment_20261009/PRESERVATION_BASELINE.json').read_text(encoding='utf-8'))['protected_files']
 q=json.loads((ROOT/'results/diagnostics/ga_initialization_reconciliation_20261009/PRESERVATION_BASELINE.json').read_text(encoding='utf-8'))['files_sha256']
 protected={k:sha(ROOT/k) for k in sorted(set(p)|set(q))}
 dump('PRESERVATION_BASELINE.json',{'head':BASE,'analysis_reference':'d5d51c6ad1659c82c3b6717ab14a31f3e5cd78c7','original_212_count':len(p),'protected_files':protected,'original_staging_sha256':hashlib.sha256(idx).hexdigest(),'prior_baseline_differences':[k for k in p if p[k]!=protected[k]],'staged_count':len(git('diff','--cached','--name-only').decode().splitlines()),'lfs_status':git('lfs','status').decode(errors='replace'),'disk_free_bytes':shutil.disk_usage(ROOT).free})
 dump('RUNTIME.json',{'python':sys.version,'executable':sys.executable})
 print('SNAPSHOT',len(p),len(protected),flush=True)
def inventory():
 roots=[Path('D:/R2D_Windows_Download/R2D_Windows_Download'),Path('C:/2025-2026 Fall'),Path('C:/Users/yinch'),Path('C:/ABAQUS/temp')]
 skip={'.git','node_modules','.codex','.cache','anaconda3','Miniconda3','Windows','Program Files','Program Files (x86)','__pycache__','site-packages'}
 candidates=[]; errors=[]; logs=[]; seen=set()
 tokens=['merged_school','long beach result','northridge result','san fernando result','runbrails','brails','lariac','scag','building','simcenter','2pc50','hazard','pga','nshm','usgs']
 for root in roots:
  start=time.monotonic();n=0;truncated=False
  if not root.exists():logs.append({'root':str(root),'exists':False});continue
  for folder,dirs,files in os.walk(root,onerror=lambda e:errors.append(str(e))):
   dirs[:]=[d for d in dirs if d not in skip and not d.endswith('.gdb')]
   if time.monotonic()-start>120:truncated=True;break
   for d in os.scandir(folder):
    name=d.name.lower();path=Path(d.path)
    if path==OUT or OUT in path.parents:continue
    if (d.is_dir() and name.endswith('.gdb')) or (d.is_file() and (any(t in name for t in tokens) or (path.suffix.lower() in {'.gpkg','.geojson'} and any(t in str(path).lower() for t in ['ce294','r2d','simcenter'])))):
     key=str(path)
     if key not in seen:
      seen.add(key);candidates.append({'path':key,'bytes':d.stat().st_size if d.is_file() else None,'directory':d.is_dir(),'kind':path.suffix.lower()})
   n+=len(files)
  logs.append({'root':str(root),'exists':True,'files_examined':n,'seconds':time.monotonic()-start,'time_limit_reached':truncated})
 dump('WINDOWS_INVENTORY_DISCOVERY.json',{'search_roots':logs,'errors':errors,'candidates':candidates,'unmounted_prior_D_drive':not Path('D:/').exists()})
 print('INVENTORY',len(candidates),logs,flush=True)
def probe():
 sources={'SCAG2019':'https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0','LARIAC6_2020':'https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_%282020%29/FeatureServer/0','LARIAC4_2014':'https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1'}
 dest=OUT/'sources';dest.mkdir(exist_ok=True);logs=[]
 for name,url in sources.items():
  for phase,endpoint,params in [('metadata',url,{'f':'json'}),('count',url+'/query',{'f':'json','where':"COUNTY = 'Los Angeles'" if name=='SCAG2019' else '1=1','returnCountOnly':'true'}),('geometry_sample',url+'/query',{'f':'json','where':"COUNTY = 'Los Angeles'" if name=='SCAG2019' else '1=1','outFields':'*','returnGeometry':'true','resultRecordCount':10,'outSR':4326})]:
   try:
    response=requests.get(endpoint,params=params,timeout=(12,35));response.raise_for_status();data=response.json();raw=response.content
    (dest/f'{name}_{phase}.json').write_bytes(raw)
    logs.append({'source':name,'phase':phase,'url':response.url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'count':data.get('count'),'error':data.get('error'),'record_count':len(data.get('features',[])) if phase=='geometry_sample' else None,'exceededTransferLimit':data.get('exceededTransferLimit')})
   except Exception as e:logs.append({'source':name,'phase':phase,'url':endpoint,'error':str(e)})
  print('PROBE',name,logs[-3:],flush=True)
 dump('LIVE_SOURCE_PROBE_LOG.json',logs)
if __name__=='__main__':
 {'snapshot':snapshot,'inventory':inventory,'probe':probe}[sys.argv[1]]()
