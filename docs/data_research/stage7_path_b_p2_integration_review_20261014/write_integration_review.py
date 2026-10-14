"""Coordinated review drafts and exact future routing plan, never production edits."""
import json
import re
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).parent))
import analyze_path_b as a


def table(frame):
    return frame.to_markdown(index=False,floatfmt='.4f')


def text(name,body):
    a.u.write(a.HERE/name,body.strip()+'\n')


def main():
    d=a.load_frozen();x=d.loc[d.Population>0]
    prof=pd.read_csv(a.u.lp(a.HERE/'CLUSTER_ORIGINAL_UNIT_PROFILES.csv'))
    counts=pd.read_csv(a.u.lp(a.HERE/'CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv'))
    evidence=pd.read_csv(a.u.lp(a.HERE/'P2_REGISTERED_K_EVIDENCE.csv'))
    seed=pd.read_csv(a.u.lp(a.HERE/'P2_SEED_STABILITY.csv'))
    spatial=pd.read_csv(a.u.lp(a.HERE/'P2_SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv'))
    policy=pd.read_csv(a.u.lp(a.HERE/'P2_POLICY_SET_CLUSTER_STABILITY.csv'))
    rare=pd.read_csv(a.u.lp(a.HERE/'Q_LINKED_34_IN_P2.csv'),dtype={'tract_id':str})
    init=pd.read_csv(a.u.lp(a.HERE/'inputs/INIT_ALGEBRAIC_DISTANCE_DIAGNOSTICS.csv'))
    krows=[]
    for k in [3,4,5]:
        f=evidence.loc[evidence.k.eq(k)]
        p=policy.query("comparison == 'policy_set' and scaling == 'cohort' and k == @k and seed == 42")
        r=init.query("specification == 'P2' and policy_set == 'main5' and k == @k")
        krows.append(dict(k=k,mean_silhouette=f.mean_silhouette.mean(),seed_min_ARI=seed.loc[seed.k.eq(k),'ARI'].min(),
            geographic_full_median_ARI=spatial.loc[spatial.k.eq(k),'full_ARI'].median(),
            geographic_heldout_min_ARI=spatial.loc[spatial.k.eq(k),'held_out_ARI'].min(),
            leave_one_policy_out_min_ARI=p.loc[~p.policy_set.eq('plus_random'),'ARI'].min(),
            leave_one_policy_out_max_ARI=p.loc[~p.policy_set.eq('plus_random'),'ARI'].max(),
            min_class_tracts=f.min_cluster_tracts.min()))
    a.save('K3_K4_K5_DECISION_EVIDENCE.csv',pd.DataFrame(krows))
    a.save('P2_K3_K4_INIT_DISTANCE_LEVERAGE.csv',init.query("specification == 'P2' and policy_set == 'main5' and k in [3,4]"))
    a.save('P2_K3_K4_RARE_SOURCE_STATE.csv',a.read('RARE_Q_GROUP_MEMBERSHIP_AUDIT.csv').query(
        "specification == 'P2' and policy_set == 'main5' and k in [3,4]"))

    variables=[
        ('RQ1','Init_Supply','Mean frozen initial modeled tract availability, including functionality threshold and Core-source reachability','Fraction (0-1)','None','1/9'),
        ('RQ1','Grid_Impact','Tract-dependency-weighted frozen substation spectral connectivity impact','Unitless spectral descriptor','None','1/9'),
        ('RQ1','Redundancy_HHI','Sum of squared normalized tract-to-substation dependency weights','Unitless concentration (not independent electrical paths)','None','1/9'),
        ('RQ2','B_Unconstrained','Realization-mean integral of 1 minus modeled service availability under Unconstrained, 0-480 h','Equivalent full-service-deficit hours','None','1/6'),
        ('RQ2','MeanDelta','Equal mean of five matched constrained-minus-Unconstrained realization-mean deficits','Equivalent full-service-deficit hours','None','1/6'),
        ('RQ3','SOVI_SCORE','Frozen FEMA NRI v1.19 composite social-vulnerability score and original quartiles','National percentile score, 0-100','None','1/6'),
        ('RQ3','Population','Frozen formal tract resident count; magnitude of population representation, not electricity demand','Persons','log1p','1/6')]
    v=pd.DataFrame(variables,columns=['RQ','variable','definition','units','transformation','squared_distance_budget'])
    v['source_commit']=a.MP;v['valid_eligible_tracts']=2299
    a.save('CLUSTERING_VARIABLE_TABLE.csv',v)
    text('RQ_ALIGNMENT_AND_VARIABLE_TABLE.md',f'''# Path B research-question alignment - proposed manuscript text

RQ1: How do earthquake ground motion and network dependency shape modeled tract-level electricity-service disruption?

RQ2: Under finite repair resources and travel constraints, how do restoration priorities change overall and critical-service recovery?

RQ3: How are modeled recovery burdens and restoration-policy effects distributed across communities, and where do high cumulative service deficits co-occur with social vulnerability and other pre-existing risk-relevant conditions?

RQ3 is broader than a single social-vulnerability score. Its primary fitted measurements remain composite SOVI and population magnitude; environmental-hazard context is assessed separately. This wording does not imply that health dependence, income, all vulnerability dimensions or actual outage damages have been independently measured. Cumulative deficit includes depth and duration: it is not simply an outage-duration threshold.

{table(v[['RQ','variable','units','transformation','squared_distance_budget']])}

RQ1 distinguishes initial modeled state, spectral structure and dependency concentration. RQ2 separates common frozen baseline recovery from additional finite-resource/dispatch/travel burden across a declared policy set. RQ3 describes residents and composite vulnerability, with supplementary screening geography rather than another fitted hazard coordinate. Grid_Impact is not the population-impact repair priority. HHI is not feeder redundancy. Population is not power demand. NCV14 is not vulnerability, total risk or modeled recovery.
''')
    text('STAGE7_METHODS_DRAFT.md','''# Stage 7 Methods - Path B replacement draft

We characterized tract-level recovery patterns with the seven-coordinate P2 specification organized around three research questions. The clustering cohort comprised all 2,299 tracts with positive frozen formal population, including eight positive-population tracts with zero conventional housing units. The sixteen zero-population tracts remained in the 2,315-tract service model but were unclassified. Exact GEOIDs, population values and original FEMA NRI v1.19 social-vulnerability quartiles were retained.

RQ1 used initial modeled availability, spectral network impact and tract-dependency HHI. RQ2 used the Unconstrained cumulative deficit and the equally weighted mean additional deficit across Impact-first, Hospital-first, Degree-first, Betweenness-first and Vulnerability-first. Each deficit integrates one minus modeled availability over 0-480 h and is averaged over the same 1,000 frozen physical realizations under 2pc50/C57_D1/M1_UTILITY_003/G1_BASELINE_050. The policy set is a finite experimental comparison design, not a probability distribution of future decisions. Its average does not represent an implemented average repair schedule. The increment combines resource, dispatch and travel effects; it does not separately identify travel delay.

RQ3 used frozen SOVI_SCORE and log1p of frozen formal population. No CDC theme mean, building value or natural-hazard index entered P2. Continuous features were centered and divided by the eligible cohort population standard deviation (ddof=0). Each RQ received one-third of squared-distance budget: 1/9 for the three RQ1 coordinates and 1/6 for each RQ2/RQ3 coordinate. Standardized values were multiplied by the square root of these budgets, with equal tract weights. These are prespecified construct budgets, not estimated optimal weights or equal realized separation.

The saved registered K-means results used k-means++ initialization, n_init=50, Lloyd iterations, max_iter=500 and tol=1e-4, seeds 42-46. K3 is the author's conditional main-text choice for parsimonious regional interpretation; K4 is retained as mandatory sensitivity. K4 has stronger geographic agreement in the registered leave-out design, which is disclosed rather than treated as equivalent robustness. The saved K1-8 inertia, full-cohort silhouette, seed agreement, geographic leave-block-out and policy-set sensitivity were considered jointly, without treating silhouette as independent physical validation. This review imported saved labels and matrices and performed no new fitting.

Figure 7D overlays the frozen Q1-Q4 groups on continuous five-policy mean total deficit R=B_Unconstrained+MeanDelta. A separately identified direct-co-occurrence outline marks frozen Q4 and R at or above the frozen cohort P75. It is a descriptive, policy-conditioned screen, not a composite score, statistically significant hotspot or validated intervention ranking. Environmental-hazard geography is reported separately using the previously audited NCV14 measure.
''')
    means=prof.query("model == 'P2_K3'").pivot(index='class_id',columns='variable',values='mean').reset_index()
    main_counts=counts.query("model == 'P2_K3'")
    text('STAGE7_RESULTS_DRAFT.md',f'''# Stage 7 Results - Path B replacement draft

The three saved P2 classes represent contrasting combinations rather than a hierarchy of resilience or total risk. C1 comprises 1,235 tracts and 5,184,036 residents; C2 comprises 428 tracts and 1,695,501 residents; C3 comprises 636 tracts and 2,186,985 residents. Display IDs are specific to P2 and are not the previous NCV14/H2 class memberships.

C1 has relatively high mean SOVI (78.92 versus cohort 66.51), low spectral impact and smaller additional constraint deficit (1.75 h). C2 combines relatively lower Unconstrained deficit (27.80 h) with the greatest mean added constraint burden (7.10 h). C3 has greater spectral impact and Unconstrained deficit (37.20 h), with intermediate additional burden (3.97 h). HHI distributions substantially overlap; not every retained construct separates every class. These profiles describe the frozen earthquake-conditioned network and policy design, not causal neighborhood characteristics or actual delivered electricity.

{table(means[['class_id','Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','Population']])}

{table(main_counts[['class_id','tracts','population','hospital_linked_tracts','Q1','Q2','Q3','Q4']])}

K3 mean silhouette is approximately 0.2487; K4 is approximately 0.2530 and K5 approximately 0.2633. The smooth endpoint-chord inertia diagnostic favors K3, but does not establish a unique optimum. K4 isolates a 37-tract source-proxy-conditioned class, while K5 can isolate twelve very-low-population tracts. K3 retains broad recovery/vulnerability contrasts without presenting the source-proxy state as a separate universal community type. K4 is nevertheless more geographically stable: median full-cohort leave-out ARI is 0.8613 versus 0.7610 for K3, and the minimum held-out ARI is 0.8057 versus 0.4189. The author accepts K3 conditionally for broad interpretation, with this K4 advantage retained in supplementary sensitivity evidence. These coarse geographic checks are not independent spatial validation. Removing initial availability also redistributes RQ1 weights and materially changes the partition.

The Figure 7D direct screen reproduces 94 Q4/high-deficit tracts and 350,799 represented residents at P75=38.38135467381475 h. The global tract-level high-deficit prevalence is lower in Q4 (16.23%) than non-Q4 (27.97%), not evidence of positive regional concentration. The pattern remains negative after removing Vulnerability-first, but is weaker and substantially reduced or reversed in geographic common-support descriptions. This conditional spatial result should not be promoted to a causal equity benefit. These numerical details belong in Results or supplemental analysis, not the short figure caption.
''')
    text('K3_K4_AUTHOR_DECISION.md',f'''# P2 K3/K4 scientific decision

Author decision: saved P2/K3 is accepted as the conditional parsimonious main-text choice. Saved P2/K4 must remain as sensitivity with its stronger geographic agreement explicitly disclosed. This records the scientific choice, not permission to execute formal Stage 7 or figure-suite migration.

{table(pd.DataFrame(krows))}

K3 preserves a large high-SOVI/lower-increment class, a smaller low-baseline/high-increment class and a higher-spectral-impact/high-baseline class. RQ3 remains interpretable: 429/50/100 frozen Q4 tracts are distributed across C1/C2/C3. Hospital-linked incidence and quartiles are descriptive context, not independent validation of features derived from the same SOVI and modeled service data.

K4 provides slightly higher silhouette and stronger median geographic agreement, but adds a 37-tract class (130,518 residents) strongly associated with the frozen Core-source proxy. The exact historical 34 Q-linked tracts occur in P2 classes as follows: K3 {rare.P2_K3_class.value_counts().sort_index().to_dict()}; K4 {rare.P2_K4_sensitivity_class.value_counts().sort_index().to_dict()}. Their mean initial availability is {rare.Init_Supply.mean():.6f}, only {100*rare.Init_Supply.mean():.3f}% in absolute terms. Stable detection is not physical verification of resilient supply. The scalar ablation and fixed-budget distance diagnostics are retained in CSVs; deletion and redistribution are not interchangeable effects.

K5 has the highest internal mean silhouette but competing seeds, weaker geographic agreement and a twelve-tract/754-person low-population class in the saved seed42 fit. No tract is discarded to improve geometry. A modest numerical gain alone is not sufficient to prefer K4 or K5 for regional interpretation.

The policy ensemble removes reliance on one incumbent policy but does not make labels policy-independent. K3 leave-one-policy-out ARIs are approximately 0.619-0.792 at seed42. The lowest geographic held-out agreement is only 0.419 for K3, versus 0.806 for K4; K4 has a real geographic-stability advantage in this registered design. Four median-quadrant leave-outs are sensitivity, not independent spatial validation. K3 is therefore a conditional parsimony choice, not a dominance claim. The main text and supplementary sensitivity must retain this trade-off. No universal optimal K is established. No additional clustering search is required by this decision.
''')
    captionA='(A) Six descriptive empirical feature distributions; markers locate class medians on the 50% guide. (B) Cohort-standardized class means of all seven fitted P2 variables. (C) Saved P2/K3 geography. (D) Continuous five-policy mean total service deficit (equivalent hours), with frozen Q1-Q4 textures. Black outlines identify Q4 and deficit at or above frozen P75: descriptive co-occurrence, not a composite score. White outlined tracts are N/A. Population is fitted as log1p.'
    captionB=captionA.replace('with frozen Q1-Q4 textures','with frozen Q1-Q4 hue families and a common burden-to-lightness scale')
    text('FIGURE7_AND_S9_CAPTION_DRAFTS.md',f'''# Short proposed captions - not applied to the current suite

## Figure 7 - candidate A

{captionA}

## Figure 7 - candidate B

{captionB}

## Stage 7 diagnostics (legacy Figure S9; current active Figure S8)

Weighted-space inertia and full-cohort silhouette for the saved P2 fits. K3 is the parsimonious main-text candidate; K4 is a sensitivity, not a second primary typology. Lines retain registered seeds. K3 does not maximize silhouette. Initialization, geographic leave-out and policy-set agreement are internal sensitivity diagnostics, not independent physical validation; removing Init_Supply also redistributes RQ1 weights.

The active suite was renumbered continuously before this Path B review: old S09 diagnostics is current FigS08; current FigS09 is restoration-priority geography. Do not replace current S09 artwork with clustering evidence or restore retired numbering. The author-requested S9 caption is supplied with this explicit crosswalk.
''')
    ncvinfo=pd.read_csv(a.u.lp(a.HERE/'NCV14_VS_P2_INFORMATION.csv'))
    ncvprof=pd.read_csv(a.u.lp(a.HERE/'NCV14_P2_CLASS_DISTRIBUTIONS.csv'))
    text('NCV14_INCREMENTAL_VALUE_AND_REVIEWER_DEFENSIBILITY.md',f'''# NCV14: supplementary environmental-hazard context

Status: retained only as a researcher-derived geographic screening descriptor. No NCV14 value is in P2, and no new index or weight is calculated here. Source authorities are 49cc153 and 0c5365; exact file SHA256s are in SOURCE_PAYLOAD_HASHES.csv. This is not FEMA's RISK_SCORE, a comprehensive vulnerability/disaster-risk index, physical intensity validation or a prediction of multi-hazard power failures.

{table(ncvinfo[['variable','Pearson','Spearman']])}

The seven P2 coordinates jointly explain 18.17% of NCV14 variance in a descriptive linear regression (VIF 1.222). P2/K3 class means explain only 6.38% of NCV14 variance: most variation remains within classes. SOVI association is small, while the inverse association with MeanDelta is stronger; neither establishes independence or a causal hazard/recovery interaction.

{table(ncvprof[['class_id','n','mean','median','P10','P90']])}

The context shows that environmental screening burden, social vulnerability and modeled recovery penalties need not align. C1 has the highest mean NCV14 and highest SOVI but lower added constraint deficit; C2 has greater constraint deficit yet lower mean NCV14. Broad overlapping distributions rule out a new class-level risk ranking. A concise supplemental table and, if the author intends to discuss this geographic contrast, the optional context map are sufficient. Do not add another numbered graphic merely to display an unused variable.

## Methodological boundary

Williams, Summers and Harwell (2024), Sustainability 16, 10778, doi:10.3390/su162310778, provides a county-scale frequency-area/min-max/sum precedent. The frozen audit did not establish an exact original county aggregate replication: its hazard roster, normalization universe and numerical workbook were not unambiguously recovered. FEMA NRI v1.19 provides hazard-specific input fields, not this official composite. Our tract scale, fourteen-hazard roster and California reference scaling are researcher extensions and must be named as such. A later public catalog listing alone would not establish identity with the original numerical workbook.

For each retained hazard h, x_i,h=AFREQ_i,h*EXP_AREA_i,h/AREA_i. Hazard components are min-max scaled across valid California reference records, summed with equal nominal hazard weights, then the complete-case California sum is min-max scaled. The fourteen retained hazards are coastal flood, cold wave, drought, earthquake, hail, heat wave, landslide, lightning, riverine flood, strong wind, tornado, tsunami, wildfire and winter weather. Four target-all-null hazards are excluded, not filled with zero. Cold wave is locally constant zero. All 2,299 positive-population tracts have the frozen NCV14 value; that completeness is not proof of complete direct physical observation.

Heat wave, hail and strong wind account for about 89.5% of signed covariance contribution to local index variance. These are effective regional contributions, not optimized weights or independent hazard probabilities. NOAA reporting, buffers/fishnets and warning-zone crosswalks create coarse/shared geography and reporting biases. A documented heat period/frequency discrepancy and strong-wind period wording conflict remain source limitations. AFREQ may already encode area support; multiplying by EXP_AREA/AREA may repeat geographic exposure weighting. It is a screening construction, not an independent frequency-times-probability identity.

Earthquake's released frequency surrogate and the independent CGS 2pc50 PGA represent different thresholds and supports. Earthquake is a high-background, low-contrast component locally; its weak or signed negative contribution to relative index variance does not mean absence of earthquake hazard. Heat/hail/wind overlap and the low earthquake contrast prevent describing the regional index as balanced information about fourteen independent hazards.

Previously saved hazard-removal ranks and California-versus-Los-Angeles normalization sensitivity are included. CA/LA rank correlation is about 0.983, but this does not validate physical intensity or weights. Historical NCV14-fitted clustering sensitivity must not be claimed as validation of P2: removing a contextual hazard cannot change a model that never fits it. No new hazard-removal fits are warranted.
''')
    text('SUPPLEMENTARY_ENVIRONMENTAL_METHODS_RESULTS_DRAFT.md','''# Supplementary environmental context - proposed text

Methods. We retained the previously audited FEMA_NCV14_CA_v119 vector as a separate environmental-hazard geographic screening descriptor. Following a county-scale frequency-area precedent, the researcher tract extension uses fourteen available FEMA NRI v1.19 hazard frequency-area factors with California reference min-max scaling. It does not incorporate SOVI, building asset value, community resilience or modeled service outcomes directly, and does not enter the seven-variable typology. Source definitions, missingness, roster choices, normalization and hazard-removal sensitivities are reported separately. Its environmental screening construct is distinct from vulnerability, expected losses and calibrated electrical-system failure probabilities.

Results. Environmental screening geography is not reducible to the P2 classes. Class NCV14 means differ, but overlapping distributions and substantial within-class variation are more important than a new ordinal class risk label. The largest class combines relatively higher SOVI and NCV14 with lower added restoration-constraint deficit; the high-increment class has lower mean NCV14. Local index variation is dominated by heat wave, hail and strong wind, while the earthquake component has little local differentiation. These comparisons provide context, not causal explanation or independent validation of the frozen earthquake-recovery model. The optional author-review map/table should be included only when this contrast is discussed explicitly.
''')
    text('LIMITATIONS_AND_REVIEWER_RATIONALE.md','''# Path B limitations and reviewer rationale

P2 keeps disruption/dependency, baseline recovery, additional restoration constraints, composite social vulnerability and population magnitude distinct. RQ3 is broadened through descriptive geographic context rather than silently calling all context vulnerability or inserting a weakly validated eighth fitted coordinate. This preserves the scientific decision while allowing environmental conditions to be discussed accurately.

Initial availability is zero for 1,533 of 2,299 tracts and never exceeds 2.45%. Its standardized upper tail has distance leverage linked to the retained STATION Q (HARBOR, 308581) Core-source proxy. The 34 reference tracts' approximately 1.815% mean availability is not strong absolute resilience. P2/K4 isolates a 37-tract extension of this condition; K3 combines it within broader types. Retaining Init describes a real frozen-model initial condition, not independently established physical supply adequacy. Registered minus-Init comparisons also change within-RQ1 budgets and must disclose both effects.

The five policy weights are equal descriptive weights over selected priorities, not adoption probabilities. The classification is conditional on that set and the severe earthquake benchmark. Leaving policies out changes labels materially; excluding Vulnerability-first does not remove all procedural/spatial coupling. Vulnerability-first targets frozen Q4, so SOVI-based clustering, quartile descriptions and this policy's outcomes share information. They are not independent validation. The same network/mapping and physical draws create further cross-domain dependence.

High cumulative deficit combines depth and duration. Q4/high-deficit co-occurrence is not a new hazard score or a statistically significant hotspot. The global lower Q4 high-deficit prevalence persists without Vulnerability-first but geographic common-support estimates reduce or reverse it. Spatially correlated tracts do not justify naive IID significance claims. Four quadrant leave-outs are coarse sensitivity, not external validation; 5/10-km common-support descriptions have restricted denominators and are not universal spatial controls.

The model propagates graph-based service proxies, not AC/DC power flow, feeder/customer outages, dispatch, hospital delivered power or compound-hazard damage. No climate failure mechanism is simulated. NCV14 inherits coarse reporting/crosswalks and unequal effective regional hazard influence; frequency-area products may repeat exposure weighting. Population values are frozen and hash-verified; the earlier audit's unresolved original Census release/batch identity is not resolved by numerical agreement. Do not replace those values silently or make a stronger vintage claim.

Clean-clone post-processing of this package is reproducible from compact archived inputs. Full source-event reconstruction additionally requires the previously manifest-bound local trajectory archive, not all of which is in Git. This review checks all 1,000 compact physical identities, station order, exact mapping and station-integral arithmetic; it does not claim a new clean-room full physical run.
''')
    make_plan()
    text('FIGURE7_VISUAL_COMPARISON_AND_RECOMMENDATION.md','''# Figure 7D comparison at 7.2-inch width

Recommend candidate B in principle for the full-color main-figure author-review choice; retain A as the grayscale/accessibility-oriented alternative. B communicates quartile regions more clearly and avoids the dense pattern interference in A. The author has requested final-page-size review and comparison to existing figures, not certification based on width alone. This is a conditional readability recommendation, not universal accessibility certification or automatic production approval.

A provides one perceptually ordered burden scale for every quartile, with quartile texture orthogonal to intensity. Its grayscale and red-green deficiency stress tests retain burden order and the pattern key. However, Q2/Q3 textures and the smallest tracts require vector zoom; some printed polygons are too small to contain even one identifiable hatch cycle. The geometry/display-support table quantifies that scale limitation. Do not claim every tract's quartile can be read from a printed regional map.

B is cleaner in ordinary color and makes quartile regions more immediately apparent. Its exact two-dimensional legend uses four hue families with the same CIELAB L* and sRGB relative luminance at every common hour, rather than independently scaled quartile ramps. Thus equally dark cells mean equal burden in all quartiles. Matched luminance deliberately makes quartile identity disappear in grayscale; red-green and blue-yellow simulations also merge some hue distinctions. B therefore cannot be called fully grayscale/color-vision accessible. Preserve it for author comparison, not automatically as the main figure.

Both retain the exact P2/K3 labels, seven-coordinate ordinary-z profile, six ECDFs and common EPSG:3310 geography. All 2,299 eligible tracts are mapped, including eight zero-housing tracts; sixteen zero-population tracts have white fill/dark boundaries rather than zero deficit. Black outlines mark only frozen Q4 and R>=38.38135467381475 h. These are conditional direct-co-occurrence areas, not significant hotspots or repair priorities. No composite or Top-10 score is present.

The six ECDFs are spectral impact, HHI, Unconstrained deficit, MeanDelta, SOVI and population in persons (fitted as log1p). Initial service and log population remain in the seven-cell-per-class ordinary cohort-z profile. Three class colors are reused after explicit Hungarian membership matching to the historical palette, but model namespaces and changed counts remain explicit. No old NCV14 members are silently presented as P2.

The original review PDFs remain 7.2 x 10.4 inches, with 4,320 x 6,240 pixel exports at 600 dpi. Minimum extracted text is 6 pt and substantive labels include 6.4 pt; a proportional reduction to 9-inch height reduces those sizes further. They are therefore not certified as final-size artwork. Separate 7.2 x 9.0-inch print-fit proofs under docs/reproducibility/path_b_pre_migration_publication_gate_20261014/ use a 7.5-pt minimum and the previous figures' Arial hierarchy. They change typography/spacing only, retain exact observations, and remain review-only. The author agreed to this conservative review size; the journal-specific maximum height and caption space have not been confirmed. Maps, ECDFs, profiles and legends are vector objects. Native, grayscale and three Machado severity100 simulations are stress tests, not accessibility certification.
''')
    text('FIGURE_NATIVE_SIZE_VISUAL_QA.md','''# Publication-size visual inspection

Inspected both complete candidates at 7.2-inch width, enlarged A/B and the map/legend region, plus grayscale and protanopia/deuteranopia/tritanopia simulated views. No text clipping, axis-label overlap or footer/legend collision remains. Six empirical distributions retain tails and repeated observations; all 21 ordinary-z cells are printed with signed values. Continuous hour scales share the full eligible range. The black joint outlines are distinguishable from white N/A polygons. No NCV14 profile or K4 classification enters either main candidate.

Original review text includes 6-pt legend ticks and 6.4-pt substantive labels. Uniform reduction to 9-inch height makes these approximately 5.19 and 5.54 pt. The separate pre-migration print-fit proofs use 7.5-pt minimum text at 7.2 x 9.0 inches, matching the established Arial font family and 7.5-pt floor of Figures 2-5/7. They do not replace the original candidates or official artwork. Reduced-height evidence and exact text-size tables are archived in the publication-gate directory. Small-tract hatching remains unresolved in some polygons; B's matched-luminance quartile hues collapse in grayscale and partly under CVD simulation. Larger text does not remove either limitation.

The optional NCV14 context and saved P2 K-evidence PDFs were also rendered and inspected. They remain unnumbered author-review material, not extra adopted supplementary figures. The current 17 numbered artwork pairs were neither rerendered nor replaced by these proposals.
''')
    text('FINAL_PATH_B_SCIENTIFIC_DECISION.md','''# Final Path B author-review decision

Primary specification: seven-variable P2 with the previously registered equal-RQ squared-distance budgets. The author accepts saved P2/K3/seed42 as a conditional main-text choice. P2/K4 is mandatory supplementary sensitivity, not a second main classification, and its stronger geographic stability must be disclosed. Figure 7 candidate B is recommended in principle for full-color readability; A remains the grayscale-oriented alternative. B loses quartile hue information in grayscale and merges some families under CVD simulation. The pre-migration publication gate provides separate print-size proofs; final submission dimensions remain unconfirmed. No formal promotion is performed.

Verified: 2,299 eligible tracts, eight zero-housing tracts retained, sixteen zero-population exclusions, 9,066,522 represented residents. P2/K3 counts are 1,235/428/636 and populations 5,184,036/1,695,501/2,186,985. These are not the eight-variable class counts. Frozen labels, all seven coordinates, ddof0 standardization, weights, original SOVI quartiles and five-policy burden agree with source authorities. Independent compact-integral checks verify all 1,000 physical identities and reproduce the 94-tract/350,799-resident direct screen. No K-means or physical model ran.

K3 distinguishes higher SOVI/lower added burden, lower baseline/higher added burden, and higher spectral impact/higher baseline burden. K4 modestly improves silhouette and geographic median agreement but isolates the Q-proxy condition; K5's maximum silhouette can isolate very-low-population special-use tracts. Policy and spatial sensitivities are moderate, not proof of universal types. Initial-state and shared SOVI limitations remain explicit.

NCV14 stays supplementary: it contributes geographically distinct context but mostly within-class variation, is locally weather-dominated and has coarse-source/frequency-area limitations. Its existence is not independent validation of P2 or evidence of multi-hazard electrical failure.

Readiness: K3 main/K4 mandatory sensitivity and the in-principle B preference are now recorded; do not ask for the same scientific decisions again. Formal promotion still requires final submission-size and grayscale/CVD handling approval, the conditional co-occurrence caption, environmental-context scope, named manuscript/supplement targets and the exact migration/rollback authorization. The original Census population release identity and access to full manifest-bound trajectories remain provenance limitations. All formal Stage 7, manuscript and current numbered artwork are unchanged.
''')
    text('README.md','''# Path B P2 scientific and Figure 7 integration review

This is an isolated author-review package. It adopts the author's seven-variable scientific scope, imports frozen fits and makes no formal Stage 7, manuscript or current Figure 7 replacement.

Start with FINAL_PATH_B_SCIENTIFIC_DECISION.md, K3_K4_AUTHOR_DECISION.md and FIGURE7_VISUAL_COMPARISON_AND_RECOMMENDATION.md. The two complete figure candidates are under figures/. Methods, Results, RQ alignment, captions, supplementary context and limitations are separate proposed text files. Exact future paths are in PATH_B_PROMOTION_PATH_REGISTRY.csv and ACTIVE_DEPENDENCY_MATCHES.csv; no listed promotion is executed.

Reproduce from repository root using Python 3.12 and the existing scientific/PDF dependencies:

```text
python docs/data_research/stage7_path_b_p2_integration_review_20261014/analyze_path_b.py
python docs/data_research/stage7_path_b_p2_integration_review_20261014/make_review_figures.py
python docs/data_research/stage7_path_b_p2_integration_review_20261014/independent_qa.py
python docs/data_research/stage7_path_b_p2_integration_review_20261014/write_integration_review.py
```

Git/LFS source acquisition requires the pinned source commits and actual payloads. inputs/ retains compact exact-byte scientific authorities for offline arithmetic/figure reproduction; full original event archives remain external manifest-bound dependencies. Do not run the formal pipeline or legacy run_stage_7 to reproduce these review figures. The official shortened caption packet is a separate completed change on this same review branch.
''')
    print(pd.DataFrame(krows).to_string(index=False))


def make_plan():
    old=a.read('FORMAL_PROMOTION_PATH_REGISTRY.csv')
    rows=[]
    for r in old.itertuples():
        path=r.path.replace('NCV14_H2_K3_2299','P2_K3_2299')
        path=path.replace('Supplement/FigS09','Supplement/FigS08').replace('FigS09_Stage7_Diagnostics','FigS08_Stage7_Diagnostics')
        path=path.replace('Fig07_Community_Typology_and_Hotspots','Fig07_Community_Typology_and_Service_Deficit')
        reason='Review coordinated version-aware P2 routing; retain historical authority unchanged'
        if '/P2_K3_2299/' in path:
            reason='New versioned seven-feature P2 authority, exact saved K3/K4 labels, ddof0 standardizer, P2 budgets and original Q1-Q4'
        rows.append(dict(path=path,planned_action=r.planned_action,reason=reason,execution_authorized=False))
    extra=[
        ('src/la_grid/plotting/build_current_suite_k3.py','NEW_VERSION_AWARE_P2_MODE','Keep archived NCV14 mode; new accepted P2 builder must not restore old coordinates/labels'),
        ('src/la_grid/plotting/short_current_captions_20261013.py','TARGETED_CAPTION_SOURCE_UPDATE','Only accepted F7/currentS08 references; keep all other short captions and artwork'),
        ('src/la_grid/plotting/figure7_candidate_a.py','KEEP_HISTORICAL_NCV14_MODE','Do not reinterpret an archived eight-feature generator as seven-feature P2'),
        ('tests/test_current_figure_suite_integration.py','ADD_CURRENT_P2_VERSION_TESTS','Seven features, new exact counts, Q1-Q4 overlay and burden identity; explicit archived NCV fixtures'),
        ('results/figure_review/CURRENT_CLUSTER_PALETTE.json','MODEL_SPECIFIC_REGISTRY','P2 namespace and counts; same colors after transparent overlap alignment'),
        ('results/figure_review/Page_Previews/Fig07.png','RENDER_ACCEPTED_CANDIDATE','Only after layout approval'),
        ('results/figure_review/Page_Previews/FigS08.png','RENDER_ACCEPTED_P2_DIAGNOSTIC','Current numbering, not currentS09 priority map'),
        ('results/figures/FIGURE_REVIEW_GALLERY.html','SYNC_ONLY_APPROVED_REFERENCES','No competing current version or obsolete NCV fitted claim'),
        ('results/stage7/P2_K3_2299/direct_cooccurrence_94.csv','CREATE_VERSIONED_DESCRIPTOR','Frozen Q4 and fixedP75 only; no score or priority field')]
    rows.extend(dict(path=p,planned_action=act,reason=reason,execution_authorized=False) for p,act,reason in extra)
    frame=pd.DataFrame(rows).drop_duplicates('path')
    head=a.u.git('rev-parse','HEAD').decode().strip()
    existing=set(a.u.git('ls-tree','-r','--name-only','-z',head).decode().split('\0'))
    frame['tracked_at_review_HEAD']=frame.path.isin(existing)
    retired=frame.path.str.endswith('.py') & ~frame.tracked_at_review_HEAD
    frame.loc[retired,'planned_action']='RETIRED_PATH_NO_RECREATION'
    frame.loc[retired,'reason']='Earlier audit path no longer tracked at current HEAD; do not recreate expanded wrappers'
    a.save('PATH_B_PROMOTION_PATH_REGISTRY.csv',frame)
    inspect={p for p in frame.path if p in existing and p.endswith(('.py','.md','.json','.csv','.html'))}
    inspect.update(p for p in existing if p.startswith(('src/la_grid/plotting/','src/la_grid/revision/','tests/')) and
                   p.endswith('.py') and any(s in p.lower() for s in ['stage7','figure','suite','visualizer','composite']))
    hits=[];sources=[]
    pat=re.compile(r'2291|2,291|five.class|5.class|eleven|11.feature|NCV14|H2|SlowVulnerable|Hotspot|hotspot|FigS0[89]|PCA')
    for p in sorted(inspect):
        raw=a.u.payload(head,p)
        sources.append(dict(path=p,sha256=a.u.digest(raw),classification='Version-aware update if active; preserve historical modes'))
        for n,line in enumerate(raw.decode('utf-8-sig').splitlines(),1):
            if pat.search(line):hits.append(dict(path=p,line=n,text=line.strip(),sha256=a.u.digest(raw)))
    a.save('ACTIVE_DEPENDENCY_MATCHES.csv',pd.DataFrame(hits))
    a.save('DEPENDENCY_SOURCE_HASHES.csv',pd.DataFrame(sources))
    text('CONTROLLED_PROMOTION_AND_ROLLBACK_PLAN.md','''# Controlled Path B promotion and rollback - not executed

1. Carry forward the accepted conditional P2/K3 main choice, mandatory K4 sensitivity and in-principle B preference. Resolve the final submission dimensions and accessibility treatment, then obtain coordinated migration authorization for the actual editable manuscript/supplement targets. Do not reopen the clustering search or ask for the same scientific choice again.
2. Snapshot current suite HEAD, index/status and actual PDF/PNG bytes; retain 950 science hashes. Create a separate implementation branch. Do not reset dirty worktrees or overwrite historical Stage 7 directories.
3. Create the versioned results/stage7/P2_K3_2299 authority listed in PATH_B_PROMOTION_PATH_REGISTRY.csv. Copy exact approved source values, labels and class registry; never run legacy K-means or manufacture old compatibility columns. Freeze 2,315 domain status and 2,299 eligibility separately. Keep K4 sensitivity labels in a distinct namespace.
4. Add explicit current P2 routing to formal readers/verifiers and the canonical suite builder while preserving historical five-class and NCV14 modes. Replace hardcoded residential/five-class/eleven-feature/PCA assumptions only on new-version paths. Do not alter Stages1-6, schedules, GA, vulnerability quartiles or underlying model arrays.
5. Coordinate Figure7 A-C P2 labels, selected D overlay, profile tables, current FigS08 clustering diagnostics (legacy S9), captions, palette registry, mirrors, manifest, gallery, previews and all dependent packets. Current numbering is Main01-07/Supp01-10; the concise packet is now21 pages. Never restore retired numbering. Preserve every unrelated numbered artwork hash.
6. Apply approved manuscript Methods/Results/RQ/caption/supplement/limitations changes only to author-confirmed files. Existing old Stage7 descriptions and NCV14-as-fitted claims must be removed from active text, not historical audits. Source files and packet artifacts must agree before delivery.
7. Run version-aware numeric/membership/format/palette/packet tests and actual publication-size QA. Rebuild twice, require deterministic outputs and verify all mirror bytes. Commit/push scoped changes with LFS payload download checks; no merge without separate approval.

Rollback: before promotion record a JSON ledger of every replaced current file and actual payload SHA256. If an acceptance check fails, stop and discard only newly generated uncommitted files from that isolated implementation checkout after preserving evidence. If a committed promotion must be undone, make a non-destructive revert commit on the implementation branch, restoring recorded previous figure/routing files and removing only newly created version pointers. Do not reset/rewrite Git history or remove archived scientific results. Confirm original index/status and950 hashes after rollback. Manuscript rollback requires restoring the separately captured author-confirmed document, not an assumed Downloads copy.

Unresolved: the current editable manuscript target is not established by the earlier authority path audit. The full external event archive and original population release provenance remain documented dependencies. This prevents claiming complete clean-room physical reproduction, not compact post-processing reproduction. The review package is ready for author review; formal promotion remains gated.
''')
    text('STAGE7_DEPENDENCY_AND_INTEGRATION_GATE.md','''# Dependency gate

PATH_B_PROMOTION_PATH_REGISTRY.csv lists exact new authority, code, reader, artwork, packet, registry and document targets. ACTIVE_DEPENDENCY_MATCHES.csv records baseline line-level legacy/NCV references and source hashes; it is a scoped scan, not permission to replace historical text globally. Original FORMAL_DEPENDENCY_MATCHES.csv retains the full earlier scientific-reader inventory.

Required active changes include src/la_grid/revision/r1_stage7_harmonized.py and run_stage7_sovi_harmonization.py, the final Stage7 run-sequence verifier, Project_Visualizer/render_revised_stage7/make_manuscript_composites/refine_policy_cluster_presentation readers, and the canonical figure builder. Legacy PCA, five-class score/Top10, residential eligibility and eleven-feature assertions must stay explicitly historical, not silently accept the P2 table. Never fabricate SlowVulnerable_Hotspot_Score for compatibility.

The current official figure suite is still NCV14/H2/K3. It has17 numbered artwork pairs and continuously numbered supplements; the caption-only change made its packet21 pages. No current Fig07 or current FigS08 diagnostics has been replaced here. Current FigS09 is a different priority-context figure, so the requested legacy S9 replacement requires an explicit numbering crosswalk, not an accidental overwrite.

Author approval checklist: primary P2 and conditional K3 main/K4 mandatory sensitivity are accepted; B is preferred in principle and A retained. Remaining gates are final publication dimensions/accessibility handling, descriptive co-occurrence caption, useful NCV supplemental context, named manuscript/supplement targets and coordinated migration/rollback authorization. No formal Stage7 or manuscript/suite promotion is executed before those gates.
''')


if __name__=='__main__':main()
