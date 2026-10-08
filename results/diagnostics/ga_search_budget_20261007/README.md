# GA search-budget diagnostic

Same 64 planning realizations, objective, exact scheduler/source gate and GA operators as the original formal run. The formal evaluation sequence and results are not replaced.

- `GA_SEARCH_BUDGET_SENSITIVITY.csv`: all 25 runs, including exact baseline replays and 20 extended-budget seeds.
- `INPUT_IDENTITY.json`: physical inputs, mapping, travel, graph, source set, implementation and planning horizon identities.
- `SEARCH_DECISION.json`: early-improvement stopping decision; larger budgets were skipped.
- `POSTRUN_AUDIT.json` and `OBJECTIVE_LANDSCAPE_AUDIT.csv`: candidate identities, objective ties and effective-order checks.
- `p100_g100_s42` etc.: full config/sequence record, generation history, unique candidate permutations/fitness and 64 planning-realization differences.
- `GA_SEARCH_BUDGET_DIAGNOSTIC.pdf/.png`: current S05 artwork, not a separate manuscript figure.

[Interpretation and objective formula](../../../docs/reviewer/GA_SEARCH_BUDGET_SENSITIVITY_20261007.md).
