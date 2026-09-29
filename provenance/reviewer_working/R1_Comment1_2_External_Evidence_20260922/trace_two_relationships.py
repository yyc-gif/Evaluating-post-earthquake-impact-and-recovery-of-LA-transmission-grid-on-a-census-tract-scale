"""Read-only local provenance trace; no topology generation or scientific execution."""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
s = pd.read_csv(ROOT/'Data/working_area_substations_with_fragility.csv', dtype={'ID': str}).set_index('ID')
xy = gpd.GeoSeries(gpd.points_from_xy(s.LONGITUDE, s.LATITUDE), index=s.index, crs=4326).to_crs(3310)
t = pd.read_csv(ROOT/'Data/Tracts_Within_Expanded_Area.csv', dtype={'GEOID': str})
tract = gpd.GeoSeries.from_wkt(t.wkt_geom, crs=4326).to_crs(3310).iloc[t.index[t.GEOID == '06037980028'][0]]
c = tract.centroid
edges = pd.read_csv(ROOT/'Data/substation_graph_CEC_edges_expanded.csv', dtype={'u': str, 'v': str})
# Read the existing 318-edge graph; do not build or infer new edges from geometry.
G = nx.from_pandas_edgelist(edges, 'u', 'v', 'length_km')
access = xy.distance(c).idxmin()
dist = nx.single_source_dijkstra_path_length(G, access, weight='length_km')
access_km = xy[access].distance(c)/1000
f = pd.DataFrame([dict(station_id=sid, name=s.loc[sid, 'NAME'], centroid_direct_km=xy[sid].distance(c)/1000,
    access_id=access, access_km=access_km, network_km=dist[sid], total_km=access_km+dist[sid],
    inverse_square=1/(access_km+dist[sid])**2) for sid in s.index])
f['precut_weight'] = f.inverse_square/f.inverse_square.sum()
f['survives_003'] = f.precut_weight >= .03
f['postcut_weight'] = f.precut_weight.where(f.survives_003, 0)
f.postcut_weight /= f.postcut_weight.sum()
f.to_csv(OUT/'LAX_MAPPING_STEP_TRACE.csv', index=False)

# The retained HTML contains the actual exported edge path, rounded to canvas pixels.
# Its source renderer is linear in lon/lat; inverse fitting is for locating raw vertices,
# not for creating new line geometry or asserting electrical connections.
h = (ROOT/'Data/topology_interactive_validation_expanded.html').read_text(encoding='utf-8')
a = json.JSONDecoder().raw_decode(h[re.search(r'const payload\s*=\s*', h).end():])[0]
n = a['main_nodes']
screen = np.array([[v['x'], v['y'], 1] for v in n])
lonlat = np.array([[s.loc[v['id'], 'LONGITUDE'], s.loc[v['id'], 'LATITUDE']] for v in n])
coef = np.linalg.lstsq(screen, lonlat, rcond=None)[0]
edge = next(v for v in a['direct_links'] if {v['src'], v['tgt']} == {'301105', '306694'})
(OUT/'COLORADO_RETAINED_HTML_PATH.json').write_text(json.dumps(edge, indent=2), encoding='utf-8')
ll = np.column_stack([np.array(edge['coords']), np.ones(len(edge['coords']))]) @ coef
pts = gpd.GeoSeries(gpd.points_from_xy(ll[:, 0], ll[:, 1]), crs=4326).to_crs(3310)
l = gpd.read_file(ROOT/'Data/TransmissionLine_CEC.shp').to_crs(3310)
line_ids = [5320, 5321, 5322, 5323]
q = l.loc[line_ids].copy()
q['distance_Colorado_m'] = q.distance(xy['306694'])
q['distance_RSK_m'] = q.distance(xy['301105'])
q['length_m'] = q.length
q['geometry_wkt'] = q.geometry.to_wkt()
q.drop(columns='geometry').to_csv(OUT/'COLORADO_CEC_LOCAL_LINE_TRACE.csv', index_label='CEC_row_index')
vertices = [(k, j, Point(v)) for k in [5320, 5322] for j, v in enumerate(l.loc[k].geometry.coords)]
rows = []
coords = [xy['306694'].coords[0]]
for i, p in enumerate(pts):
    k, j, v = min(vertices, key=lambda x: p.distance(x[2]))
    rows.append(dict(path_vertex=i, CEC_row=k, CEC_vertex=j, html_inverse_offset_m=p.distance(v)))
    if i not in [0, len(pts)-1]:
        coords.append(v.coords[0])
coords.append(xy['301105'].coords[0])
pd.DataFrame(rows).to_csv(OUT/'COLORADO_RAW_VERTEX_CORRESPONDENCE.csv', index=False)
# July graph keys round projected coordinates to 0.1 m. Checking the retained path
# against those same raw vertices is a local provenance calculation, not rerouting.
rounded = [(round(x, 1), round(y, 1)) for x, y in coords]
stored = float(edges[((edges.u == '301105') & (edges.v == '306694')) | ((edges.v == '301105') & (edges.u == '306694'))].length_km.iloc[0])
summary = dict(LAX_tract='06037980028', centroid_lonlat=list(gpd.GeoSeries([c], crs=3310).to_crs(4326).iloc[0].coords[0]),
    area_km2=tract.area/1e6, RSN=f[f.station_id == '301637'].iloc[0].to_dict(),
    Colorado_path_stored_m=stored*1000, Colorado_path_raw_vertices_rounded_m=LineString(rounded).length,
    path_difference_m=LineString(rounded).length-stored*1000,
    raw_lines_shared_endpoint_exact=list(l.loc[5320].geometry.coords[0]) == list(l.loc[5322].geometry.coords[0]),
    topology_regeneration=False, scientific_execution_count=0)
(OUT/'TWO_RELATIONSHIP_TRACE_VALUES.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
