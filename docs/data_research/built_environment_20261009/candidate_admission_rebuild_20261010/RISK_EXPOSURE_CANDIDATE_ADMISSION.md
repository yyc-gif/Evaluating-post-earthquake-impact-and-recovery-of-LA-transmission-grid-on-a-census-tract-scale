# Risk/exposure candidate admission

All fields come from the SAME archived NRI v1.19 Mar-23 California table and exact2315/2291 GEOIDs. BUILDVALUE and SOVI reproduce prior saved values. Scores remain published0-100 percentile scales; standardization below is only for VIF, not a new clustering model.

| Construct | Candidate representation | Meaning and limitation |
| --- | --- | --- |
| Asset scale | BUILDVALUE; raw or log1p | Building monetary stock; not building form and not expected loss. |
| Exposure-bearing expected losses | EAL_SCORE OR EAL_VALT/log1p(EAL_VALT) | Multi-hazard annual building+population-equivalent+agriculture loss; rank versus monetary level, never independent duplicate coordinates. |
| Exposure-normalized loss propensity | ALR_NPCTL | Official unadjusted composite rate percentile; not pure hazard and not totalEAL/BUILDVALUE. |
| Consequence-specific rate | ALR_VALB or ALR_VALP | Building or population component only; cannot represent all consequences. |

EAL_h = exposure_h * annual_frequency_h * historic_loss_ratio_h, summed over applicable hazards. EAL_VALT=EAL_VALB+EAL_VALPE+EAL_VALA; EAL_VALPE=11,600,000 * EAL_VALP in this dollar framework. ALR_VALB=EAL_VALB/BUILDVALUE, ALR_VALP=EAL_VALP/POPULATION, ALR_VALA=EAL_VALA/AGRIVALUE where each denominator is positive. ALR_NPCTL combines national component rate percentiles with EAL weighting per v1.19 methodology. It is not the percentile of an invented total-loss/building-value ratio. The source combines all relevant hazards even where earthquake contributions dominate regionally.

RISK_SCORE ranks EAL multiplied by a community factor using social vulnerability/resilience; ALR_VRA_NPCTL is also community-adjusted. With mandatory independent SOVI, RISK is descriptive and ALR_VRA is rejected for proposed primary coordinates. Agricultural zero exposure is undefined, not a manufactured0 rate. Low marginal correlation does not prove socioeconomic independence.

## Actual diagnostic evidence

BUILDVALUE–EAL_SCORE: N=2291, Pearson=0.585312, Spearman=0.858475.
BUILDVALUE–ALR_NPCTL: N=2291, Pearson=0.233407, Spearman=0.234890.
SOVI–EAL_SCORE: N=2291, Pearson=-0.044018, Spearman=-0.068479.
Full pairwise raw/log monetary comparisons, component values/rates, same-sample VIF and partial-control diagnostics are supplied. VIF does not establish causal or construct equivalence.

## Candidate designs for author decision (no weights assigned)

1. Separate stock and propensity: log1p(BUILDVALUE)+ALR_NPCTL. Preferred when both amount of assets and exposure-normalized multi-hazard loss propensity are research coordinates. This is a construct reason; D has no automatic admission privilege.
2. Propensity only: ALR_NPCTL. Removes explicit asset scale; appropriate only if economic stock is intentionally not a separate coordinate. Not an equivalent smaller version of design1.
3. Combined expected-loss/exposure: EAL_SCORE, alternatively log1p(EAL_VALT). Integrates expected annual consequences and asset/population/agriculture exposure; omits a separately identifiable asset-stock coordinate. Do not combine the score and value as two constructs.
4. Building-only or population-only rate alternatives are conditional consequence-specific sensitivity, not an all-hazard all-consequence replacement without changing the declared construct.

SOVI and Init_Supply remain mandatory. No domain20% weighting, no five-domain acceptance, no new hazard variable or new composite score is adopted.
