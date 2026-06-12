from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors
from matplotlib.transforms import Bbox
from strategy_names import (
    CANONICAL_STRATEGY_LABELS,
    CANONICAL_STRATEGY_ORDER,
    canonical_strategy_key,
    canonical_strategy_label,
)


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "Data"
CLEAN_DIR = PROJECT_ROOT / "Sensitivity Output_clean"
MAIN_DIR = CLEAN_DIR / "Main"
SUPP_DIR = CLEAN_DIR / "Supplementary"
TABLE_DIR = CLEAN_DIR / "Tables"
SUMMARY_PATH = DATA_DIR / "sensitivity_summary_2pc50.csv"
MAPPING_DIAGNOSTICS_PATH = DATA_DIR / "sensitivity_mapping_diagnostics.csv"
SOURCE_GATE_DIAGNOSTICS_PATH = (
    DATA_DIR / "sensitivity_source_gate_diagnostics_2pc50.csv"
)
SOURCE_GATE_SUMMARY_PATH = (
    DATA_DIR / "sensitivity_source_gate_mechanism_summary_2pc50.csv"
)
SENSITIVITY_SCENARIO = "2pc50"
EXPORT_DPI = 600
CM_PER_INCH = 2.54
FIGURE_WIDTH_SINGLE_CM = 8.9
FIGURE_WIDTH_MEDIUM_CM = 13.2
FIGURE_WIDTH_FULL_CM = 18.5
FS_TITLE = 9.5
FS_LABEL = 8.5
FS_TICK = 7.5
FS_LEGEND = 7.5
FS_COLORBAR = 7.5
FS_ANNOTATION = 7.0
FS_TABLE = 7.4
FS_TABLE_HEADER = 7.8

STRATEGY_ORDER = CANONICAL_STRATEGY_ORDER

STRATEGY_STYLE = {
    "centrality-first": {
        "color": "#e41a1c", "linewidth": 1.08, "linestyle": "-.",
        "alpha": 0.82, "zorder": 6, "marker": None,
    },
    "betweenness-first": {
        "color": "#ffd92f", "linewidth": 1.05,
        "linestyle": (0, (5.0, 1.5, 1.2, 1.5)),
        "alpha": 0.82, "zorder": 5, "marker": None,
    },
    "impact-first": {
        "color": "#ff7f00", "linewidth": 1.12, "linestyle": ":",
        "alpha": 0.82, "zorder": 4, "marker": None,
    },
    "degree-first": {
        "color": "#4daf4a", "linewidth": 1.05, "linestyle": "--",
        "alpha": 0.82, "zorder": 7, "marker": None,
    },
    "closeness-first": {
        "color": "#377eb8", "linewidth": 1.05,
        "linestyle": (0, (4.0, 1.6)),
        "alpha": 0.82, "zorder": 8, "marker": None,
    },
    "hospital-first": {
        "color": "#555555", "linewidth": 1.02,
        "linestyle": (0, (2.2, 1.4)),
        "alpha": 0.82, "zorder": 3, "marker": None,
    },
    "random": {
        "color": "lightgray", "linewidth": 1.10, "linestyle": "-",
        "alpha": 0.82, "zorder": 1, "marker": None,
    },
    "GA_Balanced": {
        "color": "#6a3d9a", "linewidth": 1.22, "linestyle": "-",
        "alpha": 0.92, "zorder": 10, "marker": None,
    },
    "GA_HospFirst": {
        "color": "#c51b7d", "linewidth": 1.18, "linestyle": "-",
        "alpha": 0.90, "zorder": 9, "marker": None,
    },
    "GA_Efficiency": {
        "color": "#1b9e77", "linewidth": 1.18, "linestyle": "-",
        "alpha": 0.90, "zorder": 9, "marker": None,
    },
}

STRATEGY_LABELS = CANONICAL_STRATEGY_LABELS

PANEL_CONFIG = [
    (
        "crew_availability",
        "Crew availability",
        r"Crew availability ($K/K_0$)",
    ),
    (
        "repair_time_scale",
        "Repair-time scale",
        "Repair-time scale",
    ),
    (
        "idw_threshold",
        r"IDW threshold ($\theta_W$)",
        r"$\theta_W$",
    ),
    (
        "source_gate_threshold",
        r"Source-gate threshold ($\tau_g$)",
        r"$\tau_g$",
    ),
]

RANK_ROW_ORDER = [group for group, _, _ in PANEL_CONFIG]

GROUP_LABELS = {
    "crew_availability": "crew availability",
    "repair_time_scale": "repair-time scale",
    "idw_threshold": r"IDW $\theta_W$",
    "source_gate_threshold": r"source gate $\tau_g$",
}

EXPECTED_PARAMETER_VALUES = {
    "crew_availability": (0.5, 1.0, 1.5, 2.0),
    "repair_time_scale": (0.75, 1.0, 1.25, 1.5),
    "idw_threshold": (0.05, 0.10, 0.15, 0.20),
    "source_gate_threshold": (0.40, 0.50, 0.60),
}

PARAMETER_TABLE_META = {
    "crew_availability": (
        "Crew availability",
        "(0.5)\u2013(2.0)",
    ),
    "repair_time_scale": (
        "Repair-time scale",
        "(0.75)\u2013(1.50)",
    ),
    "idw_threshold": (
        "IDW threshold theta_W",
        "(0.05)\u2013(0.20)",
    ),
    "source_gate_threshold": (
        "Source-gate threshold tau_g",
        "(0.40)\u2013(0.60)",
    ),
}


def ensure_dirs() -> None:
    for folder in [MAIN_DIR, SUPP_DIR, TABLE_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def cm_to_inch(width_cm: float, height_cm: float) -> tuple[float, float]:
    return width_cm / CM_PER_INCH, height_cm / CM_PER_INCH


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans"],
            "mathtext.fontset": "custom",
            "mathtext.rm": "Arial",
            "mathtext.it": "Arial:italic",
            "mathtext.bf": "Arial:bold",
            "axes.titlesize": FS_TITLE,
            "axes.labelsize": FS_LABEL,
            "xtick.labelsize": FS_TICK,
            "ytick.labelsize": FS_TICK,
            "legend.fontsize": FS_LEGEND,
            "legend.title_fontsize": FS_LEGEND,
            "figure.dpi": 150,
            "savefig.dpi": EXPORT_DPI,
            "axes.unicode_minus": False,
            "axes.linewidth": 0.6,
            "grid.color": "#d9d9d9",
            "grid.linewidth": 0.4,
            "lines.linewidth": 1.2,
            "patch.linewidth": 0.5,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 3.0,
            "ytick.major.size": 3.0,
            "axes.titlepad": 4.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def tiered_export_bbox(fig: plt.Figure) -> Bbox:
    """Keep tight vertical cropping while preserving the assigned width tier."""
    fig.canvas.draw()
    tight = fig.get_tightbbox(fig.canvas.get_renderer())
    target_width = fig.get_figwidth()
    if tight.width >= target_width:
        return tight
    pad_inches = 0.04
    return Bbox.from_bounds(
        tight.x0 - (target_width - tight.width) / 2.0,
        tight.y0 - pad_inches,
        target_width,
        tight.height + 2.0 * pad_inches,
    )


def save(fig: plt.Figure, path: Path) -> None:
    export_bbox = tiered_export_bbox(fig)
    fig.savefig(
        path,
        dpi=EXPORT_DPI,
        bbox_inches=export_bbox,
        pad_inches=0,
        facecolor="white",
        edgecolor="none",
    )
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        fig.savefig(
            path.with_suffix(".pdf"),
            format="pdf",
            bbox_inches=export_bbox,
            pad_inches=0,
            facecolor="white",
            edgecolor="none",
        )
    plt.close(fig)


def fmt_tick(value: float) -> str:
    return f"{value:g}"


def reorder_legend_row_major(
    handles: list,
    labels: list[str],
    ncol: int,
) -> tuple[list, list[str]]:
    """Reorder inputs so Matplotlib's column fill reads row by row."""
    n_items = len(labels)
    nrows = int(np.ceil(n_items / ncol))
    order = [
        row * ncol + col
        for col in range(ncol)
        for row in range(nrows)
        if row * ncol + col < n_items
    ]
    return [handles[idx] for idx in order], [labels[idx] for idx in order]


def prepare_summary(summary: pd.DataFrame) -> pd.DataFrame:
    """Validate a freshly computed live sensitivity summary."""
    df = summary.copy()
    required_columns = {
        "scenario",
        "strategy",
        "sensitivity_group",
        "parameter_value",
        "T80_pop",
    }
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Live sensitivity summary is missing {sorted(missing_columns)}."
        )
    resolved_keys = df["strategy"].map(canonical_strategy_key)
    if resolved_keys.isna().any():
        unknown = sorted(df.loc[resolved_keys.isna(), "strategy"].astype(str).unique())
        raise ValueError(f"Unknown sensitivity strategies: {unknown}.")
    df["strategy"] = resolved_keys
    df["parameter_value"] = pd.to_numeric(df["parameter_value"], errors="coerce")
    df["T80_pop"] = pd.to_numeric(df["T80_pop"], errors="coerce")
    if df[["parameter_value", "T80_pop"]].isna().any().any():
        raise ValueError(
            "Live sensitivity summary contains missing parameter_value or T80_pop values."
        )
    _validate_summary(df)
    return df


def _validate_summary(summary: pd.DataFrame) -> None:
    """Reject mixed scenarios or incomplete 2pc50 sensitivity grids."""
    expected_rows = len(STRATEGY_ORDER) * (
        1 + sum(len(values) for values in EXPECTED_PARAMETER_VALUES.values())
    )
    if len(summary) != expected_rows:
        raise ValueError(
            f"2pc50 sensitivity summary must contain {expected_rows} rows; "
            f"found {len(summary)}."
        )
    duplicate_keys = summary.duplicated(
        ["strategy", "sensitivity_group", "parameter_value"],
        keep=False,
    )
    if duplicate_keys.any():
        examples = (
            summary.loc[
                duplicate_keys,
                ["strategy", "sensitivity_group", "parameter_value"],
            ]
            .drop_duplicates()
            .head(10)
            .to_dict("records")
        )
        raise ValueError(
            f"2pc50 sensitivity summary contains duplicate cases: {examples}."
        )

    scenarios = set(summary["scenario"].astype(str))
    if scenarios != {SENSITIVITY_SCENARIO}:
        raise ValueError(
            f"Sensitivity analysis must contain only {SENSITIVITY_SCENARIO}; "
            f"found {sorted(scenarios)}."
        )

    expected_strategies = set(STRATEGY_ORDER)
    baseline = summary[summary["sensitivity_group"] == "baseline"]
    if set(baseline["strategy"]) != expected_strategies:
        raise ValueError("2pc50 baseline does not contain the complete strategy set.")

    observed_groups = set(summary["sensitivity_group"]) - {"baseline"}
    if observed_groups != set(EXPECTED_PARAMETER_VALUES):
        raise ValueError(
            "2pc50 sensitivity groups are incomplete or unexpected: "
            f"{sorted(observed_groups)}."
        )

    for group, expected_values in EXPECTED_PARAMETER_VALUES.items():
        group_df = summary[summary["sensitivity_group"] == group]
        observed_values = tuple(sorted(group_df["parameter_value"].unique()))
        if not np.allclose(observed_values, expected_values, rtol=0.0, atol=1e-12):
            raise ValueError(
                f"{group} parameter grid mismatch: {observed_values}."
            )
        for value, value_df in group_df.groupby("parameter_value"):
            if set(value_df["strategy"]) != expected_strategies:
                raise ValueError(
                    f"{group}={value:g} does not contain the complete strategy set."
                )


def _tied_minimum_strategies(frame: pd.DataFrame) -> list[str]:
    """Return all strategies tied at the minimum T80 value."""
    minimum = float(frame["T80_pop"].min())
    tied = frame.loc[
        np.isclose(frame["T80_pop"], minimum, rtol=0.0, atol=1e-9),
        "strategy",
    ]
    return sorted(tied.astype(str).unique())


def _second_tier_strategies(frame: pd.DataFrame) -> list[str]:
    """Return all strategies in the second distinct T80 tier."""
    values = np.sort(frame["T80_pop"].dropna().unique())
    if len(values) < 2:
        return []
    second = float(values[1])
    tied = frame.loc[
        np.isclose(frame["T80_pop"], second, rtol=0.0, atol=1e-9),
        "strategy",
    ]
    return sorted(tied.astype(str).unique())


def compute_rank_stability(summary: pd.DataFrame) -> pd.DataFrame:
    """Compute tie-corrected 2pc50 Spearman stability against the baseline."""
    rows = []
    varied = summary[summary["sensitivity_group"] != "baseline"]
    baseline = summary[summary["sensitivity_group"] == "baseline"][
        ["strategy", "T80_pop"]
    ]
    for (group, parameter_value), current in varied.groupby(
        ["sensitivity_group", "parameter_value"],
        sort=True,
    ):
        paired = baseline.merge(
            current[["strategy", "T80_pop"]],
            on="strategy",
            suffixes=("_baseline", "_current"),
        ).dropna()
        current_spread = float(
            paired["T80_pop_current"].max() - paired["T80_pop_current"].min()
        )
        if len(paired) < 2:
            rho = np.nan
        else:
            baseline_ranks = paired["T80_pop_baseline"].rank(method="average")
            current_ranks = paired["T80_pop_current"].rank(method="average")
            rho = baseline_ranks.corr(current_ranks)

        baseline_top = set(
            _tied_minimum_strategies(
                paired.rename(columns={"T80_pop_baseline": "T80_pop"})
            )
        )
        current_for_tiers = paired[["strategy", "T80_pop_current"]].rename(
            columns={"T80_pop_current": "T80_pop"}
        )
        current_top = set(_tied_minimum_strategies(current_for_tiers))
        current_second = _second_tier_strategies(current_for_tiers)
        rows.append(
            {
                "scenario": SENSITIVITY_SCENARIO,
                "sensitivity_group": group,
                "parameter_value": parameter_value,
                "top_strategy_by_T80": "; ".join(
                    canonical_strategy_label(value)
                    for value in sorted(current_top)
                ),
                "second_strategy_by_T80": "; ".join(
                    canonical_strategy_label(value) for value in current_second
                ),
                "spearman_rank_corr_vs_baseline_T80": rho,
                "top_strategy_changed_T80": baseline_top.isdisjoint(current_top),
                "T80_strategy_spread_hr": current_spread,
                "rank_status": "estimated",
            }
        )
    return pd.DataFrame(rows)


def _format_rho_range(values: pd.Series, separator: str = "\u2013") -> str:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return ""
    lower = float(numeric.min())
    upper = float(numeric.max())
    if np.isclose(lower, upper, rtol=0.0, atol=5e-13):
        return f"{lower:.2f}"
    return f"{lower:.2f}{separator}{upper:.2f}"


def _format_rank_stability(
    rank_subset: pd.DataFrame,
    separator: str = "\u2013",
) -> str:
    return _format_rho_range(
        rank_subset["spearman_rank_corr_vs_baseline_T80"],
        separator=separator,
    )


def build_main_table(
    summary: pd.DataFrame,
    rank_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build the compact 2pc50 table directly from validated experiment rows."""
    def interpret(max_change: float, rho_values: pd.Series) -> str:
        if max_change < 1.0:
            timing = "Little change in absolute T80"
        elif max_change < 10.0:
            timing = "Moderate change in absolute T80"
        else:
            timing = "Large change in absolute T80"

        rho = pd.to_numeric(rho_values, errors="coerce").dropna()
        if rho.empty:
            ranking = "rank stability unavailable"
        elif float(rho.min()) >= 0.90:
            ranking = "strategy ranking remains stable"
        elif float(rho.min()) >= 0.70:
            ranking = "strategy ranking is generally stable"
        else:
            ranking = "strategy ranking is parameter-sensitive"
        return f"{timing}; {ranking}."

    rows = []
    for group in RANK_ROW_ORDER:
        group_df = summary[summary["sensitivity_group"] == group]
        within_strategy_change = group_df.groupby("strategy")["T80_pop"].agg(
            lambda values: float(values.max() - values.min())
        )
        max_change = float(within_strategy_change.max())
        rank_subset = rank_df[rank_df["sensitivity_group"] == group]
        label, tested_range = PARAMETER_TABLE_META[group]
        rows.append(
            {
                "Parameter": label,
                "Tested range": tested_range,
                "Max within-strategy change in T80_pop (h)": (
                    f"{max_change:.1f}"
                ),
                "Rank stability (Spearman rho)": _format_rank_stability(
                    rank_subset
                ),
                "Interpretation": interpret(
                    max_change,
                    rank_subset["spearman_rank_corr_vs_baseline_T80"],
                ),
            }
        )
    return pd.DataFrame(rows)


def write_rank_stability_table(rank_df: pd.DataFrame) -> None:
    """Save the detailed 2pc50 rank-stability values used by the heatmap."""
    rank_df.to_csv(
        TABLE_DIR / "Table_Sensitivity_Rank_Stability_2pc50.csv",
        index=False,
    )


def plot_t80_response(summary: pd.DataFrame, scenario: str, output_path: Path) -> None:
    scenario_df = summary[summary["scenario"] == scenario].copy()
    fig, axes = plt.subplots(2, 2, figsize=cm_to_inch(18.5, 13.2))

    for ax, (group, panel_title, xlabel) in zip(axes.flat, PANEL_CONFIG):
        group_df = scenario_df[scenario_df["sensitivity_group"] == group]
        for strategy in STRATEGY_ORDER:
            line_df = (
                group_df[group_df["strategy"] == strategy]
                .sort_values("parameter_value")
                .copy()
            )
            if line_df.empty:
                continue
            style = STRATEGY_STYLE[strategy].copy()
            marker = style.pop("marker", None)
            linestyle = style.pop("linestyle", "-")
            ax.plot(
                line_df["parameter_value"],
                line_df["T80_pop"],
                label=STRATEGY_LABELS[strategy],
                marker=marker,
                linestyle=linestyle,
                markersize=3.4 if marker else 0,
                **style,
            )

        ax.set_title(panel_title, fontsize=FS_TITLE, fontweight="normal", pad=4)
        ax.set_xlabel(xlabel, fontsize=FS_LABEL)
        ax.set_ylabel(r"Population-weighted $T_{80}^{pop}$ (h)", fontsize=FS_LABEL)
        ax.tick_params(axis="both", labelsize=FS_TICK, width=0.6, length=3)
        ax.grid(True, alpha=0.9)
        values = sorted(group_df["parameter_value"].dropna().unique())
        ax.set_xticks(values)
        ax.set_xticklabels([fmt_tick(v) for v in values])

    handles, labels = axes.flat[0].get_legend_handles_labels()
    label_to_handle = dict(zip(labels, handles))
    ordered_labels = [STRATEGY_LABELS[s] for s in STRATEGY_ORDER]
    ordered_handles = [
        label_to_handle[label]
        for label in ordered_labels
        if label in label_to_handle
    ]
    ordered_labels = [label for label in ordered_labels if label in label_to_handle]
    ordered_handles, ordered_labels = reorder_legend_row_major(
        ordered_handles,
        ordered_labels,
        ncol=5,
    )
    fig.legend(
        ordered_handles,
        ordered_labels,
        ncol=5,
        loc="lower center",
        frameon=False,
        bbox_to_anchor=(0.5, 0.0),
        fontsize=FS_LEGEND,
    )
    fig.subplots_adjust(
        left=0.08,
        right=0.98,
        top=0.96,
        bottom=0.20,
        hspace=0.54,
        wspace=0.23,
    )
    save(fig, output_path)


def plot_idw_diagnostics(
    mapping_diagnostics: pd.DataFrame,
    output_path: Path,
) -> None:
    df = mapping_diagnostics.copy()
    df["theta_W"] = pd.to_numeric(df["theta_W"], errors="coerce")
    df["mean_supply_count"] = pd.to_numeric(df["mean_supply_count"], errors="coerce")
    df["mean_HHI"] = pd.to_numeric(df["mean_HHI"], errors="coerce")
    df = df.dropna(subset=["theta_W", "mean_supply_count", "mean_HHI"]).sort_values("theta_W")
    expected_theta = EXPECTED_PARAMETER_VALUES["idw_threshold"]
    observed_theta = tuple(df["theta_W"].tolist())
    if not np.allclose(observed_theta, expected_theta, rtol=0.0, atol=1e-12):
        raise ValueError(
            f"Live IDW diagnostic grid mismatch: {observed_theta}."
        )

    fig, ax_left = plt.subplots(figsize=cm_to_inch(FIGURE_WIDTH_MEDIUM_CM, 7.4))
    ax_right = ax_left.twinx()
    line_left = ax_left.plot(
        df["theta_W"],
        df["mean_supply_count"],
        color="#2166ac",
        marker="o",
        markersize=3.8,
        linewidth=1.5,
        label="Mean supplying substations",
    )
    line_right = ax_right.plot(
        df["theta_W"],
        df["mean_HHI"],
        color="#bf1b2c",
        marker="s",
        markersize=3.8,
        linewidth=1.5,
        label="Mean HHI",
    )
    ax_left.set_xlabel(r"IDW threshold ($\theta_W$)", fontsize=FS_LABEL)
    ax_left.set_ylabel("Mean supplying substations", color="#2166ac", fontsize=FS_LABEL)
    ax_right.set_ylabel("Mean HHI", color="#bf1b2c", fontsize=FS_LABEL)
    ax_left.tick_params(axis="both", labelsize=FS_TICK, width=0.6, length=3)
    ax_right.tick_params(axis="both", labelsize=FS_TICK, width=0.6, length=3)
    ax_left.tick_params(axis="y", colors="#2166ac")
    ax_right.tick_params(axis="y", colors="#bf1b2c")
    ax_left.set_xticks(df["theta_W"])
    ax_left.set_xticklabels([f"{v:.2f}" for v in df["theta_W"]])
    ax_left.grid(True, alpha=0.9)
    lines = line_left + line_right
    ax_left.legend(lines, [line.get_label() for line in lines], frameon=False, loc="center right", fontsize=FS_LEGEND)
    fig.subplots_adjust(left=0.16, right=0.84, top=0.98, bottom=0.18)
    save(fig, output_path)


def summarize_source_gate_diagnostics(
    source_gate_diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and summarize source-connected functional-substation trajectories."""
    required = {
        "scenario",
        "source_gate_threshold",
        "time_hr",
        "source_connected_functional_count",
        "source_connected_functional_share",
        "n_substations",
    }
    missing = required - set(source_gate_diagnostics.columns)
    if missing:
        raise ValueError(
            f"Source-gate diagnostics are missing {sorted(missing)}."
        )

    df = source_gate_diagnostics.copy()
    numeric_cols = [
        "source_gate_threshold",
        "time_hr",
        "source_connected_functional_count",
        "source_connected_functional_share",
        "n_substations",
    ]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(df[numeric_cols].to_numpy(dtype=float)).all():
        raise ValueError("Source-gate diagnostics contain non-finite values.")
    if set(df["scenario"].astype(str)) != {SENSITIVITY_SCENARIO}:
        raise ValueError("Source-gate diagnostics must contain only 2pc50.")
    if df.duplicated(
        ["source_gate_threshold", "time_hr"],
        keep=False,
    ).any():
        raise ValueError("Source-gate diagnostics contain duplicate time rows.")

    expected_thresholds = EXPECTED_PARAMETER_VALUES["source_gate_threshold"]
    rows = []
    observed_thresholds = tuple(sorted(df["source_gate_threshold"].unique()))
    if not np.allclose(
        observed_thresholds,
        expected_thresholds,
        rtol=0.0,
        atol=1e-12,
    ):
        raise ValueError(
            f"Source-gate diagnostic grid mismatch: {observed_thresholds}."
        )
    for threshold, case in df.groupby("source_gate_threshold", sort=True):
        case = case.sort_values("time_hr")
        time = case["time_hr"].to_numpy(dtype=float)
        if len(time) < 2 or np.any(np.diff(time) <= 0):
            raise ValueError(
                f"Source-gate diagnostics require increasing time at "
                f"tau_g={threshold:g}."
            )
        n_substations = case["n_substations"].unique()
        if len(n_substations) != 1 or n_substations[0] <= 0:
            raise ValueError("Invalid n_substations in source-gate diagnostics.")
        count = case[
            "source_connected_functional_count"
        ].to_numpy(dtype=float)
        share = case[
            "source_connected_functional_share"
        ].to_numpy(dtype=float)
        if np.any(count < 0) or np.any(share < 0) or np.any(share > 1):
            raise ValueError("Source-gate diagnostics are outside physical bounds.")
        if not np.allclose(
            count / float(n_substations[0]),
            share,
            rtol=0.0,
            atol=1e-10,
        ):
            raise ValueError(
                "Source-gate count and share diagnostics are inconsistent."
            )
        duration = float(time[-1] - time[0])
        rows.append(
            {
                "scenario": SENSITIVITY_SCENARIO,
                "source_gate_threshold": float(threshold),
                "time_averaged_source_connected_count": float(
                    getattr(np, "trapezoid", np.trapz)(count, time) / duration
                ),
                "time_averaged_source_connected_share": float(
                    getattr(np, "trapezoid", np.trapz)(share, time) / duration
                ),
                "source_connected_count_24h": float(
                    np.interp(24.0, time, count)
                ),
                "source_connected_share_24h": float(
                    np.interp(24.0, time, share)
                ),
                "n_substations": int(n_substations[0]),
            }
        )
    summary = pd.DataFrame(rows)
    expected_rows = len(expected_thresholds)
    if len(summary) != expected_rows:
        raise ValueError(
            f"Source-gate mechanism summary must contain {expected_rows} rows; "
            f"found {len(summary)}."
        )
    return summary


def plot_source_gate_diagnostics(
    source_gate_summary: pd.DataFrame,
    output_path: Path,
) -> None:
    """Plot the source-gate mechanism counterpart to the IDW diagnostic."""
    fig, ax = plt.subplots(figsize=cm_to_inch(FIGURE_WIDTH_MEDIUM_CM, 7.4))
    line_df = source_gate_summary.sort_values("source_gate_threshold")
    ax.plot(
        line_df["source_gate_threshold"],
        line_df["time_averaged_source_connected_count"],
        color="#2166ac",
        marker="o",
        linestyle="-",
        linewidth=1.6,
        markersize=4.0,
    )

    n_values = source_gate_summary["n_substations"].unique()
    if len(n_values) != 1:
        raise ValueError("Source-gate plot requires one common substation count.")
    n_substations = float(n_values[0])
    secondary = ax.secondary_yaxis(
        "right",
        functions=(
            lambda count: count / n_substations,
            lambda share: share * n_substations,
        ),
    )
    ax.set_xlabel(r"Source-gate threshold ($\tau_g$)", fontsize=FS_LABEL)
    ax.set_ylabel(
        "Time-averaged source-connected\nfunctional substations (0-480 h)",
        fontsize=FS_LABEL,
    )
    secondary.set_ylabel(
        "Share of all substations",
        fontsize=FS_LABEL,
    )
    ax.tick_params(axis="both", labelsize=FS_TICK, width=0.6, length=3)
    secondary.tick_params(axis="y", labelsize=FS_TICK, width=0.6, length=3)
    thresholds = sorted(source_gate_summary["source_gate_threshold"].unique())
    ax.set_xticks(thresholds)
    ax.set_xticklabels([f"{value:.2f}" for value in thresholds])
    ax.grid(True, alpha=0.9)
    fig.subplots_adjust(left=0.16, right=0.84, top=0.98, bottom=0.18)
    save(fig, output_path)


def plot_rank_stability(df: pd.DataFrame, output_path: Path) -> None:
    df = df.copy()
    df["parameter_value"] = pd.to_numeric(df["parameter_value"], errors="coerce")
    df["rho"] = pd.to_numeric(df["spearman_rank_corr_vs_baseline_T80"], errors="coerce")
    columns = sorted(df["parameter_value"].dropna().unique())

    matrix = np.full((len(RANK_ROW_ORDER), len(columns)), np.nan)
    row_labels = []
    for row_idx, group in enumerate(RANK_ROW_ORDER):
        row_labels.append(GROUP_LABELS[group])
        subset = df[df["sensitivity_group"] == group]
        for _, row in subset.iterrows():
            col_idx = columns.index(float(row["parameter_value"]))
            matrix[row_idx, col_idx] = row["rho"]

    masked = np.ma.masked_invalid(matrix)
    cmap = plt.cm.RdBu.copy()
    cmap.set_bad("white")

    fig, ax = plt.subplots(figsize=cm_to_inch(18.5, 7.4))
    im = ax.imshow(masked, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(np.arange(len(columns)))
    ax.set_xticklabels([fmt_tick(v) if v >= 0.1 else f"{v:.2f}" for v in columns])
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.set_xlabel("Parameter value", fontsize=FS_LABEL)
    ax.tick_params(axis="both", labelsize=FS_TICK, width=0.6, length=3)

    ax.set_xticks(np.arange(-0.5, len(columns), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax.grid(which="minor", color="#e0e0e0", linewidth=0.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    for row_idx in range(matrix.shape[0]):
        for col_idx in range(matrix.shape[1]):
            value = matrix[row_idx, col_idx]
            if np.isfinite(value):
                color = "white" if abs(value) >= 0.75 else "black"
                ax.text(col_idx, row_idx, f"{value:.2f}", ha="center", va="center", color=color, fontsize=FS_ANNOTATION)

    cbar = fig.colorbar(im, ax=ax, fraction=0.033, pad=0.02)
    cbar.set_label(r"Spearman $\rho$", fontsize=FS_COLORBAR)
    cbar.ax.tick_params(labelsize=FS_COLORBAR, width=0.6, length=2.5)
    fig.text(
        0.01,
        0.070,
        "Blank cells indicate parameter values not applicable to that sensitivity group.",
        ha="left",
        va="bottom",
        fontsize=FS_ANNOTATION,
        color="#555555",
    )
    fig.text(
        0.01,
        0.025,
        r"Spearman $\rho$ uses average ranks for tied $T_{80}^{pop}$ values.",
        ha="left",
        va="bottom",
        fontsize=FS_ANNOTATION,
        color="#555555",
    )
    fig.subplots_adjust(left=0.22, right=0.91, top=0.98, bottom=0.30)
    save(fig, output_path)


def normalize_text(value: object) -> str:
    text = str(value)
    replacements = {
        "â€“": "\u2013",
        "theta_W": r"$\theta_W$",
        "tau_g": r"$\tau_g$",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def wrap_cell(value: object, width: int) -> str:
    return "\n".join(textwrap.wrap(normalize_text(value), width=width, break_long_words=False))


def plot_table_preview(table_df: pd.DataFrame, output_path: Path) -> None:
    display_df = table_df.copy()
    display_df.columns = [
        "Parameter",
        "Tested\nrange",
        "Max within-strategy\nchange in\n" + r"$T_{80}^{pop}$ (h)",
        "Rank stability\n" + r"($\rho$)",
        "Interpretation",
    ]
    wrapped_rows = []
    for _, row in display_df.iterrows():
        wrapped_rows.append(
            [
                wrap_cell(row["Parameter"], 17),
                wrap_cell(row["Tested\nrange"], 12),
                wrap_cell(row["Max within-strategy\nchange in\n" + r"$T_{80}^{pop}$ (h)"], 10),
                wrap_cell(row["Rank stability\n" + r"($\rho$)"], 10),
                wrap_cell(row["Interpretation"], 30),
            ]
        )

    fig, ax = plt.subplots(figsize=cm_to_inch(FIGURE_WIDTH_FULL_CM, 6.2))
    ax.axis("off")
    table = ax.table(
        cellText=wrapped_rows,
        colLabels=list(display_df.columns),
        cellLoc="left",
        colLoc="left",
        colWidths=[0.18, 0.12, 0.25, 0.14, 0.31],
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(FS_TABLE)
    table.scale(1.0, 2.45)

    for (row_idx, col_idx), cell in table.get_celld().items():
        cell.set_edgecolor("#c9c9c9")
        if row_idx == 0:
            cell.set_facecolor("#e8eef6")
            cell.set_text_props(fontweight="bold", va="center", fontsize=FS_TABLE_HEADER)
        else:
            cell.set_facecolor("#f7f7f7" if row_idx % 2 == 0 else "white")
            cell.set_text_props(va="center", fontsize=FS_TABLE)

    save(fig, output_path)


def write_table_files(table_df: pd.DataFrame) -> None:
    clean = table_df.copy()
    for col in clean.columns:
        clean[col] = clean[col].map(normalize_text)

    clean.to_csv(TABLE_DIR / "Table_Sensitivity_Summary_2pc50.csv", index=False)

    md_lines = [
        "| " + " | ".join(clean.columns) + " |",
        "| " + " | ".join(["---"] * len(clean.columns)) + " |",
    ]
    for _, row in clean.iterrows():
        md_lines.append("| " + " | ".join(str(row[col]) for col in clean.columns) + " |")
    (TABLE_DIR / "Table_Sensitivity_Summary_2pc50.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    tex_columns = [
        "Parameter",
        "Tested range",
        r"Max within-strategy change in $T_{80}^{pop}$ (h)",
        r"Rank stability ($\rho$)",
        "Interpretation",
    ]
    latex_lines = [
        r"\begin{table}",
        r"\caption{Compact sensitivity summary for the 2\%-in-50-year scenario.}",
        r"\begin{tabular}{lllll}",
        r"\hline",
        " & ".join(tex_columns) + r" \\",
        r"\hline",
    ]
    for _, row in clean.iterrows():
        latex_lines.append(" & ".join(str(row[col]) for col in clean.columns) + r" \\")
    latex_lines.extend([r"\hline", r"\end{tabular}", r"\end{table}", ""])
    latex = "\n".join(latex_lines)
    (TABLE_DIR / "Table_Sensitivity_Summary_2pc50.tex").write_text(latex, encoding="utf-8")


def render_sensitivity_outputs_2pc50(
    summary: pd.DataFrame,
    mapping_diagnostics: pd.DataFrame,
    source_gate_diagnostics: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Render validated outputs from the current live 2pc50 experiments."""
    ensure_dirs()
    apply_style()

    summary = prepare_summary(summary)
    mapping_diagnostics = mapping_diagnostics.copy()
    source_gate_diagnostics = source_gate_diagnostics.copy()
    source_gate_summary = summarize_source_gate_diagnostics(
        source_gate_diagnostics
    )
    exported_summary = summary.copy()
    exported_summary["strategy"] = exported_summary["strategy"].map(
        canonical_strategy_label
    )
    exported_summary.to_csv(SUMMARY_PATH, index=False)
    mapping_diagnostics.to_csv(MAPPING_DIAGNOSTICS_PATH, index=False)
    source_gate_diagnostics.to_csv(SOURCE_GATE_DIAGNOSTICS_PATH, index=False)
    source_gate_summary.to_csv(SOURCE_GATE_SUMMARY_PATH, index=False)
    rank_df = compute_rank_stability(summary)
    table_df = build_main_table(summary, rank_df)

    plot_t80_response(
        summary,
        SENSITIVITY_SCENARIO,
        MAIN_DIR / "Fig_Sensitivity_T80_Response_2pc50.png",
    )
    plot_idw_diagnostics(
        mapping_diagnostics,
        SUPP_DIR / "Fig_Supp_IDW_Mapping_Diagnostics.png",
    )
    plot_source_gate_diagnostics(
        source_gate_summary,
        SUPP_DIR / "Fig_Supp_Source_Gate_Mechanism_Diagnostics.png",
    )
    plot_rank_stability(rank_df, SUPP_DIR / "Fig_Supp_Rank_Stability_T80.png")
    plot_table_preview(table_df, MAIN_DIR / "Table_Sensitivity_Summary_2pc50.png")
    write_table_files(table_df)
    write_rank_stability_table(rank_df)

    return {
        "summary": summary,
        "rank_stability": rank_df,
        "table": table_df,
        "source_gate_diagnostics": source_gate_diagnostics,
        "source_gate_summary": source_gate_summary,
    }


def main() -> None:
    raise RuntimeError(
        "Sensitivity experiments are computed by C257H_Project_Main.py. "
        "This module is now a renderer and requires live DataFrame inputs."
    )


if __name__ == "__main__":
    main()
