# Frozen population and building-asset source QA

**AUTHOR REVIEW - NOT FORMAL STAGE 7.** Baseline commit: `ef40eba552a2b33eea364d23a8695d3d96edb326`. Actual Git LFS source bytes, not pointer text, are checked in `SOURCE_HASH_VERIFICATION.csv` and the independent source record.

## Population authority

`Data/Tracts_Within_Expanded_Area.csv::population` matches the formal metadata and prior audit on all 2,315 exact GEOIDs. It is the only population used for eligibility and `log1p(Population)`. The existing harmonization report calls it 2020-based, but its direct upstream Census release/batch remains **unresolved**. Frozen numerical identity is verified; external vintage is not newly authenticated. NRI/Hazus population and CDC 2022 population are not substituted. Density remains the existing CDC 2022 `E_TOTPOP / AREA_SQMI` (persons/square mile), a different denominator/vintage and descriptive only.

## Exact BUILDVALUE identity and units

`Data/NRI_Table_CensusTracts_California.csv::BUILDVALUE`, NRI v1.19, March 2023 (`NRI_VER=Mar-23`, 9,106 archived California rows), exactly joins every study GEOID. It is **total building exposure stock in 2022 USD**, using **Hazus 6.0 2022 valuations on 2020 Census support**. The archived version-specific FEMA Technical Documentation, printed p.5-9 (PDF index68), states this lineage; [official FEMA document retained by Ohio EMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf). The verified local PDF and page text are used because a current web fetch rejected the 23MB PDF. Current v1.20 documentation was not substituted.

This field is not electricity-interruption damage, actual power demand, household income, earthquake damage or another social-vulnerability measure. A larger stock can occur in special-use or employment tracts and can coexist with high SOVI. It is not evidence that residents are wealthy. All NRI values are retained exactly; the frozen SOVI representation differs from full NRI decimals by at most 4.82e-09, explicitly tolerated below 1e-8 without changing scores or quartiles.

## Distribution and coverage, positive-population cohort

BUILDVALUE valid=2299, missing=0, zero=0. Minimum=$7,243,309; P10=$240,868,785; P25=$324,946,262; median=$463,027,239; P75=$692,709,280; P90=$1,036,165,605; maximum=$9,419,166,254. Mean=$590,411,184; population SD=$513,388,905; skewness=6.666. Full original and transformed distributions are in `FEATURE_ORIGINAL_UNIT_DISTRIBUTIONS.csv`.

`log1p(BUILDVALUE)` is ln(1 + stock measured in USD), then cohort-standardized, not a locally re-ranked NRI percentile. The highest 23 stocks account for about 6.58% of assets but 1.09% of frozen population. `HIGH_ASSET_TRACT_REGISTER.csv` preserves exact locations/types; two largest are 06037980016 and 06037980035, each above $9 billion. Their SOVI scores are about 73.21 and 83.21: high stock does not imply low vulnerability. Tract-specific land-use identities are not inferred from monetary values alone.

The eight added records span $7,243,309 to $3,190,633,584; zero housing units are not zero economic stock. `BUILDVALUE_SPATIAL_CONCENTRATION.csv` reports the same official-point quadrants, not an unverified neighborhood aggregation.

## Incremental information, not automatic admission

| predictor         |   pearson |   spearman |   linear_R2 |   spline_random_tract_CV_R2 |
|:------------------|----------:|-----------:|------------:|----------------------------:|
| Init_Supply       |   -0.0293 |    -0.0358 |      0.0009 |                      0.0071 |
| Grid_Impact       |    0.0582 |     0.0828 |      0.0034 |                      0.0032 |
| Redundancy_HHI    |    0.0858 |     0.0811 |      0.0074 |                      0.0046 |
| B_480_hr          |    0.0710 |     0.0659 |      0.0050 |                      0.0080 |
| Delta_B_logistics |    0.0761 |     0.0195 |      0.0058 |                      0.0027 |
| SOVI_SCORE        |   -0.3160 |    -0.3506 |      0.0999 |                      0.0910 |
| log1p_Population  |    0.3602 |     0.4372 |      0.1297 |                      0.1747 |
| Population        |    0.4314 |     0.4372 |      0.1861 |                      0.1801 |
| Pop_Density       |   -0.4320 |    -0.5667 |      0.1866 |                      0.2808 |
| EAL_SCORE         |    0.8358 |     0.8596 |      0.6986 |                      0.7662 |
| EAL_VALT          |    0.6830 |     0.8596 |      0.4664 |                      0.7055 |
| ALR_NPCTL         |    0.2329 |     0.2336 |      0.0542 |                      0.1031 |

Conditioning on all seven A coordinates, log stock has linear R2=0.2804, VIF=1.3896, additive-spline five-fold random-tract CV R2=0.3177. Thus the added coordinate is not a mechanical duplicate. Nonlinear diagnostics and MI are descriptive; neither establishes causality or spatially independent prediction.

EAL_SCORE, EAL_VALT and ALR_NPCTL appear only in construct diagnostics. EAL mixes hazard, stock and annual modeled consequences; ALR is a distinct normalized loss-propensity construct. The strong stock/EAL association does not turn stock into a power-interruption loss estimate. None of these, nor RISK_SCORE, enters any registered primary fit. No geographic or economic loss validation is claimed.
