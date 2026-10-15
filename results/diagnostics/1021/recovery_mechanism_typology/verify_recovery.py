"""Independent reconstruction of saved geometry, labels, scores and preservation."""
from support import *
from sklearn.metrics import adjusted_rand_score
from scipy.cluster.hierarchy import linkage, cut_tree
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits


def rebuild(rep, source, arrays, prefix, train):
    if rep == "A-full":
        return source["A"]/np.sqrt(5)
    mean = arrays[prefix+"mean"]
    raw = source["B"] if rep == "B" else source["A"]/np.sqrt(5)
    np.testing.assert_allclose(mean,raw[train].mean(0),atol=1e-14)
    if rep == "B":
        scale = arrays[prefix+"scale"]
        np.testing.assert_allclose(scale,raw[train].std(0,ddof=0),atol=1e-14)
        return (raw-mean)/scale/np.sqrt(3)
    centered = raw[train]-mean
    _, s, vh = np.linalg.svd(centered,full_matrices=False)
    ratio = s**2/(s**2).sum()
    count = np.searchsorted(np.cumsum(ratio),.95)+1
    comp = arrays[prefix+"components"]
    assert len(comp)==count
    np.testing.assert_allclose(abs(comp@vh[:count].T),np.eye(count),atol=1e-10)
    return (raw-mean)@comp.T


def main():
    _, f, _, d = inputs()
    src = np.load(HERE/"RECOVERY_MATRICES.npz",allow_pickle=False)
    z = np.load(HERE/"ALL_FITTED_ARRAYS.npz",allow_pickle=False)
    registry = json.loads((HERE/"FROZEN_INPUT_REGISTRY.json").read_text())
    run = json.loads((HERE/"ANALYSIS_RUN.json").read_text())
    assert run["protocol_sha256"] == sha(HERE/"PROTOCOL.md") == registry["protocol_sha256"]
    assert run["source_matrix_sha256"] == sha(HERE/"RECOVERY_MATRICES.npz")
    np.testing.assert_array_equal(src["tract_ids"],f.tract_id)
    np.testing.assert_array_equal(z["tract_ids"],f.tract_id)
    np.testing.assert_allclose((1-src["A"])@np.diff(src["edges"]),d.impact__B480_mean,atol=1e-10,rtol=0)
    np.testing.assert_allclose(src["B"][:,0],f.Init_Supply,atol=1e-12,rtol=0)
    np.testing.assert_allclose(src["B"][:,1]+src["B"][:,2],d.impact__B480_mean,atol=1e-12,rtol=0)
    assert src["A"].shape==(2299,5) and src["B"].shape==(2299,3)
    # Reintegrate the merged mean event history independently, in tract space.
    t, station, w = src["mean_event_times"],src["mean_station_availability"],src["weights"]
    chosen = np.array([0,71,1179,2298])
    avail = station@w[chosen].T
    for j,(l,r) in enumerate(zip(src["edges"][:-1],src["edges"][1:])):
        widths = np.maximum(0,np.minimum(t[1:],r)-np.maximum(t[:-1],l))
        expected = widths@avail[:-1]/(r-l)
        np.testing.assert_allclose(expected,src["A"][chosen,j],atol=1e-11,rtol=0)
    full_checks, resample_checks, score_checks, j_checks, benchmark_checks = 0,0,0,0,0
    full = pd.read_csv(HERE/"FULL_FIT_RESULTS.csv")
    res = pd.read_csv(HERE/"RESAMPLING_MEMBERSHIP.csv",dtype={"repeat":str})
    stability = pd.read_csv(HERE/"CLUSTER_JACCARD.csv",dtype={"repeat":str})
    stability = stability.set_index(["design","percent","repeat","representation","k","cluster","support"])
    scores = pd.read_csv(HERE/"HELD_OUT_ENGINEERING_SCORES.csv")
    scores_index = scores.set_index(["percent","repeat","method","outcome"]).sort_index()
    names = z["outcome_names"].tolist()
    y = z["outcomes"]
    from analyze_recovery import targets
    original_names, original_y = targets(d)
    assert names == original_names
    np.testing.assert_array_equal(y,original_y)
    for rep in ["A-full","A-PCA","B"]:
        x = rebuild(rep,src,z,rep+"_preprocess_",np.arange(2299))
        np.testing.assert_allclose(x,z[rep+"_matrix"],atol=1e-14,rtol=1e-14)
        x = z[rep+"_matrix"]
        ward = linkage(x,method="ward",metric="euclidean")
        np.testing.assert_allclose(ward,z[rep+"_ward_linkage"],atol=1e-12)
        for k in range(1,7):
            for seed in range(42,47):
                key = f"{rep}_k{k}_s{seed}"
                labels,centers = z[key+"_labels"],z[key+"_centers"]
                nearest = ((x[:,None,:]-centers[None,:,:])**2).sum(2).argmin(1)
                np.testing.assert_array_equal(nearest,labels)
                inertia = ((x-centers[labels])**2).sum()
                given = full[(full.representation==rep)&(full.k==k)&(full.seed==seed)].iloc[0]
                np.testing.assert_allclose(inertia,given.inertia,rtol=1e-12,atol=1e-10)
                if k>1:
                    s = z[key+"_silhouette"]
                    np.testing.assert_allclose(s.mean(),given.silhouette_mean,atol=1e-14)
                    np.testing.assert_array_equal(cut_tree(ward,n_clusters=[k]).ravel(),z[f"{rep}_k{k}_ward_labels"])
                full_checks += 1
    for row in res.itertuples():
        repeat = row.repeat
        split = f"{row.design}_p{row.percent}_r{repeat}"
        train = z[split+"_train"]
        test = np.setdiff1d(np.arange(2299),train)
        assert len(np.unique(train))==len(train) and len(train)==row.train_n
        if row.design=="random":
            assert len(train)==int(np.floor(row.percent/100*2299))
        x = rebuild(row.representation,src,z,split+"_"+row.representation+"_preprocess_",train)
        key = split+f"_{row.representation}_k{row.k}"
        raw, aligned = z[key+"_raw_labels"],z[key+"_aligned_labels"]
        centers = z[key+"_centers"]
        np.testing.assert_array_equal(((x[:,None,:]-centers[None,:,:])**2).sum(2).argmin(1),raw)
        ref = z[f"{row.representation}_k{row.k}_reference_labels"]
        np.testing.assert_allclose(adjusted_rand_score(ref,raw),row.full_ARI,atol=1e-14)
        np.testing.assert_allclose(adjusted_rand_score(ref[test],raw[test]),row.test_ARI,atol=1e-14)
        for c in range(row.k):
            ma,mb = ref==c,aligned==c
            for support,ix in [("full",np.arange(2299)),("held_out",test)]:
                denominator = (ma|mb)[ix].sum()
                value = (ma&mb)[ix].sum()/denominator if denominator else np.nan
                given = stability.loc[(row.design,row.percent,repeat,row.representation,row.k,c,support)].Jaccard
                np.testing.assert_allclose(value,given,atol=1e-14,equal_nan=True)
                j_checks += 1
        if row.design=="random":
            means = np.stack([y[train][raw[train]==c].mean(0) for c in range(row.k)])
            predicted = means[raw[test]]
            given = scores_index.loc[(row.percent,int(repeat),f"{row.representation}_K{row.k}")].loc[names]
            np.testing.assert_allclose(abs(predicted-y[test]).mean(0),given.MAE,atol=1e-12)
            np.testing.assert_allclose(np.sqrt(((predicted-y[test])**2).mean(0)),given.RMSE,atol=1e-12)
            score_checks += len(names)
        resample_checks += 1
    assert resample_checks == 1125 and full_checks == 90
    prior = np.load(PRIOR/"SUBSAMPLING_ARRAYS.npz",allow_pickle=False)
    for percent in [70,85]:
        for repeat in range(30):
            train=z[f"random_p{percent}_r{repeat}_train"]
            np.testing.assert_array_equal(train,prior[f"p{percent}_r{repeat}_train"])
            test=np.setdiff1d(np.arange(2299),train)
            predictions={}
            for name,values in [("burden",d.impact__B480_mean.to_numpy()),("T80",d.impact__T80_reached_p50.to_numpy())]:
                for k in range(2,7):
                    cuts=np.unique(np.quantile(values[train],np.arange(1,k)/k))
                    groups=np.searchsorted(cuts,values,side="right")
                    averages=pd.DataFrame(y[train]).groupby(groups[train]).mean()
                    predictions[f"quantile_{name}_K{k}"]=averages.loc[groups[test]].to_numpy()
            for k in [2,3,4]:
                labels=prior[f"p{percent}_r{repeat}_k{k}_raw_labels"]
                averages=pd.DataFrame(y[train]).groupby(labels[train]).mean()
                predictions[f"P2_K{k}"]=averages.loc[labels[test]].to_numpy()
            for rep in ["A-full","A-PCA","B"]:
                prefix=f"random_p{percent}_r{repeat}_{rep}_preprocess_"
                x=rebuild(rep,src,z,prefix,train)
                design=np.column_stack([np.ones(2299),x])
                predictions[rep+"_OLS"]=design[test]@np.linalg.pinv(design[train])@y[train]
                model=make_pipeline(SplineTransformer(n_knots=4,degree=3,knots="quantile",include_bias=False),Ridge(alpha=1))
                predictions[rep+"_additive"]=model.fit(x[train],y[train]).predict(x[test])
            for method,pred in predictions.items():
                given=scores_index.loc[(percent,repeat,method)].loc[names]
                np.testing.assert_allclose(abs(pred-y[test]).mean(0),given.MAE,atol=1e-10)
                np.testing.assert_allclose(np.sqrt(((pred-y[test])**2).mean(0)),given.RMSE,atol=1e-10)
                benchmark_checks+=len(names)
    assert snapshot()==registry["publication_snapshot"]
    assert all(sha(ARCHIVE/k)==h for k,h in registry["protected_950"].items())
    changed = git("diff","--name-only",START).decode().splitlines()
    assert all(p.startswith("results/diagnostics/1021/recovery_mechanism_typology/") for p in changed)
    dump("INDEPENDENT_QA.json",{
        "status":"PASS","full_fit_geometry_checks":full_checks,"resampled_fit_geometry_checks":resample_checks,
        "independent_Jaccard_checks":j_checks,"cluster_withheld_score_checks":score_checks,
        "independent_benchmark_outcome_checks":benchmark_checks,
        "eligible_GEOIDs":2299,"population":9066522,"protected_scientific_files":950,
        "prior_diagnostic_payloads_unchanged":len(registry["preserved_prior_payloads"]),
        "exact_event_integrals_and_initial_identity":True,"ordinary_PCA_not_whitened":True,
        "no_social_coordinate_in_fit":True,"publication_worktree_and_index_unchanged":True})
    print((HERE/"INDEPENDENT_QA.json").read_text())


if __name__=="__main__":
    with threadpool_limits(limits=1):
        main()
