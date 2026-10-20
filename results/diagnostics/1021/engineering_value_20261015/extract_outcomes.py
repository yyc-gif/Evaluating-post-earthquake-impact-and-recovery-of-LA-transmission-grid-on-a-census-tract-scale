"""Post-process saved event states and integrals, without running physical models."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
import io
import json
from itertools import product
import numpy as np
import pandas as pd
from scipy import sparse
from threadpoolctl import threadpool_limits
from common import *


def overlap_deficit(t, service, left, right):
    widths = np.maximum(0, np.minimum(t[1:], right)-np.maximum(t[:-1], left))
    return (1-service[:, :-1]) @ widths


def first_threshold(t, service, threshold=.8):
    passed = service >= threshold
    indices = np.argmax(passed, axis=1)
    return np.where(passed.any(1), t[indices], np.nan)


def main():
    a, cohort, _ = inputs()
    sys.path.insert(0, str(PARENT))
    import preflight
    dump("PRESERVATION_BEFORE.json", preflight.snapshot())
    order_table = csv_payload("Data/Tracts_Within_Expanded_Area.csv", dtype={"GEOID": str})
    assert order_table.GEOID.is_unique and len(order_table) == 2315
    order = pd.Index(order_table.GEOID)
    eligible = order.get_indexer(cohort.tract_id)
    assert (eligible >= 0).all()
    np.testing.assert_array_equal(order_table.population.to_numpy()[eligible], cohort.Population)
    physical = csv_payload(FORMAL+"Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv")
    mapping = csv_payload("Data/JULY_UTILITY_CONSTRAINED_92.csv", dtype={"tract_id": str, "substation_id": str})
    records, qa, event_qa, values, arrays = [], [], [], {"tract_id": cohort.tract_id.to_numpy()}, {}
    for rel in ["Data/Tracts_Within_Expanded_Area.csv", "Data/JULY_UTILITY_CONSTRAINED_92.csv",
                FORMAL+"Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv",
                FORMAL+"Stage 5 Output_expanded/tract_kpis_2pc50.csv",
                "src/la_grid/revision/formal/stage7.py"]:
        records.append({"path": rel, "sha256": hashlib.sha256(payload(rel)).hexdigest(), "role": "Git-bound lineage/input"})
    off = ARCHIVE/FORMAL/"Formal_Offline_Evaluation"
    external = json.loads(payload("FINAL_REVISION_RUN_SEQUENCE/EXTERNAL_ARCHIVE_MANIFEST.json"))
    anchor = next(r for r in external["artifacts"] if r["artifact_id"] == "formal_offline_shards")
    assert sha(ARCHIVE/anchor["identity_index_file"]) == anchor["identity_index_sha256"]
    assert sha(off/"FORMAL_REALIZATION_STRATEGY_SUMMARY.parquet") == anchor["expected_hash_or_manifest_chain_hash"]
    records.append({"path": str(off/"FORMAL_REALIZATION_STRATEGY_SUMMARY.parquet"), "sha256": anchor["expected_hash_or_manifest_chain_hash"], "role": "Git-manifest-bound consolidated summary"})
    cases = [("2pc50", "C57_D1", p) for p in ["impact-first", "random", "unconstrained"]]
    cases += [("2pc50", c, "impact-first") for c in ["C29_D1", "C114_D1"]]
    cases += [(h, "C57_D1", "impact-first") for h in ["Northridge", "LongBeach", "SanFernando"]]
    for hazard, resource, policy in cases:
        stem = f"{hazard}__{resource}__{policy}"
        meta_path = off/(stem+"__EVALUATION.json")
        meta = json.loads(meta_path.read_text())
        ident = meta["identity"]
        assert ident["H_eval_hr"] == 480 and ident["hazard"] == hazard and ident["resource_case"] == resource
        assert ident["strategy"] == policy and meta["realization_count"] == 1000
        assert "M1_UTILITY_003" in ident["mapping_cases"] and "G1_BASELINE_050" in ident["gate_cases"]
        path = off/(stem+"__INTEGRALS.npz")
        assert sha(path) == meta["integral_sha256"]
        summary_path = off/(stem+"__SUMMARY.parquet")
        assert sha(summary_path) == meta["summary_sha256"]
        records.extend([{"path": str(meta_path), "sha256": sha(meta_path), "role": "shard identity"},
                        {"path": str(path), "sha256": sha(path), "role": "existing tract/station integrals"},
                        {"path": str(summary_path), "sha256": sha(summary_path), "role": "existing aggregate summary"}])
        z = np.load(path, allow_pickle=False)
        sample = physical[(physical.scenario == hazard) & (physical.split == "evaluation")].sort_values("realization_id")
        assert len(sample) == 1000
        np.testing.assert_array_equal(z["physical_hashes"], sample.physical_input_hash)
        stations = pd.Index(z["station_ids"].astype(str))
        weights = sparse.csr_matrix((mapping.weight, (order.get_indexer(mapping.tract_id), stations.get_indexer(mapping.substation_id))), shape=(2315, 92))
        mass = np.asarray(weights.sum(1)).ravel()
        np.testing.assert_allclose(mass, 1, atol=1e-12)
        b = z["M1_UTILITY_003__normalized_burden_hr"]
        loss = z["G1_BASELINE_050__L_total"]
        assert b.shape == (1000, 2315) and np.isfinite(b).all()
        np.testing.assert_allclose(b, (weights @ loss.T).T/mass, atol=1e-10, rtol=0)
        summary = pd.read_parquet(summary_path)
        chosen = summary[(summary.mapping == "M1_UTILITY_003") & (summary.gate == "G1_BASELINE_050") & (summary.comparison_domain == "mapping_native_domain")].sort_values("realization_id")
        np.testing.assert_array_equal(chosen.realization_id, sample.realization_id)
        expected_pop = b @ order_table.population.to_numpy()/order_table.population.sum()
        error = float(np.max(abs(expected_pop-chosen.population_weighted_normalized_burden_hr.to_numpy())))
        assert error < 1e-10
        short = policy.replace("-first", "") if resource == "C57_D1" and hazard == "2pc50" else stem
        values[short+"__B480_mean"] = b[:, eligible].mean(0)
        qa.append({"case": stem, "n_realizations": 1000, "n_tracts": 2315, "eligible_tracts": 2299,
                   "population_summary_max_abs_error": error, "physical_identity_matched": True,
                   "same_physical_samples_as_primary": hazard == "2pc50"})
        if (hazard, resource) == ("2pc50", "C57_D1"):
            sums = {k: np.empty((1000, 2299)) for k in ["early24", "middle24_72", "late72", "T80"]}
            for m, row in enumerate(sample.itertuples()):
                folder = ARCHIVE/FORMAL/"Formal_Trajectories"/hazard/resource/policy
                event_meta_path = folder/(row.realization_id+".json")
                event = json.loads(event_meta_path.read_text())
                ri = event["identity"]
                for key, wanted in [("realization_id", row.realization_id), ("physical_sample_hash", row.physical_input_hash),
                                    ("DS_hash", row.DS_hash), ("duration_hash", row.duration_hash), ("hazard", hazard),
                                    ("resource_scenario", resource), ("strategy", policy), ("event_horizon_hr", 480),
                                    ("mapping_method_id", "M1_UTILITY_003"), ("split", "evaluation")]:
                    assert ri[key] == wanted, (stem, m, key)
                event_path = folder/(row.realization_id+".npz")
                assert sha(event_path) == event["npz_sha256"]
                ez = np.load(event_path, allow_pickle=False)
                np.testing.assert_array_equal(ez["station_ids"].astype(str), stations)
                t, e = ez["event_time_hr"], ez["e"]
                assert t[0] == 0 and t[-1] == 480 and (np.diff(t) > 0).all()
                station_loss = ((1-e[:-1])*np.diff(t)[:, None]).sum(0)
                np.testing.assert_allclose(station_loss, loss[m], atol=1e-10, rtol=0)
                service = (weights[eligible] @ e.T)/mass[eligible, None]
                assert np.isfinite(service).all() and service.min() >= 0 and service.max() <= 1+1e-12
                for name, left, right in [("early24", 0, 24), ("middle24_72", 24, 72), ("late72", 72, 480)]:
                    sums[name][m] = overlap_deficit(t, service, left, right)
                sums["T80"][m] = first_threshold(t, service)
                np.testing.assert_allclose(sum(sums[k][m] for k in ["early24", "middle24_72", "late72"]), b[m, eligible], atol=1e-10, rtol=0)
                event_qa.append({"case": stem, "realization_id": row.realization_id, "physical_hash": row.physical_input_hash,
                                 "DS_hash": row.DS_hash, "duration_hash": row.duration_hash,
                                 "graph_hash": ri["graph_hash"], "source_set_hash": ri["source_set_hash"],
                                 "crew_hash": ri["crew_roster_hash"], "travel_hash": ri["directed_travel_hash"],
                                 "event_path": str(event_path), "event_npz_sha256": event["npz_sha256"],
                                 "event_manifest_sha256": sha(event_meta_path)})
            for name in ["early24", "middle24_72", "late72"]:
                values[short+"__"+name+"_mean"] = sums[name].mean(0)
            times = sums["T80"]
            values[short+"__T80_unreached_fraction"] = np.mean(~np.isfinite(times), axis=0)
            values[short+"__T80_reached_mean"] = np.nanmean(times, axis=0)
            for q in [.1, .5, .9]:
                values[short+f"__T80_reached_p{int(q*100)}"] = np.nanquantile(times, q, axis=0)
            values[short+"__T80_reached_width90_10"] = np.nanquantile(times, .9, axis=0)-np.nanquantile(times, .1, axis=0)
            arrays[short+"__T80"] = times
            print("verified 1000 stored event states", short, flush=True)
    f = pd.DataFrame(values)
    np.testing.assert_allclose(f.unconstrained__B480_mean, cohort.B_Unconstrained, atol=1e-11, rtol=0)
    save("UNFITTED_TRACT_OUTCOMES.csv", f)
    save("SOURCE_HASHES.csv", records)
    save("SOURCE_PAIRING_AND_INTEGRAL_QA.csv", qa)
    save("EVENT_SOURCE_HASHES_AND_IDENTITIES.csv", event_qa)
    np.savez_compressed(HERE/"T80_REALIZATION_VALUES.npz", tract_ids=cohort.tract_id.to_numpy(dtype="U11"), **arrays)
    dump("SOURCE_QA.json", {"status": "PASS", "protocol_commit": git("log", "-1", "--format=%H", "--", str(HERE/"PROTOCOL.md")).decode().strip(),
                            "cases": len(qa), "event_realizations": len(event_qa), "raw_events_are_external_archive_dependencies": True,
                            "no_trajectory_regeneration": True, "original_tract_order_verified": True,
                            "independent_external_validation": False,
                            "legacy_T80_table": "not substituted: older aggregation authority differs; exact event-based reached distributions used"})


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
