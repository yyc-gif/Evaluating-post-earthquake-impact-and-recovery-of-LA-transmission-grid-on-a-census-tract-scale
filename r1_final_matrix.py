"""Read-only validation of the frozen July92 formal experiment matrix.

This module neither samples physical inputs nor runs a scientific stage. The
expanded July entry point remains the only pipeline entry point.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np


FREEZE_COMMIT = "517a755fbf334af3c8ee269b35027f9befdf0776"
ARCHIVE_COMMIT = "182686868cffe962739804f6bc0ccecaed73d601"
MATRIX_ID = "JULY92_REVIEWER_REVISION_FINAL_V1"
HAZARDS = ["Northridge", "SanFernando", "LongBeach", "2pc50"]
RULES = ["hospital-first", "impact-first", "degree-first", "closeness-first",
         "betweenness-first", "centrality-first", "random"]
SCHEDULED = RULES + ["direct-community"]
MAPPINGS = ["M0_JULY_003", "M1_UTILITY_003", "M0_JULY_NO_CUTOFF",
            "M0_JULY_001", "M1_UTILITY_NO_CUTOFF", "M1_UTILITY_001",
            "M3_SCE_SUPPORTED"]


def _git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(actual, expected, label: str) -> None:
    if actual != expected:
        raise ValueError(f"Frozen matrix mismatch: {label}: {actual!r} != {expected!r}")


def load_frozen_matrix(path: Path, repo: Path) -> tuple[dict, str]:
    """Require exact frozen JSON bytes from the committed authority."""
    path = path.resolve()
    repo = repo.resolve()
    if path != repo / "FINAL_EXPERIMENT_MATRIX.json":
        raise ValueError("Formal run must read this branch's FINAL_EXPERIMENT_MATRIX.json")
    if _git("rev-parse", "--abbrev-ref", "HEAD", cwd=repo) != "revision/reviewer-driven-core-rebuild-v2":
        raise ValueError("Formal run is restricted to the revision v2 branch")
    if _git("merge-base", "--is-ancestor", FREEZE_COMMIT, "HEAD", cwd=repo) != "":
        raise ValueError("Frozen matrix commit is not in this branch's history")
    frozen_bytes = subprocess.check_output(
        ["git", "show", f"{FREEZE_COMMIT}:FINAL_EXPERIMENT_MATRIX.json"], cwd=repo
    )
    actual_bytes = path.read_bytes()
    if actual_bytes != frozen_bytes:
        raise ValueError("Frozen matrix bytes differ from freeze commit")
    m = json.loads(actual_bytes)
    _require(m["matrix_id"], MATRIX_ID, "matrix_id")
    _require(m["status"], "FROZEN_BEFORE_FORMAL_EXECUTION", "status")
    _require(m["implementation_code_commit_sha"],
             "b88ccbfb19dae5860225dd06c4385de110dcf43f", "implementation baseline")
    _require(m["protected_submission_sha"], ARCHIVE_COMMIT, "protected archive")
    _require(m["domain"], {"stations": 92, "edges": 318, "tracts": 2315}, "domain")
    p = m["physical_samples"]
    _require(p["hazards_in_seed_order"], HAZARDS, "hazards")
    _require(p["N_EVAL_per_hazard"], 1000, "N_EVAL")
    _require(p["planning_hazard"], "2pc50", "planning hazard")
    _require(p["N_PLANNING"], 64, "N_PLANNING")
    _require(p["master_seed"], 42, "master seed")
    _require(p["seed_sequence"],
             "SeedSequence([42, hazard_index, split_code, realization_index]); hazard_index follows hazards_in_seed_order; planning=0, evaluation=1",
             "seed stream")
    _require(m["production"]["mapping"], "JULY_UTILITY_CONSTRAINED_92", "mapping")
    _require(m["production"]["gate"], "G1_BASELINE_050: e=f*F_0.5*C_14Core", "gate")
    _require(m["production"]["functional_threshold"], 0.5, "functional threshold")
    _require(m["production"]["crews"],
             "C57 pooled regional resource, 57 crews at frozen active origins", "crew baseline")
    _require(m["production"]["integration"], "event-exact left rectangle", "integration")
    ga = m["GA"]
    for key, expected in {"planning_only_on": "2pc50", "planning_N": 64,
                          "population": 100, "generations": 100,
                          "crossover_probability": 0.8, "mutation_probability": 0.2,
                          "tournament_size": 3, "seeds": [42, 43, 44, 45, 46],
                          "legacy_station_completion_surrogate": False}.items():
        _require(ga[key], expected, "GA." + key)
    _require(m["strategies"]["scheduled"], SCHEDULED, "strategies")
    _require(m["strategies"]["baseline_trajectory_count"], 36000, "baseline count")
    _require(m["resource_sensitivity"]["additional_trajectory_count"], 48000, "OFAT count")
    _require(m["resource_sensitivity"]["crew_scales_at_duration_1"],
             [0.5, 1.0, 1.5, 2.0], "crew scales")
    _require(m["resource_sensitivity"]["duration_scales_at_crew_1"],
             [0.75, 1.0, 1.25, 1.5], "duration scales")
    _require(m["offline_robustness"]["2pc50_C57_mapping_cases"], MAPPINGS, "mappings")
    _require(m["offline_robustness"]["2pc50_C57_gate_cases"],
             {"G0_NO_GATE": "e=f", "G1_BASELINE_050": "threshold 0.5 and 14 sources",
              "G2_RELAXED_005": "threshold 0.05 and 14 sources",
              "G3_STRICT_075": "threshold 0.75 and 14 sources"}, "gates")
    _require(m["horizon"]["base_hours"], 480, "horizon base")
    _require(m["horizon"]["evaluation"],
             "after all scheduled completions are known but before service integration, one H_eval=max(480, ceil(max completion across all hazards, samples, eight strategies and OFAT resource cases)); same horizon for every evaluation comparison",
             "common horizon")
    _require(_git("rev-parse", "archive/ijdrr-submission-20260722", cwd=repo),
             ARCHIVE_COMMIT, "local July archive")
    return m, _sha(path)


def validate_final_inputs(matrix: dict, cfg, repo: Path, output: Path) -> dict:
    """Read current inputs and write one manifest; never sample or dispatch."""
    from C257H_Project_Main import (
        _revision_context, build_W_matrix, load_mapping, load_pga, run_stage_0,
    )

    repo = repo.resolve()
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Formal output directory must be new or empty for dry validation")
    if cfg.REVISION_TRIAL or not cfg.REVISION_EVENT_PATH or cfg.RUN_SENSITIVITY_ANALYSIS:
        raise ValueError("Trial, legacy or legacy sensitivity path is active")
    if not all(Path(x).is_file() for x in [cfg.DEVICES_CSV, cfg.PGA_CSV,
                                           cfg.MAP_TRACT_SUB_CSV,
                                           cfg.JULY_BASELINE_MAPPING_CSV]):
        raise ValueError("A required July92 input is missing")
    stage0 = run_stage_0(cfg)
    context = _revision_context(cfg, stage0)
    _require(len(stage0["sub_index"]), 92, "actual station count")
    _require(len(set(map(str, stage0["sub_index"]))), 92, "unique station IDs")
    _require(context["G"].number_of_nodes(), 92, "actual graph nodes")
    _require(context["G"].number_of_edges(), 318, "actual graph edges")
    _require(len(context["sources"]), 14, "actual Core sources")
    _require(len(stage0["tract_index"]), 2315, "actual tract rows")
    _require(len(set(map(str, stage0["tract_index"]))), 2315, "unique tract IDs")
    _require(len(context["origins"]), 57, "actual crews")
    _require(tuple(stage0["W_mat"].shape), (2315, 92), "production mapping dimensions")
    july, tract_ids, station_ids = build_W_matrix(load_mapping(cfg.JULY_BASELINE_MAPPING_CSV))
    _require(tuple(july.shape), (2315, 92), "July baseline dimensions")
    _require(set(map(str, tract_ids)), set(map(str, stage0["tract_index"])), "July tract set")
    _require(set(map(str, station_ids)), set(map(str, stage0["sub_index"])), "July station set")
    pga = load_pga(cfg.PGA_CSV, cfg.SCENARIOS)
    pga.index = pga.id.astype(str)
    if pga.index.has_duplicates or not set(map(str, stage0["sub_index"])) <= set(pga.index):
        raise ValueError("Formal PGA station IDs are incomplete or duplicated")
    pga = pga.reindex(list(map(str, stage0["sub_index"])))
    for hazard in matrix["physical_samples"]["hazards_in_seed_order"]:
        col = "pga_" + hazard
        if col not in pga or pga[col].isna().any() or not np.isfinite(pga[col].to_numpy(float)).all():
            raise ValueError(f"Formal PGA incomplete: {col}; no zero-fill allowed")
    paths = [cfg.DEVICES_CSV, cfg.PGA_CSV, cfg.MAP_TRACT_SUB_CSV,
             cfg.JULY_BASELINE_MAPPING_CSV, cfg.CEC_GRAPH_EDGES_CSV,
             cfg.CEC_GRAPH_NODES_CSV, cfg.SOURCE_NODES_CSV,
             cfg.TRAVEL_BASE_TO_TASK_CSV, cfg.TRAVEL_TASK_TO_TASK_CSV,
             cfg.STAGE45_DEPOT_INPUT_CSV, cfg.STAGE45_ACTIVE_CREW_BASES_CSV,
             cfg.STAGE45_EXPANDED_CREW_ORIGINS_CSV, cfg.HOSPITAL_TRACTS_CSV,
             cfg.SVI_CSV]
    hashes = {str(Path(x).resolve().relative_to(repo)): _sha(Path(x)) for x in paths}
    _require(_git("rev-parse", "archive/ijdrr-submission-20260722", cwd=repo),
             ARCHIVE_COMMIT, "archive unchanged")
    result = {
        "status": "PASS_DRY_VALIDATION_NO_SAMPLING_OR_SCHEDULING",
        "matrix_id": matrix["matrix_id"],
        "matrix_sha256": _sha(repo / "FINAL_EXPERIMENT_MATRIX.json"),
        "validation_source_commit_sha": _git("rev-parse", "HEAD", cwd=repo),
        "actual_executable_commit_sha": "RECORDED_AFTER_WIRING_COMMIT",
        "protected_archive_sha": ARCHIVE_COMMIT,
        "counts": {"stations": 92, "edges": 318, "tracts": 2315,
                   "Core_sources": 14, "baseline_crews": 57,
                   "evaluation_physical": 4000, "planning_physical": 64,
                   "baseline_trajectories": 36000, "additional_OFAT_trajectories": 48000,
                   "GA_seeds": 5},
        "production_mapping": cfg.MAPPING_METHOD,
        "production_gate_threshold": cfg.FUNCTIONAL_THRESHOLD,
        "input_sha256": hashes,
        "frozen_context_hash": context["hash"],
        "output_directory_new_or_empty_before_validation": True,
        "trial_flags_active": False,
        "legacy_sensitivity_active": False,
        "physical_samples_generated": 0,
        "GA_executed": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "FINAL_EXECUTION_VALIDATION.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def configure_formal(cfg, matrix: dict, output: Path) -> None:
    """Set executable controls exclusively from the committed matrix values."""
    cfg.REVISION_EVENT_PATH = True
    cfg.REVISION_TRIAL = False
    cfg.REVISION_FORMAL = True
    cfg.REVISION_FINAL_MATRIX_FROZEN = True
    cfg.REVISION_MATRIX_ID = matrix["matrix_id"]
    cfg.REVISION_PLANNING_HAZARD = matrix["physical_samples"]["planning_hazard"]
    cfg.SCENARIOS = tuple(matrix["physical_samples"]["hazards_in_seed_order"])
    cfg.N_MC = matrix["physical_samples"]["N_EVAL_per_hazard"]
    cfg.REVISION_PLANNING_N = matrix["physical_samples"]["N_PLANNING"]
    cfg.RNG_SEED = matrix["physical_samples"]["master_seed"]
    cfg.GA_POP_SIZE = matrix["GA"]["population"]
    cfg.GA_N_GEN = matrix["GA"]["generations"]
    cfg.GA_CXPB = matrix["GA"]["crossover_probability"]
    cfg.GA_MUTPB = matrix["GA"]["mutation_probability"]
    cfg.REVISION_GA_TOURNAMENT_SIZE = matrix["GA"]["tournament_size"]
    cfg.REVISION_GA_SEEDS = tuple(matrix["GA"]["seeds"])
    cfg.TIME_END_HR = matrix["horizon"]["base_hours"]
    cfg.FUNCTIONAL_THRESHOLD = matrix["production"]["functional_threshold"]
    cfg.RUN_SENSITIVITY_ANALYSIS = False
    cfg.REVISION_OFFLINE_EVALUATION = False  # no offline views before station archives
    cfg.OUTPUT_DIRECTORY = str(output.resolve())
    _require(cfg.MAPPING_METHOD, matrix["production"]["mapping"], "active production mapping")
    _require(cfg.MAP_TRACT_SUB_CSV.endswith("JULY_UTILITY_CONSTRAINED_92.csv"), True,
             "production mapping file")
    _require(cfg.SOURCE_GATE_ENABLED, True, "source gate active")


def require_dry_validation(matrix: dict, repo: Path, output: Path) -> str:
    """Refuse formal work if frozen inputs or tracked executable code changed."""
    path = output / "FINAL_EXECUTION_VALIDATION.json"
    if not path.is_file():
        raise ValueError("Run --validate-final-matrix on a new output directory first")
    record = json.loads(path.read_text(encoding="utf-8"))
    _require(record["status"], "PASS_DRY_VALIDATION_NO_SAMPLING_OR_SCHEDULING", "dry validation")
    _require(record["matrix_id"], matrix["matrix_id"], "validated matrix")
    _require(record["matrix_sha256"], _sha(repo / "FINAL_EXPERIMENT_MATRIX.json"), "matrix hash")
    _require(record["protected_archive_sha"], ARCHIVE_COMMIT, "archive SHA")
    for relative, digest in record["input_sha256"].items():
        path = repo / relative
        if not path.is_file() or _sha(path) != digest:
            raise ValueError(f"Validated input changed: {relative}")
    if _git("diff", "--name-only", cwd=repo) or _git("diff", "--cached", "--name-only", cwd=repo):
        raise ValueError("Executable tracked worktree must be clean before formal execution")
    executable_sha = _git("rev-parse", "HEAD", cwd=repo)
    if executable_sha == FREEZE_COMMIT:
        raise ValueError("Formal entry wiring must be committed before execution")
    return executable_sha
