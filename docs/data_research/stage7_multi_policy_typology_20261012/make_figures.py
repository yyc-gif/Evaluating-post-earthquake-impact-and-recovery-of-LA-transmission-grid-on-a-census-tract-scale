"""Data-only Matplotlib vector review figures, never numbered manuscript assets."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import Normalize
import fitz
from common import *

WARN='AUTHOR REVIEW \u2014 NOT FORMAL STAGE 7'
COLORS={'A':'#235789','P2':'#19836b','P3':'#b34b36'}
CLASSES=['#19836b','#235789','#c87921','#8e5ca2','#ba4242','#737373','#56a9b2','#999d29']
NAMES={p:p.replace('-first','').capitalize() for p in PRIMARY+['random']}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,
    'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42,
    'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})


def new(title,height=5.0):
    fig=plt.figure(figsize=(7.2,height))
    fig.suptitle(title,x=.07,ha='left',y=.955,fontsize=12,fontweight='bold')
    fig.text(.07,.025,WARN,fontsize=8,color='#a62f27')
    return fig


def finish(fig,name,foot):
    fig.text(.07,.063,foot,fontsize=7.6,va='bottom')
    fig.savefig(lp(OUT/(name+'.pdf')))
    fig.savefig(lp(OUT/(name+'.png')),dpi=600)
    plt.close(fig)


def main():
    assert json.loads(lp(OUT/'INDEPENDENT_QA_RESULTS.json').read_text())['status']=='PASS'
    d=dataset(); e=frame('ELBOW_AND_SILHOUETTE_COMPARISON.csv'); results=frame('A_VS_P2_VS_P3_CLUSTERING_RESULTS.csv')
    lab=np.load(lp(OUT/'REGISTERED_FIT_ARRAYS.npz')); keys={k:i for i,k in enumerate(lab['keys'])}
    def labels(sp,k): return lab['labels'][keys[key(sp,'main5','cohort',k,42)]]
    fig=new('Baseline burden and multi-policy constraint burden',5.1)
    gs=fig.add_gridspec(1,2,left=.10,right=.95,bottom=.23,top=.84,wspace=.32,width_ratios=[1.7,1])
    ax=fig.add_subplot(gs[0]); sc=ax.scatter(d.B_Unconstrained,d.MeanDelta,c=d.PolicySD,cmap='cividis',s=7,alpha=.8,rasterized=False)
    ax.set(xlabel='Unconstrained deficit (h)',ylabel='Mean additional deficit (h)')
    ax.set_title('(A) All 2,299 positive-population tracts',loc='left',fontsize=9)
    cbar=fig.colorbar(sc,ax=ax,pad=.02); cbar.set_label('Policy SD (h)')
    ax=fig.add_subplot(gs[1]); ax.scatter(d.MeanDelta,d.PolicySD,s=6,color=COLORS['P3'],alpha=.5)
    ax.set(xlabel='Mean additional deficit (h)',ylabel='Policy SD (h)'); ax.set_title('(B) Overlap of RQ2 summaries',loc='left',fontsize=9)
    r=d.MeanDelta.corr(d.PolicySD); ax.text(.04,.95,f'Pearson r = {r:.3f}',transform=ax.transAxes,va='top',fontsize=8)
    finish(fig,'01_Baseline_and_constraint_burden','Five predefined priorities; equal descriptive weights. All deficits are full-service-deficit hours.\nPolicy SD varies across policy means, not across earthquake realizations.')

    fig=new('Geographic distribution of restoration-priority sensitivity',5.6)
    ax=fig.add_axes([.11,.24,.75,.60]); sc=ax.scatter(d.INTPTLON,d.INTPTLAT,c=d.PolicySD,cmap='cividis',s=9,linewidths=0)
    ax.set(xlabel='Longitude',ylabel='Latitude'); ax.set_aspect(1/np.cos(np.radians(34)))
    fig.colorbar(sc,ax=ax,pad=.025,fraction=.04,label='Policy SD (h)')
    high=d.PolicySD.ge(d.PolicySD.quantile(.9))
    finish(fig,'02_Policy_SD_geography',f'Official tract internal points; no tracts excluded for polygon geometry. P90 = {d.PolicySD.quantile(.9):.2f} h.\n{high.sum():,} tracts at or above P90 represent {d.loc[high,"Population"].sum()/d.Population.sum():.2%} of resident population.')

    fig=new('Policy contribution and policy-set influence',5.3)
    gs=fig.add_gridspec(1,2,left=.20,right=.96,bottom=.29,top=.81,wspace=.90)
    influence=frame('POLICY_VARIANCE_INFLUENCE_SUMMARY.csv').set_index('policy').reindex(PRIMARY)
    ax=fig.add_subplot(gs[0]); ax.barh([NAMES[p] for p in PRIMARY],100*influence.share_of_total_policy_variance,color='#235789')
    ax.invert_yaxis(); ax.set(xlabel='Share of summed policy\nvariance (%)'); ax.set_title('(A) Five-policy\nvariance contributions',loc='left',fontsize=9)
    summary=frame('POLICY_SET_FEATURE_SENSITIVITY_SUMMARY.csv').query("policy_set!='main5' and variable=='PolicySD'")
    ax=fig.add_subplot(gs[1]); labels2=[('+'+NAMES['random']) if n=='plus_random' else '-'+NAMES[n.replace('without_','')] for n in summary.policy_set]
    ax.barh(labels2,summary.p90_absolute_change_hr,color=[COLORS['P3'] if n=='plus_random' else COLORS['P2'] for n in summary.policy_set]); ax.invert_yaxis()
    ax.set(xlabel='P90 absolute Policy SD\nchange (h)'); ax.set_title('(B) Changes from\nmain five-policy set',loc='left',fontsize=9)
    finish(fig,'03_Policy_influence','Variance contribution = summed squared policy deviation / summed five-policy variance.\nLOO exclusions are unique; omitting Vulnerability is not counted twice. Random is a sensitivity only.')

    fig=new('Weighted-space elbow diagnostics',5.2)
    gs=fig.add_gridspec(1,2,left=.11,right=.96,bottom=.24,top=.83,wspace=.35)
    ax=fig.add_subplot(gs[0]); ax2=fig.add_subplot(gs[1])
    for sp in ['A','P2','P3']:
        part=e.query('specification==@sp and policy_set=="main5"').sort_values('k')
        ax.plot(part.k,part.mean_WCSS,color=COLORS[sp],marker='o',markersize=4,label=sp)
        ax2.plot(part.k,part.chord_gap,color=COLORS[sp],marker='o',markersize=4,label=sp)
    ax.set(xlabel='K',ylabel='Weighted WCSS'); ax2.set(xlabel='K',ylabel='Normalized endpoint-chord gap')
    ax.set_xticks(range(1,9)); ax2.set_xticks(range(1,9)); ax.legend(frameon=False)
    ax.set_title('(A) Mean over seeds 42-46',loc='left',fontsize=9); ax2.set_title('(B) Bend diagnostic, not a selected K',loc='left',fontsize=9)
    finish(fig,'04_Elbow_comparison','Each feature space has its own coordinates and budgets. Smooth inertia reduction does not imply a sharp elbow.\nA is the verified saved Impact-first reference; P2/P3 use the main five-policy set.')

    fig=new('Full-cohort silhouette diagnostics',5.4)
    gs=fig.add_gridspec(1,2,left=.11,right=.96,bottom=.26,top=.83,wspace=.36)
    ax=fig.add_subplot(gs[0]); ax2=fig.add_subplot(gs[1])
    for sp in ['A','P2','P3']:
        part=e.query('specification==@sp and policy_set=="main5" and k>1').sort_values('k')
        ax.plot(part.k,part.mean_silhouette,color=COLORS[sp],marker='o',markersize=4,label=sp)
        ax.fill_between(part.k,part.min_seed_silhouette,part.max_seed_silhouette,color=COLORS[sp],alpha=.12)
        rows=results.query('specification==@sp and policy_set=="main5" and scaling=="cohort" and k>1')
        q=rows.groupby('k').min_cluster_tracts.agg(['mean','min','max'])
        ax2.plot(q.index,q['mean'],color=COLORS[sp],marker='o',markersize=4,label=sp)
        ax2.fill_between(q.index,q['min'],q['max'],color=COLORS[sp],alpha=.12)
    ax.set(xlabel='K',ylabel='Mean silhouette'); ax2.set(xlabel='K',ylabel='Smallest class (tracts)',yscale='log'); ax2.axhline(34,color='#777',ls=':',lw=1)
    ax2.set_yticks([10,34,100,300,1000],['10','34','100','300','1000'])
    ax.set_xticks(KS); ax2.set_xticks(KS); ax.legend(frameon=False)
    ax.set_title('(A) Conditional internal geometry',loc='left',fontsize=9); ax2.set_title('(B) Small classes across seeds',loc='left',fontsize=9)
    finish(fig,'05_Silhouette_comparison','Full 2,299-tract Euclidean silhouette; shading shows seed range. Values across spaces are not a common physical metric.\nThe dotted line is the size of the previously verified Q-dependent group, not a minimum-size rule.')

    pdf=OUT/'06_Community_profiles_and_memberships.pdf'
    profile=frame('CLUSTER_ORIGINAL_UNIT_PROFILES.csv').query('policy_set=="main5"')
    groups=frame('CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv').query('policy_set=="main5"')
    with PdfPages(lp(pdf)) as book:
        for k in [3,4,5]:
            fig=new(f'Original-unit community profiles: K = {k}',10.5)
            for i,sp in enumerate(['A','P2','P3']):
                ax=fig.add_axes([.07,.66-i*.275,.89,.235]); ax.axis('off')
                part=profile.query('specification==@sp and k==@k').pivot(index='variable',columns='diagnostic_cluster',values='mean')
                grp=groups.query('specification==@sp and k==@k').set_index('diagnostic_cluster')
                rows=[['Tracts']+[str(int(grp.loc[c,'n_tracts'])) for c in range(k)],
                      ['Population share (%)']+[f'{100*grp.loc[c,"population_share"]:.2f}' for c in range(k)],
                      ['Median population']+[f'{grp.loc[c,"median_population"]:.0f}' for c in range(k)]]
                for v,label,mult,digits in [('Init_Supply','Initial service (%)',100,3),('Grid_Impact','Spectral grid impact',1,3),('Redundancy_HHI','Dependency HHI',1,3),
                    ('B_Unconstrained','Unconstrained deficit (h)',1,2),('MeanDelta','Mean additional deficit (h)',1,2),('PolicySD','Policy SD (h)',1,2),('SOVI_SCORE','FEMA SOVI (0-100)',1,1),('B_480_hr','Impact-first deficit (h)',1,2)]:
                    rows.append([label]+[f'{part.loc[v,c]*mult:.{digits}f}' for c in range(k)])
                table=ax.table(cellText=rows,colLabels=['Mean unless stated']+[f'{sp}-D{c+1}' for c in range(k)],cellLoc='center',colWidths=[.38]+[.62/k]*k,bbox=[0,0,1,1])
                table.auto_set_font_size(False); table.set_fontsize(7.7)
                for (r,c),cell in table.get_celld().items():
                    cell.set_linewidth(.25); cell.set_edgecolor('#cccccc')
                    cell.set_facecolor('#eef1f1' if r==0 else 'white')
                    if c==0:cell.set_text_props(ha='left')
                ax.set_title(f'{sp}: model-specific class IDs; all 2,299 tracts',loc='left',fontsize=10,pad=7,color=COLORS[sp])
            fig.text(.07,.07,'All values are actual units. Additional descriptors are not fitted coordinates. Quartiles are frozen.\nClass IDs are ordered within each model by burden, not equated to formal Stage 7 or other models.',fontsize=7.6)
            book.savefig(fig)
            fig.savefig(lp(OUT/f'06_Profiles_K{k}.png'),dpi=600); plt.close(fig)
        fig=new('Geographic membership: model-specific IDs',7.4)
        gs=fig.add_gridspec(2,3,left=.08,right=.97,bottom=.25,top=.85,hspace=.55,wspace=.25)
        for i,k in enumerate([4,5]):
            for j,sp in enumerate(['A','P2','P3']):
                ax=fig.add_subplot(gs[i,j]); l=labels(sp,k)
                for c in range(k):
                    sel=l==c; ax.scatter(d.loc[sel,'INTPTLON'],d.loc[sel,'INTPTLAT'],s=3,color=CLASSES[c],label=f'D{c+1}')
                ax.set_title(f'{sp}, K={k}',loc='left'); ax.set_aspect(1/np.cos(np.radians(34)))
                ax.set_xticks([-118.6,-118.2,-117.8]); ax.tick_params(labelsize=7)
                if j==0:ax.set_ylabel('Latitude')
                if i==1:ax.set_xlabel('Longitude')
                ax.legend(frameon=False,ncol=3,fontsize=7,loc='upper center',bbox_to_anchor=(.5,-.34),handletextpad=.1,columnspacing=.6)
        fig.text(.07,.075,'Exact official tract internal points, including all eight positive-population zero-housing tracts.\nColors identify model-specific ordered IDs only; transitions use explicit Hungarian matching and ARI.',fontsize=7.5)
        book.savefig(fig); fig.savefig(lp(OUT/'06_Membership_maps.png'),dpi=600); plt.close(fig)

    fig=new('Membership sensitivity to the predefined policy set',5.5)
    gs=fig.add_gridspec(1,2,left=.20,right=.92,bottom=.26,top=.83,wspace=.80)
    stab=frame('POLICY_SET_CLUSTER_STABILITY.csv').query('comparison=="policy_set" and scaling=="cohort"')
    names=[n for n in SETS if n!='main5']; ticks=['-'+NAMES[n.replace('without_','')] if n!='plus_random' else '+Random' for n in names]
    for i,sp in enumerate(['P2','P3']):
        ax=fig.add_subplot(gs[i]); q=stab.query('specification==@sp').groupby(['policy_set','k']).ARI.mean().unstack().reindex(names)[[3,4,5]]
        im=ax.imshow(q.to_numpy(),vmin=0,vmax=1,cmap='cividis',aspect='auto')
        for r in range(len(names)):
            for c in range(3):ax.text(c,r,f'{q.iloc[r,c]:.2f}',ha='center',va='center',fontsize=8,color='white' if q.iloc[r,c]<.5 else 'black')
        ax.set_xticks(range(3),['K=3','K=4','K=5']); ax.set_yticks(range(len(names)),ticks)
        ax.set_title(sp,loc='left',color=COLORS[sp]);
    fig.colorbar(im,ax=fig.axes[:2],fraction=.022,pad=.04,label='Mean ARI, seeds 42-46')
    finish(fig,'07_Policy_set_membership_stability','ARI is label-invariant. All policy sets use the same tracts and domain budgets.\nCohort standardization is recalculated by set; fixed-main5 scaling checks are supplied separately.')
    render=[]
    lp(OUT/'pdf_review').mkdir(exist_ok=True)
    for p in sorted(lp(OUT).glob('*.pdf')):
        doc=fitz.open(p)
        for i,page in enumerate(doc):
            spans=[sp for b in page.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for sp in line['spans']]
            clipped=[sp['text'] for sp in spans if not page.rect.contains(fitz.Rect(sp['bbox']))]
            assert not clipped,(p.name,i,clipped)
            assert 'AUTHOR REVIEW' in page.get_text() and 'NOT FORMAL STAGE 7' in page.get_text()
            path=OUT/'pdf_review'/f'{p.stem}_page{i+1}.png'
            page.get_pixmap(matrix=fitz.Matrix(150/72,150/72),alpha=False).save(lp(path))
            render.append(dict(pdf=p.name,page=i+1,width_in=page.rect.width/72,height_in=page.rect.height/72,
                clipped_spans=0,review_preview=path.name,pdf_sha256=sha(p),rendered_preview_sha256=sha(path)))
    dump('PDF_RENDER_QA.json',dict(pages=render,all_pages_rendered=True,all_text_within_page=True,visual_review_required=True))


if __name__=='__main__':main()
