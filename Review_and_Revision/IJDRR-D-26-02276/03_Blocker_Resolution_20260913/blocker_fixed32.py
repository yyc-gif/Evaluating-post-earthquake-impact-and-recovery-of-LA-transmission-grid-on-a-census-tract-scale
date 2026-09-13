"""Fixed-sample blocker checks. No random sampling, GA calls, or crew-level sweep.
The archived 32x4 pilot and submission-era sources are read-only.
A is the frozen positive-conditioned candidate; B is the legacy clipped-normal
candidate using the SAME stored uniforms. B is not promoted as a correction.
Mapping alternatives reuse A's saved station trajectories without re-dispatch.
"""
from pathlib import Path
import os, sys, importlib.util, hashlib, json, argparse
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import t as student_t
from threadpoolctl import threadpool_limits

OUT = Path(__file__).resolve().parent
ROOT = next(p for p in OUT.parents if (p / "C257H_Project_Main.py").is_file())
FROZEN = OUT.parent / "02_Paired_Pilot_20260912"
def path(p):
    p = Path(p).resolve()
    s = str(p)
    return ("\\\\?\\" + s) if os.name == "nt" and not s.startswith("\\\\?\\") else s

sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("frozen_pilot", path(FROZEN / "paired_pilot.py"))
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
# The archived driver retains its historical external-directory assumptions.
# Only its event kernel is reused; load_inputs(), pilot(), and physical_draw() are never called.
N = 32
POLICIES = list(pilot.POLICIES)
METRICS = ["makespan_h", "population_T50_h", "population_T80_h", "population_T90_h",
           "population_deficit_proxy_h", "hospital_tract_deficit_proxy_h"]
KEY_IDS = ["300232","302187","306450","301517","303899","303099","307693",
           "305984","306489","303169","301105","305885","303344","309703","302923"]

def read(p, **kwargs):
    return pd.read_csv(path(p), **kwargs)

def sha(p):
    return hashlib.sha256(Path(path(p)).read_bytes()).hexdigest()

def mean_ci(values):
    v = np.asarray(values, float)
    assert len(v) == N and np.isfinite(v).all()
    mean = float(v.mean()); sd = float(v.std(ddof=1))
    h = float(student_t.ppf(.975, N-1)*sd/np.sqrt(N))
    return dict(mean=mean, sd=sd, ci95_low=mean-h, ci95_high=mean+h,
                negative_count=int((v < -1e-9).sum()), positive_count=int((v > 1e-9).sum()))

def inputs():
    z = dict(np.load(path(FROZEN/"PAIRED_EVENT_DATA.npz"), allow_pickle=False))
    meta = json.loads(str(z["metadata_json"]))
    # Git may checkout LF or CRLF. Accept only that byte-level difference;
    # these canonical hashes pin the exact source text used by the frozen run.
    source_text = Path(path(ROOT/"C257H_Project_Main.py")).read_bytes().replace(b"\r\n", b"\n")
    kernel_text = Path(path(FROZEN/"paired_pilot.py")).read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(source_text).hexdigest() == "4a73c21982a56e46f7808a7434f67f9888b25730c79acc822247489f2eebc9c5"
    assert hashlib.sha256(kernel_text).hexdigest() == meta["revision_driver_sha256"]
    assert np.array_equal(z["realization_ids"], np.arange(N))
    ids = z["station_ids"].astype(str); lookup = {s:i for i,s in enumerate(ids)}
    edges = read(ROOT/"Data/substation_graph_CEC_edges_expanded.csv",dtype={"u":str,"v":str})
    graph = nx.Graph(); graph.add_nodes_from(range(len(ids)))
    graph.add_edges_from((lookup[a],lookup[b]) for a,b in zip(edges.u,edges.v))
    assert graph.number_of_nodes()==92 and graph.number_of_edges()==318
    hospital = read(ROOT/"Data/hospital_with_tract_expanded.csv")
    hids = set(hospital.GEOID.astype(str).str.replace(r"\.0$", "", regex=True).str.lstrip("0"))
    hosp = np.array([s.lstrip("0") in hids for s in z["tract_ids"].astype(str)],float)
    bm = read(ROOT/"Stage 4 Output_expanded/travel_base_to_task.csv",index_col=0)
    tm = read(ROOT/"Stage 4 Output_expanded/travel_task_to_task.csv",index_col=0)
    bm.index=bm.index.astype(str); bm.columns=bm.columns.astype(str)
    tm.index=tm.index.astype(str); tm.columns=tm.columns.astype(str)
    bm=bm.reindex(columns=ids); tm=tm.reindex(index=ids,columns=ids)
    origins=read(ROOT/"Data/stage45_C57_expanded_crew_origins.csv").travel_matrix_origin_key.astype(str)
    origin_idx=np.array([list(bm.index).index(s) for s in origins])
    assert len(origin_idx)==57
    gantt=read(ROOT/"Stage 4 Output_expanded/Gantt_Data_Stage4.csv",dtype={"Substation_ID":str})
    orders=[]
    for name in POLICIES:
        if name=="Hospital-first":
            q=gantt[gantt.Stage=="Stage4_2pc50_hospital-first"]; column="Substation_ID"
        elif name=="Population-impact":
            q=gantt[gantt.Stage=="Stage4_2pc50_impact-first"]; column="Substation_ID"
        else:
            tag="Efficiency" if name=="GA-Efficiency" else "HospFirst"
            q=read(ROOT/f"Stage 5 Output_expanded/GA_Schedule_2pc50_{tag}.csv",dtype={"substation_id":str})
            column="substation_id"
        order=np.array([lookup[s] for s in q[column].astype(str)])
        assert len(order)==92 and len(np.unique(order))==92
        orders.append(order)
    x=dict(ids=ids,tids=z["tract_ids"].astype(str),W=z["W"],pop=z["population"],hosp=hosp,
           graph=graph,sources=z["source_flags"],base=bm.to_numpy(),travel=tm.to_numpy(),
           origin_idx=origin_idx,orders=orders)
    return z,x

def trajectory_metrics(x, times, eff, W):
    valid=np.isfinite(times); times=times[valid]; eff=eff[valid]
    service=eff@W.T; dt=np.diff(times)
    b=(1-service[:-1]).T@dt
    pw=x["pop"]/x["pop"].sum(); hw=x["hosp"]/x["hosp"].sum()
    curve=service@pw; hc=service@hw
    cross=lambda c,q:float(times[np.flatnonzero(c >= q-1e-12)[0]])
    tt=times[np.argmax(service >= .8-1e-12,axis=0)]
    metrics={f"population_T{q}_h":cross(curve,q/100) for q in [50,80,90]}
    metrics.update(population_deficit_proxy_h=float(pw@b),hospital_tract_deficit_proxy_h=float(hw@b),
                   hospital_tract_T80_h=cross(hc,.8),population_AUC=float(1-pw@b/480))
    return metrics,b,tt

def community(b,pop,groups):
    # b axes: realization, strategy, tract; all delta signs H-first minus GA-Efficiency.
    delta=b[:,0]-b[:,1]; md=delta.mean(0); pw=pop/pop.sum()
    result=dict(mean_effect_improving_tracts=int((md < -1e-9).sum()),
                mean_effect_worsening_tracts=int((md > 1e-9).sum()),
                mean_effect_improving_population=float(pop[md < -1e-9].sum()),
                mean_effect_worsening_population=float(pop[md > 1e-9].sum()),
                realization_improving_population=mean_ci((delta < -1e-9)@pop),
                realization_worsening_population=mean_ci((delta > 1e-9)@pop),
                net_population_B_H_minus_GA=mean_ci(delta@pw),
                gross_improvement_h=float(np.mean(np.maximum(-delta,0)@pw)),
                gross_worsening_h=float(np.mean(np.maximum(delta,0)@pw)),groups={})
    for group in ["Q1","Q2","Q3","Q4"]:
        mask=groups==group; w=pop[mask]/pop[mask].sum()
        result["groups"][group]=mean_ci(delta[:,mask]@w)
    return result

def alternative_mappings(x):
    import geopandas as gpd
    from scipy.spatial.distance import cdist
    nodes=read(ROOT/"Data/working_area_substations_with_fragility.csv",dtype={"ID":str}).set_index("ID").loc[x["ids"]]
    eligible=nodes.TYPE.eq("SUBSTATION") & nodes.STATUS.eq("IN SERVICE") & (nodes.voltage_for_fragility>=34.5)
    assert eligible.sum()==84 and len(eligible)==92
    tracts=gpd.read_file(ROOT/"Data/LA_Tracts_With_Population.shp").to_crs(3310)
    idcol=next(k for k in ["GEOID","GEOID20","tract_id"] if k in tracts)
    tracts[idcol]=tracts[idcol].astype(str).str.replace(r"\.0$","",regex=True).str.lstrip("0")
    tracts=tracts.set_index(idcol).loc[np.char.lstrip(x["tids"],"0")]
    cen=tracts.geometry.centroid
    stations=gpd.GeoSeries(gpd.points_from_xy(nodes.LONGITUDE,nodes.LATITUDE),crs=4326).to_crs(3310)
    dist=cdist(np.c_[cen.x,cen.y],np.c_[stations.x,stations.y])
    nearest=np.argmin(np.where(eligible.to_numpy()[None,:],dist,np.inf),axis=1)
    w1=np.zeros_like(x["W"]);w1[np.arange(len(nearest)),nearest]=1
    # No new k, cutoff, utility assumption, or arbitrary decay exponent.
    # Same accepted candidates as original W; replace network distance by geographic distance.
    weights=np.where(x["W"]>0,1/np.maximum(dist,1e-3)**2,0)
    w2=weights/weights.sum(1,keepdims=True)
    assert np.allclose(w1.sum(1),1) and np.allclose(w2.sum(1),1)
    return {"nearest_documented_in_service_84":w1,"geographic_IDW_existing_candidates":w2},dist

def run():
    z,x=inputs()
    maps,dist=alternative_mappings(x)  # Validate mapping inputs before any fixed-sample execution.
    frozen_files=['paired_pilot.py','PAIRED_EVENT_DATA.npz','PAIRED_PILOT_RESULTS.csv',
                  'TRACT_DISTRIBUTIONAL_EFFECTS.csv','CORE_REVISION_FINDINGS.md','CORE_DIAGNOSTIC.png']
    original_hashes={name:sha(FROZEN/name) for name in frozen_files}
    frozen=read(FROZEN/"PAIRED_PILOT_RESULTS.csv").set_index(["realization_id","strategy"])
    tracts=read(FROZEN/"TRACT_DISTRIBUTIONAL_EFFECTS.csv",dtype={"tract_id":str})
    groups=tracts.SVI_quartile.to_numpy()
    ds=z["damage_state"];dur=z["repair_duration_h"];raw=z["duration_unconditioned_h"]
    variants={"A_positive_conditioned":dur,"B_legacy_clipped_same_uniform":np.maximum(raw,0)}
    store={"realization_ids":z["realization_ids"],"station_ids":x["ids"],"tract_ids":x["tids"],
           "strategy_names":np.array(POLICIES),"damage_state":ds,"duration_uniform":z["duration_uniform"],
           "W_baseline":x["W"],"population":x["pop"],"SVI_quartile":groups.astype(str)}
    records=[]; analyses={}; comparisons=[]; bsets={}
    for variant,duration in variants.items():
        rows=[]; bs=[]; ts=[]; starts=[]; finishes=[]; crews=[]; predecessors=[]; moves=[]; event_times=[]; event_eff=[]
        for r in range(N):
            rb=[];rt=[]; rs=[];rf=[];rc=[];rp=[];rm=[];ret=[];ree=[]
            sample=hashlib.sha256(ds[r].tobytes()+duration[r].tobytes()).hexdigest()[:16]
            for j,strategy in enumerate(POLICIES):
                start,finish,crew,prev,move=pilot.execute_queue(x["orders"][j],ds[r]>0,duration[r],
                                                             x["base"],x["travel"],x["origin_idx"])
                ans=pilot.evaluate_events(x,ds[r],finish)
                m=ans["metrics"]; old=frozen.loc[(r,strategy)]
                row=dict(implementation=variant,realization_id=r,strategy=strategy,scenario="2pc50",crews=57,
                         sample_key=sample,sample_uniform_source="frozen_32",**m)
                for metric in METRICS:
                    row["change_"+metric+"_vs_frozen"]=float(m[metric]-old[metric])
                rows.append(row);records.append(row)
                rb.append(ans["tract_b"]);rt.append(ans["tract_times"]);rs.append(start);rf.append(finish)
                rc.append(crew);rp.append(prev);rm.append(move)
                tpad=np.full(94,np.nan);epad=np.full((94,92),np.nan)
                tpad[:len(ans["times"])]=ans["times"];epad[:len(ans["eff"])]=ans["eff"]
                ret.append(tpad);ree.append(epad)
                if variant.startswith("A_"):
                    np.testing.assert_allclose(finish,z["finishes"][r,j],atol=1e-11,rtol=0)
                    np.testing.assert_allclose(ans["tract_b"],z["tract_b"][r,j],atol=1e-10,rtol=0)
                    for metric in METRICS:assert abs(m[metric]-old[metric])<1e-10
            for dest,v in [(bs,rb),(ts,rt),(starts,rs),(finishes,rf),(crews,rc),(predecessors,rp),(moves,rm),
                           (event_times,ret),(event_eff,ree)]:dest.append(v)
        b=np.array(bs);bsets[variant]=b
        for key,value in [("duration",duration),("tract_b",b),("tract_times",ts),("starts",starts),("finishes",finishes),
                          ("crews",crews),("previous",predecessors),("travel_used",moves),
                          ("event_times_h",event_times),("event_station_service",event_eff)]:
            store[variant+"__"+key]=np.array(value)
        frame=pd.DataFrame(rows)
        analyses[variant]={"community":community(b,x["pop"],groups),"strategy_difference_H_minus_GA":{}}
        for metric in METRICS:
            p=frame.pivot(index="realization_id",columns="strategy",values=metric)
            before=frozen[metric].unstack()["Hospital-first"]-frozen[metric].unstack()["GA-Efficiency"]
            after=p["Hospital-first"]-p["GA-Efficiency"]; change=after-before
            analyses[variant]["strategy_difference_H_minus_GA"][metric]={"before":mean_ci(before),"after":mean_ci(after),"change":mean_ci(change)}
            for r in range(N):
                comparisons.append(dict(implementation=variant,realization_id=r,metric=metric,
                    comparison="Hospital-first_minus_GA-Efficiency",before=float(before.iloc[r]),after=float(after.iloc[r]),
                    paired_change=float(change.iloc[r]),direction_same=bool(np.sign(before.iloc[r])==np.sign(after.iloc[r]))))
        # Quantify propagation to dispatch and major task completion events.
        changed=np.abs(np.array(finishes)-z["finishes"])
        order_changes=0
        for r in range(N):
            for j in range(4):
                before_order=np.lexsort((z["crews"][r,j],z["starts"][r,j]-z["travel_used"][r,j]))
                after_order=np.lexsort((np.array(crews)[r,j],np.array(starts)[r,j]-np.array(moves)[r,j]))
                order_changes+=not np.array_equal(before_order,after_order)
        analyses[variant]["completion_changes"]={"max_abs_h":float(changed.max()),
            "mean_abs_h":float(changed.mean()),"changed_asset_strategy_events":int((changed>1e-9).sum()),
            "priority_list_changed":False,"dispatch_order_changed_runs":int(order_changes),
            "crew_assignment_changed_tasks":int((np.array(crews)!=z["crews"]).sum()),"key_stations":[]}
        for sid in KEY_IDS:
            i=list(x["ids"]).index(sid)
            analyses[variant]["completion_changes"]["key_stations"].append(dict(id=sid,
                H_before_mean_h=float(z["finishes"][:,0,i].mean()),GA_before_mean_h=float(z["finishes"][:,1,i].mean()),
                H_after_mean_h=float(np.array(finishes)[:,0,i].mean()),GA_after_mean_h=float(np.array(finishes)[:,1,i].mean())))
        print("finished",variant,"same 32 IDs x 4 strategies",flush=True)
    neg=(ds>0)&(raw<0)
    negative_entries=[]
    for r,i in np.argwhere(neg):
        negative_entries.append(dict(realization_id=int(r),station_id=x["ids"][i],DS=int(ds[r,i]),
            raw_h=float(raw[r,i]),A_positive_h=float(dur[r,i]),B_clipped_h=0.,
            H_completion_A=float(z["finishes"][r,0,i]),H_completion_B=float(store["B_legacy_clipped_same_uniform__finishes"][r,0,i]),
            GA_completion_A=float(z["finishes"][r,1,i]),GA_completion_B=float(store["B_legacy_clipped_same_uniform__finishes"][r,1,i])))
    analyses["negative_draws"]={"actual_frozen_negatives":int((dur[ds>0]<0).sum()),"actual_frozen_zero_repairs":int((dur[ds>0]==0).sum()),
        "unconditioned_negative_count":int(neg.sum()),"unique_stations":int(neg.any(0).sum()),
        "unique_realizations":int(neg.any(1).sum()),"entries":negative_entries,
        "damaged_counts_by_DS":{str(k):int((ds==k).sum()) for k in range(1,5)}}
    maprecords=[]
    for label,W in maps.items():
        bs=[]; rows=[]
        for r in range(N):
            rb=[]
            for j,strategy in enumerate(POLICIES):
                m,b,tt=trajectory_metrics(x,z["event_times_h"][r,j],z["event_station_service"][r,j],W)
                row=dict(mapping=label,realization_id=r,strategy=strategy,**m)
                for metric in [k for k in METRICS if k!="makespan_h"]:
                    row["change_"+metric+"_vs_baseline_mapping"]=m[metric]-frozen.loc[(r,strategy),metric]
                row["makespan_h"]=frozen.loc[(r,strategy),"makespan_h"]
                rows.append(row);maprecords.append(row);rb.append(b)
            bs.append(rb)
        b=np.array(bs);frame=pd.DataFrame(rows)
        analysis={"community":community(b,x["pop"],groups),"strategy_difference_H_minus_GA":{}}
        for metric in [k for k in METRICS if k!="makespan_h"]:
            p=frame.pivot(index="realization_id",columns="strategy",values=metric)
            analysis["strategy_difference_H_minus_GA"][metric]=mean_ci(p["Hospital-first"]-p["GA-Efficiency"])
        analyses[label]=analysis;store[label+"__W"]=W;store[label+"__tract_b"]=b
        print("mapping postprocess",label,"same saved station trajectories",flush=True)
        t80=analysis['strategy_difference_H_minus_GA']['population_T80_h']
        if t80['ci95_high']>=0 or abs(t80['mean'])<=0.37:
            analyses['mapping_stop_reason']='T80 direction lost or mean effect within prior 0.37 h near-tie scale; no further mapping cases.'
            break
    analyses["frozen_hashes"]=original_hashes
    analyses["driver_sha256"]=sha(__file__)
    analyses["semantics"]="repair-task completion is used as the modeled functionality-restoration event"
    store["analysis_json"]=np.array(json.dumps(analyses,ensure_ascii=False))
    pd.DataFrame(records).to_csv(path(OUT/"CORRECTED_PAIRED_RESULTS.csv"),index=False)
    pd.DataFrame(comparisons).to_csv(path(OUT/"BEFORE_AFTER_COMPARISON.csv"),index=False)
    pd.DataFrame(maprecords).to_csv(path(OUT/"MAPPING_SENSITIVITY_SUMMARY.csv"),index=False)
    np.savez_compressed(path(OUT/"BLOCKER_PAIRED_EVENT_DATA.npz"),**store)
    for name in frozen_files:
        assert sha(FROZEN/name)==original_hashes[name]
    print(json.dumps({k:v.get('strategy_difference_H_minus_GA', {}) for k,v in analyses.items()
                      if isinstance(v,dict) and 'strategy_difference_H_minus_GA' in v},ensure_ascii=False,indent=2))

def summarize_saved():
    """Only postprocess saved results; no dispatch, gate evaluation, or random draw."""
    data=dict(np.load(path(OUT/'BLOCKER_PAIRED_EVENT_DATA.npz'),allow_pickle=False))
    a=json.loads(str(data['analysis_json'])); pop=data['population']
    base=data['A_positive_conditioned__tract_b']; d0=base[:,0]-base[:,1]; m0=d0.mean(0)
    table=read(OUT/'CORRECTED_PAIRED_RESULTS.csv')
    table['implementation_status']='candidate_only_source_unresolved'
    table['duration_coupling']=np.where(table.implementation.str.startswith('A_'),
        'exact_frozen_duration_values','same_frozen_uniform_quantiles_different_durations')
    table.to_csv(path(OUT/'CORRECTED_PAIRED_RESULTS.csv'),index=False)
    comparisons=read(OUT/'BEFORE_AFTER_COMPARISON.csv')
    comparisons=comparisons[comparisons.metric.isin(METRICS)]
    extra=[]; a['distributional_changes']={}
    for tag in ['A_positive_conditioned','B_legacy_clipped_same_uniform',
                'nearest_documented_in_service_84','geographic_IDW_existing_candidates']:
        key=tag+'__tract_b'
        if key not in data: continue
        b=data[key]; d=b[:,0]-b[:,1]; md=d.mean(0)
        a['distributional_changes'][tag]=dict(
            mean_effect_sign_changed_tracts=int((m0*md<0).sum()),
            mean_effect_sign_changed_population=float(pop[m0*md<0].sum()),
            max_abs_mean_tract_effect_change_h=float(np.max(abs(md-m0))),
            population_weighted_abs_mean_effect_change_h=float(abs(md-m0)@pop/pop.sum()))
        for metric,before,after in [
            ('realization_worsening_population',(d0>1e-9)@pop,(d>1e-9)@pop),
            ('realization_improving_population',(d0<-1e-9)@pop,(d<-1e-9)@pop),
            ('realization_worsening_tract_count',(d0>1e-9).sum(1),(d>1e-9).sum(1))]:
            a['distributional_changes'][tag][metric+'_change']=mean_ci(after-before)
            for r in range(N):extra.append(dict(implementation=tag,realization_id=r,metric=metric,
                comparison='classification_by_realization_specific_H_minus_GA_tract_B',
                before=float(before[r]),after=float(after[r]),paired_change=float(after[r]-before[r]),direction_same=''))
        for metric,before,after in [
            ('mean_effect_improving_population',pop[m0<-1e-9].sum(),pop[md<-1e-9].sum()),
            ('mean_effect_worsening_population',pop[m0>1e-9].sum(),pop[md>1e-9].sum())]:
            extra.append(dict(implementation=tag,realization_id='aggregate_tract_mean',metric=metric,
                comparison='classification_by_mean_H_minus_GA_tract_B',before=float(before),after=float(after),
                paired_change=float(after-before),direction_same=''))
    pd.concat([comparisons,pd.DataFrame(extra)],ignore_index=True).to_csv(path(OUT/'BEFORE_AFTER_COMPARISON.csv'),index=False)
    a['postprocess_driver_sha256']=sha(__file__)
    data['analysis_json']=np.array(json.dumps(a,ensure_ascii=False))
    np.savez_compressed(path(OUT/'BLOCKER_PAIRED_EVENT_DATA.npz'),**data)
    print('Saved-only comparison enriched; no simulation performed.')

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-fixed-32",action="store_true")
    parser.add_argument("--summarize-saved",action="store_true")
    args=parser.parse_args()
    if args.run_fixed_32==args.summarize_saved:parser.error('Select exactly one explicit operation.')
    with threadpool_limits(limits=1):
        if args.run_fixed_32:
            run()
            summarize_saved()
        else:
            summarize_saved()
