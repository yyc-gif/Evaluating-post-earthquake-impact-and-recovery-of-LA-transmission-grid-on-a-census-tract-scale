"""Assemble the July92 revised viewing suite from frozen outputs only.

This script organizes frozen results and calls the retained July visualizer.
It never invokes sampling, GA, scheduling, or recovery production code.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# The retained July visualizer prints Unicode status markers. Windows pipes may
# otherwise use cp1252 and interrupt a successful figure export.
if hasattr(sys.stdout, "reconfigure"):
 sys.stdout.reconfigure(encoding="utf-8")

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

for d in [*(SUITE/f'Stage {i} Output_expanded' for i in range(1,8)),SUITE/'Sensitivity Output_clean',
 SUITE/'Submission_Package'/'Main_Figures',SUITE/'Submission_Package'/'Supplementary_Figures',
 SUITE/'Submission_Package'/'Tables']:
 d.mkdir(parents=True,exist_ok=True)
manifest=[]

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

# The builder stops at organized tables and display-only curve export.
# July visualization functions and the formal comparison renderer own all panels.
import subprocess
import Project_Visualizer as july
for name in ('impact_centrality_substations.csv','percolation_curve_impact.csv','percolation_curve_random.csv'):
 copy(FORMAL/'Stage 2 Output_expanded'/name,'Stage 2 Output_expanded/'+name)
july.OUTPUT_ROOT=str(SUITE)
july.apply_publication_style()
july.vis_stage2()
for name in ('vis_stage4_crew_bases_map','vis_stage4_logistics_heatmap_base_to_task_full','vis_stage4_logistics_heatmap_full'):
 for ext in ('.png','.pdf'):
  src=JULY/'Stage 4 Output_expanded'/(name+ext)
  if src.is_file(): copy(src,'Stage 4 Output_expanded/'+name+ext,kind='retained_july_static')
for script in ('render_revised_suite.py','render_revised_suite_comparisons.py'):
 subprocess.run([sys.executable,str(ROOT/script)],check=True)
main_pairs={
 'Candidate_Figure_Population_Burden':'Stage 6 Output_expanded/vis_stage6_paired_population_resolved_mass_weighted_burden_hr_2pc50',
 'Candidate_Figure_T80':'Stage 6 Output_expanded/vis_stage6_paired_population_T80_hr_2pc50',
 'Candidate_Figure_Hospital_Burden':'Stage 6 Output_expanded/vis_stage6_paired_hospital_mean_normalized_burden_hr_2pc50',
 'Candidate_Figure_Q1_Q4_Absolute_Burden':'Stage 6 Output_expanded/vis_stage6_absolute_group_burdens_2pc50',
 'Candidate_Figure_Source_Path_Burden':'Stage 6 Output_expanded/vis_stage6_paired_source_loss_2pc50',
 'Candidate_Figure_Network_Topology':'Stage 2 Output_expanded/vis_stage2_topology_with_tracts_latlon',
}
supp_pairs={
 'Candidate_S4_Unconstrained_T80_Map':'Stage 3 Output_expanded/vis_stage3_map_T80_2pc50',
 'Candidate_S5_Directed_Travel':'Stage 4 Output_expanded/vis_stage4_logistics_heatmap_full',
 'Candidate_S6_SCE_Candidate_Benchmark':'Sensitivity Output_clean/vis_sce_candidate_benchmark',
 'Candidate_S7_Gate_Decomposition':'Stage 3 Output_expanded/vis_stage3_loss_decomposition_2pc50',
 'Candidate_S8_Dynamic_Path_Concentration':'Sensitivity Output_clean/vis_dynamic_source_loss_concentration',
 'Candidate_S9_GA_Reproducibility':'Stage 5 Output_expanded/vis_stage5_five_seed_convergence',
 'Candidate_S15_Mapping_Shift':'Sensitivity Output_clean/vis_mapping_shift_magnitude_2pc50',
 'Candidate_S16_Cutoff_Robustness':'Sensitivity Output_clean/vis_mapping_cutoff_response',
 'Candidate_S17_Resource_Sensitivity':'Sensitivity Output_clean/vis_resource_crew_population_resolved_mass_weighted_burden_hr',
 'Candidate_S18_Equity_Efficiency_Tradeoff':'Stage 6 Output_expanded/vis_stage6_equity_efficiency_2pc50',
 'Candidate_S19_Vulnerability_Tract_Effects':'Stage 6 Output_expanded/vis_stage6_vulnerability_effect_magnitude_vs_hospital-first',
 'Candidate_S20_Resource_Equity_Tradeoff':'Sensitivity Output_clean/vis_resource_duration_burden_Q4_hr',
}
for folder,pairs in (('Main_Figures',main_pairs),('Supplementary_Figures',supp_pairs)):
 for target,origin in pairs.items():
  for ext in ('.png','.pdf'):
   src=SUITE/(origin+ext)
   assert src.is_file(),src
   shutil.copy2(src,SUITE/'Submission_Package'/folder/(target+ext))
subprocess.run([sys.executable,str(ROOT/'index_revised_suite.py')],check=True)
print('Revised suite organized and rendered from the July visualizer + frozen formal outputs.')
