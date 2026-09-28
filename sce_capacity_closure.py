from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import run_sce_capacity_supported_sensitivity as base

ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "Formal_Experiment_20260923"
GNA_SCREEN = ROOT / "Revision_Mapping_Gate" / "LOCAL_GNA_CAPACITY_SCREEN.csv"
ORIGINAL_PRIMARY = FORMAL / "Formal_Results" / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet"
VULNERABILITY_PRIMARY = FORMAL / "Equity_Amendment" / "VULNERABILITY_PRIMARY_SUMMARY.parquet"
VULNERABILITY_TRAJECTORY_DIR = Path(os.environ.get(
    "VULNERABILITY_TRAJECTORY_DIR",
    FORMAL / "Equity_Amendment" / "T" / "2pc50" / "C57_D1",
))

HAZARDS = ["Northridge", "SanFernando", "LongBeach", "2pc50"]
SCHEDULED = [
    "centrality-first", "impact-first", "betweenness-first", "degree-first",
    "closeness-first", "hospital-first", "random", "vulnerability-first",
]
TRACE_FIELDS = ("f", "F", "C", "e", "L_self", "L_threshold", "L_source", "L_total")
N = 1000
CAP_TOL = 1e-12
RECON_TOL = 1e-9
ANCHORS = {
    "hospital-first": (34.306, 45.971, 33.367),
    "impact-first": (33.594, 45.251, 33.059),
    "vulnerability-first": (34.258, 46.437, 33.939),
}


def _label(policy):
    return "Unconstrained" if policy == "unconstrained" else policy


def _cases():
    a = [(h, "hospital-first") for h in HAZARDS]
    b = [("2pc50", p) for p in [*SCHEDULED, "unconstrained"]]
    return list(dict.fromkeys(a + b))


def _assert_direct_duplicate():
    impact = json.loads((base.SCHEDULE_DIR / "2pc50__C57_D1__impact-first.json").read_text())
    direct = json.loads((base.SCHEDULE_DIR / "2pc50__C57_D1__direct-community.json").read_text())
    if impact["identity"]["sequence_sha256"] != direct["identity"]["sequence_sha256"]:
        raise ValueError("direct-community does not duplicate impact-first")


def _validate_vulnerability_archive():
    if not VULNERABILITY_TRAJECTORY_DIR.is_dir():
        raise FileNotFoundError(
            f"Missing frozen vulnerability-first archive: {VULNERABILITY_TRAJECTORY_DIR}. "
            "Do not reschedule it."
        )
    missing = []
    for i in range(N):
        stem = f"2pc50__evaluation_{i:04d}"
        for suffix in (".npz", ".json", "__TASK_EVENTS.csv"):
            if not (VULNERABILITY_TRAJECTORY_DIR / f"{stem}{suffix}").is_file():
                missing.append(f"{stem}{suffix}")
                if len(missing) >= 10:
                    break
        if len(missing) >= 10:
            break
    if missing:
        raise FileNotFoundError("Incomplete vulnerability archive: " + ", ".join(missing))


def _load_supported(station_ids):
    supported, idx, caps = base._load_supported(station_ids)
    below = supported.loc[caps < 1 - CAP_TOL, "StationID"].astype(str).tolist()
    if below != ["306279"]:
        raise ValueError(f"K/D<1 must occur only at OLINDA 306279; got {below}")

    gna = pd.read_csv(GNA_SCREEN, dtype={"July_ID": str})
    year = gna["year_value"].astype(str).str.replace(".0", "", regex=False)
    d = pd.to_numeric(gna["cumulative_demand"], errors="coerce")
    k = pd.to_numeric(gna["fac_load_limit"], errors="coerce")
    numeric = gna.loc[
        year.eq("2026") & gna["July_ID"].notna() & d.notna() & k.notna() & (k > 0)
    ].copy()
    numeric["July_ID"] = numeric["July_ID"].map(base._clean_id)
    numeric = numeric[numeric.July_ID.isin(set(map(str, station_ids)))]
    counts = numeric.groupby("July_ID").size()
    single = set(counts.index[counts.eq(1)])
    multi = set(counts.index[counts.gt(1)])
    if len(numeric) != 37 or len(counts) != 28:
        raise ValueError(f"Numeric GNA domain must be 37 rows / 28 stations, got {len(numeric)} / {len(counts)}")
    if len(single) != 19 or len(multi) != 9:
        raise ValueError(f"Expected 19 single-facility and 9 multi-facility stations, got {len(single)} / {len(multi)}")
    if set(supported.StationID) != single or set(supported.StationID) & multi:
        raise ValueError("Station capacity factors are not restricted to the 19 single-facility stations")
    if len(set(map(str, station_ids)) - set(supported.StationID)) != 73:
        raise ValueError("Unsupported station count must be 73")
    return supported, idx, caps


def _capacity_arrays(arrays, supported_idx, caps, station_ids):
    e = np.asarray(arrays["e"], float)
    ecap = e.copy()
    ecap[:, supported_idx] = np.minimum(ecap[:, supported_idx], caps[None, :])
    smask = np.zeros(len(station_ids), dtype=bool)
    smask[supported_idx] = True
    umask = ~smask
    if umask.sum() != 73:
        raise ValueError("Unsupported station mask is not 73")
    if not np.array_equal(ecap[:, umask], e[:, umask], equal_nan=True):
        raise ValueError("Unsupported stations must satisfy e_cap=e exactly")
    known = np.isfinite(e[:, supported_idx])
    if np.any(ecap[:, supported_idx][known] > e[:, supported_idx][known] + CAP_TOL):
        raise ValueError("Supported stations must satisfy e_cap<=e")
    lcap = e - ecap
    ltotal = 1 - ecap
    unknown = ~np.isfinite(np.asarray(arrays["f"], float))
    ecap[unknown] = np.nan
    lcap[unknown] = np.nan
    ltotal[unknown] = np.nan
    accounting = (
        np.asarray(arrays["L_self"], float)
        + np.asarray(arrays["L_threshold"], float)
        + np.asarray(arrays["L_source"], float)
        + lcap
    )
    if not np.allclose(accounting, ltotal, rtol=0, atol=1e-12, equal_nan=True):
        raise ValueError("Capacity loss accounting does not conserve")
    return {
        "f": np.asarray(arrays["f"], float), "e": ecap,
        "L_self": np.asarray(arrays["L_self"], float),
        "L_threshold": np.asarray(arrays["L_threshold"], float),
        "L_source": np.asarray(arrays["L_source"], float),
        "L_capacity": lcap, "L_total": ltotal,
    }


def _trace_arrays(trace):
    return {name: getattr(trace, name).to_numpy(float) for name in TRACE_FIELDS}


def _load_vulnerability_trace(i, station_ids, physical_manifest):
    stem = f"2pc50__evaluation_{i:04d}"
    npz_path = VULNERABILITY_TRAJECTORY_DIR / f"{stem}.npz"
    json_path = VULNERABILITY_TRAJECTORY_DIR / f"{stem}.json"
    events_path = VULNERABILITY_TRAJECTORY_DIR / f"{stem}__TASK_EVENTS.csv"
    manifest = json.loads(json_path.read_text())
    identity = manifest.get("identity", {})
    expected = {
        "hazard": "2pc50", "realization_id": stem, "split": "evaluation",
        "strategy": "vulnerability-first", "resource_scenario": "C57_D1",
        "mapping_method_id": "M1_UTILITY_003",
    }
    for key, value in expected.items():
        if identity.get(key) != value:
            raise ValueError(f"Vulnerability archive identity mismatch for {stem}: {key}")
    if float(identity.get("event_horizon_hr", np.nan)) != 480.0:
        raise ValueError(f"Vulnerability horizon changed for {stem}")
    if identity.get("physical_sample_hash") != physical_manifest["sample_hashes"].get(stem):
        raise ValueError(f"Vulnerability physical pairing changed for {stem}")
    if manifest.get("status") != "FORMAL_FROZEN_MATRIX_V1":
        raise ValueError(f"Vulnerability archive status changed for {stem}")
    if base.sha256_file(npz_path) != manifest.get("npz_sha256"):
        raise ValueError(f"Vulnerability NPZ hash changed for {stem}")
    if base.sha256_file(events_path) != manifest.get("task_events_sha256"):
        raise ValueError(f"Vulnerability task-event hash changed for {stem}")
    with np.load(npz_path, allow_pickle=False) as z:
        if set(z.files) != set(TRACE_FIELDS) | {"station_ids", "event_time_hr"}:
            raise ValueError(f"Vulnerability trace fields changed for {stem}")
        if not np.array_equal(z["station_ids"].astype(str), station_ids):
            raise ValueError(f"Vulnerability station order changed for {stem}")
        time = z["event_time_hr"].astype(float).copy()
        arrays = {name: z[name].astype(float).copy() for name in TRACE_FIELDS}
    if time[0] != 0 or time[-1] != 480 or np.any(np.diff(time) <= 0):
        raise ValueError(f"Vulnerability event time invalid for {stem}")
    if not np.allclose(
        arrays["L_self"] + arrays["L_threshold"] + arrays["L_source"],
        arrays["L_total"], rtol=0, atol=1e-12, equal_nan=True
    ):
        raise ValueError(f"Vulnerability source-gate loss accounting changed for {stem}")
    return stem, time, arrays


def _reference(hazard, policy):
    path = VULNERABILITY_PRIMARY if policy == "vulnerability-first" else ORIGINAL_PRIMARY
    f = pd.read_parquet(path)
    f = f.loc[
        f.hazard.eq(hazard)
        & f.resource_scenario.eq("C57_D1")
        & f.mapping.eq("M1_UTILITY_003")
        & f.gate.eq("G1_BASELINE_050")
        & f.comparison_domain.eq("mapping_native_domain")
        & f.strategy_id.eq(policy)
    ].copy()
    cols = [
        "population_weighted_normalized_burden_hr",
        "population_T80_hr",
        "hospital_mean_normalized_burden_hr",
    ]
    if len(f) != N or f.realization_id.nunique() != N or f[cols].isna().any().any():
        raise ValueError(f"Frozen baseline reference incomplete for {hazard}/{policy}")
    return f.set_index("realization_id")[cols].sort_index()


def _reconcile_before_capacity(hazard, policy, rid, summary, ref, maxima):
    if rid not in ref.index:
        raise ValueError(f"Frozen reference missing {rid} for {hazard}/{policy}")
    row = ref.loc[rid]
    fields = {
        "population_burden": "population_weighted_normalized_burden_hr",
        "T80": "population_T80_hr",
        "hospital_burden": "hospital_mean_normalized_burden_hr",
    }
    for label, field in fields.items():
        diff = abs(float(summary[field]) - float(row[field]))
        maxima[label] = max(maxima[label], diff)
        if diff >= RECON_TOL:
            raise ValueError(
                f"Baseline reconciliation failed before ceiling for {hazard}/{policy}/{rid}/{label}: "
                f"{diff:.3e} >= {RECON_TOL:.1e}"
            )


def _assert_anchors(summary):
    for policy, expected in ANCHORS.items():
        row = summary.loc[summary.Hazard.eq("2pc50") & summary.Policy.eq(policy)]
        if len(row) != 1:
            raise ValueError(f"Missing anchor row for {policy}")
        actual = (
            float(row.iloc[0].population_burden_base),
            float(row.iloc[0].T80_base),
            float(row.iloc[0].hospital_base),
        )
        for value, target, metric in zip(actual, expected, ("population burden", "T80", "hospital burden")):
            if f"{value:.3f}" != f"{target:.3f}":
                raise ValueError(f"{policy} {metric} does not reproduce frozen anchor")


def _contrasts(case_metrics):
    rows = []
    for candidate, reference in [
        ("impact-first", "hospital-first"),
        ("degree-first", "hospital-first"),
        ("vulnerability-first", "hospital-first"),
    ]:
        c = case_metrics[("2pc50", candidate)].set_index("realization_id")
        r = case_metrics[("2pc50", reference)].set_index("realization_id")
        if not c.index.equals(r.index):
            raise ValueError(f"Pairing differs for {candidate} vs {reference}")
        pb = float((c.pop_base - r.pop_base).mean())
        pc = float((c.pop_cap - r.pop_cap).mean())
        tb = float((c.t80_base - r.t80_base).mean())
        tc = float((c.t80_cap - r.t80_cap).mean())
        hb = float((c.hosp_base - r.hosp_base).mean())
        hc = float((c.hosp_cap - r.hosp_cap).mean())
        rows.append({
            "row_type": "pairwise_contrast", "Hazard": "2pc50",
            "Policy": f"{candidate} - {reference}",
            "candidate_policy": candidate, "reference_policy": reference,
            "population_burden_base": pb, "population_burden_cap": pc, "delta": pc - pb,
            "T80_base": tb, "T80_cap": tc, "delta_T80": tc - tb,
            "hospital_base": hb, "hospital_cap": hc,
            "affected_population": np.nan, "binding_station_count": np.nan,
            "binding_tract_count": np.nan, "baseline_reconciled": True,
            "reconciliation_max_abs_population_burden": np.nan,
            "reconciliation_max_abs_T80": np.nan,
            "reconciliation_max_abs_hospital_burden": np.nan,
            "sign_flipped_population_burden": (
                np.sign(pb) != np.sign(pc) and abs(pb) > 1e-12 and abs(pc) > 1e-12
            ),
        })
    return pd.DataFrame(rows)


def _write_figure(supported, summary, binding_count):
    base.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    a = supported.sort_values("D_MW").reset_index(drop=True)
    y = np.arange(len(a))
    axes[0].scatter(a["D_MW"], y, label="D (MW)", marker="o")
    axes[0].scatter(a["K_MW"], y, label="K (MW)", marker="s")
    for i, row in a.iterrows():
        axes[0].plot([row["D_MW"], row["K_MW"]], [i, i], linewidth=.8)
        if row["D_MW"] > row["K_MW"]:
            axes[0].annotate("D>K", (row["D_MW"], i), xytext=(4, 4), textcoords="offset points", fontsize=8)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(a["StationName"], fontsize=7)
    axes[0].set_xlabel("MW")
    axes[0].set_title(f"A. Supported one-to-one facilities\nBinding-capable: {binding_count} of 19")
    axes[0].legend(fontsize=8)

    b = summary.loc[summary.Policy.eq("hospital-first")].set_index("Hazard").reindex(HAZARDS).reset_index()
    axes[1].bar(b["Hazard"], b["delta"])
    axes[1].axhline(0, linewidth=.8)
    axes[1].tick_params(axis="x", rotation=30)
    axes[1].set_ylabel("Capacity-bounded minus baseline burden (h)")
    axes[1].set_title("B. Hospital-first across four hazards")

    c = summary.loc[summary.Hazard.eq("2pc50")].set_index("Policy").reindex([*SCHEDULED, "Unconstrained"]).reset_index()
    axes[2].bar(np.arange(len(c)), c["delta"])
    axes[2].axhline(0, linewidth=.8)
    axes[2].set_xticks(np.arange(len(c)))
    axes[2].set_xticklabels(c["Policy"], rotation=55, ha="right", fontsize=8)
    axes[2].set_ylabel("Capacity-bounded minus baseline burden (h)")
    axes[2].set_title("C. 2pc50 frozen policy comparison")
    fig.suptitle("SCE-supported capacity-ceiling sensitivity", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, .95))
    fig.savefig(base.FIGURE_STEM.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(base.FIGURE_STEM.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def _write_audit(validation, physical_manifest, horizon, supported, support_weight,
                 population, support_mask, summary, contrasts, recon, binding_ids, binding_tract):
    qs = np.quantile(support_weight, [.25, .5, .75])
    pop_support = float(np.dot(population, support_weight) / population.sum())
    binding = supported.loc[supported.StationID.isin(binding_ids), ["StationID", "Facility"]]
    binding_text = ", ".join(f"{x.StationID} ({x.Facility})" for x in binding.itertuples()) or "none"
    case_lines = [
        f"- {x.Hazard} / {x.Policy}: population burden delta={x.delta:.6f} h; "
        f"T80 delta={x.delta_T80:.6f} h; hospital burden delta={(x.hospital_cap-x.hospital_base):.6f} h; "
        f"binding stations={int(x.binding_station_count)}; binding tracts={int(x.binding_tract_count)}; "
        f"affected population={x.affected_population:.0f}."
        for x in summary.itertuples(index=False)
    ]
    recon_lines = [
        f"- {x.Hazard} / {x.Policy}: max abs difference population burden={x.population_burden:.3e}, "
        f"T80={x.T80:.3e}, hospital burden={x.hospital_burden:.3e}."
        for x in recon.itertuples(index=False)
    ]
    contrast_lines = [
        f"- {x.Policy}: population burden {x.population_burden_base:+.6f} -> {x.population_burden_cap:+.6f} h "
        f"(change {x.delta:+.6f} h; sign flipped={'YES' if x.sign_flipped_population_burden else 'no'}); "
        f"T80 {x.T80_base:+.6f} -> {x.T80_cap:+.6f} h; "
        f"hospital burden {x.hospital_base:+.6f} -> {x.hospital_cap:+.6f} h."
        for x in contrasts.itertuples(index=False)
    ]
    two = summary.loc[summary.Hazard.eq("2pc50")]
    audit = f"""# SCE Capacity Sensitivity Audit

## Closure status

This is the closed Reviewer 1 Comment 2 capacity sensitivity. It is post-processing only. No sampling, damage state, repair duration, dispatch, priority sequence, GA, source gate, tract mapping, or restoration schedule is recomputed. Vulnerability-first is read only from the saved station trajectories at {VULNERABILITY_TRAJECTORY_DIR}. direct-community is excluded after verifying that its frozen sequence hash is identical to Impact-first.

Every baseline realization is reconciled before the capacity ceiling is applied. Original policies are checked against Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet and Vulnerability-first against Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet. The tolerance is {RECON_TOL:.1e} h for population burden, T80, and hospital burden.

## Coverage and formula

- Supported station factors: 19/92.
- Numeric-evidence retained SCE stations: 28; 9 are multi-facility and receive no station factor.
- Unsupported retained stations: 73, asserted to satisfy e_cap=e exactly.
- Tracts with supported dependency: {int(support_mask.sum())}/2315.
- Population-weighted supported dependency mass: {pop_support:.4f}.
- W_r^sup P25/P50/P75: {qs[0]:.6f}, {qs[1]:.6f}, {qs[2]:.6f}.
- Only OLINDA 306279 has K/D<1 in the supported subset.
- Actual binding stations in the evaluated cases: {len(binding_ids)} ({binding_text}).
- Tracts with positive capacity-induced burden in at least one case: {int(binding_tract.sum())}.

Production service remains e_i(t)=f_i(t)F_i(t)C_i(t). For supported stations, a_i=min(1,K_i/D_i) and e_i^cap(t)=min[e_i(t),a_i]. Unsupported stations retain e_i^cap=e_i. Tract service remains A_r^cap(t)=sum_i w_ri e_i^cap(t). FACILITY_LOADING is QA only. The three rows exceeding the earlier 0.05 percentage-point D/K-versus-provider-loading QA tolerance remain in the evidence audit rather than being deleted: COLORADO 66/4.16 (+0.07704 pp), GANESHA 12/4.16 (-0.05190 pp), and REPETTO 66/4.16 (+0.06551 pp). They are excluded from station-level capacity factors only because their retained stations are multi-facility and SCE provides no public aggregation rule.

Hard assertions require 19 supported stations, 9 multi-facility exclusions, K/D<1 only at OLINDA 306279, 73 unsupported stations unchanged, e_cap<=e on supported stations, strict loss accounting including L_capacity, exactly eight distinct scheduled 2pc50 policies plus Unconstrained, no direct-community output, and inclusion of vulnerability-first.

## Baseline reconciliation

{chr(10).join(recon_lines)}

Frozen 2pc50 anchors reproduce as reported: Hospital-first 34.306 / 45.971 / 33.367 h; Impact-first 33.594 / 45.251 / 33.059; Vulnerability-first 34.258 / 46.437 / 33.939.

## Effect sizes

{chr(10).join(case_lines)}

Across the nine 2pc50 cases, population-burden increments range from {two.delta.min():.6f} to {two.delta.max():.6f} h.

### Required pairwise contrasts

{chr(10).join(contrast_lines)}

## Reviewer 1 Comment 2 response

1. Source-gate interpretation. C_i(t) represents surviving source-path availability only. e_i(t) is a modeled service-availability proxy, not delivered MW. The model does not solve AC/DC power flow and does not represent branch loading, voltage, reactive power, generation/import dispatch, or load shedding.

2. External-data-constrained stress test. SCE public planning data provide facility-level forecast peak demand D and loading limit K. For the 19/92 retained stations with a strict one-to-one facility interpretation, we imposed the static planning-peak ceiling e_i^cap(t)=min[e_i(t),K_i/D_i]. The supported subset intersects {int(support_mask.sum())}/2315 tracts and has population-weighted supported dependency mass {pop_support:.4f}. Nine additional numeric-evidence stations have multiple facility rows and were not aggregated.

3. Result and boundary. Within the strictly supported subset, only OLINDA is capacity-binding. The four-hazard Hospital-first population-burden increment is about 0.12-0.13 h; the complete 2pc50 strategy range and the three direct pairwise contrasts are reported above. The principal strategy comparisons are therefore not strongly driven by this particular class of documented SCE facility planning-capacity constraints within the supported subset. This test cannot establish adequacy for unsupported facilities, source-generation availability, branch-flow feasibility, voltage, reactive power, dispatch, or load shedding.

> Within the subset of retained facilities for which public SCE data support a strict one-to-one interpretation, imposing provider-defined planning capacity ceilings produced only small changes in modeled recovery outcomes. The principal strategy comparisons therefore were not strongly driven by this class of documented facility-capacity constraint. However, the stress test covers only part of the modeled network and does not establish adequacy for unsupported facilities, source-generation availability, branch flow, voltage, reactive power, dispatch, or load-shedding feasibility.
"""
    base.OUTPUT_AUDIT.write_text(audit, encoding="utf-8")


def run():
    validation = base._load_frozen_validation()
    physical_manifest = json.loads(base.PHYSICAL_MANIFEST_PATH.read_text())
    horizon = json.loads(base.HORIZON_PATH.read_text())
    if physical_manifest.get("evaluation_count") != 4000 or physical_manifest.get("planning_count") != 64:
        raise ValueError("Frozen physical sample count changed")
    if horizon.get("status") != "FORMAL_FROZEN_MATRIX_V1" or float(horizon.get("H_eval_hr", np.nan)) != 480:
        raise ValueError("Frozen common horizon changed")

    with np.load(base.PHYSICAL_DIR / "physical_inputs_2pc50.npz", allow_pickle=False) as z:
        station_ids = z["station_ids"].astype(str)
    mapping = base._load_mapping(station_ids)
    graph, sources = base._load_graph_and_sources(station_ids)
    supported, supported_idx, caps = _load_supported(station_ids)
    _assert_direct_duplicate()
    _validate_vulnerability_archive()

    support_station_mask = np.isin(mapping.station_ids, supported.StationID.astype(str))
    support_weight = mapping.weight[:, support_station_mask].sum(axis=1)
    support_tract_mask = support_weight > CAP_TOL
    population = mapping.population.astype(float)

    station_rows, tract_rows, summary_rows, recon_rows = [], [], [], []
    case_metrics, physical_cache = {}, {}
    global_binding_ids = set()
    global_binding_tract = np.zeros(len(mapping.tract_ids), dtype=bool)

    for hazard, policy in _cases():
        ref = _reference(hazard, policy)
        schedule = None
        if policy != "vulnerability-first":
            if hazard not in physical_cache:
                physical_cache[hazard] = base._load_physical(hazard, station_ids, physical_manifest)
            ds_all, duration_all = physical_cache[hazard]
            schedule = None if policy == "unconstrained" else base._load_schedule(hazard, policy, station_ids)

        sb_sum, sc_sum = np.zeros(92), np.zeros(92)
        tb_sum, tc_sum = np.zeros(len(mapping.tract_ids)), np.zeros(len(mapping.tract_ids))
        bind_hours, bind_n = np.zeros(19), np.zeros(19, dtype=int)
        recon = {"population_burden": 0.0, "T80": 0.0, "hospital_burden": 0.0}
        metrics = []

        try:
            for i in range(N):
                if policy == "vulnerability-first":
                    rid, time, arrays = _load_vulnerability_trace(i, station_ids, physical_manifest)
                else:
                    rid = f"{hazard}__evaluation_{i:04d}"
                    ds = ds_all[:, i].astype(int)
                    duration = duration_all[:, i].astype(float)
                    completion = np.where(ds > 0, duration, np.nan) if policy == "unconstrained" else schedule["completion"][i].astype(float)
                    completed = completion[np.isfinite(completion)]
                    time = np.unique(np.r_[0.0, completed, 480.0])
                    raw = base.evaluate_completion_step_functionality(
                        damage_state=pd.Series(ds, index=station_ids, dtype="int64"),
                        completion_time_hr=pd.Series(completion, index=station_ids, dtype=float),
                        time_hr=time, initial_functionality_by_ds=base.INITIAL_BY_DS,
                    )
                    arrays = _trace_arrays(base.evaluate_source_gate(raw, graph, sources, threshold=.5, mode="source_gate"))

                bsum, btract, bstation = base.evaluate_exact_event_arrays(
                    mapping=mapping, event_time_hr=time,
                    f=arrays["f"], e=arrays["e"], L_self=arrays["L_self"],
                    L_threshold=arrays["L_threshold"], L_source=arrays["L_source"], L_total=arrays["L_total"],
                )
                _reconcile_before_capacity(hazard, policy, rid, bsum, ref, recon)

                cap = _capacity_arrays(arrays, supported_idx, caps, station_ids)
                csum, ctract, cstation = base.evaluate_exact_event_arrays(
                    mapping=mapping, event_time_hr=time,
                    f=cap["f"], e=cap["e"], L_self=cap["L_self"],
                    L_threshold=cap["L_threshold"], L_source=cap["L_source"],
                    L_capacity=cap["L_capacity"], L_total=cap["L_total"],
                )
                sb_sum += bstation["L_total"]; sc_sum += cstation["L_total"]
                tb_sum += btract["normalized_burden_hr"]; tc_sum += ctract["normalized_burden_hr"]
                metrics.append({
                    "realization_id": rid,
                    "pop_base": bsum["population_weighted_normalized_burden_hr"],
                    "pop_cap": csum["population_weighted_normalized_burden_hr"],
                    "t80_base": bsum["population_T80_hr"], "t80_cap": csum["population_T80_hr"],
                    "hosp_base": bsum["hospital_mean_normalized_burden_hr"],
                    "hosp_cap": csum["hospital_mean_normalized_burden_hr"],
                })
                dt = np.diff(time)
                binding = arrays["e"][:-1, supported_idx] > caps[None, :] + CAP_TOL
                hours = np.sum(binding * dt[:, None], axis=0)
                bind_hours += hours
                bind_n += hours > CAP_TOL
        finally:
            if schedule is not None:
                schedule.close()

        m = pd.DataFrame(metrics)
        if len(m) != N or m.realization_id.nunique() != N:
            raise ValueError(f"Case realization count changed for {hazard}/{policy}")
        case_metrics[(hazard, policy)] = m
        sb, sc = sb_sum / N, sc_sum / N
        tb, tc = tb_sum / N, tc_sum / N
        td = tc - tb
        affected = td > CAP_TOL
        binding_station = bind_n > 0
        global_binding_ids |= set(supported.loc[binding_station, "StationID"])
        global_binding_tract |= affected
        label = _label(policy)

        for k, row in supported.iterrows():
            j = supported_idx[k]
            station_rows.append({
                "Hazard": hazard, "Policy": label, "Station": row.StationID,
                "baseline_service_burden": sb[j], "capacity_bounded_service_burden": sc[j],
                "difference": sc[j] - sb[j], "binding_hours": bind_hours[k] / N,
                "binding_realization_fraction": bind_n[k] / N,
            })
        for j, tract_id in enumerate(mapping.tract_ids):
            tract_rows.append({
                "Hazard": hazard, "Policy": label, "Tract": tract_id,
                "Population": population[j], "supported_dependency_weight": support_weight[j],
                "baseline_burden": tb[j], "capacity_burden": tc[j], "paired_difference": td[j],
            })
        summary_rows.append({
            "row_type": "policy", "Hazard": hazard, "Policy": label,
            "candidate_policy": label, "reference_policy": "",
            "population_burden_base": m.pop_base.mean(), "population_burden_cap": m.pop_cap.mean(),
            "delta": m.pop_cap.mean() - m.pop_base.mean(),
            "T80_base": m.t80_base.mean(), "T80_cap": m.t80_cap.mean(),
            "delta_T80": m.t80_cap.mean() - m.t80_base.mean(),
            "hospital_base": m.hosp_base.mean(), "hospital_cap": m.hosp_cap.mean(),
            "affected_population": population[affected].sum(),
            "binding_station_count": int(binding_station.sum()), "binding_tract_count": int(affected.sum()),
            "baseline_reconciled": True,
            "reconciliation_max_abs_population_burden": recon["population_burden"],
            "reconciliation_max_abs_T80": recon["T80"],
            "reconciliation_max_abs_hospital_burden": recon["hospital_burden"],
            "sign_flipped_population_burden": False,
        })
        recon_rows.append({"Hazard": hazard, "Policy": label, **recon})

    station = pd.DataFrame(station_rows)
    tract = pd.DataFrame(tract_rows)
    summary = pd.DataFrame(summary_rows)
    if len(station) != len(_cases()) * 19 or len(tract) != len(_cases()) * 2315 or len(summary) != len(_cases()):
        raise ValueError("Capacity output row count incomplete")
    if (station.difference < -1e-10).any() or (tract.paired_difference < -1e-10).any():
        raise ValueError("Capacity ceiling unexpectedly reduced burden")

    two = summary.loc[summary.Hazard.eq("2pc50")]
    expected = set(SCHEDULED) | {"Unconstrained"}
    if len(two) != 9 or set(two.Policy) != expected:
        raise ValueError(f"2pc50 policy set is wrong: {sorted(two.Policy)}")
    if "direct-community" in set(station.Policy) | set(tract.Policy) | set(summary.Policy):
        raise ValueError("direct-community must not appear in output")
    if "vulnerability-first" not in set(two.Policy):
        raise ValueError("vulnerability-first missing from output")

    _assert_anchors(summary)
    contrast = _contrasts(case_metrics)
    combined = pd.concat([summary, contrast], ignore_index=True, sort=False)

    station.to_csv(base.OUTPUT_STATION, index=False, float_format="%.10g")
    tract.to_csv(base.OUTPUT_TRACT, index=False, float_format="%.10g")
    combined.to_csv(base.OUTPUT_SUMMARY, index=False, float_format="%.10g")
    _write_audit(
        validation, physical_manifest, horizon, supported, support_weight, population,
        support_tract_mask, summary, contrast, pd.DataFrame(recon_rows),
        global_binding_ids, global_binding_tract,
    )
    _write_figure(supported, summary, len(global_binding_ids))
    print(combined.to_string(index=False))


if __name__ == "__main__":
    run()
