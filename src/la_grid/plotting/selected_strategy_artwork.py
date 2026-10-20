"""Selected-policy artwork and saved network-centrality presentation."""
from pathlib import Path
import csv,hashlib,json,re,shutil,subprocess,tempfile
import numpy as np,pandas as pd,fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import seaborn as sns
from la_grid.paths import REPO_ROOT
from la_grid.plotting import apply_coauthor_figure_feedback as common
from la_grid.plotting import build_meeting_figure_collection as meeting
from la_grid.plotting.apply_outcome_display_feedback import fonts,sha,text,update_csv
from la_grid.plotting.apply_map_metric_identity_feedback import packets
ROOT=REPO_ROOT;REVIEW=ROOT/'results/figure_review'
BASE='2cfd9ce5f5c65c7edb575ebd4e8174c4f2fa817b'
TEMP=Path(tempfile.gettempdir())/'la_selected_strategy_20261008'
MM=72/25.4
SELECTED=['impact-first','hospital-first','degree-first','vulnerability-first','betweenness-first','random']
ORDER=SELECTED+['unconstrained'];CORE=SELECTED[:4]
GENERATOR=Path(__file__).relative_to(ROOT).as_posix()
common.BASE_COMMIT=BASE;common.TEMP=TEMP
plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial'],'font.size':7.5,'axes.titlesize':9.5,'axes.titleweight':'bold','axes.labelsize':8.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,'axes.linewidth':.6,'pdf.fonttype':42,'figure.facecolor':'white'})

def right_aligned_feature_labels(ax,labels):
    ax.set_yticklabels(labels,rotation=0,ha='right')
    for label in ax.get_yticklabels():
        label.set_horizontalalignment('right')
        label.set_multialignment('right')

def overlay(doc,rect,figure):
    p=doc[0];result=fitz.open();page=result.new_page(width=p.rect.width,height=p.rect.height)
    if rect.y0>0:page.show_pdf_page(fitz.Rect(0,0,p.rect.width,rect.y0),doc,0,clip=fitz.Rect(0,0,p.rect.width,rect.y0))
    if rect.y1<p.rect.height:page.show_pdf_page(fitz.Rect(0,rect.y1,p.rect.width,p.rect.height),doc,0,clip=fitz.Rect(0,rect.y1,p.rect.width,p.rect.height))
    page.show_pdf_page(rect,figure,0);doc.close();return result

def export_figure(fig,key):
    target=TEMP/(key.replace('/','_')+'.pdf');fig.savefig(target);plt.close(fig)
    return common.finish(fitz.open(target),key,{'change':'Selected-policy presentation; numerical sources read-only.'})

def fig07():
    path=ROOT/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/stage7_cluster_profiles_raw_values.csv'
    profiles=pd.read_csv(path).set_index('cluster')
    fields=['T80','Pre_1970_Ratio','Pop_Density','NRI_RISK_SCORE','NRI_BUILDVALUE','SOVI_SCORE']
    labels=['Recovery time (T80, h)','Pre-1970 housing ratio','Population density','NRI risk score','NRI building value','Social vulnerability score']
    values=profiles[[f+'_mean' for f in fields]].copy();values.columns=fields
    standardized=(values-values.mean())/values.std(ddof=1);assert list(values.index)==[1,2,3,4,5]
    fig=plt.figure(figsize=(185/25.4,72/25.4));ax=fig.add_axes([.405,.15,.355,.735]);cax=fig.add_axes([.782,.15,.018,.735])
    sns.heatmap(standardized.T,cmap='coolwarm',center=0,annot=True,fmt='.1f',annot_kws={'fontsize':7.5},ax=ax,cbar_ax=cax,cbar_kws={'label':'Profile z-score'})
    right_aligned_feature_labels(ax,labels)
    ax.set_xticklabels([f'C{v}' for v in values.index],rotation=0);ax.set_xlabel('');ax.set_ylabel('Feature',labelpad=6)
    ax.tick_params(axis='y',length=0,pad=3);ax.tick_params(axis='x',length=0)
    fig.text(2/185,1-3/72,'B. Standardized feature profiles by cluster',fontsize=9.5,fontweight='bold',va='top')
    file=TEMP/'Fig07_right_aligned_panel.pdf';fig.savefig(file);plt.close(fig)
    doc,before=common.baseline('Main/Fig07')
    with fitz.open(file) as b:result=overlay(doc,fitz.Rect(0,95*MM,185*MM,167*MM),b)
    return common.finish(result,'Main/Fig07',{'before_sha256':before,'change':'Only profile panel B labels explicitly ha=right and multialignment=right; A/C/D native artwork preserved.','source_sha256':{path.relative_to(ROOT).as_posix():sha(path)},'profile_values':standardized.T.to_numpy().tolist()})

def centrality():
    source=ROOT/'Formal_Experiment_20260923/Stage 2 Output_expanded/impact_centrality_substations.csv'
    metrics=pd.read_csv(source,dtype={'substation_id':str})
    nodes=pd.read_csv(ROOT/'Data/substation_graph_CEC_nodes_expanded.csv',dtype={'id':str})
    tracts=meeting.tract_geometry().to_crs('EPSG:3310')
    points=meeting.map_points(nodes,tracts.crs).merge(metrics,left_on='id',right_on='substation_id',validate='one_to_one');assert len(points)==92
    fig=plt.figure(figsize=(185/25.4,168/25.4))
    bounds=tracts.total_bounds;x0,y0,x1,y1=bounds
    for j,(metric,label,cmap) in enumerate([('degree','Degree','Blues'),('betweenness_centrality','Betweenness centrality','YlOrBr')]):
        ax=fig.add_axes([.04+j*.5,.47,.42,.46]);tracts.plot(ax=ax,color='#f2f2f2',edgecolor='white',lw=.07)
        points.plot(ax=ax,column=metric,cmap=cmap,markersize=13,edgecolor='#404040',lw=.25,zorder=3)
        ax.set_xlim(x0-.025*(x1-x0),x1+.025*(x1-x0));ax.set_ylim(y0-.025*(y1-y0),y1+.025*(y1-y0));ax.set_aspect('equal');ax.set_axis_off()
        ax.set_title(f'{chr(65+j)}. {label}',pad=4)
        norm=plt.Normalize(points[metric].min(),points[metric].max());cax=fig.add_axes([.10+j*.5,.45,.30,.012])
        cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal');cb.set_label('Neighboring substations' if metric=='degree' else 'Betweenness centrality',fontsize=8.5,labelpad=2);cb.ax.tick_params(labelsize=7.5,length=2)
        hist=fig.add_axes([.105+j*.5,.105,.36,.235]);v=metrics[metric].to_numpy(float)
        bins=np.arange(v.min()-.5,v.max()+1.5,1) if metric=='degree' else np.linspace(0,v.max(),13)
        hist.hist(v,bins=bins,color='#4daf4a' if j==0 else '#b59a00',edgecolor='white',lw=.5)
        hist.set_xlabel('Degree' if j==0 else 'Betweenness centrality');hist.set_ylabel('Substations');hist.set_title(f'{chr(67+j)}. Station distribution',fontsize=9.5)
        hist.spines[['top','right']].set_visible(False);hist.grid(axis='y',color='#e5e5e5',lw=.4)
    folder=REVIEW/'Additional_Evidence';folder.mkdir(exist_ok=True)
    key='Additional_Evidence/Degree_and_Betweenness';result=export_figure(fig,key)
    (folder/'Degree_and_Betweenness.md').write_text('Degree and betweenness in the study network. A/B show the saved station centrality values on the common study-area extent; C/D show their distributions over the modeled substations. Degree counts neighboring substations. Betweenness describes intermediary position on shortest network paths. These static metrics define two infrastructure priorities; neither is a direct measure of delivered electricity or a validated optimal repair order. Values are read from '+source.relative_to(ROOT).as_posix()+'. No network metric is recalculated.\n',encoding='utf-8')
    return result

def main():
    TEMP.mkdir(exist_ok=True)
    records=[fig07(),centrality()]
    (TEMP/'artwork_records.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(records,indent=2))
if __name__=='__main__':main()
