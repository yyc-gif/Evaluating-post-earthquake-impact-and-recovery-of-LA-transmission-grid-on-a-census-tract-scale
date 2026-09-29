"""Read-only station-fragility connectivity reliability on the frozen July92 graph.

This is an initial-state topology MC, not a recovery/crew/GA execution. The
production gate and all formal physical samples remain unchanged.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

from la_grid.diagnostics.r1_dynamic_topology_kernel import _reachable, station_independent_routes_mask
from la_grid.diagnostics.r1_formal_dynamic_topology import _graph_arrays

ROOT = Path("Formal_Experiment_20260923")
HAZARDS = ("Northridge", "SanFernando", "LongBeach", "2pc50")
N_MC = 100_000
IDS_FILE = ROOT / "Stage 1 Output_expanded" / "physical_inputs_2pc50.npz"
PGA_FILE = Path("Data/Substations_PGA_IDW_CEC_expanded.csv")
MAP_FILE = Path("Data/JULY_UTILITY_CONSTRAINED_92.csv")


@njit(cache=True)
def _forced_importance_counts(states, source_flag, adjacency, degree):
    """Exact paired forcing of each station with all other states held fixed.

    C_i includes station i's own functionality, matching the production gate.
    This returns the 92x92 numerator counts for I[j,i].
    """
    n = states.shape[1]
    counts = np.zeros((n, n), dtype=np.int64)
    for row in range(states.shape[0]):
        active = states[row].copy()
        for j in range(n):
            active[j] = True
            _, _, reachable_on = _reachable(active, active & source_flag, adjacency, degree, -1)
            active[j] = False
            _, _, reachable_off = _reachable(active, active & source_flag, adjacency, degree, -1)
            for i in range(n):
                counts[j, i] += int(active[i] or i == j) * int(reachable_on[i] > 0) - int(active[i]) * int(reachable_off[i] > 0)
            active[j] = states[row, j]
    return counts


def _mapped_weights(ids):
    mapping = pd.read_csv(MAP_FILE, dtype={"tract_id": str, "substation_id": str})
    if mapping.tract_id.nunique() != 2315:
        raise ValueError("Production mapping does not cover 2,315 tracts")
    tracts = sorted(mapping.tract_id.unique())
    tid = {x: i for i, x in enumerate(tracts)}
    sid = {x: i for i, x in enumerate(ids)}
    weight = np.zeros((len(tracts), len(ids)), dtype=np.float64)
    population = np.full(len(tracts), np.nan)
    for row in mapping.itertuples(index=False):
        weight[tid[row.tract_id], sid[row.substation_id]] += float(row.weight)
        ix = tid[row.tract_id]
        if np.isnan(population[ix]):
            population[ix] = float(row.population)
        elif population[ix] != float(row.population):
            raise ValueError("Population varies within tract mapping row")
    if not np.allclose(weight.sum(axis=1), 1, atol=1e-9):
        raise ValueError("Production mapping has non-unit row sums")
    if not np.isfinite(population).all() or (population < 0).any():
        raise ValueError("Invalid tract population")
    pop_exposure = population @ weight / population.sum()
    tract_exposure = weight.mean(axis=0)
    return tracts, weight, population, pop_exposure, tract_exposure


def _fragility_probability(frame, hazard):
    # Mirror the production five-DS probability cleanup.  The DS2 shortcut is
    # not exact when exceedance curves cross at a station's scenario PGA.
    from la_grid.diagnostics.fragility_connectivity_audit import production_ds_probabilities
    vintage = "" if hazard == "2pc50" else "_old"
    pga = frame[f"PGA_{hazard}"].to_numpy(float)
    mu = frame[[f"mu_DS{i}{vintage}" for i in range(1, 5)]].to_numpy(float)
    beta = frame[[f"beta_DS{i}{vintage}" for i in range(1, 5)]].to_numpy(float)
    _, ds = production_ds_probabilities(pga, mu, beta)
    p = ds[:, 0] + ds[:, 1]
    if not ((p >= 0) & (p <= 1)).all():
        raise ValueError("Invalid station functionality probability")
    return p


def _characterize(states, source_flag, eu, ev, adj, deg):
    n_samples, n = states.shape
    connected = np.zeros((n_samples, n), dtype=np.uint8)
    routes = np.zeros((n_samples, n), dtype=np.int8)
    source_count = np.zeros((n_samples, n), dtype=np.uint8)
    for k, active in enumerate(states):
        _, _, count = _reachable(active, active & source_flag, adj, deg, -1)
        connected[k] = (count > 0).astype(np.uint8)
        source_count[k] = count.astype(np.uint8)
        routes[k] = station_independent_routes_mask(active, source_flag, eu, ev).astype(np.int8)
    if ((connected > 0) & ~states).any():
        raise AssertionError("Inactive station marked source-connected")
    if ((routes == 0) != (connected == 0)).any():
        # Active Core sources are recorded as -1, never zero.
        raise AssertionError("Route and source-connectivity identity failed")
    return connected, routes, source_count


def _formal_states(hazard, station_ids, source_flag, eu, ev, adj, deg):
    path = ROOT / "Stage 1 Output_expanded" / f"physical_inputs_{hazard}.npz"
    with np.load(path, allow_pickle=False) as z:
        if z["station_ids"].astype(str).tolist() != station_ids:
            raise ValueError("Formal sample station order differs")
        ds = z["evaluation_ds"]
    if ds.shape != (92, 1000):
        raise ValueError("Formal evaluation sample shape differs")
    formal_states = (ds.T <= 1)
    con, route, count = _characterize(formal_states, source_flag, eu, ev, adj, deg)
    # Check every frozen t=0 production trajectory against recomputed F/C.
    for k in range(1000):
        trajectory = ROOT / "Formal_Trajectories" / hazard / "C57_D1" / "hospital-first" / f"{hazard}__evaluation_{k:04d}.npz"
        with np.load(trajectory, allow_pickle=False) as z:
            if z["station_ids"].astype(str).tolist() != station_ids or float(z["event_time_hr"][0]) != 0:
                raise ValueError("Frozen trajectory identity differs")
            if not np.array_equal(z["F"][0].astype(bool), formal_states[k]):
                raise AssertionError("Formal t=0 F differs from DS<=1")
            if not np.array_equal(z["C"][0].astype(bool), con[k].astype(bool)):
                raise AssertionError("Formal t=0 C differs from recomputed gate")
    return formal_states, con, route, count


def main():
    with np.load(IDS_FILE, allow_pickle=False) as z:
        ids = z["station_ids"].astype(str).tolist()
    eu, ev, adj, deg, sf, intact = _graph_arrays(ids)
    if len(ids) != 92 or len(eu) != 318 or int(sf.sum()) != 14:
        raise ValueError("July topology/source identity differs")
    frame = pd.read_csv(PGA_FILE, dtype={"ID": str}).set_index("ID").loc[ids]
    if frame.index.tolist() != ids:
        raise ValueError("Fragility station order differs")
    tracts, weight, pop, pop_exposure, tract_exposure = _mapped_weights(ids)
    station_rows, tract_rows, route_rows, importance_rows = [], [], [], []
    summary = {"n_mc_per_hazard": N_MC, "graph_nodes": 92, "graph_edges": 318, "core_sources": 14,
               "pga_sha256": hashlib.sha256(PGA_FILE.read_bytes()).hexdigest(),
               "mapping_sha256": hashlib.sha256(MAP_FILE.read_bytes()).hexdigest(), "hazards": {}}
    for hidx, hazard in enumerate(HAZARDS):
        p = _fragility_probability(frame, hazard)
        rng = np.random.default_rng(np.random.SeedSequence([20260926, hidx, 721]))
        states = rng.random((N_MC, 92)) < p
        con, route, source_count = _characterize(states, sf, eu, ev, adj, deg)
        formal_states, formal_con, formal_route, formal_source_count = _formal_states(
            hazard, ids, sf, eu, ev, adj, deg
        )
        # Save all per-sample functional masks and exact route counts locally.
        state_path = ROOT / "Formal_Reviewer_Results" / f"CONNECTIVITY_RELIABILITY_STATES_{hazard}.npz"
        np.savez_compressed(state_path, station_ids=np.array(ids), functional=states,
                            source_connected=con, independent_routes=route,
                            reachable_active_sources=source_count)
        r_conn = con.mean(axis=0)
        functional_count = states.sum(axis=0)
        r_path = np.divide(con.sum(axis=0), functional_count,
                           out=np.full(92, np.nan), where=functional_count > 0)
        # An active Core source is connected to itself by definition. This
        # exact conditional identity also covers a rare source never sampled
        # functional in a finite Monte Carlo draw.
        r_path[sf] = 1.0
        formal_r_conn = formal_con.mean(axis=0)
        formal_den = formal_states.sum(axis=0)
        formal_r_path = np.divide(formal_con.sum(axis=0), formal_den,
                                  out=np.full(92, np.nan), where=formal_den > 0)
        route0 = (route == 0).mean(axis=0)
        route1 = (route == 1).mean(axis=0)
        route2 = (route >= 2).mean(axis=0)
        source_local = (route == -1).mean(axis=0)
        if not np.allclose(route0 + route1 + route2 + source_local, 1, atol=1e-12):
            raise AssertionError("Route-state partition incomplete")
        static_routes = station_independent_routes_mask(
            np.ones(92, dtype=np.bool_), sf, eu, ev
        )
        for i, station in enumerate(ids):
            station_rows.append({"hazard": hazard, "station_id": station, "station_name": frame.loc[station, "NAME"],
                                 "is_core_source": bool(sf[i]), "p_functional_fragility": p[i],
                                 "p_functional_mc": states[:, i].mean(), "R_conn": r_conn[i], "R_path": r_path[i],
                                 "R_conn_formal1000": formal_r_conn[i], "R_path_formal1000": formal_r_path[i],
                                 "formal_functional_count": formal_den[i], "intact_independent_routes": int(static_routes[i]),
                                 "p_kappa_0": route0[i], "p_kappa_1": route1[i], "p_kappa_ge2": route2[i],
                                 "p_local_active_source": source_local[i],
                                 "p_one_route_given_connected_non_source": (route1[i] / max(route1[i]+route2[i], 1e-12)),
                                 "p_multiple_routes_given_connected_non_source": (route2[i] / max(route1[i]+route2[i], 1e-12)),
                                 "population_dependency_weight": pop_exposure[i]})
        tract_path = weight @ r_path
        tract_conn = weight @ r_conn
        tract_one = weight @ route1
        tract_multi = weight @ route2
        for i, tract in enumerate(tracts):
            tract_rows.append({"hazard": hazard, "tract_id": tract, "population": pop[i],
                               "R_path_tract": tract_path[i], "R_conn_tract": tract_conn[i],
                               "mapped_probability_one_route": tract_one[i],
                               "mapped_probability_multiple_routes": tract_multi[i]})
        # Same 100,000 states, same non-j state for both interventions.
        numerator = _forced_importance_counts(states, sf, adj, deg)
        importance = numerator / N_MC
        if (importance < -1e-12).any() or (importance > 1+1e-12).any():
            raise AssertionError("Non-monotone component importance")
        weighted = importance @ pop_exposure
        weighted_downstream = weighted - np.diag(importance) * pop_exposure
        tract_weighted = importance @ tract_exposure
        for j, station_j in enumerate(ids):
            for i, station_i in enumerate(ids):
                importance_rows.append({"hazard": hazard, "forced_station_j": station_j, "target_station_i": station_i,
                                        "I_ij": importance[j, i], "is_direct_self": i == j,
                                        "population_weighted_importance_j": weighted[j],
                                        "population_weighted_downstream_importance_j": weighted_downstream[j],
                                        "tract_weighted_importance_j": tract_weighted[j]})
        for group, mask in (("intact_one_route", static_routes == 1),
                            ("intact_multiple_routes", static_routes >= 2),
                            ("active_core_source", sf)):
            route_rows.append({"hazard": hazard, "intact_route_class": group, "station_count": int(mask.sum()),
                               "mean_R_path": float(r_path[mask].mean()) if mask.any() else np.nan,
                               "population_dependency_weighted_R_path": float(np.average(r_path[mask], weights=pop_exposure[mask])) if pop_exposure[mask].sum() else np.nan,
                               "mean_R_conn": float(r_conn[mask].mean()) if mask.any() else np.nan,
                               "mean_p_functional": float(p[mask].mean()) if mask.any() else np.nan,
                               "mean_p_one_route": float(route1[mask].mean()) if mask.any() else np.nan,
                               "mean_p_multiple_routes": float(route2[mask].mean()) if mask.any() else np.nan})
        # Conditional redundancy within the same sampled functional states.
        for group, mask in (("sampled_one_route", route == 1), ("sampled_multiple_routes", route >= 2)):
            route_rows.append({"hazard": hazard, "intact_route_class": group, "station_count": int(mask.any(axis=0).sum()),
                               "mean_R_path": np.nan, "population_dependency_weighted_R_path": np.nan,
                               "mean_R_conn": np.nan, "mean_p_functional": np.nan,
                               "mean_p_one_route": float(np.mean(mask)),
                               "mean_p_multiple_routes": np.nan})
        summary["hazards"][hazard] = {
            "population_weighted_R_path": float(pop_exposure @ r_path),
            "population_weighted_R_conn": float(pop_exposure @ r_conn),
            "tract_R_path_p05": float(np.quantile(tract_path, .05)),
            "tract_R_path_median": float(np.median(tract_path)),
            "tract_R_path_p95": float(np.quantile(tract_path, .95)),
            "population_weighted_abs_formal1000_MC_difference_R_path_observed": float(
                np.nansum(pop_exposure * abs(r_path-formal_r_path)) /
                pop_exposure[np.isfinite(formal_r_path)].sum()),
            "max_abs_formal1000_MC_difference_R_path_observed": float(np.nanmax(abs(r_path-formal_r_path))),
            "formal1000_stations_without_functional_draw": int((formal_den == 0).sum()),
            "top_downstream_bottlenecks": [{"station_id": ids[j], "importance": float(weighted_downstream[j])}
                                          for j in np.argsort(-weighted_downstream)[:10]],
            "lowest_R_path_tracts": [{"tract_id": tracts[j], "R_path": float(tract_path[j]), "population": float(pop[j])}
                                     for j in np.argsort(tract_path)[:10]],
        }
        print(hazard, summary["hazards"][hazard]["population_weighted_R_path"], flush=True)
    pd.DataFrame(station_rows).to_csv(Path("results/diagnostics/SUBSTATION_CONNECTIVITY_RELIABILITY.csv"), index=False)
    pd.DataFrame(tract_rows).to_csv(Path("results/diagnostics/TRACT_CONNECTIVITY_RELIABILITY.csv"), index=False)
    pd.DataFrame(route_rows).to_csv(Path("results/diagnostics/CONNECTIVITY_ROUTE_RELIABILITY_CROSSWALK.csv"), index=False)
    pd.DataFrame(importance_rows).to_csv(Path("results/diagnostics/CONNECTIVITY_COMPONENT_IMPORTANCE.csv"), index=False)
    (ROOT / "Formal_Reviewer_Results" / "CONNECTIVITY_RELIABILITY_NUMERICAL_SUMMARY.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
