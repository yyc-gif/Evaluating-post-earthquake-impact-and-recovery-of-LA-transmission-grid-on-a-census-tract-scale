# Continuing GA method investigation — prespecified tests and decision boundaries

Source base: commit `13f8ef8e5d244c70a92a06a45540460c736c70f9`, original 92-station, 64-sample 2pc50/C57_D1 planning objective. This *does not authorize* generating independent physical-validation realizations, replacing a formal sequence, or changing the model, mapping, scheduler, gate or scientific figures.

## Why the previous stopping recommendation was premature

1. Earlier GA variants could fail to improve Impact-first because the chromosome archive contained a good incumbent while evolutionary populations could discard its lineage. Correctly scoring and returning the archive is not proof evolutionary search contributed.
2. The 7/1/25/67 initialization percentages are a recipe, not a general GA rule. The full heuristic archive can remain even when heuristic chromosomes are removed; neighbor removal is not the same as removal of the inherited quality source.
3. Changing population size while fixing seven heuristics and one quality copy but seeding floor(P/4) neighbors changes several percentages simultaneously. One-factor population comparisons are conditional package effects, not clean population-only identification.
4. A plateau on 64 planning samples can reflect scheduler-induced equivalence or overfitting. Searches need tests against other optimizers and out-of-training checks; more search evaluations do not add physical samples.
5. Current best-vs-relaxation gap near 4.96% is **not** a tight global optimality certificate.

## Phase A: factor interactions and provenance, already coded and launched

Source: `src/la_grid/diagnostics/ga_factorial_research_20261009.py`.

- Full 2x2x2x2: population 50/100, tournament 3/5, swap mutation 0.10/0.20, inversion-neighbor count zero / floor(P/4). Maintain ordered crossover 0.80 and one elite. Twelve new GA seeds 200..211, 20,000 distinct expensive scores for each configuration.
- Three controls additionally hold the final operators fixed: seven heuristic chromosomes but no inherited best; Impact-first only incumbent archive; fixed Random incumbent only archive and otherwise random initial population. **No-prior controls remove previous GA best from both initialization and best-so-far archive**. The second retains Impact-first; the third retains neither Impact-first nor previous optimized sequence as injected reference.
- Record full final chromosomes and hashes, per-seed objective, initial and final quality, evolutionary gain, attempts, generations and checkpoints.
- The factorial is a bounded interaction screen; full-budget replication of promising contrasts remains necessary before performance claims. Single lowest run cannot determine the method.

## Phase B: GA versus non-GA permutation search, already coded and launched

Source: `src/la_grid/diagnostics/ga_alternative_optimizer_20261009.py`.

- Twenty new, common pseudorandom seeds 300..319, three algorithms per seed: final GA (P100/OX0.80/swap0.10/tournament3/elite1), iterated local search (random swap/insertion/inversion proposals with fixed perturbations after stagnation), and simulated annealing (fixed operator mixture; temperatures calibrated from 128 initial neighbor probes counted within budget).
- Every method begins with the same seven reference evaluations and inherited prior-best sequence. All expensive objective calls are counted against **100,000 distinct evaluations per method**, no shared cross-method free fitness cache. Methods do not have identical random-number streams simply because seeds match.
- Preserve attempted evaluations and elapsed wall, learning curve at 20k/50k/100k, best identity and all final permutations. Do not claim superiority over all possible local search or annealing configurations: these are prespecified practical benchmarks.
- Historical deterministic steepest-neighborhood local refinement from inherited best (`local_search/previous_best/RUN.json`, J=32.998626840923 h after 464,141 distinct scores) is an additional context comparator. Historical runs are **not** a matched-hardware cost comparison.

## Inferential reporting

- Equal distinct-evaluation budgets, complete seed-paired differences for every case. Bootstrap resample whole GA seeds, report mean/median/SD and finite-seed empirical win frequency.
- Report factorial interaction contrasts, not just separate main effects. No universal claims from seeds or one planning scenario; ensure each search reached its budget. All additional designs/data postdate many earlier optimization choices and are descriptive unless an explicit familywise testing plan is adopted.
- Report original Impact-first baseline separately. For a no-prior GA, assess probability of *failing to beat Impact-first* and the percentage attaining various gaps to warm-start algorithms.
- If local or annealed searches beat GA, report the result, examine mechanism and allocate a new stage for stronger matched-budget comparisons rather than insisting on GA. If no material differences are identifiable, report uncertainty and continue with a distinct algorithmic approach, not only a larger generation count.
- Do not use the proposed 2,000-realization independent physical cohort or the already inspected 1,000 cohort for selecting GA parameters or chromosomes.

## Explicit remaining work rather than premature stop

1. If factorial interactions appear, replicate chosen contrasts at 100k and 500k with adequately sized *fresh* seed sets; precommit the confirmatory selection rule and cost.
2. Benchmark high-quality deterministic best-improvement local search and stronger variable-neighborhood / iterated search, especially from the same warm start and with a matched computational budget.
3. Test ranking stability with predeclared internal 64-sample cross-fitting. Those 64 samples have been used during development: this is **diagnostic**, not independent physical validation.
4. Quantify ability to generalize before formal promotion; define any scientific negligibility/equivalence threshold from physical meaning *before* looking at a future comparison.
5. Keep best-observed objective and chronology updated if a better candidate is found, but do not silently replace the frozen sequence or report one lucky lowest score as an expected method advantage.
6. Preserve full sequences, reproducible algorithm-source hashes and workload cost. Reuse completed cloud artifacts rather than rerunning them to recover missing chromosomes.

No blanket claim that reviewers cannot object, that hyperparameters are optimal, or that global optimality was reached. Research continues until evidence addresses *algorithmic improvement, initialization attribution, sample overfitting and comparator performance*, or an explicit documented limitation remains after bounded analysis.
