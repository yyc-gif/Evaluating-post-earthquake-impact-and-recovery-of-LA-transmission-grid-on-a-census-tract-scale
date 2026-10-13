"""Figures from retained formal results and event archives; no scientific rerun."""

from pathlib import Path
import hashlib
import json

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def render_formal_figures(output_root: Path, tract_ids, population, weights,
                          executable_sha: str) -> dict:
    root = Path(output_root)
    out = root / "Stage 6 Output_expanded"
    out.mkdir(parents=True, exist_ok=True)
    results = pd.read_parquet(root / "Formal_Results" /
                              "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet")
    primary = results.loc[(results.resource_scenario == "C57_D1") &
                          (results.mapping == "M1_UTILITY_003") &
                          (results.gate == "G1_BASELINE_050")].copy()
    if len(primary) != 36000:
        raise ValueError("Formal Stage 6 expected 36,000 baseline metric rows")
    order = ["Northridge", "SanFernando", "LongBeach", "2pc50"]
    strategies = ["unconstrained", "hospital-first", "impact-first", "degree-first",
                  "closeness-first", "betweenness-first", "centrality-first", "random",
                  "direct-community"]
    means = primary.groupby(["hazard", "strategy_id"], sort=False)[
        "population_resolved_mass_weighted_burden_hr"].mean().unstack()
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for ax, hazard in zip(axes.flat, order):
        values = means.loc[hazard, strategies]
        ax.barh(np.arange(len(values)), values.to_numpy(), color="#467b9f")
        ax.set_yticks(np.arange(len(values)), values.index, fontsize=7)
        ax.invert_yaxis()
        ax.set_title(hazard)
        ax.set_xlabel("Mean resolved-mass population burden (h)")
    burden_path = out / "formal_population_burden_by_hazard.png"
    fig.savefig(burden_path, dpi=180)
    plt.close(fig)

    # Mean source-gated population availability on a display-only 1 h grid.
    # Metrics remain the event-exact integrals in Formal_Results.
    ids = np.asarray(list(map(str, tract_ids)), dtype=str)
    pop = np.asarray(population, dtype=float)
    w = np.asarray(weights, dtype=float)
    if len(ids) != 2315 or w.shape != (2315, 92) or pop.shape != (2315,):
        raise ValueError("Formal Stage 6 mapping/population domain changed")
    station_mass = w.T @ pop
    denominator = float(station_mass.sum())
    if denominator <= 0:
        raise ValueError("Formal Stage 6 population mass is zero")
    curves = []
    for strategy in ("unconstrained", "hospital-first", "impact-first", "random"):
        total = np.zeros(481, dtype=float)
        for index in range(1000):
            stem = f"2pc50__evaluation_{index:04d}"
            path = root / "Formal_Trajectories" / "2pc50" / "C57_D1" / strategy / (stem + ".npz")
            with np.load(path, allow_pickle=False) as z:
                t, state = z["event_time_hr"], z["e"]
                if t[0] != 0 or t[-1] != 480 or state.shape[1] != 92:
                    raise ValueError("Formal Stage 6 event archive identity changed")
                positions = np.searchsorted(t, np.arange(481), side="right") - 1
                total += state[positions] @ station_mass / denominator
        mean = total / 1000
        curves.append(pd.DataFrame({"time_hr": np.arange(481), "strategy": strategy,
                                    "mean_population_availability_proxy": mean}))
    curve_df = pd.concat(curves, ignore_index=True)
    curve_path = out / "formal_2pc50_population_availability_curves.csv"
    curve_df.to_csv(curve_path, index=False)
    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    for strategy, group in curve_df.groupby("strategy", sort=False):
        ax.plot(group.time_hr, group.mean_population_availability_proxy, label=strategy)
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Hours since event")
    ax.set_ylabel("Modeled population-weighted availability proxy")
    ax.legend(frameon=False, fontsize=8)
    curve_figure = out / "formal_2pc50_recovery_curves.png"
    fig.savefig(curve_figure, dpi=180)
    plt.close(fig)

    # Retained tract geometry is display-only; it does not enter mapping or metrics.
    geometry = gpd.read_file("Data/LA_Tracts_With_Population.shp")[["GEOID", "geometry"]]
    geometry["tract_id"] = geometry.GEOID.astype(str).str.lstrip("0")
    kpis = pd.read_csv(root / "Stage 5 Output_expanded" / "tract_kpis_2pc50.csv")
    kpis["tract_id"] = kpis.tract_id.astype(str).str.lstrip("0")
    merged = geometry.merge(kpis[["tract_id", "T80"]], on="tract_id", how="inner")
    if len(merged) != 2315:
        raise ValueError("Formal Stage 6 spatial join does not cover all 2,315 tracts")
    fig, ax = plt.subplots(figsize=(9, 7), constrained_layout=True)
    merged.plot(column="T80", ax=ax, cmap="viridis", legend=True, linewidth=0)
    ax.set_title("2pc50: direct-community mean modeled tract T80")
    ax.set_axis_off()
    map_path = out / "formal_2pc50_tract_T80_map.png"
    fig.savefig(map_path, dpi=180)
    plt.close(fig)

    shifts = pd.read_parquet(root / "Formal_Results" / "TRACT_MAPPING_SHIFT.parquet")
    shifts = shifts.loc[(shifts.hazard == "2pc50") &
                        (shifts.strategy_id == "impact-first"),
                        ["tract_id", "mean_M1_minus_M0_burden_hr"]].copy()
    shifts["tract_id"] = shifts.tract_id.astype(str).str.lstrip("0")
    mapped = geometry.merge(shifts, on="tract_id", how="inner")
    if len(mapped) != 2315:
        raise ValueError("Formal Stage 6 mapping-shift map does not cover all tracts")
    vmax = float(np.nanpercentile(np.abs(mapped.mean_M1_minus_M0_burden_hr), 99))
    fig, ax = plt.subplots(figsize=(9, 7), constrained_layout=True)
    mapped.plot(column="mean_M1_minus_M0_burden_hr", ax=ax, cmap="RdBu_r",
                vmin=-vmax, vmax=vmax, legend=True, linewidth=0)
    ax.set_title("2pc50: M1 minus July M0 mean modeled burden (h)")
    ax.set_axis_off()
    shift_path = out / "formal_2pc50_mapping_burden_shift_map.png"
    fig.savefig(shift_path, dpi=180)
    plt.close(fig)
    paths = [burden_path, curve_path, curve_figure, map_path, shift_path]
    payload = {"status": "FORMAL_FROZEN_MATRIX_V1", "executable_code_commit_sha": executable_sha,
               "source_baseline_rows": len(primary), "curve_archive_count": 4000,
               "tract_rows": len(merged), "files_sha256": {
                   p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (out / "FORMAL_FIGURES_INDEX.json").write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return payload
