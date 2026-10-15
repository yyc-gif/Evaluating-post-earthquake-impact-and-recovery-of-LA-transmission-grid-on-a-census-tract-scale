"""Independent arithmetic checks; no K-means or physical model is fitted."""
import json
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
from common import *


def main():
    a, cohort, refs = inputs()
    run = json.loads((HERE/"ANALYSIS_RUN.json").read_text())
    assert run["protocol_sha256"] == sha(HERE/"PROTOCOL.md")
    assert run["source_tract_values_sha256"] == sha(HERE/"UNFITTED_TRACT_OUTCOMES.csv")
    d = pd.read_csv(HERE/"UNFITTED_TRACT_OUTCOMES.csv", dtype={"tract_id": str})
    np.testing.assert_array_equal(d.tract_id, cohort.tract_id)
    assert d.tract_id.str.fullmatch(r"\d{11}").all()
    assert d.drop(columns="tract_id").notna().all().all()
    t80 = np.load(HERE/"T80_REALIZATION_VALUES.npz", allow_pickle=False)
    for policy in ["impact", "random", "unconstrained"]:
        times = t80[policy+"__T80"]
        assert times.shape == (1000,2299)
        for q in [.1,.5,.9]:
            np.testing.assert_allclose(np.nanquantile(times,q,axis=0), d[policy+f"__T80_reached_p{int(q*100)}"], atol=1e-12)
        np.testing.assert_array_equal(np.mean(~np.isfinite(times),axis=0), d[policy+"__T80_unreached_fraction"])
        np.testing.assert_allclose(sum(d[policy+"__"+k+"_mean"] for k in ["early24","middle24_72","late72"]), d[policy+"__B480_mean"], atol=1e-10)
    events = pd.read_csv(HERE/"EVENT_SOURCE_HASHES_AND_IDENTITIES.csv")
    assert len(events) == 3000
    shared = ["physical_hash","DS_hash","duration_hash","graph_hash","source_set_hash","crew_hash","travel_hash"]
    assert (events.groupby("realization_id")[shared].nunique() == 1).all().all()
    z = np.load(HERE/"SUBSAMPLING_ARRAYS.npz", allow_pickle=False)
    scores = pd.read_csv(HERE/"HELD_OUT_OUTCOME_SCORES.csv")
    memberships = pd.read_csv(HERE/"SUBSAMPLING_MEMBERSHIP.csv")
    assert len(memberships) == 600
    stability = pd.read_csv(HERE/"SUBSAMPLING_CLASS_JACCARD.csv")
    cores = pd.read_csv(HERE/"TRACT_MEMBERSHIP_CORE_FREQUENCIES.csv", dtype={"tract_id":str})
    names = z["outcome_names"].tolist()
    assert "unconstrained__B480_mean" not in names
    y = d[names].to_numpy()
    class_checks, score_checks, benchmark_checks = 0,0,0
    cut_table = pd.read_csv(HERE/"SIMPLE_BENCHMARK_CUTS.csv")
    benchmark_values = {"baseline_deficit":cohort.B_Unconstrained.to_numpy(),
                        "constraint_increment":cohort.MeanDelta.to_numpy(),
                        "SOVI":cohort.SOVI_SCORE.to_numpy(),
                        "mean_total_deficit":(cohort.B_Unconstrained+cohort.MeanDelta).to_numpy()}
    counts = {k:np.zeros((2,2299),dtype=int) for k in refs}
    for fi, percent in enumerate([70,85]):
        subset = memberships[memberships.percent == percent]
        for b in range(100):
            train = z[f"p{percent}_r{b}_train"]
            test = np.setdiff1d(np.arange(2299),train)
            assert len(train) == int(np.floor(percent/100*2299)) and len(np.unique(train)) == len(train)
            for k in refs:
                labels = z[f"p{percent}_r{b}_k{k}_labels"]
                raw = z[f"p{percent}_r{b}_k{k}_raw_labels"]
                centers = z[f"p{percent}_r{b}_k{k}_centers"]
                nearest = ((a["weighted_matrix"][:,None,:]-centers[None,:,:])**2).sum(2).argmin(1)
                np.testing.assert_array_equal(nearest,raw)
                row = subset[(subset.repeat == b)&(subset.k == k)].iloc[0]
                np.testing.assert_allclose(adjusted_rand_score(refs[k],labels),row.full_ARI,atol=1e-14)
                counts[k][fi] += labels == refs[k]
                for c in range(k):
                    expected = set(np.flatnonzero(refs[k] == c))
                    actual = set(np.flatnonzero(labels == c))
                    for support,ix in [("full",np.arange(2299)),("held_out",test)]:
                        allowed = set(ix.tolist())
                        union = (expected|actual)&allowed
                        value = len((expected&actual)&allowed)/len(union) if union else np.nan
                        given = stability[(stability.percent==percent)&(stability.repeat==b)&(stability.k==k)&(stability.cluster==c)&(stability.support==support)].iloc[0].Jaccard
                        np.testing.assert_allclose(value,given,atol=1e-14,equal_nan=True)
                        class_checks += 1
                # Independently estimate training class means and score all outcome columns.
                means = np.stack([np.mean(y[train][raw[train]==c],axis=0) for c in range(k)])
                predicted = means[raw[test]]
                actual_scores = scores[(scores.percent==percent)&(scores.repeat==b)&(scores.method==f"K{k}")].set_index("outcome").loc[names]
                np.testing.assert_allclose(np.mean(abs(predicted-y[test]),axis=0),actual_scores.MAE,atol=1e-12)
                np.testing.assert_allclose(np.sqrt(np.mean((predicted-y[test])**2,axis=0)),actual_scores.RMSE,atol=1e-12)
                score_checks += len(names)
            predictions = {}
            for label, values in benchmark_values.items():
                for k in [2,3,4]:
                    cuts = cut_table[(cut_table.percent==percent)&(cut_table.repeat==b)&(cut_table.benchmark==label)&(cut_table.requested_k==k)].iloc[0]
                    edges = np.unique(np.quantile(values[train],np.arange(1,k)/k))
                    np.testing.assert_allclose(edges,json.loads(cuts.cutpoints),atol=1e-14)
                    groups = np.searchsorted(edges,values,side="right")
                    means = pd.DataFrame(y[train]).groupby(groups[train]).mean()
                    predictions[f"Q{k}_{label}"] = means.loc[groups[test]].to_numpy()
            design = np.column_stack([np.ones(len(train)),a["weighted_matrix"][train]])
            design_test = np.column_stack([np.ones(len(test)),a["weighted_matrix"][test]])
            predictions["OLS_seven"] = design_test @ np.linalg.pinv(design) @ y[train]
            continuous = make_pipeline(SplineTransformer(n_knots=4,degree=3,knots="quantile",include_bias=False),Ridge(alpha=1))
            predictions["additive_seven"] = continuous.fit(a["weighted_matrix"][train],y[train]).predict(a["weighted_matrix"][test])
            for method,predicted in predictions.items():
                given = scores[(scores.percent==percent)&(scores.repeat==b)&(scores.method==method)].set_index("outcome").loc[names]
                np.testing.assert_allclose(np.mean(abs(predicted-y[test]),axis=0),given.MAE,atol=1e-10)
                np.testing.assert_allclose(np.sqrt(np.mean((predicted-y[test])**2,axis=0)),given.RMSE,atol=1e-10)
                benchmark_checks += len(names)
    for k in refs:
        given = cores[cores.k==k].set_index("tract_id").loc[cohort.tract_id]
        np.testing.assert_allclose(counts[k].sum(0)/200,given.pooled_same_class_frequency,atol=1e-15)
        np.testing.assert_array_equal(counts[k].sum(0)/200 >= .9,given.stable_core_ge_0_9)
    sys.path.insert(0,str(PARENT))
    import preflight
    assert preflight.snapshot() == json.loads((HERE/"PRESERVATION_BEFORE.json").read_text())
    prior = json.loads((PARENT/"PACKAGE_HASHES.json").read_text())
    assert all(sha(PARENT/name)==h for name,h in prior.items())
    changed = git("diff","--name-only",START).decode().splitlines()
    assert all(p.startswith("results/diagnostics/1021/engineering_value_20261015/") for p in changed)
    protected = json.loads(payload("docs/reproducibility/author_suite_final_layout_20261012/PRESERVATION_BEFORE.json"))["protected_files"]
    assert len(protected)==950 and all(sha(ARCHIVE/name)==h for name,h in protected.items())
    dump("INDEPENDENT_QA.json", {"status":"PASS","exact_GEOIDs":2299,"population":9066522,
                                "old_diagnostic_payloads_unchanged":len(prior),"protected_scientific_files_unchanged":950,
                                "all_registered_subsampling_fits_verified":600,"class_Jaccard_checks":class_checks,
                                "held_out_cluster_outcome_score_checks":score_checks,"event_pairing_identities":3000,
                                "held_out_simple_and_continuous_benchmark_checks":benchmark_checks,
                                "original_worktree_and_index_unchanged":True,"formal_files_unchanged":True})
    print((HERE/"INDEPENDENT_QA.json").read_text())


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
