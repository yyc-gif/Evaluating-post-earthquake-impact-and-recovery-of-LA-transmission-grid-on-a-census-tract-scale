"""Read saved scientific evidence and actual manuscript OOXML; no estimator fits."""
import json,zipfile,re,hashlib
import numpy as np
import pandas as pd
from lxml import etree as E
from common import *

S19=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_manuscript_rebuild\LA_Grid_Manuscript_Resubmission_Rebuild.docx')
assert sha(S19)=='a61472ed6918f505dfd0c26b88ce24f9d184f6dca076194b5032014142acd253'
record(S19,sha(S19),'author-confirmed S19; byte-identical to confirmed source','AUTHOR_CONFIRMED_S19')

METHODS=[
"We characterized communities using a joint descriptive classification of recovery and initial modeled service, grid dependency, built environment, social vulnerability, and economic stock and multi-hazard expected-loss propensity. The recovery coordinate B is the tract mean normalized cumulative modeled service deficit over 0–480 h, averaged over the existing 1,000 2pc50 realizations under C57/D1 and the direct-community sequence, production utility-compatible mapping and baseline source-connectivity gate. Init_Supply is the saved initial modeled service measure. B summarizes the full evaluation horizon; T80 is retained only for description and is not a clustering coordinate. Recovery and initial service are inputs to this classification, so their between-class differences do not independently validate it.",
"The twelve coordinates were B, Init_Supply, mapping-weighted Grid_Degree, Grid_Impact, Grid_Betweenness and Redundancy_HHI; EMC2022 total built-land fraction, ACS 2022 five-year share of housing units in structures with five or more units, SCAG2020 classified-parcel land-use entropy; FEMA SOVI_SCORE; log1p(BUILDVALUE); and ALR_NPCTL. Grid_Impact is the dependency-weighted network λ2-impact descriptor. These grid measures describe modeled dependency, not delivered electricity or electrical capacity. EMC uses Sentinel-2 observations from 2022 in the JRC EMC-BUILT R2025A product. ACS describes housing units over 2018–2022, not building counts. SCAG entropy describes the classified parcel land in the 2020 inventory, including carried-forward 2019 classifications; it does not represent all tract land. FEMA NRI v1.19 (March 2023) supplies social vulnerability, monetary building stock and the unadjusted composite annualized loss-rate percentile. ALR is multi-hazard expected-loss propensity, not pure hazard intensity. Building age and population density are not primary coordinates.",
"We standardized each coordinate using the saved full-cohort StandardScaler mean and population standard deviation, then multiplied it by sqrt(w/q), where w is its domain's squared-distance budget and q its number of coordinates. W1 assigns 0.20 each to recovery/service, grid, physical and social domains, and 0.10 each to stock and ALR. Thus stock and loss propensity share a 0.20 parent budget while remaining separate measurements. Coordinates share their own domain budget equally. This convention expresses a declared conceptual balance, not empirically optimal weights. We used the previously selected four-class K-means solution (seed 42, n_init=100, max_iter=500, tol=10⁻⁴, Lloyd algorithm; scikit-learn 1.5.1), without PCA reduction. Of the 2,291 residential tracts, 2,287 have complete inputs; four unresolved geometry records remain unclassified without imputation. The other 24 tracts in the 2,315-tract electricity-model domain are outside this residential typology cohort.",
"We assessed optimization sensitivity using the twenty saved seeds 42–61 and specification sensitivity using four registered alternative weight conventions. Geographic sensitivity used twenty registered 20-km spatial-block deletion cases representing seventeen unique deletion sets. Each saved spatial fit estimated its scaler and centroids on retained training tracts and predicted the complete cohort. Class alignment used maximum training-set overlap only; held-out labels were not used to select the mapping. We report raw contingency tables, ARI, retention, purity and Jaccard. These perturbations test sample sensitivity and are not independent geographic validation. Class identifiers C1–C4 refer only to this specification."
]
RESULTS=[
"Under CORE3/W1, the 2,287 classified tracts formed groups of 650 (C1), 802 (C2), 801 (C3) and 34 (C4), containing 2,441,616, 3,143,470, 3,327,909 and 124,158 mapped residents, respectively (temporary Figures 7–8 and Table 4). Tract-mean cumulative modeled service loss was 36.25, 35.21, 31.09 and 23.60 h. Mean SOVI_SCORE was 31.14, 84.16, 77.51 and 67.99. C1 therefore combined lower social vulnerability with greater modeled service loss than C2 and C3 within this specification; this co-occurrence does not imply that vulnerability causes recovery differences.",
"C2 had larger mean built-land fraction (0.331), five-or-more-unit housing share (0.506) and classified-land entropy (0.453) than C3 (0.301, 0.214 and 0.301). C1 had the greatest median monetary building stock ($667.14 million), compared with $484.27 million for C2, $350.34 million for C3 and $389.58 million for C4. Median ALR percentiles were 79.24, 89.04, 75.19 and 69.55. These quantities characterize different physical and economic dimensions; their alignment is conditional on the selected weights. Median classified-land coverage was 0.764, 0.748, 0.750 and 0.715, respectively, and entropy excludes unclassified land. All means here weight tracts equally; Table 4 separately identifies population-weighted service loss.",
"The twenty optimization seeds gave a median pairwise ARI of 1.0000 and minimum 0.9987 (190 seed pairs). Registered W1 spatial deletions gave median ARI 0.8792, minimum 0.6929, and at most 255 reassigned tracts after training-based alignment. C1's greater mean loss than C3 was retained in all 20 W1 spatial cases and all 80 full-cohort W2–W5 comparisons. Some class rankings did not persist: the C2–C3 mean service-loss and SOVI ordering reversed in all 20 full-cohort stock-emphasis W5 comparisons. Median same-seed reassignment relative to W1 was 12.33%, 34.50%, 5.99% and 23.87% for W2–W5. Consequently the four classes are a conditional descriptive partition, not a stable universal taxonomy.",
"C4's initial modeled service mean was 0.01815 (1.815%), higher than the other class means but far from continuously available service. Under a deletion leaving only four original C4 members in training, the W1 matched prediction retained all 34 original members but expanded to 92 tracts, with 36.96% purity and Jaccard overlap. Retention therefore did not establish membership specificity. We retain C4 as a specification-dependent subgroup and do not assign it a stable resilience archetype or a class-based intervention priority. The four unresolved residential tracts, containing 12,390 mapped residents, remain unclassified."
]
DISCUSSION=[
"The joint classification describes where modeled recovery, physical form, vulnerability and economic loss propensity co-occur. Its strongest W1 contrasts support tract-group descriptions; they do not isolate a built-environment effect or independently validate recovery, which is itself an input. Social and recovery/service coordinates accounted for median shares of 39.98% and 29.15% of weighted between-class separation across the twenty W1 fits; physical, ALR, stock and grid shares were 11.07%, 11.44%, 5.99% and 2.38%. These observed contributions differ from the nominal distance budgets. Weak between-class grid separation does not establish that grid dependency is irrelevant or redundant.",
"Interpretation remains conditional on fixed k=4 and the W1 conceptual hierarchy. Reasonable alternative weights change substantial membership and some recovery and vulnerability rankings, while sparse spatial support reduces the specificity of the 34-tract subgroup. Geographic deletions are dependent perturbations of this study population. EMC cell resolution and boundary support, ACS sampling uncertainty, SCAG partial classified-land coverage and carried-forward records, and FEMA vintage and loss construction limit the physical and economic descriptions. ALR represents multi-hazard loss propensity, whose regional composition is strongly earthquake-dominated; it is not a tract shaking variable. Four unresolved residential geometry records remain unclassified. The previous five-class names, age/density interpretations, PCA presentation and hotspot-by-class recommendations do not transfer to CORE3/W1. Existing restoration-policy and SOVI-quartile comparisons remain separate analyses."
]
CAPTIONS={
 'FIG_CORE3_W1_MEMBERSHIP':"Temporary Figure 7. CORE3/W1 residential tract membership. The saved four-class seed-42 partition classifies 2,287 of 2,291 residential tracts using twelve standardized coordinates and W1 squared-distance budgets. Gray denotes the four geometry-unresolved residential tracts; white denotes the 24 tracts outside the residential cohort, not necessarily tracts without residents. Boundaries are the archived study tract polygons, not utility service territories. CORE3 combines 2022 EMC built surface, ACS 2018–2022 housing structure and SCAG2020 classified-parcel composition; these measurements are not fully contemporaneous. Class membership is descriptive and specification-dependent.",
 'FIG_CORE3_W1_PROFILES':"Temporary Figure 8. CORE3/W1 joint profiles. Cells show unweighted tract-mean standardized coordinates relative to the 2,287-tract reference scaler, solely for visual comparability. Numeric annotations show the actual z values; color saturates outside ±2.5. The clustering itself uses W1 domain weights, not this unweighted color scale. Columns show the saved four classes (seed 42). Table 4 reports original-unit means and medians. B and initial modeled service are classification inputs, so their class differences are not independent validation or causal effects. EMC2022, ACS 2018–2022, SCAG2020 and FEMA v1.19 have distinct observation scopes and restrictions.",
 'FIG_CORE3_W1_STABILITY':"Temporary Supplementary Figure S_CORE3_STABILITY. Registered weight and geographic sensitivity at fixed k=4. A shows all twenty saved spatial-deletion ARIs per scheme, with median and minimum; cases represent seventeen unique deletion sets and are not independent validation. B shows same-seed full-cohort reassignment relative to W1 after overlap alignment (twenty seeds). C shows median observed between-class separation shares, distinct from nominal squared-distance budgets. Empirical ranges are not confidence intervals. W2 separates stock and ALR parent budgets; W3 is inherited; W4 and W5 emphasize ALR and stock within a combined 0.20 budget, respectively.",
 'FIG_CORE3_W1_MINORITY':"Temporary Supplementary Figure S_CORE3_MINORITY. Specificity of the exact 34-tract W1 reference subgroup. A compares W1 spatial retention and purity across twenty cases. B shows the adverse seed-54 deletion (blocks 7:-24 and 7:-23), leaving four original members in training: all 34 original members remain in the matched 92-tract full prediction, which absorbs 58 other tracts (36.96% purity and Jaccard). C reports where those original 34 tracts are predicted under the same deletion for W2–W5; a zero one-to-one matched retention does not imply that tracts disappear. Alignment uses training overlap only. This subgroup has specification-dependent boundaries and does not support a stable resilience archetype.",
 'TABLE_CORE3_W1_PROFILES':"Temporary Table 4. Original-unit CORE3/W1 class profiles (fixed k=4, seed 42, 2,287 classified residential tracts). Entries are unweighted tract means [medians] unless otherwise stated. Population is the sum of saved mapping populations; population-weighted service loss is identified separately. Log stock is the fitted coordinate; original monetary stock is also reported. T80 and measurement coverage are descriptive, not additional clustering inputs. B is mean normalized modeled service loss over 0–480 h for the saved 2pc50/C57/D1 direct-community trajectories. Four unresolved residential tracts are reported separately and receive no class. No intervals in this table represent confidence intervals."
}
METHODS[0]=METHODS[0].replace('T80 is retained only for description and is not a clustering coordinate.','T80 is the first exact completion-event crossing of 0.8 by the mean tract service trajectory, not the mean of realization-specific crossing times; it is retained only for description and is not a clustering coordinate.')
CAPTIONS['TABLE_CORE3_W1_PROFILES']+=' T80 summaries are across tract mean-trajectory crossing times, not across realization-specific T80 values.'
dump('REVIEW_TEXT_AND_CAPTIONS.json',dict(methods=METHODS,results=RESULTS,discussion=DISCUSSION,captions=CAPTIONS))
for name,paras in [('METHODS',METHODS),('RESULTS',RESULTS),('DISCUSSION_LIMITATIONS',DISCUSSION)]:text('STAGE7_'+name+'_AUTHOR_REVIEW.md','\n\n'.join(paras))
text('REVIEW_FIGURE_CAPTIONS.md','\n\n'.join(CAPTIONS.values()))

q=json.loads(lp(OUT/'INDEPENDENT_SCIENTIFIC_QA.json').read_text())
p=pd.read_csv(lp(OUT/'CORE3_W1_PROFILE_TABLE.csv'))
memo=f"""# CORE3 W1 scientific adoption decision

**ADOPT_AS_CONDITIONAL_STAGE7_REFERENCE.** Use a concise descriptive Stage 7 account in the main manuscript, with the full profiles, weight comparisons and geographic sensitivity in the supplementary material. This is a review recommendation, not formal promotion. Do not call the partition a universal, independently validated, predictive or causal community taxonomy.

## 1 Reproducibility

The archived input matrix was independently reconstructed from the actual source bytes in exact GEOID order. All twelve coordinates, the saved scaler, weighted matrix, seed-42 labels and actual saved estimator centers agree. Nearest-center evaluation reproduces every saved label without fitting. The complete sample is 2,287, the residential master 2,291, and the electricity-model universe 2,315. Four geometry-unresolved records remain null. Their 12,390 mapped residents are distinct from the 16,979 residents of the 24 outside-cohort tracts. Formal CSV identifiers serialized without their leading zero were restored deterministically to eleven digits solely for comparison; no original table was edited. See INDEPENDENT_SCIENTIFIC_QA.json and FORMAL_GEOID_SERIALIZATION_AUDIT.json.

## 2 Constructs and weights

CORE3 distinguishes built-surface coverage, housing-unit configuration and classified-parcel composition. It does not measure the entire built environment. W1 is defensible as a transparent equal-five-parent convention: recovery, grid, physical, social and economic stock/loss each receive 0.20; stock and ALR split the economic parent equally. Distinct measurement meanings do not require separate equal parent budgets. No data-driven optimality is claimed. Scores retain their published scales before standardization; only monetary stock is log1p transformed. ALR is unadjusted multi-hazard loss propensity, not pure hazard. The feature-selection and weighting gates are closed.

## 3 Supported original-unit descriptions

C1/C2/C3/C4 contain 650/802/801/34 tracts. Mean B is 36.2488/35.2091/31.0927/23.6011 h; mean SOVI is 31.1408/84.1608/77.5061/67.9862. C1 combines relatively lower SOVI with greater B than C2 and C3 under W1. C2 has greater built coverage, 5+ housing share, entropy and ALR than C3 under W1. C1 has the largest median monetary stock ($667.1411 million). All twelve-coordinate raw profiles, medians and measurement coverage are in CORE3_W1_VERIFIED_PROFILES.csv and CORE3_W1_PROFILE_TABLE.csv. Tract-weighted values and population-weighted B are explicitly separate. C4's initial service is 1.8153%, not uninterrupted service or a universally resilient class.

## 4 Stability and failures

The 190 W1 seed pairs have median ARI 1.0000 and minimum 0.998737625. Twenty spatial cases (seventeen unique deletion sets) have median ARI 0.879221778, fifth percentile 0.715234632 and minimum 0.692932771, with at most 255 reassignments. These are registered sample perturbations, not independent geographic validation. No post-result acceptance threshold is introduced.

Direction support is counted against W1 seed42 after explicit overlap alignment. C1>B(C3) persists in 20/20 W1 spatial cases and 80/80 W2–W5 complete-cohort cases; C1's lower SOVI than C2 and C3 persists in the same sets. Yet W3 geographic cases reverse each of these SOVI comparisons in 2/20 cases. C2>B(C3) and C2>SOVI(C3) persist in 20/20 W1 spatial cases, but both reverse in 20/20 complete-cohort W5 cases (and in 15/20 and 17/20 W5 geographic cases). Minor W1 rankings also reverse: C1 versus C3 HHI reverses in 4/20 spatial cases; their initial-service and 5+ housing directions each reverse in 1/20. Support for a direction is not membership stability, magnitude equivalence or statistical significance. CORE3_W1_CLAIM_STABILITY.csv provides all 720 pair/feature/family summaries, with exact N=20 and per-case evidence.

Median same-seed reassignment relative to W1 is W2 12.3306%, W3 34.4993%, W4 5.9904%, W5 23.8741%. The nominal W1 grid budget is 20%, whereas its median observed BSS share is 2.3821%; social and recovery shares are 39.9791% and 29.1452%. BSS/TSS and within-class spread distinguish modest grid mean separation from lack of relevant dependency information. These results do not demonstrate that grid measurements are irrelevant or redundant.

## 5 Minority specificity

The exact 34-GEOID set is verified, not inferred from a historical class number. In the adverse seed54 deletion, four original members remain in training; all 34 remain in the W1 matched full prediction, which expands to 92 and absorbs 58. Retention=100%, purity=Jaccard=36.9565%. The failure is loss of specificity despite training support, not disappearance of tracts. W2/W3/W5 can yield zero original-member retention in the training-aligned counterpart, while those same original tracts are predicted in other destination classes. Full raw contingency and destination counts are retained. Do not name this group a stable archetype or justify intervention by its membership.

## 6 Conditional use versus stable taxonomy

The candidate is sufficiently documented and reproducible for an explicitly conditional exploratory main-text characterization. The evidence is insufficient for a stable community taxonomy. Optimization consistency does not resolve model-definition sensitivity. W1 is the reference convention, not a uniquely correct geographical partition. The current gate supports the separate S19 review copy, not replacement of formal Stage 7.

## 7 Withdrawn previous findings

Withdraw the original five-class names and the BE0 counts 850/34/651/752 as descriptions of CORE3/W1. On 2,287 common GEOIDs, formal5 versus CORE3 ARI is 0.201656240; BE0 versus CORE3 is 0.655022087. These partitions are scientifically different. Withdraw age/density-based class mechanisms, old PCA/loading descriptions as the new model specification, old hotspot-by-cluster ranks and class-dependent funding/dispatch recommendations. Original PCA was diagnostic/visualization after clustering in standardized coordinates; the new solution uses no PCA. Historical hotspot scores used rank-percentiles of T80, ACS pre1970, composite NRI risk and SOVI. Those inputs are not the current primary specification and their ranks are not transferred. Preserve historical records as provenance, not current claims.

## 8 Independent findings retained

Retain the established restoration-policy, fixed SOVI quartile and source-gated service analyses independently of clustering. S19 Figures 1–6 and Tables 1–3 are not Stage 7 figures and are not replaced. KEEP in the ledger means unaffected by this Stage 7 change; it is not revalidation of all numerical content or the unrelated GA narrative. Between-class B/initial-service differences are descriptive because those variables enter the clustering.

## 9 Remaining uncertainty and integration boundary

Fixed k=4 and W1 remain conceptual/specification choices, not proof of uniquely valid classes. Geographic support is dependent and sparse for the minority class. EMC resolution, ACS variance, SCAG partial coverage/carry-forward classifications and FEMA vintage/construction constrain meaning. Four geometry records remain unresolved. No new source acquisition, k/weight search, fitting, PCA or physical computation is required or authorized by this decision. Main text should present the conditional large-class descriptions and immediately disclose sensitivity; detailed alternatives and the minority specificity failure belong in the supplementary material. The exact numbering is proposed only and requires author approval together with adoption.
"""
text('CORE3_W1_ADOPTION_DECISION.md',memo)

versions=[
dict(version='A_FORMAL5',cohort=2291,common_comparison_n=2287,k=5,coordinates='T80; Init_Supply; Grid_Degree; Grid_Impact; Grid_Betweenness; Redundancy_HHI; Pre_1970_Ratio; Pop_Density; SOVI_SCORE; NRI_BUILDVALUE; NRI_RISK_SCORE',transform='log1p population density and building value; per-coordinate StandardScaler',weight='equal standardized coordinates; not W1 domain budgets',PCA='diagnostics and plotted scores, not fitted clustering space',labels='original formal saved labels',counts='910/183/619/545/34 in full2291',centers='not required or regenerated here',hotspot='sum of percentile ranks: T80, ACS residential pre1970, composite risk, SOVI; independent historical score'),
dict(version='B_BE0_4',cohort=2287,common_comparison_n=2287,k=4,coordinates='B; Init_Supply; four grid; SCAG2019 entropy; LARIAC2020 footprint; LARIAC2014 observed valid-age pre1970 share; SOVI; log1p stock; ALR',transform='raw B; log1p stock; StandardScaler',weight='equal five parent budgets; economic stock and ALR share0.20',PCA='none',labels='D equal_five_domains saved seed42 k4',counts='850/34/651/752 in prior display ordering',centers='old preview centers reconstructed from labels; not serialized fitted estimator centers',hotspot='no new hotspot; no historical ranks transferred'),
dict(version='C_CORE3_W1_4',cohort=2287,common_comparison_n=2287,k=4,coordinates='; '.join(COLS),transform='raw B; log1p stock; saved StandardScaler; sqrt(w/q)',weight='W1 .20/.20/.20/.20/.10/.10',PCA='none',labels='saved W1 seed42; C1=raw0 C2=raw1 C3=raw2 C4=raw3',counts='650/802/801/34',centers='actual archived fitted estimator centers verified byte identity',hotspot='none generated; class-dependent hotspot/intervention claims require separate validation')]
save('STAGE7_VERSION_SPECIFICATIONS.csv',versions)
z=np.load(lp(OUT/'CORE3_W1_FROZEN_REFERENCE.npz'));meta=json.loads(src(W+'run_records/W1.json').read_text(encoding='utf-8'))
dump('CORE3_W1_FREEZE_RECORD.json',dict(authoritative_commit=BASELINE,review_only=True,reference='CORE3/W1 k4 seed42',exact_saved_solution_not_refit=True,features=COLS,tract_order=z['tract_ids'],residential_master_n=2291,complete_n=2287,unclassified=UNRESOLVED,missing_treatment='no imputation; four UNCLASSIFIED_GEOMETRY',transform='raw B; log1p BUILDVALUE; published scores unchanged before StandardScaler',domain_squared_budgets=dict(zip(DOMAINS,[.2,.2,.2,.2,.1,.1])),coordinate_factors=z['coordinate_factors'],coordinate_squared_budgets=np.square(z['coordinate_factors']),scaler_mean=z['scaler_mean'],scaler_scale=z['scaler_scale'],actual_fitted_centers=z['fitted_centers'],saved_settings=meta['signature']['settings'],random_state=42,scikit_learn='1.5.1',old_to_new_id={'0':'C1','1':'C2','2':'C3','3':'C4'},source_npz=PREFIX+W+'run_records/W1.npz',source_metadata=PREFIX+W+'run_records/W1.json',output_npz_sha256=sha(OUT/'CORE3_W1_FROZEN_REFERENCE.npz'),array_hashes={k:hashlib.sha256(z[k].tobytes()).hexdigest() for k in z.files if k not in ['tract_ids','feature_columns']}))
text('METRIC_AND_SOURCE_DEFINITIONS.md',r"""# Frozen measurement definitions and restrictions

For tract i, B is (1/1000) sum_r integral_0^480 [1 - A_ir(t)/R_i] dt in hours: A is the saved source-gated mapped available mass and R is the unchanged resolved mapping mass. The archived normalized integrals supply B directly. This task does not evaluate new trajectories. Init_Supply is the preserved initial modeled source-connected service measure. T80 is the exact event-time crossing of the mean tract trajectory, not a mean over realization crossings. See the source-hashed local extraction RECOVERY_METRIC_QA.md; no Unconstrained metric is substituted.

Grid_Degree, Grid_Impact and Grid_Betweenness are the existing tract–substation mapping-weighted graph descriptors. Redundancy_HHI is the saved concentration of dependency weights. Grid_Impact is the network λ2-impact descriptor, not the fitness function or identity of restoration policy Impact-first. These are dependency statistics and do not establish feeder assignment, delivered MW or electrical adequacy.

EMC2022 built-land fraction uses total built surface supported by 2022 Sentinel-2 observations in EMC-BUILT R2025A V1.0 at 100m. Its numerator and valid tract-land support were verified in the closed measurement package. Complete valid-raster coverage is not remote-sensing classification accuracy. ACS housing_5plus_share=(B25024_006E+007E+008E+009E)/B25024_001E, using 2018–2022 five-year estimates and the verified 80 variance replicates. The denominator is housing units, not buildings. SCAG2020 entropy=-sum_j p_j ln(p_j)/ln(11), with p_j from exclusive classified-parcel land areas. It omits unclassified tract land; carried-forward LU19 records and 2020 classification do not make it synchronized with 2022 inputs. No building-age coordinate enters CORE3.

FEMA v1.19 (March2023) supplies SOVI_SCORE, BUILDVALUE and ALR_NPCTL. Stock is log1p of the archived monetary building value. ALR_NPCTL is the national percentile of an unadjusted EAL-weighted composite of consequence-specific loss-rate percentiles; it is not total EAL/BUILDVALUE, not a social-adjusted risk score and not pure hazard. Existing version-specific FEMA evidence is retained; no newer-release values are merged.

For standardized z coordinates, squared distance is sum_d (w_d/q_d) sum_j_in_d (z_ij-z_lj)^2. Thus coordinate multipliers are sqrt(w_d/q_d). The profile heatmap deliberately displays unweighted tract-mean z values, with exact numeric labels and saturated colors beyond ±2.5. Raw table values use unweighted tracts unless an explicit population-weighted row is named. No class comparison is a causal effect or independent recovery validation.
""")
text('FIGURE_TABLE_INTEGRATION_MAP.md',"""# Proposed Stage 7 integration map

S19 is the author-confirmed source. All numbering below is temporary and review-only.

| Material | Proposed location | Existing material affected |
|---|---|---|
| CORE3/W1 membership map | New Figure 7, main or combined Stage7 figure after author allocation | No existing S19 figure overwritten |
| Joint twelve-coordinate profile | New Figure 8, main or supplement after author allocation | No historical five-class profiles reused |
| Raw profiles and coverage | New Table 4 in the Stage7 results; full CSV in supplement | Tables1–3 preserved |
| Weight and geographic sensitivity | S_CORE3_STABILITY, supplement | Historical BE0 stability values superseded for CORE3 |
|34-member specificity/destinations|S_CORE3_MINORITY,supplement|No old hotspot/archetype claims transferred|

Modify only the Stage7 clauses in S19 research question3 (P9), Methods2.5 (P23), Results3.4 (P40) and limitations (P47); insert targeted new paragraphs there. Figures1–6 and Tables1–3 are independent restoration material and remain byte-identical. Add the two proposed figure previews and their captions at the existing figure section's end. Add Table4 without changing existing tables. No current supplementary number is silently reassigned. The latest BE0 review copy is comparison evidence, not the template or current class authority. Old July Figure6/7 identities are not the S19 identities.
""")
text('STAGE7_SUPPLEMENTARY_AUTHOR_REVIEW.md',"""The supplementary review should report the exact twelve-coordinate definition, W1 factors and scaler, all original-unit means and medians, the 2,291-row label master, the four null geometry records, and the formal5/BE0/CORE3 contingency tables. W1 optimization consistency (190 seed pairs) is distinct from geographic sample sensitivity (20 registered cases; 17 unique deletion sets) and from W2–W5 model-definition sensitivity (20 seeds each). Empirical ranges and lower tails are descriptive, not confidence intervals or accuracy rates.

Mean class contrasts are assessed after documented overlap matching; spatial matching uses retained training tracts only. Raw contingency tables expose splits and merges. The full 720 direction summaries distinguish support and reversal counts with their denominators. A preserved direction alone does not establish unchanged class membership. The 34-tract specificity diagnostic reports both retention and purity, the four retained training members and absorption of 58 additional tracts. Alternative-weight zero matched retention is reported together with actual destination counts, rather than interpreted as disappearance.

Historical BE0 age/SCAG2019/footprint and formal five-class PCA/raw-log results remain explicitly historical comparisons. They are not robustness evidence for unchanged CORE3 meanings. No new hotspot ranking is proposed: original scores depended on T80, residential age, composite risk and SOVI. The old score, cluster membership and targeted intervention inference are distinct scientific dependencies. Neither the new joint classification nor its between-class recovery contrasts provide causal or independently validated policy effects.
""")

NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def flat(el):return ''.join(el.xpath('.//*[local-name()="t"]/text()'))
def extract(path):
 with zipfile.ZipFile(lp(path)) as z:
  tree=E.fromstring(z.read('word/document.xml'));body=tree.find('w:body',NS);rows=[];pn=tn=0
  for child in body:
   if child.tag.endswith('}p'):
    pn+=1;rows.append((f'P{pn:04d}',flat(child)))
   elif child.tag.endswith('}tbl'):
    tn+=1
    for ri,tr in enumerate(child.findall('w:tr',NS),1):
     for ci,tc in enumerate(tr.findall('w:tc',NS),1):rows.append((f'T{tn}R{ri}C{ci}',flat(tc)))
  for name in z.namelist():
   if re.match(r'word/(header|footer|footnotes|endnotes)\d*\.xml$',name):rows.append((name,flat(E.fromstring(z.read(name)))))
  # Embedded text boxes are included in their enclosing paragraph's exact text.
 return rows

old=json.loads(lp(OUT/'S19_PARAGRAPHS.json').read_text(encoding='utf-8'))
old={r['paragraph']:r['text'] for r in old}
replacements={
2:'Author review copy proposing the conditional CORE3/W1 Stage 7 reference. Other sections, numerical results and existing figures retain the author-confirmed S19 working draft. This copy does not promote the new classification to the formal analysis.',
9:old[9].replace('built-environment exposure, risk, and modeled grid dependency','physical built environment, economic stock, multi-hazard loss propensity, and modeled grid dependency'),
23:old[23].split('The retained Stage 7')[0]+"The joint CORE3/W1 community classification is descriptive and conditional on its feature definitions, fixed four-class partition and declared domain weights.",
40:old[40].split('The Stage 7 descriptive')[0],
47:old[47].replace('Cluster and hotspot outputs are descriptive screening.','CORE3/W1 class descriptions are conditional on the chosen specification and geographic support; historical hotspot ranks are not transferred to the new partition.')}
dump('S19_TARGETED_REPLACEMENTS.json',replacements)
rows=[]
for loc,t in extract(S19):
 if not t.strip():continue
 n=int(loc[1:]) if re.fullmatch('P[0-9]+',loc) else None
 affected=n in replacements
 stage=bool(re.search(r'Stage 7|cluster|typolog|hotspot|PCA|archetype',t,re.I))
 rows.append(dict(source_id='AUTHOR_CONFIRMED_S19',source_file=str(S19),source_sha256=sha(S19),exact_location=loc,original_exact_text=t,scientific_version='A_FORMAL5' if stage else 'independent restoration/model/reference material',supported='partially; independent clauses retained' if affected else 'outside Stage7 change scope; not independently re-certified',evidence='STAGE7_VERSION_CROSSWALK.csv; CORE3_W1_CLAIM_STABILITY.csv' if affected else 'source S19 byte preservation',required_action='REVISE' if affected else 'KEEP',proposed_replacement=replacements.get(n,t),numerical_verification='INDEPENDENT_SCIENTIFIC_QA.json' if affected else 'No numerical change',scope='only Stage7-specific clauses' if affected else 'preserve exact source XML'))
review=src(M+'Manuscript_Stage7_Integration_REVIEW.docx')
for loc,t in extract(review):
 if not re.search(r'Stage 7|cluster|typolog|hotspot|PCA|archetype|2014|entropy|coverage',t,re.I):continue
 action='REVISE';proposal='Use the targeted CORE3/W1 Methods/Results/Discussion text and exact new profiles; preserve independent restoration clauses.'
 if 'hotspot' in t.lower():action='REQUIRES SEPARATE VALIDATION';proposal='Do not transfer historical hotspot ranks or class-specific intervention recommendations.'
 if loc.startswith('T4') or ('Table 4' in t and len(t)<400):proposal=CAPTIONS['TABLE_CORE3_W1_PROFILES']
 if re.search(r'850|651|752|2014|SCAG 2019',t):proposal='Historical BE0 definition/results: replace with CORE3/W1 sources, labels and raw profiles; no age coordinate.'
 rows.append(dict(source_id='LATEST_PREVIOUS_STAGE7_REVIEW',source_file=str(review),source_sha256=sha(review),exact_location=loc,original_exact_text=t,scientific_version='B_BE0_4',supported='historical provenance only; not current CORE3 findings',evidence='STAGE7_VERSION_SPECIFICATIONS.csv; STAGE7_VERSION_CROSSWALK.csv',required_action=action,proposed_replacement=proposal,numerical_verification='BE0–CORE3 common-N ARI0.655022087; actual contingency retained',scope='comparison only; this old DOCX is not modified'))

# Recheck exact text and bytes from each historical manuscript named in the previous ledger.
legacy=pd.read_csv(src(M+'MANUSCRIPT_CLAIM_RECONCILIATION.csv')).fillna('')
cache={}
for _,r in legacy.iterrows():
 if r.source_id=='S19':continue
 path=Path(r.source_manuscript)
 if r.source_manuscript not in cache:
  assert lp(path).exists(),str(path)
  assert sha(path)==r.source_sha256,str(path)
  cache[r.source_manuscript]=dict(extract(path));record(path,sha(path),'archived manuscript verified current actual bytes','HISTORICAL_MANUSCRIPT_'+r.source_id)
 loc=r.exact_location.split(' /')[0];t=str(r.current_claim)
 actual=cache[r.source_manuscript].get(loc)
 # Legacy ledger can address body-block indices; exact text must exist in actual OOXML.
 matches=[(k,v) for k,v in cache[r.source_manuscript].items() if re.sub(r'\s+','',v)==re.sub(r'\s+','',t)]
 assert matches,(r.source_id,loc,t[:70])
 loc,t=matches[0]  # use current exact OOXML text including equation text and whitespace
 if re.search(r'hotspot|top.?10|top.?ten|funding|intervention',t,re.I):action='REQUIRES SEPARATE VALIDATION';proposal='Withdraw transfer to CORE3/W1. Original score and class-specific recommendations are separate dependencies.'
 elif re.search(r'PCA|eigenvalue|loading|principal component',t,re.I):action='MOVE TO SUPPLEMENTARY';proposal='Historical PCA diagnostics only; CORE3/W1 clusters use twelve weighted standardized coordinates without PCA.'
 elif re.search(r'cluster|typolog|archetype|Pre.?1970|housing.age|population.density',t,re.I):action='REVISE';proposal='Use current CORE3/W1 conditional results; withdraw old five-class names, physical-age/density characterization and historical counts.'
 else:action='KEEP';proposal='Independent of Stage7 replacement; not re-certified here.'
 rows.append(dict(source_id=r.source_id,source_file=str(path),source_sha256=sha(path),exact_location=loc,original_exact_text=t,scientific_version='historical five-class/earlier manuscript; not CORE3',supported='version-specific only',evidence='actual source OOXML and STAGE7_VERSION_SPECIFICATIONS.csv',required_action=action,proposed_replacement=proposal,numerical_verification='actual source hash and exact text verified',scope='legacy claim audit; no source manuscript edited'))
save('MANUSCRIPT_CLAIM_RECONCILIATION.csv',rows)
dump('MANUSCRIPT_SOURCE_QA.json',dict(S19_sha256=sha(S19),previous_review_sha256=sha(review),ledger_rows=len(rows),S19_rows=sum(r['source_id']=='AUTHOR_CONFIRMED_S19' for r in rows),legacy_source_files=len(cache),exact_source_text_verified=True,replacement_paragraphs=list(replacements)))
log(f'Prepared adoption decision, twelve-coordinate profiles/claims and {len(rows)} exact-text manuscript reconciliation rows; no source manuscripts changed.')
