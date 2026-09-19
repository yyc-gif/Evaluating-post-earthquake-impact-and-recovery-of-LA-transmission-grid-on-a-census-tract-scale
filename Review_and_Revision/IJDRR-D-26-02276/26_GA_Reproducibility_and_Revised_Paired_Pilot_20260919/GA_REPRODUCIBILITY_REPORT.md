# GA Reproducibility Report

## Role and declared information set

The GA is an **optimization benchmark/comparator**, not a methodological contribution or proof of optimality. It generated ex-ante full D302 permutations before any of the 32 physical realizations were sampled. It never observed realized damage, realized repair durations, service trajectories, T80, tract burden, or winners/losers.

All policies use only frozen Architecture B population, hospital, and NRI-derived SOVI priority components. `NETWORK_IMPORTANCE_TERM = DROP`. Weights are **policy-design / optimization objective coefficients**. `W_HOSP=20` defines a deliberately hospital-dominant archetype; it is not empirical, calibrated, or utility-recommended.

## Algorithm and workload

- chromosome: full 302-ID permutation
- population: 100
- generations: 100 fixed; no early stopping
- ordered crossover: 0.8
- inversion mutation: 0.2
- tournament size: 3
- seeds: 42–51 for every policy (30 runs)
- objective horizon: `Tmax=504 h` (`480+24`), frozen before optimization
- workload: 2pc50 expected positive on-site workload; no realized pilot duration
- exact same-seed five-generation repeat: PASS

## Ten-seed results

| policy | mean | sd | min | max | best | worst | sequence_count | last20_improvement_mean | canonical_seed | sequence_hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GA-Balanced | 0.7597 | 0.0134 | 0.7427 | 0.7810 | 0.7810 | 0.7427 | 10 | 0.0014 | 51 | 1ac180bb40fa2bc52736c0d07659088d1a0b697d18cde998ec795b7b8cad1c62 |
| GA-Efficiency | 0.3279 | 0.0262 | 0.2904 | 0.3683 | 0.3683 | 0.2904 | 10 | 0.0031 | 47 | dd9752311f6b59134e73e603f74a8776932ee93c2c297214382d30431c8d42aa |
| GA-HospFirst | 0.8851 | 0.0106 | 0.8655 | 0.9006 | 0.9006 | 0.8655 | 10 | 0.0028 | 46 | 39b4d300c0471a9eb65bb458cefc50b5d706c7863c27cbcaa44a60b47f9e7132 |

Each policy produced 10 distinct final sequences. The final-fitness spread and nonzero mean last-20-generation improvement show seed dependence and continued late-budget search. No parameter was tuned after results were seen. Canonical selection used the declared highest-fitness, smallest-seed tie rule. Curves and final hashes are in `GA_CONVERGENCE_BY_SEED.csv`; canonical 302-ID permutations are in `GA_CANONICAL_SEQUENCES.csv`.

## Hospital-first versus GA-HospFirst surrogate

- canonical GA-HospFirst fitness: `0.900607781997`
- Hospital-first fitness under the identical objective: `0.916319981609`
- GA minus Hospital-first: `-0.015712199612`
- sequences identical: `False`

Hospital-first scored `0.015712` higher. Under the frozen 100-by-100 budget, GA-HospFirst did **not** surpass the deterministic rule even on its own surrogate. The GA sequence is a reproducible finite-budget stochastic comparator, not a verified optimum. Objective alignment still matters because the surrogate is not T80, realized burden, travel, or disparity, but it cannot explain away this search shortfall.
