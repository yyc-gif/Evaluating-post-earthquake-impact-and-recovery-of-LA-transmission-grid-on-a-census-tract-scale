"""Event-exact planning-sample influence, without optimizing or changing physics."""
from __future__ import annotations
import itertools
import json
import numpy as np
import pandas as pd
import networkx as nx

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_research_collect_20261009 import ROOT, save
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_search_budget_sensitivity import identity, per_sample
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_realization_scheduling import evaluate_completion_step_functionality
from la_grid.revision.r1_source_gate import evaluate_source_gate

COMPONENTS = ("L_self", "L_threshold", "L_source", "L_total")


def trace(k, context, decoder, origins, sequence, sample):
    finish, arrival, travel, crew, previous, dispatch, *_ = decoder.decode(
        order=decoder.order(sequence), damage=k.damage[sample],
        duration=k.duration[sample], origins=origins)
    clock = np.unique(np.r_[0., finish[np.isfinite(finish) & (finish > 0) & (finish < k.horizon)], k.horizon])
    raw = evaluate_completion_step_functionality(
        damage_state=pd.Series(k.damage[sample], index=k.ids),
        completion_time_hr=pd.Series(finish, index=k.ids), time_hr=clock)
    gate = evaluate_source_gate(raw, context["graph"], context["sources"], threshold=.5)
    mass = k.station_mass / k.total_mass
    integrals = {name: float(np.diff(clock) @ (getattr(gate, name).to_numpy()[:-1] @ mass))
                 for name in COMPONENTS}
    assert abs(sum(integrals[x] for x in COMPONENTS[:3])-integrals["L_total"]) < 1e-8
    events = []
    for j, t in enumerate(clock[:-1]):
        functional = gate.F.iloc[j].eq(1)
        connected = gate.C.iloc[j].eq(1)
        active = set(functional.index[functional])
        components = []
        for comp in nx.connected_components(context["graph"].subgraph(active)):
            sources = sorted(comp & context["sources"])
            indices = [k.index[s] for s in comp]
            components.append(dict(stations=sorted(comp), sources=sources,
                population_dependency_mass=float(k.station_mass[indices].sum()),
                population_dependency_fraction=float(mass[indices].sum())))
        changed = (connected & ~gate.C.iloc[j-1].eq(1)) if j else connected
        completed = np.flatnonzero(np.isclose(finish, t, atol=1e-10, rtol=0))
        events.append(dict(time_hr=float(t), completed_stations=[k.ids[i] for i in completed],
            active_sources=sorted(active & context["sources"]),
            source_connected_stations=sorted(connected.index[connected]),
            newly_source_connected_stations=sorted(changed.index[changed]),
            newly_connected_dependency_mass=float(k.station_mass[changed.to_numpy()].sum()),
            components=components,
            effective_service=float(gate.e.iloc[j].to_numpy() @ mass)))
    schedule = [dict(station=s, damage_state=int(k.damage[sample, i]),
        duration_hr=float(k.duration[sample, i]), finish_hr=float(finish[i]) if np.isfinite(finish[i]) else None,
        arrival_hr=float(arrival[i]) if np.isfinite(arrival[i]) else None,
        travel_hr=float(travel[i]) if np.isfinite(travel[i]) else None, crew_index=int(crew[i]),
        dispatch_rank=int(dispatch[i]), source=s in context["sources"],
        population_dependency_mass=float(k.station_mass[i])) for i, s in enumerate(k.ids)]
    return integrals, dict(events=events, station_schedule=schedule)


def influences(d):
    d = np.asarray(d)
    assert d.shape == (64,) and np.isfinite(d).all()
    total = float(d.sum())
    omitted = []
    for i in range(64):
        mean = (total-d[i])/63
        omitted.append(dict(omitted_realization=i, full_mean_delta_hr=total/64,
            leave_one_out_mean_delta_hr=float(mean),
            ranking_reversed=bool(mean > 0),
            change_in_estimated_mean_hr=float(mean-total/64), sample_delta_hr=float(d[i])))
    exhaustive = []
    for count in (1, 2, 3):
        values = np.array([(total-sum(d[i] for i in idx))/(64-count)
                           for idx in itertools.combinations(range(64), count)])
        exhaustive.append(dict(omitted_count=count, subsets=len(values),
            ga_better_count=int((values > 1e-9).sum()), ils_better_count=int((values < -1e-9).sum()),
            mean_delta_min_hr=float(values.min()), mean_delta_max_hr=float(values.max())))
    targeted = []
    rank = np.argsort(d)
    for count in (1, 2, 3, 5, 10):
        drop = rank[:count]
        targeted.append(dict(omitted_most_beneficial_samples=drop.tolist(),
            retained_mean_delta_hr=float(np.delete(d, drop).mean())))
    return dict(mean_delta_hr=float(d.mean()), median_delta_hr=float(np.median(d)),
        sd_delta_hr=float(d.std(ddof=1)), better_samples=int((d < -1e-9).sum()),
        worse_samples=int((d > 1e-9).sum()), quartiles_hr=np.quantile(d, [.25,.75]).tolist(),
        leave_one_out=omitted, exhaustive_omissions=exhaustive, targeted_omissions=targeted,
        interpretive_scope="Conditional selected-candidate sensitivity; not unbiased external validation")


def main():
    k, _, _, model = load()
    context, decoder, _ = execution_context(k.ids)
    origins = decoder.origins(context["origins"])
    records = {
        "FrozenGA": json.loads((REPO_ROOT/"results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json").read_text()),
        "FirstILS": json.loads((ROOT/"ILS_BEST_SEED304_PLANNING_CANDIDATE.json").read_text()),
        "RefinedILS": json.loads((ROOT/"ILS_REFINED_BEST_SEED304_PLANNING_CANDIDATE.json").read_text()),
    }
    assert all(identity(r["sequence"]) == r["sequence_sha256"] for r in records.values())
    losses = {name: per_sample(k, r["sequence"]) for name, r in records.items()}
    rows = []
    for sample in range(64):
        for name, record in records.items():
            integrals, detail = trace(k, context, decoder, origins, record["sequence"], sample)
            assert abs(integrals["L_total"]-losses[name][sample]) < 1e-8
            rows.append(dict(realization=sample, strategy=name,
                sequence_sha256=record["sequence_sha256"], **integrals))
            if sample == 15:
                save(ROOT/"continuation"/f"SAMPLE15_{name}_EVENTS.json", detail)
        print("EVENT_PARITY", sample, flush=True)
    pd.DataFrame(rows).to_csv(ROOT/"continuation/ALL64_EXACT_LOSS_COMPONENTS.csv", index=False)
    comparison = pd.DataFrame(dict(realization=range(64),
        ds0_exclusions=(k.damage == 0).sum(axis=1), frozen_ga_loss_hr=losses["FrozenGA"],
        first_ils_loss_hr=losses["FirstILS"], refined_ils_loss_hr=losses["RefinedILS"],
        first_ils_minus_ga_hr=losses["FirstILS"]-losses["FrozenGA"],
        refined_ils_minus_ga_hr=losses["RefinedILS"]-losses["FrozenGA"]))
    comparison.to_csv(ROOT/"continuation/ALL64_SAMPLE_INFLUENCE.csv", index=False)
    influence = {name: influences(losses[name]-losses["FrozenGA"])
                 for name in ("FirstILS", "RefinedILS")}
    save(ROOT/"continuation/SAMPLE_INFLUENCE_DIAGNOSTICS.json", influence)
    save(ROOT/"continuation/MODEL_IDENTITY.json", model)
    save(ROOT/"continuation/EXACT_MECHANISM_QA.json", dict(status="ALL192_EVENT_COMPONENT_PARITY_PASS",
        original_planning_horizon_hr=k.horizon, original_planning_samples=64,
        diagnostic_per_sample_compiled_calls=192, loader_reference_mean_calls=8,
        new_physical_samples=0, objective_changed=False, formal_candidate_replaced=False))
    print("COMPLETE", json.dumps({n: {key: influence[n][key] for key in (
        "mean_delta_hr", "median_delta_hr", "better_samples", "worse_samples")}
        for n in influence}), flush=True)


if __name__ == "__main__":
    main()
