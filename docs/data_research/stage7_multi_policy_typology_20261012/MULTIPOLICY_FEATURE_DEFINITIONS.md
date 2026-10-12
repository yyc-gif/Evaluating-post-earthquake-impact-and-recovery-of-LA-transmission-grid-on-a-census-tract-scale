# Multi-policy definitions and registered design

AUTHOR REVIEW — NOT FORMAL STAGE 7


## Frozen condition and cohort
2pc50; C57_D1 (57 crews, restoration-duration multiplier 1); M1_UTILITY_003; G1_BASELINE_050 (functionality threshold 0.5 with retained Core source connectivity); horizon 480 h; 1,000 matched evaluation realizations. The clustering cohort is all 2,299 positive frozen population tracts, including eight with zero conventional housing units. Only 16 zero-population GEOIDs are excluded here; they remain in all existing 2,315-tract system outputs. No geometry exclusions or imputation. Population and frozen FEMA NRI v1.19 SOVI quartiles are unchanged.

2pc50 denotes 2% ground-motion exceedance probability in 50 years, approximately 2,475-year mean return period. It is not one earthquake rupture, ASCE 41 BSE-2E, a community risk score, or a station damage-state probability. The source identity and bounded vintage caveats remain those verified in the preceding hazard audit.

## Recovery quantities
For tract i, physical realization m and policy p: B_i,p,m = integral_0^480 [1 - S_i,p,m(t)] dt. Availability is the existing normalized source-gated tract service proxy, not power flow. Integrals use the archived exact piecewise-constant event convention. B_i,p = mean_m B_i,p,m; B_i,U = mean_m B_i,U,m; Delta_i,p = mean_m(B_i,p,m - B_i,U,m). Thus B_i,p = B_i,U + Delta_i,p. Units are equivalent full-service-deficit hours, not a unitless fraction divided by 480.

Main ensemble: Impact-first, Hospital-first, Degree-first, Betweenness-first, Vulnerability-first. MeanDelta_i = sum_p Delta_i,p / 5. PolicySD_i = sqrt(sum_p(Delta_i,p - MeanDelta_i)^2 / 5), ddof=0. Equal weights describe this finite registered design; they are not policy-adoption probabilities. Direct-community is excluded as an exact frozen duplicate of Impact-first. Random is a separate sixth-policy sensitivity; Unconstrained is never an ensemble member.

PolicySD equals SD_p(B_i,p) algebraically because the same B_i,U is subtracted from every policy. It measures variation among realization-mean policy burdens, not earthquake uncertainty, error, causal effects or a confidence interval. The separately saved mean_m SD_p(B_i,p,m) is a different diagnostic estimand. Cohort averages are 2.3458 h and 2.6888 h respectively; their mean gap is 0.3430 h. The independently checked Jensen inequality holds, but the quantities are not interchangeable.

## Fitted coordinates and distance budgets
A: Init_Supply, spectral Grid_Impact, dependency HHI; Impact-first B and Delta; FEMA SOVI_SCORE and log1p frozen Population. P2 replaces only RQ2 with B_Unconstrained and MeanDelta. P3 uses B_Unconstrained, MeanDelta and PolicySD. Grid_Impact is the frozen tract-weighted spectral-connectivity importance measure, not the population-impact dispatch score. HHI = sum_j W_ij^2 for normalized tract dependency weights.

All observations have equal fitting weights. Each RQ receives one-third of squared-distance budget. RQ1 coordinates each 1/9; RQ3 coordinates each 1/6. A/P2 RQ2 each 1/6; P3 RQ2 each 1/9. Z scores use cohort population SD (ddof=0); apply square roots of budgets. P2-to-P3 changes coordinate inclusion AND RQ2 allocation. Minus-Init diagnostics preserve RQ1 total, allocating 1/6 to each remaining coordinate. Exact identities are not fitted as separate inputs: MeanTotalBurden = B_Unconstrained + MeanDelta; Impact B = B_Unconstrained + Impact Delta; AUC = 1 - B/480.

Five leave-one-out sets and main5+Random are seven unique sets including main5. Omitting Vulnerability is one of the five LOO cases, not an eighth independent comparison. Raw changes are retained before scaling. Main fits standardize separately by set; seed42 K2-8 fixed-main5-scaling fits isolate rescaling effects. Training-only scaling is used for geographic refits.

K1 inertia and K2-8 full-cohort silhouettes; seeds42-46, k-means++, n_init50, Lloyd, max_iter500, tol1e-4. Endpoint-chord bend is a finite-range diagnostic, not an optimized physical K. Saved A labels are reused after exact matrix and silhouette verification. P2/P3 minus-Init is restricted to main5 K1 and K3-5. All individual fits/labels and four-quadrant spatial predictions are retained. Diagnostic IDs are model-specific and ordered by mean burden, then population; ARI is invariant; Hungarian matching is for transitions only.
