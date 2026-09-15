from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd


ROOT = Path(r"C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale")
REVIEW = ROOT / "Review_and_Revision" / "IJDRR-D-26-02276"
OUT = REVIEW / "13_TimeIndexed_Interface_QA_20260914"

NODES_PATH = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914" / "SCE_SERVICE_NODES_196.csv"
ATTACHMENT_PATH = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914" / "SERVICE_UPSTREAM_ATTACHMENT_LEDGER.csv"
W1_PATH = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914" / "SCE_TRACT_SERVICE_W1.csv"
TRACT_INPUT_PATH = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914" / "SERVICE_LAYER_COVERAGE_QA.csv"
BASELINE_NODE_PATH = REVIEW / "11_TwoLayer_Static_QA_20260914" / "SERVICE_NODE_BASELINE_QA.csv"
BASELINE_TRACT_PATH = REVIEW / "11_TwoLayer_Static_QA_20260914" / "TRACT_BASELINE_INTERVAL_QA.csv"
R1_CONNECTION_PATH = REVIEW / "06_R1_310_LocalClosure_20260914" / "STATION_CONNECTION_DECISIONS.csv"
TOPOLOGY_PATH = REVIEW / "06_R1_310_LocalClosure_20260914" / "R1_310_EDGES.csv"
SOURCE_LEDGER_PATH = REVIEW / "08_UtilitySpecific_SetC_20260914" / "R1_SERVICE_ROLE_CROSSWALK.csv"
TRAJECTORY_PATH = OUT / "EXTERNAL_R1_EFFECTIVE_STATE_TRAJECTORY.csv"

CENTER_ID = "300232"
MESA_ID = "301541"
EXPECTED_SOURCE_COUNT = 21
EXPECTED_SOURCE_HASH = "c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3"
TARGET_PATTERN = {
    0: {CENTER_ID: 1.0, MESA_ID: 1.0},
    1: {CENTER_ID: 0.0, MESA_ID: 1.0},
    2: {CENTER_ID: 0.0, MESA_ID: 0.0},
    3: {CENTER_ID: 1.0, MESA_ID: 0.0},
    4: {CENTER_ID: 1.0, MESA_ID: 1.0},
}
TOL = 1e-12


def safe(path: Path) -> str:
    value = str(path)
    return value if value.startswith("\\\\?\\") else "\\\\?\\" + value


def read(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(safe(path), keep_default_na=False, **kwargs)


def bool_value(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(safe(path), "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


frozen_paths = [
    NODES_PATH,
    ATTACHMENT_PATH,
    W1_PATH,
    TRACT_INPUT_PATH,
    BASELINE_NODE_PATH,
    BASELINE_TRACT_PATH,
    R1_CONNECTION_PATH,
    TOPOLOGY_PATH,
    SOURCE_LEDGER_PATH,
]
hashes_before = {str(path.relative_to(ROOT)): sha256(path) for path in frozen_paths}

nodes = read(NODES_PATH, dtype={"upstream_R1_station_id": str})
attachments = read(ATTACHMENT_PATH, dtype={"selected_upstream_R1_id": str})
w1 = read(W1_PATH, dtype={"tract_id": str})
tract_input = read(TRACT_INPUT_PATH, dtype={"tract_id": str}).set_index("tract_id")
baseline_nodes = read(BASELINE_NODE_PATH, dtype={"record_id": str, "upstream_R1_id": str})
baseline_tracts = read(BASELINE_TRACT_PATH, dtype={"tract_id": str}).set_index("tract_id")
r1_connection = read(R1_CONNECTION_PATH, dtype={"station_id": str})
source_ledger = read(SOURCE_LEDGER_PATH, dtype={"station_id": str})

assert len(r1_connection) == 310 and r1_connection["station_id"].nunique() == 310
assert len(nodes) == 196 and nodes["service_node_id"].nunique() == 196
assert len(w1) == 817 and len(tract_input) == 817
assert set(attachments["service_node_id"]) == set(nodes["service_node_id"])

source_ids = sorted(
    source_ledger.loc[source_ledger["SOURCE_SCENARIO_REFERENCE"].map(bool_value), "station_id"]
)
source_hash = hashlib.sha256(("\n".join(source_ids) + "\n").encode("utf-8")).hexdigest()
if len(source_ids) != EXPECTED_SOURCE_COUNT or source_hash != EXPECTED_SOURCE_HASH:
    raise RuntimeError(
        f"STOP: frozen 21-source scenario mismatch; count={len(source_ids)}, hash={source_hash}"
    )

network_ids = sorted(r1_connection["station_id"])
service_ids = sorted(nodes["service_node_id"])
network_id_hash = hashlib.sha256(("\n".join(network_ids) + "\n").encode("utf-8")).hexdigest()
service_id_hash = hashlib.sha256(("\n".join(service_ids) + "\n").encode("utf-8")).hexdigest()

baseline_network = baseline_nodes[baseline_nodes["record_type"].eq("R1_NETWORK_ASSET")].copy()
baseline_service = baseline_nodes[baseline_nodes["record_type"].eq("SCE_SERVICE_NODE")].copy()
assert set(baseline_network["record_id"]) == set(network_ids)
assert set(baseline_service["record_id"]) == set(service_ids)

t0_semantic = pd.to_numeric(
    baseline_network.set_index("record_id")["effective_no_damage_network_state"], errors="coerce"
).reindex(network_ids)
t0_identified = t0_semantic.notna()
# Finite serialization for the explicit external file. The identified flag is part of the state.
t0_serialized_value = t0_semantic.fillna(0.0)
assert t0_semantic.loc[CENTER_ID] == 1.0 and t0_semantic.loc[MESA_ID] == 1.0

# Create the explicit 5 x 310 external trajectory without calling any model function.
trajectory_rows = []
for time_index in sorted(TARGET_PATTERN):
    for station_id in network_ids:
        value = float(t0_serialized_value.loc[station_id])
        if station_id in TARGET_PATTERN[time_index]:
            value = TARGET_PATTERN[time_index][station_id]
        trajectory_rows.append(
            {
                "time_index": time_index,
                "R1_station_id": station_id,
                "effective_state_value": value,
                "state_identified": bool(t0_identified.loc[station_id]),
                "state_representation": (
                    "identified_effective_state"
                    if t0_identified.loc[station_id]
                    else "finite_placeholder_with_state_identified_false_semantic_NA"
                ),
                "trajectory_role": (
                    "CENTER_controlled_target"
                    if station_id == CENTER_ID
                    else "MESA_controlled_target"
                    if station_id == MESA_ID
                    else "frozen_T0_state"
                ),
            }
        )
if not TRAJECTORY_PATH.exists():
    pd.DataFrame(trajectory_rows).to_csv(
        safe(TRAJECTORY_PATH), index=False, encoding="utf-8-sig", float_format="%.15g"
    )
trajectory_hash = sha256(TRAJECTORY_PATH)

# Strict loader QA on the independent file.
trajectory = read(TRAJECTORY_PATH, dtype={"R1_station_id": str})
if len(trajectory) != 5 * 310:
    raise RuntimeError(f"STOP: trajectory row count is {len(trajectory)}, expected 1550")
if trajectory.duplicated(["time_index", "R1_station_id"]).any():
    raise RuntimeError("STOP: duplicate time-index/station IDs")
time_indices = sorted(pd.to_numeric(trajectory["time_index"]).unique().tolist())
if time_indices != [0, 1, 2, 3, 4] or any(b <= a for a, b in zip(time_indices, time_indices[1:])):
    raise RuntimeError(f"STOP: invalid time indexes {time_indices}")
values = pd.to_numeric(trajectory["effective_state_value"], errors="coerce")
if not np.isfinite(values).all() or not values.between(0.0, 1.0).all():
    raise RuntimeError("STOP: trajectory contains nonfinite or out-of-range state values")
trajectory["effective_state_value"] = values
trajectory["state_identified"] = trajectory["state_identified"].map(bool_value)
for time_index in time_indices:
    block = trajectory[trajectory["time_index"].eq(time_index)].set_index("R1_station_id")
    if set(block.index) != set(network_ids) or len(block) != 310:
        raise RuntimeError(f"STOP: time {time_index} does not contain the exact frozen 310 IDs")
    if not block["state_identified"].equals(t0_identified.reindex(block.index)):
        raise RuntimeError(f"STOP: time {time_index} changes the frozen identified/missing mask")
    non_targets = sorted(set(network_ids) - {CENTER_ID, MESA_ID})
    if not np.array_equal(
        block.loc[non_targets, "effective_state_value"].to_numpy(),
        t0_serialized_value.loc[non_targets].to_numpy(),
    ):
        raise RuntimeError(f"STOP: time {time_index} changes a non-target R1 value")
    for target_id, expected in TARGET_PATTERN[time_index].items():
        if block.loc[target_id, "effective_state_value"] != expected:
            raise RuntimeError(f"STOP: time {time_index} target {target_id} mismatch")

# ---------------- ANALYTIC EXPECTATION, frozen before propagation ----------------
node_by_id = nodes.set_index("service_node_id").reindex(service_ids)
w1_by_tract = w1.set_index("tract_id")
w_matrix = w1_by_tract[service_ids].astype(float)

def attached_service_ids(upstream_id: str) -> list[str]:
    mask = (
        node_by_id["upstream_R1_station_id"].eq(upstream_id)
        & node_by_id["attachment_class"].isin(
            ["A_DIRECT_IDENTITY_ATTACHMENT", "B_NAMED_SYSTEM_UPSTREAM_PROXY"]
        )
    )
    return sorted(node_by_id.index[mask])


center_service_ids = attached_service_ids(CENTER_ID)
mesa_service_ids = attached_service_ids(MESA_ID)
if not center_service_ids or not mesa_service_ids:
    raise RuntimeError("STOP: CENTER or MESA has no A/B attachment")
if set(center_service_ids) & set(mesa_service_ids):
    raise RuntimeError("STOP: one service node has two upstream attachments")

center_mass = w_matrix[center_service_ids].sum(axis=1)
mesa_mass = w_matrix[mesa_service_ids].sum(axis=1)
center_tracts = set(center_mass.index[center_mass > 0])
mesa_tracts = set(mesa_mass.index[mesa_mass > 0])
overlap_tracts = center_tracts & mesa_tracts

population = tract_input.loc[w_matrix.index, "population"].astype(float)
total_population = float(population.sum())
center_pop_mass = float(np.dot(population.to_numpy(), center_mass.to_numpy()))
mesa_pop_mass = float(np.dot(population.to_numpy(), mesa_mass.to_numpy()))
center_pop_share = center_pop_mass / total_population
mesa_pop_share = mesa_pop_mass / total_population

l0 = pd.to_numeric(baseline_tracts.loc[w_matrix.index, "baseline_lower"])
h0 = pd.to_numeric(baseline_tracts.loc[w_matrix.index, "baseline_upper"])
u0 = h0 - l0
expected_tract = {}
for time_index in time_indices:
    center_drop = 1.0 - TARGET_PATTERN[time_index][CENTER_ID]
    mesa_drop = 1.0 - TARGET_PATTERN[time_index][MESA_ID]
    lower = l0 - center_drop * center_mass - mesa_drop * mesa_mass
    upper = h0 - center_drop * center_mass - mesa_drop * mesa_mass
    expected_tract[time_index] = pd.DataFrame(
        {"lower": lower, "upper": upper, "width": upper - lower}, index=w_matrix.index
    )

# ---------------- PROPAGATION: consume external state vectors only ----------------
def load_semantic_vector(time_index: int) -> pd.Series:
    block = trajectory[trajectory["time_index"].eq(time_index)].set_index("R1_station_id")
    vector = block["effective_state_value"].astype(float).copy()
    vector.loc[~block["state_identified"]] = np.nan
    return vector.reindex(network_ids)


def propagate_service(network_vector: pd.Series) -> pd.Series:
    result = pd.Series(np.nan, index=service_ids, dtype=float)
    for service_id, node in node_by_id.iterrows():
        if node["attachment_class"] == "C_UNRESOLVED_ATTACHMENT":
            continue
        result.loc[service_id] = network_vector.loc[node["upstream_R1_station_id"]]
    return result


resolved_mask = node_by_id["attachment_class"].ne("C_UNRESOLVED_ATTACHMENT").to_numpy()
unresolved_mask = ~resolved_mask
resolved_mass = w_matrix.to_numpy()[:, resolved_mask].sum(axis=1)
unresolved_mass = w_matrix.to_numpy()[:, unresolved_mask].sum(axis=1)

def aggregate_tract(service_vector: pd.Series) -> pd.DataFrame:
    known = w_matrix.to_numpy()[:, resolved_mask] @ service_vector.to_numpy()[resolved_mask]
    lower = known
    upper = known + unresolved_mass
    return pd.DataFrame(
        {
            "resolved_mass": resolved_mass,
            "unresolved_mass": unresolved_mass,
            "known_available_mass": known,
            "lower": lower,
            "upper": upper,
            "width": upper - lower,
        },
        index=w_matrix.index,
    )


network_vectors = {t: load_semantic_vector(t) for t in time_indices}
service_vectors = {t: propagate_service(network_vectors[t]) for t in time_indices}
tract_vectors = {t: aggregate_tract(service_vectors[t]) for t in time_indices}

service_rows = []
for time_index in time_indices:
    expected_state = pd.Series(np.nan, index=service_ids, dtype=float)
    for service_id, node in node_by_id.iterrows():
        if node["attachment_class"] == "C_UNRESOLVED_ATTACHMENT":
            continue
        upstream_id = node["upstream_R1_station_id"]
        expected_state.loc[service_id] = TARGET_PATTERN[time_index].get(
            upstream_id, t0_semantic.loc[upstream_id]
        )
    for service_id in service_ids:
        node = node_by_id.loc[service_id]
        observed = service_vectors[time_index].loc[service_id]
        expected = expected_state.loc[service_id]
        service_rows.append(
            {
                "time_index": time_index,
                "service_node_id": service_id,
                "normalized_official_name": node["normalized_official_name"],
                "attachment_class": node["attachment_class"],
                "upstream_R1_id": node["upstream_R1_station_id"],
                "CENTER_attached": service_id in center_service_ids,
                "MESA_attached": service_id in mesa_service_ids,
                "expected_service_state": expected,
                "observed_service_state": observed,
                "state_matches_expected_1e-12": (
                    pd.isna(expected) and pd.isna(observed)
                )
                or np.isclose(expected, observed, atol=TOL),
                "Class_C_preserved_missing": (
                    pd.isna(observed)
                    if node["attachment_class"] == "C_UNRESOLVED_ATTACHMENT"
                    else True
                ),
                "state_lookup_count": 0
                if node["attachment_class"] == "C_UNRESOLVED_ATTACHMENT"
                else 1,
                "duplicate_state_check": "no_lookup_missing"
                if node["attachment_class"] == "C_UNRESOLVED_ATTACHMENT"
                else "one_upstream_R1_lookup",
            }
        )
service_time_qa = pd.DataFrame(service_rows)

tract_rows = []
for time_index in time_indices:
    observed = tract_vectors[time_index]
    expected = expected_tract[time_index]
    for tract_id in w_matrix.index:
        tract_rows.append(
            {
                "time_index": time_index,
                "tract_id": tract_id,
                "attachment_tier": tract_input.loc[tract_id, "attachment_tier"],
                "population": float(population.loc[tract_id]),
                "CENTER_mass": float(center_mass.loc[tract_id]),
                "MESA_mass": float(mesa_mass.loc[tract_id]),
                "CENTER_affected": tract_id in center_tracts,
                "MESA_affected": tract_id in mesa_tracts,
                "CENTER_MESA_overlap": tract_id in overlap_tracts,
                "unresolved_Class_C_mass": float(unresolved_mass[list(w_matrix.index).index(tract_id)]),
                "expected_lower": float(expected.loc[tract_id, "lower"]),
                "observed_lower": float(observed.loc[tract_id, "lower"]),
                "expected_upper": float(expected.loc[tract_id, "upper"]),
                "observed_upper": float(observed.loc[tract_id, "upper"]),
                "baseline_interval_width": float(u0.loc[tract_id]),
                "observed_interval_width": float(observed.loc[tract_id, "width"]),
                "lower_matches_expected_1e-12": np.isclose(
                    expected.loc[tract_id, "lower"], observed.loc[tract_id, "lower"], atol=TOL
                ),
                "upper_matches_expected_1e-12": np.isclose(
                    expected.loc[tract_id, "upper"], observed.loc[tract_id, "upper"], atol=TOL
                ),
                "width_matches_baseline_exact": observed.loc[tract_id, "width"]
                == tract_vectors[0].loc[tract_id, "width"],
                "width_matches_baseline_1e-12": np.isclose(
                    observed.loc[tract_id, "width"], tract_vectors[0].loc[tract_id, "width"], atol=TOL
                ),
            }
        )
tract_time_qa = pd.DataFrame(tract_rows)

aggregate_rows = []
for time_index in time_indices:
    observed = tract_vectors[time_index]
    expected = expected_tract[time_index]
    aggregate_rows.append(
        {
            "time_index": time_index,
            "CENTER_state": TARGET_PATTERN[time_index][CENTER_ID],
            "MESA_state": TARGET_PATTERN[time_index][MESA_ID],
            "expected_population_lower": float(np.average(expected["lower"], weights=population)),
            "observed_population_lower": float(np.average(observed["lower"], weights=population)),
            "expected_population_upper": float(np.average(expected["upper"], weights=population)),
            "observed_population_upper": float(np.average(observed["upper"], weights=population)),
            "observed_population_width": float(np.average(observed["width"], weights=population)),
        }
    )
aggregate = pd.DataFrame(aggregate_rows).set_index("time_index")

# Time-transition and superposition identities.
all_t2_change = tract_vectors[2]["lower"] - tract_vectors[0]["lower"]
all_superposition_expected = -(center_mass + mesa_mass)
superposition_pass = bool(np.allclose(all_t2_change, all_superposition_expected, atol=TOL))
overlap_index = sorted(overlap_tracts)
overlap_specific_pass = (
    bool(
        np.allclose(
            all_t2_change.loc[overlap_index],
            all_superposition_expected.loc[overlap_index],
            atol=TOL,
        )
    )
    if overlap_index
    else None
)
t2_to_t3 = tract_vectors[3]["lower"] - tract_vectors[2]["lower"]
t3_to_t4 = tract_vectors[4]["lower"] - tract_vectors[3]["lower"]

# Acceptance checks.
prior_service = pd.to_numeric(
    baseline_service.set_index("record_id")["baseline_service_state"], errors="coerce"
).reindex(service_ids)
assert np.allclose(service_vectors[0], prior_service, atol=TOL, equal_nan=True)
assert np.allclose(tract_vectors[0]["lower"], l0, atol=TOL)
assert np.allclose(tract_vectors[0]["upper"], h0, atol=TOL)
assert service_time_qa["state_matches_expected_1e-12"].all()
assert service_time_qa["Class_C_preserved_missing"].all()
assert tract_time_qa["lower_matches_expected_1e-12"].all()
assert tract_time_qa["upper_matches_expected_1e-12"].all()
assert tract_time_qa["width_matches_baseline_1e-12"].all()
assert superposition_pass
assert np.allclose(t2_to_t3, center_mass, atol=TOL)
assert np.allclose(t3_to_t4, mesa_mass, atol=TOL)
assert np.array_equal(network_vectors[0].to_numpy(), network_vectors[4].to_numpy(), equal_nan=True)
assert np.array_equal(service_vectors[0].to_numpy(), service_vectors[4].to_numpy(), equal_nan=True)
assert np.array_equal(tract_vectors[0].to_numpy(), tract_vectors[4].to_numpy(), equal_nan=True)
assert np.allclose(aggregate["observed_population_lower"], aggregate["expected_population_lower"], atol=TOL)
assert np.allclose(aggregate["observed_population_upper"], aggregate["expected_population_upper"], atol=TOL)
assert np.allclose(aggregate["observed_population_width"], aggregate.loc[0, "observed_population_width"], atol=TOL)
assert int((node_by_id["attachment_class"] == "C_UNRESOLVED_ATTACHMENT").sum()) == 12
assert not attachments["physical_edge_created"].map(bool_value).any()
assert not attachments["topology_modified"].map(bool_value).any()
assert not attachments["source_activated"].map(bool_value).any()

hashes_after = {str(path.relative_to(ROOT)): sha256(path) for path in frozen_paths}
assert hashes_before == hashes_after

service_time_qa.to_csv(
    safe(OUT / "SERVICE_NODE_TIME_QA.csv"), index=False, encoding="utf-8-sig", float_format="%.15g"
)
tract_time_qa.to_csv(
    safe(OUT / "TRACT_TIME_INTERVAL_QA.csv"), index=False, encoding="utf-8-sig", float_format="%.15g"
)

def service_details(ids: list[str]) -> list[dict]:
    details = []
    for service_id in ids:
        node = node_by_id.loc[service_id]
        details.append(
            {
                "service_node_id": service_id,
                "name": node["normalized_official_name"],
                "attachment_class": node["attachment_class"],
                "tract_candidate_relations": int((w_matrix[service_id] > 0).sum()),
                "population_weighted_W1_mass": float(np.dot(population, w_matrix[service_id])),
            }
        )
    return details


summary = {
    "decision": "PASS_TIME_INDEXED_INTERFACE_VERIFIED",
    "trajectory_hash_sha256": trajectory_hash,
    "trajectory_rows": len(trajectory),
    "trajectory_time_indices": time_indices,
    "source_count": len(source_ids),
    "source_hash": source_hash,
    "network_id_count": len(network_ids),
    "network_id_hash": network_id_hash,
    "service_id_count": len(service_ids),
    "service_id_hash": service_id_hash,
    "frozen_hashes_unchanged": hashes_before == hashes_after,
    "unresolved_network_state_serialization_count": int((~t0_identified).sum()),
    "CENTER_service_node_count": len(center_service_ids),
    "CENTER_A_count": int((node_by_id.loc[center_service_ids, "attachment_class"] == "A_DIRECT_IDENTITY_ATTACHMENT").sum()),
    "CENTER_B_count": int((node_by_id.loc[center_service_ids, "attachment_class"] == "B_NAMED_SYSTEM_UPSTREAM_PROXY").sum()),
    "CENTER_service_nodes": service_details(center_service_ids),
    "MESA_service_node_count": len(mesa_service_ids),
    "MESA_A_count": int((node_by_id.loc[mesa_service_ids, "attachment_class"] == "A_DIRECT_IDENTITY_ATTACHMENT").sum()),
    "MESA_B_count": int((node_by_id.loc[mesa_service_ids, "attachment_class"] == "B_NAMED_SYSTEM_UPSTREAM_PROXY").sum()),
    "MESA_service_nodes": service_details(mesa_service_ids),
    "CENTER_population_weighted_W1_mass": center_pop_mass,
    "CENTER_population_weighted_W1_share": center_pop_share,
    "MESA_population_weighted_W1_mass": mesa_pop_mass,
    "MESA_population_weighted_W1_share": mesa_pop_share,
    "CENTER_affected_tracts": len(center_tracts),
    "MESA_affected_tracts": len(mesa_tracts),
    "overlap_tracts": len(overlap_tracts),
    "overlap_tract_ids": sorted(overlap_tracts),
    "service_state_all_match": bool(service_time_qa["state_matches_expected_1e-12"].all()),
    "Class_C_missing_all_times": bool(service_time_qa["Class_C_preserved_missing"].all()),
    "tract_lower_all_match": bool(tract_time_qa["lower_matches_expected_1e-12"].all()),
    "tract_upper_all_match": bool(tract_time_qa["upper_matches_expected_1e-12"].all()),
    "interval_width_all_match_1e-12": bool(tract_time_qa["width_matches_baseline_1e-12"].all()),
    "interval_width_exact_count": int(tract_time_qa["width_matches_baseline_exact"].sum()),
    "interval_record_count": len(tract_time_qa),
    "superposition_identity_pass": superposition_pass,
    "overlap_specific_superposition_pass": overlap_specific_pass,
    "t2_to_t3_equals_CENTER_mass": bool(np.allclose(t2_to_t3, center_mass, atol=TOL)),
    "t3_to_t4_equals_MESA_mass": bool(np.allclose(t3_to_t4, mesa_mass, atol=TOL)),
    "t4_exact_network_restore": bool(np.array_equal(network_vectors[0].to_numpy(), network_vectors[4].to_numpy(), equal_nan=True)),
    "t4_exact_service_restore": bool(np.array_equal(service_vectors[0].to_numpy(), service_vectors[4].to_numpy(), equal_nan=True)),
    "t4_exact_tract_restore": bool(np.array_equal(tract_vectors[0].to_numpy(), tract_vectors[4].to_numpy(), equal_nan=True)),
    "aggregate": aggregate.reset_index().to_dict("records"),
    "duplicate_state_check": "PASS_ONE_UPSTREAM_R1_LOOKUP_PER_A_B_SERVICE_NODE_PER_TIME",
}
summary_path = Path(r"C:\ABAQUS\temp\sce_service_layer_20260914\time_indexed_summary.json")
with open(safe(summary_path), "w", encoding="utf-8") as handle:
    json.dump(summary, handle, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
