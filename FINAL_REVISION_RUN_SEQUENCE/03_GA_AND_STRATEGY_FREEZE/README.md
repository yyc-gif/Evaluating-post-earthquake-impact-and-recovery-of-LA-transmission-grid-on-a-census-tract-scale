# 03 GA AND STRATEGY FREEZE

Validates GA provenance and frozen final sequence registry. Does not execute GA.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_03_strategy_freeze.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/03_GA_AND_STRATEGY_FREEZE/run_03_strategy_freeze.py --resume
```
