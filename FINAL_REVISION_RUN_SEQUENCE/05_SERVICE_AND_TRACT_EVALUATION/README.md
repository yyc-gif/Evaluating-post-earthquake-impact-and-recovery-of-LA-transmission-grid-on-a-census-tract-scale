# 05 SERVICE AND TRACT EVALUATION

Validates formal offline shards and accepted service/distribution result identities. Does not recompute metrics.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_05_service_evaluation.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/05_SERVICE_AND_TRACT_EVALUATION/run_05_service_evaluation.py --resume
```
