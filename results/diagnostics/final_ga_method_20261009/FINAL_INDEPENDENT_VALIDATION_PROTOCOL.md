# Independent final validation protocol â€” proposed

**No new physical samples are authorized or generated.** Approve the pinned method, budget, selection rule, sequence and statistical plan together before filling a new validation archive. FREEZE_RECEIPT.json pins protocol/config/sequence/comparator hashes before any physical draw; author approval is still required.

## Physical samples and scope

Fixed N=**2,000 2pc50/C57_D1 realizations**, with no optional extension. Use `numpy.default_rng(SeedSequence([202610091,3,2,r]))`, r0..1999, and the pinned software/ordered 92 IDs. Original master42 and split0/1 are not reused. Invoke the existing `sample_damage_states` and `damage_to_functionality_and_repair` functions with unchanged 2pc50 PGA/fragility and duration parameters. Draw DS0-DS4 and strictly positive durations once per realization; DS0 duration0. Share the same samples across all policies. Do not introduce new correlations or physical assumptions. Record canonical DS/duration hashes and source identities; compare to all original 64/1000 hashes. Any exact overlap aborts for review rather than silent redraw. Use a separate archive namespace.

This is Monte Carlo validation conditional on the same earthquake/network/service model, not empirical validation against observed outage records or a cross-hazard assessment.

## Fixed comparisons and endpoint definitions

Selected GA sequence: `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`. Primary reference **Impact-first**; secondary fixed comparators Hospital-first, Degree-first, Betweenness-first, Vulnerability-first, Random, Unconstrained and both prior exploratory GA sequences. Exact comparator sequences and hashes are pinned in VALIDATION_COMPARATOR_SEQUENCES.json before sampling. Random is the saved fixed ordering, not a new ordering per realization. Unconstrained uses the same DS/durations without crew competition. Ten policy conditions in total.

Primary endpoint: population-weighted cumulative modeled service loss over **0-480 h**, with unchanged production mapping, station/service gate and normalization. Estimand: mean within-realization candidate-minus-Impact-first difference; negative favors candidate. Audit kernel population-dependency-mass and tract-normalized endpoint agreement without changing either denominator. Production mapping row-mass minimum/maximum=0.999999999999999/1.000000000000000; maximum deviation from 1=5.55e-16. No weights were renormalized.

Secondary: Q1-Q4 service loss, signed Q4-Q1, realization-level |Q4-Q1| then average (not absolute difference of mean outcomes), population-weighted Gini, equal-tract mean hospital-linked service loss, population T80, self/threshold/source-path components, f/F/C/e trajectories, and task execution/travel/completion. Quartile assignments and hospital flags are fixed. These are consequences of aggregate optimization, not a new multi-objective fitness. Hospital-linked loss does not measure electricity delivery or clinical capacity.

Do not extend the 480-h endpoint when a new realization finishes later. Report unreached-T80 counts and conditional T80 summaries with denominators; do not silently omit censored rows or assign a favorable recovery time. Population T80 and mean tract T80 are distinct. Missing outcomes trigger explicit reporting rather than imputation.

## Uncertainty and decision rule

Retain identical realization IDs across policies. Report mean/median differences and empirical 5th-95th realization ranges. Obtain **20,000-resample 95% percentile bootstrap CIs for mean differences**, seed 2026100901, by resampling whole realizations jointly across policies/metrics in memory-bounded batches. Do not resample tracts independently. Also report primary Monte Carlo SE. Only the GA/Impact-first contrast is primary. Secondary CIs are pointwise descriptive and are not adjusted confirmatory multiple comparisons.

No validation-based chromosome tie-break, hyperparameter selection, metric/subgroup selection or optional stopping. If performance fails to transfer, report that result. Any later tuning creates a new algorithm and requires a new assessment plan; this cohort cannot remain an untouched test after that tuning.

## Sample size and estimated compute

N = 2000 is a bounded precision choice, not assumed power for an unknown true effect. The inspected exploratory difference SD=0.540046 h implies an approximate 95% mean-CI half-width **0.023669 h** if variance transfers. This planning estimate is not a validation finding.

Timing six already inspected saved samples generated no new physical data. Warm pipeline median 0.004131 s per candidate-realization suggests approximately **82.6 serial seconds** for 20,000 policy-realizations. That extrapolation excludes new physical generation, file writing, bootstrap and setup; the first timed call includes cold compilation/setup effects. Reserve **10-30 minutes** as an unmeasured engineering allowance, then measure authorized setup/I/O before a full run. Subsecond CPU measurements are quantized and do not justify precise CPU projections. Existing archive sizes imply about **1.07 GiB**, reserving at least **3.20 GiB** for temporary files and verification. Check free disk before author-approved execution. Physical sampling was not benchmarked or performed.

## Existing evidence and approval gate

The 64 repeatedly optimized planning samples and previously inspected 1000 evaluation samples are not untouched final validation. Existing favorable exploratory results retain that qualification. The algorithm is ready to report transparently and to enter final validation; independent performance confirmation and formal strategy promotion remain pending author authorization. No validation run has started and original formal files remain unchanged.
