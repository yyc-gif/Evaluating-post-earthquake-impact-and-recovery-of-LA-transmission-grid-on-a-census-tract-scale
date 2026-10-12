# Route A: social vulnerability and population exposure

Status: candidate evidence only; no formal Stage 7 replacement, regrouping or clustering. Statistics below use the same 2291 residential GEOIDs unless a source comparison explicitly says otherwise.

## Composite source identity and harmonization

Use **FEMA NRI v1.19 March 2023 `SOVI_SCORE`**, not NRI total risk or an older HVRI SoVI release. All 2,315 source rows match exact eleven-digit GEOIDs and `NRI_VER=Mar-23`; all values match the frozen candidate source and score helper (helper decimal tolerance 1e-5). The authoritative existing [harmonization decision](../../methodology/STAGE7_SVI_HARMONIZATION_DECISION.md) and [source review](../../reviewer/SOCIAL_VULNERABILITY_MEASURE_REVIEW.md) document CDC/ATSDR **SVI 2020** lineage and a **national percentile-based 0-100 scale**. These are source vintages, not earthquake dates. FEMA v1.19 documentation: [provider version record](https://www.fema.gov/sites/default/files/documents/fema_national-risk-index-data-version-and-update-documentation.pdf). The score is relative social vulnerability, not a probability of outage or absolute welfare loss.

CDC 2022 California official `RPL_THEMES` is a **state-relative 0-1 overall percentile**, using ACS 2018-2022. It is distinct from the historical local arithmetic mean of `RPL_THEME1` through `RPL_THEME4`. Ranking and combining underlying variables and then ranking an overall score is not equivalent to averaging four percentile themes. [Official CDC 2022 documentation](https://www.atsdr.cdc.gov/place-health/media/pdfs/2024/10/SVI2022Documentation.pdf). The local mean is reproduced solely to audit the discrepancy; neither it nor four separate theme coordinates is recommended for Route A.

`SVI_COMPOSITE_SOURCE_COMPARISON.csv` independently reproduces the earlier harmonization associations and membership comparisons. SOVI versus CDC official overall: Pearson 0.9468, Spearman 0.9480; versus local theme mean: 0.9255 and 0.9292. Similarity is high, but ranking is not identical. Median absolute percentile-rank displacement is 0.0543 and 0.0633, respectively; P95 is 0.1880 and 0.2217.

On the 2,291 common valid source rows, replacing the **actual frozen** Q4 by newly cut CDC overall Q4 gives overlap 466, entrants 106, departures 111, Jaccard 0.6823. Replacing it by the local mean gives overlap 450, entrants 122, departures 127, Jaccard 0.6438. These are diagnostic comparisons, NOT applied group changes. All original full-domain groups (Q1=579, Q2=580, Q3=577, Q4=579) and the Vulnerability-first strategy remain unchanged. Freshly cutting even FEMA quartiles does not exactly reproduce the frozen original membership; do not silently recut it.

## Population exposure, not another vulnerability index

`Population` is copied from `Data/Tracts_Within_Expanded_Area.csv` and agrees with formal evaluation metadata and prior frozen candidate population on **2,315/2,315** rows. The harmonization record describes it as 2020-based; a direct upstream Census release/batch record was not recovered in this audit. Exact computational provenance is clean; that remaining external-vintage documentation must be resolved by the authors, not guessed. No CDC 2022 population, canopy-layer population or NRI population replaced the frozen values. NRI `POPULATION` is not interchangeable (only 7/2,315 exact matches in an exploratory check).

Propose `log1p(Population)` for scale compression of exposed people. Total population measures exposed magnitude; density measures spatial concentration and has an area denominator; population-weighted aggregate loss is a downstream weighted summary; `Population * B` is person-hours constructed from existing exposure and duration. The latter is not a new independent coordinate. Do not retain raw Population and its log transform together.

Residential Pearson correlation of log population with SOVI is 0.2010. Controlling the other six proposed coordinates gives linear R-squared 0.0655, VIF 1.0701 and additive-spline cross-validated R-squared 0.0639. Exposure magnitude is not mechanically duplicated by the vulnerability score. Population density remains a descriptive diagnostic, with a separate CDC denominator/vintage. No outcome-correlated variable selection is performed.

## Possible third coordinate: electricity heating

The prior independently sourced [living-environment audit](../built_environment_20261009/living_environment_audit_20261011/) supplies ACS B25040 electricity-as-principal-heating-fuel share, ACS **2018-2022 five-year**, 2020 tract support. This is occupied housing units, not residents or all buildings. Source: [official Census 80-replicate B25040 archive](https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/B25040_06.csv.zip). Estimates and MOEs were validated there against official source cells; that diagnostic package is separately pinned to commit f321517.

All 2,291 residential records are valid. With SOVI, log population, log density and 5+ housing-unit share as controls, heating has linear R-squared 0.4092, VIF 1.6927, and additive-spline CV R-squared 0.4209. Thus it is **not simply a statistical duplicate**. Its Pearson association with 5+ housing share is 0.6314. Housing-unit composition overlaps the composite's housing-related components; statistical residual variation alone does not establish a new community-dependence construct.

Uncertainty is material: median share MOE90=0.0848; P90=0.1173; **569/2291 (24.84%)** exceed 0.10 (ten percentage points). The prior MOE uses correlated numerator/denominator 80-replicate ratio variance, including documented Census boundary fallback, not independent MOE division. These are survey estimates, not observed post-event household electricity needs.

Recommendation: **CONDITIONAL** for a specifically declared residential-heating interruption sensitivity experiment, not a third primary Route A coordinate. Temperature, alternative fuels, backup supply, cooling and medically necessary loads are absent. Completeness does not cure limited construct scope or large uncertainty. No reasonably complete verified tract-level medical electricity-dependence measure was found. Hospital location is not resident dependence; age/disability shares are already component-related to SVI; stock value or general built environment is not interruption loss. Keep RQ3 at **two coordinates** rather than manufacture a weak third.

## Original comment record

An original local `CommentsLAGrid.docx` was inspected read-only; SHA256 `36fa7ec2b99c3058952de9f21d9024187a52d8fdb1f6482cd82db125851aba05`; location and exact quote are in `ORIGINAL_COMMENT_SOURCE_RECORD.json`. The relevant readable comment is:

>         20)You do not need to explain K means in this paper, that is unnecessary, just use a reference. It is not very clearly stated in page 20 which are the variables for the k-means and what is the objective of doing k-mans.

This asks for clear K-means variables and purpose. No explicit recommendation to average the four SVI theme percentiles was located in readable main-document text, and no comments XML was present. The record is the locally supplied reviewer file; author metadata does not independently authenticate attribution. **Do not attribute an SVI aggregation recommendation to Marta from this evidence.** Embedded-image-only content, if any, is not evidence of a new recommendation. No comment document is republished here.

Q4 mean burden, Q4-Q1 gap, Gini and Hospital-linked mean burden remain downstream strategy-evaluation metrics, not tract clustering coordinates.
