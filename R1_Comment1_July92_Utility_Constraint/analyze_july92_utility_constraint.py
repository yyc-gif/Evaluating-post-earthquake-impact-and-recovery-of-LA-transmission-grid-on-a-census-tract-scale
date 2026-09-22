"""Offline Reviewer 1 #1 analysis on the frozen July 92-station network.

This script does not modify the production mapping, topology, damage model,
scheduler, source gate, or recovery results.  It reconstructs the submitted
July mapping, applies one utility-eligibility constraint, benchmarks both maps
against retained SCE public candidate evidence, and inventories which outcome
sensitivity metrics can be recomputed from retained July artifacts.
"""

from __future__ import annotations

import hashlib
import io
import json
import pathlib
import re
import subprocess
from typing import Iterable

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from pyproj import Transformer


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(__file__).resolve().parent
HISTORIC_COMMIT = "87110da"
HISTORIC_PREFIX = "Review_and_Revision/IJDRR-D-26-02276/"

IDW_POWER = 2.0
MIN_DISTANCE_KM = 1e-3
MIN_WEIGHT = 0.03


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_common_dir() -> pathlib.Path:
    raw = subprocess.check_output(
        ["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True
    ).strip()
    path = pathlib.Path(raw)
    return path if path.is_absolute() else (ROOT / path).resolve()


def lfs_object_bytes(oid: str) -> bytes:
    path = git_common_dir() / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
    return pathlib.Path("\\\\?\\" + str(path)).read_bytes()


def historic_bytes(relative_path: str) -> bytes:
    data = subprocess.check_output(
        ["git", "show", f"{HISTORIC_COMMIT}:{HISTORIC_PREFIX}{relative_path}"],
        cwd=ROOT,
    )
    if data.startswith(b"version https://git-lfs"):
        match = re.search(rb"oid sha256:([a-f0-9]+)", data)
        if not match:
            raise RuntimeError(f"Malformed LFS pointer: {relative_path}")
        data = lfs_object_bytes(match.group(1).decode())
    return data


def historic_csv(relative_path: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(historic_bytes(relative_path)), dtype=str)


def parse_id_set(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    return {item.strip() for item in str(value).split(";") if item.strip()}


def build_graph(station_ids: list[str], edges: pd.DataFrame) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(station_ids)
    for row in edges.itertuples(index=False):
        u, v, length = str(row.u), str(row.v), float(row.length_km)
        if u not in graph or v not in graph:
            raise ValueError(f"Edge references a station outside the frozen 92: {u}, {v}")
        if graph.has_edge(u, v):
            graph[u][v]["weight"] = min(graph[u][v]["weight"], length)
        else:
            graph.add_edge(u, v, weight=length)
    if not nx.is_connected(graph):
        raise ValueError("Frozen July 92 graph is not connected")
    return graph


def all_pairs_distance(graph: nx.Graph, station_ids: list[str]) -> np.ndarray:
    index = {sid: i for i, sid in enumerate(station_ids)}
    distance = np.full((len(station_ids), len(station_ids)), np.inf, dtype=float)
    for source, lengths in nx.all_pairs_dijkstra_path_length(graph, weight="weight"):
        for target, value in lengths.items():
            distance[index[source], index[target]] = float(value)
    return distance


def threshold_and_renormalize(weights: np.ndarray) -> np.ndarray:
    original = weights.copy()
    weights[weights < MIN_WEIGHT] = 0.0
    if weights.sum() <= 0:
        weights[np.argmax(original)] = 1.0
    return weights / weights.sum()


def build_july_mapping(
    *,
    centroid_xy: np.ndarray,
    station_xy: np.ndarray,
    network_distance: np.ndarray,
    station_owners: np.ndarray,
    utility_domains: np.ndarray,
    constrained: bool,
) -> np.ndarray:
    """Apply the July formula, optionally restricting eligible station IDs."""
    n_tracts, n_stations = len(centroid_xy), len(station_xy)
    result = np.zeros((n_tracts, n_stations), dtype=float)
    euclidean_km = np.linalg.norm(
        centroid_xy[:, None, :] - station_xy[None, :, :], axis=2
    ) / 1000.0

    for tract_index in range(n_tracts):
        domain = str(utility_domains[tract_index])
        if constrained and domain in {"SCE", "LADWP"}:
            eligible = station_owners == domain
        else:
            eligible = np.ones(n_stations, dtype=bool)
        if not eligible.any():
            raise ValueError(f"No eligible station for tract index {tract_index} ({domain})")

        eligible_indices = np.flatnonzero(eligible)
        access = eligible_indices[np.argmin(euclidean_km[tract_index, eligible])]
        access_distance = euclidean_km[tract_index, access]
        total_distance = access_distance + network_distance[access]
        valid = eligible & np.isfinite(total_distance)
        if not valid.any():
            raise ValueError(f"No reachable eligible station for tract index {tract_index}")

        raw = np.zeros(n_stations, dtype=float)
        distance = np.maximum(total_distance[valid], MIN_DISTANCE_KM)
        raw[valid] = 1.0 / np.power(distance, IDW_POWER)
        raw /= raw.sum()
        result[tract_index] = threshold_and_renormalize(raw)
    return result


def mapping_long(
    weights: np.ndarray,
    tract_ids: list[str],
    station_ids: list[str],
    utility_domains: np.ndarray,
    station_owners: np.ndarray,
) -> pd.DataFrame:
    tract_index, station_index = np.nonzero(weights > 0)
    return pd.DataFrame(
        {
            "tract_id": np.asarray(tract_ids)[tract_index],
            "utility_domain": utility_domains[tract_index],
            "substation_id": np.asarray(station_ids)[station_index],
            "station_owner": station_owners[station_index],
            "weight": weights[tract_index, station_index],
        }
    )


def weighted_summary(values: np.ndarray, weights: np.ndarray) -> float:
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    return float(np.average(values[valid], weights=weights[valid])) if valid.any() else np.nan


def candidate_metrics(
    *,
    mapping_name: str,
    weights: np.ndarray,
    tract_indices: Iterable[int],
    official_candidates: list[set[str]],
    station_ids: list[str],
    station_xy_lookup: dict[str, np.ndarray],
    tract_ids: list[str],
) -> pd.DataFrame:
    station_array = np.asarray(station_ids)
    rows: list[dict[str, object]] = []
    for tract_index in tract_indices:
        official = official_candidates[tract_index]
        if not official:
            continue
        positive_index = np.flatnonzero(weights[tract_index] > 0)
        ranked_index = positive_index[
            np.argsort(-weights[tract_index, positive_index], kind="stable")
        ]
        candidates = set(station_array[positive_index])
        overlap = candidates & official
        top1 = str(station_array[ranked_index[0]])
        top3 = set(station_array[ranked_index[:3]])
        hhi = float(np.square(weights[tract_index, positive_index]).sum())
        top1_xy = station_xy_lookup[top1]
        nearest_distance = min(
            float(np.linalg.norm(top1_xy - station_xy_lookup[station]) / 1000.0)
            for station in official
        )
        rows.append(
            {
                "mapping": mapping_name,
                "tract_id": tract_ids[tract_index],
                "official_candidates_in_July92": ";".join(sorted(official)),
                "mapped_candidates": ";".join(sorted(candidates)),
                "any_candidate_match": bool(overlap),
                "top1_station": top1,
                "top1_agreement": top1 in official,
                "top3_agreement": bool(top3 & official),
                "precision_like_overlap": len(overlap) / len(candidates),
                "recall_like_overlap": len(overlap) / len(official),
                "candidate_count": len(candidates),
                "max_weight": float(weights[tract_index, ranked_index[0]]),
                "HHI": hhi,
                "effective_candidate_count": 1.0 / hhi,
                "top1_to_nearest_official_candidate_km": nearest_distance,
            }
        )
    return pd.DataFrame(rows)


def summarize_benchmark(
    benchmark: pd.DataFrame,
    *,
    strict_sce_tracts: int,
    crosswalked_evidence_tracts: int,
    representable_evidence_tracts: int,
) -> pd.DataFrame:
    rows = []
    for mapping_name, group in benchmark.groupby("mapping", sort=False):
        rows.append(
            {
                "mapping": mapping_name,
                "strict_SCE_tracts": strict_sce_tracts,
                "tracts_with_any_crosswalked_official_candidate": crosswalked_evidence_tracts,
                "benchmark_tracts_with_official_candidate_in_July92": representable_evidence_tracts,
                "any_candidate_match_rate": group.any_candidate_match.mean(),
                "top1_agreement_rate": group.top1_agreement.mean(),
                "top3_agreement_rate": group.top3_agreement.mean(),
                "mean_precision_like_overlap": group.precision_like_overlap.mean(),
                "mean_recall_like_overlap": group.recall_like_overlap.mean(),
                "average_candidate_count": group.candidate_count.mean(),
                "average_max_weight": group.max_weight.mean(),
                "average_HHI": group.HHI.mean(),
                "average_effective_candidate_count": group.effective_candidate_count.mean(),
                "mean_top1_to_nearest_official_candidate_km": (
                    group.top1_to_nearest_official_candidate_km.mean()
                ),
                "median_top1_to_nearest_official_candidate_km": (
                    group.top1_to_nearest_official_candidate_km.median()
                ),
            }
        )
    return pd.DataFrame(rows)


def mapping_structure(
    *,
    baseline: np.ndarray,
    constrained: np.ndarray,
    tract_ids: list[str],
    station_ids: list[str],
    utility_domains: np.ndarray,
    population: np.ndarray,
    quartiles: np.ndarray,
    hospital: np.ndarray,
) -> pd.DataFrame:
    station_array = np.asarray(station_ids)
    baseline_top1 = station_array[np.argmax(baseline, axis=1)]
    constrained_top1 = station_array[np.argmax(constrained, axis=1)]
    baseline_hhi = np.square(baseline).sum(axis=1)
    constrained_hhi = np.square(constrained).sum(axis=1)
    l1 = np.abs(constrained - baseline).sum(axis=1)
    rows = pd.DataFrame(
        {
            "tract_id": tract_ids,
            "utility_domain": utility_domains,
            "population": population,
            "SOVI_quartile": quartiles,
            "hospital_tract": hospital,
            "baseline_candidate_count": (baseline > 0).sum(axis=1),
            "constrained_candidate_count": (constrained > 0).sum(axis=1),
            "baseline_top1": baseline_top1,
            "constrained_top1": constrained_top1,
            "top1_changed": baseline_top1 != constrained_top1,
            "L1_weight_shift": l1,
            "total_variation_weight_shift": 0.5 * l1,
            "baseline_max_weight": baseline.max(axis=1),
            "constrained_max_weight": constrained.max(axis=1),
            "baseline_HHI": baseline_hhi,
            "constrained_HHI": constrained_hhi,
            "baseline_effective_candidate_count": 1.0 / baseline_hhi,
            "constrained_effective_candidate_count": 1.0 / constrained_hhi,
        }
    )
    return rows


def summarize_structure(structure: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_specs = [("ALL", structure)] + list(structure.groupby("utility_domain", sort=True))
    for label, group in group_specs:
        pop = group.population.to_numpy(dtype=float)
        rows.append(
            {
                "tract_group": label,
                "tract_count": len(group),
                "population": float(pop.sum()),
                "changed_weight_rows": int((group.L1_weight_shift > 1e-12).sum()),
                "top1_changed_count": int(group.top1_changed.sum()),
                "top1_changed_fraction": float(group.top1_changed.mean()),
                "mean_total_variation_shift": float(group.total_variation_weight_shift.mean()),
                "population_weighted_total_variation_shift": weighted_summary(
                    group.total_variation_weight_shift.to_numpy(dtype=float), pop
                ),
                "median_total_variation_shift": float(group.total_variation_weight_shift.median()),
                "p90_total_variation_shift": float(group.total_variation_weight_shift.quantile(0.9)),
                "mean_candidate_count_change": float(
                    (group.constrained_candidate_count - group.baseline_candidate_count).mean()
                ),
                "mean_max_weight_change": float(
                    (group.constrained_max_weight - group.baseline_max_weight).mean()
                ),
                "mean_HHI_change": float(
                    (group.constrained_HHI - group.baseline_HHI).mean()
                ),
            }
        )
    return pd.DataFrame(rows)


def outcome_availability() -> pd.DataFrame:
    common_reason = (
        "Retained July strategy outputs store aggregate tract curves/KPIs, not the "
        "time-indexed 92-station state trajectory required to apply a new tract mapping."
    )
    required = (
        "Use the same saved physical realization, schedule, source-gated 92-station "
        "state trajectory, and strategy sequence; recompute only the tract mapping layer "
        "during the final authorized science rerun."
    )
    metrics = [
        "population_T80",
        "population_cumulative_burden",
        "hospital_burden",
        "Q1_absolute_burden",
        "Q2_absolute_burden",
        "Q3_absolute_burden",
        "Q4_absolute_burden",
        "Q4_minus_Q1_signed_gap",
        "absolute_gap",
        "population_weighted_Gini",
        "tract_burden_shift",
        "improved_near_zero_worsened_unresolved_population",
    ]
    return pd.DataFrame(
        {
            "requested_metric": metrics,
            "offline_status": "NOT_COMPUTABLE_FROM_RETAINED_JULY_STRATEGY_OUTPUTS",
            "reason": common_reason,
            "minimum_required_future_calculation": required,
        }
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    station_path = ROOT / "Data" / "working_area_substations_with_fragility.csv"
    node_path = ROOT / "Data" / "substation_graph_CEC_nodes_expanded.csv"
    edge_path = ROOT / "Data" / "substation_graph_CEC_edges_expanded.csv"
    tract_path = ROOT / "Data" / "Tracts_Within_Expanded_Area.csv"
    submitted_mapping_path = ROOT / "Data" / "tract_to_substation_mapping_CEC_expanded.csv"

    stations = pd.read_csv(station_path, dtype=str)
    nodes = pd.read_csv(node_path, dtype=str)
    edges = pd.read_csv(edge_path, dtype=str)
    tracts = pd.read_csv(tract_path, dtype=str)
    submitted = pd.read_csv(submitted_mapping_path, dtype=str)
    utility = historic_csv("08_UtilitySpecific_SetC_20260914/TRACT_UTILITY_DOMAIN.csv")
    tier = historic_csv("09_MappingArchitecture_20260914/EVIDENCE_TIER_COVERAGE.csv")

    station_ids = nodes.id.astype(str).tolist()
    if len(station_ids) != 92 or len(set(station_ids)) != 92 or len(edges) != 318:
        raise ValueError("Frozen July topology identity is not 92 stations / 318 edges")
    station_by_id = stations.assign(ID=stations.ID.astype(str)).set_index("ID").reindex(station_ids)
    if station_by_id.Owner.isna().sum() != 1:
        raise ValueError("Unexpected July station-owner inventory")
    station_owners = station_by_id.Owner.fillna("UNSPECIFIED").to_numpy(dtype=str)

    tract_ids = tracts.GEOID.astype(str).str.zfill(11).tolist()
    if len(tract_ids) != 2315 or len(set(tract_ids)) != 2315:
        raise ValueError("Frozen July tract identity is not 2,315 unique tracts")
    utility = utility.assign(tract_id=utility.tract_id.astype(str).str.zfill(11)).set_index("tract_id").reindex(tract_ids)
    tier = tier.assign(tract_id=tier.tract_id.astype(str).str.zfill(11)).set_index("tract_id").reindex(tract_ids)
    if utility.UTILITY_DOMAIN.isna().any() or tier.population.isna().any():
        raise ValueError("Retained utility/evidence records do not cover all July tracts")
    utility_domains = utility.UTILITY_DOMAIN.to_numpy(dtype=str)

    tract_geometry = gpd.GeoSeries.from_wkt(tracts.wkt_geom, crs="EPSG:4326").to_crs(3310)
    centroids = tract_geometry.centroid
    centroid_xy = np.column_stack((centroids.x.to_numpy(), centroids.y.to_numpy()))
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3310", always_xy=True)
    sx, sy = transformer.transform(
        pd.to_numeric(nodes.lon).to_numpy(), pd.to_numeric(nodes.lat).to_numpy()
    )
    station_xy = np.column_stack((sx, sy))
    station_xy_lookup = {sid: station_xy[index] for index, sid in enumerate(station_ids)}

    graph = build_graph(station_ids, edges)
    network_distance = all_pairs_distance(graph, station_ids)
    baseline = build_july_mapping(
        centroid_xy=centroid_xy,
        station_xy=station_xy,
        network_distance=network_distance,
        station_owners=station_owners,
        utility_domains=utility_domains,
        constrained=False,
    )
    constrained = build_july_mapping(
        centroid_xy=centroid_xy,
        station_xy=station_xy,
        network_distance=network_distance,
        station_owners=station_owners,
        utility_domains=utility_domains,
        constrained=True,
    )

    submitted.weight = pd.to_numeric(submitted.weight)
    submitted.tract_id = submitted.tract_id.astype(str).str.zfill(11)
    submitted.substation_id = submitted.substation_id.astype(str)
    submitted_matrix = submitted.pivot_table(
        index="tract_id", columns="substation_id", values="weight", aggfunc="sum", fill_value=0
    ).reindex(index=tract_ids, columns=station_ids, fill_value=0).to_numpy(dtype=float)
    maximum_error = float(np.max(np.abs(submitted_matrix - baseline)))
    differing_cells = int((np.abs(submitted_matrix - baseline) > 1e-12).sum())
    if maximum_error > 1e-12:
        raise ValueError(f"July baseline reconstruction mismatch: {maximum_error}")
    if not np.allclose(baseline.sum(axis=1), 1) or not np.allclose(constrained.sum(axis=1), 1):
        raise ValueError("A mapping row does not sum to one")
    sce_rows = utility_domains == "SCE"
    ladwp_rows = utility_domains == "LADWP"
    if np.any(constrained[sce_rows][:, station_owners != "SCE"] > 0):
        raise ValueError("A strict SCE tract retained a non-SCE-compatible station")
    if np.any(constrained[ladwp_rows][:, station_owners != "LADWP"] > 0):
        raise ValueError("A strict LADWP tract retained a non-LADWP-compatible station")
    mixed = ~np.isin(utility_domains, ["SCE", "LADWP"])
    if not np.array_equal(baseline[mixed], constrained[mixed]):
        raise ValueError("Mixed/ambiguous tracts changed under utility constraint")

    constrained_long = mapping_long(
        constrained, tract_ids, station_ids, utility_domains, station_owners
    )
    constrained_long.to_csv(OUT / "JULY_UTILITY_CONSTRAINED_92.csv", index=False)

    official_all = [parse_id_set(value) for value in utility.official_candidate_R1_ids]
    july_set = set(station_ids)
    official_july92 = [candidates & july_set for candidates in official_all]
    strict_sce_index = np.flatnonzero(utility_domains == "SCE")
    benchmark_index = [index for index in strict_sce_index if official_july92[index]]
    benchmark = pd.concat(
        [
            candidate_metrics(
                mapping_name="JULY_BASELINE_92",
                weights=baseline,
                tract_indices=benchmark_index,
                official_candidates=official_july92,
                station_ids=station_ids,
                station_xy_lookup=station_xy_lookup,
                tract_ids=tract_ids,
            ),
            candidate_metrics(
                mapping_name="JULY_UTILITY_CONSTRAINED_92",
                weights=constrained,
                tract_indices=benchmark_index,
                official_candidates=official_july92,
                station_ids=station_ids,
                station_xy_lookup=station_xy_lookup,
                tract_ids=tract_ids,
            ),
        ],
        ignore_index=True,
    )
    benchmark.to_csv(OUT / "SCE_CANDIDATE_BENCHMARK_TRACTS.csv", index=False)
    benchmark_summary = summarize_benchmark(
        benchmark,
        strict_sce_tracts=len(strict_sce_index),
        crosswalked_evidence_tracts=sum(bool(official_all[index]) for index in strict_sce_index),
        representable_evidence_tracts=len(benchmark_index),
    )
    benchmark_summary.to_csv(OUT / "SCE_CANDIDATE_BENCHMARK_SUMMARY.csv", index=False)

    population = pd.to_numeric(tier.population).to_numpy(dtype=float)
    quartiles = tier.SOVI_fullregion_quartile.fillna("UNAVAILABLE").to_numpy(dtype=str)
    hospital = tier.hospital_tract.eq("True").to_numpy(dtype=bool)
    structure = mapping_structure(
        baseline=baseline,
        constrained=constrained,
        tract_ids=tract_ids,
        station_ids=station_ids,
        utility_domains=utility_domains,
        population=population,
        quartiles=quartiles,
        hospital=hospital,
    )
    structure.to_csv(OUT / "MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv", index=False)
    summarize_structure(structure).to_csv(OUT / "MAPPING_STRUCTURE_SENSITIVITY_SUMMARY.csv", index=False)
    outcome_availability().to_csv(OUT / "OUTCOME_SENSITIVITY_AVAILABILITY.csv", index=False)

    manifest = {
        "analysis_scope": "Reviewer 1 Comment #1, frozen July 92-station mapping only",
        "mapping_names": ["JULY_BASELINE_92", "JULY_UTILITY_CONSTRAINED_92"],
        "station_count": len(station_ids),
        "edge_count": len(edges),
        "tract_count": len(tract_ids),
        "idw_power": IDW_POWER,
        "minimum_weight_cutoff": MIN_WEIGHT,
        "station_owner_counts": pd.Series(station_owners).value_counts().to_dict(),
        "utility_domain_counts": pd.Series(utility_domains).value_counts().to_dict(),
        "strict_sce_crosswalked_evidence_tracts": sum(
            bool(official_all[index]) for index in strict_sce_index
        ),
        "strict_sce_benchmark_tracts_representable_in_July92": len(benchmark_index),
        "unique_official_candidate_ids_representable_in_July92": len(
            set().union(*(official_july92[index] for index in benchmark_index))
        ),
        "submitted_baseline_reconstruction_max_abs_error": maximum_error,
        "submitted_baseline_reconstruction_cells_over_1e_12": differing_cells,
        "input_sha256": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in (station_path, node_path, edge_path, tract_path, submitted_mapping_path)
        },
        "retained_external_evidence_sha256": {
            f"{HISTORIC_COMMIT}:{HISTORIC_PREFIX}08_UtilitySpecific_SetC_20260914/TRACT_UTILITY_DOMAIN.csv": sha256_bytes(
                historic_bytes("08_UtilitySpecific_SetC_20260914/TRACT_UTILITY_DOMAIN.csv")
            ),
            f"{HISTORIC_COMMIT}:{HISTORIC_PREFIX}09_MappingArchitecture_20260914/EVIDENCE_TIER_COVERAGE.csv": sha256_bytes(
                historic_bytes("09_MappingArchitecture_20260914/EVIDENCE_TIER_COVERAGE.csv")
            ),
        },
        "output_sha256": {
            name: sha256_file(OUT / name)
            for name in (
                "JULY_UTILITY_CONSTRAINED_92.csv",
                "SCE_CANDIDATE_BENCHMARK_TRACTS.csv",
                "SCE_CANDIDATE_BENCHMARK_SUMMARY.csv",
                "MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv",
                "MAPPING_STRUCTURE_SENSITIVITY_SUMMARY.csv",
                "OUTCOME_SENSITIVITY_AVAILABILITY.csv",
            )
        },
        "production_default_mapping_modified": False,
        "scientific_pipeline_executions": 0,
    }
    (OUT / "ANALYSIS_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
