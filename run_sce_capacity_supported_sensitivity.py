from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from r1_formal_offline import PreparedMapping, evaluate_exact_event_arrays
from r1_realization_scheduling import INITIAL_BY_DS, evaluate_completion_step_functionality
from r1_source_gate import evaluate_source_gate


ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "Formal_Experiment_20260923"
SUPPORTED_PATH = ROOT / "SCE_CAPACITY_SUPPORTED_STATIONS.csv"
MAPPING_PATH = ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv"
META_PATH = ROOT / "R1_Comment1_July92_Utility_Constraint" / "MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv"
GRAPH_PATH = ROOT / "Data" / "substation_graph_CEC_edges_expanded.csv"
SOURCE_PATH = ROOT / "Data" / "source_nodes_core_expanded.csv"
VALIDATION_PATH = FORMAL / "FINAL_EXECUTION_VALIDATION.json"
PHYSICAL_MANIFEST_PATH = FORMAL / "Stage 1 Output_expanded" / "PHYSICAL_INPUTS_FROZEN.json"
HORIZON_PATH = FORMAL / "Formal_Schedule_Prepass" / "EVALUATION_HORIZON.json"
SCHEDULE_DIR = FORMAL / "Formal_Schedule_Prepass"
PHYSICAL_DIR = FORMAL / "Stage 1 Output_expanded"
FIGURE_DIR = ROOT / "Manuscript_Figures"

HAZARDS = ["Northridge", "SanFernando", "LongBeach", "2pc50"]
SCHEDULED = [
    "hospital-first",
    "impact-first",
    "degree-first",
    "closeness-first",
    "betweenness-first",
    "centrality-first",
    "random",
    "direct-community",
]
POLICY_OUTPUT = {"unconstrained": "Unconstrained", **{x: x for x in SCHEDULED}}
CAPACITY_TOL = 1e-12
N_REALIZATIONS = 1000


OUTPUT_STATION = ROOT / "SCE_CAPACITY_SENSITIVITY_STATION.csv"
OUTPUT_TRACT = ROOT / "SCE_CAPACITY_SENSITIVITY_TRACT.csv"
OUTPUT_SUMMARY = ROOT / "SCE_CAPACITY_SENSITIVITY_SUMMARY.csv"
OUTPUT_AUDIT = ROOT / "SCE_CAPACITY_SENSITIVITY_AUDIT.md"
FIGURE_STEM = FIGURE_DIR / "vis_sce_capacity_supported_sensitivity"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _require_file_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing frozen input: {path}")
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"Frozen input hash changed for {label}: {actual} != {expected}")


def _load_frozen_validation() -> dict:
    validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    if validation.get("status") != "PASS_DRY_VALIDATION_NO_SAMPLING_OR_SCHEDULING":
        raise ValueError("Formal frozen-input validation is not PASS")
    if validation.get("counts", {}).get("stations") != 92 or validation.get("counts", {}).get("tracts") != 2315:
        raise ValueError("Formal domain differs from 92 stations / 2315 tracts")
    expected = {k.replace("\\", "/"): v for k, v in validation["input_sha256"].items()}
    for path in (MAPPING_PATH, GRAPH_PATH, SOURCE_PATH):
        rel = path.relative_to(ROOT).as_posix()
        if rel not in expected:
            raise ValueError(f"Frozen validation lacks hash for {rel}")
        _require_file_hash(path, expected[rel], rel)
    return validation


def _load_mapping(station_ids: np.ndarray) -> PreparedMapping:
    long = pd.read_csv(MAPPING_PATH, dtype={"tract_id": str, "substation_id": str})
    if long.duplicated(["tract_id", "substation_id"]).any():
        raise ValueError("Production mapping has duplicated tract-station rows")
    frame = long.pivot(index="tract_id", columns="substation_id", values="weight").fillna(0.0)
    meta = pd.read_csv(META_PATH, dtype={"tract_id": str}).set_index("tract_id")
    if len(meta) != 2315 or meta.index.has_duplicates:
        raise ValueError("Frozen tract metadata differs from 2315 unique tracts")
    if not {"population", "SOVI_quartile", "hospital_tract"}.issubset(meta.columns):
        raise ValueError("Frozen tract metadata lacks formal population/quartile/hospital fields")
    hospital_tracts = set(meta.index[meta["hospital_tract"]])
    return PreparedMapping.from_frame(
        "M1_UTILITY_003",
        frame,
        station_ids,
        meta.population,
        meta.SOVI_quartile,
        hospital_tracts,
    )


def _clean_id(value: object) -> str:
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def _load_graph_and_sources(station_ids: np.ndarray) -> tuple[nx.Graph, set[str]]:
    edges = pd.read_csv(GRAPH_PATH, dtype={"u": str, "v": str})
    if not {"u", "v"}.issubset(edges.columns):
        raise ValueError("Frozen graph edge file lacks u/v columns")
    graph = nx.from_pandas_edgelist(edges, "u", "v")
    ids = set(map(str, station_ids))
    if graph.number_of_nodes() != 92 or graph.number_of_edges() != 318 or set(map(str, graph.nodes)) != ids:
        raise ValueError("Frozen graph differs from the 92-node / 318-edge formal graph")

    src = pd.read_csv(SOURCE_PATH)
    id_col = next((c for c in ["substation_id", "HIFLD_ID", "ID", "id", "node_id"] if c in src.columns), None)
    if id_col is None:
        raise ValueError("Source table lacks a usable station ID column")
    role_cols = [c for c in ["level", "role", "source_level", "source_type", "active_set"] if c in src.columns]
    role_text = pd.Series("", index=src.index, dtype="object")
    for col in role_cols:
        role_text = role_text + " " + src[col].astype(str).str.lower()
    is_source = (
        role_text.str.contains("core", na=False)
        | role_text.str.contains("import_interface_proxy", na=False)
        | role_text.str.contains("in_basin_generation_proxy", na=False)
    )
    is_source &= ~role_text.str.contains(r"transit_hub_not_source|\btransit\b", na=False, regex=True)
    sources = {_clean_id(v) for v in src.loc[is_source, id_col]}
    sources &= ids
    if len(sources) != 14:
        raise ValueError(f"Frozen source set differs from 14 Core sources: {len(sources)}")
    return graph, sources


def _load_supported(station_ids: np.ndarray) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    supported = pd.read_csv(SUPPORTED_PATH, dtype={"StationID": str})
    required = [
        "StationID", "StationName", "Facility", "Voltage", "D_MW", "K_MW", "K_over_D",
        "calculated_loading_pct", "provider_loading_pct", "loading_difference_pp", "provenance",
    ]
    if list(supported.columns) != required or len(supported) != 19 or supported.StationID.nunique() != 19:
        raise ValueError("Supported-station table must contain exactly the fixed 19 one-to-one stations")
    supported["D_MW"] = pd.to_numeric(supported["D_MW"], errors="raise")
    supported["K_MW"] = pd.to_numeric(supported["K_MW"], errors="raise")
    calc_ratio = supported["K_MW"] / supported["D_MW"]
    if not np.allclose(calc_ratio, supported["K_over_D"], rtol=0, atol=5e-9):
        raise ValueError("Supported-station K/D values are inconsistent with D and K")
    lookup = {sid: i for i, sid in enumerate(station_ids)}
    if not set(supported.StationID).issubset(lookup):
        raise ValueError("A supported SCE station is absent from the frozen 92-station domain")
    idx = np.array([lookup[sid] for sid in supported.StationID], dtype=int)
    caps = np.minimum(1.0, calc_ratio.to_numpy(float))
    if int(np.count_nonzero(caps < 1.0 - CAPACITY_TOL)) != 1:
        raise ValueError("Expected exactly one supported facility with K/D < 1 in the retained evidence")
    return supported, idx, caps


def _load_physical(hazard: str, station_ids: np.ndarray, manifest: dict) -> tuple[np.ndarray, np.ndarray]:
    path = PHYSICAL_DIR / f"physical_inputs_{hazard}.npz"
    expected = manifest["files_sha256"].get(hazard)
    if not expected:
        raise ValueError(f"Frozen physical manifest lacks {hazard}")
    _require_file_hash(path, expected, f"physical_inputs_{hazard}")
    with np.load(path, allow_pickle=False) as z:
        ids = z["station_ids"].astype(str)
        if not np.array_equal(ids, station_ids):
            raise ValueError(f"Physical station order changed for {hazard}")
        ds = z["evaluation_ds"].copy()
        duration = z["evaluation_duration"].copy()
    if ds.shape != (92, N_REALIZATIONS) or duration.shape != ds.shape:
        raise ValueError(f"Frozen evaluation samples are not 92 x {N_REALIZATIONS} for {hazard}")
    return ds, duration


def _load_schedule(hazard: str, policy: str, station_ids: np.ndarray):
    npz_path = SCHEDULE_DIR / f"{hazard}__C57_D1__{policy}.npz"
    json_path = npz_path.with_suffix(".json")
    record = json.loads(json_path.read_text(encoding="utf-8"))
    if record.get("status") != "FORMAL_FROZEN_MATRIX_V1" or record.get("schedule_count") != N_REALIZATIONS:
        raise ValueError(f"Frozen schedule record is invalid: {json_path.name}")
    _require_file_hash(npz_path, record["npz_sha256"], npz_path.name)
    z = np.load(npz_path, allow_pickle=False)
    if not np.array_equal(z["station_ids"].astype(str), station_ids):
        z.close()
        raise ValueError(f"Frozen schedule station order changed for {hazard}/{policy}")
    if z["completion"].shape != (N_REALIZATIONS, 92):
        z.close()
        raise ValueError(f"Frozen completion array has unexpected shape for {hazard}/{policy}")
    return z


def _capacity_trace_arrays(trace, supported_idx: np.ndarray, caps: np.ndarray) -> dict[str, np.ndarray]:
    e_base = trace.e.to_numpy(float)
    e_cap = e_base.copy()
    e_cap[:, supported_idx] = np.minimum(e_cap[:, supported_idx], caps[None, :])
    l_capacity = e_base - e_cap
    l_total = 1.0 - e_cap
    unknown = ~np.isfinite(trace.f.to_numpy(float))
    e_cap[unknown] = np.nan
    l_capacity[unknown] = np.nan
    l_total[unknown] = np.nan
    return {
        "f": trace.f.to_numpy(float),
        "e": e_cap,
        "L_self": trace.L_self.to_numpy(float),
        "L_threshold": trace.L_threshold.to_numpy(float),
        "L_source": trace.L_source.to_numpy(float),
        "L_capacity": l_capacity,
        "L_total": l_total,
    }


def _case_list() -> list[tuple[str, str]]:
    batch_a = [(hazard, "hospital-first") for hazard in HAZARDS]
    batch_b = [("2pc50", p) for p in [*SCHEDULED, "unconstrained"]]
    return list(dict.fromkeys(batch_a + batch_b))


def _output_policy(policy: str) -> str:
    return POLICY_OUTPUT[policy]


def run() -> None:
    validation = _load_frozen_validation()
    physical_manifest = json.loads(PHYSICAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    if physical_manifest.get("evaluation_count") != 4000 or physical_manifest.get("planning_count") != 64:
        raise ValueError("Frozen physical manifest count changed")
    horizon_record = json.loads(HORIZON_PATH.read_text(encoding="utf-8"))
    if horizon_record.get("status") != "FORMAL_FROZEN_MATRIX_V1" or horizon_record.get("schedule_shards") != 80:
        raise ValueError("Frozen formal schedule horizon record is invalid")
    horizon = float(horizon_record["H_eval_hr"])
    if horizon != 480.0:
        raise ValueError(f"Expected frozen common evaluation horizon 480 h, got {horizon}")

    # Use the frozen station order stored with the formal physical samples as the authority.
    with np.load(PHYSICAL_DIR / "physical_inputs_2pc50.npz", allow_pickle=False) as z:
        station_ids = z["station_ids"].astype(str)
    if len(station_ids) != 92 or len(set(station_ids)) != 92:
        raise ValueError("Frozen station identity/order is not 92 unique IDs")

    mapping = _load_mapping(station_ids)
    graph, sources = _load_graph_and_sources(station_ids)
    supported, supported_idx, caps = _load_supported(station_ids)
    supported_set = set(supported.StationID)

    support_mask = np.isin(mapping.station_ids, list(supported_set))
    supported_dependency_weight = mapping.weight[:, support_mask].sum(axis=1)
    population = mapping.population.astype(float)
    support_tract_mask = supported_dependency_weight > CAPACITY_TOL
    population_weighted_support = float(np.dot(population, supported_dependency_weight) / population.sum())
    support_quantiles = np.quantile(supported_dependency_weight, [0.25, 0.50, 0.75])

    station_rows: list[dict] = []
    tract_rows: list[dict] = []
    summary_rows: list[dict] = []
    global_binding_station_ids: set[str] = set()
    global_binding_tract = np.zeros(len(mapping.tract_ids), dtype=bool)

    physical_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    for hazard, policy in _case_list():
        if hazard not in physical_cache:
            physical_cache[hazard] = _load_physical(hazard, station_ids, physical_manifest)
        ds_all, duration_all = physical_cache[hazard]
        schedule = None if policy == "unconstrained" else _load_schedule(hazard, policy, station_ids)

        station_base_sum = np.zeros(92, dtype=float)
        station_cap_sum = np.zeros(92, dtype=float)
        tract_base_sum = np.zeros(len(mapping.tract_ids), dtype=float)
        tract_cap_sum = np.zeros(len(mapping.tract_ids), dtype=float)
        pop_base = []
        pop_cap = []
        t80_base = []
        t80_cap = []
        hospital_base = []
        hospital_cap = []
        binding_hours_sum = np.zeros(19, dtype=float)
        binding_realization_count = np.zeros(19, dtype=int)

        try:
            for r in range(N_REALIZATIONS):
                ds = ds_all[:, r].astype(int)
                duration = duration_all[:, r].astype(float)
                if policy == "unconstrained":
                    completion = np.where(ds > 0, duration, np.nan)
                else:
                    completion = schedule["completion"][r].astype(float)

                completed = completion[np.isfinite(completion)]
                times = np.unique(np.r_[0.0, completed, horizon])
                ds_series = pd.Series(ds, index=station_ids, dtype="int64")
                completion_series = pd.Series(completion, index=station_ids, dtype=float)
                raw = evaluate_completion_step_functionality(
                    damage_state=ds_series,
                    completion_time_hr=completion_series,
                    time_hr=times,
                    initial_functionality_by_ds=INITIAL_BY_DS,
                )
                trace = evaluate_source_gate(raw, graph, sources, threshold=0.5, mode="source_gate")

                base_summary, base_tract, base_station = evaluate_exact_event_arrays(
                    mapping=mapping,
                    event_time_hr=times,
                    f=trace.f.to_numpy(float),
                    e=trace.e.to_numpy(float),
                    L_self=trace.L_self.to_numpy(float),
                    L_threshold=trace.L_threshold.to_numpy(float),
                    L_source=trace.L_source.to_numpy(float),
                    L_total=trace.L_total.to_numpy(float),
                )
                cap_arrays = _capacity_trace_arrays(trace, supported_idx, caps)
                cap_summary, cap_tract, cap_station = evaluate_exact_event_arrays(
                    mapping=mapping,
                    event_time_hr=times,
                    f=cap_arrays["f"],
                    e=cap_arrays["e"],
                    L_self=cap_arrays["L_self"],
                    L_threshold=cap_arrays["L_threshold"],
                    L_source=cap_arrays["L_source"],
                    L_capacity=cap_arrays["L_capacity"],
                    L_total=cap_arrays["L_total"],
                )

                station_base_sum += base_station["L_total"]
                station_cap_sum += cap_station["L_total"]
                tract_base_sum += base_tract["normalized_burden_hr"]
                tract_cap_sum += cap_tract["normalized_burden_hr"]
                pop_base.append(base_summary["population_weighted_normalized_burden_hr"])
                pop_cap.append(cap_summary["population_weighted_normalized_burden_hr"])
                t80_base.append(base_summary["population_T80_hr"])
                t80_cap.append(cap_summary["population_T80_hr"])
                hospital_base.append(base_summary["hospital_mean_normalized_burden_hr"])
                hospital_cap.append(cap_summary["hospital_mean_normalized_burden_hr"])

                dt = np.diff(times)
                e_supported = trace.e.to_numpy(float)[:-1, supported_idx]
                binding = e_supported > caps[None, :] + CAPACITY_TOL
                hours = np.sum(binding * dt[:, None], axis=0)
                binding_hours_sum += hours
                binding_realization_count += hours > CAPACITY_TOL
        finally:
            if schedule is not None:
                schedule.close()

        station_base_mean = station_base_sum / N_REALIZATIONS
        station_cap_mean = station_cap_sum / N_REALIZATIONS
        tract_base_mean = tract_base_sum / N_REALIZATIONS
        tract_cap_mean = tract_cap_sum / N_REALIZATIONS
        tract_difference = tract_cap_mean - tract_base_mean
        affected = tract_difference > CAPACITY_TOL
        binding_station = binding_realization_count > 0
        binding_ids = set(supported.loc[binding_station, "StationID"])
        global_binding_station_ids |= binding_ids
        case_binding_tract = affected.copy()
        global_binding_tract |= case_binding_tract

        policy_out = _output_policy(policy)
        for k, row in supported.iterrows():
            idx = supported_idx[k]
            station_rows.append({
                "Hazard": hazard,
                "Policy": policy_out,
                "Station": row["StationID"],
                "baseline_service_burden": station_base_mean[idx],
                "capacity_bounded_service_burden": station_cap_mean[idx],
                "difference": station_cap_mean[idx] - station_base_mean[idx],
                "binding_hours": binding_hours_sum[k] / N_REALIZATIONS,
                "binding_realization_fraction": binding_realization_count[k] / N_REALIZATIONS,
            })

        for i, tract_id in enumerate(mapping.tract_ids):
            tract_rows.append({
                "Hazard": hazard,
                "Policy": policy_out,
                "Tract": tract_id,
                "Population": population[i],
                "supported_dependency_weight": supported_dependency_weight[i],
                "baseline_burden": tract_base_mean[i],
                "capacity_burden": tract_cap_mean[i],
                "paired_difference": tract_difference[i],
            })

        pop_base_mean = float(np.mean(pop_base))
        pop_cap_mean = float(np.mean(pop_cap))
        t80_base_mean = float(np.mean(t80_base))
        t80_cap_mean = float(np.mean(t80_cap))
        hosp_base_mean = float(np.mean(hospital_base))
        hosp_cap_mean = float(np.mean(hospital_cap))
        summary_rows.append({
            "Hazard": hazard,
            "Policy": policy_out,
            "population_burden_base": pop_base_mean,
            "population_burden_cap": pop_cap_mean,
            "delta": pop_cap_mean - pop_base_mean,
            "T80_base": t80_base_mean,
            "T80_cap": t80_cap_mean,
            "delta_T80": t80_cap_mean - t80_base_mean,
            "hospital_base": hosp_base_mean,
            "hospital_cap": hosp_cap_mean,
            "affected_population": float(population[affected].sum()),
            "binding_station_count": int(binding_station.sum()),
            "binding_tract_count": int(case_binding_tract.sum()),
        })

    station_df = pd.DataFrame(station_rows)
    tract_df = pd.DataFrame(tract_rows)
    summary_df = pd.DataFrame(summary_rows)

    if len(station_df) != len(_case_list()) * 19:
        raise ValueError("Station sensitivity output row count is incomplete")
    if len(tract_df) != len(_case_list()) * 2315:
        raise ValueError("Tract sensitivity output row count is incomplete")
    if len(summary_df) != len(_case_list()):
        raise ValueError("Summary sensitivity output row count is incomplete")
    if (station_df["difference"] < -1e-10).any() or (tract_df["paired_difference"] < -1e-10).any():
        raise ValueError("A capacity ceiling unexpectedly reduced service burden")

    station_df.to_csv(OUTPUT_STATION, index=False, float_format="%.10g")
    tract_df.to_csv(OUTPUT_TRACT, index=False, float_format="%.10g")
    summary_df.to_csv(OUTPUT_SUMMARY, index=False, float_format="%.10g")

    _write_audit(
        validation=validation,
        physical_manifest=physical_manifest,
        horizon_record=horizon_record,
        supported=supported,
        supported_dependency_weight=supported_dependency_weight,
        population=population,
        support_tract_mask=support_tract_mask,
        population_weighted_support=population_weighted_support,
        support_quantiles=support_quantiles,
        summary=summary_df,
        global_binding_station_ids=global_binding_station_ids,
        global_binding_tract=global_binding_tract,
    )
    _write_figure(supported, summary_df, len(global_binding_station_ids))

    print(summary_df.to_string(index=False))
    print(
        json.dumps(
            {
                "supported_stations": 19,
                "multi_facility_excluded": 9,
                "tracts_with_supported_dependency": int(support_tract_mask.sum()),
                "tracts_without_supported_dependency": int((~support_tract_mask).sum()),
                "population_weighted_mean_supported_dependency_mass": population_weighted_support,
                "binding_station_count_any_case": len(global_binding_station_ids),
                "binding_tract_count_any_case": int(global_binding_tract.sum()),
            },
            indent=2,
        )
    )


def _write_audit(*, validation: dict, physical_manifest: dict, horizon_record: dict,
                 supported: pd.DataFrame, supported_dependency_weight: np.ndarray,
                 population: np.ndarray, support_tract_mask: np.ndarray,
                 population_weighted_support: float, support_quantiles: np.ndarray,
                 summary: pd.DataFrame, global_binding_station_ids: set[str],
                 global_binding_tract: np.ndarray) -> None:
    discrepant_multi = (
        "COLORADO 66/4.16 (+0.07704 pp), GANESHA 12/4.16 (-0.05190 pp), "
        "and REPETTO 66/4.16 (+0.06551 pp)"
    )
    binding_names = supported.loc[supported.StationID.isin(global_binding_station_ids), ["StationID", "Facility"]]
    binding_text = ", ".join(f"{r.StationID} ({r.Facility})" for r in binding_names.itertuples()) or "none"
    case_lines = []
    for r in summary.itertuples(index=False):
        case_lines.append(
            f"- {r.Hazard} / {r.Policy}: population burden Δ={r.delta:.6f} h; "
            f"T80 Δ={r.delta_T80:.6f} h; hospital burden Δ={(r.hospital_cap-r.hospital_base):.6f} h; "
            f"binding stations={int(r.binding_station_count)}; binding tracts={int(r.binding_tract_count)}; "
            f"affected population={r.affected_population:.0f}."
        )
    audit = f"""# SCE Capacity Sensitivity Audit

## Data definition

The sensitivity uses only the 28 retained SCE stations with numeric 2026 `CUMULATIVE_DEMAND` and `FAC_LOAD_LIMIT` evidence, and only the 19 stations with one numeric provider facility row are assigned a station-level capacity ceiling. `CUMULATIVE_DEMAND` is used as D (MW) and `FAC_LOAD_LIMIT` as K (MW), following the SCE GNA/DUPR public definitions. Provider `FACILITY_LOADING` is QA only and never enters the sensitivity equation. The 19-row input is `SCE_CAPACITY_SUPPORTED_STATIONS.csv`.

The earlier 0.05-percentage-point loading-consistency screen is not used as an eligibility test. The three retained numeric facility rows above that QA discrepancy threshold are {discrepant_multi}. All three belong to multi-facility retained stations. They are retained as QA discrepancies; their stations are excluded from station-level capacity assignment solely because a one-to-one station-facility interpretation is unavailable, not because of the discrepancy.

## 19-station coverage

- Supported retained stations: 19 of 92.
- Numeric-evidence retained SCE stations: 28; the remaining 9 are multi-facility.
- Tracts with positive weight on at least one supported station: {int(support_tract_mask.sum())} of 2315.
- Tracts with zero supported-station weight: {int((~support_tract_mask).sum())} of 2315.
- Population-weighted mean supported dependency mass: {population_weighted_support:.6f}.
- `W_r^sup` P25/P50/P75 across all 2315 tracts: {support_quantiles[0]:.6f}, {support_quantiles[1]:.6f}, {support_quantiles[2]:.6f}.
- Stations for which the capacity ceiling actually binds in at least one evaluated realization/case: {len(global_binding_station_ids)} ({binding_text}).
- Tracts with a positive capacity-induced burden change in at least one evaluated case: {int(global_binding_tract.sum())}.

These coverage statistics describe where public SCE evidence permits the perturbation. Unsupported stations remain at baseline service in the sensitivity; they are not classified as capacity-adequate.

## Formula

Production service is unchanged: `e_i(t)=f_i(t)F_i(t)C_i(t)`. For each of the 19 supported stations, `a_i=min(1,K_i/D_i)` and the sensitivity service is `e_i^cap(t)=min(e_i(t),a_i)`. Equivalently, `P_i^base(t)=D_i e_i(t)`, `P_i^served(t)=min(P_i^base(t),K_i)`, and `e_i^cap(t)=P_i^served(t)/D_i`. Unsupported stations use `e_i^cap(t)=e_i(t)`.

Tract service uses the frozen production weights: `A_r^cap(t)=sum_i w_ri e_i^cap(t)`. The capacity loss term is `L_capacity=e-e_cap`, and the existing formal exact-event evaluator is used for cumulative burden, population T80, and hospital burden with `L_total=1-e_cap`. No multiplicative derating and no new metric definition are used. Positive differences in the output tables mean capacity-bounded burden minus baseline burden.

## Why 9 multi-facility stations do not enter

The 28 numeric-evidence retained stations contain 37 numeric voltage-level facility rows: 19 stations have one facility row and 9 stations have two. SCE's public definitions provide facility-level demand and facility loading limits but no official rule for summing, averaging, minimizing, maximizing, or otherwise aggregating multiple facility rows into one retained-station capacity. The 9 multi-facility stations therefore receive no station-level capacity factor in this sensitivity.

## Frozen inputs

Batch A is the four hazards (`Northridge`, `SanFernando`, `LongBeach`, `2pc50`) under `hospital-first`. Batch B is `2pc50` under the eight frozen scheduled policies (`hospital-first`, `impact-first`, `degree-first`, `closeness-first`, `betweenness-first`, `centrality-first`, `random`, `direct-community`) plus `Unconstrained`. The overlapping `2pc50 / hospital-first` case is evaluated once, giving 12 distinct hazard-policy cases.

Every case uses the frozen 1000 evaluation realizations, damage states, repair durations, 57-crew C57_D1 schedule completions for scheduled policies, baseline 0.5 source gate with 14 Core sources, production `JULY_UTILITY_CONSTRAINED_92` tract mapping, and common {float(horizon_record['H_eval_hr']):.0f}-h exact-event horizon. The script verifies the formal hashes for the physical files, schedule shards, graph, source table, and production mapping before evaluation. No GA is run, no policy is reoptimized, and no schedule is redispatched. Formal matrix ID: `{validation['matrix_id']}`; matrix SHA-256: `{validation['matrix_sha256']}`; physical executable identity: `{physical_manifest['executable_code_commit_sha']}`.

`binding_hours` in the station table is the mean exact-event duration per realization for which baseline `e_i(t)>a_i`; `binding_realization_fraction` is the fraction of the 1000 paired realizations with positive binding duration. `affected_population` is the population in tracts with positive mean paired capacity-induced burden for that hazard-policy case.

## Effect sizes

{chr(10).join(case_lines)}

The sensitivity answers only how much modeled recovery outcomes change when provider-defined planning capacity ceilings are imposed on the retained facilities for which public SCE data support an unambiguous one-to-one station-facility interpretation. It does not validate a complete capacity model or a Los Angeles AC/DC power-flow model.
"""
    OUTPUT_AUDIT.write_text(audit, encoding="utf-8")


def _write_figure(supported: pd.DataFrame, summary: pd.DataFrame, binding_station_count: int) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))

    # A: one-to-one supported facilities, D and K on the same MW axis.
    a = supported.sort_values("D_MW").reset_index(drop=True)
    y = np.arange(len(a))
    axes[0].scatter(a["D_MW"], y, label="D (MW)", marker="o")
    axes[0].scatter(a["K_MW"], y, label="K (MW)", marker="s")
    for i, r in a.iterrows():
        axes[0].plot([r["D_MW"], r["K_MW"]], [i, i], linewidth=0.8)
        if r["D_MW"] > r["K_MW"]:
            axes[0].annotate("D>K", (r["D_MW"], i), xytext=(4, 4), textcoords="offset points", fontsize=8)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(a["StationName"], fontsize=7)
    axes[0].set_xlabel("MW")
    axes[0].set_title(f"A. Supported one-to-one facilities\nBinding-capable: {binding_station_count} of 19")
    axes[0].legend(fontsize=8)

    # B: four-hazard Hospital-first effect.
    b = summary[summary["Policy"].eq("hospital-first")].set_index("Hazard").reindex(HAZARDS).reset_index()
    axes[1].bar(b["Hazard"], b["delta"])
    axes[1].axhline(0.0, linewidth=0.8)
    axes[1].tick_params(axis="x", rotation=30)
    axes[1].set_ylabel("Capacity-bounded minus baseline burden (h)")
    axes[1].set_title("B. Hospital-first across four hazards")
    for i, v in enumerate(b["delta"]):
        axes[1].annotate(f"{v:.4g}", (i, v), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=8)

    # C: all 2pc50 policies, including Unconstrained.
    order = [*SCHEDULED, "Unconstrained"]
    c = summary[summary["Hazard"].eq("2pc50")].set_index("Policy").reindex(order).reset_index()
    axes[2].bar(np.arange(len(c)), c["delta"])
    axes[2].axhline(0.0, linewidth=0.8)
    axes[2].set_xticks(np.arange(len(c)))
    axes[2].set_xticklabels(c["Policy"], rotation=55, ha="right", fontsize=8)
    axes[2].set_ylabel("Capacity-bounded minus baseline burden (h)")
    axes[2].set_title("C. 2pc50 frozen policy comparison")
    for i, v in enumerate(c["delta"]):
        axes[2].annotate(f"{v:.4g}", (i, v), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=7)

    fig.suptitle("SCE-supported capacity-ceiling sensitivity", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(FIGURE_STEM.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(FIGURE_STEM.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    from sce_capacity_closure import run as run_closed_capacity_sensitivity
    run_closed_capacity_sensitivity()
