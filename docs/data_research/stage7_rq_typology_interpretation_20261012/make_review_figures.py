"""Vector scientific diagnostics from frozen extracts and saved labels only."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, NullFormatter
import numpy as np
import pandas as pd
import fitz
from common import *

NOTICE = 'AUTHOR REVIEW \u2014 NOT FORMAL STAGE 7'
FIG = OUT/'figures'
PREVIEW = OUT/'pdf_review'
BLUE, ORANGE, GREEN = '#176fa4','#ba581e','#26775b'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,
    'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,
    'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})


def header(fig,title,note):
    height=fig.get_figheight()
    fig.suptitle(title,fontsize=11,y=1-.16/height,va='top')
    fig.text(.5,1-.40/height,NOTICE,ha='center',va='top',fontsize=8,color='#a52c2c')
    fig.text(.5,.025,note,ha='center',va='bottom',fontsize=7)


def finish(fig,stem,pdf=None,page=0):
    if pdf is None:fig.savefig(lp(FIG/(stem+'.pdf')))
    else:pdf.savefig(fig)
    suffix=f'_k{page}' if page else ''
    fig.savefig(lp(FIG/(stem+suffix+'.png')),dpi=600)
    plt.close(fig)


def profiles(p,c):
    stem='K3_K4_K5_ORIGINAL_UNIT_PROFILES'
    variables=['Init_Supply','Grid_Impact','Redundancy_HHI','B_480_hr','Delta_B_logistics','SOVI_SCORE','Population','BUILDVALUE']
    titles=['Initial service (%)','Spectral grid impact','Dependency HHI','Cumulative deficit (h)','Extra logistics deficit (h)','SOVI (0-100)','Tract population (persons)','Building stock (million USD)']
    with PdfPages(lp(FIG/(stem+'.pdf'))) as pdf:
        for k in KS:
            fig,axes=plt.subplots(3,3,figsize=(7.2,8.4))
            header(fig,f'Original-unit profiles: saved k={k}, seed 42',
                'Means (circles), medians (diamonds), P10-P90 (lines); not confidence intervals.\n'
                'A: seven variables; B: eight. Raw population/stock shown; fitted exposure uses ln(1+x).')
            fig.subplots_adjust(left=.075,right=.975,bottom=.11,top=.835,wspace=.48,hspace=.52)
            fig.legend(handles=[Line2D([0],[0],color=BLUE,marker='o',label='A'),Line2D([0],[0],color=ORANGE,marker='o',label='B'),
                Line2D([0],[0],color='#8c8c8c',linestyle='--',label='Cohort median')],loc='upper center',bbox_to_anchor=(.5,.895),ncol=3,frameon=False)
            for ax,v,title in zip(axes.flat,variables,titles):
                scale=100 if v=='Init_Supply' else 1e-6 if v=='BUILDVALUE' else 1
                for model,off,color in [('A',-.15,BLUE),('B',.15,ORANGE)]:
                    part=p[(p.specification==model)&(p.k==k)&(p.seed==42)&(p.variable==v)].sort_values('diagnostic_cluster')
                    y=np.arange(k)+off
                    ax.hlines(y,part.p10*scale,part.p90*scale,color=color,lw=1.3,alpha=.8)
                    ax.scatter(part['mean']*scale,y,color=color,s=18,zorder=3)
                    ax.scatter(part['median']*scale,y,facecolors='white',edgecolors=color,marker='D',s=13,zorder=4)
                ax.axvline(part.cohort_median.iloc[0]*scale,color='#8c8c8c',ls='--',lw=.8)
                ax.set_yticks(range(k),[f'D{i+1}' for i in range(k)])
                ax.set_ylim(k-.5,-.5);ax.set_title(title,pad=7);ax.grid(axis='x',alpha=.15)
                ax.xaxis.set_major_locator(MaxNLocator(4))
                if v in ['Population','BUILDVALUE']:
                    ax.set_xscale('log')
                    ticks=[2000,4000,6000] if v=='Population' else [300,600,1000]
                    ax.set_xticks(ticks,[f'{tick:,}' for tick in ticks])
                    ax.xaxis.set_minor_formatter(NullFormatter())
                elif v in ['Init_Supply','Grid_Impact','Redundancy_HHI','Delta_B_logistics']:ax.set_xlim(left=-.01 if v!='Init_Supply' else -.02)
                if v=='BUILDVALUE':ax.text(.02,.02,'A: descriptive only',transform=ax.transAxes,fontsize=6.8,color=BLUE)
            ax=axes.flat[8];ax.axis('off')
            ax.set_title('Tracts / resident share',loc='left',fontsize=9)
            counts={}
            for model in ['A','B']:
                cc=c[(c.specification==model)&(c.k==k)&(c.seed==42)].sort_values('diagnostic_cluster')
                counts[model]=[f'{int(row.n_tracts)} / {row.population_share*100:.1f}%' for _,row in cc.iterrows()]
            cells=[[f'D{i+1}',counts['A'][i],counts['B'][i]] for i in range(k)]
            tab=ax.table(cellText=cells,colLabels=['ID','A','B'],cellLoc='left',bbox=[0,.20,1,.75],colWidths=[.15,.43,.42])
            tab.auto_set_font_size(False);tab.set_fontsize(6.8)
            for cell in tab.get_celld().values():cell.set_edgecolor('#ddd');cell.set_linewidth(.4)
            ax.text(0,.05,'IDs are specific to each model/k.',transform=ax.transAxes,fontsize=6.8)
            finish(fig,stem,pdf,k)


def transitions():
    tr=frame('MEMBERSHIP_TRANSITIONS_AND_CLASS_MATCHING.csv')
    summary=frame('SEVEN_EIGHT_MATCHED_MEMBERSHIP_SUMMARY.csv')
    fig,axes=plt.subplots(1,3,figsize=(7.2,3.6))
    header(fig,'Seven-to-eight variable membership transitions',
        'Maximum-count Hungarian matching reorders B columns only. All tract counts shown.\n'
        'A-to-B adds stock and halves population budget; this is not a pure feature-addition test.')
    fig.subplots_adjust(left=.07,right=.98,bottom=.28,top=.77,wspace=.35)
    for ax,k in zip(axes,KS):
        t=tr[(tr.specification_a=='A')&(tr.specification_b=='B')&(tr.k_a==k)&(tr.seed==42)]
        order=t[['target_cluster','target_matched_to_source']].drop_duplicates().sort_values('target_matched_to_source').target_cluster.to_list()
        mat=t.pivot(index='source_cluster',columns='target_cluster',values='n_tracts').reindex(index=range(k),columns=order).to_numpy()
        ax.imshow(mat,cmap='Blues',vmin=0,vmax=mat.max())
        for i in range(k):
            for j in range(k):ax.text(j,i,str(mat[i,j]),ha='center',va='center',fontsize=7,color='white' if mat[i,j]>mat.max()*.55 else '#222')
        ax.set_xticks(range(k),[f'D{i+1}' for i in order]);ax.set_yticks(range(k),[f'D{i+1}' for i in range(k)])
        row=summary[(summary.k==k)&(summary.seed==42)].iloc[0]
        ax.set_title(f'k={k}: {int(row.changed)} reassigned\nARI={row.ARI:.3f}',fontsize=9)
        ax.set_xlabel('Matched B class');ax.set_ylabel('A class')
    finish(fig,'SEVEN_EIGHT_MEMBERSHIP_TRANSITIONS')


def initial(d,rare):
    a=frame('INIT_ALGEBRAIC_DISTANCE_DECOMPOSITION.csv')
    mask=d.index.isin(rare)
    fig,axes=plt.subplots(2,2,figsize=(7.2,6.6))
    header(fig,'Initial service: sparse rare-state information and scaling leverage',
        'Actual initial availability remains very low. Algebra holds the exact 34 labels and scaler fixed;\n'
        'omission with fixed budgets is not a fitted candidate. Registered ablations also reallocate RQ1.')
    fig.subplots_adjust(left=.105,right=.97,bottom=.14,top=.84,hspace=.45,wspace=.32)
    ax=axes[0,0]
    counts=[int(d.Init_Supply.eq(0).sum()),int((d.Init_Supply.gt(0)&~mask).sum()),int(mask.sum())]
    bars=ax.bar(['Exact zero','Other nonzero','Rare 34'],counts,color=['#999999',BLUE,ORANGE],width=.6)
    for b,n in zip(bars,counts):ax.text(b.get_x()+b.get_width()/2,n+35,str(n),ha='center',fontsize=8)
    ax.set_ylim(0,1800);ax.set_ylabel('Tracts');ax.set_title('(A) 2,299 positive-population tracts')
    ax=axes[0,1]
    bins=np.linspace(0,2.5,31)
    ax.hist(d.loc[d.Init_Supply.gt(0)&~mask,'Init_Supply']*100,bins=bins,color=BLUE,alpha=.7,label='Other nonzero')
    ax.hist(d.loc[mask,'Init_Supply']*100,bins=bins,color=ORANGE,alpha=.8,label='Rare 34')
    ax.set_yscale('log');ax.set_ylabel('Tracts (log scale)');ax.set_xlabel('Initial availability (%)')
    ax.set_title('(B) Nonzero distribution');ax.legend(frameon=False)
    ax=axes[1,0]
    ax.scatter(d.loc[~mask,'Init_Supply']*100,d.loc[~mask,'B_480_hr'],s=5,color='#999',alpha=.4,rasterized=True)
    ax.scatter(d.loc[mask,'Init_Supply']*100,d.loc[mask,'B_480_hr'],s=13,color=ORANGE,label='Rare 34')
    ax.set_xlabel('Mean initial availability (%)');ax.set_ylabel('Cumulative deficit B (h)');ax.set_title('(C) Actual-unit recovery contrast')
    ax=axes[1,1]
    variants=['registered','drop_Init_fixed_other_budgets','drop_Init_RQ1_redistributed']
    for model,offset,color in [('A',-.17,BLUE),('B',.17,ORANGE)]:
        val=a[a.specification==model].groupby('algebraic_variant').rare_centroid_global_between_SS.sum().reindex(variants)
        ax.bar(np.arange(3)+offset,val,width=.32,color=color,label=model)
    ax.set_xticks(range(3),['Full','Omit Init\nother fixed','Omit Init\nRQ1 reallocated'])
    ax.set_ylabel('Rare centroid separation (weighted SS)');ax.set_title('(D) Init explains 89.11% (A)');ax.legend(frameon=False)
    finish(fig,'INIT_SUPPLY_RARE_STATE_AND_SCALING')


def geography(d,rare):
    st=frame('STATION_INITIAL_STATE_AND_DAMAGE_SUMMARY.csv').set_index('substation_id').loc['308581']
    small=d.loc[d.index.isin(rare)]
    fig,axes=plt.subplots(1,2,figsize=(7.2,4.9))
    header(fig,'Location of the 34 Q-dependent tracts',
        'Official tract internal points, not neighborhood boundaries. Color is frozen mean availability.\n'
        'Q is the retained Core supply proxy; no capacity or power-flow adequacy is implied.')
    fig.subplots_adjust(left=.10,right=.85,bottom=.23,top=.81,wspace=.35)
    for i,ax in enumerate(axes):
        ax.scatter(d.INTPTLON,d.INTPTLAT,s=4,color='#c4c4c4',rasterized=True)
        points=ax.scatter(small.INTPTLON,small.INTPTLAT,c=small.Init_Supply*100,cmap='viridis',s=22 if i else 13,vmin=1.1,vmax=2.45,edgecolors='white',linewidths=.3,zorder=3)
        ax.scatter([st.LONGITUDE],[st.LATITUDE],marker='^',s=48,color='#b22c28',edgecolors='white',lw=.5,zorder=4)
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.set_aspect(1/np.cos(np.deg2rad(34)))
        ax.ticklabel_format(axis='both',useOffset=False);ax.xaxis.set_major_locator(MaxNLocator(4));ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.set_title('(A) Study-cohort points' if i==0 else '(B) Rare-state detail')
        if i:
            ax.set_xlim(min(small.INTPTLON.min(),st.LONGITUDE)-.014,max(small.INTPTLON.max(),st.LONGITUDE)+.014)
            ax.set_ylim(min(small.INTPTLAT.min(),st.LATITUDE)-.014,max(small.INTPTLAT.max(),st.LATITUDE)+.014)
    cbax=fig.add_axes([.89,.32,.017,.36]);fig.colorbar(points,cax=cbax,label='Initial availability (%)')
    fig.legend(handles=[Line2D([0],[0],marker='^',color='none',markerfacecolor='#b22c28',label='Q (308581)'),
        Line2D([0],[0],marker='o',color='none',markerfacecolor='#c4c4c4',label='Other cohort internal points')],loc='lower center',bbox_to_anchor=(.5,.115),ncol=2,frameon=False)
    finish(fig,'THIRTYFOUR_GEOGRAPHIC_INITIAL_SERVICE')


def dependency():
    contrib=frame('THIRTYFOUR_TRACT_STATION_DEPENDENCY.csv')
    st=frame('STATION_INITIAL_STATE_AND_DAMAGE_SUMMARY.csv').set_index('substation_id')
    at=frame('TRACT_Q_DEPENDENCY_AND_INITIAL_CONTRIBUTION.csv')
    rd=frame('THIRTYFOUR_REALIZATION_SERVICE_DISTRIBUTIONS.csv')
    fig,axes=plt.subplots(2,2,figsize=(7.2,6.7))
    header(fig,'Frozen evidence: station dependence and source qualification',
        'All quantities are extracted from 1,000 saved physical samples; no new source gate was run.\n'
        'Q is a Core proxy and directly qualifies when functional, not proof of surviving remote supply.')
    fig.subplots_adjust(left=.105,right=.97,bottom=.14,top=.84,wspace=.4,hspace=.6)
    ax=axes[0,0]
    agg=contrib.groupby('substation_id').initial_service_contribution.sum().sort_values(ascending=False)
    agg=agg/agg.sum()*100
    ax.barh(['Q','Wilmington','Harbor Gen','Dock'],agg.iloc[:4],color=[BLUE,'#999','#999','#999'])
    ax.invert_yaxis();ax.set_xlim(0,110);ax.set_xlabel('Share of rare-group mean initial service (%)')
    for i,x in enumerate(agg.iloc[:4]):ax.text(x+.8,i,f'{x:.2f}%',va='center',fontsize=7)
    ax.set_title('(A) Contribution, not electrical capacity')
    ax=axes[0,1]
    names=['308581','309853','310179','304450'];y=np.arange(4)
    ax.bar(y-.17,st.loc[names,'eligible_fraction']*100,width=.32,color=ORANGE,label='f >= 0.5')
    ax.bar(y+.17,st.loc[names,'source_connected_fraction']*100,width=.32,color=BLUE,label='Saved F and C')
    ax.set_xticks(y,['Q','Dock','Wilmington','Harbor Gen'],rotation=20,ha='right');ax.set_ylabel('Existing samples (%)')
    ax.set_ylim(0,5);ax.set_title('(B) Qualification changes the comparison');ax.legend(frameon=False)
    ax=axes[1,0]
    nonrare=~at.rare34
    ax.scatter(at.loc[nonrare,'Q_weight'],at.loc[nonrare,'Init_Supply']*100,s=5,color='#999',alpha=.45,rasterized=True)
    ax.scatter(at.loc[~nonrare,'Q_weight'],at.loc[~nonrare,'Init_Supply']*100,s=13,color=ORANGE)
    ax.set_xlabel('Normalized dependency weight on Q');ax.set_ylabel('Mean initial availability (%)');ax.set_title('(C) Continuous mapping, not a binary class')
    ax=axes[1,1]
    rows=rd.sort_values('positive_sample_fraction')
    ax.scatter(np.arange(1,35),rows.positive_sample_fraction*100,s=16,color=BLUE)
    ax.set_ylim(0,6.5);ax.set_xlabel('34 tracts, ordered by positive frequency');ax.set_ylabel('Samples with positive service (%)')
    ax.set_title('(D) Every tract has zero sample median')
    finish(fig,'FROZEN_STATION_DEPENDENCY_EXPLANATION')


def stability():
    s=frame('K_SEED_AND_GEOGRAPHIC_STABILITY.csv')
    fig,(ax,txt)=plt.subplots(1,2,figsize=(7.2,5.8),gridspec_kw={'width_ratios':[1.1,1]})
    header(fig,'k: scientific resolution and saved stability',
        'Points are medians, intervals are minima/maxima, not confidence limits.\n'
        'Geographic test refits/predicts in the earlier archive; no new fits or scientific optimum here.')
    fig.subplots_adjust(left=.18,right=.98,bottom=.20,top=.82,wspace=.3)
    y=0;names=[]
    for model in SPECS:
        for k in KS:
            names.append(f'{model}, k{k}')
            for kind,offset,color in [('seed_pair',-.15,BLUE),('spatial_leave_quadrant_out',.15,ORANGE)]:
                x=s[(s.specification==model)&(s.k==k)&(s.kind==kind)].ARI.dropna()
                if x.empty:continue
                ax.hlines(y+offset,x.min(),x.max(),color=color,lw=1.8)
                ax.scatter([x.median()],[y+offset],color=color,s=17)
            y+=1
    ax.set_yticks(range(len(names)),names);ax.set_ylim(len(names)-.5,-.5);ax.set_xlim(0,1.04)
    ax.set_xlabel('Adjusted Rand index');ax.grid(axis='x',alpha=.15)
    fig.legend(handles=[Line2D([0],[0],color=BLUE,marker='o',label='Seed pairs'),Line2D([0],[0],color=ORANGE,marker='o',label='Four quadrant tests')],loc='center',bbox_to_anchor=(.5,.10),frameon=False,ncol=2)
    txt.axis('off')
    lines=[('k3: broad three-RQ comparison','Large lower-burden / higher-SOVI class;\nhigher-importance / longer-loss class;\nstrongly logistics-sensitive class.'),
        ('k4: local rare-state resolution','Mainly separates 34 Q-dependent tracts.\nMean initial availability is only 1.82%;\n89.11% rare centroid leverage is Init.'),
        ('k5: finer structural differentiation','Adds 225 (A) / 229 (B) high-impact tracts.\nRecovery differences versus another class\nare modest; not five recovery regimes.'),
        ('Decision, not score optimization','A/k3 is the parsimonious broad candidate.\nA/k5 is conditional on structural detail.\nNo k is adopted; author approval required.')]
    for i,(title,body) in enumerate(lines):
        yy=.99-i*.245
        txt.text(0,yy,title,va='top',fontsize=8.5,weight='bold')
        txt.text(0,yy-.067,body,va='top',fontsize=7.5,linespacing=1.6)
    finish(fig,'K_INTERPRETATION_AND_STABILITY')


def render():
    records=[]
    for file in sorted(FIG.glob('*.pdf')):
        doc=fitz.open(lp(file))
        for i,page in enumerate(doc):
            assert abs(page.rect.width-7.2*72)<.1
            pix=page.get_pixmap(matrix=fitz.Matrix(150/72,150/72),alpha=False)
            name=f'{file.stem}_p{i+1}.png';pix.save(str(lp(PREVIEW/name)))
            text=page.get_text()
            assert 'AUTHOR REVIEW' in text and 'NOT FORMAL STAGE 7' in text
            words=page.get_text('words')
            out=[w[:4] for w in words if w[0]<0 or w[1]<0 or w[2]>page.rect.width+.1 or w[3]>page.rect.height+.1]
            assert not out,(file.name,i,out)
            records.append(dict(pdf=file.name,page=i+1,width_in=page.rect.width/72,height_in=page.rect.height/72,
                render=name,render_dpi=150,notice_present=True,text_within_page=True,pdf_sha256=sha(file),render_sha256=sha(PREVIEW/name)))
        doc.close()
    dump('PDF_RENDER_AND_BOUNDS_QA.json',records)


def main():
    lp(FIG).mkdir(exist_ok=True);lp(PREVIEW).mkdir(exist_ok=True)
    d=frame('VERIFIED_INTERPRETATION_TRACT_VALUES.csv').set_index('tract_id')
    rare=set(frame('THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv').tract_id)
    profiles(frame('CLUSTER_ORIGINAL_UNIT_PROFILES.csv'),frame('CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv'))
    transitions();initial(d,rare);geography(d,rare);dependency();stability();render()
    print('Six scientific PDFs and 600-dpi previews created; eight PDF pages rendered at publication width.')


if __name__=='__main__':main()
