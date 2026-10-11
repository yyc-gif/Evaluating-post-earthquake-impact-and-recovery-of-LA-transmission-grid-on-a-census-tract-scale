"""Actual-size vector diagnostic figures; no fitted-model or source-data changes."""
from weight_path import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import Normalize
from matplotlib.patches import Patch
plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':.6,'savefig.facecolor':'white','figure.facecolor':'white'})
COL={'BE0':'#235A89','BE1':'#C26724'}
DCOL=['#245A88','#72A5C5','#CF8B3D','#674F89','#368474']
DLABEL=['Recovery / initial service','Grid dependency','Built environment','Social vulnerability','Economic stock / loss']
def panel(ax,letter,title):
 ax.set_title(title,pad=8);ax.text(-.13,1.1,letter,transform=ax.transAxes,fontweight='bold',fontsize=10)
 ax.spines[['top','right']].set_visible(False)
def band(ax,g,xcol,ycol,color,label):
 ag=g.groupby(xcol)[ycol];x=np.array(sorted(g[xcol].unique()));med=ag.median().loc[x];lo=ag.quantile(.05).loc[x];hi=ag.quantile(.95).loc[x]
 ax.errorbar(x,med,yerr=[med-lo,hi-med],fmt='o-',color=color,label=label,lw=1.2,ms=3,capsize=2)
def export(pdf,fig,num):
 pdf.savefig(fig);fig.savefig(OUT/f'WEIGHT_CONSTRUCT_DIAGNOSTICS_PAGE{num}.png',dpi=600);plt.close(fig)
def main():
 summary=pd.read_csv(OUT/'MODEL_SUMMARY.csv');full=pd.read_csv(OUT/'WEIGHT_PATH_RESULTS.csv');pairs=pd.read_csv(OUT/'WEIGHT_PATH_PAIRWISE_COMPARISONS.csv');sp=pd.read_csv(OUT/'WEIGHT_PATH_SPATIAL_STABILITY.csv');dom=pd.read_csv(OUT/'DOMAIN_SEPARATION_SUMMARY.csv');coords=pd.read_csv(OUT/'DOMAIN_DISTANCE_CONTRIBUTIONS.csv');age=pd.read_csv(OUT/'BE0_BE1_CONSTRUCT_COMPARISON.csv').drop_duplicates(['lambda_value','seed']);minor=pd.read_csv(OUT/'MINORITY_34_GROUP_AUDIT.csv');ref=np.load(OUT/'run_records/BE0_L000.npz')['full_s42'];_,d,_,_=inputs()
 with PdfPages(OUT/'WEIGHT_CONSTRUCT_DIAGNOSTICS.pdf') as pdf:
  fig,axs=plt.subplots(2,2,figsize=(185/25.4,163/25.4));fig.subplots_adjust(left=.105,right=.97,bottom=.09,top=.85,hspace=.65,wspace=.32)
  fig.legend([Patch(color=COL[k]) for k in COL],['BE0: entropy, footprint, historical age','BE1: entropy and footprint'],loc='upper center',ncol=1,frameon=False,bbox_to_anchor=(.5,.995))
  for be in COL:
   band(axs[0,0],full.loc[full.be==be],'lambda_value','ARI_vs_BE0_same_seed',COL[be],be)
   q=pairs.loc[(pairs.be==be)&pairs.neighbor];band(axs[0,1],q,'lambda_b','ARI',COL[be],be)
   band(axs[1,0],sp.loc[sp.be==be],'lambda_value','ARI_all',COL[be],be)
   band(axs[1,1],sp.loc[sp.be==be],'lambda_value','ARI_heldout',COL[be],be)
  for ax,l,t in zip(axs.flat,'ABCD',['Partition relative to equal-weight BE0','Changes between adjacent weight settings','Spatial stability: all complete tracts','Spatial stability: held-out tracts']):
   panel(ax,l,t);ax.set(xlabel='Weight-path setting',ylabel='Adjusted Rand index',xticks=LAMBDAS,ylim=(0,1.03));ax.grid(axis='y',alpha=.15)
  export(pdf,fig,1)
  fig,axs=plt.subplots(2,4,figsize=(185/25.4,133/25.4));fig.subplots_adjust(left=.10,right=.99,bottom=.10,top=.87,hspace=.72,wspace=.37)
  fig.text(.5,.975,'Members moving between adjacent weight settings (seed 42)',ha='center',fontsize=10)
  for row,be in enumerate(COL):
   for col,(a,b) in enumerate(zip(LAMBDAS[:-1],LAMBDAS[1:])):
    ax=axs[row,col];ya=np.load(OUT/'run_records'/f'{name(be,a)}.npz')['full_s42'];yb=np.load(OUT/'run_records'/f'{name(be,b)}.npz')['full_s42'];_,aa,_=align(ref,ya,np.ones(len(d),bool));_,bb,_=align(ref,yb,np.ones(len(d),bool));tab=np.array([[((aa==i)&(bb==j)).sum() for j in range(4)] for i in range(4)])
    fractions=tab/tab.sum(axis=1,keepdims=True);ax.pcolormesh(np.arange(5)-.5,np.arange(5)-.5,fractions,cmap='Blues',vmin=0,vmax=1,rasterized=False);ax.set(xlim=(-.5,3.5),ylim=(3.5,-.5),aspect='equal')
    for i,j in itertools.product(range(4),repeat=2):ax.text(j,i,str(tab[i,j]),ha='center',va='center',fontsize=7.5,color='white' if fractions[i,j]>.55 else '#202020')
    ax.set(xticks=range(4),yticks=range(4),xticklabels=['1','2','3','4'],yticklabels=['1','2','3','4'],xlabel='Next-setting class')
    if col==0:ax.set_ylabel(be+' prior-setting class')
    ax.set_title(f'{a:.2f} to {b:.2f}',fontsize=8.5,pad=10);ax.text(-.25,1.15,chr(65+row*4+col),transform=ax.transAxes,fontweight='bold',fontsize=10)
  export(pdf,fig,2)
  fig,axs=plt.subplots(2,2,figsize=(185/25.4,161/25.4));fig.subplots_adjust(left=.105,right=.97,bottom=.09,top=.82,hspace=.67,wspace=.33)
  fig.legend([Patch(color=c) for c in DCOL],DLABEL,loc='upper center',ncol=2,frameon=False,bbox_to_anchor=(.5,.995))
  for j,be in enumerate(COL):
   bottom=np.zeros(5)
   for domain,color in zip(DOMAINS,DCOL):
    vals=[dom.loc[(dom.model==name(be,x))&(dom.domain==domain),'between_fraction_mean'].iloc[0]*100 for x in LAMBDAS]
    axs[0,j].bar(np.arange(5),vals,bottom=bottom,color=color,width=.7);bottom+=vals
   axs[0,j].set(xticks=range(5),xticklabels=[f'{x:.2f}' for x in LAMBDAS],xlabel='Weight-path setting',ylabel='Share of between-class separation (%)',ylim=(0,100))
   panel(axs[0,j],chr(65+j),be+' domain contributions')
   for feature,c in zip(GRID,['#235A89','#C26724','#547B3D','#674F89']):
    g=coords.loc[(coords.be==be)&(coords.feature==feature)];band(axs[1,j],g,'lambda_value','partition_R2',c,feature.replace('Grid_','').replace('Redundancy_HHI','Dependency HHI'))
   axs[1,j].set(xlabel='Weight-path setting',ylabel='Grid variance explained by partition',xticks=LAMBDAS,ylim=(0,1));panel(axs[1,j],chr(67+j),be+' grid variation')
   axs[1,j].legend(loc='upper left',frameon=False,handlelength=1.2,labelspacing=.25)
  export(pdf,fig,3)
  fig,axs=plt.subplots(2,2,figsize=(185/25.4,155/25.4));fig.subplots_adjust(left=.105,right=.97,bottom=.09,top=.89,hspace=.70,wspace=.33)
  band(axs[0,0],age,'lambda_value','aligned_reassigned_n','#235A89','');axs[0,0].set(ylabel='Reassigned tracts',xlabel='Weight-path setting',xticks=LAMBDAS,ylim=(0,None));panel(axs[0,0],'A','Age inclusion versus exclusion')
  band(axs[0,1],age,'lambda_value','ARI','#235A89','');axs[0,1].set(ylabel='Adjusted Rand index',xlabel='Weight-path setting',xticks=LAMBDAS,ylim=(0,1.03));panel(axs[0,1],'B','Same-weight BE0 versus BE1')
  for be in COL:
   g=minor.loc[(minor.be==be)&(minor.scope=='spatial')];band(axs[1,0],g,'lambda_value','purity',COL[be],be)
   # Minimum is shown explicitly; median alone masks the sparse-support case.
   gg=g.groupby('lambda_value').purity.min();axs[1,0].plot(gg.index,gg.values,':',color=COL[be],lw=1)
  axs[1,0].set(xlabel='Weight-path setting',ylabel='Original 34-tract group purity',xticks=LAMBDAS,ylim=(0,1.03));panel(axs[1,0],'C','Minority-group specificity');axs[1,0].legend(frameon=False,loc='center left')
  axs[1,1].scatter(d.SOVI_SCORE,d.B_480_hr,s=2,color='#235A89',alpha=.23,rasterized=False)
  q=pd.qcut(d.SOVI_SCORE,10,duplicates='drop');med=d.groupby(q,observed=True)[['SOVI_SCORE','B_480_hr']].median();axs[1,1].plot(med.SOVI_SCORE,med.B_480_hr,color='#C26724',lw=1.4,label='Within-decile median')
  axs[1,1].set(xlabel='Social Vulnerability Score',ylabel='Cumulative modeled service loss (h)');panel(axs[1,1],'D','Continuous tract-level relationship');axs[1,1].legend(frameon=False,loc='upper right',handlelength=1.2)
  export(pdf,fig,4)
 (OUT/'DIAGNOSTIC_FIGURE_CAPTIONS.md').write_text('''# Diagnostic captions

Page 1. Predefined weight-path comparison for BE0 and BE1 at fixed k=4. Setting0 is equal-five-domain weighting; setting1 is inherited weighting, with the three registered intermediate settings. A compares each model with same-seed equal BE0; B compares neighboring settings within the same physical specification. C/D compare each spatial prediction with its own same-seed full-cohort baseline. Points are medians and bars5th-95th empirical percentiles over20 fixed cases, not confidence intervals. The20 spatial cases contain17 distinct deletion sets.

Page 2. Seed42 contingency counts across each adjacent weight step. Columns and rows are separately aligned to the BE0 seed42 reference by full-cohort overlap for display only; spatial label matching is a separate training-only procedure. Color indicates the fraction of the preceding class going to a column, from0 to1; printed values are tract counts. These transitions show changes of specification, not observed community migration or classification error.

Page 3. Domain contributions are BSS_domain/BSS_all in the standardized weighted space, averaged over20 seeds; they are not nominal domain weights or causal importance. BSS=sum_c n_c||mean_c-mean_all||^2; TSS=BSS+WSS. Bottom panels show BSS_feature/TSS_feature for grid coordinates. Recovery and social variables are fitting inputs; between-class differences do not independently validate the partition.

Page 4. A/B compare age retention and deletion at identical parent-domain weights; deleting age reallocates the physical budget to entropy and footprint. Points/ranges are20-seed medians and5th-95th empirical percentiles. C traces the original34-member reference set after spatial prediction: purity differs from retention; dotted curves are the observed minimum case. D uses the same2287 tract measurements without cluster labels; the orange line is the median within each SOVI decile, not a fitted recovery model. Hours are normalized service deficit integrated over0-480h under the established2pc50/C57/D1 direct-community outputs.
''',encoding='utf-8')
 print('Wrote four vector diagnostic pages and600-dpi previews',flush=True)
if __name__=='__main__':main()
