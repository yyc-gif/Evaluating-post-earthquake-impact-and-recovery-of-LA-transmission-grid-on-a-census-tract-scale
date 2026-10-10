"""Verify saved Stage 7 records and render original PDFs without fitting a model."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pypdfium2 as pdfium
from pypdf import PdfReader


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return pd.read_csv(path, dtype={"tract_id": str}, float_precision="round_trip")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    a = ap.parse_args()
    repo = a.repo.resolve()
    if os.name == "nt":
        repo = Path("\\\\?\\" + str(repo))
    base = repo / "docs/data_research/built_environment_20261009"
    src = base / "manuscript_integration_preview_20261010"
    out = base / "manuscript_reconciliation_20261010"
    spatial = base / "spatial_k4_validation_20261010"
    freeze = json.loads((src / "STAGE7_CANDIDATE_FREEZE.json").read_text())
    checks = []

    def check(name, condition, evidence):
        checks.append({"check": name, "pass": bool(condition), "evidence": evidence})
        assert condition, name

    manifest = read(src / "OUTPUT_HASHES.csv")
    for row in manifest.itertuples():
        check("Preview payload " + row.file, sha(src / row.file) == row.sha256,
              {"sha256": sha(src / row.file), "bytes": (src / row.file).stat().st_size})
    labels = read(src / "STAGE7_CANDIDATE_LABELS_2291.csv")
    x = read(src / "CLASSIFIED_FEATURE_VALUES_2287.csv")
    full = read(base / "local_joint_feature_extraction_20261009/TRACT_FEATURE_CANDIDATES.csv")
    residential = full.loc[full.residential_member]
    outside = full.loc[~full.residential_member]
    check("Full study cohort", len(full) == 2315 and full.tract_id.is_unique
          and full.formal_population.sum() == 9066522, {"tracts": len(full), "population": int(full.formal_population.sum())})
    check("Saved residential cohort identity", set(residential.tract_id) == set(labels.tract_id)
          and residential.formal_population.sum() == 9049543, {"tracts": len(residential), "population": int(residential.formal_population.sum())})
    check("Outside cohort is not zero residents", len(outside) == 24
          and outside.formal_population.sum() == 16979, {"tracts": len(outside), "population": int(outside.formal_population.sum())})
    outside[["tract_id", "formal_population", "housing_total", "residential_member"]].to_csv(
        out / "OUTSIDE_TYPOLOGY_COHORT_AUDIT.csv", index=False)
    profiles = read(src / "STAGE7_CLUSTER_PROFILES.csv").set_index("candidate_cluster")
    p = np.load(src / "STAGE7_CANDIDATE_PARAMETERS.npz", allow_pickle=False)
    check("Cohorts and GEOID uniqueness", len(labels) == 2291 and len(x) == 2287
          and labels.tract_id.is_unique and x.tract_id.is_unique, {"residential": len(labels), "classified": len(x)})
    null_ids = labels.loc[labels.candidate_cluster.isna(), "tract_id"].tolist()
    check("Four unclassified GEOIDs", sorted(null_ids) == sorted(freeze["unclassified_geoids"]), null_ids)
    check("Saved order and labels", x.tract_id.tolist() == p["tract_id"].tolist()
          and (x.candidate_cluster == ["C" + str(int(i) + 1) for i in p["labels"]]).all(),
          {"saved_labels_sha256": hashlib.sha256(p["labels"].tobytes()).hexdigest()})
    check("Original saved labels", hashlib.sha256(p["labels"].tobytes()).hexdigest()
          == freeze["original_saved_label_sha256"], freeze["original_saved_label_sha256"])
    check("Saved weighted matrix byte hash", hashlib.sha256(p["weighted_standardized_matrix"].tobytes()).hexdigest()
          == freeze["matrix_sha256"], freeze["matrix_sha256"])
    factors = p["coordinate_factors"]
    for name, d in freeze["domains"].items():
        indices = [freeze["coordinate_order"].index(f) for f in d["features"]]
        check("Domain squared-distance budget " + name,
              np.isclose(np.sum(factors[indices] ** 2), .2), float(np.sum(factors[indices] ** 2)))
    values = x[freeze["coordinate_order"]].to_numpy(float)
    weighted = (values - p["scaler_mean"]) / p["scaler_std"] * factors
    check("Raw input preprocessing tolerance", np.allclose(weighted, p["weighted_standardized_matrix"], rtol=0, atol=1e-11),
          {"max_absolute_error": float(np.max(np.abs(weighted - p["weighted_standardized_matrix"])))})
    check("Stock log transform", np.allclose(x.log1p_NRI_BUILDVALUE, np.log1p(x.NRI_BUILDVALUE), rtol=0, atol=1e-12), "Natural log1p only for stock in primary coordinates")
    numeric_rows = []
    for c, g in x.groupby("candidate_cluster"):
        check("Count " + c, len(g) == int(profiles.loc[c, "n_tracts"]), len(g))
        check("Population " + c, g.formal_population.sum() == profiles.loc[c, "population_sum"], int(g.formal_population.sum()))
        for col in profiles.columns:
            suffix = next((s for s in ["_mean", "_median", "_p10", "_p90", "_zero_fraction", "_n_observed"] if col.endswith(s)), None)
            if suffix is None:
                continue
            field = col[:-len(suffix)]
            if field not in g.columns:
                continue
            v = g[field].dropna()
            actual = {"_mean": lambda: v.mean(), "_median": lambda: v.median(),
                      "_p10": lambda: v.quantile(.1), "_p90": lambda: v.quantile(.9),
                      "_zero_fraction": lambda: (v == 0).mean(), "_n_observed": lambda: len(v)}[suffix]()
            saved = float(profiles.loc[c, col])
            check(c + " " + col, np.isclose(actual, saved, rtol=2e-12, atol=1e-11), {"saved": saved, "recomputed": float(actual)})
            numeric_rows.append({"cluster": c, "statistic": col, "saved": saved, "verified": actual})
        pw = np.average(g.B_480_hr, weights=g.formal_population)
        check(c + " population weighted B", np.isclose(pw, profiles.loc[c, "B_480_hr_population_weighted_mean"]), float(pw))
    unclassified = read(src / "UNCLASSIFIED_TRACT_CHARACTERISTICS.csv")
    check("Unclassified population", unclassified.formal_population.sum() == 12390, int(unclassified.formal_population.sum()))
    check("Classified population", x.formal_population.sum() == 9037153, int(x.formal_population.sum()))
    composition = read(base / "nri_eal_redundancy_audit_20261009/EAL_BUILDING_POPULATION_AGRICULTURE_COMPONENTS.csv")
    check("FEMA composition cohort", set(composition.tract_id) == set(labels.tract_id)
          and len(composition) == 2291, len(composition))
    earthquake_pooled = composition.ERQK_EALT.sum() / composition.EAL_VALT.sum() * 100
    earthquake_median = composition.ERQK_EALT_share.median() * 100
    check("Pooled earthquake EAL percent", round(earthquake_pooled, 4) == 98.1563, float(earthquake_pooled))
    check("Median tract earthquake EAL percent", round(earthquake_median, 4) == 99.2745, float(earthquake_median))
    cross = read(src / "STAGE7_OLD_NEW_CROSSWALK.csv")
    counts = cross.pivot(index="original_cluster", columns="candidate_cluster", values="n_intersection").to_numpy()
    choose = lambda v: np.sum(v * (v - 1) / 2)
    total = choose(np.array([counts.sum()]))
    expected = choose(counts.sum(axis=1)) * choose(counts.sum(axis=0)) / total
    ari = (choose(counts) - expected) / ((choose(counts.sum(axis=1)) + choose(counts.sum(axis=0))) / 2 - expected)
    check("Crosswalk ARI", np.isclose(ari, .21662371649602213, rtol=0, atol=1e-14), float(ari))
    check("Old cluster 5 and C2 contingency", counts[4].tolist() == [0, 34, 0, 0], counts[4].tolist())
    runs = read(spatial / "SPATIAL_K4_RUNS.csv")
    for model, expected_ari in [("D", .9234), ("EAL", .9458)]:
        g = runs[runs.model == model]
        check(model + " spatial 20 / 17", len(g) == 20 and g.removed_blocks.nunique() == 17,
              {"cases": len(g), "unique_deletions": int(g.removed_blocks.nunique())})
        check(model + " median ARI", round(g.full_ARI.median(), 4) == expected_ari, float(g.full_ARI.median()))
    small = read(spatial / "SMALL_CLUSTER_34_AUDIT.csv")
    worst = small[(small.model == "D") & (small.seed == 54) & (small.target == "D_SEED42_34")].iloc[0]
    check("Worst C2 specificity", int(worst.prediction_n) == 92 and int(worst.original_members_in_match) == 34
          and np.isclose(worst.prediction_target_purity, 34 / 92), worst.to_dict())
    directions = read(spatial / "SPATIAL_K4_PROFILE_DIRECTION_SUMMARY.csv")
    for ca, cb, feature, reversals in [(1, 4, "land_use_entropy", 0),
                                      (1, 4, "all_use2014_pre1970_area_share", 0),
                                      (1, 4, "Grid_Degree", 12), (1, 4, "Grid_Impact", 12),
                                      (3, 4, "all_use2014_pre1970_area_share", 7),
                                      (1, 3, "B_480_hr", 0), (1, 3, "SOVI_SCORE", 0),
                                      (1, 3, "T80", 0), (3, 4, "B_480_hr", 0),
                                      (3, 4, "SOVI_SCORE", 0), (3, 4, "T80", 0)]:
        row = directions[(directions.model == "D") & (directions.display_class_a == ca)
                         & (directions.display_class_b == cb) & (directions.feature == feature)].iloc[0]
        check("Profile direction C" + str(ca) + "/C" + str(cb) + " " + feature,
              row.reversal_count == reversals and row.replicates == 20, row.to_dict())
    directions[directions.model == "D"].to_csv(out / "VERIFIED_CLASS_DIRECTION_STABILITY.csv", index=False)
    pd.DataFrame(numeric_rows).to_csv(out / "NUMERICAL_PROFILE_VERIFICATION.csv", index=False)
    visual = []
    render = out / "rendered_qa"
    render.mkdir(exist_ok=True)
    for name in ["FIG_STAGE7_TYPOLOGY_MAP", "FIG_STAGE7_CLUSTER_PROFILE", "FIG_STAGE7_SPATIAL_ROBUSTNESS"]:
        path = src / (name + ".pdf")
        reader = PdfReader(path)
        check(name + " one page", len(reader.pages) == 1, len(reader.pages))
        page = reader.pages[0]
        width_mm = float(page.mediabox.width) * 25.4 / 72
        height_mm = float(page.mediabox.height) * 25.4 / 72
        fonts = []
        for font in page["/Resources"]["/Font"].values():
            font = font.get_object()
            if "/DescendantFonts" in font:
                font = font["/DescendantFonts"][0].get_object()
            desc = font.get("/FontDescriptor")
            fonts.append(bool(desc and any(k in desc.get_object() for k in ["/FontFile", "/FontFile2", "/FontFile3"])))
        check(name + " embedded fonts", all(fonts), fonts)
        doc = pdfium.PdfDocument(str(path))
        for target in [185, 178]:
            scale = target / width_mm * 160 / 72
            image = doc[0].render(scale=scale).to_pil()
            dest = render / (name + "_" + str(target) + "mm_160dpi.png")
            image.save(dest, dpi=(160, 160))
        visual.append({"file": str(path), "sha256": sha(path), "native_width_mm": width_mm,
                       "native_height_mm": height_mm, "tested_widths_mm": [185, 178], "embedded_fonts": all(fonts),
                       "text": page.extract_text(), "manual_inspection": "PENDING"})
    result = {"status": "PASS", "checks": checks, "new_clustering_fits": 0, "new_physical_samples": 0,
              "new_simulations": 0, "new_GIS_extraction": 0, "profile_weighting": "equal tract; population weighting only explicitly named statistics",
              "runtime": {"numpy": np.__version__, "pandas": pd.__version__},
              "note": "Statistics reaggregated from frozen labels and inputs; no model inference or refit."}
    (out / "NUMERICAL_QA.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out / "FIGURE_RENDER_QA.json").write_text(json.dumps(visual, indent=2) + "\n", encoding="utf-8")
    print("PASS", len(checks), "checks; original PDFs rendered at 185 and 178 mm")


if __name__ == "__main__":
    main()
