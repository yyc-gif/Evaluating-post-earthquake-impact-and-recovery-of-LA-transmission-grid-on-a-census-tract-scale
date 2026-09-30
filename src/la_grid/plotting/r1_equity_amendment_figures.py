"""Paper figures from frozen formal summaries; no trajectory evaluation."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import la_grid.plotting.Project_Visualizer as july
from la_grid.paths import REPO_ROOT as ROOT
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

PUBLICATION_FIGURES = ROOT / "results" / "figures"
EQUITY_POLICIES = ["hospital-first", "impact-first", "vulnerability-first"]
EQUITY_LABELS = {
    "hospital-first": "Hospital-first",
    "impact-first": "Impact-first",
    "vulnerability-first": "Vulnerability-first",
}
EQUITY_MARKERS = {"hospital-first": "o", "impact-first": "s", "vulnerability-first": "D"}
EQUITY_HATCHES = {"hospital-first": "", "impact-first": "//", "vulnerability-first": "xx"}


def _publication_equity_colors() -> dict[str, str]:
    """Use July strategy colors plus the established Vulnerability-first extension."""
    july.STAGE6_RECOVERY_STYLE_CONFIG.setdefault(
        "vulnerability-first",
        {"label": "Vulnerability-first", "color": "#a65628", "ls": "-", "lw": 1.08},
    )
    return {
        "hospital-first": july.STAGE6_RECOVERY_STYLE_CONFIG["hospital-first"]["color"],
        "impact-first": july.STAGE6_RECOVERY_STYLE_CONFIG["impact-first"]["color"],
        "vulnerability-first": july.STAGE6_RECOVERY_STYLE_CONFIG["vulnerability-first"]["color"],
        "random": july.STAGE6_RECOVERY_STYLE_CONFIG["random"]["color"],
    }


def render_presentation_copy_from_frozen_sources() -> list[Path]:
    """Render the publication copies from the already frozen figure-source CSVs.

    This entrypoint intentionally does not read realization summaries, bootstrap,
    recompute policy metrics, or replace the frozen original figures. It only
    draws the four precomputed CSV tables into the shared July size/style system.
    """
    import geopandas as gpd
    from matplotlib.colors import TwoSlopeNorm
    from matplotlib.cm import ScalarMappable
    from shapely import wkt

    july.apply_publication_style()
    colors = _publication_equity_colors()
    PUBLICATION_FIGURES.mkdir(parents=True, exist_ok=True)
    out_paths: list[Path] = []

    # A. Uses the already frozen hazard-by-strategy mean table.
    a = pd.read_csv(OUT / "FIGURE_A_SOURCE.csv")
    fig, axes = plt.subplots(
        2, 2,
        figsize=july.get_figsize("COMPOSITE_FULL_DEFAULT", width_cm=18.5, height_cm=13.0),
    )
    for ax, hazard in zip(axes.flat, HAZARDS):
        sub = a.loc[a.hazard.eq(hazard)]
        for strategy, label in [
            ("hospital-first", "Hospital-first"),
            ("impact-first", "Impact-first"),
            ("vulnerability-first", "Vulnerability-first"),
            ("random", "Random"),
        ]:
            row = sub.loc[sub.strategy_id.eq(strategy)]
            if len(row) != 1:
                raise ValueError(f"FIGURE_A_SOURCE lacks one {hazard}/{strategy} row")
            x = float(row.population_weighted_normalized_burden_hr.iloc[0])
            y = float(row.burden_Q4_hr.iloc[0])
            ax.scatter(x, y, s=28, color=colors[strategy], marker=EQUITY_MARKERS.get(strategy, "o"),
                       edgecolor="#333333", linewidth=.3, label=label, zorder=3)
        july.style_axis(
            ax, title=hazard,
            xlabel="Population mean normalized burden (h)",
            ylabel="Q4 absolute mean burden (h)",
        )
        ax.grid(True, color="#e4e4e4", linewidth=.4)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc="upper center", ncol=4,
                        bbox_to_anchor=(.5, .995), frameon=True)
    july.format_legend(legend)
    fig.subplots_adjust(left=.09, right=.985, bottom=.09, top=.88, hspace=.39, wspace=.30)
    p = PUBLICATION_FIGURES / "FIGURE_A_EQUITY_EFFICIENCY.png"
    july.save_plot(fig, str(PUBLICATION_FIGURES), p.name)
    out_paths.extend([p, p.with_suffix(".pdf")])

    # B. Reuses the frozen means and bootstrap intervals; no resampling occurs.
    b = pd.read_csv(OUT / "FIGURE_B_SOURCE.csv")
    fig, ax = plt.subplots(
        figsize=july.get_figsize("COMPOSITE_FULL_DEFAULT", width_cm=18.5, height_cm=10.5)
    )
    x = np.arange(4)
    width = .23
    for j, strategy in enumerate(EQUITY_POLICIES):
        sub = b.loc[b.strategy.eq(strategy)].set_index("quartile").reindex([f"Q{i}" for i in range(1, 5)])
        if sub[["mean_burden_hr", "ci_low", "ci_high"]].isna().any().any():
            raise ValueError(f"FIGURE_B_SOURCE has incomplete intervals for {strategy}")
        y = sub.mean_burden_hr.to_numpy(float)
        low = sub.ci_low.to_numpy(float)
        high = sub.ci_high.to_numpy(float)
        pos = x + (j - 1) * width
        ax.bar(pos, y, width, color=colors[strategy], edgecolor="#333333", linewidth=.35,
               hatch=EQUITY_HATCHES[strategy], label=EQUITY_LABELS[strategy], zorder=2)
        ax.errorbar(pos, y, yerr=[y-low, high-y], fmt="none", ecolor="#222222",
                    capsize=2, linewidth=.65, zorder=3)
    ax.set_xticks(x, ["Q1 lowest", "Q2", "Q3", "Q4 highest"])
    july.style_axis(ax, title="A  Absolute burden by fixed social-vulnerability quartile",
                    ylabel="Population-weighted tract normalized burden (h)")
    legend = ax.legend(frameon=True, ncol=3, loc="upper center", bbox_to_anchor=(.5, 1.0))
    july.format_legend(legend)
    ax.grid(axis="y", color="#e4e4e4", linewidth=.4, zorder=0)
    fig.subplots_adjust(left=.13, right=.985, bottom=.16, top=.84)
    p = PUBLICATION_FIGURES / "FIGURE_B_QUARTILE_ABSOLUTE_BURDEN.png"
    july.save_plot(fig, str(PUBLICATION_FIGURES), p.name)
    out_paths.extend([p, p.with_suffix(".pdf")])

    # C. Reuses the frozen per-tract paired effects and retains their display clip.
    c = pd.read_csv(OUT / "FIGURE_C_SOURCE.csv", dtype={"tract_id": str})
    tract_table = pd.read_csv(ROOT / "Data" / "Tracts_Within_Expanded_Area.csv",
                              dtype={"GEOID": str})
    geo = gpd.GeoDataFrame(
        tract_table[["GEOID"]].copy(),
        geometry=gpd.GeoSeries.from_wkt(tract_table.wkt_geom), crs="EPSG:4326",
    )
    finite = c.mean_paired_delta_burden_hr.dropna().to_numpy(float)
    bound = float(np.nanpercentile(np.abs(finite), 99))
    norm = TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound)
    fig, axes = plt.subplots(
        1, 2,
        figsize=july.get_figsize("COMPOSITE_FULL_DEFAULT", width_cm=18.5, height_cm=10.0),
    )
    for ax, ref, panel in zip(axes, ["hospital-first", "impact-first"], ["A", "B"]):
        sub = c.loc[c.reference_strategy.eq(ref)]
        q = geo.merge(sub, left_on="GEOID", right_on="tract_id", how="left", validate="one_to_one")
        if len(q) != 2315:
            raise ValueError(f"FIGURE_C_SOURCE map domain changed for {ref}")
        q.plot(ax=ax, column="mean_paired_delta_burden_hr", cmap="RdBu_r", norm=norm,
               missing_kwds={"color": "#eeeeee"}, linewidth=0, rasterized=False)
        ax.set_title(f"{panel}  Vulnerability-first minus {EQUITY_LABELS[ref]}",
                     fontsize=july.FS_PANEL, fontweight="semibold")
        ax.set_axis_off()
    sm = ScalarMappable(norm=norm, cmap="RdBu_r")
    cbar = fig.colorbar(sm, ax=axes, orientation="horizontal", shrink=.70, pad=.06)
    july.style_colorbar(cbar, label="Mean paired tract burden change (h)")
    fig.suptitle("2pc50 paired-mean tract burden change (display clipped at 99th percentile)",
                 fontsize=july.FS_SUPTITLE, y=.98)
    fig.subplots_adjust(left=.04, right=.98, bottom=.12, top=.87, wspace=.06)
    p = PUBLICATION_FIGURES / "FIGURE_C_TRACT_EFFECT_MAP.png"
    july.save_plot(fig, str(PUBLICATION_FIGURES), p.name)
    out_paths.extend([p, p.with_suffix(".pdf")])

    # D. Uses only the frozen one-factor-at-a-time mean table.
    d = pd.read_csv(OUT / "FIGURE_D_SOURCE.csv")
    ylabels = {
        "population_weighted_normalized_burden_hr": "Population burden (h)",
        "burden_Q4_hr": "Q4 burden (h)",
        "signed_Q4_minus_Q1_hr": "Signed Q4−Q1 gap (h)",
    }
    metrics = list(ylabels)
    fig, axes = plt.subplots(
        3, 2,
        figsize=july.get_figsize("COMPOSITE_FULL_DENSE", width_cm=18.5, height_cm=16.0),
        sharex="col",
    )
    for i, metric in enumerate(metrics):
        for j, axis in enumerate(["crew", "duration"]):
            ax = axes[i, j]
            for strategy in EQUITY_POLICIES:
                sub = d.loc[d.axis.eq(axis) & d.metric.eq(metric) & d.strategy.eq(strategy)].sort_values("x")
                if len(sub) != 4:
                    raise ValueError(f"FIGURE_D_SOURCE lacks four {axis}/{metric}/{strategy} rows")
                style = july.STAGE6_RECOVERY_STYLE_CONFIG[strategy]
                ax.plot(sub.x, sub["mean"], marker="o", markersize=3.0,
                        color=colors[strategy], linestyle=style.get("ls", "-"), linewidth=1.1,
                        markeredgecolor="#333333", markeredgewidth=.3,
                        label=EQUITY_LABELS[strategy])
            july.style_axis(ax, ylabel=ylabels[metric])
            ax.grid(True, color="#e4e4e4", linewidth=.4)
            if i == 0:
                ax.set_title("A  Crew count (one factor at a time)" if axis == "crew"
                             else "B  Duration scale (one factor at a time)",
                             fontsize=july.FS_PANEL, fontweight="semibold")
            if axis == "crew":
                ax.set_xticks([29, 57, 86, 114], ["29", "57", "86", "114"])
                ax.set_xlabel("Available crews")
            else:
                ax.set_xticks([.75, 1.0, 1.25, 1.5], ["0.75", "1.00", "1.25", "1.50"])
                ax.set_xlabel("Repair-duration scale")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc="upper center", ncol=3,
                        bbox_to_anchor=(.5, .995), frameon=True)
    july.format_legend(legend)
    fig.subplots_adjust(left=.13, right=.985, bottom=.09, top=.88, hspace=.38, wspace=.27)
    p = PUBLICATION_FIGURES / "FIGURE_D_RESOURCE_EQUITY_SENSITIVITY.png"
    july.save_plot(fig, str(PUBLICATION_FIGURES), p.name)
    out_paths.extend([p, p.with_suffix(".pdf")])
    return out_paths

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
    fig.savefig(OUT / f"{stem}.png", dpi=600, bbox_inches="tight")
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
             "mean_paired_delta_burden_hr","probability_delta_below_zero"]].to_csv(
                 OUT/"FIGURE_C_SOURCE.csv",index=False)
    geo=gpd.GeoDataFrame(tr[["GEOID"]].copy(),geometry=gpd.GeoSeries.from_wkt(tr.wkt_geom),crs="EPSG:4326")
    fig,axes=plt.subplots(1,2,figsize=(12,6),constrained_layout=True)
    from matplotlib.colors import TwoSlopeNorm
    from matplotlib.cm import ScalarMappable
    finite=effects.mean_paired_delta_burden_hr.dropna().to_numpy()
    bound=float(np.nanpercentile(np.abs(finite),99))
    norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound)
    for ax,ref in zip(axes,["hospital-first","impact-first"]):
        q=geo.merge(effects[effects.reference_strategy==ref],left_on="GEOID",right_on="tract_id",how="left",validate="one_to_one")
        q.plot(ax=ax,column="mean_paired_delta_burden_hr",cmap="RdBu_r",norm=norm,
               missing_kwds={"color":"#eeeeee"},linewidth=0,rasterized=True)
        ax.set_title(f"Vulnerability-first minus {LABELS[ref]}")
        ax.axis("off")
    fig.colorbar(ScalarMappable(norm=norm,cmap="RdBu_r"),ax=axes,orientation="horizontal",
                 shrink=.7,pad=.02,label="Mean paired tract burden change (h)")
    fig.suptitle("2pc50 paired-mean tract burden change (display clipped at 99th percentile)")
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
