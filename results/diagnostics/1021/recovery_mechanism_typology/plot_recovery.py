"""Three compact, vector, original-response diagnostic figures; no model fitting."""
from support import *
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import fitz

COLORS=["#147f98","#d07734","#7a5899","#55834e","#bd6379","#646464"]
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8,"axes.titlesize":9,
                    "axes.labelsize":8,"xtick.labelsize":7.5,"ytick.labelsize":7.5,
                    "legend.fontsize":7.3,"pdf.fonttype":42,"axes.spines.top":False,
                    "axes.spines.right":False,"axes.titleweight":"bold"})
LABEL="EXPLORATORY RECOVERY ANALYSIS - NOT PUBLICATION FIGURES"


def finish(fig,name):
    fig.suptitle(LABEL,fontsize=8,y=.992)
    fig.savefig(HERE/(name+".pdf"),metadata={"CreationDate":None,"ModDate":None,"Creator":"1021 recovery exploration"})
    fig.savefig(HERE/(name+".png"),dpi=300)
    plt.close(fig)


def main():
    _,f,_,d=inputs()
    src=np.load(HERE/"RECOVERY_MATRICES.npz")
    z=np.load(HERE/"ALL_FITTED_ARRAYS.npz")
    models=[("A-full",2),("A-full",3),("B",2),("B",3)]
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.9))
    fig.subplots_adjust(left=.085,right=.975,top=.91,bottom=.075,wspace=.30,hspace=.45)
    curves={"event_time_hr":src["mean_event_times"]}
    for panel,(ax,(rep,k)) in enumerate(zip(axes.flat,models)):
        labels=z[f"{rep}_k{k}_reference_labels"]
        ax.set_title(f"{'ABCD'[panel]}  {'Trajectories' if rep=='A-full' else 'Mechanisms'}, K={k}",loc="left",pad=8)
        small=ax.inset_axes([.64,.16,.33,.26])
        for c in range(k):
            mask=labels==c
            weight=src["weights"][mask].mean(0)
            mean=src["mean_station_availability"]@weight
            curves[f"{rep}_K{k}_group{c}"]=mean
            ax.step(src["mean_event_times"],mean,where="post",color=COLORS[c],lw=1.4,label=f"Group {c}: {mask.sum():,} tracts")
            small.step(src["mean_event_times"],mean,where="post",color=COLORS[c],lw=.75)
        ax.set(xlim=(0,96),ylim=(-.02,1.03),xlabel="Time after earthquake (h)",ylabel="Mean modeled availability")
        ax.set_xticks([0,24,48,72,96]);ax.grid(axis="y",lw=.4,alpha=.25)
        ax.legend(loc="upper left",bbox_to_anchor=(0,.96),frameon=False)
        small.set(xlim=(0,480),ylim=(0,1.02),xticks=[0,480],yticks=[0,1])
        small.tick_params(labelsize=7,length=2,pad=1)
        small.set_title("Full 480 h",fontsize=7,pad=2,weight="normal")
    finish(fig,"01_ACTUAL_RECOVERY_TRAJECTORIES")
    save("PLOTTED_EXACT_CLASS_MEAN_CURVES.csv",curves)
    fig,axes=plt.subplots(3,2,figsize=(7.2,8.3))
    fig.subplots_adjust(left=.085,right=.975,top=.935,bottom=.09,wspace=.30,hspace=.62)
    x=[29,57,114]
    for panel,(ax,(rep,k)) in enumerate(zip(axes[:2].flat,models)):
        labels=z[f"{rep}_k{k}_reference_labels"]
        ax.set_title(f"{'ABCD'[panel]}  {'Trajectories' if rep=='A-full' else 'Mechanisms'}, K={k}",loc="left",pad=8)
        for c in range(k):
            mask=labels==c
            vals=[d["2pc50__C29_D1__impact-first__B480_mean"][mask].mean(),d.impact__B480_mean[mask].mean(),
                  d["2pc50__C114_D1__impact-first__B480_mean"][mask].mean()]
            ax.plot(x,vals,color=COLORS[c],lw=1.3,label=f"Group {c}")
            ax.scatter([29,114],[vals[0],vals[2]],color=COLORS[c],s=16,zorder=3)
            ax.scatter([57],[vals[1]],edgecolor=COLORS[c],facecolor="white",s=22,zorder=4)
        ax.set(xticks=x,xlabel="Available crews",ylabel="Mean deficit (h)",ylim=(15,80))
        ax.grid(axis="y",lw=.4,alpha=.25);ax.legend(frameon=False,ncol=1)
    scores=pd.read_csv(HERE/"HELD_OUT_ENGINEERING_SCORES.csv")
    means=scores.groupby(["method","outcome"]).MAE.mean()
    display=[("A-full_K","Trajectories",COLORS[0],"o"),("B_K","Mechanisms",COLORS[1],"s"),
             ("quantile_burden_K","Burden quantiles","#737373","^"),("P2_K","P2 reference",COLORS[2],"D")]
    for ax,outcome,title in [(axes[2,0],"Random_deficit_hr","E  Random-priority outcome"),(axes[2,1],"C29_deficit_hr","F  Reduced-crew outcome")]:
        for prefix,label,color,marker in display:
            ks=list(range(2,5)) if prefix=="P2_K" else list(range(2,7))
            ax.plot(ks,[means.loc[(prefix+str(k),outcome)] for k in ks],marker=marker,color=color,label=label,lw=1.1,ms=3)
        for method,color,ls in [("A-full_additive",COLORS[0],":"),("B_additive",COLORS[1],"--")]:
            ax.axhline(means.loc[(method,outcome)],color=color,ls=ls,lw=1.2)
        ax.set_title(title,loc="left",pad=8)
        ax.set(xticks=range(2,7),xlabel="Number of groups",ylabel="Held-out mean absolute error (h)")
        ax.grid(axis="y",lw=.4,alpha=.25)
    handles,labels=axes[2,0].get_legend_handles_labels()
    handles += [Line2D([],[],color=COLORS[0],ls=":"),Line2D([],[],color=COLORS[1],ls="--")]
    labels += ["Continuous trajectories","Continuous mechanisms"]
    fig.legend(handles,labels,loc="lower center",bbox_to_anchor=(.5,.006),ncol=3,frameon=False)
    finish(fig,"02_RESOURCE_AND_WITHHELD_RESPONSES")
    fig,axes=plt.subplots(3,2,figsize=(7.2,8.0))
    fig.subplots_adjust(left=.085,right=.975,top=.935,bottom=.09,wspace=.32,hspace=.57)
    for panel,(ax,(rep,k)) in enumerate(zip(axes[:2].flat,models)):
        labels=z[f"{rep}_k{k}_reference_labels"]
        for c in range(k):
            values=np.sort(f.SOVI_SCORE[labels==c])
            ax.step(values,np.arange(1,len(values)+1)/len(values),where="post",color=COLORS[c],lw=1.3,label=f"Group {c}")
        ax.set_title(f"{'ABCD'[panel]}  {'Trajectories' if rep=='A-full' else 'Mechanisms'}, K={k}",loc="left",pad=8)
        ax.set(xlim=(0,100),ylim=(0,1),xlabel="Social vulnerability score",ylabel="Fraction of tracts")
        ax.legend(frameon=False);ax.grid(axis="y",lw=.4,alpha=.25)
    stability=pd.read_csv(HERE/"MEMBERSHIP_STABILITY_SUMMARY.csv")
    for rep,color,label in [("A-full",COLORS[0],"Trajectories"),("B",COLORS[1],"Mechanisms")]:
        for design,ls in [("random","-"),("spatial","--")]:
            sub=stability[(stability.representation==rep)&(stability.design==design)].groupby("k").mean_full_ARI.mean()
            axes[2,0].plot(sub.index,sub,ls=ls,marker="o",ms=3,color=color,label=label+(" random" if design=="random" else " spatial"))
    axes[2,0].set_title("E  Membership reproducibility",loc="left",pad=8)
    axes[2,0].set(xticks=range(2,7),xlabel="Number of groups",ylabel="Mean adjusted Rand index",ylim=(0,1.03))
    axes[2,0].legend(frameon=False,fontsize=7,loc="lower right")
    social=pd.read_csv(HERE/"SOCIAL_CONTEXT_SCORE_SUMMARY.csv")
    for rep,color,label in [("A-full",COLORS[0],"Trajectories"),("B",COLORS[1],"Mechanisms")]:
        sub=social[(social.representation==rep)&(social.design=="random")].groupby("k").mean_MAE_gain.mean()
        axes[2,1].plot(sub.index,sub,color=color,marker="o",ms=3,label=label)
    axes[2,1].axhline(2,color="#666666",ls=":",lw=1)
    axes[2,1].axhline(0,color="#999999",lw=.6)
    axes[2,1].set_title("F  Social-context information",loc="left",pad=8)
    axes[2,1].set(xticks=range(2,7),xlabel="Number of groups",ylabel="Added-class SOVI MAE gain",ylim=(-.15,2.15))
    axes[2,1].legend(frameon=False)
    finish(fig,"03_VULNERABILITY_AND_REPRODUCIBILITY")
    preview=HERE/"pdf_previews"
    preview.mkdir(exist_ok=True)
    qa=[]
    for path in sorted(HERE.glob("*.pdf")):
        doc=fitz.open(path)
        page=doc[0]
        page.get_pixmap(matrix=fitz.Matrix(150/72,150/72),alpha=False).save(preview/(path.stem+".png"))
        spans=[s for b in page.get_text("dict")["blocks"] if "lines" in b for line in b["lines"] for s in line["spans"] if s["text"].strip()]
        qa.append({"file":path.name,"pages":len(doc),"width_inches":page.rect.width/72,"height_inches":page.rect.height/72,
                   "min_text_points":min(s["size"] for s in spans),"raster_images":len(page.get_images()),
                   "vector_paths":len(page.get_drawings()),"text_inside_page":all(page.rect.contains(fitz.Rect(s["bbox"])) for s in spans)})
    dump("PDF_STRUCTURE_QA.json",qa)


if __name__=="__main__":
    main()
