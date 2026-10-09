"""Independent public-data pilot; never calls the LA simulation or clustering."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import subprocess
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd


FEATURES = ["T80", "Init_Supply", "Grid_Degree", "Grid_Impact",
            "Grid_Betweenness", "Redundancy_HHI", "Pre_1970_Ratio",
            "Pop_Density", "NRI_RISK_SCORE", "NRI_BUILDVALUE", "SOVI_SCORE"]
STAGE7 = Path("Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized")
ACS_ROOT = "https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData/"
EPA = "https://services1.arcgis.com/IqEe3YDHhqT8n4KU/ArcGIS/rest/services/EPA_SmartLocationDatabase_V3_Jan_2021_Final/FeatureServer/0"
SCAG19 = "https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0"
SCAG24 = "https://maps.scag.ca.gov/scaggis/rest/services/LDX/Existinglanduse_poly_LA/MapServer"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def fetch(url, target):
    target = Path(target)
    if target.exists():
        return {"url": url, "file": target.name, "bytes": target.stat().st_size,
                "sha256": digest(target), "cached": True, "accessed_date": "2026-10-09"}
    req = urllib.request.Request(url, headers={"User-Agent": "LA-built-environment-research/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        content = response.read()
        info = {"url": url, "resolved_url": response.url,
                "content_type": response.headers.get("Content-Type"),
                "last_modified": response.headers.get("Last-Modified"),
                "bytes": len(content)}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    info.update(file=target.name, sha256=digest(target), accessed_date="2026-10-09")
    return info


def get_json(url, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as response:
        result = json.load(response)
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(result["error"])
    return result


def snapshot(repo, out):
    folders = [STAGE7, Path("results/figure_review"), Path("results/figures")]
    paths = set()
    for folder in folders:
        paths.update(p for p in (repo / folder).rglob("*") if p.is_file())
    for name in ["Data/ACSDT5Y2022.B25034-Data.csv", "Data/LA_Tracts_With_Population.shp",
                 "Data/LA_Tracts_With_Population.dbf", "Data/LA_Tracts_With_Population.shx",
                 "Data/NRI_Table_CensusTracts_California.csv",
                 "src/la_grid/core/C257H_Project_Main.py"]:
        if (repo / name).exists():
            paths.add(repo / name)
    result = {"base_head": git(repo, "rev-parse", "HEAD").decode().strip(),
              "branch": git(repo, "branch", "--show-current").decode().strip(),
              "staged_diff_raw_sha256": hashlib.sha256(git(repo, "diff", "--cached", "--raw", "-z")).hexdigest(),
              "protected_files": {p.relative_to(repo).as_posix(): digest(p) for p in sorted(paths)}}
    (out / "PRESERVATION_BASELINE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"base_head": result["base_head"], "protected_files": len(paths)}))


def fetch_sources(out):
    raw = out / "pilot/source_snapshots"
    urls = {
        "acsdt5y2022-b25024.dat": ACS_ROOT + "acsdt5y2022-b25024.dat",
        "B25024_metadata.json": "https://api.census.gov/data/2022/acs/acs5/groups/B25024.json",
        "B25034_metadata.json": "https://api.census.gov/data/2022/acs/acs5/groups/B25034.json",
        "EPA_SLD_v3_layer.json": EPA + "?f=pjson",
        "SCAG_2019_1_layer.json": SCAG19 + "?f=pjson",
        "SCAG_current_LA_service.json": SCAG24 + "?f=pjson",
        "nlcd_s3_c1_listing.xml": "https://usgs-landcover.s3.us-west-2.amazonaws.com/?list-type=2&prefix=annual-nlcd/c1/&delimiter=/",
        "census_relationship_page.html": "https://www.census.gov/geographies/reference-files/2020/geo/relationship-files.html",
        "FEMA_March2023_documentation.pdf": "https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf",
        "Annual_NLCD_WMS_capabilities.xml": "https://dmsdata.cr.usgs.gov/geoserver/mrlc_Fractional-Impervious-Surface-Native_conus_year_data/wms?service=WMS&request=GetCapabilities",
    }
    records = []
    def one(item):
        name, url = item
        try:
            result = fetch(url, raw / name)
            print(f"Retrieved {name}: {result['bytes']} bytes", flush=True)
            return result
        except Exception as exc:
            print(f"Unavailable {name}: {exc}", flush=True)
            return {"url": url, "file": name, "error": str(exc), "accessed_date": "2026-10-09"}
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(one, urls.items()))
    (out / "pilot/SOURCE_DOWNLOAD_MANIFEST.json").write_text(json.dumps(records, indent=2), encoding="utf-8")


def acs_audit(repo, out):
    full = pd.read_csv(repo / STAGE7 / "stage7_full_domain_tract_status.csv", dtype={"tract_id": str})
    clusters = pd.read_csv(repo / STAGE7 / "clusters_labels_final.csv", dtype={"tract_id": str})
    for frame in (full, clusters):
        frame["tract_id"] = frame.tract_id.str.zfill(11)
        assert not frame.tract_id.duplicated().any()
    assert (len(full), len(clusters)) == (2315, 2291)
    dat = out / "pilot/source_snapshots/acsdt5y2022-b25024.dat"
    selected = []
    header = None
    with dat.open(encoding="utf-8-sig") as stream:
        for line in stream:
            if header is None:
                header = line
            elif line.startswith("1400000US06037"):
                selected.append(line)
    acs = pd.read_csv(io.StringIO(header + "".join(selected)), sep="|", dtype=str)
    idcol = next(c for c in acs if c.upper() == "GEO_ID")
    acs["tract_id"] = acs[idcol].str.split("US").str[-1].str.zfill(11)
    assert not acs.tract_id.duplicated().any()
    acs.to_csv(out / "pilot/ACS2022_B25024_LA_tracts.csv", index=False)
    acs = acs.rename(columns={c: f"B25024_{c[-3:]}{c.split('_')[1][0]}"
                             for c in acs if c.startswith("B25024_")})
    for c in acs:
        if c.startswith("B25024_"):
            acs[c] = pd.to_numeric(acs[c], errors="coerce")
            acs[c] = acs[c].where(acs[c] >= 0)
    bins = [f"B25024_{i:03d}E" for i in range(6, 10)]
    moes = [c[:-1] + "M" for c in bins]
    acs["housing_5plus_units"] = acs[bins].sum(axis=1, min_count=4)
    acs["housing_5plus_units_moe90"] = np.sqrt((acs[moes] ** 2).sum(axis=1, min_count=4))
    denominator = acs.B25024_001E.where(acs.B25024_001E > 0)
    acs["housing_5plus_share"] = acs.housing_5plus_units / denominator
    radicand = acs.housing_5plus_units_moe90 ** 2 - acs.housing_5plus_share ** 2 * acs.B25024_001M ** 2
    fallback = radicand < 0
    radicand = radicand.where(~fallback, acs.housing_5plus_units_moe90 ** 2 + acs.housing_5plus_share ** 2 * acs.B25024_001M ** 2)
    acs["housing_5plus_share_moe90"] = np.sqrt(radicand) / denominator
    acs["moe_ratio_fallback"] = fallback
    acs["housing_5plus_share_moe90_gt_1"] = acs.housing_5plus_share_moe90.gt(1)
    acs["housing_total_ci90_includes_zero"] = acs.B25024_001E.le(acs.B25024_001M)
    numeric = [c for c in acs if c.startswith("B25024_") or c.startswith("housing_") or c == "moe_ratio_fallback"]
    coverage = full.merge(acs[["tract_id"] + numeric], on="tract_id", how="left", validate="one_to_one", indicator=True)
    coverage["b25024_record_present"] = coverage["_merge"].eq("both")
    coverage["b25024_status"] = np.select(
        [~coverage.b25024_record_present, coverage.B25024_001E.isna(), coverage.B25024_001E.eq(0), coverage.housing_5plus_share.isna()],
        ["missing_source_record", "missing_total_estimate", "zero_housing_denominator", "missing_numerator"], default="valid")
    coverage["b25034_total_matches"] = coverage.B25024_001E.eq(coverage.Housing_Units_Total)
    coverage["residential_typology_member"] = coverage.tract_id.isin(set(clusters.tract_id))
    coverage["nlcd_status"] = "not_extracted"
    coverage["sld_tract_indicator_status"] = "not_crosswalked"
    coverage["scag_tract_indicator_status"] = "not_spatially_aggregated"
    coverage = coverage.drop(columns="_merge")
    coverage.to_csv(out / "BUILT_ENVIRONMENT_TRACT_COVERAGE.csv", index=False)
    eligible = coverage.loc[coverage.residential_typology_member].copy()
    assert eligible.b25024_status.eq("valid").all()
    assert coverage.b25034_total_matches.all()
    all_bins = [f"B25024_{i:03d}E" for i in range(2, 12)]
    assert np.array_equal(coverage[all_bins].sum(axis=1, min_count=10), coverage.B25024_001E)
    assert eligible.housing_5plus_share.between(0, 1).all()
    matrix = clusters[FEATURES].copy()
    raw_matrix = matrix.copy()
    for c in ("Pop_Density", "NRI_BUILDVALUE"):
        matrix[c] = np.log1p(matrix[c])
    matrix["housing_5plus_share"] = eligible.set_index("tract_id").housing_5plus_share.reindex(clusters.tract_id).values
    raw_matrix["housing_5plus_share"] = matrix.housing_5plus_share
    rows = []
    for label, values in [("clustering_transform", matrix), ("raw", raw_matrix)]:
        for method in ["pearson", "spearman"]:
            corr = values.corr(method=method)
            for i, first in enumerate(corr.columns):
                for second in corr.columns[i+1:]:
                    rows.append(dict(scale=label, method=method, first=first, second=second,
                                     correlation=corr.loc[first, second], n=len(values[[first, second]].dropna())))
    pd.DataFrame(rows).to_csv(out / "pilot/FEATURE_PAIRWISE_CORRELATIONS.csv", index=False)
    profiles = eligible
    assert np.array_equal(profiles.set_index("tract_id").cluster.reindex(clusters.tract_id), clusters.cluster)
    profiles.groupby("cluster").housing_5plus_share.agg(["count", "mean", "median", "min", "max"]).to_csv(out / "pilot/B25024_EXISTING_CLUSTER_DESCRIPTIONS.csv")
    summary = {"study_tracts": len(full), "residential_tracts": len(clusters), "LA_source_tracts": len(acs),
               "source_records_in_study": int(coverage.b25024_record_present.sum()),
               "valid_study": int(coverage.b25024_status.eq("valid").sum()),
               "valid_residential": int(eligible.b25024_status.eq("valid").sum()),
               "status_counts": coverage.b25024_status.value_counts().to_dict(),
               "denominator_mismatches_with_existing_B25034": int((~coverage.b25034_total_matches).sum()),
               "share_quantiles": eligible.housing_5plus_share.quantile([0,.1,.25,.5,.75,.9,1]).to_dict(),
               "moe90_share_quantiles": eligible.housing_5plus_share_moe90.quantile([0,.5,.9,.95,1]).to_dict(),
               "moe90_gt_0_10": int(eligible.housing_5plus_share_moe90.gt(.10).sum()),
               "moe90_gt_0_20": int(eligible.housing_5plus_share_moe90.gt(.20).sum()),
               "total_units_lt_100": int(eligible.B25024_001E.lt(100).sum()),
               "total_ci90_includes_zero": int(eligible.housing_total_ci90_includes_zero.sum()),
               "share_moe90_gt_1": int(eligible.housing_5plus_share_moe90_gt_1.sum()),
               "moe_ratio_fallback_count": int(eligible.moe_ratio_fallback.sum()),
               "undefined_tract_ids": coverage.loc[~coverage.b25024_status.eq("valid"), "tract_id"].tolist()}
    (out / "pilot/ACS_PILOT_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def verify(repo, out):
    baseline = json.loads((out / "PRESERVATION_BASELINE.json").read_text())
    changed = [name for name, expected in baseline["protected_files"].items()
               if not (repo / name).exists() or digest(repo / name) != expected]
    staged = hashlib.sha256(git(repo, "diff", "--cached", "--raw", "-z")).hexdigest()
    result = {"initial_snapshot_head": baseline["base_head"],
              "verified_head": git(repo,"rev-parse","HEAD").decode().strip(),
              "protected_file_count": len(baseline["protected_files"]),
              "changed_protected_files": changed,
              "preexisting_staged_diff_preserved": staged == baseline["staged_diff_raw_sha256"]}
    (out / "PRESERVATION_VERIFICATION.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    assert not changed and result["preexisting_staged_diff_preserved"]


def secondary_sources(out):
    raw = out / "pilot/source_snapshots"
    manifest = json.loads((out / "pilot/SOURCE_DOWNLOAD_MANIFEST.json").read_text())
    relurl = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/blkgrp/tab20_blkgrp20_blkgrp10_st06.txt"
    manifest.append(fetch(relurl, raw / "tab20_blkgrp20_blkgrp10_st06.txt"))
    records = []
    fields = "GEOID10,GEOID20,HH,TotEmp,E5_Ret,E5_Off,E5_Ind,E5_Svc,E5_Ent,D2A_EPHHM,D2B_E8MIXA"
    expected = get_json(EPA + "/query", dict(f="json", where="STATEFP=6 AND COUNTYFP=37", returnCountOnly="true"))["count"]
    meta = json.loads((raw / "EPA_SLD_v3_layer.json").read_text())
    page_size = meta["maxRecordCount"]
    for offset in range(0, expected, page_size):
        url = EPA + "/query?" + urllib.parse.urlencode(dict(f="json", where="STATEFP=6 AND COUNTYFP=37",
              outFields=fields, returnGeometry="false", resultOffset=offset, resultRecordCount=page_size, orderByFields="OBJECTID"))
        name = f"EPA_LA_BG_page_{offset:05d}.json"
        manifest.append(fetch(url, raw / name))
        page = json.loads((raw / name).read_text())
        if "error" in page:
            raise RuntimeError(page["error"])
        records.extend(f["attributes"] for f in page["features"])
    assert len(records) == expected
    pd.DataFrame(records).to_csv(out / "pilot/EPA_SLD_V3_LA_BG_SOURCE.csv", index=False)
    metadata_url = SCAG24 + "/0?f=pjson"
    manifest.append(fetch(metadata_url, raw / "SCAG_current_LA_layer.json"))
    queries = {
        "SCAG2019_LA_count_verified": dict(f="json", where="COUNTY_ID='037'", returnCountOnly="true"),
        "SCAG2019_LA_source_counts_verified": dict(f="json", where="COUNTY_ID='037'", returnGeometry="false",
            groupByFieldsForStatistics="LU19_SRC", outStatistics=json.dumps([dict(statisticType="count", onStatisticField="OBJECTID", outStatisticFieldName="parcel_records")])),
        "SCAG2019_LA_landuse_counts_verified": dict(f="json", where="COUNTY_ID='037'", returnGeometry="false",
            groupByFieldsForStatistics="LU19", outStatistics=json.dumps([dict(statisticType="count", onStatisticField="OBJECTID", outStatisticFieldName="parcel_records")])),
        "SCAG2019_LA_qa_counts_verified": dict(f="json", where="COUNTY_ID='037' AND (STACK>0 OR APN_DUP>0)", returnCountOnly="true"),
        "SCAG2019_LA_stack_distribution": dict(f="json", where="COUNTY_ID='037'", returnGeometry="false",
            groupByFieldsForStatistics="STACK", outStatistics=json.dumps([dict(statisticType="count", onStatisticField="OBJECTID", outStatisticFieldName="parcel_records")])),
        "SCAG2019_LA_apn_distribution": dict(f="json", where="COUNTY_ID='037'", returnGeometry="false",
            groupByFieldsForStatistics="APN_DUP", outStatistics=json.dumps([dict(statisticType="count", onStatisticField="OBJECTID", outStatisticFieldName="parcel_records")])),
    }
    for name, params in queries.items():
        url = SCAG19 + "/query?" + urllib.parse.urlencode(params)
        try:
            manifest.append(fetch(url, raw / (name + ".json")))
            print(name, json.loads((raw / (name + ".json")).read_text()), flush=True)
        except Exception as exc:
            print(name, str(exc), flush=True)
    (out / "pilot/SOURCE_DOWNLOAD_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"EPA LA source block groups retrieved: {expected}")


def crosswalk_audit(out):
    src = pd.read_csv(out / "pilot/EPA_SLD_V3_LA_BG_SOURCE.csv")
    src["GEOID10"] = src.GEOID10.astype("int64").astype(str).str.zfill(12)
    src["GEOID20"] = src.GEOID20.astype("int64").astype(str).str.zfill(12)
    assert not src.GEOID10.duplicated().any()
    relation = pd.read_csv(out / "pilot/source_snapshots/tab20_blkgrp20_blkgrp10_st06.txt", sep="|", dtype=str)
    area_cols = ["AREALAND_BLKGRP_20", "AREALAND_PART"]
    relation[area_cols] = relation[area_cols].apply(pd.to_numeric)
    coverage = pd.read_csv(out / "BUILT_ENVIRONMENT_TRACT_COVERAGE.csv", dtype={"tract_id": str})
    relation["tract_id"] = relation.GEOID_BLKGRP_20.str[:11]
    target = relation.loc[relation.tract_id.isin(coverage.tract_id) & relation.AREALAND_PART.gt(0)].copy()
    target["source_present"] = target.GEOID_BLKGRP_10.isin(set(src.GEOID10))
    geographic_land = target.assign(covered_land=target.AREALAND_PART.where(target.source_present, 0)).groupby("tract_id").agg(
        target_land_m2=("AREALAND_PART", "sum"), source_land_m2=("covered_land", "sum"),
        relationship_parts=("source_present", "size"))
    geographic_land["sld_relationship_land_fraction"] = geographic_land.source_land_m2 / geographic_land.target_land_m2
    joins = target.loc[target.source_present].merge(src, left_on="GEOID_BLKGRP_10", right_on="GEOID10", validate="many_to_one")
    active_counts = src[["HH", "E5_Ret", "E5_Off", "E5_Ind", "E5_Svc", "E5_Ent"]].gt(0).sum(axis=1)
    donor_targets = joins.groupby("GEOID10").tract_id.nunique()
    summary = {"source_LA_block_groups": len(src),
               "source_GEOID10_GEOID20_differences": int(src.GEOID10.ne(src.GEOID20).sum()),
               "naive_old_prefix_study_matches": int(coverage.tract_id.isin(src.GEOID10.str[:11]).sum()),
               "study_tracts_with_positive_land_relationship": int(coverage.tract_id.isin(joins.tract_id).sum()),
               "donors_overlapping_multiple_study_2020_tracts": int(donor_targets.gt(1).sum()),
               "maximum_2020_tracts_per_donor": int(donor_targets.max()),
               "source_HH_plus_employment_zero": int((src.HH + src.TotEmp).eq(0).sum()),
               "source_D2A_negative": int(src.D2A_EPHHM.lt(0).sum()),
               "source_D2B_negative": int(src.D2B_E8MIXA.lt(0).sum()),
               "source_activity_category_count_le_1": int(active_counts.le(1).sum()),
               "relationship_land_fraction_min": float(geographic_land.sld_relationship_land_fraction.min()),
               "study_tracts_land_fraction_below_0_999": int(geographic_land.sld_relationship_land_fraction.lt(.999).sum()),
               "status": "GEOGRAPHY_FEASIBILITY_ONLY_NO_TRACT_ACTIVITY_INDICATOR"}
    coverage = coverage.drop(columns="sld_relationship_land_fraction", errors="ignore")
    coverage = coverage.merge(geographic_land[["sld_relationship_land_fraction"]], on="tract_id", how="left", validate="one_to_one")
    coverage["sld_tract_indicator_status"] = "geographic_relationship_only_indicator_not_computed"
    coverage.to_csv(out / "BUILT_ENVIRONMENT_TRACT_COVERAGE.csv", index=False)
    geographic_land.to_csv(out / "pilot/EPA_CROSSWALK_GEOGRAPHIC_COVERAGE.csv")
    (out / "pilot/EPA_CROSSWALK_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def reliability_audit(repo, out):
    coverage = pd.read_csv(out / "BUILT_ENVIRONMENT_TRACT_COVERAGE.csv", dtype={"tract_id": str})
    clusters = pd.read_csv(repo / STAGE7 / "clusters_labels_final.csv", dtype={"tract_id": str})
    clusters["tract_id"] = clusters.tract_id.str.zfill(11)
    values = clusters[["tract_id"] + FEATURES].merge(
        coverage[["tract_id","B25024_001E","housing_5plus_share","housing_5plus_share_moe90"]],
        on="tract_id", how="left", validate="one_to_one")
    for col in ("Pop_Density", "NRI_BUILDVALUE"):
        values[col] = np.log1p(values[col])
    subsets = {
        "all_residential": pd.Series(True, index=values.index),
        "total_units_ge_100": values.B25024_001E.ge(100),
        "share_moe90_le_0_20": values.housing_5plus_share_moe90.le(.20),
    }
    rows = []
    for label, mask in subsets.items():
        selected = values.loc[mask]
        for feature in FEATURES:
            for method in ("pearson", "spearman"):
                rows.append(dict(subset=label, existing_feature=feature, method=method,
                    n=len(selected), correlation=selected[[feature,"housing_5plus_share"]].corr(method=method).iloc[0,1]))
    pd.DataFrame(rows).to_csv(out / "pilot/B25024_RELIABILITY_SENSITIVITY.csv", index=False)
    src = pd.read_csv(out / "pilot/EPA_SLD_V3_LA_BG_SOURCE.csv")
    checks = {
        "ACS_missing_estimate_or_moe_cells_in_study": int(coverage[[c for c in coverage if c.startswith("B25024_")]].isna().sum().sum()),
        "EPA_missing_selected_activity_cells": int(src[["HH","TotEmp","E5_Ret","E5_Off","E5_Ind","E5_Svc","E5_Ent","D2A_EPHHM","D2B_E8MIXA"]].isna().sum().sum()),
        "EPA_five_sector_total_mismatches": int(src[["E5_Ret","E5_Off","E5_Ind","E5_Svc","E5_Ent"]].sum(axis=1).ne(src.TotEmp).sum()),
        "EPA_entropy_outside_0_1": int((~src.D2A_EPHHM.between(0,1) | ~src.D2B_E8MIXA.between(0,1)).sum()),
        "nonresidential_positive_housing_tract": coverage.loc[~coverage.residential_typology_member & coverage.B25024_001E.gt(0),"tract_id"].tolist(),
    }
    (out / "pilot/ADDITIONAL_QA.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))


def package_audit(out):
    target = out / "package"
    source_names = ["B25024_metadata.json", "B25034_metadata.json", "EPA_SLD_v3_layer.json",
        "SCAG_2019_1_layer.json", "SCAG_current_LA_service.json", "SCAG_current_LA_layer.json",
        "Annual_NLCD_WMS_capabilities.xml", "SCAG2019_LA_count_verified.json",
        "SCAG2019_LA_source_counts_verified.json", "SCAG2019_LA_landuse_counts_verified.json",
        "SCAG2019_LA_qa_counts_verified.json", "SCAG2019_LA_stack_distribution.json",
        "SCAG2019_LA_apn_distribution.json"]
    names = ["BUILT_ENVIRONMENT_INDICATOR_RESEARCH.md", "BUILT_ENVIRONMENT_DATA_SOURCE_AUDIT.csv",
        "BUILT_ENVIRONMENT_TRACT_COVERAGE.csv", "BUILT_ENVIRONMENT_FEATURE_REDUNDANCY.md",
        "STAGE7_BUILT_ENVIRONMENT_RECOMMENDATION.md", "PRESERVATION_BASELINE.json",
        "PRESERVATION_VERIFICATION.json", "pilot_audit.py", ".gitattributes",
        "pilot/ACS2022_B25024_LA_tracts.csv", "pilot/ACS_PILOT_SUMMARY.json",
        "pilot/FEATURE_PAIRWISE_CORRELATIONS.csv", "pilot/B25024_EXISTING_CLUSTER_DESCRIPTIONS.csv",
        "pilot/B25024_RELIABILITY_SENSITIVITY.csv", "pilot/ADDITIONAL_QA.json",
        "pilot/EPA_SLD_V3_LA_BG_SOURCE.csv", "pilot/EPA_CROSSWALK_GEOGRAPHIC_COVERAGE.csv",
        "pilot/EPA_CROSSWALK_SUMMARY.json"]
    names += ["pilot/source_snapshots/" + name for name in source_names]
    for name in names:
        dst = target / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out / name, dst)
    manifest = json.loads((out / "pilot/SOURCE_DOWNLOAD_MANIFEST.json").read_text())
    for item in manifest:
        item["accessed_date"] = "2026-10-09"
        item["retained_in_commit"] = item["file"] in source_names
    (target / "pilot/SOURCE_DOWNLOAD_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    hashes = {p.relative_to(target).as_posix(): digest(p) for p in sorted(target.rglob("*"))
              if p.is_file() and p.name != "AUDIT_FILE_MANIFEST.json"}
    (target / "AUDIT_FILE_MANIFEST.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    print(json.dumps({"packaged_files": len(hashes) + 1,
                      "total_bytes": sum(p.stat().st_size for p in target.rglob("*") if p.is_file())}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["snapshot", "fetch", "audit", "secondary", "crosswalk", "reliability", "verify", "package"])
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.phase == "snapshot":
        snapshot(args.repo, args.out)
    elif args.phase == "fetch":
        fetch_sources(args.out)
    elif args.phase == "audit":
        acs_audit(args.repo, args.out)
    elif args.phase == "secondary":
        secondary_sources(args.out)
    elif args.phase == "crosswalk":
        crosswalk_audit(args.out)
    elif args.phase == "reliability":
        reliability_audit(args.repo, args.out)
    elif args.phase == "package":
        package_audit(args.out)
    else:
        verify(args.repo, args.out)


if __name__ == "__main__":
    main()
