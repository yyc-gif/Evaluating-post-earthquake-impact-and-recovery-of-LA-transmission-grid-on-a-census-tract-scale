"""Explain a selected ILS-vs-GA planning loss outlier via exact scheduler outputs.

Use only frozen 64 planning states, original formal decoder, unchanged kernel.
Attribution is descriptive of schedule differences, not a single-station causal
intervention, and never substitutes a new objective or physical validation.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_search_budget_sensitivity import per_sample
from la_grid.revision.r1_equity_amendment_execute import execution_context

OUT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"
ILS=OUT/"ILS_BEST_SEED304_PLANNING_CANDIDATE.json"
GA=REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json"

def main():
    a=json.loads(ILS.read_text());b=json.loads(GA.read_text())
    kernel,inc,quality,_=load()
    context,decoder,_=execution_context(kernel.ids)
    origins=decoder.origins(context["origins"])
    scores={name:per_sample(kernel,seq) for name,seq in
        (("ils",a["sequence"]),("ga",b["sequence"]))}
    loss=scores["ils"]-scores["ga"]
    rows=[]
    extrema=[]
    for r in range(64):
        schedule={}
        for name,record in (("ils",a),("ga",b)):
            order=decoder.order(record["sequence"])
            values=decoder.decode(
                order=order,damage=kernel.damage[r],
                duration=kernel.duration[r],origins=origins)
            finish,arrival,travel,crew,previous,dispatch,*rest=values
            schedule[name]=dict(finish=finish,arrival=arrival,travel=travel,
                crew=crew,previous=previous,dispatch=dispatch)
        s=schedule["ils"];t=schedule["ga"];valid=kernel.damage[r]>0
        count=int(valid.sum())
        delta=s["finish"][valid]-t["finish"][valid]
        if len(delta):
            changed=int(np.count_nonzero(abs(delta)>1e-9))
            improved=int(np.count_nonzero(delta< -1e-9))
            worsened=int(np.count_nonzero(delta>1e-9))
            maxtime=float(np.max(np.abs(delta)))
            avg=float(np.mean(delta))
            pweights=kernel.station_mass[valid]
            wsum=float(np.sum(delta*pweights)/np.sum(pweights))
            sa=float(np.sum(s["travel"][valid]))
            sb=float(np.sum(t["travel"][valid]))
        else:
            changed=improved=worsened=0;maxtime=avg=wsum=sa=sb=0
        rows.append(dict(realization=r,loss_ils_hr=float(scores["ils"][r]),
            loss_ga_hr=float(scores["ga"][r]),loss_difference_hr=float(loss[r]),
            damaged_station_count=count,changed_completion_count=changed,
            earlier_ils_completions=improved,later_ils_completions=worsened,
            max_absolute_completion_difference_hr=maxtime,
            mean_completion_difference_hr=avg,
            population_mass_weighted_mean_completion_difference_hr=wsum,
            total_directed_travel_ils_hr=sa,total_directed_travel_ga_hr=sb,
            travel_difference_hr=sa-sb))
        if r in (15,55,13,58,50):
            idx=np.flatnonzero(valid)
            details=[]
            for i in idx:
                details.append(dict(station=kernel.ids[i],damage_state=int(kernel.damage[r,i]),
                    mass_weight=float(kernel.station_mass[i]),duration_hr=float(kernel.duration[r,i]),
                    ils_finish_hr=float(s["finish"][i]),ga_finish_hr=float(t["finish"][i]),
                    finish_delta_hr=float(s["finish"][i]-t["finish"][i]),
                    ils_arrival_hr=float(s["arrival"][i]),ga_arrival_hr=float(t["arrival"][i]),
                    ils_crew_index=int(s["crew"][i]),ga_crew_index=int(t["crew"][i]),
                    ils_dispatch_rank=int(s["dispatch"][i]),ga_dispatch_rank=int(t["dispatch"][i]),
                    ils_travel_hr=float(s["travel"][i]),ga_travel_hr=float(t["travel"][i])))
            extrema.append(dict(realization=r,loss_delta_hr=float(loss[r]),
                station_details=details))
    assert abs(np.mean(scores["ils"])-a["loss_hr"])<1e-8
    assert abs(np.mean(scores["ga"])-b["planning_loss_hr"])<1e-8
    report=dict(status="COMPLETED",new_physical_samples=0,
        current_model_unchanged=True,
        total_planning_realizations=64,
        mean_ils_minus_ga=float(np.mean(loss)),
        median_ils_minus_ga=float(np.median(loss)),
        sample15_difference_hr=float(loss[15]),
        samples_worse_under_ils=int(np.sum(loss>1e-9)),
        samples_better_under_ils=int(np.sum(loss< -1e-9)),
        sample15_schedule=[x for x in rows if x["realization"]==15][0],
        all_samples=rows,
        selected_sample_details=extrema,
        provenance=dict(ils_sha256=a["sequence_sha256"],
                        ga_sha256=b["sequence_sha256"]))
    path=OUT/"ILS_SCHEDULE_INFLUENCE_MECHANISM.json"
    path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("MECHANISM_RESEARCH_RESULT",json.dumps(dict(
        sample15=report["sample15_schedule"],
        mean_delta=report["mean_ils_minus_ga"],
        worse_count=report["samples_worse_under_ils"],
        better_count=report["samples_better_under_ils"])),flush=True)

if __name__=="__main__":main()
