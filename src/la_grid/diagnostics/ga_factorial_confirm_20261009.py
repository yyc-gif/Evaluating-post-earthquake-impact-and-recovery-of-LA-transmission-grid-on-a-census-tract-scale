"""Preselected 100k follow-up: interaction and no-prior controls.

These cases were fixed before reading the 12-seed 20k screen, not chosen
because one short-budget run had a low score. No new physical realizations.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from la_grid.diagnostics.ga_factorial_research_20261009 import CASES, run_case
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.paths import REPO_ROOT

OUT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"/"factorial_confirm_100k"
SEEDS=tuple(range(400,420))
BUDGET=100000
METHODS=(
    "p100_k3_m10_nquarter",
    "p100_k5_m10_nquarter",
    "p100_k3_m20_nquarter",
    "p100_k5_m20_nquarter",
    "p100_k3_m10_nnone",
    "p100_k5_m10_nnone",
    "p50_k3_m10_nquarter",
    "p50_k5_m10_nquarter",
    "heuristic_only_no_quality",
    "impact_only_archive_no_quality",
    "random_only_archive_no_quality",
)
assert len(METHODS)==11 and len(set(METHODS))==11
assert all(k in CASES for k in METHODS)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--budget",type=int,default=BUDGET)
    a=p.parse_args()
    assert a.seed in SEEDS and a.budget==BUDGET
    kernel,inc,quality,_=load()
    folder=OUT/f"seed_{a.seed}"
    folder.mkdir(parents=True,exist_ok=True)
    cases=[]
    for k in METHODS:
        r=run_case(kernel,inc,quality,a.seed,k,CASES[k],a.budget)
        cases.append(r)
        (folder/(k+".json")).write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
        print("FACTOR_CONFIRM",json.dumps(dict(case=k,seed=a.seed,
             final_loss_hr=r["final_loss_hr"],attempts=r["attempts"],
             expensive_calls=r["expensive_calls"],
             sequence_sha256=r["sequence_sha256"])),flush=True)
    (folder/"ALL_CASES.json").write_text(
        json.dumps(dict(status="COMPLETE",seed=a.seed,budget=a.budget,
             cases=cases,physical_sampling=False,formal_policy_replaced=False),
             indent=2)+"\n",encoding="utf-8")
    print("FACTOR_CONFIRM_SEED_COMPLETE",a.seed,flush=True)

if __name__=="__main__": main()
