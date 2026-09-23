"""July92 IDW with explicit utility eligibility; never rebuilds topology."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx

ROOT = Path(__file__).resolve().parent
BASELINE_PATH = ROOT/'Data/tract_to_substation_mapping_CEC_expanded.csv'
REVISED_PATH = ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv'
REVISED_RAW_PATH = ROOT/'Data/JULY_UTILITY_CONSTRAINED_92_UNTHRESHOLDED.csv'


def threshold_weights(raw, cutoff=.03):
    if not 0 <= cutoff < 1:
        raise ValueError('Invalid cutoff')
    x = raw.to_numpy(float)
    if not np.isfinite(x).all() or (x < 0).any() or not np.allclose(x.sum(axis=1), 1):
        raise ValueError('Raw mapping must be normalized and finite')
    out = x.copy()
    out[out < cutoff] = 0
    empty = out.sum(axis=1) == 0
    for i in np.flatnonzero(empty):
        out[i, np.argmax(x[i])] = 1  # unchanged July cutoff fallback
    out /= out.sum(axis=1)[:, None]
    return pd.DataFrame(out, index=raw.index, columns=raw.columns)


def load_mapping(path):
    x = pd.read_csv(path, dtype={'tract_id': str, 'substation_id': str})
    if x.duplicated(['tract_id', 'substation_id']).any():
        raise ValueError('Duplicate mapping identity')
    return x.pivot(index='tract_id', columns='substation_id', values='weight').fillna(0)


def generate_mapping(*, utility_constrained=True, cutoff=.03):
    """Read frozen 92/318 inputs; return labelled matrix, including all IDs."""
    s = pd.read_csv(ROOT/'Data/working_area_substations_with_fragility.csv', dtype={'ID': str}).set_index('ID')
    t = pd.read_csv(ROOT/'Data/Tracts_Within_Expanded_Area.csv', dtype={'GEOID': str})
    e = pd.read_csv(ROOT/'Data/substation_graph_CEC_edges_expanded.csv', dtype={'u': str, 'v': str})
    if len(s) != 92 or len(e) != 318 or len(t) != 2315:
        raise ValueError('Not the frozen July domain')
    G = nx.from_pandas_edgelist(e, 'u', 'v', 'length_km')
    if set(G) != set(s.index):
        raise ValueError('Graph/station mismatch')
    # Freeze the previously benchmarked CEC territory classification, not new geography.
    domains = pd.read_csv(ROOT/'R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv', dtype={'tract_id': str}).set_index('tract_id').utility_domain.reindex(t.GEOID)
    if domains.isna().any():
        raise ValueError('Missing utility classification')
    xy = gpd.GeoSeries(gpd.points_from_xy(s.LONGITUDE, s.LATITUDE), crs=4326).to_crs(3310)
    centroids = gpd.GeoSeries.from_wkt(t.wkt_geom, crs=4326).to_crs(3310).centroid
    ds = dict(nx.all_pairs_dijkstra_path_length(G, weight='length_km'))
    rows = []
    for c, domain in zip(centroids, domains):
        eligible = s.Owner.eq(domain).to_numpy() if utility_constrained and domain in {'SCE', 'LADWP'} else np.ones(len(s), bool)
        if not eligible.any():
            raise ValueError('No compatible candidate; no nearest fallback')
        euclid = xy.distance(c).to_numpy()/1000
        access = np.flatnonzero(eligible)[np.argmin(euclid[eligible])]
        distance = np.array([ds[s.index[access]].get(sid, np.inf) for sid in s.index]) + euclid[access]
        valid = eligible & np.isfinite(distance)
        weights = np.zeros(len(s))
        weights[valid] = 1/np.maximum(distance[valid], .001)**2
        weights /= weights.sum()
        rows.append(weights)
    raw = pd.DataFrame(rows, index=pd.Index(t.GEOID, name='tract_id'), columns=pd.Index(s.index, name='substation_id'))
    return threshold_weights(raw, cutoff), raw


def export_long(matrix, path):
    x = matrix.rename_axis(index='tract_id', columns='substation_id').stack().rename('weight').reset_index()
    x = x[x.weight > 0]
    metadata = pd.read_csv(ROOT/'Data/Tracts_Within_Expanded_Area.csv', dtype={'GEOID': str}).set_index('GEOID')
    original = pd.read_csv(BASELINE_PATH, dtype={'tract_id': str})
    population = original.drop_duplicates('tract_id').set_index('tract_id').population
    x['population'] = x.tract_id.map(population)
    stations = pd.read_csv(ROOT/'Data/working_area_substations_with_fragility.csv', dtype={'ID': str}).set_index('ID')
    x['lat'] = x.substation_id.map(stations.LATITUDE)
    x['lon'] = x.substation_id.map(stations.LONGITUDE)
    x.to_csv(path, index=False)


if __name__ == '__main__':
    revised, raw = generate_mapping()
    retained = load_mapping(ROOT/'R1_Comment1_July92_Utility_Constraint/JULY_UTILITY_CONSTRAINED_92.csv').reindex(index=revised.index, columns=revised.columns, fill_value=0)
    np.testing.assert_allclose(revised, retained, rtol=0, atol=1e-12)
    export_long(revised, REVISED_PATH)
    export_long(raw, REVISED_RAW_PATH)
    print('Revised mapping generated; max retained difference', np.max(np.abs(revised.to_numpy()-retained.to_numpy())))
