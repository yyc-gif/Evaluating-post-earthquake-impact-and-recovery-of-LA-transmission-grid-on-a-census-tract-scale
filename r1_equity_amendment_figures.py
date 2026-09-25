"""Paper figures from frozen formal summaries; no trajectory evaluation."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "Formal_Experiment_20260923"
AMEND = FORMAL / "Equity_Amendment"
OUT = AMEND / "Figures"
ORIGINAL = FORMAL / "Formal_Results" / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet"
M1 = "M1_UTILITY_003"
G1 = "G1_BASELINE_050"
COLORS = {"hospital-first":"#2765a8", "impact-first":"#ec7c34",
          "vulnerability-first":"#693a98", "random":"#748472"}
LABELS = {"hospital-first":"Hospital-first", "impact-first":"Impact-first",
          "vulnerability-first":"Vulnerability-first", "random":"Random"}
HAZARDS = ["Northridge", "SanFernando", "LongBeach", "2pc50"]

def source_data() -> pd.DataFrame:
    old = pd.read_parquet(ORIGINAL)
    new = pd.read_parquet(AMEND / "VULNERABILITY_PRIMARY_SUMMARY.parquet")
    old = old[(old.mapping == M1) & (old.gate == G1) &
              (old.comparison_domain == "mapping_native_domain") &
              (old.strategy_id.isin(COLORS))]
    new = new[(new.mapping == M1) & (new.gate == G1) &
              (new.comparison_domain == "mapping_native_domain")]
    data = pd.concat([old,new], ignore_index=True)
    keys = ["hazard","realization_id","resource_scenario","strategy_id"]
    if data.duplicated(keys).any():
        raise ValueError("Duplicate formal summary identity")
    return data

def save(fig, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)

def figure_a(data: pd.DataFrame) -> None:
    data = data[data.resource_scenario == "C57_D1"]
    rows = data.groupby(["hazard","strategy_id"],as_index=False)[
        ["population_weighted_normalized_burden_hr","burden_Q4_hr"]].mean()
    rows.to_csv(OUT/"FIGURE_A_SOURCE.csv",index=False)
    fig, axes = plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
    for ax,h in zip(axes.flat,HAZARDS):
        sub = rows[rows.hazard==h]
        for _,r in sub.iterrows():
            s=r.strategy_id
            ax.scatter(r.population_weighted_normalized_burden_hr,r.burden_Q4_hr,
                       s=65,color=COLORS[s],label=LABELS[s],zorder=3)
        ax.set_title(h)
        ax.grid(alpha=.2)
        ax.set_xlabel("Population mean normalized burden (h)")
        ax.set_ylabel("Q4 absolute mean burden (h)")
    handles,labels=axes.flat[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="upper center",ncol=4,bbox_to_anchor=(.5,1.04))
    save(fig,"FIGURE_A_EQUITY_EFFICIENCY")

def figure_b(data: pd.DataFrame) -> None:
    d=data[(data.hazard=="2pc50")&(data.resource_scenario=="C57_D1")&
           data.strategy_id.isin(["hospital-first","impact-first","vulnerability-first"])]
    cols=[f"burden_Q{i}_hr" for i in range(1,5)]
    ids=sorted(d.realization_id.unique())
    rng=np.random.default_rng(240914)
    draws=rng.integers(0,len(ids),size=(2000,len(ids)))
    rows=[]
    for s in ["hospital-first","impact-first","vulnerability-first"]:
        q=d[d.strategy_id==s].set_index("realization_id").loc[ids]
        for i,col in enumerate(cols,1):
            vals=q[col].to_numpy(dtype=float)
            boot=vals[draws].mean(axis=1)
            rows.append(dict(strategy=s,quartile=f"Q{i}",mean_burden_hr=vals.mean(),
                             ci_low=np.quantile(boot,.025),ci_high=np.quantile(boot,.975)))
    out=pd.DataFrame(rows)
    out.to_csv(OUT/"FIGURE_B_SOURCE.csv",index=False)
    fig,ax=plt.subplots(figsize=(9,5),constrained_layout=True)
    x=np.arange(4); width=.25
    for j,s in enumerate(["hospital-first","impact-first","vulnerability-first"]):
        q=out[out.strategy==s]
        y=q.mean_burden_hr.to_numpy(); low=q.ci_low.to_numpy(); high=q.ci_high.to_numpy()
        ax.bar(x+(j-1)*width,y,width,color=COLORS[s],label=LABELS[s])
        ax.errorbar(x+(j-1)*width,y,yerr=[y-low,high-y],fmt="none",ecolor="black",capsize=2,lw=.8)
    ax.set_xticks(x,["Q1 lowest","Q2","Q3","Q4 highest"])
    ax.set_ylabel("Population-weighted tract normalized burden (h)")
    ax.set_title("2pc50: absolute burden by fixed vulnerability quartile")
    ax.legend(frameon=False,ncol=3)
    ax.grid(axis="y",alpha=.2)
    save(fig,"FIGURE_B_QUARTILE_ABSOLUTE_BURDEN")

def figure_c() -> None:
    from shapely import wkt
    import geopandas as gpd
    tr=pd.read_csv(ROOT/"Data"/"Tracts_Within_Expanded_Area.csv",dtype={"GEOID":str})
    effects=pd.read_parquet(AMEND/"VULNERABILITY_TRACT_EFFECTS.parquet")
    effects=effects[effects.hazard=="2pc50"].copy()
    effects[["hazard","reference_strategy","tract_id","quartile","population",
             "mean_paired_delta_burden_hr","probability_delta_below_zero",
             "mean_effect_classification"]].to_csv(OUT/"FIGURE_C_SOURCE.csv",index=False)
    geo=gpd.GeoDataFrame(tr[["GEOID"]].copy(),geometry=gpd.GeoSeries.from_wkt(tr.wkt_geom),crs="EPSG:4326")
    fig,axes=plt.subplots(1,2,figsize=(12,6),constrained_layout=True)
    color={"improved":"#358bb8","near-zero":"#dfdfdf","worsened":"#d45c4a","unresolved":"#f0ca69"}
    for ax,ref in zip(axes,["hospital-first","impact-first"]):
        q=geo.merge(effects[effects.reference_strategy==ref],left_on="GEOID",right_on="tract_id",how="left",validate="one_to_one")
        q["mean_effect_classification"]=q.mean_effect_classification.fillna("unresolved")
        q.plot(ax=ax,color=q.mean_effect_classification.map(color),linewidth=0,rasterized=True)
        ax.set_title(f"Vulnerability-first minus {LABELS[ref]}")
        ax.axis("off")
    from matplotlib.patches import Patch
    fig.legend([Patch(facecolor=color[k],label=k) for k in color],list(color),loc="lower center",ncol=4,bbox_to_anchor=(.5,-.01))
    fig.suptitle("2pc50 paired-mean tract effects; ±1 h practical threshold")
    save(fig,"FIGURE_C_TRACT_EFFECT_MAP")

def figure_d(data: pd.DataFrame) -> None:
    d=data[(data.hazard=="2pc50")&data.strategy_id.isin(["hospital-first","impact-first","vulnerability-first"])]
    metrics=[("population_weighted_normalized_burden_hr","Population burden (h)"),
             ("burden_Q4_hr","Q4 burden (h)"),("signed_Q4_minus_Q1_hr","Signed Q4−Q1 gap (h)")]
    crew=[("C29_D1",29),("C57_D1",57),("C86_D1",86),("C114_D1",114)]
    duration=[("C57_D075",.75),("C57_D1",1.0),("C57_D125",1.25),("C57_D150",1.5)]
    rows=[]
    for metric,_ in metrics:
        for axis,settings in [("crew",crew),("duration",duration)]:
            for scenario,x in settings:
                for s in ["hospital-first","impact-first","vulnerability-first"]:
                    q=d[(d.resource_scenario==scenario)&(d.strategy_id==s)]
                    if len(q)!=1000:raise ValueError(f"Missing resource summary {scenario} {s}")
                    rows.append(dict(axis=axis,scenario=scenario,x=x,strategy=s,metric=metric,
                                     mean=q[metric].mean()))
    out=pd.DataFrame(rows);out.to_csv(OUT/"FIGURE_D_SOURCE.csv",index=False)
    fig,axes=plt.subplots(3,2,figsize=(11,10),constrained_layout=True)
    for i,(metric,ylab) in enumerate(metrics):
        for j,axis in enumerate(["crew","duration"]):
            ax=axes[i,j]
            for s in ["hospital-first","impact-first","vulnerability-first"]:
                q=out[(out.axis==axis)&(out.metric==metric)&(out.strategy==s)].sort_values("x")
                ax.plot(q.x,q["mean"],"o-",color=COLORS[s],label=LABELS[s],lw=1.8)
            ax.set_ylabel(ylab)
            ax.set_xlabel("Crews" if axis=="crew" else "Realized duration scale")
            ax.grid(alpha=.2)
            if i==0:ax.set_title("Crew availability" if axis=="crew" else "Repair workload")
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="upper center",ncol=3,bbox_to_anchor=(.5,1.03))
    save(fig,"FIGURE_D_RESOURCE_EQUITY_SENSITIVITY")

def main() -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    data=source_data()
    figure_a(data);figure_b(data);figure_c();figure_d(data)
    print(f"Saved four PNG/PDF figures and source CSVs in {OUT}")

if __name__=="__main__":main()
