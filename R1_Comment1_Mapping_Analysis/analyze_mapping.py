"""Read-only R1 #1 mapping analysis: no topology/recovery/scheduling/GA execution."""

import io
import json
import pathlib
import re
import subprocess
import zipfile

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from pyproj import Transformer


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(__file__).resolve().parent
HIST = "87110da"
PREFIX = "Review_and_Revision/IJDRR-D-26-02276/"
CHECKPOINT_OID = "257c9475433ee697989e96e90d2e8d5528502a832f2a22795963796217c01cb6"


def git_dir():
    return pathlib.Path(subprocess.check_output(
        ["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True
    ).strip())


def lfs_bytes(oid):
    p = git_dir() / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
    return pathlib.Path("\\\\?\\" + str(p)).read_bytes()


def historic_bytes(path):
    b = subprocess.check_output(["git", "show", f"{HIST}:{PREFIX}{path}"], cwd=ROOT)
    if b.startswith(b"version https://git-lfs"):
        b = lfs_bytes(re.search(rb"oid sha256:([a-f0-9]+)", b).group(1).decode())
    return b


def historic_csv(path):
    return pd.read_csv(io.BytesIO(historic_bytes(path)), dtype=str)


def local_csv(path):
    return pd.read_csv("\\\\?\\" + str((ROOT / path).resolve()), dtype=str)


def parse_ids(x):
    return set() if pd.isna(x) else {s.strip() for s in str(x).split(";") if s.strip()}


def make_weights(dist, eligible):
    valid = eligible & np.isfinite(dist)
    w = np.zeros(len(dist))
    if not valid.any():
        return w
    raw = np.maximum(dist[valid], 1e-3) ** -2
    raw /= raw.sum()
    keep = raw >= 0.03
    if not keep.any():
        keep[np.argmax(raw)] = True
    w[np.flatnonzero(valid)[keep]] = raw[keep] / raw[keep].sum()
    return w


def gini(x, p):
    use = np.isfinite(x) & (p > 0)
    if not use.any():
        return np.nan
    order = np.argsort(x[use])
    a, q = x[use][order], p[use][order]
    if np.sum(a * q) == 0:
        return 0.0
    xx = np.r_[0, np.cumsum(q) / q.sum()]
    yy = np.r_[0, np.cumsum(a * q) / np.sum(a * q)]
    return float(1 - 2 * np.trapz(yy, xx))


def main():
    role = historic_csv("08_UtilitySpecific_SetC_20260914/R1_SERVICE_ROLE_CROSSWALK.csv")
    util = historic_csv("08_UtilitySpecific_SetC_20260914/TRACT_UTILITY_DOMAIN.csv")
    tier = historic_csv("09_MappingArchitecture_20260914/EVIDENCE_TIER_COVERAGE.csv")
    station = historic_csv("05_R1_310_DryBuild_20260913/R1_310_STATIONS_QA.csv")
    edges = historic_csv("06_R1_310_LocalClosure_20260914/R1_310_EDGES.csv")
    z = np.load(io.BytesIO(historic_bytes(
        "06_R1_310_LocalClosure_20260914/R1_310_CLOSURE_DATA.npz")), allow_pickle=True)
    sid, tid = z["station_ids"].astype(str), z["tract_ids"].astype(str)
    assert (len(sid), len(tid)) == (310, 2315)
    role = role.set_index("station_id").reindex(sid)
    station = station.set_index("station_id").reindex(sid)
    util = util.set_index("tract_id").reindex(tid)
    tier = tier.set_index("tract_id").reindex(tid)
    assert not util.UTILITY_DOMAIN.isna().any()
    tracts = local_csv("Data/Tracts_Within_Expanded_Area.csv").set_index("GEOID").reindex(tid)
    centroids = gpd.GeoSeries.from_wkt(tracts.wkt_geom, crs="EPSG:4326").to_crs(3310).centroid
    to_xy = Transformer.from_crs("EPSG:4326", "EPSG:3310", always_xy=True)
    sx, sy = to_xy.transform(pd.to_numeric(role.longitude), pd.to_numeric(role.latitude))
    sc = np.column_stack((sx, sy))
    dist = np.hypot(centroids.x.to_numpy()[:, None] - sx[None, :],
                    centroids.y.to_numpy()[:, None] - sy[None, :]) / 1000
    assert np.isfinite(dist).all()
    graph = nx.Graph()
    graph.add_nodes_from(sid)
    for row in edges.itertuples():
        a, b, d = str(row.src), str(row.tgt), float(row.length_km)
        graph.add_edge(a, b, weight=min(d, graph[a][b]["weight"]) if graph.has_edge(a, b) else d)
    ix = {s: j for j, s in enumerate(sid)}
    nd = np.full((310, 310), np.inf)
    for a, links in nx.all_pairs_dijkstra_path_length(graph, weight="weight"):
        for b, d in links.items():
            nd[ix[a], ix[b]] = d
    owner = role.inventory_owner_unchanged.fillna("").to_numpy()
    eligible_network = (station.registered.eq("True").to_numpy()
                        & (pd.to_numeric(station.component_source_count, errors="coerce").fillna(0).to_numpy() > 0))

    july = local_csv("Data/tract_to_substation_mapping_CEC_expanded.csv")
    july["weight"] = pd.to_numeric(july.weight)
    old_ids = sorted(july.substation_id.unique())
    old_w = july.pivot_table(index="tract_id", columns="substation_id", values="weight",
                             aggfunc="sum", fill_value=0).reindex(index=tid, columns=old_ids, fill_value=0).to_numpy()
    r1_w = np.asarray(z["W"], dtype=float)
    assert np.allclose(old_w.sum(axis=1), 1) and np.allclose(r1_w.sum(axis=1), 1)
    m1, m2 = np.zeros_like(r1_w), np.zeros_like(r1_w)
    for r, domain in enumerate(util.UTILITY_DOMAIN):
        owner_ok = owner == domain if domain in ("SCE", "LADWP") else np.ones(310, dtype=bool)
        m1[r] = make_weights(dist[r], owner_ok)
        ok = owner_ok & eligible_network
        if ok.any():
            access = np.flatnonzero(ok)[np.argmin(dist[r, ok])]
            m2[r] = make_weights(dist[r, access] + nd[access], ok)
    maps = {"M0_July_92": (old_w, old_ids), "M0_R1_310": (r1_w, list(sid)),
            "M1_utility_spatial": (m1, list(sid)), "M2_utility_network": (m2, list(sid))}
    sce = np.flatnonzero(util.UTILITY_DOMAIN.eq("SCE").to_numpy())
    official = [parse_ids(x) for x in util.official_candidate_R1_ids]
    old_coords = july.groupby("substation_id")[["lon", "lat"]].first()
    ox, oy = to_xy.transform(pd.to_numeric(old_coords.lon), pd.to_numeric(old_coords.lat))
    coords = {s: (float(x), float(y)) for s, x, y in zip(sid, sx, sy)}
    coords.update({s: (float(x), float(y)) for s, x, y in zip(old_coords.index, ox, oy)})
    bench = []
    for name, (w, col) in maps.items():
        hits, prec, rec, top1, top3, counts, maximum, hhi, offset = ([] for _ in range(9))
        for r in sce:
            if not official[r]:
                continue
            positive = set(np.asarray(col)[w[r] > 0])
            overlap = positive & official[r]
            rank = np.argsort(-w[r], kind="stable")
            first = col[rank[0]] if w[r, rank[0]] > 0 else None
            hits.append(bool(overlap))
            prec.append(len(overlap) / len(positive) if positive else 0)
            rec.append(len(overlap) / len(official[r]))
            top1.append(first in official[r])
            top3.append(bool(set(np.asarray(col)[rank[:3]]) & official[r]))
            counts.append(len(positive))
            maximum.append(w[r].max())
            hhi.append(np.square(w[r]).sum())
            if first:
                p = np.asarray(coords[first])
                offset.append(min(np.linalg.norm(p - np.asarray(coords[s])) / 1000 for s in official[r]))
        bench.append({"mapping": name, "strict_SCE_tracts": len(sce), "matched_evidence_tracts": len(hits),
                      "any_match_rate": np.mean(hits), "mean_precision_like": np.mean(prec),
                      "mean_recall_like": np.mean(rec), "top1_agreement": np.mean(top1),
                      "top3_agreement": np.mean(top3), "mean_candidate_count": np.mean(counts),
                      "mean_max_weight": np.mean(maximum), "mean_HHI": np.mean(hhi),
                      "mean_effective_candidate_count": np.mean(1 / np.asarray(hhi)),
                      "median_top1_to_nearest_supported_R1_km": np.median(offset),
                      "mean_top1_to_nearest_supported_R1_km": np.mean(offset),
                      "p90_top1_to_nearest_supported_R1_km": np.quantile(offset, 0.9),
                      "unsupported_full_region_tracts": int((w.sum(axis=1) == 0).sum())})
    pd.DataFrame(bench).to_csv(OUT / "SCE_CANDIDATE_BENCHMARK.csv", index=False)

    pop = pd.to_numeric(tier.population).to_numpy()
    hospital = tier.hospital_tract.eq("True").to_numpy()
    quartile = tier.SOVI_fullregion_quartile.to_numpy()
    tiers = pd.DataFrame({"tract_id": tid, "utility_domain": util.UTILITY_DOMAIN.to_numpy(),
                          "population": pop, "official_matched_R1_candidates": [len(x) for x in official],
                          "M1_supported": m1.sum(axis=1) > 0, "M2_supported": m2.sum(axis=1) > 0})
    tiers["evidence_tier"] = np.select([
        tiers.utility_domain.eq("SCE") & tiers.official_matched_R1_candidates.gt(0),
        tiers.utility_domain.isin(["SCE", "LADWP"]) & tiers.M2_supported,
        tiers.M1_supported | tiers.M2_supported
    ], ["Tier 1: SCE public candidate", "Tier 2: utility and network proxy",
        "Tier 3: general proxy"], default="Unsupported")
    tiers.to_csv(OUT / "MAPPING_EVIDENCE_TIERS.csv", index=False)

    known = ~np.isin(sid, ["301479", "303265", "304137", "305021"])
    coverage = []
    for name in ("M0_R1_310", "M1_utility_spatial", "M2_utility_network"):
        resolved = maps[name][0][:, known].sum(axis=1)
        coverage.append({"mapping": name, "all_tracts": len(tid),
                         "tracts_with_resolved_mass": int((resolved > 0).sum()),
                         "fully_unresolved_tracts": int((resolved == 0).sum()),
                         "population_with_resolved_mass": float(pop[resolved > 0].sum()),
                         "population_fully_unresolved": float(pop[resolved == 0].sum()),
                         "population_times_resolved_mass": float(np.sum(pop * resolved))})
    pd.DataFrame(coverage).to_csv(OUT / "MAPPING_RESOLVED_COVERAGE.csv", index=False)
    common = np.logical_and.reduce([maps[n][0][:, known].sum(axis=1) > 0
                                    for n in ("M0_R1_310", "M1_utility_spatial", "M2_utility_network")])
    rows, tracts_out = [], []
    with zipfile.ZipFile(io.BytesIO(lfs_bytes(CHECKPOINT_OID))) as archive:
        for realization in range(32):
            for strategy in ("GA-Balanced", "GA-HospFirst"):
                run = np.load(io.BytesIO(archive.read(
                    f"baseline/r{realization:02d}/{strategy}/evidence.npz")), allow_pickle=True)
                if not np.array_equal(run["full_r1_ids"].astype(str), sid):
                    raise ValueError("Saved trajectory station identity mismatch")
                if not np.array_equal(run["identified"], np.broadcast_to(known, run["identified"].shape)):
                    raise ValueError("Saved trajectory mask mismatch")
                times, state = run["times"], run["effective"]
                # Event-step integral: the pre-completion state holds until the next event.
                deficits = np.sum((1 - state[:-1, known]) * np.diff(times)[:, None], axis=0)
                if not np.array_equal(deficits, run["network_deficit_integrals"][known]):
                    raise ValueError("Saved network deficit integrals differ from offline event-step calculation")
                for name in ("M0_R1_310", "M1_utility_spatial", "M2_utility_network"):
                    wk = maps[name][0][:, known]
                    resolved = wk.sum(axis=1)
                    valid = resolved > 0
                    mass = wk @ deficits
                    burden = np.divide(mass, resolved, out=np.full(len(tid), np.nan), where=valid)
                    use = valid & (pop > 0)
                    common_use = common & use
                    groups = {f"{q}_burden_hr": np.average(burden[use & (quartile == q)],
                              weights=pop[use & (quartile == q)]) for q in ("Q1", "Q2", "Q3", "Q4")}
                    hp = use & hospital
                    curve = state[:, known] @ (wk.T @ pop) / np.sum(pop * resolved)
                    cross = np.flatnonzero(curve >= 0.8)
                    rows.append({"mapping": name, "realization": realization, "strategy": strategy,
                                 "population_T80_hr": float(times[cross[0]]) if len(cross) else np.nan,
                                 "population_normalized_burden_hr": np.average(burden[use], weights=pop[use]),
                                 "common_domain_tracts": int(common.sum()),
                                 "common_domain_population": float(pop[common].sum()),
                                 "common_domain_population_burden_hr": np.average(
                                     burden[common_use], weights=pop[common_use]),
                                 "population_resolved_mass_burden_hr": np.sum(pop * mass) / np.sum(pop * resolved),
                                 "hospital_burden_hr": np.average(burden[hp], weights=pop[hp]),
                                 "Gini": gini(burden, pop),
                                 "Q4_minus_Q1_hr": groups["Q4_burden_hr"] - groups["Q1_burden_hr"], **groups})
                    tracts_out.append((name, realization, strategy, burden))
    metric = pd.DataFrame(rows)
    metric.to_csv(OUT / "OFFLINE_MAPPING_METRICS_TWO_STRATEGIES.csv", index=False)
    metric.groupby(["mapping", "strategy"], as_index=False).mean(numeric_only=True).drop(
        columns="realization").to_csv(OUT / "MAPPING_ROBUSTNESS_METRICS.csv", index=False)
    pair_rows = []
    cols = [c for c in metric.columns if c not in (
        "mapping", "realization", "strategy", "common_domain_tracts", "common_domain_population")]
    for name in ("M0_R1_310", "M1_utility_spatial", "M2_utility_network"):
        a = metric[(metric.mapping == name) & (metric.strategy == "GA-Balanced")].sort_values("realization")
        b = metric[(metric.mapping == name) & (metric.strategy == "GA-HospFirst")].sort_values("realization")
        assert np.array_equal(a.realization, b.realization)
        for col in cols:
            d = a[col].to_numpy() - b[col].to_numpy()
            pair_rows.append({"mapping": name, "contrast": "GA-Balanced minus GA-HospFirst",
                              "metric": col, "paired_realizations": len(d),
                              "mean_paired_difference": float(np.nanmean(d)),
                              "median_paired_difference": float(np.nanmedian(d)),
                              "fraction_negative": float(np.mean(d < 0))})
    pd.DataFrame(pair_rows).to_csv(OUT / "MAPPING_PAIRWISE_EFFECTS.csv", index=False)
    spatial_shifts = []
    for strategy in ("GA-Balanced", "GA-HospFirst"):
        for name in ("M1_utility_spatial", "M2_utility_network"):
            shifts = []
            for r in range(32):
                baseline = next(v for m, rr, s, v in tracts_out if m == "M0_R1_310" and rr == r and s == strategy)
                alt = next(v for m, rr, s, v in tracts_out if m == name and rr == r and s == strategy)
                shifts.append(alt - baseline)
            shifts = np.asarray(shifts)
            finite = np.isfinite(shifts)
            spatial_shifts.append({"mapping": name, "strategy": strategy,
                "mean_absolute_tract_shift_hr": float(np.mean(np.abs(shifts[finite]))),
                "tract_realization_cells_compared": int(finite.sum()),
                "fraction_of_compared_cells_shift_gt_1hr": float(np.mean(np.abs(shifts[finite]) > 1)),
                "mean_tract_shift_hr": float(np.mean(shifts[finite]))})
    pd.DataFrame(spatial_shifts).to_csv(OUT / "MAPPING_TRACT_SHIFT_SUMMARY.csv", index=False)
    effects = []
    for name in ("M0_R1_310", "M1_utility_spatial", "M2_utility_network"):
        paired = []
        for r in range(32):
            a = next(v for m, rr, s, v in tracts_out if m == name and rr == r and s == "GA-Balanced")
            b = next(v for m, rr, s, v in tracts_out if m == name and rr == r and s == "GA-HospFirst")
            paired.append(a - b)
        stacked = np.asarray(paired)
        n = np.isfinite(stacked).sum(axis=0)
        mean = np.divide(np.nansum(stacked, axis=0), n, out=np.full(len(tid), np.nan), where=n > 0)
        classes = np.select([~np.isfinite(mean), mean < -1, mean > 1],
                            ["unresolved", "Balanced_improved", "Balanced_worsened"], default="near_zero")
        effects.extend({"mapping": name, "tract_id": t, "population": p,
                        "mean_paired_Balanced_minus_HospFirst_hr": b, "category_at_1hr": c}
                       for t, p, b, c in zip(tid, pop, mean, classes))
    pd.DataFrame(effects).to_csv(OUT / "OFFLINE_TRACT_ATTRIBUTION_TWO_STRATEGIES.csv", index=False)
    print(json.dumps({"benchmark": bench, "tier_counts": tiers.evidence_tier.value_counts().to_dict()}, indent=2))


if __name__ == "__main__":
    main()
