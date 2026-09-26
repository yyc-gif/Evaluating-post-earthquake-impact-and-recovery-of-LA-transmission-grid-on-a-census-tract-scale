"""Figure-ready views of frozen connectivity-state analysis, July style."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd

import Project_Visualizer as july

if hasattr(sys.stdout,"reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT=Path(__file__).resolve().parent
RESULTS=ROOT/"Formal_Experiment_20260923"/"Formal_Reviewer_Results"
SUITE=ROOT.parent/"LA_Grid_Revised_Suite_20260925"
S3=SUITE/"Stage 3 Output_expanded"
S6=SUITE/"Stage 6 Output_expanded"
july.OUTPUT_ROOT=str(SUITE)
july.apply_publication_style()
july.STAGE6_SHARED_LINE_STYLES["vulnerability-first"]={
    "color":"#a65628","ls":"-","lw_recovery":1.08,
    "lw_topology":.98,"alpha_recovery":.85,"alpha_topology":.82,"zorder":9}
july.STAGE6_RECOVERY_STYLE_CONFIG["vulnerability-first"]={
    "label":"Vulnerability First (Q4)",**july._stage6_line_style("vulnerability-first")}
HAZARDS=["Northridge","SanFernando","LongBeach","2pc50"]
POLICIES=["centrality-first","impact-first","betweenness-first","degree-first",
          "closeness-first","hospital-first","random","vulnerability-first"]

for name in ("FORMAL_CONNECTIVITY_STATE_SUMMARY.csv",
             "FORMAL_CONNECTIVITY_TIME_SERIES.csv",
             "FORMAL_CONNECTIVITY_STRATEGY_EFFECTS.csv"):
    shutil.copy2(RESULTS/name,S6/name)
shutil.copy2(RESULTS/"FORMAL_CONNECTIVITY_TRACT_EFFECTS.parquet",
             S3/"FORMAL_CONNECTIVITY_TRACT_EFFECTS.parquet")
shutil.copy2(RESULTS/"FORMAL_CONNECTIVITY_ROUTE_SOURCE_CROSSTAB.csv",
             S3/"FORMAL_CONNECTIVITY_ROUTE_SOURCE_CROSSTAB.csv")

time=pd.read_csv(RESULTS/"FORMAL_CONNECTIVITY_TIME_SERIES.csv")
summary=pd.read_csv(RESULTS/"FORMAL_CONNECTIVITY_STATE_SUMMARY.csv")
for hazard in HAZARDS:
    d=time[(time.hazard==hazard)&(time.strategy=="hospital-first")]
    assert len(d)==481
    fig,ax=plt.subplots(figsize=july.get_figsize("PANEL_FULLROW",height_cm=7.0))
    for column,label,color in (
        ("total_modeled_service","Total modeled service","#222222"),
        ("active_source_supported_service","Active source","#8172b2"),
        ("one_route_supported_service","One route","#e69f00"),
        ("multiple_route_supported_service","Multiple routes","#009e73")):
        ax.plot(d.time_hr,d[column],label=label,color=color,lw=1.2)
    ax.set_xlim(0,120)
    july.style_axis(ax,title=f"{hazard}: connected service composition, first 120 h",
                    xlabel="Time after earthquake (h)",
                    ylabel="Mean population-weighted modeled service")
    lg=ax.legend(frameon=False,ncol=2);july.format_legend(lg)
    july.save_plot(fig,str(S3),f"vis_stage3_connected_service_composition_{hazard}.png")

fig,ax=plt.subplots(figsize=july.get_figsize("PANEL_FULLROW",height_cm=7.0))
for strategy in POLICIES:
    d=time[(time.hazard=="2pc50")&(time.strategy==strategy)]
    assert len(d)==481
    style=july.STAGE6_RECOVERY_STYLE_CONFIG[strategy]
    ax.plot(d.time_hr,d.multiple_route_supported_service,
            label=style["label"],color=style["color"],ls=style["ls"],lw=1.2)
ax.set_xlim(0,120)
july.style_axis(ax,title="2pc50: multiple-route service, first 120 h",
                xlabel="Time after earthquake (h)",
                ylabel="Mean population-weighted modeled service")
fig.subplots_adjust(right=.57)
lg=ax.legend(frameon=False,ncol=1,loc="center left",bbox_to_anchor=(1.01,.5))
july.format_legend(lg)
july.save_plot(fig,str(S6),"vis_stage6_multiple_route_service_2pc50.png")

for hazard in HAZARDS:
    d=summary[(summary.hazard==hazard)&(summary.strategy.isin(POLICIES))]
    d=d.set_index("strategy").reindex(POLICIES)
    assert len(d)==8 and d.multiple_route_share_mean.notna().all()
    assert np.allclose(d.active_source_share_mean+d.one_route_share_mean+
                       d.multiple_route_share_mean,1,atol=1e-10)
    fig,ax=plt.subplots(figsize=july.get_figsize("PANEL_FULLROW",height_cm=7.0))
    y=np.arange(8)
    ax.barh(y,d.active_source_share_mean,color="#8172b2",label="Active source")
    ax.barh(y,d.one_route_share_mean,left=d.active_source_share_mean,
            color="#e69f00",label="One route")
    ax.barh(y,d.multiple_route_share_mean,
            left=d.active_source_share_mean+d.one_route_share_mean,
            color="#009e73",label="Multiple routes")
    short=["Centrality first","Impact first","Betweenness first","Degree first",
           "Closeness first","Hospital first","Random","Vulnerability first"]
    ax.set_yticks(y,short)
    ax.invert_yaxis()
    ax.set_xlim(0,1)
    july.style_axis(ax,title=f"{hazard}: connected service by route class",
                    xlabel="Mean realization share of connected service")
    fig.subplots_adjust(right=.78)
    lg=ax.legend(frameon=False,ncol=1,loc="center left",bbox_to_anchor=(1.01,.5))
    july.format_legend(lg)
    july.save_plot(fig,str(S6),f"vis_stage6_route_composition_{hazard}.png")

tract=pd.read_parquet(RESULTS/"FORMAL_CONNECTIVITY_TRACT_EFFECTS.parquet")
geo=gpd.read_file(ROOT/"Data/LA_Tracts_With_Population.shp")
geo["tract_id"]=geo.GEOID.astype(str).str.zfill(11)
geo=geo[geo.tract_id.isin(tract.tract_id)].copy()
assert len(geo)==2315
for strategy in ("hospital-first","impact-first","centrality-first","vulnerability-first"):
    d=tract[tract.strategy==strategy].set_index("tract_id")
    assert len(d)==2315
    july.plot_map(geo.copy(),d.one_route_share_pooled,
                  f"2pc50: one-route service, {strategy}",str(S3),
                  f"vis_stage3_one_route_service_share_2pc50_{strategy}.png",
                  cmap="YlOrBr",label="Share of connected service",
                  vmin=0,vmax=1,cmap_low=0,figure_role="PANEL_MAP_TALL")
print("Connectivity state figures exported from frozen analysis.")
