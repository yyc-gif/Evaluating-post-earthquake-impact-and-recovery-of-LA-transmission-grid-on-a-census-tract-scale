"""Analysis only: frozen July92 maps, new external evidence and static single-node outages."""
from pathlib import Path
import ast, csv, hashlib, importlib.util, json, logging, re, types
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
EXT=ROOT/'External_Validation_Data'
N=EXT/'normalized'
OLD=ROOT/'R1_Comment1_July92_Utility_Constraint'
OUT.mkdir(exist_ok=True)
USED={}
def read(p,**kw):
    p=Path(p);USED[str(p.relative_to(ROOT))]=True
    return pd.read_csv(p,**kw)
def save(df,name):
    if name.endswith('.parquet'):df.to_parquet(OUT/name,index=False)
    else:df.to_csv(OUT/name,index=False,encoding='utf-8-sig')
def norm(x):
    if pd.isna(x):return ''
    return re.sub('[^A-Z0-9]','',str(x).upper())
def site(x):
    # Explicit voltage suffix, not fuzzy spelling/nearest matching.
    return norm(re.sub(r'\s+\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)+(?:\s*kV)?(?:\s*System)?\s*$','',str(x),flags=re.I))
def unique_lookup(frame,namecol,idcol):
    return {k:sorted(set(v[idcol].astype(str))) for k,v in frame.assign(_key=frame[namecol].map(norm)).groupby('_key')}
def getone(k,lookup):
    a=lookup.get(k,[])
    return a[0] if len(a)==1 else ''
def load():
    global stations,sids,tids,tracts,xy,G,maps,utility,pop,circuits,subs,cross,cand
    stations=read(ROOT/'Data/working_area_substations_with_fragility.csv',dtype={'ID':str}).set_index('ID')
    nodes=read(ROOT/'Data/substation_graph_CEC_nodes_expanded.csv',dtype={'id':str})
    edges=read(ROOT/'Data/substation_graph_CEC_edges_expanded.csv',dtype={'u':str,'v':str})
    sids=nodes.id.tolist()
    assert len(sids)==92 and len(edges)==318
    stations=stations.reindex(sids)
    rawtract=read(ROOT/'Data/Tracts_Within_Expanded_Area.csv',dtype={'GEOID':str})
    rawtract.GEOID=rawtract.GEOID.str.zfill(11);tids=rawtract.GEOID.tolist()
    tracts=gpd.GeoDataFrame(rawtract.drop(columns='wkt_geom'),geometry=gpd.GeoSeries.from_wkt(rawtract.wkt_geom,crs=4326)).to_crs(3310)
    xy=gpd.GeoSeries(gpd.points_from_xy(stations.LONGITUDE,stations.LATITUDE),crs=4326).to_crs(3310)
    xy.index=sids
    G=nx.Graph();G.add_nodes_from(sids);G.add_weighted_edges_from(edges[['u','v','length_km']].itertuples(index=False,name=None))
    assert len(G.edges)==318
    maps={}
    for name,path in [('JULY_BASELINE_92',ROOT/'Data/tract_to_substation_mapping_CEC_expanded.csv'),('JULY_UTILITY_CONSTRAINED_92',OLD/'JULY_UTILITY_CONSTRAINED_92.csv')]:
        df=read(path,dtype={'tract_id':str,'substation_id':str});df.tract_id=df.tract_id.str.zfill(11)
        maps[name]=df.pivot_table(index='tract_id',columns='substation_id',values='weight',aggfunc='sum',fill_value=0).reindex(index=tids,columns=sids,fill_value=0).to_numpy()
    structure=read(OLD/'MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv',dtype={'tract_id':str})
    structure.tract_id=structure.tract_id.str.zfill(11);structure=structure.set_index('tract_id').reindex(tids)
    utility=structure.utility_domain.to_numpy();pop=structure.population.to_numpy()
    p=N/'SCE_Distribution_circuits_0_Distribution_Circuits.geojson';USED[str(p.relative_to(ROOT))]=True
    circuits=gpd.read_file(p).to_crs(3310)
    p=N/'SCE_ICA_Layer_18_Substations.geojson';USED[str(p.relative_to(ROOT))]=True
    subs=gpd.read_file(p).to_crs(3310)
    lookup=unique_lookup(stations.reset_index().query("Owner=='SCE'"),'NAME','ID')
    circuits['direct_id']=[getone(site(x),lookup) for x in circuits.sub_name]
    circuits['system_id']=[getone(site(x),lookup) for x in circuits.sys_name]
    circuits['direct_key']=circuits.sub_name.map(site)
    cross=[]
    for name,g in circuits.groupby(['sub_name','sys_name'],dropna=False):
        a,b=name;did=g.direct_id.iloc[0];sid=g.system_id.iloc[0]
        sn=subs[subs.sub_name.map(norm)==site(a)]
        dist=np.nan
        if did and len(sn):
            dist=float(sn.geometry.distance(xy.loc[did]).min()/1000)
        cross.append(dict(external_substation=a,external_system=b,direct_July92_id=did,system_July92_id=sid,direct_match_rule='Unique normalized name after explicit voltage suffix removal' if did else 'No exact identity; no forced nearest match',direct_station_point_distance_km=dist,circuit_records=len(g),circuit_names=';'.join(sorted(set(g.circt_nam))),external_substation_point_count=len(sn)))
    cross=pd.DataFrame(cross)
    # Exact names whose external station points disagree spatially are not accepted automatically.
    bad=cross.loc[cross.direct_station_point_distance_km>2,'direct_July92_id'].unique()
    if len(bad):raise RuntimeError('Exact name with >2km coordinate discrepancy: '+str(bad))
    save(cross,'SCE_STATION_EVIDENCE_CROSSWALK.csv')
    p=N/'SCE_CIRCUIT_SUBSTATION_LOAD_LINK_READINESS.csv';link=read(p,dtype={'circuit_id':str})
    circuits['circuit_id']=circuits.circuit_id.astype(str)
    circuits=circuits.merge(link[['circuit_id','historical_circuit_exact_name_match','forecast_circuit_exact_name_match']],on='circuit_id',how='left',validate='one_to_one')
    # Positive line length inside a tract; mere boundary point contact is not evidence.
    joined=gpd.sjoin(circuits,tracts[['GEOID','geometry']],predicate='intersects',how='inner')
    joined['intersection_m']=np.array([g.intersection(tracts.geometry.loc[int(i)]).length for g,i in zip(joined.geometry,joined.index_right)])
    joined=joined[joined.intersection_m>0].copy()
    save(pd.DataFrame(joined.drop(columns='geometry')),'SCE_CIRCUIT_TRACT_EVIDENCE.parquet')
    cand={}
    for t in tids:
        q=joined[joined.GEOID==t]
        cand[t]={'official':set(q.direct_key)-{''},'direct':set(q.direct_id)-{''},'system':set(q.system_id)-{''},'circuit_count':len(q),'historical_linked_circuits':int(q.historical_circuit_exact_name_match.sum())}
    print('LOADED',len(joined),'circuit-tract intersections',flush=True)

def benchmark():
    coverage=[]
    for i,t in enumerate(tids):
        c=cand[t];coverage.append(dict(tract_id=t,utility_domain=utility[i],official_site_candidate_count=len(c['official']),represented_direct_count=len(c['direct']),represented_direct_ids=';'.join(sorted(c['direct'])),represented_system_ids=';'.join(sorted(c['system'])),intersecting_circuit_rows=c['circuit_count'],historical_load_linked_circuit_rows=c['historical_linked_circuits'],represented_direct_fraction=len(c['direct'])/len(c['official']) if c['official'] else np.nan))
    save(pd.DataFrame(coverage),'SCE_TRACT_INVENTORY_COVERAGE.csv')
    old=read(OLD/'SCE_CANDIDATE_BENCHMARK_TRACTS.csv',dtype={'tract_id':str})
    old.tract_id=old.tract_id.str.zfill(11)
    oldsets={x.tract_id:set(str(x.official_candidates_in_July92).split(';')) for x in old.itertuples()}
    matched_new={t for i,t in enumerate(tids) if utility[i]=='SCE' and cand[t]['direct']}
    common=matched_new & set(oldsets)
    def rows(version,kind,sets,subset=None):
        out=[]
        for i,t in enumerate(tids):
            if utility[i]!='SCE' or not sets.get(t) or (subset is not None and t not in subset):continue
            c=sets[t]
            for name,w in maps.items():
                ix=np.flatnonzero(w[i]>0);ix=ix[np.argsort(-w[i,ix],kind='stable')]
                pids=[sids[k] for k in ix];a=set(pids);m=a&c
                dist=min(xy.loc[pids[0]].distance(xy.loc[cid]) for cid in c)/1000
                out.append(dict(version=version,candidate_kind=kind,mapping=name,tract_id=t,official_ids=';'.join(sorted(c)),mapped_ids=';'.join(pids),any_match=bool(m),top1=pids[0] in c,top3=bool(set(pids[:3])&c),precision=len(m)/len(a),recall=len(m)/len(c),candidate_count=len(a),max_weight=w[i].max(),HHI=float(w[i]@w[i]),effective_count=1/float(w[i]@w[i]),top1_distance_km=dist,represented_official_weight=float(sum(w[i,sids.index(cid)] for cid in c))))
        return out
    allrows=[]
    allrows+=rows('NEW_20260922','direct_site',{t:cand[t]['direct'] for t in tids})
    allrows+=rows('NEW_20260922','named_system_context_only',{t:cand[t]['system'] for t in tids})
    allrows+=rows('OLD_RETAINED','old_crosswalk',oldsets)
    allrows+=rows('NEW_ON_COMMON_TRACTS','direct_site',{t:cand[t]['direct'] for t in tids},common)
    allrows+=rows('OLD_ON_COMMON_TRACTS','old_crosswalk',oldsets,common)
    df=pd.DataFrame(allrows);save(df,'SCE_MAPPING_BENCHMARK_TRACTS.csv')
    met=['any_match','top1','top3','precision','recall','candidate_count','max_weight','HHI','effective_count','top1_distance_km','represented_official_weight']
    summary=df.groupby(['version','candidate_kind','mapping'])[met].mean().reset_index()
    summary['tract_count']=df.groupby(['version','candidate_kind','mapping']).size().to_numpy()
    save(summary,'SCE_MAPPING_BENCHMARK_SUMMARY.csv')
    v=[]
    for t in sorted(set(oldsets)|matched_new):
        oldc=oldsets.get(t,set());newc=cand[t]['direct']
        v.append(dict(tract_id=t,old_ids=';'.join(sorted(oldc)),new_ids=';'.join(sorted(newc)),old_present=bool(oldc),new_present=bool(newc),same_candidate_set=oldc==newc,added=';'.join(sorted(newc-oldc)),removed=';'.join(sorted(oldc-newc))))
    save(pd.DataFrame(v),'BENCHMARK_VERSION_COVERAGE_CHANGE.csv')
    print(summary.to_string(index=False),flush=True)

def gate_diagnostics():
    global impact,gs,gate_meta
    source=read(ROOT/'Data/source_nodes_core_expanded.csv',dtype={'ID':str})
    source_ids=set(source.loc[source.level.str.lower().eq('core'),'ID'])&set(sids)
    # Execute the frozen production gate function only, without importing/running the pipeline.
    p=ROOT/'C257H_Project_Main.py';USED[str(p.relative_to(ROOT))]=True
    text=p.read_text(encoding='utf-8-sig');tree=ast.parse(text)
    names={'clean_substation_id','apply_source_gate_to_substation_series'}
    fs=[f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name in names]
    code=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+fs,type_ignores=[])
    ns=dict(np=np,pd=pd,nx=nx,logging=logging)
    exec(compile(ast.fix_missing_locations(code),str(p),'exec'),ns)
    cfg=types.SimpleNamespace(FUNCTIONAL_THRESHOLD=0.5,SOURCE_GATE_ENABLED=True)
    cases=['300493','301637','308581','310179','301105','307693'] # J,N,Q,C,K,Rinaldi
    raw=pd.DataFrame(np.ones((1+len(cases),len(sids))),columns=sids,index=['ALL_FUNCTIONAL']+cases)
    for sid in cases:raw.loc[sid,sid]=0
    states=ns['apply_source_gate_to_substation_series'](raw,G,cfg,source_ids=source_ids,label='static_named_outage')
    base=states.loc['ALL_FUNCTIONAL'].to_numpy()
    assert np.all(base==1)
    out=[];sums=[]
    for sid in cases:
        loss=base-states.loc[sid].to_numpy()
        extra=[sids[j] for j in np.flatnonzero(loss) if sids[j]!=sid]
        for name,w in maps.items():
            direct=w[:,sids.index(sid)];total=w@loss;extra_impact=total-direct
            assert np.all(extra_impact>=-1e-12)
            for i,t in enumerate(tids):
                out.append(dict(station_id=sid,station_name=stations.loc[sid,'NAME'],mapping=name,tract_id=t,utility_domain=utility[i],population=pop[i],direct_weight_loss=direct[i],additional_path_loss=extra_impact[i],total_proxy_loss=total[i],single_station_outage=True))
            sums.append(dict(station_id=sid,station_name=stations.loc[sid,'NAME'],mapping=name,is_original_source=sid in source_ids,remaining_connected_stations=int((states.loc[sid]>0).sum()),additional_disconnected_station_count=len(extra),additional_disconnected_ids=';'.join(extra),tracts_direct_positive=int((direct>0).sum()),tracts_additional_path_positive=int((extra_impact>1e-12).sum()),tracts_total_positive=int((total>0).sum()),mean_proxy_loss=float(total.mean()),population_weighted_proxy_loss=float(np.average(total,weights=pop)),sum_population_times_proxy_loss=float(pop@total),population_in_any_positive_tract=float(pop[total>0].sum()),max_tract_proxy_loss=float(total.max())))
    impact=pd.DataFrame(out);gs=pd.DataFrame(sums)
    save(impact,'STATIC_EVENT_TRACT_IMPACTS.parquet');save(gs,'STATIC_EVENT_DIAGNOSTICS.csv')
    gate_meta=dict(source_ids=sorted(source_ids),source_count=len(source_ids),static_states_evaluated=len(raw),gate_function_sha256=hashlib.sha256(ast.get_source_segment(text,next(f for f in fs if f.name=='apply_source_gate_to_substation_series')).encode()).hexdigest(),interpretation='all-other-stations-functional single-node outage; not accident replay',pipeline_MC_GA_recovery_runs=0)
    (OUT/'STATIC_DIAGNOSTIC_DEFINITION.json').write_text(json.dumps(gate_meta,indent=2),encoding='utf-8')
    print(gs.to_string(index=False),flush=True)

def cpuc_links():
    cn=circuits.assign(_name=circuits.circt_nam.map(norm))
    byname={k:g for k,g in cn.groupby('_name')}
    out=[];summaries=[]
    def parse_clock(date_value,time_value):
        ds=str(date_value).strip();ts=str(time_value).strip()
        if not re.match(r'^2025-\d{2}-\d{2}',ds):return pd.NaT
        # The second workbook encodes full datetimes in its time cells.
        if re.match(r'^2025-\d{2}-\d{2} ',ts):
            if ts[:10]!=ds[:10]:return pd.NaT
            return pd.to_datetime(ts,format='%Y-%m-%d %H:%M:%S',errors='coerce')
        if re.fullmatch(r'\d{1,2}:\d{2}',ts):ts+=':00'
        return pd.to_datetime(ds[:10]+' '+ts,format='%Y-%m-%d %H:%M:%S',errors='coerce')
    def countykey(x):return ';'.join(sorted(re.split(r'[,;]\s*',str(x).strip().upper())))
    for sheet in sorted((N/'CPUC').glob('2025*event-data-workbookfinal/T05.csv')):
        USED[str(sheet.relative_to(ROOT))]=True;stem=sheet.parent.name
        rr=list(csv.reader(sheet.open(encoding='utf-8-sig')));timing=[];customers={};mode=None;shared=False
        for n,v in enumerate(rr):
            if len(v)==1:
                mode=None
                if 'PG&E Shared' in v[0]:shared=True
            if len(v)>2 and v[0]=='County' and v[1]=='Circuit Name':
                mode='time' if 'Date' in v[2] else 'customer';continue
            if len(v)<8 or not mode or shared:continue
            k=(countykey(v[0]),norm(v[1]))
            if mode=='customer':customers.setdefault(k,[]).append(v)
            else:timing.append(dict(zip(['county','circuit_name','deenergization_date_raw','deenergization_time_raw','all_clear_date_raw','all_clear_time_raw','restoration_date_raw','restoration_time_raw','HFTD','classification'],v))|dict(normalized_sheet_row=n+1,shared_PGE=shared))
        d=pd.DataFrame(timing)
        reasonfile=N/'CPUC'/stem/'T14.csv'; reasons={}
        if reasonfile.exists():
            USED[str(reasonfile.relative_to(ROOT))]=True
            rr=list(csv.reader(reasonfile.open(encoding='utf-8-sig')))
            start=next(i for i,v in enumerate(rr) if v and v[0]=='Circuit Name')
            for row in rr[start+1:]:
                if len(row)>1 and row[0]:reasons.setdefault(norm(row[0]),[]).append(row[1])
        for i,row in d.iterrows():
            key=norm(row.circuit_name);g=byname.get(key)
            begin=parse_clock(row.deenergization_date_raw,row.deenergization_time_raw)
            finish=parse_clock(row.restoration_date_raw,row.restoration_time_raw)
            clear=parse_clock(row.all_clear_date_raw,row.all_clear_time_raw)
            cust=customers.get((countykey(row.county),norm(row.circuit_name)),[])
            custcount=pd.to_numeric(cust[0][6],errors='coerce') if len(cust)==1 else np.nan
            out.append(dict(workbook=stem,source_row=row.normalized_sheet_row,shared_PGE=row.shared_PGE,customer_table_matches=len(cust),reported_total_customers=custcount,raw_deenergization_date=row.deenergization_date_raw,raw_deenergization_time=row.deenergization_time_raw,raw_restoration_date=row.restoration_date_raw,raw_restoration_time=row.restoration_time_raw,circuit_name=row.circuit_name,county=row.county,circuit_identity_matches=0 if g is None else len(g),matched_circuit_ids='' if g is None else ';'.join(g.circuit_id.astype(str)),external_substations='' if g is None else ';'.join(sorted(set(g.sub_name))),direct_July92_ids='' if g is None else ';'.join(sorted(set(g.direct_id)-{''})),system_July92_ids='' if g is None else ';'.join(sorted(set(g.system_id)-{''})),deenergization_local=begin,all_clear_local=clear,restoration_local=finish,duration_hr=(finish-begin).total_seconds()/3600 if pd.notna(begin) and pd.notna(finish) else np.nan,all_clear_to_restoration_hr=(finish-clear).total_seconds()/3600 if pd.notna(clear) and pd.notna(finish) else np.nan,reported_over24h_reason=' | '.join(reasons.get(key,[])),spatial_status='Circuit name match to2026 geometry; not proof of2025 affected polygon',tract_outage_key='NOT_PRESENT'))
    q=pd.DataFrame(out);save(q,'CPUC_CIRCUIT_TIME_LINKS.csv')
    for wb,g in q.groupby('workbook'):
        summaries.append(dict(scope=wb,rows=len(g),customer_key_unique_matches=int((g.customer_table_matches==1).sum()),parseable_actual_duration_rows=int(g.duration_hr.notna().sum()),exact_unique_circuit_geometry_links=int((g.circuit_identity_matches==1).sum()),ambiguous_links=int((g.circuit_identity_matches>1).sum()),no_links=int((g.circuit_identity_matches==0).sum()),has_direct_July92=int(g.direct_July92_ids.ne('').sum()),has_named_system_July92=int(g.system_July92_ids.ne('').sum()),over24h_reason_rows=int(g.reported_over24h_reason.ne('').sum()),complete_circuit_to_observed_tract_links=0))
    # Compare provider event IDs literally after whitespace/case normalization, not inferred dates.
    a=read(N/'CPUC_circuit_events_public_-sce_psdr_4-1-2024.csv')
    b=read(N/'CPUC_tract_events_sce_2023amended_postsr2b_1-22-2025.csv',dtype={'GEOID_11':str})
    key=lambda x:re.sub(r'\s+',' ',str(x).strip()).upper()
    a['event_key']=a.event.map(key);b['event_key']=b.EVENTID.map(key)
    event=[]
    for k,g in a.groupby('event_key'):
        tr=b[b.event_key==k]
        event.append(dict(event_key=k,unique_reported_circuit_tract_link=bool(len(g)==1 and len(tr)==1 and g.customers.sum()==tr.all_accounts.sum()),unique_tract_id=tr.GEOID_11.iloc[0] if len(g)==1 and len(tr)==1 else '',named_circuit_rows=len(g),official_tract_rows=len(tr),unique_official_tracts=tr.GEOID_11.nunique(),tracts_in_July_domain=int(tr.GEOID_11.isin(tids).sum()),circuit_names=';'.join(sorted(set(g.circuit_segment_name.dropna()))),observed_customers_circuit_sum=float(g.customers.sum()),observed_customers_tract_sum=float(tr.all_accounts.sum()) if len(tr) else np.nan,link_meaning=('SAME PROVIDER EVENT ID; circuit-to-individual-tract allocation NOT identified' if len(tr) else 'NO EXACT PROVIDER EVENT ID MATCH; no circuit-to-tract linkage inferred')))
    save(pd.DataFrame(event),'CPUC_EVENT_KEY_COVERAGE.csv')
    # GIS may aggregate by month/tract; inspect real shared keys but do not create event assignments.
    gis=read(N/'CPUC_2025_SCE_POSTSR2A_3_2_2026.csv')
    gis['GEOID_11']=gis.Track.map(lambda x:str(int(float(x))).zfill(11) if pd.notna(x) else '')
    tr25=read(N/'CPUC_tract_events_sce_postsr2b_3-2-2026.csv',dtype={'GEOID_11':str})
    summaries.append(dict(scope='2025_POSTSR2A_vs_2B',rows=len(gis),shared_unique_tract_identifiers=len(set(gis.GEOID_11)&set(tr25.GEOID_11)),gis_rows_in_July_domain=int(gis.GEOID_11.isin(tids).sum()),complete_circuit_to_observed_tract_links=0,limitation='2A has YYYYMM/Track aggregate, not event/circuit ID; shared GEOID alone cannot attribute a circuit event'))
    save(pd.DataFrame(summaries),'CPUC_LINKAGE_SUMMARY.csv')
    print('CPUC',json.dumps(summaries),flush=True)

def capacity():
    lookup=unique_lookup(stations.reset_index().query("Owner=='SCE'"),'NAME','ID')
    hist=read(N/'SCE_ICA_Tables_2_Historical_Substation_Load_Profile.csv')
    hist['site_key']=hist.substation.map(norm)
    hist['direct_id']=[getone(k,lookup) for k in hist.site_key]
    h=hist[hist.direct_id.ne('')].copy()
    # Provider redaction sentinel remains in raw; analytical numeric summary excludes it explicitly.
    h['valid_max_load_mw']=pd.to_numeric(h.max_load_mw,errors='coerce').where(pd.to_numeric(h.max_load_mw,errors='coerce')>=0)
    hs=h.groupby(['direct_id','substation','substation_voltage','year'],dropna=False).agg(rows=('objectid','size'),observed_numeric_rows=('valid_max_load_mw','count'),maximum_of_reported_hourly_envelopes_mw=('valid_max_load_mw','max')).reset_index()
    hs['interpretation']='Monthly hour-of-day envelope maximum, not reconstructed8760 coincident station total; voltage banks kept separate'
    save(hs,'SCE_REPRESENTED_HISTORICAL_LOAD.csv')
    p=read(N/'SCE_GNA_Layer_5_Substation_Level_Planning_Assumptions.csv')
    p['direct_July92_id']=[getone(site(x),lookup) for x in p.substation_name]
    p=p[p.direct_July92_id.ne('')].copy()
    for c in ['cumulative_demand','fac_load_limit','facility_loading','subst_capacity']:p[c]=pd.to_numeric(p[c],errors='coerce')
    good=(p.cumulative_demand>=0)&(p.fac_load_limit>0)&(p.facility_loading>=0)
    p['screenable_same_row_ratio']=good
    p['planning_demand_to_limit_ratio']=np.where(good,p.cumulative_demand/p.fac_load_limit,np.nan)
    p['ratio_vs_reported_loading_error_pp']=np.where(good,100*p.planning_demand_to_limit_ratio-p.facility_loading,np.nan)
    p['demand_above_same_year_limit']=pd.Series(np.where(good,p.planning_demand_to_limit_ratio>1,None),index=p.index,dtype='object')
    p['remaining_margin_field_identity_error']=np.where(good,(p.fac_load_limit-p.cumulative_demand)-p.subst_capacity,np.nan)
    p['capacity_scope']='Named downstream voltage facility; not entire July transmission station; subst_capacity is treated as reported margin, not nameplate'
    p['unit_boundary']='Only dimensionless same-row loading screen; native absolute power base/unit not independently established from retained table dictionary. No historic-MW/forecast-limit division.'
    save(p,'SCE_LOCAL_PLANNING_SCREEN.csv')
    screen=[]
    for year,g in p.groupby('year_value'):
        valid=g[g.screenable_same_row_ratio]
        screen.append(dict(year=year,represented_named_facilities=g.facility.nunique(),rows=len(g),numeric_screen_rows=len(valid),redacted_or_invalid_rows=len(g)-len(valid),above_limit_rows=int((valid.planning_demand_to_limit_ratio>1).sum()),max_ratio=valid.planning_demand_to_limit_ratio.max(),max_loading_equation_error_pp=valid.ratio_vs_reported_loading_error_pp.abs().max(),max_margin_identity_error=valid.remaining_margin_field_identity_error.abs().max()))
    save(pd.DataFrame(screen),'SCE_LOCAL_SCREEN_SUMMARY.csv')
    # ICA's remaining integration capacity cannot be interpreted as station/edge thermal rating.
    meta=read(N/'SCE_ICA_Layer_18_Substations.csv');meta['direct_July92_id']=[getone(norm(x),lookup) for x in meta.sub_name]
    meta=meta[meta.direct_July92_id.ne('')]
    meta['use']='Named site context only; voltage bank and projected_load/redaction retained; max_remain_cap not a branch thermal limit'
    save(meta,'SCE_REPRESENTED_ICA_CAPACITY_CONTEXT.csv')
    print('SCREEN',pd.DataFrame(screen).to_string(index=False),flush=True)

if __name__=='__main__':
    load();benchmark();gate_diagnostics();cpuc_links();capacity()
