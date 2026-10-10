# FEMA v1.19 Multi-Hazard EAL, SOVI and Building Stock Audit

**2026-10-09.** Reproducible independent diagnostic audit using the frozen March 2023 FEMA NRI data in `Data/NRI_Table_CensusTracts_California.csv` and original Stage 7 residential tract IDs in `Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv`.

This is **not a manuscript figure or an approved replacement of Stage 7 cluster features**. It does not rerun recovery simulations or mutate scientific outputs. All correlations have exactly **n=2,291** valid and matched tracts. Original-stage NRI RISK_SCORE differs from archived NRI_RISK_SCORE by ≤1.42e−14; source building value agrees exactly; source SOVI and archived SOVI differ by ≤4.83e−9. Frozen source SHA-256 values and all field diagnostics are recorded in `results/EAL_AUDIT_SUMMARY.json`.

## Component interpretation

The original FEMA National Risk Index v1.19 (March 2023) **RISK_SCORE** is a nationally referenced *multi-hazard* risk percentile that combines Expected Annual Loss (EAL) with social vulnerability and community resilience. Thus if Stage 7 separately includes SOVI_SCORE, RISK_SCORE duplicates social vulnerability **by construction**.

EAL_SCORE and EAL_VALT represent the composite annual expected **monetized** losses from all included natural hazard types before FEMA's *additional* SOVI/resilience risk factor. **EAL contains building value, population equivalence and agriculture consequence exposure** and is not a pure occurrence-probability or physical-hazard measure. In the 2023 v1.19 release, EAL_SCORE is a national percentile, while EAL_VALT is in annual expected dollars. Direct EAL_VALT equals EAL_VALB + EAL_VALPE + EAL_VALA to ≤7.45e−9 in the studied tracts; EAL_VALP is people, not money and must not be added to monetary consequence totals.

**SOVI_SCORE is mandatory** as a separate social-vulnerability feature. Do not use earthquake-only ERQK_RISKS/PGA as a replacement for a multi-hazard aggregate, and do not delete SOVI when changing risk features.

## Original same-tract empirical statistics

| Comparison | Pearson r | Spearman rho |
|---|---:|---:|
| SOVI_SCORE vs EAL_SCORE | **−0.0440** | −0.0685 |
| SOVI_SCORE vs log1p(BUILDVALUE) | −0.3244 | −0.3515 |
| EAL_SCORE vs log1p(BUILDVALUE) | **0.8310** | 0.8585 |
| log1p(EAL_VALT) vs log1p(BUILDVALUE) | **0.8780** | 0.8585 |
| EAL_SCORE vs overall RISK_SCORE | 0.8933 | 0.8864 |
| Overall RISK_SCORE vs SOVI_SCORE | 0.3805 | 0.3530 |
| ALR_NPCTL vs log1p(BUILDVALUE) | 0.2470 | 0.2349 |
| ALR_NPCTL vs SOVI_SCORE | 0.2173 | 0.2263 |
| EAL_SCORE vs ALR_NPCTL | 0.6267 | 0.6275 |

Same-input-set VIF results:

- SOVI_SCORE + EAL_SCORE: each **1.00194**. Minimal mutual collinearity.
- SOVI_SCORE + log1p(BUILDVALUE) + EAL_SCORE: maximum **4.4160** (building stock and EAL repeat exposure).
- SOVI_SCORE + log1p(BUILDVALUE) + overall RISK_SCORE: maximum **3.9721**.
- SOVI_SCORE + log1p(BUILDVALUE) + ALR_NPCTL: maximum **1.2675**, potentially better at distinguishing economic stock from normalized loss rate.
- SOVI_SCORE + log1p(BUILDVALUE) + log1p(EAL_VALT): maximum **6.6475**, particularly strong scale-related stock/exposure duplication.

Resilience source score RESL_SCORE is **15.44 for all 2,291 studied LA tracts**, so it has no within-domain variation and is not useful as an additional clustering coordinate.

## Critical caveat: all-hazard composition is highly earthquake-concentrated

The annual expected monetary loss total was independently recomputed from all **18 original hazard-specific EALT fields**, maximum discrepancy with EAL_VALT **7.45e−9 dollars**. Thus the dataset truly includes all supported types; no analyst cherry-picking was done.

But over these 2,291 tracts:

- **98.1563%** of summed multi-hazard EAL dollars comes from **earthquake**; wildfire **1.1723%**, tornado **0.4288%**, heat wave **0.1348%**, remaining hazards collectively ~0.108%.
- Mean tract earthquake share: **98.2648%**. Median tract share: **99.2745%**.
- Earthquake is the **largest EAL type in 2,281/2,291 tracts**; wildfire leads in 10.
- Pearson r(EAL_SCORE, ERQK_EALS) = **0.98222**, Spearman rho **0.98856**.
- Pearson r(ALR_NPCTL, ERQK_ALR_NPCTL) = **0.95280**, Spearman rho **0.96841**.
- Median effective number of monetary risk-contributing hazard types (1/Herfindahl shares) ~**1.015**.

Therefore neither EAL_SCORE nor the exposure-normalized ALR_NPCTL is a *balanced* representation of separate peril exposures in this LA sample. This is a property of FEMA's loss models and the local community, **not a decision by the analyst to exclude non-earthquake hazards**. Summing losses is legitimate for a **total expected annual economic consequence**, but do not equate that measure with diversity or equal representation of the 18 hazard threats. Do not assign arbitrary equal loss weights merely to make non-earthquake hazards more prominent without a separate scientific objective.

If the scientific question specifically needs geographic multi-hazard diversity, create a **separate documented hazard profile/diagnostic**, such as original peril EAL shares, leading hazards, conditional hazard presence and concentration. Do NOT relabel such profiles as original FEMA total risk score. Avoid simply summing heterogeneous event frequencies (days vs counts, different hazard applicability).

## Recommendation for controlled local analysis

**Leading hypothesis B:** keep SOVI_SCORE, replace both NRI_BUILDVALUE and RISK_SCORE with EAL_SCORE. Statistically low collinearity and transparent joint hazard/economic-loss construct. This sacrifices a **separate building-stock/economic-inventory coordinate**; EAL remains an economic consequence measure and is earthquake-dominated in this sample. Do not claim it measures pure hazard.

**Alternative D:** keep SOVI_SCORE and log1p(NRI_BUILDVALUE) as separate social/economic features, and use the national ALR_NPCTL as exposure-normalized loss-rate context. Three predictor VIFs all ≤1.268. It too is strongly correlated with earthquake-specific ALR, so it does NOT solve the hazard-type-concentration concern.

Compare both hypotheses within fixed Stage 7 domain weights and same recovery/service/grid/built-environment controls. Include EAL_VALT as a transform sensitivity and original RISK_SCORE as a benchmark only. Never use the best silhouette alone as a feature-selection rule. Do not use previous cluster labels as input selection evidence. Protect manuscript and original 212 scientific files.

## Deliverables

- `audit_eal.py`: original same-tract joins, source hash checks, peer-independent covariance recalculation, component sums, multi-hazard attribution and VIF calculations.
- `results/EAL_AUDIT_SUMMARY.json`: complete numeric statistical and source audit.
- `results/PAIRWISE_CORRELATIONS.csv`: pairs with matched N, raw and log modes.
- `results/CANDIDATE_SET_VIF.json`: each exact candidate set and its predictor-level VIF.
- `results/EAL_HAZARD_COMPOSITION.csv`: source hazard-specific monetary contribution across tracts.
- `results/TRACT_HAZARD_CONCENTRATION.csv`: hazard concentration diagnostics and effective hazard count for each tract.
- `results/SAME_TRACT_SOURCE_VALUES.csv`: exact original source matrix (Git LFS).
- GitHub Actions workflow under `.github/workflows/stage7-nri-eal-overlap-20261009.yml`.

The original manuscript branch and scientific Stage 7 outputs remain untouched.
