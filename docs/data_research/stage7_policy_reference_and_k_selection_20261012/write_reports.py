"""Evidence-bound decision reports, not manuscript changes or formal promotion."""
from common import *


def table(df,decimals=4):
    return df.round(decimals).to_markdown(index=False)


def main():
    e=frame('K_SELECTION_EVIDENCE_MATRIX.csv')
    pref=frame('ELBOW_SILHOUETTE_PREFERENCE_SUMMARY.csv')
    impact=e.loc[e.policy.eq('impact-first')&e.specification.eq('A')&e.scaling.eq('policy_cohort')]
    policies=pref.loc[pref.specification.eq('A')&pref.scaling.eq('policy_cohort')]
    fixedpref=pref.loc[pref.specification.eq('A')&pref.scaling.eq('fixed_impact')]
    pair=frame('POLICY_REFERENCE_PAIRWISE_COMPARISONS.csv')
    c=frame('POLICY_CONDITIONAL_MEMBERSHIP_COMPARISONS.csv')
    qa=json.loads(lp(OUT/'POLICY_PAIRING_QA.json').read_text())
    bcompare=pair.loc[pair.policy_a.eq('impact-first')&pair.variable.eq('B_480_hr')]
    comparison=c.loc[c.comparison.eq('policy')&c.policy_a.eq('impact-first')&c.specification.eq('A')&c.scaling.eq('policy_cohort')&c.k.isin([3,4,5])]
    comparative=comparison.groupby(['policy_b','k']).agg(median_ARI=('ARI','median'),median_reassigned_tracts=('aligned_changed_tracts','median'),median_reassigned_population_share=('aligned_changed_population_share','median')).reset_index()
    aggregates=pd.DataFrame([{k:v[k] for k in ['policy','population_burden_hr','Q4_burden_hr','hospital_burden_hr']} for v in qa['policies']])
    md('IMPACT_FIRST_REFERENCE_DECISION.md',f'''# Restoration-reference scientific decision
AUTHOR REVIEW - NOT FORMAL STAGE 7

## Why Impact-first was used

The prior three-RQ audit declared Impact-first / C57_D1 as its operational reference. It inherited the frozen direct-community recovery input; exact integral SHA256 equality confirms that these are identical in this experiment. It was a population-impact-oriented incumbent reference, not a demonstrated policy-invariant community classification. Spectral Grid_Impact is not its population-impact task-order score.

## Source-complete alternatives

All six scheduled policies pass 1,000-realization matching and exact-event/W/aggregate checks. Vulnerability-first uses the independently frozen equity-amendment archive; damage, durations, graph/source, crew/travel, mapping, gate and horizon match. No missing policy is substituted with an aggregate-derived spatial pattern. The event/integral files remain external local archive dependencies; this package retains their hashes and the complete derived tract metrics.

Frozen aggregate deficits (hours; population-weighted regional and Q4 means; hospital-linked mean is the original tract-group definition):

{table(aggregates)}

These values show why the aggregate optimum is not a complete reference-policy justification: Vulnerability-first reduces Q4 mean deficit relative to Impact-first while increasing the regional mean. Hospital location is not a measure of every resident's electricity-dependent medical need. These are frozen downstream descriptors, not clustering coordinates or independent validation.

## The policy premise matters spatially

Alternative-minus-Impact comparisons on exactly 2,299 positive-population tracts:

{table(bcompare[['policy_b','pearson','spearman','p90_abs_difference_hr','max_abs_difference_hr','abs_gt_5hr_tracts','abs_gt_5hr_population']])}

Matched seed median memberships under policy-specific scaling:

{table(comparative)}

ARI and Hungarian display alignment answer different questions. Reassignment counts maximize unweighted tract overlap; they do not establish population-optimal class correspondence. The full pairwise/scaling/ablation results and class-level Q4 overlaps are retained. Broad groups shift materially; their policy-independence is not established. Shared RQ1/RQ3 values do not prevent a different RQ2 benchmark from changing class boundaries.

## Recommendation for author approval

**Option 1 is defensible:** keep Impact-first if the typology is explicitly 'communities under the population-impact-oriented operational benchmark'. Do not call it a neutral underlying community typology. Its low regional aggregate burden alone is not the reason to retain it.

**Option 2 is an objective change:** Hospital-first is a critical-service benchmark; Degree/Betweenness are structural benchmarks. None is intrinsically more scientifically correct without a declared operational question. Vulnerability-first builds its schedule from frozen Q4, so subsequent Q4 concentration is partly policy-induced and must not be presented as independently discovered social inequity.

**Option 3 is not achieved by the present fits:** the policy-robust interpretation is not justified for the full membership. No average-policy trajectory is constructed. A future explicitly defined multi-policy construct would need separate authorization; it is not a physical schedule and is outside this task.

Keep the frozen reference for a conditional analysis, report policy sensitivity prominently, and obtain author approval of that conditional scope before promotion.
''')
    elbow=frame('ELBOW_INERTIA_BY_K.csv')
    ei=elbow.loc[elbow.policy.eq('impact-first')&elbow.specification.eq('A')&elbow.scaling.eq('policy_cohort')]
    md('K_SELECTION_STATISTICAL_EVIDENCE.md',f'''# Statistical and robustness evidence for K
AUTHOR REVIEW - NOT FORMAL STAGE 7

## Registered analysis

Common 2,299-tract positive-frozen-population cohort; six paired policies; seven-variable A and registered six-variable minus-Init. K=1 inertia, K=2-8 partitions; five fixed seeds (42-46), k-means++, n_init=50, Lloyd, max_iter=500, tol=1e-4. Standardization uses cohort mean/population SD and square-root squared-distance budgets. All silhouettes use the full 2,299 observations and weighted Euclidean distances. 960 individual fit records include 80 exact aliases for Impact-first's identical scaling rules: 880 distinct fits, plus 672 spatial training perturbation fits. All labels and per-tract silhouettes are saved.

The primary rule is per-policy scaling; a separate fixed Impact-first scaler test keeps the affine metric fixed. Its fixed coefficients still follow the declared budgets, but policies with larger RQ2 variance contribute more realized distance under that scaler. Therefore its WCSS/silhouette values cannot be read as evidence that a policy/scaler is scientifically better. All source data and RQ1/RQ3 coordinates remain fixed.

## Elbow

The normalized endpoint-chord diagnostic uses g(K)=(I1-IK)/(I1-I8)-(K-1)/7. Its maximum is a reproducible bend candidate, not an automatic selection or a significance test. It depends on the registered endpoint range. The curve is smooth; there is no sharply separated universal elbow.

Impact-first A:

{table(ei[['k','mean_WCSS','relative_reduction_from_previous','fraction_K1_inertia_removed','chord_gap']])}

K4 has the largest chord gap (0.18984), but K3 is almost equal (0.18853); a gap difference of only about 0.00131 does not sharply establish K4. K4->5 still reduces WCSS by 11.88%. The second-stage K5->6 reduction is 12.69%, so the curve does not justify claiming a definitive plateau at K4.

## Silhouette and disagreement

Policy-specific primary A preferences:

{table(policies[['policy','endpoint_chord_elbow_candidate','maximum_mean_silhouette_k','maximum_mean_silhouette','elbow_and_silhouette_agree']])}

Fixed Impact-first scaling:

{table(fixedpref[['policy','endpoint_chord_elbow_candidate','maximum_mean_silhouette_k','maximum_mean_silhouette']])}

For Impact-first, silhouette favors K5 (0.28294), not K3 (0.24972) or K4 (0.26831). These are modest separations, not evidence of natural universally separated types. Elbow prioritizes diminishing total distance reduction; silhouette favors compactness and nearest competing-class separation. Sparse initial-state isolation, skewed logistics burdens and policy-specific covariance can make their preferences differ. The reference/scaler choice changes both preferences.

## Impact-first transparent evidence matrix

{table(impact[['k','silhouette_mean','negative_fraction_mean','seed_ARI_min','spatial_full_ARI_min','spatial_full_ARI_median','policy_pair_ARI_median','min_class_tracts']])}

The complete matrix includes every policy, specification, scaler and K2-8. Spatial testing uses the same frozen TIGER internal-point UTM quadrants, all tracts retained for prediction, seed42, and scaler refitting only on training tracts for the policy-cohort rule. Four coarse leave-out tests are sensitivity checks, not independent geographic validation or spatial bootstrap confidence intervals. Fixed-scaler tests intentionally retain the full Impact scaler. Geographic source points are consistent for all 2,299 tracts; no old geometry exclusions are inherited.

## Scientific readings of K2-8 under Impact-first

| K | Scientific reading and limitation |
|---|---|
| 2 | Broad lower/higher burden contrast; strong coarse spatial agreement, but merges the high-logistics-burden group and heterogeneous structural/vulnerability patterns. One class has many negative silhouettes. Too coarse for the requested joint interpretation. |
| 3 | Parsimonious majority high-SOVI/lower-deficit class, structurally higher-impact/lower-SOVI class, and high-extra-logistics-deficit class. Useful coarse operational summary; not the statistical optimum and does not expose the extreme spectral-impact class separately. |
| 4 | Mostly extracts the 34-tract Q-dependent initial-state group from K3. Weak elbow advantage; a large heterogeneous class still has poor silhouette. Its extra type is conditional on a Core proxy and strong standardization leverage. |
| 5 | Adds a substantially high-spectral-impact class while separating low-SOVI tracts from the high-SOVI majority; retains the high-logistics class and Q rare state. Highest Impact silhouette, strong initialization stability. Spatial and policy memberships remain conditional. |
| 6 | Further subdivisions include a 12-tract extreme class; five-seed minimum ARI falls to 0.638. No overall silhouette improvement over K5. Does not justify a primary six-type selection. |
| 7 | More subdivisions, lower silhouette, a 12-tract class and weakest tested Impact spatial minimum (0.376). No demonstrated added joint-RQ construct. |
| 8 | More finely partitioned groups and improved coarse spatial agreement versus K7, but silhouette remains lower than K5 and a 12-tract class remains. No new scientific construct requires these extra subdivisions. |

Class means/medians/P10/P90, represented population and all frozen Q1-Q4 compositions are supplied for every primary K and policy. These are descriptions of inputs/shared frozen outputs, not independent validation. No formal class IDs or old manuscript narrative are acceptance criteria.
''')
    init=frame('INIT_RARE_GROUP_SILHOUETTE_COMPOSITION.csv')
    rare=init.loc[init.policy.eq('impact-first')&init.scaling.eq('policy_cohort')&init.seed.eq(42)&init.k.isin([4,5])]
    minus=pref.loc[pref.specification.eq('A-minus-Init')&pref.scaling.eq('policy_cohort')]
    md('INIT_SUPPLY_K_SENSITIVITY.md',f'''# Initial-state sensitivity within K selection
AUTHOR REVIEW - NOT FORMAL STAGE 7

Init_Supply is retained in the primary A. On 2,299 tracts, 1,533 exact zeros (66.6812%) and the 23 largest observations account for 62.4799% of its original variance. Standardization places the maximum near +9.73 SD. This is real frozen modeled information, but a sparse fractional service state, not observed electrical resilience.

The original 34 GEOIDs are kept fixed. Their previously authenticated mechanism is strong W dependence on station 308581 (STATION Q), a retained Core-source proxy. Q contributes 97.1891% of their aggregate initial modeled availability, which averages only 1.8153%. Its 40/1,000 threshold-eligible initial samples are source-qualified by that role; each rare tract's sample median availability is zero. This is not independent generation, feeder-service or power-flow evidence. The original physical audit is referenced, not regenerated.

Across policies, the small state recurs at K4-5, sometimes with 1-4 extra members; Vulnerability-first and Random already isolate a 36/38-tract state at K3. Thus sparse-state extraction partly explains why a policy can favor a different K. Every original rare member's policy/sample initial state is identical, but which other tracts join its class depends on recovery inputs and scaling.

Impact-first rare-class influence:

{table(rare[['k','rare_class_n','rare_class_mean_silhouette','nonrare_mean_silhouette','all_mean_silhouette','rare_composition_effect_on_mean','centroid_Init_fraction']])}

About 89.11% of its centroid separation comes from Init, but its 34 members are only 1.48% of tracts / 1.369% of residents. Its effect on the *overall mean* silhouette is only around 0.005, so the K5 maximum cannot be attributed solely to giving a very small class a high silhouette. The nonrare mean still supports substantive distinctions. However, extracting that rare state consumes a class and changes the remaining partition; the composition calculation does not isolate that whole optimization effect.

Minus-Init preferences under policy-specific scaling:

{table(minus[['policy','endpoint_chord_elbow_candidate','maximum_mean_silhouette_k','maximum_mean_silhouette']])}

Most minus-Init policies favor K3 silhouette (Random favors K2). The small Q state no longer forms a high-purity independent class under these registered alternatives; membership is distributed according to other features. The effect includes both deleting the initial-state construct and increasing Grid_Impact/HHI budgets from 1/9 to 1/6. INIT_ALGEBRAIC_DISTANCE_DIAGNOSTICS.csv holds the original partitions fixed: remove Init's squared centroid distance, then separately add 50% of Impact/HHI squared distances. This distinguishes presence from reallocation algebraically without fitting an unauthorized alternative model. No clipping, tail trimming, zero replacement, winsorization or jitter was performed.

Retain Init only with the rare-state/Core-proxy interpretation and ablation caveat. A statistical preference for K3 after deletion is not authorization to drop this scientifically distinct initial-disruption coordinate. Four-quadrant holdouts show that rare precision can fail even when all rare observations remain eligible; seed stability alone is insufficient.
''')
    profiles=frame('CLUSTER_ORIGINAL_UNIT_PROFILES.csv')
    texts=[]
    for policy in POLICIES:
        for k in [3,4,5]:
            p=profiles.loc[profiles.policy.eq(policy)&profiles.specification.eq('A')&profiles.scaling.eq('policy_cohort')&profiles.k.eq(k)]
            wide=p.pivot(index='diagnostic_cluster',columns='variable',values='mean')[['Init_Supply','Grid_Impact','Redundancy_HHI','B_480_hr','Delta_B_logistics','SOVI_SCORE','Population']]
            counts=p.drop_duplicates('diagnostic_cluster').set_index('diagnostic_cluster')[['n_tracts','population_share']]
            joined=counts.join(wide).reset_index()
            joined['Init_Supply_percent']=joined.pop('Init_Supply')*100
            texts.append(f'## {policy}, K={k}\n\n'+table(joined))
    md('K3_K4_K5_POLICY_ORIGINAL_UNIT_PROFILE_TABLES.md','''# Original-unit policy profiles
AUTHOR REVIEW - NOT FORMAL STAGE 7

Seed42, primary A, policy-cohort scaling. All diagnostic IDs are model-specific; means are shown here, complete medians/P10/P90/ranges in the CSV. Compare high/low to the retained same-cohort reference, not an arbitrary universal cutoff. Init is a percentage; B/Delta are hours; SOVI is 0-100; Population is persons. Impact is W-weighted relative spectral connectivity loss; HHI is sum W squared. Population share is a fraction of 9,066,522 frozen residents. These input profiles are not independent validation.

'''+ '\n\n'.join(texts))
    md('FINAL_POLICY_AND_K_AUTHOR_DECISION.md',f'''# Final policy and K decision for author review
AUTHOR REVIEW - NOT FORMAL STAGE 7

## Direct answers

1. **Why previously Impact-first?** It was a declared population-impact-oriented operational benchmark inherited from the byte-identical direct-community frozen recovery reference. No earlier completed policy-reference/K-selection study established it as universally representative.
2. **Still defensible? Yes, conditionally.** Retain it if the intended question is community types under that incumbent operational priority. Do not characterize it as an intrinsic or policy-neutral typology; do not justify it solely by lowest regional mean deficit. Vulnerability-first improves frozen Q4 outcomes but introduces deliberate Q4 policy targeting, not independent discovery.
3. **How much change under other policies? Material.** Impact-versus-alternative P90 absolute tract B differences are 6.58-15.41 h. A/K5 policy-cohort median ARIs range 0.434-0.709; at K3 they range 0.135-0.502. Fixed reference scaling does not remove the dependence (K5 ARI as low as 0.060 for Random). Both operational assumptions and standardization matter. No policy-robust full membership is demonstrated.
4. **Elbow supports which K?** Impact-first's reproducible endpoint-chord bend candidate is K4, but K3 is nearly tied and the curve lacks a sharp elbow. Other policies/scalers produce K2 or K3 candidates. Do not report K4 as a uniquely proven elbow optimum.
5. **Silhouette supports which K?** Impact-first A favors K5, mean 0.28294 across five seeds, versus 0.24972 at K3 and 0.26831 at K4. Hospital-first also favors K5 under policy scaling; Degree/Betweenness favor K2, Vulnerability/Random K3. Fixed scaling changes these preferences. There is no universal K across restoration references.
6. **Seed/spatial/policy tests?** Impact K3/K4/K5 seed-minimum ARI=1.000/0.990/0.994, but four spatial leave-outs have median ARI=0.705/0.728/0.701 and minima=0.597/0.616/0.516. Policy sensitivity is larger than initialization uncertainty. K6 has substantial initialization instability (minimum ARI=0.638). Geographic tests are coarse perturbations, not external validation.
7. **K3, K4, K5 or another?** **If Impact-first and the initial-state construct are retained, recommend A/K5 as the leading conditional candidate**, not an approved formal model. Its silhouette, fewer negative silhouettes (6.79% versus 10.70% K3 and 13.56% K4), seed stability and interpretable structural split give more complete evidence than the previous narrative-led K3 preference. K3 remains a defensible parsimonious summary, with less explicit structural/vulnerability separation. K4 largely adds the Q-proxy rare state and lacks a compelling advantage over both. K2 is too coarse for joint interpretation; K6-8 are not justified by added constructs. K5 has no universal or spatially robust superiority; do not force this recommendation if the author wants a policy-robust rather than operationally conditional typology.
8. **Meaningful differences across the RQs? Yes, conditionally at K5.** The high-SOVI majority (1,334 tracts, 62.50% of residents) has mean SOVI=82.18 and B=32.18 h; a lower-SOVI class (558, 21.00%) has SOVI=36.58 and B=35.48 h; a high-spectral-impact class (225, 8.72%) has mean Impact=0.7909, B=36.76 h and SOVI=53.66; the high-additional-logistics class (148, 6.42%) has Delta=12.00 h and B=41.46 h. The rare Q-dependent class (34, 1.37%) has mean initial availability 1.815%, not high absolute service. Not every class is extreme in every RQ, and these are not five independent recovery regimes. Detailed input distributions and frozen Q1-Q4 compositions remain descriptive, not independent tests of the model.
9. **What must the author approve?** The operational-reference objective (Impact-first conditional versus a separately designed policy-robust analysis), per-policy scaling as the primary metric with fixed-scaler sensitivity, retaining Init with Core-proxy/rare-state caveats, and conditional K5 versus coarse K3. Only then explicitly authorize formal Stage7 replacement and any subsequent numbered-figure/manuscript changes. No such promotion has occurred here.

## Source and inference limitations

All six policies pass full 1,000-sample pairing and exact-event service-integral checks. The original raw event/integral archives are local manifest-bound dependencies and not promised by a clean Git clone. Derived matrices/metrics and all fit labels/silhouettes are committed for diagnostic reproduction. Frozen population values are confirmed, but direct upstream Census release/batch identity remains unresolved as in the prior audit. Geographic support uses official internal points, not independently verified community boundaries. STATION Q remains a retained source proxy, not a verified generation/capacity or power-flow result. The 2pc50 field is a probabilistic ground-motion level, not a unique rupture or integrated social risk measure. No new physical simulations, policy schedules, quartiles, formal labels or figures were generated.

## Reading order

- POLICY_REFERENCE_SOURCE_AND_PAIRING_QA.md and POLICY_PAIRING_QA.json: physical/data comparability.
- IMPACT_FIRST_REFERENCE_DECISION.md: policy premise and spatial changes.
- K_SELECTION_STATISTICAL_EVIDENCE.md and K_SELECTION_EVIDENCE_MATRIX.csv: all K2-8, seed/scaler/spatial evidence.
- INIT_SUPPLY_K_SENSITIVITY.md: rare initial-state influence and registered ablation.
- K3_K4_K5_POLICY_ORIGINAL_UNIT_PROFILE_TABLES.md: all policies in original units.
- figures/: six vector PDFs and high-resolution previews, all for author review only.
''')
    md('README.md','''# Stage 7 policy-reference and K-selection diagnostics
AUTHOR REVIEW - NOT FORMAL STAGE 7

Start: 66d16d61b13c05785f58795ef9d13ba82ece472e. Read FINAL_POLICY_AND_K_AUTHOR_DECISION.md first. This isolated package changes no formal scientific outputs.

Python 3.12; see requirements-diagnostics.txt. Set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS and MKL_NUM_THREADS to 1 for deterministic registered fits. Run from this package:

```powershell
python audit_policies.py
python fit_registered.py
python build_evidence.py
python write_reports.py
python make_figures.py
python verify_independent.py
python verify_package.py
```

audit_policies.py requires the original read-only manifest-bound Formal_Experiment_20260923 archive. Set LA_GRID_FROZEN_SOURCE_ROOT to its checkout path; the default only records the local reference location. The preceding audit's verified Sources reader resolves commit/LFS-bound files from that checkout, sibling audit worktrees or the common LFS object cache. It never imports/runs physical model stages. Clean-clone post-processing can instead begin from the committed VERIFIED_FIXED_FEATURES_2315.csv and POLICY_REFERENCE_TRACT_METRICS.csv (git lfs pull first); fit_registered.py additionally verifies the preceding rare-ID, label and geographic source tables. Supply a cache/checkout with those actual LFS bytes. Full preservation/source tests require the protected scientific archive.

REGISTERED_ANALYSIS.json predeclares settings; all 960 fit records, full labels and silhouettes, 672 spatial checks and scaler matrices are retained. Two scalers are not scientifically equivalent. No unregistered feature search or weight optimization is performed. Generated content is confined to this package. The package's default external path is an operational archive locator, not an input substitution; no formal data are modified.

pdf_review/ is an ignored rendering scratch area; figures/ contains vector PDFs and 600-dpi PNGs. VISUAL_QA.json records actual publication-size review. All preceding diagnostic packages and 950 protected scientific files are independently hash-checked. Git delivery is restricted to this package; no merge, release or formal Stage7 promotion is authorized.
''')
    md('requirements-diagnostics.txt','''numpy==1.26.4
pandas==2.2.2
scipy==1.11.4
scikit-learn==1.5.1
matplotlib==3.9.2
PyMuPDF==1.28.0
pyarrow==16.1.0
tabulate==0.9.0
requests==2.32.3
''')
    print('Scientific decision reports generated.',flush=True)


if __name__=='__main__':main()
