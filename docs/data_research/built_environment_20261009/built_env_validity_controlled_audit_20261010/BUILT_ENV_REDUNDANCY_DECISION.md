# Built-environment redundancy and scientific-validity decision

## Recommendation

Retain the three coordinates in the **historically qualified, descriptive joint candidate**: classified-parcel land-use mix, observed ground-building coverage, and the pre-1970 share of valid-age 2014 building area. Do not call these a comprehensive, synchronized or independently validated representation of the contemporary built environment. This recommendation does not authorize changing formal labels, the manuscript or existing figures.

| Coordinate | Scientific decision | Required interpretation |
|---|---|---|
| SCAG entropy | KEEP as a primary coordinate | Land-use mixture within classified parcel land, not entire tract land |
| LARIAC6 footprint coverage | KEEP as a primary coordinate | Ground-building coverage of the mixed-vintage outline inventory, not floor-area density |
| LARIAC4 2014 observed-age share | KEEP as a primary coordinate, with explicit historical scope | Observed valid-age building stock of the 2014 inventory, not complete 2020/2022 stock, structural fragility or current building condition |
| ACS residential age | DESCRIPTION/SENSITIVITY ONLY | Housing-unit-weighted residential estimate for 2018-2022; it cannot replace all-use area age without changing the research construct |
| Building-count density | DESCRIPTION ONLY in this decision | Segmentation/centroid-based count intensity; it measures something different from footprint coverage |
| Impervious fraction | NOT ADMITTED as primary | The existing pilot's direct USGS source/version correspondence is still unverified |

The minimum defensible **two-coordinate** physical alternative is entropy + footprint (BE1), if the author decides that historical building age should be outside the primary research construct. It preserves mix and physical coverage but loses age composition. The evidence does not establish that this is scientifically superior: its higher median spatial ARI accompanies a worse lower tail and a small-group matching failure in one prescribed deletion. Do not choose it solely for dimensional parsimony, silhouette or average stability. No contemporaneous all-use replacement with comparable coverage is currently validated.

## Controlled design and actual calculations

The parent is `5f49471ac707c001baefa1fa860aa77971dd62c5`. All comparisons use the same 2,287 complete residential GEOIDs, retained in original order, from a 2,291-row master. Four unresolved geometry records remain unclassified and unimputed. B in original hours, Init_Supply, four grid descriptors and SOVI remain identical. Fixed k=4, seeds42-61, n_init=100, max_iter=500, tol=1e-4, Lloyd, scikit-learn1.5.1. No k search, simulations, scheduler, GA, GIS extraction or formal-file replacement was performed.

There are29 distinct model specifications, each20 complete-cohort baselines and20 spatial cases:880 new fits and280 existing runs reused after matrix/sample/hash/settings checks. BE0 and EAL equal-domain spatial results are reused byte-for-byte. Full D/EAL, ACS/no-age and available inherited-bound/allocation labels are reused. Proportional missing-land allocation is a mathematical identity, with only floating-point serialization differences; its two entries are aliases, not additional independent runs. Checkpoint archives retain actual IDs, raw labels, scalers, factors, train masks, and new fitted centers. Reused full-cohort centers are explicitly **label-member means**, because the original algorithm centers were not saved; no baseline is refitted to invent those centers.

Spatial cases reuse the existing20-km blocks and exact20 seed/deletion pairs, comprising17 distinct geographic deletion sets. Each training subset fits its own scaler and predicts the whole common cohort. Spatial ARI compares with that model's same-seed full-cohort baseline. Class matching uses training overlap only, then applies that mapping to all/heldout records. Raw contingency tables are retained so a one-to-one assignment cannot conceal merging. Full feature comparisons provide both frozen BE0-seed42 and same-seed BE0 references. The tables below use **same-seed BE0** for both ARI and reassignment, and each model's own baseline for spatial ARI. Empirical ranges/percentiles are not confidence intervals or classification accuracy.

## Statistical overlap and source interpretation

Current three-feature maximum VIF is 1.118765. The actual pilot and current-cohort correlations are:

| scope                        | feature                     | other_feature                  |    n |     value |
|:-----------------------------|:----------------------------|:-------------------------------|-----:|----------:|
| current_2287                 | land_use_entropy            | building_footprint_coverage    | 2287 | -0.117030 |
| current_2287                 | land_use_entropy            | all_use2014_pre1970_area_share | 2287 | -0.310203 |
| current_2287                 | building_footprint_coverage | all_use2014_pre1970_area_share | 2287 |  0.056523 |
| legacy_2276_current_values   | land_use_entropy            | building_footprint_coverage    | 2276 | -0.118313 |
| legacy_2276_current_values   | land_use_entropy            | all_use2014_pre1970_area_share | 2276 | -0.309553 |
| legacy_2276_current_values   | building_footprint_coverage | all_use2014_pre1970_area_share | 2276 |  0.057242 |
| original_pilot_actual_values | land_use_entropy            | building_footprint_coverage    | 2276 | -0.118313 |
| original_pilot_actual_values | land_use_entropy            | all_use2014_pre1970_area_share | 2276 | -0.309553 |
| original_pilot_actual_values | building_footprint_coverage | all_use2014_pre1970_area_share | 2276 |  0.057242 |

The pilot2276 rows are reproduced from their original saved values. The current legacy2276 subset uses the subsequently validated data version; the current2287 adds11 resolved geometry records and keeps the four unresolved records excluded. The small correlation differences are therefore membership/version differences, not an unreported new variable. VIF does not establish scientific independence or correct sources. Conditional relationships, coverage-stratified correlations and spatial-fivefold polynomial diagnostics are in BUILT_ENV_REDUNDANCY_METRICS.csv. Mild nonlinear overlap exists: age can predict entropy with out-of-block R2 up to 0.128; this remains incomplete overlap, not zero dependence or causal evidence. Predicting age from footprint reaches R2 0.052. No independent-tract p-values are used to certify validity.

SCAG classified-land coverage median is 75.107% on2287. Entropy is normalized over11 exclusive classified categories. Assigning all unknown land to transport or the observed dominant category is a hypothetical stress test, not recovered land use; proportional assignment preserves proportions. LARIAC6 is a2020 release of cumulative outlines, predominantly older imagery, not a synchronized2020 survey. Geometry measures roof/ground projection, not floor area, structural type or occupancy.

2014 valid-age coverage median is 95.251% **of original2014 outlines**, versus 4.342% for strict2020 age transfer on the same cohort. Government missing-age area fraction in the saved by-use audit is95.804%; cross-use unions overlap and must not be summed into a county denominator. The lower/upper bounds cover missing ages of2014 outlines, not demolitions/new construction or unobserved later changes. Retaining the historical variable is a construct judgment with these limits, not proof that high conditional coverage validates contemporary age. A more recent residential-only measure is not a general all-use substitute.

## Ablation, weighting and measurement uncertainty

| model                |   ARI_BE0_same_seed_median |   reassigned_median |   spatial_ARI_median |   spatial_ARI_min |   D34_spatial_purity_min |
|:---------------------|---------------------------:|--------------------:|---------------------:|------------------:|-------------------------:|
| BE0                  |                     1.0000 |              0.0000 |               0.9234 |            0.7522 |                   0.3696 |
| BE1_EQUAL            |                     0.8445 |            121.0000 |               0.9352 |            0.6571 |                   0.0000 |
| BE1_FIXED_COORD      |                     0.8966 |             78.5000 |               0.8630 |            0.6910 |                   0.3696 |
| BE2_EQUAL            |                     0.8236 |            139.0000 |               0.9674 |            0.8628 |                   0.3656 |
| BE3_EQUAL            |                     0.5548 |            405.0000 |               0.8875 |            0.6372 |                   0.3696 |
| BE4_EQUAL            |                     0.6892 |            256.0000 |               0.9682 |            0.9039 |                   0.3656 |
| BE5_EQUAL            |                     0.3561 |            696.0000 |               0.8680 |            0.6666 |                   0.3696 |
| BE6_EQUAL            |                     0.3888 |            787.0000 |               0.9260 |            0.4869 |                   0.0028 |
| BE7_ACS_EQUAL        |                     0.9148 |             64.0000 |               0.8951 |            0.6956 |                   0.3696 |
| BE8_LOWER_EQUAL      |                     0.9313 |             52.0000 |               0.9473 |            0.7050 |                   0.3696 |
| BE8_UPPER_EQUAL      |                     0.9853 |             11.0000 |               0.9297 |            0.7401 |                   0.3696 |
| SCAG_TRANSPORT_EQUAL |                     0.9251 |             57.0000 |               0.9166 |            0.7328 |                   0.3696 |
| SCAG_DOMINANT_EQUAL  |                     0.9322 |             51.0000 |               0.9481 |            0.6874 |                   0.3696 |

Deleting age with physical budget fixed at20% changes a median 121 tracts; retaining original per-coordinate weights changes 78.5. Deletion and amplification of the remaining coordinates both matter. The fixed-coordinate experiment keeps each retained physical coordinate at0.2/3, leaves all other domains untouched, and reduces the total squared weight; it is not silently renormalized. PHYSICAL_REDISTRIBUTION_EFFECTS.csv directly compares the same surviving coordinates under the two budgets, rather than attributing their combined effect solely to removed information.

ACS substitution changes a median 64 tracts and is a change in population/denominator/vintage. Age lower/upper scenarios change 52/11 tracts. Equal-domain transport/dominant missing-land scenarios change 57/51. These tests close the earlier **equal-domain SCAG evidence gap**, while showing residual lower-tail geographic sensitivity. They do not fill missing land or certify a fully observed entropy field.

The original34-member set is audited by membership, not a hard-coded class ID. Under BE0 deletion seed54, only4 target training members remain; all34 original members are in a92-member predicted class, retention100% but purity36.96%. EAL has90 members and37.78% purity. Some age-deleted/inherited specifications do not retain a distinct one-to-one-matched minority class under the same cases. A zero matching purity is a merging/matching failure, not proof that the original tracts vanished; destinations are retained in SMALL_34_GROUP_SENSITIVITY.csv and raw cross-tabs. Median ARI cannot hide this failure. Original-unit profiles, deletion-only shifts, reclassification shifts, common-BE0-coordinate center shifts and ranking reversals are supplied. Small differences and changes involving sparse support must not become stable archetype names or built-environment causation.

The recovery/SOVI profile audit explicitly tests class ordering across the six equal-domain no-age/ACS/age-bound/SCAG scenarios and all20 seeds. Among C3's pairwise B/SOVI contrasts, there are 0 reversals over 720 tested comparisons. The full-cohort seed42 no-age comparison shifts C1 service loss32.424 to32.875h and C4 from33.893 to33.486h, while C3 changes36.339 to36.244h and mean SOVI31.058 to30.852. Thus those particular full-cohort changes largely modify high-SOVI subgroup separation rather than remove the lower-SOVI/higher-loss C3 contrast. This narrow observation does not validate geographic prediction, all single-coordinate ablations, inherited weights, or stable archetype names. CORE_PROFILE_INTERPRETATION_AUDIT.csv retains all pairwise directions, including any reversals in finer contrasts.

## Risk/exposure content versus domain weights

On2287, Pearson r(log1p building stock, ALR)=0.2473; r(log1p stock,EAL)=0.8314. After controlling for SOVI and log population density, the former is 0.3240, and the latter 0.8595. Stock and ALR are related but not interchangeable; EAL has much greater stock overlap. ALR is the published unadjusted, EAL-weighted multi-hazard loss-rate percentile, not a simple EAL/BUILDVALUE ratio, pure seismic hazard or socially adjusted risk. EAL combines loss and exposure and omits separately interpretable economic stock. Keep SOVI independent in all specifications.

| model              |   ARI_BE0_same_seed_median |   reassigned_median |   spatial_ARI_median |   spatial_ARI_min |
|:-------------------|---------------------------:|--------------------:|---------------------:|------------------:|
| BE0                |                     1.0000 |              0.0000 |               0.9234 |            0.7522 |
| D_INHERITED        |                     0.2123 |           1053.0000 |               0.3405 |            0.1881 |
| ALR_ONLY_EQUAL     |                     0.5493 |            413.0000 |               0.8886 |            0.7792 |
| EAL_EQUAL          |                     0.6286 |            319.0000 |               0.9458 |            0.8666 |
| ALR_ONLY_INHERITED |                     0.2330 |            867.0000 |               0.9240 |            0.4106 |
| EAL_INHERITED      |                     0.2614 |            782.5000 |               0.8487 |            0.3295 |

D remains the recommended scientific definition when **economic stock and loss propensity** are both intended domains. ALR-only intentionally omits economic stock and doubles the surviving rate coordinate within the fixed exposure/loss budget. EAL changes that domain into combined expected loss/exposure. Thus ALR-only is not merely a harmless redundancy deletion, and its partition effect cannot be attributed to stock removal alone. Neither alternate is rejected for a lower ARI; they answer different scientific questions. Source-exposure overlap and locally earthquake-dominated multi-hazard loss also preclude claims of statistical/physical independence.

Pure weight changes with identical features are:

|                                                      |   ARI_median |   ARI_min |   reassigned_median |
|:-----------------------------------------------------|-------------:|----------:|--------------------:|
| ('ALR_ONLY_EQUAL', 'ALR_ONLY_INHERITED')             |       0.4598 |    0.4545 |            573.5000 |
| ('BE0', 'D_INHERITED')                               |       0.2123 |    0.2033 |           1053.0000 |
| ('BE1_EQUAL', 'BE1_INHERITED')                       |       0.3718 |    0.3689 |            675.0000 |
| ('BE7_ACS_EQUAL', 'BE7_ACS_INHERITED')               |       0.3003 |    0.2926 |            756.0000 |
| ('BE8_LOWER_EQUAL', 'BE8_LOWER_INHERITED')           |       0.3597 |    0.3553 |            680.5000 |
| ('BE8_UPPER_EQUAL', 'BE8_UPPER_INHERITED')           |       0.2099 |    0.1994 |           1072.0000 |
| ('EAL_EQUAL', 'EAL_INHERITED')                       |       0.4312 |    0.4222 |            587.5000 |
| ('SCAG_DOMINANT_EQUAL', 'SCAG_DOMINANT_INHERITED')   |       0.2152 |    0.2036 |           1041.5000 |
| ('SCAG_TRANSPORT_EQUAL', 'SCAG_TRANSPORT_INHERITED') |       0.2157 |    0.2048 |           1047.5000 |

Within each weight scheme, content-only comparisons are separately supplied in WITHIN_WEIGHT_SPECIFICATION_EFFECTS.csv and WITHIN_WEIGHT_PROFILE_CHANGES.csv. This prevents inherited SCAG/age/risk comparisons against equal-domain BE0 from conflating content and parent-budget effects. At fixedk4, inherited D spatial median/minimum ARI 0.3405/0.1881 differ sharply from equal D. Earlier selected-k5 inherited stability does not validate this fixedk4 model. Equal-five-domain weights are an explicit conceptual balance, not an empirically discovered optimum; the effect of weights is a major substantive limitation.

## Distance contributions and remaining decisions

|                                                |   squared_weight |   between_class_fraction |   variance_explained |
|:-----------------------------------------------|-----------------:|-------------------------:|---------------------:|
| ('grid', 'Grid_Betweenness')                   |           0.0500 |                   0.0027 |               0.0185 |
| ('grid', 'Grid_Degree')                        |           0.0500 |                   0.0044 |               0.0305 |
| ('grid', 'Grid_Impact')                        |           0.0500 |                   0.0094 |               0.0647 |
| ('grid', 'Redundancy_HHI')                     |           0.0500 |                   0.0002 |               0.0014 |
| ('loss_exposure', 'ALR_NPCTL')                 |           0.1000 |                   0.1143 |               0.3918 |
| ('loss_exposure', 'log1p_NRI_BUILDVALUE')      |           0.1000 |                   0.0865 |               0.2965 |
| ('physical', 'all_use2014_pre1970_area_share') |           0.0667 |                   0.0247 |               0.1271 |
| ('physical', 'building_footprint_coverage')    |           0.0667 |                   0.0114 |               0.0588 |
| ('physical', 'land_use_entropy')               |           0.0667 |                   0.0695 |               0.3576 |
| ('recovery_service', 'B_480_hr')               |           0.1000 |                   0.0446 |               0.1530 |
| ('recovery_service', 'Init_Supply')            |           0.1000 |                   0.2249 |               0.7714 |
| ('social', 'SOVI_SCORE')                       |           0.2000 |                   0.4073 |               0.6984 |

Between-class fractions are contributions to separation of the partition fitted using these same coordinates, not independent validation or causal importance. Low pairwise r, a nonzero fraction, optimizer stability and similarity to BE0 are insufficient selection rules.

1. **Entropy and footprint:** yes, different constructs and low linear/conditional overlap; nonlinear/coverage diagnostics do not collapse them into one indicator.
2. **Age:** a meaningful separate historical-stock coordinate, sufficiently observed for a qualified descriptive role; not independently validated current all-use age. Its temporal and nonrandom missingness limitations must stay explicit.
3. **Two variables:** the smallest reasonable alternative is entropy+footprint, but it is not established as preferable. Removing age sacrifices historical composition and does not resolve the geographic minority-group weakness.
4. **Physical20% after deletion:** defensible only as an author-declared conceptual-domain convention. It raises surviving-coordinate weights from6.67% to10%; it requires scientific approval if adopted, not automatic implementation.
5. **Established versus judgment:** exact coverage, overlap, changed memberships and finite-case spatial results are measured. Whether historical age belongs in the intended construct and whether all five parent domains deserve20% are scientific design judgments. This audit recommends retaining all three with historical scope, D for separately interpretable stock/rate, and keeping equal-domain weighting explicit; it does not freeze a new primary model.

Do not call this a comprehensive built-environment classification, universal geographic taxonomy, predictive validation, causal explanation of recovery, or proof of optimal features/weights. Formal science, formal labels, manuscripts and figures remain untouched.
