"""Evidence-bounded scientific recommendation; text proposals only."""
from weight_path import *
import re
def md(n,t):(OUT/n).write_bytes(t.encode())
def table(x):return x.to_markdown(index=False,floatfmt='.4f')
def main():
 summary=pd.read_csv(OUT/'MODEL_SUMMARY.csv');steps=pd.read_csv(OUT/'NEIGHBOR_WEIGHT_STEP_SUMMARY.csv');age=pd.read_csv(OUT/'BE0_BE1_CONSTRUCT_COMPARISON.csv').drop_duplicates(['lambda_value','seed']);counts=pd.read_csv(OUT/'CLASS_INTERPRETATION_SUPPORT_COUNTS.csv');imp=pd.read_csv(OUT/'MINORITY_VS_LARGE_PARTITION_CHANGE.csv');grid=pd.read_csv(OUT/'GRID_DOMAIN_LOW_SEPARATION_DIAGNOSTICS.csv');dom=pd.read_csv(OUT/'DOMAIN_SEPARATION_SUMMARY.csv');prof=pd.read_csv(OUT/'CLASS_PROFILES_ORIGINAL_UNITS.csv');minor=pd.read_csv(OUT/'MINORITY_DOMINANT_DESTINATION_TRACE.csv');facts=json.loads((AUD/'MEASUREMENT_LIMITATIONS_FACTS.json').read_text());decomp=json.loads((OUT/'BETWEEN_CLASS_DECOMPOSITION_VERIFICATION.json').read_text());continuous=pd.read_csv(OUT/'CONTINUOUS_RECOVERY_SOVI_EVIDENCE.csv');new=json.loads((OUT/'FIT_EXECUTION_RECORD.json').read_text())
 g=counts.loc[counts.finding=='large_reference_group_service_loss_and_SOVI_directions'];large=g.groupby('scope')[['n_tested','supporting_n','contradicting_n']].sum().reset_index()
 physical=counts.loc[counts.finding.str.endswith('_pairwise_class_mean_sign')].groupby(['scope','finding'])[['n_tested','supporting_n','contradicting_n']].sum().reset_index()
 save('MANUSCRIPT_FINDING_SUPPORT_SUMMARY.csv',pd.concat([large.assign(finding='large_group_recovery_SOVI_contrast'),physical],ignore_index=True))
 age_summary=age.groupby('lambda_value').agg(n_seeds=('seed','size'),ARI_median=('ARI','median'),reassigned_median=('aligned_reassigned_n','median'),reassigned_min=('aligned_reassigned_n','min'),reassigned_max=('aligned_reassigned_n','max')).reset_index()
 physical_range=[]
 for (model,scope,seed,feature),sub in prof.loc[prof.feature.isin(PHYS)].groupby(['model','scope','seed','feature']):
  physical_range.append(dict(model=model,scope=scope,seed=seed,feature=feature,class_mean_range=sub['mean'].max()-sub['mean'].min(),all_four_classes=len(sub)==4))
 save('PHYSICAL_PROFILE_DIFFERENTIATION.csv',physical_range)
 physical_range=pd.DataFrame(physical_range)
 comparison=summary[['model','lambda_value','seed_ARI_median','seed_ARI_min','spatial_ARI_median','spatial_ARI_p05','spatial_ARI_min','target34_purity_min']]
 nominal=[]
 for lam in LAMBDAS:
  w=(1-lam)*EQ+lam*INH;nominal.append(dict(lambda_value=lam,**dict(zip(DOMAINS,w))))
 save('DOMAIN_WEIGHT_VECTORS.csv',nominal)
 between=dom.loc[dom.model.isin(['BE0_L000','BE0_L100','BE1_L000','BE1_L100'])]
 baseprofiles=prof.loc[(prof.model=='BE0_L000')&(prof.scope=='full')&(prof.seed==42)]
 base_profiles=baseprofiles.pivot(index='BE0_seed42_class',columns='feature',values='mean')[['B_480_hr','Init_Supply','SOVI_SCORE',*PHYS,*GRID]].reset_index()
 endchanges=pd.read_csv(OUT/'ENDPOINT_CLASS_CHANGES.csv');end42=endchanges.loc[endchanges.seed==42,['be','reference_class','baseline_n','predicted_n','intersection','retention','purity','jaccard','largest_destination_fraction','destinations','origins']]
 worst=minor.sort_values('purity').groupby(['model','scope'],sort=False).head(1)
 reversals=pd.read_csv(OUT/'CLASS_INTERPRETATION_ROBUSTNESS.csv');rev=reversals.loc[(reversals.finding=='large_group_recovery_SOVI_contrast')&~reversals.supports_joint_direction.eq(True),['model','scope','seed','loss_difference_hr','SOVI_difference']]
 md('DOMAIN_WEIGHT_RATIONALE.md',f'''# Domain-weight rationale

The scientific target is a joint electricity-service recovery/community-characteristics description. Five equal domain budgets are defensible as an explicit conceptual balance, not a discovered optimum. The inherited scheme assigns distance budget in proportions associated with the earlier coordinate counts and places substantially more emphasis on grid dependency. Neither budget is a causal-effect weight or a guarantee of equal observed class separation.

## Predeclared path

For lambda in{{0,.25,.50,.75,1}}, w(lambda)=(1-lambda)w_equal+lambda w_inherited. StandardScaler uses population variance; each standardized coordinate is multiplied by sqrt(w_domain/number of retained coordinates in that domain). D remains log1p building value plus published unadjusted ALR percentile. BE1 retains the whole physical budget and shares it over two coordinates; it is a deliberate redistribution. The parent audit's fixed-coordinate deletion control isolates that redistribution and is not replaced here.

{table(pd.DataFrame(nominal))}

The equal scheme increases SOVI from1/11 to.2 (a2.2-fold squared-distance budget), reduces grid from4/11 to.2 (factor.55), and raises the other three budgets from2/11 to.2 (factor1.1). In BE0 the equal physical-coordinate budget is.2/3, not.2 each. In BE1 it is.2/2. These are the full changes, not only an increase in social emphasis.

## Observed consequences

{table(steps)}

The largest observed reorganization in both physical definitions occurs between the prescribed.75 and1 settings. This does not locate a continuous change point: the interval was not sampled further. Equal weighting is justified by the intended conceptual balance, not the relatively favorable seed/spatial metrics atlambda0. No apparent plateau identifies correct weights. All conditional four-class claims must name the weights; inherited fixedk4 results cannot be validated by earlier selectedk5 evidence.
''')
 text=f'''# Stage7 construct and domain-weight final review

## Preferred scientific recommendation

Retain BE0's historical2014 age coordinate in the **explicitly historical, descriptive reference specification**, with five equal conceptual domain budgets and D's separately interpretable economic stock/loss propensity. Its added historical-stock meaning is relevant to community characterization; it is not a building-damage predictor or a contemporaneous all-use measurement. Retention is a construct judgment, not a reward for preserving the four classes. BE1 is the meaningful physical-form/no-age comparator.

Reduce the four-class partition's manuscript role to a **weight-conditional exploratory joint profile analysis**. Do not present it as a unique or generally stable community taxonomy or assign universal archetype names. Put the continuous tract-level recovery/social relationship ahead of label-dependent conclusions. The diagnostic evidence is ready for author manuscript review under this restricted scope; an unqualified substantive four-archetype claim is not ready. This is one coherent recommendation, not a search for the empirically best intermediate weight.

## Execution and identity

Parent {PARENT}; independent branch analysis/stage7-construct-weight-decision-20261010. Same2287 complete residential GEOIDs in original saved order, within2291 master records. The four unresolved records remain unclassified and unimputed. Fixedk4, seeds42-61,n_init100,max_iter500,tol1e-4,Lloyd; sklearn{sklearn.__version__}. D, raw-hour B, Init_Supply, grid features, SOVI and preprocessing are fixed. All20 registered spatial cases reuse exact20-km deletion sets; only17 geographic sets are distinct. Spatial scalers use retained training tracts only; predictions include all2287. Spatial class matching uses training overlap only and is never reselected using held-out tracts.

Completed exactly{new['new_fits']} missing intermediate fits; reused{new['reused_endpoint_runs']} endpoint runs. Intermediate-fit wall time {new['elapsed_s']:.3f}s. No earlier880 fits repeated; no k search, source downloads, GIS, simulations, scheduling or GA. The four endpoint NPZ archives are copied byte-for-byte; original saved-label means remain explicitly identified where fitted full-cohort centers were absent. No baseline refit invents those centers. New intermediate actual fitted centers/scalers/labels are saved.

The decision rule was written before intermediate fits. Numerical, specification and spatial stability have separate denominators and no result-selected acceptance threshold. Empirical seed/deletion ranges are not confidence intervals or geographic accuracy. All400 model runs are conditional computational cases, not400 independent datasets.

## Building-age construct and measurement validity

BE0 combines classified-parcel land-use composition, observed ground-building coverage and the pre1970 share of **valid-age building area in the original2014 inventory**. BE1 deliberately omits historical stock composition. Historical age is not essential to predicting modeled electricity restoration, which does not simulate building damage; its contribution is descriptive characterization of community stock. That is relevant to the declared joint typology, provided the manuscript specifies the historical inventory instead of implying contemporary physical condition.

The modeled2pc50 recovery is a hazard/scenario model rather than a literal2014 historical event. Other inputs are heterogeneous-vintage descriptors: SCAG2019 classified parcels, a2020 LARIAC release with older/mixed imagery, ACS2018-2022 housing estimates, and FEMA v1.19 March2023 exposure/loss scores. They do not form a synchronized contemporary census. Retaining age is temporally defensible only as a historical-stock coordinate. It is not appropriate for claims about current all-use age, current seismic fragility, post-event building damage, or causally explaining outage loss.

Median valid-age coverage is{facts['age2014_valid_area_coverage_median_2287']*100:.3f}% of the original2014 outlines. This supports observation of that inventory's valid-age stock, not correct construction years or representative contemporary coverage. Strict2014-to2020 transfer covers only{facts['strict2020_age_transfer_coverage_median_2287']*100:.3f}% of2020 footprint area on this cohort and cannot establish an all-use2020 age measure. Missing age is nonrandom: the saved within-use pooled government area audit has95.804% missing age, versus1.031% residential; cross-use unions must not be added into one denominator. Valid-age conditioning underrepresents government/unknown-use stock and limits interpretation even when the overall median is high.

ACS2018-2022 age uses residential housing-unit counts and survey estimates, while2014 age uses observed all-use valid-age footprint area. Its newer vintage does not make it an interchangeable or more complete all-building substitute. The parent audit's ACS/bounds/coverage comparisons are retained, not repeated. SCAG median classified-land coverage is{facts['classified_land_coverage_median_2287']*100:.3f}%; entropy describes only that classified area. Footprint coverage is ground/roof projection, not floor area or structural condition.

Historical age gains a separate stock-composition descriptor without claiming damage prediction. This gain warrants BE0 as the historically qualified exploratory reference; it does not warrant strengthening the four-class scientific claim. If the author requires contemporaneous all-use stock, BE0 fails that meaning and BE1 must be used instead; no validated modern all-use replacement is available. This condition is about the claimed construct, not a post hoc ARI preference.

Same-weight age inclusion/exclusion effects:

{table(age_summary)}

Every tested age contrast changes memberships; that is not evidence the age coordinate is causally important or that BE0 is truer. Parent fixed-coordinate controls show median121 reassignments when the equal physical20% budget is redistributed, versus78.5 when surviving physical weights remain. Content and redistribution both contribute. Original-unit age/profile changes are in BE0_BE1_CONSTRUCT_COMPARISON.csv; denominator/vintage limits remain unchanged.

## Weight sensitivity: boundaries, mergers and geographic identity

{table(comparison)}

Neighbor-step results are listed in DOMAIN_WEIGHT_RATIONALE.md and NEIGHBOR_WEIGHT_STEP_SUMMARY.csv. Early predefined steps move tens of tracts, but the.75-to1 step reorganizes hundreds to over1000. BE0 neighbor median ARI is.2400 with1043.5 reassignments; BE1 is.4460 with564. The equal/inherited BE0 endpoint median ARI is.212286. This is a large partition reorganization, not a consequence of moving only34 tracts.

After removing the original34 only from the endpoint comparison (no new fitting), median ARI is{imp.loc[imp.be=='BE0','ARI_excluding_original34'].median():.4f} for BE0 and{imp.loc[imp.be=='BE1','ARI_excluding_original34'].median():.4f} for BE1. Median reassignments among the other2253 are{imp.loc[imp.be=='BE0','reassigned_other2253_n'].median():.1f} and{imp.loc[imp.be=='BE1','reassigned_other2253_n'].median():.1f}. Raw seed42 class flows:

{table(end42)}

These raw destination/origin counts expose mergers/splits despite optimal one-to-one display matching. Many large-class boundaries change; it is not just an isolated minority-class merger. Neighbor row split entropy and full counts are saved for everyseed. Geographic block-count distributions and total-variation changes identify where matched groups expand/contract without downloading or inventing new geography. Those are member-count distributions across registered blocks, not tract physical area.

The34-member reference set has a sparse-support problem under specific deletions. BE0lambda0 seed54 retains only4 target training tracts and expands to92, retaining all34 but purity36.96%. Hungarian matching failures under alternatives are explicitly distinct from disappearance: raw destination counts and a separate dominant-destination trace show where originals actually went. Some predicted groups absorb hundreds of other tracts. No weight setting establishes a generally specific34-tract archetype. Original-member retention alone cannot support that claim.

## What the classes represent and why grid separation is low

For coordinatex_j in weighted standardized space, TSS_j=sum_i(x_ij-mean_j)^2; BSS_j=sum_c n_c(mean_cj-mean_j)^2; WSS_j=TSS_j-BSS_j. Domain contribution=sum_j_in_domain BSS_j/sum_all_j BSS_j. Units here are squared scaled distances; all tracts are equally counted. This is neither nominal budget nor population-weighted variance nor causal variable importance. Source reproduction maximum absolute error is{decomp['max_source_absolute_error']:.3g}.

{table(between)}

At equal BE0, recovery/initial service contributes26.9525%, grid1.6790%, physical10.5757%, social40.7068%, stock/loss20.0860%. The earlier rounded26.95/1.67/10.56/40.73/20.08 figures are close but not exactly the same20-seed aggregation; the values above independently reproduce the actual source with the stated denominator. At inherited BE0, grid rises to38.4090% and social falls to4.8848%. Weighting changes which dimensions define class boundaries.

Grid's low equal-weight separation is primarily weak class-mean contrasts with substantial within-class variation, not an accidentally omitted budget. Standardization gives the grid exactly20% ofTSS. Only about{dom.loc[(dom.model=='BE0_L000')&(dom.domain=='grid'),'domain_variance_explained_mean'].iloc[0]*100:.3f}% of grid-domain variance is between these classes; the remainder stays within them. Coordinate-level explained fractions are saved, along with the following descriptive associations:

{table(grid)}

Degree has moderate association with service loss, while the remaining grid coordinates have weaker linear overlap with the other domains. Thus some shared information exists, but the low BSS is not evidence that all grid descriptors are redundant. Continuous grid variation need not define discrete community boundaries. Increasing grid weights changes the partition, but cannot validate that change. Recovery and initial service are clustering inputs: their resulting class contrasts are not independent validation.

The equal-weight reference is best called **joint recovery/community profiles dominated by social vulnerability and initial service, with secondary physical/exposure variation**. Across the whole path, the safer label is **a weight-dependent descriptive partition**. Distinct, stable multidimensional archetypes is too strong.

## Manuscript-level finding checks

The large-group rule selects the highest/lowest mean service-loss classes among reference groups with at least10% of cohort membership. That threshold only defines this descriptive comparison; it is not a model-admission criterion. Reference raw class labels are{decomp['large_group_reference_labels']}. Full-class display matching uses reference overlap; spatial matching is derived from own-model training overlap only. Case counts are:

{table(large)}

The loss/SOVI opposing direction holds in all200 complete-cohort model-seed cases;193 of200 spatial cases support it and7 contradict it. Explicit contradictory cases:

{table(rev)}

The full-cohort persistence does not mean identical class membership or unchanged archetype meaning. Continuously measured B and SOVI have Pearson r={continuous.loc[continuous.measure=='Pearson','value'].iloc[0]:.4f}, Spearman r={continuous.loc[continuous.measure=='Spearman','value'].iloc[0]:.4f}. At the respective sample75th percentiles,580 tracts have high loss,572 highSOVI,116 overlap;464 high-loss tracts are outside highSOVI and456 highSOVI outside high loss. Ties are retained with>=, so high-loss membership exceeds one quarter. This is direct tract-level descriptive evidence of noncoincidence, independent of cluster weights, not a causal or universally negative social effect.

Physical class-pair direction checks:

{table(physical)}

These counts use sixreference class-pairs times20seeds times10specifications (1200 perfeature/scope). They describe sign consistency only. PHYSICAL_PROFILE_DIFFERENTIATION.csv provides actual original-unit class-mean ranges for everycase; a nonzero difference or a persistent sign alone does not establish substantive importance. Equal BE0 entropy/footprint contribute to descriptive differentiation, but neither their precise rankings nor age-based class interpretations are invariant over weights and geographic cases.

No test here validates built environment as a cause of service loss. No global stability threshold is retrofitted. Optimization reproducibility, source validity and specification validity remain separate.

## Five validity judgments

|Criterion|Judgment|
|---|---|
|Measurement validity|Inputs are credible only with classified-land, mixed-vintage footprint and valid-age2014 limits; contemporary all-use age is not supported.|
|Construct validity|BE0 suits historically qualified joint profiles; neither BE0 norBE1 is comprehensive built environment or a damage predictor.|
|Numerical stability|Most medians are high, but lower-tail seed cases vary; optimizer repeatability does not resolve weighting.|
|Specification stability|A major endpoint reorganization occurs under both age definitions; universal four-class taxonomy is not supported.|
|Spatial stability|Large reference contrast usually persists, but7 direction reversals and minority-class expansion/merging prevent general geographic archetype claims.|

## Final answers

1. **Age:** retain2014 age in the explicitly historical exploratory reference. It need not be a contemporary main interpretive claim; report its source/denominator and sensitivity. Do not replace it with ACS as the same measurement.
2. **BE0 versusBE1:** BE0 more fully describes joint community stock composition when historical scope is accepted. BE1 answers a narrower physical-form question and is the primary no-age comparison, not a proven scientific improvement.
3. **Equal weights:** defensible as equal conceptual-domain budgets; not objective optimality, equal empirical separation or independence. Disclose greaterSOVI and lowergrid emphasis relative to inherited weights and the fullpath sensitivity.
4. **Four classes:** conditionally interpretable at a named specification, not substantively invariant across reasonable weight choices. Avoid stable archetype names, especially the34-tract group.
5. **Readiness:** ready for restricted manuscript integration review as exploratory supporting joint profiles; not ready for an unqualified unique/stable four-class substantive finding. Prefer the continuous recovery/social noncoincidence as the stronger descriptive result.
6. **Exact text changes:** Methods must state historical scopes, fixedcohort exclusions, Ddefinitions, formula/weights and training-only spatial matching. Results must name the reference specification, quantify reorganization and distinguish retention/purity, with continuous evidence before archetypes. Discussion must state weight dependence, vintage/missingness limits and noncausality. Supplement must contain all predefined path results, age deletion/redistribution controls and full spatial lower tails. Text proposals are in MANUSCRIPT_DECISION_OPTIONS.md; no manuscript has been edited.

There is no missing numerical input preventing this restricted decision. The unresolved scientific blocker is the stronger taxonomy claim itself, not a request for more optimization. Four source geometries remain unresolved and unclassified; contemporary all-use age remains unavailable. No promotion or formal-source changes are authorized or performed.
'''
 md('STAGE7_CONSTRUCT_WEIGHT_FINAL_REVIEW.md',text)
 md('MANUSCRIPT_DECISION_OPTIONS.md',f'''# Manuscript decision and text proposals

## Preferred route

Use BE0/equal-five-domains/D as a **historically qualified exploratory reference**, keep BE1 and the full predefined weight path as sensitivity evidence, and give continuous recovery/social noncoincidence the main descriptive interpretation. Do not elevate one intermediate weight because its partition looks stable. Do not remove age to fix a small cluster or rename fourclasses into universal archetypes.

## Methods proposal

We characterized joint recovery and community profiles using cumulative normalized modeled service loss over0-480h and initial modeled service availability, four grid-dependency descriptors, classified-parcel land-use entropy, building-footprint coverage, historical observed building-stock age, social vulnerability, and economic stock/multi-hazard loss propensity. The age coordinate is the pre1970 share of valid-age building area in the original2014 inventory; it is not contemporary all-use age. Building stock was log1p transformed, while cumulative loss and publishedFEMA scores retained their original scales beforestandardization. Each of fiveconceptual domains received20% of squared-distance weight, shared equally among thatdomain's coordinates. This convention was compared with inheriteddomain weights through fivepredeclared settings and with a no-age physical-form specification. Fixedk4 computations used20seeds and100initializations. The analysis used2287complete residential tracts; four unresolved geometry records in the2291master remained unclassified. Geographic perturbations reused20registered spatial deletion cases; scalers were fitted on retainedtracts and matching used retainedtraining overlap only.

## Results proposal

The equal-domain profiles separated recovery/initial service and social vulnerability strongly but explained little between-class grid variance. At fixedk4, moving from equal to inheritedweights reorganized the partition substantially (BE0same-seed medianARI.2123), including multiple large groups rather than only the34-member subgroup. The largest prescribed weightstep had median1043.5 reassignments forBE0 and564forBE1. The higher-loss/lower-SOVI largegroup contrast persisted across200complete-cohort cases but reversed in7of200spatial cases. At the tractlevel, highloss and highsocial vulnerability did not coincide:116of580upper-quartile-loss tracts also belonged to the572upper-quartile-SOVI tracts. These findings support descriptive noncoincidence, not causal effects or a unique community taxonomy. Under one sparse-support deletion, all34original subgroup members remained in a92-member predicted group, so retention100% coexisted with purity36.96%.

## Discussion proposal

The jointprofiles depend on the scientific definitions and relative influence assigned to their inputs. Equal conceptualbudgets do not yield equal observed separation. Land-use entropy conditions on classifiedparcelland; footprintgeometry and age have heterogeneousvintages; validconstructionyears are missing nonrandomly bybuildinguse. Thehistorical agecoordinate adds stockcomposition but cannotrepresent contemporary allbuildingcondition. Cluster-level recovery differences are internal descriptive features because recovery enters fitting. Geographic and weighting sensitivity limit stable archetype names and minority-group specificity; continuous relationships should not depend exclusively on labels.

## Supplement proposal

Report original-unitprofiles, fullseed/spatial ranges, allfivepath settings forBE0/BE1, rawneighbor/endpointcontingencies and domainBSS/TSSdefinitions. Retain prior age/ACS/bounds/SCAGtests with their correct denominators, the fixed-coordinate no-redistributioncontrol, and minority rawdestinations/purity/Jaccard. Separate optimizedlabels from spatial predictions and distinguish empiricalfixed-case spread fromconfidenceintervals.

## Alternative if contemporary physical form is required

Use BE1 entropy+footprint, retain2014age only in descriptiveprofiles and sensitivity. This loses historicalage composition; it neither establishes better spatialspecificity nor solves weightdependence. Do not substitute ACSas equivalentall-useage. This change requires an authorconstructdecision and is not applied here.

## If four-class substantive taxonomy is essential

Current evidence does notsupport a unique generallystabletaxonomy. Deemphasize clustering rather than searchweights until it passes. Existing continuous/stratified tractmeasurements can show recovery/SOVInoncoincidence without additionaloptimization, restoration or physicalsampling. No newanalysis ormanuscript replacementis triggered by this recommendation.
''')
 md('README.md','''# Stage7 final construct and domain-weight diagnostic review

Start with STAGE7_CONSTRUCT_WEIGHT_FINAL_REVIEW.md and DOMAIN_WEIGHT_RATIONALE.md. This package is a scientific decision record, not a replacement of formalStage7 or a promotion.

- WEIGHT_CONSTRUCT_DIAGNOSTICS.pdf: fouractual-size185-mm diagnostic pages with separatecaptions.
- WEIGHT_PATH_RESULTS.csv:200full-cohort summaries; the paired/reference ARIs and reassignments are explicitly named.
- WEIGHT_PATH_PAIRWISE_COMPARISONS.csv: all within-physical-definition weightpairs; ALL_SPECIFICATION_PAIRWISE_ARI.csv coversall45modelpairs.
- WEIGHT_PATH_SPATIAL_STABILITY.csv:200spatialcases, eachcomparedwith itsownsame-seedfullbaseline.
- BE0_BE1_CONSTRUCT_COMPARISON.csv:100same-weight/seedagecontrasts withoriginal-unitprofiles.
- CLASS_INTERPRETATION_ROBUSTNESS.csv andsupport-counttables: exactdirectionchecksanddenominators; no significanceclaim.
- Rawclasscontingencies, original-unitprofiles, training-onlymatching, minoritydestinationtraces andgeographicblockdistributions retain counterexamples.
- run_records:10NPZ/JSONbundles withlabels, GEOIDs, scalers, coordinatefactors andcenters. FourendpointNPZs areexactcopies; originalcenter-kindlimitationsarepreserved.
- PREDECLARED_RUN_SPECIFICATION.json and PREDECLARED_DECISION_RULE.md define the bounded experimentbeforefits.
- Scripts declare/fit/analyze, summarize, write text, render andverify. Runonlythisdirectory'sscripts; noformalstagecommands.

The commoncohort is2287of2291residentialtracts. Fourgeometry-unresolved recordsareunclassified; noimputation. Completed240newfits and160reusedendpointruns; noadditionalfitsareproposed. Scientificvalidityisnotjudgedfromsilhouette, oldlabelagreement, or a thresholdchosenafterresults.
''')
 # Normalize prose spacing while protecting literal feature names, filenames and hashes.
 compounds={'fixedcohort':'fixed cohort','stockcomposition':'stock composition','highSOVI':'high SOVI','highloss':'high loss','retainedtraining':'retained training','validconstructionyears':'valid construction years','buildinguse':'building use','allbuildingcondition':'all-building condition','land-useentropy':'land-use entropy','lowSOVI':'low SOVI','fullpath':'full path','rawdestinations':'raw destinations','sourcegeometries':'source geometries','no-agephysical':'no-age physical','coordinatebudget':'coordinate budget','stock/loss':'stock/loss','classmeans':'class means','nominalbudget':'nominal budget','equalweights':'equal weights','inheritedweights':'inherited weights','standardizedcoordinates':'standardized coordinates','geographiccases':'geographic cases','registeredblocks':'registered blocks','referencegroups':'reference groups','domainweights':'domain weights','physicalbudget':'physical budget','loss/SOVI':'loss/SOVI','publishedFEMA':'published FEMA','completecohort':'complete cohort','equal-domainprofiles':'equal-domain profiles','physical-form/no-age':'physical-form/no-age','cohortmembership':'cohort membership','constantweights':'constant weights','label-dependent':'label-dependent','seed/deletion':'seed/deletion','independentdatasets':'independent datasets','mixed-vintage':'mixed-vintage','formalStage7':'formal Stage 7','smallcluster':'small cluster','all-useage':'all-use age','classmembership':'class membership','noimputation':'no imputation','allfivepath':'all five path','valid-age2014':'valid-age 2014','geographicaccuracy':'geographic accuracy','agecoordinate':'age coordinate','observedconstruction':'observed construction','currentbuilding':'current building','economicstock':'economic stock','lowergrid':'lower grid','greaterSOVI':'greater SOVI','originalcenter-kind':'original center-kind','predefinedsettings':'predefined settings'}
 for path in OUT.glob('*.md'):
  text=path.read_text(encoding='utf-8')
  for a,b in compounds.items():text=text.replace(a,b)
  for a,b in {'n_init100':'n_init = 100','max_iter500':'max_iter = 500','tol1e-4':'tol = 1e-4','Fixedk4':'Fixed k=4','fixedk4':'fixed k=4','from1/11':'from 1/11','to.2':'to 0.2','factor.55':'factor 0.55','by.':'by 0.','with.':'with 0.','prescribed.75':'prescribed 0.75','the.75':'the 0.75','meanB':'mean B','highSOVI':'high SOVI','thatdomain':'that domain','somepredicted':'some predicted','fullseed':'full seed','currentall-use':'current all-use','fourclasses':'four classes','forBE0':'for BE0','forBE1':'for BE1','ofTSS':'of TSS'}.items():text=text.replace(a,b)
  lines=[]
  for line in text.splitlines():
   if line.startswith('|'):lines.append(line);continue
   protected={}
   def protect(mt):
    key=f'@@TOKEN{len(protected)}@@';protected[key]=mt.group(0);return key
   line=re.sub(r'(?:\b[a-f0-9]{40,64}\b|\b\w+_\w+\b|\S+\.(?:csv|npz|json|md|pdf)\b|BE[01]|log1p|2pc50|SOVI|1e-4)',protect,line)
   line=re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ',line)
   line=re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ',line)
   line=re.sub(r'(?<=[a-z])(?=\.[0-9])',' ',line)
   for a,b in protected.items():line=line.replace(a.replace('TOKEN','TOKEN '),b).replace(a,b)
   line=line.replace('pre 1970','pre-1970').replace('k 4','k = 4').replace('k 5','k = 5').replace('analysis/stage 7-','analysis/stage7-').replace('v 1.19','v1.19')
   lines.append(line)
  path.write_bytes(('\n'.join(lines)+'\n').encode())
 # Manuscript-facing paragraphs use full words and parallel definitions.
 md('MANUSCRIPT_DECISION_OPTIONS.md','''# Manuscript decision and text proposals

## Preferred route

Use BE0, five equal domain weights and D as a historically qualified exploratory reference. Retain BE1 and the entire predefined weight path as sensitivity evidence. Give continuous recovery/social-vulnerability noncoincidence the main descriptive interpretation. Do not select an intermediate weight for its favorable partition, delete age to preserve a small class, or assign universal archetype names.

## Methods proposal

We characterized joint recovery and community profiles using normalized modeled service loss integrated over 0-480 h and initial modeled service availability; four grid-dependency descriptors; classified-parcel land-use entropy, building-footprint coverage and historical building-stock age; social vulnerability; and economic stock and multi-hazard loss propensity. The age coordinate is the pre-1970 share of valid-age building area in the original 2014 inventory, rather than contemporary all-use age. Building value was log1p transformed; service loss and published FEMA scores retained their original scales before standardization. Each of the five conceptual domains received 20% of squared-distance weight, shared equally among its coordinates. We compared this convention with inherited domain weights through five predeclared settings, and with a no-age physical-form specification. Fixed k=4 comparisons used 20 seeds and 100 initializations. The analysis included 2,287 complete residential tracts; four unresolved geometry records in the 2,291-row master remained unclassified. Spatial perturbations reused 20 registered block-deletion cases. Scalers were fitted on retained training tracts; one-to-one class matching used their overlap only.

## Results proposal

The equal-domain profiles separated recovery/initial service and social vulnerability strongly, but left most grid-descriptor variation within classes. At fixed k=4, moving from equal to inherited weights substantially reorganized the BE0 partition (same-seed median ARI=0.2123), including several large groups. The largest prescribed weight step produced median reassignments of 1,043.5 tracts for BE0 and 564 for BE1. The higher-loss/lower-SOVI large-group contrast persisted in all 200 complete-cohort cases, but reversed in seven of 200 spatial cases. At the tract level, high service loss and high social vulnerability did not coincide: 116 of 580 upper-quartile-loss tracts were also among the 572 upper-quartile-SOVI tracts. These are descriptive relationships, not causal effects or evidence of a unique community taxonomy. Under one sparse-support deletion, all 34 original subgroup members remained in a 92-member predicted group: 100% retention coexisted with 36.96% purity.

## Discussion proposal

The joint profiles depend on input definitions and their relative distance weights. Equal conceptual budgets do not yield equal observed class separation. Land-use entropy conditions on classified parcel land; footprint geometry and age have heterogeneous vintages; missing construction years vary by building use. Historical age adds stock-composition information but does not measure contemporary all-building condition. Recovery differences are internal descriptive features because recovery enters clustering. Geographic and specification sensitivity limit stable archetype names and the specificity of the small subgroup. Continuous relationships should therefore be reported independently of cluster labels.

## Supplement proposal

Report original-unit profiles, complete seed and spatial ranges, all five predefined settings for BE0 and BE1, raw neighbor/endpoint contingencies, and domain BSS/TSS definitions. Retain prior ACS, age-bound and SCAG comparisons with their correct denominators; include the fixed-coordinate deletion control and minority destination, purity and Jaccard records. Separate full-cohort fitted labels from spatial predictions, and empirical fixed-case ranges from confidence intervals.

## Alternative if contemporary physical form is required

Use BE1 entropy plus footprint coverage, with 2014 age in descriptive profiles and sensitivity only. This loses historical composition information; it neither establishes better spatial specificity nor resolves weight dependence. ACS residential age is not an equivalent all-use replacement. This alternative requires an author construct decision and has not been applied to formal outputs.

## If a substantive four-class taxonomy is essential

Current evidence does not support a unique, generally stable taxonomy. Reduce that claim rather than repeatedly adjusting weights. Existing continuous or stratified measurements can show recovery/social-vulnerability noncoincidence without further optimization, restoration calculations or physical sampling. This recommendation does not trigger manuscript replacement.
''')
 md('README.md','''# Stage 7 construct and domain-weight decision

Start with STAGE7_CONSTRUCT_WEIGHT_FINAL_REVIEW.md and DOMAIN_WEIGHT_RATIONALE.md. This is a diagnostic scientific decision package; it does not replace formal Stage 7 or the manuscript.

- WEIGHT_CONSTRUCT_DIAGNOSTICS.pdf contains four 185-mm diagnostic pages; separate captions define the empirical intervals and comparisons.
- WEIGHT_PATH_RESULTS.csv contains 200 full-cohort results with explicitly named references. WEIGHT_PATH_SPATIAL_STABILITY.csv contains 200 spatial cases, each compared with its own same-seed full-cohort baseline.
- WEIGHT_PATH_PAIRWISE_COMPARISONS.csv covers all weight pairs within BE0 and BE1. ALL_SPECIFICATION_PAIRWISE_ARI.csv covers all 45 model pairs.
- BE0_BE1_CONSTRUCT_COMPARISON.csv reports the 100 same-weight/seed age contrasts and original-unit profile changes.
- CLASS_INTERPRETATION_ROBUSTNESS.csv and the support-count tables retain exact comparison definitions and counterexamples.
- Raw contingencies, original-unit profiles, training-only matching, minority destination traces and geographic block distributions support the interpretation checks.
- run_records contains ten NPZ/JSON bundles with GEOIDs, labels, scalers, coordinate factors and centers. Four endpoint NPZs are exact copies; their original center-provenance limitations are preserved.
- PREDECLARED_RUN_SPECIFICATION.json and PREDECLARED_DECISION_RULE.md define the experiment before its new fits. Scripts, input-byte verification, tests and preservation records make the package reproducible.

The common cohort contains 2,287 of 2,291 residential tracts. Four unresolved records remain unclassified, without imputation. Exactly 240 new fits were completed and 160 endpoint runs reused. No additional fits, promotion or formal-source changes are proposed.
''')
 print('Decision memo and manuscript proposals written; no promotion',flush=True)
if __name__=='__main__':main()
