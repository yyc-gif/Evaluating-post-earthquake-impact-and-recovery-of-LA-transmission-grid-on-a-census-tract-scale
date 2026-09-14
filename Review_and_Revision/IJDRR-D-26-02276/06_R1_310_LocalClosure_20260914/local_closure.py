"""One R1 local-closure dry build; no recovery/MC/dispatch/GA modules run.
All 310 IDs and the 05 build remain immutable. Source and road rules are
fixed before the one revised build; failing inputs are retained, not repaired
by dropping stations, adding edges, or reassigning service weights.
"""
import os,sys
sys.dont_write_bytecode=True
os.environ.setdefault('OMP_NUM_THREADS','1')
from pathlib import Path
import json,hashlib,pickle,tempfile,logging,io,collections,importlib.util,argparse,ast,types,re
import numpy as np,pandas as pd,geopandas as gpd,networkx as nx,shapely
from shapely.geometry import LineString,Point
from scipy.spatial import cKDTree
OUT=Path(__file__).resolve().parent
ROOT=next(p for p in OUT.parents if (p/'Topology_and_Weight.py').is_file())
OLD=OUT.parent/'05_R1_310_DryBuild_20260913'
sys.path.insert(0,str(ROOT))
import Topology_and_Weight as topo
import topology_outputs as wm
TMP=Path(tempfile.gettempdir())/'r1_310_localclosure_0a9e763.pkl'
RADIUS=250.0
ROAD_RADIUS=500.0 # prior dry-build road QA threshold, not fitted to WESTHILL
PLANT_SCREEN_RADIUS=1000.0 # candidate discovery only; not a source promotion rule
def safe(p):
    s=str(Path(p).resolve());return '\\\\?\\'+s if os.name=='nt' and not s.startswith('\\\\?\\') else s
def sha(p):return hashlib.sha256(Path(safe(p)).read_bytes()).hexdigest()
def read(p,**kw):return pd.read_csv(safe(p),**kw)
def csv(df,name):df.to_csv(safe(OUT/name),index=False)
def records(df):return json.loads(df.to_json(orient='records'))
def olddata():
    with np.load(safe(OLD/'R1_310_BUILD_DATA.npz'),allow_pickle=False) as z:a={k:z[k] for k in z.files}
    return a,json.loads(str(a['metadata_json']))
def prepare():
    a,m=olddata();d=pd.DataFrame(m['frozen_station_input_records']);d.ID=d.ID.astype(str);d.id=d.id.astype(str)
    assert hashlib.sha256(('\n'.join(d.ID)+'\n').encode()).hexdigest()==m['station_set_sha256']
    p=next((ROOT.parent/'01_Source_Data').glob('California Electric Substations (2022)/data/v101/*.gdb'))
    c=gpd.read_file(p,layer='CA_Substations_Final',ignore_geometry=True)
    c.HIFLD_ID=c.HIFLD_ID.astype(str).str.replace(r'\.0$','',regex=True)
    assert not c[c.HIFLD_ID.isin(d.id)].HIFLD_ID.duplicated().any()
    c=c.set_index('HIFLD_ID');dec=[]
    for i,row in d.iterrows():
        ce=c.loc[row.id] if row.id in c.index else None
        value=ce.Max_Voltage if ce is not None else np.nan
        use=ce is not None and str(ce.Source).upper()=='CEC' and str(row.MAX_INFER).upper()=='Y' and pd.notna(value) and float(value)>0
        change=bool(use and float(value)!=float(row.MAX_VOLT))
        if change:d.loc[i,['MAX_VOLT','MAX_VOLT_N','voltage_for_fragility']]=float(value)
        dec.append(dict(station_id=row.id,station_name=row.NAME,old_max_voltage=row.MAX_VOLT,
            connection_max_voltage=float(value) if use else row.MAX_VOLT,raw_max_inferred=row.MAX_INFER,
            CEC_2022_name=ce.Name if ce is not None else '',CEC_2022_max_voltage=value,
            CEC_2022_source=ce.Source if ce is not None else '',metadata_changed=change,
            metadata_evidence='CEC2022 nonmissing Max_Voltage replaces HIFLD inferred MAX only' if change else 'no metadata change',
            voltage_evidence_strength='CEC_documented_value' if use else ('HIFLD_inferred_provisional' if str(row.MAX_INFER)=='Y' else 'inventory_not_flagged_inferred'),
            old_status=row.STATUS,new_status=row.STATUS))
    # No coordinate/status/owner changes inferred merely from nearby line labels.
    subs=gpd.GeoDataFrame(d,geometry=gpd.points_from_xy(d.LONGITUDE,d.LATITUDE),crs=4326)
    tr=read(ROOT/'Data/Tracts_Within_Expanded_Area.csv',dtype={'GEOID':str});tr['tract_id']=tr.GEOID.str.zfill(11)
    tr=gpd.GeoDataFrame(tr,geometry=shapely.from_wkt(tr.wkt_geom.to_numpy()),crs=4326)
    return subs,tr,pd.DataFrame(dec),m,a

def register(G,sp,lines,dec):
    nodes=list(G);xy=np.array([topo._node_xy(n) for n in nodes]);tree=cKDTree(xy)
    signature_map=collections.defaultdict(set)
    for _,r in lines.iterrows():
        sig=topo._line_topology_signature(r,topo._detect_voltage_column(lines))
        for q in r.geometry.coords:signature_map[topo._graph_node_key(q)].add(sig)
    def signatures(n):
        sig=topo._node_attribute_signature(n)
        return {sig} if sig is not None else signature_map[topo._graph_node_key(topo._node_xy(n))]
    sn={};rows=[]
    old=read(OLD/'R1_310_STATIONS_QA.csv',dtype={'station_id':str}).set_index('station_id')
    for _,r in sp.iterrows():
        q=np.array([r.geometry.x,r.geometry.y]);sv=topo._substation_voltage_families(r)
        candidate=tree.query_ball_point(q,RADIUS);valid=[]
        for j in candidate:
            n=nodes[j];sigs=signatures(n);nf={dict(s).get('voltage_family','') for s in sigs}
            if nf&sv:
                # rounded 1e-7 m tie tolerance; explicit scope then stable node key.
                dd=float(np.linalg.norm(xy[j]-q));key=(round(dd,7),0 if topo._node_attribute_signature(n) is not None else 1,repr(n))
                valid.append((key,n,dd,sigs))
        chosen=min(valid,key=lambda x:x[0]) if valid else None
        assert (min(list(reversed(valid)),key=lambda x:x[0])[1] if valid else None)==(chosen[1] if chosen else None)
        n=chosen[1] if chosen else None
        if n is not None:sn[r.id]=n
        ss=chosen[3] if chosen else set();nf={dict(z).get('voltage_family','') for z in ss};owners={dict(z).get('Owner','') for z in ss}
        owner=topo._normalized_line_owner(r);owner_match=any(topo._topology_owner_group(owner,v) in owners for v in nf)
        rows.append(dict(station_id=r.id,old_registered_node=old.loc[r.id,'registered_graph_node'],
            proposed_registered_node=repr(n) if n is not None else '',registered_node_changed=(repr(n) if n is not None else '')!=old.loc[r.id,'registered_graph_node'],
            old_registration_distance_m=old.loc[r.id,'snap_distance_m'],proposed_registration_distance_m=chosen[2] if chosen else np.nan,
            candidates_within_250m=len(candidate),voltage_compatible_candidates=len(valid),station_voltage_families=';'.join(sorted(sv)),
            selected_node_voltage_families=';'.join(sorted(nf)),selected_node_owners=';'.join(sorted(owners)),
            registration_status='registered_compatible' if chosen else 'unresolved_no_compatible_scope',
            owner_review='unknown' if not owner or owner=='OTHER' else ('match' if chosen and owner_match else ('mismatch_review' if chosen else 'no_registration')),
            tied_compatible_nodes=sum(abs(v[2]-chosen[2])<=1e-7 for v in valid) if chosen else 0,
            deterministic_reverse_candidate_order_check=True))
    return sn,dec.merge(pd.DataFrame(rows),on='station_id',validate='one_to_one')

def source_roles(subs,con,boundary,plant):
    """Finite audit, not unconditional promotion of nearby generators or crossings."""
    from pyproj import Transformer
    fs=plant['result']['features'];pp=pd.DataFrame([dict(**f['attributes'],longitude=f['geometry']['x'],latitude=f['geometry']['y']) for f in fs])
    tf=Transformer.from_crs(4326,3310,always_xy=True);pxy=np.array(tf.transform(pp.longitude,pp.latitude)).T
    sx=np.array(tf.transform(subs.LONGITUDE,subs.LATITUDE)).T;tree=cKDTree(pxy)
    # Explicit station/plant identity crosswalks reviewed without outcome data.
    # Only these newly matched same-facility generation proxies are promoted;
    # other geographic matches remain candidates, including PV and batteries.
    supported={'301318':'E0127','302865':'G0084','303473':'G0925',
       '300232':'G9222','302376':'G1072','306001':'H0437','306365':'G0035',
       '306450':'G0894','306473':'H0541','307512':'G0236'}
    focus={'301215':'E0130','301318':'E0127','302865':'G0084','303277':'G0203','303364':'G0673',
           '303547':'E0112','303622':'C0002','303473':'G0925','308844':'G0490'}
    cc=con.set_index('station_id');byplant=pp.set_index('CECPlantID',drop=False);rows=[];sources=set()
    for k,(_,r) in enumerate(subs.iterrows()):
        hits=sorted(tree.query_ball_point(sx[k],PLANT_SCREEN_RADIUS),key=lambda j:np.linalg.norm(pxy[j]-sx[k]));closest=pp.iloc[hits[0]] if hits else None
        bid=focus.get(r.id,supported.get(r.id));matched=byplant.loc[bid] if bid in byplant.index else closest
        md=float(np.linalg.norm(np.array(tf.transform(matched.longitude,matched.latitude))-sx[k])) if matched is not None else np.nan
        existing=bool(r.existing_source_proxy);compatible=cc.loc[r.id,'registration_status']=='registered_compatible'
        active=matched is not None and matched.Retired_Plant==0 and matched.Capacity_Latest>0
        new=bool(r.id in supported and compatible and active and md<=250)
        reason='existing source retained as explicit proxy; completeness not presumed' if existing else 'no candidate evidence'
        if new:reason='reviewed station/CEC plant identity + <=250m colocation + nonretired generation + compatible line registration; generation proxy, not capacity/blackstart proof'
        elif r.id in focus and matched is not None and matched.Retired_Plant==1:reason='matched plant retired in current CEC snapshot; not an active source for contemporary baseline'
        elif hits or r.id in focus:reason='geographic/name candidate only; no confirmed station interconnection/operating-source role'
        b=boundary.get(r.id,{})
        if b and not(existing or new):reason+='; boundary corridor is a candidate, direction/external supply not established'
        decision='existing_source_retained' if existing else ('newly_supported_source_proxy' if new else ('candidate_but_unsupported' if b or (hits and not(r.id in focus and matched is not None and matched.Retired_Plant==1)) else ('rejected_generation_candidate' if r.id in focus else 'not_a_candidate')))
        if existing or new:sources.add(r.id)
        rows.append(dict(station_id=r.id,station_name=r.NAME,decision=decision,source_active_for_drybuild=existing or new,
            existing_source_type=r.source_type,plant_id=str(matched.CECPlantID) if matched is not None else '',plant_name=str(matched.PlantName) if matched is not None else '',
            plant_distance_m=md,plant_retired=matched.Retired_Plant if matched is not None else np.nan,
            plant_capacity_nameplate_MW=matched.Capacity_Latest if matched is not None else np.nan,
            plants_within_1km=';'.join(pp.iloc[hits].CECPlantID.astype(str)),boundary_interface_candidate=bool(b),
            boundary_path_km=b.get('distance_km',np.nan),boundary_crossing_xy=json.dumps(b.get('crossing_xy',[])),
            boundary_path_nodes_json=b.get('path_nodes_json',''),generation_identity_review=r.id in supported or r.id in focus,
            evidence=reason,evidence_source_url=plant['url'],temporal_scope='2026-06-12 CEC snapshot; historical 2022 candidates separately discussed'))
    return sources,pd.DataFrame(rows)

def baseline_gate(H,ids,sources):
    # Execute the actual normal source-gate helper in isolation using AST.
    # No main-module import, model initialization or sampler is executed.
    tree=ast.parse((ROOT/'C257H_Project_Main.py').read_text(encoding='utf-8-sig'))
    funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['clean_substation_id','apply_source_gate_to_substation_series']]
    assert len(funcs)==2
    mod=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+funcs,type_ignores=[])
    ns=dict(np=np,pd=pd,nx=nx,logging=logging,re=re)
    exec(compile(ast.fix_missing_locations(mod),'frozen_source_gate_only','exec'),ns)
    cfg=types.SimpleNamespace(SOURCE_GATE_ENABLED=True,FUNCTIONAL_THRESHOLD=.5)
    assert sources # do not trigger original helper's no-source ungated fallback
    out=ns['apply_source_gate_to_substation_series'](pd.DataFrame(np.ones((1,len(ids))),columns=ids),H,cfg,source_ids=sources,label='DryBuild_no_damage_baseline')
    return out.iloc[0].to_numpy(float)

def build():
    if TMP.exists():raise RuntimeError('One-build checkpoint already exists; do not silently rerun.')
    subs,tracts,dec,meta,olda=prepare();before={str((OLD/p.name).relative_to(ROOT)):sha(p) for p in Path(safe(OLD)).iterdir() if p.is_file()}
    plantfile=OUT/'SOURCE_EVIDENCE_SNAPSHOT.json'
    if not Path(safe(plantfile)).exists():
        z=json.loads((Path(tempfile.gettempdir())/'r1_closure_plant_source.json').read_text(encoding='utf-8'))
        Path(safe(plantfile)).write_text(json.dumps(z,ensure_ascii=False),encoding='utf-8')
    plant=json.loads(Path(safe(plantfile)).read_text(encoding='utf-8'))
    log=logging.getLogger();log.setLevel(logging.INFO);stream=io.StringIO();log.addHandler(logging.StreamHandler(stream));log.addHandler(logging.StreamHandler(sys.stdout))
    cfg=topo.Paths(OUTPUT_LINE_SPLIT_AUDIT_CSV=None,OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_AUDIT_CSV=None,OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_DEBUG_CSV=None)
    G,lines,sp,raw,split=topo.build_topology_wrapper(cfg,str(ROOT/'Data/TransmissionLine_CEC.shp'),subs,cfg.BBOX_PAD_KM,cfg.LINE_SNAP_TOLERANCE_M,cfg.LINE_SNAP_SECONDARY_TOLERANCE_M,cfg.LINE_SNAP_SECONDARY_MARGIN_M,cfg.LINE_SNAP_SECONDARY_RATIO_MAX)
    P=topo._collapse_multigraph_min_weight(G);sn,con=register(G,sp,lines,dec);print('COMPATIBLE REGISTRATION',len(sn),'/310',flush=True)
    # Uniform boundary-interface candidate: first modeled station reachable from
    # a crossing of the fixed study-tract UNION boundary, without intervening
    # registered stations. Keep candidate only; crossing does not prove import.
    area=tracts.to_crs(3310).geometry.union_all();rev={n:i for i,n in sn.items()};cross={}
    es=list(P.edges());geoms=np.array([LineString([topo._node_xy(u),topo._node_xy(v)]) for u,v in es],dtype=object)
    crossing=shapely.intersects(geoms,area.boundary)
    for edge_index in np.flatnonzero(crossing):
        u,v=es[edge_index];geom=geoms[edge_index]
        for n in [u,v]:
            if area.covers(Point(topo._node_xy(n))):cross[n]=list(geom.intersection(area.boundary).centroid.coords)[0]
    dist={};links=[];seen=set();boundary={};special={}
    for k,(sid,node) in enumerate(sn.items()):
        lengths,paths=nx.single_source_dijkstra(P,node,weight='weight');dist[sid]={t:lengths[n]/1000 for t,n in sn.items() if n in lengths}
        log.setLevel(logging.WARNING);got=topo.compute_direct_links({sid:dist[sid]},sn,{sid:paths},projection_anchor_df=split);log.setLevel(logging.INFO)
        for e in got:
            key=(e['src'],e['tgt'])
            if key not in seen:seen.add(key);links.append(e)
        for cn in sorted((n for n in cross if n in lengths),key=lambda n:(lengths[n],repr(n))):
            pa=paths[cn]
            if not any(n in rev and rev[n]!=sid for n in pa[1:]):
                boundary[sid]=dict(distance_km=lengths[cn]/1000,crossing_xy=cross[cn],path_nodes_json=json.dumps([topo._node_xy(n) for n in pa]));break
        if sid=='300105':
            for target in ['305984','307564']:
                if target in sn and sn[target] in paths:special[target]=paths[sn[target]]
        if (k+1)%50==0:print('PATHS',k+1,'direct links',len(links),flush=True)
    H=nx.Graph();H.add_nodes_from(subs.id);H.add_edges_from((e['src'],e['tgt'],{'weight':e['length_km']}) for e in links)
    comps=sorted(nx.connected_components(H),key=lambda c:(-len(c),min(c)));cm={i:k for k,c in enumerate(comps,1) for i in c}
    # Preserve completed construction before any table/export work.
    stage=dict(subs=subs,tracts=tracts,dec=dec,meta=meta,olda=olda,before=before,plant=plant,G=G,lines=lines,sp=sp,raw=raw,split=split,P=P,sn=sn,con=con,dist=dist,links=links,boundary=boundary,special=special,H=H,comps=comps,cm=cm,seen=seen,log_text=stream.getvalue())
    with (TMP.parent/'r1_closure_constructed_0a9e763.pkl').open('wb') as f:pickle.dump(stage,f,pickle.HIGHEST_PROTOCOL)
    sources,roles=source_roles(subs,con,boundary,plant);ids=subs.id.to_numpy(dtype=str)
    W0=wm.build_W_matrix(subs,tracts,dist);W=wm.apply_min_weight_threshold(W0,.03)
    gate=baseline_gate(H,ids,sources);service=W.to_numpy()@gate;pop=tracts.population.to_numpy(float)
    con['component']=con.station_id.map(cm);con['is_proposed_source']=con.station_id.isin(sources)
    con['baseline_source_reachable']=gate.astype(bool);con['population_weighted_dependency']=W.to_numpy().T@pop
    erows=[]
    oldpairs=set(zip(read(OLD/'R1_310_EDGES.csv',dtype={'src':str,'tgt':str}).src,read(OLD/'R1_310_EDGES.csv',dtype={'src':str,'tgt':str}).tgt))
    for e in links:erows.append(dict(src=e['src'],tgt=e['tgt'],length_km=e['length_km'],component=cm[e['src']],existed_in_05=(e['src'],e['tgt']) in oldpairs,path_wkt_epsg3310=LineString([topo._node_xy(n) for n in e['path_nodes']]).wkt))
    ed=pd.DataFrame(erows);csv(ed,'R1_310_EDGES.csv');csv(con,'STATION_CONNECTION_DECISIONS.csv');csv(roles,'SOURCE_ROLE_DECISIONS.csv')
    wa=W.to_numpy();w0=W0.to_numpy();top=wa.argmax(1);sort=np.sort(wa,axis=1);unresolved=set(con.loc[con.registration_status!='registered_compatible','station_id'])
    cause=[]
    for row in wa:
        targets=set(ids[row>0]);bad=targets-set(ids[gate>0]);cause.append('unresolved_registration' if bad&unresolved else ('source_less_component' if bad else 'baseline_complete'))
    q=pd.DataFrame(dict(tract_id=W.index,population=pop,row_sum=wa.sum(1),nonzero_before=(w0>0).sum(1),nonzero_after=(wa>0).sum(1),max_weight=sort[:,-1],top3_weight=sort[:,-3:].sum(1),top1_station=ids[top],baseline_service=service,baseline_incomplete=service<1-1e-10,cause=cause,
        cutoff_fallback=(w0>=.03).sum(1)==0,unregistered_access_finite_self_override=[ids[i] in unresolved for i in top],
        old_one_hot=(olda['W']>0).sum(1)==1,old_top1_station=olda['station_ids'][olda['W'].argmax(1)],old_baseline_service=olda['W']@np.array([0 if i in ['303547','307683','306980','309598'] else 1 for i in olda['station_ids']]),
        W_L1_change=np.abs(wa-olda['W']).sum(1)))
    q['old_one_hot_now_unresolved']=q.old_one_hot&q.old_top1_station.isin(unresolved)
    q['old_one_hot_now_source_less']=q.old_one_hot&q.old_top1_station.isin(set(ids[gate==0])-unresolved)
    q['old_one_hot_raw_inferred_voltage']=q.old_one_hot&q.old_top1_station.isin(set(subs.loc[subs.MAX_INFER=='Y','id']))
    csv(q,'R1_310_DEPENDENCY_QA.csv')
    meta2=dict(parent_commit='0a9e763cde7be7be7fc22c7e8656399a66e425f6',station_set_sha256=meta['station_set_sha256'],rules=dict(registration_radius_m=RADIUS,road_radius_m=ROAD_RADIUS,plant_candidate_radius_m=PLANT_SCREEN_RADIUS),
        metadata_changes=records(con[con.metadata_changed]),components=[dict(component=k,station_ids=sorted(c),source_ids=sorted(c&sources)) for k,c in enumerate(comps,1)],
        baseline_min=float(service.min()),baseline_incomplete_tracts=int((service<1-1e-10).sum()),baseline_incomplete_population=float(pop[service<1-1e-10].sum()),
        topology_log=stream.getvalue(),immutable_05_hashes=before,frozen_original_hashes=meta['frozen_input_hashes'],boundary_candidate_count=len(boundary),source_ids=sorted(sources),
        added_edges=[list(e) for e in sorted(seen-oldpairs)],removed_edges=[list(e) for e in sorted(oldpairs-seen)],
        source_evidence_sha256=sha(plantfile),driver_sha256=sha(__file__),
        physical_nodes=len(P),physical_edges=P.number_of_edges(),direct_edges=len(ed),registered_count=len(sn),
        W_row_sum_max_error=float(abs(wa.sum(1)-1).max()),W_one_hot_count=int(((wa>0).sum(1)==1).sum()),
        one_hot_433_associations=dict(unresolved=int(q.old_one_hot_now_unresolved.sum()),source_less=int(q.old_one_hot_now_source_less.sum()),raw_inferred=int(q.old_one_hot_raw_inferred_voltage.sum())))
    state=dict(subs=subs,tracts=tracts,G=G,P=P,lines=lines,sp=sp,raw=raw,split=split,sn=sn,dist=dist,H=H,links=links,con=con,roles=roles,comps=comps,gate=gate,W=W,W0=W0,special=special,meta=meta2)
    with TMP.open('wb') as f:pickle.dump(state,f,pickle.HIGHEST_PROTOCOL)
    save_arrays(state)
    for rel,h in before.items():assert sha(ROOT/rel)==h
    for rel,h in meta['frozen_input_hashes'].items():assert sha(ROOT/rel)==h
    print('BUILD DONE',json.dumps({k:meta2[k] for k in ['registered_count','direct_edges','baseline_min','baseline_incomplete_tracts','baseline_incomplete_population','source_ids','boundary_candidate_count','one_hot_433_associations']}),flush=True)

def save_arrays(s):
    with open(safe(OUT/'R1_310_CLOSURE_DATA.npz'),'wb') as f:np.savez_compressed(f,W=s['W'].to_numpy(),W_before_cutoff=s['W0'].to_numpy(),station_ids=s['subs'].id.to_numpy(dtype=str),tract_ids=s['W'].index.to_numpy(dtype=str),baseline_station_functionality=s['gate'],metadata_json=np.array(json.dumps(s['meta'],ensure_ascii=False,default=str)))

def road_access():
    from lxml import etree
    from pyproj import Transformer
    from sklearn.neighbors import BallTree
    subs,_,_,_,_=prepare();old=read(OLD/'R1_310_INPUT_READINESS.csv',dtype={'station_id':str,'road_node':str}).set_index('station_id')
    ns='{http://graphml.graphdrawing.org/xmlns}';keys={};coords={};edges=[];near_edges=[]
    focus=['305751','300950','301318','302923','307373','307683']
    foci=subs[subs.id.isin(focus)][['LONGITUDE','LATITUDE']].to_numpy(float)
    for _,e in etree.iterparse(str(ROOT/'Data/la_drive.graphml'),events=('end',),tag=[ns+'key',ns+'node',ns+'edge']):
        if e.tag==ns+'key':keys[e.get('id')]=e.get('attr.name')
        else:
            d={keys.get(c.get('key'),c.get('key')):c.text for c in e if c.tag==ns+'data'}
            if e.tag==ns+'node':coords[e.get('id')]=(float(d['x']),float(d['y']))
            else:
                u,v=e.get('source'),e.get('target');edges.append((u,v));q=np.array(coords[u])
                if np.any((abs(foci[:,0]-q[0])<.027)&(abs(foci[:,1]-q[1])<.027)):
                    geom=shapely.from_wkt(d['geometry']) if 'geometry' in d else LineString([coords[u],coords[v]])
                    near_edges.append(dict(u=u,v=v,geometry=geom,name=d.get('name',''),highway=d.get('highway',''),oneway=d.get('oneway','')))
        e.clear()
        while e.getprevious() is not None:del e.getparent()[0]
    G=nx.DiGraph();G.add_nodes_from(coords);G.add_edges_from(edges);ids=list(coords);ll=np.array([coords[i] for i in ids]);bt=BallTree(np.deg2rad(ll[:,::-1]),metric='haversine')
    bases=read(ROOT/'Data/stage45_C57_expanded_crew_origins.csv').drop_duplicates('yard_id');_,bi=bt.query(np.deg2rad(np.array([bases.latitude,bases.longitude]).T),k=1);bn=[ids[j] for j in bi.ravel()]
    comps=list(nx.strongly_connected_components(G));cm={i:k for k,c in enumerate(comps) for i in c};allowed_c={cm[i] for i in bn};allowed=set().union(*(comps[i] for i in allowed_c))
    tf=Transformer.from_crs(4326,3310,always_xy=True);xy=np.array(tf.transform(ll[:,0],ll[:,1])).T;tree=cKDTree(xy)
    ax=np.array([j for j,i in enumerate(ids) if i in allowed]);at=cKDTree(xy[ax]);sx=np.array(tf.transform(subs.LONGITUDE,subs.LATITUDE)).T
    rows=[]
    for k,(_,r) in enumerate(subs.iterrows()):
        cand=[j for j in tree.query_ball_point(sx[k],ROAD_RADIUS) if ids[j] in allowed]
        key=lambda j:(round(float(np.linalg.norm(xy[j]-sx[k])),7),int(ids[j]))
        chosen=min(cand,key=key) if cand else None
        assert (min(list(reversed(cand)),key=key) if cand else None)==chosen
        nearest_distance,nearidx=at.query(sx[k]);oi=old.loc[r.id,'road_node'];ni=ids[chosen] if chosen is not None else ''
        baseids=[str(bases.iloc[j].yard_id) for j,n in enumerate(bn) if chosen is not None and cm[n]==cm[ni]]
        rows.append(dict(station_id=r.id,station_name=r.NAME,longitude=r.LONGITUDE,latitude=r.LATITUDE,
            old_road_node=oi,old_distance_m=old.loc[r.id,'road_snap_distance_m'],old_roundtrip_to_same_base=cm[oi] in allowed_c,
            proposed_road_node=ni,proposed_distance_m=float(np.linalg.norm(xy[chosen]-sx[k])) if chosen is not None else np.nan,
            compatible_nodes_within_500m=len(cand),node_changed=ni!=oi,
            proposed_roundtrip_to_base=chosen is not None,compatible_base_ids=';'.join(baseids),
            nearest_roundtrip_node_without_radius=ids[ax[nearidx]],nearest_roundtrip_distance_m=float(nearest_distance),
            decision='accepted_geometric_road_access_proxy' if chosen is not None else 'unresolved_no_roundtrip_node_within_500m',
            evidence='same directed SCC as at least one original base; nearest by EPSG3310 distance and stable node-ID tie' if chosen is not None else 'no candidate within fixed 500m review radius; no presumed public gate or invented private road',
            physical_gate_verified=False))
    df=pd.DataFrame(rows);csv(df,'ROAD_ACCESS_DECISIONS.csv')
    nr=gpd.GeoDataFrame(near_edges,geometry='geometry',crs=4326).to_crs(3310)
    pdata={}
    for sid in focus:
        row=df[df.station_id==sid].iloc[0];k=list(subs.id).index(sid);p=sx[k]
        nearby=tree.query_ball_point(p,2200);pdata[sid]=dict(station_xy=p,old_xy=np.array(tf.transform(*coords[row.old_road_node])),new_xy=np.array(tf.transform(*coords[row.proposed_road_node])) if row.proposed_road_node else None,
          nodes_xy=xy[nearby],allowed=np.array([ids[j] in allowed for j in nearby]),
          edges=nr[nr.intersects(shapely.box(p[0]-2200,p[1]-2200,p[0]+2200,p[1]+2200))])
    rm=dict(rule_radius_m=ROAD_RADIUS,base_count=len(bn),same_base_SCC_rule=True,allowed_node_count=len(allowed),
        accepted=int(df.proposed_roundtrip_to_base.sum()),unresolved_ids=df.loc[~df.proposed_roundtrip_to_base,'station_id'].tolist(),
        changed_ids=df.loc[df.node_changed,'station_id'].tolist(),road_graph_sha256=sha(ROOT/'Data/la_drive.graphml'),
        original_base_input_sha256=sha(ROOT/'Data/stage45_C57_expanded_crew_origins.csv'))
    with (Path(tempfile.gettempdir())/'r1_closure_road_0a9e763.pkl').open('wb') as f:pickle.dump(dict(meta=rm,plot=pdata),f,pickle.HIGHEST_PROTOCOL)
    print('ROAD DONE',rm,flush=True);print(df[df.station_id.isin(focus)].to_string(index=False),flush=True)

def finish():
    """Local path QA and artifact completion from saved dry-build inputs only."""
    with TMP.open('rb') as f:s=pickle.load(f)
    with (TMP.parent/'r1_closure_road_0a9e763.pkl').open('rb') as f:road=pickle.load(f)
    P,H,sn,split=s['P'],s['H'],s['sn'],s['split']
    anchor=split[split.substation_id.astype(str)=='310294'].iloc[0]
    anchor_key=topo._graph_node_key((anchor.cut_x,anchor.cut_y));station_node=sn['310294']
    anchors=[n for n in P if topo._graph_node_key(topo._node_xy(n))==anchor_key]
    projection=dict(anchor=records(split[split.substation_id.astype(str)=='310294'])[0],
        registered_node=repr(station_node),anchor_nodes=[repr(n) for n in anchors],
        connector_present=any(P.has_edge(station_node,n) for n in anchors),special_paths=[])
    reverse=collections.defaultdict(list)
    for sid,n in sn.items():reverse[n].append(sid)
    for target,path in s['special'].items():
        projection['special_paths'].append(dict(src='300105',tgt=target,
            registered_station_sequence=[sid for n in path for sid in reverse[n]],
            registered_310294_on_path=station_node in path,
            projection_310294_on_path=any(n in path for n in anchors),
            facility_shortest_chain=nx.shortest_path(H,'300105',target,weight='weight')))
    # Only the ten immediate facility neighbours of the one disputed anchor.
    # This is a local representation counterfactual, never adopted as topology.
    neighbours=sorted(H.neighbors('310294'));current=set();without=set()
    noanchor=split[split.substation_id.astype(str)!='310294']
    for sid in neighbours:
        lengths,paths=nx.single_source_dijkstra(P,sn[sid],weight='weight')
        d={sid:{t:lengths[n]/1000 for t,n in sn.items() if n in lengths}}
        for a,result in [(split,current),(noanchor,without)]:
            for e in topo.compute_direct_links(d,sn,{sid:paths},projection_anchor_df=a):result.add((e['src'],e['tgt']))
    projection.update(local_sources_checked=neighbours,local_links_added_if_only_310294_anchor_disabled=[list(e) for e in sorted(without-current)],
        local_links_removed_if_only_310294_anchor_disabled=[list(e) for e in sorted(current-without)],
        scope='ten existing neighbours; not an exhaustive all-pairs projection sensitivity',
        algorithm_change_applied=False,
        interpretation='deliberate virtual facility interface in frozen compute_direct_links; series electrical role is an unvalidated representation assumption')
    unresolved=set(s['con'].loc[s['con'].registration_status!='registered_compatible','station_id'])
    bypass=[]
    for sid in sorted(unresolved):
        row=s['sp'][s['sp'].id==sid].iloc[0];key=topo._graph_node_key((row.geometry.x,row.geometry.y))
        for e in s['links']:
            if any(topo._graph_node_key(topo._node_xy(n))==key for n in e['path_nodes'][1:-1]):bypass.append(dict(unresolved_site=sid,src=e['src'],tgt=e['tgt']))
    # Keep candidate matches distinct from reviewed same-facility identities.
    roles=s['roles'].copy()
    roles['plant_match_basis']=np.where(roles.generation_identity_review,'reviewed_facility_identity_crosswalk','nearest_point_candidate_only_not_identity')
    roles['generation_decision']=np.where(roles.decision=='newly_supported_source_proxy','supported_generation_proxy',
        np.where(roles.generation_identity_review&(roles.plant_retired==1),'rejected_current_generation_candidate',
        np.where(roles.existing_source_type=='in_basin_generation_proxy','retained_existing_generation_assumption',
        np.where(roles.plants_within_1km.fillna('')!='','candidate_but_unsupported','not_a_generation_candidate'))))
    roles['import_decision']=np.where(roles.existing_source_type=='import_interface_proxy','retained_existing_import_assumption',
        np.where(roles.boundary_interface_candidate,'boundary_crossing_candidate_not_promoted','not_a_boundary_candidate'))
    roles['source_energized_condition']='proxy assumed available at baseline; no blackstart, capacity or external supply verification'
    roles['operating_epoch_note']='inventory/line vintage differs from 2026 generator-status screen; no historical operation inferred solely from current status'
    roles.loc[roles.station_id=='303547','operating_epoch_note']='SERRF generated in 2022; retired 2024-04-01 in CEC; official FY25 record reports 66kV station and lines de-energized after November 2024 decommissioning'
    roles.loc[roles.station_id=='308844','operating_epoch_note']='Redondo units 5,6,8 removed from service 2024-01-01 per Water Board 2025 order p2 para10; historical 2022 role differs'
    roles.loc[roles.station_id=='304450','operating_epoch_note']='HARBORGEN retained only as legacy source assumption; nearest retired Calciner plant is NOT an identity match; current electrical source identity remains unverified'
    csv(roles,'SOURCE_ROLE_DECISIONS.csv');s['roles']=roles
    s['meta']['projection_review']=projection;s['meta']['direct_paths_through_unresolved_site_coordinates']=bypass;s['meta']['road_access']=road['meta']
    con=s['con'].copy()
    con['selected_node_has_multiple_voltage_families']=con.selected_node_voltage_families.str.contains(';',regex=False)
    con['local_boundary_decision']='retain eligible facility; no source or edge added'
    for sid,note in {
        '303547':'Case C for contemporary baseline: retired SERRF; official 66kV de-energization; historical 2022 generation differs',
        '307683':'Case C: paired with retired SERRF geometry; actual upstream service relation unresolved',
        '306980':'Case C: isolated 66kV geometry; nearby main graph is not evidence of an electrical tie',
        '309598':'Case C: CEC Montrose; 66kV stub near 230kV scope; no supported transformer/tie',
        '301479':'unresolved 120kV line scope; no fallback to 66/69',
        '303265':'unresolved inferred 230kV; CEC Max missing; no inferred replacement from nearby 66/69',
        '304137':'unresolved 138kV scope; geometry through this site is retained but nine direct paths bypass its facility role',
        '305021':'unresolved inferred 230kV; nearby hydro point alone does not establish station voltage/connection'
    }.items():con.loc[con.station_id==sid,'local_boundary_decision']=note
    csv(con,'STATION_CONNECTION_DECISIONS.csv');s['con']=con
    dq=read(OUT/'R1_310_DEPENDENCY_QA.csv',dtype={'tract_id':str,'top1_station':str,'old_top1_station':str})
    dq['old_one_hot_current_inferred_provisional']=dq.old_one_hot&dq.old_top1_station.isin(set(con.loc[con.voltage_evidence_strength=='HIFLD_inferred_provisional','station_id']))
    csv(dq,'R1_310_DEPENDENCY_QA.csv')
    s['meta']['one_hot_433_associations']['current_inferred_provisional']=int(dq.old_one_hot_current_inferred_provisional.sum())
    ed=read(OUT/'R1_310_EDGES.csv',dtype={'src':str,'tgt':str});bp=collections.defaultdict(set)
    for row in bypass:bp[(row['src'],row['tgt'])].add(row['unresolved_site'])
    ed['unresolved_site_coordinates_on_path']=[';'.join(sorted(bp[(a,b)])) for a,b in zip(ed.src,ed.tgt)]
    csv(ed,'R1_310_EDGES.csv')
    rdf=read(OUT/'ROAD_ACCESS_DECISIONS.csv',dtype={'station_id':str,'old_road_node':str,'proposed_road_node':str,'nearest_roundtrip_node_without_radius':str})
    rdf['geometry_review']='not individually reviewed; accepted nodes remain geometric access proxies, not verified facility gates'
    for sid,d in road['plot'].items():
        dd=d['edges'].geometry.distance(Point(d['station_xy']));j=dd.idxmin();e=d['edges'].loc[j]
        notes={
            '305751':'old sink node replaced by same-base roundtrip node under all-station rule; facility gate unverified',
            '300950':'road geometry only 78m away but nearest graph vertex 838m: simplified-node spacing contributes; not evidence of missing public road',
            '301318':'road geometry 526m away; landfill/energy site interior access not represented or verified; keep unresolved',
            '302923':'road geometry 781m away; industrial facility interior consistent with sparse drive graph; public gate/private route unverified',
            '307373':'road geometry 428m away but nearest vertex 545m: simplified-node spacing contributes; gate/private connection unverified',
            '307683':'road geometry 1355m away; port-area drive graph coverage gap near facility; no verified gate or traversable connector'
        }
        mask=rdf.station_id==sid;rdf.loc[mask,'geometry_review']=notes[sid]
        rdf.loc[mask,'nearest_local_road_geometry_distance_m']=float(dd.loc[j])
        rdf.loc[mask,'nearest_local_road_name']=str(e['name'])
        rdf.loc[mask,'nearest_local_road_edge_uv']=str(e.u)+';'+str(e.v)
    csv(rdf,'ROAD_ACCESS_DECISIONS.csv')
    evidence=con[['station_id','CEC_2022_name','CEC_2022_max_voltage','CEC_2022_source']]
    s['meta']['CEC_2022_exact_ID_evidence_records']=records(evidence)
    s['meta']['CEC_2022_exact_ID_evidence_sha256']=hashlib.sha256(json.dumps(records(evidence),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    s['meta']['source_gate_module_sha256']=sha(ROOT/'C257H_Project_Main.py')
    s['meta']['official_SERRF_evidence']=dict(url='https://www.longbeach.gov/globalassets/city-manager/media-library/documents/memos-to-the-mayor-tabbed-file-list-folders/2026/april-3--2026---citywide-accomplishment-dashboard-and-webpage---fy-25',
        sha256='93039e5347b243f018dd111901a59ecbc7766c4dd734e76e2ece67dd807b90b2',pdf_page=28,printed_page='24 of 69',item=1500,
        interpretation='SCE de-energized 66kV substation/transmission lines after November 2024 decommissioning; independently rendered and read')
    s['meta']['decision']='FAIL';s['meta']['recovery_preparation_authorized']=False
    s['meta']['driver_sha256']=sha(__file__)
    save_arrays(s)
    # One geometry figure; no outcome, damage or strategy variables are read.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig,axes=plt.subplots(3,3,figsize=(16,14),layout='constrained')
    def topo_panel(ax,focus,radius,title):
        pp=s['sp'][s['sp'].id==focus].iloc[0].geometry;x,y=pp.x,pp.y
        crop=shapely.box(x-radius,y-radius,x+radius,y+radius)
        seg=s['lines'][s['lines'].intersects(crop)]
        for _,r in seg.iterrows():
            xy=np.array(r.geometry.coords);sig=topo._line_topology_signature(r,topo._detect_voltage_column(s['lines']));family=dict(sig).get('voltage_family','')
            ax.plot(xy[:,0]-x,xy[:,1]-y,color='#2563eb' if family=='66_69' else '#c2410c',lw=1.3)
        for sid in s['sp'][s['sp'].intersects(crop)].id:
            rr=s['sp'][s['sp'].id==sid].iloc[0];p=rr.geometry
            ax.scatter(p.x-x,p.y-y,marker='^',color='black',s=40,zorder=5);ax.annotate(sid,(p.x-x,p.y-y),fontsize=7,xytext=(3,4),textcoords='offset points')
            if sid in sn:
                xx,yy=topo._node_xy(sn[sid]);ax.plot([p.x-x,xx-x],[p.y-y,yy-y],color='#059669',ls='--');ax.scatter(xx-x,yy-y,marker='x',color='#059669',s=35,zorder=7)
        ax.set(xlim=(-radius,radius),ylim=(-radius,radius),title=title,xlabel='Easting relative to station (m)',ylabel='Northing (m)');ax.set_aspect('equal');ax.grid(alpha=.2)
    topo_panel(axes[0,0],'308336',260,'AIRCHEM: blue 66/69; orange other voltage')
    topo_panel(axes[0,1],'310294',8,'310294: 1.785 m virtual projection interface')
    topo_panel(axes[0,2],'303547',2600,'SERRF / NAVY MOLE: retained source-less geometry')
    labels={'305751':'WESTHILL','300950':'SHELLWATT','301318':'HILGEN','302923':'UNKNOWN302923 / Chevron Central','307373':'HAYNES','307683':'NAVY MOLE'}
    for ax,(sid,dat) in zip(axes.flat[3:],road['plot'].items()):
        p=dat['station_xy'];extent=max(750,float(np.linalg.norm(dat['old_xy']-p))*1.25)
        lines=[np.array(g.coords)-p for g in dat['edges'].geometry if g.geom_type=='LineString']
        ax.add_collection(LineCollection(lines,colors='#9ca3af',linewidths=.7))
        xy=dat['nodes_xy']-p;allowed=dat['allowed'];ax.scatter(xy[allowed,0],xy[allowed,1],s=3,color='#93c5fd',alpha=.6)
        ax.add_patch(plt.Circle((0,0),500,fill=False,color='#64748b',ls='--',lw=1))
        ax.scatter(0,0,marker='^',color='black',s=60,label='Facility coordinate',zorder=6)
        old=dat['old_xy']-p;ax.scatter(*old,marker='x',color='#dc2626',s=75,label='Previous nearest node',zorder=7)
        ax.plot([0,old[0]],[0,old[1]],color='#dc2626',lw=.9,ls=':')
        if dat['new_xy'] is not None:
            new=dat['new_xy']-p;ax.scatter(*new,marker='o',facecolors='none',edgecolors='#059669',s=85,label='Accepted roundtrip node',zorder=8)
        ax.set(xlim=(-extent,extent),ylim=(-extent,extent),title=labels[sid],xlabel='Easting relative to facility (m)',ylabel='Northing (m)');ax.set_aspect('equal');ax.grid(alpha=.2)
    axes[1,0].legend(fontsize=7,loc='lower right')
    fig.suptitle('R1-310 local input QA | no recovery simulation | geometry does not verify facility gates',fontsize=14)
    fig.savefig(safe(OUT/'R1_310_LOCAL_QA_MAP.png'),dpi=180);plt.close(fig)
    print('PROJECTION',json.dumps(projection,default=str),flush=True)
    print('UNRESOLVED_SITE_BYPASS',json.dumps(bypass),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--road',action='store_true');p.add_argument('--finish',action='store_true');args=p.parse_args()
    if args.build:build()
    if args.road:road_access()
    if args.finish:finish()
    if not args.build and not args.road and not args.finish:p.error('Explicit --build, --road or --finish required; no recovery command exists')
