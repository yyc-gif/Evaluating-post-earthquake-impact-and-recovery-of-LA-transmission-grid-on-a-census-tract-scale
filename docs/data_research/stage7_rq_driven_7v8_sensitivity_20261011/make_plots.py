"""Matplotlib diagnostic figures, never formal figure outputs."""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import fitz

from common import OUT, SPEC, dump, frame, lp, sha

NOTICE = 'AUTHOR REVIEW \u2014 NOT FORMAL STAGE 7'
COLORS = ['#0072B2','#D55E00','#009E73','#CC79A7']
SPECS = ['A','B','A-minus-Init','B-minus-Init','B-equal-RQ3']
DISPLAY = ['A','B','A - Init','B - Init','B equal RQ3']
LABELS = {'Init_Supply':'Initial service','Grid_Impact':'Grid impact','Redundancy_HHI':'Dependency HHI',
    'B_480_hr':'Deficit (h)','Delta_B_logistics':'Logistics increment (h)', 'SOVI_SCORE':'SOVI',
    'log1p_Population':'Log population','log1p_BUILDVALUE':'Log assets'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
    'axes.labelsize':9,'xtick.labelsize':8.5,'ytick.labelsize':8.5,'legend.fontsize':8.5,
    'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
RECORDS=[]


def title(fig, subtitle):
    fig.suptitle(NOTICE+'\n'+subtitle, fontsize=10, y=.995)


def finish(fig,name):
    folder=OUT/'figures'
    folder.mkdir(exist_ok=True)
    pdf=lp(folder/(name+'.pdf'))
    png=lp(folder/(name+'.png'))
    fig.savefig(pdf,metadata={'Creator':'Matplotlib controlled diagnostic script','Title':NOTICE},dpi=300)
    fig.savefig(png,dpi=300)
    plt.close(fig)
    # Render every complete PDF at 150 dpi at the actual 7.2-inch publication width.
    doc=fitz.open(pdf)
    assert len(doc)==1
    page=doc[0]
    text=page.get_text()
    assert 'AUTHOR REVIEW' in text and 'NOT FORMAL STAGE 7' in text
    clipped=[]
    fonts=[]
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for span in line['spans']:
                fonts.append(span['size'])
                box=fitz.Rect(span['bbox'])
                if not page.rect.contains(box):
                    clipped.append(span['text'])
    assert not clipped,clipped
    image=lp(folder/(name+'_publication_review.png'))
    pix=page.get_pixmap(matrix=fitz.Matrix(150/72,150/72),alpha=False)
    pix.save(image)
    RECORDS.append(dict(file='figures/'+name+'.pdf',sha256=sha(pdf),pages=1,
        width_inches=page.rect.width/72,height_inches=page.rect.height/72,
        min_pdf_font_points=min(fonts),text_within_page_bounds=True,
        review_render='figures/'+name+'_publication_review.png'))
    doc.close()


def assets(d):
    fig,ax=plt.subplots(2,2,figsize=(7.2,6.4))
    title(fig,'Building-asset stock and incremental information | positive-population cohort')
    ax[0,0].hist(d.BUILDVALUE/1e9,bins=45,color=COLORS[0],edgecolor='white',linewidth=.3)
    ax[0,0].set(xlabel='Building stock (billion 2022 USD)',ylabel='Tracts',title='(A) Original monetary values')
    ax[0,0].set_yscale('log')
    ax[0,1].hist(d.log1p_BUILDVALUE,bins=40,color=COLORS[2],edgecolor='white',linewidth=.3)
    ax[0,1].set(xlabel='ln(1 + building stock in USD)',ylabel='Tracts',title='(B) Registered log transformation')
    scatter=ax[1,0].scatter(d.log1p_Population,d.log1p_BUILDVALUE,c=d.SOVI_SCORE,
        cmap='viridis',s=6,alpha=.65,rasterized=True)
    extra=d.additional_zero_housing_positive_population
    ax[1,0].scatter(d.loc[extra,'log1p_Population'],d.loc[extra,'log1p_BUILDVALUE'],
        facecolors='none',edgecolors='black',s=34,linewidths=.75,label='8 added tracts')
    ax[1,0].set(xlabel='ln(1 + population)',ylabel='ln(1 + building stock in USD)',title='(C) People, assets and SOVI')
    ax[1,0].legend(loc='upper left',frameon=False,markerscale=.8)
    cb=fig.colorbar(scatter,ax=ax[1,0],fraction=.048,pad=.04)
    cb.set_label('SOVI (0-100)')
    info=frame('BUILDVALUE_INCREMENTAL_INFORMATION.csv')
    info=info[(info.cohort=='positive_population')&(info.kind=='pairwise')]
    cols=[c for c in SPEC['specifications']['A']]
    y=np.arange(len(cols))
    values=info.set_index('predictor').reindex(cols)
    ax[1,1].barh(y-.15,values.pearson,height=.3,color=COLORS[0],label='Pearson')
    ax[1,1].barh(y+.15,values.spearman,height=.3,color=COLORS[1],label='Spearman')
    ax[1,1].set(yticks=y,yticklabels=[LABELS[c] for c in cols],xlim=(-1,1),
        xlabel='Association with log assets',title='(D) Same-cohort overlap')
    ax[1,1].set_yticklabels(['Initial service','Grid impact','HHI','B (h)','Delta B (h)','SOVI','Log population'])
    ax[1,1].axvline(0,color='.5',lw=.6)
    ax[1,1].legend(loc='lower right',frameon=False)
    fig.subplots_adjust(top=.88,bottom=.08,left=.09,right=.97,wspace=.68,hspace=.45)
    finish(fig,'BUILDVALUE_ASSET_INFORMATION')


def initial(d):
    fig,ax=plt.subplots(2,2,figsize=(7.2,6.1))
    title(fig,'Initial-service sparsity, distance leverage and rare modeled states')
    a=d.Init_Supply
    ax[0,0].hist(a*100,bins=45,color=COLORS[0],edgecolor='white',linewidth=.3)
    ax[0,0].set_yscale('log')
    ax[0,0].set(xlabel='Initial service availability (%)',ylabel='Tracts (log scale)',
        title=f'(A) {int(a.eq(0).sum()):,} exact zeros / {len(a):,}')
    z=(a-a.mean())/a.std(ddof=0)
    ax[0,1].hist(z,bins=45,color=COLORS[1],edgecolor='white',linewidth=.3)
    ax[0,1].set_yscale('log')
    ax[0,1].set(xlabel='Cohort-standardized initial service',ylabel='Tracts (log scale)',title='(B) Standardized tail')
    leverage=frame('INIT_SUPPLY_DISTANCE_LEVERAGE.csv')
    lev=leverage[(leverage.cohort=='positive_population')&(leverage.subset=='Init_P99')].iloc[0]
    ax[0,1].text(.98,.96,f'Top 1%: {int(lev.n)} tracts\n{lev.fraction_of_Init_total_SS:.1%} of Init SS',
        transform=ax[0,1].transAxes,ha='right',va='top',fontsize=9)
    c=frame('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv')
    c=c[(c.cohort=='positive_population')&(c.coordinate=='Init_Supply')]
    for spec,color in [('A',COLORS[0]),('B',COLORS[1])]:
        for k in SPEC['k_values']:
            v=c[(c.specification==spec)&(c.k==k)].fraction_of_between*100
            ax[1,0].plot(k,v.median(),'o',color=color)
            ax[1,0].vlines(k,v.min(),v.max(),color=color)
        grouped=c[c.specification==spec].groupby('k').fraction_of_between.median()*100
        ax[1,0].plot(grouped.index,grouped.values,color=color,label=spec)
    ax[1,0].set(xticks=SPEC['k_values'],xlabel='Registered k',ylabel='Share of between-cluster SS (%)',
        title='(C) Init contribution; seed range')
    ax[1,0].legend(frameon=False)
    cs=frame('CLUSTER_SIZE_POPULATION_AND_EXTREMES.csv')
    cs=cs[(cs.cohort=='positive_population')&(cs.k==4)&(cs.seed==42)&(cs.specification=='A')]
    labels=['D'+str(int(v)+1)+'\nn='+str(int(n)) for v,n in zip(cs.diagnostic_cluster,cs.n_tracts)]
    ax[1,1].bar(np.arange(4),cs.Init_mean*100,color=COLORS)
    ax[1,1].set(xticks=np.arange(4),xticklabels=labels,ylabel='Mean initial service (%)',
        title='(D) A, k=4, seed 42')
    fig.subplots_adjust(top=.87,bottom=.1,left=.09,right=.97,wspace=.42,hspace=.45)
    finish(fig,'INITIAL_SERVICE_ZERO_INFLUENCE')


def stability():
    fig,ax=plt.subplots(2,2,figsize=(7.2,6.6))
    title(fig,'Budget allocation and registered stability checks | no winner selected')
    c=frame('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv')
    c=c[(c.cohort=='positive_population')&(c.k==4)&(c.seed==42)&(c.kind=='domain')]
    pivot=c.pivot(index='specification',columns='domain',values='fraction_of_between').reindex(SPECS)
    bottom=np.zeros(5)
    for domain,color in zip(['RQ1','RQ2','RQ3'],COLORS[:3]):
        ax[0,0].bar(np.arange(5),pivot[domain]*100,bottom=bottom,color=color,label=domain)
        bottom+=pivot[domain].values*100
    ax[0,0].set(xticks=np.arange(5),xticklabels=DISPLAY,ylabel='Between-cluster SS (%)',
        title='(A) Equal budgets; unequal separation')
    ax[0,0].set_ylim(0,115)
    ax[0,0].set_yticks([0,25,50,75,100])
    ax[0,0].tick_params(axis='x',rotation=45)
    ax[0,0].legend(loc='upper center',ncol=3,fontsize=8,frameon=False,bbox_to_anchor=(.5,1.0))
    compare=frame('CLUSTER_MEMBERSHIP_COMPARISONS.csv')
    compare=compare[compare.cohort=='positive_population']
    for a,b,color,label in [('A','B',COLORS[0],'A vs B'),('A','A-minus-Init',COLORS[1],'A vs A - Init'),
                           ('B','B-minus-Init',COLORS[2],'B vs B - Init')]:
        group=compare[(compare.specification_a==a)&(compare.specification_b==b)].groupby('k').ARI
        ax[0,1].plot(group.median().index,group.median().values,'o-',color=color,label=label)
    ax[0,1].set(xticks=SPEC['k_values'],ylim=(0,1.02),xlabel='Registered k',ylabel='Adjusted Rand index',
        title='(B) Specification agreement')
    ax[0,1].legend(fontsize=8,frameon=False,loc='lower right')
    allst=frame('SPATIAL_AND_SEED_STABILITY.csv')
    for spec,color in zip(SPECS,COLORS+['#555555']):
        seed=allst[(allst.cohort=='positive_population')&(allst.specification==spec)&(allst.kind=='seed_pair')].groupby('k').ARI
        ax[1,0].plot(seed.median().index,seed.median().values,'o-',color=color,label=spec.replace('-minus-',' - '))
    ax[1,0].set(xticks=SPEC['k_values'],ylim=(.5,1.02),xlabel='Registered k',ylabel='Median seed-pair ARI',title='(C) Five-seed stability')
    ax[1,0].legend(fontsize=8,frameon=False,loc='lower left',ncol=2)
    spatial=allst[(allst.cohort=='positive_population')&(allst.k==4)&(allst.kind=='spatial_leave_quadrant_out')]
    for pos,spec in enumerate(SPECS):
        vals=spatial[spatial.specification==spec].ARI
        ax[1,1].scatter(np.repeat(pos,len(vals)),vals,color=COLORS[pos%4],s=18)
        ax[1,1].plot([pos-.18,pos+.18],[vals.median()]*2,color='black',lw=1)
    ax[1,1].set(xticks=np.arange(5),xticklabels=DISPLAY,ylim=(0,1.02),ylabel='All-tract ARI after leaveout',
        title='(D) Four spatial leaveouts, k=4')
    ax[1,1].tick_params(axis='x',rotation=45)
    fig.subplots_adjust(top=.87,bottom=.13,left=.09,right=.97,wspace=.43,hspace=.67)
    finish(fig,'BUDGET_AND_STABILITY_COMPARISONS')


def profiles(d):
    profiles=frame('CLUSTER_PROFILE_DISTRIBUTIONS.csv')
    counts=frame('CLUSTER_SIZE_POPULATION_AND_EXTREMES.csv')
    fig,axes=plt.subplots(2,2,figsize=(7.2,6.8))
    title(fig,'Input-based diagnostic profiles, k=4, seed42 | not independent validation')
    for ax,spec in zip(axes.ravel(),SPECS[:4]):
        cols=list(SPEC['specifications'][spec])
        p=profiles[(profiles.cohort=='positive_population')&(profiles.specification==spec)&
            (profiles.k==4)&(profiles.seed==42)].pivot(index='diagnostic_cluster',columns='variable',values='mean')[cols]
        z=(p-d[cols].mean())/d[cols].std(ddof=0)
        im=ax.imshow(z,vmin=-2,vmax=2,cmap='RdBu_r',aspect='auto')
        cs=counts[(counts.cohort=='positive_population')&(counts.specification==spec)&(counts.k==4)&(counts.seed==42)]
        short_labels={'Init_Supply':'Initial','Grid_Impact':'Impact','Redundancy_HHI':'HHI','B_480_hr':'Deficit',
                      'Delta_B_logistics':'Logistics','SOVI_SCORE':'SOVI','log1p_Population':'Log pop','log1p_BUILDVALUE':'Log assets'}
        ax.set(yticks=range(4),yticklabels=['D'+str(int(r.diagnostic_cluster)+1)+' ('+str(int(r.n_tracts))+')' for r in cs.itertuples()],
               xticks=range(len(cols)),xticklabels=[short_labels[c] for c in cols],title=spec.replace('-minus-',' - '))
        ax.tick_params(axis='x',rotation=50)
        for i in range(4):
            for j in range(len(cols)):
                v=z.iloc[i,j]
                ax.text(j,i,f'{v:.1f}',ha='center',va='center',fontsize=8,color='white' if abs(v)>1.2 else 'black')
    fig.subplots_adjust(top=.87,bottom=.25,left=.13,right=.98,wspace=.42,hspace=1.2)
    cbax=fig.add_axes([.30,.075,.45,.018])
    fig.colorbar(im,cax=cbax,orientation='horizontal',label='Cluster mean in cohort SD units')
    finish(fig,'K4_DIAGNOSTIC_FEATURE_PROFILES')


def spatial(d):
    membership=frame('CLUSTER_MEMBERSHIPS_POSITIVE_POPULATION.csv').set_index('tract_id')
    fig,axes=plt.subplots(2,2,figsize=(7.2,6.6),sharex=True,sharey=True)
    title(fig,'Exploratory membership at frozen tract internal points | k=4, seed42')
    for ax,spec in zip(axes.ravel(),SPECS[:4]):
        labels=membership[f'{spec}__k4__s42'].reindex(d.index)
        for label,color in enumerate(COLORS):
            mask=labels.eq(label)
            ax.scatter(d.loc[mask,'utm_x_m']/1000,d.loc[mask,'utm_y_m']/1000,s=3.5,color=color,rasterized=True,
                label=f'D{label+1} (n={int(mask.sum())})')
        extra=d.additional_zero_housing_positive_population
        ax.scatter(d.loc[extra,'utm_x_m']/1000,d.loc[extra,'utm_y_m']/1000,s=28,facecolors='none',edgecolors='black',lw=.7)
        counts=[int(labels.eq(i).sum()) for i in range(4)]
        ax.set_title(spec.replace('-minus-',' - ')+'\nn(D1-D4): '+' / '.join(map(str,counts)),fontsize=9)
        ax.set_aspect('equal')
    for ax in axes[1,:]:ax.set_xlabel('UTM11N easting (km)')
    for ax in axes[:,0]:ax.set_ylabel('UTM11N northing (km)')
    handles=[Line2D([],[],marker='o',linestyle='none',color=color,markersize=4,label=f'D{i+1}') for i,color in enumerate(COLORS)]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.07),ncol=4,frameon=False)
    fig.text(.5,.035,'Black rings: 8 additional positive-population, zero-housing tracts. D labels are diagnostic only.',
        ha='center',fontsize=8.5)
    fig.subplots_adjust(top=.83,bottom=.18,left=.11,right=.98,wspace=.27,hspace=.35)
    finish(fig,'K4_SPATIAL_MEMBERSHIP_REVIEW')


def main():
    d=frame('TRACT_FEATURES_VERIFIED_2315.csv').set_index('tract_id')
    d=d.loc[d.Population>0]
    assets(d)
    initial(d)
    stability()
    profiles(d)
    spatial(d)
    dump('PDF_RENDER_AND_BOUNDARY_QA.json',dict(figures=RECORDS,all_pages_rendered=True,
        all_text_within_page=True,all_figures_generated_with_matplotlib=True,
        visual_review_status='RENDERED_AWAITING_HUMAN_AGENT_INSPECTION'))
    print(json.dumps({'diagnostic_pdfs':len(RECORDS),'all_pages_rendered':True}),flush=True)


if __name__=='__main__':main()
