"""Candidate-only Matplotlib publication artwork; saved data, no new fitting."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.backends.backend_pdf import PdfPages
import geopandas as gpd
from shapely.geometry import Point
import fitz
from common import *

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
PALETTE=['#147f98','#d07734','#7a5899']
K4_COLORS=['#608543',PALETTE[0],PALETTE[1],PALETTE[2]]
manifest=[]

def style(fig,title,note):
    fig.text(.5,.985,WARN,ha='center',va='top',fontsize=7,color='#963d29')
    if title:fig.suptitle(title,y=.951,fontsize=11)
    fig.text(.035,.015,note,fontsize=7,ha='left',va='bottom')

def emit(fig,name,title,note,writer=None,page=1):
    style(fig,title,note)
    if writer is None:fig.savefig(dest('figures/'+name+'.pdf'))
    else:writer.savefig(fig)
    suffix='' if page==1 else '_page'+str(page)
    fig.savefig(dest('figures/'+name+suffix+'.png'),dpi=600)
    manifest.append(dict(name=name,page=page,pdf='figures/'+name+'.pdf',PNG='figures/'+name+suffix+'.png',width_inches=fig.get_figwidth(),height_inches=fig.get_figheight(),PNG_dpi=600,review_status=WARN,AI_media=False))
    plt.close(fig)

def continuous_map(ax,g,values,title,label,cmap='viridis'):
    val=pd.Series(values,index=g.index,dtype=float);norm=colors.Normalize(val.min(),val.max())
    g.assign(value=val).plot(column='value',ax=ax,cmap=cmap,norm=norm,edgecolor='none',missing_kwds={'color':'#d3d3d3'})
    ax.set_axis_off();ax.set_title(title,pad=14)
    cb=plt.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,shrink=.85,fraction=.043,pad=.014);cb.set_label(label,fontsize=7)
    cb.solids.set_rasterized(False)

def category_map(ax,g,ids,title,palette,k,legend=True):
    # Full2315 boundary support; only the2299 eligible rows receive a class.
    val=pd.Series(ids,index=g.index)
    g.plot(ax=ax,color='#d4d4d4',edgecolor='none')
    gg=g.loc[val.notna()].assign(class_id=val.loc[val.notna()].astype(int))
    gg.plot(column='class_id',ax=ax,cmap=colors.ListedColormap(palette),vmin=-.5,vmax=k-.5,edgecolor='none')
    ax.set_axis_off();ax.set_title(title,pad=6)
    if legend:ax.legend(handles=[Patch(facecolor=palette[c],label='C'+str(c+1)) for c in range(k)]+[Patch(facecolor='#d4d4d4',label='Zero population')],loc='upper right',fontsize=6,frameon=True)

def main():
    d=frame('inputs/FROZEN_COHORT.csv','tract_id');d['FEMA_NCV14_CA_v119']=frame('inputs/NCV_VECTOR.csv','tract_id').FEMA_NCV14_CA_v119
    g=gpd.read_file(lp(OUT/'candidate/FULL_2315_GEOMETRY.gpkg')).set_index('tract_id');gp=g.reindex(d.index)
    profiles=frame('K3_K4_ORIGINAL_UNIT_PROFILES.csv');sizes=frame('K3_K4_QUARTILE_POPULATION_HOSPITAL.csv')
    fits=np.load(lp(OUT/'inputs/SAVED_LABELS_AND_SILHOUETTES.npz'));ix={k:i for i,k in enumerate(fits['keys'])}
    def lab(k,condition='main'):return fits['labels'][ix[f'NCV14__{condition}__k{k}__s42']]
    # Phase1: direct source rank comparison, not inference about actual events.
    quake=frame('EARTHQUAKE_MATCHED_TRACT_VALUES.csv','tract_id');weather=frame('WEATHER_PAIRWISE_DEPENDENCE.csv');impact=frame('HAZARD_SET_AND_NORMALIZATION_EFFECTIVE_INFLUENCE.csv')
    fig,ax=plt.subplots(2,3,figsize=(7.2,6.3));fig.subplots_adjust(left=.10,right=.94,bottom=.14,top=.83,hspace=.55,wspace=.70)
    continuous_map(ax[0,0],gp,quake.ERQK_frequency_area_factor,'Released earthquake\nfrequency-area factor','Factor')
    continuous_map(ax[0,1],gp,quake.CGS_PGA_land_mean_g,'Independent CGS\n2pc50 land-mean PGA','g','magma')
    valid=quake[['CGS_PGA_land_mean_g','ERQK_frequency_area_factor']].dropna()
    ax[0,2].scatter(valid.CGS_PGA_land_mean_g,valid.ERQK_frequency_area_factor,s=3,alpha=.4,color='#397d85');ax[0,2].set(xlabel='CGS PGA (g)',title='ERQK factor versus PGA\nSpearman = -0.038');ax[0,2].ticklabel_format(axis='y',style='sci',scilimits=(0,0))
    p=weather.loc[weather.measurement.eq('frequency_area')]
    ticks=np.arange(len(p));ax[1,0].bar(ticks-.15,p.Pearson,width=.3,color=PALETTE[0],label='Pearson');ax[1,0].bar(ticks+.15,p.Spearman,width=.3,color=PALETTE[1],label='Spearman');ax[1,0].set_xticks(ticks,['Heat /\nhail','Heat /\nwind','Hail /\nwind']);ax[1,0].set(ylim=(-.3,1.05),ylabel='Association',title='Shared weather sources');ax[1,0].legend()
    ax[1,1].barh(impact.hazard,impact.signed_covariance_share*100,color=['#c16b43' if h=='ERQK' else '#407e8e' for h in impact.hazard]);ax[1,1].invert_yaxis();ax[1,1].set(xlabel='Signed variance share (%)',title='Effective local influence');ax[1,1].axvline(0,color='black',lw=.5)
    leave=frame('inputs/EXISTING_HAZARD_LEAVEOUT.csv');names=['no_ERQK','no_HWAV','no_HAIL','no_SWND','LA_component_normalization']
    for k,color in [(3,PALETTE[0]),(4,K4_COLORS[0])]:
        vals=leave.loc[leave.k.eq(k)].set_index('condition').reindex(names);ax[1,2].plot(np.arange(5),vals.ARI,'-o',label='K'+str(k),color=color,ms=3)
    ax[1,2].set_xticks(range(5),['No\nquake','No\nheat','No\nhail','No\nwind','LA\nscale']);ax[1,2].set(ylim=(.95,1.005),ylabel='Membership ARI',title='Reused hazard sensitivities');ax[1,2].legend()
    emit(fig,'01_Natural_Hazard_Final_Source_Review','Natural hazard: qualified geographic screening, not physical risk','CGS: 2,294 valid land means; 5 partial supports remain missing. All 2,299 still enter the typology.\nWeather fields inherit forecast zones / 80-km buffers / 49-km fishnets; no new hazard simulation.')
    # Phase2 original-unit profiles are deliberately not standardized heatmaps alone.
    titles=['Initial service\n(%)','Spectral grid\nimpact','Dependency\nHHI','Unconstrained\ndeficit (h)','Mean extra\ndeficit (h)','FEMA SOVI\n(0-100)','Mean population\n(persons)','Natural-hazard\nscreen (0-1)']
    display=FEATURES.copy();display[6]='Population'
    with PdfPages(dest('figures/02_K3_K4_Scientific_Comparison.pdf')) as pdf:
        fig,ax=plt.subplots(2,4,figsize=(7.2,5.8));fig.subplots_adjust(left=.085,right=.97,bottom=.15,top=.85,hspace=.62,wspace=.70)
        for j,(a,field,title) in enumerate(zip(ax.flat,display,titles)):
            for k,color,marker in [(3,PALETTE[0],'o'),(4,K4_COLORS[0],'s')]:
                val=profiles.loc[profiles.condition.eq('main')&profiles.k.eq(k)&profiles.variable.eq(field)].sort_values('model_class')
                y=val['mean'].to_numpy()*(100 if field=='Init_Supply' else 1)
                a.plot(np.arange(k)+1,y,marker+'-',color=color,label='K'+str(k),ms=4,lw=1)
            a.set_title(title);a.set_xlabel('Within-model class');a.set_xticks([1,2,3,4]);a.set_xlim(.75,4.25)
            if j==0:a.legend()
        emit(fig,'02_K3_K4_Scientific_Comparison','K3 / K4: original-unit profiles and the initial-state refinement','Class numbers are model-specific, not an alignment. K4 C1 is the 38-tract initial exception.\nK3 C2 contains the 475-tract parent. Lower/higher profile values are not independent validation.',writer=pdf,page=1)
        fig,ax=plt.subplots(2,2,figsize=(7.2,6.5));fig.subplots_adjust(left=.10,right=.93,bottom=.13,top=.86,hspace=.42,wspace=.45)
        trans=frame('K3_TO_K4_EXACT_MEMBERSHIP.csv').pivot(index='K3_model_class',columns='K4_model_class',values='n_tracts')
        ax[0,0].pcolormesh(np.arange(5)-.5,np.arange(4)-.5,trans.to_numpy(),cmap='Blues',shading='flat');ax[0,0].set(ylim=(2.5,-.5),xticks=range(4),xticklabels=['K4 C1\nQ state','K4 C2','K4 C3','K4 C4'],yticks=range(3),yticklabels=['K3 C1','K3 C2','K3 C3'],title='Exact saved-fit transitions')
        for i in range(3):
            for j in range(4):ax[0,0].text(j,i,str(trans.iloc[i,j]),ha='center',va='center',color='white' if trans.iloc[i,j]>800 else 'black')
        groups=sizes.loc[sizes.condition.eq('main')&sizes.k.eq(3)].sort_values('model_class');bottom=np.zeros(3)
        for q,color in [('Q1','#e3d7ba'),('Q2','#99c2bd'),('Q3','#43868d'),('Q4','#503a73')]:
            y=groups[q+'_n'].to_numpy()/groups.n_tracts.to_numpy()*100;ax[0,1].bar(np.arange(3)+1,y,bottom=bottom,color=color,label=q);bottom+=y
        ax[0,1].set(xlabel='K3 primary candidate class',ylabel='Tracts (%)',title='Original frozen quartile composition');ax[0,1].set_xticks([1,2,3]);ax[0,1].legend(ncol=2,fontsize=6)
        rare=frame('K4_38_TRACT_EXACT_IDENTITY.csv','tract_id');gr=gp.loc[rare.index]
        gp.plot(ax=ax[1,0],color='#efefef',edgecolor='none');gr.assign(value=100*rare.Init_Supply).plot(column='value',ax=ax[1,0],cmap='viridis',vmin=0,vmax=2.5,edgecolor='none')
        dep=frame('inputs/PRIOR_Q34_DEPENDENCY.csv');q=dep.loc[dep.substation_id.astype(str).eq('308581')].iloc[0];point=gpd.GeoSeries([Point(q.lon,q.lat)],crs=4326).to_crs(3310).iloc[0]
        ax[1,0].scatter(point.x,point.y,marker='^',s=24,color='#b34739',zorder=8)
        bounds=gr.total_bounds;ax[1,0].set_xlim(bounds[0]-2500,bounds[2]+2500);ax[1,0].set_ylim(bounds[1]-2500,bounds[3]+2500);ax[1,0].set_axis_off();ax[1,0].set_title('38 saved-fit members and Q proxy')
        ax[1,0].legend(handles=[Line2D([],[],marker='^',color='none',markerfacecolor='#b34739',label='STATION Q proxy')],loc='upper left',fontsize=6)
        cb=plt.colorbar(plt.cm.ScalarMappable(norm=colors.Normalize(0,2.5),cmap='viridis'),ax=ax[1,0],fraction=.04,pad=.02);cb.set_label('Initial modeled service (%)',fontsize=7)
        cb.solids.set_rasterized(False)
        trace=frame('Q38_ALL_STATION_DEPENDENCY_AND_CONTRIBUTION.csv');q_share=trace.groupby('substation_id').initial_tract_contribution.sum();q_share=q_share.sort_values(ascending=False)
        name_lookup=trace.drop_duplicates('substation_id').set_index('substation_id')['name']
        names=[name_lookup.loc[z].replace('STATION Q (HARBOR)','STATION Q\n(HARBOR)').replace('WILMINGTON (STATION C)','WILMINGTON\n(STATION C)') for z in q_share.index[:4]]
        ax[1,1].barh(names,100*q_share.iloc[:4]/q_share.sum(),color='#487f7d');ax[1,1].invert_yaxis();ax[1,1].set(xlabel='Share of initial service (%)',title='Frozen station contributions\nnot generation capacity');ax[1,1].set_xlim(0,105);ax[1,1].tick_params(axis='y',labelsize=6)
        emit(fig,'02_K3_K4_Scientific_Comparison','The extra class is a source-linked frozen-model state, not verified resilience','34 members depend on Q; the additional 4 depend mainly on HAYNES / ALAMITOS, not Q.\nQuartile composition shares fitted SOVI. Hospital incidence does not measure clinical electricity delivery.',writer=pdf,page=2)
    # Phase3 Figure7: coordinated candidate, never written into formal figure paths.
    fig=plt.figure(figsize=(7.2,8.2));gs=fig.add_gridspec(4,4,height_ratios=[.7,.82,.82,1.25],left=.08,right=.97,bottom=.11,top=.93,hspace=.75,wspace=.78)
    a1=fig.add_subplot(gs[0,:2]);a2=fig.add_subplot(gs[0,2:]);q=sizes.loc[sizes.condition.eq('main')&sizes.k.eq(3)].sort_values('model_class')
    a1.bar([1,2,3],q.n_tracts,color=PALETTE);a1.set_xticks([1,2,3],['C1','C2','C3']);a1.set(ylabel='Tracts',title='(A) Primary K3 class coverage')
    a2.bar([1,2,3],q.population_share*100,color=PALETTE);a2.set_xticks([1,2,3],['C1','C2','C3']);a2.set(ylabel='Residents (%)',title='Frozen population represented')
    for r in q.itertuples():
        a1.text(r.model_class+1,r.n_tracts+20,str(r.n_tracts),ha='center',fontsize=7)
        a2.text(r.model_class+1,r.population_share*100+.7,f'{r.population_share*100:.2f}',ha='center',fontsize=7)
    a1.set_ylim(0,1400);a2.set_ylim(0,64)
    for j,(field,title) in enumerate(zip(display,titles)):
        a=fig.add_subplot(gs[1+j//4,j%4]);vals=profiles.loc[profiles.condition.eq('main')&profiles.k.eq(3)&profiles.variable.eq(field)].sort_values('model_class');scale=100 if field=='Init_Supply' else 1
        a.bar([1,2,3],vals['mean']*scale,color=PALETTE);a.axhline(d[field].mean()*scale,color='black',ls='--',lw=.7);a.set_title(('(B) ' if j==0 else '')+title,fontsize=7);a.set_xticks([1,2,3],['C1','C2','C3']);a.tick_params(labelsize=6)
    membership=pd.Series(lab(3),index=d.index).reindex(g.index);a=fig.add_subplot(gs[3,:2]);category_map(a,g,membership,'(C) Primary candidate memberships',PALETTE,3)
    a=fig.add_subplot(gs[3,2:]);co=frame('candidate/PROPOSED_DESCRIPTIVE_COOCCURRENCE_TABLE.csv','tract_id');cats=co.candidate_display_category.reindex(g.index);cp=['#ececec','#e6b260','#779aae','#765080'];g.plot(ax=a,color='#d4d4d4',edgecolor='none');gg=g.loc[cats.notna()].assign(category=cats.dropna().astype(int));gg.plot(column='category',ax=a,cmap=colors.ListedColormap(cp),vmin=-.5,vmax=3.5,edgecolor='none');a.set_axis_off();a.set_title('(D) Proposed Q4 / high-deficit co-occurrence',fontsize=7,pad=6)
    a.legend(handles=[Patch(facecolor=cp[i],label=name) for i,name in enumerate(['Neither','Frozen Q4 only','High deficit only','Both conditions'])]+[Patch(facecolor='#d4d4d4',label='Zero population')],loc='upper right',fontsize=5.5)
    emit(fig,'Figure7_candidate',None,'All 2,299 positive-population tracts; 16 zero-population tracts are gray/unassigned. Dashed lines: cohort means.\nPanel D is a separately proposed descriptive screen, not the old weighted hotspot score or intervention ranking.')
    ev=frame('inputs/EXISTING_K_EVIDENCE.csv');fig,ax=plt.subplots(2,2,figsize=(7.2,6.0));fig.subplots_adjust(left=.10,right=.94,bottom=.14,top=.88,hspace=.48,wspace=.45)
    ax[0,0].plot(ev.k,ev.mean_WCSS,'o-',ms=3,color=PALETTE[0]);ax[0,0].axvspan(2.8,4.2,color='#e3eae7',alpha=.6);ax[0,0].set(xlabel='K',ylabel='Weighted WCSS',title='(A) Saved-fit elbow evidence')
    ax[0,1].plot(ev.k,ev.mean_silhouette,'o-',ms=3,color=PALETTE[1]);ax[0,1].axvspan(2.8,4.2,color='#e3eae7',alpha=.6);ax[0,1].set(xlabel='K',ylabel='Full-cohort mean silhouette',title='(B) Maximum at 4, not selected by score alone')
    st=frame('inputs/EXISTING_STABILITY.csv');tests=['seed','geographic','policy','Init_ablation'];values=[]
    for j,(k,color) in enumerate([(3,PALETTE[0]),(4,K4_COLORS[0])]):
        for i,test in enumerate(tests):
            sub=st.loc[st.k.eq(k)&st.test.eq(test)]
            if test=='policy':sub=sub.loc[sub.condition.str.contains('without_')&sub.condition.str.endswith('__cohort')]
            x0=i+(j-.5)*.18;ax[1,0].plot([x0,x0],[sub.ARI.min(),sub.ARI.max()],color=color,lw=2);ax[1,0].scatter(x0,sub.ARI.mean(),s=20,color=color)
    ax[1,0].set_xticks(range(4),['Seed','Geographic','Policy\nleaveout','Minus\nInit']);ax[1,0].set(ylim=(0,1.07),ylabel='ARI',title='(C) Conditional membership sensitivity');ax[1,0].legend(handles=[Line2D([],[],marker='o',color=PALETTE[0],label='K3'),Line2D([],[],marker='o',color=K4_COLORS[0],label='K4')])
    trans=frame('K3_TO_K4_EXACT_MEMBERSHIP.csv').pivot(index='K3_model_class',columns='K4_model_class',values='n_tracts');ax[1,1].pcolormesh(np.arange(5)-.5,np.arange(4)-.5,trans.to_numpy(),cmap='Blues',shading='flat');ax[1,1].set(ylim=(2.5,-.5),xticks=range(4),xticklabels=['C1\nQ state','C2','C3','C4'],yticks=range(3),yticklabels=['C1','C2','C3'],xlabel='K4 within-model class',ylabel='K3 within-model class',title='(D) Refinement, not four new mechanisms')
    for i in range(3):
        for j in range(4):ax[1,1].text(j,i,str(trans.iloc[i,j]),ha='center',va='center',color='white' if trans.iloc[i,j]>800 else 'black')
    emit(fig,'FigureS9_candidate','K3 primary interpretation; K4 explicit sensitivity','Existing K2-8 curves are reused; no new search or fitted PCA. Range lines are sensitivity ranges, not CIs.\nInit deletion also redistributes RQ1 weights. Class numbers are within-model and not old formal IDs.')
    fig,ax=plt.subplots(2,2,figsize=(7.2,6.7));fig.subplots_adjust(left=.035,right=.96,bottom=.12,top=.89,hspace=.15,wspace=.15)
    for a,k,condition,title,palette in [(ax[0,0],3,'main','Primary K3',PALETTE),(ax[0,1],4,'main','Sensitivity K4',K4_COLORS),(ax[1,0],3,'minus_Init','K3 without Init (RQ1 redistributed)',PALETTE),(ax[1,1],4,'minus_Init','K4 without Init (RQ1 redistributed)',K4_COLORS)]:
        category_map(a,g,pd.Series(lab(k,condition),index=d.index).reindex(g.index),title,palette,k)
    emit(fig,'03_Classification_Robustness_candidate','Same cohort, source reference and saved labels; different feature conditions','K4 colors align broad main-class patterns for display; class IDs remain model-specific.\nMinus-Init palettes do not assert matching classes. All zero-population study records remain gray.')
    dump('FIGURE_MANIFEST.json',dict(review_status=WARN,figures=manifest,vector_PDF=True,AI_generated_images=False,formal_paths_written=False))
    for name in sorted({r['name'] for r in manifest}):
        with fitz.open(str(lp(OUT/'figures'/ (name+'.pdf')))) as pdf:
            for i,page in enumerate(pdf):page.get_pixmap(matrix=fitz.Matrix(2,2)).save(str(dest('tmp/pdfs/'+name+'_page'+str(i+1)+'_review.png')))
    print('5 candidate PDFs,6 pages;600dpi PNGs;formal writes0',flush=True)

if __name__=='__main__':main()
