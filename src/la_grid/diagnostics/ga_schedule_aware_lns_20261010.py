"""Schedule-aware, source-gate-driven Large Neighborhood Search (LNS).

This is a diagnostic optimization *method*, NOT a revised damage/restoration
model. Uses original frozen 64 planning realizations, exact population loss
kernel, original 57-crew directed scheduler and actual source-connected graph.

EVENT-ROUTE LNS:
   - Build event-complete schedules for 4 RNG-selected frozen planning states;
   - detect completion events that reconnect already functional components to
     a Core source, weighting by population dependency mass and event delay;
   - build 2–8-station repair bundles from the actual restored source path,
     newly reconnected members and their priority context;
   - remove that bundle from the full 92-ID chromosome and reinsert as one
     contiguous construction with source-path-aware ordering.

CONTROL: identical candidate machinery, bundle size and event schedule-bank
refreshing, but select k damaged-priority stations uniformly at random instead
of the source-path / effective-service-informed stations.

Test with equal expensive *distinct-permutation evaluations* and preserve
attempted calls/wall time separately. Diagnostic scores remain 64-sample means;
never inspect the proposed 2000-realization validation set.
"""
from __future__ import annotations
import argparse
import json
import math
import random
import time
from pathlib import Path

import networkx as nx
import numpy as np

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_init_param_20261009 import load, BASE
from la_grid.diagnostics.ga_alternative_optimizer_20261009 import Meter,local_search,run_ga,proposal
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_equity_amendment_execute import execution_context

OUT=REPO_ROOT/"results/diagnostics/ga_scheduling_aware_lns_20261010"
MODEL_BASE="409693a68a099e6c1ec2fee093b3bfd2ecf80dd6"
METHODS=("ga_baseline","iterated_local","lns_event_route","lns_random_bundle")
CHECKPOINTS=(20000,50000,100000)
BUDGET=100000
SCREEN_SEEDS=(800,801,802,803)
CONFIRM_SEEDS=tuple(range(820,840))
SNAPSHOT_SAMPLES=4
SNAPSHOT_INTERVAL=2500
MAX_REPAIR_BUNDLE=8
NEUTRAL_ACCEPT_PROB=0.15
STAGNATION_ATTEMPTS=1200

def connected_to_source(G,active,sources):
    """Native graph reachability, restricted to currently source-eligible nodes."""
    subset=G.subgraph(active)
    seen=set()
    for root in sorted(set(sources)&set(active)):
        if root not in seen:
            seen.update(nx.node_connected_component(subset,root))
    return seen

def collect_source_events(kernel,ctx,decoder,crew_keys,sequence,sample_index):
    ds=kernel.damage[sample_index]
    duration=kernel.duration[sample_index]
    seq_order=decoder.order(sequence)
    finish,*_=decoder.decode(order=seq_order,damage=ds,
                            duration=duration,origins=crew_keys)
    G=ctx["graph"]
    source_names=set(ctx["sources"])
    initially_active={str(kernel.ids[i]) for i in range(92) if ds[i]<=1}
    active=set(initially_active)
    connected=connected_to_source(G,active,source_names)
    events=[]
    sequence_positions={s:i for i,s in enumerate(sequence)}
    tasks=sorted([(float(finish[i]),i) for i in range(92)
                  if ds[i]>=2 and np.isfinite(finish[i])],key=lambda p:(p[0],p[1]))
    for t,i in tasks:
        station=str(kernel.ids[i])
        assert station not in active
        active.add(station)
        newly_connected=connected_to_source(G,active,source_names)
        gained=newly_connected-connected
        if gained and t<480:
            # A service-eligible, already repaired DS2+ station is worth full
            # population dependency mass. DS0 full and DS1 half/full likewise.
            gained_mass=0.
            for node in gained:
                j=kernel.index[node]
                factor=(1. if ds[j]==0 or finish[j]<=t+1e-9 else
                        0.5 if ds[j]==1 else 0.)
                gained_mass+=float(kernel.station_mass[j])*factor
            # Obtain one *actual active* Core-source route; not a speculative
            # electrical flow or unique essential-source-path assertion.
            sub=G.subgraph(active)
            paths=[]
            for root in sorted(source_names&active):
                if nx.has_path(sub,root,station):
                    path=nx.shortest_path(sub,root,station)
                    paths.append(path)
            if paths:
                selected=min(paths,key=lambda p:(len(p),tuple(p)))
                # Nodes on source path must have been repaired or initially
                # functional at this event; only scheduled damaged tasks are
                # manipulable as restoration priority chromosomes.
                ordered=[node for node in selected if ds[kernel.index[node]]>0]
                # Add two largest-mass newly connected damaged stations
                # to make a genuine multi-station reconnect bundle.
                additions=sorted(
                    (node for node in gained if ds[kernel.index[node]]>0
                     and node not in ordered),
                    key=lambda x:(-kernel.station_mass[kernel.index[x]],x)
                )[:2]
                bundle=list(dict.fromkeys((ordered+additions)))[:MAX_REPAIR_BUNDLE]
                # A singleton may still trigger a reconnection. Supplement
                # from graph-adjacent damaged tasks already close in priority.
                if len(bundle)<2:
                    near=[v for v in G.neighbors(station)
                        if ds[kernel.index[str(v)]]>0
                        and str(v) not in bundle]
                    near=sorted(map(str,near),key=lambda x:(sequence_positions[x],x))
                    bundle.extend(near[:2-len(bundle)])
                if bundle:
                    # A delayed large reconnect is a plausible intervention;
                    # use it only for proposal targeting, never change the J.
                    score=max(gained_mass,1.)/kernel.total_mass*(1.+math.sqrt(max(t,0.)))
                    events.append(dict(sample=int(sample_index),gateway=station,
                        time_hr=t,newly_reconnected=len(gained),
                        dependency_mass=gained_mass,weighted_priority=score,
                        bundle=tuple(bundle),
                        path=tuple(selected)))
        connected=newly_connected
    return events

def schedule_bank(kernel,ctx,decoder,crew_keys,sequence,rng):
    choices=rng.sample(range(64),SNAPSHOT_SAMPLES)
    bank=[]
    for sample in choices:
        bank.extend(collect_source_events(kernel,ctx,decoder,crew_keys,sequence,sample))
    return bank,choices

def reconstruct(parent,event,rng,mode,kernel):
    seq=tuple(parent)
    orig_pos={v:i for i,v in enumerate(seq)}
    k=min(MAX_REPAIR_BUNDLE,len(event["bundle"]))
    if mode=="lns_event_route":
        bundle=list(event["bundle"][:k])
    else:
        # Control draws from the *same sampled realization's damaged task
        # pool*. Otherwise moving DS0 tasks would artificially handicap it.
        eligible=[x for x in seq if kernel.damage[event['sample'],kernel.index[x]]>0]
        bundle=rng.sample(eligible,k)
        bundle.sort(key=lambda x:orig_pos[x])
    # Preserve event-route source -> gateway precedence from actual connected
    # path; random comparator shuffles destroyed stations with same p=.35.
    if rng.random()<.35:
        rng.shuffle(bundle)
    remainder=[s for s in seq if s not in set(bundle)]
    initial=min(orig_pos[x] for x in bundle)
    # Combined block move to an earlier priority rank; source path and the
    # gateway are moved together, rather than one single-gene insertion.
    shift=rng.randint(2,36)
    anchor=max(0,initial-shift)
    if rng.random()<.15: anchor=rng.randrange(len(remainder)+1)
    result=tuple(remainder[:anchor]+bundle+remainder[anchor:])
    if len(result)!=len(seq) or len(set(result))!=len(seq):raise RuntimeError("Corrupt LNS chromosome")
    return result

def evaluate_lns(kernel,inc,quality,ctx,decoder,crew_keys,seed,budget,mode):
    rng=random.Random(int(seed))
    meter=Meter(kernel,budget)
    start=time.perf_counter()
    for candidate in inc.values():meter.evaluate(tuple(candidate))
    incumbent=tuple(quality)
    current=incumbent
    current_value=meter.evaluate(current)
    strict_moves=0
    neutral_moves=0
    stagnant=0
    restarts=0
    event_rebuilds=0
    sampled_event_count=0
    event_bundle_proposals=0
    fallback_proposals=0
    bundle_size_counts={}
    bank=[]
    snapshot_samples=[]
    refreshed_at=-1
    while meter.expensive<budget and meter.attempts<80*budget:
        if not bank or meter.expensive-refreshed_at>=SNAPSHOT_INTERVAL or stagnant>=3000:
            bank,snapshot_samples=schedule_bank(kernel,ctx,decoder,crew_keys,current,rng)
            sampled_event_count+=len(bank)
            event_rebuilds+=1
            refreshed_at=meter.expensive
        if bank:
            weights=[max(1e-14,q["weighted_priority"]) for q in bank]
            pick=rng.choices(bank,weights=weights,k=1)[0]
            candidate=reconstruct(current,pick,rng,mode,kernel)
            event_bundle_proposals+=1
            k=len(pick['bundle'])
            bundle_size_counts[str(k)]=bundle_size_counts.get(str(k),0)+1
        else:
            candidate=proposal(current,rng)
            fallback_proposals+=1
        if candidate==current:
            candidate=proposal(current,rng)
            fallback_proposals+=1
        try:
            value=meter.evaluate(candidate)
        except StopIteration:
            break
        delta=value-current_value
        if delta>1e-12:
            current=candidate;current_value=value
            strict_moves+=1
            stagnant=0
            # Refresh event bundle immediately after substantial changes
            # only when stale events could have become unrepresentative.
            if strict_moves%8==0: bank=[]
        elif abs(delta)<=1e-9 and rng.random()<NEUTRAL_ACCEPT_PROB:
            current=candidate;current_value=value
            neutral_moves+=1
            stagnant+=1
        else:
            stagnant+=1
        if stagnant>=STAGNATION_ATTEMPTS:
            current=tuple(meter.best_seq)
            # Apply a controlled multiple-move perturbation to escape the
            # basin. These moves are proposals; their objective evaluations
            # are metered when scored (not treated as free fitness calls).
            for _ in range((2,4,8)[restarts%3]):
                current=proposal(current,rng)
            try:current_value=meter.evaluate(current)
            except StopIteration:break
            stagnant=0;restarts+=1
            bank=[]
    assert meter.expensive==budget, dict(method=mode,seed=seed,expense=meter.expensive,
                                        attempts=meter.attempts)
    final=meter.record()
    assert abs(kernel.score(final["best_sequence"])+final["search_best_loss_hr"])<1e-9
    cp=[]
    for bound in (q for q in CHECKPOINTS if q<=budget):
        history=[q["best_loss_hr"] for q in meter.path if q["evaluation"]<=bound]
        assert history
        cp.append(dict(evaluations=bound,loss_hr=min(history)))
    final.update(method=mode,seed=seed,budget=budget,
       checkpoints=cp,
       strict_moves=strict_moves,neutral_moves=neutral_moves,
       restarts=restarts,event_bank_refreshes=event_rebuilds,
       source_reconnection_events_sampled=sampled_event_count,
       event_bundle_proposals=event_bundle_proposals,
       bundle_size_proposal_counts=bundle_size_counts,
       random_proposal_fallbacks=fallback_proposals,
       sample_snapshot_count=SNAPSHOT_SAMPLES,
       snapshot_refresh_interval_distinct=SNAPSHOT_INTERVAL,
       bundle_max_nodes=MAX_REPAIR_BUNDLE,
       acceptance_neutral_probability=NEUTRAL_ACCEPT_PROB,
       elapsed_wall_seconds=time.perf_counter()-start,
       original_model_unchanged=True,physical_validation_unused=True)
    return final

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed",required=True,type=int)
    p.add_argument("--budget",type=int,default=BUDGET)
    p.add_argument("--method",choices=METHODS,default=None)
    a=p.parse_args()
    assert a.seed in SCREEN_SEEDS or a.seed in CONFIRM_SEEDS
    assert a.budget in (20000,100000)
    kernel,inc,quality,ident=load()
    methods=[a.method] if a.method else METHODS
    ctx,decoder,_=execution_context(kernel.ids)
    crew_keys=decoder.origins(ctx["origins"])
    results=[]
    directory=OUT/f"budget_{a.budget}"/f"seed_{a.seed}"
    directory.mkdir(parents=True,exist_ok=True)
    for method in methods:
        if method=="ga_baseline":result=run_ga(kernel,inc,quality,a.seed,a.budget)
        elif method=="iterated_local":result=local_search(kernel,inc,quality,"iterated_local",a.seed,a.budget)
        else:result=evaluate_lns(kernel,inc,quality,ctx,decoder,crew_keys,a.seed,a.budget,method)
        assert result["distinct_evaluations"]==a.budget and result.get("completed_budget",True)
        assert len(result["best_sequence"])==92
        assert old.identity(result["best_sequence"])==result["sequence_sha256"]
        result.update(original_model_base_commit=MODEL_BASE,
                      new_physical_realizations=0,formal_strategy_changed=False)
        results.append(result)
        (directory/(method+".json")).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print("LNS_RESULT",json.dumps({k:result[k] for k in (
            "method","seed","budget","search_best_loss_hr",
            "attempted_evaluations","elapsed_wall_seconds","sequence_sha256")}),flush=True)
    (directory/"ALL_METHODS.json").write_text(json.dumps(
        dict(status="COMPLETE",seed=a.seed,budget=a.budget,method_count=len(results),
             methods=results,original_physical_samples=64,
             new_physical_samples=0,formal_policy_replaced=False),indent=2)+"\n",encoding="utf-8")
    print("LNS_SEED_COMPLETE",a.seed,flush=True)

if __name__=="__main__":
    main()
