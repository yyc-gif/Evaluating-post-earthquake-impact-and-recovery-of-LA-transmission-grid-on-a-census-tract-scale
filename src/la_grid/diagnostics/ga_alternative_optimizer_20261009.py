"""Fair-budget GA vs non-GA permutation search baselines on frozen 64-sample model.

The same previous-best quality sequence and seven frozen heuristics are available
to all methods, with every expensive objective call counted per method. These
are diagnostic optimization baselines; not new formal strategies, physical
validation samples, or evidence of universal optimizer superiority.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import random
import time

import numpy as np

from la_grid.diagnostics import ga_variant_engine as eng
from la_grid.diagnostics.ga_init_param_20261009 import BASE, load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.paths import REPO_ROOT

OUT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"/"alternative"
SOURCE="13f8ef8e5d244c70a92a06a45540460c736c70f9"
SEEDS=tuple(range(300,320))
BUDGET=100000
METHODS=("ga_baseline","iterated_local","annealed_local")

def proposal(current,rng,operator=None):
    if operator is None:
        # Fixed, non-tuned equal operator mixture
        operator=("swap","insertion","inversion")[rng.randrange(3)]
    return eng.mutation(current,rng,operator)

class Meter:
    def __init__(self,kernel,budget):
        self.kernel=kernel
        self.budget=budget
        self.cache={}
        self.attempts=0
        self.expensive=0
        self.best_value=-float("inf")
        self.best_seq=None
        self.path=[]
    def evaluate(self,seq):
        self.attempts+=1
        seq=tuple(seq)
        key=bytes(self.kernel.index[s] for s in seq)
        if key not in self.cache:
            if self.expensive>=self.budget: raise StopIteration
            score=float(self.kernel.score(seq))
            self.cache[key]=score
            self.expensive+=1
            if score>self.best_value:
                self.best_value=score
                self.best_seq=seq
                self.path.append(dict(evaluation=self.expensive,best_loss_hr=-score,
                    sequence_sha256=old.identity(seq)))
        return self.cache[key]
    def record(self):
        return dict(distinct_evaluations=self.expensive,
                    attempted_evaluations=self.attempts,
                    search_best_loss_hr=-self.best_value,
                    best_sequence=list(self.best_seq),
                    sequence_sha256=old.identity(self.best_seq),
                    strict_improvements=self.path,
                    completed_budget=self.expensive==self.budget)


def local_search(kernel,inc,quality,method,seed,budget):
    rng=random.Random(seed)
    meter=Meter(kernel,budget)
    start=time.perf_counter()
    # Reference scoring inside the budget, as in the final GA.
    for s in inc.values(): meter.evaluate(tuple(s))
    current=tuple(quality)
    current_value=meter.evaluate(current)
    init_value=current_value
    accepted=0
    worse_accepted=0
    restarts=0
    calibration_deltas=[]
    checkpoints=[]
    check=(20000,50000,100000)
    last_cp=0

    if method=="annealed_local":
        # Count 128 landscape calibration probes within the search budget.
        # All temperature scales derive from positive neighbor loss increases.
        for i in range(128):
            candidate=proposal(current,rng)
            score=meter.evaluate(candidate)
            penalty=max(0.0,current_value-score)
            if penalty>1e-10: calibration_deltas.append(penalty)
        scale=float(np.median(calibration_deltas)) if calibration_deltas else .05
        temp0=scale/(-math.log(.80))
        temp_end=scale/(-math.log(.01))
        temp0=max(temp0,1e-6)
        temp_end=max(min(temp_end,temp0),1e-8)
    else:
        temp0=temp_end=None

    stagnant=0
    def maybe_checkpoint():
        nonlocal last_cp
        for cp in check:
            if last_cp<cp<=meter.expensive:
                checkpoints.append(dict(evaluations=cp,loss_hr=-meter.best_value))
                last_cp=cp

    safety=60*budget
    while meter.expensive<budget and meter.attempts<safety:
        if method=="iterated_local":
            candidate=proposal(current,rng)
            try:
                score=meter.evaluate(candidate)
            except StopIteration:break
            if score>current_value+1e-12:
                current=candidate;current_value=score
                accepted+=1;stagnant=0
            else:
                stagnant+=1
            if stagnant>=800:
                # Fixed-size perturbations of the global best; no fitness
                # evaluations are hidden here. Perturbations are only proposals.
                current=tuple(meter.best_seq)
                for _ in range((2,4,8)[restarts%3]):
                    current=proposal(current,rng)
                try:
                    current_value=meter.evaluate(current)
                except StopIteration:break
                stagnant=0;restarts+=1
        elif method=="annealed_local":
            candidate=proposal(current,rng)
            try:
                score=meter.evaluate(candidate)
            except StopIteration:break
            progress=(meter.expensive-1)/max(1,budget-1)
            temp=temp0*(temp_end/temp0)**progress
            delta=score-current_value
            if delta>=0 or rng.random()<math.exp(max(-700,delta/max(temp,1e-12))):
                if delta < -1e-12: worse_accepted+=1
                current=candidate;current_value=score;accepted+=1
                stagnant=0
            else:
                stagnant+=1
            if stagnant>=2500:
                # Fixed reheating to best-seen; never truncate metric history.
                current=tuple(meter.best_seq)
                current_value=meter.evaluate(current)
                stagnant=0;restarts+=1
        else: raise ValueError(method)
        maybe_checkpoint()

    rec=meter.record()
    assert rec["completed_budget"],(method,seed,rec["distinct_evaluations"])
    assert abs(kernel.score(tuple(rec["best_sequence"]))+rec["search_best_loss_hr"])<1e-9
    rec.update(method=method,seed=seed,budget=budget,elapsed_wall_seconds=time.perf_counter()-start,
               generation0_loss_hr=-init_value,
               accepted_moves=accepted,accepted_worse_moves=worse_accepted,
               restart_count=restarts,annealing_initial_temperature_hr=temp0,
               annealing_final_temperature_hr=temp_end,
               calibration_positive_count=len(calibration_deltas),
               checkpoints=checkpoints)
    return rec


def run_ga(kernel,inc,quality,seed,budget):
    st=time.perf_counter()
    result=eng.run_search(items=kernel.ids,incumbents=inc,
                          objective=kernel.score,seed=seed,config=BASE,
                          max_evaluations=budget,quality=quality,
                          checkpoints=(20000,50000,100000),folder=None)
    s=result["state"]
    assert s["expensive_calls"]==budget and len(result["cache"])==budget
    b=result["best_sequence"]
    obj=-float(result["best_fitness"])
    assert abs(obj+kernel.score(b))<1e-9
    return dict(method="ga_baseline",seed=seed,budget=budget,
       distinct_evaluations=len(result["cache"]),
       attempted_evaluations=int(s["attempts"]),
       search_best_loss_hr=obj,
       best_sequence=list(b),sequence_sha256=old.identity(b),
       completed_budget=True,elapsed_wall_seconds=time.perf_counter()-st,
       generation0_loss_hr=-float(result["history"].iloc[0]["generation_best"]),
       actual_generations=int(s["generation"]),
       checkpoints=[dict(evaluations=int(q["distinct_evaluations"]),
                         loss_hr=float(q["best_service_loss_hr"]))
                    for q in result["budget_rows"]],
       strict_improvements=[dict(evaluation=int(v["distinct_evaluations"]),
              best_loss_hr=float(v["service_loss_hr"]))
              for v in result["state"].get("best_path",[])])


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--budget",type=int,default=BUDGET)
    a=p.parse_args()
    assert a.seed in SEEDS and a.budget==BUDGET
    kernel,inc,quality,_=load()
    folder=OUT/f"seed_{a.seed}"
    folder.mkdir(parents=True,exist_ok=True)
    report=[]
    for method in METHODS:
        row=run_ga(kernel,inc,quality,a.seed,a.budget) if method=="ga_baseline" else local_search(kernel,inc,quality,method,a.seed,a.budget)
        row.update(original_input_commit=SOURCE,planning_realizations=64,
                   fresh_physical_samples=0,formal_policy_changed=False)
        report.append(row)
        (folder/(method+".json")).write_text(json.dumps(row,indent=2)+"\n",encoding="utf-8")
        print("ALTERNATIVE_RESULT",json.dumps({k:row[k] for k in (
            "method","seed","budget","search_best_loss_hr",
            "attempted_evaluations","elapsed_wall_seconds","sequence_sha256")}),flush=True)
    (folder/"ALL_METHODS.json").write_text(
        json.dumps(dict(status="COMPLETE",seed=a.seed,budget=a.budget,
                        methods=report,no_validation_samples=True),indent=2)+"\n")
    print("ALTERNATIVE_SEED_COMPLETE",a.seed,flush=True)

if __name__=="__main__":
    main()
