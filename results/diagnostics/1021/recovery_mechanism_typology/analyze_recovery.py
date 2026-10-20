"""Bounded, preregistered clustering of recovery responses, not social features."""
from support import *
from itertools import combinations
import time
from scipy.cluster.hierarchy import linkage, cut_tree
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.metrics import adjusted_rand_score, silhouette_samples
from sklearn.preprocessing import SplineTransformer
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits

REPS = ["A-full", "A-PCA", "B"]


def preprocess(rep, source, train):
    raw = source["B"] if rep == "B" else source["A"]
    if rep == "B":
        mean, scale = raw[train].mean(0), raw[train].std(0,ddof=0)
        assert (scale>0).all()
        return (raw-mean)/scale/np.sqrt(3), {"mean":mean,"scale":scale}
    x = raw/np.sqrt(5)
    if rep == "A-full":
        return x, {}
    pca = PCA(n_components=.95,svd_solver="full").fit(x[train])
    return pca.transform(x), {"mean":pca.mean_,"components":pca.components_,
                              "variance_ratio":pca.explained_variance_ratio_}


def fit(x, train, k, seed):
    return KMeans(n_clusters=k, init="k-means++", n_init=50, algorithm="lloyd",
                  max_iter=500,tol=1e-4,random_state=seed).fit(x[train])


def align(reference, prediction, k):
    counts = np.zeros((k,k),dtype=int)
    np.add.at(counts,(reference,prediction),1)
    a,b = linear_sum_assignment(-counts)
    lookup = np.empty(k,dtype=int)
    lookup[b] = a
    return lookup[prediction]


def predict_groups(train_labels, test_labels, y):
    means = {c:y[train_labels==c].mean(0) for c in np.unique(train_labels)}
    return np.stack([means[c] for c in test_labels])


def targets(d):
    names = ["Random_deficit_hr","Random_T80_median_hr","C29_deficit_hr","C114_deficit_hr",
             "Northridge_deficit_hr","LongBeach_deficit_hr","SanFernando_deficit_hr",
             "C29_minus_reference_hr","C114_minus_reference_hr","Random_minus_reference_hr"]
    impact = d.impact__B480_mean.to_numpy()
    values = [d.random__B480_mean,d.random__T80_reached_p50,
              d["2pc50__C29_D1__impact-first__B480_mean"],d["2pc50__C114_D1__impact-first__B480_mean"],
              *[d[h+"__C57_D1__impact-first__B480_mean"] for h in ["Northridge","LongBeach","SanFernando"]]]
    return names,np.column_stack([*values,values[2]-impact,values[3]-impact,values[0]-impact])


def main():
    started = time.time()
    protocol = git("log","-1","--format=%H","--",str(HERE/"PROTOCOL.md")).decode().strip()
    git("merge-base","--is-ancestor",protocol,"refs/remotes/origin/1021")
    a, f, p2, d = inputs()
    source = np.load(HERE/"RECOVERY_MATRICES.npz",allow_pickle=False)
    context = pd.read_csv(HERE/"CONTEXT_AND_SPATIAL_BLOCKS.csv",dtype={"tract_id":str})
    prior = np.load(PRIOR/"SUBSAMPLING_ARRAYS.npz",allow_pickle=False)
    names, y = targets(d)
    assert np.isfinite(y).all() and (d.random__T80_unreached_fraction==0).all()
    n = len(f)
    all_ix = np.arange(n)
    arrays = {"tract_ids":a["tract_ids"],"outcome_names":np.array(names),"outcomes":y}
    fits, silhouettes, profiles, agreement, cross, contributions = [],[],[],[],[],[]
    references, full_x = {},{}
    descriptive = np.column_stack([source["A"],source["B"],d.impact__B480_mean,d.impact__T80_reached_p50,y,f.SOVI_SCORE,f.Population])
    desc_names = [*source["A_names"],*source["B_names"],"reference_total_deficit_hr","reference_T80_median_hr",*names,"SOVI_SCORE","Population"]

    def profile(rep, method, k, labels):
        for c in range(k):
            mask = labels==c
            for j,name in enumerate(desc_names):
                v = descriptive[mask,j]
                profiles.append({"representation":rep,"algorithm":method,"k":k,"cluster":c,"variable":name,
                                 "tracts":int(mask.sum()),"population":int(f.Population[mask].sum()),
                                 "mean":v.mean(),"sd":v.std(ddof=0),"median":np.median(v),
                                 "p10":np.quantile(v,.1),"p25":np.quantile(v,.25),"p75":np.quantile(v,.75),
                                 "p90":np.quantile(v,.9),"min":v.min(),"max":v.max()})
    for rep in REPS:
        x, prep = preprocess(rep,source,all_ix)
        full_x[rep] = x
        arrays[rep+"_matrix"] = x
        for key,v in prep.items():
            arrays[rep+"_preprocess_"+key] = v
        tree = linkage(x,method="ward",metric="euclidean")
        arrays[rep+"_ward_linkage"] = tree
        for k in range(1,7):
            candidates = []
            for seed in range(42,47):
                model = fit(x,all_ix,k,seed)
                labels = model.labels_
                key = f"{rep}_k{k}_s{seed}"
                arrays[key+"_labels"] = labels.astype(np.int16)
                arrays[key+"_centers"] = model.cluster_centers_
                if k>1:
                    sil = silhouette_samples(x,labels,metric="euclidean")
                    arrays[key+"_silhouette"] = sil
                    for c in range(k):
                        v = sil[labels==c]
                        silhouettes.append({"representation":rep,"k":k,"seed":seed,"cluster":c,
                                            "tracts":len(v),"population":int(f.Population[labels==c].sum()),
                                            "mean":v.mean(),"median":np.median(v),"p10":np.quantile(v,.1),
                                            "p90":np.quantile(v,.9),"negative_fraction":np.mean(v<0)})
                else:
                    sil = np.array([np.nan])
                fits.append({"representation":rep,"k":k,"seed":seed,"inertia":model.inertia_,
                             "silhouette_mean":np.mean(sil),"silhouette_median":np.median(sil),
                             "negative_fraction":np.mean(sil<0) if k>1 else np.nan,
                             "min_cluster":int(np.bincount(labels).min()),"components":x.shape[1]})
                candidates.append((model.inertia_,seed,labels))
            _,seed,labels = min(candidates,key=lambda r:(r[0],r[1]))
            references[rep,k] = labels
            arrays[f"{rep}_k{k}_reference_labels"] = labels.astype(np.int16)
            arrays[f"{rep}_k{k}_reference_seed"] = np.array(seed)
            profile(rep,"KMeans",k,labels)
            if k == 1:
                continue
            ward = cut_tree(tree,n_clusters=[k]).ravel()
            arrays[f"{rep}_k{k}_ward_labels"] = ward.astype(np.int16)
            profile(rep,"Ward",k,ward)
            agreement.append({"representation":rep,"k":k,"comparison":"Ward","other":"Ward","ARI":adjusted_rand_score(labels,ward)})
            for sa,sb in combinations(range(42,47),2):
                agreement.append({"representation":rep,"k":k,"comparison":"seed_pair","other":f"{sa}_{sb}",
                                  "ARI":adjusted_rand_score(arrays[f"{rep}_k{k}_s{sa}_labels"],arrays[f"{rep}_k{k}_s{sb}_labels"])})
            for kp,old in p2.items():
                agreement.append({"representation":rep,"k":k,"comparison":"P2","other":f"K{kp}","ARI":adjusted_rand_score(labels,old)})
            total = ((x-x.mean(0))**2).sum(0)
            between = np.stack([np.sum(labels==c)*(x[labels==c].mean(0)-x.mean(0))**2 for c in range(k)])
            for c in range(k):
                for j in range(x.shape[1]):
                    contributions.append({"representation":rep,"k":k,"cluster":c,"coordinate":j,
                                          "between_SS":between[c,j],"total_coordinate_SS":total[j],
                                          "within_SS":total[j]-between[:,j].sum(),
                                          "share_class_centroid_distance":between[c,j]/between[c].sum(),
                                          "removing_initial_without_reweighting":rep=="B" and j==0})
        print("full fits and Ward",rep,flush=True)
    for rep in REPS:
        for ka,kb in combinations(range(2,7),2):
            la,lb = references[rep,ka],references[rep,kb]
            for ca in range(ka):
                for cb in range(kb):
                    ma,mb = la==ca,lb==cb
                    cross.append({"representation":rep,"k_a":ka,"k_b":kb,"class_a":ca,"class_b":cb,
                                  "tracts":int((ma&mb).sum()),"population":int(f.Population[ma&mb].sum()),
                                  "Jaccard":(ma&mb).sum()/(ma|mb).sum(),"ARI":adjusted_rand_score(la,lb)})
    save("FULL_FIT_RESULTS.csv",fits)
    save("PER_CLUSTER_SILHOUETTE.csv",silhouettes)
    save("ORIGINAL_UNIT_PROFILES.csv",profiles)
    save("ALGORITHM_SEED_AND_P2_AGREEMENT.csv",agreement)
    save("CROSS_K_MEMBERSHIP.csv",cross)
    save("COORDINATE_DISTANCE_CONTRIBUTIONS.csv",contributions)
    resampling, stability, shifts, contrast, scores, social_scores, benchmark_cuts = [],[],[],[],[],[],[]
    counts = {(r,k):np.zeros(n,dtype=int) for r in REPS for k in range(2,7)}
    q = p2[4] == 0
    assert q.sum()==37
    social = f.SOVI_SCORE.to_numpy()[:,None]
    xy = context[["x_m","y_m"]].to_numpy()/100000
    geography = np.column_stack([xy,xy[:,0]*xy[:,1],xy**2])

    def record_prediction(method, percent, repeat, train, test, pred):
        for j,name in enumerate(names):
            scores.append({"percent":percent,"repeat":repeat,"method":method,"outcome":name,
                           "MAE":np.mean(abs(pred[:,j]-y[test,j])),"RMSE":np.sqrt(np.mean((pred[:,j]-y[test,j])**2)),
                           "notable_MAE_margin":2. if "T80" in name else 1.})

    designs = [("random",percent,b,prior[f"p{percent}_r{b}_train"]) for percent in [70,85] for b in range(30)]
    designs += [("spatial",0,cell,np.flatnonzero(context.spatial_block.to_numpy()!=cell))
                for cell in sorted(context.spatial_block.unique())]
    for design, percent, repeat, train in designs:
        test = np.setdiff1d(all_ix,train)
        split = f"{design}_p{percent}_r{repeat}"
        arrays[split+"_train"] = train
        for rep in REPS:
            x,prep = preprocess(rep,source,train)
            for key,v in prep.items():
                arrays[split+"_"+rep+"_preprocess_"+key] = v
            continuous = make_pipeline(SplineTransformer(n_knots=4,degree=3,knots="quantile",include_bias=False),Ridge(alpha=1))
            continuous.fit(x[train],y[train])
            social_model = make_pipeline(SplineTransformer(n_knots=4,degree=3,knots="quantile",include_bias=False),Ridge(alpha=1))
            social_model.fit(x[train],social[train])
            social_fit = social_model.predict(x)
            # Same recovery basis in both contextual models; only class indicators differ.
            basis = social_model[0].transform(x)
            social_design = np.column_stack([basis,geography])
            social_base = Ridge(alpha=1).fit(social_design[train],social[train]).predict(social_design[test])
            if design == "random":
                record_prediction(rep+"_additive",percent,repeat,train,test,continuous.predict(x[test]))
                lin = np.column_stack([np.ones(n),x])
                record_prediction(rep+"_OLS",percent,repeat,train,test,lin[test]@np.linalg.pinv(lin[train])@y[train])
            for k in range(2,7):
                model = fit(x,train,k,42+int(repeat) if design=="random" else 42)
                raw = model.predict(x)
                ref = references[rep,k]
                aligned = align(ref,raw,k)
                key = split+f"_{rep}_k{k}"
                arrays[key+"_raw_labels"] = raw.astype(np.int16)
                arrays[key+"_aligned_labels"] = aligned.astype(np.int16)
                arrays[key+"_centers"] = model.cluster_centers_
                resampling.append({"design":design,"percent":percent,"repeat":repeat,"representation":rep,"k":k,
                                   "train_n":len(train),"test_n":len(test),"components":x.shape[1],
                                   "full_ARI":adjusted_rand_score(ref,raw),"test_ARI":adjusted_rand_score(ref[test],raw[test])})
                if design=="random":
                    counts[rep,k] += aligned==ref
                    record_prediction(rep+f"_K{k}",percent,repeat,train,test,predict_groups(raw[train],raw[test],y[train]))
                for c in range(k):
                    ma,mb = ref==c,aligned==c
                    for support,ix in [("full",all_ix),("held_out",test)]:
                        union = (ma|mb)[ix].sum()
                        stability.append({"design":design,"percent":percent,"repeat":repeat,"representation":rep,"k":k,"cluster":c,
                                          "support":support,"Jaccard":(ma&mb)[ix].sum()/union if union else np.nan,
                                          "reference_n":int(ma[ix].sum()),"predicted_n":int(mb[ix].sum())})
                    for j,name in enumerate(names):
                        shifts.append({"design":design,"percent":percent,"repeat":repeat,"representation":rep,"k":k,"cluster":c,
                                       "outcome":name,"reference_mean":y[ma,j].mean(),"new_mean":y[mb,j].mean(),
                                       "mean_change":y[mb,j].mean()-y[ma,j].mean()})
                for ca,cb in combinations(range(k),2):
                    old = y[ref==ca].mean(0)-y[ref==cb].mean(0)
                    new = y[aligned==ca].mean(0)-y[aligned==cb].mean(0)
                    for j,name in enumerate(names):
                        threshold = 6. if "T80" in name else 5.
                        contrast.append({"design":design,"percent":percent,"repeat":repeat,"representation":rep,"k":k,
                                         "a":ca,"b":cb,"outcome":name,"reference_difference":old[j],"new_difference":new[j],
                                         "reference_meaningful":abs(old[j])>=threshold,
                                         "same_sign_and_meaningful":np.sign(old[j])==np.sign(new[j]) and abs(new[j])>=threshold})
                augmented = np.column_stack([social_design,np.eye(k)[raw]])
                pred = Ridge(alpha=1).fit(augmented[train],social[train]).predict(augmented[test])
                social_scores.append({"design":design,"percent":percent,"repeat":repeat,"representation":rep,"k":k,
                                      "baseline_MAE":np.mean(abs(social_base-social[test])),
                                      "with_class_MAE":np.mean(abs(pred-social[test])),
                                      "class_MAE_gain":np.mean(abs(social_base-social[test]))-np.mean(abs(pred-social[test]))})
        if design=="random":
            for k in range(2,7):
                for name,v in [("burden",d.impact__B480_mean.to_numpy()),("T80",d.impact__T80_reached_p50.to_numpy())]:
                    cuts = np.unique(np.quantile(v[train],np.arange(1,k)/k))
                    groups = np.searchsorted(cuts,v,side="right")
                    record_prediction(f"quantile_{name}_K{k}",percent,repeat,train,test,
                                      predict_groups(groups[train],groups[test],y[train]))
                    benchmark_cuts.append({"percent":percent,"repeat":repeat,"k":k,"variable":name,"cuts":json.dumps(cuts.tolist())})
            for k in [2,3,4]:
                labels = prior[f"p{percent}_r{repeat}_k{k}_raw_labels"]
                record_prediction(f"P2_K{k}",percent,repeat,train,test,predict_groups(labels[train],labels[test],y[train]))
        print("completed",design,percent,repeat,flush=True)
    save("RESAMPLING_MEMBERSHIP.csv",resampling)
    save("CLUSTER_JACCARD.csv",stability)
    save("RESAMPLED_OUTCOME_PROFILE_SHIFTS.csv",shifts)
    save("WITHHELD_CONTRAST_PERSISTENCE.csv",contrast)
    save("HELD_OUT_ENGINEERING_SCORES.csv",scores)
    save("SOCIAL_CONTEXT_INCREMENTAL_SCORES.csv",social_scores)
    save("QUANTILE_BENCHMARK_CUTS.csv",benchmark_cuts)
    cores,context_rows,rare = [],[],[]
    for rep in REPS:
        for k in range(2,7):
            labels = references[rep,k]
            for i in range(n):
                cores.append({"tract_id":f.tract_id[i],"representation":rep,"k":k,"cluster":int(labels[i]),
                              "same_class_frequency":counts[rep,k][i]/60,"stable_core_ge_0_9":counts[rep,k][i]/60>=.9})
            for c in range(k):
                mask = labels==c
                cells = context.spatial_block[mask].value_counts()
                row = {"representation":rep,"k":k,"cluster":c,"tracts":int(mask.sum()),
                       "population":int(f.Population[mask].sum()),"population_fraction":f.Population[mask].sum()/f.Population.sum(),
                       "SOVI_mean":f.SOVI_SCORE[mask].mean(),"SOVI_p25":f.SOVI_SCORE[mask].quantile(.25),
                       "SOVI_p75":f.SOVI_SCORE[mask].quantile(.75),"SOVI_min":f.SOVI_SCORE[mask].min(),"SOVI_max":f.SOVI_SCORE[mask].max(),
                       "hospital_tract_fraction":context.hospital_tract[mask].mean(),
                       "special_zero_housing_tracts":int(f.additional_zero_housing_positive_population[mask].sum()),
                       "largest_20km_block_fraction":cells.max()/mask.sum(),"occupied_blocks":len(cells)}
                for quartile in [1,2,3,4]:
                    row[f"Q{quartile}_tracts"] = int((f.frozen_SOVI_quartile[mask].astype(str)==f"Q{quartile}").sum())
                context_rows.append(row)
                rare.append({"representation":rep,"k":k,"cluster":c,"tracts":int(mask.sum()),
                             "Q_proxy_37_overlap":int((q&mask).sum()),"fraction_Q_proxy_retained":(q&mask).sum()/37,
                             "class_purity_Q_proxy":(q&mask).sum()/mask.sum(),
                             "zero_initial_fraction":np.mean(source["B"][mask,0]==0),
                             "initial_mean":source["B"][mask,0].mean()})
    save("MEMBERSHIP_CORES.csv",cores)
    save("SOCIAL_AND_GEOGRAPHIC_CONTEXT.csv",context_rows)
    save("Q_SOURCE_PROXY_OVERLAP.csv",rare)
    np.savez_compressed(HERE/"ALL_FITTED_ARRAYS.npz",**arrays)
    dump("ANALYSIS_RUN.json",{
        "protocol_commit":protocol,"protocol_sha256":sha(HERE/"PROTOCOL.md"),"runtime_seconds":time.time()-started,
        "new_full_fits":90,"new_resampling_fits":len(resampling),"seeds":[42,43,44,45,46],
        "n_init":50,"max_iter":500,"tol":1e-4,"algorithm":"lloyd","init":"k-means++",
        "source_matrix_sha256":sha(HERE/"RECOVERY_MATRICES.npz"),"prior_subsamples_sha256":sha(PRIOR/"SUBSAMPLING_ARRAYS.npz"),
        "A_PCA_reference_components":full_x["A-PCA"].shape[1],
        "A_PCA_explained_variance":arrays["A-PCA_preprocess_variance_ratio"].tolist(),
        "all_withheld_T80_uncensored":True,"no_social_variables_in_fit":True,"no_new_physical_model_runs":True,
        "observations":"Equal-tract fitting; held-out tract experiments are conditional same-simulation tests, not empirical validation."})


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
