"""Publication-size visualizations of saved candidate and spatial diagnostics."""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import font_manager
from pyproj import Transformer

COLORS={'C1':'#0072B2','C2':'#E69F00','C3':'#009E73','C4':'#D55E00'}
MODEL_COLORS={'D':'#0072B2','EAL':'#D55E00'}
SMALL_BLUE='#0072B2'; ADD_ORANGE='#E69F00'
NAMES=['C1','C2','C3','C4']
MM=1/25.4

def setup():
    assert 'arial' in font_manager.findfont('Arial',fallback_to_default=False).lower()
    plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.titlesize':9.5,
        'axes.labelsize':8.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,
        'legend.fontsize':7.5,'axes.linewidth':.6,'lines.linewidth':1.2,
        'patch.linewidth':.5,'xtick.major.width':.6,'ytick.major.width':.6,
        'pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white','figure.facecolor':'white'})

def save(fig,out,name):
    fig.savefig(out/(name+'.pdf'))
    fig.savefig(out/(name+'.png'),dpi=600)
    plt.close(fig)

def map_axes(ax,g,classified,legend=False):
    g.plot(ax=ax,facecolor='#FAFAFA',edgecolor='#C1C1C1',linewidth=.15)
    for c in NAMES:
        g.loc[g.candidate_cluster==c].plot(ax=ax,color=COLORS[c],edgecolor='white',linewidth=.12)
    unknown=g.loc[g.classification_status=='UNCLASSIFIED_GEOMETRY']
    if len(unknown):unknown.plot(ax=ax,color='#A0A0A0',edgecolor='#404040',linewidth=.5)
    gpd.GeoSeries([g.geometry.union_all().boundary],crs=g.crs).plot(ax=ax,color='#666666',linewidth=.5)
    ax.set_aspect('equal');ax.set_axis_off()
    if legend:
        counts=classified.candidate_cluster.value_counts()
        handles=[Patch(facecolor=COLORS[c],label=f'{c} ({counts[c]:,} tracts)') for c in NAMES]
        handles += [Patch(facecolor='#A0A0A0',label='Unclassified (4 tracts)'),
                    Patch(facecolor='#FAFAFA',edgecolor='#999999',label='No residents (24 tracts)')]
        ax.legend(handles=handles,loc='upper right',bbox_to_anchor=(1.02,1),frameon=True,
                  edgecolor='none',facecolor='white',framealpha=1,title='Candidate class',title_fontsize=8,
                  handlelength=1.5,labelspacing=.55,borderpad=.6)

def scale_north(ax,g):
    x0,y0,x1,y1=g.total_bounds; dx=x1-x0;dy=y1-y0
    x=x0+.05*dx;y=y0-.08*dy
    ax.plot([x,x+20000],[y,y],color='#333333',lw=1.1)
    ax.plot([x,x],[y-1500,y+1500],color='#333333',lw=.8)
    ax.plot([x+20000,x+20000],[y-1000,y+1000],color='#333333',lw=.8)
    ax.text(x+10000,y+2000,'20 km',ha='center',va='bottom',fontsize=8)
    ax.set_ylim(y0-.12*dy,y1+.04*dy)
    x=x0-.015*dx;y=y1-.14*dy
    to_geo=Transformer.from_crs(3310,4326,always_xy=True);to_map=Transformer.from_crs(4326,3310,always_xy=True)
    lon,lat=to_geo.transform(x,y);xn,yn=to_map.transform(lon,lat+.1)
    vec=np.array([xn-x,yn-y]);vec=vec/np.linalg.norm(vec)*.06*dy
    ax.annotate('',xy=(x+vec[0],y+vec[1]),xytext=(x,y),zorder=20,arrowprops={'arrowstyle':'-|>','lw':1.1,'color':'black'})
    ax.text(x+vec[0],y+vec[1]+3000,'N',ha='center',fontsize=8)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);args=ap.parse_args()
    repo=args.repo;root=repo/'docs/data_research/built_environment_20261009';out=root/'manuscript_integration_preview_20261010';s=root/'spatial_k4_validation_20261010'
    setup();lab=pd.read_csv(out/'STAGE7_CANDIDATE_LABELS_2291.csv',dtype={'tract_id':str})
    d=pd.read_csv(out/'CLASSIFIED_FEATURE_VALUES_2287.csv',dtype={'tract_id':str})
    g=gpd.read_file(repo/'Data/LA_Tracts_With_Population.shp');g['tract_id']=g.GEOID.astype(str).str.zfill(11)
    universe=pd.read_csv(root/'local_joint_feature_extraction_20261009/TRACT_FEATURE_CANDIDATES.csv',dtype={'tract_id':str})
    assert len(universe)==2315 and universe.tract_id.is_unique
    assert g.tract_id.is_unique and set(universe.tract_id)<=set(g.tract_id)
    g=g.set_index('tract_id',drop=False).loc[universe.tract_id].reset_index(drop=True)
    assert len(g)==2315 and set(lab.tract_id)<=set(g.tract_id)
    assert g.geometry.is_valid.all() and not g.geometry.is_empty.any()
    g=g.to_crs(3310).merge(lab[['tract_id','candidate_cluster','classification_status']],on='tract_id',how='left',validate='one_to_one')
    assert g.candidate_cluster.notna().sum()==2287 and g.classification_status.eq('UNCLASSIFIED_GEOMETRY').sum()==4
    fig,ax=plt.subplots(figsize=(185*MM,165*MM));fig.subplots_adjust(left=.025,right=.975,bottom=.02,top=.94)
    map_axes(ax,g,d,legend=True);scale_north(ax,g)
    ax.set_title('Four-class joint community typology',pad=8)
    save(fig,out,'FIG_STAGE7_TYPOLOGY_MAP')

    freeze=json.loads((out/'STAGE7_CANDIDATE_FREEZE.json').read_text());p=np.load(out/'STAGE7_CANDIDATE_PARAMETERS.npz')
    columns=freeze['coordinate_order'];z=(d[columns].to_numpy()-p['scaler_mean'])/p['scaler_std']
    values=np.stack([z[d.candidate_cluster.eq(c)].mean(axis=0) for c in NAMES],axis=1)
    short=['Service loss (h)','Initial service availability','Mapped degree','Mapped network impact',
           'Mapped betweenness','Dependency concentration','Land-use entropy','Building footprint fraction',
           'Pre-1970 building-area fraction','Social vulnerability score',
           'Building value (log scale)','Multi-hazard loss-rate percentile']
    fig=plt.figure(figsize=(185*MM,145*MM));ax=fig.add_axes([.45,.20,.48,.70])
    cmap=LinearSegmentedColormap.from_list('profile',['#3B75A3','#F5F5F5','#C34C35'])
    im=ax.pcolormesh(np.arange(-.5,4.5),np.arange(-.5,12.5),values,vmin=-1.5,vmax=1.5,cmap=cmap,shading='flat',rasterized=False)
    ax.set_xlim(-.5,3.5);ax.set_ylim(11.5,-.5)
    ax.set_xticks(range(4),[f'{c}\nn = {(d.candidate_cluster==c).sum():,}' for c in NAMES])
    ax.set_yticks(range(12),short)
    for t in ax.get_yticklabels():t.set_horizontalalignment('right')
    ax.tick_params(axis='both',length=0,pad=5)
    for i in range(12):
        for j in range(4):
            v=values[i,j];ax.text(j,i,f'{v:+.2f}',ha='center',va='center',fontsize=7.5,
                                  color='white' if abs(v)>1 else '#222222')
    # Domain grouping uses subtle rules and a narrow adjacent color-free strip.
    bounds=[0,2,6,9,10,12]
    for y in bounds[1:-1]:ax.axhline(y-.5,color='#444444',lw=.65)
    for a,b,title in zip(bounds[:-1],bounds[1:],['Recovery /\ninitial service','Grid\ndependency','Built\nenvironment','Social\nvulnerability','Economic stock /\nmulti-hazard loss']):
        fig.text(.035,.90-((a+b)/2)*(.70/12),title,va='center',ha='left',fontsize=7.5,color='#555555')
    cax=fig.add_axes([.45,.075,.48,.022]);cb=fig.colorbar(im,cax=cax,orientation='horizontal',extend='both',ticks=[-1.5,-1,0,1,1.5])
    cb.solids.set_rasterized(False)
    cb.set_label('Mean standardized coordinate (whole classified cohort = 0)',fontsize=8,labelpad=4)
    cb.ax.tick_params(labelsize=7.5,length=2)
    fig.suptitle('Joint cluster profiles',x=.68,y=.97,fontsize=9.5)
    save(fig,out,'FIG_STAGE7_CLUSTER_PROFILE')
    pd.DataFrame(values,index=short,columns=NAMES).to_csv(out/'PROFILE_VISUAL_STANDARDIZED_MEANS.csv',index_label='reader_facing_feature')

    runs=pd.read_csv(s/'SPATIAL_K4_RUNS.csv');m=pd.read_csv(s/'SPATIAL_K4_CLUSTER_MATCHING.csv');small=pd.read_csv(s/'SMALL_CLUSTER_34_AUDIT.csv')
    fig=plt.figure(figsize=(185*MM,188*MM));gs=fig.add_gridspec(2,2,left=.085,right=.97,bottom=.14,top=.935,wspace=.42,hspace=.49,height_ratios=[1,.98])
    a=fig.add_subplot(gs[0,0]);b=fig.add_subplot(gs[0,1]);c=fig.add_subplot(gs[1,0]);e=fig.add_subplot(gs[1,1])
    for i,model in enumerate(['D','EAL']):
        v=runs.loc[runs.model==model,'full_ARI'].to_numpy()
        a.boxplot(v,positions=[i],widths=.42,patch_artist=True,showfliers=False,
                  boxprops={'facecolor':MODEL_COLORS[model],'alpha':.25},medianprops={'color':MODEL_COLORS[model],'linewidth':1.4},
                  whiskerprops={'color':MODEL_COLORS[model]},capprops={'color':MODEL_COLORS[model]})
        a.scatter(np.full(len(v),i)+np.linspace(-.11,.11,len(v)),v,color=MODEL_COLORS[model],s=10,alpha=.8,zorder=3)
    a.set(xticks=[0,1],xticklabels=['D','EAL'],ylim=(.7,1.01),ylabel='Adjusted Rand index',xlabel='Model specification')
    a.set_title('A  Spatial partition stability',loc='left',pad=7)
    a.grid(axis='y',alpha=.2,lw=.4)
    # Class-level retention and Jaccard shown on the same 0-1 scale.
    y=np.arange(4); full=m[m.scope=='full']
    for i,model in enumerate(['D','EAL']):
        for metric,marker,offset in [('retention','o',-.10),('jaccard','s',.10)]:
            sub=full[full.model==model];med=sub.groupby('display_seed42_cluster')[metric].median().reindex(range(1,5));lo=sub.groupby('display_seed42_cluster')[metric].min().reindex(range(1,5));hi=sub.groupby('display_seed42_cluster')[metric].max().reindex(range(1,5))
            ypos=y+(i-.5)*.34+offset
            b.errorbar(med,ypos,xerr=[med-lo,hi-med],fmt=marker,color=MODEL_COLORS[model],ms=3.2,lw=.8,capsize=2)
    b.set(yticks=y,yticklabels=NAMES,xlim=(.3,1.035),xlabel='Membership agreement');b.invert_yaxis();b.grid(axis='x',alpha=.2,lw=.4)
    b.set_title('B  Retention and class overlap',loc='left',pad=7)
    handles=[Line2D([],[],color=MODEL_COLORS[model],lw=1.3,label=model) for model in ['D','EAL']]
    handles += [Line2D([],[],marker='o',ls='',color='#333333',ms=3.5,label='Retention'),Line2D([],[],marker='s',ls='',color='#333333',ms=3.5,label='Jaccard')]
    b.legend(handles=handles,ncol=2,loc='upper center',bbox_to_anchor=(.5,-.17),frameon=False,columnspacing=1.4,handletextpad=.5)
    worst=small[(small.target=='D_SEED42_34')&(small.seed==54)]
    assert worst.set_index('model').prediction_n.to_dict()=={'D':92,'EAL':90}
    for i,model in enumerate(['D','EAL']):
        r=worst[worst.model==model].iloc[0]
        c.bar(i,34,width=.55,color=SMALL_BLUE)
        c.bar(i,r.new_other_members,bottom=34,width=.55,color=ADD_ORANGE)
        c.text(i,r.prediction_n+3,f'{int(r.prediction_n)} tracts\n{100*r.prediction_target_purity:.2f}% purity',ha='center',va='bottom',fontsize=7.5)
    c.set(xticks=[0,1],xticklabels=['D','EAL'],ylim=(0,118),ylabel='Tracts in the predicted class')
    c.set_title('C  Sparse-support class expansion',loc='left',pad=7)
    c.text(.5,.9,'4 of 34 members in training',transform=c.transAxes,ha='center',fontsize=7.5)
    c.legend(handles=[Patch(color=SMALL_BLUE,label='Original 34'),Patch(color=ADD_ORANGE,label='Additional members')],
             loc='upper center',bbox_to_anchor=(.5,-.15),frameon=False,ncol=1,labelspacing=.35)
    pred=pd.read_csv(s/'SPATIAL_K4_TRACT_PREDICTIONS.csv',dtype={'tract_id':str})
    # Inspect schema explicitly; use saved training-derived class mapping.
    target=pred[(pred.model=='D')&(pred.seed==54)]
    display_col='aligned_display_seed42_cluster'
    assert display_col in target
    print('prediction map field',display_col)
    target_ids=set(target.loc[target[display_col]==2,'tract_id'])
    original_ids=set(d.loc[d.candidate_cluster=='C2','tract_id'])
    assert len(target_ids)==92 and original_ids<=target_ids
    expand=g[g.tract_id.isin(target_ids)].copy();x0,y0,x1,y1=expand.total_bounds;pad=.08*max(x1-x0,y1-y0)
    nearby=g.cx[x0-pad:x1+pad,y0-pad:y1+pad]
    nearby.plot(ax=e,facecolor='#F2F2F2',edgecolor='#B9B9B9',linewidth=.2)
    expand[~expand.tract_id.isin(original_ids)].plot(ax=e,color=ADD_ORANGE,edgecolor='#555555',linewidth=.3)
    expand[expand.tract_id.isin(original_ids)].plot(ax=e,color=SMALL_BLUE,edgecolor='#333333',linewidth=.35)
    e.set_xlim(x0-pad,x1+pad);e.set_ylim(y0-pad,y1+pad);e.set_aspect('equal');e.set_anchor('N');e.set_axis_off()
    e.set_title('D  Expanded class: D model',loc='left',pad=7)
    save(fig,out,'FIG_STAGE7_SPATIAL_ROBUSTNESS')
    (out/'FIGURE_STYLE.json').write_text(json.dumps({'width_mm':185,'font':'Arial','minimum_requested_font_pt':7.5,
        'cluster_id_palette':COLORS,'map_crs':'EPSG:3310','map_geometry':'exact archived tract polygons, no simplification',
        'heatmap':'Unweighted means of original cohort z scores; color saturation at +/-1.5 SD, actual values annotated',
        'spatial_B_interval':'minimum to maximum over 20 cases; dot median, not CI',
        'map_D':'D seed54, training-derived class matching; region cropped to actual expanded group bounds'},indent=2)+'\n')

if __name__=='__main__':main()
