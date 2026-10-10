"""Factorial interaction and true-no-prior tests on the unchanged GA objective.

Isolated diagnostic process. Frozen scientific evaluator and GA engine unchanged.
No new physical samples or previously untouched validation access.

The 2x2x2x2 is population {50,100} x tournament {3,5} x swap mutation
probability {.10,.20} x local seed-neighbors {0, floor(P/4)}.
These contrasts deliberately distinguish the algorithm from an inherited
quality chromosome. Additional no-prior mechanisms remove inherited sequence
from *both* initialization and the incumbent archive.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import random
import time

from la_grid.diagnostics import ga_variant_engine as eng
from la_grid.diagnostics.ga_init_param_20261009 import BASE, load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.paths import REPO_ROOT

OUT = REPO_ROOT / "results/diagnostics/ga_deeper_research_20261009"
SOURCE = "13f8ef8e5d244c70a92a06a45540460c736c70f9"
SEEDS = tuple(range(200,212))
BUDGET = 20000

def make_cases():
    cases = {}
    for population in (50, 100):
        for tournament in (3, 5):
            for mutation in (.10, .20):
                for neighbor in ("none", "quarter"):
                    name = f"p{population}_k{tournament}_m{int(mutation*100):02}_n{neighbor}"
                    cases[name] = dict(population=population,
                                       tournament=tournament,
                                       mutation=mutation,
                                       neighbors=neighbor,
                                       incumbents="all7", exact_warm=True)
    cases["heuristic_only_no_quality"] = dict(
        population=100,tournament=3,mutation=.10,neighbors="none",
        incumbents="all7",exact_warm=False)
    cases["impact_only_archive_no_quality"] = dict(
        population=100,tournament=3,mutation=.10,neighbors="none",
        incumbents="impact",exact_warm=False)
    cases["random_only_archive_no_quality"] = dict(
        population=100,tournament=3,mutation=.10,neighbors="none",
        incumbents="random",exact_warm=False)
    assert len(cases) == 19
    return cases

CASES = make_cases()


def initialize_factory(spec,expected_domain,expected_inc,quality):
    def initialize(domain,inc,rng,config,quality_arg):
        assert tuple(domain)==tuple(expected_domain)
        assert list(inc)==list(expected_inc)
        population=list(inc.values())
        if spec["exact_warm"]:
            assert tuple(quality_arg)==tuple(quality)
            population.append(tuple(quality))
        n=0 if spec["neighbors"]=="none" else max(1,config.population//4)
        for j in range(n):
            parent=tuple(quality) if j%2==0 else tuple(inc["impact-first"])
            population.append(eng.mutation(parent,rng,"inversion"))
        while len(population)<config.population:
            population.append(tuple(rng.sample(domain,len(domain))))
        assert len(population)==config.population
        return population
    return initialize


def run_case(kernel,inc,quality,seed,name,spec,budget):
    assert budget in (20000,100000)
    if spec["neighbors"]=="quarter" and not spec["exact_warm"]:
        raise ValueError("No-quality case cannot contain quality neighbors")
    if spec["incumbents"]=="all7":
        subset=inc
    else:
        subset={spec["incumbents"]+"-first":inc[spec["incumbents"]+"-first"]} if spec["incumbents"]=="impact" else {"random":inc["random"]}
    if spec["incumbents"]=="impact":
        assert list(subset)==["impact-first"]
    config=replace(BASE,population=spec["population"],
                   tournament=spec["tournament"],mutation=spec["mutation"],
                   initialization="quality_mix" if spec["exact_warm"] else "legacy")
    original=eng.initialize
    eng.initialize=initialize_factory(spec,kernel.ids,subset,quality)
    try:
        start=time.perf_counter()
        result=eng.run_search(items=kernel.ids,incumbents=subset,
            objective=kernel.score,seed=seed,config=config,
            max_evaluations=budget,quality=quality,
            checkpoints=(20000,50000,100000),folder=None)
        wall=time.perf_counter()-start
    finally:
        eng.initialize=original
    st=result["state"]
    assert len(result["cache"])==budget and st["expensive_calls"]==budget
    first=result["history"].iloc[0]
    best=result["best_sequence"]
    score=-float(result["best_fitness"])
    assert abs(score+kernel.score(best))<1e-9
    row=dict(case=name,seed=seed,budget=budget,spec=spec,config=asdict(config),
             warm_start_accepted=spec["exact_warm"],
             original_seven_incumbents_in_archive=spec["incumbents"]=="all7",
             init_best_hr=-float(first["generation_best"]),
             init_mean_hr=float(first["population_mean_service_loss_hr"]),
             init_unique_count=int(first["unique_population"]),
             init_entropy=float(first["position_entropy"]),
             final_loss_hr=score,
             observed_search_gain_hr=-float(first["generation_best"])-score,
             best_sequence=list(best),sequence_sha256=old.identity(best),
             attempts=int(st["attempts"]),
             expensive_calls=int(st["expensive_calls"]),
             actual_generations=int(st["generation"]),
             completed_generation_archive_loss_hr=-float(result["archive_fitness"]),
             wall_seconds=wall,
             checkpoint=[dict(evaluations=int(q["distinct_evaluations"]),
                              loss_hr=float(q["best_service_loss_hr"]))
                          for q in result["budget_rows"]],
             objective_realization_count=64,no_new_physical_samples=True)
    return row


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--seed",type=int,required=True)
    parser.add_argument("--budget",type=int,default=BUDGET)
    args=parser.parse_args()
    assert args.seed in SEEDS
    kernel,inc,quality,_=load()
    rows=[]
    out=OUT/"factorial"/f"seed_{args.seed}"
    out.mkdir(parents=True,exist_ok=True)
    for name,spec in CASES.items():
        result=run_case(kernel,inc,quality,args.seed,name,spec,args.budget)
        rows.append(result)
        (out/(name+".json")).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print("FACTOR_RESULT",json.dumps({k:result[k] for k in (
            "case","seed","budget","final_loss_hr","init_best_hr",
            "attempts","expensive_calls","sequence_sha256")}),flush=True)
    record=dict(status="COMPLETE",source_commit=SOURCE,seed=args.seed,
         budget=args.budget,distinct_case_count=len(rows),
         no_new_physical_sampling=True,formal_policy_changed=False,results=rows)
    (out/"ALL_CASES.json").write_text(json.dumps(record,indent=2)+"\n")
    print("FACTOR_SEED_COMPLETE",args.seed,len(rows),flush=True)


if __name__ == "__main__":
    main()
