"""Numerical checks, preservation proof and evidence-bounded decision packet."""
from pathlib import Path
import sys,json,itertools,subprocess,time,hashlib,shutil
import pandas as pd,numpy as np
from scipy.stats import pearsonr,spearmanr
from validate_stage7 import ROOT,OUT,OLD,BASE,PARENT,SCIENCE,read,save,dump,sha,git
def additional_qa():
 f=read('FINAL_CANDIDATE_FEATURE_MATRIX.csv',OUT);d=f.loc[f.primary_complete_case];cols=json.loads((OUT/'FEATURE_MATRIX_QA.json').read_text())['required'];corr=[]
 for a,b in itertools.combinations(list(dict.fromkeys(cols+['T80','Init_Supply','residential_pre1970_housing_share','log1p_Pop_Density'])),2):
  if a==b:continue
  v=d[[a,b]].dropna();corr.append({'a':a,'b':b,'n':len(v),'pearson_r':pearsonr(v[a],v[b]).statistic,'spearman_rho':spearmanr(v[a],v[b]).statistic,'sample':'resolved complete-case cohort; not previous2291 correlation audit'})
 save('CANDIDATE_MATCHED_CORRELATIONS.csv',pd.DataFrame(corr));vifs=[]
 for name,fields in [('D',cols),('EAL',[c for c in cols if c not in ['log1p_NRI_BUILDVALUE','ALR_NPCTL']]+['EAL_SCORE'])]:
  x=d[fields].to_numpy();z=(x-x.mean(axis=0))/x.std(axis=0);condition=np.linalg.cond(z)
  for i,c in enumerate(fields):
   y=z[:,i];a=np.c_[np.ones(len(y)),np.delete(z,i,axis=1)];res=y-a@np.linalg.lstsq(a,y,rcond=None)[0];r2=1-(res@res)/(y@y);vifs.append({'model':name,'feature':c,'n':len(d),'vif':1/(1-r2),'conditional_R2':r2,'condition_number':condition,'interpretation':'simultaneous-coordinate linear redundancy; not feature value or causal evidence'})
 save('CANDIDATE_VIF.csv',pd.DataFrame(vifs))
 q=read('LANDMASK_18_TRACT_RESOLUTION.csv',OUT);q['individual_evidence']=q.apply(lambda r:f"Original mask {r.before_land_area_m2:.3f} m2; archived ALAND {r.census_ALAND_m2:.0f}; 2020 ALAND {r.census2020_ALAND_m2:.0f}; hydrography {r.hydro_names}; boundary symmetric difference {r['2020_boundary_symmetric_difference_m2']:.3f} m2; projected/geodesic relative difference {r.projection_relative_error:.9g}",axis=1)
 save('LANDMASK_18_TRACT_RESOLUTION.csv',q,index=True)
 # Prior by-use geometries use the old mask; recompute the corrected four uses explicitly.
 import geopandas as gpd,pyogrio,shapely
 t=gpd.read_file(ROOT/'Data/LA_Tracts_With_Population.shp');t['tract_id']=t.GEOID.astype(str);t=t.set_index('tract_id').to_crs(3310);w=gpd.read_file('zip://'+str(OLD/'sources/tl_2020_06037_areawater.zip')).to_crs(3310);u='/vsizip/'+str(OLD/'sources/LARIAC4_BUILDINGS_2014.zip').replace('\\','/')+'/LARIAC4_BUILDINGS_2014/LARIAC4_BUILDINGS_2014.gdb';info=pyogrio.read_info(u,layer='LARIAC4_BUILDINGS_2014');ur=[]
 for key in q.index[q.status.str.startswith('CORRECTED')]:
  geo=t.loc[key].geometry;land=geo if t.loc[key,'AWATER']==0 else geo.difference(shapely.union_all(w.loc[w.AWATER.gt(0)&w.intersects(geo)].geometry.to_numpy()));box=gpd.GeoSeries([geo],crs=3310).to_crs(info['crs']).total_bounds
  a=pyogrio.read_dataframe(u,layer='LARIAC4_BUILDINGS_2014',bbox=tuple(box),columns=['CODE','UseType','YearBuilt1','Roll_Year']);a=a.loc[a.CODE.eq('Building')&a.geometry.notna()].copy();a.geometry=a.geometry.make_valid();a['_hash']=[hashlib.sha256(x).hexdigest() for x in shapely.to_wkb(shapely.normalize(a.geometry.to_numpy()))];y=pd.to_numeric(a.YearBuilt1,errors='coerce');roll=pd.to_numeric(a.Roll_Year,errors='coerce');a['_valid']=y.between(1800,2014)&y.mod(1).eq(0)&(roll.isna()|y.le(roll));a['_year']=y.where(a._valid);a['_attrs']=list(zip(a._year.fillna(-1),a.UseType.fillna('None')));conf=a.groupby('_hash')._attrs.nunique();a.loc[a._hash.isin(conf[conf>1].index),'_valid']=False;a=a.drop_duplicates('_hash').to_crs(3310)
  for use,g in a.groupby('UseType',dropna=False):
   clips=shapely.intersection(g.geometry.to_numpy(),land);ar=shapely.union_all(clips).area;va=shapely.union_all(clips[g._valid]).area;pa=shapely.union_all(clips[g._valid & g._year.lt(1970)]).area
   ur.append({'tract_id':key,'use':use,'outline_union_area_m2':ar,'valid_age_union_area_m2':va,'pre1970_union_area_m2':pa,'valid_age_area_coverage':va/ar if ar>0 else np.nan,'scope':'CORRECTED_2014_MASK_BY_USE_DIAGNOSTIC'})
 old=pd.read_csv(OLD/'BUILDING_AGE_2014_BY_USE_COVERAGE.csv',dtype={'tract_id':str});old=old.loc[~old.tract_id.isin(q.index[q.status.str.startswith('CORRECTED')])].copy();old['scope']='ORIGINAL_UNCHANGED_2014_MASK_BY_USE_DIAGNOSTIC';uses=pd.concat([old,pd.DataFrame(ur)],ignore_index=True);save('BUILDING_AGE_USE_MISSINGNESS.csv',uses)
 pooled=[]
 for use,g in uses.loc[uses.tract_id.isin(f.index)].groupby('use',dropna=False):
  pooled.append({'use':use,'tracts':g.tract_id.nunique(),'pooled_outline_area_m2':g.outline_union_area_m2.sum(),'pooled_valid_age_area_m2':g.valid_age_union_area_m2.sum(),'pooled_missing_area_fraction':1-g.valid_age_union_area_m2.sum()/g.outline_union_area_m2.sum(),'note':'within-use unions; cross-use areas may overlap, do not sum across uses as overall area'})
 save('BUILDING_AGE_POOLED_USE_MISSINGNESS.csv',pd.DataFrame(pooled));print('ADDITIONAL_QA_COMPLETE',flush=True)
def spatial_complete():
 """Same twenty block perturbations for both constructs and both domain budgets."""
 import geopandas as gpd
 from sklearn.cluster import KMeans
 from sklearn.metrics import adjusted_rand_score
 from threadpoolctl import threadpool_limits
 from controlled_clustering import variants,design,SEEDS
 f=read('FINAL_CANDIDATE_FEATURE_MATRIX.csv',OUT);d=f.loc[f.primary_complete_case];b=pd.read_csv(OUT/'TRACT_SPATIAL_BLOCKS.csv',dtype={'tract_id':str}).set_index('tract_id').loc[d.index];blocks=b.block;unique=sorted(blocks.unique());rows=[]
 # Reuse the exact previous block selections rather than sampling a different study.
 former=pd.read_csv(OUT/'SPATIAL_BLOCK_STABILITY.csv');original=former.loc[former.model.eq('D__inherited')] if 'model' in former else former
 selected=[s for s in variants() if s['name'] in ['D__inherited','EAL__inherited','D__equal_five_domains','EAL__equal_five_domains']]
 with threadpool_limits(limits=1):
  for s in selected:
   labs=np.load(OUT/'run_records'/(s['name']+'.npz'))
   for seed in SEEDS:
    # Stored block IDs were serialized x:y; table uses tuple strings.
    old=original.loc[original.seed.eq(seed)].iloc[0];removed={tuple(map(int,x.split(':'))) for x in old.removed_blocks.split(';')};mask=np.array([tuple(map(int,x.strip('()').split(','))) in removed for x in blocks]);train=d.loc[~mask];mat,cols,domains,scaler,factors,_=design(train,s);km=KMeans(n_clusters=5,n_init=100,random_state=seed,max_iter=500,tol=1e-4).fit(mat);pred=km.predict(scaler.transform(d[cols])*factors);ref=labs[f's{seed}_k5']
    rows.append({'model':s['name'],'seed':seed,'n_training':len(train),'n_heldout':int(mask.sum()),'occupied_blocks':len(unique),'removed_blocks':old.removed_blocks,'full_prediction_ARI':adjusted_rand_score(ref,pred),'training_ARI':adjusted_rand_score(ref[~mask],pred[~mask]),'heldout_ARI':adjusted_rand_score(ref[mask],pred[mask]),'method':'same20km blocks and deletion sets in both constructs/weight schemes; scaler refit','meaning':'scientific partition sensitivity, not independent validation'})
 result=pd.DataFrame(rows);save('SPATIAL_BLOCK_STABILITY.csv',result);save('SPATIAL_BLOCK_STABILITY_SUMMARY.csv',result.groupby('model',as_index=False).agg(replicates=('seed','size'),median_ARI=('full_prediction_ARI','median'),minimum_ARI=('full_prediction_ARI','min'),p05_ARI=('full_prediction_ARI',lambda x:x.quantile(.05)),minimum_training_n=('n_training','min'),maximum_training_n=('n_training','max')))
 qa=json.loads((OUT/'CLUSTER_EXECUTION_QA.json').read_text());qa['spatial_replicates_per_model']=20;qa['spatial_total_fits']=80;qa['seconds_definition']='Elapsed postprocessing and20 initial spatial fits in resumed invocation; full fitting times are recorded by run, not claimed equal to this elapsed value';dump('CLUSTER_EXECUTION_QA.json',qa)
 print('SPATIAL_COMPLETE',len(result),flush=True)
def report():
 f=read('FINAL_CANDIDATE_FEATURE_MATRIX.csv',OUT);q=read('LANDMASK_18_TRACT_RESOLUTION.csv',OUT);e=pd.read_csv(OUT/'SCAG_ENTROPY_SCENARIO_SUMMARY.csv');c=pd.read_csv(OUT/'CONTROLLED_CLUSTERING_COMPARISON.csv');s=pd.read_csv(OUT/'CLUSTER_STABILITY_AND_PROFILES.csv');a=pd.read_csv(OUT/'CLUSTER_BETWEEN_MODEL_ARI.csv');spall=pd.read_csv(OUT/'SPATIAL_BLOCK_STABILITY.csv');sp=spall.loc[spall.model.eq('D__inherited')] if 'model' in spall else spall;age=read('BUILDING_AGE_SENSITIVITY.csv',OUT).loc[f.index];use=pd.read_csv(OUT/'BUILDING_AGE_POOLED_USE_MISSINGNESS.csv');vif=pd.read_csv(OUT/'CANDIDATE_VIF.csv')
 summaries=[]
 for (name,role),g in a.groupby(['model','role']):summaries.append({'model':name,'role':role,'n_common':g.n_common.iloc[0],'ari_median':g.ari.median(),'ari_min':g.ari.min(),'ari_p05':g.ari.quantile(.05),'n_paired_seeds':len(g)})
 save('BETWEEN_MODEL_COMPARISON_SUMMARY.csv',pd.DataFrame(summaries));stab=s.loc[s.record_type.eq('OPTIMIZATION_SEED_STABILITY')].copy();save('OPTIMIZATION_STABILITY_SUMMARY.csv',stab)
 def table(df,cols):return df[cols].to_markdown(index=False,floatfmt='.5f')
 primary=stab.loc[stab.model.eq('D__inherited') & stab.role.eq('fixed_k5')].iloc[0];comparison=pd.DataFrame(summaries)
 text=f"""# Stage 7 candidate feature decision packet — 2026-10-10

This package is an exploratory joint recovery–service–grid–built-environment–social–multi-hazard loss comparison. It does not replace stored Stage 7 labels, manuscript inputs, or figures. The candidate matrix preserves all 2,291 original residential GEOIDs and all 2,315 full-domain source identities. Scientific baseline: `{SCIENCE}`; independently reviewed feature-gate parent: `{PARENT}`; prior FEMA evidence: `65f388f9710566ffa845808bd7b10503de4da608`.

## Land-mask disposition

Four demonstrable mask errors were corrected by actual SCAG/LARIAC reintersection of cached source geometries. Eight cases were explained by the 2020 statistical-water definition versus archived tract ALAND/AWATER versions, retaining exact existing numerators/denominators and recording that difference. Six full-domain cases remain spatially unresolved, including four residential members. Projection and cached-area arithmetic do not account for these discrepancies. No polygon was rescaled to ALAND and no Census field was changed.

{table(q.reset_index(),['tract_id','residential_member','status','before_relative_error','after_relative_error','after_vs_census2020_relative_error'])}

The unresolved cases contain mixed land/water within named river hydrography; whole-feature ALAND/AWATER attributes do not locate the statistical-land portion. Even a close total-area fit from deleting a complete river is insufficient spatial evidence. Their land entropy, footprint fraction and original2014 age candidate remain null. Specific feature intersections, river names, both Census attribute versions and boundary symmetric differences appear in LANDMASK_18_TRACT_RESOLUTION.csv and LANDMASK_HYDRO_FEATURE_INTERSECTIONS.csv. Pure AWATER=0 hydrography and tracts reported as AWATER=0 in both versions are the only geometry corrections.

Actual primary complete cases: **{int(f.primary_complete_case.sum())}**. Also delivered: the explicitly named **2,276-row legacy complete-case** cohort and its controlled partition comparison. Four remaining residential records are not imputed or assigned new exploratory cluster labels.

Census documentation explains that intermittent water, swamps and glaciers may count as statistical land, while area hydrography includes those features. [Census glossary, Area Measurement](https://cdn.www.census.gov/programs-surveys/geography/about/glossary.html), [2020 TIGER/Line technical documentation, section4.10 and AppendixJ](https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2020/TGRSHP2020_TechDoc.pdf). Only18 official [2020 tract geometries](https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/Tracts_Blocks/MapServer/0) were retrieved for boundary comparison. No SCAG/LARIAC source records were downloaded again.

## Land-use measurement uncertainty

Entropy is eleven-class normalized **classified-land entropy**, not a complete all-land measure. Median classified coverage on the current complete cohort is {e.classified_land_coverage.median() if 'classified_land_coverage' in e else e.median_coverage.iloc[0]:.3%}. Missing-to-transport, dominant-category and proportional scenarios are hypothetical allocations, never observed classifications. Formal unconstrained lower/upper entropy bounds allow any allocation over the eleven categories; they are not confidence intervals.

{table(e,['scenario','n','spearman_vs_observed','median_abs_entropy_change','p95_abs_entropy_change','p95_abs_percentile_rank_change'])}

Proportional allocation preserves entropy mathematically. Concentrating missing area in the dominant category lowers it; assigning transport can raise or lower it. Strong rank correlation does not remove coverage uncertainty. The explicit lowest-coverage-quartile exclusion is a diagnostic sample perturbation, not an adopted threshold, and has its own sample hash. An85% primary cutoff was not imposed.

## Building age

Primary candidate: original2014 all-use valid-age footprint area share, never the sparse 2014-to-2020 transfer. Residential median valid-age coverage is **{age.all_use2014_age_coverage.median():.3%}**; median missing-age bound width is **{age.missing_age_bound_width.median():.3f}**. Strict2020 transfer median coverage is **{age.strict_2020_transfer_age_coverage_diagnostic.median():.3%}**. Lower bound = known pre1970 area / all footprint area; upper = (known pre1970 + unknown-age area) / all area. These represent unknown-age scenarios, not estimated construction years or CI. ACS is housing-unit weighted residential age, a scientifically different construct.

{table(use,['use','tracts','pooled_missing_area_fraction'])}

Government missingness is not treated as residential or zero. By-use unions cannot be added as though mutually exclusive overall areas. Age lower/upper, ACS replacement and no-age comparisons all preserve the remaining coordinate values and common primary tract sample.

## Controlled input and weighting

Primary candidate D retains raw B_480_hr, mandatory Init_Supply, four unchanged grid descriptors, classified-land entropy, union footprint coverage, original2014 all-use observed-age share, SOVI_SCORE, log1p building stock and ALR_NPCTL. EAL alternative replaces stock and rate with EAL_SCORE under exactly the same total loss/exposure budget. Published FEMA scores stay on their original scales before standardization. SOVI remains in every configuration. Neither ALR nor EAL is pure hazard; applicable multi-hazard FEMA losses are locally earthquake-dominated. The previous FEMA interpretation is reused, not recomputed as a new release.

Inherited five parent-domain budgets: recovery+initial service2/11, grid4/11, physical2/11, social1/11, loss/exposure2/11. Equal-domain alternative assigns0.2 to each of those same five parent domains. The three physical constructs share the physical total equally. Coordinate multiplier is sqrt(domain budget / coordinate count). Omitting age redistributes that fixed physical budget; it does not weaken the whole physical domain. This comparison is explicitly equal **five parent domains**, not equal weight to nine conceptual constructs. Housing5+ remains diagnostic. Population density is a separate demographic sensitivity receiving half the existing exposure-domain budget; it is not silently another physical-density feature.

B is mean realization-normalized deficit integrated0–480h; T80 is first crossing of80% by the mean tract service trajectory, not the average realization T80. AUC480=1−B/480 is redundant and excluded. Raw versus log1p B is a preprocessing sensitivity. Source/units/vintage/transformation and quality flags are listed per coordinate in FINAL_FEATURE_DEFINITIONS_AND_QA.csv.

## Optimization stability versus scientific sensitivity

{len(c.model.unique())} models, each20 independent seeds42–61, n_init100, direct weighted-coordinate KMeans for every k2–8. Each seed selects k by the normalized endpoint-chord elbow, never maximum silhouette. Fixed k5 is separately retained. No PCA or old labels enter this exploratory method. Each model/seed/k record is unique; proportional entropy is a same-definition diagnostic, not extra independent replication. Seed ranges are optimization variability and are not tract-sampling confidence intervals.

{table(stab.loc[stab.role.eq('fixed_k5')],['model','n','ari_median','ari_min','silhouette_mean','minimum_cluster_size'])}

Between-model results (same seed, common tract IDs):

{table(comparison.loc[comparison.role.eq('fixed_k5')],['model','n_common','ari_median','ari_min'])}

The fixed-k5 D optimization median pairwise ARI is {primary.ari_median:.5f}. Scientific stability is assessed separately through measurement, risk construct, weights, k, age definition and spatial sample changes. Twenty spatial block deletions yield D/inherited full-cohort prediction ARI median **{sp.full_prediction_ARI.median():.5f}**, minimum **{sp.full_prediction_ARI.min():.5f}**. The identical20 deletion sets are also evaluated for EAL and both domain budgets (80 fits total).20km projected centroid blocks remove10% of occupied blocks, refit scaling and clustering on retained tracts, and predict the entire complete cohort. This is a spatial sensitivity diagnostic, not new independent data or spatially representative validation. Descriptive profile quantiles are across tracts, not CI.

Simultaneous-coordinate VIF maxima: D **{vif.loc[vif.model.eq('D'),'vif'].max():.4f}**, EAL **{vif.loc[vif.model.eq('EAL'),'vif'].max():.4f}**. VIF diagnoses redundancy, not scientific validity.

## Recommendation and remaining author decisions

Use the specified D input as the provisional construct-driven primary candidate: it keeps economic stock and normalized multi-hazard loss distinct, retains the mandated social and immediate-service dimensions, and combines land-use mix, physical coverage and all-use2014 age rather than a residential-density typology. Retain EAL as a combined loss/exposure sensitivity. The raw B coordinate is interpretable in equivalent complete-service-loss hours; T80 and log1p B remain mandatory comparison evidence. This recommendation is not based on old labels or silhouette ranking.

Do not yet publish a complete2291-label replacement. Resolve the four remaining residential river masks or explicitly approve the documented complete-case domain. Classified coverage and all-use age incompleteness remain substantive uncertainty even when optimizer seeds are stable. Author decisions are required for inherited versus equal parent-domain weights, selected k, all-use2014 age versus ACS/no-age, and treatment of coverage uncertainty. Disagreement among these partitions is evidence of construct sensitivity, not a failure to search long enough. No cluster archetypes or causal claims were selected from the results.

All original physical inputs, schedules, trajectories, GA results, source tables, formal Stage7 labels, manuscript and figures remain unchanged. New calculations are candidate feature corrections and exploratory clustering only. Hash preservation and tests are reported in PRESERVATION_FINAL_QA.json and VERIFICATION_RESULTS.json.
"""
 (OUT/'STAGE7_FEATURE_DECISION_PACKET.md').write_text(text,encoding='utf-8',newline='\n')
 (OUT/'README.md').write_text('# Joint Stage 7 candidate QA and controlled exploratory comparisons\n\nRead STAGE7_FEATURE_DECISION_PACKET.md first. This directory contains new analysis only; it does not replace formal Stage7 results.\n\nReproduce with the Anaconda GIS/scikit-learn environment:\n\n```text\npython validate_stage7.py initialize\npython validate_stage7.py landqa\npython validate_stage7.py corrections\npython validate_stage7.py features\npython controlled_clustering.py\npython summarize_and_verify.py additional\npython summarize_and_verify.py spatial\npython summarize_and_verify.py report\npython -m pytest test_final_validation.py\npython summarize_and_verify.py verify\n```\n\nThe unchanged earlier extraction and FEMA audit are inherited on this analysis branch. Large raw source caches stay local and are referenced by exact hashes; no raw-source reacquisition is needed on this Windows checkout. The only fresh acquisition was18 Census2020 tract geometries for QA.\n\nFINAL_CANDIDATE_FEATURE_MATRIX.csv keeps2291 rows with nulls; COMPLETE_CASE_FEATURE_MATRIX.csv contains2287 rows. LEGACY_2276_COMPLETE_CASE_FEATURE_MATRIX.csv is separately retained. run_records/ contains all20-seed,k2–8 labels and fit metrics. Original Stage7 labels were not used for feature selection or fitting.\n',encoding='utf-8',newline='\n')
 print('REPORT_COMPLETE',flush=True)
def verify():
 b=json.loads((OUT/'PRESERVATION_BASELINE.json').read_text());changes=[k for k,v in b['protected_files'].items() if sha(ROOT/k)!=v];formal=json.loads((OLD/'INPUT_SOURCE_HASHES.json').read_text());print('FORMAL_HASH_SCHEMA',type(formal).__name__,flush=True)
 if isinstance(formal,dict) and 'files' in formal:formal=formal['files']
 sourcechanges=[]
 if isinstance(formal,dict):
  for k,v in formal.items():
   expected=v.get('sha256') if isinstance(v,dict) else v
   if expected and (ROOT/k).is_file() and sha(ROOT/k)!=expected:sourcechanges.append(k)
 assert not changes and not sourcechanges
 original_index=(OUT/'original_state/index.bin').read_bytes();assert git('ls-files','--stage','-z')==original_index
 assert git('rev-parse','HEAD').decode().strip()==b['head']==SCIENCE
 dump('PRESERVATION_FINAL_QA.json',{'protected_count':len(b['protected_files']),'protected_files_changed':len(changes),'formal_source_manifest_entries':len(formal),'formal_source_files_changed':len(sourcechanges),'original_index_unchanged':True,'original_staged_count':b['staged_count'],'original_head_and_branch_unchanged':True,'scientific_files_changed':0,'formal_Stage7_replaced':False})
 print('PRESERVATION_PASS',len(b['protected_files']),len(formal),flush=True)
if __name__=='__main__':{'additional':additional_qa,'spatial':spatial_complete,'report':report,'verify':verify}[sys.argv[1]]()
