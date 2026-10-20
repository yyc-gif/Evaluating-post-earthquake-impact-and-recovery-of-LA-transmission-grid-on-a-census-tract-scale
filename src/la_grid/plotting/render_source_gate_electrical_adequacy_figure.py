"""Render the facility-level electrical-adequacy evidence figure.

Presentation only: reads the retained SCE benchmark table and does not execute
hazard, recovery, scheduling, mapping, or source-gate calculations.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import la_grid.plotting.Project_Visualizer as july
from la_grid.paths import REPO_ROOT as ROOT

BENCHMARK = ROOT / "results" / "capacity" / "CONNECTED_VS_ELECTRICAL_CONSTRAINT_BENCHMARK.csv"
CANONICAL = ROOT / "results" / "figures"
SUITE = ROOT / "results" / "revised_suite" / "LA_Grid_Revised_Suite_20260925"
STAGE = SUITE / "Stage 3 Output_expanded"
SUPP = SUITE / "Submission_Package" / "Supplementary_Figures"
STEM = "vis_source_gate_connected_vs_facility_loading"


def _load_level_a() -> pd.DataFrame:
    table = pd.read_csv(BENCHMARK, dtype={"station_id": str})
    direct = table.loc[
        table["evidence_level"].eq("A")
        & table["direct_benchmark_eligible"].astype(str).str.lower().eq("true")
        & table["has_simultaneous_demand_and_limit"].astype(str).str.lower().eq("true")
    ].copy()
    direct["provider_loading_percent"] = pd.to_numeric(
        direct["provider_loading_percent"], errors="raise"
    )
    assert len(table) == 35
    assert len(direct) == 34
    assert direct["station_id"].nunique() == 28
    assert (direct["constraint_status"] == "above documented limit").sum() == 1
    assert direct.loc[direct["constraint_status"].eq("above documented limit"), "facility"].tolist() == ["OLINDA 66/12"]
    rsq = table.loc[table["evidence_level"].eq("B")]
    assert len(rsq) == 1
    assert not bool(rsq.iloc[0]["direct_benchmark_eligible"])

    parsed = direct["facility"].astype(str).str.extract(
        r"^(?P<base>.+?)\s+\d+(?:\.\d+)?/(?P<low>\d+(?:\.\d+)?)$"
    )
    direct["display_station"] = parsed["base"].fillna(direct["facility"]).str.strip()
    direct["low_side_kv"] = pd.to_numeric(parsed["low"], errors="coerce")
    if direct["low_side_kv"].isna().any():
        raise ValueError("Unable to parse low-side voltage class from a Level-A facility label")
    return direct.sort_values("provider_loading_percent", ascending=True).reset_index(drop=True)


def render() -> tuple[Path, Path]:
    july.apply_publication_style()
    data = _load_level_a()
    y = np.arange(len(data))
    loading = data["provider_loading_percent"].to_numpy(float)
    is_olinda = data["facility"].eq("OLINDA 66/12").to_numpy()

    fig, ax = plt.subplots(
        figsize=july.get_figsize("COMPOSITE_FULL_DENSE", width_cm=18.5, height_cm=15.5)
    )
    ax.hlines(y, 0, loading, color="#b9c7d5", linewidth=0.65, zorder=1)

    markers = ("o", "s", "^", "D", "P", "v")
    voltage_classes = sorted(data["low_side_kv"].dropna().unique())
    marker_by_voltage = {v: markers[i % len(markers)] for i, v in enumerate(voltage_classes)}
    for voltage in voltage_classes:
        mask = data["low_side_kv"].eq(voltage).to_numpy() & ~is_olinda
        ax.scatter(
            loading[mask], y[mask], s=20, marker=marker_by_voltage[voltage],
            color="#377eb8", edgecolor="white", linewidth=0.4, zorder=3,
            label=f"{voltage:g} kV low-side",
        )

    ax.scatter(
        loading[is_olinda], y[is_olinda], s=48, marker="*",
        color="#d95f02", edgecolor="white", linewidth=0.5, zorder=4,
        label="OLINDA above planning limit",
    )
    ax.axvline(
        100.0, color="#555555", linewidth=1.0, linestyle="--", zorder=2,
        label="Provider-defined planning limit (100%)",
    )

    oi = int(np.flatnonzero(is_olinda)[0])
    ax.annotate(
        "109.04%", xy=(loading[oi], y[oi]), xytext=(4, 0),
        textcoords="offset points", ha="left", va="center",
        fontsize=july.FS_ANNOTATION, fontweight="semibold", color="#b44700",
    )
    ax.set_yticks(y)
    ax.set_yticklabels(data["display_station"], fontsize=july.FS_TICK)
    ax.set_xlim(0, max(116.0, float(loading.max()) + 7.0))
    ax.set_ylim(-0.8, len(data) - 0.1)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color="#dddddd", linewidth=0.4)
    july.style_axis(
        ax,
        title="SCE planning loading for retained source-reachable facilities\n"
              "Marker shape denotes low-side voltage class",
        xlabel="Provider-reported facility loading (%)",
        ylabel="SCE station",
    )
    legend = ax.legend(loc="lower right", frameon=True, borderpad=0.5, handletextpad=0.5)
    july.format_legend(legend)
    fig.subplots_adjust(left=0.22, right=0.985, bottom=0.09, top=0.92)

    CANONICAL.mkdir(parents=True, exist_ok=True)
    july.save_plot(fig, str(CANONICAL), STEM + ".png")
    if SUITE.is_dir():
        for suffix in (".png", ".pdf"):
            source = CANONICAL / (STEM + suffix)
            if not source.is_file() or source.stat().st_size == 0:
                raise RuntimeError(f"Missing figure output: {source}")
            for folder in (STAGE, SUPP):
                folder.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, folder / source.name)
    return CANONICAL / (STEM + ".png"), CANONICAL / (STEM + ".pdf")


if __name__ == "__main__":
    png, pdf = render()
    print(png)
    print(pdf)
