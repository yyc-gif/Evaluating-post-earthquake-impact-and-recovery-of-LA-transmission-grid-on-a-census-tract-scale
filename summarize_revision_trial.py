"""Read completed small-trial files; summarize observed effects without simulation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd

ROOT=Path(__file__).resolve().parent
TRIAL=ROOT/"Revised_Entry_Trial_20260922"
OFF=TRIAL/"Offline_Mapping_Gate"
RESULT=TRIAL/"TRIAL_RESULTS"
RESULT.mkdir(exist_ok=True)

summary=pd.read_csv(OFF/"SUMMARY.csv",dtype={"realization_id":str,"strategy_id":str})
burden=pd.read_parquet(OFF/"TRACT_BURDEN.parquet")
effects=pd.read_parquet(OFF/"TRACT_EFFECTS.parquet")
status=pd.read_csv(TRIAL/"Stage 1 Output_expanded"/"PHYSICAL_SAMPLE_MANIFEST.csv")
kpis=pd.read_csv(TRIAL/"Stage 6 Output_expanded"/"TRIAL_SYSTEM_KPIS.csv")
native=summary[summary.comparison_domain.eq("mapping_native_domain")].copy()
base=native[native.gate.eq("G1_BASELINE_050")&native.mapping.isin(["M0_JULY_003","M1_UTILITY_003"])]
keys=["realization_id","strategy_id"]
compare=base.pivot(index=keys,columns="mapping",values=[
    "population_T50_hr","population_T80_hr",
    "population_weighted_normalized_burden_hr",
    "population_resolved_mass_weighted_burden_hr",
    "hospital_mean_normalized_burden_hr",
    "signed_Q4_minus_Q1_hr","burden_gini"])
compare.columns=[c+"__"+m for c,m in compare.columns]
for metric in ["population_T50_hr","population_T80_hr","population_weighted_normalized_burden_hr",
               "population_resolved_mass_weighted_burden_hr","hospital_mean_normalized_burden_hr",
               "signed_Q4_minus_Q1_hr","burden_gini"]:
    compare[metric+"__M1_minus_M0"]=compare[metric+"__M1_UTILITY_003"]-compare[metric+"__M0_JULY_003"]
compare.reset_index().to_csv(RESULT/"PAIRED_MAPPING_EFFECTS.csv",index=False)

losscols=["L_self_population_mass_weighted_hr","L_threshold_population_mass_weighted_hr",
          "L_source_population_mass_weighted_hr","L_total_population_mass_weighted_hr"]
prod=native[native.mapping.eq("M1_UTILITY_003")&native.gate.eq("G1_BASELINE_050")].copy()
loss=prod.groupby("strategy_id")[losscols].mean()
for col in losscols[:3]:
    loss[col.replace("_population_mass_weighted_hr","_share")]=loss[col]/loss[losscols[-1]]
loss.to_csv(RESULT/"GATE_LOSS_DECOMPOSITION_TRIAL.csv")

comparison_metrics=["population_T80_hr","population_weighted_normalized_burden_hr",
                    "population_resolved_mass_weighted_burden_hr","hospital_mean_normalized_burden_hr",
                    "burden_Q1_hr","burden_Q2_hr","burden_Q3_hr","burden_Q4_hr",
                    "signed_Q4_minus_Q1_hr","absolute_Q4_minus_Q1_hr","burden_gini"]
slice=prod.groupby("strategy_id")[comparison_metrics].agg(["mean","std"])
slice.columns=[str(a)+"__"+b for a,b in slice.columns]
slice.to_csv(RESULT/"SMALL_TRIAL_STRATEGY_DESCRIPTIVES.csv")

# Each tract has an explicit geography and population in the frozen utility table.
geo=pd.read_csv(ROOT/"R1_Comment1_July92_Utility_Constraint"/"MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv",
                dtype={"tract_id":str}).set_index("tract_id")
q=burden[(burden.mapping.isin(["M0_JULY_003","M1_UTILITY_003"]))&burden.gate.eq("G1_BASELINE_050")]
t=q.pivot_table(index=["realization_id","strategy_id","tract_id"],columns="mapping",
                values="normalized_burden_hr",dropna=False)
t["M1_minus_M0_hr"]=t["M1_UTILITY_003"]-t["M0_JULY_003"]
t=t.reset_index().merge(geo[["population","SOVI_quartile"]],left_on="tract_id",right_index=True,validate="many_to_one")
t.to_parquet(RESULT/"TRACT_MAPPING_SHIFTS.parquet",index=False)
t.groupby("strategy_id").agg(tracts_compared=("M1_minus_M0_hr","count"),
    mean_absolute_shift_hr=("M1_minus_M0_hr",lambda x:float(x.abs().mean())),
    median_absolute_shift_hr=("M1_minus_M0_hr",lambda x:float(x.abs().median())),
    maximum_absolute_shift_hr=("M1_minus_M0_hr",lambda x:float(x.abs().max()))).to_csv(RESULT/"TRACT_SHIFT_SUMMARY.csv")

# This figures are model trial outputs, not manuscript-ready inferences.
fig,ax=plt.subplots(figsize=(9,4))
ordered=loss.reindex(["unconstrained","hospital-first","impact-first","direct-community","random"]).dropna(how="all")
bottom=np.zeros(len(ordered))
for col,color in zip(losscols[:3],["#6b7280","#e7a23b","#4169a8"]):
    v=ordered[col].to_numpy(float);ax.bar(ordered.index,v,bottom=bottom,label=col.split("_")[1],color=color);bottom+=v
ax.set(ylabel="Population x resolved-mass normalized loss (hours)",title="2pc50 / C57 / 3 evaluation samples: gate loss components")
ax.tick_params(axis="x",rotation=25);ax.legend();fig.tight_layout();fig.savefig(RESULT/"GATE_LOSS_COMPONENTS.png",dpi=180);plt.close(fig)

g=pd.read_csv(ROOT/"Data"/"Tracts_Within_Expanded_Area.csv",dtype={"GEOID":str})
geo_map=gpd.GeoDataFrame(g[["GEOID"]],geometry=gpd.GeoSeries.from_wkt(g.wkt_geom,crs=4326)).to_crs(3310)
h=t[t.strategy_id.eq("hospital-first")].groupby("tract_id").M1_minus_M0_hr.mean()
geo_map["mapping_burden_shift_hr"]=geo_map.GEOID.str.lstrip("0").map(h.rename(index=lambda x:x.lstrip("0")))
scale=float(geo_map.mapping_burden_shift_hr.abs().max())
fig,ax=plt.subplots(figsize=(9,7))
geo_map.plot(column="mapping_burden_shift_hr",ax=ax,cmap="RdBu_r",vmin=-scale,vmax=scale,
             legend=True,missing_kwds={"color":"#ddd"})
ax.set_axis_off();ax.set_title("Hospital-first: utility minus July burden (3-sample trial)")
fig.tight_layout();fig.savefig(RESULT/"MAPPING_BURDEN_SHIFT.png",dpi=180);plt.close(fig)

out=dict(status="SMALL_REAL_DATA_TRIAL_NOT_FINAL_SCIENCE",physical_realizations=int(status.shape[0]),
         planning_realizations=int(status.split.eq("planning").sum()),evaluation_realizations=int(status.split.eq("evaluation").sum()),
         evaluation_strategy_archives=int(pd.read_csv(TRIAL/"SAVED_EVENT_INDEX.csv").shape[0]),
         mapping_results=int(native.shape[0]),common_320_summaries=int(summary.comparison_domain.eq("SCE_common_positive_support").sum()),
         stage7_tracts=int(pd.read_csv(TRIAL/"Stage 7 Output_expanded"/"clusters_labels_final.csv").shape[0]))
(RESULT/"RESULT_COUNTS.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
