"""Presentation from saved labels and existing polygons; no scientific fitting/extraction."""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import TwoSlopeNorm
import fitz
from common import *
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':8.5,'ytick.labelsize':8.5,'legend.fontsize':8.5,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
MM=1/25.4
qa=[]
def export(fig,name):
 fig.savefig(lp(OUT/(name+'.pdf')));fig.savefig(lp(OUT/(name+'.png')),dpi=600)
 doc=fitz.open(lp(OUT/(name+'.pdf')));page=doc[0]
 page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(str(lp(OUT/(name+'_native_preview.png'))))
 fonts=[s['size'] for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
 qa.append(dict(figure=name,pages=len(doc),width_mm=page.rect.width*25.4/72,height_mm=page.rect.height*25.4/72,min_font_pt=min(fonts),vector_pdf=True,png_dpi=600,visual_inspection='pending'))
 doc.close();plt.close(fig)

z=np.load(lp(OUT/'CORE3_W1_FROZEN_REFERENCE.npz'));ids=z['tract_ids'].astype(str);labels=z['labels']
p=pd.read_csv(lp(OUT/'CORE3_W1_PROFILE_TABLE.csv')).set_index('review_class')
master=pd.read_csv(lp(OUT/'CORE3_W1_LABELS_2291.csv'),dtype={'tract_id':str})
for ext in ['shp','shx','dbf','prj','cpg']:source('Data/LA_Tracts_With_Population.'+ext,'031d2c675f8e7d58035d27448be040b809ced086')
g=gpd.read_file(source('Data/LA_Tracts_With_Population.shp','031d2c675f8e7d58035d27448be040b809ced086'))
idcol=next(c for c in ['GEOID','GEOID20','tract_id'] if c in g)
g['tract_id']=g[idcol].astype(str).str.zfill(11)
allids=pd.read_csv(lp(OUT/'OUTSIDE_RESIDENTIAL_COHORT.csv'),dtype={'tract_id':str}).tract_id.tolist()+master.tract_id.tolist()
g=g[g.tract_id.isin(allids)].copy();assert len(g)==2315 and g.tract_id.nunique()==2315 and g.is_valid.all()
g=g.to_crs(3310).merge(master[['tract_id','review_class']],on='tract_id',how='left',validate='one_to_one')
fig,ax=plt.subplots(figsize=(185*MM,165*MM));fig.subplots_adjust(left=.025,right=.98,top=.93,bottom=.13)
ax.set_title('CORE3/W1 residential community classification',pad=9)
g.plot(ax=ax,color='white',edgecolor='#b5b5b5',linewidth=.12)
g[g.tract_id.isin(UNRESOLVED)].plot(ax=ax,color='#858585',edgecolor='#525252',linewidth=.25)
for cl,c in PALETTE.items():g[g.review_class==cl].plot(ax=ax,color=c,edgecolor='white',linewidth=.08)
gpd.GeoSeries([g.geometry.union_all().boundary],crs=g.crs).plot(ax=ax,color='#555555',linewidth=.6)
x0,y0,x1,y1=g.total_bounds;spanx=x1-x0;spany=y1-y0
ax.set_xlim(x0-.02*spanx,x1+.02*spanx);ax.set_ylim(y0-.02*spany,y1+.02*spany);ax.set_axis_off()
# The scale is in the existing EPSG3310 meter coordinates; north orientation at study center.
sx=x0+.08*spanx;sy=y0+.07*spany
ax.plot([sx,sx+20000],[sy,sy],color='#222222',lw=1.8);ax.text(sx+10000,sy+.02*spany,'20 km',ha='center',fontsize=9)
from pyproj import Transformer
to_ll=Transformer.from_crs(3310,4326,always_xy=True);to_xy=Transformer.from_crs(4326,3310,always_xy=True)
nx=x1-.08*spanx;ny=y0+.11*spany;lon,lat=to_ll.transform(nx,ny);ex,ey=to_xy.transform(lon,lat+.1)
v=np.array([ex-nx,ey-ny]);v=v/np.linalg.norm(v)*.07*spany
ax.annotate('',xy=(nx+v[0],ny+v[1]),xytext=(nx,ny),arrowprops=dict(arrowstyle='-|>',color='#222',lw=1));ax.text(nx+v[0],ny+v[1]+.018*spany,'N',ha='center',fontsize=9)
handles=[Patch(facecolor=c,label=f'{cl}  (n={int(p.loc[cl,"n"]):,})') for cl,c in PALETTE.items()]
handles += [Patch(facecolor='#858585',label='Unclassified geometry (4)'),Patch(facecolor='white',edgecolor='#888',label='Outside residential cohort (24)')]
fig.legend(handles=handles,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.015),columnspacing=1.2,handlelength=1.2)
export(fig,'FIG_CORE3_W1_MEMBERSHIP')
dump('MAP_GEOMETRY_QA.json',dict(n=2315,classified=2287,unclassified=4,outside_residential=24,valid_polygons=2315,CRS='EPSG3310',study_boundary='union of archived tract polygons; not service territory',palette=PALETTE))

names=['Cumulative modeled service loss (h)','Initial modeled service','Dependency-weighted degree','Dependency-weighted λ2 impact','Dependency-weighted betweenness','Dependency concentration (HHI)','EMC2022 built-land fraction','ACS housing units in 5+ structures','SCAG2020 classified-land entropy','FEMA social vulnerability score','Log monetary building stock','Multi-hazard loss-rate percentile']
means=np.array([z['values'][labels==c].mean(0) for c in range(4)]).T
visual=(means-z['scaler_mean'][:,None])/z['scaler_scale'][:,None]
fig,ax=plt.subplots(figsize=(185*MM,148*MM));fig.subplots_adjust(left=.47,right=.93,top=.89,bottom=.22)
im=ax.imshow(visual,cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-2.5,vcenter=0,vmax=2.5),aspect='auto')
ax.set_yticks(range(12),names);plt.setp(ax.get_yticklabels(),ha='right');ax.tick_params(axis='y',length=0,pad=6)
ax.set_xticks(range(4),[f'C{i+1}\nn={int(p.iloc[i]["n"]):,}' for i in range(4)]);ax.tick_params(axis='x',length=0,pad=6)
for j in range(12):
 for i in range(4):ax.text(i,j,f'{visual[j,i]:+.2f}',ha='center',va='center',fontsize=9,color='white' if abs(visual[j,i])>1.5 else '#222')
for y in [1.5,5.5,8.5,9.5,10.5]:ax.axhline(y,color='white',lw=2)
for sp in ax.spines.values():sp.set_visible(False)
fig.suptitle('Joint CORE3/W1 profiles',y=.96,fontsize=11)
cax=fig.add_axes([.47,.075,.46,.025]);cb=fig.colorbar(im,cax=cax,orientation='horizontal',extend='both',ticks=[-2.5,0,2.5]);cb.set_label('Tract-mean z score; colors saturate beyond ±2.5',fontsize=8.5)
export(fig,'FIG_CORE3_W1_PROFILES')

sp=pd.read_csv(lp(OUT/'VERIFIED_SPATIAL_RUNS.csv'));we=pd.read_csv(lp(OUT/'VERIFIED_WEIGHT_REASSIGNMENTS.csv'));dom=pd.read_csv(lp(OUT/'VERIFIED_DOMAIN_SEPARATION.csv'))
fig=plt.figure(figsize=(185*MM,158*MM));gs=fig.add_gridspec(2,2,left=.10,right=.97,bottom=.16,top=.90,hspace=.56,wspace=.32,height_ratios=[1.1,1])
axes=[fig.add_subplot(gs[0,0]),fig.add_subplot(gs[0,1]),fig.add_subplot(gs[1,:])]
for j,scheme in enumerate(['W1','W2','W3','W4','W5']):
 vals=sp[sp.scheme==scheme].ARI_all.to_numpy();axes[0].scatter(j+np.linspace(-.13,.13,20),vals,s=16,alpha=.65,color='#4477AA');axes[0].plot([j-.2,j+.2],[np.median(vals)]*2,color='black',lw=1.7)
 vals=we[we.scheme==scheme].reassigned_percentage.to_numpy();axes[1].scatter(j+np.linspace(-.13,.13,20),vals,s=16,alpha=.65,color='#4477AA');axes[1].plot([j-.2,j+.2],[np.median(vals)]*2,color='black',lw=1.7)
for ax in axes[:2]:ax.set_xticks(range(5),['W1','W2','W3','W4','W5']);ax.grid(axis='y',alpha=.18)
axes[0].set_ylabel('Spatial-deletion ARI');axes[0].set_ylim(0,1.035);axes[0].set_title('A  Geographic sensitivity',loc='left');axes[1].set_ylabel('Reassigned tracts (%)');axes[1].set_title('B  Weight-dependent membership',loc='left');axes[1].set_ylim(-1,42)
colors=['#4477AA','#66CCEE','#228833','#EE7733','#CCBB44','#AA3377'];left=np.zeros(5)
for domain,c in zip(DOMAINS,colors):
 vals=np.array([dom[(dom.scheme==s)&(dom.domain==domain)].domain_between_fraction.median()*100 for s in ['W1','W2','W3','W4','W5']]);axes[2].barh(range(5),vals,left=left,color=c,label=domain,height=.64);left+=vals
axes[2].set_yticks(range(5),['W1','W2','W3','W4','W5']);axes[2].invert_yaxis();axes[2].set_xlim(0,100.5);axes[2].set_xlabel('Median between-class separation share (%)');axes[2].set_title('C  Observed domain contribution',loc='left');axes[2].legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.30),frameon=False,columnspacing=1.6)
fig.suptitle('Specification and spatial sensitivity',y=.97,fontsize=11);export(fig,'FIG_CORE3_W1_STABILITY')

mi=pd.read_csv(lp(OUT/'CORE3_W1_MINOR_GROUP_AUDIT.csv'));a=mi.query('scheme=="W1" and scope=="spatial_all"').sort_values('seed')
fig=plt.figure(figsize=(185*MM,150*MM));gs=fig.add_gridspec(2,2,left=.10,right=.97,top=.89,bottom=.21,hspace=.65,wspace=.35,height_ratios=[1,1.1]);ax=fig.add_subplot(gs[0,:]);ab=fig.add_subplot(gs[1,0]);ac=fig.add_subplot(gs[1,1])
ax.plot(a.seed,a.retention*100,'o-',color='#4477AA',ms=4,label='Original-member retention');ax.plot(a.seed,a.purity*100,'s-',color='#CC3311',ms=4,label='Predicted-class purity');ax.set_ylim(0,108);ax.set_xticks([42,46,50,54,58,61]);ax.set_ylabel('Percent');ax.set_xlabel('Registered spatial case seed');ax.set_title('A  Retention is distinct from specificity',loc='left');ax.legend(loc='lower left',frameon=False,ncol=2)
ab.bar([0,1],[34,34],color='#4477AA',label='Original members');ab.bar(1,58,bottom=34,color='#c4c4c4',label='Incoming members');ab.set_xticks([0,1],['Reference','Seed54 deletion']);ab.set_ylabel('Tracts in matched class');ab.set_ylim(0,112);ab.set_title('B  Four training members remain',loc='left');ab.text(1,94,'34 + 58 = 92',ha='center',fontsize=9);ab.legend(loc='upper center',bbox_to_anchor=(.5,-.28),frameon=False,fontsize=8.5)
for j,s in enumerate(['W1','W2','W3','W4','W5']):
 r=mi.query('scheme==@s and seed==54 and scope=="spatial_all"').iloc[0];raw=sorted(json.loads(r.destination_counts),reverse=True);counts=[raw[0],sum(raw[1:])];b=0
 for k,n in enumerate(counts):
  if n:ac.bar(j,n,bottom=b,color=['#4477AA','#66CCEE','#CCBB44','#CC3311'][k],width=.65);b+=n
ac.set_xticks(range(5),['W1','W2','W3','W4','W5']);ac.set_ylim(0,39);ac.set_ylabel('Original 34 tracts');ac.set_title('C  Actual destination distribution',loc='left');ac.legend(handles=[Patch(color='#4477AA',label='Largest destination'),Patch(color='#66CCEE',label='All other destinations')],loc='upper center',bbox_to_anchor=(.5,-.28),frameon=False,fontsize=8.5)
fig.suptitle('Minority-group specificity',y=.97,fontsize=11);export(fig,'FIG_CORE3_W1_MINORITY')

table_rows=[('Tracts',[f'{int(v):,}' for v in p.n]),('Mapped population',[f'{int(v):,}' for v in p.mapped_population])]
for c,n in zip(COLS,names):
 scale=100 if c=='Init_Supply' else 1
 if scale==100:n+=' (%)'
 table_rows.append((n,[f'{p.loc[k,c+"_mean"]*scale:.3f} [{p.loc[k,c+"_median"]*scale:.3f}]' for k in PALETTE]))
table_rows += [('Monetary stock ($ million)',[f'{p.loc[k,"NRI_BUILDVALUE_mean"]/1e6:.2f} [{p.loc[k,"NRI_BUILDVALUE_median"]/1e6:.2f}]' for k in PALETTE]),('T80 (h), descriptive',[f'{p.loc[k,"T80_mean"]:.2f} [{p.loc[k,"T80_median"]:.2f}]' for k in PALETTE]),('SCAG classified coverage, median',[f'{p.loc[k,"scag2020_classified_land_coverage_median"]:.3f}' for k in PALETTE]),('ACS 5+ share 90% MOE, median',[f'{p.loc[k,"housing_5plus_share_moe90_median"]:.3f}' for k in PALETTE]),('Population-weighted loss (h)',[f'{p.loc[k,"population_weighted_service_loss_hr"]:.3f}' for k in PALETTE])]
dump('PROFILE_TABLE_DISPLAY.json',dict(columns=['Measurement','C1','C2','C3','C4'],rows=[[n,*v] for n,v in table_rows],mean_median='mean [median]; tract-weighted except explicitly identified rows'))
fig,ax=plt.subplots(figsize=(185*MM,205*MM));fig.subplots_adjust(left=.025,right=.975,top=.94,bottom=.08);ax.axis('off');ax.set_title('Original-unit CORE3/W1 class profiles',fontsize=11,pad=12)
tbl=ax.table(cellText=[[n,*v] for n,v in table_rows],colLabels=['Measurement','C1','C2','C3','C4'],colWidths=[.40,.15,.15,.15,.15],loc='upper center',cellLoc='center',bbox=[0,.02,1,.95]);tbl.auto_set_font_size(False);tbl.set_fontsize(8.5)
for (r,c),cell in tbl.get_celld().items():
 cell.set_edgecolor('#d0d0d0');cell.set_linewidth(.4)
 if r==0:cell.set_facecolor('#e6e6e6');cell.set_text_props(weight='bold')
 elif c==0:cell.set_text_props(ha='left');cell.set_facecolor('#f5f5f5');cell.PAD=.025
fig.text(.5,.035,'Mean [median]; unweighted tracts unless stated. Coverage and T80 are descriptive.',ha='center',fontsize=8.5)
export(fig,'TABLE_CORE3_W1_PROFILES')
dump('FIGURE_RENDER_QA.json',qa);log('Rendered four new vector figures and one raw-profile table from saved data, with 600-dpi PNGs and native-width previews; all actual pages require visual inspection.')
