"""Plot/table-only supplement rebuild from frozen July92 formal outputs."""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Supplement_Rebuild_20260925'
FIG = OUT / 'Figures'
TAB = OUT / 'Tables'
FORMAL = ROOT / 'Formal_Experiment_20260923'
REV = FORMAL / 'Formal_Reviewer_Results'
EQUITY = FORMAL / 'Equity_Amendment'
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.size': 9, 'figure.dpi': 150, 'savefig.dpi': 300, 'pdf.fonttype': 42})

inventory = []
captions = []
script = 'Supplement_Rebuild_20260925/build_supplement.py'

def add(sid, section, title, status, source, table='', png='', pdf='', main='no', supp='yes', notes='', caption=''):
    inventory.append(dict(supp_id=sid, proposed_section=section, title=title, status=status,
        source_results_path=source, source_csv_or_table=table, figure_script_path=script if png else '',
        output_png=png, output_pdf=pdf, needed_for_main_paper=main,
        needed_for_supplement=supp, notes=notes))
    if caption:
        captions.append(f'**{sid}. {title}.** {caption} Source: `{source}`' + (f'; `{table}`.' if table else '.'))

def save(name):
    plt.tight_layout()
    plt.savefig(FIG / f'{name}.png', bbox_inches='tight')
    plt.savefig(FIG / f'{name}.pdf', bbox_inches='tight')
    plt.close()
    return (f'Supplement_Rebuild_20260925/Figures/{name}.png',
            f'Supplement_Rebuild_20260925/Figures/{name}.pdf')

# S1. Frozen evaluation damage draws; no new damage sampling.
hazards = ['Northridge', 'SanFernando', 'LongBeach', '2pc50']
counts = []
for hazard in hazards:
    with np.load(FORMAL / 'Stage 1 Output_expanded' / f'physical_inputs_{hazard}.npz') as z:
        ds = z['evaluation_ds']
        assert ds.shape == (92, 1000)
        counts.extend({'hazard': hazard, 'DS': d, 'mean_station_count': float((ds == d).sum(axis=0).mean())} for d in range(5))
damage = pd.DataFrame(counts)
damage.to_csv(TAB / 'S1_DAMAGE_STATE_COUNTS.csv', index=False)
fig, ax = plt.subplots(figsize=(7, 3.5))
pivot = damage.pivot(index='hazard', columns='DS', values='mean_station_count').loc[hazards]
pivot.plot.bar(stacked=True, ax=ax, color=['#87969f','#e9cc7a','#e7a567','#d46b53','#872c43'])
ax.set_ylabel('Mean number of 92 stations'); ax.set_xlabel('Hazard')
ax.legend(title='Damage state', ncol=5, loc='upper center', bbox_to_anchor=(.5, 1.23))
png,pdf=save('S1_damage_state_severity')
add('S1','S1 Damage and initial conditions','Damage-state severity across four hazards','KEEP_UPDATE',
    'Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_*.npz',
    'Supplement_Rebuild_20260925/Tables/S1_DAMAGE_STATE_COUNTS.csv',png,pdf,
    caption='Mean counts of stations in DS0–DS4 across the 1,000 frozen evaluation realizations per hazard. These are model draws, not observed earthquake damage.')

# S3. External benchmark is conditional on directly representable 337 tracts.
bpath = 'R1_Comment1_2_External_Evidence_20260922/SCE_MAPPING_BENCHMARK_SUMMARY.csv'
benchmark = pd.read_csv(ROOT/bpath)
b = benchmark[(benchmark.version == 'NEW_20260922') & (benchmark.candidate_kind == 'direct_site')]
assert set(b.tract_count) == {337} and len(b)==2
b.to_csv(TAB/'S3_SCE_337_CANDIDATE_BENCHMARK.csv',index=False)
labels=['Any candidate','Top 1','Top 3']; cols=['any_match','top1','top3']
fig,ax=plt.subplots(figsize=(6.5,3.5)); x=np.arange(3)
for shift,(_,row),label,color in [(-.19,next(b[b.mapping=='JULY_BASELINE_92'].iterrows()),'July M0','#596e87'),(.19,next(b[b.mapping=='JULY_UTILITY_CONSTRAINED_92'].iterrows()),'Utility M1','#c56048')]:
    ax.bar(x+shift,[100*row[c] for c in cols],width=.36,label=label,color=color)
ax.set_xticks(x,labels);ax.set_ylim(80,101);ax.set_ylabel('Conditional agreement (%)');ax.legend()
png,pdf=save('S3_SCE_candidate_consistency_337')
add('S3a','S3 Mapping methodology and robustness','SCE public-candidate consistency on 337 comparable tracts','NEW_NEEDED',
    bpath,'Supplement_Rebuild_20260925/Tables/S3_SCE_337_CANDIDATE_BENCHMARK.csv',png,pdf,
    caption='Agreement with public SCE circuit/substation candidate evidence, conditional on 337 strict-SCE tracts whose direct official candidate is representable among the July 92 stations. The other 480 strict-SCE tracts are a coverage limitation. Candidate evidence is not customer-feeder ground truth.')

mpath='Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_MAPPING_EFFECTS.csv'
mapping=pd.read_csv(ROOT/mpath)
mm=mapping[(mapping.comparison=='full92')&(mapping.strategy_id=='hospital-first')&(mapping.metric.isin(['population_T80_hr','population_weighted_normalized_burden_hr','hospital_mean_normalized_burden_hr']))].copy()
mm.to_csv(TAB/'S3_M1_MINUS_M0_HOSPITAL_FIRST.csv',index=False)
fig,axes=plt.subplots(1,3,figsize=(10,3.4))
for ax,(metric,group) in zip(axes,mm.groupby('metric',sort=False)):
    group=group.set_index('hazard').reindex(hazards)
    ax.bar(range(4),group.mean_delta,color='#567f9a');ax.axhline(0,color='black',lw=.8)
    ax.set_xticks(range(4),['NR','SF','LB','2pc50']);ax.set_title(metric.replace('_',' ').replace('population weighted normalized','Pop.').replace('hospital mean normalized','Hospital '),fontsize=8)
    ax.set_ylabel('M1 − M0 (hours)')
png,pdf=save('S3_mapping_outcome_shift')
add('S3b','S3 Mapping methodology and robustness','Paired M1 minus M0 outcomes by hazard','NEW_NEEDED',mpath,
    'Supplement_Rebuild_20260925/Tables/S3_M1_MINUS_M0_HOSPITAL_FIRST.csv',png,pdf,
    caption='Mean within-realization difference under Hospital-first, holding frozen station states and schedules fixed. Bars compare production utility-compatible M1 with submitted July M0; positive means a larger modeled metric under M1.')

cut=mapping[mapping.comparison.str.contains('cutoff|SCE_common320',regex=True)].copy()
cut.to_csv(TAB/'S3_CUTOFF_AND_COMMON320.csv',index=False)
add('Table S3c','S3 Mapping methodology and robustness','Cutoff and SCE common-support contrasts','ALREADY_READY',mpath,
    'Supplement_Rebuild_20260925/Tables/S3_CUTOFF_AND_COMMON320.csv',
    notes='Formal output has cutoff/no-cutoff and common-positive-mass SCE subset; not a complete 337-tract outcome domain.')

# S4 gate components, dynamic redundancy and equivalence table.
gpath='Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_GATE_COMPONENTS.csv'
gate=pd.read_csv(ROOT/gpath)
gg=gate[(gate.resource_scenario=='C57_D1')&(gate.strategy_id=='hospital-first')].set_index('hazard').loc[hazards].reset_index()
gg.to_csv(TAB/'S4_GATE_COMPONENTS_HOSPITAL_FIRST.csv',index=False)
fig,ax=plt.subplots(figsize=(7,3.5));bottom=np.zeros(4)
for col,label,color in [('self_mean_hr','Self','#527c9b'),('threshold_mean_hr','Threshold','#d8a55b'),('source_mean_hr','Source path','#a5545a')]:
    vals=gg[col].to_numpy();ax.bar(np.arange(4),vals,bottom=bottom,label=label,color=color);bottom+=vals
ax.set_xticks(range(4),hazards);ax.set_ylabel('Mean cumulative service-loss contribution (h)');ax.legend()
png,pdf=save('S4_source_gate_loss_decomposition')
add('S4a','S4 Source-gate diagnostics','Self, threshold, and source-path loss by hazard','NEW_NEEDED',gpath,
    'Supplement_Rebuild_20260925/Tables/S4_GATE_COMPONENTS_HOSPITAL_FIRST.csv',png,pdf,
    caption='Hospital-first, C57, M1, G1 means over 1,000 paired physical realizations per hazard. Components sum to the modeled cumulative service-loss proxy; they are not MW or observed outage hours.')

tpath='Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv'
top=pd.read_csv(ROOT/tpath)
tt=top[(top.resource_scenario=='C57_D1')&(top.strategy_id=='hospital-first')].set_index('hazard').loc[hazards].reset_index()
tt.to_csv(TAB/'S4_DYNAMIC_TOPOLOGY_HOSPITAL_FIRST.csv',index=False)
fig,ax=plt.subplots(figsize=(7,3.5))
for col,label,color in [('top1_fraction__mean','Top 1','#c66a56'),('top5_fraction__mean','Top 5','#8e6a9e'),('static_eight_fraction__mean','Static eight','#527c9b')]:
    ax.plot(hazards,tt[col],marker='o',label=label,color=color)
ax.set_ylabel('Fraction of source-path loss');ax.set_ylim(0,1);ax.legend()
png,pdf=save('S4_dynamic_source_loss_concentration')
add('S4b','S4 Source-gate diagnostics','Dynamic source-path loss concentration','NEW_NEEDED',tpath,
    'Supplement_Rebuild_20260925/Tables/S4_DYNAMIC_TOPOLOGY_HOSPITAL_FIRST.csv',png,pdf,
    caption='Concentration of modeled source-path loss for Hospital-first under C57. The companion table preserves reachable-source, disjoint-path, cut, bridge, articulation, and single-path summaries. These are topological diagnostics, not power-flow or capacity validation.')
equiv=EQUITY/'NO_THRESHOLD_CONNECTIVITY_EQUIVALENCE.json'
shutil.copy2(equiv,TAB/'S4_NO_THRESHOLD_CONNECTIVITY_EQUIVALENCE.json')
add('Table S4c','S4 Source-gate diagnostics','Positive-connectivity equivalence to ungated G0','ALREADY_READY',
    'Formal_Experiment_20260923/Equity_Amendment/NO_THRESHOLD_CONNECTIVITY_EQUIVALENCE.json',
    'Supplement_Rebuild_20260925/Tables/S4_NO_THRESHOLD_CONNECTIVITY_EQUIVALENCE.json',
    notes='Interpretation only; does not change production G1.')

# S5 GA reproducibility from frozen five-seed histories.
ga_dir=FORMAL/'Stage 5 Output_expanded'
ga=pd.read_csv(ga_dir/'GA_FIVE_SEED_CONVERGENCE.csv')
ga.to_csv(TAB/'S5_GA_FIVE_SEED_SUMMARY.csv',index=False)
fig,ax=plt.subplots(figsize=(7,3.5))
for seed in [42,43,44,45,46]:
    hist=pd.read_csv(ga_dir/f'GA_HISTORY_2pc50_{seed}.csv')
    col=next((c for c in ['best_so_far','best_so_far_fitness','retained_best_fitness','best_fitness'] if c in hist),None)
    if col is None: raise ValueError(f'No best-so-far field in seed {seed}: {list(hist)}')
    ax.plot(np.arange(len(hist)),hist[col],label=f'Seed {seed}',alpha=.8)
ax.axhline(float(ga.incumbent_fitness.iloc[0]),color='black',ls='--',lw=1,label='Impact-first incumbent')
ax.set_xlabel('Generation');ax.set_ylabel('Retained fitness');ax.legend(ncol=3,fontsize=7)
png,pdf=save('S5_GA_five_seed_convergence')
add('S5','S5 GA reproducibility','Five-seed direct-objective search and incumbent','NEW_NEEDED',
    'Formal_Experiment_20260923/Stage 5 Output_expanded/GA_HISTORY_2pc50_42–46.csv',
    'Supplement_Rebuild_20260925/Tables/S5_GA_FIVE_SEED_SUMMARY.csv',png,pdf,
    caption='Retained direct-community fitness by generation on 64 independent 2pc50 planning realizations. All five seeds retained the impact-first deterministic incumbent; direct-community is the same 92-station sequence, not a new GA improvement.')

# S6 full formal summary table and resource effects.
primary=pd.read_parquet(FORMAL/'Formal_Results'/'PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet')
base=primary[(primary.resource_scenario=='C57_D1')&(primary.mapping=='M1_UTILITY_003')&(primary.gate=='G1_BASELINE_050')&(primary.comparison_domain=='mapping_native_domain')]
assert len(base)==36000, len(base)
metrics=['population_weighted_normalized_burden_hr','population_resolved_mass_weighted_burden_hr','population_T50_hr','population_T80_hr','hospital_mean_normalized_burden_hr','burden_Q1_hr','burden_Q2_hr','burden_Q3_hr','burden_Q4_hr','signed_Q4_minus_Q1_hr','absolute_Q4_minus_Q1_hr','burden_gini','L_source_population_mass_weighted_hr','L_source_fraction','makespan_hr','total_travel_hr']
summary=base.groupby(['hazard','strategy_id'],sort=False)[metrics].agg(['mean','median','std']).reset_index()
summary.columns=['_'.join(str(x) for x in c if x) for c in summary.columns]
summary.to_csv(TAB/'S6_ALL_HAZARD_STRATEGY_BASELINE.csv',index=False)
add('Table S6a','S6 Full strategy and resource results','Four-hazard full-strategy C57 formal summary','NEW_NEEDED',
    'Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet',
    'Supplement_Rebuild_20260925/Tables/S6_ALL_HAZARD_STRATEGY_BASELINE.csv',
    notes='36,000 frozen baseline trajectories; 1,000 realizations per hazard × 9 baseline trajectories.')
respath='Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_RESOURCE_EFFECTS.csv'
shutil.copy2(ROOT/respath,TAB/'S6_RESOURCE_EFFECTS.csv')
add('Table S6b','S6 Full strategy and resource results','One-factor resource effects','ALREADY_READY',respath,
    'Supplement_Rebuild_20260925/Tables/S6_RESOURCE_EFFECTS.csv')

# S7 retains both absolute quartile and tract-effect source tables.
for code,name,title in [('A','EQUITY_EFFICIENCY','Equity–efficiency tradeoff'),('B','QUARTILE_ABSOLUTE_BURDEN','Q1–Q4 absolute burden'),('C','TRACT_EFFECT_MAP','Vulnerability-first tract effects'),('D','RESOURCE_EQUITY_SENSITIVITY','Resource sensitivity of equity tradeoff')]:
    src=EQUITY/'Figures'
    basename=f'FIGURE_{code}_{name}'
    for ext in ['png','pdf']:
        shutil.copy2(src/f'{basename}.{ext}',FIG/f'S7_{basename}.{ext}')
    shutil.copy2(src/f'FIGURE_{code}_SOURCE.csv',TAB/f'S7_{basename}_SOURCE.csv')
    png=f'Supplement_Rebuild_20260925/Figures/S7_{basename}.png'
    pdf=f'Supplement_Rebuild_20260925/Figures/S7_{basename}.pdf'
    add(f'S7{code.lower()}','S7 Distributional and vulnerability-first',title,'ALREADY_READY',
        f'Formal_Experiment_20260923/Equity_Amendment/Figures/{basename}.pdf',
        f'Supplement_Rebuild_20260925/Tables/S7_{basename}_SOURCE.csv',png,pdf,
        caption='Frozen 1,000-realization formal evaluation, reproduced without rerunning scheduling or recovery. Vulnerability-first is a deterministic equity-informed comparator, not an equity-optimal policy. See source CSV for plotted values.')
for srcname in ['VULNERABILITY_GROUP_SUMMARY.csv','VULNERABILITY_PAIRWISE_EFFECTS.csv','VULNERABILITY_CLASSIFICATION_POPULATION.csv','VULNERABILITY_RESOURCE_EFFECTS.csv']:
    shutil.copy2(EQUITY/srcname,TAB/f'S7_{srcname}')
add('Table S7e','S7 Distributional and vulnerability-first','Group, paired, classification, and resource effects','ALREADY_READY',
    'Formal_Experiment_20260923/Equity_Amendment/',
    'Supplement_Rebuild_20260925/Tables/S7_VULNERABILITY_GROUP_SUMMARY.csv',
    notes='Other three companion S7_VULNERABILITY_* CSVs are in the same Tables directory.')

# S8 Stage 7 PCA and cluster diagnostics; no re-clustering.
s7=FORMAL/'Stage 7 Output_expanded'
pca=pd.read_csv(s7/'pca_stats_with_eigenvalues.csv');pca.to_csv(TAB/'S8_PCA_STATS.csv',index=False)
fig,ax=plt.subplots(figsize=(6,3.5));ax.bar(pca.PC,pca.Explained_Variance_Ratio,color='#587f9c');ax.plot(pca.PC,pca.Cumulative_Ratio,color='#b45a4f',marker='o');ax.set_ylabel('Explained / cumulative variance');ax.tick_params(axis='x',rotation=45)
png,pdf=save('S8_PCA_scree')
add('S8a','S8 Typology and hotspot diagnostics','Formal Stage 7 PCA scree','KEEP_UPDATE',
    'Formal_Experiment_20260923/Stage 7 Output_expanded/pca_stats_with_eigenvalues.csv',
    'Supplement_Rebuild_20260925/Tables/S8_PCA_STATS.csv',png,pdf,
    caption='PCA diagnostic for the frozen formal Stage 7 feature matrix. The plotted ratios are from the formal output and do not rerun PCA or clustering.')
k=pd.read_csv(s7/'kmeans_k_diagnostics.csv');k.to_csv(TAB/'S8_KMEANS_K_DIAGNOSTICS.csv',index=False)
fig,ax=plt.subplots(figsize=(6,3.5));ax.plot(k.k,k.inertia,marker='o',color='#587f9c');ax.set_xlabel('Number of clusters k');ax.set_ylabel('Within-cluster inertia')
png,pdf=save('S8_Kmeans_elbow')
add('S8b','S8 Typology and hotspot diagnostics','Formal Stage 7 K-means elbow','KEEP_UPDATE',
    'Formal_Experiment_20260923/Stage 7 Output_expanded/kmeans_k_diagnostics.csv',
    'Supplement_Rebuild_20260925/Tables/S8_KMEANS_K_DIAGNOSTICS.csv',png,pdf,
    caption='Inertia across pre-evaluated k values in the formal Stage 7 analysis. Clusters are descriptive community typology, not causal classes.')
load=pd.read_csv(s7/'pca_loadings.csv').rename(columns={'Unnamed: 0':'feature'});load.to_csv(TAB/'S8_PCA_LOADINGS.csv',index=False)
fig,ax=plt.subplots(figsize=(6.5,max(3.5,.34*len(load))));im=ax.imshow(load.drop(columns='feature').to_numpy(),cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto');ax.set_yticks(np.arange(len(load)),load.feature);ax.set_xticks(np.arange(5),load.columns[1:]);fig.colorbar(im,ax=ax,label='Loading')
png,pdf=save('S8_PCA_loadings')
add('S8c','S8 Typology and hotspot diagnostics','Formal Stage 7 PCA loading structure','KEEP_UPDATE',
    'Formal_Experiment_20260923/Stage 7 Output_expanded/pca_loadings.csv',
    'Supplement_Rebuild_20260925/Tables/S8_PCA_LOADINGS.csv',png,pdf,
    caption='Formal PCA loadings by feature and component; sign denotes direction in the standardized descriptive feature space.')
for name in ['stage7_cluster_profiles_raw_values.csv','stage7_top10_slow_vulnerable_tracts.csv','stage7_raw_vs_log_robustness_summary.csv']:
    shutil.copy2(s7/name,TAB/('S8_'+name))
add('Table S8d','S8 Typology and hotspot diagnostics','Cluster profiles and hotspot screening','ALREADY_READY',
    'Formal_Experiment_20260923/Stage 7 Output_expanded/',
    'Supplement_Rebuild_20260925/Tables/S8_stage7_cluster_profiles_raw_values.csv',
    notes='Hotspot and raw-vs-log summaries copied as separate S8 tables; descriptive screening only.')

# Existing directed July92 road matrix and frozen Stage 7 spatial join.
travel_path='Stage 4 Output_expanded/travel_task_to_task.csv'
travel=pd.read_csv(ROOT/travel_path,index_col=0)
assert travel.shape==(92,92) and np.isfinite(travel.to_numpy()).all()
fig,ax=plt.subplots(figsize=(5.6,4.8));im=ax.imshow(travel.to_numpy(),cmap='viridis',aspect='auto')
ax.set_xlabel('Next restoration task');ax.set_ylabel('Previous restoration task')
fig.colorbar(im,ax=ax,label='Directed road travel (h)')
png,pdf=save('S2_directed_task_travel_matrix')
add('S2a','S2 Restoration setup','Directed task-to-task road travel','KEEP_UPDATE',travel_path,
    travel_path,png,pdf,
    caption='The frozen 92 × 92 directed road-travel matrix used by the event scheduler. Matrix entries need not be symmetric; this plot does not assert actual post-earthquake road conditions.')

cutplot=mapping[(mapping.strategy_id=='hospital-first')&(mapping.hazard=='2pc50')&(mapping.metric=='population_weighted_normalized_burden_hr')&mapping.comparison.str.contains('cutoff')].copy()
cutplot.to_csv(TAB/'S3_CUTOFF_HOSPITAL_FIRST_2PC50.csv',index=False)
fig,ax=plt.subplots(figsize=(7,3.2))
ax.bar(np.arange(len(cutplot)),cutplot.mean_delta,color=['#5b809e','#84aab7','#be745f','#dfaa6a'][:len(cutplot)])
ax.axhline(0,color='black',lw=.8);ax.set_xticks(np.arange(len(cutplot)),cutplot.comparison.str.replace('2pc50_cutoff_','',regex=False),rotation=20)
ax.set_ylabel('Mean change in burden (h)')
png,pdf=save('S3_cutoff_robustness_2pc50')
add('S3d','S3 Mapping methodology and robustness','Cutoff robustness in 2pc50','NEW_NEEDED',mpath,
    'Supplement_Rebuild_20260925/Tables/S3_CUTOFF_HOSPITAL_FIRST_2PC50.csv',png,pdf,
    caption='Hospital-first mean paired burden change under 1% or no cutoff, relative to each mapping’s 3% cutoff, using unchanged frozen 2pc50 physical and station-state trajectories. Cutoff sensitivity is not external feeder validation.')

import geopandas as gpd
tracts=gpd.read_file(ROOT/'Data/LA_Tracts_With_Population.shp')[['GEOID','geometry']]
tracts['tract_id']=tracts.GEOID.astype(str).str.zfill(11)
labels=pd.read_csv(s7/'clusters_labels_final.csv',dtype={'tract_id':str})
labels['tract_id']=labels.tract_id.str.zfill(11)
spatial=tracts.merge(labels[['tract_id','cluster','SlowVulnerable_Hotspot_Top10']],on='tract_id',how='left',validate='one_to_one')
assert spatial.cluster.notna().sum()>2200
fig,ax=plt.subplots(figsize=(7,6));spatial.plot(column='cluster',ax=ax,cmap='tab10',legend=True,linewidth=0,missing_kwds={'color':'#eeeeee'});ax.axis('off')
png,pdf=save('S8_formal_cluster_map')
add('S8e','S8 Typology and hotspot diagnostics','Formal descriptive community clusters','NEW_NEEDED',
    'Formal_Experiment_20260923/Stage 7 Output_expanded/clusters_labels_final.csv',
    'Formal_Experiment_20260923/Stage 7 Output_expanded/clusters_labels_final.csv',png,pdf,
    caption='Formal Stage 7 cluster labels joined by 11-digit tract GEOID to retained tract geometry. Clusters describe joint features and do not establish causal community types.')
fig,ax=plt.subplots(figsize=(7,6));spatial.plot(ax=ax,color='#dddddd',linewidth=0)
spatial[spatial.SlowVulnerable_Hotspot_Top10.fillna(False).astype(bool)].plot(ax=ax,color='#bd553e',linewidth=0)
ax.axis('off')
png,pdf=save('S8_formal_hotspot_screen_map')
add('S8f','S8 Typology and hotspot diagnostics','Slow-vulnerable hotspot screening','NEW_NEEDED',
    'Formal_Experiment_20260923/Stage 7 Output_expanded/clusters_labels_final.csv',
    'Supplement_Rebuild_20260925/Tables/S8_stage7_top10_slow_vulnerable_tracts.csv',png,pdf,
    caption='Descriptive Stage 7 top-decile slow/vulnerable screening tracts in red; this is not a causal or observed-outage hotspot map.')

# Deliberately register unmet lower-priority material instead of creating unsupported figures.
frozen='Formal_Experiment_20260923/Formal_Trajectories/*/C57_D1/unconstrained/*.npz'
source='Supplement_Rebuild_20260925/Tables/S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv'
for sid,section,title,name,caption in [
    ('S1b','S1 Damage and initial conditions','Initial tract service CDF across four hazards','S1_initial_service_CDF',
     'Empirical CDF across 2,315 tracts of mean initial modeled service availability, projected from each hazard’s 1,000 frozen unconstrained event archives using frozen M1. This is a service proxy, not delivered electricity.'),
    ('S1c','S1 Damage and initial conditions','Initial tract service maps','S1_initial_service_maps',
     'Spatial mean initial modeled service availability across 1,000 frozen realizations per hazard. All panels use the same 0–1 color scale; no event simulation was rerun.'),
    ('S2b','S2 Restoration setup','Historical unconstrained tract T80 maps','S2_historical_unconstrained_T80_maps',
     'Per-tract mean time to 80% modeled service availability among realizations that reached it under frozen unconstrained event trajectories. Unreached cases remain NA in the source table; these maps do not imply observed restoration times.')]:
    png=f'Supplement_Rebuild_20260925/Figures/{name}.png';pdf=f'Supplement_Rebuild_20260925/Figures/{name}.pdf'
    assert (ROOT/png).exists() and (ROOT/pdf).exists() and (ROOT/source).exists()
    add(sid,section,title,'NEW_NEEDED',frozen,source,png,pdf,caption=caption)
    inventory[-1]['figure_script_path']='Supplement_Rebuild_20260925/plot_initial_and_historical.py'

for item in inventory:
    if item['status']=='NEW_NEEDED' and item['output_png'] and item['output_pdf']:
        if (ROOT/item['output_png']).exists() and (ROOT/item['output_pdf']).exists():
            item['status']='ALREADY_READY'
            item['notes']=(item['notes']+'; ' if item['notes'] else '')+'New in reviewer revision; generated from frozen results.'
    elif item['status']=='NEW_NEEDED' and item['source_csv_or_table'] and (ROOT/item['source_csv_or_table']).exists():
        item['status']='ALREADY_READY'
        item['notes']=(item['notes']+'; ' if item['notes'] else '')+'New formal summary table generated from frozen results.'
with (ROOT/'SUPPLEMENT_FIGURE_INVENTORY.csv').open('w',newline='',encoding='utf-8-sig') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(inventory[0]));writer.writeheader();writer.writerows(inventory)
(OUT/'SUPPLEMENT_CAPTIONS_DRAFT.md').write_text('# Supplement caption drafts\n\n'+'\n\n'.join(captions)+'\n',encoding='utf-8')
print('inventory_items',len(inventory),'figures_png_pdf',sum(bool(x['output_pdf']) for x in inventory),'table_files',len(list(TAB.iterdir())))
