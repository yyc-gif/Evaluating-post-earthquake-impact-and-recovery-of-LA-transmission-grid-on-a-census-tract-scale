"""Complete deterministic local-neighborhood audit of the discovered ILS best.

Explore all swaps, insertions, inversions, and adjacent block exchanges from
the already observed 92-station chromosome. Existing 64 planning samples only.
This is a feasibility/optimization-quality diagnostic, not final strategy
promotion, global optimality certification, or physical validation.
"""
from __future__ import annotations
import hashlib
import json

from la_grid.paths import REPO_ROOT as ROOT
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_local_refinement_20261009 import refine
from la_grid.diagnostics import ga_search_budget_sensitivity as old

OUT=ROOT/"results/diagnostics/ga_deeper_research_20261009"
SOURCE=OUT/"ILS_BEST_SEED304_PLANNING_CANDIDATE.json"
FROZEN=ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json"

def main():
    candidate=json.loads(SOURCE.read_text(encoding="utf-8"))
    frozen=json.loads(FROZEN.read_text(encoding="utf-8"))
    kernel,inc,quality,_=load()
    seq=tuple(candidate["sequence"])
    assert len(seq)==len(kernel.ids)==92
    assert set(seq)==set(kernel.ids)
    assert old.identity(seq)==candidate["sequence_sha256"]
    assert abs(kernel.score(seq)+candidate["loss_hr"])<1e-9
    result,cache=refine(kernel=kernel,start_sequence=seq,budget=500000,
        folder=OUT/"ils_seed304_deterministic_refinement")
    assert result["best_planning_loss_hr"]<=candidate["loss_hr"]+1e-9
    report=dict(source_commit="13f8ef8e5d244c70a92a06a45540460c736c70f9",
        original_ils_loss_hr=candidate["loss_hr"],
        frozen_ga_loss_hr=frozen["planning_loss_hr"],
        deterministic_refinement_best_loss_hr=result["best_planning_loss_hr"],
        improvement_after_ils_hr=candidate["loss_hr"]-result["best_planning_loss_hr"],
        total_neighbor_evaluations=result["distinct_evaluations"],
        accepted_moves=result["accepted_moves"],
        complete_neighborhood_scan=result["last_scan_complete"],
        local_optimal_up_to_1e_minus_9=result["local_optimal_up_to_1e_minus_9"],
        result_sequence_sha256=result["sequence_sha256"],
        global_optimality_proven=False,
        physical_samples_created=0,formal_strategy_changed=False)
    (OUT/"ILS_DETERMINISTIC_REFINEMENT_DECISION.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("ILS_REFINEMENT_RESULT",json.dumps(report),flush=True)

if __name__=="__main__":
    main()
