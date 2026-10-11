from controlled_audit import *
def md(name,text):(OUT/name).write_bytes(text.encode('utf-8'))
def main():
 r=pd.read_csv(OUT/'CONTROLLED_MODEL_SUMMARY.csv').set_index('model');metrics=pd.read_csv(OUT/'BUILT_ENV_REDUNDANCY_METRICS.csv');facts=json.loads((OUT/'MEASUREMENT_LIMITATIONS_FACTS.json').read_text());within=pd.read_csv(OUT/'WITHIN_WEIGHT_SPECIFICATION_EFFECTS.csv');weight=pd.read_csv(OUT/'WEIGHT_SCHEME_EFFECTS.csv');dist=pd.read_csv(OUT/'CLUSTER_DISTANCE_CONTRIBUTIONS.csv')
 def m(scope,measure,a,b=None):
  z=metrics.loc[metrics.scope.eq(scope)&metrics.measure.eq(measure)&metrics.feature.eq(a)]
  if b is not None:z=z.loc[z.other_feature.eq(b)]
  assert len(z)==1;return z.value.iloc[0]
 pair=metrics.loc[metrics.scope.isin(['current_2287','original_pilot_actual_values','legacy_2276_current_values'])&metrics.measure.eq('Pearson')&metrics.feature.isin(PHYS)&metrics.other_feature.isin(PHYS),['scope','feature','other_feature','n','value']]
 comparison=r.loc[['BE0','BE1_EQUAL','BE1_FIXED_COORD','BE2_EQUAL','BE3_EQUAL','BE4_EQUAL','BE5_EQUAL','BE6_EQUAL','BE7_ACS_EQUAL','BE8_LOWER_EQUAL','BE8_UPPER_EQUAL','SCAG_TRANSPORT_EQUAL','SCAG_DOMINANT_EQUAL'],['ARI_BE0_same_seed_median','reassigned_median','spatial_ARI_median','spatial_ARI_min','D34_spatial_purity_min']]
 rc=r.loc[['BE0','D_INHERITED','ALR_ONLY_EQUAL','EAL_EQUAL','ALR_ONLY_INHERITED','EAL_INHERITED'],['ARI_BE0_same_seed_median','reassigned_median','spatial_ARI_median','spatial_ARI_min']]
 contributions=dist.loc[dist.model.eq('BE0')].groupby(['domain','feature']).agg(squared_weight=('coordinate_squared_weight','median'),between_class_fraction=('between_class_fraction','median'),variance_explained=('variance_explained_by_partition','median'))
 wtable=weight.groupby(['equal_domain_model','inherited_domain_model']).agg(ARI_median=('ARI','median'),ARI_min=('ARI','min'),reassigned_median=('aligned_reassigned_n','median'))
 within_table=within.groupby(['model','reference_model']).agg(ARI_median=('ARI_vs_same_weight_reference','median'),reassigned_median=('aligned_reassigned_n','median'),spatial_ARI_difference_median=('spatial_ARI_difference_vs_same_weight_reference','median'))
 words=f'''# Built-environment redundancy and scientific-validity decision

## Recommendation

Retain the three coordinates in the **historically qualified, descriptive joint candidate**: classified-parcel land-use mix, observed ground-building coverage, and the pre-1970 share of valid-age 2014 building area. Do not call these a comprehensive, synchronized or independently validated representation of the contemporary built environment. This recommendation does not authorize changing formal labels, the manuscript or existing figures.

| Coordinate | Scientific decision | Required interpretation |
|---|---|---|
| SCAG entropy | KEEP as a primary coordinate | Land-use mixture within classified parcel land, not entire tract land |
| LARIAC6 footprint coverage | KEEP as a primary coordinate | Ground-building coverage of the mixed-vintage outline inventory, not floor-area density |
| LARIAC4 2014 observed-age share | KEEP as a primary coordinate, with explicit historical scope | Observed valid-age building stock of the 2014 inventory, not complete 2020/2022 stock, structural fragility or current building condition |
| ACS residential age | DESCRIPTION/SENSITIVITY ONLY | Housing-unit-weighted residential estimate for 2018-2022; it cannot replace all-use area age without changing the research construct |
| Building-count density | DESCRIPTION ONLY in this decision | Segmentation/centroid-based count intensity; it measures something different from footprint coverage |
| Impervious fraction | NOT ADMITTED as primary | The existing pilot's direct USGS source/version correspondence is still unverified |

The minimum defensible **two-coordinate** physical alternative is entropy + footprint (BE1), if the author decides that historical building age should be outside the primary research construct. It preserves mix and physical coverage but loses age composition. The evidence does not establish that this is scientifically superior: its higher median spatial ARI accompanies a worse lower tail and a small-group matching failure in one prescribed deletion. Do not choose it solely for dimensional parsimony, silhouette or average stability. No contemporaneous all-use replacement with comparable coverage is currently validated.

## Controlled design and actual calculations

The parent is `{PARENT}`. All comparisons use the same 2,287 complete residential GEOIDs, retained in original order, from a 2,291-row master. Four unresolved geometry records remain unclassified and unimputed. B in original hours, Init_Supply, four grid descriptors and SOVI remain identical. Fixed k=4, seeds42-61, n_init=100, max_iter=500, tol=1e-4, Lloyd, scikit-learn1.5.1. No k search, simulations, scheduler, GA, GIS extraction or formal-file replacement was performed.

There are29 distinct model specifications, each20 complete-cohort baselines and20 spatial cases:880 new fits and280 existing runs reused after matrix/sample/hash/settings checks. BE0 and EAL equal-domain spatial results are reused byte-for-byte. Full D/EAL, ACS/no-age and available inherited-bound/allocation labels are reused. Proportional missing-land allocation is a mathematical identity, with only floating-point serialization differences; its two entries are aliases, not additional independent runs. Checkpoint archives retain actual IDs, raw labels, scalers, factors, train masks, and new fitted centers. Reused full-cohort centers are explicitly **label-member means**, because the original algorithm centers were not saved; no baseline is refitted to invent those centers.

Spatial cases reuse the existing20-km blocks and exact20 seed/deletion pairs, comprising17 distinct geographic deletion sets. Each training subset fits its own scaler and predicts the whole common cohort. Spatial ARI compares with that model's same-seed full-cohort baseline. Class matching uses training overlap only, then applies that mapping to all/heldout records. Raw contingency tables are retained so a one-to-one assignment cannot conceal merging. Full feature comparisons provide both frozen BE0-seed42 and same-seed BE0 references. The tables below use **same-seed BE0** for both ARI and reassignment, and each model's own baseline for spatial ARI. Empirical ranges/percentiles are not confidence intervals or classification accuracy.

## Statistical overlap and source interpretation

Current three-feature maximum VIF is {metrics.loc[metrics.scope.eq('physical_3')&metrics.measure.eq('VIF'),'value'].max():.6f}. The actual pilot and current-cohort correlations are:

{pair.to_markdown(index=False,floatfmt='.6f')}

The pilot2276 rows are reproduced from their original saved values. The current legacy2276 subset uses the subsequently validated data version; the current2287 adds11 resolved geometry records and keeps the four unresolved records excluded. The small correlation differences are therefore membership/version differences, not an unreported new variable. VIF does not establish scientific independence or correct sources. Conditional relationships, coverage-stratified correlations and spatial-fivefold polynomial diagnostics are in BUILT_ENV_REDUNDANCY_METRICS.csv. Mild nonlinear overlap exists: age can predict entropy with out-of-block R2 up to {metrics.loc[metrics.scope.eq('spatial_5fold_block_prediction')&metrics.feature.eq('land_use_entropy')&metrics.other_feature.eq('all_use2014_pre1970_area_share'),'value'].max():.3f}; this remains incomplete overlap, not zero dependence or causal evidence. Predicting age from footprint reaches R2 {metrics.loc[metrics.scope.eq('spatial_5fold_block_prediction')&metrics.feature.eq('all_use2014_pre1970_area_share')&metrics.other_feature.eq('building_footprint_coverage'),'value'].max():.3f}. No independent-tract p-values are used to certify validity.

SCAG classified-land coverage median is {100*facts['classified_land_coverage_median_2287']:.3f}% on2287. Entropy is normalized over11 exclusive classified categories. Assigning all unknown land to transport or the observed dominant category is a hypothetical stress test, not recovered land use; proportional assignment preserves proportions. LARIAC6 is a2020 release of cumulative outlines, predominantly older imagery, not a synchronized2020 survey. Geometry measures roof/ground projection, not floor area, structural type or occupancy.

2014 valid-age coverage median is {100*facts['age2014_valid_area_coverage_median_2287']:.3f}% **of original2014 outlines**, versus {100*facts['strict2020_age_transfer_coverage_median_2287']:.3f}% for strict2020 age transfer on the same cohort. Government missing-age area fraction in the saved by-use audit is95.804%; cross-use unions overlap and must not be summed into a county denominator. The lower/upper bounds cover missing ages of2014 outlines, not demolitions/new construction or unobserved later changes. Retaining the historical variable is a construct judgment with these limits, not proof that high conditional coverage validates contemporary age. A more recent residential-only measure is not a general all-use substitute.

## Ablation, weighting and measurement uncertainty

{comparison.to_markdown(floatfmt='.4f')}

Deleting age with physical budget fixed at20% changes a median {r.loc['BE1_EQUAL','reassigned_median']:.0f} tracts; retaining original per-coordinate weights changes {r.loc['BE1_FIXED_COORD','reassigned_median']:.1f}. Deletion and amplification of the remaining coordinates both matter. The fixed-coordinate experiment keeps each retained physical coordinate at0.2/3, leaves all other domains untouched, and reduces the total squared weight; it is not silently renormalized. PHYSICAL_REDISTRIBUTION_EFFECTS.csv directly compares the same surviving coordinates under the two budgets, rather than attributing their combined effect solely to removed information.

ACS substitution changes a median {r.loc['BE7_ACS_EQUAL','reassigned_median']:.0f} tracts and is a change in population/denominator/vintage. Age lower/upper scenarios change {r.loc['BE8_LOWER_EQUAL','reassigned_median']:.0f}/{r.loc['BE8_UPPER_EQUAL','reassigned_median']:.0f} tracts. Equal-domain transport/dominant missing-land scenarios change {r.loc['SCAG_TRANSPORT_EQUAL','reassigned_median']:.0f}/{r.loc['SCAG_DOMINANT_EQUAL','reassigned_median']:.0f}. These tests close the earlier **equal-domain SCAG evidence gap**, while showing residual lower-tail geographic sensitivity. They do not fill missing land or certify a fully observed entropy field.

The original34-member set is audited by membership, not a hard-coded class ID. Under BE0 deletion seed54, only4 target training members remain; all34 original members are in a92-member predicted class, retention100% but purity36.96%. EAL has90 members and37.78% purity. Some age-deleted/inherited specifications do not retain a distinct one-to-one-matched minority class under the same cases. A zero matching purity is a merging/matching failure, not proof that the original tracts vanished; destinations are retained in SMALL_34_GROUP_SENSITIVITY.csv and raw cross-tabs. Median ARI cannot hide this failure. Original-unit profiles, deletion-only shifts, reclassification shifts, common-BE0-coordinate center shifts and ranking reversals are supplied. Small differences and changes involving sparse support must not become stable archetype names or built-environment causation.

## Risk/exposure content versus domain weights

On2287, Pearson r(log1p building stock, ALR)={m('current_2287','Pearson','log1p_NRI_BUILDVALUE','ALR_NPCTL'):.4f}; r(log1p stock,EAL)={m('current_2287','Pearson','log1p_NRI_BUILDVALUE','EAL_SCORE'):.4f}. After controlling for SOVI and log population density, the former is {m('risk_exposure','partial_Pearson','log1p_NRI_BUILDVALUE','ALR_NPCTL'):.4f}, and the latter {m('risk_exposure','partial_Pearson','log1p_NRI_BUILDVALUE','EAL_SCORE'):.4f}. Stock and ALR are related but not interchangeable; EAL has much greater stock overlap. ALR is the published unadjusted, EAL-weighted multi-hazard loss-rate percentile, not a simple EAL/BUILDVALUE ratio, pure seismic hazard or socially adjusted risk. EAL combines loss and exposure and omits separately interpretable economic stock. Keep SOVI independent in all specifications.

{rc.to_markdown(floatfmt='.4f')}

D remains the recommended scientific definition when **economic stock and loss propensity** are both intended domains. ALR-only intentionally omits economic stock and doubles the surviving rate coordinate within the fixed exposure/loss budget. EAL changes that domain into combined expected loss/exposure. Thus ALR-only is not merely a harmless redundancy deletion, and its partition effect cannot be attributed to stock removal alone. Neither alternate is rejected for a lower ARI; they answer different scientific questions. Source-exposure overlap and locally earthquake-dominated multi-hazard loss also preclude claims of statistical/physical independence.

Pure weight changes with identical features are:

{wtable.to_markdown(floatfmt='.4f')}

Within each weight scheme, content-only comparisons are separately supplied in WITHIN_WEIGHT_SPECIFICATION_EFFECTS.csv and WITHIN_WEIGHT_PROFILE_CHANGES.csv. This prevents inherited SCAG/age/risk comparisons against equal-domain BE0 from conflating content and parent-budget effects. At fixedk4, inherited D spatial median/minimum ARI {r.loc['D_INHERITED','spatial_ARI_median']:.4f}/{r.loc['D_INHERITED','spatial_ARI_min']:.4f} differ sharply from equal D. Earlier selected-k5 inherited stability does not validate this fixedk4 model. Equal-five-domain weights are an explicit conceptual balance, not an empirically discovered optimum; the effect of weights is a major substantive limitation.

## Distance contributions and remaining decisions

{contributions.to_markdown(floatfmt='.4f')}

Between-class fractions are contributions to separation of the partition fitted using these same coordinates, not independent validation or causal importance. Low pairwise r, a nonzero fraction, optimizer stability and similarity to BE0 are insufficient selection rules.

1. **Entropy and footprint:** yes, different constructs and low linear/conditional overlap; nonlinear/coverage diagnostics do not collapse them into one indicator.
2. **Age:** a meaningful separate historical-stock coordinate, sufficiently observed for a qualified descriptive role; not independently validated current all-use age. Its temporal and nonrandom missingness limitations must stay explicit.
3. **Two variables:** the smallest reasonable alternative is entropy+footprint, but it is not established as preferable. Removing age sacrifices historical composition and does not resolve the geographic minority-group weakness.
4. **Physical20% after deletion:** defensible only as an author-declared conceptual-domain convention. It raises surviving-coordinate weights from6.67% to10%; it requires scientific approval if adopted, not automatic implementation.
5. **Established versus judgment:** exact coverage, overlap, changed memberships and finite-case spatial results are measured. Whether historical age belongs in the intended construct and whether all five parent domains deserve20% are scientific design judgments. This audit recommends retaining all three with historical scope, D for separately interpretable stock/rate, and keeping equal-domain weighting explicit; it does not freeze a new primary model.

Do not call this a comprehensive built-environment classification, universal geographic taxonomy, predictive validation, causal explanation of recovery, or proof of optimal features/weights. Formal science, formal labels, manuscripts and figures remain untouched.
'''
 md('BUILT_ENV_REDUNDANCY_DECISION.md',words)
 md('MANUSCRIPT_IMPLICATIONS.md',f'''# Manuscript implications for author review

No manuscript edits or new formal classification are made in this audit.

## Methods wording

Describe the physical domain as three historical descriptive coordinates: SCAG2019 classified-parcel land-use entropy; ground-building coverage from the mixed-vintage LARIAC6 outline release; and observed pre-1970 valid-age building-area share in the original2014 LARIAC4 inventory. Do not call any one coordinate a complete built-environment measure, footprint coverage floor-area density, or age an observed2020/2022 stock. Report coverage separately. SOVI and initial modeled service availability remain mandatory.

State that five equal parent-domain budgets are a declared interpretation convention. Standardize within each training cohort; multiply each coordinate by sqrt(domain budget / retained coordinate count). At fixedk4, compare content within each weight scheme and weights with the same content. Holding a domain budget when deleting age is a conscious redistribution, not an absence of weighting changes.

Keep economic building stock and the published unadjusted multi-hazard loss-rate percentile separately interpretable if using D. ALR-only removes stock; EAL combines exposure and expected loss. These are different constructs, not three interchangeable measures of pure hazard.

## Results constraints

Report same-seed paired model contrasts or explicitly frozen seed42 contrasts, without mixing references. Exact counts/ARI in CONTROLLED_MODEL_SUMMARY.csv and the within-weight tables determine the statements. Equal-domain SCAG transport/dominant allocations give median {r.loc['SCAG_TRANSPORT_EQUAL','reassigned_median']:.0f}/{r.loc['SCAG_DOMINANT_EQUAL','reassigned_median']:.0f} reassignments. Age removal gives {r.loc['BE1_EQUAL','reassigned_median']:.0f} with20% redistributed versus {r.loc['BE1_FIXED_COORD','reassigned_median']:.1f} without redistribution. These are source/specification sensitivities, not observed land or age changes and not reclassification error rates.

Report substantial weight dependence at fixedk4; do not inherit a selected-k5 stability claim. Do not claim the four groups are invariant across scientifically different exposure/age specifications. Interpret the34-member class with retention and purity together and disclose sparse-training-support expansion. The published-class labels are not modified here.

## Limitations paragraph draft

The physical indicators describe land-use composition, ground-building coverage and observed historical age rather than all dimensions of the built environment. Classified SCAG land covers only part of tract land; hypothetical missing-land allocations do not recover its actual composition. LARIAC geometry and associated age attributes have mixed vintages, and valid-age completeness pertains to observed2014 outlines rather than the later building stock. Missing construction years differ strongly by building use. Equal-domain weighting is a conceptual convention, and the partitions are sensitive to this choice and to feature definitions. Spatial block deletion supports some broad patterns but reveals reduced specificity of a small group when few training members remain. Joint classification containing recovery outcomes is descriptive and cannot establish that built environment causes recovery differences.

## Remaining author decisions

Confirm whether historical age composition is intended as a primary construct and whether five parent domains should each retain20% total weight. If contemporary all-use age is required, a validated replacement is missing; neither ACS housing age nor sparse strict2020 linkage supplies it. Do not automatically delete age, adopt alternate weights, refit formal labels or promote diagnostic figures.
''')
 md('FIGURE_CAPTIONS.md','''# Diagnostic captions

## Measurement diagnostics

Distributions and relationships of three built-environment measurements on the same2,287 complete residential census tracts. Histograms show tract counts. Points represent tracts; black lines connect within-decile median values as descriptive shape summaries. Entropy is normalized over eleven classified land-use categories; footprint coverage and the2014 observed pre-1970 valid-age area share are percentages of their respective denominators. Pearson correlations are descriptive, and low linear association is not independent source validation. Building age represents observed2014 stock; all figures preserve the four unresolved residential records outside the common analysis cohort.

## Controlled comparisons, page1

Economic-stock/loss representation and domain-weight sensitivity at fixedk4. PanelA compares each20-seed complete-cohort partition with D/equal-domains/seed42; PanelB compares each spatial prediction with its own same-seed full-cohort partition. Colors identify declared parent-domain budgets. The loss-only and EAL models change the interpretation of the economic/loss domain. Dots show prescribed cases; large dots are medians and lines show observed minima/maxima, not confidence intervals. Spatial deletions comprise20 seed/case pairs over17 distinct deletion sets.

## Controlled comparisons, page2

Physical-coordinate ablation. Blue retains20% total physical budget and redistributes it over the surviving coordinates; orange retains6.67% per surviving coordinate, reducing the physical budget while leaving other domains unchanged. PanelA uses the frozen D/equal-domains/seed42 partition reference; PanelB uses each specification's own same-seed complete-cohort labels. ACS age represents housing units in2018-2022, rather than the all-use2014 area-weighted age construct. Case ranges are descriptive and do not establish scientific validity.

## Controlled comparisons, page3

Measurement sensitivity and minority-group specificity. Missing-land allocations and missing-age extremes are hypothetical scenarios, not observed measurements or imputations. PanelA compares partitions with frozen D/equal-domains/seed42. PanelB measures purity after train-only one-to-one class matching for the predicted class associated with the original34-member group; zero purity can arise when that group merges into another class. Original-member destinations and retention are reported separately. Retaining original members does not prevent absorption of other tracts and loss of class specificity.
''')
 md('README.md','''# Controlled Stage7 feature and weight audit

Start with BUILT_ENV_REDUNDANCY_DECISION.md. No formal labels, manuscript material or existing figures are replaced.

Required comparisons are complete: building stock+ALR versus ALR-only versus EAL; inherited/equal parent-domain weights; all-use2014/ACS/no-age; equal-domain SCAG missing-land allocation; BE0-BE8 ablation and nonredistributed deletion controls. All comparisons use2287 complete GEOIDs, k4, seeds42-61 and n_init100. No new k selection or physical-model runs.

The two diagnostic PDFs are actual185-mm vector files with Arial text. Captions are in FIGURE_CAPTIONS.md. CONTROLLED_FEATURE_COMPARISONS has three pages; PNGs preserve each page separately.

BUILT_ENV_ABLATION_RESULTS reports both frozen-seed42 and same-seed BE0 references; default reassignment uses same-seed BE0. WITHIN_WEIGHT_SPECIFICATION_EFFECTS isolates content changes within the same parent budgets. WEIGHT_SCHEME_EFFECTS holds content fixed. PHYSICAL_REDISTRIBUTION_EFFECTS isolates surviving-coordinate amplification. Spatial ARI always uses each specification's own full-cohort baseline, and class matching is trained only on retained members. CSV feature names are provenance keys, not proposed axis wording.

run_records contains29 compressed NPZ archives and JSON metadata, including20 full and20 spatial cases per archive. Reused full centers are label-member means, not original fitted centers. Proportional missing-land scenarios are aliases, not independent observations. No statistical pool of these cases is treated as independent replication.

Reproduce from the parent commit with NumPy1.26.4, pandas2.2.2, scikit-learn1.5.1 and SciPy as recorded in CONTROLLED_COMPARISON_SPECIFICATION.json. Hydrate source LFS files. Run controlled_audit.py --fit --analyze, finish_audit.py, write_decision.py, diagnostic_figures.py and pytest test_controlled_audit.py. Existing input-identical archives are reused; remove only this new package's checkpoints deliberately if a refit is intended. Do not invoke any formal stage runner. Checkpoint counters in FIT_EXECUTION_RECORD describe the original audited execution, not a later cache-only invocation.
''')
 save('WITHIN_WEIGHT_EFFECT_SUMMARY.csv',within_table.reset_index())
 print('DECISION AND IMPLICATIONS WRITTEN',flush=True)
if __name__=='__main__':main()
