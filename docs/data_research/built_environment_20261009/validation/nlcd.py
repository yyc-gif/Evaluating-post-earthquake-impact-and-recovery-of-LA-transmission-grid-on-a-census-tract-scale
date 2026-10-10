"""Download numeric 2022 MRLC WCS coverages and audit exact tract aggregation."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
import argparse
import json
import hashlib
import math
import shutil
import requests
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.windows import from_bounds
from rasterio.features import geometry_mask
from exactextract import exact_extract
from shapely.geometry import box

ROOT = Path(__file__).resolve().parent
STAGE7 = 'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized'
PRODUCTS = {'fis': 'Fractional-Impervious-Surface', 'lc': 'Land-Cover'}
SERVICES = {'fis':'USA_NLCD_Annual_LandCover_Fractional_Impervious_Surface', 'lc':'USA_NLCD_Annual_LandCover'}

def shapes(repo, crs=5070):
    ids = pd.read_csv(repo / STAGE7 / 'stage7_full_domain_tract_status.csv', dtype={'tract_id': str})
    ids['tract_id'] = ids.tract_id.str.zfill(11)
    g = gpd.read_file(repo / 'Data/LA_Tracts_With_Population.shp').rename(columns={'GEOID': 'tract_id'})
    assert not g.tract_id.duplicated().any() and g.geometry.is_valid.all()
    g = g.merge(ids[['tract_id']], on='tract_id', validate='one_to_one').sort_values('tract_id').reset_index(drop=True)
    assert len(g) == 2315 and set(g.tract_id) == set(ids.tract_id)
    return g.to_crs(crs)

def mirror_metadata(product):
    base=f'https://di-nlcd.img.arcgis.com/arcgis/rest/services/{SERVICES[product]}/ImageServer'
    metadata=requests.get(base,params={'f':'pjson'},timeout=60).json()
    catalog=requests.get(base+'/query',params={'f':'pjson','where':'Year=2022 AND Category=1','outFields':'*','returnGeometry':'false'},timeout=60).json()
    assert 'error' not in metadata and 'error' not in catalog
    assert len(catalog['features'])==1
    for label,obj in [('service',metadata),('2022_catalog',catalog)]:
        (ROOT/f'sources/Esri_{product}_{label}.json').write_text(json.dumps(obj,indent=2),encoding='utf8')
    return base,metadata,catalog['features'][0]['attributes']

def mirror_request(product,bounds,metadata=None,attributes=None):
    base=f'https://di-nlcd.img.arcgis.com/arcgis/rest/services/{SERVICES[product]}/ImageServer'
    if metadata is None:base,metadata,attributes=mirror_metadata(product)
    wkt=metadata['spatialReference']['wkt']
    params={'f':'json','bbox':','.join(map(str,bounds)), 'bboxSR':json.dumps({'wkt':wkt}), 'imageSR':json.dumps({'wkt':wkt}),
            'size':f'{round((bounds[2]-bounds[0])/30)},{round((bounds[3]-bounds[1])/30)}','format':'tiff','pixelType':'U8',
            'interpolation':'RSP_NearestNeighbor','adjustAspectRatio':'false','noData':'250',
            'mosaicRule':json.dumps({'mosaicMethod':'esriMosaicLockRaster','lockRasterIds':[attributes['OBJECTID']],'mosaicOperation':'MT_FIRST'}),
            'renderingRule':json.dumps({'rasterFunction':'None'})}
    res=requests.get(base+'/exportImage',params=params,timeout=(20,240));res.raise_for_status()
    reply=res.json(); assert 'error' not in reply,reply
    image_response=requests.get(reply['href'],timeout=(20,240));image_response.raise_for_status()
    data=image_response.content;assert data[:2] in (b'II',b'MM')
    return data,{'export_url':res.url,'export_response':reply,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
                'product':product,'year':2022,'retrieved':'2026-10-09','catalog_attributes':attributes,'host':'Esri numeric mirror of USGS Annual NLCD C1.0'}

def mirror_fetch(repo):
    log=[]
    for product in PRODUCTS:
        base,meta,attr=mirror_metadata(product)
        assert attr['Year']==2022 and attr['Name'].endswith('_2022_CU_C1V0')
        assert attr['Version'] in ['Annual NLCD Collection 1.0: 1985 - 2023','Annual NLCD Collction 1.0: 1985 - 2023']
        g=shapes(repo,meta['spatialReference']['wkt']);b=g.total_bounds
        origin=(-2415585,3314805)
        bounds=[origin[0]+30*math.floor((b[0]-origin[0])/30)-60,origin[1]+30*math.floor((b[1]-origin[1])/30)-60,
                origin[0]+30*math.ceil((b[2]-origin[0])/30)+60,origin[1]+30*math.ceil((b[3]-origin[1])/30)+60]
        file=ROOT/f'sources/Annual_NLCD_2022_{product}_study_clip.tif'
        data,record=mirror_request(product,bounds,meta,attr)
        file.write_bytes(data)
        with MemoryFile(data) as mem,mem.open() as src:
            record.update(crs=src.crs.to_wkt(),transform=list(src.transform),shape=list(src.shape),bands=src.count,
                          dtype=src.dtypes[0],nodata=src.nodata,tags=src.tags(),values=np.unique(src.read(1)).tolist(),file='sources/'+file.name)
            assert src.count==1 and src.dtypes[0]=='uint8' and np.allclose(src.res,(30,30),atol=1e-5)
        log.append(record)
        (ROOT/'NLCD_ACQUISITION.json').write_text(json.dumps(log,indent=2),encoding='utf8');print(json.dumps(record),flush=True)

def request(product, bounds):
    name = PRODUCTS[product] + '-Native_conus_year_data'
    url = f'https://dmsdata.cr.usgs.gov/geoserver/mrlc_{name}/wcs'
    params = [('service', 'WCS'), ('version', '2.0.1'), ('request', 'GetCoverage'),
              ('coverageId', f'mrlc_{name}__{name}'), ('format', 'image/tiff'),
              ('subset', f'X({bounds[0]},{bounds[2]})'),
              ('subset', f'Y({bounds[1]},{bounds[3]})'),
              ('subset', 'time("2022-01-01T00:00:00.000Z")')]
    res = requests.get(url, params=params, timeout=(20, 240))
    res.raise_for_status()
    assert res.content[:2] in (b'II', b'MM'), res.text[:2000]
    return res.content, {'url': res.url, 'content_type': res.headers.get('Content-Type'),
                         'sha256': hashlib.sha256(res.content).hexdigest(), 'bytes': len(res.content),
                         'product': product, 'year': 2022, 'retrieved': '2026-10-09'}

def fetch(repo):
    g = shapes(repo)
    b = g.total_bounds
    origin = (-2415585, 3314805)
    bounds = [origin[0] + 30 * math.floor((b[0]-origin[0])/30)-60,
              origin[1] + 30 * math.floor((b[1]-origin[1])/30)-60,
              origin[0] + 30 * math.ceil((b[2]-origin[0])/30)+60,
              origin[1] + 30 * math.ceil((b[3]-origin[1])/30)+60]
    log = []
    for product in PRODUCTS:
        file = ROOT / f'sources/Annual_NLCD_2022_{product}_study_clip.tif'
        if file.exists():
            print(f'Cached {file.name}', flush=True)
            continue
        data, record = request(product, bounds)
        file.write_bytes(data)
        with MemoryFile(data) as mem, mem.open() as src:
            record.update(crs=src.crs.to_string(), transform=list(src.transform),
                          shape=list(src.shape), bands=src.count, dtype=src.dtypes[0], nodata=src.nodata,
                          tags=src.tags(), band_tags=src.tags(1), file='sources/' + file.name)
            assert src.count == 1 and src.dtypes[0] == 'uint8'
            assert np.allclose(src.res, (30,30), atol=1e-5) and src.crs.to_epsg() == 5070
            vals = np.unique(src.read(1))
            record['values'] = vals.tolist()
        log.append(record)
        (ROOT/'NLCD_ACQUISITION.json').write_text(json.dumps(log, indent=2), encoding='utf8')
        print(json.dumps(record), flush=True)

def aggregate(repo):
    paths = {p: ROOT / f'sources/Annual_NLCD_2022_{p}_study_clip.tif' for p in PRODUCTS}
    with rasterio.open(paths['fis']) as f, rasterio.open(paths['lc']) as l:
        assert f.count==l.count==1 and np.allclose(f.res,(30,30))
        g = shapes(repo, f.crs)
        assert f.transform == l.transform and f.shape == l.shape and f.crs == l.crs
        fis, lc = f.read(1), l.read(1)
        assert set(np.unique(fis)) <= set(range(101)) | {250}
        assert set(np.unique(lc)) <= {11,12,21,22,23,24,31,41,42,43,52,71,81,82,90,95,250}
        valid = (fis <= 100) & (lc != 250)
        water = (lc == 11) & valid
        land = valid & ~water
        masks = {'valid':valid, 'water':water, 'land':land, 'missing':~valid}
        derived = {}
        for key, mask in masks.items():
            dest = ROOT / f'_mask_{key}.tif'
            with rasterio.open(dest, 'w', **dict(f.profile, nodata=None, compress='deflate')) as d:
                d.write(mask.astype('uint8'),1)
            derived[key] = dest
        land_fis = ROOT / '_land_fis.tif'
        with rasterio.open(land_fis, 'w', **dict(f.profile, nodata=250, compress='deflate')) as d:
            d.write(np.where(land, fis, 250).astype('uint8'),1)
        total = exact_extract(str(paths['fis']), g, ['count','mean','sum'], include_cols=['tract_id'], output='pandas')
        out = g[['tract_id','ALAND','AWATER']].copy()
        out['geometry_area_m2'] = g.geometry.area
        for key, path in derived.items():
            table = exact_extract(str(path), g, ['sum'], output='pandas')
            out[f'{key}_area_m2'] = table['sum'].to_numpy()*900
        means = exact_extract(str(land_fis), g, ['count','mean','sum'], output='pandas')
        out['impervious_land_fraction'] = means['mean'].to_numpy()/100
        out['impervious_whole_tract_valid_fraction'] = total['mean'].to_numpy()/100
        out['impervious_area_m2'] = means['sum'].to_numpy()*9
        out['land_valid_pixel_equivalents'] = means['count'].to_numpy()
        out['valid_coverage_fraction'] = out.valid_area_m2 / out.geometry_area_m2
        out['land_mask_fraction'] = out.land_area_m2 / out.geometry_area_m2
        out['water_mask_fraction'] = out.water_area_m2 / out.geometry_area_m2
        out['coverage_status'] = np.where(out.valid_coverage_fraction >= .99, 'pass_ge_99pct', 'incomplete_lt_99pct')
        center_means=[]; touched_means=[]
        for geom in g.geometry:
            w=from_bounds(*geom.bounds,transform=f.transform)
            r0=max(0,math.floor(w.row_off));r1=min(f.height,math.ceil(w.row_off+w.height))
            c0=max(0,math.floor(w.col_off));c1=min(f.width,math.ceil(w.col_off+w.width))
            transform=f.window_transform(rasterio.windows.Window(c0,r0,c1-c0,r1-r0))
            v=fis[r0:r1,c0:c1];ok=land[r0:r1,c0:c1]
            for touched,dest in [(False,center_means),(True,touched_means)]:
                mask=geometry_mask([geom],out_shape=v.shape,transform=transform,invert=True,all_touched=touched)&ok
                dest.append(float(v[mask].mean()/100) if mask.any() else np.nan)
        out['center_cell_land_fraction']=center_means
        out['all_touched_land_fraction']=touched_means
        out['center_minus_exact']=out.center_cell_land_fraction-out.impervious_land_fraction
        out['all_touched_minus_exact']=out.all_touched_land_fraction-out.impervious_land_fraction
        out['water_mask_mean_change']=out.impervious_land_fraction-out.impervious_whole_tract_valid_fraction
        assert np.allclose(out.valid_area_m2 + out.missing_area_m2, out.geometry_area_m2, rtol=2e-6)
        assert np.allclose(out.land_area_m2 + out.water_area_m2, out.valid_area_m2, rtol=1e-8)
        assert out.impervious_land_fraction.between(0,1).all()
        out.to_csv(ROOT/'NLCD_TRACT_EXTRACTION.csv',index=False)
        # Independent polygon-cell intersections, deliberately using no exactextract.
        checks=[]
        sample = pd.concat([g.loc[g.geometry.area.nsmallest(8).index], g.sample(8,random_state=20261009)]).drop_duplicates('tract_id')
        for _,row in sample.iterrows():
            geom=row.geometry
            window=from_bounds(*geom.bounds,transform=f.transform)
            r0=max(0,math.floor(window.row_off)); r1=min(f.height,math.ceil(window.row_off+window.height))
            c0=max(0,math.floor(window.col_off)); c1=min(f.width,math.ceil(window.col_off+window.width))
            numer=denom=0.
            for rr in range(r0,r1):
                for cc in range(c0,c1):
                    if not land[rr,cc]:
                        continue
                    x,y=f.transform*(cc,rr)
                    area=geom.intersection(box(x,y-30,x+30,y)).area
                    denom+=area; numer+=area*fis[rr,cc]/100
            exact=float(out.loc[out.tract_id.eq(row.tract_id),'impervious_land_fraction'].iloc[0])
            center=geometry_mask([geom],out_shape=(r1-r0,c1-c0),transform=f.window_transform(rasterio.windows.Window(c0,r0,c1-c0,r1-r0)),invert=True)
            touched=geometry_mask([geom],out_shape=center.shape,transform=f.window_transform(rasterio.windows.Window(c0,r0,c1-c0,r1-r0)),invert=True,all_touched=True)
            v=fis[r0:r1,c0:c1]; ok=land[r0:r1,c0:c1]
            checks.append({'tract_id':row.tract_id,'cells_in_bbox':(r1-r0)*(c1-c0),'exact_mean':exact,
                           'independent_intersection_mean':numer/denom,'absolute_difference':abs(exact-numer/denom),
                           'center_cell_mean':float(v[ok&center].mean()/100),'all_touched_mean':float(v[ok&touched].mean()/100)})
        check=pd.DataFrame(checks)
        assert check.absolute_difference.max()<1e-6
        check.to_csv(ROOT/'NLCD_AGGREGATION_CHECKS.csv',index=False)
        repeat=exact_extract(str(land_fis),g,['mean'],output='pandas')['mean'].to_numpy()/100
        assert np.array_equal(repeat, out.impervious_land_fraction.to_numpy())
        summary={'study_n':len(g),'geoid_unmatched':0,'valid_coverage_min':float(out.valid_coverage_fraction.min()),
                 'land_fraction_nonmissing':int(out.impervious_land_fraction.notna().sum()),'coverage_ge_99pct_n':int(out.valid_coverage_fraction.ge(.99).sum()),
                 'nodata_area_m2':float(out.missing_area_m2.sum()), 'water_excluded_area_m2':float(out.water_area_m2.sum()),
                 'max_independent_difference':float(check.absolute_difference.max()),'repeat_bitwise_equal':True,
                 'crs':f.crs.to_string(),'resolution_m':list(f.res), 'geometry_crs_original':'EPSG:4269',
                 'valid_codes':'FIS 0..100; LC != 250; exclude LC 11 only for land mean',
                 'smallest_land_cell_equivalents':float(out.land_valid_pixel_equivalents.min()),
                 'center_abs_difference_max_pp':float(out.center_minus_exact.abs().max()*100),
                 'center_abs_difference_p95_pp':float(out.center_minus_exact.abs().quantile(.95)*100),
                 'all_touched_abs_difference_max_pp':float(out.all_touched_minus_exact.abs().max()*100),
                 'all_touched_abs_difference_p95_pp':float(out.all_touched_minus_exact.abs().quantile(.95)*100),
                 'water_mask_mean_change_max_pp':float(out.water_mask_mean_change.abs().max()*100),
                 'collection_build':'Collection 1.0: 1985-2023, pinned 2022 catalog object; downloaded from Esri numeric mirror; not C1.2',
                 'publication_status':'CONDITIONAL: source mirror has explicit beta/not-recommended-for-production notice; direct USGS reference validation remains open'}
        (ROOT/'NLCD_VERIFICATION.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
        print(json.dumps(summary),flush=True)

def reference(repo,fis_path,lc_path,out,build,pilot_root):
    global ROOT
    assert fis_path.is_file() and lc_path.is_file()
    assert not out.exists(), 'Use a new reference output directory'
    ROOT=out.resolve();(ROOT/'sources').mkdir(parents=True)
    provenance={'declared_build':build,'provenance_status':'USER_SUPPLIED_REFERENCE_REQUIRES_DOCUMENT_REVIEW',
                'source_files':{},'pilot_directory':str(pilot_root)}
    for product,path in [('fis',fis_path),('lc',lc_path)]:
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
        provenance['source_files'][product]={'path':str(path.resolve()),'sha256':digest.hexdigest()}
        with rasterio.open(path) as src:
            assert src.count==1 and np.allclose(src.res,(30,30))
            assert src.crs.is_projected and 'Albers' in src.crs.to_wkt()
            g=shapes(repo,src.crs);win=from_bounds(*g.total_bounds,transform=src.transform)
            r0=max(0,math.floor(win.row_off)-2);c0=max(0,math.floor(win.col_off)-2)
            r1=min(src.height,math.ceil(win.row_off+win.height)+2);c1=min(src.width,math.ceil(win.col_off+win.width)+2)
            win=rasterio.windows.Window(c0,r0,c1-c0,r1-r0)
            profile=dict(src.profile,width=int(win.width),height=int(win.height),transform=src.window_transform(win),compress='deflate')
            dest=ROOT/f'sources/Annual_NLCD_2022_{product}_study_clip.tif'
            with rasterio.open(dest,'w',**profile) as target:target.write(src.read(window=win))
    aggregate(repo)
    verification=json.loads((ROOT/'NLCD_VERIFICATION.json').read_text())
    verification.update(collection_build=build,publication_status='REFERENCE_EXTRACTION_ONLY: provenance documents and version comparison require review')
    (ROOT/'NLCD_VERIFICATION.json').write_text(json.dumps(verification,indent=2),encoding='utf8')
    (ROOT/'REFERENCE_PROVENANCE.json').write_text(json.dumps(provenance,indent=2),encoding='utf8')
    pilot=pd.read_csv(pilot_root/'NLCD_TRACT_EXTRACTION.csv',dtype={'tract_id':str})
    ref=pd.read_csv(ROOT/'NLCD_TRACT_EXTRACTION.csv',dtype={'tract_id':str})
    compare=pilot[['tract_id','impervious_land_fraction']].merge(ref[['tract_id','impervious_land_fraction']],on='tract_id',suffixes=('_pilot','_reference'),validate='one_to_one')
    assert len(compare)==2315
    compare['reference_minus_pilot']=compare.impervious_land_fraction_reference-compare.impervious_land_fraction_pilot
    compare.to_csv(ROOT/'REFERENCE_PILOT_COMPARISON.csv',index=False)

def repeat_download():
    path=ROOT/'sources/Annual_NLCD_2022_fis_study_clip.tif'
    with rasterio.open(path) as src:
        window=rasterio.windows.Window(500,500,128,128)
        bounds=rasterio.windows.bounds(window,src.transform)
        expected=src.read(1,window=window)
        data,record=mirror_request('fis',bounds)
        (ROOT/'sources/FIS_repeat_subwindow.tif').write_bytes(data)
        with MemoryFile(data) as mem,mem.open() as check:
            arr=check.read(1)
            record.update(expected_shape=list(expected.shape),actual_shape=list(arr.shape),transform=list(check.transform),
                          expected_transform=list(src.window_transform(window)),pixel_equal=bool(np.array_equal(arr,expected)))
        (ROOT/'NLCD_REPEAT_DOWNLOAD.json').write_text(json.dumps(record,indent=2),encoding='utf8')
        assert record['pixel_equal']
        print(json.dumps(record),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--repo',type=Path,required=True); p.add_argument('--phase',choices=['fetch','mirror','aggregate','repeat','reference'],required=True)
    p.add_argument('--fis-raster',type=Path);p.add_argument('--lc-raster',type=Path);p.add_argument('--reference-out',type=Path);p.add_argument('--reference-build')
    a=p.parse_args()
    if a.phase=='fetch':fetch(a.repo)
    elif a.phase=='mirror':mirror_fetch(a.repo)
    elif a.phase=='aggregate':aggregate(a.repo)
    elif a.phase=='repeat':repeat_download()
    else:
        if not all([a.fis_raster,a.lc_raster,a.reference_out,a.reference_build]):p.error('reference requires both rasters, a new output directory and the declared build')
        reference(a.repo,a.fis_raster,a.lc_raster,a.reference_out,a.reference_build,ROOT)
