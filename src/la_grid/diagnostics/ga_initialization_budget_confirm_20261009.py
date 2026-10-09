"""Fixed 100k-evaluation follow-up for five preselected initialization contrasts.

No post-screening or evaluation-guided method selection. Fresh 20-seed results
use only original 64 planning realizations. The 100k runs restart from scratch
(20k prefixes are NOT treated as zero-cost continuation).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import time

from la_grid.diagnostics import ga_variant_engine as eng
from la_grid.diagnostics.ga_init_param_20261009 import BASE, load
from la_grid.diagnostics.ga_initialization_replication_20261009 import (
    CASES, initial_population, neighbor_prior_positions)
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.paths import REPO_ROOT

OUT=REPO_ROOT/"results/diagnostics/ga_initialization_100k_confirmation_20261009"
CONFIRM_CASES=(
    "baseline_7h_1w_25n",
    "heuristics_only",
    "neighbors_0",
    "neighbors_50",
    "heuristics_0",
)

def perform(seed:int,budget:int):
    assert seed in range(100,120)
    assert budget==100000
    kernel,inc,quality,identity=load()
    inc={str(k):tuple(v) for k,v in inc.items()}
    domain=tuple(str(x) for x in kernel.ids)
    original=eng.initialize
    folder=OUT/("seed_"+str(seed))
    folder.mkdir(parents=True,exist_ok=True)
    results=[]
    for name in CONFIRM_CASES:
        spec=CASES[name]
        expected,composition=initial_population(spec,domain,inc,quality,seed)
        def initializer(items,incumbents,rng,config,prior):
            h,w,n,source=spec
            assert config==BASE and tuple(items)==domain
            assert list(incumbents)==list(inc)
            if h==7:
                pop=list(incumbents.values())
            elif h==6:
                pop=[v for k,v in incumbents.items() if k!="random"]
            elif h==3:
                pop=[incumbents[k] for k in ("impact-first","hospital-first","closeness-first")]
            elif h==1:
                pop=[incumbents["impact-first"]]
            else:
                pop=[]
            pop=[tuple(x) for x in pop]+[tuple(prior)]*w
            priors=neighbor_prior_positions(n,source)
            for j in range(n):
                parent=prior if j in priors else incumbents["impact-first"]
                pop.append(eng.mutation(tuple(parent),rng,"inversion"))
            while len(pop)<config.population:
                pop.append(tuple(rng.sample(items,len(items))))
            assert pop==expected
            return pop
        try:
            eng.initialize=initializer
            start=time.perf_counter()
            result=eng.run_search(
                items=kernel.ids,incumbents=inc,objective=kernel.score,
                seed=seed,config=BASE,max_evaluations=budget,
                checkpoints=(20000,50000,100000),folder=None,quality=quality)
            sec=time.perf_counter()-start
        finally:
            eng.initialize=original
        state=result["state"]
        assert state["expensive_calls"]==budget and len(result["cache"])==budget
        hist=result["history"]
        first=hist.iloc[0]
        row=dict(
            case=name,seed=seed,budget=budget,**composition,
            initial_best_loss_hr=-float(first["generation_best"]),
            generation0_population_mean_loss_hr=float(first["population_mean_service_loss_hr"]),
            final_best_loss_hr=-float(result["best_fitness"]),
            postinitialization_gain_hr=-float(first["generation_best"])+float(result["best_fitness"]),
            total_attempted_evaluations=int(state["attempts"]),
            completed_generations=int(state["generation"]),
            elapsed_wall_seconds=sec,
            final_sequence_sha256=old.identity(result["best_sequence"]),
            objective_planning_realizations=64,
            no_new_physical_sampling=True,
        )
        checkpoints=[dict(evaluations=int(q["distinct_evaluations"]),
                          loss_hr=float(q["best_service_loss_hr"]))
                     for q in result["budget_rows"]]
        row["checkpoints"]=checkpoints
        results.append(row)
        (folder/(name+".json")).write_text(json.dumps(row,indent=2)+"\n",encoding="utf-8")
        print("CONFIRM_RESULT",json.dumps(row,sort_keys=True),flush=True)
    (folder/"ALL_CASES.json").write_text(json.dumps(
        dict(status="COMPLETED",seed=seed,base_commit="b1030f839d522fed4af21e424472e3f8b076797b",
             budget=budget, cases=results,formal_policy_replaced=False,
             physical_sampling=False),indent=2)+"\n",encoding="utf-8")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--seed",type=int,required=True)
    parser.add_argument("--budget",type=int,default=100000)
    args=parser.parse_args()
    perform(args.seed,args.budget)

if __name__=="__main__":
    main()
