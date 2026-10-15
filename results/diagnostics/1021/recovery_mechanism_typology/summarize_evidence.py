"""Complete summaries; no fitting, endpoint selection or threshold optimization."""
from support import *
from scipy.stats import spearmanr, pearsonr
from sklearn.metrics import adjusted_rand_score
from itertools import combinations


def main():
    res=pd.read_csv(HERE/"RESAMPLING_MEMBERSHIP.csv")
    summary=res.groupby(["representation","k","design","percent"]).agg(
        mean_full_ARI=("full_ARI","mean"),min_full_ARI=("full_ARI","min"),
        mean_withheld_ARI=("test_ARI","mean"),min_withheld_ARI=("test_ARI","min"),draws=("full_ARI","size")).reset_index()
    save("MEMBERSHIP_STABILITY_SUMMARY.csv",summary)
    j=pd.read_csv(HERE/"CLUSTER_JACCARD.csv")
    rows=[]
    for key,g in j.groupby(["representation","k","cluster","design","percent","support"]):
        v=g.Jaccard.dropna()
        rows.append(dict(zip(["representation","k","cluster","design","percent","support"],key))|
                    {"median_Jaccard":v.median(),"p10_Jaccard":v.quantile(.1),"dissolution_fraction":np.mean(v<.5),
                     "meets_registered_class_rule":v.median()>=.75 and np.mean(v<.5)<=.1,"valid_draws":len(v)})
    save("CLUSTER_STABILITY_SUMMARY.csv",rows)
    c=pd.read_csv(HERE/"WITHHELD_CONTRAST_PERSISTENCE.csv")
    summary=c.groupby(["representation","k","a","b","outcome","design","percent"]).agg(
        reference_difference=("reference_difference","first"),reference_meaningful=("reference_meaningful","first"),
        persistent_fraction=("same_sign_and_meaningful","mean"),minimum_difference=("new_difference","min"),
        maximum_difference=("new_difference","max")).reset_index()
    save("CONTRAST_PERSISTENCE_SUMMARY.csv",summary)
    scores=pd.read_csv(HERE/"HELD_OUT_ENGINEERING_SCORES.csv")
    save("ENGINEERING_SCORE_SUMMARY.csv",scores.groupby(["method","outcome","percent"]).agg(
        mean_MAE=("MAE","mean"),sd_MAE=("MAE","std"),mean_RMSE=("RMSE","mean")).reset_index())
    rows=[]
    for rep in ["A-full","A-PCA","B"]:
        for k in range(2,7):
            ours=scores[scores.method==f"{rep}_K{k}"]
            others=[f"quantile_burden_K{k}",f"quantile_T80_K{k}",rep+"_additive",rep+"_OLS"]
            others += [f"P2_K{p}" for p in [2,3,4]]
            for method in others:
                paired=ours.merge(scores[scores.method==method],on=["percent","repeat","outcome"],suffixes=("_new","_benchmark"))
                paired["gain"]=paired.MAE_benchmark-paired.MAE_new
                paired["notable"]=paired.gain>=paired.notable_MAE_margin_new
                for (name,percent),g in paired.groupby(["outcome","percent"]):
                    rows.append({"representation":rep,"k":k,"comparator":method,"outcome":name,"percent":percent,
                                 "mean_MAE_gain":g.gain.mean(),"p10_gain":g.gain.quantile(.1),"p90_gain":g.gain.quantile(.9),
                                 "fraction_notable_gain":g.notable.mean()})
    save("PAIRED_BENCHMARK_COMPARISONS.csv",rows)
    social=pd.read_csv(HERE/"SOCIAL_CONTEXT_INCREMENTAL_SCORES.csv")
    save("SOCIAL_CONTEXT_SCORE_SUMMARY.csv",social.groupby(["representation","k","design","percent"]).agg(
        mean_MAE_gain=("class_MAE_gain","mean"),min_MAE_gain=("class_MAE_gain","min"),
        max_MAE_gain=("class_MAE_gain","max")).reset_index())
    source=np.load(HERE/"RECOVERY_MATRICES.npz")
    _,f,_,d=inputs()
    names=[*source["A_names"],*source["B_names"],"reference_total_hr","reference_T80_hr","SOVI_SCORE","log_population"]
    raw=np.column_stack([source["A"],source["B"],d.impact__B480_mean,d.impact__T80_reached_p50,f.SOVI_SCORE,np.log1p(f.Population)])
    associations=[]
    for i in range(len(names)):
        for jj in range(i+1,len(names)):
            valid=raw[:,i].std()>1e-12 and raw[:,jj].std()>1e-12
            associations.append({"a":names[i],"b":names[jj],"Pearson":pearsonr(raw[:,i],raw[:,jj]).statistic if valid else np.nan,
                                 "Spearman":spearmanr(raw[:,i],raw[:,jj]).statistic if valid else np.nan,
                                 "constant_coordinate_pair":not valid})
    save("MECHANISM_AND_CONTEXT_ASSOCIATIONS.csv",associations)
    table=pd.read_csv(HERE/"FULL_FIT_RESULTS.csv")
    save("K_EVIDENCE_SUMMARY.csv",table.groupby(["representation","k"]).agg(
        inertia_mean=("inertia","mean"),inertia_min=("inertia","min"),
        silhouette_mean=("silhouette_mean","mean"),silhouette_sd=("silhouette_mean","std"),
        smallest_class_min=("min_cluster","min"),retained_components=("components","first")).reset_index())
    z=np.load(HERE/"ALL_FITTED_ARRAYS.npz")
    _,_,p2,_=inputs()
    partitions={f"{rep}_K{k}":z[f"{rep}_k{k}_reference_labels"] for rep in ["A-full","A-PCA","B"] for k in range(2,7)}
    partitions.update({f"P2_K{k}":v for k,v in p2.items()})
    for k in range(2,7):
        partitions[f"quantile_burden_K{k}"]=np.searchsorted(np.quantile(d.impact__B480_mean,np.arange(1,k)/k),d.impact__B480_mean,side="right")
    matches=[]
    for (name,la),(other,lb) in combinations(partitions.items(),2):
        matches.append({"partition_a":name,"partition_b":other,"ARI":adjusted_rand_score(la,lb)})
    save("REFERENCE_PARTITION_COMPARISONS.csv",matches)
    merged=[]
    for (name,la),(other,lb) in combinations(partitions.items(),2):
        if not (name.endswith(("K2","K3","K4")) and other.endswith(("K2","K3","K4"))):
            continue
        for ca in np.unique(la):
            for cb in np.unique(lb):
                mask=(la==ca)&(lb==cb)
                if not mask.any():
                    continue
                merged.append({"partition_a":name,"partition_b":other,"class_a":int(ca),"class_b":int(cb),
                               "tracts":int(mask.sum()),"population":int(f.Population[mask].sum()),
                               "reference_deficit_mean":d.impact__B480_mean[mask].mean(),
                               "C29_deficit_mean":d["2pc50__C29_D1__impact-first__B480_mean"][mask].mean(),
                               "Random_deficit_mean":d.random__B480_mean[mask].mean(),"SOVI_mean":f.SOVI_SCORE[mask].mean()})
    save("CROSS_REPRESENTATION_SHARED_SUBSET_PROFILES.csv",merged)
    shape=np.column_stack([source["A"],source["B"]])
    shape_names=[*source["A_names"],*source["B_names"]]
    shifts=[]
    for row in res.itertuples():
        split=f"{row.design}_p{row.percent}_r{row.repeat}"
        key=split+f"_{row.representation}_k{row.k}"
        labels=z[key+"_aligned_labels"]
        ref=z[f"{row.representation}_k{row.k}_reference_labels"]
        for c in range(row.k):
            reference=shape[ref==c].mean(0)
            current=shape[labels==c].mean(0)
            for jj,name in enumerate(shape_names):
                shifts.append({"representation":row.representation,"k":row.k,"cluster":c,"design":row.design,
                               "percent":row.percent,"repeat":row.repeat,"coordinate":name,
                               "reference_mean":reference[jj],"resample_mean":current[jj],"mean_change":current[jj]-reference[jj]})
    save("RECOVERY_SHAPE_RESAMPLING.csv",shifts)
    algebra=[]
    for k in range(2,7):
        seed=int(z[f"B_k{k}_reference_seed"])
        centers=z[f"B_k{k}_s{seed}_centers"]
        x=z["B_matrix"]
        full=z[f"B_k{k}_reference_labels"]
        projected=((x[:,None,1:]-centers[None,:,1:])**2).sum(2).argmin(1)
        for c in range(k):
            old,new=full==c,projected==c
            algebra.append({"k":k,"cluster":c,"reference_n":int(old.sum()),"projected_centroid_n":int(new.sum()),
                            "retained_members":int((old&new).sum()),"fraction_retained":(old&new).sum()/old.sum(),
                            "projection_ARI":adjusted_rand_score(full,projected),
                            "refit":False,"weight_redistribution":False})
    save("B_INITIAL_COORDINATE_ALGEBRA.csv",algebra)
    membership={"tract_id":f.tract_id,"Population":f.Population}
    membership.update(partitions)
    save("TRACT_CLASSIFICATIONS.csv",membership)
    components=z["A-PCA_preprocess_components"]
    save("TRAJECTORY_PCA_LOADINGS.csv",[{"component":i+1,"interval":str(name),"loading":components[i,jj],
                                          "explained_variance_fraction":z["A-PCA_preprocess_variance_ratio"][i]}
                                         for i in range(len(components)) for jj,name in enumerate(source["A_names"])])
    print("A/B K2-4 stability (all registered draws):")
    print(pd.read_csv(HERE/"MEMBERSHIP_STABILITY_SUMMARY.csv").query("representation != 'A-PCA' and k<=4").to_string(index=False))
    print("All outcomes, pooled mean MAE (actual units):")
    chosen=["A-full_K2","A-full_K3","B_K2","B_K3","A-full_additive","B_additive","quantile_burden_K2","quantile_burden_K3","P2_K2","P2_K3","P2_K4"]
    print(scores[scores.method.isin(chosen)].groupby(["outcome","method"]).MAE.mean().unstack().round(3).to_string())


if __name__=="__main__":
    main()
