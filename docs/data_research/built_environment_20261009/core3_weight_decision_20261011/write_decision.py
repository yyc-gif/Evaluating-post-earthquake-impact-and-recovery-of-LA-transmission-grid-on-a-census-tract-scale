"""One scientific reference convention, with numerical evidence and qualifications."""
from common import *
import numpy as np,pandas as pd

def read(n):return pd.read_csv(lp(OUT/n))
def main():
    summary=read('CORE3_WEIGHT_COMPARISONS.csv');domains=read('CORE3_DOMAIN_SEPARATION_SUMMARY.csv');profiles=read('CORE3_CLASS_PROFILES.csv');minor=read('CORE3_34TRACT_AUDIT.csv');runs=read('CORE3_RUN_SUMMARY.csv');ov=read('CORE3_GRID_RECOVERY_INFORMATION_OVERLAP.csv');rev=read('CORE3_PROFILE_REVERSAL_SUMMARY.csv');trans=read('CORE3_WEIGHT_CLASS_TRANSITIONS.csv');patterns=read('CORE3_CLASS_MEANING_PATTERNS.csv')
    core=summary.set_index('scheme').loc['W1'];w1=domains.loc[domains.scheme.eq('W1')].set_index('domain');w3=domains.loc[domains.scheme.eq('W3')].set_index('domain')
    tab=summary[['scheme','seed_pair_ARI_median','seed_pair_ARI_min','W1_same_seed_ARI_median','reassigned_fraction_median','spatial_ARI_median','spatial_ARI_p05','spatial_ARI_min']].to_markdown(index=False,floatfmt='.4f')
    prof=profiles.loc[profiles.seed.eq(42)&profiles.scheme.eq('W1')&profiles.feature.isin(['B_480_hr','Init_Supply','SOVI_SCORE',*DOMAIN_COLUMNS['Physical']])].pivot_table(index='W1_seed42_display_class',columns='feature',values='mean')
    econ=profiles.loc[profiles.seed.eq(42)&profiles.feature.isin(['NRI_BUILDVALUE','ALR_NPCTL'])].pivot_table(index=['scheme','W1_seed42_display_class'],columns='feature',values='median')
    minority54=minor.loc[minor.seed.eq(54)&minor.scope.eq('spatial_all'),['scheme','reference_group_training_n','predicted_dominant_class_n','retention','purity','number_of_destination_classes','largest_destination_original_members','largest_destination_total_n','largest_destination_purity']]
    textfile('CORE3_FINAL_WEIGHT_DECISION.md',f'''# Final CORE3 reference-weight decision

Recommend **W1** as the reference convention for the frozen CORE3 candidate: recovery/service0.20, grid dependency0.20, physical CORE3 0.20, social vulnerability0.20, monetary stock0.10 and multi-hazard loss propensity0.10. This is an explicitly chosen hierarchical representation convention, not an empirically optimal or uniquely identified set of scientific weights. It does not promote formal Stage7 labels or change any measurement.

## Answers to the six decision questions

1. **CORE3 should share one physical parent budget.** Coverage, residential configuration and classified-parcel diversity are distinct named subconstructs of community physical setting. Within that parent they receive equal one-third shares. This limits automatic extra influence from having three supported physical coordinates; it does not assert their measurement errors, populations or definitions are identical. No separate-physical-parent scheme was authorized in this experiment, so this hierarchy choice is conceptual, not a tested superiority claim.
2. **Keep Stock and ALR as separate measurements under one parent budget.** Call the parent economic exposure and expected loss. Monetary stock measures asset amount; unadjusted ALR measures loss propensity after exposure normalization and component aggregation. Neither duplicates the other, and low correlation does not determine their relative scientific importance. Their equal0.10 split is the neutral declared reference within the shared0.20 parent. W4/W5 retain the same parent but change its internal emphasis; W2 grants economic/loss information one-third of the total and therefore changes the joint-characterization question.
3. **Use W1, not a performance winner.** The research combines recovery/service, grid dependency, physical setting, social vulnerability and economic/loss context. Giving each parent0.20 is transparent and avoids inherited column counts automatically dominating the distance. W3's larger grid and smaller social budget is defensible for a more network-focused question, but is not the balanced joint question here. W4's higher spatial median does not make ALR emphasis scientifically better, nor does W5's worse lower tail invalidate measured asset stock. W2 remains a substantive hierarchy sensitivity, not an automatic correction for Stock/ALR correlation.
4. **Reasonable weights materially affect membership.** Relative to same-seed W1, median aligned reassignment is12.33% under W2,34.50% under W3,5.99% under W4 and23.87% under W5. Raw class flows and original-unit means show genuine reorganizations, not merely a class-ID permutation. The taxonomy is specification-conditional.
5. **The four classes support qualified descriptions, not universal archetypes.** W1 optimization is highly reproducible (median seed-pair ARI{core.seed_pair_ARI_median:.4f}, minimum{core.seed_pair_ARI_min:.4f}). Its spatial ARI median is{core.spatial_ARI_median:.4f}, 5th percentile{core.spatial_ARI_p05:.4f}, minimum{core.spatial_ARI_min:.4f}, with up to {int(core.spatial_changed_n_max)} aligned reassignments. Several major W1 profile directions persist under the registered deletions, but its 34-member class can expand to92 and lose specificity. Other reasonable schemes reorganize major groups and can split that subgroup. Do not assign the small group a stable community-archetype name or insist that four groups are uniquely correct.
6. **Remaining limits:** weights are normative representation assumptions; k is fixed rather than newly validated; the 20 spatial cases contain 17 unique geographic deletion sets; measurement-support qualifications remain; four residential geometries remain unclassified; initial service and recovery are modeled inputs; clusters are descriptive and cannot attribute recovery causally to physical/social features. High seed agreement is optimization reproducibility, not independent validation. No extra weights, variables, k values or algorithms were searched to erase these weaknesses.

## Exact distance convention

After the unchanged full-cohort StandardScaler convention, squared coordinate weights in saved column order are [0.10,0.10,0.05,0.05,0.05,0.05,1/15,1/15,1/15,0.20,0.10,0.10]. Multiply standardized values by their square roots. B and Init split recovery equally; four grid descriptors split grid equally; three CORE3 coordinates split physical equally. Total squared-distance budget is one. The individual Stock/ALR measurements remain visible in all profiles.

## What this decision permits

Use W1 as the declared reference candidate and W2-W5 as the bounded hierarchy/emphasis sensitivities. Report major descriptions conditionally on this definition and carry the observed sensitivity into interpretation. This closes the weighting decision for the present candidate; it is not approval to overwrite formal Stage7, manuscript or figures. No additional model optimization is proposed or launched.

{tab}

Empirical medians/ranges/lower tails are not confidence intervals. ARI is partition agreement, not the percentage of correctly classified tracts. Pairwise seed statistics are not independent observations.
''')
    textfile('CORE3_SCIENTIFIC_INTERPRETATION.md',f'''# Scientific interpretation of the fixed CORE3 weight comparison

## Measurement, constructs, weights, stability and interpretation

Measurement validity is held fixed at the independently reviewed CORE3 package. Construct validity concerns how named measurements form parents; weight justification concerns a declared research emphasis; partition stability concerns the reproducibility of membership under seeds/weights/geographic deletion; interpretability concerns which joint descriptions survive. Neither stability nor low correlation identifies a unique conceptual weight. W1 is recommended for balanced parent representation; it is not selected for an ARI, silhouette, class-size or minority-retention maximum.

All five schemes use the same twelve exact input coordinates, same2,287 GEOIDs/order, fixed k4, n_init100 and seeds42-61. Scaling in spatial fits uses training only. W1's20 full and20 spatial models were reused after exact byte/matrix/scaler/factor/prediction verification, including actual saved estimator centers. W2-W5 added exactly160 fits. No new variable selection, k search, PCA, GIS extraction, physical simulation, scheduling or GA occurred.

## Major membership and meaning changes

{tab}

At seed 42, W3 sends 272/802 (33.9%) of W1 class1 into the class matched to W1 class0 and 213/650 (32.8%) of W1 class0 into the class matched to class2. This is substantial mixing of the large groups. W5 sends 305/802 (38.0%) of W1 class1 into the class matched to class2; its stock emphasis changes the separation of the two higher-SOVI groups. W4 is less disruptive at this seed but still changes memberships and profiles. No alignment is treated as scientific class equivalence.

Under W1 seed 42, original-unit class means are:

{prof.to_markdown(floatfmt='.5f')}

Display IDs0-3 are diagnostic W1 seed 42 IDs, not published formal labels. Class0 has greater modeled loss and lower SOVI than classes1/2; class1 has greater five-plus share, classified entropy and built coverage than class2. These directions do not reverse in W1's20 registered spatial perturbations. This does not mean all members persist, all dimensions are stable, or physical setting causes recovery. Across the100 full fits, the highest-mean loss class is never the highest-mean SOVI class. This broad ordinal statement differs from a claim that the highest-loss class is always low-vulnerability: its mean SOVI shifts from31.14 in W1 seed 42 to56.23 in W3.

The class1-versus-class2 mean loss contrast is approximately+4.12h under W1 but-0.64h under W5 (median across seeds). Their SOVI contrast changes from+6.65 to-1.78 score points. This is a change in descriptive class meaning, not just boundary membership. W5 spatially reverses those within-specification loss/SOVI orders in5/20 and3/20 cases, respectively. Class numbering is aligned only for display and cannot fix this scientific dependence on the chosen budget.

## Nominal versus actual influence

Under W1, social vulnerability contributes a median{100*w1.loc['Social','between_median']:.2f}% of between-class variation, recovery/service{100*w1.loc['Recovery','between_median']:.2f}%, physical{100*w1.loc['Physical','between_median']:.2f}%, ALR{100*w1.loc['ALR','between_median']:.2f}%, stock{100*w1.loc['Stock','between_median']:.2f}% and grid{100*w1.loc['Grid','between_median']:.2f}%. These differ from nominal weights. Each coordinate's TSS/BSS/WSS is audited, and TSS=BSS+WSS uses partition means rather than pretending fitted centers exactly equal them after numerical convergence tolerance.

Only{100*w1.loc['Grid','explained_median']:.2f}% of grid-domain variance lies between W1 classes;{100*w1.loc['Grid','within_median']:.2f}% remains within them. Thus weak grid separation reflects small mean contrasts relative to within-class dispersion. Recovery shares some network information: regressing B on the four grid coordinates gives in-sample linear R-squared0.3806; degree on B/Init gives0.3303, whereas impact/betweenness/HHI on B/Init give0.0739/0.0199/0.0400. Shared information is partial and does not prove the grid descriptors are wholly redundant or causally unimportant.

W3 increases nominal grid budget from0.20 to4/11 while reducing SOVI to1/11. Grid between-class contribution rises to{100*w3.loc['Grid','between_median']:.2f}% and grid explained fraction to{100*w3.loc['Grid','explained_median']:.2f}%; social contribution falls to{100*w3.loc['Social','between_median']:.2f}%. The partition therefore changes with the research emphasis. This is not a justification to raise grid weight merely to manufacture a larger contribution.

## Stock and ALR

Stock and unadjusted ALR remain scientifically different coordinates. On this exact2,287 primary cohort Pearson r is 0.24734 and Spearman rho is 0.23530, independently recomputed rather than assumed from the previous2,286 cross-source cohort. W2 gives them a combined one-third budget, W4/W5 retain combined0.20 but favor ALR/Stock. Relative to W1 these materially change membership, economic profiles and spatial lower tails. Their low correlation cannot determine their conceptual importance.

Original-unit seed 42 class medians:

{econ.to_markdown(floatfmt='.2f')}

NRI_BUILDVALUE is archived source dollars; ALR_NPCTL is the unadjusted multi-hazard loss-rate percentile, not a pure hazard measure. For W1 display class1, median stock changes from about$484million to$622million under W5, while class2 changes from$350million to$311million. This is membership sorting under the stock emphasis. It does not indicate changed economic values, better measurement or a more truthful clustering.

## Spatial lower tails and the34-tract group

W1's worst overall case is seed 56, blocks 7:-22/8:-21, with ARI0.6929 and255 reassignments. W3's worst is seed 45, blocks 8:-23/9:-22: ARI0.1092,1117 reassignments. W2/W5 have relatively high medians yet adverse cases0.5050/0.3691 and768/829 reassignments. These cases cannot be hidden by only reporting median ARI. Block-level changed counts, standardized center shifts and margin distributions separate large reorganizations from small boundary changes without a post-result boundary threshold.

At seed 54 the shared deletion of blocks 7:-24 and 7:-23 leaves four reference members in training:

{minority54.to_markdown(index=False,floatfmt='.5f')}

W1/W4 retain all34 original members in a92-member predicted class (purity36.96%), absorbing58 other tracts. Under W2/W3/W5 the training-aligned counterpart has zero original members, while the reference members have predictions in3/2/3 other destination classes. Their largest destinations contain 24/648, 32/813 and 19/688 original/total tracts. Zero matched retention does not mean records vanished; the raw destination counts show splitting/merging and the one-to-one alignment limitation. No case lacks every member's training support: these failures occur despite four remaining members, not because support is entirely absent. No held-out rematching was used to improve these statistics.

Do not assign the34-member group a stable archetype name. Its relatively higher Init_Supply is only about0.01815 (1.8%) in the original full partition; it is not continuous power, independently established resilience or a verified service class.

## Boundary of the recommendation

W1 supports specification-qualified descriptions of three large groups and an explicitly fragile small subgroup. Across reasonable budgets, major membership and some meaning change substantially; the four-class taxonomy is not universally stable. SCAG diversity remains conditional on classified land, EMC remains100m modeled built surface, ACS retains survey/boundary uncertainty, ALR retains consequence/exposure composition, and four geometries remain unclassified. Joint clustering uses modeled recovery and cannot provide causal attribution. No independent predictive validation is claimed. Stop here: choose the declared W1 reference convention and report sensitivities; do not search new weights or k values to remove these limitations.
''')
    config=dict(reference_scheme='W1',domain_squared_budgets=dict(zip(DOMAIN_COLUMNS,WEIGHTS['W1'])),coordinate_squared_weights=dict(zip(COLS,np.square(factors('W1')))),standardized_multipliers=dict(zip(COLS,factors('W1'))),measurement_baseline=BASELINE,primary_n=2287,master_n=2291,unclassified=UNRESOLVED,KMeans=PARAMS,diagnostic_seeds=SEEDS,reference_display_seed=42,weight_choice_basis='Balanced five-parent representation, not numerical optimization.',formal_promotion=False,scientific_interpretation='Descriptive specification-conditional joint typology; fragile34-member subgroup.')
    dump('CORE3_REFERENCE_WEIGHT_SPECIFICATION.json',config)
    textfile('README.md','''# CORE3 final domain-weight decision

Start with CORE3_FINAL_WEIGHT_DECISION.md. It recommends W1 as the single reference convention and qualifies the four-class taxonomy. CORE3_SCIENTIFIC_INTERPRETATION.md supplies the numerical evidence, class-meaning changes and minority failure cases. The selected measurement set is unchanged.

Required tables cover the five vectors, same-seed changes, raw transitions, spatial stability, stock/ALR profiles, domain/feature sums of squares and the exact34-member group. Full run_records preserve actual estimator centers, scalers, factors, labels/predictions and11-digit GEOID order. CORE3_EXACT_INPUTS.npz retains exact floating-point input values; CORE3_MASTER_2291.csv retains the four unclassified records. Tables contain empirical summaries, not confidence intervals.

Reproduction: use the recorded Python3.12.3/scikit-learn 1.5.1 environment. Run preregister.py once; fit_weights.py reuses complete hash-matching checkpoints; summarize_weights.py and meaning_audit.py derive tables without fitting; write_decision.py writes the decision from completed results; make_diagnostics.py and render_and_check_pdfs.py create/render the diagnostic figures. Tests recompute consequential numerical identities without new KMeans fits. Do not import the parent package's common.py, which writes to its own output directory.

Diagnostic figures are185mm wide with minimum7.5pt text, vector PDFs and600dpi PNGs, with actual-PDF render previews and captions. They are not manuscript replacements. W1's40 original fits are reused; W2-W5 added160 fits. No additional schemes, variables, k values, PCA or scientific simulation was executed. The20 spatial cases represent17 unique geographic deletion sets. All interpretation retains measurement-source and spatial-sample limitations.

The original950 protected scientific files,862 staged items, formal Stage7, manuscript, figures, trajectories, scheduling and GA outputs remain untouched. Only this isolated diagnostic package is committed on its research branch. No formal promotion is authorized.
''')
    # Light editing only in authored prose, never in input names or values.
    for name in ['CORE3_FINAL_WEIGHT_DECISION.md','CORE3_SCIENTIFIC_INTERPRETATION.md','README.md','CORE3_WEIGHT_PREREGISTRATION.md','DIAGNOSTIC_FIGURE_CAPTIONS.md']:
        path=lp(OUT/name);t=path.read_text(encoding='utf-8')
        for a,b in {'service0.20':'service 0.20','dependency0.20':'dependency 0.20','vulnerability0.20':'vulnerability 0.20','stock0.10':'stock 0.10','propensity0.10':'propensity 0.10','equal0.10':'equal 0.10','shared0.20':'shared 0.20','parent0.20':'parent 0.20','is12.33%':'is 12.33%','W2,34.50%':'W2, 34.50%','W3,5.99%':'W3, 5.99%','W4 and23.87%':'W4 and 23.87%','ARI1.0000':'ARI 1.0000','minimum0.9987':'minimum 0.9987','is0.8792':'is 0.8792','percentile0.7152':'percentile 0.7152','minimum0.6929':'minimum 0.6929','to92':'to 92','same2,287':'same 2,287','fixed k4':'fixed k=4','n_init100':'n_init=100',"W1's20":"W1's 20",'and20':'and 20','exactly160':'exactly 160','all34':'all 34','the34':'the 34','a92-member':'a 92-member','purity36.96%':'purity 36.96%','absorbing58':'absorbing 58','in3/2/3':'in 3/2/3','give0.0739':'give 0.0739','R-squared0.3806':'R-squared 0.3806','gives0.3303':'gives 0.3303','from0.20':'from 0.20','to4/11':'to 4/11','to1/11':'to 1/11','combined0.20':'combined 0.20','about$':'about $','to$':'to $','cohort0':'cohort 0','ARI0.6929':'ARI 0.6929','and255':'and 255','ARI0.1092,1117':'ARI 0.1092, 1117','cases0.5050/0.3691':'cases 0.5050/0.3691','and768/829':'and 768/829','about0.01815':'about 0.01815','and11-digit':'and 11-digit','Python3.12.3':'Python 3.12.3','wide with minimum7.5pt':'wide with minimum 7.5 pt','are185mm':'are 185 mm','and600dpi':'and 600 dpi',"W1's40":"W1's 40",'added160':'added 160','The20':'The 20','represent17':'represent 17','original950':'original 950','files,862':'files, 862','exact34':'exact 34','cases5/20':'cases 5/20','in5/20':'in 5/20','and3/20':'and 3/20','from31.14':'from 31.14','to56.23':'to 56.23','approximately+4.12h':'approximately +4.12 h','but-0.64h':'but -0.64 h','from+6.65':'from +6.65','to-1.78':'to -1.78','Only4.16%':'Only 4.16%',';95.84%':'; 95.84%','remaining20':'remaining 20','the100':'the 100','this exact2,287':'this exact 2,287','previous2,286':'previous 2,286','remains100m':'remains 100 m'}.items():t=t.replace(a,b)
        textfile(name,t)
    log('W1 reference decision and specification-qualified scientific interpretation written; no model selected by a fit-metric ranking.')
if __name__=='__main__':main()
