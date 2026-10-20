"""Produce spatial result figures from saved diagnostics; does not execute the source gate."""
from pathlib import Path
import json, hashlib, ast
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, FormatStrFormatter
import fitz

R=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent;E=R/'External_Validation_Data'
read=lambda p,**k:pd.read_csv(p,**k)
tr=read(R/'Data/Tracts_Within_Expanded_Area.csv',dtype={'GEOID':str});tr.GEOID=tr.GEOID.str.zfill(11)
geo=gpd.GeoDataFrame(tr.drop(columns='wkt_geom'),geometry=gpd.GeoSeries.from_wkt(tr.wkt_geom,crs=4326))
s=read(R/'Data/working_area_substations_with_fragility.csv',dtype={'ID':str}).set_index('ID')
imp=pd.read_parquet(O/'STATIC_EVENT_TRACT_IMPACTS.parquet')
cover=read(O/'SCE_TRACT_INVENTORY_COVERAGE.csv',dtype={'tract_id':str})
bench=read(O/'SCE_MAPPING_BENCHMARK_TRACTS.csv',dtype={'tract_id':str})
names=['JULY_BASELINE_92','JULY_UTILITY_CONSTRAINED_92']
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'savefig.dpi':180,'font.family':'DejaVu Sans'})
def finish(fig,name):
    fig.savefig(O/(name+'.png'),bbox_inches='tight');fig.savefig(O/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
def geographic(ax,extent):
    ax.set_xlim(extent[:2]);ax.set_ylim(extent[2:]);ax.set_aspect(1/np.cos(np.radians(34)))
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.tick_params(labelsize=8)
    ax.xaxis.set_major_locator(MaxNLocator(4));ax.yaxis.set_major_locator(MaxNLocator(5))
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'));ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
def base(ax):
    geo.plot(ax=ax,facecolor='#f7f7f7',edgecolor='#dadada',linewidth=.15)
def point(ax,sid,label=None):
    q=s.loc[sid];ax.scatter(q.LONGITUDE,q.LATITUDE,marker='^',s=50,c='black',zorder=5)
    if label:ax.annotate(label,(q.LONGITUDE,q.LATITUDE),xytext=(4,4),textcoords='offset points',fontsize=8,zorder=6)
# New snapshot benchmark; gray candidates absent from92 not counted as mapping failure.
fig,axes=plt.subplots(1,2,figsize=(12,5.5))
palette=['#bdbdbd','#c35a4a','#278a7b']
for ax,name in zip(axes,names):
    base(ax)
    subset=bench[(bench.version=='NEW_20260922')&(bench.candidate_kind=='direct_site')&(bench.mapping==name)].set_index('tract_id')
    q=geo.merge(cover[cover.utility_domain=='SCE'][['tract_id','represented_direct_count']],left_on='GEOID',right_on='tract_id')
    q['class']=q.GEOID.map(lambda t:0 if t not in subset.index else (2 if subset.loc[t,'any_match'] else 1))
    for n,c in enumerate(palette):q[q['class']==n].plot(ax=ax,color=c,edgecolor='white',linewidth=.18)
    ax.set_title(name.replace('JULY_','').replace('_92','').replace('_',' '))
    geographic(ax,[-118.73,-117.69,33.68,34.38])
fig.legend(handles=[Line2D([0],[0],color=c,lw=8,label=t) for c,t in zip(palette,['Official candidates outside92','Represented, no mapped match','Represented, mapping match'])],loc='lower center',ncol=3,bbox_to_anchor=(.5,-.045))
fig.suptitle('SCE external consistency: coverage and conditional agreement are separate')
fig.tight_layout(rect=[0,.045,1,.96]);finish(fig,'Fig1_SCE_candidate_consistency')
# Station weights for local LADWP cases, no inferred neighborhood outage polygons.
fig,axes=plt.subplots(3,2,figsize=(11.3,12))
regions=[('300493','RS-J: Northridge / Reseda context',[-118.68,-118.35,34.12,34.34]),('301637','RS-N: LAX supply context',[-118.49,-118.30,33.87,34.015]),('308581','RS-Q: San Pedro / Port context',[-118.36,-118.18,33.69,33.83])]
for i,(sid,label,ext) in enumerate(regions):
    for j,name in enumerate(names):
        ax=axes[i,j];base(ax);d=imp[(imp.station_id==sid)&(imp.mapping==name)]
        q=geo.merge(d[['tract_id','direct_weight_loss']],left_on='GEOID',right_on='tract_id')
        q[q.direct_weight_loss>0].plot(ax=ax,column='direct_weight_loss',cmap='viridis',vmin=0,vmax=1,edgecolor='#666666',linewidth=.15)
        point(ax,sid,sid+' '+label.split(':')[0])
        if sid=='301637':
            geo[geo.GEOID=='06037980028'].boundary.plot(ax=ax,color='#cc3311',linewidth=1.5)
            ax.annotate('LAX interior reference tract\nRS-N weight = 0 in both maps',(-118.435,33.927),fontsize=8,color='#9e2518')
        ax.set_title(label+'\n'+('Baseline' if j==0 else 'Utility-constrained'))
        geographic(ax,ext)
sm=plt.cm.ScalarMappable(cmap='viridis',norm=plt.Normalize(0,1))
fig.colorbar(sm,ax=axes.ravel().tolist(),fraction=.024,pad=.03,label='Direct station weight (not observed outage fraction)')
fig.suptitle('Named LADWP relationships and July tract weights\nNeighborhood mentions are contextual; no full-neighborhood outage is assumed',y=.985,fontsize=13)
fig.subplots_adjust(top=.90,bottom=.06,left=.075,right=.84,hspace=.43,wspace=.30)
finish(fig,'Fig2_LADWP_named_geographies')
# Colorado's single graph edge vs public named system; plot actual public circuit geometry.
cir=gpd.read_file(E/'normalized/SCE_Distribution_circuits_0_Distribution_Circuits.geojson')
col=cir[cir.sub_name.str.startswith('Colorado')]
fig,axes=plt.subplots(1,3,figsize=(15,5))
for ax in axes:base(ax);geographic(ax,[-118.515,-118.345,33.985,34.095])
col.plot(ax=axes[0],color='#187ca3',linewidth=.6)
p1=s.loc['301105'];p2=s.loc['306694']
axes[0].plot([p1.LONGITUDE,p2.LONGITUDE],[p1.LATITUDE,p2.LATITUDE],color='#c8342d',lw=2.5)
for sid,label in [('301105','RS-K (LADWP)'),('306694','COLORADO (SCE)'),('308786','LA CIENEGA (SCE)')]:point(axes[0],sid,label)
axes[0].set_title('Only retained Colorado edge: RS-K\nBlue: public Colorado circuits')
axes[0].text(.02,.02,'Public sys_name: La Cienega 220/66\nSystem name is not a verified wire diagram.',transform=axes[0].transAxes,fontsize=8,bbox=dict(facecolor='white',alpha=.9,edgecolor='none'))
for ax,name in zip(axes[1:],names):
    d=imp[(imp.station_id=='301105')&(imp.mapping==name)]
    q=geo.merge(d[['tract_id','additional_path_loss']],left_on='GEOID',right_on='tract_id')
    q[q.additional_path_loss>1e-12].plot(ax=ax,column='additional_path_loss',cmap='magma_r',vmin=0,vmax=1,edgecolor='#555555',linewidth=.15)
    point(ax,'306694','COLORADO')
    ax.set_title(('Baseline' if name==names[0] else 'Utility-constrained')+'\nAdditional loss after RS-K removal')
fig.suptitle('Specific dependency mismatch: Colorado is isolated by RS-K removal in the abstract graph')
fig.tight_layout(rect=[0,.08,1,.92])
fig.colorbar(plt.cm.ScalarMappable(cmap='magma_r',norm=plt.Normalize(0,1)),ax=axes[1:],orientation='horizontal',fraction=.05,pad=.14,label='Additional tract proxy loss via Colorado disconnection (0–1)')
finish(fig,'Fig3_Colorado_dependency_diagnostic')
# Rotate the official page at PDF-render time; no reconstructed service geometry.
doc=fitz.open(E/'raw/references/LAX_RSX_FinalEA_2019.pdf')
doc[30].get_pixmap(matrix=fitz.Matrix(1.2,1.2).prerotate(-90)).save(O/'LAX_OFFICIAL_CONTEXT.png')
# Explicitly illustrative map-reading probes, not sampled observed customer territories.
rows=[]
probes=[('LAX interior',-118.408,33.9425,'301637','2019 EA PDF29 and31; analyst reference point within airport; not service boundary'),('San Pedro reference',-118.292,33.736,'308581','ZEPEO PDF24 names San Pedro; illustrative location, not proof all customers served byQ'),('Port terminal reference',-118.247,33.743,'308581','ZEPEO PDF24 names Port; illustrative location, no terminal-specific assignment established')]
for label,lon,lat,sid,basis in probes:
    tid=geo.loc[geo.intersects(Point(lon,lat)),'GEOID'].iloc[0]
    for name,path in zip(names,[R/'Data/tract_to_substation_mapping_CEC_expanded.csv',R/'R1_Comment1_July92_Utility_Constraint/JULY_UTILITY_CONSTRAINED_92.csv']):
        w=read(path,dtype={'tract_id':str,'substation_id':str});w.tract_id=w.tract_id.str.zfill(11);q=w[w.tract_id==tid].sort_values('weight',ascending=False)
        rows.append(dict(reference=label,longitude=lon,latitude=lat,tract_id=tid,mapping=name,queried_station=sid,station_weight=float(q.loc[q.substation_id==sid,'weight'].sum()),candidate_ids=';'.join(q.substation_id),candidate_weights=';'.join(f'{v:.9f}' for v in q.weight),basis=basis,not_observed_outage_polygon=True))
pd.DataFrame(rows).to_csv(O/'LADWP_GEOGRAPHIC_REFERENCE_CHECKS.csv',index=False,encoding='utf-8-sig')
# Explicit per-event chronology from preserved official articles.
news=read(E/'normalized/LADWP_OFFICIAL_NEWS_RECORDS.csv').set_index('post_id')
case=[]
for time,stage,status,customers,post,notes in [
('2017-07-08 18:52','fire begins','reported occurred','not yet determined',4867,'One part burns; not all equipment known damaged'),
('2017-07-08 18:55','station isolated','reported occurred','initial >140000',4888,'Full shutdown for firefighter/crew safety'),
('2017-07-08 22:00','partial restoration','reported occurred','>50000 restored',4888,'Operators stabilized surrounding system; no claim all permanent repairs finished'),
('2017-07-09 05:00','inspection / equipment clearance','reported ongoing','approximately94000 remain',4888,'Conductors/breakers/transformers cleared; inspection before re-energization'),
('2017-07-09 05:00','majority restoration in2–4h','forecast only','not an actual restoration count',4888,'Conditional on no further problems'),
('2017-07-09 06:00–08:00','remaining customers restored','reported occurred','94000 restored; allby08:00',4911,'Actual later update supersedes forecast'),
('2017-07-09 10:30 update','permanent repairs','ongoing; completion not reported','service already restored',4911,'Customer restoration precedes full permanent repair completion')]:
    case.append(dict(case='RS-J2017',July92_ID='300493',time_local=time,process_stage=stage,evidence_status=status,customers_wording=customers,notes=notes,official_URL=news.loc[post,'URL'],raw_source=news.loc[post,'raw_file']))
other=read(E/'normalized/LADWP_NAMED_STATION_CASES.csv',keep_default_na=False)
for q in other.itertuples():
    if q.station=='RS-J':continue
    case.append(dict(case=q.station,July92_ID='',time_local=q.event_date,process_stage='Retained case, not linked toJuly92 without upstream evidence',evidence_status=q.evidence_status,customers_wording=q.customers_affected,notes=q.safety_isolation_inspection_notes,official_URL=q.official_URLs,raw_source=q.source_snapshot))
pd.DataFrame(case).to_csv(O/'NAMED_EVENT_PROCESS.csv',index=False,encoding='utf-8-sig')
# One uniquely identifiable circuit–tract relationship from same provider event, not proximity.
p=O/'CPUC_EVENT_KEY_COVERAGE.csv';z=read(p)
t=read(E/'normalized/CPUC_tract_events_sce_2023amended_postsr2b_1-22-2025.csv',dtype={'GEOID_11':str})
z['unique_reported_circuit_tract_link']=(z.named_circuit_rows==1)&(z.official_tract_rows==1)&(z.observed_customers_circuit_sum==z.observed_customers_tract_sum)
z['unique_tract_id']=''
for i,row in z[z.unique_reported_circuit_tract_link].iterrows():
    q=t[t.EVENTID.str.strip().str.upper()==row.event_key];z.loc[i,'unique_tract_id']=q.GEOID_11.iloc[0]
    z.loc[i,'link_meaning']='One named circuit + one tract + identical5 accounts under exact same provider event ID; outsideJuly study tract domain; not individual customer key'
z.to_csv(p,index=False,encoding='utf-8-sig')
print('Figures and case/reference tables saved.')
