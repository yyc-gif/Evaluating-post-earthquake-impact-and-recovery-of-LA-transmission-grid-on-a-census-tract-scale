"""Publication-size vector figures generated from verified scientific tables."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import geopandas as gpd
import fitz
from common import *

F=OUT/'figures'
COLORS={'P2':'#277b83','H1':'#be503c','H2':'#7255a0'}
CLASS=['#277b83','#e7a536','#7255a0','#bd5145','#7d9c43','#4b8cbd','#876a48','#888888']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,
    'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42})


def finish(fig,name):
    lp(F).mkdir(exist_ok=True)
    fig.text(.5,.992,WARN,ha='center',va='top',fontsize=7.5,color='#922d2d')
    fig.savefig(lp(F/(name+'.pdf')))
    fig.savefig(lp(F/(name+'.png')),dpi=600)
    plt.close(fig)
    doc=fitz.open(lp(F/(name+'.pdf')))
    assert len(doc)==1 and not doc[0].get_images()
    doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(str(lp(F/(name+'_publication_review.png'))))


def main():
    d=frame('VERIFIED_COHORT_AND_DESCRIPTORS.csv'); ranks=frame('NATIONAL_COMPONENT_REMOVAL_TRACT_RANKS.csv')
    s=sources(); g=gpd.read_file(s.source(MH+'sources/TRACT_FULL_3310.gpkg',AUTH)).set_index('tract_id').reindex(d.index).to_crs(4326)
    assert len(g)==2299 and g.geometry.notna().all()
    geo=g[['geometry']].join(d)
    fits=pd.read_csv(lp(OUT/'P2_VS_P2_CBM_K_DIAGNOSTICS.csv')).query("condition=='published'")
    evidence=pd.read_csv(lp(OUT/'K_EVIDENCE_MATRIX.csv'))
    prof=pd.read_csv(lp(OUT/'PER_CLUSTER_CBM_AND_RQ_PROFILES.csv'))
    group=pd.read_csv(lp(OUT/'CLUSTER_QUARTILE_HOSPITAL_GEOGRAPHY.csv'))
    comp=pd.read_csv(lp(OUT/'P2_VS_P2_CBM_MEMBERSHIP_COMPARISONS.csv'))
    size=pd.read_csv(lp(OUT/'PER_CLUSTER_SILHOUETTE_AND_SIZE.csv'))
    archive=np.load(lp(OUT/'REGISTERED_FIT_ARRAYS.npz')); keys={k:i for i,k in enumerate(archive['keys'])}
    def label(sp,k): return archive['labels'][keys[f'{sp}__published__k{k}__s42']]
    fig,axes=plt.subplots(2,2,figsize=(7.2,7.2));fig.subplots_adjust(left=.025,right=.92,bottom=.09,top=.925,wspace=.23,hspace=.18)
    for i,(ax,col,title) in enumerate(zip(axes.flat,['RPL_CBM','RPL_CBM_DOM1','RPL_CBM_DOM2','RPL_CBM_DOM3'],['Climate module','Heat domain','Wildfire domain','Extreme-events domain'])):
        geo.plot(column=col,ax=ax,cmap='YlGnBu',vmin=0,vmax=1,linewidth=0)
        ax.set_axis_off();ax.set_title(f'({chr(65+i)}) {title}')
        bar=fig.colorbar(plt.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0,1),cmap='YlGnBu'),ax=ax,fraction=.035,pad=.02)
        bar.solids.set_rasterized(False);bar.set_label('National percentile')
    fig.text(.04,.035,'Official CDC 2024 ranks unchanged; 2,299 frozen-positive-population tracts.\nNo earthquake indicator. Unresolved source-zero semantics are preserved, not corrected by these maps.',fontsize=7)
    finish(fig,'01_Official_CBM_and_domains')

    fig,axes=plt.subplots(2,2,figsize=(7.2,6.0));fig.subplots_adjust(left=.09,right=.97,bottom=.13,top=.90,wspace=.30,hspace=.40)
    q=pd.read_csv(lp(OUT/'CBM_COMPONENT_REMOVAL_RANK_QA.csv')).set_index('diagnostic')
    titles={'no_riverine':'No riverine','no_burn':'No burned area','no_heat':'No heat','no_wildfire':'No wildfire indicators'}
    for i,(name,ax) in enumerate(zip(REMOVALS,axes.flat)):
        ax.scatter(d.RPL_CBM,ranks[name],s=3,alpha=.25,color='#277b83')
        ax.plot([0,1],[0,1],color='#999999',lw=.7)
        ax.set(xlim=(0,1),ylim=(0,1),xlabel='Official CDC CBM',ylabel='Researcher national rerank')
        ax.set_title(f'({chr(65+i)}) {titles[name]}')
        ax.text(.03,.96,f'rho={q.loc[name,"Spearman"]:.3f}\nTop-230 retained: {q.loc[name,"top230_retention"]:.1%}',transform=ax.transAxes,va='top',fontsize=7)
    fig.text(.05,.035,'Fixed eligible national universe: 83,509 tracts. Researcher diagnostics, NOT official CDC alternatives.\nNational recalibration and local rank changes are different effects; no new physical observations are created.',fontsize=7)
    finish(fig,'02_National_component_removal_ranks')

    c=frozen(s,CB+'CBM_DOMAIN_AND_INDICATOR_CONTRIBUTIONS.csv',key='component').query("type=='indicator'").reindex(CODES)
    fig,axes=plt.subplots(1,2,figsize=(7.2,4.9));fig.subplots_adjust(left=.16,right=.97,bottom=.20,top=.86,wspace=.5)
    short=['Heat','Smoke','Burned area','Coastal flood','Drought','Riverine flood','Hurricane','Wind','Tornado']
    axes[0].barh(range(9),c.covariance_share_of_local_SPL_variance*100,color='#277b83')
    axes[0].set_yticks(range(9),short);axes[0].invert_yaxis();axes[0].set_xlabel('Local score covariance share (%)');axes[0].set_title('(A) Published score composition')
    for sp in ['H1','H2']:
        for name,ls in zip(REMOVALS,['-','--',':','-.']):
            part=comp.loc[comp.comparison.eq('component')&comp.specification.eq(sp)&comp.alternative.eq('component_'+name)]
            avg=part.groupby('k').ARI.mean();axes[1].plot(avg.index,avg,marker='o',color=COLORS[sp],ls=ls,lw=1,label=sp+' / '+titles[name])
    axes[1].set(xlabel='K',ylabel='ARI with published-as-is fit',ylim=(0,1.02),xticks=[3,4,5]);axes[1].set_title('(B) Component-removal memberships')
    axes[1].legend(loc='lower left',fontsize=6,frameon=False)
    fig.text(.04,.045,'Covariance shares are not causal weights. Component fits use only registered K3-5 and seeds42-46.\nRemoving burned area tests leverage; it does not identify which of 2,251 unresolved zeros is invalid.',fontsize=7)
    finish(fig,'03_Component_influence_and_clustering')

    fig,axes=plt.subplots(1,2,figsize=(7.2,4.4));fig.subplots_adjust(left=.10,right=.98,bottom=.22,top=.85,wspace=.32)
    for sp in BUDGETS:
        part=fits.loc[fits.specification.eq(sp)]; m=part.groupby('k').WCSS.mean()
        axes[0].plot(m.index,m,marker='o',color=COLORS[sp],label=sp)
        sil=part.loc[part.k.gt(1)].groupby('k').mean_silhouette.agg(['mean','min','max'])
        axes[1].plot(sil.index,sil['mean'],marker='o',color=COLORS[sp],label=sp)
        axes[1].fill_between(sil.index,sil['min'],sil['max'],color=COLORS[sp],alpha=.16)
    axes[0].set(xlabel='K',ylabel='Weighted-space WCSS',xticks=range(1,9));axes[0].set_title('(A) Elbow curves')
    axes[1].set(xlabel='K',ylabel='Full-cohort mean silhouette',xticks=KS);axes[1].set_title('(B) Five seeds; bands show range')
    axes[0].legend(frameon=False)
    fig.text(.045,.045,'Silhouette is conditional on each feature space, not a common physical-quality score.\nEndpoint-chord bends are checked for K1-6/7/8; neither bend nor silhouette automatically selects K.',fontsize=7)
    finish(fig,'04_Elbow_and_silhouette')

    fig,axes=plt.subplots(2,3,figsize=(7.2,6.8));fig.subplots_adjust(left=.025,right=.98,bottom=.15,top=.91,wspace=.07,hspace=.20)
    for row,k in enumerate([3,4]):
        for col,sp in enumerate(BUDGETS):
            ax=axes[row,col]; geo.plot(color=[CLASS[c] for c in label(sp,k)],ax=ax,linewidth=0)
            ax.set_axis_off();ax.set_title(f'{sp} / K{k}',fontsize=9)
    fig.legend(handles=[Patch(color=CLASS[c],label=f'C{c+1}') for c in range(4)],loc='lower center',bbox_to_anchor=(.5,.078),ncol=4,frameon=False)
    fig.text(.04,.025,'Seed42; model-specific IDs ordered by mean total frozen burden, NOT formal Stage7 IDs.\nColors do not imply matched classes across models. Exact Hungarian transitions are reported separately.',fontsize=7)
    finish(fig,'05_Model_specific_membership_maps')

    fig,axes=plt.subplots(2,1,figsize=(7.2,4.8));fig.subplots_adjust(left=.025,right=.975,bottom=.15,top=.88,hspace=.45)
    variables=['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','RPL_CBM']
    for ax,sp in zip(axes,['H1','H2']):
        p=prof.loc[prof.specification.eq(sp)&prof.condition.eq('published')&prof.k.eq(3)].pivot(index='cluster',columns='variable',values='mean')
        gr=group.loc[group.specification.eq(sp)&group.condition.eq('published')&group.k.eq(3)].set_index('cluster')
        data=[]
        for cl,row in p.iterrows():
            n=int(gr.loc[cl,'n_tracts']);pct=100*gr.loc[cl,'population']/d.Population.sum()
            data.append([f'C{cl+1}',f'{n:,}',f'{pct:.1f}',f'{row.Init_Supply*100:.3f}',f'{row.Grid_Impact:.3f}',f'{row.Redundancy_HHI:.3f}',f'{row.B_Unconstrained:.2f}',f'{row.MeanDelta:.2f}',f'{row.SOVI_SCORE:.1f}',f'{row.RPL_CBM:.3f}'])
        ax.set_axis_off();ax.set_title(sp+' / K3: original-unit class means',pad=9)
        table=ax.table(cellText=data,colLabels=['Class','Tracts','Pop %','Init %','Impact','HHI','B_U h','Delta h','SOVI','CBM'],loc='center',cellLoc='center')
        table.auto_set_font_size(False);table.set_fontsize(7);table.scale(1,1.55)
        for (r,c),cell in table.get_celld().items():
            cell.set_linewidth(.25);cell.set_edgecolor('#cccccc')
            if r==0: cell.set_facecolor('#e8ebed')
    fig.text(.035,.035,'Model-specific IDs; complete mean/median/P10/P90 profiles for every K are in the CSV.\nB_U and Delta are full-service-deficit hours. CBM is a percentile, not hazard intensity or outage risk.',fontsize=7)
    finish(fig,'06_Original_unit_research_question_profiles')

    fig,axes=plt.subplots(1,3,figsize=(7.2,4.6));fig.subplots_adjust(left=.07,right=.98,bottom=.23,top=.84,wspace=.36)
    for sp in BUDGETS:
        p=evidence.loc[evidence.specification.eq(sp)].set_index('k')
        for ax,col,title in zip(axes,['seed_min_ARI','geographic_min_ARI','policy_LOO_min_ARI'],['Seed stability (minimum)','Geographic leave-out (minimum)','Policy-set LOO (minimum)']):
            ax.plot(p.index,p[col],marker='o',lw=1.2,color=COLORS[sp],label=sp)
            ax.set(xlabel='K',ylim=(0,1.03),xticks=KS);ax.set_title(title,fontsize=8)
    axes[0].set_ylabel('ARI to corresponding baseline');axes[0].legend(frameon=False)
    fig.text(.04,.045,'Geographic: four frozen quadrants, training-only scaling. Policy: five LOO sets, cohort scaling.\nPerturbations use seed42; initializations use seeds42-46. These are sensitivity diagnostics, not independent validation.',fontsize=7)
    finish(fig,'07_Policy_and_geographic_robustness')

    fig,axes=plt.subplots(2,2,figsize=(7.2,5.6));fig.subplots_adjust(left=.10,right=.98,bottom=.15,top=.89,wspace=.32,hspace=.40)
    for sp in ['H1','H2']:
        p=comp.loc[comp.comparison.eq('feature_specification')&comp.specification.eq('P2')&comp.alternative.eq(sp)].groupby('k').mean(numeric_only=True)
        axes[0,0].plot(p.index,p.ARI,marker='o',color=COLORS[sp],label='P2 to '+sp)
        axes[0,1].plot(p.index,100*p.reassigned_population_share,marker='o',color=COLORS[sp],label=sp)
    axes[0,0].set(xlabel='K',ylabel='ARI',ylim=(0,1.02),xticks=KS);axes[0,0].set_title('(A) New versus seven-coordinate model');axes[0,0].legend(frameon=False)
    axes[0,1].set(xlabel='K',ylabel='Reassigned resident population (%)',xticks=KS);axes[0,1].set_title('(B) Hungarian display alignment')
    for sp in BUDGETS:
        p=evidence.loc[evidence.specification.eq(sp)]
        axes[1,0].plot(p.k,100*p.RQ3_between_share,marker='o',color=COLORS[sp],label=sp)
        p=size.loc[size.specification.eq(sp)&size.condition.eq('published')&size.seed.eq(42)&size.k.gt(1)]
        rc=p.sort_values('rare34_members').groupby('k').tail(1).sort_values('k')
        axes[1,1].plot(rc.k,rc.n_tracts,marker='o',color=COLORS[sp],label=sp)
    axes[1,0].set(xlabel='K',ylabel='Observed between-class RQ3 share (%)',xticks=KS);axes[1,0].set_title('(C) Assigned 1/3 is not realized 1/3')
    axes[1,1].set(xlabel='K',ylabel='Size of class containing most Q tracts',xticks=KS);axes[1,1].set_title('(D) Frozen 34-tract Q group')
    axes[1,1].set_yscale('log');axes[1,0].legend(frameon=False)
    fig.text(.04,.028,'Reassignment includes feature addition AND RQ3 budget changes. Q means a retained source proxy;\nabout 1.815% initial service is not strong absolute resilience. All special-use tracts remain represented.',fontsize=7)
    finish(fig,'08_Reassignment_population_and_rare_group')
    save('SOURCE_HASH_VERIFICATION_FIGURES.csv',s.records)
    print('Eight vector PDFs and 600dpi previews generated',flush=True)


if __name__=='__main__': main()
