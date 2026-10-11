"""Scientific diagnostics from completed tables only, no fits or data changes."""
from common import *
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter

MM=1/25.4
DOMAIN_COLORS={'Recovery':'#0072B2','Grid':'#D55E00','Physical':'#009E73','Social':'#CC79A7','Stock':'#E69F00','ALR':'#56B4E9'}
CLASS_COLORS=['#0072B2','#D55E00','#009E73','#6F6F6F']
SCHEME_COLORS=['#202020','#0072B2','#D55E00','#009E73','#8B5B25']
plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,'axes.linewidth':.6,'pdf.fonttype':42,'savefig.facecolor':'white','figure.facecolor':'white'})
def read(n):return pd.read_csv(lp(OUT/n))
def letter(ax,s):ax.text(-.11,1.055,s,transform=ax.transAxes,ha='left',va='bottom',weight='bold',fontsize=10)
def export(fig,n):
    fig.savefig(lp(OUT/(n+'.pdf')));fig.savefig(lp(OUT/(n+'.png')),dpi=600)
    plt.close(fig)

def transitions():
    t=read('CORE3_WEIGHT_CLASS_TRANSITIONS.csv');fig,axes=plt.subplots(2,2,figsize=(185*MM,151*MM));fig.subplots_adjust(left=.13,right=.84,bottom=.10,top=.91,wspace=.37,hspace=.50)
    for ax,w,lab in zip(axes.flat,['W2','W3','W4','W5'],'ABCD'):
        q=t.loc[t.scheme.eq(w)&t.seed.eq(42)];a=np.zeros((4,4));counts=np.zeros((4,4),int)
        for _,r in q.iterrows():a[int(r.W1_seed42_display_class),int(r.scheme_W1_overlap_display_class)]=r.fraction_of_W1_class;counts[int(r.W1_seed42_display_class),int(r.scheme_W1_overlap_display_class)]=r.n
        im=ax.imshow(a,vmin=0,vmax=1,cmap='Blues',aspect='equal');ax.set_xticks(range(4),[str(k) for k in range(4)]);ax.set_yticks(range(4),[str(k) for k in range(4)]);ax.set_xlabel('Weight-scheme class (overlap display ID)');ax.set_ylabel('W1 reference class');ax.set_title(w+' versus W1',pad=8);letter(ax,lab)
        for i,j in np.ndindex(a.shape):ax.text(j,i,f'{counts[i,j]}\n{100*a[i,j]:.1f}%',ha='center',va='center',fontsize=7.5,color='white' if a[i,j]>.65 else '#222222')
    cax=fig.add_axes([.885,.28,.018,.46]);cb=fig.colorbar(im,cax=cax);cb.set_label('Fraction of W1 class');export(fig,'FIG_CORE3_WEIGHT_CLASS_TRANSITIONS')

def domains():
    q=read('CORE3_DOMAIN_SEPARATION.csv');fig,axes=plt.subplots(2,1,figsize=(185*MM,148*MM),gridspec_kw={'height_ratios':[1.2,1]});fig.subplots_adjust(left=.15,right=.88,bottom=.15,top=.85,hspace=.55)
    ax=axes[0];left=np.zeros(5);right=np.zeros(5)
    for d in DOMAIN_COLUMNS:
        nominal=np.array([dict(zip(DOMAIN_COLUMNS,WEIGHTS[w]))[d] for w in WEIGHTS]);observed=np.array([q.loc[q.scheme.eq(w)&q.domain.eq(d),'domain_between_fraction'].median() for w in WEIGHTS]);ax.barh(np.arange(5)-.18,nominal,left=left,height=.30,color=DOMAIN_COLORS[d]);ax.barh(np.arange(5)+.18,observed,left=right,height=.30,color=DOMAIN_COLORS[d]);left+=nominal;right+=observed
    ax.set_yticks(range(5),list(WEIGHTS));ax.invert_yaxis();ax.set_xlim(0,1);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.set_xlabel('Share of nominal budget / observed class separation');ax.set_title('Nominal budget (upper) and observed separation (lower)',pad=8);letter(ax,'A')
    fig.legend([Patch(color=DOMAIN_COLORS[d]) for d in DOMAIN_COLUMNS],list(DOMAIN_COLUMNS),loc='upper center',bbox_to_anchor=(.52,.99),ncol=3,frameon=False,columnspacing=1.5,handlelength=1.5)
    ax=axes[1];a=np.array([[q.loc[q.scheme.eq(w)&q.domain.eq(d),'domain_explained_fraction'].median() for d in DOMAIN_COLUMNS] for w in WEIGHTS]);im=ax.imshow(a,vmin=0,vmax=1,cmap='YlGnBu',aspect='auto');ax.set_yticks(range(5),list(WEIGHTS));ax.set_xticks(range(6),list(DOMAIN_COLUMNS));ax.set_title('Fraction of each domain’s variance explained by classes',pad=8);letter(ax,'B')
    for i,j in np.ndindex(a.shape):ax.text(j,i,f'{100*a[i,j]:.1f}%',ha='center',va='center',fontsize=8,color='white' if a[i,j]>.58 else '#202020')
    cax=fig.add_axes([.925,.15,.015,.26]);fig.colorbar(im,cax=cax).set_label('Domain BSS / domain TSS');export(fig,'FIG_CORE3_DOMAIN_INFLUENCE')

def economy():
    p=read('CORE3_CLASS_PROFILES.csv');fig,axes=plt.subplots(1,2,figsize=(185*MM,104*MM));fig.subplots_adjust(left=.12,right=.96,bottom=.18,top=.80,wspace=.42)
    for ax,c,lab,ylabel,scale in [(axes[0],'NRI_BUILDVALUE','A','Median building value ($ million)',1e6),(axes[1],'ALR_NPCTL','B','Mean multi-hazard loss-rate percentile',1)]:
        for k,color in enumerate(CLASS_COLORS):
            xs=[];ys=[];lo=[];hi=[]
            for i,w in enumerate(WEIGHTS):
                v=p.loc[p.scheme.eq(w)&p.W1_seed42_display_class.eq(k)&p.feature.eq(c),'median' if c=='NRI_BUILDVALUE' else 'mean']/scale;xs.append(i+(k-1.5)*.105);ys.append(v.median());lo.append(v.median()-v.min());hi.append(v.max()-v.median())
            ax.errorbar(xs,ys,yerr=np.array([lo,hi]),fmt='o',markersize=4,color=color,linewidth=.85,capsize=2,label=f'Reference class {k}')
        ax.set_xticks(range(5),list(WEIGHTS));ax.set_ylabel(ylabel);ax.set_title('Economic stock' if c=='NRI_BUILDVALUE' else 'Expected-loss propensity',pad=10);ax.set_ylim(0,1000 if c=='NRI_BUILDVALUE' else 100);letter(ax,lab)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.52,.99),ncol=2,frameon=False,columnspacing=2);export(fig,'FIG_CORE3_STOCK_ALR_EFFECTS')

def minority():
    q=read('CORE3_34TRACT_AUDIT.csv');s=q.loc[q.scope.eq('spatial_all')];fig,axes=plt.subplots(2,2,figsize=(185*MM,156*MM),gridspec_kw={'height_ratios':[1,1.1]});fig.subplots_adjust(left=.12,right=.96,bottom=.16,top=.93,wspace=.38,hspace=.55)
    for ax,c,lab,title in [(axes[0,0],'retention','A','Original-member retention'),(axes[0,1],'purity','B','Specificity of the train-aligned class')]:
        for i,w in enumerate(WEIGHTS):
            g=s.loc[s.scheme.eq(w)].sort_values('seed');jitter=np.linspace(-.12,.12,len(g));ax.scatter(i+jitter,g[c],s=11,color=SCHEME_COLORS[i],alpha=.65,edgecolors='none');ax.scatter([i],[g[c].median()],s=26,color=SCHEME_COLORS[i],marker='D')
        ax.set_xticks(range(5),list(WEIGHTS));ax.set_ylim(-.06,1.06);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_title(title,pad=9);letter(ax,lab)
    ax=axes[1,0];g=s.loc[s.seed.eq(54)].set_index('scheme');members=g.loc[list(WEIGHTS),'largest_destination_original_members'].to_numpy();total=g.loc[list(WEIGHTS),'largest_destination_total_n'].to_numpy();ax.barh(range(5),members,color='#0072B2',height=.58,label='Original subgroup');ax.barh(range(5),total-members,left=members,color='#D5D8DA',height=.58,label='Other tracts');ax.set_yticks(range(5),list(WEIGHTS));ax.invert_yaxis();ax.set_xlim(0,980);ax.set_xlabel('Tracts in largest destination');ax.set_title('Sparse-support case: largest destination',pad=9);letter(ax,'C')
    for i,(a,b) in enumerate(zip(members,total)):ax.text(b+15,i,f'{a}/{b}',va='center',fontsize=7.5)
    handles,labels=ax.get_legend_handles_labels();fig.legend(handles,labels,loc='lower left',bbox_to_anchor=(.15,.025),ncol=2,frameon=False,fontsize=7.5,handlelength=1)
    ax=axes[1,1];g=s.loc[s.seed.eq(54)].set_index('scheme');counts=g.loc[list(WEIGHTS),'number_of_destination_classes'];ax.bar(range(5),counts,color=SCHEME_COLORS,width=.55);ax.set_xticks(range(5),list(WEIGHTS));ax.set_ylim(0,4);ax.set_yticks(range(5));ax.set_ylabel('Classes containing subgroup members');ax.set_title('Sparse-support case: subgroup splitting',pad=9);letter(ax,'D');export(fig,'FIG_CORE3_MINORITY_GROUP_STABILITY')

if __name__=='__main__':
    transitions();domains();economy();minority()
    textfile('DIAGNOSTIC_FIGURE_CAPTIONS.md','''# Diagnostic figure captions

Class transitions: W2-W5 versus W1 at seed42, using the exact same 2,287 GEOIDs. Rows are W1 reference classes; columns use maximum-overlap display IDs. Cells show tract count and fraction of the W1 source class. Display matching is descriptive and does not make categories scientifically equivalent. All20 same-seed comparisons and raw transition tables are separately reported.

Domain influence: A compares nominal squared-distance budgets with median observed domain_BSS/total_BSS over20 full-cohort fits. Stacked medians may differ from unity only through rounding or joint-summary effects. B shows median domain_BSS/domain_TSS. TSS=BSS+WSS uses unweighted tract observations after standardization and the registered coordinate factors; nominal importance and observed separation are different. These are descriptive variance contributions, not causal effects or weight-quality scores.

Stock/ALR effects: Points are medians across20 seeds of class-level median archived building value (A) or mean unadjusted ALR percentile (B); whiskers span the minimum and maximum across seeds, not confidence intervals. Classes use W1 seed42 overlap display IDs. Monetary values are shown in source dollars divided by one million solely for display. ALR is expected-loss propensity, not pure hazard. Changed class profiles reflect changed membership and weights, not changed tract measurements.

Minority stability: A/B show20 spatial-deletion cases per scheme, with empirical observations and the median diamond. They are17 distinct deletion sets, not20 independent validation replicates. Primary retention and purity follow the own-full dominant subgroup class through training-only overlap matching. C/D describe the fixed seed54 deletion of blocks7:-24 and7:-23, leaving four of the34 reference members in training. C shows the largest observed original-member destination and its full predicted class size; it is a descriptive count, not a new held-out rematching rule. D shows how many destination classes contain the34 original members. All members have predictions; zero aligned retention means failure to retain the matched class, not deletion of tract records. The exact raw destination counts and training-supported flags remain in the audit table.
''')
    log('Four 185-mm diagnostic PDFs and 600-dpi PNGs generated from completed tables only.')
