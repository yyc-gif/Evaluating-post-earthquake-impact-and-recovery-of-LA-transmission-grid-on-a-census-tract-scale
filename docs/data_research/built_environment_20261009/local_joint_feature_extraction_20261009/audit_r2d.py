"""Audit discovered school inventories without treating them as LA-wide taxonomy."""
import os,json,re
from pathlib import Path
import pandas as pd,numpy as np,geopandas as gpd,shapely,fitz
from source_audit import OUT,ROOT,sha,dump
from extract_gis import tracts
FIELDS=['YearBuilt','StructureType','OccupancyClass','BuildingType','NumberOfStories','PlanArea','BuildingHeight','Latitude','Longitude','AIM_id','APN','AIN']
def run():
 base=Path(r'C:/Users/yinch/Downloads/R2D_Windows_Download/R2D_Windows_Download');project=Path(r'C:/2024-2025 Fall/CIV ENG 294 - Disaster Risk Analysis of Infrastructure Systems/05_Project/Project_Files');files=[];examples=[]
 for folder,dirs,names in os.walk(base):
  dirs[:]=[d for d in dirs if d not in ['site-packages','python','__pycache__']]
  for n in names:
   p=Path(folder)/n
   if p.suffix.lower() in ['.csv','.geojson','.gpkg','.shp','.xlsx'] or n.endswith('AIM.json'):examples.append({'path':str(p),'bytes':p.stat().st_size,'status':'INSTALLATION_DATA_OR_EXAMPLE_NOT_COMPLETED_LA_INVENTORY'})
 study=tracts().to_crs(4326);rows=[];attrs=[]
 for p in sorted(project.rglob('*')):
  if not p.is_file() or p.suffix.lower() not in ['.csv','.xlsx']:continue
  if not any(x in p.name.lower() for x in ['merged_school','long beach result','northridge result','san fernando result']):continue
  d=pd.read_csv(p) if p.suffix.lower()=='.csv' else pd.read_excel(p);lon=pd.to_numeric(d.get('Longitude'),errors='coerce');lat=pd.to_numeric(d.get('Latitude'),errors='coerce');geo=gpd.GeoDataFrame({'record':range(len(d))},geometry=gpd.points_from_xy(lon,lat),crs=4326);joined=gpd.sjoin(geo,study[['geometry']].rename_axis('index_right'),how='left',predicate='intersects');covered=joined['index_right'].dropna().nunique();identity=next((c for c in ['AIM_id','id'] if c in d),None);row={'path':str(p),'sha256':sha(p),'records':len(d),'identity_field':identity,'duplicate_identity_records':int(d[identity].duplicated().sum()) if identity else None,'duplicate_coordinate_records':int(pd.DataFrame({'lon':lon,'lat':lat}).duplicated().sum()),'study_tracts_with_records':int(covered),'unmatched_record_count':int(joined['index_right'].isna().sum()),'coverage':'LAUSD SCHOOL PORTFOLIO; NOT countywide or full 2315 tract inventory','geometry_type':'WKT footprints plus points' if 'wkt_geom' in d and d.wkt_geom.astype(str).str.contains('POLYGON').any() else 'point coordinates','coordinate_bounds':[float(lon.min()),float(lat.min()),float(lon.max()),float(lat.max())],'occupancy_values':d.OccupancyClass.value_counts().to_dict() if 'OccupancyClass' in d else {},'attribute_origin':'CE294 report: FEMA USA Structures / NSI via BRAILS; field-level prediction vs estimate lineage not preserved','simulation_results':bool(any('Repair' in c for c in d))}
  rows.append(row)
  for field in FIELDS:
   if field in d:
    x=d[field];attrs.append({'path':str(p),'field':field,'nonmissing':int(x.notna().sum()),'records':len(d),'completeness':float(x.notna().mean()),'origin_status':'NSI_ESTIMATE_OR_BRAILS_DERIVED_UNRESOLVED_FIELD_LINEAGE' if field in ['YearBuilt','StructureType','NumberOfStories','PlanArea'] else 'PORTFOLIO_OR_SIMULATION_FIELD'})
 pd.DataFrame(rows).to_csv(OUT/'R2D_BRAILS_DISCOVERED_INVENTORIES.csv',index=False);pd.DataFrame(attrs).to_csv(OUT/'R2D_BRAILS_ATTRIBUTE_COMPLETENESS.csv',index=False);dump('R2D_INSTALLATION_DATA_DISCOVERY.json',examples)
 report=project/'Final Report CE294 at Berkeley.pdf';doc=fitz.open(report);text=' '.join(p.get_text() for p in doc);evidence=[text[max(0,m.start()-80):m.end()+600] for m in re.finditer(r'National Structure Inventory|Structural Data Acquisition',text,re.I)]
 dump('R2D_BRAILS_PROVENANCE_EVIDENCE.json',{'report':str(report),'sha256':sha(report),'excerpts':evidence,'prior_D_path_available':Path('D:/R2D_Windows_Download/R2D_Windows_Download').exists(),'actual_installation':str(base),'runBrails':str(base/'applications/tools/BRAILS/runBrails.py'),'runBrails_sha256':sha(base/'applications/tools/BRAILS/runBrails.py'),'cloud_folder':'https://drive.google.com/drive/folders/1gPQtfb0IdBci6ekXDcKHV3YDw-SsisVX','cloud_notebook':'FilteringPublicSchoolData.ipynb, ID 1vtOn4axxsKeWCAXMV9M3ygpoFx4P0i65; explicitly filters CDE records to active Los Angeles Unified schools; no countywide building inventory in direct folder children'})
 lines=['# Existing Windows R2D / BRAILS inventory audit','','The prior D: drive is not mounted. The installation exists at `'+str(base)+'`. It includes runBrails.py and model/example files, not a completed countywide building attribute census.','', 'The archived CE294 project files were found outside the initial 2025 search roots at `'+str(project)+'`. The source report describes FEMA USA Structures / National Structure Inventory obtained through BRAILS. Per-field observed-versus-predicted lineage is not retained; no school YearBuilt or StructureType is admitted as an observed countywide variable.','','| file | records | tracts intersected | identity duplicates | source/coverage |','|---|---:|---:|---:|---|']
 lines += [f"| {r['path']} | {r['records']} | {r['study_tracts_with_records']} | {r['duplicate_identity_records']} | LAUSD school portfolio; estimates/derived attributes |" for r in rows]
 lines += ['','All three hazard XLSX files are R2D school simulation outputs, not assessor observations or new physical hazard inputs. The 884-record portfolios do not support countywide structural taxonomy or all-use building age. Exact hashes, field completeness, duplicates and tract intersection coverage are in companion tables. LARIAC6 provides independent observed roof geometry; school attributes are not propagated to its millions of buildings. No API/image predictions or new R2D analysis was run.']
 (OUT/'R2D_BRAILS_INVENTORY_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print('R2D_AUDIT',len(rows),flush=True)
if __name__=='__main__':run()
