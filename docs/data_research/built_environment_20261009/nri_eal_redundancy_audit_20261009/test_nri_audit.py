"""Independent numerical and preservation checks for the isolated FEMA audit."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np,pandas as pd
from scipy.stats import pearsonr,spearmanr
from sklearn.metrics import adjusted_rand_score,silhouette_score
from sklearn.preprocessing import StandardScaler
O=Path(__file__).resolve().parent;R=O.parents[3]
def table(name):return pd.read_csv(O/name,dtype={'tract_id':str})
def j(name):return json.loads((O/name).read_text(encoding='utf-8'))
def paired(c,a,b):return c[((c.field_a==a)&(c.field_b==b))|((c.field_a==b)&(c.field_b==a))].iloc[0]
def test_exact_membership_and_frozen_common_fields():
 d=table('MATCHED_FEMA_STAGE7_FEATURES.csv').set_index('tract_id');old=pd.read_csv(R/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv',dtype={'tract_id':str});old.tract_id=old.tract_id.str.zfill(11);old=old.set_index('tract_id')
 assert len(d)==2291 and d.index.is_unique and (d.index.str.len()==11).all() and d.index.equals(old.index)
 for c in ['T80','Init_Supply','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','Pre_1970_Ratio','Pop_Density','SOVI_SCORE','NRI_BUILDVALUE','NRI_RISK_SCORE']:assert np.allclose(d[c],old[c],atol=1e-12,rtol=1e-14)

def test_exact_release_and_document_identity():
 source=pd.read_csv(R/'Data/NRI_Table_CensusTracts_California.csv',low_memory=False);assert source.NRI_VER.eq('Mar-23').all()
 text=j('sources/FEMA_V119_PAGE_TEXT.json');assert 'March 2023' in text['1'] and '1.19.0' in text['32']
 entry=[x for x in j('DOCUMENT_ACQUISITION.json') if x['file']=='FEMA_V119_TECHNICAL_DOCUMENTATION.pdf'][0]
 assert hashlib.sha256((O/'sources'/entry['file']).read_bytes()).hexdigest()==entry['sha256']

def test_population_dollar_and_loss_composition():
 d=table('EAL_BUILDING_POPULATION_AGRICULTURE_COMPONENTS.csv');assert np.allclose(d.EAL_VALT,d.EAL_VALB+d.EAL_VALPE+d.EAL_VALA,rtol=1e-13,atol=1e-6)
 assert np.allclose(d.EAL_VALPE,11600000*d.EAL_VALP,rtol=1e-13,atol=1e-6)
 assert np.allclose(d.building_loss_share+d.population_equivalent_loss_share+d.agriculture_loss_share,1,atol=1e-13)
 hazards=[c for c in d if c.endswith('_EALT')];assert len(hazards)==18 and d.AVLN_EALT.isna().all()
 assert np.allclose(d[hazards].sum(axis=1,min_count=1),d.EAL_VALT,rtol=1e-13,atol=1e-6)
 assert np.allclose(d.ALR_VALB,d.EAL_VALB/d.BUILDVALUE,atol=1e-14)
 assert np.allclose(d.ALR_VALP,d.EAL_VALP/d.POPULATION,atol=1e-14)

def test_reported_correlations_and_constant_resilience():
 d=table('MATCHED_FEMA_STAGE7_FEATURES.csv').set_index('tract_id');c=table('NRI_EAL_SOVI_BUILDVALUE_CORRELATIONS.csv')
 for a,b in [('SOVI_SCORE','EAL_SCORE'),('SOVI_SCORE','EAL_VALT'),('SOVI_SCORE','NRI_BUILDVALUE'),('EAL_SCORE','NRI_BUILDVALUE'),('EAL_VALT','NRI_BUILDVALUE'),('EAL_SCORE','NRI_RISK_SCORE'),('EAL_SCORE','Pop_Density'),('EAL_SCORE','Pre_1970_Ratio'),('EAL_SCORE','building_footprint_coverage'),('EAL_VALB','EAL_VALPE')]:
  sub=d[[a,b]].dropna();row=paired(c,a,b);assert len(sub)==row.n and row.missing_from_2291==2291-len(sub)
  assert abs(row.pearson_r-pearsonr(sub[a],sub[b]).statistic)<1e-12 and abs(row.spearman_rho-spearmanr(sub[a],sub[b]).statistic)<1e-12
  assert row.matched_tract_sha256==hashlib.sha256('\n'.join(sorted(sub.index)).encode()).hexdigest()
 row=paired(c,'EAL_SCORE','RESL_SCORE');assert np.isnan(row.pearson_r) and np.isnan(row.spearman_rho) and row.status.startswith('UNDEFINED') and d.RESL_SCORE.nunique()==1

def test_vif_with_independent_inverse_correlation_formula():
 d=table('MATCHED_FEMA_STAGE7_FEATURES.csv');v=table('PARTIAL_CORRELATIONS_AND_VIF.csv');sets={'A':['SOVI_SCORE','NRI_BUILDVALUE','NRI_RISK_SCORE'],'B':['SOVI_SCORE','EAL_SCORE'],'C':['SOVI_SCORE','NRI_BUILDVALUE','EAL_SCORE'],'D':['SOVI_SCORE','NRI_BUILDVALUE','ALR_NPCTL']}
 for name,cols in sets.items():
  f=d[cols].copy()
  if 'NRI_BUILDVALUE' in f:f.NRI_BUILDVALUE=np.log1p(f.NRI_BUILDVALUE)
  corr=f.corr().to_numpy();expected=np.diag(np.linalg.inv(corr));rows=v[(v.analysis=='VIF')&(v.feature_set==name)&(v.scope=='nri_coordinates')&(v['transform']=='log_exposures')].set_index('feature_a').reindex(cols)
  assert np.allclose(rows.value,expected,atol=1e-10)
  eigen=np.linalg.eigvalsh(corr);assert np.allclose(rows.condition_number_standardized,np.sqrt(eigen[-1]/eigen[0]),atol=1e-10)

def test_fixed_domain_budgets_and_constant_membership():
 w=table('CLUSTER_DOMAIN_WEIGHTS.csv');g=w.groupby(['feature_set','transform','budget','domain']);assert np.allclose(g.coordinate_squared_weight.sum(),g.domain_weight.first(),atol=1e-14)
 assert np.allclose(g.observed_coordinate_variance.sum(),g.domain_weight.first(),atol=1e-14)
 s=table('CONTROLLED_CLUSTERING_SENSITIVITY.csv');assert len(s)==195 and s.n.eq(2291).all() and set(s.seed)=={42,43,44,45,46}
 assert not s.duplicated(['feature_set','transform','budget','seed','k']).any()
 assert j('CLUSTER_RUN_SPECIFICATION.json')['mandatory_social']=='SOVI_SCORE'

def test_cluster_replay_and_independent_silhouette():
 d=table('MATCHED_FEMA_STAGE7_FEATURES.csv');labels=table('EXPLORATORY_CLUSTER_LABELS.csv');assert labels.tract_id.equals(d.tract_id)
 assert adjusted_rand_score(d.cluster,labels['A__log_exposures__original_domain_totals__k5__s42'])==1
 row=table('CONTROLLED_CLUSTERING_SENSITIVITY.csv');row=row[(row.feature_set=='B')&(row['transform']=='log_exposures')&(row.budget=='original_domain_totals')&(row.seed==43)&(row.k==5)].iloc[0]
 cols=['T80','Init_Supply','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','Pre_1970_Ratio','Pop_Density','SOVI_SCORE','EAL_SCORE'];x=d[cols].copy();x.Pop_Density=np.log1p(x.Pop_Density);z=StandardScaler().fit_transform(x);weights=np.array([1/11]*9+[2/11]);z*=np.sqrt(weights);lab=labels['B__log_exposures__original_domain_totals__k5__s43']
 assert abs(row.silhouette-silhouette_score(z,lab))<1e-12
 assert row.minimum_cluster_size==lab.value_counts().min()

def test_preservation_of_scientific_files_and_original_index():
 q=j('PRESERVATION_FINAL_QA.json');assert q['scientific_files_changed']==0 and q['protected_files_checked']==950 and q['formal_input_files_checked']==2008
 assert not q['protected_hash_changes'] and not q['formal_input_hash_changes'] and not q['used_source_hash_changes']
 assert q['original_index_unchanged'] and q['original_staged_count']==862
 actual=subprocess.check_output(['git','-C',str(R),'ls-files','--stage','-z']);assert actual==(O/'ORIGINAL_STAGING.bin').read_bytes()
