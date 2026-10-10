"""Feasible one-priority interventions, not altered completion-time trajectories."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_research_collect_20261009 import ROOT, long_path, save
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_search_budget_sensitivity import identity, per_sample
from la_grid.diagnostics.ga_research_mechanism_20261009 import trace
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_realization_scheduling import RealizationInputs
from la_grid.revision.r1_ga_revision import evaluate_direct_population_burden_aggregate
from la_grid.revision.r1_source_gate import evaluate_source_gate

OUT = ROOT/"continuation"
STATION = "301745"


def main():
    k, _, _, _ = load()
    context, decoder, _ = execution_context(k.ids)
    origins = decoder.origins(context["origins"])
    parents = dict(
        FrozenGA=json.loads((REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json").read_text()),
        FirstILS=json.loads((ROOT/"ILS_BEST_SEED304_PLANNING_CANDIDATE.json").read_text()),
        RefinedILS=json.loads((ROOT/"ILS_REFINED_BEST_SEED304_PLANNING_CANDIDATE.json").read_text()))
    assert parents["FrozenGA"]["sequence"].index(STATION)==62
    assert parents["FirstILS"]["sequence"].index(STATION)==parents["RefinedILS"]["sequence"].index(STATION)==21
    baseline = pd.read_csv(long_path(OUT/"ALL64_EXACT_LOSS_COMPONENTS.csv"))
    def gate(raw):
        return evaluate_source_gate(raw, context["graph"], context["sources"], threshold=.5)
    records = []
    per_state = []
    for name, target in (("FrozenGA",21), ("FirstILS",62), ("RefinedILS",62)):
        parent = parents[name]
        seq = list(parent["sequence"])
        old = seq.index(STATION)
        seq.insert(target, seq.pop(old))
        assert len(seq)==92 and set(seq)==set(k.ids) and seq.index(STATION)==target
        assert [s for s in seq if s!=STATION] == [s for s in parent["sequence"] if s!=STATION]
        compiled = per_sample(k, seq)
        production = []
        for b in range(64):
            realized = RealizationInputs(f"2pc50__planning_{b:04}",
                pd.Series(k.damage[b], index=k.ids), pd.Series(k.duration[b], index=k.ids))
            value = evaluate_direct_population_burden_aggregate(sequence=seq,
                realization=realized, crew_origin_ids=context["origins"],
                base_to_task_hr=context["base"], task_to_task_hr=context["task"],
                horizon_hr=k.horizon, source_gate=gate, station_population_mass=k.station_mass,
                population_resolved_mass=k.total_mass)
            assert np.isfinite(value) and abs(value-compiled[b])<1e-8
            production.append(value)
        reference = baseline[baseline.strategy.eq(name)].set_index("realization").loc[range(64),"L_total"].to_numpy()
        delta = np.array(production)-reference
        components, details = trace(k,context,decoder,origins,seq,15)
        original_components = baseline[(baseline.strategy==name)&(baseline.realization==15)].iloc[0]
        label = f"{name}_move_{STATION}_{old}_to_{target}"
        station = next(s for s in details["station_schedule"] if s["station"]==STATION)
        save(OUT/f"{label}_SAMPLE15_EVENTS.json", details)
        record = dict(label=label, parent=name, parent_sequence_sha256=parent["sequence_sha256"],
            sequence=seq, sequence_sha256=identity(seq), intervention_station=STATION,
            original_full_priority_index=old, counterfactual_full_priority_index=target,
            all_other_relative_priorities_unchanged=True, scheduler_unchanged=True,
            original_duration_and_damage_unchanged=True,
            production_mean_loss_hr=float(np.mean(production)),
            mean_counterfactual_minus_parent_hr=float(delta.mean()),
            sample15_delta_hr=float(delta[15]), sample15_station_completion_hr=station["finish_hr"],
            sample15_component_changes_hr={c:float(components[c]-original_components[c]) for c in (
                "L_self","L_threshold","L_source","L_total")},
            improved_realizations=int((delta < -1e-9).sum()), worsened_realizations=int((delta > 1e-9).sum()),
            max_production_compiled_error_hr=float(np.max(np.abs(np.array(production)-compiled))),
            formal_candidate_promoted=False)
        records.append(record)
        per_state.extend(dict(label=label, realization=b, production_loss_hr=float(production[b]),
            compiled_loss_hr=float(compiled[b]), counterfactual_minus_parent_hr=float(delta[b])) for b in range(64))
        print("FEASIBLE_PRIORITY_INTERVENTION", label, record["sample15_delta_hr"], record["mean_counterfactual_minus_parent_hr"], flush=True)
    save(OUT/"CONTROLLED_PRIORITY_INTERVENTIONS.json", dict(status="ALL192_NATIVE_PRODUCTION_COUNTERFACTUAL_PARITY_PASS",
        design="Three declared priority-index insertions; no search or best-candidate selection",
        original_planning_samples=64, physical_samples_generated=0,
        production_sample_calls=192, compiled_sample_calls=192, loader_mean_calls=8,
        interventions=records,
        causal_scope="Effect of the specified full feasible priority edit includes all scheduler cascades; not an isolated restoration-time effect"))
    pd.DataFrame(per_state).to_csv(long_path(OUT/"CONTROLLED_PRIORITY_PER_REALIZATION.csv"), index=False)


if __name__ == "__main__":
    main()
