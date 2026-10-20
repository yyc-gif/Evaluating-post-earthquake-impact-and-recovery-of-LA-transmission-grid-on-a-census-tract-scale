from __future__ import annotations

import csv
import math
from pathlib import Path

import pandas as pd


from la_grid.paths import REPO_ROOT as ROOT
STATIONS = ROOT / "Data" / "working_area_substations_with_fragility.csv"
SOURCES = ROOT / "Data" / "source_nodes_core_expanded.csv"
GNA = ROOT / "provenance/reviewer_working/Revision_Mapping_Gate" / "LOCAL_GNA_CAPACITY_SCREEN.csv"
RELIABILITY = ROOT / "results" / "diagnostics" / "SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv"
LADWP_PUBLIC = ROOT / "data/external_validation" / "normalized" / "LADWP_JULY92_PUBLIC_EVIDENCE.csv"


COLUMNS = [
    "station_id", "project_station_name", "utility_assignment", "voltage_kV",
    "is_core_source", "source_role", "matched_external_facility",
    "matched_external_facility_voltage", "provider", "dataset", "match_basis",
    "match_confidence", "planning_year", "demand_value", "demand_unit",
    "demand_definition", "facility_limit_value", "facility_limit_unit",
    "facility_limit_definition", "provider_loading_percent",
    "calculated_loading_ratio", "capacity_margin", "constraint_type",
    "transformer_capacity", "line_rating", "source_capacity", "evidence_level",
    "evidence_file", "evidence_row_id", "evidence_notes",
    "usable_for_connected_vs_constrained_check", "reason_not_usable",
    "r_i_2pc50", "R_path_full_2pc50", "R_conn_full_2pc50",
]


def text(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return str(v)


def numeric(v):
    try:
        if v is None or str(v).strip() in {"", "Redacted", "nan"}:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def fmt(v, digits=6):
    if v is None:
        return ""
    return f"{v:.{digits}f}".rstrip("0").rstrip(".")


def build():
    stations = pd.read_csv(STATIONS, dtype={"ID": str})
    assert len(stations) == 92 and stations["ID"].nunique() == 92
    sources = pd.read_csv(SOURCES, dtype={"ID": str})
    sources = sources[sources["source_type"].isin(["import_interface_proxy", "in_basin_generation_proxy"])]
    assert len(sources) == 14
    source_role = dict(zip(sources["ID"], sources["source_type"]))
    rel = pd.read_csv(RELIABILITY, dtype={"station_id": str}).set_index("station_id")
    gna = pd.read_csv(GNA, dtype={"July_ID": str, "objectid": str})
    gna_2026 = gna[gna["year_value"].astype(str) == "2026"].copy()
    ladwp = pd.read_csv(LADWP_PUBLIC, dtype={"July92_ID": str}) if LADWP_PUBLIC.exists() else pd.DataFrame()

    records = []
    for _, s in stations.sort_values("ID").iterrows():
        sid = s["ID"]
        row = {c: "" for c in COLUMNS}
        row.update({
            "station_id": sid,
            "project_station_name": s["NAME"],
            "utility_assignment": s.get("Owner", ""),
            "voltage_kV": f"{s.get('MAX_VOLT_N', '')}/{s.get('MIN_VOLT_N', '')}",
            "is_core_source": str(sid in source_role),
            "source_role": source_role.get(sid, "not_core_source"),
            "match_confidence": "unresolved",
            "evidence_level": "none",
            "usable_for_connected_vs_constrained_check": "False",
            "reason_not_usable": "No retained same-facility electrical demand/limit evidence",
        })
        if sid in rel.index:
            rr = rel.loc[sid]
            row["r_i_2pc50"] = text(rr.get("r_i"))
            row["R_path_full_2pc50"] = text(rr.get("R_path_full"))
            row["R_conn_full_2pc50"] = text(rr.get("R_conn_full"))

        gm = gna_2026[gna_2026["July_ID"] == sid]
        if not gm.empty:
            usable = gm[gm["screenable"].astype(str).str.lower() == "true"]
            chosen = (usable if not usable.empty else gm).copy()
            if "facility_loading" in chosen:
                chosen["_loading"] = pd.to_numeric(chosen["facility_loading"], errors="coerce")
                chosen = chosen.sort_values("_loading", ascending=False, na_position="last")
            g = chosen.iloc[0]
            demand = numeric(g.get("cumulative_demand"))
            limit = numeric(g.get("fac_load_limit"))
            ratio = demand / limit if demand is not None and limit not in (None, 0) else None
            row.update({
                "matched_external_facility": g.get("facility", ""),
                "matched_external_facility_voltage": str(g.get("facility", "")).split(" ", 1)[1] if " " in str(g.get("facility", "")) else "",
                "provider": "Southern California Edison",
                "dataset": "GNA Layer 5 Substation Level Planning Assumptions",
                "match_basis": "normalized station-name equality; SCE utility assignment; named voltage-level facility retained separately",
                "match_confidence": "strong",
                "planning_year": "2026",
                "demand_value": fmt(demand),
                "demand_unit": "provider table unit not stated in retained layer metadata",
                "demand_definition": "CUMULATIVE_DEMAND (provider field); annual GNA planning assumption, not observed earthquake demand",
                "facility_limit_value": fmt(limit),
                "facility_limit_unit": "provider table unit not stated in retained layer metadata",
                "facility_limit_definition": "FAC_LOAD_LIMIT (provider field); facility-level planning load limit; contingency/bank basis not stated in layer metadata",
                "provider_loading_percent": text(g.get("facility_loading")),
                "calculated_loading_ratio": fmt(ratio, 9),
                "capacity_margin": text(g.get("subst_capacity")),
                "constraint_type": "provider-defined GNA facility planning limit; detailed contingency basis not stated",
                "evidence_level": "A" if str(g.get("screenable", "")).lower() == "true" else "C",
                "evidence_file": "data/external_validation/normalized/SCE_GNA_Layer_5_Substation_Level_Planning_Assumptions.csv",
                "evidence_row_id": text(g.get("objectid")),
                "evidence_notes": f"GNA_ID={g.get('gna_id','')}; DEFICIENCY={g.get('deficiency','')}; SUBST_CAPACITY={g.get('subst_capacity','')}; absolute unit absent from layer metadata",
                "usable_for_connected_vs_constrained_check": str(str(g.get("screenable", "")).lower() == "true"),
                "reason_not_usable": "" if str(g.get("screenable", "")).lower() == "true" else "Demand/limit/loading fields are absent or redacted for the 2026 voltage-level facility",
            })

        # Conservative LADWP named-facility context. Do not overwrite Level-A SCE evidence.
        if sid == "308581":
            row.update({
                "matched_external_facility": "Receiving Station Q, existing Rack B",
                "matched_external_facility_voltage": "receiving-station transformer rack; voltage not stated with rating excerpt",
                "provider": "Los Angeles Department of Water and Power",
                "dataset": "ZEPEO MND 2025",
                "match_basis": "project Station Q (Harbor) identity matches named LADWP Receiving Station Q at Harbor Generating Station",
                "match_confidence": "strong", "planning_year": "2025 document",
                "transformer_capacity": "160 MVA existing Rack B",
                "facility_limit_definition": "existing transformer rack nameplate/project rating context; proposed Rack D is separately 160 MVA",
                "constraint_type": "documented expansion context; no simultaneous station demand/limit pair",
                "evidence_level": "B", "evidence_file": "data/external_validation/raw/references/ZEPEO_MND_2025.pdf",
                "evidence_row_id": "PDF p24 (document page 15); project description also PDF p210",
                "evidence_notes": "RS-Q is a receiving station, not a documented generator. Existing Rack B and proposed Rack D must not be summed as current capacity.",
                "usable_for_connected_vs_constrained_check": "False",
                "reason_not_usable": "Capacity/rating exists but no simultaneous RS-Q demand or loading ratio",
            })
        elif sid == "307693":
            row.update({
                "matched_external_facility": "Adelanto-Rinaldi 500 kV Line 1 at Rinaldi endpoint",
                "matched_external_facility_voltage": "500 kV",
                "provider": "Los Angeles Department of Water and Power",
                "dataset": "Adelanto-Rinaldi Transmission Line Upgrade MND 2025",
                "match_basis": "Rinaldi named endpoint, utility, geography and 500 kV voltage agree; evidence is line-level, not station-bank capacity",
                "match_confidence": "strong", "planning_year": "2025 document",
                "line_rating": "1593 A existing; proposed 1680 A continuous and 1965 A emergency",
                "facility_limit_definition": "line ampacity; proposed ratings excluded from current-network capacity",
                "constraint_type": "line rating without simultaneous flow",
                "evidence_level": "B", "evidence_file": "data/external_validation/raw/references/Adelanto_Rinaldi_MND_2025.pdf",
                "evidence_row_id": "PDF p9",
                "evidence_notes": "No MW conversion: contemporaneous flow, power factor and provider conversion basis are unavailable.",
                "usable_for_connected_vs_constrained_check": "False",
                "reason_not_usable": "Line ampacity exists but no actual/planning line flow",
            })
        elif not ladwp.empty and sid in set(ladwp["July92_ID"]):
            ev = ladwp[ladwp["July92_ID"] == sid].iloc[0]
            row.update({
                "matched_external_facility": text(ev.get("public_station", s["NAME"])),
                "provider": "Los Angeles Department of Water and Power",
                "dataset": "LADWP public facility/project evidence",
                "match_basis": "named July station and LADWP public project/event evidence",
                "match_confidence": "strong",
                "evidence_level": "C",
                "evidence_file": "data/external_validation/normalized/LADWP_JULY92_PUBLIC_EVIDENCE.csv",
                "evidence_notes": text(ev.get("public_evidence", "Named identity/context only")),
                "usable_for_connected_vs_constrained_check": "False",
                "reason_not_usable": "Named facility context lacks a simultaneous same-facility demand and limit",
            })
        records.append(row)

    cross = pd.DataFrame(records, columns=COLUMNS)
    assert len(cross) == 92 and cross["station_id"].nunique() == 92
    cross.to_csv(ROOT / "results" / "capacity" / "RETAINED_92_ELECTRICAL_EVIDENCE_CROSSWALK.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    # Every consistent Level-A voltage-facility row is a usable local check, not only the constrained row.
    bench_rows = []
    usable = gna_2026[gna_2026["screenable"].astype(str).str.lower() == "true"].copy()
    for _, g in usable.sort_values(["July_ID", "facility"]).iterrows():
        sid = g["July_ID"]
        demand, limit = numeric(g["cumulative_demand"]), numeric(g["fac_load_limit"])
        ratio = demand / limit
        provider_pct = numeric(g["facility_loading"])
        if provider_pct is not None and provider_pct > 100:
            status = "above documented limit"
        elif provider_pct is not None:
            status = "within documented limit"
        else:
            status = "indeterminate"
        rr = rel.loc[sid]
        bench_rows.append({
            "station_id": sid, "facility": g["facility"], "utility": "SCE",
            "evidence_date_year": "GNA snapshot 2026-08-27; planning year 2026",
            "topology_status_in_intact_model": "retained node in intact 92-node/318-edge graph",
            "production_source_connected_when_functional": "True",
            "documented_demand": demand,
            "documented_demand_unit": "provider table unit not stated",
            "documented_limit": limit,
            "documented_limit_unit": "provider table unit not stated",
            "provider_loading_percent": provider_pct,
            "calculated_loading_ratio": ratio,
            "capacity_margin_provider_SUBST_CAPACITY": g["subst_capacity"],
            "provider_DEFICIENCY": g["deficiency"],
            "evidence_level": "A",
            "direct_benchmark_eligible": True,
            "constraint_status": status,
            "has_simultaneous_demand_and_limit": True,
            "documented_constraint_status": status,
            "evidence_type": "Level A: same voltage-level facility/year demand, limit, loading and margin",
            "interpretation": "Planning-condition facility adequacy screen; not an earthquake overload result",
            "r_i_2pc50": rr["r_i"], "R_path_full_2pc50": rr["R_path_full"], "R_conn_full_2pc50": rr["R_conn_full"],
            "evidence_file": "data/external_validation/normalized/SCE_GNA_Layer_5_Substation_Level_Planning_Assumptions.csv",
            "evidence_row_id": g["objectid"], "GNA_ID": g["gna_id"],
        })
    rsq = rel.loc["308581"]
    bench_rows.append({
        "station_id": "308581", "facility": "Receiving Station Q, existing Rack B", "utility": "LADWP",
        "evidence_date_year": "ZEPEO MND 2025",
        "topology_status_in_intact_model": "retained Core source node in intact 92-node/318-edge graph",
        "production_source_connected_when_functional": "True (local active Core source)",
        "documented_demand": "", "documented_demand_unit": "",
        "documented_limit": "160", "documented_limit_unit": "MVA existing Rack B capacity",
        "provider_loading_percent": "", "calculated_loading_ratio": "",
        "capacity_margin_provider_SUBST_CAPACITY": "", "provider_DEFICIENCY": "",
        "evidence_level": "B",
        "direct_benchmark_eligible": False,
        "constraint_status": "constraint explicitly identified",
        "has_simultaneous_demand_and_limit": False,
        "documented_constraint_status": "constraint explicitly identified",
        "evidence_type": "Level B: provider project document identifies existing capacity and circuit-congestion/capacity limitations without simultaneous demand",
        "interpretation": "Existing RS-Q Rack B is 160 MVA and documented as limited for future Port load growth; not an earthquake loading result",
        "r_i_2pc50": rsq["r_i"], "R_path_full_2pc50": rsq["R_path_full"], "R_conn_full_2pc50": rsq["R_conn_full"],
        "evidence_file": "data/external_validation/raw/references/ZEPEO_MND_2025.pdf",
        "evidence_row_id": "PDF p24 (document page 15)", "GNA_ID": "",
    })
    bench = pd.DataFrame(bench_rows)
    assert len(bench) == 35
    bench.to_csv(ROOT / "results" / "capacity" / "CONNECTED_VS_ELECTRICAL_CONSTRAINT_BENCHMARK.csv", index=False)

    strong = cross["match_confidence"].isin(["exact", "strong"])
    has_demand = cross["demand_value"].astype(str).ne("")
    has_limit = cross["facility_limit_value"].astype(str).ne("") | cross["transformer_capacity"].astype(str).ne("") | cross["line_rating"].astype(str).ne("")
    both = cross["demand_value"].astype(str).ne("") & cross["facility_limit_value"].astype(str).ne("")
    coverage = pd.DataFrame([
        ["retained_stations_total", 92, "Fixed July inventory"],
        ["exact_or_strong_real_facility_matches", int(strong.sum()), "Identity evidence; not all have electrical loading data"],
        ["stations_with_demand", int(has_demand.sum()), "2026 SCE GNA CUMULATIVE_DEMAND"],
        ["stations_with_meaningful_capacity_or_limit", int(has_limit.sum()), "SCE facility limit or LADWP rating"],
        ["stations_with_both_demand_and_limit", int(both.sum()), "Same station; voltage-level rows retained in benchmark"],
        ["stations_usable_for_direct_connected_vs_adequacy_benchmark", int(cross["usable_for_connected_vs_constrained_check"].eq("True").sum()), "28 SCE stations represented by Level-A rows; RS-Q excluded"],
        ["level_A_voltage_facility_rows", int(bench["evidence_level"].eq("A").sum()), "Provider-consistent 2026 SCE rows"],
        ["additional_level_B_constraint_context_stations", int(bench.loc[bench["evidence_level"].eq("B"), "station_id"].nunique()), "RS-Q existing Rack B; no simultaneous demand"],
        ["connected_and_documented_above_limit_level_A_facilities", int(((bench["evidence_level"] == "A") & (bench["constraint_status"] == "above documented limit")).sum()), "OLINDA 66/12"],
        ["connected_and_provider_constraint_identified_facilities", int((bench["documented_constraint_status"] == "constraint explicitly identified").sum()), "RS-Q existing Rack B"],
        ["core_sources_with_real_injection_availability_evidence", 0, "Named identity/site evidence does not provide time-specific P availability or import bounds"],
        ["stations_without_exact_or_strong_match", int((~strong).sum()), "No conservative real-facility identity match"],
    ], columns=["metric", "count", "definition"])
    coverage.to_csv(ROOT / "results" / "capacity" / "ELECTRICAL_EVIDENCE_COVERAGE_SUMMARY.csv", index=False)
    return cross, bench, coverage


if __name__ == "__main__":
    c, b, s = build()
    direct = b[b["direct_benchmark_eligible"]]
    context = b[b["evidence_level"].eq("B")]
    print(
        f"crosswalk={len(c)} direct_level_A_rows={len(direct)} "
        f"direct_benchmark_stations={direct.station_id.nunique()} "
        f"additional_level_B_context_stations={context.station_id.nunique()}"
    )
    print(s.to_string(index=False))
