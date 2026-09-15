from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd


ROOT = Path(r"C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale")
REVIEW = ROOT / "Review_and_Revision" / "IJDRR-D-26-02276"
OUT = REVIEW / "12_CENTER_Deterministic_Event_20260914"

NODES_PATH = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914" / "SCE_SERVICE_NODES_196.csv"
ATTACHMENT_PATH = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914" / "SERVICE_UPSTREAM_ATTACHMENT_LEDGER.csv"
W1_PATH = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914" / "SCE_TRACT_SERVICE_W1.csv"
TRACT_INPUT_PATH = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914" / "SERVICE_LAYER_COVERAGE_QA.csv"
BASELINE_NODE_PATH = REVIEW / "11_TwoLayer_Static_QA_20260914" / "SERVICE_NODE_BASELINE_QA.csv"
BASELINE_TRACT_PATH = REVIEW / "11_TwoLayer_Static_QA_20260914" / "TRACT_BASELINE_INTERVAL_QA.csv"
R1_CONNECTION_PATH = REVIEW / "06_R1_310_LocalClosure_20260914" / "STATION_CONNECTION_DECISIONS.csv"
TOPOLOGY_PATH = REVIEW / "06_R1_310_LocalClosure_20260914" / "R1_310_EDGES.csv"
SOURCE_LEDGER_PATH = REVIEW / "08_UtilitySpecific_SetC_20260914" / "R1_SERVICE_ROLE_CROSSWALK.csv"

CENTER_ID = "300232"
EXPECTED_SOURCE_COUNT = 21
EXPECTED_SOURCE_HASH = "c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3"
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


input_paths = [
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
hashes_before = {str(path.relative_to(ROOT)): sha256(path) for path in input_paths}

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

network_t0 = pd.to_numeric(
    baseline_network.set_index("record_id")["effective_no_damage_network_state"], errors="coerce"
).reindex(network_ids)
assert network_t0.loc[CENTER_ID] == 1.0

node_by_id = nodes.set_index("service_node_id").reindex(service_ids)
w1_by_tract = w1.set_index("tract_id")
w_matrix = w1_by_tract[service_ids].astype(float)

# ---------------- ANALYTIC EXPECTATION: derived before event propagation ----------------
center_service_ids = sorted(
    node_by_id.index[
        node_by_id["upstream_R1_station_id"].eq(CENTER_ID)
        & node_by_id["attachment_class"].isin(
            ["A_DIRECT_IDENTITY_ATTACHMENT", "B_NAMED_SYSTEM_UPSTREAM_PROXY"]
        )
    ]
)
if not center_service_ids:
    raise RuntimeError("STOP: CENTER has no A/B service attachment in the frozen ledger")

center_nodes = node_by_id.loc[center_service_ids]
center_mass = w_matrix[center_service_ids].sum(axis=1)
affected_mask = center_mass > 0

t0_expected_lower = pd.to_numeric(baseline_tracts.loc[w_matrix.index, "baseline_lower"])
t0_expected_upper = pd.to_numeric(baseline_tracts.loc[w_matrix.index, "baseline_upper"])
t0_expected_width = t0_expected_upper - t0_expected_lower
t1_analytic_lower = t0_expected_lower - center_mass
t1_analytic_upper = t0_expected_upper - center_mass
t1_analytic_width = t1_analytic_upper - t1_analytic_lower

population = tract_input.loc[w_matrix.index, "population"].astype(float)
total_population = float(population.sum())
center_population_mass = float(np.dot(population.to_numpy(), center_mass.to_numpy()))
center_population_share = center_population_mass / total_population
analytic_aggregate = {
    "t0_lower": float(np.average(t0_expected_lower, weights=population)),
    "t0_upper": float(np.average(t0_expected_upper, weights=population)),
    "t0_width": float(np.average(t0_expected_width, weights=population)),
}
analytic_aggregate.update(
    {
        "t1_lower": analytic_aggregate["t0_lower"] - center_population_share,
        "t1_upper": analytic_aggregate["t0_upper"] - center_population_share,
        "t1_width": analytic_aggregate["t0_width"],
    }
)

# ---------------- EXECUTED PROPAGATION: no source gate or topology call ----------------
def propagate_service(network_vector: pd.Series) -> pd.Series:
    """One state lookup per A/B service node; Class C remains NaN."""
    result = pd.Series(np.nan, index=service_ids, dtype=float)
    for service_id, node in node_by_id.iterrows():
        if node["attachment_class"] == "C_UNRESOLVED_ATTACHMENT":
            continue
        upstream = node["upstream_R1_station_id"]
        result.loc[service_id] = network_vector.loc[upstream]
    return result


def aggregate_tract(service_vector: pd.Series) -> pd.DataFrame:
    resolved_mask = node_by_id["attachment_class"].ne("C_UNRESOLVED_ATTACHMENT").to_numpy()
    unresolved_mask = ~resolved_mask
    resolved_mass = w_matrix.to_numpy()[:, resolved_mask].sum(axis=1)
    unresolved_mass = w_matrix.to_numpy()[:, unresolved_mask].sum(axis=1)
    resolved_states = service_vector.to_numpy()[resolved_mask]
    known_available = w_matrix.to_numpy()[:, resolved_mask] @ resolved_states
    lower = known_available
    upper = known_available + unresolved_mass
    return pd.DataFrame(
        {
            "resolved_mass": resolved_mass,
            "unresolved_mass": unresolved_mass,
            "known_available_mass": known_available,
            "lower": lower,
            "upper": upper,
            "width": upper - lower,
        },
        index=w_matrix.index,
    )


network_t1 = network_t0.copy(deep=True)
network_t1.loc[CENTER_ID] = 0.0
network_t2 = network_t1.copy(deep=True)
network_t2.loc[CENTER_ID] = 1.0

service_t0 = propagate_service(network_t0)
service_t1 = propagate_service(network_t1)
service_t2 = propagate_service(network_t2)
tract_t0 = aggregate_tract(service_t0)
tract_t1 = aggregate_tract(service_t1)
tract_t2 = aggregate_tract(service_t2)

expected_service_t1 = service_t0.copy()
expected_service_t1.loc[center_service_ids] = 0.0

service_event_rows = []
for service_id in service_ids:
    node = node_by_id.loc[service_id]
    attached_center = service_id in center_service_ids
    relations = int((w_matrix[service_id] > 0).sum())
    service_population_mass = float(np.dot(population.to_numpy(), w_matrix[service_id].to_numpy()))
    service_event_rows.append(
        {
            "service_node_id": service_id,
            "normalized_official_name": node["normalized_official_name"],
            "attachment_class": node["attachment_class"],
            "damage_role_metadata_only": node["damage_role"],
            "upstream_R1_id": node["upstream_R1_station_id"],
            "attached_to_CENTER_300232": attached_center,
            "tract_candidate_relation_count": relations,
            "population_weighted_W1_mass": service_population_mass,
            "T0_service_state": service_t0.loc[service_id],
            "T1_expected_service_state": expected_service_t1.loc[service_id],
            "T1_observed_service_state": service_t1.loc[service_id],
            "T2_service_state": service_t2.loc[service_id],
            "T1_changed_from_T0": (
                False
                if pd.isna(service_t0.loc[service_id]) and pd.isna(service_t1.loc[service_id])
                else service_t0.loc[service_id] != service_t1.loc[service_id]
            ),
            "T1_matches_analytic_expectation_1e-12": (
                pd.isna(expected_service_t1.loc[service_id]) and pd.isna(service_t1.loc[service_id])
            )
            or np.isclose(expected_service_t1.loc[service_id], service_t1.loc[service_id], atol=TOL),
            "T2_exactly_restores_T0": (
                pd.isna(service_t0.loc[service_id]) and pd.isna(service_t2.loc[service_id])
            )
            or service_t0.loc[service_id] == service_t2.loc[service_id],
            "state_lookup_count_per_event": 0 if node["attachment_class"] == "C_UNRESOLVED_ATTACHMENT" else 1,
            "duplicate_state_check": (
                "one_R1_state_lookup"
                if node["attachment_class"] != "C_UNRESOLVED_ATTACHMENT"
                else "no_lookup_state_missing"
            ),
        }
    )
service_event_qa = pd.DataFrame(service_event_rows)

tract_event_rows = []
for tract_id in w_matrix.index:
    meta = tract_input.loc[tract_id]
    delta_lower = tract_t1.loc[tract_id, "lower"] - tract_t0.loc[tract_id, "lower"]
    delta_upper = tract_t1.loc[tract_id, "upper"] - tract_t0.loc[tract_id, "upper"]
    tract_event_rows.append(
        {
            "tract_id": tract_id,
            "attachment_tier": meta["attachment_tier"],
            "population": float(meta["population"]),
            "hospital_tract": bool_value(meta["hospital_tract"]),
            "official_candidate_count": int(meta["official_candidate_count"]),
            "CENTER_mass": float(center_mass.loc[tract_id]),
            "affected_by_CENTER": bool(affected_mask.loc[tract_id]),
            "unresolved_Class_C_mass": float(tract_t0.loc[tract_id, "unresolved_mass"]),
            "T0_lower": float(tract_t0.loc[tract_id, "lower"]),
            "T0_upper": float(tract_t0.loc[tract_id, "upper"]),
            "T0_width": float(tract_t0.loc[tract_id, "width"]),
            "T1_expected_lower": float(t1_analytic_lower.loc[tract_id]),
            "T1_observed_lower": float(tract_t1.loc[tract_id, "lower"]),
            "T1_expected_upper": float(t1_analytic_upper.loc[tract_id]),
            "T1_observed_upper": float(tract_t1.loc[tract_id, "upper"]),
            "T1_width": float(tract_t1.loc[tract_id, "width"]),
            "observed_delta_lower": float(delta_lower),
            "observed_delta_upper": float(delta_upper),
            "expected_delta": float(-center_mass.loc[tract_id]),
            "delta_lower_matches_analytic_1e-12": np.isclose(delta_lower, -center_mass.loc[tract_id], atol=TOL),
            "delta_upper_matches_analytic_1e-12": np.isclose(delta_upper, -center_mass.loc[tract_id], atol=TOL),
            "width_matches_T0_exact": tract_t1.loc[tract_id, "width"] == tract_t0.loc[tract_id, "width"],
            "width_matches_T0_1e-12": np.isclose(tract_t1.loc[tract_id, "width"], tract_t0.loc[tract_id, "width"], atol=TOL),
            "T2_lower": float(tract_t2.loc[tract_id, "lower"]),
            "T2_upper": float(tract_t2.loc[tract_id, "upper"]),
            "T2_width": float(tract_t2.loc[tract_id, "width"]),
            "T2_lower_exactly_restores_T0": tract_t2.loc[tract_id, "lower"] == tract_t0.loc[tract_id, "lower"],
            "T2_upper_exactly_restores_T0": tract_t2.loc[tract_id, "upper"] == tract_t0.loc[tract_id, "upper"],
            "T2_width_exactly_restores_T0": tract_t2.loc[tract_id, "width"] == tract_t0.loc[tract_id, "width"],
        }
    )
tract_event_qa = pd.DataFrame(tract_event_rows)

observed_aggregate = {}
for state_name, table in [("t0", tract_t0), ("t1", tract_t1), ("t2", tract_t2)]:
    observed_aggregate[state_name] = {
        "lower": float(np.average(table["lower"], weights=population)),
        "upper": float(np.average(table["upper"], weights=population)),
        "width": float(np.average(table["width"], weights=population)),
    }

# Hard acceptance checks.
prior_service = pd.to_numeric(
    baseline_service.set_index("record_id")["baseline_service_state"], errors="coerce"
).reindex(service_ids)
assert np.allclose(service_t0.to_numpy(), prior_service.to_numpy(), atol=TOL, equal_nan=True)
assert np.allclose(tract_t0["lower"], t0_expected_lower, atol=TOL)
assert np.allclose(tract_t0["upper"], t0_expected_upper, atol=TOL)
assert network_t0.drop(index=CENTER_ID).equals(network_t1.drop(index=CENTER_ID))
assert network_t1.loc[CENTER_ID] == 0.0
assert network_t0.equals(network_t2)
assert service_event_qa["T1_matches_analytic_expectation_1e-12"].all()
assert service_event_qa["T2_exactly_restores_T0"].all()
assert int(service_event_qa["T1_changed_from_T0"].sum()) == len(center_service_ids)
assert service_event_qa.loc[service_event_qa["T1_changed_from_T0"], "attached_to_CENTER_300232"].all()
assert service_event_qa.loc[service_event_qa["attachment_class"].eq("C_UNRESOLVED_ATTACHMENT"), "T0_service_state"].isna().all()
assert service_event_qa.loc[service_event_qa["attachment_class"].eq("C_UNRESOLVED_ATTACHMENT"), "T1_observed_service_state"].isna().all()
assert service_event_qa.loc[service_event_qa["attachment_class"].eq("C_UNRESOLVED_ATTACHMENT"), "T2_service_state"].isna().all()
assert tract_event_qa["delta_lower_matches_analytic_1e-12"].all()
assert tract_event_qa["delta_upper_matches_analytic_1e-12"].all()
assert tract_event_qa["width_matches_T0_1e-12"].all()
assert tract_event_qa["T2_lower_exactly_restores_T0"].all()
assert tract_event_qa["T2_upper_exactly_restores_T0"].all()
assert tract_event_qa["T2_width_exactly_restores_T0"].all()
assert np.isclose(observed_aggregate["t1"]["lower"], analytic_aggregate["t1_lower"], atol=TOL)
assert np.isclose(observed_aggregate["t1"]["upper"], analytic_aggregate["t1_upper"], atol=TOL)
assert np.isclose(observed_aggregate["t0"]["width"], observed_aggregate["t1"]["width"], atol=TOL)
assert np.isclose(observed_aggregate["t0"]["width"], observed_aggregate["t2"]["width"], atol=TOL)
assert np.isclose(observed_aggregate["t0"]["lower"] - observed_aggregate["t1"]["lower"], center_population_share, atol=TOL)
assert np.isclose(observed_aggregate["t0"]["upper"] - observed_aggregate["t1"]["upper"], center_population_share, atol=TOL)
assert np.array_equal(tract_t0.to_numpy(), tract_t2.to_numpy(), equal_nan=True)

hashes_after = {str(path.relative_to(ROOT)): sha256(path) for path in input_paths}
assert hashes_before == hashes_after
assert len(source_ids) == EXPECTED_SOURCE_COUNT and source_hash == EXPECTED_SOURCE_HASH
assert len(network_ids) == 310 and len(service_ids) == 196
assert int((nodes["attachment_class"] == "C_UNRESOLVED_ATTACHMENT").sum()) == 12

for filename in ["SERVICE_NODE_EVENT_QA.csv", "TRACT_EVENT_INTERVAL_QA.csv"]:
    if (OUT / filename).exists():
        raise FileExistsError(f"Refusing to overwrite {OUT / filename}")
service_event_qa.to_csv(safe(OUT / "SERVICE_NODE_EVENT_QA.csv"), index=False, encoding="utf-8-sig", float_format="%.15g")
tract_event_qa.to_csv(safe(OUT / "TRACT_EVENT_INTERVAL_QA.csv"), index=False, encoding="utf-8-sig", float_format="%.15g")

affected = tract_event_qa[tract_event_qa["affected_by_CENTER"]]
center_mass_values = affected["CENTER_mass"].to_numpy(float)
center_node_details = []
for service_id in center_service_ids:
    row = service_event_qa.set_index("service_node_id").loc[service_id]
    center_node_details.append(
        {
            "service_node_id": service_id,
            "name": row["normalized_official_name"],
            "attachment_class": row["attachment_class"],
            "tract_candidate_relations": int(row["tract_candidate_relation_count"]),
            "population_weighted_W1_mass": float(row["population_weighted_W1_mass"]),
        }
    )

summary = {
    "decision": "PASS_EVENT_PROPAGATION_VERIFIED",
    "source_count": len(source_ids),
    "source_hash": source_hash,
    "network_id_count": len(network_ids),
    "network_id_hash": network_id_hash,
    "service_id_count": len(service_ids),
    "service_id_hash": service_id_hash,
    "input_hashes_before": hashes_before,
    "input_hashes_after_equal": hashes_before == hashes_after,
    "center_id": CENTER_ID,
    "center_service_node_count": len(center_service_ids),
    "center_A_count": int((center_nodes["attachment_class"] == "A_DIRECT_IDENTITY_ATTACHMENT").sum()),
    "center_B_count": int((center_nodes["attachment_class"] == "B_NAMED_SYSTEM_UPSTREAM_PROXY").sum()),
    "center_service_nodes": center_node_details,
    "center_candidate_relation_count": int((w_matrix[center_service_ids] > 0).sum().sum()),
    "center_population_weighted_W1_mass": center_population_mass,
    "center_population_weighted_W1_share": center_population_share,
    "affected_tract_count": int(len(affected)),
    "affected_population": float(affected["population"].sum()),
    "affected_hospital_tract_count": int(affected["hospital_tract"].sum()),
    "affected_tier_counts": affected.groupby("attachment_tier").size().to_dict(),
    "center_mass_min": float(center_mass_values.min()),
    "center_mass_median": float(np.median(center_mass_values)),
    "center_mass_max": float(center_mass_values.max()),
    "analytic_aggregate": analytic_aggregate,
    "observed_aggregate": observed_aggregate,
    "T1_changed_service_node_count": int(service_event_qa["T1_changed_from_T0"].sum()),
    "T1_unintended_service_node_changes": int((service_event_qa["T1_changed_from_T0"] & ~service_event_qa["attached_to_CENTER_300232"]).sum()),
    "class_C_missing_T0_T1_T2": bool(
        service_event_qa.loc[service_event_qa["attachment_class"].eq("C_UNRESOLVED_ATTACHMENT"), ["T0_service_state", "T1_observed_service_state", "T2_service_state"]].isna().all().all()
    ),
    "tract_delta_lower_all_match": bool(tract_event_qa["delta_lower_matches_analytic_1e-12"].all()),
    "tract_delta_upper_all_match": bool(tract_event_qa["delta_upper_matches_analytic_1e-12"].all()),
    "interval_width_all_match_1e-12": bool(tract_event_qa["width_matches_T0_1e-12"].all()),
    "interval_width_exact_match_count": int(tract_event_qa["width_matches_T0_exact"].sum()),
    "T2_exact_network_restore": bool(network_t0.equals(network_t2)),
    "T2_exact_service_restore": bool(service_event_qa["T2_exactly_restores_T0"].all()),
    "T2_exact_tract_restore": bool(
        tract_event_qa[["T2_lower_exactly_restores_T0", "T2_upper_exactly_restores_T0", "T2_width_exactly_restores_T0"]].all().all()
    ),
    "duplicate_state_check": "PASS_ONE_LOOKUP_PER_A_B_SERVICE_NODE",
}
summary_path = Path(r"C:\ABAQUS\temp\sce_service_layer_20260914\center_event_summary.json")
with open(safe(summary_path), "w", encoding="utf-8") as handle:
    json.dump(summary, handle, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
