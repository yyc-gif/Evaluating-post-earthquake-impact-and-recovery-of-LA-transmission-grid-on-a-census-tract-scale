# GA optimization decision record — 2026-10-09

Original formal policies and artwork remain in force. This round adds a separate parameter/operator/local-search diagnostic, including completed exploratory reuse of the existing evaluation cohort.

[Algorithm audit and Q1–Q5](../../results/diagnostics/ga_optimization_20261009/GA_HYPERPARAMETER_AND_OPERATOR_AUDIT.md), [solution quality/generalization and Q6–Q8](../../results/diagnostics/ga_optimization_20261009/GA_SOLUTION_QUALITY_AND_GENERALIZATION.md), [actual-size artwork and captions](../../results/figure_review/Additional_Evidence/GA_Optimization_20261009/GA_OPTIMIZATION_REVIEW_PACKET.pdf).

The best new planning loss is 32.997840774 h, compared with 33.038131743 h previously and 33.578302560 h for Impact-first. A fixed-model relaxation gives a conservatively rounded mathematical lower bound of 31.360999855 h. The remaining gap precludes a global-optimality claim. Three different selected full permutations tie on planning loss and completion arrays; their reused-cohort results are reported without reselection.

The recommended tested operating region uses population100, crossover0.80, swap mutation0.10, tournament3, one elite and an explicitly declared prior-quality initialization. Its twenty-seed mean is 32.999625 h (SD0.001300); fifteen additional restart seeds are distinguished from five common screening seeds. This is a conditional recommendation, not an optimal configuration. Mixed mutation remains a promising alternative. The tested hybrid did not outperform the confirmed swap variant at equal joint budget.

Current S11 retains four-hazard policy comparisons. Historical hazards and 2pc50 parameterization differ; the comparison is not pure hazard-intensity sensitivity. The station/network/community mechanism companion explains f, fFC and population dependency without replacing the distinct S04 static-criticality/dynamic-component purpose or equating functionality with delivered MW.

No formal sequence replacement or fresh physical validation sample is authorized by these results. Before any later formal promotion, fix the selection rule and sequence identity; the existing inspected1,000 cohort cannot be relabeled as untouched validation.
