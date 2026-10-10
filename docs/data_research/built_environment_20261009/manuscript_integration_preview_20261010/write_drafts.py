"""Write evidence-bounded integration drafts from validated saved tables."""
import argparse,json,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);a=ap.parse_args()
    repo=a.repo;root=repo/'docs/data_research/built_environment_20261009';out=root/'manuscript_integration_preview_20261010';s=root/'spatial_k4_validation_20261010';f=root/'final_feature_validation_20261010'
    p=pd.read_csv(out/'STAGE7_CLUSTER_PROFILES.csv').set_index('candidate_cluster');d=pd.read_csv(out/'CLASSIFIED_FEATURE_VALUES_2287.csv',dtype={'tract_id':str})
    sens=pd.read_csv(out/'SAVED_SENSITIVITY_SUMMARY.csv');runs=pd.read_csv(s/'SPATIAL_K4_RUNS.csv');opt=json.loads((out/'OPTIMIZATION_STABILITY_SUMMARY.json').read_text())
    freeze=json.loads((out/'STAGE7_CANDIDATE_FREEZE.json').read_text());unknown=pd.read_csv(out/'UNCLASSIFIED_TRACT_CHARACTERISTICS.csv',dtype={'tract_id':str})
    def write(name,text):(out/name).write_text(text.strip()+'\n',encoding='utf-8')
    def stat(model,k=4):return sens[(sens.model==model)&(sens.fixed_k==k)].iloc[0]
    recovery=[]
    for x,y in itertools.combinations(['B_480_hr','T80','Init_Supply'],2):
        v=d[[x,y]].dropna();recovery.append({'x':x,'y':y,'n':len(v),'Pearson':v[x].corr(v[y]),'Spearman':v[x].corr(v[y],method='spearman')})
    pd.DataFrame(recovery).to_csv(out/'CLASSIFIED_RECOVERY_CORRELATIONS.csv',index=False)
    methods=r'''
# Methods draft - Joint community typology

We characterized joint patterns of modeled electricity-service recovery, grid dependency and community conditions, rather than a residential-density classification or a predictive model. The primary analysis used 2,287 complete residential census tracts from the original 2,291-tract residential domain. Four tracts (06037189703, 06037301601, 06037301602 and 06037404600) lacked defensible physical-feature geometry and remained unclassified. Their available demographic and recovery measurements were retained, without imputing physical values or assigning cluster predictions. The full electricity-model domain contained 2,315 tracts, including 24 outside the residential typology.

Five conceptual domains entered the analysis: (1) cumulative modeled service loss and immediate post-event service availability; (2) tract-weighted substation degree, network impact, betweenness and dependency concentration; (3) land-use composition, building-footprint coverage and observed all-use building age; (4) social vulnerability; and (5) economic building stock and multi-hazard expected-loss propensity. Each domain contributed 20% of the squared-distance budget. This is equal weighting of five domains, not of the 12 individual coordinates or every underlying construct.

The recovery input was mean normalized cumulative service loss over 0-480 h, under 2pc50, the reference 57-crew condition, unit repair-duration multiplier, the direct-community sequence, production utility-compatible mapping and baseline source-connectivity/functionality gate. The same 1,000 saved physical evaluation realizations supplied recovery and initial-service measurements. If s_ir(t) is tract i's normalized modeled source-connected service availability in realization r, then

\[
B_i=\frac{1}{1000}\sum_{r=1}^{1000}\int_0^{480}[1-s_{ir}(t)]\,dt.
\]

The integral uses previous-state event steps and has units of equivalent complete-service-loss hours. B summarizes the whole evaluated trajectory; it is not a duration until threshold crossing. Initial service is the mean s_ir(0), a modeled service-availability proxy rather than delivered electricity, electrical MW capacity or continuous physical power. T80 remains descriptive: it is the first exact completion-event time when the mean tract trajectory reaches 80%, not the mean of individual-realization T80 values. All saved mean tract trajectories reached this threshold before 480 h. AUC over this same horizon equals 1-B/480 and was not included as a second recovery coordinate.

Grid features were retained from the production tract-substation dependency mapping: mapped degree, network impact and betweenness, plus the concentration index HHI of the normalized dependency shares. Higher HHI indicates more concentrated mapped dependence; it is not electrical redundancy in MW. These existing four descriptors were not redefined or recomputed.

SCAG 2019 Annual Land Use (ALU2019.1) supplied normalized land-use entropy across 11 mutually exclusive classified-land categories: -sum(p_j log p_j)/log(11). Category proportions refer only to classified parcel land, not the whole tract, and classified-land coverage was reported separately. Building-footprint coverage used geometrically unioned LARIAC6 footprints clipped to the validated tract land mask. Its 2020 release includes cumulative outlines predominantly originating from 2008 imagery; it does not establish a uniformly observed 2020 building stock. The all-use pre-1970 building-area fraction used original LARIAC4 2014 outlines and valid assessor-associated construction years. Its denominator is the area with observed valid ages, not all building area; observed-age coverage was reported separately. Residential ACS age and housing configuration were descriptive or sensitivity measurements, not substitutes for the primary all-use feature.

The separate social dimension retained the published SOVI_SCORE from archived FEMA NRI v1.19 (March 2023). Economic stock was log(1+NRI_BUILDVALUE), with stock in 2022 USD before transformation. ALR_NPCTL is the unadjusted national percentile of FEMA's composite multi-hazard expected annual loss rate. It ranks EAL-weighted component-rate percentiles, rather than a simple total-loss/total-exposure quotient. It contains loss and exposure information and is not a pure physical hazard measure. Neither the socially adjusted ALR percentile nor the composite NRI risk score was added. Published FEMA scores remained on their original scales before standardization. EAL_SCORE was reserved for a combined expected-loss/exposure sensitivity, preserving the same overall domain budget.

For coordinate j in domain d, we used z_ij=(x_ij-mu_j)/sigma_j, with whole-cohort means and population standard deviations (ddof=0), then multiplied z_ij by sqrt(0.2/p_d), where p_d is that domain's coordinate count. Only building stock was log-transformed in the primary model; B remained in raw hours. Population density, housing 5+ share, T80, EAL_SCORE and ACS residential age were excluded from the primary fitting coordinates. The clustering minimized within-class squared Euclidean distance in these weighted standardized coordinates (MacQueen, 1967; Lloyd, 1982), without PCA.

Existing controlled runs used scikit-learn 1.5.1 KMeans, the Lloyd algorithm, n_init=100, max_iter=500 and tol=1e-4. Seeds 42-61 each evaluated k=2-8; k was selected by maximum perpendicular distance below the endpoint chord of the normalized inertia curve, an operational elbow criterion (Thorndike, 1953). Silhouette was descriptive, not the selection rule. Both equal-domain D and EAL selected k=4 for all 20 seeds. The candidate uses the original full-cohort D seed-42 labels. C1-C4 map explicitly to its original integer identifiers 0-3; these identifiers imply no scientific ranking.

Optimization variability was distinguished from specification sensitivity and geographic sample sensitivity. The latter reused 20 previously specified deletions of two occupied 20-km EPSG:3310 centroid blocks per case (17 unique geographic deletion sets). For D and EAL at fixed k=4, each case refitted scaling and clustering on the remaining tracts, then predicted all 2,287 complete tracts. Each prediction was compared with that model's same-seed full-cohort partition. Class alignment used maximum one-to-one overlap on training tracts only; the same alignment applied to held-out and full cohorts. We reported ARI, retention, purity and Jaccard separately. ARI measures partition agreement, not classification accuracy, and these perturbations are not an independent validation cohort.

## References carried from the existing manuscript

- MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability, Vol. 1, 281-297.
- Lloyd, S. (1982). Least squares quantization in PCM. IEEE Transactions on Information Theory, 28(2), 129-137.
- Thorndike, R. L. (1953). Who belongs in the family? Psychometrika, 18(4), 267-276.

Dataset release details and source identifiers accompany VALIDATED_FEATURE_DEFINITIONS.csv and SOURCE_HASH_VERIFICATION.csv. New dataset bibliographic entries should be checked against the manuscript reference manager before insertion; no unverified author-year citation has been invented.
'''
    write('STAGE7_METHODS_DRAFT.md',methods)
    results=['# Results draft - Joint community typology','',
        'The four classes describe distinct combinations of modeled recovery and community attributes. They are retained as C1-C4 rather than assigned archetype names from small or unstable profile differences. Means below give equal weight to each tract; population shares use summed study population. Table 1 provides medians and coverage as well as means.']
    for c in p.index:
        r=p.loc[c]
        results+=['',f"{c} contains {int(r.n_tracts):,} tracts ({r.tract_share*100:.2f}% of classified tracts) and {int(r.population_sum):,} residents ({r.population_share*100:.2f}% of classified population). Mean service loss is {r.B_480_hr_mean:.3f} h (median {r.B_480_hr_median:.3f} h), and mean descriptive T80 is {r.T80_mean:.3f} h. Mean social-vulnerability score is {r.SOVI_SCORE_mean:.2f} (median {r.SOVI_SCORE_median:.2f}). Mean classified-land entropy is {r.land_use_entropy_mean:.3f}, mean footprint coverage is {r.building_footprint_coverage_mean*100:.2f}%, and mean observed-age pre-1970 building-area share is {r.all_use2014_pre1970_area_share_mean*100:.2f}%. Median building stock is ${r.NRI_BUILDVALUE_median/1e6:.2f} million and median loss-rate percentile is {r.ALR_NPCTL_median:.2f}."]
    results+=['',
        'C1 and C4 both have comparatively high social-vulnerability scores, but differ substantially in land-use mix and observed building age. C1 has lower entropy and a higher pre-1970 share than C4. C3 has the largest mean cumulative service loss and descriptive T80, yet its mean social-vulnerability score is much lower than C1 and C4. Modeled recovery delay and social vulnerability therefore do not form a single ordering. These joint associations do not establish that building form or social conditions caused recovery outcomes.',
        '',f"C2 is the 34-tract subgroup (1.49% of classified tracts). Its mean initial modeled service availability is {p.loc['C2','Init_Supply_mean']*100:.3f}%, compared with {p.loc['C1','Init_Supply_mean']*100:.3f}%, {p.loc['C3','Init_Supply_mean']*100:.3f}% and {p.loc['C4','Init_Supply_mean']*100:.3f}% in C1, C3 and C4. It has the lowest mean service loss. Higher initial availability is relative to these other groups: even C2's mean is only about 1.8%, and it is not a continuously powered or universally resilient community class. Its mean SOVI of 67.99 and median of 85.04 also caution against describing all its members as low vulnerability.",
        '',
        'Under the 20 spatial perturbation cases, full-cohort ARI had median 0.9234 and minimum 0.7522 for D, and median 0.9458 and minimum 0.8666 for EAL. The corresponding fifth-percentile values were 0.8278 and 0.8728. These summarize tested spatial sensitivity, not percentages of correctly classified tracts or population confidence limits.',
        '',
        'The largest small-class expansion occurred for seed 54, deleting blocks 7:-23 and 7:-24. Only four of its original 34 members remained in training. Full-cohort predictions retained all 34, but the aligned class expanded to 92 tracts under D and 90 under EAL. Purity consequently fell to 36.96% and 37.78%; retention remained 100%. This is a sparse-support loss of class specificity, rather than disappearance of the original group. Broad large-class profile differences persist, while some fine rankings reverse: D C1/C4 degree and network-impact differences reverse in 12/20 cases. These rankings should not define class names.',
        '',f"The four unclassified residential tracts contain {int(unknown.formal_population.sum()):,} residents. Their known service loss spans {unknown.B_480_hr.min():.3f}-{unknown.B_480_hr.max():.3f} h and T80 spans {unknown.T80.min():.3f}-{unknown.T80.max():.3f} h; each has zero initial modeled service. They remain explicitly outside class summaries, with their measurements reported separately."]
    write('STAGE7_RESULTS_DRAFT.md','\n'.join(results))
    # Weight sensitivity requires a separate reference, not each model against itself.
    zd=np.load(f/'run_records/D__equal_five_domains.npz');zi=np.load(f/'run_records/D__inherited.npz')
    weight_ari=[adjusted_rand_score(zd[f's{x}_k4'],zi[f's{x}_k4']) for x in range(42,62)]
    pd.DataFrame({'seed':range(42,62),'fixed_k':4,'n':2287,'equal_D_vs_inherited_D_ARI':weight_ari}).to_csv(out/'DOMAIN_WEIGHT_SENSITIVITY.csv',index=False)
    supp=f'''
# Supplementary Methods and Results draft

## Three distinct kinds of stability

Optimization stability repeats the same feature specification on the same full cohort with seeds 42-61. At k=4, median pairwise ARI across the 190 seed pairs was {opt[0]['pairwise_ARI_median']:.4f} for D (minimum {opt[0]['pairwise_ARI_min']:.4f}) and {opt[1]['pairwise_ARI_median']:.4f} for EAL (minimum {opt[1]['pairwise_ARI_min']:.4f}). Seed pairs are dependent summaries, not 190 independent experiments or sampling-confidence intervals. This does not resolve uncertainty in feature meaning or geographic sampling.

Specification comparisons use existing saved labels only. The full controlled study had 20 model specifications, 20 seeds and seven k values (2,800 recorded fits). This preview performs no additional cluster fitting. SAVED_SENSITIVITY_SUMMARY.csv reports fixed-k=4 and fixed-k=5 comparisons separately, with their actual reference and selected-k counts. Results at k=5 do not substitute for validation of the chosen k=4 candidate.

## Loss/exposure construct and recovery metric

Replacing separate log building stock and ALR with EAL_SCORE under the same 0.2 domain budget gives median fixed-k4 ARI {stat('EAL__equal_five_domains').ARI_median:.4f} against D. Both specifications select k=4 in all 20 seeds, but the larger classes differ. The seed-42 34-member subgroup is identical in both models. D preserves stock and multi-hazard loss propensity as separately interpretable coordinates; EAL combines expected loss and exposure. Better ARI or silhouette is not the scientific reason for selecting either representation.

Substituting T80 for raw B, with initial service and all other domains held constant, gives median k4 ARI {stat('D_T80__equal_five_domains').ARI_median:.4f}. On the same 2,287 tracts, B-T80 Pearson correlation is {recovery[0]['Pearson']:.4f} and Spearman correlation is {recovery[0]['Spearman']:.4f}. They describe related recovery information but different estimands: an integrated deficit versus an 80% crossing of the mean trajectory. We use B because cumulative service loss is the study's substantive recovery quantity, not because it maximizes clustering performance. Replacing raw B by log1p(B) gives median k4 ARI {stat('D_logB__equal_five_domains').ARI_median:.4f}; it is a transformation sensitivity, not authorization to change the primary raw-hour input.

## Building age and domain weights

Replacing all-use 2014 observed-age share with the ACS residential pre-1970 housing share gives median fixed-k4 ARI {stat('D_ACS_age__equal_five_domains').ARI_median:.4f}; omitting age gives {stat('D_no_age__equal_five_domains').ARI_median:.4f}. Both age alternatives select k=5 in all 20 seeds, unlike the primary equal-domain D k=4. They change the physical construct and selected resolution. Omitting age redistributes the unchanged physical-domain budget across entropy and footprint coverage rather than reducing that entire domain's importance.

Inherited domain budgets were recovery/initial service 2/11, grid 4/11, built environment 2/11, social 1/11 and loss/exposure 2/11. Equal-five-domain weighting assigns 0.2 to each domain. At fixed k=4, median ARI between D under these two budgets is {np.median(weight_ari):.4f} (range {min(weight_ari):.4f}-{max(weight_ari):.4f}). Inherited D selects k=5 in all 20 seeds. The weighting decision therefore changes representation as well as selected resolution and must be stated rather than treated as a neutral preprocessing detail.

## Incomplete land classification and age observations

Existing SCAG missing-land scenarios allocate unclassified area to transportation, to the dominant class, or proportionally to classified categories. These are deliberately different measurement assumptions, not new observed land use. Under the inherited budget at fixed k=5, median ARI relative to inherited D is {stat('D_entropy_transport__inherited',5).ARI_median:.4f}, {stat('D_entropy_dominant__inherited',5).ARI_median:.4f} and {stat('D_entropy_proportional__inherited',5).ARI_median:.4f}, respectively. Proportional allocation leaves entropy unchanged and is not an independent replication. Corresponding fixed-k4 records are available, but this sensitivity family uses inherited weights and is not a direct equal-domain-primary robustness test.

Age lower/upper bounds treat missing observed-age footprint area as entirely post-1970 or pre-1970. Under inherited weights at fixed k=5 their median ARIs are {stat('D_age_lower_bound__inherited',5).ARI_median:.4f} and {stat('D_age_upper_bound__inherited',5).ARI_median:.4f}. These bound incomplete age observations and do not validate missing government-building years. No new equal-domain missing-land/age-bound factorial comparison was run, so that scope remains a limitation.

## Fixed-k4 geographic perturbations

Each model used the same 20 predefined spatial cases, with 17 unique geographic deletion sets, not IID tract bootstrap. The 20-km blocks were defined in EPSG:3310 from the original centroid positions. Two of 15 occupied blocks were deleted per case; training size ranged from 1,753 to 2,270 and held-out size from 17 to 534. Scaling and centroids were estimated only on training tracts in the earlier spatial study. Labels were aligned by one-to-one training overlap and that mapping was carried unchanged to the full and held-out cohorts. Statistical references were each seed's own saved full-cohort labels; display IDs were aligned within each model to its seed-42 partition and do not identify identical communities across D and EAL.

Member retention is intersection/baseline membership; purity is intersection/predicted membership; Jaccard is intersection/union. In seed 54's small-class case all 34 original members remain, but 58 other tracts join under D and 56 under EAL. This gives retention 1 and purity/Jaccard 34/92 or 34/90. No case lacked all training support; sparse support must not be described as zero support. Class-level summaries, raw contingency tables and feature shifts accompany the prior validation package. The combined profile is descriptive and cannot validate causal effects of variables also used to construct the partition.
'''
    write('STAGE7_SUPPLEMENTARY_DRAFT.md',supp)
    discussion='''
# Discussion and limitations draft

The candidate typology brings cumulative electricity-service loss, immediate service, grid dependence and community conditions into one explicitly weighted description. The contrast between high-SOVI classes and a lower-SOVI class with slower modeled recovery demonstrates why recovery vulnerability should not be collapsed into a single socioeconomic ordering. It does not establish causal pathways from built environment to service restoration; recovery outcomes themselves are clustering inputs.

ALR represents multi-hazard modeled expected-loss propensity, not pure seismic hazard. FEMA's component-rate percentile construction contains loss/exposure information, and low marginal correlation does not imply independence from social or economic conditions. The archived audit across 2,291 residential tracts found earthquake accounted for 98.1563% of pooled FEMA expected annual loss (median tract share 99.2745%). This is a multi-hazard index with a locally earthquake-dominated composition, not evidence for equal importance of all hazards. These figures describe the archived 2,291-tract FEMA audit, not a newly recomputed 2,287-tract statistic. Building stock is an exposure measure, not income or wealth.

The physical coordinates have qualified coverage and vintages. SCAG entropy concerns classified parcel land only; unclassified land may have a different mix. Footprint release year does not establish image-acquisition year, and LARIAC6 outlines include older imagery. LARIAC4 age concerns 2014 stock with valid observed years; missing-age area and use-dependent completeness, especially government properties, prevent describing it as a complete all-building age census. ACS residential age is a distinct housing-unit measurement. Coverage tables and sensitivity scenarios remain essential when interpreting class differences.

Four unresolved residential land geometries remain unclassified. Complete-case class shares use 2,287 tracts and their population, not all 2,291 residential tracts or all 2,315 electricity-model tracts. This explicit exclusion is preferable to imputing a geographic measure with no defensible support, but does not remove the possibility of selection effects.

The 34-tract class has low mean modeled service loss and relatively higher initial availability, yet its initial availability remains low in absolute terms. Under deletion of its main spatial support, four training members still define a class that absorbs 58 additional D-model tracts. Perfect member retention therefore does not imply stable specificity. The small group's exact boundary and profile should be presented as specification-dependent; universal resilience or continuous power is not supported. Minor class rankings also reverse under perturbation, notably the nearly equal C1/C4 grid-degree and network-impact profiles.

Optimizer seed agreement, model-definition sensitivity and spatial sample stability answer different questions. Twenty seeds do not constitute independent scientific validation; ARI is not classification accuracy. The tested block deletions are finite perturbations of the same dataset, not new geographic evidence. The four classes are not an invariant or unique taxonomy. Spatial patterns can inform hypotheses and further review, but they do not establish intervention priorities, clinical capacity, electrical adequacy or a causal rationale for funding allocations. No new hotspot ranking follows from freezing this candidate.

The original five-class interpretation cannot be transferred by class number. It used a different feature/model specification, and several class profiles in the older manuscript no longer correspond to current formal stored labels. The candidate should be integrated as an explicitly revised descriptive analysis, with old archetype claims rewritten from the new raw profiles and any hotspot definition reviewed separately.
'''
    write('STAGE7_DISCUSSION_LIMITATIONS_DRAFT.md',discussion)
    # Compact reader-facing tables complement full machine-readable statistics.
    table=['# Candidate cluster profile tables','',
        'Statistics below are unweighted across tracts unless stated otherwise. Fractions are shown as percentages. Population is summed, and shares use only the classified universe. CSV files retain raw fractions and full precision. These are member descriptions, not confidence intervals.','',
        '| Class | Tracts (% classified) | Population (% classified) | Service loss mean / median (h) | T80 mean / median (h) | Initial service mean / median (%) | Exact-zero initial service (%) | SOVI mean / median |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for c,r in p.iterrows():
        table.append(f'| {c} | {int(r.n_tracts):,} ({r.tract_share*100:.2f}) | {int(r.population_sum):,} ({r.population_share*100:.2f}) | {r.B_480_hr_mean:.3f} / {r.B_480_hr_median:.3f} | {r.T80_mean:.3f} / {r.T80_median:.3f} | {r.Init_Supply_mean*100:.4f} / {r.Init_Supply_median*100:.4f} | {r.Init_Supply_zero_fraction*100:.2f} | {r.SOVI_SCORE_mean:.2f} / {r.SOVI_SCORE_median:.2f} |')
    table+=['','| Class | Entropy mean / median | Classified-land coverage median (%) | Footprint coverage mean (%) | Observed-age pre-1970 share mean (%) | Valid-age coverage median (%) | Building stock median (million 2022 USD) | ALR median |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    for c,r in p.iterrows():
        table.append(f'| {c} | {r.land_use_entropy_mean:.3f} / {r.land_use_entropy_median:.3f} | {r.land_use_classified_land_coverage_median*100:.2f} | {r.building_footprint_coverage_mean*100:.2f} | {r.all_use2014_pre1970_area_share_mean*100:.2f} | {r.all_use2014_age_coverage_median*100:.2f} | {r.NRI_BUILDVALUE_median/1e6:.2f} | {r.ALR_NPCTL_median:.2f} |')
    table+=['','| Class | Mapped degree mean | Mapped impact mean | Mapped betweenness mean | HHI mean | Population density mean (persons/km2) | Population-weighted service loss (h) |',
            '|---|---:|---:|---:|---:|---:|---:|']
    for c,r in p.iterrows():
        table.append(f'| {c} | {r.Grid_Degree_mean:.4f} | {r.Grid_Impact_mean:.5f} | {r.Grid_Betweenness_mean:.5f} | {r.Redundancy_HHI_mean:.4f} | {r.Pop_Density_per_km2_mean:.2f} | {r.B_480_hr_population_weighted_mean:.3f} |')
    table+=['','T80 is the threshold of the mean trajectory. Stock is total tract building exposure, not household income. The final service-loss column alone weights tracts by population; it must not replace the unweighted primary profile.','',
            '| Unclassified GEOID | Population | Service loss (h) | T80 (h) | Initial service | SOVI |', '|---|---:|---:|---:|---:|---:|']
    for _,r in unknown.iterrows():table.append(f'| {r.tract_id} | {int(r.formal_population):,} | {r.B_480_hr:.3f} | {r.T80:.3f} | {r.Init_Supply:g} | {r.SOVI_SCORE:.2f} |')
    write('STAGE7_PROFILE_TABLES.md','\n'.join(table))
    cross=pd.read_csv(out/'STAGE7_OLD_NEW_CROSSWALK.csv')
    disposition=f'''
# Original Stage 7 interpretation crosswalk

The statistical comparator is the authoritative formal SOVI-harmonized five-class label file, not the older manuscript's class prose. The manuscript inspected was provenance/legacy_outputs/Submission_Package/Manuscript_IJDRR.docx, whose Section 2.6 and Section 3.4 describe the older five-class framework. Its class numbers and narrative are not assumed to describe the harmonized source correctly. On the 2,287 common residential tracts, original-versus-candidate ARI = {freeze['original_to_candidate_ARI']:.6f}. This is a descriptive comparison, never an optimization target.

{cross.pivot(index='original_cluster',columns='candidate_cluster',values='n_intersection').to_markdown()}

STAGE7_OLD_NEW_CROSSWALK.csv contains every cell's fraction of original membership and fraction of candidate membership, the four excluded original members and both denominator definitions. Original cluster 5 maps entirely to C2 (34/34). This correspondence preserves membership, not its former characterization as slower/high-density/high-grid-centrality: C2 now has the lowest service loss and lower mapped degree/betweenness than the larger groups. The formal label numbering and older manuscript description therefore cannot be treated as an authoritative semantic match.

| Previous interpretation | Disposition for integration |
|---|---|
| Recovery delay and social vulnerability do not share one ranking | Retain the broad descriptive point: C3 has higher loss/T80 but much lower mean SOVI than C1/C4. No causal claim. |
| Old C1-C5 archetype names, colors and numbered comparisons | Withdraw direct transfer. Most old classes split; C1-C4 are explicitly new IDs tied to raw saved labels. |
| Old fastest class has particularly high impact centrality | Rewrite. Candidate C2 has mean mapped impact 0.02870, below the three large classes; it is characterized by relatively higher initial service and lower loss. |
| Slowest group is not necessarily the most socially vulnerable | Retain, with candidate C3's reproduced means, not the old class number. |
| Old C3/C5 comparison of dense, vulnerable groups with different recovery | Rewrite from the new profiles; the old source partition and older prose do not identify the same joint groups. |
| Top-10 hotspots concentrate in old class 5 with others in 1/3 | Do not carry forward. No candidate hotspot score/rank was calculated, and no new hotspot boundary or intervention priority is authorized. |
| Structural influence or built environment explains recovery causally | Withdraw causal phrasing. These are variables in a descriptive joint classification. |

The crosswalk cannot validate the new typology or establish that the old one was scientifically wrong. Changed inputs, domain weights and four rather than five classes change the question and its partition.
'''
    write('OLD_INTERPRETATION_DISPOSITION.md',disposition)
    captions='''
# Figure captions for integration review

## Figure A - Spatial joint community typology

Four-class joint typology of 2,287 complete residential tracts under 2pc50, the reference 57-crew/unit-duration condition and direct-community recovery sequence. Classes use the five equal analytical domains in the Methods; C1-C4 denote saved seed-42 membership and imply no ranking. Four residential tracts with unresolved physical-feature geometry are gray and unclassified. The 24 tracts outside the residential domain are white. Boundaries are archived census-tract polygons within the exact 2,315-tract electricity-model domain, projected in California Albers (EPSG:3310); the outer outline is the study-tract union, not an invented utility boundary. The scale bar is in km and the arrow follows geographic north at its mapped position. This is descriptive spatial classification, not causal attribution or validated intervention priority.

## Figure B - Joint cluster profiles

Tract-unweighted means of the 12 primary coordinates after standardization across the same 2,287 classified tracts (whole-cohort mean zero, population standard deviation one). Five grouped row blocks represent recovery/initial service, grid dependency, built environment, social vulnerability and economic stock/multi-hazard loss. The heatmap shows unweighted coordinate z scores for visual comparison, not the sqrt-domain-weighted values used for clustering. Cell annotations retain actual standardized means; colors saturate outside +/-1.5 standard deviations, indicated by colorbar extensions, including the C2 initial-service mean (+7.15). Building stock is log1p-transformed before standardization. Labels identify the underlying measurements; the color scale is dimensionless, not hours, fractions or dollars. Raw means, medians, units and observation coverage are in the companion profile tables. T80 and population density are descriptions outside the primary coordinates.

## Figure C - Spatial stability and small-class specificity

(A) Full-cohort ARI for 20 predefined block-deletion cases per model, using each model/seed's saved complete-cohort k=4 labels as reference. Points are individual cases; boxes show quartiles and median, with conventional 1.5-IQR whiskers and all case values plotted. The 20 cases include 17 distinct geographic deletion sets, and are not independent validation data or accuracy estimates. (B) Median retention (circles) and Jaccard (squares), with minimum-maximum ranges across the 20 cases. Classes are aligned by maximum training overlap; display IDs refer to each model's own seed-42 partition, so identically numbered D/EAL large classes are not identical tract sets. Ranges are not confidence intervals. (C) The seed-54 sparse-support case: only four of the original 34 small-class members remain in training. All 34 are retained in full-cohort predictions, but the class contains 92 D-model tracts or 90 EAL-model tracts; purity is 36.96% or 37.78%. Blue shows original members; orange shows additional members. (D) Geographic membership expansion in the D model for that same case, with the same blue/orange coding and archived tract boundaries. The map is cropped to the expanded group's actual bounds for readability; background tracts have no class meaning in this panel. Retention, purity and Jaccard quantify different properties; retained original membership alone does not establish a stable class boundary.
'''
    write('FIGURE_CAPTIONS.md',captions)
    review='''
# Manuscript integration review

This directory is an isolated author-review preview. It does not replace formal Stage 7, manuscript material, figures or hotspot results.

## Files ready for author review

- STAGE7_CANDIDATE_FREEZE.json and STAGE7_CANDIDATE_PARAMETERS.npz: source commits/hashes, exact tract order, labels, transformations, domain factors and reconstructed preprocessing. No new KMeans fit. Original scaler/algorithm centers were not serialized; label-member centers are explicitly identified as reconstructed, reproduce every original assignment and reproduce the selected run's inertia within tolerance.
- STAGE7_CANDIDATE_LABELS_2291.csv: exact 2,287 saved seed-42 labels and four UNCLASSIFIED_GEOMETRY records; no predicted or imputed labels.
- STAGE7_CLUSTER_PROFILES.csv, STAGE7_PROFILE_TABLES.md and UNCLASSIFIED_TRACT_CHARACTERISTICS.csv: raw-unit statistics, explicit population summaries and all four excluded tracts.
- STAGE7_OLD_NEW_CROSSWALK.csv and OLD_INTERPRETATION_DISPOSITION.md: common-domain contingency, ARI and interpretation changes, including the old manuscript/source-label semantic discrepancy.
- Three vector PDFs and 600-dpi PNGs, with captions in FIGURE_CAPTIONS.md: map, joint profiles and spatial stability/small-class expansion.
- Four section drafts: Methods, Results, Supplementary and Discussion/Limitations. The existing manuscript was read, not edited. New dataset bibliographic entries remain an editorial reference-manager check.
- Reproducible scripts, SOURCE_HASH_VERIFICATION.csv, OUTPUT_HASHES.csv, tests, VISUAL_QA.json and preservation checks.

## Claims supported with qualifications

The large-class contrast of modeled service loss versus social vulnerability, older observed buildings versus more mixed classified land use, and the relatively higher-initial-service 34-tract class can enter integration review as descriptive joint patterns. Optimizer seed agreement and broad spatial partition agreement are supported. Neither establishes causal effects, universal validation or an invariant taxonomy.

The C2 geographic boundary/profile is sensitive when only four members remain in spatial training; all original members survive but purity falls substantially. Fine C1/C4 grid rankings reverse in 12/20 cases. SCAG coverage, older imagery, partial 2014 age coverage and earthquake-dominated multi-hazard loss must remain visible. Old class names and old hotspot narratives must be rewritten or excluded from this candidate integration.

## Remaining scientific adoption gates

No missing numerical evidence blocks delivery of this preview: labels, source hashes, model matrix and raw profiles reproduce. Scientific qualifications remain substantive, especially the complete-case exclusion of four residential geometries and sparse-support contamination of the 34-tract group. The author must accept these limited descriptions before any formal replacement. Equal-domain missing-land/age-bound perturbations were not newly fitted; existing inherited-weight sensitivities cannot be called direct validation of the primary specification. No new hotspot score or intervention-response model is part of this preview. A future hotspot update requires a separate approved definition.

No formal Stage 7 labels, PCA, scientific source arrays, manuscript, existing figures, schedules, physical samples or GA results were modified. This round stops at the integration preview.
'''
    write('MANUSCRIPT_INTEGRATION_REVIEW.md',review)
    write('README.md','''# Stage 7 manuscript integration preview

Start with MANUSCRIPT_INTEGRATION_REVIEW.md, STAGE7_PROFILE_TABLES.md and FIGURE_CAPTIONS.md. Open the three FIG_STAGE7 PDFs at their native 185-mm width.

Candidate: D, five equal domains, k=4, seed 42, exact saved full-cohort labels. Classified residential sample: 2,287. Master labels: 2,291 with four explicitly unclassified records. No promotion or new clustering.

Reproduce from the repository root with:

```
python docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010/build_preview.py --repo .
python docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010/render_preview.py --repo .
python docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010/write_drafts.py --repo .
python -m pytest docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010/test_preview.py
```

Arial is required for the PDF renderer; no font files are distributed. The source commits and exact bytes are recorded; SOURCE_HASH_VERIFICATION.csv explicitly distinguishes payload hashes from Git text normalization. Display identifiers map source 0-3 to C1-C4 with no reordering.
''')
    print('Four section drafts, captions, publication tables and interpretation crosswalk written.')

if __name__=='__main__':main()
