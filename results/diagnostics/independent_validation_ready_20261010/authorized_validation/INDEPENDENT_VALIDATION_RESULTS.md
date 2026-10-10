# Fixed Independent Validation Results

Status: **INDEPENDENT_VALIDATION_COMPLETED**. Diagnostic publication only; no formal strategy replacement.

## Frozen Execution

Execution commit: `c178bff7f924257b33f1e8c17e0d5e59a1fe68e9`. Freeze SHA-256: `45d157c0a3b9460d7c29e389b649afef0f0e6bc568bfba8eb773f9b5b974ae15`.
Author confirmation and unchanged supplied authorization are archived alongside this report.
Exactly 2,000 new physical pairs and 26,000 policy-realization records; 13 frozen conditions.
Original 92 stations, 318 edges, 14 sources, 57 C57_D1 crews, 2,315-tract M1 mapping, directed travel,
DS>0 task queue, repair-duration laws and 0.5 source gate remain unchanged.
One independent PCG64 SeedSequence([202610091,3,2,r]) per r=0..1999. Each physical pair was shared across all conditions.
No overlap with the old 64 planning/1,000 inspected pairs, no within-cohort duplicate, no redraw or sample-count extension.

## Prespecified Primary Comparison

Population-weighted normalized modeled service deficit integrated over 0-480 hours.
Effect is Frozen GA minus Impact-first; negative favors GA. Hours are equivalent normalized service-loss hours,
not a change in station repair duration, outage duration for every customer, delivered MW or calendar recovery time.

- Impact-first mean: 33.522649523125 h.
- Frozen GA mean: 33.020747887680 h.
- Paired mean difference: -0.501901635445 h (-30.114098127 min).
- Monte Carlo SE: 0.011604801347 h.
- Fixed 95% paired percentile-bootstrap interval: [-0.524975128718, -0.479472230142] h.
- Relative mean difference versus Impact-first: -1.497201571%.
- Improved/worsened/tied states: 1810/190/0.

The prespecified interval supports lower mean modeled burden for Frozen GA than Impact-first.
This is independent Monte Carlo generalization evidence conditional on the unchanged physical and service model,
not an empirical test against actual utility restoration. Statistical evidence does not establish a large practical benefit.

The original 20,000 whole-realization resamples, seed 2026100901 and common resample bank were retained.
All 2,000 observations enter the analysis. No intermediate effect inspection, tuning, selection or optional stopping occurred.

## All Frozen Conditions

Rows retain the frozen manifest order and are not a newly selected ranking.

| Condition | Mean burden (h) | MCSE (h) | 95% pointwise interval (h) | Restricted mean T80 (h) | Censored / 2,000 |
|---|---:|---:|---|---:|---:|
| impact-first | 33.522649523 | 0.057207193 | [33.411733164, 33.634913460] | 45.248108536 | 0 |
| hospital-first | 34.224993918 | 0.057186058 | [34.114494902, 34.337451809] | 45.883167182 | 0 |
| degree-first | 35.627253678 | 0.058762505 | [35.515014635, 35.740820270] | 49.636448303 | 0 |
| betweenness-first | 35.470856100 | 0.058988614 | [35.357473776, 35.585700183] | 47.870860932 | 0 |
| random | 39.405895865 | 0.064795616 | [39.281192165, 39.533515119] | 52.926443705 | 0 |
| vulnerability-first | 34.192875393 | 0.057103626 | [34.083022006, 34.304691231] | 46.488672922 | 0 |
| ga-exploratory-01 | 33.072854155 | 0.055137479 | [32.967300865, 33.181425764] | 45.086691530 | 0 |
| ga-exploratory-02 | 33.047880982 | 0.055166672 | [32.942333076, 33.156357783] | 45.053578748 | 0 |
| ga-final-method-candidate | 33.020747888 | 0.054829710 | [32.915519154, 33.128068096] | 45.059622299 | 0 |
| centrality-first | 36.064589403 | 0.060117859 | [35.949397877, 36.181304355] | 48.381612672 | 0 |
| closeness-first | 35.493697534 | 0.058696529 | [35.381058231, 35.608718073] | 49.588977139 | 0 |
| refined-ils-secondary-diagnostic | 32.996198796 | 0.054293208 | [32.892294591, 33.102894521] | 45.126947028 | 0 |
| unconstrained | 31.294745912 | 0.052676840 | [31.193794568, 31.397669509] | 43.476160285 | 0 |

Policy-level intervals and every comparison other than the single prespecified primary are descriptive pointwise intervals.
They are not multiplicity-adjusted evidence that a newly highest-ranked strategy should be promoted.
Unconstrained removes travel/crew competition but retains the same physical durations and gate; it is not a feasible dispatch policy.

## Refined ILS Secondary Diagnostic

ILS minus Frozen GA: -0.024549091909 h; MCSE 0.007338083738 h;
95% descriptive interval [-0.039332393533, -0.010473325774] h.
Improved/worsened/tied: 608/1392/0.
The earlier planning objective favored the refined ILS by about 0.001703408495 h, with 14/64 improved states and a realization-15 ranking reversal.
This fresh result is evaluated without replacing the formal GA candidate or choosing a new sequence from this cohort.
PAIRED_DIFFERENCE_DISTRIBUTIONS.csv reports distribution quantiles for both predeclared comparisons.

## Equity And Hospital Endpoints

The following Frozen-GA-minus-Impact-first effects are prespecified secondary descriptions, not additional confirmatory tests.

| Endpoint | Mean difference | MCSE | 95% pointwise interval |
|---|---:|---:|---|
| burden_Q1_hr | -0.442223303540 | 0.014266506951 | [-0.470303347545, -0.414279453549] |
| burden_Q4_hr | -0.656640349523 | 0.012973323009 | [-0.682560661530, -0.631494594152] |
| signed_Q4_minus_Q1_hr | -0.214417045984 | 0.010155263786 | [-0.234263047376, -0.194512937407] |
| absolute_Q4_minus_Q1_hr | 0.158232892912 | 0.010262779036 | [0.138352384318, 0.178127943814] |
| burden_gini | 0.008311508732 | 0.000204320410 | [0.007921456044, 0.008717886048] |
| hospital_mean_normalized_burden_hr | -0.283895943586 | 0.011943620282 | [-0.307756413197, -0.260680610973] |
| T80_restricted_hr | -0.188486236263 | 0.029051047593 | [-0.246315719697, -0.132365143207] |
| T80_censored | 0.000000000000 | 0.000000000000 | [0.000000000000, 0.000000000000] |

Gini is dimensionless and computed per realization before averaging. The signed Q4-Q1 gap is not the absolute gap;
absolute differences are also computed per realization before averaging. Hospital burden uses equal-tract weighting among hospital-linked tracts.
T80 means are restricted to 480 h with unreached observations retained as censored; the reached-only conditional mean is separately labeled in T80_CENSORING.csv.
T80_censored contrasts are probability-point differences, not hours. Figure disparity is Q4-Q1 availability, not cumulative burden.

## Exact Loss Accounting

L_total = L_self + L_threshold + L_source. Entries below are mean normalized population-weighted integrals in hours.

| Condition | Self | Threshold | Source connectivity | Total |
|---|---:|---:|---:|---:|
| impact-first | 28.456563791 | 0.933484657 | 4.132601075 | 33.522649523 |
| ga-final-method-candidate | 28.660326188 | 0.941304230 | 3.419117470 | 33.020747888 |
| refined-ils-secondary-diagnostic | 28.713026346 | 0.943198713 | 3.339973736 | 32.996198796 |
| unconstrained | 26.854496659 | 0.875679221 | 3.564570032 | 31.294745912 |

These are accounting components, not causal station-level counterfactuals. Shared physical states do not imply identical self-loss
because dispatch arrival/completion times can differ. No station movement is assigned a causal benefit here.

## Verification And Reproduction

POST_COMPLETION_QA.json verifies all 2,000 draw payloads, checkpoint files, shared-policy identities, saved gate algebra,
exact-event station integrals, population-weighted tract loss, primary/secondary means and the complete fixed bootstrap export.
Protected revision HEAD, branch, staged binary diff and 950 protected-file hashes match the pre-run baseline.
No original samples, strategies, source gate, evaluator, scientific figures, manuscript or Stage 7 labels were replaced.

Full per-state evidence is retained locally and published losslessly as FIXED_2000_FULL_ARCHIVE.zip with FULL_ARCHIVE_MANIFEST.json.
Extract the capsule to a new diagnostic directory to inspect original draw RNG pre/post states, loss trajectories and dispatch records.
Publication may advance the diagnostic branch only; the launcher intentionally demands the original c178bff checkout for execution.

```powershell
$env:PYTHONPATH='src'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMBA_NUM_THREADS='1'
& C:\Users\yinch\anaconda3\python.exe -B results/diagnostics/independent_validation_ready_20261010/authorized_validation/audit_completed_validation.py audit
& C:\Users\yinch\anaconda3\python.exe -B results/diagnostics/independent_validation_ready_20261010/authorized_validation/audit_completed_validation.py package
```

These commands audit/package existing evidence. They do not authorize generating another cohort.

## Decision

The fixed independent-validation batch is complete. Preserve its prespecified primary interpretation and report secondary findings with their limits.
Do not tune, select a replacement chromosome, extend this cohort, promote a strategy, or automatically update manuscript/formal figures from these results.
Any scientific or editorial promotion remains a separate author decision.
