"""Reduce current manuscript displays without changing original experiments."""
from pathlib import Path
import json
import fitz,numpy as np,pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from la_grid.plotting import selected_strategy_artwork as art
from la_grid.plotting import apply_coauthor_figure_feedback as common
R=art.ROOT;T=art.TEMP;REV=art.REVIEW;MM=art.MM
SEL=art.SELECTED;ORDER=art.ORDER;CORE=art.CORE
SUITE=R/'results/revised_suite/LA_Grid_Revised_Suite_20260925'
MARK={'impact-first':'s','hospital-first':'o','degree-first':'^','vulnerability-first':'D','betweenness-first':'P','random':'o','unconstrained':'o'}

def grouped_key(fig,height,top=3,markers=False,include_unconstrained=True):
    for x,title,keys in [(27,'Infrastructure-based',['degree-first','betweenness-first']),(89,'Community / equity-informed',['impact-first','hospital-first','vulnerability-first']),(153,'Baselines',['unconstrained','random'])]:
        fig.text(x/185,1-top/height,title,fontsize=7.5,fontweight='bold',va='top')
        if not include_unconstrained:keys=[k for k in keys if k!='unconstrained']
        for j,k in enumerate(keys):
            y=1-(top+5+j*4.2)/height
            fig.add_artist(Line2D([(x+3)/185] if markers else [x/185,(x+6)/185],[y] if markers else [y,y],transform=fig.transFigure,color=common.COLORS[k],lw=1.3 if k=='unconstrained' else 1.15,marker=MARK[k] if markers else None,markersize=3.5,linestyle='none' if markers else '-'))
            fig.text((x+8)/185,y,common.LABEL[k],fontsize=7.5,va='center',fontweight='bold' if k in CORE+['unconstrained'] else 'normal')

def curve(ax,data,column,keys,horizon,ylabel,ylim):
    for k in keys+['unconstrained']:
        p=data[data.strategy_id.eq(k)&data.time_hr.le(horizon)].sort_values('time_hr');assert not p.empty
        ax.plot(p.time_hr,p[column],color=common.COLORS[k],lw=1.3 if k=='unconstrained' else 1.15,ls='-',alpha=1)
    ax.set_xlim(0,horizon);ax.set_ylim(*ylim);ax.set_ylabel(ylabel);ax.spines[['top','right']].set_visible(False);ax.grid(color='#e6e6e6',lw=.4);ax.set_xlabel('Time after earthquake (h)',fontsize=7.5)

def all_summary():
    ps=[R/'Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet',R/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet']
    d=pd.concat([pd.read_parquet(p) for p in ps],ignore_index=True)
    return d[d.mapping.eq('M1_UTILITY_003')&d.gate.eq('G1_BASELINE_050')&d.strategy_id.isin(ORDER)].copy()

def fig04(data):
    q=data[data.hazard.eq('2pc50')&data.resource_scenario.eq('C57_D1')]
    assert q.groupby('strategy_id').size().to_dict()=={k:1000 for k in ORDER}
    curves=pd.read_csv(SUITE/'Stage 6 Output_expanded/ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv');curves=curves[curves.hazard.eq('2pc50')]
    fig=plt.figure(figsize=(185/25.4,205/25.4));grouped_key(fig,205)
    fig.text(.5,1-28/205,'A. Population-weighted service recovery',ha='center',va='top',fontsize=9.5,fontweight='bold')
    for x,keys,title in [(.115,CORE,'Four focal policies'),(.605,SEL[4:],'Other selected policies')]:
        ax=fig.add_axes([x,1-99/205,.36,58/205]);curve(ax,curves,'mean_population_availability_proxy',keys,100,'Population-weighted\nservice availability' if x<.2 else '',(-.025,1.04));ax.set_xticks([0,25,50,75,100]);ax.set_title(title,fontsize=7.5,pad=4)
    fig.text(.5,1-116/205,'B. Service loss and recovery time',ha='center',va='top',fontsize=9.5,fontweight='bold')
    fig.text(.5,1-125/205,'Means; T80 ranges: 5th-95th percentiles',ha='center',fontsize=7.5)
    metrics=[('population_weighted_normalized_burden_hr','All-tract','#497f9b'),('burden_Q4_hr','Q4 tract','#c48a43'),('hospital_mean_normalized_burden_hr','Hospital-tract','#8a989f')]
    fig.legend(handles=[Patch(facecolor=c,label=l+' service loss') for _,l,c in metrics],loc='upper center',bbox_to_anchor=(.5,1-128/205),ncol=3,frameon=False,handlelength=1.0,handletextpad=.4,columnspacing=.8)
    ax=fig.add_axes([.205,.12,.48,.185]);tx=fig.add_axes([.785,.12,.18,.185]);rows=[]
    for i,k in enumerate(ORDER):
        p=q[q.strategy_id.eq(k)]
        for j,(field,label,color) in enumerate(metrics):
            v=p[field].to_numpy();mean=v.mean();lo,hi=np.quantile(v,[.05,.95]);ax.barh(i+(j-1)*.22,mean,height=.20,color=color,alpha=1 if k in CORE+['unconstrained'] else .7,edgecolor='white',lw=.25);rows.append(dict(strategy=k,metric=field,mean=float(mean),p05=float(lo),p95=float(hi)))
        v=p.population_T80_hr.to_numpy();mean=v.mean();lo,hi=np.quantile(v,[.05,.95]);tx.errorbar(mean,i,xerr=[[mean-lo],[hi-mean]],fmt=MARK[k],color=common.COLORS[k],ms=3,lw=.7,capsize=1.5)
    ax.set_yticks(range(7),[common.LABEL[k] for k in ORDER]);ax.tick_params(axis='y',length=0,pad=4)
    for k,l in zip(ORDER,ax.get_yticklabels()):l.set_fontweight('bold' if k in CORE+['unconstrained'] else 'normal')
    for a in [ax,tx]:a.set_ylim(6.6,-.6);a.spines[['top','right']].set_visible(False);a.grid(axis='x',color='#e6e6e6',lw=.4)
    ax.set_xlim(0,50);ax.set_xlabel('Service loss (h)');tx.set_yticks([]);tx.set_xlim(35,62);tx.set_xticks([40,50,60]);tx.set_xlabel('Population T80 (h)',fontsize=7.5)
    result=art.export_figure(fig,'Main/Fig04');result['display_values']=rows;return result

def fig05(data):
    d=data[data.hazard.eq('2pc50')&data.resource_scenario.eq('C57_D1')];old,before=common.baseline('Main/Fig05')
    fig=plt.figure(figsize=(185/25.4,24/25.4));grouped_key(fig,24,top=1,markers=True)
    f=T/'Fig05_selected_legend.pdf';fig.savefig(f);plt.close(fig)
    fig,ax=plt.subplots(figsize=(92/25.4,66/25.4));fig.subplots_adjust(left=.22,right=.94,bottom=.2,top=.88)
    for k in ORDER:
        p=d[d.strategy_id.eq(k)];x=p.population_weighted_normalized_burden_hr.mean();y=p.burden_Q4_hr.mean()
        ax.scatter(x,y,color=common.COLORS[k],marker=MARK[k],s=19 if k in CORE+['unconstrained'] else 16,alpha=1,edgecolors='none')
        if k=='vulnerability-first':ax.annotate('Vulnerability-first',(x,y),xytext=(x-.8,y-1.0),fontsize=7.5,fontweight='bold',arrowprops={'arrowstyle':'-','lw':.55,'color':'#404040'},ha='center')
    ax.set_xlim(30,40);ax.set_ylim(28.5,40);ax.set_xlabel('All-tract\nservice loss (h)');ax.set_ylabel('Q4 tract\nservice loss (h)');ax.set_title('A. Overall and Q4 service loss',fontsize=9.5,pad=4);ax.grid(color='#e6e6e6',lw=.4);ax.spines[['top','right']].set_visible(False)
    a=T/'Fig05_selected_plane.pdf';fig.savefig(a);plt.close(fig)
    doc=fitz.open();p=doc.new_page(width=old[0].rect.width,height=old[0].rect.height)
    with fitz.open(f) as b:p.show_pdf_page(fitz.Rect(0,0,185*MM,24*MM),b,0)
    with fitz.open(a) as b:p.show_pdf_page(fitz.Rect(0,24*MM,92*MM,90*MM),b,0)
    fig,ax=plt.subplots(figsize=(92/25.4,66/25.4));fig.subplots_adjust(left=.22,right=.96,bottom=.20,top=.88)
    for j,k in enumerate(CORE):
        q=d[d.strategy_id.eq(k)];means=[];lower=[];upper=[]
        for quartile in range(1,5):
            v=q[f'burden_Q{quartile}_hr'].to_numpy();m=v.mean();lo,hi=np.quantile(v,[.05,.95]);means.append(m);lower.append(m-lo);upper.append(hi-m)
        ax.errorbar(np.arange(4)+(j-1.5)*.07,means,yerr=[lower,upper],color=common.COLORS[k],marker=MARK[k],ms=3,lw=1,elinewidth=.6,capsize=1.5,ls='-')
    ax.set_xticks(range(4),['Q1 lowest','Q2','Q3','Q4 highest']);ax.set_ylabel('Tract service loss (h)');ax.set_title('B. Quartile service loss',fontsize=9.5,pad=4);ax.grid(color='#e6e6e6',lw=.4);ax.spines[['top','right']].set_visible(False)
    f=T/'Fig05_selected_quartiles.pdf';fig.savefig(f);plt.close(fig)
    with fitz.open(f) as b:p.show_pdf_page(fitz.Rect(93*MM,24*MM,185*MM,90*MM),b,0)

    p.show_pdf_page(fitz.Rect(0,90*MM,185*MM,250*MM),old,0,clip=fitz.Rect(0,90*MM,185*MM,250*MM));old.close()
    return common.finish(doc,'Main/Fig05',{'before_sha256':before,'change':'Seven-point policy plane and selected grouped key; B/C/D/E unchanged.'})

def s04():
    old,before=common.baseline('Supplement/FigS04');data=pd.read_csv(SUITE/'Stage 6 Output_expanded/NETWORK_TOPOLOGY_DISPLAY_CURVES_2pc50.csv')
    fig=plt.figure(figsize=(185/25.4,154/25.4))
    for row,(field,title,yl,ylim) in enumerate([('mean_lcc_fraction','B. Largest connected component fraction','Largest component\nfraction',(-.02,1.04)),('mean_lcc_average_degree','C. Average degree within the largest component','Mean degree',(-.15,7.3))]):
        top=5+row*62;fig.text(.5,1-top/154,title,ha='center',va='top',fontsize=9.5,fontweight='bold')
        for x,keys in [(.11,CORE),(.605,SEL[4:])]:
            ax=fig.add_axes([x,1-(top+49)/154,.36,36/154]);curve(ax,data,field,keys,120,yl if x<.2 else '',ylim);ax.set_xticks([0,30,60,90,120])
            if row==0:ax.set_title('Four focal policies' if x<.2 else 'Other selected policies',fontsize=7.5,pad=4)
    grouped_key(fig,154,top=132);f=T/'S04_selected_dynamic.pdf';fig.savefig(f);plt.close(fig)
    doc=fitz.open();p=doc.new_page(width=185*MM,height=216*MM);p.show_pdf_page(fitz.Rect(0,0,185*MM,62*MM),old,0,clip=fitz.Rect(0,0,185*MM,62*MM))
    with fitz.open(f) as d:p.show_pdf_page(fitz.Rect(0,62*MM,185*MM,216*MM),d,0)
    old.close();return common.finish(doc,'Supplement/FigS04',{'before_sha256':before,'change':'Six scheduled dynamic policies, preserved static attack diagnostic A.'})

def resources(data,kind):
    cases=['C29_D1','C57_D1','C86_D1','C114_D1'] if kind=='crew' else ['C57_D075','C57_D1','C57_D125','C57_D150']
    xvalues=np.array([29/57,1,86/57,2] if kind=='crew' else [.75,1,1.25,1.5]);xlabel='Crew-availability multiplier' if kind=='crew' else 'Repair-duration multiplier'
    fig=plt.figure(figsize=(185/25.4,171/25.4));grouped_key(fig,171,top=13,markers=True,include_unconstrained=False)
    fig.text(.5,.982,'Community outcomes across '+('crew availability' if kind=='crew' else 'repair durations'),ha='center',va='top',fontsize=9.5,fontweight='bold')
    metrics=[('population_weighted_normalized_burden_hr','All-tract service loss','Modeled service loss (h)'),('burden_Q4_hr','Q4 tract service loss','Modeled service loss (h)'),('absolute_Q4_minus_Q1_hr','High-low vulnerability service-loss gap','High-low service-loss gap (h)'),('hospital_mean_normalized_burden_hr','Hospital-tract service loss','Modeled service loss (h)')]
    for n,(field,title,yl) in enumerate(metrics):
        ax=fig.add_axes([.115+(n%2)*.50,.10+(1-n//2)*.39,.35,.27]);ax.set_title(f'{chr(65+n)}. {title}',fontsize=8.5,pad=4)
        for j,k in enumerate(SEL):
            vals=[];lower=[];upper=[]
            for case in cases:
                q=data[data.hazard.eq('2pc50')&data.resource_scenario.eq(case)&data.strategy_id.eq(k)];assert len(q)==1000
                v=q[field].to_numpy();m=v.mean();lo,hi=np.quantile(v,[.05,.95]);vals.append(m);lower.append(m-lo);upper.append(hi-m)
            offset=(j-2.5)*(.022 if kind=='duration' else .027)
            ax.errorbar(xvalues+offset,vals,yerr=[lower,upper],fmt=MARK[k],color=common.COLORS[k],ms=3,elinewidth=.7,capsize=0,alpha=1 if k in CORE else .75)
        ax.set_xticks(xvalues,['0.5','1.0','1.5','2.0'] if kind=='crew' else ['0.75','1.00','1.25','1.50']);ax.set_xlabel(xlabel,fontsize=7.5);ax.set_ylabel(yl,fontsize=7.5);ax.spines[['top','right']].set_visible(False);ax.grid(color='#e6e6e6',lw=.4)
    fig.text(.98,.015,'Dots: means; whiskers: 5th-95th realization ranges',ha='right',fontsize=7.5)
    return art.export_figure(fig,'Supplement/FigS12' if kind=='crew' else 'Supplement/FigS13')

def s11():
    source=R/'provenance/figure_review_history/candidate_v2.1/CROSS_HAZARD_POLICY_EFFECTS.csv';d=pd.read_csv(source)
    hazards=['LongBeach','SanFernando','Northridge','2pc50'];names=['Long Beach','San Fernando','Northridge','2pc50'];fields=['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr','population_T80_hr'];labels=['All-tract\nservice loss','Q4 tract\nservice loss','Hospital-tract\nservice loss','Population\nT80']
    values=[]
    for h in hazards:
        a=np.array([[d.loc[d.hazard.eq(h)&d.strategy_id.eq(k)&d.metric.eq(m),'mean_paired_difference'].item() for m in fields] for k in SEL]);values.append(a)
    vmax=max(abs(a).max() for a in values);cmap=plt.get_cmap('RdBu_r');fig=plt.figure(figsize=(185/25.4,180/25.4))
    for i,(h,name,a) in enumerate(zip(hazards,names,values)):
        ax=fig.add_axes([.19+(i%2)*.46,.16+(1-i//2)*.42,.30,.30]);im=ax.pcolormesh(np.arange(5)-.5,np.arange(7)-.5,a,cmap=cmap,vmin=-vmax,vmax=vmax,rasterized=False);ax.set_ylim(5.5,-.5);ax.grid(False);ax.set_xticks(range(4),labels,fontsize=7.0);ax.set_yticks(range(6),[common.LABEL[k] for k in SEL],fontsize=7.5);ax.tick_params(length=0,pad=4);ax.set_title(f'{chr(65+i)}. {name}',pad=5);ax.axvline(2.5,color='white',lw=1.2)
        for row in range(6):
            for col in range(4):
                c=cmap((a[row,col]+vmax)/(2*vmax))[:3];lum=np.dot(c,[.2126,.7152,.0722]);ax.text(col,row,f'{a[row,col]:+.2f}',ha='center',va='center',fontsize=7.0,color='white' if lum<.45 else '#15232a')
    cax=fig.add_axes([.28,.073,.50,.012]);cb=fig.colorbar(im,cax=cax,orientation='horizontal');cb.set_label('Mean change relative to Unconstrained (h)',fontsize=8.5);cb.ax.tick_params(labelsize=7.5)
    return art.export_figure(fig,'Supplement/FigS11')

def main():
    data=all_summary();records=[fig04(data),fig05(data),s04(),s11(),resources(data,'crew'),resources(data,'duration')]
    p=T/'artwork_records.json';old=json.loads(p.read_text());p.write_text(json.dumps(old+records,indent=2));print([r['file'] for r in records])
if __name__=='__main__':main()
