"""Equal-budget original-vs-tuned GA root-cause controlled search.

Pairs to existing 100k confirmation on exact same seeds 400..419, comparing
legacy archive-only inversion GA, warm-start, generational elitism and final
operator. Scientific evaluator and 64 training realizations unchanged.
"""
from __future__ import annotations
import argparse,json,time
from dataclasses import asdict,replace

from la_grid.diagnostics.ga_variant_engine import Variant,run_search
from la_grid.diagnostics.ga_init_param_20261009 import BASE,load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.paths import REPO_ROOT

OUT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"/"root_cause_100k"
SEEDS=tuple(range(400,420))
BUDGET=100000
CASES={
 "legacy_original":Variant(population=100,crossover=.8,mutation=.2,tournament=3,elites=0,
                           initialization="legacy",mutation_operator="inversion",
                           crossover_operator="ordered"),
 "legacy_plus_warm":Variant(population=100,crossover=.8,mutation=.2,tournament=3,elites=0,
                           initialization="quality_mix",mutation_operator="inversion",
                           crossover_operator="ordered"),
 "legacy_plus_warm_and_elite":Variant(population=100,crossover=.8,mutation=.2,tournament=3,elites=1,
                           initialization="quality_mix",mutation_operator="inversion",
                           crossover_operator="ordered"),
 "final_swap_without_elite":replace(BASE,elites=0),
}
assert len(CASES)==4

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--seed",type=int,required=True)
 p.add_argument("--budget",type=int,default=BUDGET)
 a=p.parse_args()
 assert a.seed in SEEDS and a.budget==BUDGET
 kernel,inc,quality,_=load()
 folder=OUT/f"seed_{a.seed}"
 folder.mkdir(parents=True,exist_ok=True)
 rows=[]
 for name,config in CASES.items():
    start=time.perf_counter()
    r=run_search(items=kernel.ids,incumbents=inc,objective=kernel.score,
       seed=a.seed,config=config,max_evaluations=a.budget,
       quality=quality,checkpoints=(20000,50000,100000),folder=None)
    assert len(r["cache"])==a.budget and r["state"]["expensive_calls"]==a.budget
    seq=r["best_sequence"];score=-float(r["best_fitness"])
    assert abs(score+kernel.score(seq))<1e-9
    row=dict(case=name,seed=a.seed,budget=a.budget,config=asdict(config),
       generation0_best_loss_hr=-float(r["history"].iloc[0]["generation_best"]),
       final_loss_hr=score,
       completed_archive_loss_hr=-float(r["archive_fitness"]),
       best_sequence=list(seq),sequence_sha256=old.identity(seq),
       attempted_evaluations=int(r["state"]["attempts"]),
       expensive_evaluations=a.budget,
       actual_generations=int(r["state"]["generation"]),
       checkpoints=[dict(evaluations=int(x["distinct_evaluations"]),
                         loss_hr=float(x["best_service_loss_hr"])) for x in r["budget_rows"]],
       elapsed_wall_seconds=time.perf_counter()-start,
       new_physical_samples=0,formal_strategy_changed=False)
    rows.append(row)
    (folder/(name+".json")).write_text(json.dumps(row,indent=2)+"\n")
    print("ROOT_CAUSE_RESULT",json.dumps({k:row[k] for k in (
       "case","seed","budget","final_loss_hr","generation0_best_loss_hr",
       "attempted_evaluations","sequence_sha256")}),flush=True)
 (folder/"ALL_CASES.json").write_text(json.dumps(
     dict(status="COMPLETE",seed=a.seed,budget=a.budget,cases=rows,
          new_physical_samples=0,formal_policy_changed=False),indent=2)+"\n")
 print("ROOT_CAUSE_SEED_COMPLETE",a.seed,flush=True)

if __name__=="__main__":main()
