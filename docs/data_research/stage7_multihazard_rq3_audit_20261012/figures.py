"""Actual-value source diagnostics; no cluster models and no synthetic imagery."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import geopandas as gpd
import fitz
from common import *

LABEL='AUTHOR REVIEW \u2014 NOT FORMAL STAGE 7'
F=OUT/'figures'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,
    'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42})


def finish(fig,name):
    lp(F).mkdir(exist_ok=True)
    fig.text(.5,.99,LABEL,ha='center',va='top',fontsize=8,color='#862c2c')
    fig.savefig(lp(F/(name+'.pdf')),bbox_inches=None)
    fig.savefig(lp(F/(name+'.png')),dpi=600,bbox_inches=None)
    plt.close(fig)
    doc=fitz.open(lp(F/(name+'.pdf')))
    assert len(doc)==1 and 'AUTHOR REVIEW' in doc[0].get_text()
    doc[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(str(lp(F/(name+'_publication_review.png'))))


def main():
    v=pd.read_csv(lp(OUT/'PHYSICAL_HAZARD_TRACT_VALUES.csv'),dtype={'tract_id':str}).set_index('tract_id')
    d=pd.read_csv(lp(OUT/'FROZEN_P2_AND_COHORT.csv'),dtype={'tract_id':str}).set_index('tract_id').reindex(v.index)
    g=gpd.read_file(lp(OUT/'sources/TRACT_FULL_3310.gpkg')).set_index('tract_id').reindex(v.index).to_crs(4326)
    data=g.join(v)
    fig,axes=plt.subplots(3,2,figsize=(7.2,9.3));fig.subplots_adjust(left=.035,right=.94,bottom=.055,top=.945,hspace=.30,wspace=.11)
    panels=[('tract_seismic_PGA','(A) Earthquake: supported land mean','PGA (g)','YlOrRd'),
        ('Historical_heat_days_2018_2022','(B) Historical extreme heat','Days/year (2018-2022)','YlOrRd'),
        ('Wildfire_high_land_fraction','(C) High / Very High FHSZ','Land fraction','Oranges'),
        ('Wildfire_FHSZ_mapped_land_fraction','(D) Fire classification coverage','Mapped land fraction','viridis'),
        ('Flood_SFHA_land_fraction_complete','(E) Determinate SFHA overlap','Land fraction','Blues'),
        ('Flood_known_zones_land_fraction','(F) Known flood-zone coverage','Known land fraction','viridis')]
    for ax,(c,title,unit,cmap) in zip(axes.flat,panels):
        data.plot(column=c,ax=ax,cmap=cmap,linewidth=0,legend=False,
            missing_kwds={'color':'#d5d5d5','label':'Incomplete support'})
        values=data[c].dropna();norm=matplotlib.colors.Normalize(values.min(),values.max())
        color=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,fraction=.036,pad=.02)
        color.solids.set_rasterized(False)
        color.set_label(unit);ax.set_title(title,pad=4);ax.set_axis_off()
    fig.text(.04,.022,'Grey: incomplete source support. Area and point values do not locate residents; no multi-hazard damage simulation.',fontsize=7)
    finish(fig,'01_physical_hazard_context')
    loss=pd.read_csv(lp(OUT/'HAZARD_EXPECTED_LOSS_CONTRIBUTIONS.csv'))
    fig,axes=plt.subplots(1,2,figsize=(7.2,4.6));fig.subplots_adjust(left=.08,right=.97,top=.85,bottom=.25,wspace=.60)
    eq=loss.loc[loss.prefix.eq('ERQK'),'pooled_share'].iloc[0]*100
    axes[0].bar(['Earthquake','Other applicable\nhazards'],[eq,100-eq],color=['#c54b3e','#286c9a'],width=.62)
    axes[0].set_ylim(0,110);axes[0].set_ylabel('Share of pooled expected annual loss (%)')
    axes[0].set_title('(A) FEMA NRI v1.19; 2,299 tracts')
    for i,y in enumerate([eq,100-eq]):axes[0].text(i,y+2,f'{y:.3f}%',ha='center',fontsize=8)
    other=loss.loc[~loss.prefix.eq('ERQK')&loss.pooled_share.notna()].sort_values('pooled_share')
    axes[1].barh(other.hazard,other.pooled_share*100,color='#286c9a')
    axes[1].set_xlabel('Share of total EAL (%)');axes[1].set_title('(B) Non-earthquake contributions')
    fig.text(.06,.035,'Avalanche, hurricane, ice storm and volcanic activity: source null / not applicable, not measured zeros.\nEAL is loss-based; it is not a balanced physical-exposure coordinate.',fontsize=7)
    finish(fig,'02_expected_loss_composition')
    fig,axes=plt.subplots(1,3,figsize=(7.2,3.2));fig.subplots_adjust(left=.07,right=.98,bottom=.25,top=.82,wspace=.48)
    specs=[('tract_seismic_PGA','PGA_centroid_IDW_g','PGA land mean (g)','Centroid estimate (g)'),
        ('Wildfire_high_land_fraction','Wildfire_high_centroid_flag','High-FHSZ land fraction','Centroid in High / Very High'),
        ('Flood_SFHA_land_fraction_complete','Flood_SFHA_centroid_flag','SFHA land fraction','Centroid in SFHA')]
    for i,(ax,(x,y,xlabel,ylabel)) in enumerate(zip(axes,specs)):
        pair=v[[x,y]].dropna();ax.scatter(pair[x],pair[y],s=4,alpha=.28,color='#286c9a',rasterized=False)
        ax.set_xlabel(xlabel);ax.set_ylabel(ylabel);ax.set_title(f'({chr(65+i)}) n = {len(pair):,}')
        if i:ax.set_yticks([0,1])
    fig.text(.06,.055,'Binary point intersection and exposed area fraction are different measurements.\nA centroid is not the location of residents; unmapped fire and D flood areas are not zero hazard.',fontsize=7)
    finish(fig,'03_point_polygon_support')
    corr=pd.read_csv(lp(OUT/'PHYSICAL_PLUS_P2_PAIRWISE.csv'))
    p2=['SOVI_SCORE','log1p_Population','Init_Supply','B_Unconstrained','MeanDelta']
    h=['tract_seismic_PGA','Wildfire_high_land_fraction','Flood_SFHA_land_fraction_complete','Historical_heat_days_2018_2022']
    mat=np.full((4,5),np.nan)
    for i,a in enumerate(h):
        for j,b in enumerate(p2):
            row=corr.loc[((corr.variable_a==a)&(corr.variable_b==b))|((corr.variable_b==a)&(corr.variable_a==b))]
            mat[i,j]=row.same_cohort_Spearman.iloc[0]
    fig,axes=plt.subplots(1,2,figsize=(7.2,4.1),gridspec_kw={'width_ratios':[1.7,1]})
    fig.subplots_adjust(left=.19,right=.94,top=.82,bottom=.28,wspace=.85)
    im=axes[0].pcolormesh(np.arange(6)-.5,np.arange(5)-.5,mat,vmin=-1,vmax=1,cmap='RdBu_r',rasterized=False)
    axes[0].invert_yaxis()
    axes[0].set_xticks(range(5),['SOVI','log1p(Pop)','Initial\nservice','Baseline\nburden','Mean\nincrement'],rotation=35,ha='right')
    axes[0].set_yticks(range(4),['PGA','Fire area','Flood area','Historical heat'])
    for i in range(4):
        for j in range(5):axes[0].text(j,i,f'{mat[i,j]:.2f}',ha='center',va='center',fontsize=7)
    axes[0].set_title('(A) Spearman; same 2,032 complete cases')
    color=fig.colorbar(im,ax=axes[0],fraction=.045,pad=.03)
    color.solids.set_rasterized(False)
    valid=[int(v[c].notna().sum()) for c in h]
    axes[1].barh(range(4),valid,color='#286c9a');axes[1].set_yticks(range(4),['PGA','Fire','Flood','Heat'])
    axes[1].invert_yaxis();axes[1].set_xlim(0,2800);axes[1].set_xlabel('Complete tract values')
    axes[1].axvline(2299,color='#862c2c',linewidth=.9,linestyle='--');axes[1].set_title('(B) Coverage gate')
    for i,n in enumerate(valid):axes[1].text(n+30,i,str(n),va='center',fontsize=7)
    fig.text(.055,.055,'Complete-case associations are diagnostics only; 267 eligible tracts lack at least one complete polygon measure.\nNo physical composite or eight-variable K-means fit is admitted.',fontsize=7)
    finish(fig,'04_incremental_information_and_coverage')
    print('Four vector PDFs and 600dpi previews created',flush=True)


if __name__=='__main__':main()
