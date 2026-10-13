"""Seven publication-size review figures, using actual frozen tables and polygons."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import geopandas as gpd
import fitz
from common import *

COLORS={'P2':'#277b83','H1':'#bc573d','H2':'#6e56a0'}
CLASS=['#277b83','#dfae2b','#7452a4','#c45242','#648c39','#4d8dbe','#89634b','#888888']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,
     'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42})


def finish(fig,name,note):
    fig.text(.5,.988,WARN,ha='center',va='top',fontsize=6.9,color='#922d2d')
    fig.text(.045,.025,note,ha='left',va='bottom',fontsize=7)
    fig.savefig(destination('figures/'+name+'.pdf'))
    fig.savefig(destination('figures/'+name+'.png'),dpi=600)
    plt.close(fig)
    doc=fitz.open(lp(OUT/'figures'/f'{name}.pdf'));assert len(doc)==1 and not doc[0].get_images()
    doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(str(destination('figures/'+name+'_publication_review.png')))


def main():
    s=source_reader();d=frame('VERIFIED_EIGHT_VARIABLE_COHORT.csv','tract_id')
    g=gpd.read_file(s.source(MH+'sources/TRACT_FULL_3310.gpkg',AUTH)).set_index('tract_id').reindex(d.index).to_crs(4326)
    assert len(g)==2299 and g.geometry.notna().all()
    geo=g[['geometry']].join(d)
    f=np.load(lp(OUT/'REUSED_MAIN_FIT_ARRAYS.npz'));keys={k:i for i,k in enumerate(f['keys'])}
    lab=lambda sp,k:f['labels'][keys[f'{sp}__published__k{k}__s42']]
    evidence=frame('EIGHT_VARIABLE_K_EVIDENCE.csv');fits=frame('ALL_REGISTERED_K_AND_SEED_DIAGNOSTICS.csv')
    profiles=frame('EIGHT_VARIABLE_CLUSTER_PROFILES.csv');per=frame('PER_CLUSTER_SILHOUETTE_AND_SIZE.csv')
    fig,axes=plt.subplots(2,2,figsize=(7.2,6.8));fig.subplots_adjust(left=.025,right=.94,bottom=.12,top=.915,wspace=.18,hspace=.2)
    for ax,col,title in zip(axes.flat,['RPL_CBM','RPL_CBM_DOM1','RPL_CBM_DOM2','RPL_CBM_DOM3'],['Official climate burden','Heat','Wildfire','Extreme events']):
        geo.plot(column=col,ax=ax,cmap='YlGnBu',vmin=0,vmax=1,linewidth=0)
        ax.set_axis_off();ax.set_title(title)
        bar=fig.colorbar(plt.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0,1),cmap='YlGnBu'),ax=ax,fraction=.03,pad=.02)
        bar.solids.set_rasterized(False);bar.set_label('National percentile',fontsize=7)
    finish(fig,'01_Climate_hazard_coordinate_and_domains','Official published-as-is CDC 2024 ranks; all 2,299 frozen-positive-population tracts.\nNo earthquake component; full ranks do not certify complete original physical observations.')

    fig,axes=plt.subplots(1,2,figsize=(7.2,4.6));fig.subplots_adjust(left=.19,right=.97,bottom=.20,top=.87,wspace=.48)
    q=frame('MULTIHAZARD_COMPONENT_AND_COVERAGE_QA.csv').set_index('indicator').reindex(CODES)
    names=['Heat days','Smoke days','Burned area','Coastal flood','Drought','Riverine flood','Hurricane','Strong wind','Tornado']
    axes[0].barh(range(9),q.covariance_share_of_local_SPL*100,color='#277b83');axes[0].invert_yaxis();axes[0].set_yticks(range(9),names)
    axes[0].set(xlabel='Signed local score covariance share (%)',title='(A) Local component concentration')
    cov=[2299,1879,2032];labels=['CDC CBM rank','PRISM same-ID only','Four physical layers']
    axes[1].barh(range(3),cov,color=['#6e56a0','#999999','#4d8dbe']);axes[1].set_yticks(range(3),labels);axes[1].invert_yaxis()
    axes[1].set(xlim=(0,2400),xlabel='Tracts with stated support',title='(B) Candidate coverage gate')
    for i,n in enumerate(cov):axes[1].text(n+20,i,str(n),va='center',fontsize=7)
    finish(fig,'02_Hazard_content_and_alternative_coverage','Covariance shares are not causal weights or independent hazard counts. PRISM matches are identifiers,\nnot boundary-verified measurements. NASA raster unavailable; no missing-to-zero fills or new exclusions.')

    fig,axes=plt.subplots(1,2,figsize=(7.2,4.5));fig.subplots_adjust(left=.10,right=.975,bottom=.21,top=.86,wspace=.32)
    for sp in ['P2','H1','H2']:
        part=fits.loc[fits.specification.eq(sp)&fits.condition.eq('published')]
        m=part.groupby('k').WCSS.mean();sil=part.loc[part.k.gt(1)].groupby('k').mean_silhouette.agg(['mean','min','max'])
        name={'P2':'P2: 7-variable ablation','H1':'H1: RQ3 equal sensitivity','H2':'H2: 8-variable candidate'}[sp]
        axes[0].plot(m.index,m,marker='o',color=COLORS[sp],lw=1.2,label=name)
        axes[1].plot(sil.index,sil['mean'],marker='o',color=COLORS[sp],lw=1.2)
        axes[1].fill_between(sil.index,sil['min'],sil['max'],color=COLORS[sp],alpha=.17)
    axes[0].set(xlabel='K',ylabel='Weighted Euclidean WCSS',xticks=range(1,9),title='(A) Smooth Elbow curves')
    axes[1].set(xlabel='K',ylabel='Full-cohort mean silhouette',xticks=range(2,9),title='(B) Seeds 42-46; range bands')
    axes[0].legend(frameon=False,fontsize=6.5)
    finish(fig,'03_Seven_eight_variable_elbow_and_silhouette','H2 bends: K3 for K1-6/7, K4 for K1-8. Silhouette peaks at K5; K4/5 seed ranges overlap.\nDifferent feature-space silhouettes are internal diagnostics, not a shared physical-quality scale.')

    fig,axes=plt.subplots(1,3,figsize=(7.2,4.2));fig.subplots_adjust(left=.025,right=.975,bottom=.19,top=.86,wspace=.05)
    for ax,k in zip(axes,[3,4,5]):
        geo.plot(color=[CLASS[c] for c in lab('H2',k)],ax=ax,linewidth=0);ax.set_axis_off();ax.set_title('H2 / K'+str(k))
    fig.legend(handles=[Patch(color=CLASS[c],label=f'C{c+1}') for c in range(5)],ncol=5,frameon=False,loc='lower center',bbox_to_anchor=(.5,.105))
    finish(fig,'04_Eight_variable_membership_maps','Seed42, complete 2,299-tract cohort. IDs are model-specific, ordered by total frozen burden.\nColors are not an assertion of matched classes across K. No formal Stage7 IDs replaced.')

    fig,axes=plt.subplots(2,4,figsize=(7.2,5.2));fig.subplots_adjust(left=.075,right=.97,bottom=.17,top=.88,wspace=.52,hspace=.50)
    variables=['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','Population','Published_RPL_CBM']
    titles=['RQ1: Initial service (%)','RQ1: Spectral impact','RQ1: Dependency HHI','RQ2: Unconstrained loss (h)','RQ2: Mean increment (h)','RQ3: SOVI (0-100)','RQ3: Population (persons)','RQ3: Climate rank (0-1)']
    for ax,col,title in zip(axes.flat,variables,titles):
        p=profiles.loc[profiles.specification.eq('H2')&profiles.condition.eq('published')&profiles.k.eq(4)&profiles.variable.eq(col)].sort_values('cluster')
        factor=100 if col=='Init_Supply' else 1
        mean=p['mean'].to_numpy()*factor;lower=p.p10.to_numpy()*factor;upper=p.p90.to_numpy()*factor
        ax.vlines(np.arange(1,5),lower,upper,color=CLASS[:4],lw=2,alpha=.55)
        ax.scatter(np.arange(1,5),mean,c=CLASS[:4],s=22,zorder=3)
        ax.axhline(p.cohort_mean.iloc[0]*factor,color='#555555',ls=':',lw=.8)
        ax.set(xticks=range(1,5),xticklabels=['C1','C2','C3','C4']);ax.set_title(title,fontsize=7.5)
        ax.ticklabel_format(axis='y',style='plain',useOffset=False);ax.spines[['top','right']].set_visible(False)
    finish(fig,'05_Original_unit_three_RQ_profiles','H2/K4 seed42: dots=class means; vertical lines=P10-P90; dotted=cohort mean.\nCounts C1-C4: 38 / 1,228 / 440 / 593. Population is shown in persons but fitted as log1p.')

    fig,axes=plt.subplots(1,2,figsize=(7.2,4.9));fig.subplots_adjust(left=.19,right=.975,bottom=.20,top=.86,wspace=.37)
    q=frame('HAZARD_COMPONENT_SENSITIVITY.csv');order=['NEHD','SMOKE','BURN','CFLD','DRGT','RFLD','HRCN','SWND','TRND','Wildfire','Extreme_Events']
    for k,color in zip([3,4,5],['#277b83','#dfae2b','#6e56a0']):
        p=q.loc[q.k.eq(k)].set_index('removed').reindex(order)
        axes[0].plot(p.ARI,np.arange(len(order)),marker='o',color=color,label='K'+str(k))
        axes[1].plot(p.reassigned_population_share*100,np.arange(len(order)),marker='o',color=color)
    short=['Heat','Smoke','Burned area','Coastal flood','Drought','Riverine flood','Hurricane','Wind','Tornado','Wildfire domain','Extreme events']
    axes[0].set_yticks(range(len(order)),short);axes[0].invert_yaxis();axes[1].set_yticks(range(len(order)),[]);axes[1].invert_yaxis()
    axes[0].set(xlim=(.89,1.005),xlabel='ARI to published-as-is H2',title='(A) Hazard-removal partitions')
    axes[1].set(xlabel='Reassigned population (%)',title='(B) Matched-label display changes')
    axes[0].legend(frameon=False,fontsize=7)
    finish(fig,'06_Hazard_sensitivity_and_tract_reassignment','Researcher national reranks, fixed 83,509 eligibility and exact ties; NOT official CDC indices.\nSeed42, K3-5; major removals reused, remaining removals narrowly fitted. Source-zero ambiguity remains.')

    fig,axes=plt.subplots(1,3,figsize=(7.2,4.4));fig.subplots_adjust(left=.075,right=.975,bottom=.22,top=.85,wspace=.40)
    for sp in ['P2','H1','H2']:
        p=evidence.loc[evidence.specification.eq(sp)].sort_values('k')
        for ax,col,title in zip(axes,['seed_min_ARI','geographic_min_ARI','policy_LOO_min_ARI'],['Seeds 42-46','Geographic leave-block-out','Policy-set leave-one-out']):
            ax.plot(p.k,p[col],color=COLORS[sp],marker='o',lw=1,label=sp)
            ax.set(xticks=range(2,9),ylim=(0,1.03),xlabel='K');ax.set_title(title,fontsize=8)
    axes[0].set_ylabel('Minimum membership ARI');axes[0].legend(frameon=False)
    finish(fig,'07_Geographic_and_policy_set_stability','P2 is ablation; H2 is intended eight-variable candidate. Geographic/policy fits use seed42;\ngeographic training-only scaling; policy cohort scaling. Neither is independent scientific validation.')
    save('SOURCE_HASH_VERIFICATION_FIGURES.csv',s.records)
    print('Seven vector PDFs and 600 dpi previews created',flush=True)


if __name__=='__main__':main()
