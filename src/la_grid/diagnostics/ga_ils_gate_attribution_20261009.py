"""Inspect the nonlinear source-gate mechanism behind ILS outlier 15.

Event-complete trajectories for both existing priority sequences on the SAME
previously saved sample. Decomposes L_self, L_threshold, L_source and L_total
exactly; station-level differences are descriptive contributions, not isolated
counterfactual intervention effects. No new model or physical samples.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_search_budget_sensitivity import per_sample
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_realization_scheduling import evaluate_completion_step_functionality
from la_grid.revision.r1_source_gate import evaluate_source_gate

OUT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"
ILS=OUT/"ILS_BEST_SEED304_PLANNING_CANDIDATE.json"
GA=REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json"
COMPONENTS=("L_self","L_threshold","L_source","L_total")
SAMPLES=(15,55,13,58,50)

def analyze(k,decoder,context,origin_keys,r,a,b):
    sequences={"ILS":a["sequence"],"FrozenGA":b["sequence"]}
    schedule={}
    times=[0.,480.]
    for label,seq in sequences.items():
        finish,*_=decoder.decode(order=decoder.order(seq),
             damage=k.damage[r],duration=k.duration[r],origins=origin_keys)
        schedule[label]=finish
        times.extend(float(q) for q in finish if np.isfinite(q) and 0<q<480)
    clock=np.unique(np.array(times,np.float64))
    assert clock[0]==0 and clock[-1]==480
    widths=np.diff(clock)
    per_strategy={}
    mass=k.station_mass/k.total_mass
    for label,seq in sequences.items():
        raw=evaluate_completion_step_functionality(
            damage_state=pd.Series(k.damage[r],index=k.ids),
            completion_time_hr=pd.Series(schedule[label],index=k.ids),
            time_hr=clock)
        trace=evaluate_source_gate(raw,context["graph"],context["sources"],threshold=.5)
        fields={name:getattr(trace,name).loc[:,list(k.ids)].to_numpy(float) for name in COMPONENTS}
        effective=trace.e.loc[:,list(k.ids)].to_numpy(float)
        values={}
        for name,array in fields.items():
            weighted=array[:-1]@mass
            values[name]=float(np.sum(weighted*widths))
        values["loss_norm_from_e"]=float(np.sum(((1-effective[:-1])@mass)*widths))
        assert abs(values["loss_norm_from_e"]-values["L_total"])<1e-9
        expected=float(per_sample(k,seq)[r])
        assert abs(values["L_total"]-expected)<1e-8,(r,label,values["L_total"],expected)
        per_strategy[label]=dict(totals=values,fields=fields,e=effective)
    signed={}
    for comp in COMPONENTS:
        signed[comp]=per_strategy["ILS"]["totals"][comp]-per_strategy["FrozenGA"]["totals"][comp]
    assert abs(sum(signed[q] for q in COMPONENTS[:3])-signed["L_total"])<1e-8
    effective_ils=per_strategy["ILS"]["e"][:-1]
    effective_ga=per_strategy["FrozenGA"]["e"][:-1]
    e_diff=effective_ils-effective_ga
    interval_loss_change=(effective_ga-effective_ils)@mass*widths
    assert abs(interval_loss_change.sum()-signed["L_total"])<1e-8
    station_loss_deltas=(-e_diff*widths[:,None]).sum(axis=0)*mass
    assert abs(np.sum(station_loss_deltas)-signed["L_total"])<1e-8
    intervals=[dict(start_hr=float(clock[i]),end_hr=float(clock[i+1]),
        loss_change_contribution_hr=float(v),
        mean_effective_service_ILS=float(np.dot(effective_ils[i],mass)),
        mean_effective_service_GA=float(np.dot(effective_ga[i],mass)))
        for i,v in enumerate(interval_loss_change)]
    stations=[dict(station=k.ids[i],mass_weight=float(k.station_mass[i]),
        service_loss_change_contribution_hr=float(station_loss_deltas[i]),
        recovered_service_improvement_hr=float(-station_loss_deltas[i]))
        for i in range(92)]
    return dict(realization=r,
        loss_ils_hr=per_strategy["ILS"]["totals"]["L_total"],
        loss_frozen_ga_hr=per_strategy["FrozenGA"]["totals"]["L_total"],
        loss_delta_ils_minus_ga_hr=signed["L_total"],
        component_changes_hr=signed,
        component_integrals_by_strategy={label:entry["totals"] for label,entry in per_strategy.items()},
        event_time_count=len(clock),
        largest_beneficial_intervals=sorted(intervals,key=lambda z:z["loss_change_contribution_hr"])[:15],
        largest_harmful_intervals=sorted(intervals,key=lambda z:z["loss_change_contribution_hr"],reverse=True)[:15],
        largest_beneficial_station_contributions=sorted(stations,key=lambda z:z["service_loss_change_contribution_hr"])[:20],
        largest_harmful_station_contributions=sorted(stations,key=lambda z:z["service_loss_change_contribution_hr"],reverse=True)[:20])

def main():
    k,inc,quality,_=load()
    a=json.loads(ILS.read_text());b=json.loads(GA.read_text())
    context,decoder,hashes=execution_context(k.ids)
    origins=decoder.origins(context["origins"])
    rows=[analyze(k,decoder,context,origins,r,a,b) for r in SAMPLES]
    rec=dict(status="INDEPENDENT_EVENT_AND_GATE_COMPONENT_PARITY_PASS",
       no_new_physical_realizations=True,
       no_revised_optimization_objective=True,
       no_formal_replacement=True,
       kernel_and_model_unchanged=True,
       candidate_ils_sha256=a["sequence_sha256"],
       frozen_ga_sha256=b["sequence_sha256"],
       sample_ids=list(SAMPLES),results=rows)
    out=OUT/"ILS_EXACT_GATE_ATTRIBUTION.json"
    out.write_text(json.dumps(rec,indent=2)+"\n",encoding="utf-8")
    print("GATE_INFLUENCE_RESULT",json.dumps([
        dict(realization=q["realization"],total=q["loss_delta_ils_minus_ga_hr"],
        components=q["component_changes_hr"],
        top_interval=q["largest_beneficial_intervals"][0],
        top_station=q["largest_beneficial_station_contributions"][0])
        for q in rows]),flush=True)

if __name__=="__main__":main()
