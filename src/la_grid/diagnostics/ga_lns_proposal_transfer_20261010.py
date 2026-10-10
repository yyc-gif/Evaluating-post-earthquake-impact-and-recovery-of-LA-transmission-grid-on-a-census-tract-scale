"""Test why event-route LNS is ineffective, without optimizing or new sampling.

For each of two frozen, common starting chromosomes, compare candidate quality
from *identical source-event banks* using route-targeted versus damaged-random
bundles. For each event, choose best of up to 36 repaired full permutations
against the SAME original 64-sample mean objective, without updating the parent.

Also score that best candidate in its event-generating single realization to
compare single-state source-event ranking to all-64 aggregate impact. Explicitly
diagnostic, not a new algorithm performance test or physical validation.
"""
from __future__ import annotations
import argparse
import json
import random
import time
from pathlib import Path

import numpy as np

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_schedule_aware_lns_20261010 import schedule_bank
from la_grid.diagnostics.ga_schedule_aware_lns_repair_v2_20261010 import repair_candidates
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_ga_exact_kernel import _one_sample
from la_grid.revision.r1_equity_amendment_execute import execution_context

OUT=REPO_ROOT/"results/diagnostics/ga_scheduling_aware_lns_20261010"/"proposal_transfer"
FROZEN=REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json"
METHODS=("lns_repair_route","lns_repair_random")
SEEDS=tuple(range(1000,1008))
EVENT_MACROS=64
SNAPSHOTS=4

def sample_score(kernel,seq,sample):
    order=np.asarray([kernel.index[x] for x in seq],dtype=np.int64)
    return float(_one_sample(order,kernel.damage[sample],kernel.duration[sample],
         kernel.origin_index,kernel.base,kernel.travel,
         kernel.neighbor_offset,kernel.neighbors,kernel.source_flag,
         kernel.station_mass,kernel.total_mass,kernel.horizon))

def test_start(kernel,inc,sequence,label,ctx,decoder,origins,seed):
    rng=random.Random(seed)
    baseline=-float(kernel.score(sequence))
    cache={tuple(sequence):baseline}
    baseline_sample_scores={}
    rows=[]
    banks_rebuilt=0
    active_bank=[]
    initial=time.perf_counter()
    for macro in range(EVENT_MACROS):
        if macro%16==0 or not active_bank:
            active_bank,chosen=schedule_bank(kernel,ctx,decoder,origins,sequence,rng)
            banks_rebuilt+=1
            if not active_bank: raise AssertionError("No route-reconnection events for frozen real samples")
        event=rng.choices(active_bank,weights=[max(1e-14,q["weighted_priority"]) for q in active_bank],k=1)[0]
        idx=int(event["sample"])
        if idx not in baseline_sample_scores:
            baseline_sample_scores[idx]=sample_score(kernel,sequence,idx)
        for mode in METHODS:
            r=random.Random(seed*100000+macro*3+1)
            candidates,k=repair_candidates(sequence,event,r,mode,kernel)
            assert len(candidates)>0 and k>=1
            best_loss=float("inf")
            best_seq=None
            for candidate in candidates:
                if candidate not in cache:cache[candidate]=-float(kernel.score(candidate))
                val=cache[candidate]
                if val<best_loss:
                    best_loss=val
                    best_seq=candidate
            assert best_seq is not None
            origin_value=sample_score(kernel,best_seq,idx)
            rows.append(dict(start=label,seed=seed,macro=macro,
                 selected_sample=idx,event_station=event["gateway"],
                 event_time_hr=float(event["time_hr"]),
                 event_gained_mass=float(event["dependency_mass"]),
                 reconnect_station_count=int(event["newly_reconnected"]),
                 route_bundle_size=k,method=mode,
                 candidate_count=len(candidates),
                 best_candidate_sha256=old.identity(best_seq),
                 baseline_64_loss_hr=baseline,
                 best_candidate_64_loss_hr=best_loss,
                 mean64_delta_hr=best_loss-baseline,
                 baseline_event_sample_loss_hr=baseline_sample_scores[idx],
                 best_candidate_event_sample_loss_hr=origin_value,
                 event_sample_delta_hr=origin_value-baseline_sample_scores[idx]))
    return dict(start=label,seed=seed,baseline_loss_hr=baseline,
                event_macro_count=EVENT_MACROS,event_bank_rebuilds=banks_rebuilt,
                distinct_candidate_scores=len(cache),
                wall_seconds=time.perf_counter()-initial,records=rows)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--seed",type=int,required=True)
    args=a.parse_args()
    assert args.seed in SEEDS
    kernel,inc,quality,_=load()
    f=json.loads(FROZEN.read_text(encoding="utf-8"))
    formal=tuple(f["sequence"])
    assert old.identity(formal)==f["sequence_sha256"]
    ctx,decoder,_=execution_context(kernel.ids)
    origins=decoder.origins(ctx["origins"])
    starts=(("prior_optimized_warm",tuple(quality)),
            ("frozen_formal_ga",formal))
    results=[test_start(kernel,inc,seq,label,ctx,decoder,origins,args.seed+i*200000)
             for i,(label,seq) in enumerate(starts)]
    assert all(len(x["records"])==EVENT_MACROS*2 for x in results)
    p=OUT/f"seed_{args.seed}"
    p.mkdir(parents=True,exist_ok=True)
    rows=[q for r in results for q in r["records"]]
    for label in [x["start"] for x in results]:
        selected=[q for q in rows if q["start"]==label]
        pairs={}
        for q in selected:
            pairs.setdefault(q["macro"],{})[q["method"]]=q
        assert len(pairs)==EVENT_MACROS and all(set(v)==set(METHODS) for v in pairs.values())
        means={}
        for method in METHODS:
            a=[v[method] for v in pairs.values()]
            means[method]=dict(
                mean_sample_delta_hr=float(np.mean([x["event_sample_delta_hr"] for x in a])),
                mean_64_delta_hr=float(np.mean([x["mean64_delta_hr"] for x in a])),
                fraction_origin_sample_improved=float(np.mean([x["event_sample_delta_hr"]< -1e-10 for x in a])),
                fraction_global64_improved=float(np.mean([x["mean64_delta_hr"]< -1e-10 for x in a])),
                fraction_origin_improved_but_global_worse=float(np.mean([
                    x["event_sample_delta_hr"]< -1e-10 and x["mean64_delta_hr"]>1e-10 for x in a])),
                mean_candidates_per_bundle=float(np.mean([x["candidate_count"] for x in a])))
        print("LNS_TRANSFER_SUMMARY",json.dumps(dict(seed=args.seed,start=label,methods=means)),flush=True)
    (p/"RESULTS.json").write_text(json.dumps(
        dict(status="COMPLETE",seed=args.seed,start_results=results,
             no_optimization_performed=True,new_physical_samples=0,
             total_macro_pairs=EVENT_MACROS*2,
             original_mean_objective_unchanged=True),indent=2)+"\n",encoding="utf-8")
    print("LNS_TRANSFER_SEED_COMPLETE",args.seed,flush=True)

if __name__=="__main__":
    main()
