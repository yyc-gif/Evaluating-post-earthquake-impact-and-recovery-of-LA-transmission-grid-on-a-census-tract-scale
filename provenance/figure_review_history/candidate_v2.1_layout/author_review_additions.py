"""Author-requested presentation corrections and an uncurated result browser.

Reads accepted tables and existing vector artwork only. No physical model,
schedule, optimizer, PCA fit, clustering or kernel-density fit is executed.
"""
from pathlib import Path
import hashlib
import io
import re
import subprocess
import textwrap

import fitz
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from PIL import Image

JULY_SHA = "182686868cffe962739804f6bc0ccecaed73d601"
JULY_FIG1_OID = "740a7eeea5f3dfc810f51c2265329c362283609cf64d7f8a9d948312ad1fdf2a"


def export_native(pdf_path):
    with fitz.open(pdf_path) as doc:
        for dpi, suffix in [(600,""),(150,"_preview")]:
            doc[0].get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False).save(pdf_path.with_name(pdf_path.stem+suffix+".png"))


def restore_july_figure1(root, out):
    source = root/"provenance/legacy_outputs/Submission_Package/Figure_1.pdf"
    blob = subprocess.check_output(["git","show",JULY_SHA+":Submission_Package/Figure_1.pdf"],cwd=root)
    assert f"oid sha256:{JULY_FIG1_OID}".encode() in blob
    assert hashlib.sha256(source.read_bytes()).hexdigest()==JULY_FIG1_OID
    dest=out/"Fig01_Revised_Analytical_Framework.pdf"
    dest.write_bytes(source.read_bytes())
    export_native(dest)
    return source


def recolor_native_kde(source, palette):
    """Only PDF stroke/fill colors change; all existing KDE coordinates stay."""
    old=["#607D9E","#B99B4A","#5E8B61","#86AFC0","#92607F"]
    old_rgb=[np.asarray(colors.to_rgb(c)) for c in old]
    replacements=[0]*5
    doc=fitz.open(source)
    pattern=re.compile(rb"([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+(RG|rg)\b")
    def replace(match):
        rgb=np.array([float(match.group(i)) for i in (1,2,3)])
        for idx, target in enumerate(old_rgb):
            if np.allclose(rgb,target,atol=1e-6,rtol=0):
                replacements[idx]+=1
                return (" ".join(f"{x:.9f}" for x in colors.to_rgb(palette[idx]))+" "+match.group(4).decode()).encode()
        return match.group(0)
    for xref in doc[0].get_contents():
        stream=doc.xref_stream(xref)
        doc.update_stream(xref,pattern.sub(replace,stream))
    assert all(n>0 for n in replacements),replacements
    return doc


def build_figure7(root,out,v):
    stage=v.STAGE7
    palette,_=v.get_cluster_palette()
    labels=pd.read_csv(stage/"clusters_labels_final.csv")
    labels=labels[labels.scenario.eq("2pc50")].copy()
    status=pd.read_csv(stage/"stage7_full_domain_tract_status.csv")
    status=status[status.scenario.eq("2pc50")].copy()
    top=pd.read_csv(stage/"stage7_top10_slow_vulnerable_tracts.csv")
    top=top[top.scenario.eq("2pc50")].copy()
    for frame in (labels,status,top):frame["tract_id"]=frame.tract_id.astype(str).str.zfill(11)
    assert len(status)==2315 and len(labels)==2291 and len(top)==10
    geo=v.base.projected_map_data(v.base.map_domain().merge(status,on="tract_id",validate="one_to_one"))
    chosen=geo[geo.tract_id.isin(top.tract_id)]
    assert len(chosen)==10
    # July's bottom map row, using the current harmonized membership/scores.
    fig=plt.figure(figsize=(185/25.4,75/25.4))
    axc=fig.add_axes([9/185,14/75,76/185,59/75])
    axd=fig.add_axes([94/185,14/75,76/185,59/75])
    for cid,color in enumerate(palette[:5],1):
        geo[geo.cluster.eq(cid)].plot(ax=axc,color=color,edgecolor="white",linewidth=.08)
    missing=geo[geo.cluster.isna()]
    missing.plot(ax=axc,color="#eeeeee",edgecolor="#777777",hatch="///",linewidth=.16)
    norm=colors.Normalize(vmin=0,vmax=4)
    cmap=colors.LinearSegmentedColormap.from_list("july_hotspots",["#2C7BB6","#ABD9E9","#FFFFBF","#F46D43","#8B1E3F"])
    geo.plot(column="SlowVulnerable_Hotspot_Score",ax=axd,cmap=cmap,norm=norm,edgecolor="#eeeeee",linewidth=.05,
             missing_kwds={"color":"#eeeeee","edgecolor":"#777777","hatch":"///"})
    for ax in (axc,axd):
        chosen.boundary.plot(ax=ax,color="#222222",linewidth=1.0,zorder=8)
        v.base.style_map_axis(ax)
    cbar_ax=fig.add_axes([172/185,18/75,2.2/185,50/75])
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cbar_ax,ticks=range(5))
    cb.set_label("Hotspot score",fontsize=8.5,labelpad=2);cb.ax.tick_params(labelsize=7.5,length=2,width=.6)
    cb.outline.set_linewidth(.5)
    handles=[Patch(facecolor=c,label=f"C{i}") for i,c in enumerate(palette[:5],1)]
    handles+=[Patch(facecolor="#eeeeee",edgecolor="#777777",hatch="///",label="N/A (24)"),Line2D([0],[0],color="#222222",lw=1,label="Top-10 boundary")]
    fig.legend(handles=handles,ncol=4,loc="lower center",bbox_to_anchor=(47/185,0),frameon=False,fontsize=7.5,
               handlelength=.9,handletextpad=.3,columnspacing=.6,labelspacing=.3)
    fig.legend(handles=[handles[-2],handles[-1]],ncol=1,loc="lower center",bbox_to_anchor=(134/185,0),
               frameon=False,fontsize=7.5,handlelength=1.3,labelspacing=.3)
    buffer=io.BytesIO();fig.savefig(buffer,format="pdf",dpi=600);plt.close(fig)
    maps=fitz.open(stream=buffer.getvalue(),filetype="pdf")
    result=fitz.open();page=result.new_page(width=185/25.4*72,height=267.6/25.4*72)
    mm=72/25.4
    page.insert_font(fontname="LocalArial",fontfile="C:/Windows/Fonts/arial.ttf")
    page.insert_font(fontname="LocalArialBold",fontfile="C:/Windows/Fonts/arialbd.ttf")
    kde_path=stage/"vis_stage7_kde_profiles.pdf"
    with recolor_native_kde(kde_path,palette) as kde:
        page.show_pdf_page(fitz.Rect(0,1*mm,185*mm,(1+110.0824)*mm),kde,0)
    with fitz.open(stage/"vis_stage7_heatmap.pdf") as heat:
        page.show_pdf_page(fitz.Rect(26.5*mm,114*mm,158.5*mm,(114+72.3071)*mm),heat,0)
    page.show_pdf_page(fitz.Rect(0,192*mm,185*mm,267*mm),maps,0)
    for letter,x,y in [("A",1,5),("B",1,118),("C",9,194),("D",94,194)]:
        page.insert_text((x*mm,y*mm),letter,fontname="LocalArialBold",fontsize=9.5)
    for text,x,y in [("Community clusters",15,194),("Hotspot score",100,194)]:
        page.insert_text((x*mm,y*mm),text,fontname="LocalArialBold",fontsize=9.5)
    path=out/"Fig07_Community_Typology_and_Hotspots.pdf"
    result.save(path,garbage=4,deflate=True);result.close();maps.close();export_native(path)
    return [kde_path,stage/"vis_stage7_heatmap.pdf",stage/"stage7_top10_slow_vulnerable_tracts.csv",stage/"stage7_full_domain_tract_status.csv"]


def build_ga(root,out,v):
    folder=v.FORMAL/"Stage 5 Output_expanded"
    scores=pd.read_csv(folder/"INCUMBENT_DIRECT_SCORES_2pc50.csv")
    assert np.allclose(scores.planning_burden_hr,-scores.planning_fitness)
    conv=pd.read_csv(folder/"GA_FIVE_SEED_CONVERGENCE.csv")
    assert not conv.search_improved_incumbent.astype(bool).any()
    incumbent=-float(conv.incumbent_fitness.iloc[0])
    fig=plt.figure(figsize=(185/25.4,155/25.4))
    a=fig.add_axes([.14,.36,.82,.54]);b=fig.add_axes([.14,.095,.82,.16])
    seedcolors=["#1b6b83","#537f68","#a65628","#6b5b95","#8c6d31"]
    for seed,color in zip(sorted(conv.seed.astype(int)),seedcolors):
        h=pd.read_csv(folder/f"GA_HISTORY_2pc50_{seed}.csv")
        a.plot(h.generation,-h.generation_mean,color=color,lw=.9,label=f"Seed {seed}")
    a.axhline(incumbent,color="black",ls="--",lw=1.2,label="Impact-first incumbent")
    a.set_title("A. Genetic algorithm search on planning realizations",loc="left",fontsize=9.5,weight="bold")
    a.set_xlabel("Generation",fontsize=8.5);a.set_ylabel("Mean candidate cumulative service loss (h)\nLower is better",fontsize=8.5)
    a.tick_params(labelsize=7.5);a.grid(alpha=.18,lw=.4)
    a.legend(ncol=3,loc="upper right",frameon=False,fontsize=7.5)
    keys=scores.rule.tolist();x=np.arange(len(keys)+1)
    b.scatter(x,np.r_[scores.planning_burden_hr.to_numpy(),incumbent],s=22,color=[v.STYLE[k][0] for k in keys]+["black"])
    b.axhline(incumbent,color="black",ls="--",lw=.7)
    b.set_xticks(x,[v.POLICY_LABEL[k].replace("-first","\nfirst") for k in keys]+["GA output\nImpact-first"])
    b.set_ylabel("Planning loss (h)",fontsize=8.5);b.tick_params(labelsize=7.5);b.grid(axis="y",alpha=.18,lw=.4)
    b.set_title("B. No seed improved the Impact-first sequence",loc="left",fontsize=9.5,weight="bold")
    path=out/"FigS05_GA_Reproducibility.pdf";fig.savefig(path,dpi=600);plt.close(fig);export_native(path)
    return [folder/"INCUMBENT_DIRECT_SCORES_2pc50.csv",folder/"GA_FIVE_SEED_CONVERGENCE.csv",*[folder/f"GA_HISTORY_2pc50_{s}.csv" for s in sorted(conv.seed.astype(int))]]


METRIC_LABELS={
 "population_weighted_normalized_burden_hr":"Population-weighted cumulative service loss (h)",
 "population_resolved_mass_weighted_burden_hr":"Dependency-mass-weighted cumulative service loss (h)",
 "burden_gini":"Population-weighted tract-loss Gini (unitless)",
 **{f"burden_Q{i}_hr":f"Q{i} population-weighted cumulative service loss (h)" for i in range(1,5)},
 "signed_Q4_minus_Q1_hr":"Signed Q4 minus Q1 cumulative-loss difference (h)",
 "absolute_Q4_minus_Q1_hr":"Absolute Q4 minus Q1 cumulative-loss difference (h)",
 "hospital_mean_normalized_burden_hr":"Hospital-linked tract mean cumulative service loss (h)",
 **{f"population_T{t}_hr":f"Population-weighted time to {t}% service (h)" for t in (50,80,90)},
 "L_self_population_mass_weighted_hr":"Local-damage cumulative service loss (h)",
 "L_threshold_population_mass_weighted_hr":"Threshold-related cumulative service loss (h)",
 "L_source_population_mass_weighted_hr":"Source-path-related cumulative service loss (h)",
 "L_total_population_mass_weighted_hr":"Total dependency-mass-weighted cumulative service loss (h)",
 "L_self_fraction":"Local-damage share of cumulative loss (fraction)",
 "L_threshold_fraction":"Threshold-loss share of cumulative loss (fraction)",
 "L_source_fraction":"Source-path-loss share of cumulative loss (fraction)",
 "task_count":"Damaged repair tasks (count)","makespan_hr":"Last crew task completion time (h)","total_travel_hr":"Total crew travel time (h)"}


def complete_metric_review(root,out,v):
    """Plot every outcome column already saved in the paired summary tables.

    Means/ranges are presentation summaries, not new experiments or metrics.
    Each page retains all policies/cases; raw rows are neither modified nor saved.
    """
    sources=[v.FORMAL/"Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",
             v.EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"]
    # v2.1 module uses the base constant for the formal summary.
    raw=pd.concat([pd.read_parquet(p) for p in sources],ignore_index=True)
    raw=raw[raw.strategy_id.isin(v.STRATEGY_ORDER)&raw.mapping.eq("M1_UTILITY_003")&raw.gate.eq("G1_BASELINE_050")].copy()
    if raw.empty:raise ValueError("Accepted summary selection is empty")
    policies=v.STRATEGY_ORDER
    scenarios=[("Hazard comparison",v.HAZARDS,[v.HAZARD_LABEL[h] for h in v.HAZARDS],"hazard"),
               ("Crew-count sensitivity",["C29_D1","C57_D1","C86_D1","C114_D1"],["29","57","86","114"],"crew"),
               ("Repair-duration sensitivity",["C57_D075","C57_D1","C57_D125","C57_D150"],["0.75×","1×","1.25×","1.50×"],"duration")]
    packet=fitz.open(); rows=[]
    for metric,label in METRIC_LABELS.items():
        fig=plt.figure(figsize=(185/25.4,205/25.4))
        gs=fig.add_gridspec(2,2,left=.22,right=.95,top=.91,bottom=.12,hspace=.46,wspace=.34)
        for j,(title,cases,case_labels,kind) in enumerate(scenarios):
            ax=fig.add_subplot(gs[j//2,j%2]);matrix=np.full((len(policies),len(cases)),np.nan)
            for iy,policy in enumerate(policies):
                for ix,case in enumerate(cases):
                    use=raw[(raw.strategy_id.eq(policy))&((raw.hazard.eq(case)&raw.resource_scenario.eq("C57_D1")) if kind=="hazard" else (raw.hazard.eq("2pc50")&raw.resource_scenario.eq(case)))]
                    if not use.empty:matrix[iy,ix]=pd.to_numeric(use[metric],errors="coerce").mean()
            ax.imshow(np.ma.masked_invalid(matrix),aspect="auto",cmap="Blues")
            ax.set_xticks(range(len(cases)),case_labels,rotation=20 if kind=="hazard" else 0,ha="right" if kind=="hazard" else "center")
            ax.set_yticks(range(len(policies)),[v.POLICY_LABEL[k] for k in policies] if j in (0,2) else [""]*len(policies))
            for iy in range(len(policies)):
                for ix in range(len(cases)):
                    value=matrix[iy,ix]
                    if np.isfinite(value):
                        norm=(value-np.nanmin(matrix))/(np.nanmax(matrix)-np.nanmin(matrix)+1e-15)
                        fmt=f"{value:.3f}" if "Gini" in label or "fraction" in label else f"{value:.2f}"
                        ax.text(ix,iy,fmt,ha="center",va="center",fontsize=7,color="white" if norm>.65 else "#14212a")
                    else:
                        ax.text(ix,iy,"N/A",ha="center",va="center",fontsize=7,color="#777777")
            ax.set_title("ABCD"[j]+". "+title,loc="left",fontsize=9.5,weight="bold");ax.tick_params(labelsize=7.5)
        ax=fig.add_subplot(gs[1,1]);use=raw[raw.hazard.eq("2pc50")&raw.resource_scenario.eq("C57_D1")]
        for iy,policy in enumerate(policies):
            vals=pd.to_numeric(use.loc[use.strategy_id.eq(policy),metric],errors="coerce").dropna()
            if not vals.empty:
                m=vals.mean();lo,hi=vals.quantile([.05,.95]);color=v.STYLE[policy][0]
                ax.errorbar(m,iy,xerr=[[max(0,m-lo)],[max(0,hi-m)]],fmt="o",color=color,ms=3,elinewidth=.75,capsize=2)
        ax.set_yticks(range(len(policies)),[""]*len(policies));ax.invert_yaxis();ax.grid(axis="x",alpha=.18)
        ax.set_title("D. 2pc50 / 57 crews",loc="left",fontsize=9.5,weight="bold");ax.tick_params(labelsize=7.5)
        ax.set_xlabel("Mean and 5th–95th realization range",fontsize=7.5)
        fig.suptitle("\n".join(textwrap.wrap(label,65)),fontsize=10,weight="bold",y=.985)
        fig.text(.22,.045,"Every accepted policy is displayed. Cells are means; missing cases remain NA.\nHazard parameterizations differ. Crew/duration panels show discrete tested cases.",fontsize=7.5)
        buffer=io.BytesIO();fig.savefig(buffer,format="pdf",dpi=600);plt.close(fig)
        with fitz.open(stream=buffer.getvalue(),filetype="pdf") as page:packet.insert_pdf(page)
        rows.append({"source_metric":metric,"reader_facing_label":label,"review_packet":"ALL_SUMMARY_METRICS_REVIEW.pdf","page":len(packet),"cases":"4 hazards; crews 29/57/86/114; duration 0.75/1/1.25/1.50; every distinct policy"})
    packet.save(out/"ALL_SUMMARY_METRICS_REVIEW.pdf",garbage=4,deflate=True);packet.close()
    pd.DataFrame(rows).to_csv(out/"SUMMARY_METRIC_REVIEW_INDEX.csv",index=False)
    allcols=[]
    for col in raw.columns:
        allcols.append({"source_column":col,"role":"outcome" if col in METRIC_LABELS else "identity/domain/configuration metadata",
                        "visual_location":"ALL_SUMMARY_METRICS_REVIEW.pdf page "+str(next(r["page"] for r in rows if r["source_metric"]==col)) if col in METRIC_LABELS else "source table; not disguised as an outcome figure"})
    pd.DataFrame(allcols).to_csv(out/"ALL_SUMMARY_COLUMN_COVERAGE.csv",index=False)
    # Existing analyses remain available, even when absent from the 12 drafts.
    catalog=[]
    for folder in [root/"results/diagnostics",root/"results/capacity",root/"results/vulnerability",v.FORMAL/"Formal_Reviewer_Results",v.FORMAL/"Equity_Amendment"]:
        for path in sorted(folder.glob("*")):
            if path.is_file() and path.suffix in (".csv",".parquet",".json",".md"):
                catalog.append({"source_file":str(path.relative_to(root)).replace("\\","/"),"exists":True,"bytes":path.stat().st_size,
                                "visibility":"Available result; inclusion in the 12-layout set is not a completeness claim"})
    pd.DataFrame(catalog).to_csv(out/"EXISTING_ANALYSIS_CATALOG.csv",index=False)
    return sources,rows
