"""Build concise, source-specific interpretation from completed audit outputs."""
from pathlib import Path
import json,pandas as pd,numpy as np
from run_nri_audit import ROOT,OUT,STAGE,SETS,sha

def md(name,text):(OUT/name).write_text(text.strip()+'\n',encoding='utf-8',newline='\n')
def main():
 c=pd.read_csv(OUT/'NRI_EAL_SOVI_BUILDVALUE_CORRELATIONS.csv');v=pd.read_csv(OUT/'PARTIAL_CORRELATIONS_AND_VIF.csv');f=pd.read_csv(OUT/'FOUR_FEATURE_SET_COMPARISON.csv');s=pd.read_csv(OUT/'CONTROLLED_CLUSTERING_SENSITIVITY.csv');summary=pd.read_csv(OUT/'CONTROLLED_CLUSTERING_SUMMARY.csv');st=pd.read_csv(OUT/'CLUSTER_SEED_STABILITY.csv');comp=pd.read_csv(OUT/'EAL_COMPONENT_AND_HAZARD_SUMMARY.csv')
 def corr(a,b):
  r=c[((c.field_a==a)&(c.field_b==b))|((c.field_a==b)&(c.field_b==a))].iloc[0];return f'{r.pearson_r:.4f} / {r.spearman_rho:.4f}'
 pairs=[('SOVI_SCORE','NRI_RISK_SCORE'),('SOVI_SCORE','EAL_SCORE'),('SOVI_SCORE','EAL_VALT'),('SOVI_SCORE','NRI_BUILDVALUE'),('SOVI_SCORE','log1p_NRI_BUILDVALUE'),('EAL_SCORE','NRI_BUILDVALUE'),('EAL_SCORE','log1p_NRI_BUILDVALUE'),('EAL_VALT','NRI_BUILDVALUE'),('log1p_EAL_VALT','log1p_NRI_BUILDVALUE'),('EAL_SCORE','NRI_RISK_SCORE'),('EAL_SCORE','Pop_Density'),('EAL_SCORE','Pre_1970_Ratio'),('EAL_SCORE','ALR_NPCTL'),('SOVI_SCORE','ALR_NPCTL')]
 correlation_table='| Pair | Pearson / Spearman |\n|---|---|\n'+'\n'.join(f'| {a} vs {b} | {corr(a,b)} |' for a,b in pairs)
 defs=[
 ('RISK_VALUE','CRF-adjusted composite multi-hazard risk value','annual-dollar convention','EAL_VALT multiplied by Community Risk Factor; not unadjusted expected loss','3-1, 4-5'),
 ('RISK_SCORE','National percentile of composite risk value','0-100','National tract comparison, not a probability, rating, or dollar loss','3-1 to 3-3'),
 ('EAL_SCORE','National percentile of composite expected annual loss','0-100','Ranking of EAL_VALT over the national tract universe; not local re-ranking','4-7'),
 ('EAL_VALT','Total multi-hazard expected annual loss','2022 USD/year','Sum of building, monetized population-equivalent and agriculture expected loss over applicable hazards','4-6 to 4-7'),
 ('EAL_VALB','Building expected annual loss','2022 USD/year','Hazard-specific exposed building stock times annual frequency and historic loss ratio, with documented hazard-specific methods','4-6, 5-9'),
 ('EAL_VALP','Population expected annual loss','fatality-equivalents/year','Fatalities plus one-tenth injuries, not number of electricity customers losing service','4-6'),
 ('EAL_VALPE','Population-equivalent expected annual loss','2022 USD/year','EAL_VALP times 11.6 million USD value of statistical life','4-6, 5-9'),
 ('EAL_VALA','Agricultural expected annual loss','2022 USD/year','Crops/livestock exposure and relevant hazard losses; not all consequence types apply to every hazard','4-6, 5-9'),
 ('BUILDVALUE','Total building exposure stock','2022 USD','Hazus 6.0 2022 valuations associated with 2020 Census geography; not annual loss, land value or tract income','5-9'),
 ('POPULATION','Population used in FEMA exposure calculation','people','Archived Hazus exposure population; do not substitute study population in archived-rate reproduction','5-9'),
 ('AGRIVALUE','Agricultural exposure stock','2022 USD','USDA 2017 Census of Agriculture source, inflation-adjusted, geography allocated by documented agriculture method','5-9 to 5-12'),
 ('SOVI_SCORE','National percentile social vulnerability','0-100','Mandatory separate social dimension; v1.19 uses CDC/ATSDR SVI inputs, not income quartiles','4-1 to 4-3'),
 ('RESL_SCORE','National percentile community resilience','0-100','HVRI BRIC county-level value assigned to tracts; constant 15.44 in this study subset','4-3 to 4-4'),
 ('RESL_VALUE','Underlying community resilience index value','index','Underlying source value, distinct from nationally ranked RESL_SCORE','4-3 to 4-4'),
 ('CRF_VALUE','Community Risk Factor','dimensionless','Social-vulnerability/resilience ratio mapped to triangular distribution bounded 0.5-2, mode1; multiplies EAL to form risk','4-5'),
 ('ALR_VALB','Composite expected annual building-loss rate','fraction/year','EAL_VALB / BUILDVALUE, across applicable hazards','5-34'),
 ('ALR_VALP','Composite expected annual population-loss rate','fraction/year','EAL_VALP / POPULATION, using population-equivalent loss in people units','5-34'),
 ('ALR_VALA','Composite expected annual agricultural-loss rate','fraction/year','EAL_VALA / AGRIVALUE where agriculture exposure is positive; zero-exposure zero is not a measured rate','5-34'),
 ('ALR_NPCTL','Unadjusted composite expected-annual-loss-rate national percentile','0-100','National rank of EAL-weighted component-rate national percentiles; not a simple total-EAL/total-exposure quotient','5-35 to 5-36'),
 ('ALR_VRA_NPCTL','Social-vulnerability/resilience-adjusted loss-rate percentile','0-100','Rate adjusted by CRF before percentile transformation; excluded from candidate D because it reintroduces the social factor','5-36')]
 pd.DataFrame(defs,columns=['field','definition','units','qualification','v119_printed_pages']).to_csv(OUT/'FEMA_FIELD_DEFINITIONS.csv',index=False)
 md('FEMA_FIELD_DEFINITIONS_AND_COMPOSITION.md',f'''# FEMA v1.19 fields and composition

Source data are the archived Data/NRI_Table_CensusTracts_California.csv, 9,106 rows, every NRI_VER = Mar-23. All analyses use the exact 2,291 saved residential tract identities. Published percentile scores are retained without recomputing ranks in California or Los Angeles. RISK_SCORE, BUILDVALUE and SOVI_SCORE reproduce the saved Stage7 columns within recorded floating-point tolerance; see SAVED_STAGE7_SOURCE_REPRODUCTION.csv.

## Version-specific documentation

FEMA National Risk Index Technical Documentation, March2023, specifically v1.19.0, was retrieved as the FEMA document preserved by Ohio Emergency Management in its 2023 state-plan appendix: https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf . Its exact PDF, page text, SHA256 and URL are retained. The generic current FEMA technical-document URL now describes v1.20 and was not used to define this release. The live data-dictionary endpoint returned a non-document response; this limitation is recorded rather than substituting a newer dictionary. Version-specific equations and the actual archived field identities supply the required verification.

## Composition

For tract i and applicable hazards h and consequence types c:

EAL_ihc = exposed_value_ihc × annualized_frequency_ih × historic_loss_ratio_ihc,

with hazard-specific implementations, including the probabilistic earthquake method. Composite EAL sums the hazard losses. EAL_VALT = EAL_VALB + EAL_VALPE + EAL_VALA. EAL_VALPE = 11,600,000 × EAL_VALP in 2022 USD. It monetizes fatalities and injuries, not all population disruption or electric-service losses.

EAL_SCORE = 100 × (national rank(EAL_VALT) − minimum rank)/(maximum rank − minimum rank).

This published percentile is neither dollars nor hazard occurrence probability. A score difference is a percentile difference, not a proportional loss change. EAL_VALT is a monetary loss estimate. RISK_VALUE = EAL_VALT × CRF_VALUE. CRF maps the social-vulnerability/resilience ratio to a triangular distribution bounded0.5-2 with mode1. RISK_SCORE nationally ranks the adjusted risk value. Adding RISK_SCORE beside SOVI_SCORE mechanically embeds social vulnerability twice; actual correlation is a different, empirical issue.

SOVI and RESL are not direct multipliers in the unadjusted EAL calculation. Nevertheless, population/building/agricultural exposure, hazard geography and loss history can correlate with socioeconomic conditions. Absence of the CRF does not establish statistical or causal independence from social vulnerability. Building exposure uses the same Hazus stock underlying BUILDVALUE, with hazard-specific exposed portions; EAL is not merely BUILDVALUE, nor an exposure-free hazard measure.

ALR_VALB = EAL_VALB / BUILDVALUE; ALR_VALP = EAL_VALP / POPULATION; ALR_VALA = EAL_VALA / AGRIVALUE where the denominator exists. FEMA cautions against an all-consequence total dollar-rate quotient. ALR_NPCTL instead nationally ranks an EAL-weighted average of the separate consequence-rate national percentiles. It reduces total-stock scaling but retains consequence composition and EAL-derived weights. ALR_VRA_NPCTL further introduces the Community Risk Factor and must not be treated as independent of SOVI.

All component sums, population monetization, risk adjustment and available rates reconcile numerically within rounding tolerance; see EAL_NUMERICAL_COMPOSITION_QA.csv. National percentile formulas cannot be independently reconstructed from the California-only archive, so national scores are verified by release/source identity and monotone correspondence, not recomputed locally.

## Values, scores and ratings

Values have their stated dollar, population or index units. Scores are published national percentile positions for comparable geography. RISK/EAL ratings are five nationally derived k-means/natural-breaks categories, not fixed20-point score bins; SOVI/RESL ratings use national quintile boundaries. State percentiles (SPCTL) are different from national SCORE. Ratings and state scores are retained for audit and not treated as continuous substitute measurements.

{pd.DataFrame(defs,columns=['field','definition','units','qualification','v119_printed_pages']).to_markdown(index=False)}

## Scope of multi-hazard coverage

The archive contains all18 hazard EAL fields. Non-applicable hazard values remain null with their archived rating; they are not represented as observed zero losses. Present hazard values reconcile the total. Across these residential tracts, earthquake contributes98.1563% of pooled EAL; median tract share99.2745%. This is a multi-hazard calculation with a geographically earthquake-dominated composition, not an earthquake-only variable and not balanced evidence for equal importance of every hazard. Buildings contribute69.8545%, monetized population30.1443%, agriculture0.0011% of pooled EAL. These are shares of modeled annual losses, not socioeconomic or power-recovery causal effects.
''')
 best=summary[(summary.budget=='original_domain_totals')&(summary['transform']=='log_exposures')&(summary.k==5)][['feature_set','silhouette_mean','silhouette_sd','minimum_cluster_size','ari_saved_mean','ari_vs_A_mean']]
 stable=st[(st.budget=='original_domain_totals')&(st['transform']=='log_exposures')&(st.k==5)].groupby('feature_set').ari.agg(['min','median','max'])
 modeltable=f[(f.scope=='complete_stage7')&(f['transform']=='log_exposures')][['feature_set','max_vif','condition_number_standardized']]
 md('NRI_EAL_DECISION.md',f'''# Provisional decision on multi-hazard loss, economic stock and social vulnerability

The analysis preserves SOVI_SCORE, T80 and Init_Supply; no final typology, recovery choice, built-environment variable, manuscript or figure was changed. Recommendation remains provisional pending author decisions on recovery and physical-form inputs.

## Recommendation

For an interpretable joint typology that explicitly distinguishes economic stock from normalized multi-hazard loss propensity, provisionally prefer **D: SOVI_SCORE + log1p(NRI_BUILDVALUE) + ALR_NPCTL**. The archived unadjusted rate percentile exists and its exact v1.19 methodology is documented. It preserves stock as a separate economic coordinate while reducing the stock/EAL redundancy. It is not pure hazard and still uses consequence composition and loss-derived weights. Its lower collinearity is supporting evidence, not the definition of its scientific value.

**B: SOVI_SCORE + EAL_SCORE is defensible if the intended coordinate is explicitly combined multi-hazard expected loss and exposure.** It is the leading compact alternative, not an equivalent replacement for stand-alone stock. The decision to use B must accept that absolute stock is no longer directly represented and that equal weighting inside the combined domain amplifies its single score relative to each of two separate coordinates. We do not recommend selecting it simply for higher silhouette or fewer columns.

Do not retain A as the default when independent social vulnerability is already mandatory: RISK mechanically includes the social/resilience Community Risk Factor. C remains scientifically possible when both absolute stock and total expected loss have an explicit purpose; its log-scale redundancy is material but not a universal numerical prohibition. ALR_VRA_NPCTL is not proposed because it reintroduces the social adjustment.

## Actual associations: all2,291 tracts unless a physical-form field has missing coverage

{correlation_table}

EAL_SCORE versus RESL_SCORE is undefined: RESL_SCORE is constant15.44, not zero correlation. EAL_SCORE and EAL_VALT have identical rank ordering (Spearman1), but their Pearson correlation0.5677 shows that percentile and dollar spacing are different. EAL_SCORE versus log1p(EAL_VALT) Pearson0.9375. Raw EAL_VALT skewness8.052 falls to0.806 on log1p; raw building-value skewness6.803 falls to0.464. Both main monetary fields are positive and complete. Agriculture has structural zeros, which remain valid zero losses; undefined exposure-normalized rates are not invented.

1. **Overlap with SOVI:** materially lower marginal overlap for EAL than RISK. The paired IID-tract bootstrap of absolute Pearson overlap difference gives estimate−0.3365,95% interval[−0.4068,−0.2580]; spatial dependence is not adjusted. This establishes a descriptive reduction, not independence. EAL_SCORE partial correlation with SOVI controlling log building stock and log population density is0.3468 (rank-residual partial0.4175), so the small marginal correlation conceals conditional association.
2. **Overlap with stock:** EAL_SCORE Pearson0.5853 with raw stock,0.8310 with log stock, Spearman0.8585. Raw total-dollar EAL versus raw stock Pearson0.9116. Total EAL is partly driven by asset quantity and population monetization, while differing loss rates and hazard composition provide additional information.
3. **Replacing stock:** B retains an economic-loss/exposure coordinate, but not the economic stock dimension itself. EAL_SCORE alone explains69.05% of log-stock variance linearly;30.95% remains unrepresented by that one linear coordinate. This is in-sample descriptive variance, not information-theoretic loss or out-of-sample accuracy. It cannot recover absolute stock differences, low-loss/high-stock tracts or the split between assets and human-equivalent expected loss.
4. **Score versus value:** use EAL_SCORE for nationally relative expected-loss position and log1p(EAL_VALT) when magnitude of annual-dollar losses is central. Raw dollars have substantial long-tail leverage. Neither representation is universally superior; they must not simultaneously double-weight the same EAL construct. ALR_NPCTL answers a different exposure-normalized question and belongs with explicit stock when retaining both dimensions is intended.
5. **Loss versus pure hazard:** the recommended inputs are multi-hazard expected-loss or loss-rate constructs, not PGA, loss-free hazard probability, wealth, poverty, or the earthquake-recovery scenario. No single-event or earthquake-only substitute is proposed.
6. **Scientific interpretation:** D separates stock and loss propensity; B combines expected loss and exposure. Neither can be labeled pure natural hazard. SOVI stays mandatory in both. Other feature-domain weights and all non-FEMA inputs are fixed for each controlled comparison.

## Collinearity and conditional evidence

{modeltable.to_markdown(index=False)}

EAL_SCORE is75.63% linearly explained by SOVI, log stock and log density jointly; ALR_NPCTL is16.00% explained by those same controls. These are shared statistical variance fractions, not causal attribution. C full-model maximum VIF5.35 with log exposures versus D1.75 and B1.72. Thresholds alone do not decide whether a coordinate is meaningful. VIF here refers to simultaneous predictors and standardized condition numbers exclude arbitrary unit scaling.

## Controlled clustering evidence, not a variable-selection contest

There are24 matrix conditions: six definitions (A-D plus B/C dollar-value alternatives), raw versus log-exposure preprocessing, and two explicit domain budgets. Seed42 selects k by the existing k1-10 inertia-distance elbow; five seeds42-46 compare fixed k5 and the selected k. There are{len(s)} distinct fitted run records; identical fixed/selected k5 fits are reused, not counted twice. Every matrix has the same2,291 rows, T80/Init, four grid descriptors, housing-age ratio and population density. No new building variable or final clustering is inserted.

Primary comparability reproduces the original domain totals: recovery2/11, grid4/11, built2/11, social1/11, loss/exposure2/11. Each standardized coordinate is multiplied by sqrt(domain budget / domain coordinate count). B's one loss score receives the same total budget as A/C/D's two-coordinate loss/exposure domain. A second analysis uses1/5 per domain, held constant across all alternatives. Domain budgets and actual between-cluster contributions are exported separately. Changes caused by content, log transforms and domain weighting can be located independently.

{best.to_markdown(index=False)}

Within-condition seed-pair ARI at fixed k5, log exposures and original domain totals:

{stable.to_markdown()}

B's seed variability (median pairwise ARI0.6041, minimum0.2737) is unresolved evidence against claiming a settled robust clustering. D's median0.9628 is more stable in this condition but does not itself prove superior scientific content. Equal-domain conditions choose k4 while original totals typically choose k5/6; this demonstrates that a changed weight budget is substantively influential. The A/log/original-budget seed42 replay exactly reproduces saved labels (ARI1); comparisons with old labels are descriptive only and never used as a selection rule.

## Boundaries and remaining decisions

The new physical-form metrics are correlated on explicit matched subsets only; their source limitations remain unchanged. Neither imperfect age linkage nor unverified imperviousness is promoted. Conditional associations and cluster stability do not establish causality, hazard validation, or independence. No final variable allocation is approved by this audit. The unresolved recovery B-versus-T80 and built-environment choices require a later author decision; this audit keeps T80 as the existing formal input throughout.
''')
 # Add exact interpretation to each numerical feature-set row.
 meaning={'A':'social vulnerability + building stock + socially adjusted multi-hazard risk','B':'social vulnerability + combined multi-hazard expected-loss/exposure percentile','C':'social vulnerability + building stock + total expected-loss percentile','D':'social vulnerability + building stock + unadjusted normalized multi-hazard loss-rate percentile','B_value':'social vulnerability + monetary multi-hazard expected loss','C_value':'social vulnerability + building stock + monetary expected loss'}
 f['scientific_meaning']=f.feature_set.map(meaning);f['prespecified_domain_weight_policy']='loss/exposure total2/11 (original-domain totals) or1/5 (equal domains), fixed across all compared feature sets';f['stock_information_lost']=f.feature_set.map(lambda x:'stand-alone stock coordinate omitted; economic meaning becomes modeled annual loss' if x.startswith('B') else 'stock coordinate retained');f.to_csv(OUT/'FOUR_FEATURE_SET_COMPARISON.csv',index=False,float_format='%.15g')
 md('README.md','''# FEMA multi-hazard EAL, building exposure and social vulnerability audit

Start with NRI_EAL_DECISION.md. The seven requested deliverables, original-source identities, descriptive uncertainty, full controlled clustering records, domain weights and run specification are in this folder. No formal Stage7 label, manuscript, figure, recovery simulation, GA result, mapping or independently developed physical-form input is changed.

Run the installed Anaconda Python on run_nri_audit.py, then write_report.py, then the focused pytest file. Both calculation scripts resolve repository paths from this folder. Required prior candidate physical-form table is read only and identified by SHA256. The clustering comparison uses the complete original Stage7 covariates; extra physical-form metrics are used only for pairwise correlation.

All published FEMA scores remain on their original national scale. Raw and log1p monetary representations are separately reported. Undefined constant-field correlations remain null. Published cluster labels are retained only for descriptive ARI comparisons, never feature selection. The recommendation is provisional.

Sources/FEMA_V119_TECHNICAL_DOCUMENTATION.pdf is the exact March2023 FEMA technical document preserved by Ohio Emergency Management. Source hashes and documented failed live dictionary retrieval are retained. The original California NRI data are not replaced with current FEMA data.
''')
 md('EXECUTION_LOG.md','''# Execution log

1. Confirmed baseline031d2c675f8e7d58035d27448be040b809ced086 and remote revision HEAD; inspected branch,862 staged additions, unrelated untracked work and LFS state. No reset, checkout, stash or change to the original Git index.
2. Snapshotted950 protected paths including212 original protection records. All measurements use the exact2,291 residential GEOIDs, preserving original order and11-character identity.
3. Retrieved FEMA March2023 v1.19 technical documentation from Ohio Emergency Management's preserved primary FEMA document. Current generic FEMA technical documentation is v1.20, so excluded. Dictionary endpoint returned a non-document response; definitions and actual composition verified against the archived release and v1.19 equations.
4. Reproduced Stage7 risk, stock and SOVI source values and checked the EAL sum,18-hazard total,11.6-million population monetization,CRF multiplication and consequence-rate identities. No new FEMA release merged.
5. Calculated990 pairwise raw/rank correlations,2000 descriptive paired-tract bootstrap resamples for overlap reduction, VIF/standardized condition numbers and explicit conditional/stock-reconstruction variance fractions.
6. Ran bounded controlled KMeans comparisons at24 matrix conditions with common domain budgets and five seeds. Saved195 distinct fixed/selected-k records and240 seed42 k-sweep records. Reused fits when fixed k5 equals selected k. Reproduced saved formal labels for benchmark seed42 without modifying them.
7. Initial audit-script Index API and DataFrame column-name lookups failed; corrected only the new analysis script. The final complete run supersedes partial outputs. No scientific input was changed. Runtime and algorithm versions are recorded separately.
8. Wrote decision and field-composition reports from completed numerical tables. No variable was chosen for a silhouette improvement or agreement with old clusters. Recommendation remains provisional.
9. Verified950 protected files,2008 formal numerical/GIS/trajectory inputs, all used-source hashes and original staged index unchanged. Focused numerical tests and scoped Git/LFS publication verification are recorded in separate artifacts.
''')
 print('REPORTS_COMPLETE',flush=True)
if __name__=='__main__':main()
