"""Scheduling-aware LNS v2: genuine destroy-and-repair candidate search.

Differs from v1 (randomly relocate a source-route block) by scoring a *set*
of alternative route-block insertion ranks and internal orders per destruction,
selecting the best repaired permutation under the original exact objective.

Includes matched random-damaged-bundle ablation using the same repair search,
same seeds and budgets, plus 30% conventional local proposals. Previously
observed v1 20k pilot only motivated the architectural repair; this new v2
design and seed blocks are committed before observing any v2 outcomes.

All data are original fixed 64 planning realizations, no sampling or changes
to scientific model, evaluator, scheduler or frozen GA candidate.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_alternative_optimizer_20261009 import Meter,local_search,run_ga,proposal
from la_grid.diagnostics.ga_schedule_aware_lns_20261010 import schedule_bank,MAX_REPAIR_BUNDLE
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_equity_amendment_execute import execution_context

OUT=REPO_ROOT/"results/diagnostics/ga_scheduling_aware_lns_20261010"/"repair_v2"
MODELS=("ga_baseline","iterated_local","lns_repair_route","lns_repair_random")
SCREEN_SEEDS=(900,901,902,903)
CONFIRM_SEEDS=tuple(range(920,940))
EVAL_BUDGET=100000
REPAIR_ANCHORS_PER_MOVE=12
REPAIR_ORDER_OPTIONS=3
LOCAL_PROPOSAL_FRACTION=.30
SNAPSHOT_SAMPLES=4
SNAPSHOT_REFRESH_EVALS=5000
STAGNATION_MACROS=250
NEUTRAL_P=.15

def repair_candidates(sequence,event,rng,mode,kernel):
    seq=tuple(sequence)
    pos={station:i for i,station in enumerate(seq)}
    k=len(event["bundle"])
    if mode=="lns_repair_route":
        group=list(event["bundle"])
    else:
        eligible=[x for x in seq if kernel.damage[event["sample"],kernel.index[x]]>0]
        group=rng.sample(eligible,k)
    if len(group)>MAX_REPAIR_BUNDLE or len(group)==0:
        raise ValueError("Invalid repair group")
    group=list(dict.fromkeys(group))
    group_set=set(group)
    remainder=[s for s in seq if s not in group_set]
    source_path_order=tuple(group) if mode=="lns_repair_route" else tuple(sorted(group,key=lambda x:pos[x]))
    unchanged_order=tuple(sorted(group,key=lambda x:pos[x]))
    # Three order choices, fixed count for both modes.
    noisy=list(group)
    rng.shuffle(noisy)
    orders=[source_path_order,unchanged_order,tuple(noisy)]
    if len(set(map(tuple,orders)))<len(orders):
        orders[2]=tuple(reversed(orders[0]))
    original_min=min(pos[x] for x in group)
    N=len(remainder)
    ranks=[0,max(0,original_min-40),max(0,original_min-20),
           max(0,original_min-8),max(0,original_min-2),
           max(0,original_min),min(N,original_min+5),
           N//4,N//2,3*N//4,N]
    ranks.extend(rng.randrange(N+1) for _ in range(5))
    ranks=list(dict.fromkeys(max(0,min(N,x)) for x in ranks))
    rng.shuffle(ranks)
    # At most 12 insertion ranks in a macro, across three internal orders:
    # true joint repair optimization, rather than one random relocated block.
    ranks=ranks[:REPAIR_ANCHORS_PER_MOVE]
    results=[]
    seen=set()
    for order in orders[:REPAIR_ORDER_OPTIONS]:
        for anchor in ranks:
            result=tuple(remainder[:anchor])+tuple(order)+tuple(remainder[anchor:])
            if result not in seen and result!=seq:
                assert len(result)==92 and len(set(result))==92
                results.append(result)
                seen.add(result)
    return results,len(group)


def optimize(kernel,inc,quality,ctx,decoder,crew_keys,seed,budget,mode):
    rng=random.Random(seed)
    meter=Meter(kernel,budget)
    begin=time.perf_counter()
    for s in inc.values():meter.evaluate(tuple(s))
    current=tuple(quality)
    current_value=meter.evaluate(current)
    event_bank=[];built_at=-1;refresh_count=0
    event_count=0;source_bundle_macros=0;local_macros=0
    strict_accepted=neutral_accepted=restarts=0
    repairs_evaluated=0;macros=0;stagnant=0
    sizes={};low_quality_probes=0
    while meter.expensive<budget and meter.attempts<80*budget:
        if not event_bank or meter.expensive-built_at>=SNAPSHOT_REFRESH_EVALS:
            event_bank,_=schedule_bank(kernel,ctx,decoder,crew_keys,current,rng)
            refresh_count+=1;event_count+=len(event_bank)
            built_at=meter.expensive
        if rng.random()<LOCAL_PROPOSAL_FRACTION or not event_bank:
            proposals=[proposal(current,rng)]
            local_macros+=1
        else:
            weights=[max(1e-14,e["weighted_priority"]) for e in event_bank]
            event=rng.choices(event_bank,weights=weights,k=1)[0]
            proposals,k=repair_candidates(current,event,rng,mode,kernel)
            sizes[str(k)]=sizes.get(str(k),0)+1
            source_bundle_macros+=1
        if not proposals:
            proposals=[proposal(current,rng)]
            local_macros+=1
        best_macro_value=-float("inf")
        best_macro_seq=None
        for candidate in proposals:
            try: val=meter.evaluate(candidate)
            except StopIteration:break
            repairs_evaluated+=1
            if val>best_macro_value:
                best_macro_seq=candidate
                best_macro_value=val
        if best_macro_seq is None:break
        if best_macro_value>current_value+1e-12:
            current=best_macro_seq
            current_value=best_macro_value
            strict_accepted+=1
            stagnant=0
            if strict_accepted%6==0:event_bank=[]
        elif abs(best_macro_value-current_value)<=1e-9 and rng.random()<NEUTRAL_P:
            current=best_macro_seq
            current_value=best_macro_value
            neutral_accepted+=1
            stagnant+=1
        else:
            stagnant+=1
        macros+=1
        if stagnant>=STAGNATION_MACROS and meter.expensive<budget:
            current=tuple(meter.best_seq)
            for _ in range((2,4,8)[restarts%3]):
                current=proposal(current,rng)
            try:current_value=meter.evaluate(current)
            except StopIteration:break
            restarts+=1
            event_bank=[]
            stagnant=0
    assert meter.expensive==budget,(mode,seed,meter.expensive,meter.attempts)
    result=meter.record()
    assert abs(kernel.score(result["best_sequence"])+result["search_best_loss_hr"])<1e-9
    checkpoints=[]
    for n in (20000,50000,100000):
        if n>budget:continue
        choices=[x["best_loss_hr"] for x in meter.path if x["evaluation"]<=n]
        assert choices
        checkpoints.append(dict(evaluations=n,loss_hr=min(choices)))
    result.update(method=mode,seed=seed,budget=budget,
          checkpoints=checkpoints,
          actual_repair_candidates_evaluated=repairs_evaluated,
          macro_iterations=macros,route_macros=source_bundle_macros,
          conventional_local_macros=local_macros,
          accepted_strict_repairs=strict_accepted,
          accepted_neutral_repairs=neutral_accepted,
          restart_count=restarts,event_snapshot_refreshes=refresh_count,
          event_candidates_built=event_count,bundle_size_macro_counts=sizes,
          insertion_rank_cap=REPAIR_ANCHORS_PER_MOVE,
          internal_order_cap=REPAIR_ORDER_OPTIONS,
          local_mix_probability=LOCAL_PROPOSAL_FRACTION,
          elapsed_wall_seconds=time.perf_counter()-begin,
          original_model_unchanged=True,physical_validation_unused=True)
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--seed",type=int,required=True)
    parser.add_argument("--budget",type=int,default=EVAL_BUDGET)
    parser.add_argument("--method",choices=MODELS)
    a=parser.parse_args()
    assert a.seed in SCREEN_SEEDS or a.seed in CONFIRM_SEEDS
    assert a.budget in (20000,100000)
    kernel,inc,quality,_=load()
    ctx,decoder,_=execution_context(kernel.ids)
    crew_keys=decoder.origins(ctx["origins"])
    folder=OUT/f"budget_{a.budget}"/f"seed_{a.seed}"
    folder.mkdir(parents=True,exist_ok=True)
    runs=[]
    for method in (a.method,) if a.method else MODELS:
        if method=="ga_baseline":r=run_ga(kernel,inc,quality,a.seed,a.budget)
        elif method=="iterated_local":r=local_search(kernel,inc,quality,"iterated_local",a.seed,a.budget)
        else:r=optimize(kernel,inc,quality,ctx,decoder,crew_keys,a.seed,a.budget,method)
        assert r["distinct_evaluations"]==a.budget
        assert len(r["best_sequence"])==92 and old.identity(r["best_sequence"])==r["sequence_sha256"]
        r["new_physical_realizations"]=0
        r["formal_strategy_replaced"]=False
        runs.append(r)
        (folder/(method+".json")).write_text(json.dumps(r,indent=2)+"\n")
        print("LNS_REPAIR_RESULT",json.dumps(dict(method=method,seed=a.seed,
           distinct_evaluations=r["distinct_evaluations"],
           final_loss_hr=r["search_best_loss_hr"],
           attempted_evaluations=r["attempted_evaluations"],
           wall_seconds=r["elapsed_wall_seconds"],
           best_sha=r["sequence_sha256"])),flush=True)
    (folder/"ALL_METHODS.json").write_text(json.dumps(
        dict(status="COMPLETE",seed=a.seed,budget=a.budget,
             methods=runs,physical_samples_generated=0,formal_candidate_replaced=False),
             indent=2)+"\n")
    print("LNS_REPAIR_SEED_COMPLETE",a.seed,flush=True)

if __name__=="__main__":main()
