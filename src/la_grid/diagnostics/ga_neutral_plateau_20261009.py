"""Mechanism-targeted plateau-neutral drift experiment.

Tests whether scheduler-equivalent objective plateaus suppress strict ILS.
Frozen 64 planning samples, same incumbent warm start, count-matched 100k
objective evaluations per method. The comparison explores a sensitivity grid,
not a newly established default probability.
"""
from __future__ import annotations
import argparse,json,random,time,math
from pathlib import Path

import numpy as np
from la_grid.diagnostics.ga_alternative_optimizer_20261009 import Meter,proposal,run_ga
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.paths import REPO_ROOT

OUT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"/"plateau_neutral"
SEEDS=tuple(range(500,520))
BUDGET=100000
NEUTRAL_PROBABILITIES=(0.0,.10,.50,1.0)
NEUTRAL_TOLERANCE_HR=1e-9

def search(kernel,inc,quality,seed,budget,p):
    assert 0<=p<=1
    rng=random.Random(seed)
    meter=Meter(kernel,budget)
    start=time.perf_counter()
    for seq in inc.values():
        meter.evaluate(tuple(seq))
    current=tuple(quality)
    score=meter.evaluate(current)
    first=-score
    strict_moves=neutral_moves=stagnant=restarts=neutral_proposals=0
    for_limit=80*budget
    while meter.expensive<budget and meter.attempts<for_limit:
        cand=proposal(current,rng)
        try: value=meter.evaluate(cand)
        except StopIteration:break
        delta=value-score
        if delta>NEUTRAL_TOLERANCE_HR:
            current=cand;score=value;strict_moves+=1;stagnant=0
        elif abs(delta)<=NEUTRAL_TOLERANCE_HR:
            neutral_proposals+=1;stagnant+=1
            if p>0 and rng.random()<p:
                current=cand;score=value;neutral_moves+=1
        else:
            stagnant+=1
        if stagnant>=800:
            current=tuple(meter.best_seq)
            for _ in range((2,4,8)[restarts%3]):
                current=proposal(current,rng)
            try: score=meter.evaluate(current)
            except StopIteration:break
            stagnant=0;restarts+=1
    out=meter.record()
    assert out["completed_budget"],(seed,p,out["distinct_evaluations"])
    assert abs(kernel.score(tuple(out["best_sequence"]))+out["search_best_loss_hr"])<1e-9
    out.update(method=f"neutral_{p:.2f}",seed=seed,budget=budget,
               neutral_move_probability=p,neutral_equality_tol_hr=NEUTRAL_TOLERANCE_HR,
               initial_best_loss_hr=first,
               neutral_proposals=neutral_proposals,accepted_neutral_moves=neutral_moves,
               accepted_strict_moves=strict_moves,restarts=restarts,
               elapsed_wall_seconds=time.perf_counter()-start,
               physical_realizations_generated=0,formal_strategy_changed=False)
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--seed",type=int,required=True)
    parser.add_argument("--budget",type=int,default=BUDGET)
    args=parser.parse_args()
    assert args.seed in SEEDS and args.budget==BUDGET
    kernel,inc,quality,_=load()
    folder=OUT/f"seed_{args.seed}"
    folder.mkdir(parents=True,exist_ok=True)
    records=[]
    for p in NEUTRAL_PROBABILITIES:
        rec=search(kernel,inc,quality,args.seed,args.budget,p)
        records.append(rec)
        (folder/(rec["method"]+".json")).write_text(json.dumps(rec,indent=2)+"\n")
        print("PLATEAU_RESULT",json.dumps({k:rec[k] for k in (
            "method","seed","budget","search_best_loss_hr","attempted_evaluations",
            "neutral_proposals","accepted_neutral_moves","sequence_sha256")}),flush=True)
    ga=run_ga(kernel,inc,quality,args.seed,args.budget)
    ga.update(physical_realizations_generated=0,formal_strategy_changed=False)
    records.append(ga)
    (folder/"ga_baseline.json").write_text(json.dumps(ga,indent=2)+"\n")
    print("PLATEAU_RESULT",json.dumps({k:ga[k] for k in (
        "method","seed","budget","search_best_loss_hr","attempted_evaluations","sequence_sha256")}),flush=True)
    (folder/"ALL_METHODS.json").write_text(json.dumps(
        dict(status="COMPLETE",seed=args.seed,budget=args.budget,methods=records,
             objective_realizations=64,new_physical_samples=0),indent=2)+"\n")
    print("PLATEAU_SEED_COMPLETE",args.seed,flush=True)

if __name__=="__main__": main()
