"""Diagnostic-only initialization ablation and GA hyperparameter screening.

Use the pinned 64-realization planning objective; never generate physical samples,
change formal strategies, or reselect using the exploratory evaluation cohort.
The published GA engine is left unchanged. A per-run initializer is installed only
in this dedicated diagnostic process; run_search and score are unmodified.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
import argparse
import csv
import hashlib
import json
import random
import time

import numpy as np

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics import ga_variant_engine as eng
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.diagnostics.ga_variant_engine import Variant

BASE_COMMIT = "b1030f839d522fed4af21e424472e3f8b076797b"
SOURCE = REPO_ROOT / "results/diagnostics/extended_ga_20261008/p100_g2000_s46/RUN.json"
BASE = Variant(
    population=100, crossover=.8, mutation=.1, tournament=3,
    elites=1, initialization="quality_mix",
    mutation_operator="swap", crossover_operator="ordered",
    adaptive=False, restart=False, diversity_replacement=False,
)
INIT_CASES = {
    "baseline": dict(n=25, parents="split", warm=True),
    "no_warm_no_neighbors": dict(n=0, parents="split", warm=False),
    "warm_only": dict(n=0, parents="split", warm=True),
    "neighbors_without_warm": dict(n=25, parents="split", warm=False),
    "neighbor10_split": dict(n=10, parents="split", warm=True),
    "neighbor50_split": dict(n=50, parents="split", warm=True),
    "neighbor75_split": dict(n=75, parents="split", warm=True),
    "neighbor25_prior": dict(n=25, parents="prior", warm=True),
    "neighbor25_impact": dict(n=25, parents="impact", warm=True),
}
PARAM_CASES = {
    "baseline": {},
    "crossover060": {"crossover": .6},
    "crossover095": {"crossover": .95},
    "mutation005": {"mutation": .05},
    "mutation020": {"mutation": .2},
    "tournament2": {"tournament": 2},
    "tournament5": {"tournament": 5},
    "population50": {"population": 50},
    "population250": {"population": 250},
}
OUT = REPO_ROOT / "results/diagnostics/ga_parameter_followup_20261009"

def load():
    kernel, incumbents, identity = old.load_inputs()
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    quality = tuple(source["retained_sequence"])
    assert old.identity(quality) == "3bfeafdd1adf950749e63fdbbe3b7efc21b1efd04c3b3d64c28c3d118717bbed"
    assert abs(kernel.score(quality) + 33.03813174326729) < 1e-9
    return kernel, incumbents, quality, identity

def make_initializer(spec, original):
    """Change ONLY initializer, preserving algorithm operators/RNG conventions."""
    def initializer(domain, inc, rng, config, quality):
        if spec is None:
            return original(domain, inc, rng, config, quality)
        base = list(inc.values())
        if spec["warm"]:
            base.append(tuple(quality))
        n = spec["n"]
        if n == "quarter":
            n = max(1, config.population // 4)
        for j in range(n):
            if spec["parents"] == "prior":
                parent = tuple(quality)
            elif spec["parents"] == "impact":
                parent = tuple(inc["impact-first"])
            else:
                parent = tuple(quality if j % 2 == 0 else inc["impact-first"])
            base.append(eng.mutation(parent, rng, "inversion"))
        if len(base) > config.population:
            raise ValueError("Initialization exceeds population")
        while len(base) < config.population:
            base.append(tuple(rng.sample(domain, len(domain))))
        return base
    return initializer

def run_case(kernel,inc,quality,identity,phase,name,seed,budget):
    config = BASE if phase == "initialization" else replace(BASE, **PARAM_CASES[name])
    if phase == "initialization":
        spec = INIT_CASES[name]
    else:
        spec = None if name == "baseline" else dict(n="quarter", parents="split", warm=True)
    original = eng.initialize
    try:
        eng.initialize = make_initializer(spec if phase == "initialization" and name != "baseline" else None, original)
        # Population-size variants retain the original 25%-neighbor rule.
        started = time.perf_counter()
        result = eng.run_search(
            items=kernel.ids, incumbents=inc, objective=kernel.score,
            seed=seed, config=config, max_evaluations=budget,
            checkpoints=(budget,), folder=None, quality=quality,
        )
        elapsed = time.perf_counter() - started
    finally:
        eng.initialize = original
    history = result["history"]
    assert len(history) >= 1 and int(result["state"]["generation"]) > 0
    first = history.iloc[0]
    initial = -float(first["generation_best"])
    final = -float(result["best_fitness"])
    assert final <= initial + 1e-10
    assert result["state"]["expensive_calls"] == budget
    sample = dict(
        source_commit=BASE_COMMIT, phase=phase, case=name, seed=seed,
        budget=budget, population=config.population,
        n_neighbors=(max(1,config.population//4) if phase=="parameters"
                     else INIT_CASES[name]["n"]),
        includes_warm=(True if phase=="parameters" else INIT_CASES[name]["warm"]),
        initial_best_loss_hr=initial, final_best_loss_hr=final,
        search_improvement_hr=initial-final,
        initial_mean_loss_hr=float(first["population_mean_service_loss_hr"]),
        initial_unique_population=int(first["unique_population"]),
        initial_positional_entropy=float(first["position_entropy"]),
        final_generation=int(result["state"]["generation"]),
        expensive_evaluations=result["state"]["expensive_calls"],
        total_attempts=result["state"]["attempts"],
        duplicates=result["state"]["attempts"]-len(result["cache"]),
        elapsed_seconds=elapsed,
        sequence_sha256=old.identity(result["best_sequence"]),
        no_physical_sampling=True,
    )
    assert abs(kernel.score(result["best_sequence"]) + final)<1e-9
    return sample

def output_records(rows,phase,seed,budget):
    OUT.mkdir(parents=True,exist_ok=True)
    stem=f"{phase}_s{seed}_budget{budget}"
    target=OUT/(stem+".csv")
    with target.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT/(stem+".json")).write_text(json.dumps(
        dict(base_commit=BASE_COMMIT,phase=phase,seed=seed,budget=budget,
             cases=rows),indent=2)+"\n",encoding="utf-8")
    print("PHASE_COMPLETE",phase,"seed",seed,"budget",budget,"results",target,flush=True)
    for r in rows:
        print("CASE_RESULT",json.dumps(r,sort_keys=True),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--budget",type=int,default=20000)
    p.add_argument("--phase",choices=("initialization","parameters"),required=True)
    a=p.parse_args()
    kernel,inc,quality,identity=load()
    cases=INIT_CASES if a.phase=="initialization" else PARAM_CASES
    rows=[]
    for case in cases:
        row=run_case(kernel,inc,quality,identity,a.phase,case,a.seed,a.budget)
        rows.append(row)
        print("DONE",a.phase,case,a.seed,round(row["final_best_loss_hr"],10),
              round(row["search_improvement_hr"],10),flush=True)
    output_records(rows,a.phase,a.seed,a.budget)

if __name__=="__main__":
    main()
