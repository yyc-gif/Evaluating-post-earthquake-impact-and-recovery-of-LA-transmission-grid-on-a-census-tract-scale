"""Assemble the July92 revised viewing suite from frozen outputs only.

This script reads results and redraws figures. It never invokes sampling, GA,
scheduling, source-gate evaluation, or recovery production code.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np
import pandas as pd
from PIL import Image
import fitz

ROOT=Path(__file__).resolve().parent
PARENT=ROOT.parent
SUITE=PARENT/'LA_Grid_Revised_Suite_20260925'
FORMAL=ROOT/'Formal_Experiment_20260923'
REV=FORMAL/'Formal_Reviewer_Results'
EQ=FORMAL/'Equity_Amendment'
SUP=ROOT/'Supplement_Rebuild_20260925'
JULY=PARENT/'Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale'
MANUSCRIPT=PARENT/'LA_grid_manuscript_rebuild'/'LA_Grid_Manuscript_Resubmission_Rebuild.docx'
HAZARDS=['Northridge','SanFernando','LongBeach','2pc50']
SCHEDULED=['centrality-first','impact-first','betweenness-first','degree-first','closeness-first','hospital-first','random','vulnerability-first']
STRATEGIES=['unconstrained']+SCHEDULED
DISPLAY={'unconstrained':'Unconstrained','centrality-first':'Centrality-first','impact-first':'Impact-first',
  'betweenness-first':'Betweenness-first','degree-first':'Degree-first','closeness-first':'Closeness-first',
  'hospital-first':'Hospital-first','random':'Random','vulnerability-first':'Vulnerability-first'}
PALETTE=dict(zip(STRATEGIES,['#3d4850','#6487a4','#d2784a','#728c71','#9b718f','#6fa5a2','#b79a50','#8f8f8f','#c64e4e']))

CM=2.54; DPI=600
RC={
 'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
 'mathtext.fontset':'custom','mathtext.rm':'Arial','mathtext.it':'Arial:italic','mathtext.bf':'Arial:bold',
 'axes.titlesize':9.5,'axes.labelsize':8.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,
 'legend.fontsize':7.5,'legend.title_fontsize':7.5,'figure.dpi':150,'savefig.dpi':600,
 'axes.unicode_minus':False,'axes.linewidth':.6,'grid.linewidth':.4,'grid.color':'#d9d9d9',
 'lines.linewidth':1.2,'patch.linewidth':.5,'xtick.major.width':.6,'ytick.major.width':.6,
 'xtick.major.size':3.,'ytick.major.size':3.,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
 'savefig.facecolor':'white','figure.facecolor':'white'}
plt.rcParams.update(RC)

for d in [*(SUITE/f'Stage {i} Output_expanded' for i in range(1,8)),SUITE/'Sensitivity Output_clean',
 SUITE/'Submission_Package'/'Main_Figures',SUITE/'Submission_Package'/'Supplementary_Figures',
 SUITE/'Submission_Package'/'Tables']:
 d.mkdir(parents=True,exist_ok=True)
manifest=[]; figures=[]

def sha(path:Path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def record(dst:Path,src:Path|None,kind:str,note=''):
 manifest.append({'suite_path':str(dst.relative_to(SUITE)).replace('\\','/'),
  'source_path':str(src) if src else 'generated_from_frozen_outputs',
  'source_sha256':sha(src) if src and src.is_file() else '',
  'suite_sha256':sha(dst),'bytes':dst.stat().st_size,'category':kind,'note':note})

def copy(src:Path,rel:str,kind='frozen_copy',note=''):
 assert src.is_file(),src
 dst=SUITE/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(src,dst);record(dst,src,kind,note)
 return dst

def write_df(df:pd.DataFrame,rel:str,sources:list[Path],note=''):
 dst=SUITE/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 df.to_csv(dst,index=False)
 record(dst,None,'derived_table',note+'; sources: '+'; '.join(str(p) for p in sources))
 return dst

def figsize(role):
 sizes={'fullrow':(18.5,7.0),'half':(8.9,6.6),'medium':(13.2,9.5),
  'full':(18.5,11.8),'dense':(18.5,13.0),'map':(18.5,11.8)}
 w,h=sizes[role];return (w/CM,h/CM)

def polish(ax,xlabel=None,ylabel=None):
 if xlabel:ax.set_xlabel(xlabel)
 if ylabel:ax.set_ylabel(ylabel)
 ax.grid(axis='y',color='#d9d9d9',linewidth=.4,alpha=.65)
 ax.set_axisbelow(True)
 ax.tick_params(width=.6,length=3)

def savefig(fig,base,section,title,sources,role='supp',description=''):
 folder='Main_Figures' if role=='main' else 'Supplementary_Figures'
 root=SUITE/'Submission_Package'/folder
 png=root/(base+'.png');pdf=root/(base+'.pdf')
 if base in {'Candidate_S18_Equity_Efficiency_Tradeoff','Candidate_S19_Vulnerability_Tract_Effects'}:
  fig.tight_layout(rect=(0,.10,1,1),pad=.5)
 elif base not in {'Candidate_S3_Initial_Service_Map','Candidate_S4_Unconstrained_T80_Map'}:
  fig.tight_layout(pad=.5)
 fig.savefig(png,dpi=600,facecolor='white')
 fig.savefig(pdf,facecolor='white')
 plt.close(fig)
 record(png,None,'formal_figure','; '.join(str(p) for p in sources))
 record(pdf,None,'formal_figure','; '.join(str(p) for p in sources))
 figures.append({'file':png,'pdf':pdf,'proposed_number':base,'title':title,'section':section,
  'description':description or title,'sources':'; '.join(str(p) for p in sources)})

def source(rel):return ROOT/rel

# Compact formal stage products, not the massive reproducibility event archive.
copy(ROOT/'FINAL_EXPERIMENT_MATRIX.json','Stage 1 Output_expanded/FINAL_EXPERIMENT_MATRIX.json')
for name in ['PHYSICAL_SAMPLE_MANIFEST.csv','PHYSICAL_INPUTS_FROZEN.json']:
 copy(FORMAL/'Stage 1 Output_expanded'/name,'Stage 1 Output_expanded/'+name)
for name in ['S1_DAMAGE_STATE_COUNTS.csv','S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv']:
 copy(SUP/'Tables'/name,'Stage 1 Output_expanded/'+name)
for name in ['substation_graph_CEC_edges.csv','JULY_UTILITY_CONSTRAINED_92.csv','tract_to_substation_mapping_CEC.csv']:
 copy(ROOT/'Data'/name,'Stage 2 Output_expanded/'+name)
# The 92-station topology itself is unchanged, so retain its July-standard panel.
network_png=copy(ROOT/'Manuscript_Figures'/'panel_a_direct_links_600dpi.png',
 'Submission_Package/Main_Figures/Candidate_Figure_Network_Topology.png',kind='retained_july_figure')
network_pdf=copy(ROOT/'Manuscript_Figures'/'panel_a_direct_links_600dpi.pdf',
 'Submission_Package/Main_Figures/Candidate_Figure_Network_Topology.pdf',kind='retained_july_figure')
figures.append({'file':network_png,'pdf':network_pdf,'proposed_number':'Candidate_Figure_Network_Topology',
 'title':'Retained 92-station / 318-edge study network','section':'Stage 2',
 'description':'Unchanged study topology at July manuscript size (13.2 cm width).',
 'sources':str(ROOT/'Manuscript_Figures'/'panel_a_direct_links_600dpi.pdf')})
copy(ROOT/'R1_Comment1_2_External_Evidence_20260922'/'SCE_MAPPING_BENCHMARK_SUMMARY.csv',
 'Stage 2 Output_expanded/SCE_PUBLIC_CANDIDATE_BENCHMARK.csv')
for name in ['FORMAL_MAPPING_EFFECTS.csv','FORMAL_GATE_COMPONENTS.csv','FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv',
 'FORMAL_SOURCE_LOSS_BY_STATION.csv','FORMAL_SOURCE_LOSS_BY_TRACT.csv',
 'FORMAL_SOURCE_MAPPING_SHIFT_BY_TRACT.csv']:
 section='Stage 2 Output_expanded' if name.startswith('FORMAL_MAPPING') else 'Stage 3 Output_expanded'
 copy(REV/name,section+'/'+name)
copy(FORMAL/'Stage 4 Output_expanded'/'FULL_RULE_SEQUENCES.json','Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json')
copy(EQ/'VULNERABILITY_FIRST_SEQUENCE.json','Stage 4 Output_expanded/VULNERABILITY_FIRST_SEQUENCE.json')
for name in ['GA_FIVE_SEED_CONVERGENCE.csv','INCUMBENT_DIRECT_SCORES_2pc50.csv','FINAL_DIRECT_COMMUNITY_SEQUENCE.json']:
 copy(FORMAL/'Stage 5 Output_expanded'/name,'Stage 5 Output_expanded/'+name,
  note='Direct-community is an alias of impact-first, not a distinct evaluated policy.')
for seed in range(42,47):
 copy(FORMAL/'Stage 5 Output_expanded'/f'GA_HISTORY_2pc50_{seed}.csv',f'Stage 5 Output_expanded/GA_HISTORY_2pc50_{seed}.csv')
copy(EQ/'GA_METHODS_CLARIFICATION.md','Stage 5 Output_expanded/GA_METHODS_CLARIFICATION.md')
for name in ['TRACT_PAIRED_EFFECTS.parquet','TRACT_CLASSIFICATION_POPULATION.csv']:
 copy(FORMAL/'Formal_Results'/name,'Stage 6 Output_expanded/'+name)
for f in (FORMAL/'Stage 7 Output_expanded').glob('*.csv'):
 copy(f,'Stage 7 Output_expanded/'+f.name)
for name in ['FORMAL_MAPPING_EFFECTS.csv','FORMAL_GATE_COMPONENTS.csv','FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv',
 'FORMAL_SOURCE_LOSS_CONCENTRATION.csv','FORMAL_RESOURCE_EFFECTS.csv','FORMAL_DISTRIBUTIONAL_EFFECTS.csv',
 'FORMAL_STRATEGY_EFFECTS.csv','FORMAL_MAPPING_TRACT_CLASSES.csv']:
 copy(REV/name,'Sensitivity Output_clean/'+name)
for name in ['VULNERABILITY_GROUP_SUMMARY.csv','VULNERABILITY_PAIRWISE_EFFECTS.csv',
 'VULNERABILITY_CLASSIFICATION_POPULATION.csv','VULNERABILITY_RESOURCE_EFFECTS.csv']:
 copy(EQ/name,'Sensitivity Output_clean/'+name)
copy(EQ/'NO_THRESHOLD_CONNECTIVITY_EQUIVALENCE.json','Sensitivity Output_clean/NO_THRESHOLD_CONNECTIVITY_EQUIVALENCE.json')

# One distinct-policy baseline table; duplicate direct-community rows are checked then removed.
primary=pd.read_parquet(FORMAL/'Formal_Results'/'PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet')
vulnerable=pd.read_parquet(EQ/'VULNERABILITY_PRIMARY_SUMMARY.parquet')
flt=lambda x:x[(x.resource_scenario=='C57_D1')&(x.mapping=='M1_UTILITY_003')&
 (x.gate=='G1_BASELINE_050')&(x.comparison_domain=='mapping_native_domain')]
base=flt(primary)
dup=base[base.strategy_id=='direct-community'].sort_values(['hazard','realization_id']).reset_index(drop=True)
impact=base[base.strategy_id=='impact-first'].sort_values(['hazard','realization_id']).reset_index(drop=True)
check_cols=['population_weighted_normalized_burden_hr','population_T80_hr','hospital_mean_normalized_burden_hr',
 'L_source_population_mass_weighted_hr','burden_Q4_hr','makespan_hr','total_travel_hr']
assert len(dup)==len(impact)==4000
for col in check_cols:assert np.array_equal(dup[col].to_numpy(),impact[col].to_numpy(),equal_nan=True),col
base=base[base.strategy_id!='direct-community'].copy()
vbase=flt(vulnerable)
assert len(base)==32000 and len(vbase)==4000
combined=pd.concat([base,vbase[base.columns]],ignore_index=True)
assert set(combined.strategy_id)==set(STRATEGIES) and len(combined)==36000
metric_cols=['population_weighted_normalized_burden_hr','population_resolved_mass_weighted_burden_hr',
 'population_T50_hr','population_T80_hr','hospital_mean_normalized_burden_hr','burden_Q1_hr','burden_Q2_hr',
 'burden_Q3_hr','burden_Q4_hr','signed_Q4_minus_Q1_hr','absolute_Q4_minus_Q1_hr','burden_gini',
 'L_self_population_mass_weighted_hr','L_threshold_population_mass_weighted_hr',
 'L_source_population_mass_weighted_hr','L_total_population_mass_weighted_hr','makespan_hr','total_travel_hr']
summary=combined.groupby(['hazard','strategy_id'])[metric_cols].agg(['mean','median','std']).reset_index()
summary.columns=['_'.join(str(v) for v in c if v) for c in summary.columns]
summary['strategy_id']=pd.Categorical(summary.strategy_id,STRATEGIES,ordered=True)
summary['hazard']=pd.Categorical(summary.hazard,HAZARDS,ordered=True)
summary=summary.sort_values(['hazard','strategy_id'])
sources=[FORMAL/'Formal_Results'/'PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet',EQ/'VULNERABILITY_PRIMARY_SUMMARY.parquet']
write_df(summary[summary.strategy_id=='unconstrained'],
 'Stage 3 Output_expanded/UNCONSTRAINED_RECOVERY_BY_HAZARD.csv',sources,
 'Four-hazard unconstrained recovery reference; source-connected M1 service proxy')
write_df(summary[summary.strategy_id!='unconstrained'],
 'Stage 4 Output_expanded/ALL_RULE_BASED_STRATEGIES_BY_HAZARD.csv',sources,
 'Eight distinct scheduled policies including vulnerability-first; 1,000 paired realizations per hazard')
write_df(summary,'Stage 6 Output_expanded/ALL_DISTINCT_STRATEGIES_BY_HAZARD.csv',sources,
 '36,000 rows summarized: 8 distinct scheduled policies plus unconstrained; direct-community checked identical then omitted')
write_df(summary,'Submission_Package/Tables/Table_S1_Full_Strategy_Results.csv',sources,
 'Full hazard by distinct-policy formal means, medians, SDs')
write_df(summary[summary.hazard=='2pc50'],'Submission_Package/Tables/Table_1_2pc50_Strategy_Results.csv',sources,
 'Primary hazard distinct-policy table')

# Main six complete strategy comparisons, all nine distinct/reference curves/points.
main_metrics=[
 ('population_weighted_normalized_burden_hr','Population cumulative burden','Mean normalized burden (h)','Candidate_Figure_Population_Burden'),
 ('population_T80_hr','Population T80','Modeled T80 (h)','Candidate_Figure_T80'),
 ('hospital_mean_normalized_burden_hr','Hospital-tract service burden','Hospital-tract burden (h)','Candidate_Figure_Hospital_Burden'),
 ('L_source_population_mass_weighted_hr','Source-path service loss','Source-path burden (h)','Candidate_Figure_Source_Path_Burden')]
for metric,title,xlab,name in main_metrics:
 subset=combined[combined.hazard=='2pc50']
 vals=subset.groupby('strategy_id')[metric].agg(['mean','std']).reindex(STRATEGIES)
 fig,ax=plt.subplots(figsize=figsize('fullrow'))
 y=np.arange(len(STRATEGIES))
 ax.barh(y,vals['mean'],color=[PALETTE[s] for s in STRATEGIES],height=.68)
 ax.set_yticks(y,[DISPLAY[s] for s in STRATEGIES]);ax.invert_yaxis()
 ax.set_xlabel(xlab);ax.grid(axis='x',color='#d9d9d9',linewidth=.4,alpha=.7);ax.set_axisbelow(True)
 savefig(fig,name,'Stage 6',title,sources,role='main',description='2pc50, C57, 1,000 paired realizations; eight distinct scheduled policies plus unconstrained reference.')

fig,ax=plt.subplots(figsize=figsize('dense'))
means=combined[combined.hazard=='2pc50'].groupby('strategy_id')[[f'burden_Q{i}_hr' for i in range(1,5)]].mean().reindex(STRATEGIES)
for k,s in enumerate(STRATEGIES):
 ax.plot(range(1,5),means.loc[s],marker='o',markersize=3,label=DISPLAY[s],color=PALETTE[s])
ax.set_xticks(range(1,5),[f'Q{i}' for i in range(1,5)]);polish(ax,'Fixed vulnerability quartile','Mean absolute normalized burden (h)')
ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.13),frameon=False)
savefig(fig,'Candidate_Figure_Q1_Q4_Absolute_Burden','Stage 6','Absolute burden by vulnerability quartile',sources,role='main',
 description='All distinct strategies; lower gap is not by itself an equity improvement.')

# Recovery curves reconstructed only from saved e(t) states; no evaluation kernel called.
map_df=pd.read_csv(ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv',dtype={'tract_id':str,'substation_id':str})
map_df['tract_id']=map_df.tract_id.str.zfill(11)
tr=map_df[['tract_id','population']].drop_duplicates(); pop=dict(zip(tr.tract_id,tr.population))
station_ids=[]
with np.load(next((FORMAL/'Formal_Trajectories'/'2pc50'/'C57_D1'/'impact-first').glob('*.npz'))) as z:
 station_ids=list(z['station_ids'].astype(str))
weight=np.zeros(92);denom=sum(pop.values());idx={s:i for i,s in enumerate(station_ids)}
for row in map_df.itertuples(index=False):weight[idx[row.substation_id]]+=float(row.population)*float(row.weight)/denom
assert np.isclose(weight.sum(),1)
grid=np.arange(481,dtype=float);curves=[]
for hazard in HAZARDS:
 for strategy in STRATEGIES:
  folder=(EQ/'T'/hazard/'C57_D1' if strategy=='vulnerability-first' else
          FORMAL/'Formal_Trajectories'/hazard/'C57_D1'/strategy)
  paths=sorted(folder.glob('*.npz'))
  assert len(paths)==1000,(hazard,strategy,len(paths))
  total=np.zeros(len(grid))
  for path in paths:
   with np.load(path) as z:
    assert list(z['station_ids'].astype(str))==station_ids
    values=z['e']@weight;times=z['event_time_hr']
    total+=values[np.clip(np.searchsorted(times,grid,side='right')-1,0,len(times)-1)]
  curves.extend({'hazard':hazard,'strategy_id':strategy,'time_hr':int(t),'mean_population_availability_proxy':float(v/1000)} for t,v in zip(grid,total))
 print('recovery curve projected',hazard,flush=True)
curves=pd.DataFrame(curves)
write_df(curves,'Stage 6 Output_expanded/ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv',
 [FORMAL/'FORMAL_TRAJECTORY_ARCHIVE_INDEX.json',EQ/'VULNERABILITY_TRAJECTORY_INDEX.json',ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv'],
 'Hourly display sampling of 1,000 frozen event-step e(t) curves per hazard and distinct policy; no trajectory rerun')
fig,ax=plt.subplots(figsize=figsize('fullrow'))
for strategy in STRATEGIES:
 part=curves[(curves.hazard=='2pc50')&(curves.strategy_id==strategy)]
 ax.plot(part.time_hr,part.mean_population_availability_proxy,label=DISPLAY[strategy],color=PALETTE[strategy],lw=1.2)
ax.set_xlim(0,120);ax.set_ylim(0,1.02);polish(ax,'Time after event (h)','Mean resolved service-availability proxy')
ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.17),frameon=False)
savefig(fig,'Candidate_Figure_All_Strategy_Recovery','Stage 6','All distinct strategy recovery curves',
 [SUITE/'Stage 6 Output_expanded'/'ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv'],role='main',
 description='2pc50/C57 mean of 1,000 frozen event-step trajectories; direct-community duplicate omitted.')

# Rebuild essential supplementary panels at July physical widths/typography.
damage=pd.read_csv(SUP/'Tables'/'S1_DAMAGE_STATE_COUNTS.csv')
fig,ax=plt.subplots(figsize=figsize('medium'))
piv=damage.pivot(index='hazard',columns='DS',values='mean_station_count').reindex(HAZARDS)
piv.plot.bar(stacked=True,ax=ax,color=['#87969f','#e9cc7a','#e7a567','#d46b53','#872c43'],width=.65)
polish(ax,'Hazard','Mean count of 92 stations');ax.legend(title='DS',ncol=5,fontsize=7.5,frameon=False)
savefig(fig,'Candidate_S1_Damage_Severity','Stage 1','Four-hazard damage severity',[SUP/'Tables'/'S1_DAMAGE_STATE_COUNTS.csv'])

init=pd.read_csv(SUP/'Tables'/'S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv',dtype={'tract_id':str})
fig,ax=plt.subplots(figsize=figsize('medium'))
for hazard,color in zip(HAZARDS,['#527b9a','#be8056','#6a9a73','#aa4f5d']):
 vals=np.sort(init.loc[init.hazard==hazard,'mean_initial_service_proxy'].to_numpy());ax.plot(vals,np.arange(1,len(vals)+1)/len(vals),label=hazard,color=color)
polish(ax,'Mean initial tract service proxy','Fraction of tracts');ax.set(xlim=(0,1),ylim=(0,1));ax.legend(frameon=False)
savefig(fig,'Candidate_S2_Initial_Service_CDF','Stage 1','Initial service by hazard',[SUP/'Tables'/'S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv'])

tract_geom=gpd.read_file(ROOT/'Data/LA_Tracts_With_Population.shp')[['GEOID','geometry']]
tract_geom['tract_id']=tract_geom.GEOID.astype(str).str.zfill(11)
def map_grid(data,column,filename,title,cmap,vmin,vmax,source_files,missing='#dddddd'):
 fig,axes=plt.subplots(2,2,figsize=figsize('map'))
 fig.subplots_adjust(right=.84,wspace=.08,hspace=.06)
 for ax,hazard in zip(axes.flat,HAZARDS):
  g=tract_geom.merge(data[data.hazard==hazard][['tract_id',column]],on='tract_id',how='left',validate='one_to_one')
  g.plot(column=column,ax=ax,cmap=cmap,vmin=vmin,vmax=vmax,linewidth=0,missing_kwds={'color':missing})
  ax.set_title(hazard,fontsize=9.5);ax.axis('off')
 cax=fig.add_axes([.87,.22,.022,.55]);cb=fig.colorbar(plt.cm.ScalarMappable(norm=colors.Normalize(vmin,vmax),cmap=cmap),cax=cax)
 cb.ax.tick_params(labelsize=7.5,width=.6,length=3)
 savefig(fig,filename,'Stage 1/3',title,source_files)
map_grid(init,'mean_initial_service_proxy','Candidate_S3_Initial_Service_Map','Initial modeled service map',
 'viridis',0,1,[SUP/'Tables'/'S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv'])
map_grid(init,'mean_T80_hr_when_reached','Candidate_S4_Unconstrained_T80_Map','Unconstrained tract T80 map',
 'magma',0,80,[SUP/'Tables'/'S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv'])

travel=pd.read_csv(ROOT/'Stage 4 Output_expanded/travel_task_to_task.csv',index_col=0)
assert travel.shape==(92,92)
fig,ax=plt.subplots(figsize=figsize('medium'));im=ax.imshow(travel,cmap='viridis',aspect='auto')
ax.set_xlabel('Next task');ax.set_ylabel('Previous task');cb=fig.colorbar(im,ax=ax);cb.ax.tick_params(labelsize=7.5);cb.set_label('Directed travel (h)',fontsize=7.5)
savefig(fig,'Candidate_S5_Directed_Travel','Stage 4','Directed task travel matrix',[ROOT/'Stage 4 Output_expanded/travel_task_to_task.csv'])

benchmark=pd.read_csv(ROOT/'R1_Comment1_2_External_Evidence_20260922'/'SCE_MAPPING_BENCHMARK_SUMMARY.csv')
b=benchmark[(benchmark.version=='NEW_20260922')&(benchmark.candidate_kind=='direct_site')]
assert len(b)==2 and set(b.tract_count)=={337}
fig,ax=plt.subplots(figsize=figsize('medium'));x=np.arange(3)
for offset,mapping,label,color in [(-.18,'JULY_BASELINE_92','July M0','#59758e'),(.18,'JULY_UTILITY_CONSTRAINED_92','Utility M1','#bb6b53')]:
 row=b[b.mapping==mapping].iloc[0];ax.bar(x+offset,[100*row[c] for c in ['any_match','top1','top3']],width=.36,color=color,label=label)
ax.set_xticks(x,['Any match','Top 1','Top 3']);ax.set_ylim(80,100);polish(ax,ylabel='Conditional agreement (%)');ax.legend(frameon=False)
savefig(fig,'Candidate_S6_SCE_Candidate_Benchmark','Stage 2','SCE candidate external consistency',[ROOT/'R1_Comment1_2_External_Evidence_20260922'/'SCE_MAPPING_BENCHMARK_SUMMARY.csv'])

gate=pd.read_csv(REV/'FORMAL_GATE_COMPONENTS.csv')
g=gate[(gate.resource_scenario=='C57_D1')&(gate.strategy_id=='hospital-first')].set_index('hazard').loc[HAZARDS]
fig,ax=plt.subplots(figsize=figsize('medium'));bottom=np.zeros(4)
for c,label,color in [('self_mean_hr','Self','#5a819b'),('threshold_mean_hr','Threshold','#d6ad61'),('source_mean_hr','Source path','#a55860')]:
 v=g[c].to_numpy();ax.bar(HAZARDS,v,bottom=bottom,color=color,label=label);bottom+=v
polish(ax,ylabel='Mean cumulative burden contribution (h)');ax.tick_params(axis='x',labelrotation=20);ax.legend(frameon=False)
savefig(fig,'Candidate_S7_Gate_Decomposition','Stage 3','Self/threshold/source-path loss',[REV/'FORMAL_GATE_COMPONENTS.csv'])

top=pd.read_csv(REV/'FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv')
t=top[(top.resource_scenario=='C57_D1')&(top.strategy_id=='hospital-first')].set_index('hazard').loc[HAZARDS]
fig,ax=plt.subplots(figsize=figsize('medium'))
for c,label,color in [('top1_fraction__mean','Top 1','#bb6655'),('top5_fraction__mean','Top 5','#866d9b'),('static_eight_fraction__mean','Static eight','#5a819b')]:ax.plot(HAZARDS,t[c],marker='o',markersize=3,label=label,color=color)
polish(ax,ylabel='Fraction of modeled source-path loss');ax.set_ylim(0,1);ax.legend(frameon=False)
savefig(fig,'Candidate_S8_Dynamic_Path_Concentration','Stage 3','Dynamic source-loss concentration',[REV/'FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv'])

ga=pd.read_csv(FORMAL/'Stage 5 Output_expanded'/'GA_FIVE_SEED_CONVERGENCE.csv')
fig,ax=plt.subplots(figsize=figsize('medium'))
for seed in range(42,47):
 hist=pd.read_csv(FORMAL/'Stage 5 Output_expanded'/f'GA_HISTORY_2pc50_{seed}.csv')
 ax.plot(np.arange(len(hist)),hist.best_so_far,label=f'Seed {seed}',lw=1.2)
ax.axhline(ga.incumbent_fitness.iloc[0],ls='--',lw=.8,color='black',label='Impact-first incumbent')
polish(ax,'Generation','Retained direct-objective fitness');ax.legend(ncol=3,fontsize=7.5,frameon=False)
savefig(fig,'Candidate_S9_GA_Reproducibility','Stage 5','Five-seed GA reproducibility',
 [FORMAL/'Stage 5 Output_expanded'/'GA_FIVE_SEED_CONVERGENCE.csv'])

# Formal Stage 7 diagnostics.
s7=FORMAL/'Stage 7 Output_expanded'
pca=pd.read_csv(s7/'pca_stats_with_eigenvalues.csv')
fig,ax=plt.subplots(figsize=figsize('half'));ax.bar(pca.PC,pca.Explained_Variance_Ratio,color='#5a819b')
ax.plot(pca.PC,pca.Cumulative_Ratio,color='#b65e54',marker='o',markersize=2.5)
polish(ax,ylabel='Explained / cumulative variance');ax.tick_params(axis='x',labelrotation=45)
savefig(fig,'Candidate_S10_PCA_Scree','Stage 7','PCA scree',[s7/'pca_stats_with_eigenvalues.csv'])
k=pd.read_csv(s7/'kmeans_k_diagnostics.csv')
fig,ax=plt.subplots(figsize=figsize('half'));ax.plot(k.k,k.inertia,marker='o',markersize=3,color='#5a819b')
polish(ax,'Clusters k','Within-cluster inertia')
savefig(fig,'Candidate_S11_Kmeans_Elbow','Stage 7','K-means elbow',[s7/'kmeans_k_diagnostics.csv'])
load=pd.read_csv(s7/'pca_loadings.csv').rename(columns={'Unnamed: 0':'feature'})
fig,ax=plt.subplots(figsize=figsize('medium'));im=ax.imshow(load.drop(columns='feature'),aspect='auto',cmap='RdBu_r',vmin=-1,vmax=1)
ax.set_yticks(range(len(load)),load.feature);ax.set_xticks(range(5),load.columns[1:]);cb=fig.colorbar(im,ax=ax);cb.ax.tick_params(labelsize=7.5);cb.set_label('Loading',fontsize=7.5)
savefig(fig,'Candidate_S12_PCA_Loadings','Stage 7','PCA loadings',[s7/'pca_loadings.csv'])
labels=pd.read_csv(s7/'clusters_labels_final.csv',dtype={'tract_id':str});labels.tract_id=labels.tract_id.str.zfill(11)
geo=tract_geom.merge(labels[['tract_id','cluster','SlowVulnerable_Hotspot_Top10']],on='tract_id',how='left',validate='one_to_one')
fig,ax=plt.subplots(figsize=figsize('map'));geo.plot(column='cluster',ax=ax,cmap='tab10',legend=True,linewidth=0,missing_kwds={'color':'#dddddd'});ax.axis('off')
savefig(fig,'Candidate_S13_Cluster_Map','Stage 7','Formal descriptive clusters',[s7/'clusters_labels_final.csv'])
fig,ax=plt.subplots(figsize=figsize('map'));geo.plot(ax=ax,color='#dddddd',linewidth=0)
geo[geo.SlowVulnerable_Hotspot_Top10.fillna(False).astype(bool)].plot(ax=ax,color='#ad5548',linewidth=0);ax.axis('off')
savefig(fig,'Candidate_S14_Hotspot_Map','Stage 7','Descriptive hotspot screening',[s7/'clusters_labels_final.csv'])

# Sensitivity plots from fixed-decision formal tables.
mapping=pd.read_csv(REV/'FORMAL_MAPPING_EFFECTS.csv')
mm=mapping[(mapping.comparison=='full92')&(mapping.strategy_id=='hospital-first')&
 (mapping.metric=='population_weighted_normalized_burden_hr')].set_index('hazard').loc[HAZARDS]
fig,ax=plt.subplots(figsize=figsize('half'));ax.bar(HAZARDS,mm.mean_delta,color='#5a819b');ax.axhline(0,color='black',lw=.6)
polish(ax,ylabel='M1 − M0 burden (h)');ax.tick_params(axis='x',labelrotation=35)
savefig(fig,'Candidate_S15_Mapping_Shift','Sensitivity','Production mapping effect',[REV/'FORMAL_MAPPING_EFFECTS.csv'])
cut=mapping[(mapping.hazard=='2pc50')&(mapping.strategy_id=='hospital-first')&
 (mapping.metric=='population_weighted_normalized_burden_hr')&mapping.comparison.str.contains('cutoff')]
fig,ax=plt.subplots(figsize=figsize('medium'));ax.bar(range(len(cut)),cut.mean_delta,color='#5a819b')
ax.set_xticks(range(len(cut)),cut.comparison.str.replace('2pc50_cutoff_','',regex=False),rotation=20)
polish(ax,ylabel='Burden change from own 3% baseline (h)')
savefig(fig,'Candidate_S16_Cutoff_Robustness','Sensitivity','Mapping cutoff robustness',[REV/'FORMAL_MAPPING_EFFECTS.csv'])
resource=pd.read_csv(REV/'FORMAL_RESOURCE_EFFECTS.csv')
r=resource[(resource.strategy_id=='hospital-first')&(resource.metric=='population_resolved_mass_weighted_burden_hr')]
fig,ax=plt.subplots(figsize=figsize('medium'));ax.bar(r.resource_scenario,r.target_mean,color='#7c9aaf')
polish(ax,ylabel='Mean population burden (h)');ax.tick_params(axis='x',labelrotation=45)
savefig(fig,'Candidate_S17_Resource_Sensitivity','Sensitivity','One-factor resource burden',[REV/'FORMAL_RESOURCE_EFFECTS.csv'])

# Reviewer-directed equity panels, using the same frozen 1,000-realization summaries.
fig,axes=plt.subplots(2,2,figsize=figsize('dense'))
focus=['hospital-first','impact-first','vulnerability-first','random']
for ax,hazard in zip(axes.flat,HAZARDS):
 for strategy in focus:
  row=summary[(summary.hazard==hazard)&(summary.strategy_id==strategy)].iloc[0]
  ax.scatter(row.population_weighted_normalized_burden_hr_mean,row.burden_Q4_hr_mean,
   s=26,color=PALETTE[strategy],label=DISPLAY[strategy])
 ax.set_title(hazard);polish(ax,'Population burden (h)','Q4 burden (h)')
handles,labels=axes.flat[0].get_legend_handles_labels()
fig.legend(handles,labels,ncol=4,loc='lower center',bbox_to_anchor=(.5,.01),frameon=False)
fig.subplots_adjust(bottom=.15)
savefig(fig,'Candidate_S18_Equity_Efficiency_Tradeoff','Stage 6/7',
 'Population versus highest-vulnerability burden',sources,
 description='Formal paired means for four hazards; four distinct fixed strategies. This is not an optimum frontier.')

tract_effect=pd.read_parquet(EQ/'VULNERABILITY_TRACT_EFFECTS.parquet')
tract_effect=tract_effect[(tract_effect.hazard=='2pc50')&
 tract_effect.reference_strategy.isin(['hospital-first','impact-first'])].copy()
tract_effect.tract_id=tract_effect.tract_id.astype(str).str.zfill(11)
class_color={'improved':'#4e819a','near-zero':'#eeeeee','worsened':'#c46150','unresolved':'#999999'}
fig,axes=plt.subplots(1,2,figsize=figsize('full'))
for ax,reference in zip(axes,['hospital-first','impact-first']):
 g=tract_geom.merge(tract_effect[tract_effect.reference_strategy==reference]
  [['tract_id','mean_effect_classification']],on='tract_id',how='left',validate='one_to_one')
 for klass,color in class_color.items():
  selected=g[g.mean_effect_classification==klass]
  if not selected.empty:selected.plot(ax=ax,color=color,linewidth=0,label=klass)
 ax.set_title('Vulnerability-first versus '+DISPLAY[reference]);ax.axis('off')
from matplotlib.patches import Patch
fig.legend([Patch(facecolor=c,label=k) for k,c in class_color.items()],list(class_color),
 ncol=4,loc='lower center',bbox_to_anchor=(.5,.02),frameon=False)
fig.subplots_adjust(bottom=.1)
savefig(fig,'Candidate_S19_Vulnerability_Tract_Effects','Stage 7',
 'Paired mean tract burden classification',[EQ/'VULNERABILITY_TRACT_EFFECTS.parquet'],
 description='2pc50, 1,000 paired realizations, ±1 h practical threshold; unresolved stays missing.')

resource_eq=pd.read_csv(EQ/'VULNERABILITY_RESOURCE_EFFECTS.csv')
resource_eq=resource_eq[(resource_eq.reference_strategy=='hospital-first')&
 resource_eq.metric.isin(['population_weighted_normalized_burden_hr','burden_Q4_hr'])].copy()
baseline_effect=EQ/'VULNERABILITY_PAIRWISE_EFFECTS.csv'
base_diff=pd.read_csv(baseline_effect)
base_diff=base_diff[(base_diff.hazard=='2pc50')&(base_diff.reference_strategy=='hospital-first')&
 (base_diff.metric.isin(resource_eq.metric))]
baseline_rows=base_diff.assign(resource_scenario='C57_D1')
resource_eq=pd.concat([resource_eq,baseline_rows.reindex(columns=resource_eq.columns)],ignore_index=True)
crew_cases=['C29_D1','C57_D1','C86_D1','C114_D1']
duration_cases=['C57_D075','C57_D1','C57_D125','C57_D150']
cases=crew_cases+duration_cases
fig,axes=plt.subplots(2,1,figsize=figsize('medium'),sharex=True)
for ax,metric,label in zip(axes,['population_weighted_normalized_burden_hr','burden_Q4_hr'],
 ['Population burden difference (h)','Q4 burden difference (h)']):
 vals=resource_eq[resource_eq.metric==metric].set_index('resource_scenario').reindex(cases)
 x=np.array([0,1,2,3,5,6,7,8]);y=vals.paired_mean_difference.to_numpy()
 ax.plot(x[:4],y[:4],color='#a85751',marker='o',markersize=3)
 ax.plot(x[4:],y[4:],color='#a85751',marker='o',markersize=3)
 ax.axhline(0,color='#555555',lw=.6);polish(ax,ylabel=label)
axes[-1].set_xticks(x,['29','57','86','114','0.75','1.0','1.25','1.5'])
axes[-1].set_xlabel('Crew count (left)     |     Repair-duration scale (right)')
savefig(fig,'Candidate_S20_Resource_Equity_Tradeoff','Sensitivity',
 'Vulnerability targeting under resource conditions',[EQ/'VULNERABILITY_RESOURCE_EFFECTS.csv',baseline_effect],
 description='2pc50 paired vulnerability-first minus hospital-first; crew and duration are one-factor cases.')

# Submission tables: one reference to each result family, without duplicate policy labels.
for name,src in [('Table_S2_Mapping_Effects.csv',REV/'FORMAL_MAPPING_EFFECTS.csv'),
 ('Table_S3_Gate_Components.csv',REV/'FORMAL_GATE_COMPONENTS.csv'),
 ('Table_S4_Dynamic_Topology.csv',REV/'FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv'),
 ('Table_S5_Resource_Effects.csv',REV/'FORMAL_RESOURCE_EFFECTS.csv'),
 ('Table_S6_Vulnerability_Paired_Effects.csv',EQ/'VULNERABILITY_PAIRWISE_EFFECTS.csv'),
 ('Table_S7_Cluster_Profiles.csv',s7/'stage7_cluster_profiles_raw_values.csv')]:
 copy(src,'Submission_Package/Tables/'+name)
copy(MANUSCRIPT,'Submission_Package/Manuscript_Candidate.docx',kind='draft_copy',
 note='Coauthor-review candidate copied from separate manuscript worktree; not final submission approval.')

# Ordered thumbnail index. This is a viewing aid; it never changes source panels.
idx=SUITE/'FIGURE_INDEX.pdf';doc=fitz.open();page=None
for i,entry in enumerate(figures):
 if i%3==0:page=doc.new_page(width=595.28,height=841.89)
 slot=i%3;y_top=30+slot*268
 page.insert_text((40,y_top+10),entry['proposed_number'],fontsize=10,fontname='hebo')
 page.insert_text((40,y_top+25),entry['title'][:95],fontsize=8,fontname='helv')
 page.insert_text((40,y_top+38),entry['description'][:112],fontsize=7,fontname='helv')
 im=Image.open(entry['file']);w,h=im.size;target_w=510;target_h=207
 scale=min(target_w/w,target_h/h);dw=w*scale;dh=h*scale
 left=40+(target_w-dw)/2
 page.insert_image(fitz.Rect(left,y_top+45,left+dw,y_top+45+dh),filename=str(entry['file']))
 page.draw_line((40,y_top+255),(555,y_top+255),color=(.85,.85,.85),width=.5)
doc.save(idx);doc.close();record(idx,None,'figure_index','Thumbnail previews only; images are not redrawn here')

readme=SUITE/'README_REVISED_SUITE.md'
readme.write_text('''# LA Grid revised result suite — 2026-09-25\n\n'''
 '''This is the complete **review/viewing** suite for the July 92-station, 318-edge reviewer revision. It is a sibling of, and does not modify, the protected July submission suite.\n\n'''
 '''Open `FIGURE_INDEX.pdf` first. Stage 1–7 contain results in the original analysis order; `Sensitivity Output_clean` groups all fixed-decision robustness outputs; `Submission_Package` contains candidate publication-width figures and concise tables. Figures are generated at July physical width tiers, Arial/DejaVu typography, 600 dpi PNG, and vector PDF when plotted with Matplotlib. `Candidate_` names mean panel/figure placement is not yet final.\n\n'''
 '''Formal raw event archives and reproducibility inputs remain in `LA_grid_reviewer_revision/Formal_Experiment_20260923`; they are not copied into this browsing suite. Every suite file has a source path and SHA-256 in `RESULT_SUITE_MANIFEST.csv`. Build script: `LA_grid_reviewer_revision/build_revised_result_suite.py`. The script reads only frozen results.\n\n'''
 '''The eight distinct scheduled decisions are Centrality-, Impact-, Betweenness-, Degree-, Closeness-, Hospital-, Random-, and Vulnerability-first. Unconstrained is a separate reference. The direct-community GA retained the Impact-first incumbent and is not counted as another distinct policy. Legacy GA-Balanced, GA-HospitalFirst, and GA-Efficiency are absent from revised formal comparisons.\n\n'''
 '''Figures describe source-connected service-availability proxies, not measured delivered electricity; clustering/hotspot figures are descriptive. The supplied manuscript is a coauthor-review draft.\n''',encoding='utf-8')
record(readme,None,'suite_document')

with (SUITE/'RESULT_SUITE_MANIFEST.csv').open('w',newline='',encoding='utf-8-sig') as f:
 writer=csv.DictWriter(f,fieldnames=list(manifest[0]));writer.writeheader();writer.writerows(manifest)
print('SUITE',SUITE,'FILES',len(manifest),'FIGURES',len(figures),'DISTINCT_POLICIES',len(SCHEDULED))
