"""500k-budget confirmation: tournament 3, tournament 5, and ILS.

Fix new seeds 700–709 and the three methods before observing their results.
No new physical states: all scores use the original frozen 64 planning samples.
Each run counts exactly 500k distinct expensive objective calls, with other
attempted calls and wall times reported separately.
"""
from __future__ import annotations
import argparse,json,time
from dataclasses import asdict,replace
from pathlib import Path

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_init_param_20261009 import BASE,load
from la_grid.diagnostics.ga_variant_engine import run_search
from la_grid.diagnostics.ga_alternative_optimizer_20261009 import local_search
from la_grid.diagnostics import ga_search_budget_sensitivity as old

OUT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"/"high_budget_500k"
SEEDS=tuple(range(700,710))
BUDGET=500000
GA_CASES=(("ga_k3",BASE),("ga_k5",replace(BASE,tournament=5)))

def one_ga(kernel,inc,quality,seed,name,config,budget):
    begin=time.perf_counter()
    r=run_search(items=kernel.ids,incumbents=inc,objective=kernel.score,
                 seed=seed,config=config,max_evaluations=budget,
                 checkpoints=(50000,100000,250000,500000),
                 folder=None,quality=quality)
    assert len(r["cache"])==budget and r["state"]["expensive_calls"]==budget
    best=r["best_sequence"]
    assert abs(kernel.score(best)+r["best_fitness"])<1e-9
    return dict(method=name,seed=seed,budget=budget,config=asdict(config),
        best_sequence=list(best),sequence_sha256=old.identity(best),
        planning_loss_hr=-float(r["best_fitness"]),
        attempt_count=int(r["state"]["attempts"]),
        distinct_query_count=budget,
        completed_generations=int(r["state"]["generation"]),
        elapsed_wall_seconds=time.perf_counter()-begin,
        budget_checkpoints=[dict(evaluations=int(x["distinct_evaluations"]),
             best_loss_hr=float(x["best_service_loss_hr"])) for x in r["budget_rows"]],
        no_new_physical_sampling=True,formal_policy_replaced=False)

def one_ils(kernel,inc,quality,seed,budget):
    r=local_search(kernel,inc,quality,"iterated_local",seed,budget)
    assert r["distinct_evaluations"]==budget and r["completed_budget"]
    improvements=r["strict_improvements"]
    initial=-float(kernel.score(quality))
    checkpoints=[]
    for cp in (50000,100000,250000,500000):
        best=min([initial]+[float(v["best_loss_hr"]) for v in improvements if int(v["evaluation"])<=cp])
        checkpoints.append(dict(evaluations=cp,best_loss_hr=best))
    return dict(method="iterated_local",seed=seed,budget=budget,
        best_sequence=r["best_sequence"],sequence_sha256=r["sequence_sha256"],
        planning_loss_hr=r["search_best_loss_hr"],
        attempt_count=r["attempted_evaluations"],
        distinct_query_count=r["distinct_evaluations"],
        accepted_moves=r["accepted_moves"],
        restart_count=r["restart_count"],
        elapsed_wall_seconds=r["elapsed_wall_seconds"],
        budget_checkpoints=checkpoints,
        no_new_physical_sampling=True,formal_policy_replaced=False)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--budget",type=int,default=BUDGET)
    a=p.parse_args()
    assert a.seed in SEEDS and a.budget==BUDGET
    kernel,inc,quality,_=load()
    directory=OUT/f"seed_{a.seed}"
    directory.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name,config in GA_CASES:
        item=one_ga(kernel,inc,quality,a.seed,name,config,a.budget)
        rows.append(item)
        (directory/(name+".json")).write_text(json.dumps(item,indent=2)+"\n")
        print("HIGH_BUDGET_RESULT",json.dumps({k:item[k] for k in (
            "seed","method","budget","planning_loss_hr",
            "attempt_count","sequence_sha256")}),flush=True)
    item=one_ils(kernel,inc,quality,a.seed,a.budget)
    rows.append(item)
    (directory/"iterated_local.json").write_text(json.dumps(item,indent=2)+"\n")
    print("HIGH_BUDGET_RESULT",json.dumps({k:item[k] for k in (
        "seed","method","budget","planning_loss_hr",
        "attempt_count","sequence_sha256")}),flush=True)
    (directory/"ALL_METHODS.json").write_text(json.dumps(
        dict(status="COMPLETE",seed=a.seed,budget=a.budget,
             methods=rows,physical_sampling=False,
             formal_policy_replaced=False),indent=2)+"\n")
    print("HIGH_BUDGET_SEED_COMPLETE",a.seed,flush=True)

if __name__=="__main__":main()
