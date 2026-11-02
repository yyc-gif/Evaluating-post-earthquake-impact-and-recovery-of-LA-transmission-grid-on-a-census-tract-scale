# 05 SERVICE AND TRACT EVALUATION

Validates formal offline shards and accepted service/distribution result identities. Does not recompute metrics.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Report one total-burden estimand: the population-weighted mean of tract-normalized
burden over resolved tracts (`population_weighted_normalized_burden_hr`). The
alternative that additionally weights by resolved mapping mass is retired from
new summaries; this is a reporting-definition choice, not a claim that every
historical realization was independently re-evaluated. For each resolved tract,
`resolved_mass` still normalizes its mapped deficit to `normalized_burden_hr`,
determines whether it is included, and supports coverage diagnostics. The
population-times-resolved-mass denominator is retained for population service
recovery curves and T50/T80/T90. Component-loss accounting may also use mapped
mass internally. Existing frozen archives are preserved and are not rewritten.
The same single reported total is used for mapping sensitivities: a partially
resolved tract is included with its full frozen population weight after its
burden is normalized by resolved mass. This change does not alter restoration
scheduling or the GA optimization objective.

Entrypoint: `run_05_service_evaluation.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/05_SERVICE_AND_TRACT_EVALUATION/run_05_service_evaluation.py --resume
```
