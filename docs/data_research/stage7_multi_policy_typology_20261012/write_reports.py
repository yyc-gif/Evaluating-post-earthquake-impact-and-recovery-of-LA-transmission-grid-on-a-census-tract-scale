"""Evidence-bounded author decision memos, without changing the manuscript."""
from common import *

WARN='AUTHOR REVIEW \u2014 NOT FORMAL STAGE 7'


def table(df): return df.fillna('not applicable').to_markdown(index=False,floatfmt='.4f')


def report(name,title,text):
    # Normalize prose spacing without changing variable IDs, source paths or tables.
    replacements={'same1,000':'same 1,000','from1/6':'from 1/6','to1/9':'to 1/9',
        'contributes32.64':'contributes 32.64','Hospital19.43':'Hospital 19.43','Betweenness18.49':'Betweenness 18.49',
        'Vulnerability15.84':'Vulnerability 15.84','Impact13.60':'Impact 13.60','atK5':'at K5','a12-tract':'a 12-tract',
        'The34':'The 34','enlarged37-38':'enlarged 37-38','only1.815':'only 1.815','exact34':'exact 34',
        'is7.734h':'is 7.734 h','broadP2':'broad P2','focusedP3':'focused P3','than1/6':'than 1/6',
        'from1/9':'from 1/9','to1/6':'to 1/6','all34':'all 34','to43':'to 43','purity79.1':'purity 79.1',
        'at least0.8':'at least 0.8','tracts/K':'tracts/K','represents1,235tracts':'represents 1,235 tracts',
        'and57.18':'and 57.18','baseline30.06h':'baseline 30.06 h','added1.75h':'added 1.75 h','SOVI78.92':'SOVI 78.92',
        'has428tracts/18.70':'has 428 tracts/18.70','baseline27.80h':'baseline 27.80 h','added7.10h':'added 7.10 h','SOVI48.31':'SOVI 48.31',
        'has636tracts/24.12':'has 636 tracts/24.12','baseline37.20h':'baseline 37.20 h','added3.97h':'added 3.97 h',
        'impact0.308':'impact 0.308','SOVI54.65':'SOVI 54.65','the38-tract':'the 38-tract','the1,223-tract':'the 1,223-tract',
        'the248-tract':'the 248-tract','mean0.743':'mean 0.743','contains790tracts':'contains 790 tracts','added6.14h':'added 6.14 h',
        'SD4.44h':'SD 4.44 h','are62.19':'are 62.19','means73.97,51.97,59.72':'means 73.97, 51.97, 59.72',
        'only6.45':'only 6.45','atK4':'at K4','versus18.18':'versus 18.18','forP2':'for P2','for40.78':'for 40.78',
        'inP3':'in P3','contains12tracts':'contains 12 tracts','representing754people':'representing 754 people',
        'yields12-tract':'yields 12-tract','Python3.12':'Python 3.12','NumPy1.26.4':'NumPy 1.26.4',
        'pandas2.2.2':'pandas 2.2.2','SciPy1.11.4':'SciPy 1.11.4','scikit-learn1.5.1':'scikit-learn 1.5.1',
        'Matplotlib3.9.2':'Matplotlib 3.9.2','PyMuPDF1.28.0':'PyMuPDF 1.28.0','with600dpi':'with 600 dpi'}
    for a,b in replacements.items():text=text.replace(a,b)
    md(name,'# '+title+'\n\n'+WARN+'\n\n'+text)


def main():
    qa=json.loads(lp(OUT/'POLICY_ENSEMBLE_QA.json').read_text())
    independent=json.loads(lp(OUT/'INDEPENDENT_QA_RESULTS.json').read_text()); assert independent['status']=='PASS'
    d=dataset(); ev=frame('K_SCIENTIFIC_EVIDENCE_MATRIX.csv'); prefs=frame('K_DIAGNOSTIC_PREFERENCES.csv')
    information=frame('POLICY_VARIABILITY_INFORMATION_AUDIT.csv'); associations=frame('SAME_COHORT_PAIRWISE_ASSOCIATIONS.csv')
    cir=frame('VULNERABILITY_FIRST_INFLUENCE_NUMERICS.csv'); influence=frame('POLICY_VARIANCE_INFLUENCE_SUMMARY.csv')
    feature_sens=frame('POLICY_SET_FEATURE_SENSITIVITY_SUMMARY.csv'); cmp=frame('POLICY_SET_CLUSTER_STABILITY.csv')
    profiles=frame('CLUSTER_ORIGINAL_UNIT_PROFILES.csv'); groups=frame('CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv')
    contribution=frame('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv'); rare=frame('RARE_Q_GROUP_MEMBERSHIP_AUDIT.csv')
    fits=frame('A_VS_P2_VS_P3_CLUSTERING_RESULTS.csv'); spatial=frame('SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv')
    source=sources(); rid=frozen(source,INTERPRETATION+'THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv').index
    report('MULTIPOLICY_FEATURE_DEFINITIONS.md','Multi-policy definitions and registered design',f'''
## Frozen condition and cohort
2pc50; C57_D1 (57 crews, restoration-duration multiplier 1); M1_UTILITY_003; G1_BASELINE_050 (functionality threshold 0.5 with retained Core source connectivity); horizon 480 h; 1,000 matched evaluation realizations. The clustering cohort is all 2,299 positive frozen population tracts, including eight with zero conventional housing units. Only 16 zero-population GEOIDs are excluded here; they remain in all existing 2,315-tract system outputs. No geometry exclusions or imputation. Population and frozen FEMA NRI v1.19 SOVI quartiles are unchanged.

2pc50 denotes 2% ground-motion exceedance probability in 50 years, approximately 2,475-year mean return period. It is not one earthquake rupture, ASCE 41 BSE-2E, a community risk score, or a station damage-state probability. The source identity and bounded vintage caveats remain those verified in the preceding hazard audit.

## Recovery quantities
For tract i, physical realization m and policy p: B_i,p,m = integral_0^480 [1 - S_i,p,m(t)] dt. Availability is the existing normalized source-gated tract service proxy, not power flow. Integrals use the archived exact piecewise-constant event convention. B_i,p = mean_m B_i,p,m; B_i,U = mean_m B_i,U,m; Delta_i,p = mean_m(B_i,p,m - B_i,U,m). Thus B_i,p = B_i,U + Delta_i,p. Units are equivalent full-service-deficit hours, not a unitless fraction divided by 480.

Main ensemble: Impact-first, Hospital-first, Degree-first, Betweenness-first, Vulnerability-first. MeanDelta_i = sum_p Delta_i,p / 5. PolicySD_i = sqrt(sum_p(Delta_i,p - MeanDelta_i)^2 / 5), ddof=0. Equal weights describe this finite registered design; they are not policy-adoption probabilities. Direct-community is excluded as an exact frozen duplicate of Impact-first. Random is a separate sixth-policy sensitivity; Unconstrained is never an ensemble member.

PolicySD equals SD_p(B_i,p) algebraically because the same B_i,U is subtracted from every policy. It measures variation among realization-mean policy burdens, not earthquake uncertainty, error, causal effects or a confidence interval. The separately saved mean_m SD_p(B_i,p,m) is a different diagnostic estimand. Cohort averages are {d.PolicySD.mean():.4f} h and {d.MeanWithinRealizationPolicySD.mean():.4f} h respectively; their mean gap is {(d.MeanWithinRealizationPolicySD-d.PolicySD).mean():.4f} h. The independently checked Jensen inequality holds, but the quantities are not interchangeable.

## Fitted coordinates and distance budgets
A: Init_Supply, spectral Grid_Impact, dependency HHI; Impact-first B and Delta; FEMA SOVI_SCORE and log1p frozen Population. P2 replaces only RQ2 with B_Unconstrained and MeanDelta. P3 uses B_Unconstrained, MeanDelta and PolicySD. Grid_Impact is the frozen tract-weighted spectral-connectivity importance measure, not the population-impact dispatch score. HHI = sum_j W_ij^2 for normalized tract dependency weights.

All observations have equal fitting weights. Each RQ receives one-third of squared-distance budget. RQ1 coordinates each 1/9; RQ3 coordinates each 1/6. A/P2 RQ2 each 1/6; P3 RQ2 each 1/9. Z scores use cohort population SD (ddof=0); apply square roots of budgets. P2-to-P3 changes coordinate inclusion AND RQ2 allocation. Minus-Init diagnostics preserve RQ1 total, allocating 1/6 to each remaining coordinate. Exact identities are not fitted as separate inputs: MeanTotalBurden = B_Unconstrained + MeanDelta; Impact B = B_Unconstrained + Impact Delta; AUC = 1 - B/480.

Five leave-one-out sets and main5+Random are seven unique sets including main5. Omitting Vulnerability is one of the five LOO cases, not an eighth independent comparison. Raw changes are retained before scaling. Main fits standardize separately by set; seed42 K2-8 fixed-main5-scaling fits isolate rescaling effects. Training-only scaling is used for geographic refits.

K1 inertia and K2-8 full-cohort silhouettes; seeds42-46, k-means++, n_init50, Lloyd, max_iter500, tol1e-4. Endpoint-chord bend is a finite-range diagnostic, not an optimized physical K. Saved A labels are reused after exact matrix and silhouette verification. P2/P3 minus-Init is restricted to main5 K1 and K3-5. All individual fits/labels and four-quadrant spatial predictions are retained. Diagnostic IDs are model-specific and ordered by mean burden, then population; ARI is invariant; Hungarian matching is for transitions only.
''')
    report('POLICY_ENSEMBLE_SOURCE_AND_PAIRING_QA.md','Frozen ensemble source and pairing QA',f'''
Status: PASS. Starting authority `{AUTH}`. Rechecked {qa['verified_event_payloads']:,} event payloads (seven policies times 1,000 physical IDs), their JSON and actual NPZ SHA256, station order, physical/damage/duration hashes, graph/source/crew/directed-travel identities, mapping and horizon. The frozen physical inputs are `(92 stations, 1000 samples)`; canonical hashes combine ordered station IDs, DS and repair-duration bytes, not filenames. All initial effective station states match the existing source-gate archive.

| Check | Maximum error / evidence |
|---|---|
| Exact B = U + paired Delta | {qa['identity_max_error_hr']:.3g} h |
| Archived tract projection | {max(x['projection_max_error_hr'] for x in qa['policies']):.3g} h |
| Event integration vs station integrals | {max(x['event_max_error_hr'] for x in qa['policies']):.3g} h |
| Population-weighted summary over full study | {max(x['population_summary_max_error_hr'] for x in qa['policies']):.3g} h |
| Independent ensemble arithmetic | {independent['ensemble_arithmetic_max_error_hr']:.3g} h |
| Independent SciPy full-cohort silhouettes | {independent['full_cdist_silhouette_max_error']:.3g} |

Sources: original policies and Unconstrained in `Formal_Experiment_20260923/Formal_Offline_Evaluation/` and `Formal_Trajectories/2pc50/C57_D1/`; Vulnerability-first in `Equity_Amendment/Offline/` and `Equity_Amendment/T/2pc50/C57_D1/`. Its executable commit differs, but the common physical and configuration identities are independently matched. `POLICY_ENSEMBLE_QA.json` preserves exact source identities and integral/summary hashes; `FROZEN_EVENT_VERIFICATION.csv` records all individual archive hashes. `SOURCE_HASH_VERIFICATION.csv` binds tracked inputs to actual Git/LFS bytes and external files to their manifests.

The NPZ tract arrays do not carry GEOIDs. Their order is the original frozen `Data/Tracts_Within_Expanded_Area.csv` order, explicitly recovered and independently checked by W projection; fits subsequently sort exact eleven-digit IDs. All population values are byte-source verified and unchanged. The upstream frozen Census download vintage is not newly established by this analysis.

`FROZEN_STATION_INTEGRALS_AND_MAPPING.npz` is a compact byte-exact extraction of existing station integral arrays, physical IDs/hashes and W, not new recovery simulation. It enables clean-clone reproduction of the new ensemble calculations without the large raw event archive. Rechecking ALL original event files and their physical authority still requires the manifest-bound local archive absent from a clean Git clone. No aggregate-to-tract outcomes were fabricated.

{independent['protected_scientific_files_unchanged']} protected scientific files and {independent['prior_package_files_unchanged']} files in the four preceding packages remain hash-identical. The unrelated source Git status is unchanged. This package alone is committed. No physical schedules, trajectories, formal memberships, quartiles or numbered figures were modified.
''')
    report('VULNERABILITY_FIRST_CIRCULARITY_AUDIT.md','Vulnerability-first procedural dependence',f'''
Vulnerability-first uses the frozen SOVI Q4 group to build its restoration order. Including its burden in an equally weighted outcome summary therefore creates a known procedural link from SOVI into RQ2. Small marginal correlations cannot prove independence or remove this link. This is not a mathematical identity between PolicySD and SOVI; it is a design dependence.

{table(cir)}

With all five policies, mean constraint burden is 4.4568 h in Q1 and 2.9972 h in Q4. Removing Vulnerability-first yields 4.2334 h and 3.3977 h; the Q1-Q4 contrast falls from 1.4596 to 0.8357 h. Pearson MeanDelta-SOVI changes from -0.2597 to -0.1669; PolicySD-SOVI from -0.1951 to -0.1731. Thus the targeting materially influences the mean burden association, even though its average SD influence is modest. Quartiles were never recomputed.

Main-five versus no-Vulnerability membership evidence (all five seeds, own-set scaling):

{table(cmp.loc[cmp.comparison.eq('policy_set') & cmp.policy_set.eq('without_vulnerability-first') & cmp.scaling.eq('cohort') & cmp.k.isin([3,4,5])].groupby(['specification','k']).ARI.agg(['min','mean','max']).reset_index())}

For P3/K4, high membership agreement does not make the design procedurally independent. For P2/K3 the membership effect is larger. Retain Vulnerability-first only as an explicitly declared comparison priority; report its LOO sensitivity. Do not claim the resulting clusters independently discover that vulnerability targeting causes improved equity, or validate the same Q4 strategy using a typology partly built from its own outcomes.
''')
    report('INIT_SUPPLY_MULTIPOLICY_SENSITIVITY.md','Rare initial-state leverage under multi-policy summaries',f'''
The prior frozen station-dependency audit associates the exact 34-tract group with retained Core proxy STATION Q (HARBOR, 308581): approximately 97.19% of its summed initial service contribution comes from Q. Q has source-qualified initial functionality in 40/1,000 realizations; its mean effective initial service is 0.0245. This is frozen-model evidence, not independently verified electrical capacity or customer-level resilience.

The exact same 34 tract identities are retained; their mean initial modeled service is {100*d.loc[rid,'Init_Supply'].mean():.4f}%, still near-total loss in absolute terms. Mean Unconstrained deficit = {d.loc[rid,'B_Unconstrained'].mean():.4f} h; main-five MeanDelta = {d.loc[rid,'MeanDelta'].mean():.4f} h; PolicySD = {d.loc[rid,'PolicySD'].mean():.4f} h. The previous Impact-first Delta was {d.loc[rid,'Delta_B_logistics'].mean():.4f} h. Thus relatively favorable initial-state and baseline recovery do NOT imply low burden under every constrained policy.

The cohort still has 1,533/2,299 exact zeros (66.6812%); the top23 initial values explain 62.4799% of initial-value variance. No clipping, jitter, trimming, zero replacement or imputation was used.

{table(ev.loc[ev.specification.isin(['P2','P3']) & ev.k.isin([3,4,5]),['specification','k','rare_class_tracts','rare_34_capture','rare_34_precision','rare_Init_centroid_share']])}

P2/K3 merges all34 into a broader 428-tract constraint-burden class; it is not an isolated initial exception. P2/K4 has a 37-tract class containing all34; P3/K3-5 at seed42 has 38. Approximately 80% of these rare centroids' squared distance is still attributable to Init. P2/K5 at seed42 enlarges the Q-containing group to43 (purity79.1%); other seeds may differ. Every saved fit's capture and precision is in `RARE_Q_GROUP_MEMBERSHIP_AUDIT.csv`.

The registered minus-Init main-five K3-5 results contain {int(rare.loc[rare.specification.str.endswith('-minus-Init') & rare.distinct_rare_state,'distinct_rare_state'].sum())} distinct high-purity Q classes (capture and precision both at least0.8, a diagnostic reporting criterion only). Removing the initial-state construct also increases each remaining RQ1 budget from1/9 to1/6. `INIT_ALGEBRAIC_DISTANCE_DIAGNOSTICS.csv` separates literal Init-distance deletion at unchanged other budgets from that extra redistribution; no additional fitted model was introduced to optimize this distinction.

Geographic leave-block-out tests use official tract internal points and four registered quadrants, not neighborhood polygons or a spatial-process probability sample. The rare source-supported state is spatially concentrated and may merge if its geographic training support is withheld. All predicted labels, exact deterministic replay centers and rare capture/precision are supplied. Seed stability alone is not physical validation.

Interpretation: retain Init only with explicit rare-state/proxy limitations. Its genuine frozen mapping/source explanation is not sufficient to call the rare class a universal community recovery regime. P2/K3 is a parsimonious alternative that does not spend a separate class on this exception; P3/K4 explicitly displays it. Neither is formally adopted here.
''')
    report('MULTIPOLICY_METHODS_AND_REVIEWER_RATIONALE.md','Proposed Methods and reviewer rationale',f'''
## Proposed Methods paragraph (not inserted into manuscript)
Under the fixed 2%-in-50-year ground-motion benchmark and frozen resource, mapping and source assumptions, tract recovery was summarized over five predeclared restoration priorities: population-impact, hospital, degree, betweenness and vulnerability targeting. For each priority, the 480-h normalized service-deficit integral was averaged over the same1,000 physical realizations and differenced against the paired Unconstrained reference. The compact multi-policy representation used the Unconstrained deficit and the equally weighted mean of the five additional constrained deficits. A registered extension additionally used their population standard deviation across the five policy-specific means. These equal descriptive policy weights are not probabilities of future policy adoption. Tract features were standardized on the positive-population cohort and weighted using one-third of squared-distance budget per research-question domain. Policy-set leave-one-out, geographic and initialization sensitivities were examined before author selection of any typology.

## Reviewer-facing rationale (proposal only)
A community typology based solely on Impact-first would be conditional on that particular repair priority. Separating the common Unconstrained recovery burden from the mean additional burden over an explicitly stated finite policy set avoids identifying population-impact priority as a neutral community attribute. It does not make the typology policy-independent: the registered LOO tests show only moderate and specification-dependent membership robustness. Random was held out of the main set because it is a sensitivity reference, not a substantive restoration priority. Direct-community was not counted separately because its frozen results duplicate Impact-first.

Averaging burdens is a summary of alternative experimental outcomes, not an implemented schedule or a synthesized physical service trajectory. The model estimates graph-based service availability rather than actual delivered electricity. PolicySD is restoration-priority sensitivity conditional on this policy set, not physical uncertainty or a causal policy-effect estimate. Vulnerability-first procedurally uses frozen Q4 and can influence the RQ2-SOVI association; that dependence and its LOO check must be disclosed.

All partitions are conditional on the same scenario, fragility, mapping, source proxy, resources and travel assumptions. Frozen T80 describes the Impact-first mean trajectory; it is not a multi-policy T80. SOVI quartiles re-express an input and therefore are not independent validation. Hospital presence is an external facility-location descriptor, not residents' electricity-dependent health need. Alternative-policy outcomes share the underlying physical simulation; their descriptions test sensitivity, not independent empirical accuracy. No proposed wording or diagnostic output has been inserted into formal manuscript or figures.
''')
    content='''## Recommendation for author review, not promotion
**Prefer P2 as the compact primary candidate; use PolicySD as a reported descriptor and P3 as a conditional sensitivity extension.** This is a construct/parsimony recommendation, not proof that P2 has uniformly more stable clusters. P3/K4 is a serious alternative if identifying restoration-priority sensitivity as a distinct fitted construct is an explicit author objective. No final specification or K is selected.

**P2/K3 and P3/K4 are the principal interpretable alternatives; K5 is not justified by maximum silhouette alone.** P2/K3 has a broad baseline-recovery versus constraint-burden distinction without an isolated Q class. P3/K4 provides a clearer spectral-criticality class and better geographic/average LOO agreement, but reuses strongly overlapping constraint/SD information, isolates the Q-proxy state and is less robust to adding Random. Authors must decide which construct emphasis is intended.

## Direct answers
1. Multi-policy representation is better justified than a single arbitrary reference for describing outcomes across a declared finite set. It reduces conceptual dependence on Impact-first, but empirical LOO agreement remains moderate. It is not a policy-neutral or universally robust typology.
2. P2 separates common baseline burden from mean added constraints without fitting an extra strongly overlapping coordinate. This is sufficient for a compact three-RQ design. P3 offers an explicit priority-sensitivity dimension but no unequivocal overall improvement.
3. PolicySD has a meaningful definition and is not an exact duplicate. However, MeanDelta-PolicySD Pearson=0.8567 and Spearman=0.9233; its all-other linear R2=0.7658, VIF=4.2702 and additive-spline out-of-fold R2=0.8616. It largely tracks constraint burden, and adding it plus reallocation reduces the baseline-recovery budget from1/6 to1/9. It should not be admitted merely because it is available.
4. Vulnerability-first contributes known procedural SOVI dependence and changes the Q1-Q4 mean-increment contrast. This is material for interpretation, even when P3/K4 membership changes little after omission. Keeping it requires explicit disclosure, not a claim of independent equity discovery.
5. Five-policy LOO robustness is moderate, not uniformly high. P2/K3 has a stronger worst-case LOO bound than P3/K3; P3/K4 has better average and geographic agreement than P2/K4. No one policy universally dominates SD: Degree contributes32.64% of summed variance, followed by Hospital19.43%, Betweenness18.49%, Vulnerability15.84%, Impact13.60%. Omitting Degree is important for P3; adding Random strongly changes SD and P3 memberships.
6. Endpoint-chord diagnostics suggest P2/K3 and P3/K4, while mean silhouettes peak atK5 in both. The curves are smooth; P2/K3-K4 bends are close. K5 seeds yield competing optima and, in several fits, a12-tract very-low-population class. It is not evidence for five universal community regimes.
7. The34 Q-dependent tracts remain influential. P2/K3 absorbs them into a broad class; P2/K4 and P3/K3-5 isolate enlarged37-38-tract proxy-conditioned groups. Initial availability remains only1.815% for the exact34, and their mean multi-policy added burden is7.734h. They are not strongly resilient communities.
8. A/K5 separates Impact-specific logistics burden and contains a distinct spectral-criticality class. P2/K3 instead separates relatively low baseline/low increment, lower baseline/high increment, and higher baseline/intermediate increment. SOVI is highest in the large low-increment class, not the highest-burden class. P3/K4 splits spectral importance from a high-increment/high-SD class, but social/population centroid separation is relatively weak. All interpretations are conditional, not neighborhood labels.
9. Preserved limitations: only five particular priorities; one frozen hazard/resource/mapping/gate setup; shared simulation authority; SOVI-based targeting; static directed travel; source proxies rather than electrical capacity; rare Init and low-population leverage; official-point coarse geographic tests; unresolved upstream frozen Census vintage; complete raw event re-audit needs local archives. No out-of-sample empirical validation is supplied.
10. Before promotion, authors must approve the finite policy set, equal descriptive policy weights, conditional Init interpretation, whether PolicySD is fitted or descriptive, intended broadP2/K3 versus structure/sensitivity-focusedP3/K4, and the resulting non-independent equity interpretations. A future formal Stage7 update requires separate explicit authorization.
'''
    content+='\n## Transparent K evidence (no optimized composite score)\n\n'+table(ev.loc[ev.k.isin([3,4,5]),['specification','k','mean_silhouette','seed_min_ARI','geographic_min_ARI','geographic_median_ARI','LOO_min_ARI','LOO_mean_ARI','plus_Random_mean_ARI','smallest_class_tracts']])
    content+='\n\n## Statistical preferences\n\n'+table(prefs)
    content+='\n\n## Full K2-8 evidence\n\n'+table(ev[['specification','k','mean_silhouette','chord_gap','seed_min_ARI','geographic_median_ARI','LOO_min_ARI','smallest_class_tracts']])
    content+='\n\n## Original-unit profiles for the main alternatives\n\nAll means compared with full-cohort references: Unconstrained31.6114h, MeanDelta3.3628h, PolicySD2.3458h, spectralImpact0.1122, HHI0.6399, SOVI66.5082, population3943.7. HHI varies little between the principal classes; it remains a dependency-concentration construct but does not discriminate every class. Values of clustering inputs are descriptions, not independent validation.\n'
    for sp,k in [('P2',3),('P2',4),('P3',4),('P2',5),('P3',5)]:
        q=profiles.loc[profiles.specification.eq(sp)&profiles.policy_set.eq('main5')&profiles.k.eq(k)].pivot(index='diagnostic_cluster',columns='variable',values='mean')
        gg=groups.loc[groups.specification.eq(sp)&groups.policy_set.eq('main5')&groups.k.eq(k)].set_index('diagnostic_cluster')
        q=q[['B_Unconstrained','MeanDelta','PolicySD','Grid_Impact','Redundancy_HHI','SOVI_SCORE','Population']].join(gg[['n_tracts','population_share','Q4_tracts','hospital_tracts']])
        content+=f'\n### {sp}/K{k}, seed42, model-specific IDs\n\n'+table(q.reset_index())+'\n'
    content+='''\nP2/K3: D1 represents1,235tracts and57.18% of population, with baseline30.06h, added1.75h and SOVI78.92. D2 has428tracts/18.70%, baseline27.80h but added7.10h and SOVI48.31. D3 has636tracts/24.12%, baseline37.20h, added3.97h, higher mean spectral impact0.308 and SOVI54.65. These are contrasting frozen recovery/dependency combinations, not intrinsic resilience or risk classes.

P3/K4: D1 is the38-tract Q-proxy exception; D2 is the1,223-tract low-increment class; D3 is the248-tract high spectral-impact class (mean0.743); D4 contains790tracts with added6.14h and SD4.44h. SOVI means63.49? The exact P3 rare-class SOVI is62.19, with other class means73.97,51.97,59.72 respectively (use the exact table). P3 introduces an interpretable structural distinction, but only6.45% of total between-class squared separation comes from RQ3 atK4, versus18.18% forP2/K3. Equal assigned domain budgets are not equal realized separation. MeanDelta and PolicySD jointly account for40.78% inP3/K4, reflecting their correlation plus allocated budgets, not two independent physical mechanisms.

K5 warning: P2/seed42 contains12tracts representing754people (0.0083%); five of the eight added zero-housing positive-population tracts are in it. Their low log-population values, not a newly discovered service regime, give substantial distance leverage. P3/seed43-45 also yields12-tract classes, while seed42/46 instead split broader social/structural contrasts. These admissible tracts must remain represented, but statistical isolation is not automatically a scientifically useful community type. No observations are removed to improve clustering.
'''
    content=content.replace('SOVI means63.49? The exact P3 rare-class SOVI is62.19, with other class means','SOVI means are62.19 for the rare class, with other class means')
    content+='\n## Exact comparison with A/K5\n\n'+table(frame('A_K5_TO_MULTIPOLICY_COMPARISONS.csv'))
    content+='\n\n## Independent verification and preservation\n\n'+f'{independent["independently_checked_fits"]} saved fits and {independent["independently_checked_spatial_predictions"]} spatial predictions verified. All {independent["protected_scientific_files_unchanged"]} protected scientific files and {independent["prior_package_files_unchanged"]} prior-package files are unchanged. No formal membership, manuscript or numbered figure was changed. See the full QA JSON and source hashes.\n'
    report('FINAL_P2_P3_AUTHOR_DECISION.md','Multi-policy candidate and K: author decision evidence',content)
    report('README.md','Stage7 multi-policy diagnostic package',f'''
Starting authority: `{AUTH}`. This is an isolated controlled diagnostic, not formal Stage7. Main decision: `FINAL_P2_P3_AUTHOR_DECISION.md`. Numerical evidence: `K_SCIENTIFIC_EVIDENCE_MATRIX.csv`, ensemble values, policy-set sensitivities, all fitted labels and source records.

Reproduce in Python3.12 using the repository environment (NumPy1.26.4, pandas2.2.2, SciPy1.11.4, scikit-learn1.5.1, Matplotlib3.9.2, PyMuPDF1.28.0). Limit BLAS/OpenMP to one thread as in the recorded run. Run these scripts in order from this directory:

```text
python audit_ensemble.py          # requires manifest-bound local frozen archives
python audit_information.py
python fit_registered.py
python verify_independent.py      # full source checks and exact registered spatial replays
python build_evidence.py
python write_reports.py
python make_figures.py
python verify_package.py
```

Set `LA_GRID_FROZEN_SOURCE_ROOT` only to the authoritative archive root if it differs from the archived default. No script executes physical simulation. For a clean Git clone, `git lfs pull` retrieves this package's verified compact station-integral/W snapshot and frozen descriptor table. `reproduce_from_snapshot.py` verifies the core ensemble quantities without needing all raw event files. Full event/source re-audit still needs the external archive and is not claimed clean-clone complete.

Review figures01-07 are data-only Matplotlib vector PDFs with600dpi previews. The profile PDF has four pages. Official geographic support is tract internal points, not verified neighborhood polygons. K5 profiles are seed42 illustrations only; competing seeds are retained and disclosed. All classes/IDs are diagnostic and model-specific. No method, input, quartile, formal result, manuscript or numbered figure is promoted or overwritten.

Sources, derived SHA256, independent numerical QA, visual QA and remote LFS delivery proofs are included. `REMOTE_DELIVERY_VERIFICATION.json` binds scientific payload bytes to the first delivery commit; the following provenance-only commit records that proof. Neither modifies formal science.
''')
    save('SOURCE_HASH_VERIFICATION_REPORTS.csv',source.records)


if __name__=='__main__':main()
