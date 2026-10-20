"""SCE-supported geography aggregation from saved event arrays and integrals.

No sampling, source-gate reconstruction, scheduling, or trajectory generation.
Original closure outputs and submission figures are never written.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from la_grid.paths import REPO_ROOT as ROOT
from la_grid.revision.capacity import run_sce_capacity_supported_sensitivity as source

OUT = ROOT / "results/capacity/SCE_SUPPORTED_GEOGRAPHY"
POLICIES = ["hospital-first", "impact-first", "degree-first", "vulnerability-first"]
N = 1000
TOL = 1e-12
QUANTILES = {"min": 0, "p05": .05, "p25": .25, "median": .5,
             "p75": .75, "p95": .95, "p99": .99, "max": 1}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stats(values, prefix=""):
    a = np.asarray(values, float)
    return {prefix + label + "_hr": float(np.quantile(a, q))
            for label, q in QUANTILES.items()}


def main():
    if OUT.exists():
        raise FileExistsError("Review output already exists; do not overwrite a review without inspection")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    # Preserve historical closure and all current manuscript/review artwork.
    protected = list((ROOT / "results/capacity").glob("SCE_CAPACITY_*"))
    protected += list((ROOT / "results/figure_review/Main").glob("*"))
    protected += list((ROOT / "results/figure_review/Supplement").glob("*"))
    protected += [ROOT / "results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md"]
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in protected if p.is_file()}
    validation = source._load_frozen_validation()
    physical_path = source.PHYSICAL_DIR / "physical_inputs_2pc50.npz"
    physical_manifest = json.loads(source.PHYSICAL_MANIFEST_PATH.read_text())
    assert digest(physical_path) == physical_manifest["files_sha256"]["2pc50"]
    with np.load(physical_path, allow_pickle=False) as z:
        station_ids = z["station_ids"].astype(str)
    mapping = source._load_mapping(station_ids)
    supported, supported_idx, limits = source._load_supported(station_ids)
    assert np.isfinite(mapping.weight).all() and np.allclose(mapping.weight.sum(1), 1, rtol=0, atol=1e-12)
    # No normalization or modification of W. Its original rows already sum to one.
    w = mapping.weight.copy()
    populations = mapping.population.copy()
    tract_ids = mapping.tract_ids.astype(str)
    # Historical offline shards used the saved GIS tract order (the formal
    # evaluator's mapping_cases order), not the sorted CSV-pivot order.
    tract_order_path = ROOT / "Data/Tracts_Within_Expanded_Area.csv"
    offline_tract_ids = pd.read_csv(tract_order_path, dtype={"GEOID": str}).GEOID.to_numpy()
    offline_to_current = pd.Index(offline_tract_ids).get_indexer(tract_ids)
    assert len(offline_tract_ids) == 2315 and (offline_to_current >= 0).all()
    meta = pd.read_csv(source.META_PATH, dtype={"tract_id": str}).set_index("tract_id").reindex(tract_ids)
    support_weight = w[:, supported_idx].sum(1)
    any_support = support_weight > 0
    strict_sce = meta.utility_domain.eq("SCE").to_numpy()
    primary = strict_sce & any_support
    comparison_path = ROOT / "provenance/reviewer_working/Revision_Mapping_Gate/SCE_SUPPORTED_SUBSET_STATUS.csv"
    comparison = pd.read_csv(comparison_path, dtype={"tract_id": str})
    assert len(comparison) == comparison.tract_id.nunique() == 337
    comparison_mask = np.isin(tract_ids, comparison.tract_id)
    candidates_path = ROOT / "provenance/reviewer_working/Revision_Mapping_Gate/SCE_CANDIDATES_FROZEN.csv"
    candidates = pd.read_csv(candidates_path, dtype={"tract_id": str})
    independently_337 = set(candidates.loc[candidates.utility_domain.eq("SCE") &
        (candidates.represented_direct_count > 0), "tract_id"])
    assert independently_337 == set(comparison.tract_id)
    binding = supported.loc[limits < 1 - TOL]
    assert binding.StationID.tolist() == ["306279"]
    olinda_index = list(station_ids).index("306279")
    assert any_support.sum() == 932
    old_summary = pd.read_csv(source.OUTPUT_SUMMARY)
    old_tract = pd.read_csv(source.OUTPUT_TRACT, dtype={"Tract": str})
    old_scheduled = old_summary.loc[old_summary.Hazard.eq("2pc50") & old_summary.row_type.eq("policy") &
                                   ~old_summary.Policy.eq("Unconstrained")]
    assert len(old_scheduled) == 8
    values, trace_records, reconciliation, inputs = {}, [], [], {}
    for p in [source.MAPPING_PATH, source.META_PATH, source.SUPPORTED_PATH,
              source.PHYSICAL_MANIFEST_PATH, physical_path, comparison_path, candidates_path,
              source.OUTPUT_SUMMARY, source.OUTPUT_TRACT, tract_order_path]:
        inputs[p.relative_to(ROOT).as_posix()] = digest(p)
    for policy in POLICIES:
        print("Reading saved arrays only:", policy, flush=True)
        vulnerability = policy == "vulnerability-first"
        offline_dir = source.FORMAL / ("Equity_Amendment/Offline" if vulnerability else "Formal_Offline_Evaluation")
        stem = f"2pc50__C57_D1__{policy}"
        offline_npz = offline_dir / f"{stem}__INTEGRALS.npz"
        offline_json = offline_dir / f"{stem}__EVALUATION.json"
        record = json.loads(offline_json.read_text())
        assert record["realization_count"] == N and record["status"] == "FORMAL_FROZEN_MATRIX_V1"
        assert digest(offline_npz) == record["integral_sha256"]
        for p in [offline_npz, offline_json]: inputs[p.relative_to(ROOT).as_posix()] = digest(p)
        with np.load(offline_npz, allow_pickle=False) as z:
            assert np.array_equal(station_ids, z["station_ids"].astype(str))
            baseline = z["M1_UTILITY_003__normalized_burden_hr"][:, offline_to_current].copy()
            station_integrals = z["G1_BASELINE_050__L_total"].copy()
            physical_hashes = z["physical_hashes"].astype(str)
        assert baseline.shape == (N, 2315) and np.isfinite(baseline).all()
        archive = source.FORMAL / ("Equity_Amendment/T/2pc50/C57_D1" if vulnerability else
                                   f"Formal_Trajectories/2pc50/C57_D1/{policy}")
        for pattern in ["*.npz", "*.json", "*__TASK_EVENTS.csv"]:
            assert len(list(archive.glob(pattern))) == N
        increment = np.zeros_like(baseline)
        station_error = 0.
        for i in range(N):
            rid = f"2pc50__evaluation_{i:04d}"
            npz_path, json_path = archive / (rid + ".npz"), archive / (rid + ".json")
            task_path = archive / (rid + "__TASK_EVENTS.csv")
            rec = json.loads(json_path.read_text()); ident = rec["identity"]
            assert rec["status"] == "FORMAL_FROZEN_MATRIX_V1"
            for key, expected in {"hazard": "2pc50", "strategy": policy, "resource_scenario": "C57_D1",
                "realization_id": rid, "mapping_method_id": "M1_UTILITY_003", "split": "evaluation"}.items():
                assert ident[key] == expected, (rid, key)
            assert ident["event_horizon_hr"] == 480
            assert ident["physical_sample_hash"] == physical_hashes[i] == physical_manifest["sample_hashes"][rid]
            npz_hash, task_hash = digest(npz_path), digest(task_path)
            assert npz_hash == rec["npz_sha256"] and task_hash == rec["task_events_sha256"]
            with np.load(npz_path, allow_pickle=False) as z:
                assert np.array_equal(z["station_ids"].astype(str), station_ids)
                e, time = z["e"].copy(), z["event_time_hr"].copy()
                assert np.isfinite(z["f"]).all() and np.isfinite(e).all()
            assert time[0] == 0 and time[-1] == 480 and (np.diff(time) > 0).all()
            dt = np.diff(time)
            integral = ((1 - e[:-1]) * dt[:, None]).sum(0)
            station_error = max(station_error, float(np.max(np.abs(integral - station_integrals[i]))))
            change = np.maximum(e[:-1, supported_idx] - limits[None, :], 0)
            station_change = (change * dt[:, None]).sum(0)
            assert np.count_nonzero(station_change > TOL) <= 1
            # Linear propagation through the unchanged full mapping. Unsupported
            # station contributions are identical and cancel before aggregation.
            increment[i] = w[:, supported_idx] @ station_change
            assert np.allclose(increment[i], w[:, olinda_index] * station_change[list(supported_idx).index(olinda_index)],
                               rtol=0, atol=1e-12)
            trace_records.append({"policy": policy, "realization_id": rid,
                "source_file": npz_path.relative_to(ROOT).as_posix(), "npz_sha256": npz_hash,
                "identity_file_sha256": digest(json_path), "task_events_sha256": task_hash,
                "physical_sample_hash": physical_hashes[i], "execution_commit": ident["executable_code_commit_sha"]})
        assert station_error < 1e-9
        mapping_error = float(np.max(np.abs(station_integrals @ w.T - baseline)))
        assert mapping_error < 1e-9
        full_base = baseline @ populations / populations.sum()
        reference_path = source.FORMAL / ("Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet" if vulnerability else
                                         "Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet")
        inputs[reference_path.relative_to(ROOT).as_posix()] = digest(reference_path)
        reference = pd.read_parquet(reference_path)
        reference = reference.loc[reference.hazard.eq("2pc50") & reference.resource_scenario.eq("C57_D1") &
            reference.mapping.eq("M1_UTILITY_003") & reference.gate.eq("G1_BASELINE_050") &
            reference.comparison_domain.eq("mapping_native_domain") & reference.strategy_id.eq(policy)].sort_values("realization_id")
        assert len(reference) == N
        baseline_error = float(np.max(np.abs(full_base - reference.population_weighted_normalized_burden_hr.to_numpy())))
        assert baseline_error < 1e-9
        old = old_summary.loc[old_summary.Hazard.eq("2pc50") & old_summary.Policy.eq(policy)].iloc[0]
        full_change = increment @ populations / populations.sum()
        assert abs(full_change.mean() - old.delta) < 1e-9
        old_t = old_tract.loc[old_tract.Hazard.eq("2pc50") & old_tract.Policy.eq(policy)].set_index("Tract").reindex(tract_ids)
        assert np.max(np.abs(increment.mean(0) - old_t.paired_difference.to_numpy())) < 1e-7
        assert np.max(np.abs(baseline.mean(0) - old_t.baseline_burden.to_numpy())) < 1e-7
        reconciliation.append({"policy": policy, "station_integral_max_abs_hr": station_error,
            "unchanged_mapping_max_abs_hr": mapping_error, "full_baseline_max_abs_hr": baseline_error,
            "old_full_increment_abs_hr": abs(full_change.mean() - old.delta)})
        values[policy] = (baseline, increment)
    affected_by_policy = {p: (d > TOL).any(0) for p, (_, d) in values.items()}
    local = np.logical_or.reduce(list(affected_by_policy.values()))
    assert not (local & ~primary).any()
    domains = {"strict_sce_supported": primary, "local_olinda_binding": local,
               "any_supported_diagnostic": any_support, "full_2315_provenance": np.ones(2315, bool)}
    OUT.mkdir(parents=True)
    domain_rows, summary_rows, realization_rows, tract_rows, distributions, series = [], [], [], [], [], {}
    for domain, mask in domains.items():
        pop = populations[mask]; denom = pop.sum()
        domain_rows.append({"domain": domain, "tract_count": int(mask.sum()), "population": float(denom),
            "strict_sce_tract_count": int((mask & strict_sce).sum()),
            "sce_public_record_overlap_tract_count": int((mask & comparison_mask).sum()),
            "sce_public_record_overlap_population": float(populations[mask & comparison_mask].sum())})
        for policy, (base, inc) in values.items():
            b, d = base[:, mask] @ pop / denom, inc[:, mask] @ pop / denom
            series[(domain, policy)] = (b, d)
            summary_rows.append({"domain": domain, "policy": policy, "realization_count": N,
                "tract_count": int(mask.sum()), "population": float(denom),
                "baseline_service_loss_hr": float(b.mean()), "capacity_bounded_service_loss_hr": float((b+d).mean()),
                "capacity_induced_change_hr": float(d.mean()),
                "positive_change_tract_count": int((mask & affected_by_policy[policy]).sum()), **stats(d, "realization_change_")})
            realization_rows.extend({"domain": domain, "policy": policy, "realization_id": f"2pc50__evaluation_{i:04d}",
                "baseline_service_loss_hr": float(b[i]), "capacity_bounded_service_loss_hr": float(b[i]+d[i]),
                "capacity_induced_change_hr": float(d[i])} for i in range(N))
            tmeans = inc[:, mask].mean(0)
            distributions.append({"domain": domain, "policy": policy,
                "statistical_unit": "tract mean across 1000 realizations; unweighted tract quantiles",
                "mean_across_tracts_hr": float(tmeans.mean()), **stats(tmeans, "tract_mean_change_")})
    for policy, (base, inc) in values.items():
        for j, tract in enumerate(tract_ids):
            tract_rows.append({"policy": policy, "tract_id": tract, "utility_domain": meta.iloc[j].utility_domain,
                "population": populations[j], "supported_dependency_weight": support_weight[j],
                "olinda_dependency_weight": w[j, olinda_index], "primary_domain": bool(primary[j]),
                "local_binding_domain": bool(local[j]), "sce_337_comparison_member": bool(comparison_mask[j]),
                "baseline_service_loss_hr": float(base[:, j].mean()),
                "capacity_bounded_service_loss_hr": float((base[:, j]+inc[:, j]).mean()),
                "capacity_induced_change_hr": float(inc[:, j].mean()),
                "positive_change_realization_fraction": float((inc[:, j] > TOL).mean()), **stats(inc[:, j], "change_")})
    contrast_rows = []
    for domain in domains:
        rb, rd = series[(domain, "hospital-first")]
        for policy in POLICIES[1:]:
            b, d = series[(domain, policy)]; before_c, after_c = b-rb, b+d-rb-rd
            contrast_rows.append({"domain": domain, "candidate_policy": policy, "reference_policy": "hospital-first",
                "baseline_contrast_hr": float(before_c.mean()), "capacity_bounded_contrast_hr": float(after_c.mean()),
                "change_in_contrast_hr": float((after_c-before_c).mean()),
                "sign_flipped": bool(before_c.mean() * after_c.mean() < 0),
                **stats(after_c-before_c, "realization_contrast_change_")})
    frames = {"DOMAIN_AUDIT": domain_rows, "POLICY_DOMAIN_SUMMARY": summary_rows,
        "POLICY_DOMAIN_REALIZATIONS": realization_rows, "TRACT_LEVEL_CHANGES": tract_rows,
        "TRACT_CHANGE_DISTRIBUTIONS": distributions, "POLICY_CONTRASTS": contrast_rows,
        "RECONCILIATION": reconciliation, "TRAJECTORY_SOURCE_HASHES": trace_records}
    for name, rows in frames.items(): pd.DataFrame(rows).to_csv(OUT / (name + ".csv"), index=False, float_format="%.15g")
    membership = pd.DataFrame({"tract_id": tract_ids, "utility_domain": meta.utility_domain.to_numpy(),
        "population": populations, "supported_dependency_weight": support_weight,
        "strict_sce_supported": primary, "local_olinda_binding": local, "any_supported_diagnostic": any_support,
        "sce_337_comparison_member": comparison_mask})
    membership.to_csv(OUT / "DOMAIN_MEMBERSHIP.csv", index=False, float_format="%.15g")
    report = {"source_commit": head, "scenario": "2pc50/C57_D1", "realizations_per_policy": N,
        "horizon_hr": 480, "mapping_changed": False, "weights_renormalized": False,
        "unsupported_weights_reassigned": False, "trajectories_generated": 0, "source_hashes": inputs,
        "domains": domain_rows, "policies": summary_rows, "contrasts": contrast_rows,
        "binding_provider_row": binding.to_dict("records"),
        "old_full_scheduled_range_hr": [float(old_scheduled.delta.min()), float(old_scheduled.delta.max())],
        "all_policies_have_same_affected_set": all(np.array_equal(local, m) for m in affected_by_policy.values()),
        "reconciliation": reconciliation, "source_trajectory_manifest_sha256": digest(OUT / "TRAJECTORY_SOURCE_HASHES.csv")}
    report["protected_artwork_and_closure_changes"] = [p for p,h in before.items() if digest(ROOT/p) != h]
    report["source_input_changes"] = [p for p,h in inputs.items() if digest(ROOT/p) != h]
    assert not report["protected_artwork_and_closure_changes"]
    assert not report["source_input_changes"]
    (OUT / "AUDIT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_report(report)
    print(json.dumps({"domains": domain_rows, "policies": summary_rows, "contrasts": contrast_rows}, indent=2), flush=True)


def make_figure(summary):
    from la_grid.plotting.Project_Visualizer import apply_publication_style
    apply_publication_style()
    labels = ["Hospital-first", "Impact-first", "Degree-first", "Vulnerability-first"]
    colors = ["#555555", "#ff7f00", "#4daf4a", "#a65628"]
    fig, axes = plt.subplots(1, 2, figsize=(185/25.4, 90/25.4))
    for ax, domain, title in zip(axes, ["strict_sce_supported", "local_olinda_binding"],
            ["Strict-SCE supported tracts", "OLINDA-affected tracts"]):
        f = summary.loc[summary.domain.eq(domain)].set_index("policy").reindex(POLICIES)
        for i, (_, row) in enumerate(f.iterrows()):
            ax.plot([row.realization_change_p05_hr, row.realization_change_p95_hr], [i,i], color=colors[i], lw=1.2)
            ax.scatter(row.capacity_induced_change_hr, i, color=colors[i], s=18, zorder=3)
            ax.annotate(f"{row.capacity_induced_change_hr:.3f}", (row.realization_change_p95_hr, i),
                        xytext=(5, 0), textcoords="offset points", va="center", fontsize=7.5)
        ax.set_yticks(range(4), labels); ax.invert_yaxis(); ax.set_ylim(3.5,-.5)
        ax.set_xlim(0, float(f.realization_change_p95_hr.max())*1.23)
        ax.set_title(title, fontsize=9.5, pad=22)
        ax.set_xlabel("Capacity-induced service loss (h)")
        ax.grid(axis="x", alpha=.5); ax.set_axisbelow(True)
        ax.spines[["right", "top"]].set_visible(False)
        ax.text(.5,1.02,f"{int(f.tract_count.iloc[0]):,} tracts; population {int(f.population.iloc[0]):,}",
                transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5)
    fig.subplots_adjust(left=.165, right=.965, bottom=.18, top=.8, wspace=.78)
    temporary_artwork = Path(tempfile.gettempdir()) / "sce_capacity_artwork_checks"
    temporary_artwork.mkdir(exist_ok=True)
    fig.savefig(temporary_artwork / "capacity_geography_panel.pdf")
    fig.savefig(temporary_artwork / "capacity_geography_panel.png", dpi=600)
    plt.close(fig)


def write_report(report):
    lines = ["# SCE capacity geography review", "", "Review only. Current Fig. S8 and its caption are unchanged.", "",
        "## Exact domains and estimand", "",
        "- Primary: frozen utility_domain = SCE, and positive original mapping weight to at least one of the fixed 19 one-to-one SCE stations.",
        "- Local binding: positive integrated OLINDA capacity increment in at least one of the 1,000 saved realizations of any of the four reported policies. Numerical tolerance is 1e-12 h. This set is recomputed, not imported from the old count; all four policies yield the same set.",
        "- Diagnostic: any positive dependency on the 19 stations, irrespective of utility classification. Public-record overlaps use the exact 337-tract set, independently checked against strict-SCE tracts with represented direct candidates.",
        "- Full 2,315-tract domain is provenance only; it is not the manuscript-facing SCE estimate.", "",
        "For tract r and realization n, the increment is the 0–480 h left-rectangle event integral of the original weighted station-service difference. Domain means use sum(P_r × increment_r) / sum(P_r) over that domain. Original tract weights are neither renormalized nor reassigned. Unsupported station contributions remain identical and cancel. All station trajectories are identified in TRAJECTORY_SOURCE_HASHES.csv. The saved offline tract arrays are aligned by the historical GIS tract order before comparison with the original mapping CSV; this is an ID-order alignment, not a new mapping.", "",
        "## Domain audit", "", "|Domain|Tracts|Population|Overlap with 337|", "|---|---:|---:|---:|"]
    for d in report["domains"]: lines.append(f"|{d['domain']}|{d['tract_count']}|{d['population']:,.0f}|{d['sce_public_record_overlap_tract_count']}|")
    lines += ["", "## Population-weighted service loss", "", "|Domain|Policy|Baseline (h)|Capacity-bounded (h)|Change (h)|", "|---|---|---:|---:|---:|"]
    for r in report["policies"]: lines.append(f"|{r['domain']}|{r['policy']}|{r['baseline_service_loss_hr']:.6f}|{r['capacity_bounded_service_loss_hr']:.6f}|{r['capacity_induced_change_hr']:.6f}|")
    lines += ["", "## Policy contrasts relative to Hospital-first", "", "|Domain|Policy|Baseline (h)|Capacity-bounded (h)|Change (h)|Sign flipped?|", "|---|---|---:|---:|---:|---|"]
    for r in report["contrasts"]: lines.append(f"|{r['domain']}|{r['candidate_policy']}|{r['baseline_contrast_hr']:+.6f}|{r['capacity_bounded_contrast_hr']:+.6f}|{r['change_in_contrast_hr']:+.6f}|{r['sign_flipped']}|")
    primary = [r["capacity_induced_change_hr"] for r in report["policies"] if r["domain"] == "strict_sce_supported"]
    lines += ["", f"**The old about-0.12-h statement does not survive on the primary domain:** the four policies span {min(primary):.6f}–{max(primary):.6f} h.", "",
        "The corrected S8B review candidate shows domain population-weighted mean increments (points) and 5th–95th realization ranges (lines), not confidence intervals. Both axes start at zero; their hour scales differ because the two domain averages have different magnitudes. Forecast planning ceilings are not earthquake-time flow observations or full-network electrical adequacy.", "",
        "TRACT_LEVEL_CHANGES.csv gives each tract's mean increment, realization quantiles and positive-increment frequency. TRACT_CHANGE_DISTRIBUTIONS.csv gives unweighted quantiles of tract means; these are not realization ranges and are not population-weighted percentiles. POLICY_DOMAIN_REALIZATIONS.csv supplies all 1,000 domain results per policy for independent checking.", "",
        "Only OLINDA 66/12 is binding-capable under the existing provider values. Its original forecast demand and planning limit are retained; other supported factors equal one. Existing numerical source files, trajectories, current artwork and caption hashes are unchanged."]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
