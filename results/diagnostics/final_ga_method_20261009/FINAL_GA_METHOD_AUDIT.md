# Final GA method audit

Base `73ef343f21e998eb9c9ccf7797d1aa0119d15c04`. **Scientifically ready for transparent method reporting and independent final validation; further open-ended algorithm development is not required for this candidate.** Independent validation and author approval of formal promotion remain pending. Existing formal policies are unchanged.

## Chromosome, scheduler and direct objective

Each chromosome contains each fixed station ID once: all 92! permutations are permitted. For each of 64 saved 2pc50 planning samples, remove DS0 tasks without reranking. The exact scheduler dispatches the next damaged station to the earliest-free crew (lowest crew index on an exact clock tie), adds directed travel and its saved repair duration, and restores the station at completion. C57 origins, travel, graph, gate, mapping and repair distributions are unchanged.

Let W_ti be fixed tract dependency, P_t population and m_i=sum_t P_t W_ti. Raw functionality is f_ri(t), F_ri(t)=1[f_ri(t)>=0.5], and C_ri(t) is connectivity through eligible stations to any 14 Core source. The objective is

$$m_i=\sum_t P_t W_{ti},\qquad J(\pi)=\frac{1}{64}\sum_{r=1}^{64}\frac{\sum_i m_i\int_0^{480}[1-f_{ri}(t;\pi)F_{ri}(t;\pi)C_{ri}(t;\pi)]\,dt}{\sum_i m_i}.$$

The algorithm maximizes fitness=-J using event-exact left rectangles. The unmodified kernel uses H_plan=2855.254013110100 h. PLANNING_HORIZON_AUDIT establishes an order-independent completion upper bound 134.332550166 h and a Core source in each intact component, so its post 480 loss is zero for these fixed inputs. Its scores therefore equal the 480-h endpoint. This is a proved equivalence for these inputs, not a silently altered horizon; do not assume it for future samples. Station masses and their encoded sum are retained without new mapping normalization.

## Exact initial population

Seven fixed rules, in saved dictionary order: **centrality-first, impact-first, betweenness-first, degree-first, closeness-first, hospital-first, random**. Append one prior-best sequence; append 25 independently drawn inversion neighbors (j0..24:13 even-j neighbors of prior best,12 odd-j neighbors of Impact-first); fill the remaining 67 slots with uniform full permutations. Each inversion reverses the inclusive segment between two distinct uniform positions. Initialization is 7+1+25+67=100 slots; duplicates are allowed and occupy slots. The 25 neighbors are not uniformly random chromosomes. The complete seed 42 example population is saved in INITIAL_POPULATION_SEED42.json.

Prior-best chromosome: `3bfeafdd1adf950749e63fdbbe3b7efc21b1efd04c3b3d64c28c3d118717bbed` from `results/diagnostics/extended_ga_20261008/p100_g2000_s46/RUN.json`, seed 46, population 100, generation 2000, J=33.038131743267 h. That discovery run records 81,187 distinct candidates and 138.831 s. These are one run's costs, not the complete earlier development cost. The source and sequence are fixed; newly found candidates do not replace this initialization source.

## Operators and RNG

Use Python `random.Random(seed)` and the pinned runtime/source hashes. Incumbents consume no RNG draws; inversion neighbors precede random permutations. At each generation draw 100 parents. Each tournament samples 3 indices **with replacement**; choose highest fitness and keep the first sampled index on an exact tie. Pair consecutive parents. One Bernoulli 0.80 ordered-crossover draw per pair; sample two distinct cuts, include both endpoints, inherit that segment and fill remaining positions in the other parent's cyclic order starting after the segment. Produce reciprocal children. Independently draw Bernoulli 0.10 mutation per child and, when triggered, swap two distinct uniformly sampled positions. Initialization still uses inversion, despite evolutionary swap mutation. Adaptive mutation, restarts, crowding, alternate crossover and mixed operators are disabled.

After generating 100 children, sort the parent population by descending fitness then lexicographically ascending tuple on ties; copy its one best distinct chromosome into the last child slot. RNG draws for that overwritten child still occurred. This one-elite survival changes the evolving population and is distinct from archive preservation.

The archive starts with the best of seven deterministic incumbents; incumbent ties use rule name then sequence. A completed-generation candidate uses max(fitness,lexicographically largest tuple), and the archive updates only on strictly better fitness. The separate best-observed record updates at every first expensive query only on strict improvement, retaining the earliest encountered exact tie. If budget ends mid-generation, report best-observed and separately retain the completed-generation archive. Do not discard an evaluated improvement or claim the partial generation completed.

## Caching, stopping, restarts and selection

The cache key is 92 unsigned-byte indices in the original pinned station-ID order. Cache is private to each seed and initially empty; no cross-seed scores are free. First scoring consumes one expensive query; duplicates consume attempts but no new query. Seven initial incumbent scores count against the budget; rescoring them in the initial population hits cache. No tolerance-based equivalence collapses different chromosomes.

Stop exactly at the distinct-query limit, potentially within a generation, or at the attempt safety limit50 times the total budget. The attempt cap is checked after completed generations, so it is a boundary safeguard and can overshoot by generation bookkeeping. Safety-cap runs are incomplete and cannot be reported as full budget. There is no fixed-generation or stagnation stop. Actual generations and all budget/attempt counters are saved; all reported runs reached their designated budget.

Stage A: seeds 42-61,100k distinct queries each. Stage B: **fixed seeds 42-46**, continued to 500k total each with unchanged RNG/state/cache. No evaluation or best-seed ranking chooses the extension. A deterministic500k replay from scratch reproduces the prefix, but costs another 100k prefix and must be charged as extra actual work. Existing prefix checks establish identity. Future fresh execution should retain checkpoints to avoid replay overhead.

Select the minimum exact planning loss over evaluated Stage A/Stage B chromosomes from this recommended configuration only. Across exact run ties: smallest seed, smaller total budget, sequence SHA; within a run earliest strictly improving observation wins. No evaluation-guided tie-breaking. Selected seed 43, total budget 500,000, J=32.997840773883 h, identity `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`. Other operator/local candidates remain diagnostics/comparators.

## Warm start versus evolutionary improvement

All following attribution rows use seeds 42-46 and 50k distinct queries. A/B reuse saved results. Only C and D at original mutation 0.20 were missing; ten bounded new runs add 500k queries. D at final 0.10 and the inversion0.10 bridge are saved comparisons. This separates an operator change from a simultaneous mutation-rate change.

| method                        |   seeds |   initial_mean_hr |   initial_sd_hr |   postinitialization_mean_gain_hr |   final_mean_hr |   final_sd_hr |   improve_prior_fraction |    mean_attempts |
|:------------------------------|--------:|------------------:|----------------:|----------------------------------:|----------------:|--------------:|-------------------------:|-----------------:|
| A_original                    |       5 |      33.578302560 |     0.000000000 |                       0.451859111 |    33.126443449 |   0.048495862 |              0.000000000 | 228342.200000000 |
| B_quality_original            |       5 |      33.038123943 |     0.000017441 |                       0.001865304 |    33.036258639 |   0.001551560 |              0.800000000 | 247643.200000000 |
| C_quality_elite_inversion_m02 |       5 |      33.038123943 |     0.000017441 |                       0.003087614 |    33.035036329 |   0.000759065 |              1.000000000 | 230768.400000000 |
| D_final_swap_m01              |       5 |      33.038123943 |     0.000017441 |                       0.038931637 |    32.999192306 |   0.000285667 |              1.000000000 | 453692.600000000 |
| D_quality_elite_swap_m02      |       5 |      33.038123943 |     0.000017441 |                       0.036603034 |    33.001520909 |   0.003519421 |              1.000000000 | 259495.800000000 |
| bridge_inversion_m01          |       5 |      33.038123943 |     0.000017441 |                       0.002354974 |    33.035768969 |   0.001159444 |              1.000000000 | 352191.200000000 |

| comparison                            |   seeds |   mean_final_change_hr |   sd_seed_change_hr |   initial_mean_change_hr |   search_gain_change_hr |
|:--------------------------------------|--------:|-----------------------:|--------------------:|-------------------------:|------------------------:|
| Initialization only                   |       5 |           -0.090184810 |         0.048083954 |             -0.540178617 |            -0.449993806 |
| One elite only                        |       5 |           -0.001222310 |         0.001609489 |              0.000000000 |             0.001222310 |
| Swap versus inversion at mutation 0.20 |       5 |           -0.033515420 |         0.003742093 |              0.000000000 |             0.033515420 |
| Swap rate0.10 versus0.20              |       5 |           -0.002328603 |         0.003273482 |              0.000000000 |             0.002328603 |
| Swap versus inversion at rate0.10     |       5 |           -0.036576663 |         0.001338426 |              0.000000000 |             0.036576663 |

The prior-best already contributes **0.540170817 h** of the selected sequence's0.580461786 h reduction relative to Impact-first (**93.06%**). Further reduction below that inherited best is **0.040290969 h**. This is provenance accounting, not universal causal attribution. Seed-specific improvements made by initialization neighbors are separately counted at generation zero; subsequent gains are counted after generation zero. The full reduction cannot be presented as a new random-start discovery.

The seed 46 discovery cost 81,187 queries is a component of earlier work, not the total cost of finding/selecting the warm start. The 20261009 study separately records 28,730,784 new expensive queries, including heterogeneous 48-sample CV and local/hybrid work. Those development costs are not the 4m final protocol; overlapping prefixes/lookup reuse retain their recorded accounting rather than being falsely called globally unique. Do not add the individual discovery run twice to aggregate development totals. Each loader also makes eight setup-validation objective calls outside the search budget; the ten new runs therefore add 80 such calls as well as 500,000 search queries. They are charged separately. New controlled comparisons record process CPU; historical runs did not.

## Manuscript-ready method description

We used an incumbent-preserving permutation genetic algorithm with ordered crossover, swap mutation, tournament selection and one-elite generational survival. Initial populations combined seven fixed-rule sequences, a previously optimized sequence, inversion variants of high-quality sequences and random permutations. Twenty independent pseudorandom restarts received 100,000 distinct objective evaluations each; five fixed seeds were extended to 500,000 total evaluations. Sequence selection used the unchanged 64-realization planning objective only. Initialization advantage and subsequent search gains were reported separately, alongside the computational effort underlying the warm start. The best feasible ordering and tested local stability do not establish global optimality or uniqueness.
