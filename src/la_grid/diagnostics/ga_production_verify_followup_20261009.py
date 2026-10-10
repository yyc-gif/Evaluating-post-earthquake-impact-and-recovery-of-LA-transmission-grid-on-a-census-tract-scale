"""Independent production-path audit of a newly observed local-search candidate.

Only existing frozen 64 planning realizations. Evaluate ALL saved samples through
independent pandas/NetworkX source-gate path and the compiled GA exact kernel.
No new physical draws, policy promotion or candidate reselection.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_realization_scheduling import RealizationInputs
from la_grid.revision.r1_source_gate import evaluate_source_gate
from la_grid.revision.r1_ga_revision import evaluate_direct_population_burden_aggregate
from la_grid.revision.r1_ga_exact_kernel import _one_sample

ROOT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"
CANDIDATE=ROOT/"ILS_BEST_SEED304_PLANNING_CANDIDATE.json"
FROZEN=REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json"

def main():
    kernel,inc,quality=load()
    candidate=json.loads(CANDIDATE.read_text(encoding="utf-8"))
    baseline=json.loads(FROZEN.read_text(encoding="utf-8"))
    sequences={
        "ils-new-best":candidate["sequence"],
        "frozen-ga-reference":baseline["sequence"],
    }
    context,decoder,identity=execution_context(kernel.ids)
    def gate(raw):
        return evaluate_source_gate(raw,context["graph"],context["sources"],threshold=.5)
    all_rows=[]
    for label,seq in sequences.items():
        assert len(seq)==92 and set(seq)==set(kernel.ids)
        expected=(candidate if label=="ils-new-best" else baseline)["sequence_sha256"]
        assert old.identity(seq)==expected
        order=np.array([kernel.index[s] for s in seq],dtype=np.int64)
        loss=-kernel.score(seq)
        target=candidate["loss_hr"] if label=="ils-new-best" else baseline["planning_loss_hr"]
        assert abs(loss-target)<1e-9,(label,loss,target)
        for b in range(64):
            realization=RealizationInputs(f"2pc50__planning_{b:04}",
                pd.Series(kernel.damage[b],index=kernel.ids),
                pd.Series(kernel.duration[b],index=kernel.ids))
            production=evaluate_direct_population_burden_aggregate(
                sequence=seq,realization=realization,
                crew_origin_ids=context["origins"],base_to_task_hr=context["base"],
                task_to_task_hr=context["task"],horizon_hr=kernel.horizon,
                source_gate=gate,station_population_mass=kernel.station_mass,
                population_resolved_mass=kernel.total_mass)
            exact=_one_sample(order,kernel.damage[b],kernel.duration[b],
                kernel.origin_index,kernel.base,kernel.travel,
                kernel.neighbor_offset,kernel.neighbors,kernel.source_flag,
                kernel.station_mass,kernel.total_mass,kernel.horizon)
            assert np.isfinite(production) and abs(production-exact)<1e-8,(label,b,production,exact)
            all_rows.append(dict(sequence=label,sequence_sha256=expected,
                planning_realization=b,production_loss_hr=float(production),
                compiled_loss_hr=float(exact),absolute_error_hr=float(abs(production-exact))))
        prod_mean=float(np.mean([x["production_loss_hr"] for x in all_rows if x["sequence"]==label]))
        assert abs(prod_mean-target)<1e-8,(label,prod_mean,target)
    a=np.array([x["production_loss_hr"] for x in all_rows if x["sequence"]=="ils-new-best"])
    b=np.array([x["production_loss_hr"] for x in all_rows if x["sequence"]=="frozen-ga-reference"])
    differences=a-b
    output=dict(status="ALL_64_PRODUCTION_PARITY_PASS",
       physical_sampling=False,formal_candidate_replaced=False,
       planning_realizations=64,
       ils_loss_hr=float(a.mean()),frozen_ga_loss_hr=float(b.mean()),
       improvement_hr=float(-differences.mean()),
       improvement_fraction_percent=float(-100*differences.mean()/b.mean()),
       new_lower_than_ga_samples=int((differences< -1e-9).sum()),
       new_higher_than_ga_samples=int((differences>1e-9).sum()),
       exact_tie_samples=int((abs(differences)<=1e-9).sum()),
       max_absolute_model_parity_error_hr=max(r["absolute_error_hr"] for r in all_rows),
       ils_sha=candidate["sequence_sha256"],
       ga_sha=baseline["sequence_sha256"],
       frozen_model_context_identity=identity)
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/"ILS_NEW_CANDIDATE_PRODUCTION_PARITY.json").write_text(
        json.dumps(output,indent=2)+"\n",encoding="utf-8")
    (ROOT/"ILS_NEW_CANDIDATE_PER_REALIZATION.json").write_text(
        json.dumps(dict(rows=all_rows),indent=2)+"\n",encoding="utf-8")
    print("PRODUCTION_PARITY_RESULT",json.dumps(output),flush=True)

if __name__=="__main__":main()
