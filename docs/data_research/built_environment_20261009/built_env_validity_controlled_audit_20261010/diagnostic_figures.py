"""Research diagnostics only; publication artwork and class labels are untouched."""
from controlled_audit import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,'axes.linewidth':.6,'lines.linewidth':1.1,'pdf.fonttype':42,'ps.fonttype':42,'figure.facecolor':'white','savefig.facecolor':'white'})
LABELS={'land_use_entropy':'Classified-parcel land-use entropy','building_footprint_coverage':'Building footprint coverage (%)','all_use2014_pre1970_area_share':'2014 observed pre-1970 area (%)'}
MODEL_LABELS={'BE0':'Mix + footprint + 2014 age','BE1_EQUAL':'Mix + footprint','BE2_EQUAL':'Mix + 2014 age','BE3_EQUAL':'Footprint + 2014 age','BE4_EQUAL':'Mix only','BE5_EQUAL':'Footprint only','BE6_EQUAL':'2014 age only','BE7_ACS_EQUAL':'Mix + footprint + ACS age','D_INHERITED':'Building stock + loss rate','EAL_EQUAL':'Expected annual loss score','EAL_INHERITED':'Expected annual loss score','ALR_ONLY_EQUAL':'Loss-rate percentile only','ALR_ONLY_INHERITED':'Loss-rate percentile only','BE8_LOWER_EQUAL':'All missing age newer','BE8_UPPER_EQUAL':'All missing age older','SCAG_TRANSPORT_EQUAL':'Missing land to transport','SCAG_DOMINANT_EQUAL':'Missing land to dominant use'}
def clean(ax):
 ax.spines[['top','right']].set_visible(False);ax.tick_params(length=3,width=.6);ax.set_axisbelow(True)
def letter(ax,c,title):
 ax.set_title(title,pad=9);ax.text(-.09,1.08,c,transform=ax.transAxes,fontweight='bold',fontsize=10,ha='left',va='bottom')
def measurement():
 _,d,_,_=inputs();fig,axes=plt.subplots(2,3,figsize=(185/25.4,157/25.4));fig.subplots_adjust(left=.1,right=.985,bottom=.10,top=.9,wspace=.42,hspace=.64)
 colors=['#0072B2','#009E73','#D55E00'];scaled={c:d[c]*(100 if c!=PHYS[0] else 1) for c in PHYS}
 for i,c in enumerate(PHYS):
  ax=axes[0,i];ax.hist(scaled[c],bins=25,color=colors[i],edgecolor='white',linewidth=.25);ax.set_xlabel(LABELS[c]);ax.set_ylabel('Number of tracts');letter(ax,chr(65+i),'Measurement distribution');clean(ax)
 for i,(a,b) in enumerate(itertools.combinations(PHYS,2)):
  ax=axes[1,i];ax.scatter(scaled[a],scaled[b],s=3,color='#346A86',alpha=.35,edgecolors='none',rasterized=False)
  v=pd.read_csv(OUT/'NONLINEAR_BINNED_RELATIONSHIPS.csv');v=v.loc[v.x.eq(a)&v.y.eq(b)];sx=1 if a==PHYS[0] else 100;sy=1 if b==PHYS[0] else 100
  ax.plot(v.x_median*sx,v.y_median*sy,color='#111111',lw=1.25)
  ax.set_xlabel(LABELS[a]);ax.set_ylabel(LABELS[b]);letter(ax,chr(68+i),f'Pearson r = {pearsonr(d[a],d[b]).statistic:.3f}');clean(ax)
 fig.suptitle('Built-environment measurements on the common 2,287-tract cohort',fontsize=10,y=.985)
 fig.savefig(OUT/'BUILT_ENV_MEASUREMENT_DIAGNOSTICS.pdf');fig.savefig(OUT/'BUILT_ENV_MEASUREMENT_DIAGNOSTICS.png',dpi=600);plt.close(fig)
def ranges(ax,models,frame,col,color,labels=None,offset=0):
 for i,m in enumerate(models):
  v=frame.loc[frame.model.eq(m),col].to_numpy();y=i+offset
  ax.plot([v.min(),v.max()],[y,y],color=color,lw=1.4);ax.scatter([np.median(v)],[y],s=22,color=color,zorder=4);ax.scatter(v,np.full(len(v),y),s=5,color=color,alpha=.45,zorder=3)
 ax.set_yticks(range(len(models)),labels if labels else [MODEL_LABELS.get(m,m) for m in models]);ax.invert_yaxis();clean(ax)
def comparisons():
 r=pd.read_csv(OUT/'BUILT_ENV_ABLATION_RESULTS.csv');sp=pd.read_csv(OUT/'BUILT_ENV_SPATIAL_SENSITIVITY.csv');small=pd.read_csv(OUT/'SMALL_34_GROUP_SENSITIVITY.csv');small=small.loc[small.scope.eq('spatial')]
 with PdfPages(OUT/'CONTROLLED_FEATURE_COMPARISONS.pdf') as pdf:
  fig,axes=plt.subplots(1,2,figsize=(185/25.4,110/25.4));fig.subplots_adjust(left=.28,right=.985,bottom=.20,top=.78,wspace=.65)
  riskmodels=['BE0','ALR_ONLY_EQUAL','EAL_EQUAL'];axes[0].set_ylim(2.6,-.6);axes[1].set_ylim(2.6,-.6)
  for ax,col,source,c in [(axes[0],'ARI_vs_frozen_BE0_seed42',r,'A'),(axes[1],'ARI_all',sp,'B')]:
   labels=['Building stock + loss rate','Loss-rate percentile only','Expected annual loss score']
   ranges(ax,riskmodels,source,col,'#0072B2',offset=-.12,labels=labels)
   inh=['D_INHERITED','ALR_ONLY_INHERITED','EAL_INHERITED'];ranges(ax,inh,source,col,'#D55E00',offset=.12,labels=labels);ax.set_xlim(0,1.02)
   letter(ax,c,'Partition comparison' if c=='A' else 'Spatial sample stability');ax.set_xlabel('ARI versus D, equal domains, seed 42' if c=='A' else 'ARI versus own full-cohort labels')
  for ax in axes:ax.set_ylim(2.6,-.6)
  axes[1].set_yticklabels([])
  fig.legend(handles=[plt.Line2D([],[],color='#0072B2',marker='o',label='Five equal domains'),plt.Line2D([],[],color='#D55E00',marker='o',label='Inherited domain weights')],loc='upper center',bbox_to_anchor=(.5,.98),ncol=2,frameon=False)
  fig.text(.5,.04,'Dots: 20 prescribed cases; larger dot: median; line: observed minimum to maximum.\nCase spread is not a confidence interval. Spatial cases use 17 distinct deletion sets.',ha='center',fontsize=7.5)
  pdf.savefig(fig);fig.savefig(OUT/'CONTROLLED_FEATURE_COMPARISONS_PAGE1.png',dpi=600);plt.close(fig)
  fig,axes=plt.subplots(1,2,figsize=(185/25.4,167/25.4));fig.subplots_adjust(left=.275,right=.985,bottom=.13,top=.8,wspace=.42)
  models=['BE0',*[f'BE{i}_EQUAL' for i in range(1,7)],'BE7_ACS_EQUAL']
  ranges(axes[0],models,r,'ARI_vs_frozen_BE0_seed42','#0072B2')
  for i in range(1,7):
   v=r.loc[r.model.eq(f'BE{i}_FIXED_COORD'),'ARI_vs_frozen_BE0_seed42'];axes[0].plot([v.min(),v.max()],[i+.17,i+.17],color='#D55E00',lw=1.2);axes[0].scatter([v.median()],[i+.17],s=18,color='#D55E00')
  ranges(axes[1],models,sp,'ARI_all','#0072B2');axes[1].set_yticklabels([])
  for ax in axes:ax.set_xlim(0,1.02)
  axes[0].set_xlabel('ARI versus three-feature reference');axes[1].set_xlabel('ARI versus own full-cohort labels')
  letter(axes[0],'A','Removing a physical coordinate');letter(axes[1],'B','Spatial sample stability')
  fig.legend(handles=[plt.Line2D([],[],color='#0072B2',marker='o',label='Physical domain remains 20%'),plt.Line2D([],[],color='#D55E00',marker='o',label='Surviving coordinates retain 6.67% each')],loc='upper center',bbox_to_anchor=(.5,.97),ncol=1,frameon=False)
  fig.text(.5,.035,'Fixed-coordinate deletion reduces the physical-domain budget; other domain weights stay unchanged.\nARI measures partition agreement, not scientific validity or classification accuracy.',ha='center',fontsize=7.5)
  pdf.savefig(fig);fig.savefig(OUT/'CONTROLLED_FEATURE_COMPARISONS_PAGE2.png',dpi=600);plt.close(fig)
  fig,axes=plt.subplots(1,2,figsize=(185/25.4,158/25.4));fig.subplots_adjust(left=.285,right=.985,bottom=.14,top=.88,wspace=.42)
  models=['BE0','SCAG_TRANSPORT_EQUAL','SCAG_DOMINANT_EQUAL','BE8_LOWER_EQUAL','BE8_UPPER_EQUAL','BE7_ACS_EQUAL','BE1_EQUAL']
  ranges(axes[0],models,r,'ARI_vs_frozen_BE0_seed42','#0072B2');axes[0].set_xlim(0,1.02);axes[0].set_xlabel('ARI versus three-feature reference')
  ranges(axes[1],models,small,'purity','#D55E00');axes[1].set_yticklabels([]);axes[1].set_xlim(0,1.02);axes[1].set_xlabel('Purity of class containing original 34 tracts')
  letter(axes[0],'A','Measurement-definition sensitivity');letter(axes[1],'B','Small-group specificity after deletion')
  fig.text(.5,.035,'Missing-land and unknown-age allocations are sensitivity scenarios, not new observed measurements.\nThe original 34 members can remain together while their predicted class absorbs other tracts.',ha='center',fontsize=7.5)
  pdf.savefig(fig);fig.savefig(OUT/'CONTROLLED_FEATURE_COMPARISONS_PAGE3.png',dpi=600);plt.close(fig)
if __name__=='__main__':measurement();comparisons()
