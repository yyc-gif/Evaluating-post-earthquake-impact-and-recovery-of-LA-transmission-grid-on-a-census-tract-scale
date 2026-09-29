# 09 CAPACITY ROBUSTNESS

Validates closed SCE capacity outputs only; does not call the closure computation.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_09_capacity_robustness.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/09_CAPACITY_ROBUSTNESS/run_09_capacity_robustness.py --resume
```
