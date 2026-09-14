"""R1 dry build only. No restoration model, sampler, dispatch or GA is imported.
Original topology functions are reused; shortest paths are streamed per source to
avoid retaining 310 path dictionaries. All original files remain read-only.
"""
import os,sys
sys.dont_write_bytecode=True
os.environ.setdefault("OMP_NUM_THREADS","1")
from pathlib import Path
import json,hashlib,pickle,tempfile,logging,io,collections,functools,argparse
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import shapely
from shapely.geometry import LineString
from scipy.spatial import cKDTree
OUT=Path(__file__).resolve().parent
ROOT=next(p for p in OUT.parents if (p/"Topology_and_Weight.py").is_file())
sys.path.insert(0,str(ROOT))
import Topology_and_Weight as topo
import topology_outputs as wmod
TMP=Path(tempfile.gettempdir())/"r1_310_drybuild_87d9b6c.pkl"
def safe(p):
    s=str(Path(p).resolve())
    return "\\\\?\\"+s if os.name=="nt" and not s.startswith("\\\\?\\") else s
def read(p,**kw):return pd.read_csv(safe(p),**kw)
def sha(p):return hashlib.sha256(Path(safe(p)).read_bytes()).hexdigest()
def frame_json(df):return json.loads(df.to_json(orient="records"))
def inputs():
    sel=read(OUT.parent/"04_Provenance_Decision_20260913/STATION_SELECTION_COMPARISON.csv",dtype={"ID":str})
    selected=sel[sel.new_R1_selected].sort_values("ID")
    master=read(ROOT.parent/"01_Source_Data/CA_substations_MERGED.csv",dtype={"ID":str})
    assert sha(ROOT.parent/"01_Source_Data/CA_substations_MERGED.csv")=="9036e1dbf192e853ff2fa30c615086f7f95f208bf1e314413c6aac8900ac90eb"
    d=master.set_index("ID").loc[selected.ID].reset_index()
    assert len(d)==310 and d.ID.nunique()==310
    assert selected.old_selected_92.sum()==83 and selected.key_15_station.sum()==15 and selected.existing_source_proxy.sum()==14
    # Preserve raw signed missing-value semantics, never the old +999999 artifact.
    for src,dest in [("MAX_VOLT","MAX_VOLT_N"),("MIN_VOLT","MIN_VOLT_N")]:
        d[dest]=pd.to_numeric(d[src],errors="coerce").replace(-999999,np.nan)
    d["voltage_for_fragility"]=d.MAX_VOLT_N
    d["id"]=d.ID.astype(str)
    for k in ["old_selected_92","key_15_station","existing_source_proxy","source_type"]:
        d[k]=d.ID.map(selected.set_index("ID")[k])
    subs=gpd.GeoDataFrame(d,geometry=gpd.points_from_xy(d.LONGITUDE,d.LATITUDE),crs=4326)
    wt=read(ROOT/"Data/Tracts_Within_Expanded_Area.csv",dtype={"GEOID":str})
    tracts=gpd.GeoDataFrame(wt,geometry=shapely.from_wkt(wt.wkt_geom.to_numpy()),crs=4326)
    tracts["tract_id"]=tracts.GEOID.str.zfill(11)
    assert len(tracts)==2315 and tracts.geometry.is_valid.all()
    frozen=[ROOT/"Topology_and_Weight.py",ROOT/"topology_outputs.py",ROOT/"IDW.py",
            ROOT/"Data/working_area_substations_with_fragility.csv",
            ROOT/"Data/substation_graph_CEC_edges_expanded.csv",
            ROOT/"Data/tract_to_substation_mapping_CEC_expanded.csv",
            ROOT/"Data/Tracts_Within_Expanded_Area.csv",
            ROOT/"Data/source_nodes_core_expanded.csv"]
    frozen += list((ROOT/"Data").glob("TransmissionLine_CEC.*"))
    meta={"station_set_hash_format":"sorted IDs joined by newline, trailing newline, UTF-8",
          "station_set_sha256":hashlib.sha256(("\n".join(d.ID)+"\n").encode()).hexdigest(),
          "station_input_sha256":hashlib.sha256(d.drop(columns=[],errors="ignore").to_csv(index=False).encode()).hexdigest(),
          "selection_comparison_sha256":sha(OUT.parent/"04_Provenance_Decision_20260913/STATION_SELECTION_COMPARISON.csv"),
          "frozen_input_hashes":{str(p.relative_to(ROOT)):sha(p) for p in frozen},
          "old_only":frame_json(sel[sel.set_comparison=="old_only"])}
    return subs,tracts,meta

def build():
    if TMP.exists():raise RuntimeError("Existing dry-build checkpoint: inspect before replacing it.")
    subs,tracts,meta=inputs()
    captures={}; counts=collections.Counter();stream=io.StringIO()
    log=logging.getLogger();log.setLevel(logging.INFO)
    lh=logging.StreamHandler(stream);log.addHandler(lh)
    ch=logging.StreamHandler(sys.stdout);log.addHandler(ch)
    originals={}
    for name in ["force_snap_endpoints_to_substations","snap_protected_junction_clusters_to_substations","merge_nearby_line_endpoints"]:
        f=getattr(topo,name);originals[name]=f
        def capture(*a,_f=f,_name=name,**kw):
            ans=_f(*a,**kw);captures[_name]=ans[1]
            return ans
        setattr(topo,name,capture)
    for name in ["_split_candidate_compatible_with_substation_voltage","_split_candidate_compatible_with_endpoint_snaps"]:
        f=getattr(topo,name);originals[name]=f
        def guard(*a,_f=f,_name=name,**kw):
            ans=_f(*a,**kw);counts[_name+"|"+str(ans[1])]+=1
            return ans
        setattr(topo,name,guard)
    cfg=topo.Paths(OUTPUT_LINE_SPLIT_AUDIT_CSV=None,
                  OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_AUDIT_CSV=None,
                  OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_DEBUG_CSV=None)
    G,lines,sp,raw,split=topo.build_topology_wrapper(cfg,str(ROOT/"Data/TransmissionLine_CEC.shp"),subs,
        cfg.BBOX_PAD_KM,cfg.LINE_SNAP_TOLERANCE_M,cfg.LINE_SNAP_SECONDARY_TOLERANCE_M,
        cfg.LINE_SNAP_SECONDARY_MARGIN_M,cfg.LINE_SNAP_SECONDARY_RATIO_MAX)
    for n,f in originals.items():setattr(topo,n,f)
    assert G is not None
    P=topo._collapse_multigraph_min_weight(G)
    # Identical nearest-node registration to calculate_connectivity L2225 onward.
    nodes=list(P); xy=np.array([topo._node_xy(n) for n in nodes]); tree=cKDTree(xy)
    sn={};reg=[];node_sigs=collections.defaultdict(set)
    for _,lr in lines.iterrows():
        sig=topo._line_topology_signature(lr,topo._detect_voltage_column(lines))
        for c in lr.geometry.coords:node_sigs[topo._graph_node_key(c)].add(sig)
    rawproj=raw.to_crs(3310)
    rawtree=shapely.STRtree(rawproj.geometry.to_numpy())
    for _,row in sp.iterrows():
        q=[row.geometry.x,row.geometry.y];distance,ix=tree.query(q);node=nodes[ix]
        near=tree.query_ball_point(q,250)
        tied=sum(abs(np.linalg.norm(xy[i]-q)-distance)<1e-8 for i in near)
        registered=bool(distance<=cfg.MAX_SUBSTATION_TO_GRAPH_SNAP_DIST_M)
        if registered:sn[row.id]=node
        sigs=node_sigs[topo._graph_node_key(node)]
        voltages={dict(s).get("voltage_family","") for s in sigs}
        owners={dict(s).get("Owner","") for s in sigs}
        sv=topo._substation_voltage_families(row)
        compat=bool(sv&voltages)
        owner=topo._normalized_line_owner(row)
        ogroups={topo._topology_owner_group(owner,v) for v in voltages}
        reg.append(dict(station_id=row.id,station_name=row.NAME,longitude=row.LONGITUDE,latitude=row.LATITUDE,
            old_retained=bool(row.old_selected_92),key15=bool(row.key_15_station),source_proxy=bool(row.existing_source_proxy),
            nearest_graph_node=repr(node),registered_graph_node=repr(node) if registered else "",
            registered=registered,snap_distance_m=float(distance),candidate_graph_nodes_within_250m=len(near),
            equally_nearest_candidates=tied,nearest_node_voltage_families=";".join(sorted(voltages)),
            station_voltage_families=";".join(sorted(sv)),voltage_compatibility="match_present" if compat else "no_listed_match",
            nearest_node_owner_groups=";".join(sorted(owners)),
            owner_compatibility="unknown" if not owner or owner=="OTHER" else ("match_present" if owners&ogroups else "no_listed_match"),
            original_line_distance_m=float(row.geometry.distance(rawproj.geometry.iloc[rawtree.nearest(row.geometry)]))))
    print("REGISTRATION",len(sn),"/310",flush=True)
    dist={}; links=[];seen=set();old=read(ROOT/"Data/substation_graph_CEC_edges_expanded.csv",dtype={"u":str,"v":str})
    oldpairs={tuple(sorted((a,b))) for a,b in zip(old.u,old.v)}
    oldpaths={}
    for k,(sid,node) in enumerate(sn.items()):
        lengths,paths=nx.single_source_dijkstra(P,node,weight="weight")
        dist[sid]={t:lengths[n]/1000 for t,n in sn.items() if n in lengths}
        log.setLevel(logging.WARNING)
        got=topo.compute_direct_links({sid:dist[sid]},sn,{sid:paths},projection_anchor_df=split)
        log.setLevel(logging.INFO)
        for e in got:
            key=(e["src"],e["tgt"])
            if key not in seen:seen.add(key);links.append(e)
        for pair in oldpairs:
            if pair[0]==sid and pair[1] in sn and sn[pair[1]] in paths:oldpaths[pair]=paths[sn[pair[1]]]
        del lengths,paths
        if (k+1)%25==0:print("SHORTEST PATHS",k+1,"/",len(sn),"direct links",len(links),flush=True)
    H=nx.Graph();H.add_nodes_from(subs.id)
    H.add_edges_from((e["src"],e["tgt"],{"weight":e["length_km"]}) for e in links)
    comp=sorted(nx.connected_components(H),key=lambda s:(-len(s),min(s)))
    print("FACILITY GRAPH",len(H),H.number_of_edges(),"components",[len(c) for c in comp],flush=True)
    W0=wmod.build_W_matrix(subs,tracts,dist)
    W=wmod.apply_min_weight_threshold(W0,cfg.MIN_EFFECTIVE_WEIGHT)
    meta.update(parameters={k:v for k,v in vars(cfg).items() if not k.startswith("OUTPUT") and k not in ["DEVICES_CSV","LA_TRACTS_SHP","TRANSMISSION_LINES_SHP","CITY_TRACTS_LIST_CSV"]},
       topology_log=stream.getvalue(),guard_counts=dict(counts),driver_build_sha256=sha(__file__))
    state=dict(subs=subs,tracts=tracts,meta=meta,G=G,P=P,lines=lines,raw=raw,sp=sp,split=split,
       captures=captures,sn=sn,reg=pd.DataFrame(reg),dist=dist,links=links,oldpairs=oldpairs,
       oldpaths=oldpaths,H=H,components=comp,W0=W0,W=W)
    with TMP.open("wb") as f:pickle.dump(state,f,pickle.HIGHEST_PROTOCOL)
    for rel,h in meta["frozen_input_hashes"].items():assert sha(ROOT/rel)==h
    print("CHECKPOINT",TMP,"W",W.shape,"zero rows",int((W.sum(1)==0).sum()),flush=True)

def quant(a):
    a=np.asarray(a,dtype=float);a=a[np.isfinite(a)]
    return dict(zip(['min','p25','median','p75','p95','max'],map(float,np.quantile(a,[0,.25,.5,.75,.95,1])))) if len(a) else {}

def csv(df,name):df.to_csv(safe(OUT/name),index=False)

def road_readiness(subs):
    # No shortest-path matrix or routing costs are computed. Read geometry and
    # directed reachability only; do not fill missing speeds or travel times.
    from lxml import etree
    from pyproj import Transformer
    from sklearn.neighbors import BallTree
    ns='{http://graphml.graphdrawing.org/xmlns}'
    keys={};coords={};edges=[];total=0;time_good=0;length_good=0;speed_good=0
    path=ROOT/'Data/la_drive.graphml'
    for _,e in etree.iterparse(str(path),events=('end',),tag=[ns+'key',ns+'node',ns+'edge']):
        if e.tag==ns+'key':keys[e.get('id')]=e.get('attr.name')
        else:
            d={keys.get(c.get('key'),c.get('key')):c.text for c in e if c.tag==ns+'data'}
            if e.tag==ns+'node':
                try:coords[e.get('id')]=(float(d['x']),float(d['y']))
                except (KeyError,ValueError):pass
            else:
                edges.append((e.get('source'),e.get('target')));total+=1
                for fld,label in [('travel_time','t'),('length','l'),('speed_kph','s')]:
                    try:good=np.isfinite(float(d.get(fld,''))) and float(d[fld])>=0
                    except (ValueError,KeyError):good=False
                    if label=='t':time_good+=int(good)
                    elif label=='l':length_good+=int(good)
                    else:speed_good+=int(good)
        e.clear()
        while e.getprevious() is not None:del e.getparent()[0]
    print('ROAD loaded',len(coords),'nodes',total,'edges',flush=True)
    road=nx.DiGraph();road.add_nodes_from(coords);road.add_edges_from(edges)
    ids=list(coords);ll=np.array([coords[i] for i in ids]);tf=Transformer.from_crs(4326,3310,always_xy=True)
    xy=np.array(tf.transform(ll[:,0],ll[:,1])).T;tree=cKDTree(xy)
    pts=np.array(tf.transform(subs.LONGITUDE.to_numpy(),subs.LATITUDE.to_numpy())).T
    # Match OSMnx nearest_nodes for the unprojected geographic GraphML.
    bt=BallTree(np.deg2rad(ll[:,::-1]),metric='haversine')
    _,ix=bt.query(np.deg2rad(np.array([subs.LATITUDE,subs.LONGITUDE]).T),k=1);ix=ix.ravel()
    ds=np.linalg.norm(xy[ix]-pts,axis=1);station_nodes=[ids[i] for i in ix]
    bases=read(ROOT/'Data/stage45_C57_expanded_crew_origins.csv').drop_duplicates('yard_id')
    _,bi=bt.query(np.deg2rad(np.array([bases.latitude,bases.longitude]).T),k=1);bi=bi.ravel()
    bn=[ids[i] for i in bi]
    def reachable(graph,starts):
        seen=set(starts);todo=collections.deque(starts)
        while todo:
            u=todo.popleft()
            for v in graph[u]:
                if v not in seen:seen.add(v);todo.append(v)
        return seen
    forward=reachable(road,bn);back=reachable(road.reverse(copy=False),bn)
    sc={n:(i,len(c)) for i,c in enumerate(nx.strongly_connected_components(road),1) for n in c}
    df=pd.DataFrame(dict(station_id=subs.id,road_node=station_nodes,road_snap_distance_m=ds,
        road_reachable_from_any_existing_base=[n in forward for n in station_nodes],
        road_return_to_any_existing_base=[n in back for n in station_nodes],
        road_strong_component_size=[sc[n][1] for n in station_nodes]))
    meta=dict(file_sha256=sha(path),nearest_method='haversine BallTree, matching OSMnx geographic nearest_nodes; reported distance EPSG:3310',nodes=len(road),directed_edges=total,
        edges_with_nonnegative_travel_time=time_good,edges_with_nonnegative_length=length_good,
        edges_with_nonnegative_speed_kph=speed_good,existing_unique_bases=len(bases),
        snap_distance_m=quant(ds),unreachable_from_bases=int((~df.road_reachable_from_any_existing_base).sum()),
        no_return_to_bases=int((~df.road_return_to_any_existing_base).sum()))
    return df,meta

def qa():
    with TMP.open('rb') as f:s=pickle.load(f)
    subs=s['subs'];sp=s['sp'];W=s['W'];W0=s['W0'];a=W.to_numpy();a0=W0.to_numpy();H=s['H'];sn=s['sn']
    reg=s['reg'].copy();meta=s['meta'];ids=W.columns.to_numpy(dtype=str);oldids=set(subs.loc[subs.old_selected_92,'id']);newids=set(ids)-oldids
    sources=set(subs.loc[subs.existing_source_proxy,'id']);keyids=set(subs.loc[subs.key_15_station,'id'])
    names=subs.set_index('id').NAME.to_dict();compmap={i:k for k,c in enumerate(s['components'],1) for i in c}
    comps=[dict(component=k,station_count=len(c),source_count=len(c&sources),source_ids=sorted(c&sources),
          station_ids=sorted(c)) for k,c in enumerate(s['components'],1)]
    reg['component']=reg.station_id.map(compmap);reg['component_source_count']=reg.component.map({c['component']:c['source_count'] for c in comps})
    final_audit=s['captures']['merge_nearby_line_endpoints'].copy()
    final_audit['nearest_substation_id']=final_audit.nearest_substation_id.astype(str)
    accepted=final_audit[final_audit.repair_type.isin(['substation_snap_primary','substation_snap_secondary','protected_junction_cluster_snap','local_substation_anchor_fix'])]
    for tag,types in [('primary',['substation_snap_primary']),('secondary',['substation_snap_secondary']),('protected',['protected_junction_cluster_snap','local_substation_anchor_fix'])]:
        reg['endpoint_'+tag+'_count']=reg.station_id.map(accepted[accepted.repair_type.isin(types)].groupby('nearest_substation_id').size()).fillna(0).astype(int)
    reg['max_endpoint_original_distance_m']=reg.station_id.map(accepted.groupby('nearest_substation_id').nearest_distance_m.max())
    reg['registration_method']=np.where(reg.endpoint_secondary_count>0,'endpoint_secondary_anchor_then_nearest_graph',np.where(reg.endpoint_primary_count+reg.endpoint_protected_count>0,'endpoint_primary_or_protected_anchor_then_nearest_graph','nearest_graph_without_endpoint_anchor'))
    rev=collections.defaultdict(list)
    for sid,node in sn.items():rev[node].append(sid)
    reg['co_registered_station_ids']=reg.station_id.map({sid:';'.join(v) for v in rev.values() if len(v)>1 for sid in v}).fillna('')
    # At attribute-scoped coordinates only the selected scope counts as evidence.
    for i,row in reg.iterrows():
        node=sn.get(row.station_id);sig=topo._node_attribute_signature(node) if node is not None else None
        if sig is not None:
            sd=dict(sig);v=sd.get('voltage_family','');o=sd.get('Owner','');sr=sp[sp.id==row.station_id].iloc[0]
            sv=topo._substation_voltage_families(sr);owner=topo._normalized_line_owner(sr)
            reg.loc[i,'nearest_node_voltage_families']=v;reg.loc[i,'nearest_node_owner_groups']=o
            reg.loc[i,'voltage_compatibility']='match_present' if v in sv else 'no_listed_match'
            reg.loc[i,'owner_compatibility']='unknown' if not owner or owner=='OTHER' else ('match_present' if o==topo._topology_owner_group(owner,v) else 'no_listed_match')
    # Owner is checked independently of voltage. A same-owner 66/230 kV
    # mismatch must not be counted again as an owner mismatch.
    for i,row in reg.iterrows():
        sr=sp[sp.id==row.station_id].iloc[0];owner=topo._normalized_line_owner(sr)
        og={topo._topology_owner_group(owner,v) for v in row.nearest_node_voltage_families.split(';')}
        reg.loc[i,'owner_compatibility']='unknown' if not owner or owner=='OTHER' else ('match_present' if og&set(row.nearest_node_owner_groups.split(';')) else 'no_listed_match')
    pop=pd.to_numeric(s['tracts'].set_index('tract_id').loc[W.index,'population'],errors='raise').to_numpy(float)
    assert np.isfinite(pop).all() and (pop>=0).all()
    reg['population_weighted_dependency']=a.T@pop;reg['unweighted_dependency']=a.sum(0)
    reg['population_dependency_fraction']=reg.population_weighted_dependency/pop.sum()
    reg=reg.merge(subs[['id','MAX_VOLT','MIN_VOLT','MAX_INFER','STATUS','Owner']].rename(columns={'id':'station_id'}),on='station_id',validate='one_to_one')
    # Direct edge paths retained as geometry; no straight-line substitute.
    edges=[]
    for e in s['links']:
        u,v=e['src'],e['tgt'];geom=LineString([topo._node_xy(n) for n in e['path_nodes']]);eu=sp.loc[sp.id==u].geometry.iloc[0].distance(sp.loc[sp.id==v].geometry.iloc[0])/1000
        edges.append(dict(src=u,tgt=v,src_name=names[u],tgt_name=names[v],length_km=e['length_km'],
            euclidean_km=eu,detour_ratio=e['length_km']/eu if eu>0 else np.nan,component=compmap[u],
            old318_direct=(u,v) in s['oldpairs'],path_nodes=len(e['path_nodes']),path_wkt_epsg3310=geom.wkt))
    ed=pd.DataFrame(edges);csv(ed,'R1_310_EDGES.csv')
    # Classify every old edge by its path on the NEW physical graph.
    anchors=collections.defaultdict(list)
    for _,r in s['split'].iterrows():anchors[topo._graph_node_key((r.cut_x,r.cut_y))].append((str(r.substation_id),topo._parse_line_topology_signature(r.line_topology_signature),r.distance_to_line_m))
    oldqa=[];newpairs=set(zip(ed.src,ed.tgt))
    for u,v in sorted(s['oldpairs']):
        path=s['oldpaths'].get((u,v),[]);internal=[];projected=[]
        for n in path[1:-1]:
            internal.extend(rev.get(n,[]));nsig=topo._node_attribute_signature(n)
            projected.extend(sid for sid,sig,d in anchors.get(topo._graph_node_key(topo._node_xy(n)),[]) if sid not in (u,v) and (nsig is None or nsig==sig))
        blockers=set(internal+projected)-{u,v};nb=blockers&newids;ob=blockers&oldids
        chain=[]
        if u in H and v in H and nx.has_path(H,u,v):chain=nx.shortest_path(H,u,v,weight='weight')
        ordered=[u]+[sid for n in path[1:-1] for sid in rev.get(n,[]) if sid not in (u,v)]+[v]
        ordered=list(dict.fromkeys(ordered));exact_chain=bool(path) and len(ordered)>2 and all(H.has_edge(x,y) for x,y in zip(ordered[:-1],ordered[1:]))
        if (u,v) in newpairs:reason='retained_direct'
        elif u not in H or v not in H:reason='endpoint_excluded_by_R1'
        elif u not in sn or v not in sn:reason='endpoint_unregistered'
        elif not path:reason='physical_graph_disconnected'
        elif len(path)<2:reason='co_registered_endpoints_no_direct_edge'
        elif nb:reason='new_intermediate_station_blocked_chain_available' if chain else 'new_intermediate_blocked_no_facility_chain'
        elif ob:reason='retained_station_intermediate_after_reprocessing'
        else:reason='reachable_other_requires_review'
        oldqa.append(dict(src=u,tgt=v,reason=reason,new_intermediate_ids=';'.join(sorted(nb)),
             retained_intermediate_ids=';'.join(sorted(ob)),registered_internal_ids=';'.join(sorted(set(internal))),
             projection_internal_ids=';'.join(sorted(set(projected))),facility_chain=';'.join(chain),
             exact_registered_path_chain=exact_chain,registered_path_chain=';'.join(ordered) if path else '',
             new_physical_path_wkt_epsg3310=LineString([topo._node_xy(n) for n in path]).wkt if len(path)>1 else ''))
    oq=pd.DataFrame(oldqa);csv(oq,'R1_310_OLD_EDGE_QA.csv')
    # Dependency QA is structural; population here is a static weight, no outcome.
    cent=s['tracts'].to_crs(3310).geometry.centroid;xy=np.array([cent.x,cent.y]).T
    stxy=np.array([sp.geometry.x,sp.geometry.y]).T;access_d,access_i=cKDTree(stxy).query(xy);access=ids[access_i]
    network=np.array([[s['dist'].get(i,{}).get(j,np.inf) for j in ids] for i in access])
    nz=a>0;selected_net=np.where(nz,network,np.nan)
    top=a.argmax(1);sortedw=np.sort(a,axis=1);rawsort=np.sort(a0,axis=1)
    sourcefree=np.array([comps[compmap[i]-1]['source_count']==0 for i in ids])
    q=pd.DataFrame(dict(tract_id=W.index,population=pop,row_sum=a.sum(1),negative_count=(a<0).sum(1),nan_count=np.isnan(a).sum(1),inf_count=np.isinf(a).sum(1),
        zero_row=a.sum(1)==0,cutoff_fallback_row=(a0>=.03).sum(1)==0,raw_fallback_row=np.zeros(len(a),bool),
        candidate_station_count=np.isfinite(network).sum(1),nonzero_before_cutoff=(a0>0).sum(1),nonzero_after_cutoff=nz.sum(1),
        max_weight=sortedw[:,-1],effective_station_count=1/(a*a).sum(1),top1_station=ids[top],top3_cumulative=sortedw[:,-3:].sum(1),
        raw_max_weight=rawsort[:,-1],raw_top3_cumulative=rawsort[:,-3:].sum(1),access_station=access,access_distance_km=access_d/1000,
        network_distance_weighted_km=(np.where(nz,network,0)*a).sum(1),network_distance_max_selected_km=np.nanmax(selected_net,axis=1),
        access_registered=[i in sn for i in access],access_component=[compmap[i] for i in access],source_less_dependency_weight=a[:,sourcefree].sum(1)))
    assert q.access_registered.all() # ensures no hidden unregistered-access one-hot assignment
    old=read(ROOT/'Data/tract_to_substation_mapping_CEC_expanded.csv',dtype={'tract_id':str,'substation_id':str})
    old.tract_id=old.tract_id.str.zfill(11)
    oldW=old.pivot_table(index='tract_id',columns='substation_id',values='weight',aggfunc='sum',fill_value=0).reindex(W.index,fill_value=0)
    assert len(oldW.columns)==92 and np.allclose(oldW.sum(1),1,atol=1e-10)
    oa=oldW.to_numpy();osort=np.sort(oa,axis=1);ot=oldW.columns.to_numpy()[oa.argmax(1)]
    q['old_top1_station']=ot;q['top1_changed']=q.top1_station!=ot;q['old_max_weight']=osort[:,-1];q['old_top3_cumulative']=osort[:,-3:].sum(1)
    q['old_nonzero_station_count']=(oa>0).sum(1);q['old_effective_station_count']=1/(oa*oa).sum(1)
    q['old_common83_share']=oldW[list(sorted(oldids))].sum(1).to_numpy();q['new_common83_share']=W[list(sorted(oldids))].sum(1).to_numpy()
    q['old_key15_share']=oldW[list(sorted(keyids))].sum(1).to_numpy();q['new_key15_share']=W[list(sorted(keyids))].sum(1).to_numpy()
    q['old_only9_share']=oldW[[i for i in oldW if i not in oldids]].sum(1).to_numpy()
    oldpop=oldW.to_numpy().T@pop;olddep=dict(zip(oldW.columns,oldpop))
    reg['old_population_dependency']=reg.station_id.map(olddep)
    reg['population_dependency_change_common83']=reg.population_weighted_dependency-reg.old_population_dependency
    csv(q,'R1_310_DEPENDENCY_QA.csv');csv(reg,'R1_310_STATIONS_QA.csv')
    # All PGA computations are deterministic INPUT interpolation, not damage sampling.
    import IDW as hazard
    import importlib.util
    fp=ROOT.parent/'02_Preprocessing_Scripts/extract_workinglist_substations_assign_fragility.py'
    spec=importlib.util.spec_from_file_location('fragility_inputs_only',fp);fm=importlib.util.module_from_spec(spec);spec.loader.exec_module(fm)
    ready=fm.assign_fragility(pd.DataFrame(subs.drop(columns='geometry')))
    fcols=[c for c in ready if c.startswith(('mu_','beta_'))]
    print('FRAGILITY fields',fcols,flush=True)
    ready=ready[['id','NAME','LONGITUDE','LATITUDE','MAX_VOLT_N','MIN_VOLT_N','MAX_INFER','fragility_class']+fcols].rename(columns={'id':'station_id','NAME':'station_name'})
    ready['fragility_fields_complete']=np.isfinite(ready[fcols]).all(axis=1)&(ready[fcols]>0).all(axis=1)
    hazardmeta={}
    for name,(kind,path,col) in hazard.SCENARIOS.items():
        glon,glat,gv=hazard.load_csv_grid(path,col) if kind=='csv' else hazard.load_covjson(path)
        ln=hazard.idw_core(subs.LONGITUDE.to_numpy(),subs.LATITUDE.to_numpy(),glon,glat,gv)
        ready['PGA_'+name+'_g']=np.exp(ln)
        mask=np.isfinite(glon)&np.isfinite(glat)&np.isfinite(gv)
        gx,gy=hazard.project_lonlat_to_xy(glon[mask],glat[mask]);sx,sy=hazard.project_lonlat_to_xy(subs.LONGITUDE,subs.LATITUDE)
        hd,hi=cKDTree(np.array([gx,gy]).T).query(np.array([sx,sy]).T,k=8,distance_upper_bound=11000)
        ready['PGA_'+name+'_grid_neighbors_11km']=np.isfinite(hd).sum(1)
        hazardmeta[name]=dict(valid=int(np.isfinite(ln).sum()),grid_sha256=sha(path),grid_neighbors=quant(np.isfinite(hd).sum(1)))
        print('PGA INPUT',name,np.isfinite(ln).sum(),flush=True)
    road,roadmeta=road_readiness(subs);ready=ready.merge(road,on='station_id',validate='one_to_one')
    hospital=read(ROOT/'Data/hospital_with_tract_expanded.csv')
    hc=next(c for c in ['tract_id','GEOID','GEOID10','geoid'] if c in hospital)
    hids=hospital[hc].astype(str).str.replace(r'\.0$','',regex=True).str.zfill(11)
    hindicator=np.array([i in set(hids) for i in W.index],float)
    ready['population_dependency']=a.T@pop;ready['hospital_tract_weighted_coverage']=a.T@hindicator
    ready['hospital_tract_link_count']=(a>0).T@hindicator
    ready['degree']=ready.station_id.map(dict(H.degree));ready['closeness_unweighted']=ready.station_id.map(nx.closeness_centrality(H))
    ready['source_proxy']=ready.station_id.isin(sources);ready['coordinates_valid']=np.isfinite(ready[['LONGITUDE','LATITUDE']]).all(axis=1)
    ready['source_role_name_review_flag']=ready.station_id.isin(newids)&ready.station_name.str.contains('GEN|PLANT|SWITCHYARD|GENERATING',case=False,regex=True,na=False)
    csv(ready,'R1_310_INPUT_READINESS.csv')
    rawcomps=sorted(nx.connected_components(s['P']),key=len,reverse=True);rawcid={n:k for k,c in enumerate(rawcomps,1) for n in c}
    phy_station_groups=collections.defaultdict(list)
    for i,n in sn.items():phy_station_groups[rawcid[n]].append(i)
    meta.update(components=comps,raw_physical_station_components=[dict(ids=v,source_ids=sorted(set(v)&sources)) for v in phy_station_groups.values()],
        physical_nodes=len(s['P']),physical_edges=s['P'].number_of_edges(),physical_multiedges=s['G'].number_of_edges(),
        direct_edges=len(ed),isolated_stations=list(nx.isolates(H)),articulation_stations=list(nx.articulation_points(H)),bridges=list(nx.bridges(H)),
        self_loops=nx.number_of_selfloops(H),duplicate_direct_rows=int(ed.duplicated(['src','tgt']).sum()),
        registration_distance=quant(reg.snap_distance_m),original_line_distance=quant(reg.original_line_distance_m),
        registration_groups={k:dict(n=len(g),snap=quant(g.snap_distance_m),original_line=quant(g.original_line_distance_m),
             above150=int((g.snap_distance_m>150).sum()),secondary_station_count=int((g.endpoint_secondary_count>0).sum())) for k,g in reg.groupby('old_retained')},
        voltage_mismatch_ids=reg.loc[reg.voltage_compatibility=='no_listed_match','station_id'].tolist(),
        owner_mismatch_ids=reg.loc[reg.owner_compatibility=='no_listed_match','station_id'].tolist(),
        old_edge_classification=oq.reason.value_counts().to_dict(),old_edge_exact_path_chain_count=int(oq.exact_registered_path_chain.sum()),
        new_direct_edges_not_old318=int((~ed.old318_direct).sum()),
        dependency=dict(tracts=len(W),stations=len(ids),population=float(pop.sum()),old_row_sum_max_error=float(abs(oldW.sum(1)-1).max()),
          row_sum_max_error=float(abs(a.sum(1)-1).max()),nonzero_before=int((a0>0).sum()),nonzero_after=int(nz.sum()),
          raw_fallback=0,cutoff_fallback=int(q.cutoff_fallback_row.sum()),zero_rows=int(q.zero_row.sum()),
          max_weight=quant(q.max_weight),effective_count=quant(q.effective_station_count),nonzero_count=quant(q.nonzero_after_cutoff),
          old_max_weight=quant(q.old_max_weight),old_effective_count=quant(q.old_effective_station_count),old_nonzero_count=quant(q.old_nonzero_station_count),
          top3=quant(q.top3_cumulative),old_top3=quant(q.old_top3_cumulative),access_km=quant(q.access_distance_km),
          top1_changed=int(q.top1_changed.sum()),top1_changed_old_common83=int((q.top1_changed&q.old_top1_station.isin(oldids)).sum()),
          single_station_tracts=int((q.nonzero_after_cutoff==1).sum()),max_weight_ge95_tracts=int((q.max_weight>=.95).sum()),
          old_single_station_tracts=int((q.old_nonzero_station_count==1).sum()),old_max_weight_ge95_tracts=int((q.old_max_weight>=.95).sum()),
          old_key15_population_share=float(np.dot(q.old_key15_share,pop)/pop.sum()),new_key15_population_share=float(np.dot(q.new_key15_share,pop)/pop.sum()),
          old_common83_population_share=float(np.dot(q.old_common83_share,pop)/pop.sum()),new_common83_population_share=float(np.dot(q.new_common83_share,pop)/pop.sum()),
          source_less_tracts=int((q.source_less_dependency_weight>0).sum()),source_less_dependency_population=float(np.dot(q.source_less_dependency_weight,pop))),
        top20_new_only=frame_json(reg[~reg.old_retained].nlargest(20,'population_weighted_dependency')[['station_id','station_name','population_weighted_dependency','population_dependency_fraction','snap_distance_m','voltage_compatibility','component']]),
        hazard=hazardmeta,fragility_class_counts=ready.fragility_class.value_counts().to_dict(),
        fragility_fields=fcols,fragility_valid=int(ready.fragility_fields_complete.sum()),inferred_voltage=int((ready.MAX_INFER=='Y').sum()),
        road=roadmeta,hospital_tract_column=hc,hospital_input_rows=len(hospital),hospital_unique_tracts=int(hindicator.sum()),
        new_source_role_name_flags=frame_json(ready[ready.source_role_name_review_flag][['station_id','station_name']]),
        split_records=frame_json(s['split']),endpoint_audit=frame_json(final_audit),
        software_versions=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,networkx=nx.__version__,geopandas=gpd.__version__,shapely=shapely.__version__),
        driver_qa_sha256=sha(__file__))
    # Metadata/audits travel with the matrix, avoiding dozens of intermediate files.
    with open(safe(OUT/'R1_310_BUILD_DATA.npz'),'wb') as f:
        np.savez_compressed(f,W=a,W_before_cutoff=a0,station_ids=ids,tract_ids=W.index.to_numpy(dtype=str),population=pop,
            metadata_json=np.array(json.dumps(meta,ensure_ascii=False,default=lambda x:int(x) if isinstance(x,np.integer) else str(x))))
    for rel,h in meta['frozen_input_hashes'].items():assert sha(ROOT/rel)==h
    print('QA COMPLETE',json.dumps({k:meta[k] for k in ['old_edge_classification','voltage_mismatch_ids','owner_mismatch_ids','dependency','road']},default=str),flush=True)

def inspect_geometry():
    """Bounded geometry checks and one scientific QA map; no outcome calculation."""
    with TMP.open('rb') as f:s=pickle.load(f)
    with np.load(safe(OUT/'R1_310_BUILD_DATA.npz')) as z:arrays={k:z[k] for k in z.files}
    meta=json.loads(str(arrays['metadata_json']));reg=read(OUT/'R1_310_STATIONS_QA.csv',dtype={'station_id':str})
    ed=read(OUT/'R1_310_EDGES.csv',dtype={'src':str,'tgt':str});oq=read(OUT/'R1_310_OLD_EDGE_QA.csv',dtype={'src':str,'tgt':str})
    sp=s['sp'];sn=s['sn'];raw=s['raw'].to_crs(3310);P=s['P'];xy=sp.set_index('id').geometry
    submap=sp.set_index('id');rv=reg.set_index('station_id')
    components=sorted(nx.connected_components(P),key=len,reverse=True);cid={n:i for i,c in enumerate(components) for n in c}
    main=cid[sn[reg.loc[reg.source_proxy,'station_id'].iloc[0]]];mn=list(components[main]);tree=cKDTree(np.array([topo._node_xy(n) for n in mn]))
    reviewids=set(reg.loc[reg.key15,'station_id'])|set(meta['voltage_mismatch_ids'])|set(meta['owner_mismatch_ids'])
    reviewids|=set(reg.loc[reg.component>1,'station_id'])|set(reg.nlargest(3,'snap_distance_m').station_id)|{v['station_id'] for v in meta['top20_new_only'][:6]}
    reviews=[]
    for sid in sorted(reviewids):
        point=xy[sid];d=raw.geometry.distance(point);z=raw.loc[d.nsmallest(3).index,['Name','kV','Owner','Status','GlobalID']].copy();z['distance_m']=d.loc[z.index]
        rr=dict(station_id=sid,station_name=submap.loc[sid,'NAME'],raw_nearest_lines=frame_json(z),
           component=int(rv.loc[sid,'component']),population_dependency=float(rv.loc[sid,'population_weighted_dependency']))
        if cid[sn[sid]]!=main:
            ns=list(components[cid[sn[sid]]]);dd,ii=tree.query(np.array([topo._node_xy(n) for n in ns]));k=int(dd.argmin())
            rr.update(closest_node_gap_to_source_component_m=float(dd[k]),gap_from_xy=topo._node_xy(ns[k]),gap_to_xy=topo._node_xy(mn[ii[k]]))
        reviews.append(rr)
    splitold=oq[oq.reason=='new_intermediate_station_blocked_chain_available'].copy()
    splitold['blocker_count']=splitold.new_intermediate_ids.str.split(';').str.len()
    chosen=pd.concat([splitold.sample(min(5,len(splitold)),random_state=20260913),splitold.nlargest(4,'blocker_count'),
        splitold[splitold.src.isin(reg.loc[reg.key15,'station_id'])|splitold.tgt.isin(reg.loc[reg.key15,'station_id'])].head(4)]).drop_duplicates(['src','tgt'])
    selected=[]
    for _,r in chosen.iterrows():
        line=shapely.from_wkt(r.new_physical_path_wkt_epsg3310);bs=r.new_intermediate_ids.split(';')
        selected.append(dict(src=r.src,tgt=r.tgt,blockers=bs,exact_chain=bool(r.exact_registered_path_chain),
            blocker_station_distance_to_rebuilt_path_m={i:float(xy[i].distance(line)) for i in bs},
            blocker_original_line_distance_m={i:float(rv.loc[i,'original_line_distance_m']) for i in bs},
            blocker_voltage_mismatch_ids=[i for i in bs if i in meta['voltage_mismatch_ids']]))
    # Status evidence is confined to retained project records, not an online search.
    status=[];oldonly=meta['old_only'];source_dir=ROOT.parent/'01_Source_Data'
    rawfiles=['CA_substations_MERGED.csv','CA_substations.csv','LA_County_SUBSTATION.csv']
    tables={f:read(source_dir/f,dtype={'ID':str}) for f in rawfiles}
    cecpath=next(source_dir.glob('California Electric Substations (2022)/data/v101/*.gdb'))
    cec=gpd.read_file(cecpath,layer='CA_Substations_Final',ignore_geometry=True)
    cec.HIFLD_ID=cec.HIFLD_ID.astype(str).str.replace(r'\.0$','',regex=True)
    for row in oldonly:
        sid=row['ID'];ev={f:t.loc[t.ID==sid,'STATUS'].tolist() for f,t in tables.items()}
        status.append(dict(station_id=sid,station_name=row['NAME'],retained_status_evidence=ev,
            CEC_2022_record_present=bool((cec.HIFLD_ID==sid).any()),CEC_2022_has_status_field='STATUS' in cec,
            decision='outside_study_area_non_source_keep_excluded' if sid=='306279' else 'status_still_unknown_keep_excluded'))
    meta.update(station_geometry_spot_checks=reviews,old_edge_geometry_spot_checks=selected,
        old_edge_random_sample_seed=20260913,old_only_status_review=status,
        old_edge_new_blocker_exact_chain_count=int(splitold.exact_registered_path_chain.sum()),
        old_edge_two_retained_blocker_cases=frame_json(oq[oq.reason=='retained_station_intermediate_after_reprocessing'][['src','tgt','retained_intermediate_ids','registered_path_chain']]),
        frozen_station_input_records=frame_json(pd.DataFrame(s['subs'].drop(columns='geometry'))),
        fragility_assignment_source_path=str(ROOT.parent/'02_Preprocessing_Scripts/extract_workinglist_substations_assign_fragility.py'),
        fragility_assignment_source_sha256=sha(ROOT.parent/'02_Preprocessing_Scripts/extract_workinglist_substations_assign_fragility.py'),
        fragility_assignment_source_text=(ROOT.parent/'02_Preprocessing_Scripts/extract_workinglist_substations_assign_fragility.py').read_text(encoding='utf-8'),
        final_driver_sha256=sha(__file__))
    arrays['metadata_json']=np.array(json.dumps(meta,ensure_ascii=False,default=str))
    with open(safe(OUT/'R1_310_BUILD_DATA.npz'),'wb') as f:np.savez_compressed(f,**arrays)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter
    fig=plt.figure(figsize=(20,13));gs=fig.add_gridspec(3,4,width_ratios=[1.2,1.2,1,1],hspace=.32,wspace=.22)
    ax=fig.add_subplot(gs[:,:2]);colors={1:'#2673a5',2:'#cc3311',3:'#ee7733',4:'#aa3377'}
    def lineseg(g):
        if g.geom_type=='LineString':return [np.array(g.coords)]
        if g.geom_type=='MultiLineString':return [np.array(v.coords) for v in g.geoms]
        return []
    rawsegments=[seg for g in raw.geometry for seg in lineseg(g)]
    newgeoms=shapely.from_wkt(ed.path_wkt_epsg3310.to_numpy());ec=[colors[i] for i in ed.component]
    ax.add_collection(LineCollection(rawsegments,colors='#cccccc',linewidths=.3,zorder=1))
    ax.add_collection(LineCollection([np.array(g.coords) for g in newgeoms],colors=ec,linewidths=.45,alpha=.5,zorder=2))
    for u,v in [('307039','310179'),('300105','300232'),('306224','306450')]:
        path=s['oldpaths'][(u,v)];ax.add_collection(LineCollection([np.array([topo._node_xy(n) for n in path])],colors='#198754',linewidths=1.5,alpha=.8,zorder=3))
    for old,marker in [(True,'s'),(False,'o')]:
        z=reg[reg.old_retained==old];pp=sp[sp.id.isin(z.station_id)]
        ax.scatter(pp.geometry.x,pp.geometry.y,s=18 if old else 12,marker=marker,c=[colors[int(rv.loc[i,'component'])] for i in pp.id],edgecolors='white',linewidths=.3,zorder=4)
    z=sp[sp.existing_source_proxy];ax.scatter(z.geometry.x,z.geometry.y,marker='*',s=130,c='#f5ba31',edgecolors='#322600',linewidths=.6,zorder=6)
    for _,r in sp[sp.key_15_station].iterrows():ax.annotate(r.id,(r.geometry.x,r.geometry.y),xytext=(3,3),textcoords='offset points',fontsize=6.8,zorder=7)
    for _,r in reg[reg.component>1].iterrows():
        p=xy[r.station_id];ax.annotate(r.station_id,(p.x,p.y),xytext=(4,-10),textcoords='offset points',fontsize=8,color=colors[r.component],fontweight='bold')
    xmin,ymin,xmax,ymax=sp.total_bounds;ax.set_xlim(xmin-5000,xmax+5000);ax.set_ylim(ymin-5000,ymax+5000);ax.set_aspect('equal')
    ax.set_title('R1 dry build: 310 registered stations / 1,061 direct links\nFacility components: 306 + 2 + 1 + 1; sources: 14 + 0 + 0 + 0',fontsize=13,loc='left')
    ax.legend(handles=[Line2D([],[],marker='s',linestyle='',color=colors[1],label='83 retained stations'),Line2D([],[],marker='o',linestyle='',color=colors[1],label='227 new-only stations'),Line2D([],[],marker='*',linestyle='',color='#a78000',markersize=12,label='14 source proxies (assumed)'),Line2D([],[],color='#aa3377',label='Source-less components (warm colors)'),Line2D([],[],color='#bbbbbb',label='Original line geometry')],loc='lower left',fontsize=9,framealpha=.95)
    ax.set_xlabel('EPSG:3310 easting (km)');ax.set_ylabel('EPSG:3310 northing (km)')
    for axis in [ax.xaxis,ax.yaxis]:axis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x/1000:.0f}'))
    panels=[('308336',400,'AIRCHEM: registered to 220 kV node\n66 kV inventory; 124 m graph snap'),('309598',1800,'UNKNOWN309598: source-less stub\n13 tracts; 60,661 population dependency'),('306980',900,'RINGMILL: source-less stub\n2 tracts; 10,049 population dependency'),('303547',2600,'SERFGEN / NAVY MOLE: no source\nClose corridors do not prove a junction'),('304217',1200,'STATION S: largest new dependency\n253,902 population-weighted share'),('308793',600,'MCNEIL: 372 m endpoint movement\nNear-zero final station registration')]
    for k,(sid,half,title) in enumerate(panels):
        axt=fig.add_subplot(gs[k//2,2+k%2]);pt=xy[sid];bounds=shapely.box(pt.x-half,pt.y-half,pt.x+half,pt.y+half)
        for _,lr in raw[raw.intersects(bounds)].iterrows():
            v=topo._voltage_family(lr.kV);color='#777777' if v=='66_69' else '#7e57c2'
            axt.add_collection(LineCollection(lineseg(lr.geometry),colors=color,linewidths=1.1,alpha=.65))
        processed=s['lines'][s['lines'].intersects(bounds)]
        axt.add_collection(LineCollection([seg for g in processed.geometry for seg in lineseg(g)],colors='#167cad',linewidths=.55,linestyles='dashed',alpha=.85))
        pp=sp[sp.intersects(bounds)]
        for _,r in pp.iterrows():
            c=colors[int(rv.loc[r.id,'component'])];axt.scatter(r.geometry.x,r.geometry.y,s=45,marker='s' if r.old_selected_92 else 'o',c=c,edgecolors='white',zorder=5)
            axt.annotate(r.id,(r.geometry.x,r.geometry.y),xytext=(4,5),textcoords='offset points',fontsize=7,zorder=6)
        n=topo._node_xy(sn[sid]);axt.scatter(*n,marker='x',s=60,c='black',zorder=7);axt.plot([pt.x,n[0]],[pt.y,n[1]],color='black',linewidth=1)
        axt.set_xlim(pt.x-half,pt.x+half);axt.set_ylim(pt.y-half,pt.y+half);axt.set_aspect('equal');axt.set_title(title,fontsize=10,loc='left')
        axt.tick_params(labelsize=7)
        for axis in [axt.xaxis,axt.yaxis]:axis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x/1000:.1f}'))
    fig.suptitle('INPUT QA ONLY — no damage sampling, restoration, scheduling or strategy comparison',fontsize=15,y=.99)
    fig.text(.51,.018,'Insets: gray = original 66/69 kV; purple = other original voltage; dashed blue = processed lines.\nBlack × = registered graph node. Coordinates in km (EPSG:3310). Gaps are NOT authorization to add edges.',fontsize=9)
    fig.savefig(safe(OUT/'R1_310_NETWORK_QA.png'),dpi=160,bbox_inches='tight');plt.close(fig)
    print('GEOMETRY QA',len(reviews),'stations',len(selected),'old-edge paths; map saved',flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--qa',action='store_true');p.add_argument('--inspect',action='store_true')
    args=p.parse_args()
    if not args.build and not args.qa and not args.inspect:p.error('Use explicit --build, --qa, --inspect. No recovery operation exists.')
    if args.build:build()
    if args.qa:qa()
    if args.inspect:inspect_geometry()
