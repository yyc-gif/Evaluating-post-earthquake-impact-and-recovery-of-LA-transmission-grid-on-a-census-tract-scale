# Reviewer Response Evidence Matrix

## R1 #3
- **Reviewer concern:** How damage and repair-duration uncertainty enter tasks, schedules, and comparisons.
- **Revised implementation:** `D302_2PC50_DAMAGE_PROBABILITIES.csv`; `REALIZATION_STRATEGY_SUMMARY.csv`.
- **New evidence:** 32 DS/duration vectors were each drawn once and reused across four strategies. Within every realization, damage hash, duration hash, task count, and DS counts match; mean task count was `300.47`.
- **Manuscript action:** Replace mean-duration task selection with DS>0 event tasks and report paired differences, distributions, and paired bootstrap intervals.

## R1 #5
- **Reviewer concern:** SVI-weighted T80 is not equity.
- **Revised implementation:** `TRACT_BURDEN_BY_REALIZATION.csv`; `DISTRIBUTIONAL_EFFECTS.csv`.
- **New evidence:** Fixed NRI-SOVI quartiles, signed and absolute Q4-Q1 gaps, and burden Gini replace SVI-weighted T80. GA-Efficiency minimized absolute gap in `87.5%` of realizations but raised population burden by `15.08 h`.
- **Manuscript action:** Delete equity wording from T80; report bounded distributional disparity without causal equity claims.

## R1 #6
- **Reviewer concern:** GA reproducibility, operators, stopping, multi-seed convergence, and coefficient provenance.
- **Revised implementation:** `GA_REPRODUCIBILITY_REPORT.md`; `GA_CONVERGENCE_BY_SEED.csv`; `GA_CANONICAL_SEQUENCES.csv`.
- **New evidence:** 30 runs use population 100, 100 generations, OX 0.8, inversion 0.2, tournament size 3, seeds 42–51, fixed stopping, and an exact same-seed repeat. Each policy produced 10 distinct final sequences.
- **Manuscript action:** Publish configuration and fitness spread; label weights as policy-design assumptions and sequences as finite-budget benchmarks.

## R1 #7
- **Reviewer concern:** Hospital-first versus GA-HospFirst and fitness versus reported metrics.
- **Revised implementation:** `GA_REPRODUCIBILITY_REPORT.md`; `REALIZATION_STRATEGY_SUMMARY.csv`.
- **New evidence:** Hospital-first scored `0.916320` versus `0.900608` for canonical GA-HospFirst under the identical surrogate and had lower mean population T80 (`62.00` vs `85.06 h`), hospital burden, population burden, makespan, and travel.
- **Manuscript action:** Delete the objective-mismatch-only story. Report finite-budget search limitation and the distinct surrogate/reporting metrics.

## R2 #4
- **Reviewer concern:** Findings were obvious.
- **Revised implementation:** `PAIRWISE_STRATEGY_EFFECTS.csv`; `DISTRIBUTIONAL_EFFECTS.csv`.
- **New evidence:** GA-Balanced cut makespan by `2.97 h` but raised population burden by `7.08 h`; GA-Efficiency reduced disparity/Gini while worsening burden for `80.1%` of population.
- **Manuscript action:** Center the findings on conflicts among total burden, disparity, and logistics.

## R2 #9
- **Reviewer concern:** Why GA and whether it can be trusted.
- **Revised implementation:** `GA_REPRODUCIBILITY_REPORT.md`; `GA_CONVERGENCE_BY_SEED.csv`.
- **New evidence:** GA is transparent and seed-reproducible, but distinct seed solutions, late improvement, and the GA-HospFirst shortfall bound its interpretation.
- **Manuscript action:** Present GA as a stochastic comparator, not a black box, methodological contribution, or verified optimum.

## R2 #12
- **Reviewer concern:** Insufficiently novel findings.
- **Revised implementation:** `REVISED_PAIRED_PILOT_REPORT.md`; `PAIRWISE_STRATEGY_EFFECTS.csv`.
- **New evidence:** Shorter makespan or lower inequality can coincide with higher total burden and delays for most residents, a conflict hidden by system T80.
- **Manuscript action:** Replace generic rankings with quantified redistribution, logistics, and uncertainty tradeoffs.

## R2 #13
- **Reviewer concern:** Logistics/resource constraints unclear.
- **Revised implementation:** `REALIZATION_STRATEGY_SUMMARY.csv`.
- **New evidence:** Every run uses C57 pooled crews, directed travel, completion-based release, and stores task count, makespan, travel, and on-site work; paired on-site work isolates order/travel effects.
- **Manuscript action:** Describe C57 as a scenario resource budget and publish event-dispatch semantics.

## R2 #14
- **Reviewer concern:** Who benefits, who is delayed, and at what cost.
- **Revised implementation:** `PAIRWISE_STRATEGY_EFFECTS.csv`; `DISTRIBUTIONAL_EFFECTS.csv`; `REALIZATION_STRATEGY_SUMMARY.csv`.
- **New evidence:** GA-Balanced improved 179 tracts / `22.3%` of population but worsened 574 / `69.6%`, while reducing makespan. GA-HospFirst and GA-Efficiency worsened `67.5%` and `80.1%` of population.
- **Manuscript action:** Add a winners/losers section with SOVI-quartile effects and paired logistics costs.

## R2 #16
- **Reviewer concern:** Reframe results around redistribution of recovery burden.
- **Revised implementation:** `TRACT_BURDEN_BY_REALIZATION.csv`; `REVISED_PAIRED_PILOT_REPORT.md`.
- **New evidence:** Resolved-mass-normalized burden is stored for 817 tracts × 32 realizations × 4 strategies; 12 fully unresolved tracts remain NA and Class C is never treated as failure.
- **Manuscript action:** Reorganize Results and Conclusion around tract burden redistribution and metric-specific tradeoffs.
