"""Independent-GA-seed replication of initialization allocation choices.

DIAGNOSTIC ONLY: fixed existing 64 2pc50 planning realizations and exact score,
no new physical draws, no formal strategy replacement, no validation selection.
The original GA engine and chromosome/scheduler/objective implementations are
unchanged. Each process runs one independent GA seed across 17 controlled setups.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np

from la_grid.diagnostics import ga_variant_engine as eng
from la_grid.diagnostics.ga_init_param_20261009 import BASE, load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.paths import REPO_ROOT

OUT = REPO_ROOT / "results/diagnostics/ga_initialization_replication_20261009"
SOURCE_COMMIT = "b1030f839d522fed4af21e424472e3f8b076797b"

# Fixed, announced before reading these new (100..129) GA random-seed results.
# h: seeded incumbent heuristic count; w: exact prior-GA-best copies; n:
# inversion-neighbor count; source: share of neighbors derived from prior GA.
# Baseline = 7 heuristics, 1 prior best, 13 prior neighbors, 12 impact
# neighbors, and 67 new random full permutations (population=100).
CASES = {
    "baseline_7h_1w_25n": (7, 1, 25, "split"),
    "heuristics_0": (0, 1, 25, "split"),
    "heuristics_1_impact": (1, 1, 25, "split"),
    "heuristics_3_top": (3, 1, 25, "split"),
    "heuristics_6_no_fixed_random": (6, 1, 25, "split"),
    "warm_copies_0": (7, 0, 25, "split"),
    "warm_copies_3": (7, 3, 25, "split"),
    "warm_copies_5": (7, 5, 25, "split"),
    "neighbors_0": (7, 1, 0, "split"),
    "neighbors_10": (7, 1, 10, "split"),
    "neighbors_50": (7, 1, 50, "split"),
    "neighbors_75": (7, 1, 75, "split"),
    "neighbors_25_prior_only": (7, 1, 25, "prior"),
    "neighbors_25_impact_only": (7, 1, 25, "impact"),
    "neighbors_25_prior_25pct": (7, 1, 25, "prior25"),
    "neighbors_25_prior_75pct": (7, 1, 25, "prior75"),
    "heuristics_only": (7, 0, 0, "split"),
}
assert len(CASES) == 17
HEURISTICS_TOP3 = ("impact-first", "hospital-first", "closeness-first")


def neighbor_prior_positions(n: int, source: str) -> set[int]:
    if source == "prior":
        return set(range(n))
    if source == "impact":
        return set()
    if source == "split":
        return set(range(0, n, 2))
    if source in ("prior25", "prior75"):
        fraction = .25 if source == "prior25" else .75
        selected = round(n * fraction)
        # Spread indices across the full draw sequence, not bunched at front.
        return {int((i + .5) * n / selected) for i in range(selected)}
    raise ValueError(source)


def initial_population(spec, domain, incumbents, quality, seed):
    h, w, n, source = spec
    rng = random.Random(seed)
    if h == 7:
        init = list(incumbents.values())
    elif h == 6:
        init = [seq for label, seq in incumbents.items() if label != "random"]
    elif h == 3:
        init = [incumbents[k] for k in HEURISTICS_TOP3]
    elif h == 1:
        init = [incumbents["impact-first"]]
    elif h == 0:
        init = []
    else:
        raise ValueError(h)
    init = [tuple(seq) for seq in init]
    init.extend([tuple(quality)] * w)
    priors = neighbor_prior_positions(n, source)
    assert len(priors) <= n
    for j in range(n):
        parent = quality if j in priors else incumbents["impact-first"]
        init.append(eng.mutation(tuple(parent), rng, "inversion"))
    random_count = BASE.population - len(init)
    assert random_count >= 0
    for _ in range(random_count):
        init.append(tuple(rng.sample(domain, len(domain))))
    assert len(init) == BASE.population
    assert all(len(x) == len(domain) and set(x) == set(domain) for x in init)
    assert random_count == BASE.population - h - w - n
    return init, {"heuristic_count":h,"warm_copy_count":w,"neighbor_count":n,
                  "prior_neighbor_count":len(priors),
                  "impact_neighbor_count":n-len(priors),
                  "random_count":random_count,
                  "actual_unique_chromosomes":len(set(init)),
                  "actual_duplicate_chromosomes":len(init)-len(set(init)),
                  "initial_population_sha256":hashlib.sha256(
                      ("\n".join("|".join(x) for x in init)+"\n").encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--budget", type=int, default=20000)
    a = parser.parse_args()
    assert 100 <= a.seed <= 129
    assert a.budget == 20000
    kernel, inc, quality, identity = load()
    rng_domain = tuple(str(x) for x in kernel.ids)
    inc = {str(k): tuple(v) for k, v in inc.items()}
    original_initializer = eng.initialize
    records = []
    folder = OUT / ("seed_" + str(a.seed))
    folder.mkdir(parents=True, exist_ok=True)

    for case, spec in CASES.items():
        init, comp = initial_population(spec, rng_domain, inc, quality, a.seed)
        if case == "baseline_7h_1w_25n":
            # The 17-config replication baseline must reproduce the actual
            # frozen initializer exactly for this RNG seed.
            stock = original_initializer(
                rng_domain, inc, random.Random(a.seed), BASE, quality)
            assert init == stock, "New baseline differs from frozen engine"
        def initializer(domain, incumbents, rng, config, prior):
            assert tuple(domain) == rng_domain and config == BASE
            assert tuple(prior) == tuple(quality)
            assert list(incumbents) == list(inc)
            # Generate from the RNG carried by run_search, not another seed.
            # This is equivalent to the independently checked population above.
            h, w, n, source = spec
            if h == 7:
                result = list(incumbents.values())
            elif h == 6:
                result = [x for k, x in incumbents.items() if k != "random"]
            elif h == 3:
                result = [incumbents[k] for k in HEURISTICS_TOP3]
            elif h == 1:
                result = [incumbents["impact-first"]]
            else:
                result = []
            result = [tuple(x) for x in result] + [tuple(prior)] * w
            positions = neighbor_prior_positions(n, source)
            for j in range(n):
                parent = prior if j in positions else incumbents["impact-first"]
                result.append(eng.mutation(tuple(parent), rng, "inversion"))
            while len(result) < config.population:
                result.append(tuple(rng.sample(domain, len(domain))))
            return result
        try:
            eng.initialize = initializer
            started = time.perf_counter()
            result = eng.run_search(
                items=kernel.ids, incumbents=inc, objective=kernel.score,
                seed=a.seed, config=BASE, max_evaluations=a.budget,
                checkpoints=(a.budget,), folder=None, quality=quality)
            seconds = time.perf_counter() - started
        finally:
            eng.initialize = original_initializer
        first = result["history"].iloc[0]
        assert int(first["unique_population"]) == comp["actual_unique_chromosomes"]
        assert result["state"]["expensive_calls"] == a.budget
        final = -float(result["best_fitness"])
        initial = -float(first["generation_best"])
        assert final <= initial + 1e-9 or case in ("heuristics_0",)
        row = dict(
            case=case, seed=a.seed, distinct_evaluation_budget=a.budget,
            initial_best_loss_hr=initial,
            generation0_population_mean_loss_hr=float(first["population_mean_service_loss_hr"]),
            generation0_positional_entropy=float(first["position_entropy"]),
            final_best_loss_hr=final,
            postinitialization_gain_hr=initial-final,
            total_attempted_evaluations=int(result["state"]["attempts"]),
            distinct_evaluations=len(result["cache"]),
            actual_generations=int(result["state"]["generation"]),
            elapsed_wall_seconds=seconds,
            selected_sequence_sha256=old.identity(result["best_sequence"]),
            **comp,
        )
        records.append(row)
        (folder / (case + ".json")).write_text(
            json.dumps(row, indent=2)+"\n", encoding="utf-8")
        print("CASE_RESULT", json.dumps(row, sort_keys=True), flush=True)

    assert len(records) == len(CASES)
    report = dict(status="COMPLETED", base_commit=SOURCE_COMMIT,
                  seed=a.seed,budget=a.budget,planning_realizations=64,
                  physical_sampling=False, formal_policy_replaced=False,
                  cases=records)
    (folder / "ALL_CASES.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("SEED_COMPLETE", a.seed, len(records), flush=True)


if __name__ == "__main__":
    main()
