"""Author-facing interpretation; never write to formal science or manuscript."""
from common import *


def table(df): return df.to_markdown(index=False,floatfmt='.4f')


def main():
    d=frame('VERIFIED_COHORT_AND_DESCRIPTORS.csv'); s=sources()
    e=pd.read_csv(lp(OUT/'K_EVIDENCE_MATRIX.csv'))
    comp=pd.read_csv(lp(OUT/'P2_VS_P2_CBM_MEMBERSHIP_COMPARISONS.csv'))
    rank=pd.read_csv(lp(OUT/'CBM_COMPONENT_REMOVAL_RANK_QA.csv'))
    pro=pd.read_csv(lp(OUT/'PER_CLUSTER_CBM_AND_RQ_PROFILES.csv'))
    cc=pd.read_csv(lp(OUT/'DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv'))
    qa=json.loads(lp(OUT/'SOURCE_RECONSTRUCTION_QA.json').read_text())
    paired=json.loads(lp(OUT/'FROZEN_PAIRING_AND_INFORMATION_QA.json').read_text())
    by=comp.loc[comp.comparison.eq('component')].groupby(['specification','alternative','k']).agg(
        minimum_ARI=('ARI','min'),mean_ARI=('ARI','mean'),maximum_ARI=('ARI','max'),
        mean_reassigned_tracts=('reassigned_tracts','mean'),mean_reassigned_population_share=('reassigned_population_share','mean')).reset_index()
    compare=comp.loc[comp.comparison.eq('feature_specification')&comp.specification.eq('P2')&comp.k.isin([3,4,5])].groupby(['alternative','k']).agg(
        mean_ARI=('ARI','mean'),mean_reassigned_tracts=('reassigned_tracts','mean'),mean_reassigned_population_share=('reassigned_population_share','mean')).reset_index()
    md('SOURCE_AND_PRIOR_AUDIT_RECONCILIATION.md',f'''# Source and prior audit reconciliation
{WARN}

Starting authority: `{AUTH}`. Exact source paths, actual payload hashes and Git/LFS identities are in SOURCE_HASH_VERIFICATION_*.csv. Source selection is pinned to that commit, not a live replacement release. Original CDC national/California archives, dictionary, PDF and raw/map service evidence remain in the prior CDC package; no source is changed or duplicated as a new release.

The prior audit withheld formal admission and ran no clustering. This task explicitly authorizes **published-as-is exploratory fits** while retaining the unresolved formal quality gate. This is a change in authorized analysis scope, not a reversal of the previous source findings.

Verified domain=2,315; positive-population cohort=2,299; frozen represented population=9,066,522;16 zero-population GEOIDs are exported;8 zero-housing positive-population tracts retained. Exact eleven-digit GEOIDs, frozen SOVI and original quartiles are unchanged. CDC's separate ACS population is never substituted. The seven P2 values come from their original multi-policy frozen descriptor and value tables; later audit CSV serializations agree within1e-12. Official CBM values match national-source decimal values (binary CSV-parser roundoff <=2e-16 only).

Old P2 weighted matrix is bitwise identical before reuse; scaler values and coordinate order agree. 124 P2 main/policy fits and28 P2 geographic predictions are reused; all new H1/H2 fits keep the registered settings. Inertia and full-cohort silhouettes are recomputed, not merely copied as numbers. All492 saved fits are preserved, plus geographic and narrowly scoped Init ablations. RQ3 budgets are squared-distance budgets; their square roots multiply cohort population-SD z scores.

The seven-policy frozen station-integral/mapping extraction independently reproduces all seven ensemble sets over1,000 realizations with maximum error {paired['maximum_recomputed_ensemble_error_hr']:.3g} h. No trajectories, source paths, schedules, MC samples or GA are recalculated. The previous source audit's7,000-event pairing and physical/damage/duration hashes remain authoritative; this task verifies the exact published extraction and manifest QA, not a new full raw-event re-audit. Full source-level event reconstruction still requires the manifest-bound local archive absent from Git. Core arithmetic and conditional fits use tracked hash-bound sources after Git LFS retrieval.

Protection: the950 original scientific payloads and all preceding diagnostic Git blobs are recorded at start and independently rechecked at completion, together with unrelated original Git status/staged-diff hash. Only this new package is deliverable.
''')
    md('PUBLISHED_CBM_QUALITY_LIMITATIONS.md',f'''# Published-as-is limitations retained
{WARN}

- F_NEHD, F_SMOKE and F_BURN are absent from the examined full official2024 archives, matching dictionary and raw service. Flags are not inferred from percentiles.
-2,251 burned-area zeros (8,892,273 frozen residents) have unresolved zero-versus-source-null/excluded provenance. They are **neither asserted missing nor verified physical zeros**. Removing burned area tests its numerical influence, not the validity of each zero.
- All2,299 hurricane values have F_HRCN=1: source-null/excluded values converted to zero. The code does not distinguish the exact exclusion cause. This is locally constant, so it does not drive local rank differences; national calibration can still depend on it.
- CDC documents13 nationally neighbor-interpolated heat records without releasing their GEOIDs. Their study membership cannot be determined; positive heat estimates do not prove absence of such processing.
- Riverine uses a source-frequency/minimum-frequency/spatial-support construct, not measured electricity failure. Locally its percentile has only two values (0 or0.8605;439 positive-ranked tracts).
- Historical burned area is large-wildfire intersection during2013-2022, not current CAL FIRE severity or all fires. Smoke is polygon-intersection frequency, not ground-level dose.
- CDC drought wording and matching FEMA NRI frequency units remain inconsistent (weeks wording versus event-days values); no source is silently corrected. Mixed periods/supports and minimum-frequency processing remain documented in the prior indicator source register.

Standalone RPL_CBM has no direct social-demographic, building-value or resilience adjustment, but geographic dependence remains possible. It excludes earthquake and is not an all-natural-hazard risk or multi-hazard electricity-restoration simulation. Complete published rank coverage does not establish complete underlying physical observations. Exploratory stability cannot resolve these source limitations.
''')
    md('CBM_NATIONAL_RERANK_RECONSTRUCTION.md',f'''# National rerank reconstruction
{WARN}

Original national archive=85,188 records; fixed valid published-CBM universe=83,509. Sum the nine published EPL indicator values to reproduce SPL_CBM (maximum error below1e-12). Minimum rank convention `(rank_min - 1)/(N - 1)` reproduces the exported official four-decimal RPL_CBM within {qa['max_official_rank_error']:.9g}, below5.01e-5 rounding tolerance. No LA-only percentile is substituted.

Researcher diagnostics sum the retained indicator percentiles and rerank **the same eligible national universe**, separately removing RFLD, BURN, NEHD, or both SMOKE/BURN. Published four-decimal EPLs are converted to integer ticks before summation, preserving exact ties. This conditions comparability on the original eligible universe; it does not admit previously excluded national records or recreate CDC source processing. The published official rank is used unchanged for the main fits. Counterfactual ranks are researcher diagnostics, never alternate CDC products.

Top-230 comparison is an exact-count regional upper-decile diagnostic (ceil(0.1*2,299)), with ties broken by stable sorted GEOID order. Local rank displacement is reported separately from absolute national percentile shift. Deleting an indicator also changes calibration and standardized coordinate shape; these are not new hazard observations.

{table(rank.drop(columns=['official_CDC_alternative']))}

Independent QA uses stdlib CSV, Decimal exact sums and NumPy sorted-search minimum ranks. The original prior audit's unrounded float summation produced artificial sub-ULP tie splits: maximum counterfactual rank correction0.000563. NUMERICAL_TIE_HANDLING_AMENDMENT.json records this independent numerical finding and the bounded rerun of only the120 existing component fits. Main official-CBM, P2, policy and geographic fits are unchanged. Prior packages are not overwritten. Component pre/post correction ARI is0.99047–1.0; scientific recommendations are unchanged, but corrected values are authoritative here.
''')
    md('RIVERINE_AND_BURN_SENSITIVITY.md',f'''# Riverine, burned-area, heat and wildfire sensitivity
{WARN}

Riverine contributes69.248% of local SPL covariance variance, heat12.215%, wildfire10.310%, coastal8.106%. These are local covariance shares, not declared policy weights or causal hazard shares. The binary riverine-support split explains {paired['published_CBM_riverine_binary_R2']:.2%} of official local CBM rank variance. Heat changes fine ordering substantially: removing heat retains only51.74% of top230, versus53.48% after riverine removal. Burn removal retains95.22%; wildfire-domain removal90.87%.

Bounded component fits use H1/H2 K3/4/5 and seeds42-46. Those Ks are the predeclared continuity range plus all main endpoint bends/silhouette maxima; no additional K is needed. Each counterfactual is standardized on the unchanged2,299 cohort; other coordinates are unchanged.

{table(by)}

Riverine removal has the largest membership effect, particularly H1/K5 (mean ARI0.855;6.20% of resident population reassigned). Nevertheless, K3–K5 retain broadly similar recovery/dependency contrasts rather than losing an exclusively flood-defined regional class. Burn removal gives ARI0.951–0.996 across these fits: the unresolved component is not driving the regional partition. This does not validate its zeros or restore the source-quality gate.

Heat/wildfire influence individual ranks and selected memberships but do not create stable stand-alone climate classes in the credible K3–K5 range. A modest clustering effect alongside a large top-rank change is expected when the climate coordinate provides only a small share of realized between-class separation. These are distance-geometry findings, not estimates of real multi-hazard outage consequences.
''')
    physical=pd.read_csv(lp(OUT/'CLIMATE_CONTEXT_PHYSICAL_CROSSCHECK.csv'))
    md('CLIMATE_CONTEXT_PHYSICAL_CROSSCHECK.md',f'''# Physical-context crosscheck
{WARN}

Use matched frozen physical records without replacing missing coverage by zero. Valid denominators remain CAL FIRE2,200, complete NFHL SFHA2,088, CDC historical heat2,299, and CGS PGA2,294. Joint original four-family coverage remains2,032, but no tract is removed from clustering. Per-class valid counts, ranges and cohort comparisons are in CLIMATE_CONTEXT_PHYSICAL_CROSSCHECK.csv.

The prior source-matched associations provide partial geographic consistency: riverine frequency versus SFHA land fraction Spearman0.944, burned area versus CAL FIRE high-severity fraction0.278. Event frequency differs from mapped flood area, historical burn/smoke differs from fire severity, and PGA is separate earthquake context absent from CBM. Historical heat agreement is exactly the **same CDC source**, not independent climate validation. Coastal V/VE intersections in the previous audit are partially supported lower bounds, not complete no-hazard observations.

The broad high-added-burden and higher-baseline-burden classes have higher CBM means than the large low-increment class, but no K3–K5 class represents all high-climate tracts or a measured outage response to those hazards. These physical layers support cautious climate-context descriptions, not validation of source-defined zeros, electricity-demand claims or causal interactions. See exact class-specific values rather than assuming every high-CBM tract has all hazards high.

{table(physical.query('specification=="H2" and k==3')[['cluster','physical_measure','n_class','valid_count','missing_support','mean_valid','cohort_valid_mean']])}
''')
    md('CDC_EJI_TECHNICAL_CLARIFICATION_DRAFT.md',f'''# Technical clarification email draft
{WARN}

**Draft only. Not sent; no provider contacted.**

To: CDC/ATSDR Environmental Justice Index technical team (contact address to be confirmed)
Subject: EJI 2024 Climate Burden Module: archived zero/null flags and heat interpolation identifiers

Dear EJI Technical Team,

We are auditing the standalone Climate Burden Module in the archived EJI2024 national and California CSV releases for tract-level research in Los Angeles. We use the official RPL_CBM, not RPL_EJI_CBM. Our sources are the EJI2024 CSV archives and EJI_DATADICTIONARY_2024, together with [EJI2024 Technical Documentation](https://atsdr.cdc.gov/place-health/media/pdfs/2024/10/EJI_2024_Technical_Documentation.pdf) and the [Climate Burden indicator descriptions](https://www.atsdr.cdc.gov/place-health/php/eji/eji-indicators-climate-burden-module.html).

Could you please clarify:
1. Are F_NEHD, F_SMOKE and F_BURN available for this exact2024 release, and what are their code definitions? They are absent from the full CSV archives, matching dictionary and raw service we examined.
2. Can E_BURN=0 arise both from no qualifying2013-2022 MTBS wildfire intersection and from source-null/excluded records? Is there an archived field or auditable record distinguishing these cases?
3. Can original zero-versus-source-null/exclusion flags be provided for the archived2024 CBM, including the three fields above? We are not treating all unflagged zeros as missing.
4. Can you provide the GEOIDs, or an auditable identification method, for the13 nationally interpolated extreme-heat tracts described in the technical documentation?
5. For E_HRCN/EPL_HRCN and F_HRCN=1, can geographic source exclusions be distinguished from other source-null conditions? How do zero substitution and FEMA minimum annual-frequency assumptions interact for supported versus excluded tracts?

We retain the published rankings unchanged and would like to report their data-quality limitations accurately. We can supply our archive SHA256s and affected GEOIDs if helpful.

Thank you for your assistance.
Yinchen Yi and Yutong Li
''')
    er=e.query('k in [3,4,5]')
    metrics=er[['specification','k','mean_silhouette','seed_min_ARI','geographic_min_ARI','geographic_median_ARI','policy_LOO_min_ARI','policy_LOO_mean_ARI','smallest_seed42_class','RQ3_between_share']]
    p=pro.loc[pro.condition.eq('published')&pro.k.eq(3)].pivot(index=['specification','cluster','n_tracts','population_share'],columns='variable',values='mean').reset_index()
    profile=p[['specification','cluster','n_tracts','population_share','B_Unconstrained','MeanDelta','SOVI_SCORE','Population','RPL_CBM','Grid_Impact']]
    main_cc=cc.loc[cc.condition.eq('published')&cc.specification.isin(['H1','H2'])&cc.k.isin([3,4,5])&cc.seed.eq(42)&cc.variable.eq('RPL_CBM')]
    md('FINAL_CBM_CONDITIONAL_AUTHOR_DECISION.md',f'''# Conditional CBM: scientific author decision
{WARN}

## Recommendation, not formal promotion
**Retain seven-variable P2 as the primary candidate; retain published-as-is P2-CBM as an explicitly qualified sensitivity extension and climate/domain maps as descriptors.** If an eight-coordinate sensitivity is shown, H2 preserves the declared SOVI budget and is the less disruptive K3/K4 comparison. It is not a statistically optimal weighting or uniformly superior robustness result. Neither a final K nor formal Stage7 admission is approved here.

## Direct answers
1. **Useful additional RQ3 construct? Yes as selected climate-context information, not clearly necessary for the primary typology.** Standalone CBM contains no direct demographic/SOVI/asset/resilience adjustment. Prior all-P2 conditional linear R2=0.07238,VIF=1.078; thus exclusion is not justified by simple duplication. Environmental context is different from simulated earthquake recovery.
2. **Memberships change? Moderately at K3/K4, more at K5.** H1 K3/K4 mean ARI versus P2=0.799/0.842;H2=0.906/0.934. H1 reassigns about5.81%/4.51% of population;H2 about2.37%/1.66%. K5 comparisons reassign14–15%, partly because P2 has competing seed optima and a tiny low-population class. These are feature addition **plus** RQ3 budget changes, not isolated climate effects.
3. **K evidence? Smooth bends favor K3 with K1-6/7 endpoints, K4 with K1-8 endpoints for both H1/H2.** Mean silhouette peaks at K5 (H1={e.query('specification=="H1" and k==5').mean_silhouette.iloc[0]:.6f};H2={e.query('specification=="H2" and k==5').mean_silhouette.iloc[0]:.6f}). H2 K4 and K5 are nearly tied and seed ranges overlap. K3 supplies broad recovery contrasts;K4 mostly isolates the Q-proxy initial-state exception;K5 adds a spectral-criticality split. There is no sharp, universal statistical optimum, and absolute silhouettes across spaces are not common physical validation scores.
4. **Stability? Mixed, not uniformly improved.** Main H1/H2 seeds are stable at K3–K5 (minimum ARI0.9809 or higher), improving the competing P2/K5 optima. Geographic and policy-set agreement remain moderate and configuration-dependent. H1/K5 worst LOO ARI0.394, geographic0.406;H2/K5 about0.563/0.578. H1/K4 geographic median0.965 but worst0.626;H2/K4 worst0.583 versus P2/K4 0.784. Fixed reference scaling can be highly consequential (H1/K2 one LOO ARI0.044); this is not hidden by cohort rescaling. No claim of improved universal robustness is supported.
5. **Riverine dominance? Yes for the climate score, not for the overall K3–K5 partition.** Riverine contributes69.248% of local summed-score covariance variance and its binary split explains84.332% of final rank variance. Removing it gives mean ARI0.855–0.951 for K3–K5. The overall partition remains primarily restoration/network-driven.
6. **Burn sensitivity? Small regionally.** Component-removal ARI0.951–0.996 over the registered fits; H1/K5 is most affected (~1.71% population reassigned on average). This reduces concern about partition leverage but does **not** establish that2,251 zero records were physically observed zeros.
7. **Heat and wildfire? Meaningful rank/context effects, modest classification effects.** Removing heat changes nearly half of top230 ranks, but cluster ARI0.916–0.992;wildfire removal0.907–0.985. They provide finer ordering and subset descriptions, not new simulated outage mechanisms or stable independent climate community regimes.
8. **Joint three-RQ meaning? The original joint patterns remain legible, but climate does not materially improve differentiation.** At K3–K5, CBM accounts for only {main_cc.between_fraction_of_all.min():.2%}–{main_cc.between_fraction_of_all.max():.2%} of realized between-class squared separation. H1's total RQ3 share is7.0–9.3%,H2's11.9–15.5%; assigned one-third is not realized one-third. A large low-increment class has higher SOVI; higher added/baseline burden classes have somewhat higher climate ranks. None is an observed multi-hazard outage class.
9. **Physical evidence? Partial geographic correspondence.** NFHL supports the riverine geography on2,088 complete-support tracts;fire-history/severity correspondence is weaker on2,200;heat is the same CDC source, not independent validation;PGA is separate context. No missing coverage is set to zero or excluded to improve clusters.
10. **Primary candidate? P2 remains sufficient.** CBM deserves further contextual consideration, but no clear new community construct outweighs the unresolved provenance and local component concentration. Use H2 only as an explicitly labeled sensitivity if useful; do not replace formal Stage7 automatically.

## Exact comparisons
{table(compare)}

## K, robustness and realized RQ3 evidence
{table(metrics)}

## Broad K3 interpretation in original units
{table(profile)}

Cluster IDs are model-specific zero-based IDs in CSV (C1=0 in figures). Relative descriptions use the complete cohort distributions, not invented labels. The large low-increment class contains roughly57–58% of population with mean baseline~30h and added~1.6–1.7h; SOVI~75–78 and CBM~0.23. The high-added-burden class contains~19–20% with baseline~28h and added~7.1h; SOVI~50–53 and CBM~0.37. The higher-baseline class contains~22–23% with baseline~37.5–37.7h, added~4.1–4.3h, greater spectral impact and CBM~0.34–0.35. These differ across all three RQs without being independent model validation or causal environmental findings.

## Rare groups and weight leverage
The exact34 STATION Q tracts remain within large K3 classes;H1/H2 K4/K5 isolate a38-tract group containing all34. Its mean initial availability is1.731% (the exact34 remain~1.815%), not strong absolute resilience. Removing Init with registered RQ1 redistribution eliminates this small class and changes K4 ARI to0.28–0.34. Source-proxy interpretation, not mere seed stability, remains necessary. At higher K,12-tract/754-person classes can recur; all institutional/group-quarters tracts stay included.

The fixed-partition algebra separately reports climate-added BSS and negative SOVI/population reallocation. For example,H1/K3 adds20.251 climate BSS but removes19.982 combined preexisting RQ3 BSS;H2/K3 adds13.649 and removes4.682 population BSS. These are exact distance decompositions, not pure feature-addition causal effects or newly fitted optimized weights.

## Remaining author decisions and limits
The author must separately approve primary versus contextual climate use, acceptance of published source-zero semantics, H1 versus H2 if shown, the finite five-policy reference, conditional Init interpretation and final K. Provider clarification is drafted but **not sent**. Missing F_NEHD/F_SMOKE/F_BURN,2,251 unresolved burn zeros,13 unidentified interpolated heat records, hurricane F=1 cause ambiguity, mixed supports/minimum-frequency assumptions and drought unit wording remain unresolved. No source-quality gate is declared passed.

All492 saved fitted arrays and84 geographic predictions are retained;P2 reuse is source-verified. Core frozen ensemble arithmetic repeats within2.14e-14h. Full raw event/physical re-audit needs external manifest-bound archives. Geographic tests use four coarse quadrants and seed42; policy perturbations use seed42, not a full joint seed/geographic uncertainty experiment. Profiles and quartile composition share fitted inputs and are not independent validation. No formal Stage7, quartile, frozen simulation, manuscript or numbered figure is modified.
''')
    md('README.md',f'''# Conditional CDC CBM review package
{WARN}

Start with FINAL_CBM_CONDITIONAL_AUTHOR_DECISION.md. This package is an isolated author review; formal admission remains unresolved and no final model/K is promoted.

Starting source authority: `{AUTH}`. Reproduce with Python3.12 and repository dependencies after `git lfs pull`:

```powershell
python prepare.py --core-only
python fit_registered.py
python build_evidence.py
python reports.py
python figures.py
python verify_independent.py
```

Run from this directory or give full script paths. The source resolver verifies actual Git/LFS bytes and searches the current checkout and known archived worktrees. Core-only preparation explicitly skips external-archive preservation checks; use `python prepare.py` without that flag and set LA_GRID_FROZEN_SOURCE_ROOT to the manifest-bound original archive to perform the950-file/source-Git checks. `verify_independent.py` performs that full preservation verification and therefore requires the original archive. The diagnostic arithmetic/fits use tracked prior CDC/multi-policy extracts; raw event reproduction still needs external archives. A clean clone can reproduce the core results, but cannot substantiate the unavailable original archive by inference.

Main K1–8: P2,H1,H2,seeds42–46,n_init50,Lloyd,max_iter500,tol1e-4. Component removals: national83,509, H1/H2 K3–5,seeds42–46. Policy/geographic: K2–8,seed42, documented cohort and fixed-reference/training-only scaling. Init ablation:K3–5,seed42 with RQ1 redistribution. No MC/GA/recovery code is invoked. WCSS is weighted-space within-cluster sum of squares.

Full labels, silhouettes, matrices and prediction arrays are LFS NPZs. All publication-size vector PDFs and600dpi previews are under figures/. Matplotlib/GeoPandas generate the figures; no AI-generated artwork. Every component-removal rank is a researcher diagnostic, not an official CDC replacement. PER_CLUSTER_CBM_AND_RQ_PROFILES distinguishes researcher_climate_rank from Published_RPL_CBM. CSV IDs are model-specific, not formal Stage7 IDs.

Numerical QA, source hashes, preserved-science checks and remote real-LFS-byte verification are recorded separately. CDC_EJI_TECHNICAL_CLARIFICATION_DRAFT.md is draft-only. Source/provider license terms remain those in the original repository and CDC audit; no third-party data is re-licensed here.
''')
    save('SOURCE_HASH_VERIFICATION_REPORTS.csv',s.records)
    print('Author reports written; recommendation P2 primary, H2 qualified sensitivity only',flush=True)


if __name__=='__main__': main()
