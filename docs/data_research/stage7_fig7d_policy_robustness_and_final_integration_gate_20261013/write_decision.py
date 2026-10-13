"""Evidence-bound author recommendations and coordinated migration plan only."""
from analyze_fig7d import COMPARATORS
from common import *


def main():
    e = frame('Q4_VS_NONQ4_EFFECT_SIZES.csv').set_index(['comparator', 'protocol'])
    q = frame('VULNERABILITY_QUARTILE_BURDEN_PROFILES.csv').set_index(['comparator', 'quartile'])
    s = frame('SPATIAL_AND_K3_STRATIFIED_CHECKS.csv')
    b = frame('SPATIAL_COMMON_SUPPORT_STANDARDIZATION.csv')
    m = frame('SPATIAL_DEPENDENCE_DIAGNOSTICS.csv').set_index('measure')
    base = e.loc[('Five_policy_mean', 'R')]
    four = e.loc[('Four_policy_no_Vulnerability', 'R')]
    impact = e.loc[('Impact_first', 'R')]
    contingency = frame('Q4_HIGH_DEFICIT_CONTINGENCY_TABLES.csv').query("comparator == 'Five_policy_mean' and protocol == 'F'")
    comparison = e.reset_index()[['comparator', 'protocol', 'cutoff_hr', 'n_high', 'n_joint', 'population_joint',
                                 'tract_prevalence_difference_pp', 'tract_prevalence_ratio', 'resident_prevalence_difference_pp']]
    common_support = b.loc[b.comparator.eq('Five_policy_mean'), ['grouping', 'weighting', 'common_support_tracts',
        'common_support_population', 'standardized_difference_pp', 'standardized_prevalence_ratio']]
    spatial = s.loc[s.comparator.eq('Five_policy_mean') & s.test.str.startswith('leave_group_out_')]
    spatial_summary = spatial.groupby(['grouping', 'test']).agg(min_difference_pp=('tract_prevalence_difference_pp', 'min'),
        max_difference_pp=('tract_prevalence_difference_pp', 'max'), comparisons=('group', 'size')).reset_index()
    save('SPATIAL_LEAVEOUT_SUMMARY.csv', spatial_summary)
    decision = f"""# RECOMMENDED FIGURE 7D: D3

Use continuous five-policy mean total equivalent service-deficit hours, with the original frozen Q4 extent outlined. Do not use a new threshold in the main panel. Keep D2 as explicitly policy-conditioned supplementary description, and D1 unchanged as a historical reference. This recommendation does not approve formal promotion.

## Exact original intersection

All 94 original eleven-digit GEOIDs and 350,799 frozen residents are reproduced. The cohort remains 2,299 positive-population tracts / 9,066,522 residents, including eight zero-housing tracts. The frozen Q4 count is 579. The original P75 cutoff is {FIXED_P75:.17g} h; direct source-array recomputation differs by less than 1e-10 h. NumPy linear/type-7 quantiles and >= are used. The exact list is VERIFIED_ORIGINAL_94_GEOIDS.csv, not a new ranking.

{profiles_table(contingency[['cell', 'n_tracts', 'frozen_population']])}

Q4 high-deficit prevalence is {100 * base.tract_Q4_prevalence:.4f}%, versus {100 * base.tract_nonQ4_prevalence:.4f}% for non-Q4. The difference is {base.tract_prevalence_difference_pp:.4f} percentage points, prevalence ratio {base.tract_prevalence_ratio:.6f}, descriptive odds ratio {base.tract_odds_ratio:.6f}. Equal-tract marginal independence predicts {base.tract_expected_joint_under_marginal_independence:.4f} intersections; 94 is only {100 * base.tract_observed_to_expected:.2f}% of this benchmark. These calculations contain no spatial significance test.

Resident-weighted prevalence is {100 * base.resident_Q4_prevalence:.4f}% versus {100 * base.resident_nonQ4_prevalence:.4f}%, difference {base.resident_prevalence_difference_pp:.4f} pp, ratio {base.resident_prevalence_ratio:.6f}. These are fractions of frozen residents represented by selected tracts, not actual customers without electricity or people exposed to every natural hazard. Expected represented population under weighted marginal independence is {base.resident_expected_joint_under_marginal_independence:.2f}, not a causal counterfactual.

## Policy and threshold dependence

Removing Vulnerability-first does not reverse the whole-cohort direction: four-policy R-P75 intersection is {int(four.n_joint)} / {int(four.population_joint):,} residents, difference {four.tract_prevalence_difference_pp:.4f} pp and ratio {four.tract_prevalence_ratio:.6f}. Impact-first alone gives {int(impact.n_joint)} / {int(impact.population_joint):,}, difference {impact.tract_prevalence_difference_pp:.4f} pp and ratio {impact.tract_prevalence_ratio:.6f}. Hospital-first's upper-tail difference is much smaller. The magnitude is policy-dependent even when the direction survives.

{profiles_table(comparison)}

Protocol F retains the original numeric P75 cutoff; R recomputes the same cohort's percentile within each comparator. Four-policy intersections are 103 (F) versus 105 (R); Impact is 112 (F) versus 116 (R). F answers an absolute-cutoff question; R answers a relative-rank question. MeanDelta is an additional-burden construct, not total burden: its meaningful quartiles are its own R cutoffs. F applied to MeanDelta is retained only as an explicitly incommensurate audit (no tract reaches the total-burden cutoff), not substantive evidence of absence of logistics burden.

Prespecified P70/P80 results preserve the negative aggregate five- and four-policy direction; magnitudes and memberships change. Four-policy P70 selects 705 rather than 690 due to tied values. Thresholds must not be forced to exact group sizes. Alternative quantile definitions/inclusivity and 3/6/12-digit rounding are separately audited, rather than rounded before classification.

## Baseline, quartile and geographic composition

Five-policy Q4 minus Q1 mean deficit is {q.loc[('Five_policy_mean','Q4'),'mean_hr']-q.loc[('Five_policy_mean','Q1'),'mean_hr']:.4f} h. It decomposes into an Unconstrained difference of {q.loc[('Unconstrained','Q4'),'mean_hr']-q.loc[('Unconstrained','Q1'),'mean_hr']:.4f} h plus a mean constraint-increment difference of {q.loc[('MeanDelta_five','Q4'),'mean_hr']-q.loc[('MeanDelta_five','Q1'),'mean_hr']:.4f} h. Excluding Vulnerability-first weakens but does not remove the mean difference. Q3 and Q4 are not perfectly monotone, and an average difference is not a statement about every tract.

Geographic composition is a major limitation. Within mixed-group 5-km common-support blocks, the standardized difference is slightly positive; at 10 km it is near zero/slightly negative. These calculations cover different subsets (1,075 / 1,723 tracts), use common block weights, and are not causal adjustments or full-cohort replacements.

{profiles_table(common_support)}

The global five-policy burden has descriptive Moran I={m.loc['Five_policy_mean','Moran_I']:.4f}; frozen SOVI I={m.loc['SOVI_SCORE','Moran_I']:.4f}, using symmetric 8NN internal-point support with row-standardization. No IID tests, spatial p-values or hotspot inference are asserted. Global direction after leaving individual geographic blocks out is a descriptive robustness check, not proof that local associations have the same direction.

{profiles_table(spatial_summary)}

K3 C1 contains no high-deficit tract at this cutoff and many Q4 tracts. Of the 94 intersections, 93 are in C3 and one in C2. Within C3 the Q4 high-deficit prevalence is higher, whereas within C2 it is lower. This is a composition-dependent reversal, not independent validation of K3: SOVI and recovery are already fitted coordinates. The K4 38-tract initial-state exception contains no selected high-deficit tract and does not explain the negative association by itself.

## Decision and remaining approval

D3 communicates continuous modeled burden and vulnerability geography without converting a source-/policy-dependent association into a binary priority rule. It remains conditional on the frozen hazard, network, mapping, resources and finite five-policy set, including Vulnerability-first. Equal policy weights are descriptive design weights, not future adoption probabilities, and the arithmetic mean is not a physical average schedule. D2 remains valid descriptive supplementary evidence but is not an unusually high overlap, a significant spatial hotspot, a composite risk score or an intervention priority. Author approval of D3, NCV14/H2/K3 with K4 sensitivity, and the active manuscript path is still required.
"""
    md('FIGURE7D_FINAL_AUTHOR_RECOMMENDATION.md', decision)
    md('FIGURE7D_THREE_OPTION_SCIENTIFIC_COMPARISON.md', """# Three explicit display options

| Option | Definition and support | Advantage | Scientific limitation | Recommendation |
|---|---|---|---|---|
| D1 | Exact frozen legacy sum of percentile ranks of Impact-reference T80, pre-1970 housing share, NRI_RISK_SCORE and FEMA SOVI; 2,291 original residential tracts; original Top10 | Preserves historical panel literally | NRI risk embeds vulnerability/resilience; pre-1970 housing undefined for the eight retained positive-population zero-housing tracts. Adding them/reranking changes the original definition. This is not NCV14 or the new three-RQ construct. D1 has 24 score-N/A records while A-C has only16 clustering-N/A | Preserve as unchanged historical comparison, not primary new panel |
| D2 | Frozen Q4 AND >=P75 five-policy mean total burden, on2299; four category colors | Transparent exact two-condition description | Arbitrary extra cutoff; lower than marginal-independent overlap; strategy/threshold membership sensitivity; global direction changes in geographical/class strata. Not statistical hotspots or repair priorities | Supplementary policy-conditioned description |
| D3 | Continuous five-policy mean total burden with frozen Q4 geographic outlines, on2299 | Actual-unit magnitude, no new percentile dichotomy or composite index; aligned with BU/MeanDelta input meanings | Same finite policy-set and simulated-service limitations, no causal association claim; dense Q4 boundaries need visual care | Primary author-review recommendation |

All three use the exact same saved K3 A-C content and color identities. D1's legacy N/A denominator is stated explicitly on its own panel, never used to re-exclude eight positive-population tracts from K3. The figures do not imply that community classes are statistically independent of their defining recovery/SOVI coordinates.
""")
    # Preserve unrelated prior proposal paragraphs; only revise the unapproved D display and source-exception wording.
    old_results = lp(OUT / 'inputs/RESULTS_PRIOR.md').read_text()
    paragraphs = old_results.split('\n\n')
    results = '\n\n'.join(p for p in paragraphs if not p.startswith('> ') and 'proposed separate co-occurrence screen' not in p)
    results = results.replace('Thirty-four are Q-associated,', 'Thirty-four are Q-associated; the additional four are mainly associated with HAYNES/ALAMITOS,')
    results += f"""\n\nThe continuous burden map and frozen Q4 outlines show that vulnerability and modeled recovery burden are not geographically identical. Across the full positive-population cohort, five-policy mean deficit was {q.loc[('Five_policy_mean','Q4'),'mean_hr']:.2f} h in Q4 and {q.loc[('Five_policy_mean','Q1'),'mean_hr']:.2f} h in Q1. The contrast weakened but remained when Vulnerability-first was omitted ({q.loc[('Four_policy_no_Vulnerability','Q4'),'mean_hr']:.2f} versus {q.loc[('Four_policy_no_Vulnerability','Q1'),'mean_hr']:.2f} h). However, mixed-group geographic-block and within-class descriptions showed different local relationships. The aggregate pattern is therefore interpreted as conditional on network-service geography and the declared restoration-policy set, not as evidence that social vulnerability improves recovery. The threshold-based co-occurrence analysis is reported separately in the supplement and does not define the main map or repair priorities.\n"""
    md('drafts/RESULTS_REPLACEMENT_DRAFT.md', results)
    old_methods = lp(OUT / 'inputs/METHODS_PRIOR.md').read_text()
    methods = '\n\n'.join(p for p in old_methods.split('\n\n') if not p.startswith('> ') and 'proposed hotspot display is separate' not in p)
    methods = methods.replace('chiefly isolates a Q-proxy-driven initial condition', 'chiefly isolates a retained-Core-proxy-linked initial condition, dominated by Q but also including HAYNES/ALAMITOS-linked tracts')
    methods += """\n\nFor the geographic burden display, realization-mean normalized service-deficit integrals were averaged with equal descriptive weights across the five predefined restoration priorities. This mean total deficit equals the Unconstrained mean plus MeanDelta. It is not a simulated average schedule or an expected outcome under a policy-adoption probability distribution. Figure7D displays the continuous deficit in equivalent full-service-deficit hours and outlines the original frozen FEMA SOVI Q4 extent; no additional hazard, vulnerability or burden score is constructed. A supplementary descriptive analysis separately compares original Q4 and non-Q4 using the original five-policy P75 cutoff and comparator-specific percentiles, with predeclared P70/P80, exclusion of Vulnerability-first, original-policy and Unconstrained comparisons. Spatial blocks and a descriptive nearest-neighbor Moran diagnostic characterize geographic dependence; no significant-hotspot or causal inference is made.\n"""
    md('drafts/METHODS_REPLACEMENT_DRAFT.md', methods)
    md('drafts/FIGURE7_CAPTIONS_ALL_OPTIONS.md', """# Shared Figure7 A-C caption

(A) Tract counts and frozen resident population represented by each primary K3 class (1,242/475/582 tracts). (B) Original-unit means for the eight-coordinate NCV14/H2 specification; dashed lines mark the 2,299-tract cohort mean. Population is displayed in persons although log1p population is fitted. Deficits are equivalent full-service-deficit hours over0-480h, not repair makespan or delivered electricity. The natural-hazard coordinate is a researcher-derived California-relative fourteen-hazard screening index based on frozen FEMA v1.19 inputs. (C) Saved K3 memberships, with C1-C3 colors shared with A/B. Sixteen zero-population tracts are gray/unassigned; eight positive-population zero-housing tracts remain classified. The full service domain remains2,315. IDs are specific to the new candidate, not old formal class IDs.

## D3 recommended main-panel suffix

(D) Continuous five-policy mean total modeled service deficit, with outlines delimiting the geographic extent of original frozen SOVI Q4 tracts (579). Internal boundaries between adjacent Q4 tracts are merged for legibility; membership is unchanged. The five predefined priorities are Impact-first, Hospital-first, Degree-first, Betweenness-first and Vulnerability-first. Equal weights define a finite experimental summary, not policy-adoption probabilities or a physical average schedule. The display is not a composite risk score, spatial hotspot significance result or intervention-priority map. Sixteen zero-population tracts are gray on this candidate display, without changing their study-wide service results.

## D2 supplementary comparison suffix

(D) Descriptive, policy-conditioned categories of original frozen Q4 and at-or-aboveP75 five-policy mean deficit. The original cutoff is38.38135467381475h on2,299 eligible tracts, using linear/type7 quantile and >=. Neither:1,239 tracts; Q4 only:485; high deficit only:481; both:94 (350,799 frozen residents). The intersection is smaller than the144.813-tract marginal-independent benchmark. This is not a significant hotspot or repair-priority designation. Policy-specific and threshold sensitivity results are reported separately.

## D1 unchanged historical comparison suffix

(D) Exact archived legacy hotspot score and original Top10 outlines. The score sums original tract percentile ranks of T80, pre-1970 housing share, NRI risk score and SOVI, on the original2,291 residential cohort. Twenty-four records have no legacy score, including eight positive-population zero-housing tracts classified in A-C. This denominator difference is deliberate and shown as legacy-score N/A, not a new typology exclusion. No missing score is fabricated and no original rank or Top10 is recalculated. The historical score is descriptive, not validated repair priority.
""")
    md('drafts/FIGURE_S9_CAPTION_REVIEW.md', """# Supplementary FigureS9. K3 primary and K4 sensitivity evidence

(A/B) Reused weighted WCSS and full-cohort mean silhouette from registered saved NCV14/H2 fits. K4 has the highest mean silhouette(.2444, versus.2337 forK3); K3 is selected provisionally for regional scientific interpretation, not for maximizing silhouette. The WCSS curve is smooth and endpoint-sensitive, with no uniquely sharp elbow. (C) Existing seed, geographic, policy-set and Init-ablation ARI; range bars are descriptive sensitivity ranges, not confidence intervals. Init removal also redistributes remaining RQ1 squared-distance budgets from1/9 to1/6. The four earlier geographic refit blocks are sensitivity checks, not independent external validation. (D) Exact model-specific K3-to-K4 transitions. The38-tract initial-state exception contains34 Q-associated and four HAYNES/ALAMITOS-associated tracts. It is not independently validated electrical resilience. No PCA is fitted or inherited from the former five-class residential workflow. The review-only revision corrects the overly narrow 'Q state' label to 'Initial exception'; numerical diagnostics and class assignments are unchanged.
""")
    prior_supp = lp(OUT / 'inputs/SUPPLEMENTARY_PRIOR.md').read_text()
    supplementary = '\n\n'.join(p for p in prior_supp.split('\n\n') if not p.startswith('> '))
    supplementary += f"""\n\n## Supplemental co-occurrence and geographic composition

The unapproved D2 screen is retained only as a supplementary diagnostic. It exactly reproduces94 tracts /350,799 residents at38.38135467381475h. Q4 high-deficit prevalence is16.23% versus27.97% for non-Q4, PR=.58054, OR=.49924; resident-weighted prevalence is14.62% versus26.46%. Four-policy and Impact-first R-P75 intersections are105 and116. Fixed and recalculated cutoffs answer different questions. No group count is forced under ties. Aggregate negative contrasts persist atP70/P80, but common-support geographic standardization nearly removes or reverses them; common support is partial and this is not causal adjustment. K3 strata also differ in direction and share fitted inputs. Strong spatial dependence precludes interpreting tract counts as IID evidence. No hotspot significance or intervention inference is made.

The mean deficit across five policy-specific means equals BU+MeanDelta within1e-10h. It is not a realizable averaged repair schedule. Vulnerability-first creates a procedural link from original Q4 to one policy outcome; excluding it weakens, but does not eliminate, global contrasts. Other priorities share geographic/network dependencies. Frozen recovery arrays and original quartiles are unchanged.
"""
    md('drafts/SUPPLEMENTARY_NOTES_DRAFT.md', supplementary)
    md('FIGURE7_CAPTION_AND_RESULTS_CONSISTENCY_REVIEW.md', """# Coordinated review-only wording

Recommend D3. The new Results draft removes the94-tract screen paragraph from the main typology result; the count remains explicitly supplemental. Methods and D3 caption use continuous five-policy mean total deficit, frozen Q4 outlines, no added cutoff/risk score. A-C counts, colors, original units, eight coordinates and2299 eligibility are unchanged. S9's statistical curves and saved classifications are unchanged; a real source-identity correction replaces 'Q state' with 'Initial exception' because four of38 are not Q-dependent. The revised caption also discloses smooth/endpoint-sensitive elbow, greater K4 silhouette, weight redistribution and geographic limitations. The old five-class/PCA/2291 caption remains archived, never overwritten here. Current editable manuscript authority is not established by the supplied commit, so its exact future write target requires author confirmation.
""")
    # Exact existing dependencies and proposed versioned destinations. Old frozen data remain archived.
    migration = [
        ('results/stage7/NCV14_H2_K3_2299/feature_schema_and_identity.json', 'CREATE_VERSIONED_AUTHORITY', 'Freeze exact eight-column schema, source SHAs,2299 eligibility,H2 budgets,savedK3/K4 IDs;no legacy schema fallback'),
        ('results/stage7/NCV14_H2_K3_2299/tract_features.csv', 'CREATE_VERSIONED_AUTHORITY', 'Copy verified candidate eight-variable values with exact GEOIDs and frozen population/quartiles'),
        ('results/stage7/NCV14_H2_K3_2299/preprocessing_and_labels.npz', 'CREATE_VERSIONED_AUTHORITY', 'Frozen mean/ddof0SD/sqrtbudgets;K3 primary/K4 sensitivity labels'),
        ('results/stage7/NCV14_H2_K3_2299/standardizer_and_weights.csv', 'CREATE_VERSIONED_AUTHORITY', 'Exact frozen cohort means, population SDs and H2 squared-distance budgets'),
        ('results/stage7/NCV14_H2_K3_2299/K4_sensitivity_membership.csv', 'CREATE_VERSIONED_AUTHORITY', 'Exact saved K4 labels and separate within-model registry; no refit'),
        ('results/stage7/NCV14_H2_K3_2299/cluster_profiles_original_units.csv', 'CREATE_VERSIONED_AUTHORITY', 'Frozen K3 and K4 original-unit means/medians/quantiles with population/quartile/hospital descriptions'),
        ('results/stage7/NCV14_H2_K3_2299/study_domain_geometry.gpkg', 'CREATE_VERSIONED_AUTHORITY', 'Exact prior full 2315 TIGER geometry, no inherited geometry exclusions'),
        ('results/stage7/NCV14_H2_K3_2299/saved_K_and_stability_evidence.csv', 'CREATE_VERSIONED_AUTHORITY', 'Reused elbow/silhouette/seed/policy/geographic/Init evidence, no new selection or fit'),
        ('results/stage7/NCV14_H2_K3_2299/clusters_labels_final.csv', 'CREATE_VERSIONED_AUTHORITY', '2299 saved labels and original-unit descriptors;explicit new model IDs'),
        ('results/stage7/NCV14_H2_K3_2299/stage7_full_domain_tract_status.csv', 'CREATE_VERSIONED_AUTHORITY', '2315 rows;only16 zero-population unassigned;eight zero-housing included'),
        ('results/stage7/NCV14_H2_K3_2299/class_id_registry.csv', 'CREATE_VERSIONED_AUTHORITY', 'K3C1-C3 explicit palette;K4 IDs separately registered'),
        ('results/stage7/NCV14_H2_K3_2299/five_policy_total_deficit.csv', 'CREATE_VERSIONED_AUTHORITY', 'D3 values and original Q4;not score/top10 columns'),
        ('src/la_grid/core/C257H_Project_Main.py', 'TARGETED_ROUTING_ONLY_OR_LEGACY_GUARD', 'Do not rerun legacy11-feature/PCA clustering on default path;explicit opt-in new saved authority loader,orguardlegacy mode. No Stage1-6/GA changes'),
        ('src/la_grid/revision/r1_stage7_harmonized.py', 'VERSION_AWARE_VERIFIER', 'Current hard2315/2291/24 check and residential status reject new cohort;retain legacy verifier,addnew2299/16 identity'),
        ('src/la_grid/revision/run_stage7_sovi_harmonization.py', 'VERSION_AWARE_ROUTING', 'Do not invoke legacy run_stage_7 to recreate new typology;explicitverify/import saved candidate'),
        ('src/la_grid/plotting/Project_Visualizer.py', 'VERSION_AWARE_READERS', 'LegacyPC/profile/SlowVulnerable score readers incompatible;new eight-unitprofiles,D3 values,positive cohort and registry'),
        ('src/la_grid/plotting/Project_Visualizer_expanded.py', 'VERIFY_ROUTING', 'Ensure wrapper reads declared new Stage7 version,not stale expandeddirectory'),
        ('src/la_grid/plotting/render_revised_stage7.py', 'REPLACE_ACTIVE_STAGE7_ROUTING', 'Current verifier/12PC orhotspot panels/TableS8 legacy path must not overwrite new frozencandidate'),
        ('src/la_grid/plotting/make_manuscript_composites.py', 'REPLACE_ACTIVE_PANEL7_INPUTS', 'Legacy prepared hotspot/body paths and0-4Top10 legend replaced by newNCV14/H2/D3 panels'),
        ('src/la_grid/plotting/refine_policy_cluster_presentation.py', 'REMOVE_5_CLASS_REPAINT_FOR_NEW_VERSION', 'Five-color operator assertion and legacy1-5caption replacement fail on3classes;registry-driven new routing'),
        ('src/la_grid/plotting/r1_formal_figures.py', 'VERIFY_STAGE7_RENDER_ROUTING', 'Any Fig07/S09 caller must not import legacy profile/cohort output'),
        ('src/la_grid/plotting/build_revised_result_suite.py', 'VERIFY_COLLECTION_ROUTING', 'Stage7 copied panels/tables and manuscript composite source pointer change only'),
        ('src/la_grid/plotting/render_revised_suite.py', 'VERIFY_COLLECTION_ROUTING', 'Reads harmonized/SOVI PCA/hotspot panels;stop stale generator overwrite of activeStage7'),
        ('src/la_grid/plotting/index_revised_suite.py', 'UPDATE_STAGE7_INDEX', 'New source files/labels/cohort/digests;archived outputs separate'),
        ('src/la_grid/plotting/update_coauthor_figure_index.py', 'UPDATE_STAGE7_INDEX', 'Source manifests/newcandidate generation identity'),
        ('src/la_grid/plotting/render_final_artwork_remediation.py', 'GUARD_OLD_PC_LOADINGS', 'Old Stage7PCA component/loadings art not valid fornewraw8featurefit'),
        ('src/la_grid/plotting/update_framework_figure.py', 'TEXT_CONSISTENCY_CHECK_ONLY', 'Do not redraw RQs;remove any old Stage7mechanism/cohort references ifpresent'),
        ('tests/test_stage7_sovi_harmonization.py', 'PRESERVE_LEGACY_AND_ADD_VERSIONED_TESTS', 'Keep frozen legacy coverage test;addneweligibility/H2/threecolors/label/noimputation assertions'),
        ('.github/workflows/stage7-physical-feature-gate.yml', 'VERSION_AWARE_LIGHTWEIGHT_GATE', 'Do not run physical simulation orrefit;verify source/source-indexfield meanings'),
        ('FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/run_08_stage7_typology.py', 'VERSION_AWARE_RESUME_VALIDATION', 'Current verifier_inventory points tooldharmonized outputs;new explicit approvedidentity'),
        ('FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/README.md', 'UPDATE_ACTIVE_DOCUMENTATION', 'Newsource/cohort/schema/versionedcommands;preservehistoricalinstructions asarchive'),
        ('FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/STAGE8_OUTPUT_HASHES.json', 'UPDATE_APPROVED_MANIFEST_ONLY', 'Onlyafterallnewassets approved;notchanged duringreview'),
        ('FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/STAGE_VALIDATION_MANIFEST.json', 'UPDATE_APPROVED_MANIFEST_ONLY', 'New typology authority,inputs andidentity'),
        ('FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json', 'UPDATE_APPROVED_MANIFEST_ONLY', 'Exact modifiedreader/codehashes,legacyexecutionSHAs retained'),
        ('FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.md', 'UPDATE_ACTIVE_DOCUMENTATION', 'Resume source table points toapprovednew version;noGA/physicalrebuild'),
        ('results/figure_review/Main/Fig07.pdf', 'APPROVED_FIGURE_REPLACEMENT', 'D3reviewplusunchangedA-C'),
        ('results/figure_review/Main/Fig07.png', 'APPROVED_FIGURE_REPLACEMENT', '600dpi preview matchingnewPDF'),
        ('results/figure_review/Supplement/FigS09.pdf', 'APPROVED_FIGURE_REPLACEMENT', 'K3main/K4sens savedstatistics;initialexceptionlabel'),
        ('results/figure_review/Supplement/FigS09.png', 'APPROVED_FIGURE_REPLACEMENT', '600dpi matchingPDF'),
        ('results/figures/Fig07_Community_Typology_and_Hotspots.pdf', 'APPROVED_COLLECTION_SYNC', 'Preserveoldfilenameunlessregistryrenameisapproved;title/captionmustnotclaimhotspots'),
        ('results/figures/Fig07_Community_Typology_and_Hotspots.png', 'APPROVED_COLLECTION_SYNC', 'Exactsameapprovedgraphic'),
        ('results/figures/FigS09_Stage7_Diagnostics.pdf', 'APPROVED_COLLECTION_SYNC', 'ExactsameapprovedS9'),
        ('results/figures/FigS09_Stage7_Diagnostics.png', 'APPROVED_COLLECTION_SYNC', 'ExactsameapprovedS9'),
        ('results/figure_review/Supplement/Stage7_Classification_Robustness.pdf', 'AUTHOR_CONFIRM_NUMBER_THEN_INSTALL', 'Use prior unchanged 03_Classification_Robustness_candidate.pdf; supplement number is not silently assigned'),
        ('results/figure_review/Supplement/Stage7_Classification_Robustness.png', 'AUTHOR_CONFIRM_NUMBER_THEN_INSTALL', 'Matching prior 600dpi preview; preserve old numbered supplementary assets'),
        ('results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md', 'APPROVED_TEXT_REPLACEMENT', 'OnlyF7/S9anddirectlyrelatedsupprobustness text;no unrelatedRQorfigure rewrite'),
        ('results/figure_review/FIGURE_MANIFEST.csv', 'UPDATE_APPROVED_MANIFEST_ONLY', 'Currentfilebytes/source/candidatecommit/generator'),
        ('results/figures/FIGURE_INDEX.csv', 'UPDATE_APPROVED_MANIFEST_ONLY', 'Same source and current scientific labels;no stalehotspottitle'),
        ('results/figure_review/README.md', 'UPDATE_ACTIVE_DOCUMENTATION', 'NewStage7 versionandlinkedassets'),
        ('results/figures/README.md', 'UPDATE_ACTIVE_DOCUMENTATION', 'New source/caption pointers'),
        ('results/figure_review/ALL_MAIN_FIGURES.pdf', 'APPROVED_COLLECTION_REASSEMBLY', 'ReplaceF7pageonly;otherpagesexactbytes/graphicsremain'),
        ('results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf', 'APPROVED_COLLECTION_REASSEMBLY', 'ReplaceS9andapprovedrobustnesspagesonly'),
        ('results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf', 'APPROVED_COLLECTION_REASSEMBLY', 'CoordinatedapprovedF7/S9captionpages'),
        ('AUTHOR_CONFIRMED_CURRENT_MANUSCRIPT.docx', 'UNRESOLVED_TARGET_DO_NOT_WRITE', 'Actualeditablecurrentpath notidentified;author mustconfirm;Methods/Results/captions/supplementnotesreplaceonlyStage7'),
    ]
    migration += [(p, 'ARCHIVE_UNCHANGED', 'Frozen historical data/figures/sourceidentity;never rewrite to pretendnewtypologyranatoldcommit') for p in [
        'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/', 'Formal_Experiment_20260923/Stage 7 Output_expanded/',
        'Formal_Experiment_20260923/FORMAL_STAGE7_INPUT_IDENTITY.json', 'Formal_Experiment_20260923/STAGE7_EXECUTION_IDENTITY.json',
        'provenance/legacy_outputs/stage7/', 'provenance/reviewer_working/Supplement_Rebuild_20260925/',
        'provenance/figure_review_history/', 'docs/data_research/', 'provenance/legacy_outputs/Submission_Package/Manuscript_IJDRR.docx']]
    save('FORMAL_PROMOTION_PATH_REGISTRY.csv', [dict(path=p, planned_action=a, reason=r, execution_authorized=False) for p, a, r in migration])
    md('STAGE7_FORMAL_DEPENDENCY_AND_MIGRATION_AUDIT.md', """# Formal dependency audit: replacing one PDF is insufficient

Exact committed code/caption snapshots and line references are under evidence/ and FORMAL_DEPENDENCY_MATCHES.csv. FORMAL_PROMOTION_PATH_REGISTRY.csv gives planned paths/actions, separates new versioned authority from active readers/artwork and from immutable history. The new source schema is not compatible with the current production reader by merely copying a PDF.

Critical blockers for a future promotion:
1. The legacy verifier requires(2315,2291,24) and residential status. New version requires(2315,2299,16) and positive frozen population; the original verifier must remain valid for its historical authority.
2. The old core run_stage_7 loads housing, CDC population density, NRI risk/building value, constructs old hotspot/PCA coordinates and chooses clusters. Invoking it would not reproduce NCV14/H2/savedK3. A versioned saved-authority loader and explicit routing are required; no silent replacement of oldfit behavior.
3. Project_Visualizer/composite and suite refreshers expect oldPC/loadings, six descriptive profile fields and SlowVulnerable_Hotspot_Score/Top10. D3 must read exact five-policy total deficit and frozenQ4, not invent compatibility score columns.
4. refine_policy_cluster_presentation.py has CLUSTER_OLD/NEW arrays of length5 and asserts all five colors were found. It would fail or mispaint a three-class figure. New registry colors are C1#147f98,C2#d07734,C3#7a5899; K4 sensitivity has a separate registry. Do not relabel old IDs as new IDs.
5. Stage08 resume manifests, code authority, figure manifests/indexes and assembled caption collections must update together afterapproval. Historical execution identities and archives must not be rewritten.
6. The current editable manuscript is not identifiable from the pinned repository: tracked DOCX files are older review/meeting/legacy documents; the previously mentioned Downloads path is absent. No arbitrary archived DOCX is chosen for futurewrite. Author must name the active manuscript andsupplementtargets.

The relevant current formal caption uses five classes/2291 residential tracts and PC5/eigenvalue rules. These statements must be replaced only in the active Stage7 Methods/Results/F7/S9/supplement, not globally in historical audit reports. A new supplementary robustness figure should use the previous candidate package's existing saved maps; placement/numbering needs author approval. Its current candidate source is retained at the prior commit, not regenerated.
""")
    md('CONTROLLED_PROMOTION_AND_ROLLBACK_PLAN.md', """# Future promotion plan; NOT EXECUTED

1. Obtain author approval of exact NCV14/H2/K3 and K4 source hashes, D3, coordinated drafts, the active manuscript/supplement paths and robustness-figure numbering. Record the approved candidate commit and exact files.
2. Recheck `git status` in the actual active worktree. Preserve unrelated staged/untracked work. Create an annotated backup tag or dedicated backup branch and a timestamped patch before changes. Copy every mutable target outside active output directories and hash it. Preserve existing Git/LFS objects and manuscript bytes. Do not delete history.
3. Create a separate promotion branch. Import saved data, preprocessing and IDs into `results/stage7/NCV14_H2_K3_2299/`. Do not refit K-means or recompute quartiles. Keep old Formal_Experiment Stage 7 directories and execution identities intact.
4. Add version-aware readers/verifiers and routing according to the exact registry. Fail on incorrect schema, cohort or source bytes. Never fall back to old PCA/housing/hotspot inputs. Leave Stages 1-6, physical damage, schedules, GA, distributional policy results and all 950 protected files unchanged.
5. Install approved F7/S9/robustness assets and modify only their Stage 7 text. Synchronize active figure copies, manifests, indexes and assembled collections in one coordinated commit. Preserve other numbered pages and data.
6. Run lightweight tests of the 2299/16/8 eligibility counts, 9,066,522 population, eleven-digit IDs, exact feature values, H2 standardizer/budgets, saved K3/K4 labels, registry colors, BU+MeanDelta identity, D3 meaning and absence of old Top10 labels. Check unrelated scientific hashes and absence of formal recomputation. Render every affected page at publication width.
7. Independently check reader imports, resume verification without simulation and clean-clone LFS payloads. Ask the author to review the final diff before merging. No automatic Release or Zenodo action belongs to this task.

Rollback: before merging, abandon only the promotion branch after preserving its changes; never reset unrelated dirty work. After merging, use a scoped `git revert` of the coordinated promotion commit(s). Restore active figure/data/text pointers from the verified backup, and external DOCX/supplement files only from exact timestamped copies. Verify old manifest, source and figure hashes and all 950 protected files. The new versioned candidate may remain archived but must not stay active. Do not force-push, filter history, delete LFS objects or overwrite an unconfirmed manuscript.
""")
    md('AUTHOR_APPROVAL_CHECKLIST.md', """# Approval items

- [ ] Approve the eight-variable FEMA_NCV14_CA_v119/H2 specification and exact 2,299-positive-population cohort, with unchanged frozen quartiles.
- [ ] Approve saved K3 as primary and K4 as sensitivity, with statistical and Init-source limitations.
- [ ] Approve D3 continuous five-policy mean total deficit and frozen Q4 outlines as main F7D. This is not a hotspot or priority score.
- [ ] Retain D2 and the 94-tract screen only as clearly labeled supplementary policy/threshold/geographic diagnostics, or omit them from submission.
- [ ] Preserve D1 as an unchanged historical 2,291-tract score reference, without fabricating missing values.
- [ ] Approve S9's label correction from Q state to initial exception. Its numerical evidence remains unchanged.
- [ ] Approve Stage 7 Methods/Results/F7/S9/supplement drafts as one coordinated replacement, without unrelated paper edits.
- [ ] Identify the exact active editable manuscript and supplement paths, and choose the robustness figure number without overwriting history.
- [ ] Authorize a later, separate formal promotion branch and version-aware code/data/manifest changes. This round does not authorize promotion.
""")
    md('FINAL_INTEGRATION_READINESS_DECISION.md', """# Decision: scientifically approval-ready, formal promotion not executed

RECOMMENDED FIGURE 7D: D3. The original 94 identities are verified. The negative whole-cohort Q4/high-deficit association is not solely a Vulnerability-first effect or threshold artifact. It reflects baseline and additional constraint burdens alongside strong geographic/community-type composition. Within-common-support comparisons nearly remove or reverse it, so a generalized protective-vulnerability claim is not justified.

The NCV14/H2/K3 author-review assets and D3 wording are coordinated. A-C are preserved; S9 requires only the documented initial-exception label correction. No new K fit, physical simulation, policy change or quartile reassignment is performed. Numerical/source/preservation checks and publication-size artwork inspection must pass before Git delivery; their actual records belong to this package.

This is NOT turnkey formal readiness: active production readers still implement legacy 2291/PCA/five-class/hotspot behavior. The exact migration registry and rollback plan identify coordinated changes required after author approval. The current editable manuscript and supplementary robustness numbering remain unresolved author choices; they are not silently guessed. Formal results, manuscript and numbered figures remain unchanged.
""")
    md('README.md', """# Figure7D scientific review and controlled integration gate

Authority: `0c5365cc39e2717e0fab4aa3b5d05b445d427eb6`. Recommend D3 for author review. Read FIGURE7D_FINAL_AUTHOR_RECOMMENDATION.md first, then the readiness decision, approval checklist and exact migration registry. No formal promotion is authorized.

Python 3.12 with the previous diagnostic numpy/pandas/scipy/geopandas/shapely/matplotlib/PyMuPDF/Pillow stack. Run `prepare.py`, `reconstruct_frozen.py`, `analyze_fig7d.py`, `audit_dependencies.py`, `write_decision.py`, `polish_authored_text.py`, `figures.py` and `verify_independent.py` in that order. No fitting or simulation entrypoint is called. Compact frozen station integrals/W and committed source copies support independent core arithmetic. Preparation and source-level integral/summary re-audit still require actual Git LFS objects and manifest-bound local archives. Set `LA_GRID_FROZEN_SOURCE_ROOT` to the exact original archive when needed. Clean-clone core reproduction uses `reproduce_core.py`; it does not re-audit absent original events. Long Windows checkout paths may require `\\\\?\\`-prefixed Python entrypoints; a shorter clean-clone path avoids this OS limitation.

F and R threshold protocols are separate. Population-weighted outputs are frozen residents represented by selected tracts, not delivered power, customer outages or exposure to every hazard. Spatial findings are descriptive, with no IID/spatial p-value or validated-hotspot claim. D1 is the exact legacy reference; D2 is supplementary; D3 is the main candidate. Inspect figures at 7.2-inch publication width. PDFs are vector and PNG previews are 600 dpi. Review status is printed on every new figure.
""")
    dump('FINAL_REVIEW_DECISIONS.json', dict(recommended_Figure7D='D3', D2_status='SUPPLEMENTARY_DESCRIPTIVE_ONLY', D1_status='UNCHANGED_HISTORICAL_REFERENCE',
         original94_reproduced=True, source_authority=AUTH, no_formal_promotion=True, no_new_fits=True,
         author_approval_needed=True, active_manuscript_path_unresolved=True, S9_revision_reason='Replace Q state label:4of38areHAYNES_ALAMITOS ratherthanQ-dependent'))


if __name__ == '__main__':
    main()
