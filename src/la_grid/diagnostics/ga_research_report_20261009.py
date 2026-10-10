"""Reconcile completed evidence, pairing seeds and never counting checkpoints twice."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_research_collect_20261009 import ROOT, long_path, save
from la_grid.diagnostics.ga_deeper_evidence_report_20261009 import paired_ci, factorial_effects
from la_grid.diagnostics.ga_search_budget_sensitivity import identity

OUT = ROOT / "continuation"
SPEC = {
    "factorial_20k": (38023902724, "ALL_CASES.json", "results", tuple(range(200,212)), 19, 20000),
    "alternative_100k": (38023988574, "ALL_METHODS.json", "methods", tuple(range(300,320)), 3, 100000),
    "confirmation_100k": (38024145330, "ALL_CASES.json", "cases", tuple(range(400,420)), 11, 100000),
    "neutral_100k": (38024876916, "ALL_METHODS.json", "methods", tuple(range(500,520)), 5, 100000),
    "root_cause_100k": (38024927358, "ALL_CASES.json", "cases", tuple(range(400,420)), 4, 100000),
    "high_budget_500k": (38025814612, "ALL_METHODS.json", "methods", tuple(range(700,710)), 3, 500000),
}


def read(path):
    return json.loads(long_path(path).read_text(encoding="utf-8"))


def csv(name, rows):
    pd.DataFrame(rows).to_csv(long_path(OUT / name), index=False)


def loss(row):
    return float(next(row[k] for k in ("final_loss_hr", "search_best_loss_hr", "planning_loss_hr") if k in row))


def first(row, keys, default=None):
    return next((row[k] for k in keys if k in row), default)


def members(manifest, run_id, filename):
    for a in manifest["artifacts"]:
        if a["run_id"] != run_id:
            continue
        assert not a["expired"] and "sha256" in a, a["artifact_id"]
        archive = ROOT / "actions_raw" / str(run_id) / str(a["artifact_id"])
        for member in a["members"]:
            if Path(member["path"]).name != filename:
                continue
            path = archive / member["path"]
            assert hashlib.sha256(long_path(path).read_bytes()).hexdigest() == member["sha256"]
            yield path, a


def load_batches(manifest, allow_running):
    ga = read(REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json")
    universe = set(ga["sequence"])
    batches = {}
    normalized = []
    checkpoint_rows = []
    inventory = []
    sequences = {}
    redundant_leaf_count = 0
    for batch, (run_id, filename, key, seeds, count, budget) in SPEC.items():
        values = {}
        for path, artifact in members(manifest, run_id, filename):
            data = read(path)
            seed = int(data["seed"])
            assert data["status"] == "COMPLETE" and seed in seeds
            assert seed not in values, (batch, seed, "duplicate final seed artifact")
            rows = data[key]
            assert len(rows) == count
            selected = {}
            for row in rows:
                label = row.get("case", row.get("method"))
                assert label not in selected
                assert row["seed"] == seed and row["budget"] == budget
                seq = row["best_sequence"]
                assert len(seq) == 92 and set(seq) == universe and len(set(seq)) == 92
                assert identity(seq) == row["sequence_sha256"] and np.isfinite(loss(row))
                distinct = int(first(row, ("expensive_calls", "distinct_evaluations", "expensive_evaluations", "distinct_query_count")))
                assert distinct == budget, (batch, seed, label, distinct)
                attempted = int(first(row, ("attempts", "attempted_evaluations", "attempt_count")))
                wall = float(first(row, ("wall_seconds", "elapsed_wall_seconds")))
                initial = float(first(row, ("init_best_hr", "generation0_loss_hr", "generation0_best_loss_hr", "initial_best_loss_hr"), 33.03813174326729))
                assert loss(row) <= initial+1e-8
                item = dict(batch=batch, run_id=run_id, artifact_id=artifact["artifact_id"],
                    source_commit=artifact["source_commit"], seed=seed, configuration=label,
                    budget=budget, distinct_evaluations=distinct, attempted_calls=attempted,
                    duplicate_calls=attempted-distinct, duplicate_fraction=1-distinct/attempted,
                    wall_seconds=wall, planning_loss_hr=loss(row), initial_best_hr=initial,
                    post_initialization_gain_hr=initial-loss(row),
                    sequence_sha256=row["sequence_sha256"],
                    configuration_json=json.dumps(row.get("config", row.get("spec", {})), sort_keys=True))
                normalized.append(item)
                selected[label] = row
                sequences.setdefault(row["sequence_sha256"], seq)
                leaf = path.parent / (label+".json")
                if long_path(leaf).exists():
                    assert read(leaf) == row
                    redundant_leaf_count += 1
                cp = first(row, ("checkpoint", "checkpoints", "budget_checkpoints"), [])
                for point in cp:
                    checkpoint_rows.append(dict(batch=batch, seed=seed, configuration=label,
                        evaluations=int(point["evaluations"]),
                        best_loss_hr=float(first(point, ("loss_hr", "best_loss_hr"))),
                        independent_run=False))
                assert all(cp[j]["evaluations"] < cp[j+1]["evaluations"] for j in range(len(cp)-1))
                if cp:
                    assert cp[-1]["evaluations"] == budget
                    assert abs(float(first(cp[-1], ("loss_hr", "best_loss_hr")))-loss(row)) < 1e-8
            values[seed] = selected
        present = sorted(values)
        missing = sorted(set(seeds)-set(present))
        if missing:
            assert allow_running and batch == "high_budget_500k", (batch, missing)
        assert not values or len({tuple(sorted(x)) for x in values.values()}) == 1
        batches[batch] = values
        inventory.append(dict(batch=batch, run_id=run_id, expected_seeds=len(seeds),
            present_seeds=len(values), configurations=count, budget_each=budget,
            completed_final_runs=len(values)*count, planned_final_runs=len(seeds)*count,
            missing_seeds=json.dumps(missing), complete=not missing))
    csv("SEED_LEVEL_SEARCH_RESULTS.csv", normalized)
    csv("CHECKPOINT_TRAJECTORIES.csv", checkpoint_rows)
    csv("EXPERIMENT_INVENTORY.csv", inventory)
    save(OUT/"ALL_FINAL_SEQUENCES_BY_SHA256.json", sequences)
    save(OUT/"RECONCILIATION_QA.json", dict(status="PASS" if all(x["complete"] for x in inventory) else "PARTIAL_HIGH_BUDGET_ONLY",
        final_search_records=len(normalized), distinct_final_sequences=len(sequences),
        duplicate_leaf_records_verified_not_counted=redundant_leaf_count,
        checkpoint_observations_not_independent=len(checkpoint_rows),
        duplicate_archive_sha256_groups={k:v for k,v in _duplicate_archives(manifest).items() if len(v)>1},
        all_permutations_length=92, all_sequence_sha256_verified=True,
        all_completed_search_budgets_verified=True))
    return batches, pd.DataFrame(normalized), inventory


def _duplicate_archives(manifest):
    out = {}
    for a in manifest["artifacts"]:
        out.setdefault(a["sha256"], []).append(a["artifact_id"])
    return out


def contrast(data, weights, label, family, field="loss"):
    values = [sum(w*(loss(data[s][case]) if field == "loss" else float(data[s][case][field]))
                  for case, w in weights.items()) for s in sorted(data)]
    row = paired_ci(values, family)
    return dict(contrast=label, **row, weights_json=json.dumps(weights, sort_keys=True))


def comparisons(batches):
    rows = []
    pilot = factorial_effects(batches["factorial_20k"])
    for r in pilot:
        rows.append(dict(batch="factorial_20k", contrast=r.pop("factor_term"), **r))
    d = batches["confirmation_100k"]
    contrasts = {
        "population100_minus50_x_tournament5_minus3": {"p100_k5_m10_nquarter":1,"p100_k3_m10_nquarter":-1,"p50_k5_m10_nquarter":-1,"p50_k3_m10_nquarter":1},
        "tournament5_minus3_x_mutation20_minus10": {"p100_k5_m20_nquarter":1,"p100_k3_m20_nquarter":-1,"p100_k5_m10_nquarter":-1,"p100_k3_m10_nquarter":1},
        "neighborquarter_minusnone_x_tournament5_minus3": {"p100_k5_m10_nquarter":1,"p100_k3_m10_nquarter":-1,"p100_k5_m10_nnone":-1,"p100_k3_m10_nnone":1},
        "warm_minus_no_quality_nnone_final_loss": {"p100_k3_m10_nnone":1,"heuristic_only_no_quality":-1},
        "warm_minus_no_quality_nnone_initial_loss": {"p100_k3_m10_nnone":1,"heuristic_only_no_quality":-1},
    }
    for label, weights in contrasts.items():
        field = "init_best_hr" if "initial_loss" in label else "loss"
        rows.append(dict(batch="confirmation_100k_mechanisms", **contrast(d, weights, label, 6, field)))
    gains = [
        (d[s]["p100_k3_m10_nnone"]["init_best_hr"]-loss(d[s]["p100_k3_m10_nnone"]))-
        (d[s]["heuristic_only_no_quality"]["init_best_hr"]-loss(d[s]["heuristic_only_no_quality"]))
        for s in sorted(d)]
    rows.append(dict(batch="confirmation_100k_mechanisms", contrast="warm_x_search_gain",
        **paired_ci(gains, 6), weights_json="(initial-final)_warm - (initial-final)_no_quality"))
    for batch, reference, targets in (
        ("confirmation_100k", "p100_k3_m10_nquarter", [x for x in next(iter(d.values())) if x!="p100_k3_m10_nquarter"]),
        ("alternative_100k", "ga_baseline", ["iterated_local","annealed_local"]),
        ("neutral_100k", "ga_baseline", [f"neutral_{p:.2f}" for p in (0.,.1,.5,1.)]),
        ("high_budget_500k", "ga_k3", ["ga_k5","iterated_local"]),
    ):
        if len(batches[batch]) < 2:
            continue
        for target in targets:
            rows.append(dict(batch=batch, **contrast(batches[batch], {target:1,reference:-1}, target+" minus "+reference, len(targets))))
    roots = batches["root_cause_100k"]
    combined = {s: dict(roots[s], final_swap_with_elite=d[s]["p100_k3_m10_nquarter"]) for s in roots}
    comparisons = [("legacy_plus_warm", "legacy_original"),
        ("legacy_plus_warm_and_elite", "legacy_plus_warm"),
        ("final_swap_without_elite", "final_swap_with_elite"),
        ("final_swap_with_elite", "legacy_plus_warm_and_elite")]
    for a,b in comparisons:
        rows.append(dict(batch="root_cause_100k", **contrast(combined, {a:1,b:-1}, a+" minus "+b, len(comparisons))))
    csv("PAIRED_SIMULTANEOUS_CONTRASTS.csv", rows)
    return rows


def crossfit(manifest):
    rows = []
    seen = set()
    splits = {}
    universe = set(read(REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json")["sequence"])
    for path, artifact in members(manifest, 38025701964, "RUN.json"):
        data = read(path)
        fold, seed = data["fold"], data["seed"]
        assert (fold, seed) not in seen and data["status"] == "COMPLETE"
        seen.add((fold,seed))
        train, hold = data["train_indices"], data["heldout_indices"]
        assert len(train)==48 and len(hold)==16 and not set(train)&set(hold)
        assert set(train)|set(hold)==set(range(64))
        splits.setdefault(fold, hold)
        assert splits[fold] == hold
        for r in data["run_results"]:
            assert r["no_prior_best_injected"] and identity(r["best_sequence"]) == r["sequence_sha256"]
            assert len(r["best_sequence"]) == 92 and set(r["best_sequence"]) == universe
            assert r["training_sample_count"] == 48 and r["holdout_sample_count"] == 16
            assert r["new_physical_samples"] == 0
            assert np.isfinite(r["training_loss_hr"]) and np.isfinite(r["heldout_loss_hr"])
            if r["method"] != "impact_reference":
                assert r["budget"] == 50000 and r["attempted_evaluations"] >= 50000
            rows.append({k:v for k,v in r.items() if k!="best_sequence"})
    assert seen == {(f,s) for f in range(4) for s in range(600,605)}
    assert sorted(sum(splits.values(), [])) == list(range(64))
    df = pd.DataFrame(rows)
    csv("CROSSFIT_SEED_LEVEL_RESULTS.csv", rows)
    paired = []
    for fold, seed in sorted(seen):
        group = df[(df.fold==fold)&(df.seed==seed)].set_index("method")
        ga, ils, ref = (group.loc[x] for x in ("cold_start_ga", "impact_start_ils", "impact_reference"))
        training = ils.training_loss_hr-ga.training_loss_hr
        held = ils.heldout_loss_hr-ga.heldout_loss_hr
        paired.append(dict(fold=fold, seed=seed, train_ils_minus_ga_hr=float(training),
            held_ils_minus_ga_hr=float(held), ranking_reversal=bool(training*held < 0),
            train_ga_minus_impact_hr=float(ga.training_loss_hr-ref.training_loss_hr),
            train_ils_minus_impact_hr=float(ils.training_loss_hr-ref.training_loss_hr),
            held_ga_minus_impact_hr=float(ga.heldout_loss_hr-ref.heldout_loss_hr),
            held_ils_minus_impact_hr=float(ils.heldout_loss_hr-ref.heldout_loss_hr)))
    paired = pd.DataFrame(paired)
    paired.to_csv(long_path(OUT/"CROSSFIT_PAIRED_RESULTS.csv"), index=False)
    fold_means = paired.groupby("fold").mean(numeric_only=True).reset_index()
    fold_means.to_csv(long_path(OUT/"CROSSFIT_FOLD_MEANS.csv"), index=False)
    # Average the four dependent folds within each independent search-seed block.
    blocks = paired.groupby("seed").mean(numeric_only=True)
    ci = [dict(contrast=field, uncertainty_unit="5 search-seed blocks, four folds averaged",
        **paired_ci(blocks[field], 3)) for field in (
        "held_ils_minus_ga_hr", "held_ga_minus_impact_hr", "held_ils_minus_impact_hr")]
    save(OUT/"CROSSFIT_CONDITIONAL_UNCERTAINTY.json", ci)
    return paired, fold_means, ci


def convergence_summary(checkpoints):
    rows = []
    for (batch, configuration), group in checkpoints.groupby(["batch", "configuration"]):
        pivot = group.pivot(index="seed", columns="evaluations", values="best_loss_hr")
        assert not pivot.isna().any().any(), (batch, configuration, "incomplete checkpoint grid")
        boundaries = sorted(pivot.columns)
        for earlier, later in zip(boundaries, boundaries[1:]):
            gain = pivot[earlier]-pivot[later]
            assert (gain >= -1e-8).all(), "Best-so-far loss must not increase"
            rows.append(dict(batch=batch, configuration=configuration, seeds=len(pivot),
                earlier_evaluations=int(earlier), later_evaluations=int(later),
                mean_earlier_loss_hr=float(pivot[earlier].mean()),
                mean_later_loss_hr=float(pivot[later].mean()),
                mean_within_seed_gain_hr=float(gain.mean()),
                median_within_seed_gain_hr=float(gain.median()),
                seeds_with_strict_gain=int((gain > 1e-9).sum())))
    return rows


def search_mechanisms(batches, runs):
    trajectories = convergence_summary(pd.read_csv(long_path(OUT/"CHECKPOINT_TRAJECTORIES.csv")))
    csv("WITHIN_SEED_CONVERGENCE.csv", trajectories)
    neutral = []
    for seed, methods in batches["neutral_100k"].items():
        for label, row in methods.items():
            if label == "ga_baseline":
                continue
            neutral.append(dict(seed=seed, configuration=label,
                neutral_probability=row["neutral_move_probability"],
                neutral_proposals=row["neutral_proposals"],
                accepted_neutral_moves=row["accepted_neutral_moves"],
                accepted_strict_moves=row["accepted_strict_moves"],
                restarts=row["restarts"], loss_hr=loss(row)))
    csv("NEUTRAL_MOVE_SEED_MECHANISMS.csv", neutral)
    neutral = pd.DataFrame(neutral).groupby("configuration").mean(numeric_only=True).reset_index()
    neutral.to_csv(long_path(OUT/"NEUTRAL_MOVE_MECHANISM_SUMMARY.csv"), index=False)
    high = runs[runs.batch.eq("high_budget_500k")]
    performance = []
    ga = high[high.configuration.eq("ga_k3")].set_index("seed")
    frozen = read(REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json")["planning_loss_hr"]
    for label, subset in high.groupby("configuration"):
        x = subset.set_index("seed").loc[ga.index]
        performance.append(dict(configuration=label, seeds=len(x),
            mean_loss_hr=float(x.planning_loss_hr.mean()),
            sd_loss_hr=float(x.planning_loss_hr.std()), best_loss_hr=float(x.planning_loss_hr.min()),
            median_loss_hr=float(x.planning_loss_hr.median()),
            seeds_better_than_ga_k3=int((x.planning_loss_hr < ga.planning_loss_hr-1e-9).sum()),
            seeds_better_than_formal=int((x.planning_loss_hr < frozen-1e-9).sum()),
            mean_attempts_per_distinct=float((x.attempted_calls/x.distinct_evaluations).mean()),
            paired_mean_wall_ratio_to_ga_k3=float((x.wall_seconds/ga.wall_seconds).mean()),
            paired_mean_attempt_ratio_to_ga_k3=float((x.attempted_calls/ga.attempted_calls).mean())))
    save(OUT/"HIGH_BUDGET_EFFICIENCY_AND_QUALITY.json", performance)
    return trajectories, neutral, performance


def history():
    rows = []
    for path in (REPO_ROOT/"results/diagnostics/ga_optimization_20261009/original_behavior_replay").rglob("GENERATION_DIAGNOSTICS.csv"):
        df = pd.read_csv(long_path(path))
        parity = read(path.parent/"PARITY.json")
        assert parity["status"] == "EXACT_BEHAVIOR_PARITY" and parity["actual_expensive_calls"] == 0
        absent = df.loc[df.deterministic_incumbents_remaining.eq(0), "generation"]
        archived = df.loc[df.archive_copies_in_population.eq(0), "generation"]
        rows.append(dict(replay=path.parent.name, population=parity["population"], seed=parity["seed"],
            last_generation=int(df.generation.iloc[-1]),
            first_no_incumbents_generation=int(absent.iloc[0]) if len(absent) else None,
            first_no_archived_chromosome_generation=int(archived.iloc[0]) if len(archived) else None,
            final_population_best_loss_hr=float(df.population_best_service_loss_hr.iloc[-1]),
            final_archived_loss_hr=float(df.best_so_far_service_loss_hr.iloc[-1]),
            final_position_entropy=float(df.position_entropy.iloc[-1]),
            final_unique_population=int(df.unique_population.iloc[-1]),
            final_duplicate_fraction=float(df.duplicate_objective_fraction.iloc[-1]),
            mean_offspring_parent_improvement_fraction=float(df.offspring_improving_parent_fraction.mean()),
            mean_crossover_only_success_fraction=float(df.crossover_only_success_fraction.mean()),
            mean_mutation_only_success_fraction=float(df.mutation_only_success_fraction.mean()),
            mean_combined_success_fraction=float(df.combined_success_fraction.mean()),
            mean_parent_selection_intensity=float(df.parent_selection_intensity.mean()),
            mean_parent_effective_count=float(df.parent_effective_count.mean()),
            history_max_abs_error=parity["history_max_abs_error"]))
    assert len(rows)==20
    csv("ORIGINAL_HISTORY_MECHANISM_SUMMARY.csv", rows)
    return pd.DataFrame(rows)


def table(rows, fields):
    def value(x):
        if x is None or isinstance(x, (float,np.floating)) and np.isnan(x):
            return "not recorded"
        return f"{x:.9f}" if isinstance(x, (float,np.floating)) else str(x)
    return "\n".join(["| "+" | ".join(fields)+" |", "| "+" | ".join(["---"]*len(fields))+" |"]+
        ["| "+" | ".join(value(r[f]) for f in fields)+" |" for r in rows])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--allow-running", action="store_true")
    p.add_argument("--prepare-only", action="store_true", help="Build normalized tables before the independent final-phenotype audit.")
    a = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = read(ROOT/"ACTIONS_RECONCILIATION_MANIFEST.json")
    batches, runs, inventory = load_batches(manifest, a.allow_running)
    effects = comparisons(batches)
    pairs, folds, cross_ci = crossfit(manifest)
    original = history()
    trajectories, neutral_moves, high_quality = search_mechanisms(batches, runs)
    summary = runs.groupby(["batch","configuration"]).agg(
        seeds=("seed","count"), mean_loss_hr=("planning_loss_hr","mean"),
        sd_loss_hr=("planning_loss_hr","std"), best_loss_hr=("planning_loss_hr","min"),
        mean_attempted_calls=("attempted_calls","mean"), mean_wall_seconds=("wall_seconds","mean"),
        mean_duplicate_fraction=("duplicate_fraction","mean"),
        mean_initial_best_hr=("initial_best_hr","mean"), mean_search_gain_hr=("post_initialization_gain_hr","mean")).reset_index()
    summary.to_csv(long_path(OUT/"METHOD_CONFIGURATION_SUMMARY.csv"), index=False)
    accounting = runs.groupby("batch").agg(completed_searches=("seed","count"),
        distinct_evaluations=("distinct_evaluations","sum"), attempted_calls=("attempted_calls","sum"),
        summed_search_wall_seconds=("wall_seconds","sum")).reset_index()
    accounting["kernel_planning_sample_evaluations"] = accounting.distinct_evaluations*64
    extra = dict(batch="crossfit_50k", completed_searches=40, distinct_evaluations=2000000,
        attempted_calls=int(sum(
            row["attempted_evaluations"] for path,_ in members(manifest,38025701964,"RUN.json") for row in read(path)["run_results"])),
        summed_search_wall_seconds=None, kernel_planning_sample_evaluations=2000000*48)
    accounting = pd.DataFrame(accounting.to_dict("records")+[extra])
    accounting.to_csv(long_path(OUT/"COMPUTATION_ACCOUNTING.csv"), index=False)
    if a.prepare_only:
        print("PREPARED", len(runs), flush=True)
        return
    refined = read(ROOT/"ILS_REFINED_BEST_SEED304_PLANNING_CANDIDATE.json")
    frozen = read(REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json")
    parity_path = next(members(manifest,38026109750,"ILS_REFINED_CANDIDATE_PRODUCTION_PARITY.json"))[0]
    parity = read(parity_path)
    assert parity["status"] == "REFINED_ALL_64_PRODUCTION_PARITY_PASS"
    assert parity["ils_sha"]==refined["sequence_sha256"] and parity["ga_sha"]==frozen["sequence_sha256"]
    assert abs(parity["ils_loss_hr"]-refined["loss_hr"])<1e-8
    candidates = dict(FrozenGA=frozen, FirstILS=read(ROOT/"ILS_BEST_SEED304_PLANNING_CANDIDATE.json"), RefinedILS=refined)
    for name, run_id in (("FirstILS",38025309567), ("RefinedILS",38026109750)):
        candidates[name] = dict(candidates[name], current_independent_validation=dict(
            status="ORIGINAL_PRODUCTION_PATH_ALL64_PASS", actions_run_id=run_id))
    for batch in ("alternative_100k","neutral_100k","high_budget_500k"):
        for label in sorted(set(runs.loc[runs.batch.eq(batch),"configuration"])):
            eligible = runs[(runs.batch==batch)&(runs.configuration==label)]
            best = eligible.loc[eligible.planning_loss_hr.idxmin()]
            record = batches[batch][int(best.seed)][label]
            candidates[f"{batch}_{label}_seed{int(best.seed)}"] = record
    save(OUT/"IMPORTANT_CANDIDATES.json", candidates)
    certificate = read(next(members(manifest,38025468939,"RUN.json"))[0])
    assert certificate["start_sequence_sha256"] == candidates["FirstILS"]["sequence_sha256"]
    assert certificate["sequence_sha256"] == refined["sequence_sha256"]
    assert certificate["accepted_moves"] == 7 and certificate["last_scan_complete"] and certificate["local_optimal_up_to_1e_minus_9"]
    save(OUT/"REFINEMENT_CERTIFICATE_RECONCILED.json", dict(
        start_loss_hr=certificate["start_planning_loss_hr"], end_loss_hr=certificate["best_planning_loss_hr"],
        incremental_refinement_gain_hr=certificate["start_planning_loss_hr"]-certificate["best_planning_loss_hr"],
        inherited_quality_to_refined_gain_hr=certificate["improvement_vs_previous_hr"],
        distinct_evaluations=certificate["distinct_evaluations"], attempts=certificate["total_attempts"],
        accepted_moves=certificate["accepted_moves"], complete_final_scan=True,
        local_only_not_global=True, source_artifact_run_id=38025468939))
    save(OUT/"COMPUTATION_SCOPE.json", dict(reconciled_not_reexecuted=True,
        completed_search_distinct_evaluations=int(accounting.distinct_evaluations.sum()),
        prior_refinement_distinct_evaluations=132545,
        prior_refinement_attempts=136040,
        loader_calls_and_final_parity_checks_outside_search_budget=True,
        crossfit_wall_times_not_recorded=True,
        repeated_generation_checkpoints_not_new_runs=True,
        prior_search_effort_embodied_in_warm_start=True,
        new_physical_samples=0, external_validation_accessed=False,
        new_diagnostic_event_integrations=192))
    complete = all(row["complete"] for row in inventory)
    md = ["# Consolidated GA optimization continuation", "",
        "Status: **"+("COMPLETE: outstanding batches reconciled and analyzed" if complete else "DRAFT: 500k study still running")+"**.", "",
        "Diagnostic branch only. Fetched starting HEAD: `5697f4f92fa1ac2863fbcb61e6f72e94ed9d418d`; prior baseline `13f8ef8e5d244c70a92a06a45540460c736c70f9`. No formal candidate promotion, physical resampling, objective change, revision-branch edit, or manuscript/artwork replacement.", "",
        "## 1. Authority and experiment inventory", "",
        "The unchanged model has 92 stations, 318 graph edges, 14 Core sources, C57_D1, 2,315 tract dependencies and 64 frozen 2pc50 planning states. J is the original population-dependency-weighted mean integrated effective-service loss; threshold 0.5 and original planning horizon 2855.254013110100 h are preserved. All new event accounting uses that original horizon. The independent production audit uses the original scheduler, pandas/NetworkX gate and production burden evaluator.", "",
        table(inventory,["batch","run_id","expected_seeds","present_seeds","configurations","budget_each","completed_final_runs","complete"]), "",
        "Four-fold cross-fitting additionally has 20 fold/seed jobs, 40 searches at 50k on 48 training states, plus 20 deterministic reference records (not searches). All 4x5 jobs and disjoint 16-state held-out folds passed identity checks.", "",
        "Run metadata, source commits, jobs, seeds, artifact IDs, original archive SHA-256 and every member hash are retained in `ACTIONS_RECONCILIATION_MANIFEST.json`. Every completed record has a validated 92-ID permutation, canonical newline-delimited SHA-256 and full budget. Per-case leaf copies and checkpoint observations are verified/retained but not counted as independent searches; see `RECONCILIATION_QA.json`.", "",
        "### All requested and subsequent Actions runs", ""]
    for r in manifest["runs"]:
        md.append(f"- [{r['id']}: {r['name']}](https://github.com/{manifest['repository']}/actions/runs/{r['id']}) - {r['status']}/{r['conclusion']}; commit `{r['head_sha']}`; {len(r['artifacts'])} artifacts.")
    md += ["", "The unsuccessful earlier parity run 38025031722 produced no comparison artifact and is not counted as a successful evaluation. Its stale input-identity receipt failure was corrected without changing the physical model; runs 38025309567 and 38026109750 are the subsequent successful original and refined audits. No completed batch was rerun to reconstruct available records.", "",
        "## 2. Independently verified candidates and influence", "",
        f"Frozen GA J = {frozen['planning_loss_hr']:.12f} h; refined ILS compiled J = {refined['loss_hr']:.12f} h, independently verified production J = {parity['ils_loss_hr']:.12f} h. Maximum per-realization production/compiled discrepancy = {parity['max_absolute_model_parity_error_hr']:.3g} h. Improvement = {parity['improvement_hr']:.12f} h ({parity['improvement_fraction_percent']:.6f}%). The formal GA file remains unchanged.", "",
        "Canonical permutation hashes:", ""]
    for name, record in candidates.items():
        md.append(f"- {name}: `{record['sequence_sha256']}`.")
    md += ["", "Complete permutations are in `IMPORTANT_CANDIDATES.json`; every experimental final permutation is in the raw artifacts and `ALL_FINAL_SEQUENCES_BY_SHA256.json`. These are candidate records, not policy promotion.", ""]
    influence = read(OUT/"SAMPLE_INFLUENCE_DIAGNOSTICS.json")
    for name, result in influence.items():
        md += [f"### {name} minus FrozenGA", "",
            f"Mean {result['mean_delta_hr']:+.12f} h; median {result['median_delta_hr']:+.12f} h; {result['better_samples']}/64 better and {result['worse_samples']}/64 worse. Omitting realization 15 gives {result['targeted_omissions'][0]['retained_mean_delta_hr']:+.12f} h. Omitting the five most beneficial states gives {result['targeted_omissions'][3]['retained_mean_delta_hr']:+.12f} h.", "",
            f"Per-state difference SD {result['sd_delta_hr']:.9f} h; middle 50% [{result['quartiles_hr'][0]:+.9f}, {result['quartiles_hr'][1]:+.9f}] h. Both quartiles are positive even though the original mean is negative: a small beneficial tail outweighs mostly unfavorable differences.", "",
            table(result["exhaustive_omissions"],["omitted_count","subsets","ga_better_count","ils_better_count","mean_delta_min_hr","mean_delta_max_hr"]), ""]
    md += ["All 64 leave-one-out values, exhaustive leave-two/leave-three reversal counts and targeted leave-1/2/3/5/10 results are retained. Omission checks are influence diagnostics, not a replacement objective or a license to discard difficult samples. Selected-candidate sample intervals would be postselection descriptive, not independent expected-performance evidence. The larger median disadvantage and the sign reversal after removing a small number of favorable states diagnose physical-training-sample leverage, not numerical parity failure.", "",
        "## 3. Exact physical/scheduling mechanism", ""]
    components = pd.read_csv(OUT/"ALL64_EXACT_LOSS_COMPONENTS.csv")
    for candidate in ("FirstILS","RefinedILS"):
        c = components[components.strategy.eq(candidate)].set_index("realization")
        b = components[components.strategy.eq("FrozenGA")].set_index("realization")
        changes = c[list(("L_self","L_threshold","L_source","L_total"))]-b[list(("L_self","L_threshold","L_source","L_total"))]
        md += [f"### {candidate}: signed component changes", "",
            table([dict(scope="realization15",**changes.loc[15].to_dict()),dict(scope="all64mean",**changes.mean().to_dict())],
                  ["scope","L_self","L_threshold","L_source","L_total"]), ""]
    events = {name:read(OUT/f"SAMPLE15_{name}_EVENTS.json") for name in ("FirstILS","RefinedILS","FrozenGA")}
    md += ["L_self integrates 1-f; L_threshold integrates f(1-F); L_source integrates fF(1-C). These nonnegative losses sum exactly to L_total=1-fFC. All 192 station/event integrations reproduce the compiled sample objective within 1e-8 h; no surrogate timeseries or trapezoidal approximation is used.", "",
        "For the first ILS realization-15 schedule, total directed crew travel rises by 1.142998168 h, 22 stations finish earlier and 22 later, and mean damaged-station completion is 0.050290139 h later. The 2.082523454 h benefit comes from source connectivity, not uniformly faster repairs: source loss falls by 2.279239845 h, offset by worse self and threshold loss.", ""]
    for name, data in events.items():
        station = next(r for r in data["station_schedule"] if r["station"]=="301745")
        major = [e for e in data["events"] if e["newly_connected_dependency_mass"]>500000]
        md += [f"{name}: station 301745 (not a source) finishes at {station['finish_hr']:.9f} h, crew {station['crew_index']}, dispatch rank {station['dispatch_rank']}, unchanged duration {station['duration_hr']:.9f} h.", ""]
        for e in major:
            md.append(f"- At {e['time_hr']:.9f} h, completion {', '.join(e['completed_stations'])} coincides with {len(e['newly_source_connected_stations'])} newly source-connected stations and {e['newly_connected_dependency_mass']:.3f} population-dependency mass; active sources {', '.join(e['active_sources'])}.")
        md.append("")
    counterfactual = read(OUT/"CONTROLLED_PRIORITY_INTERVENTIONS.json")
    md += ["The first ILS event at 19.043563694 h reconnects 21 stations with 2,320,857.337 dependency mass. The frozen GA large reconnection occurs at 25.242654999 h with completion of 303371 (25 stations), then at 26.335434734 h with completion of 309042 (4 stations). Between 19.166689187 and 21.042918991 h, effective service is 0.322390551 for ILS versus 0.017620177 for GA; this interval contributes -0.571819258 h. Full component memberships, active sources, newly connected IDs, completion events, crew assignment and dependency masses are retained in the SAMPLE15 event JSONs.", "",
        "### Feasible controlled priority interventions", "",
        "Three full permutations move only station 301745 between original full priority indices 21/62, retaining all other relative priorities and the original physical samples, source gate, crew scheduler and mean-loss evaluator. Each was independently checked through all64 native production evaluations (maximum parity error below 1e-8 h). These are diagnostic counterfactuals, not an optimization batch or new formal policies.", "",
        table(counterfactual["interventions"],["label","sample15_station_completion_hr","sample15_delta_hr","mean_counterfactual_minus_parent_hr","improved_realizations","worsened_realizations"]), "",
        "Moving 301745 forward in FrozenGA makes it finish at the same 19.043563694 h as FirstILS, yet improves sample15 by only 0.022576075 h rather than reproducing the full 2.082523454 h benefit. It worsens the original64 mean by 0.072395103 h. Conversely delaying 301745 in FirstILS loses 1.691373767 h on sample15; delaying it in RefinedILS loses 1.652978878 h. This asymmetric feasible intervention demonstrates dependence on the surrounding order, not one universally beneficial station move.", "",
        "The representative active ILS source path for 301745 is `301745 -> 306623 -> 304073 -> 307373`. Core source 307373 completes at 15.320528259 h in FirstILS versus 28.435441828 h in FrozenGA and the early-301745 counterfactual. Station 301637 completes at 15.197339881 h in FirstILS versus 22.282564468 h in FrozenGA and 22.772295802 h in the early counterfactual. Those two stations are inactive on retained representative ILS paths in the early-GA intervention at 19.043563694 h; FirstILS has 28 connected stations versus 3 there. `SAMPLE15_CONTROLLED_SOURCE_PATHS.json` retains the explicit station/source paths and inactive-node timings. Shortest-hop paths are descriptive reachability witnesses, not unique electrical flows or proof that all alternate routes require the same nodes.", "",
        "Dependency mass is sum_r P_r W_ri, not delivered MW, station demand, or exclusive customer counts. Event/station contributions describe the complete feasible schedules. The controlled intervention effect concerns the specified full feasible priority edit, including all scheduler cascades; it is not an isolated restoration-time causal effect or a claim that 301745 explains the entire between-strategy difference.", "",
        "## 4. Parameter interactions and initialization", "",
        table([r for r in effects if r["batch"] in ("factorial_20k","confirmation_100k_mechanisms")],
            ["batch","contrast","mean_delta_hr","simultaneous95_low_hr","simultaneous95_high_hr"]), "",
        "High-minus-low main effects and explicit difference-in-differences are computed within the same optimizer seed. Screening has 12 independently allocated seeds; confirmation has 20 different seeds. Main/two-factor screening terms form a 10-contrast family. Six confirmatory mechanism contrasts form a separate family; ten case-to-baseline confirmation comparisons are retained separately. All intervals are Bonferroni simultaneous 95% paired t intervals, conditional on the reused planning collection; no post hoc equivalence tolerance is asserted.", "",
        "Population P50/P100 with quarter allocation changes neighbors 12/25, deterministic-reference fractions 7/50 vs 7/100, and random-fill counts as well as population/generations. The population interaction therefore concerns the tested population-plus-initialization package, not isolated P. Crossover stays .8, mutation operator swap, elite count one in these factorial contrasts.", "",
        "The exact warm start is the earlier 33.03813174326729 h sequence (`3bfeafdd1adf950749e63fdbbe3b7efc21b1efd04c3b3d64c28c3d118717bbed`), not the frozen 32.997840773882714 h best. Warm/no-quality comparisons use zero neighbors and the same seven references, removing prior-best influence from both initialization and archive in the no-quality control. A larger cold-start search gain partly reflects its worse starting score; it is not by itself evidence of a better final optimizer.", "",
        "The 20k tournament5 screening benefit is not automatically carried forward as a final default. Independently seeded 100k interaction contrasts and the 500k comparison determine its supported scope. Unresolved intervals identify limited seed precision at very small effects, tested-composition dependence and budget dependence; they do not prove equal performance or justify endless repetitions of the same comparison.", "",
        "The 100k population-by-tournament, tournament-by-mutation and neighbors-by-tournament contrasts are approximately -0.000224, +0.000149 and +0.000183 h, respectively; all six-family simultaneous intervals include zero. This does not reproduce a general tournament5 benefit from the short-budget screen. Warm initialization improves the initial best by 0.540171 h, but warm-minus-no-quality final loss is +0.000501 h with an interval crossing zero. The cold-start controls catch up through search; preserving a strong initial archive is useful protection but not demonstrated to improve final search quality under this tested 100k package.", "",
        "## 5. Does GA add value?", ""]
    methods = summary[summary.batch.isin(["alternative_100k","neutral_100k","high_budget_500k"])]
    md += [table(methods.to_dict("records"), ["batch","configuration","seeds","mean_loss_hr","sd_loss_hr","best_loss_hr","mean_attempted_calls","mean_wall_seconds","mean_duplicate_fraction"]), "",
        table([r for r in effects if r["batch"] in ("alternative_100k","neutral_100k","high_budget_500k")],
            ["batch","contrast","mean_delta_hr","simultaneous95_low_hr","simultaneous95_high_hr"]), "",
        "Distinct expensive evaluations are matched within each experiment. Attempted calls additionally measure repeated permutation queries and can be much larger for GA. Checkpoint trajectories at fixed boundaries are repeated measurements of the same search, not independent runs; convergence and marginal gains must use within-seed deltas. Wall times describe these cloud implementations/runners, not universal hardware performance. Sum of concurrent job times is compute accounting, not elapsed project time.", "",
        "ILS is a substantive non-GA comparator: swap/insertion/inversion proposals, strict local acceptance and fixed cyclic 2/4/8 perturbations after stagnation. Tested annealing underperformance does not disqualify stronger annealing implementations. The neutral drift grid tests equality acceptance probabilities 0/.1/.5/1 at fixed 1e-9 h equality tolerance, not an arbitrary new default. The older joint-budget GA/local hybrid, variable perturbation sizes and the completed deterministic swap/insertion/inversion/adjacent-block(2/3/4) certificate are stronger search mechanisms already investigated; their results do not prove every possible hybrid/VNS/LNS ineffective.", "",
        "### Matched 500k quality, variability and efficiency", "",
        table(high_quality,["configuration","seeds","mean_loss_hr","sd_loss_hr","best_loss_hr","seeds_better_than_ga_k3","seeds_better_than_formal","mean_attempts_per_distinct","paired_mean_wall_ratio_to_ga_k3"]), ""]
    h = {r["configuration"]:r for r in high_quality}
    ils_effect = next(r for r in effects if r["batch"]=="high_budget_500k" and r["contrast"].startswith("iterated_local"))
    k5_effect = next(r for r in effects if r["batch"]=="high_budget_500k" and r["contrast"].startswith("ga_k5"))
    md += [f"The matched 500k ILS-minus-GAk3 mean is {ils_effect['mean_delta_hr']:+.9f} h, simultaneous interval [{ils_effect['simultaneous95_low_hr']:+.9f}, {ils_effect['simultaneous95_high_hr']:+.9f}]. ILS wins {h['iterated_local']['seeds_better_than_ga_k3']}/{h['iterated_local']['seeds']} paired seeds and beats the formal selected GA score in {h['iterated_local']['seeds_better_than_formal']} searches. Its average within-seed wall-time ratio is {h['iterated_local']['paired_mean_wall_ratio_to_ga_k3']:.3f}, and attempted-call ratio {h['iterated_local']['paired_mean_attempt_ratio_to_ga_k3']:.3f}. The benefit is small in absolute mean-loss units, but the tested ILS is a competitive optimizer with much lower repeated-call overhead; GA superiority is not supported by this evidence.", "",
        f"Tournament5-minus3 at 500k is {k5_effect['mean_delta_hr']:+.9f} h, simultaneous interval [{k5_effect['simultaneous95_low_hr']:+.9f}, {k5_effect['simultaneous95_high_hr']:+.9f}]. The final default cannot be justified from the 20k marginal screen alone. Both tested GA methods retain repeated-genotype overhead, separate from scheduler-equivalent distinct permutations.", "",
        "### Late-budget convergence", "",
        table([r for r in trajectories if r["batch"]=="high_budget_500k"],
            ["configuration","seeds","earlier_evaluations","later_evaluations","mean_within_seed_gain_hr","median_within_seed_gain_hr","seeds_with_strict_gain"]), "",
        "These are gains inside each same seeded 500k search, not a comparison of separately seeded 100k and 500k batches. They distinguish a method that continues finding useful priorities from a method that spends later budget generating repeated or non-improving candidates. Full boundary means and the other batches are in WITHIN_SEED_CONVERGENCE.csv. The current GA engine does not retain complete per-offspring lineage histories; the historical observation-only replays supply those mechanism measurements. Final hashes/checkpoints cannot establish that every distinct later candidate is scheduling-equivalent.", "",
        "In the completed ten-seed batch, GA tournament3 improves in only 3/10 searches between 100k and 250k and in 0/10 thereafter; tournament5 improves in 0/10 after 100k. ILS improves in 8/10 between 100k and 250k (mean gain 0.002789 h), then 7/10 between 250k and 500k (mean gain 0.000473 h). Thus simply multiplying the current GA budget is inefficient here, whereas the tested local-search perturbations still expose useful priorities. Neither GA500k variant beats the formal selected score in any of ten searches; ILS does in five. Its best 32.996457713 h remains worse than the independently verified refined candidate 32.996137365 h. There is no new best requiring another candidate promotion decision.", "",
        "### Neutral traversal evidence", "",
        table(neutral_moves.to_dict("records"),["configuration","neutral_proposals","accepted_neutral_moves","accepted_strict_moves","restarts","loss_hr"]), "",
        "Neutral traversal really occurred in the positive-probability variants; it was not an unexercised flag. The retained paired final-loss intervals show no reliable improvement over the GA comparator for these tested probabilities. Accepted neutral moves measure plateau exploration, not independently beneficial objective changes. The strict and neutral transition counts are per-search summaries; checkpoint observations and transitions are not additional independent optimizer runs.", "",
        "### Stronger local and hybrid mechanisms already tested", "",
        "The [prior operator/local/hybrid audit](../../ga_optimization_20261009/GA_HYPERPARAMETER_AND_OPERATOR_AUDIT.md#q5--new-planning-improvements-and-localhybrid-search) records a twenty-seed hybrid with 50k GA queries followed by local refinement in the same joint 100k cache: mean 33.018973583 h, SD 0.001260725 h, worse than its confirmed swap-GA comparator at the same total budget. Its GA prefix is counted once, not added again as fresh compute. Local-only refinement of the older warm start used 464,141 distinct queries and 28 accepted moves, reaching 32.998626841 h. Refinement of the then-selected GA/mixed best used 16,643 queries with zero accepted moves. These are prior evidence, not additional newly reconciled Actions searches or matched-hardware cost claims.", "",
        "The new seed304 multi-neighborhood refinement breaks that earlier local plateau from a different ILS basin: seven improving moves and 132,545 distinct queries, ending at 32.996137365 h. Together with the 500k late gains and actually accepted neutral transitions, this addresses basin dependence and variable-neighborhood/perturbation behavior rather than assuming GA is indispensable. A new scheduling-aware large-neighborhood destroy/reinsert algorithm has not been benchmarked; cyclic 2/4/8 random perturbations must not be mislabeled as a comprehensive LNS comparison. No evidence supports ruling out every stronger hybrid or local-search implementation.", "",
        "## 6. Original GA failure and actual search history", "",
        table([r for r in effects if r["batch"]=="root_cause_100k"],
            ["contrast","mean_delta_hr","simultaneous95_low_hr","simultaneous95_high_hr"]), "",
        "Original GA has a best-so-far incumbent archive but no surviving elite chromosome. Archive retention guarantees output preservation, not reproductive lineage survival or rediscovery. Twenty observation-only histories match original native histories (maximum error 7.11e-15, zero new expensive replay calls); full observed incumbent disappearance, archive copies, diversity, selection and offspring statistics are summarized in ORIGINAL_HISTORY_MECHANISM_SUMMARY.csv.", ""]
    for label, subset in original.groupby(original.replay.str.extract(r"(^[A-Za-z]+)", expand=False)):
        md.append(f"- {label}: mean final position entropy {subset.final_position_entropy.mean():.6f}, mean final unique population {subset.final_unique_population.mean():.2f}, mean crossover-only parent-improvement fraction {subset.mean_crossover_only_success_fraction.mean():.6f}, mutation-only {subset.mean_mutation_only_success_fraction.mean():.6f}; first no-incumbent generation range {subset.first_no_incumbents_generation.min()} to {subset.first_no_incumbents_generation.max()}.")
    phenotype = read(OUT/"FINAL_PHENOTYPE_QA.json")
    assert phenotype["final_search_records"] == len(runs), "Refresh final-phenotype audit after new seed records"
    md += ["", "Root controls distinguish warm-start plus its neighbor composition, then explicit generational elitism at fixed inversion mutation .2; final swap .1 with/without elitism is another controlled comparison. Final swap .1 versus inversion .2 is a mutation-operator-plus-probability package, not a clean isolated operator effect. Previously controlled operator studies supply the fixed-probability evidence. High population diversity without improvement is observed in failed P500 histories; a flat archive is not a global-optimality or convergence proof.", "",
        f"Current final-chromosome audit: {phenotype['final_search_records']} search outcomes, {phenotype['unique_chromosomes']} distinct chromosomes, but only {phenotype['unique_completion_phenotypes']} exact all64 completion-array phenotypes. All archived scores reproduce to a maximum error of {phenotype['max_absolute_archived_score_error_hr']:.3g} h. This is an audit of final outcomes, not the entire unretained new search trajectories. Identical final chromosomes across distinct seed/configuration searches remain separate stochastic outcomes in means and uncertainty estimates; only duplicate artifact/checkpoint observations are excluded.", "",
        "Near-best scheduling-equivalent permutations were demonstrated in the prior bounded phenotype audit despite injective joint damaged-task-order signatures. DS0 filtering alone cannot collapse all full orders because some planning states damage all 92. Equal objective values alone do not imply equal schedules. Current duplicate-call rates distinguish repeated genotype generation from that separate scheduler-induced plateau.", "",
        "## 7. Internal cross-fitting and generalization", "",
        table(folds.to_dict("records"),["fold","train_ils_minus_ga_hr","held_ils_minus_ga_hr","held_ga_minus_impact_hr","held_ils_minus_impact_hr"]), "",
        f"Individual fold/seed pairs have {int(pairs.ranking_reversal.sum())}/20 training-versus-held-out GA/ILS ranking reversals. Three of four fold-average comparisons favor ILS in training but GA on held-out states; fold3 favors GA in training but ILS on held-out states. Neither method receives the previously optimized all-64 incumbent.", "",
        table(cross_ci,["contrast","n","mean_delta_hr","simultaneous95_low_hr","simultaneous95_high_hr"]), "",
        "Uncertainty uses five independent optimizer-seed blocks after averaging the four dependent folds within each seed, with a three-comparison simultaneous interval family. These intervals describe search randomness conditional on this fixed four-fold partition, not four independent physical validations or twenty independent external datasets. Training sets overlap, and method development already saw the 64-state collection. No proposed 2,000 fresh physical states were accessed for tuning, candidate selection or repeated testing.", "",
        "## 8. Computation and explicit research decision", "",
        table(accounting.to_dict("records"),["batch","completed_searches","distinct_evaluations","attempted_calls","summed_search_wall_seconds","kernel_planning_sample_evaluations"]), "",
        f"The deterministic refined-ILS certificate adds 132,545 distinct and 136,040 attempted local queries, seven accepted improvements, with a complete final tested-neighborhood scan. Its incremental gain over first ILS is {certificate['start_planning_loss_hr']-certificate['best_planning_loss_hr']:.12f} h; the artifact's `improvement_vs_previous_hr` field measures gain over the older inherited 33.038131743 h seed, not that incremental refinement. Its 500k cap was not fully consumed; do not portray it as a 500k matched-method run. Loader parity/setup reference calls and final best-score/production checks are outside metered search and identified separately, not zero-cost science. Cold-start crossfit did not retain wall timings; this is unavailable, not reconstructed by rerunning it.", "",
        f"New continuation work performs 192 event-exact component integrations, 192 native production plus 192 compiled sample counterfactual evaluations, and {phenotype['total_retained_mean_score_audit_calls']} retained final-chromosome mean-score checks plus {phenotype['total_retained_native_schedule_decodes']} native sample-schedule decodes. None are newly executed optimizer budgets. All optimizer batch budgets above were retrieved, not reexecuted.", "",
        "Scientific decision: retain the formal GA candidate pending explicit authorization. Do not claim GA universal superiority, tournament3 exact optimality, tournament5 confirmation from a 20k screen, or robust physical improvement from one selected best. The principal reliability issue is now conditional source-reconnection timing and influential planning-state leverage, not a failed evaluator or absence of feasible better chromosomes. Replicated search, archive protection, explicit initialization accounting, exact distinct budgets and independently audited candidates are defensible method requirements.", "",
        "The existing experiments already test neutral plateau traversal, variable perturbations, deterministic multi-neighborhood refinement, cold-start search and a joint-budget hybrid. This continuation additionally verifies every retained final candidate and tests feasible priority interventions rather than merely repeating a plateau. Additional identical parameter repetitions are not warranted just to shrink a CI. Any next stronger hybrid/large-neighborhood comparison requires a declared new mechanism, joint budget and independent optimizer seeds; it cannot use the proposed fresh physical validation cohort for development. Candidate robustness remains a separate question from preserving the mean-loss optimization authority.", "",
        ("All specified outstanding batches have finished and passed final seed/configuration/budget/sequence reconciliation. No further identical GA-budget or neutral-probability sweep is justified by these results. The immediate decision is to retain the formal policy and treat ILS plus deterministic multi-neighborhood refinement as a credible challenger, not automatically promote a tiny selected mean gain. Scheduling-aware LNS remains an untested method family, not a pending launched job; only a prospectively specified mechanism comparison would warrant new development compute. The most consequential limitation is physical-sample generalization. That cannot be cured by repeatedly selecting on these same64 states; keep future validation untouched until the method and candidate-selection procedure are prospectively locked." if complete else "The 500k batch remains outstanding; this is explicitly a draft, not the completed research decision."), "",
        "## 9. Reproduction and preservation", "",
        "Run on this diagnostic branch with Python3.12, numba0.60.0, NumPy/pandas/NetworkX/SciPy and single BLAS/Numba threads. Retained artifact source commits and workflow files give exact cloud commands, runtime pins and matrix seeds. Do not rerun completed searches merely to regenerate evidence.", "",
        "```powershell", "$env:PYTHONPATH='src'", "$env:NUMBA_CACHE_DIR=Join-Path $env:TEMP 'ga-research-20261009-numba'",
        "$env:OPENBLAS_NUM_THREADS='1'", "$env:MKL_NUM_THREADS='1'", "$env:NUMBA_NUM_THREADS='1'",
        "python -m la_grid.diagnostics.ga_research_collect_20261009 --local-only",
        "python -m la_grid.diagnostics.ga_research_mechanism_20261009",
        "python -m la_grid.diagnostics.ga_research_priority_counterfactual_20261009",
        "python -m la_grid.diagnostics.ga_research_gate_paths_20261009",
        "python -m la_grid.diagnostics.ga_research_report_20261009 --prepare-only",
        "python -m la_grid.diagnostics.ga_research_phenotypes_20261009",
        "python -m la_grid.diagnostics.ga_research_report_20261009", "```", "",
        "Collector without --local-only refreshes authenticated official Actions metadata/downloads; it never launches calculations. ga_research_preserve_20261009 hydrates exact checked-in LFS bytes in the isolated checkout from verified local object hashes and records/compares the untouched revision checkout. Windows long-path runtime-cache handling changes only cache location, not evaluator code. CONTINUATION_PRESERVATION_BASELINE/VERIFIED cover the revision HEAD/branch, unrelated staged diff and 950 source/result/artwork files. MODEL_IDENTITY.json retains original file/context and all64 sample hashes. Scientific inputs/evaluator/scheduler/source gate/formal permutations remain unchanged.", ""]
    long_path(OUT/"GA_OPTIMIZATION_CONSOLIDATED_RESEARCH.md").write_text("\n".join(md).rstrip("\n")+"\n", encoding="utf-8")
    save(OUT/"CONSOLIDATION_STATUS.json", dict(status="COMPLETE" if complete else "AWAITING_500K",
        all_required_batches_complete=complete, no_formal_candidate_replacement=True,
        new_physical_samples=0, external_validation_accessed=False,
        outstanding_seeds=inventory[-1]["missing_seeds"]))
    print("REPORT", "COMPLETE" if complete else "DRAFT", len(runs), len(effects), flush=True)


if __name__ == "__main__":
    main()
