"""Source-bounded physical context overlays; unknown coverage stays unknown."""
import argparse
import shutil
import zipfile
import geopandas as gpd
import shapely
from shapely.geometry import Point
from common import *

S=OUT/'sources'


def read_layer(name):
    p=lp(S/(name+'_COMPLETE.geojson'))
    if p.exists():
        content=p.read_bytes()
    else:
        with zipfile.ZipFile(lp(S/'PHYSICAL_SOURCE_SNAPSHOTS.zip')) as z:
            content=z.read(name+'_COMPLETE.geojson')
    g=gpd.GeoDataFrame.from_features(json.loads(content)['features'],crs=4326).to_crs(3310)
    invalid=int((~g.is_valid).sum());empty=int(g.geometry.is_empty.sum())
    g.geometry=g.geometry.make_valid()
    assert g.geometry.notna().all()
    return g,dict(layer=name,features=len(g),invalid_source_geometries=invalid,empty_source_geometries=empty,
        source_sha256=hashlib.sha256(content).hexdigest(),working_crs='EPSG:3310',repair='make_valid, source bytes unchanged')


def area_and_point(tracts,geoms,points):
    tree=shapely.STRtree(geoms);area=[];point=[]
    for geom,p in zip(tracts.geometry,points):
        ids=tree.query(geom,predicate='intersects')
        a=shapely.union_all(shapely.intersection(geoms[ids],geom)).area if len(ids) else 0.
        area.append(a/geom.area if geom.area>0 else np.nan)
        point.append(bool(len(tree.query(p,predicate='intersects'))))
    return np.asarray(area),np.asarray(point)


def geometry(s,full):
    if lp(S/'TRACT_LAND_3310.gpkg').exists():
        return gpd.read_file(lp(S/'TRACT_LAND_3310.gpkg')).set_index('tract_id').reindex(full.index)
    for ext in ['shp','shx','dbf','prj']:s.source('Data/LA_Tracts_With_Population.'+ext,AUTH)
    original=gpd.read_file(s.source('Data/LA_Tracts_With_Population.shp',AUTH));original['tract_id']=original.GEOID.astype(str)
    original=original.set_index('tract_id').reindex(full.index).to_crs(3310)
    assert original.geometry.notna().all() and original.index.str.fullmatch(r'\d{11}').all()
    water=SOURCE_ROOT/(BE+'local_joint_feature_extraction_20261009/sources/tl_2020_06037_areawater.zip')
    dest=lp(S/'tl_2020_06037_areawater.zip');shutil.copyfile(lp(water),dest)
    w=gpd.read_file('zip://'+str(dest)).to_crs(3310);w.geometry=w.geometry.make_valid()
    tree=shapely.STRtree(w.geometry.to_numpy());geoms=[];qa=[]
    for key,row in original.iterrows():
        raw=row.geometry;valid=shapely.make_valid(raw);ids=tree.query(valid,predicate='intersects')
        water_clip=shapely.union_all(shapely.intersection(w.geometry.iloc[ids].to_numpy(),valid))
        land=shapely.difference(valid,water_clip);geoms.append(land)
        qa.append(dict(tract_id=key,original_valid=raw.is_valid,land_valid=land.is_valid,
            original_area_m2=raw.area,land_area_m2=land.area,water_removed_m2=water_clip.area,
            area_partition_residual_m2=land.area+water_clip.area-valid.area,empty_land=land.is_empty))
    land=gpd.GeoDataFrame({'tract_id':original.index},geometry=geoms,crs=3310).set_index('tract_id')
    assert land.is_valid.all() and land.area.gt(0).all()
    save('TRACT_GEOMETRY_LAND_WATER_QA.csv',qa)
    land.reset_index().to_file(lp(S/'TRACT_LAND_3310.gpkg'),driver='GPKG')
    original.reset_index()[['tract_id','geometry']].to_file(lp(S/'TRACT_FULL_3310.gpkg'),driver='GPKG')
    dump('sources/TIGER_WATER_SOURCE_RECORD.json',dict(original_url='https://www2.census.gov/geo/tiger/TIGER2020/AREAWATER/tl_2020_06037_areawater.zip',
        origin='cached prior official-source snapshot; no fresh network byte check in this round',
        sha256=sha(dest),bytes=dest.stat().st_size,geographic_vintage=2020,no_tract_exclusions=True))
    return land


def main():
    a=argparse.ArgumentParser();a.add_argument('--phase',choices=['base','flood'],default='base');args=a.parse_args()
    s=sources();full,d=dataset(s);g=geometry(s,full);g=g.reindex(d.index)
    fullgeom=gpd.read_file(lp(S/'TRACT_FULL_3310.gpkg')).set_index('tract_id').reindex(d.index)
    points=fullgeom.geometry.centroid.to_numpy()
    internal=gpd.GeoSeries([Point(x,y) for x,y in zip(d.INTPTLON,d.INTPTLAT)],crs=4326).to_crs(3310).to_numpy()
    result=pd.DataFrame(index=d.index);geometry_records=[]
    if args.phase=='base':
        pgarel=BE+'local_joint_feature_extraction_20261009/TRACT_SEISMIC_HAZARD.csv'
        pga=frozen(s,pgarel).set_index('tract_id').reindex(d.index)
        save('FROZEN_PGA_TRACT_EXTRACTION_SOURCE.csv',pga.reset_index())
        for c in ['tract_seismic_PGA','PGA_land_grid_coverage','PGA_centroid_IDW_g','PGA_partial_support_estimate_g']:
            result[c]=pga[c]
        for name in ['CALFIRE_SRA','CALFIRE_LRA','CALFIRE_RESPONSIBILITY']:
            layer,qa=read_layer(name);geometry_records.append(qa)
            if name.endswith('RESPONSIBILITY'):
                for responsibility,subset in layer.groupby('SRA'):
                    f,p=area_and_point(g,subset.geometry.to_numpy(),points)
                    result['Fire_responsibility_'+responsibility+'_land_fraction']=f
            else:
                for code in sorted(layer.FHSZ.unique()):
                    subset=layer.loc[layer.FHSZ.eq(code)]
                    f,p=area_and_point(g,subset.geometry.to_numpy(),points)
                    result[name+'_class_'+str(int(code))+'_land_fraction']=f
                    result[name+'_class_'+str(int(code))+'_centroid_flag']=p
        fire=pd.concat([read_layer('CALFIRE_SRA')[0],read_layer('CALFIRE_LRA')[0]],ignore_index=True)
        mapped,point_mapped=area_and_point(g,fire.geometry.to_numpy(),points)
        high,p=area_and_point(g,fire.loc[fire.FHSZ.isin([2,3])].geometry.to_numpy(),points)
        _,ip=area_and_point(g,fire.loc[fire.FHSZ.isin([2,3])].geometry.to_numpy(),internal)
        _,internal_mapped=area_and_point(g,fire.geometry.to_numpy(),internal)
        result['Wildfire_FHSZ_mapped_land_fraction']=mapped
        result['Wildfire_high_land_fraction_lower_bound']=high
        result['Wildfire_high_land_fraction']=np.where(mapped>=1-1e-6,high,np.nan)
        result['Wildfire_high_centroid_flag']=np.where(point_mapped,p,np.nan)
        result['Wildfire_high_internalpoint_flag']=np.where(internal_mapped,ip,np.nan)
        heat=pd.read_csv(lp(S/'CDC_EJI_HEAT_RAW_LA.csv'),dtype={'GEOID':str,'GEOID_2020':str})
        assert heat.GEOID_2020.is_unique and heat.GEOID.eq(heat.GEOID_2020).all()
        heat=heat.set_index('GEOID_2020').reindex(d.index)
        result['Historical_heat_days_2018_2022']=heat.E_NEHD.where(heat.E_NEHD.ge(0))
        result['Historical_heat_national_percentile']=heat.EPL_NEHD
        result['Heat_source_geoid_matched']=heat.E_NEHD.notna()
        assert len(result)==2299
        save('PHYSICAL_HAZARD_TRACT_VALUES_BASE.csv',result.reset_index())
    else:
        zones,qa=read_layer('NFHL_ZONES');geometry_records.append(qa)
        availability,qa=read_layer('NFHL_AVAILABILITY');geometry_records.append(qa)
        coverage,_=area_and_point(g,availability.geometry.to_numpy(),points)
        result['NFHL_availability_land_fraction']=coverage
        zone=zones.FLD_ZONE.fillna('').str.upper();sfha=zones.SFHA_TF.fillna('').str.upper().eq('T')
        definitions={'all_polygons':pd.Series(True,index=zones.index),'undetermined_D':zone.eq('D'),
            'known_zones':~zone.isin(['D','']),'SFHA':sfha,
            'coastal_V':zone.str.startswith('V'),'A_family':zone.str.startswith('A'),
            '0p2pct_band':zones.ZONE_SUBTY.fillna('').str.contains('0.2 PCT',case=False)}
        for name,mask in definitions.items():
            f,p=area_and_point(g,zones.loc[mask].geometry.to_numpy(),points)
            _,ip=area_and_point(g,zones.loc[mask].geometry.to_numpy(),internal)
            result['Flood_'+name+'_land_fraction']=f;result['Flood_'+name+'_centroid_flag']=p
            result['Flood_'+name+'_internalpoint_flag']=ip
        known=result.Flood_known_zones_land_fraction
        result['Flood_SFHA_land_fraction_complete']=result.Flood_SFHA_land_fraction.where(known>=1-1e-6)
        save('PHYSICAL_HAZARD_TRACT_VALUES_FLOOD.csv',result.reset_index())
        save('NFHL_ZONE_CLASS_COUNTS.csv',zones.groupby(['FLD_ZONE','ZONE_SUBTY','SFHA_TF'],dropna=False).size().rename('features').reset_index())
    save('SOURCE_GEOMETRY_QA_'+args.phase.upper()+'.csv',geometry_records)
    save('SCIENTIFIC_INPUT_HASHES_PHYSICAL_'+args.phase.upper()+'.csv',s.records)
    print(args.phase,'overlay complete',result.shape,flush=True)


if __name__=='__main__':main()
