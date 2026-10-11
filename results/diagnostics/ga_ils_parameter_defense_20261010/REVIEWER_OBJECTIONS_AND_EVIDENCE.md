# Reviewer Objections and Evidence

## 1. Why a permutation GA?

The decision is a valid priority order decoded by the unchanged nonlinear scheduler. GA is a practical finite-budget order-search method, not a global proof. Reasonable ILS comparators were actually tested.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 2. How are orders valid?

Each chromosome contains each of the 92 pinned IDs once. Swap/insertion/inversion and OX/PMX/cycle preserve the domain; property tests and every retained final sequence identity are verified.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 3. Why ordered crossover?

OX preserves the copied segment and cyclic donor order without duplicate stations. Existing PMX/cycle pilots use an inversion background; they do not establish universal final-swap superiority.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 4. Why swap mutation?

Same-initialization operator evidence supports swap under tested settings. Legacy-to-final changes also alter mutation probability and must not be attributed solely to swap.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 5. Why probabilities .80/.10?

Fresh 20-seed 100k .60/.80/.95 crossover and .05/.10/.20 swap comparisons justify tested operating choices. Intervals overlap zero for close alternatives; no exact optimum/equivalence claim is warranted.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 6. Why population 100?

A reproducible middle reference; equal-query 50/250/500 differences are small/unresolved and initializer composition changes. Legacy P500 failure is not intrinsic P500 inferiority.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 7. Why tournament 3?

Tournament-2 adds about .026100 h, simultaneous [.014669, .037531]. k5 short-screen benefit is not conclusively reproduced at 100k/500k. Histories quantify actual intensity/diversity rather than assuming it.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 8. Why one elite?

Archive protects output; elite protects a breeding chromosome. New fixed-configuration 0/1/2/3 confirmation isolates this intervention; see the full three-contrast table, without claiming one is uniquely optimal.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 9. Why mixed initialization?

Seven references, one exact older prior, 13 prior/12 Impact inversion neighbors, and 67 random permutations. It combines declared inherited quality and search breadth. Copy removal alone retains prior information in neighbors.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 10. How much gain is inherited?

Prior gain 0.540170816732 h; additional selected gain 0.040290969385 h. About 93.06% already existed in the prior, with per-seed generation-zero improvements reported separately.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 11. Why the budget/stopping?

Distinct full-64 scores represent expensive work; duplicates, attempts and time are also reported. Twenty 100k runs plus five continuations to 500k total 4 million evaluations across 20 independent seeds. Plateau is not global convergence; fixed budgets were not validation-tuned.

Evidence: GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.

## 12. Were parameters developed on planning states?

Yes. All tuning and new exploratory comparisons use the same 64 development realizations. Conditional optimizer-seed intervals are not untouched physical validation.

Evidence: GA_ILS_METHOD_CHOICE_DECISION.md; EXECUTION_ACCOUNTING.json; IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json; REPRODUCIBILITY.md.

## 13. How was stochastic variability controlled?

Paired optimizer seeds; screen/confirmation disjoint; bootstrap seed blocks and simultaneous families; failures/incomplete controls retained. No chromosome or checkpoint pseudoreplication.

Evidence: GA_ILS_METHOD_CHOICE_DECISION.md; EXECUTION_ACCOUNTING.json; IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json; REPRODUCIBILITY.md.

## 14. Is the best chromosome lucky?

It is selected from a prespecified multi-seed search, so optimism is possible. Report the distribution and independent frozen-sequence result, not selected minimum as unbiased optimizer performance.

Evidence: GA_ILS_METHOD_CHOICE_DECISION.md; EXECUTION_ACCOUNTING.json; IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json; REPRODUCIBILITY.md.

## 15. Is GA demonstrably superior?

Not universally. Mixed ILS is competitive at 100k/500k; a reduced single-swap ILS receives a fresh controlled audit. Weak SA/LNS settings cannot prove superiority over all alternatives.

Evidence: GA_ILS_METHOD_CHOICE_DECISION.md; EXECUTION_ACCOUNTING.json; IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json; REPRODUCIBILITY.md.

## 16. What does independent validation establish?

Performance of already frozen sequences under the specified sample design; not exact hyperparameter optimum, new postvalidation calibration, capacity, or robustness in every physical state.

Evidence: GA_ILS_METHOD_CHOICE_DECISION.md; EXECUTION_ACCOUNTING.json; IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json; REPRODUCIBILITY.md.

## 17. Can it be reproduced?

Pinned model/input/source hashes, seed configurations, exact 92-station permutations, actual budgets/costs, RNG/initializer fingerprints, archive records, code/tests and downloaded LFS verification. Runtime-dependent wall time is not bitwise reproducible.

Evidence: GA_ILS_METHOD_CHOICE_DECISION.md; EXECUTION_ACCOUNTING.json; IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json; REPRODUCIBILITY.md.
