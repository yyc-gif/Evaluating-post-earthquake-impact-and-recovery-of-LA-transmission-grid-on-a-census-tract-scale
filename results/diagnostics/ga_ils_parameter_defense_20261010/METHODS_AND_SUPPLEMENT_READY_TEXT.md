# Methods and Supplement Ready Text

## Main Methods: Frozen Algorithm

We represented recovery priority as a permutation of 92 substations and evaluated each order using the fixed realization-specific crew scheduler, directed travel and source-connected service model. Fitness was the negative mean population-weighted service-loss integral over 64 planning realizations. Genetic search used 100 chromosomes, reciprocal ordered crossover with probability 0.80 per parent pair, two-position swap mutation with probability 0.10 per child, tournament selection of size 3 and one surviving parent elite. Each tournament sampled with replacement; exact ties retained the first draw. The best distinct parent, with lexicographic tie-breaking, replaced the final offspring after reproduction. Passive best-so-far retention was separate from generational elite survival.

Initial populations comprised seven retained heuristic orders, one previously optimized order, 25 single-inversion neighbors (13 from that prior and 12 from Impact-first), and 67 random permutations. This starting information was disclosed rather than treated as an improvement newly discovered by genetic search. Relative to Impact-first, the prior supplied 0.540171 h of the total 0.580462 h selected planning gain; subsequent optimization supplied 0.040291 h. Search used 20 seeds at 100,000 distinct order evaluations, with five fixed seeds continued to 500,000. Repeated cached lookups were excluded from the expensive-query budget but included in attempted calls and time. The selected minimum is a development result, not an estimate of universal optimizer superiority or global optimality.

## Main Methods: Diagnostic Alternative

An iterated local-search comparator used the same planning objective and declared prior information. It selected swap, insertion or inversion proposals uniformly and accepted strict improvements (1e-12 numerical tolerance). After 800 attempted non-improving proposals, including cache hits, it perturbed the retained best by cyclic 2/4/8 primitive moves. The final perturbed sequence alone was scored; the current sequence could worsen while the best remained retained. Deterministic multi-neighborhood refinement, when reported, was a separate additional-budget stage. Equal distinct-query comparisons retained attempted work and wall time. Neither optimizer family was assumed universally superior.

## Supplement: Parameter Evidence and Postvalidation Audit

Earlier paired-seed studies tested population packages, crossover/mutation probabilities, tournament pressure, operator alternatives, initialization ablations and parameter interactions. Population comparisons changed initializer composition and were not interpreted as pure population effects. Small unresolved differences justified a reproducible reference, not exact optimality or equivalence. Weak tournament-2 selection deteriorated by approximately 0.026100 service-loss h relative to tournament-3, whereas close 3/5 comparisons remained budget- and setting-dependent.

After frozen-sequence independent validation, a separate prospectively registered diagnostic audit executed 128 engineering cases and 320 targeted confirmation cases using eight screening and twenty fresh confirmation seeds. It directly tested elite counts 0/1/2/3, individual versus mixed ILS neighborhoods, stagnation, perturbation, restart reference and warm/cold prior access. Incomplete no-perturbation cases were retained as neighborhood-accessibility diagnostics, not equal-budget optimizer replications. All new algorithmic conclusions are postvalidation development findings and were not tested on the old validation cohort.

| contrast                  |   mean_delta_hr |   simultaneous95_low_hr |   simultaneous95_high_hr |   wins |   losses |   ties |
|:--------------------------|----------------:|------------------------:|-------------------------:|-------:|---------:|-------:|
| ga_elite0 minus ga_elite1 |        0.000137 |               -0.001495 |                 0.001768 |     10 |        9 |      1 |
| ga_elite2 minus ga_elite1 |        0.000135 |               -0.001107 |                 0.001376 |     10 |       10 |      0 |
| ga_elite3 minus ga_elite1 |        0.000153 |               -0.000958 |                 0.001265 |      8 |       12 |      0 |
| ils_mix minus ga_elite1   |       -0.000039 |               -0.001853 |                 0.001775 |      9 |       11 |      0 |
| ils_cold minus ga_cold    |       -0.001069 |               -0.003039 |                 0.000900 |     11 |        9 |      0 |
| ils_mix minus ils_cold    |        0.000078 |               -0.001726 |                 0.001881 |      9 |       11 |      0 |
| ga_elite1 minus ga_cold   |       -0.000953 |               -0.002664 |                 0.000759 |     12 |        8 |      0 |

Five preselected independent ILS seeds received deterministic refinement and corresponding equal-total-distinct-budget GA continuation. A final exhaustive tested-neighborhood scan certifies only local non-improvement under its specified neighborhoods and tolerance. Per-state production parity, leave-one-out influence and cost accounting were retained. Optimizer-seed confidence intervals are conditional on fixed physical planning states; checkpoints, chromosome evaluations and overlapping seed phases are not independent replications. No new physical realizations were generated.

## Claims Not Authorized by This Evidence

Do not describe exact parameters as optimal, the total gain as independently discovered by GA, ILS as automatically simpler, the selected planning minimum as unbiased expected performance, or postvalidation candidates as independently validated. Do not promote a new policy, alter formal outputs, or use an influential-sample finding to redefine the original mean objective. This text is a separate review resource, not an in-place manuscript edit.
