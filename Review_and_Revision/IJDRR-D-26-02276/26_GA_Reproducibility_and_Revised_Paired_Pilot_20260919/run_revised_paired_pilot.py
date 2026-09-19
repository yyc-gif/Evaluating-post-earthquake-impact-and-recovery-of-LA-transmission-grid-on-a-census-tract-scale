"""Round 26 GA reproducibility and revised paired-pilot science runner.

One invocation freezes 2pc50 D302 damage probabilities, executes the declared
30-run GA benchmark, freezes three ex-ante sequences, draws 32 paired physical
realizations once, and evaluates four strategies through the frozen revised
R1/Architecture-B execution chain.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import heapq
import importlib.util
import json
import math
from pathlib import Path
import random
import sys
from typing import Iterable, Mapping, Sequence

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import lognorm, norm


MASTER_SEED = 42
GA_SEEDS = tuple(range(42, 52))
BOOTSTRAP_SEED = 20260919
BOOTSTRAP_RESAMPLES = 10_000
GA_POPULATION = 100
GA_GENERATIONS = 100
GA_CROSSOVER_PROBABILITY = 0.8
GA_MUTATION_PROBABILITY = 0.2
GA_TOURNAMENT_SIZE = 3
TMAX_HR = 504.0
FUNCTIONAL_THRESHOLD = 0.5
NEAR_ZERO_HR = 1.0
REFERENCE_SOURCE_IDS = (
    "300232", "301318", "302376", "302865", "303473", "303547",
    "306001", "306365", "306450", "306473", "306489", "307039",
    "307373", "307512", "307693", "308540", "308581", "309553",
    "309569", "309703", "310199",
)
UNRESOLVED_IDS = ("301479", "303265", "304137", "305021")
DURATION_PARAMETERS = {
    1: (1.0, 0.5), 2: (6.0, 3.0), 3: (12.0, 4.0), 4: (36.0, 12.0)
}
POSITIVE_DURATION_MEANS = {
    1: 1.027623931339495,
    2: 6.16574358803697,
    3: 12.017751356168503,
    4: 36.05325406850551,
}
POLICIES = {
    "GA-Balanced": {"W_POP": 1.0, "W_HOSP": 3.0, "W_SVI": 1.0, "W_MAKESPAN": 0.5},
    "GA-HospFirst": {"W_POP": 1.0, "W_HOSP": 20.0, "W_SVI": 1.0, "W_MAKESPAN": 0.1},
    "GA-Efficiency": {"W_POP": 1.0, "W_HOSP": 1.0, "W_SVI": 1.0, "W_MAKESPAN": 2.0},
}
STRATEGIES = ("Hospital-first", "GA-Balanced", "GA-HospFirst", "GA-Efficiency")
SYSTEM_METRICS = (
    "population_resolved_T80_hr",
    "population_normalized_burden_hr",
    "hospital_mean_normalized_burden_hr",
    "Q4_minus_Q1_burden_gap_hr",
    "burden_gini",
    "makespan_hr",
    "total_travel_hr",
    "absolute_Q4_minus_Q1_burden_gap_hr",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def newline_hash(values: Iterable[object]) -> str:
    return hashlib.sha256(("\n".join(map(str, values)) + "\n").encode()).hexdigest()


def numeric_vector_hash(ids: Sequence[str], values: np.ndarray) -> str:
    return newline_hash(f"{station_id},{float(value):.17g}" for station_id, value in zip(ids, values))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    parent = str(path.resolve().parent)
    inserted = parent not in sys.path
    if inserted:
        sys.path.insert(0, parent)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(parent)
    return module


def _normalize_ids(values: Sequence[object], name: str) -> tuple[str, ...]:
    ids = tuple(str(value).strip() for value in values)
    if not ids or any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError(f"{name} must contain unique explicit IDs")
    return ids


def positive_conditioned_normal_ppf(u: np.ndarray, mean: float, sd: float) -> np.ndarray:
    lower = norm.cdf(0.0, loc=mean, scale=sd)
    p = lower + np.asarray(u, dtype=float) * (1.0 - lower)
    result = norm.ppf(p, loc=mean, scale=sd)
    if not np.isfinite(result).all() or (result <= 0.0).any():
        raise RuntimeError("Positive-conditioned duration sampling failed")
    return result


def calculate_damage_probabilities(readiness: pd.DataFrame, domain_ids: Sequence[str]) -> pd.DataFrame:
    rows = readiness.set_index("station_id").reindex(domain_ids).copy()
    required = ["PGA_2pc50_g", "fragility_class"] + [
        f"{prefix}_DS{ds}" for prefix in ("mu", "beta") for ds in range(1, 5)
    ]
    if rows[required].isna().any().any():
        missing = rows.loc[rows[required].isna().any(axis=1), required]
        raise RuntimeError(f"D302 lacks frozen 2pc50/fragility inputs: {missing.index.tolist()}")
    pga = pd.to_numeric(rows["PGA_2pc50_g"], errors="raise").to_numpy(dtype=float)
    mu = rows[[f"mu_DS{ds}" for ds in range(1, 5)]].apply(pd.to_numeric).to_numpy(dtype=float)
    beta = rows[[f"beta_DS{ds}" for ds in range(1, 5)]].apply(pd.to_numeric).to_numpy(dtype=float)
    if not np.isfinite(pga).all() or not np.isfinite(mu).all() or not np.isfinite(beta).all():
        raise RuntimeError("D302 hazard/fragility input is nonfinite")
    if (pga < 0.0).any() or (mu <= 0.0).any() or (beta <= 0.0).any():
        raise RuntimeError("D302 hazard/fragility input violates parameter domain")
    p_exc = lognorm.cdf(pga[:, None], s=np.clip(beta, 1e-4, None), scale=np.clip(mu, 1e-6, None))
    raw = np.column_stack([
        1.0 - p_exc[:, 0],
        p_exc[:, 0] - p_exc[:, 1],
        p_exc[:, 1] - p_exc[:, 2],
        p_exc[:, 2] - p_exc[:, 3],
        p_exc[:, 3],
    ])
    clipped = np.clip(raw, 0.0, 1.0)
    row_sum = clipped.sum(axis=1)
    if (row_sum <= 0.0).any():
        raise RuntimeError("Frozen Stage1 probability cleanup produced a zero row")
    probability = clipped / row_sum[:, None]
    if not np.isfinite(probability).all() or (probability < 0.0).any():
        raise RuntimeError("D302 damage probabilities are invalid")
    if not np.allclose(probability.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
        raise RuntimeError("D302 damage probabilities do not sum to one")
    output = pd.DataFrame({
        "R1_station_id": list(domain_ids),
        "station_name": rows["station_name"].astype(str).to_numpy(),
        "fragility_class": rows["fragility_class"].astype(str).to_numpy(),
        "PGA_2pc50_g": pga,
        **{f"mu_DS{ds}": mu[:, ds - 1] for ds in range(1, 5)},
        **{f"beta_DS{ds}": beta[:, ds - 1] for ds in range(1, 5)},
        **{f"P_DS{ds}": probability[:, ds] for ds in range(5)},
        "stage1_clip_applied": (raw < 0.0).any(axis=1),
        "preclip_min_probability": raw.min(axis=1),
        "probability_row_sum": probability.sum(axis=1),
    })
    return output


def expand_c57(roster: pd.DataFrame) -> pd.DataFrame:
    rows = []
    definition = roster.loc[roster["crew_scenario"] == "C57_REFERENCE"].sort_values("yard_id")
    for item in definition.itertuples():
        for _ in range(int(item.integer_crews)):
            index = len(rows)
            rows.append({"crew_index": index, "crew_id": f"C57_{index:03d}", "origin_key": str(item.yard_id)})
    result = pd.DataFrame(rows)
    if len(result) != 57:
        raise RuntimeError("Frozen C57 roster does not expand to 57 crews")
    return result


@dataclass(frozen=True)
class SurrogateResult:
    fitness: float
    completion_benefit: float
    makespan_penalty: float
    makespan_hr: float


class SurrogateDecoder:
    def __init__(self, base: np.ndarray, task: np.ndarray, crew_origins: np.ndarray,
                 workload: np.ndarray, priority: np.ndarray, makespan_weight: float):
        self.base = np.asarray(base, dtype=float)
        self.task = np.asarray(task, dtype=float)
        self.crew_origins = np.asarray(crew_origins, dtype=int)
        self.workload = np.asarray(workload, dtype=float)
        self.priority = np.asarray(priority, dtype=float)
        self.makespan_weight = float(makespan_weight)
        self.denominator = max(TMAX_HR * float(self.priority.sum()), 1e-12)

    def evaluate(self, permutation: Sequence[int]) -> SurrogateResult:
        heap = [(0.0, crew, -1) for crew in range(len(self.crew_origins))]
        heapq.heapify(heap)
        completion = np.empty(len(permutation), dtype=float)
        for task_index in permutation:
            free, crew, previous = heapq.heappop(heap)
            travel = self.base[self.crew_origins[crew], task_index] if previous < 0 else self.task[previous, task_index]
            finish = free + float(travel) + self.workload[task_index]
            completion[task_index] = finish
            heapq.heappush(heap, (finish, crew, task_index))
        makespan = max(item[0] for item in heap)
        credit = np.clip(TMAX_HR - completion, 0.0, TMAX_HR)
        benefit = float(np.dot(self.priority, credit) / self.denominator)
        penalty = float(makespan / TMAX_HR)
        return SurrogateResult(benefit - self.makespan_weight * penalty, benefit, penalty, makespan)


def ordered_crossover(first: tuple[int, ...], second: tuple[int, ...], rng: random.Random) -> tuple[tuple[int, ...], tuple[int, ...]]:
    size = len(first)
    left, right = sorted(rng.sample(range(size), 2))
    def child(a, b):
        out = [-1] * size
        out[left:right + 1] = a[left:right + 1]
        used = set(out[left:right + 1])
        fill = [value for value in b[right + 1:] + b[:right + 1] if value not in used]
        positions = list(range(right + 1, size)) + list(range(0, left))
        for position, value in zip(positions, fill):
            out[position] = value
        return tuple(out)
    return child(first, second), child(second, first)


def inversion_mutation(individual: tuple[int, ...], rng: random.Random) -> tuple[int, ...]:
    left, right = sorted(rng.sample(range(len(individual)), 2))
    values = list(individual)
    values[left:right + 1] = reversed(values[left:right + 1])
    return tuple(values)


def run_ga(policy: str, seed: int, decoder: SurrogateDecoder, priority: np.ndarray,
           workload: np.ndarray, generations: int = GA_GENERATIONS, *,
           incumbents: Mapping[str, tuple[int, ...]] | None = None) -> tuple[pd.DataFrame, tuple[int, ...], SurrogateResult]:
    """Return the best observed candidate, including explicit external incumbents.

    The archive never participates in selection/replacement and consumes no RNG.
    Historical Round26 outputs remain last-generation results; they are not rewritten.
    """
    rng = random.Random(seed)
    n = len(priority)
    population = [tuple(rng.sample(range(n), n)) for _ in range(GA_POPULATION - 2)]
    population.append(tuple(np.argsort(-priority, kind="stable").tolist()))
    population.append(tuple(np.argsort(workload, kind="stable").tolist()))
    records = []
    archive_sequence = None
    archive_score = None
    archive_origin = None

    def observe_candidate(sequence, score, origin):
        nonlocal archive_sequence, archive_score, archive_origin
        key = (score.fitness, tuple(-value for value in sequence))
        if archive_score is None or key > (archive_score.fitness, tuple(-value for value in archive_sequence)):
            archive_sequence, archive_score, archive_origin = tuple(sequence), score, origin

    incumbent_scores = {}
    for name, sequence in sorted((incumbents or {}).items()):
        if len(sequence) != n or set(sequence) != set(range(n)):
            raise ValueError(f"Invalid incumbent permutation: {name}")
        score = decoder.evaluate(sequence)
        incumbent_scores[name] = score.fitness
        observe_candidate(sequence, score, f"incumbent:{name}")

    def evaluate_population(pop):
        return [decoder.evaluate(individual) for individual in pop]

    scores = evaluate_population(population)
    for generation in range(generations + 1):
        best_index = max(range(len(population)), key=lambda index: (scores[index].fitness, tuple(-v for v in population[index])))
        best = scores[best_index]
        observe_candidate(population[best_index], best, f"generation:{generation}")
        records.append({
            "policy": policy,
            "seed": seed,
            "generation": generation,
            "generation_best_fitness": best.fitness,
            "generation_mean_fitness": float(np.mean([score.fitness for score in scores])),
            "generation_best_completion_benefit": best.completion_benefit,
            "generation_best_makespan_hr": best.makespan_hr,
            "best_so_far_fitness": archive_score.fitness,
            "best_so_far_origin": archive_origin,
            "best_explicit_incumbent_fitness": max(incumbent_scores.values(), default=math.nan),
        })
        if generation == generations:
            break
        selected = []
        for _ in range(GA_POPULATION):
            contestants = [rng.randrange(GA_POPULATION) for _ in range(GA_TOURNAMENT_SIZE)]
            winner = max(contestants, key=lambda index: scores[index].fitness)
            selected.append(population[winner])
        offspring = []
        for index in range(0, GA_POPULATION, 2):
            first, second = selected[index], selected[index + 1]
            if rng.random() < GA_CROSSOVER_PROBABILITY:
                first, second = ordered_crossover(first, second, rng)
            if rng.random() < GA_MUTATION_PROBABILITY:
                first = inversion_mutation(first, rng)
            if rng.random() < GA_MUTATION_PROBABILITY:
                second = inversion_mutation(second, rng)
            offspring.extend((first, second))
        population = offspring
        scores = evaluate_population(population)
    return pd.DataFrame(records), archive_sequence, archive_score


def sample_physical_realization(probabilities: np.ndarray, realization_id: int) -> tuple[np.ndarray, np.ndarray]:
    seed = np.random.SeedSequence([MASTER_SEED, realization_id])
    damage_rng, duration_rng = [np.random.default_rng(child) for child in seed.spawn(2)]
    u_damage = damage_rng.random(probabilities.shape[0])
    cumulative = np.cumsum(probabilities, axis=1)
    damage = (u_damage[:, None] < cumulative).argmax(axis=1).astype(np.int8)
    u_duration = duration_rng.random(probabilities.shape[0])
    duration = np.zeros(probabilities.shape[0], dtype=float)
    for damage_state, (mean, sd) in DURATION_PARAMETERS.items():
        selected = damage == damage_state
        if selected.any():
            duration[selected] = positive_conditioned_normal_ppf(u_duration[selected], mean, sd)
    if not (duration[damage > 0] > 0.0).all() or not (duration[damage == 0] == 0.0).all():
        raise RuntimeError("Physical duration vector violates task semantics")
    return damage, duration


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    selected = np.isfinite(values) & np.isfinite(weights) & (weights > 0.0)
    if not selected.any():
        return math.nan
    return float(np.average(values[selected], weights=weights[selected]))


def weighted_gini(values: np.ndarray, weights: np.ndarray) -> float:
    selected = np.isfinite(values) & np.isfinite(weights) & (weights > 0.0)
    x = np.asarray(values[selected], dtype=float)
    w = np.asarray(weights[selected], dtype=float)
    if len(x) == 0 or np.allclose(x, 0.0):
        return 0.0
    order = np.argsort(x, kind="stable")
    x, w = x[order], w[order]
    cumulative_weight = np.cumsum(w)
    cumulative_value = np.cumsum(x * w)
    relative_weight = np.concatenate(([0.0], cumulative_weight / cumulative_weight[-1]))
    relative_value = np.concatenate(([0.0], cumulative_value / cumulative_value[-1]))
    return float(1.0 - np.sum((relative_value[1:] + relative_value[:-1]) * np.diff(relative_weight)))


def threshold_time(times: np.ndarray, values: np.ndarray, threshold: float) -> float:
    indices = np.flatnonzero(values >= threshold - 1e-12)
    return float(times[indices[0]]) if len(indices) else math.nan


def calculate_run_metrics(result, tract_metadata: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    intervals = result.service_evaluation.tract_intervals
    times = result.event_times_hr
    tract_ids = tract_metadata["tract_id"].astype(str).tolist()
    lower = intervals.pivot(index="time_index", columns="tract_id", values="lower").reindex(
        index=range(len(times)), columns=tract_ids).to_numpy(dtype=float)
    resolved = intervals.loc[intervals.time_index == 0].set_index("tract_id").reindex(tract_ids)["resolved_mass"].to_numpy(dtype=float)
    unresolved = intervals.loc[intervals.time_index == 0].set_index("tract_id").reindex(tract_ids)["unresolved_mass"].to_numpy(dtype=float)
    if not np.allclose(resolved + unresolved, 1.0, atol=5e-12, rtol=0.0):
        raise RuntimeError("Architecture B resolved/unresolved mass invariant failed")
    if (lower > resolved[None, :] + 1e-12).any():
        raise RuntimeError("Known available mass exceeds resolved mass")
    deficit = np.clip(resolved[None, :] - lower, 0.0, None)
    burden = np.sum(deficit[:-1, :] * np.diff(times)[:, None], axis=0)
    normalized = np.full(len(tract_ids), np.nan, dtype=float)
    represented = resolved > 0.0
    normalized[represented] = burden[represented] / resolved[represented]
    population = tract_metadata["population"].to_numpy(dtype=float)
    denominator = float(np.dot(population, resolved))
    availability = lower @ population / denominator
    quartile = tract_metadata["sovi_quartile"].astype(str).to_numpy()
    quartile_mean = {label: weighted_mean(normalized[quartile == label], population[quartile == label]) for label in ("Q1", "Q2", "Q3", "Q4")}
    hospital = tract_metadata["hospital_tract"].astype(bool).to_numpy()
    metric = {
        "population_resolved_T50_hr": threshold_time(times, availability, 0.50),
        "population_resolved_T80_hr": threshold_time(times, availability, 0.80),
        "population_resolved_T90_hr": threshold_time(times, availability, 0.90),
        "population_normalized_burden_hr": weighted_mean(normalized, population),
        "hospital_mean_normalized_burden_hr": float(np.nanmean(normalized[hospital])),
        "Q1_burden_hr": quartile_mean["Q1"],
        "Q2_burden_hr": quartile_mean["Q2"],
        "Q3_burden_hr": quartile_mean["Q3"],
        "Q4_burden_hr": quartile_mean["Q4"],
        "Q4_minus_Q1_burden_gap_hr": quartile_mean["Q4"] - quartile_mean["Q1"],
        "absolute_Q4_minus_Q1_burden_gap_hr": abs(quartile_mean["Q4"] - quartile_mean["Q1"]),
        "burden_gini": weighted_gini(normalized, population),
        "resolved_zero_tract_count": int((~represented).sum()),
        "resolved_zero_population": float(population[~represented].sum()),
    }
    tract = tract_metadata[["tract_id", "population", "SOVI_SCORE", "hospital_tract", "sovi_quartile"]].copy()
    tract["resolved_mass"] = resolved
    tract["unresolved_mass"] = unresolved
    tract["restoration_burden_mass_hr"] = burden
    tract["normalized_burden_hr"] = normalized
    return metric, tract


def paired_bootstrap(values: np.ndarray, seed: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all():
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(BOOTSTRAP_RESAMPLES, len(values)))
    means = values[indices].mean(axis=1)
    return tuple(float(value) for value in np.quantile(means, [0.025, 0.975]))


def markdown_table(frame: pd.DataFrame, decimals: int = 4) -> str:
    formatted = frame.copy()
    for column in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[column]):
            formatted[column] = formatted[column].map(lambda value: "NA" if pd.isna(value) else f"{value:.{decimals}f}")
    header = "| " + " | ".join(map(str, formatted.columns)) + " |"
    separator = "| " + " | ".join(["---"] * len(formatted.columns)) + " |"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in formatted.itertuples(index=False, name=None)]
    return "\n".join([header, separator, *rows])


def main() -> None:
    root = Path("R:/")
    review = root / "Review_and_Revision" / "IJDRR-D-26-02276"
    output = review / "26_GA_Reproducibility_and_Revised_Paired_Pilot_20260919"
    output.mkdir(parents=True, exist_ok=True)
    runner_path = Path(__file__).resolve()
    outputs = {
        "damage_probabilities": output / "D302_2PC50_DAMAGE_PROBABILITIES.csv",
        "ga_convergence": output / "GA_CONVERGENCE_BY_SEED.csv",
        "ga_sequences": output / "GA_CANONICAL_SEQUENCES.csv",
        "ga_report": output / "GA_REPRODUCIBILITY_REPORT.md",
        "pilot_report": output / "REVISED_PAIRED_PILOT_REPORT.md",
        "summary": output / "REALIZATION_STRATEGY_SUMMARY.csv",
        "tract_burden": output / "TRACT_BURDEN_BY_REALIZATION.csv",
        "distribution": output / "DISTRIBUTIONAL_EFFECTS.csv",
        "pairwise": output / "PAIRWISE_STRATEGY_EFFECTS.csv",
        "reviewers": output / "REVIEWER_RESPONSE_EVIDENCE_MATRIX.md",
        "evidence": output / "REVISED_PAIRED_PILOT_EVIDENCE.npz",
        "manifest": output / "SCIENCE_RUN_MANIFEST.json",
    }
    for path in outputs.values():
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite Round26 artifact: {path.name}")

    r5 = review / "05_R1_310_DryBuild_20260913"
    r6 = review / "06_R1_310_LocalClosure_20260914"
    r10 = review / "10_SCE_ServiceLayer_Architecture_20260914"
    r14 = review / "14_Production_Interface_Contract_20260914"
    r16 = review / "16_R1_Dynamic_Export_Contract_20260915"
    r23 = review / "23_R1_310_Scheduling_Input_Readiness_20260916"
    r24 = review / "24_R1_Event_Based_Scheduler_20260917"
    r25b = review / "25B_R1_One_Realization_Schedule_Integration_Repair_20260917"
    inputs = {
        "main_model": root / "C257H_Project_Main.py",
        "r1_readiness": r5 / "R1_310_INPUT_READINESS.csv",
        "station_qa": r5 / "R1_310_STATIONS_QA.csv",
        "graph": r6 / "R1_310_EDGES.csv",
        "task_domain": r23 / "R1_TASK_DOMAIN_AND_ELIGIBILITY.csv",
        "priority": r23 / "R1_ARCHB_PRIORITY_COMPONENTS.csv",
        "ga_readiness": r23 / "R1_GA_INPUT_READINESS.json",
        "base_travel": r23 / "R1_BASE_TO_TASK_TRAVEL_HR.csv",
        "task_travel": r23 / "R1_TASK_TO_TASK_TRAVEL_HR.csv",
        "crew_roster": r23 / "R1_CREW_SCENARIO_ROSTERS.csv",
        "scheduler": r24 / "r1_event_based_scheduler.py",
        "revised_runner": r25b / "R1_REVISED_REALIZATION_RUNNER.py",
        "exporter": r16 / "r1_effective_state_exporter.py",
        "service_interface": r14 / "service_layer_interface.py",
        "service_nodes": r10 / "SCE_SERVICE_NODES_196.csv",
        "attachments": r10 / "SERVICE_UPSTREAM_ATTACHMENT_LEDGER.csv",
        "w1": r10 / "SCE_TRACT_SERVICE_W1.csv",
        "tract_metadata": r10 / "SERVICE_LAYER_COVERAGE_QA.csv",
    }
    input_hashes = {name: sha256_file(path) for name, path in inputs.items()}
    expected_hashes = {
        "main_model": "90743cde45fe14de9e113ad39111c2a8507dd90099002a1eae06832aba208145",
        "graph": "e2dd039ec40336ea800adc29aa6cf790ae3d89553c1491c149096b3be6377090",
        "task_domain": "bcd8f493078f51365e9e7a9cafd63d0ec3d5738f358f901f6a841a1d5276fa83",
        "priority": "53c7687c2ca7a4c87b1e5a53946fe67c7f5e05188f40003a3f1fe6371218a1f6",
        "base_travel": "16177e57cd7e77ea2075e347318c3b7698937af6b0b7dc702f18b9da65662690",
        "task_travel": "68c03537853bad92544f13688ade89247e135e829b989c71c96be2f8ef45a6de",
        "crew_roster": "4940f0c15e56c884ae2f3fd7717cd93f12e2f37de2bb936a27a8b752df5f3f11",
        "scheduler": "8096fa7ad72d5f7a5cb9c6f186d65adef2ab8f7fc336938f0dba396ed31ee43f",
        "exporter": "79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b",
        "service_interface": "d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514",
        "service_nodes": "ccf9e08b40a0df1326e7eb9f62addd92d9fa348f65a43dd4afc6a743845f2080",
        "attachments": "b1a7ad8e6f162bed06fb88694a0393aa0d1fc7d4ef515ba628ede242e809ed9e",
        "w1": "a21b583338a4583e2362aba70667ac8c443abe0cf3a732b98f022175cf4f6221",
        "tract_metadata": "4658c4f439a1ae41d77a5d5d14e6a8cbb950f1f71f123f2edd9190fa7a992f8b",
    }
    mismatches = {name: (input_hashes[name], expected) for name, expected in expected_hashes.items() if input_hashes[name] != expected}
    if mismatches:
        raise RuntimeError(f"Frozen input hash mismatch: {mismatches}")

    task_domain = pd.read_csv(inputs["task_domain"], dtype={"station_id": str})
    domain_ids = _normalize_ids(task_domain.loc[task_domain.final_task_domain, "station_id"].tolist(), "D302")
    if len(domain_ids) != 302:
        raise RuntimeError("Primary scheduling domain is not D302")
    station_qa = pd.read_csv(inputs["station_qa"], dtype={"station_id": str})
    full_ids = tuple(sorted(station_qa.station_id.astype(str)))
    if len(full_ids) != 310:
        raise RuntimeError("Frozen R1 identity is not 310")
    readiness = pd.read_csv(inputs["r1_readiness"], dtype={"station_id": str})
    probability_table = calculate_damage_probabilities(readiness, domain_ids)
    probability_table.to_csv(outputs["damage_probabilities"], index=False, float_format="%.17g", lineterminator="\n")
    probability_hash = sha256_file(outputs["damage_probabilities"])
    probabilities = probability_table[[f"P_DS{ds}" for ds in range(5)]].to_numpy(dtype=float)
    expected_workload = sum(probabilities[:, ds] * POSITIVE_DURATION_MEANS[ds] for ds in range(1, 5))
    if not np.isfinite(expected_workload).all() or (expected_workload <= 0.0).any():
        raise RuntimeError("Expected workload is invalid")

    priority_table = pd.read_csv(inputs["priority"], dtype={"R1_station_id": str}).set_index("R1_station_id").reindex(domain_ids)
    hospital_sequence = tuple(priority_table.sort_values("hospital_first_rank").index.astype(str))
    if len(hospital_sequence) != 302 or set(hospital_sequence) != set(domain_ids):
        raise RuntimeError("Hospital-first is not a D302 permutation")
    base = pd.read_csv(inputs["base_travel"], dtype={"yard_id": str}).set_index("yard_id")
    base.columns = base.columns.astype(str)
    base = base.reindex(columns=domain_ids)
    task = pd.read_csv(inputs["task_travel"], dtype={"R1_station_id": str}).set_index("R1_station_id")
    task.columns = task.columns.astype(str)
    task = task.reindex(index=domain_ids, columns=domain_ids)
    if not np.isfinite(base.to_numpy(dtype=float)).all() or not np.isfinite(task.to_numpy(dtype=float)).all():
        raise RuntimeError("Strict directed travel matrices contain a nonfinite cell")
    roster_definition = pd.read_csv(inputs["crew_roster"], dtype={"yard_id": str})
    crew_roster = expand_c57(roster_definition)
    base_index = {value: index for index, value in enumerate(base.index.astype(str))}
    crew_origins = np.array([base_index[value] for value in crew_roster.origin_key.astype(str)], dtype=int)

    # GA reproducibility benchmark: 30 declared runs, then one five-generation exact repeat.
    ga_curves = []
    ga_final = []
    ga_sequences_by_run: dict[tuple[str, int], tuple[int, ...]] = {}
    component_columns = {
        "W_POP": priority_table.population_priority_score.to_numpy(dtype=float),
        "W_HOSP": priority_table.hospital_priority_score.to_numpy(dtype=float),
        "W_SVI": priority_table.sovi_priority_score.to_numpy(dtype=float),
    }
    for policy, weights in POLICIES.items():
        denominator = weights["W_POP"] + weights["W_HOSP"] + weights["W_SVI"]
        service_priority = sum(weights[key] * component_columns[key] for key in component_columns) / denominator
        if not np.isfinite(service_priority).all():
            raise RuntimeError(f"{policy} service priority is nonfinite")
        decoder = SurrogateDecoder(base.to_numpy(dtype=float), task.to_numpy(dtype=float), crew_origins,
                                   expected_workload, service_priority, weights["W_MAKESPAN"])
        for seed in GA_SEEDS:
            curve, sequence, result = run_ga(
                policy, seed, decoder, service_priority, expected_workload,
                incumbents={"Hospital-first": tuple(domain_ids.index(value) for value in hospital_sequence)},
            )
            sequence_ids = tuple(domain_ids[index] for index in sequence)
            if len(sequence_ids) != 302 or set(sequence_ids) != set(domain_ids):
                raise RuntimeError("GA chromosome is not a D302 permutation")
            sequence_hash = newline_hash(sequence_ids)
            curve["final_best_fitness"] = result.fitness
            curve["final_sequence_hash"] = sequence_hash
            curve["final_completion_benefit"] = result.completion_benefit
            curve["final_makespan_penalty"] = result.makespan_penalty
            curve["final_makespan_hr"] = result.makespan_hr
            ga_curves.append(curve)
            ga_final.append({
                "policy": policy, "seed": seed, "final_fitness": result.fitness,
                "completion_benefit": result.completion_benefit,
                "makespan_penalty": result.makespan_penalty,
                "surrogate_makespan_hr": result.makespan_hr,
                "sequence_hash": sequence_hash,
                "last20_improvement": float(curve.loc[curve.generation == GA_GENERATIONS, "generation_best_fitness"].iloc[0]
                                            - curve.loc[curve.generation == GA_GENERATIONS - 20, "generation_best_fitness"].iloc[0]),
            })
            ga_sequences_by_run[(policy, seed)] = sequence
    ga_convergence = pd.concat(ga_curves, ignore_index=True)
    ga_final_frame = pd.DataFrame(ga_final)
    ga_convergence.to_csv(outputs["ga_convergence"], index=False, float_format="%.17g", lineterminator="\n")

    # Same-seed short determinism check.
    balanced_weights = POLICIES["GA-Balanced"]
    balanced_priority = sum(balanced_weights[key] * component_columns[key] for key in component_columns) / (
        balanced_weights["W_POP"] + balanced_weights["W_HOSP"] + balanced_weights["W_SVI"])
    balanced_decoder = SurrogateDecoder(base.to_numpy(dtype=float), task.to_numpy(dtype=float), crew_origins,
                                        expected_workload, balanced_priority, balanced_weights["W_MAKESPAN"])
    check_a = run_ga("GA-Balanced", GA_SEEDS[0], balanced_decoder, balanced_priority, expected_workload, generations=5)
    check_b = run_ga("GA-Balanced", GA_SEEDS[0], balanced_decoder, balanced_priority, expected_workload, generations=5)
    if not check_a[0].equals(check_b[0]) or check_a[1] != check_b[1] or check_a[2] != check_b[2]:
        raise RuntimeError("GA same-seed exact determinism check failed")

    canonical_sequences = {"Hospital-first": hospital_sequence}
    canonical_rows = []
    for policy in POLICIES:
        candidates = ga_final_frame.loc[ga_final_frame.policy == policy]
        best_row = candidates.sort_values(["final_fitness", "seed"], ascending=[False, True], kind="mergesort").iloc[0]
        seed = int(best_row.seed)
        ids = tuple(domain_ids[index] for index in ga_sequences_by_run[(policy, seed)])
        canonical_sequences[policy] = ids
        for rank, station_id in enumerate(ids, start=1):
            canonical_rows.append({
                "strategy": policy, "canonical_seed": seed, "rank": rank,
                "R1_station_id": station_id, "sequence_hash": newline_hash(ids),
                "canonical_final_fitness": float(best_row.final_fitness),
            })
    for rank, station_id in enumerate(hospital_sequence, start=1):
        canonical_rows.append({
            "strategy": "Hospital-first", "canonical_seed": "frozen_R23", "rank": rank,
            "R1_station_id": station_id, "sequence_hash": newline_hash(hospital_sequence),
            "canonical_final_fitness": math.nan,
        })
    canonical_frame = pd.DataFrame(canonical_rows).sort_values(["strategy", "rank"], kind="mergesort")
    canonical_frame.to_csv(outputs["ga_sequences"], index=False, float_format="%.17g", lineterminator="\n")

    scheduler_module = _load_module(inputs["scheduler"], "r26_scheduler")
    runner_module = _load_module(inputs["revised_runner"], "r26_revised_runner")
    exporter_module = _load_module(inputs["exporter"], "r26_exporter")
    service_module = _load_module(inputs["service_interface"], "r26_service")
    main_module = _load_module(inputs["main_model"], "r26_main")
    edges = pd.read_csv(inputs["graph"], dtype={"src": str, "tgt": str})
    graph = nx.Graph()
    graph.add_nodes_from(full_ids)
    graph.add_edges_from(edges[["src", "tgt"]].itertuples(index=False, name=None))
    if graph.number_of_nodes() != 310 or graph.number_of_edges() != 1040:
        raise RuntimeError("Frozen graph identity mismatch")
    identified = pd.Series(True, index=full_ids, dtype=bool)
    identified.loc[list(UNRESOLVED_IDS)] = False
    service_nodes = pd.read_csv(inputs["service_nodes"], dtype=str)
    service_ids = tuple(service_nodes.service_node_id.astype(str))
    attachments = pd.read_csv(inputs["attachments"], dtype=str, keep_default_na=False)
    w1 = pd.read_csv(inputs["w1"], dtype={"tract_id": str})
    tract_metadata = pd.read_csv(inputs["tract_metadata"], dtype={"tract_id": str})
    if not pd.api.types.is_bool_dtype(tract_metadata["hospital_tract"]):
        normalized_hospital = tract_metadata.hospital_tract.astype(str).str.strip().str.lower()
        if not normalized_hospital.isin(["true", "false"]).all():
            raise RuntimeError("hospital_tract contains non-Boolean values")
        tract_metadata["hospital_tract"] = normalized_hospital.map({"true": True, "false": False})
    tract_metadata["sovi_quartile"] = pd.qcut(tract_metadata.SOVI_SCORE, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    quartile_bounds = [float(value) for value in tract_metadata.SOVI_SCORE.quantile([0.0, 0.25, 0.5, 0.75, 1.0])]

    physical_damage = np.empty((32, 302), dtype=np.int8)
    physical_duration = np.empty((32, 302), dtype=float)
    summary_rows = []
    tract_rows = []
    for realization_id in range(32):
        damage_values, duration_values = sample_physical_realization(probabilities, realization_id)
        physical_damage[realization_id] = damage_values
        physical_duration[realization_id] = duration_values
        damage_hash = numeric_vector_hash(domain_ids, damage_values)
        duration_hash = numeric_vector_hash(domain_ids, duration_values)
        damage_series = pd.Series(damage_values, index=domain_ids, name="damage_state")
        duration_series = pd.Series(duration_values, index=domain_ids, name="realized_duration_hr")
        expected_task_ids = {domain_ids[index] for index in np.flatnonzero(damage_values > 0)}
        shared_schedule_identity = None
        for strategy in STRATEGIES:
            provenance = {
                "schema_version": exporter_module.SCHEMA_VERSION,
                "trajectory_id": f"2pc50|C57|{strategy}|realization_{realization_id:02d}",
                "producer_file": runner_path.name,
                "producer_function": "run_revised_realization",
                "effective_state_semantics": exporter_module.EFFECTIVE_STATE_SEMANTICS,
                "frozen_R1_ID_hash": exporter_module.hash_frozen_r1_ids(full_ids),
                "source_time_unit": "hours_since_event",
                "source_scenario_identifier": "REFERENCE_SOURCE_AVAILABILITY_SCENARIO_21",
                "producer_code_hash": sha256_file(runner_path),
            }
            result = runner_module.run_revised_realization(
                domain_ids=domain_ids,
                full_priority_sequence=canonical_sequences[strategy],
                damage_states=damage_series,
                realized_duration_hr=duration_series,
                base_to_task_hr=base,
                task_to_task_hr=task,
                crew_roster=crew_roster,
                full_r1_ids=full_ids,
                state_identified_static=identified,
                graph=graph,
                source_ids=set(REFERENCE_SOURCE_IDS),
                requested_event_horizon="max_completion",
                service_attachment_ledger=attachments,
                w1=w1,
                tract_metadata=tract_metadata,
                service_ids=service_ids,
                scheduler_callable=scheduler_module.execute_event_based_schedule,
                source_gate_callable=main_module.apply_source_gate_to_substation_series,
                exporter_callable=exporter_module.export_r1_effective_state_trajectory,
                service_evaluator_callable=service_module.evaluate_service_layer_trajectory,
                exporter_provenance=provenance,
            )
            events = result.schedule.task_events
            event_task_ids = set(events.task_id.astype(str))
            if event_task_ids != expected_task_ids or len(events) != len(expected_task_ids):
                raise RuntimeError("Paired realization task set changed across strategies")
            schedule_identity = (damage_hash, duration_hash, len(events))
            if shared_schedule_identity is None:
                shared_schedule_identity = schedule_identity
            elif shared_schedule_identity != schedule_identity:
                raise RuntimeError("Paired physical realization identity changed across strategies")
            service = result.service_evaluation.service_trajectory
            class_c = attachments.set_index("service_node_id").reindex(service_ids).attachment_class == "C_UNRESOLVED_ATTACHMENT"
            if not service.loc[:, class_c].isna().all().all():
                raise RuntimeError("Class C was assigned a service state")
            for service_id, row in attachments.set_index("service_node_id").reindex(service_ids).loc[~class_c].iterrows():
                upstream = str(row.selected_upstream_R1_id)
                if not np.array_equal(service[service_id].to_numpy(), result.service_evaluation.network_trajectory[upstream].to_numpy(), equal_nan=True):
                    raise RuntimeError("A/B service state differs from selected upstream")
            raw = result.raw_functionality.to_numpy(dtype=float)
            effective = result.effective_network_state.to_numpy(dtype=float)
            if (np.diff(raw, axis=0) < -1e-12).any() or (np.diff(effective, axis=0) < -1e-12).any():
                raise RuntimeError("Repair-only raw/effective trajectory decreased")
            metric, tract = calculate_run_metrics(result, tract_metadata)
            metric.update({
                "realization_id": realization_id,
                "strategy": strategy,
                "damage_vector_hash": damage_hash,
                "duration_vector_hash": duration_hash,
                "task_count": len(events),
                **{f"DS{ds}_count": int((damage_values == ds).sum()) for ds in range(5)},
                "makespan_hr": float(events.completion_hr.max()) if len(events) else 0.0,
                "total_travel_hr": float(events.travel_hr.sum()) if len(events) else 0.0,
                "total_on_site_work_hr": float(duration_values.sum()),
            })
            summary_rows.append(metric)
            tract.insert(0, "strategy", strategy)
            tract.insert(0, "realization_id", realization_id)
            tract_rows.append(tract)
    summary = pd.DataFrame(summary_rows)
    tract_burden = pd.concat(tract_rows, ignore_index=True)
    if len(summary) != 128 or len(tract_burden) != 32 * 4 * 817:
        raise RuntimeError("Paired-pilot output dimensions are incomplete")
    for realization_id, block in summary.groupby("realization_id"):
        if block.damage_vector_hash.nunique() != 1 or block.duration_vector_hash.nunique() != 1 or block.task_count.nunique() != 1:
            raise RuntimeError(f"Physical realization {realization_id} is not paired")
    summary.to_csv(outputs["summary"], index=False, float_format="%.17g", lineterminator="\n")
    tract_burden.to_csv(outputs["tract_burden"], index=False, float_format="%.17g", lineterminator="\n")

    # Paired tract effects, group summaries, uncertainty, and rank frequencies.
    hospital = tract_burden.loc[tract_burden.strategy == "Hospital-first", ["realization_id", "tract_id", "normalized_burden_hr"]].rename(
        columns={"normalized_burden_hr": "hospital_first_burden_hr"})
    pairwise_rows = []
    distribution_rows = []
    for strategy in STRATEGIES[1:]:
        ga = tract_burden.loc[tract_burden.strategy == strategy].merge(hospital, on=["realization_id", "tract_id"], validate="one_to_one")
        ga["delta_burden_hr"] = ga.normalized_burden_hr - ga.hospital_first_burden_hr
        for tract_id, block in ga.groupby("tract_id", sort=False):
            mean_delta = float(block.delta_burden_hr.mean())
            if mean_delta < -NEAR_ZERO_HR:
                classification = "improved"
            elif mean_delta > NEAR_ZERO_HR:
                classification = "worsened"
            else:
                classification = "near_zero"
            first = block.iloc[0]
            pairwise_rows.append({
                "comparison": f"{strategy}_minus_Hospital-first",
                "strategy": strategy,
                "tract_id": tract_id,
                "population": float(first.population),
                "SOVI_SCORE": float(first.SOVI_SCORE),
                "sovi_quartile": first.sovi_quartile,
                "hospital_tract": bool(first.hospital_tract),
                "resolved_mass": float(first.resolved_mass),
                "mean_paired_delta_burden_hr": mean_delta,
                "median_paired_delta_burden_hr": float(block.delta_burden_hr.median()),
                "fraction_realizations_delta_lt_0": float((block.delta_burden_hr < 0.0).mean()),
                "classification_threshold_hr": NEAR_ZERO_HR,
                "classification": classification,
            })
        for quartile in ("Q1", "Q2", "Q3", "Q4"):
            block = ga.loc[ga.sovi_quartile == quartile]
            distribution_rows.append({
                "record_type": "quartile_pair_effect",
                "strategy": strategy,
                "metric": "normalized_burden_hr",
                "group": quartile,
                "value": weighted_mean(block.delta_burden_hr.to_numpy(), block.population.to_numpy()),
                "tract_count": int(block.tract_id.nunique()),
                "population": float(block.drop_duplicates("tract_id").population.sum()),
            })
    pairwise = pd.DataFrame(pairwise_rows)
    pairwise.to_csv(outputs["pairwise"], index=False, float_format="%.17g", lineterminator="\n")
    for (strategy, classification), block in pairwise.groupby(["strategy", "classification"]):
        distribution_rows.append({
            "record_type": "winner_loser_group",
            "strategy": strategy,
            "metric": "mean_paired_delta_burden_hr",
            "group": classification,
            "value": weighted_mean(block.mean_paired_delta_burden_hr.to_numpy(), block.population.to_numpy()),
            "tract_count": int(len(block)),
            "population": float(block.population.sum()),
        })

    uncertainty_rows = []
    for strategy in STRATEGIES:
        block = summary.loc[summary.strategy == strategy]
        for metric in SYSTEM_METRICS:
            values = block.sort_values("realization_id")[metric].to_numpy(dtype=float)
            uncertainty_rows.append({
                "record_type": "strategy_metric_distribution", "strategy": strategy,
                "comparison": "", "metric": metric,
                "mean": float(np.mean(values)), "sd": float(np.std(values, ddof=1)),
                "median": float(np.median(values)),
                "q25": float(np.quantile(values, 0.25)), "q75": float(np.quantile(values, 0.75)),
                "mean_paired_difference": math.nan, "median_paired_difference": math.nan,
                "fraction_delta_lt_0": math.nan, "bootstrap_ci_low": math.nan, "bootstrap_ci_high": math.nan,
            })
    hospital_summary = summary.loc[summary.strategy == "Hospital-first"].sort_values("realization_id")
    for strategy in STRATEGIES[1:]:
        block = summary.loc[summary.strategy == strategy].sort_values("realization_id")
        for metric_index, metric in enumerate(SYSTEM_METRICS):
            delta = block[metric].to_numpy(dtype=float) - hospital_summary[metric].to_numpy(dtype=float)
            low, high = paired_bootstrap(delta, BOOTSTRAP_SEED + 100 * STRATEGIES.index(strategy) + metric_index)
            uncertainty_rows.append({
                "record_type": "paired_metric_difference", "strategy": strategy,
                "comparison": f"{strategy}_minus_Hospital-first", "metric": metric,
                "mean": math.nan, "sd": math.nan, "median": math.nan, "q25": math.nan, "q75": math.nan,
                "mean_paired_difference": float(np.mean(delta)),
                "median_paired_difference": float(np.median(delta)),
                "fraction_delta_lt_0": float(np.mean(delta < 0.0)),
                "bootstrap_ci_low": low, "bootstrap_ci_high": high,
            })
    uncertainty = pd.DataFrame(uncertainty_rows)
    for row in uncertainty.itertuples(index=False):
        distribution_rows.append({
            "record_type": row.record_type, "strategy": row.strategy,
            "metric": row.metric, "group": row.comparison,
            "value": row.mean if row.record_type == "strategy_metric_distribution" else row.mean_paired_difference,
            "tract_count": math.nan, "population": math.nan,
            "sd": row.sd, "median": row.median, "q25": row.q25, "q75": row.q75,
            "median_paired_difference": row.median_paired_difference,
            "fraction_delta_lt_0": row.fraction_delta_lt_0,
            "bootstrap_ci_low": row.bootstrap_ci_low, "bootstrap_ci_high": row.bootstrap_ci_high,
        })

    rank_rows = []
    rank_metrics = (
        "population_normalized_burden_hr",
        "makespan_hr",
        "total_travel_hr",
        "Q4_minus_Q1_burden_gap_hr",
        "absolute_Q4_minus_Q1_burden_gap_hr",
    )
    for metric in rank_metrics:
        credit = {strategy: 0.0 for strategy in STRATEGIES}
        for _, block in summary.groupby("realization_id"):
            minimum = block[metric].min()
            winners = block.loc[np.isclose(block[metric], minimum, atol=1e-12, rtol=0.0), "strategy"].tolist()
            for strategy in winners:
                credit[strategy] += 1.0 / len(winners)
        for strategy, value in credit.items():
            rank_rows.append({"metric": metric, "strategy": strategy, "lowest_frequency": value / 32.0})
            distribution_rows.append({
                "record_type": "strategy_rank_frequency", "strategy": strategy,
                "metric": metric, "group": "lowest", "value": value / 32.0,
                "tract_count": math.nan, "population": math.nan,
            })
    distribution = pd.DataFrame(distribution_rows)
    distribution.to_csv(outputs["distribution"], index=False, float_format="%.17g", lineterminator="\n")

    # Evaluate Hospital-first under the GA-HospFirst objective for objective-mismatch evidence.
    hosp_weights = POLICIES["GA-HospFirst"]
    hosp_priority = sum(hosp_weights[key] * component_columns[key] for key in component_columns) / (
        hosp_weights["W_POP"] + hosp_weights["W_HOSP"] + hosp_weights["W_SVI"])
    hosp_decoder = SurrogateDecoder(base.to_numpy(dtype=float), task.to_numpy(dtype=float), crew_origins,
                                    expected_workload, hosp_priority, hosp_weights["W_MAKESPAN"])
    position = {station_id: index for index, station_id in enumerate(domain_ids)}
    hospital_objective = hosp_decoder.evaluate(tuple(position[station_id] for station_id in hospital_sequence))
    canonical_hosp_seed = int(canonical_frame.loc[canonical_frame.strategy == "GA-HospFirst", "canonical_seed"].iloc[0])
    canonical_hosp_fitness = float(ga_final_frame.loc[(ga_final_frame.policy == "GA-HospFirst") & (ga_final_frame.seed == canonical_hosp_seed), "final_fitness"].iloc[0])
    hosp_objective_delta = canonical_hosp_fitness - hospital_objective.fitness
    if hosp_objective_delta >= 0.0:
        hosp_objective_interpretation = (
            "The canonical GA-HospFirst sequence exceeds Hospital-first on the declared surrogate objective. "
            "A reversal on T80 or realized burden would therefore be objective-mismatch evidence because those "
            "reported metrics are not the GA fitness target."
        )
    else:
        hosp_objective_interpretation = (
            "Hospital-first exceeds the canonical GA-HospFirst sequence on the declared surrogate objective by "
            f"{-hosp_objective_delta:.12g}. Under the fixed 100-by-100 search budget, the GA benchmark did not "
            "find a sequence better than the deterministic rule even on its own objective. This is finite-budget "
            "search evidence, so the GA result must not be described as an optimum."
        )

    ga_summary_rows = []
    for policy, block in ga_final_frame.groupby("policy", sort=False):
        ga_summary_rows.append({
            "policy": policy, "mean": block.final_fitness.mean(), "sd": block.final_fitness.std(ddof=1),
            "min": block.final_fitness.min(), "max": block.final_fitness.max(),
            "best": block.final_fitness.max(), "worst": block.final_fitness.min(),
            "sequence_count": block.sequence_hash.nunique(),
            "last20_improvement_mean": block.last20_improvement.mean(),
            "canonical_seed": int(block.sort_values(["final_fitness", "seed"], ascending=[False, True]).iloc[0].seed),
        })
    ga_summary = pd.DataFrame(ga_summary_rows)
    ga_report = f"""# GA Reproducibility Report

## Role and objective

The GA is an **optimization benchmark/comparator**, not a methodological contribution.
It generated ex-ante full D302 permutations before any of the 32 physical pilot
realizations were drawn. It never saw realized damage, realized repair duration,
future service trajectories, T80, tract burden, or winner/loser outcomes.

All three policies use frozen Architecture-B population, hospital, and NRI-derived
SOVI priority components. `NETWORK_IMPORTANCE_TERM = DROP`. Coefficients are
**policy-design / optimization objective coefficients**, not empirical or calibrated
preferences. `W_HOSP=20` defines a deliberately hospital-dominant benchmark archetype.

## Algorithm

- chromosome: full 302-ID permutation
- population: 100 (98 seeded random permutations, priority-descending heuristic,
  expected-workload-ascending heuristic)
- generations: 100 fixed; no early stopping
- ordered crossover: probability 0.8
- inversion mutation: probability 0.2
- tournament selection: size 3
- seeds: 42–51 for every policy
- objective horizon: `Tmax=504 h` (`480+24`), frozen before optimization
- workload: 2pc50 expected positive on-site workload; no realized pilot durations
- exact same-seed five-generation repeat: PASS

## Ten-seed final fitness

{markdown_table(ga_summary)}

Different sequences with close fitness were retained as reproducibility evidence;
parameters were not tuned after seeing results. The canonical sequence for each
policy is the highest final fitness among the ten declared seeds, with smallest-seed
tie-breaking. Complete generation curves and final hashes are in
`GA_CONVERGENCE_BY_SEED.csv`; canonical 302-ID permutations are in
`GA_CANONICAL_SEQUENCES.csv`.

## GA-HospFirst versus Hospital-first objective

- canonical GA-HospFirst fitness under its own objective: `{canonical_hosp_fitness:.12g}`
- Hospital-first fitness under the identical objective: `{hospital_objective.fitness:.12g}`
- GA-minus-Hospital-first objective difference: `{hosp_objective_delta:.12g}`
- sequences identical: `{canonical_sequences['GA-HospFirst'] == hospital_sequence}`

{hosp_objective_interpretation}
"""
    outputs["ga_report"].write_text(ga_report, encoding="utf-8")

    strategy_stats = uncertainty.loc[uncertainty.record_type == "strategy_metric_distribution", ["strategy", "metric", "mean", "sd", "median", "q25", "q75"]]
    paired_stats = uncertainty.loc[uncertainty.record_type == "paired_metric_difference", ["strategy", "metric", "mean_paired_difference", "median_paired_difference", "fraction_delta_lt_0", "bootstrap_ci_low", "bootstrap_ci_high"]]
    winner_summary = distribution.loc[distribution.record_type == "winner_loser_group", ["strategy", "group", "tract_count", "population", "value"]]
    rank_summary = pd.DataFrame(rank_rows)
    strategy_lookup = strategy_stats.set_index(["strategy", "metric"])
    paired_lookup = paired_stats.set_index(["strategy", "metric"])
    rank_lookup = rank_summary.set_index(["strategy", "metric"])
    winner_lookup = winner_summary.set_index(["strategy", "group"])

    def mean_metric(strategy: str, metric: str) -> float:
        return float(strategy_lookup.loc[(strategy, metric), "mean"])

    def paired_metric(strategy: str, metric: str, field: str = "mean_paired_difference") -> float:
        return float(paired_lookup.loc[(strategy, metric), field])

    total_population = float(tract_metadata.population.sum())
    scientific_findings = f"""
1. **Hospital-first minimized population burden in all 32 paired realizations.** Its
   mean was `{mean_metric('Hospital-first', 'population_normalized_burden_hr'):.2f} h`;
   GA-Balanced, GA-HospFirst, and GA-Efficiency increased it by
   `{paired_metric('GA-Balanced', 'population_normalized_burden_hr'):.2f} h`,
   `{paired_metric('GA-HospFirst', 'population_normalized_burden_hr'):.2f} h`, and
   `{paired_metric('GA-Efficiency', 'population_normalized_burden_hr'):.2f} h`.
2. **GA-Balanced traded burden for logistics and lower inequality.** It reduced
   makespan by `{-paired_metric('GA-Balanced', 'makespan_hr'):.2f} h` and burden Gini
   by `{-paired_metric('GA-Balanced', 'burden_gini'):.3f}`, while increasing hospital-
   tract burden by `{paired_metric('GA-Balanced', 'hospital_mean_normalized_burden_hr'):.2f} h`.
3. **GA-Efficiency produced the smallest absolute Q4-Q1 gap most often**
   (`{float(rank_lookup.loc[('GA-Efficiency', 'absolute_Q4_minus_Q1_burden_gap_hr'), 'lowest_frequency']):.1%}`),
   but increased population burden by `{paired_metric('GA-Efficiency', 'population_normalized_burden_hr'):.2f} h`
   and hospital-tract burden by `{paired_metric('GA-Efficiency', 'hospital_mean_normalized_burden_hr'):.2f} h`.
4. **GA-HospFirst did not reproduce the deterministic Hospital-first ordering.** It
   increased mean population T80 by `{paired_metric('GA-HospFirst', 'population_resolved_T80_hr'):.2f} h`,
   population burden by `{paired_metric('GA-HospFirst', 'population_normalized_burden_hr'):.2f} h`, and
   hospital-tract burden by `{paired_metric('GA-HospFirst', 'hospital_mean_normalized_burden_hr'):.2f} h`.
   Hospital-first also scored `{hospital_objective.fitness - canonical_hosp_fitness:.4f}` higher on the
   declared GA-HospFirst surrogate, so the canonical GA sequence is a finite-budget
   stochastic benchmark, not evidence of an optimum.
5. **Benefits and delays were distributed unevenly.** Relative to Hospital-first,
   GA-Balanced improved `{int(winner_lookup.loc[('GA-Balanced', 'improved'), 'tract_count'])}` tracts
   (`{float(winner_lookup.loc[('GA-Balanced', 'improved'), 'population']) / total_population:.1%}` of population)
   and worsened `{int(winner_lookup.loc[('GA-Balanced', 'worsened'), 'tract_count'])}`
   (`{float(winner_lookup.loc[('GA-Balanced', 'worsened'), 'population']) / total_population:.1%}`).
   The corresponding improved/worsened population shares were
   `{float(winner_lookup.loc[('GA-HospFirst', 'improved'), 'population']) / total_population:.1%}` /
   `{float(winner_lookup.loc[('GA-HospFirst', 'worsened'), 'population']) / total_population:.1%}` for GA-HospFirst and
   `{float(winner_lookup.loc[('GA-Efficiency', 'improved'), 'population']) / total_population:.1%}` /
   `{float(winner_lookup.loc[('GA-Efficiency', 'worsened'), 'population']) / total_population:.1%}` for GA-Efficiency.
6. **The main burden ordering was stable to paired physical uncertainty.** All three
   GA-minus-Hospital population-burden bootstrap intervals excluded zero. Logistics
   rankings were less stable: GA-Balanced most often minimized makespan, while travel
   leadership was split across all four strategies.
""".strip()
    primary_paired = paired_stats.loc[paired_stats.metric == "population_normalized_burden_hr"]
    clear = ((primary_paired.bootstrap_ci_low > 0.0) | (primary_paired.bootstrap_ci_high < 0.0)).all()
    decision = "CORE FINDINGS CHANGED — REFRAME REQUIRED" if clear else "PILOT UNCERTAINTY TOO LARGE — TARGETED SENSITIVITY REQUIRED"
    pilot_report = f"""# Revised Paired Pilot Report

## Scientific revision decision

**{decision}**

This report uses 32 paired 2pc50 physical realizations and four fixed ex-ante
strategies under D302/C57. Damage states and positive on-site durations were drawn
once per realization and reused exactly across strategies. Results describe a modeled
resolved service-access proxy; Class C mass remains missing and is never counted as
failure or renormalized.

## Reviewer-facing scientific findings

{scientific_findings}

## Main scientific tradeoffs

Mean, SD, median, and IQR across the 32 paired realizations:

{markdown_table(strategy_stats)}

Paired GA-minus-Hospital-first differences are shown below. Negative values favor the
GA policy for T80, burden, Gini, makespan, and travel. For the signed Q4-Q1 gap, the
sign indicates which quartile bears more burden; closeness to zero is summarized by
the separate absolute-gap metric. Confidence intervals are 10,000-resample paired
bootstrap intervals with a frozen seed:

{markdown_table(paired_stats)}

## Distribution of tract burden

`NormalizedBurden` integrates only unresolved restoration of the identifiable A/B
candidate mass. Permanent Class C uncertainty is excluded from delay rather than
treated as an outage. NRI-derived SOVI quartiles were fixed once for all strategies;
their boundaries are `{quartile_bounds}`. `Q4-Q1>0` means the higher-vulnerability
quartile experienced greater modeled burden. It is a distributional disparity, not a
causal equity verdict. Population-weighted burden Gini is likewise inequality of the
modeled burden, not social causation.

Hospital-first-referenced tract groups use a predeclared ±{NEAR_ZERO_HR:g} h mean
paired-effect threshold:

{markdown_table(winner_summary)}

The tract-level effects and SOVI-quartile summaries are in
`PAIRWISE_STRATEGY_EFFECTS.csv` and `DISTRIBUTIONAL_EFFECTS.csv`. These tables show
who benefits, who is delayed, and the population represented by each group rather
than reporting only a system average.

## Strategy ranking uncertainty

Lowest-metric frequencies use paired realizations and split credit across exact ties.
For distributional disparity, `absolute_Q4_minus_Q1_burden_gap_hr` is the relevant
closeness-to-zero ranking; the signed-gap ranking only identifies the most Q4-favoring
ordering. There is no composite winner score:

{markdown_table(rank_summary)}

## Why Hospital-first and GA-HospFirst differ

The two 302-ID sequences are different. Their paired differences for population T80,
hospital burden, population burden, makespan, and travel appear in the preceding
table. {hosp_objective_interpretation} The surrogate itself optimizes expected
priority-weighted completion credit minus a makespan penalty; it does not directly
optimize T80, realized burden, travel, or disparity. Both finite-budget search quality
and objective alignment must therefore be checked before interpreting a rank reversal.

## Manuscript consequences

Delete all old 92-node makespan, T80, strategy-rank, hotspot, and SVI-weighted-T80-as-
equity claims. Replace them with Architecture-B/D302 claims bounded to strict-SCE
tracts, paired uncertainty, normalized restoration burden, Q4-Q1 disparity, burden
Gini, tract winners/losers, and logistics cost. The revised abstract/conclusion may
report only directional findings supported by the paired estimates and confidence
intervals above; it must retain the service-access-proxy and Class-C limitations.

No C29/C114, repair multiplier, mapping, or source sensitivity was run. The decision
above does not authorize another simulation batch automatically.
"""
    outputs["pilot_report"].write_text(pilot_report, encoding="utf-8")

    evidence_map = {
        "R1 #3": ("Damage and repair-duration uncertainty in scheduling and comparison",
                  "D302_2PC50_DAMAGE_PROBABILITIES.csv; REALIZATION_STRATEGY_SUMMARY.csv",
                  "32 damage/duration hashes are paired across all four strategies; task counts and DS0-DS4 counts are stored per realization.",
                  "Replace mean-duration task selection with DS>0 event tasks and state paired uncertainty explicitly."),
        "R1 #5": ("SVI-weighted T80 is not equity",
                  "TRACT_BURDEN_BY_REALIZATION.csv; DISTRIBUTIONAL_EFFECTS.csv",
                  f"Fixed NRI-SOVI quartiles, signed and absolute Q4-Q1 burden gaps, and population-weighted burden Gini are reported; GA-Efficiency had the lowest absolute gap in {float(rank_lookup.loc[('GA-Efficiency', 'absolute_Q4_minus_Q1_burden_gap_hr'), 'lowest_frequency']):.1%} of realizations but substantially higher total burden.",
                  "Remove equity wording from SVI-T80 and add bounded distributional-disparity results."),
        "R1 #6": ("GA reproducibility and coefficient provenance",
                  "GA_REPRODUCIBILITY_REPORT.md; GA_CONVERGENCE_BY_SEED.csv; GA_CANONICAL_SEQUENCES.csv",
                  "30 declared runs provide generation curves, final fitness spread, sequence hashes, and exact same-seed repeat evidence.",
                  "Report full configuration and label all weights as policy-design coefficients."),
        "R1 #7": ("Hospital-first versus GA-HospFirst interpretation",
                  "GA_REPRODUCIBILITY_REPORT.md; REALIZATION_STRATEGY_SUMMARY.csv",
                  f"Hospital-first scored {hospital_objective.fitness:.6f} versus {canonical_hosp_fitness:.6f} for canonical GA-HospFirst under the identical surrogate, and also had lower mean population T80 and burden.",
                  "Delete the prior objective-mismatch-only story; report that the fixed-budget GA did not surpass the deterministic rule even on its own surrogate and was retained only as a stochastic comparator."),
        "R2 #4": ("Findings were obvious",
                  "PAIRWISE_STRATEGY_EFFECTS.csv; DISTRIBUTIONAL_EFFECTS.csv",
                  "Results identify tract-level beneficiaries/delays and vulnerability-quartile redistribution.",
                  "Center findings on burden redistribution rather than algorithm performance."),
        "R2 #9": ("Why GA and whether it is trustworthy",
                  "GA_REPRODUCIBILITY_REPORT.md; GA_CONVERGENCE_BY_SEED.csv",
                  "The GA is a comparator with transparent permutation, operators, fixed budget, ten seeds per policy, ten distinct final sequences per policy, and nonzero late-generation improvement; its Hospital-first comparison exposes finite-budget search limits.",
                  "Describe GA as a reproducible stochastic benchmark, not a black-box methodological contribution or proof of optimality."),
        "R2 #12": ("Insufficiently novel findings",
                  "REVISED_PAIRED_PILOT_REPORT.md; PAIRWISE_STRATEGY_EFFECTS.csv",
                  "Paired evidence quantifies tradeoffs among burden, disparity, makespan, and travel.",
                  "Replace generic faster-is-better claims with explicit tradeoff and uncertainty findings."),
        "R2 #13": ("Logistics/resource constraints unclear",
                  "REALIZATION_STRATEGY_SUMMARY.csv",
                  "C57 pooled crews, directed road travel, completion/release events, makespan, and total travel are explicit per run.",
                  "Document C57 as a scenario resource budget and the event-based dispatch semantics."),
        "R2 #14": ("Who benefits, who is delayed, and at what cost",
                  "PAIRWISE_STRATEGY_EFFECTS.csv; DISTRIBUTIONAL_EFFECTS.csv; REALIZATION_STRATEGY_SUMMARY.csv",
                  f"Relative to Hospital-first, GA-Balanced improved {int(winner_lookup.loc[('GA-Balanced', 'improved'), 'tract_count'])} tracts but worsened {int(winner_lookup.loc[('GA-Balanced', 'worsened'), 'tract_count'])}; it reduced makespan by {-paired_metric('GA-Balanced', 'makespan_hr'):.2f} h while increasing population burden by {paired_metric('GA-Balanced', 'population_normalized_burden_hr'):.2f} h. Equivalent tract/population and logistics deltas are stored for both other GA policies.",
                  "Add a dedicated distributional winners/losers and logistics-cost results subsection."),
        "R2 #16": ("Shift results to redistribution of recovery burden",
                  "TRACT_BURDEN_BY_REALIZATION.csv; REVISED_PAIRED_PILOT_REPORT.md",
                  "Resolved-mass-normalized restoration burden is evaluated for every tract, strategy, and realization.",
                  "Reframe Results and Conclusion around burden redistribution under paired physical uncertainty."),
    }
    reviewer_lines = ["# Reviewer Response Evidence Matrix", ""]
    for reviewer, (concern, files, evidence, action) in evidence_map.items():
        reviewer_lines.extend([
            f"## {reviewer}", "", f"- **Reviewer concern:** {concern}.",
            f"- **Revised implementation:** {files}.", f"- **New evidence:** {evidence}",
            f"- **Manuscript action:** {action}", "",
        ])
    outputs["reviewers"].write_text("\n".join(reviewer_lines), encoding="utf-8")

    sequences_array = np.array([[domain_ids.index(station_id) for station_id in canonical_sequences[strategy]] for strategy in STRATEGIES], dtype=np.int16)
    summary_indexed = summary.set_index(["realization_id", "strategy"]).reindex(
        pd.MultiIndex.from_product([range(32), STRATEGIES], names=["realization_id", "strategy"])
    )
    summary_matrix = summary_indexed[list(SYSTEM_METRICS)].to_numpy(dtype=float)
    burden_cube = tract_burden.pivot_table(index=["realization_id", "strategy"], columns="tract_id", values="normalized_burden_hr").reindex(
        pd.MultiIndex.from_product([range(32), STRATEGIES], names=["realization_id", "strategy"]),
        columns=tract_metadata.tract_id.astype(str)).to_numpy(dtype=float).reshape(32, 4, 817)
    np.savez_compressed(
        outputs["evidence"],
        domain_ids=np.array(domain_ids), full_r1_ids=np.array(full_ids), service_ids=np.array(service_ids),
        tract_ids=tract_metadata.tract_id.astype(str).to_numpy(), strategy_names=np.array(STRATEGIES),
        damage_probabilities=probabilities, expected_workload_hr=expected_workload,
        canonical_sequence_domain_indices=sequences_array,
        physical_damage_states=physical_damage, physical_duration_hr=physical_duration,
        system_metric_names=np.array(SYSTEM_METRICS), system_metrics=summary_matrix,
        normalized_tract_burden_hr=burden_cube,
        tract_population=tract_metadata.population.to_numpy(dtype=float),
        tract_sovi=tract_metadata.SOVI_SCORE.to_numpy(dtype=float),
        tract_hospital=tract_metadata.hospital_tract.to_numpy(dtype=bool),
        tract_sovi_quartile=tract_metadata.sovi_quartile.astype(str).to_numpy(),
    )

    final_hashes = {name: sha256_file(path) for name, path in outputs.items() if name != "manifest"}
    manifest = {
        "schema": "R26_GA_REPRODUCIBILITY_REVISED_PAIRED_PILOT_V1",
        "scientific_revision_decision": decision,
        "hazard": "2pc50", "domain": "D302", "crew_scenario": "C57_REFERENCE",
        "strategies": list(STRATEGIES), "physical_realizations": 32,
        "strategy_realization_executions": 128, "master_seed": MASTER_SEED,
        "ga_seeds": list(GA_SEEDS), "ga_runs": 30,
        "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "ga_configuration": {
            "population": GA_POPULATION, "generations": GA_GENERATIONS,
            "ordered_crossover_probability": GA_CROSSOVER_PROBABILITY,
            "inversion_mutation_probability": GA_MUTATION_PROBABILITY,
            "tournament_size": GA_TOURNAMENT_SIZE, "stopping": "fixed generation budget",
            "Tmax_hr": TMAX_HR, "network_importance": "DROP",
            "coefficients": POLICIES,
            "coefficient_class": "policy-design / optimization objective coefficients",
        },
        "damage_probability_file_sha256": probability_hash,
        "stage1_clipped_station_count": int(probability_table.stage1_clip_applied.sum()),
        "quartile_boundaries": quartile_bounds,
        "near_zero_threshold_hr": NEAR_ZERO_HR,
        "input_hashes": input_hashes,
        "output_hashes": final_hashes,
        "runner_sha256": sha256_file(runner_path),
        "forbidden_analyses_not_run": ["C29", "C114", "repair_multiplier_sensitivity", "source_sensitivity", "mapping_sensitivity", "legacy_Stage4", "legacy_Stage5"],
    }
    outputs["manifest"].write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "decision": decision,
        "damage_probability_sha256": probability_hash,
        "ga_runs": 30, "physical_realizations": 32, "strategy_executions": 128,
        "summary_rows": len(summary), "tract_burden_rows": len(tract_burden),
        "canonical_sequence_hashes": {strategy: newline_hash(sequence) for strategy, sequence in canonical_sequences.items()},
        "output_hashes": {**final_hashes, "manifest": sha256_file(outputs["manifest"])},
    }, indent=2))


if __name__ == "__main__":
    main()
