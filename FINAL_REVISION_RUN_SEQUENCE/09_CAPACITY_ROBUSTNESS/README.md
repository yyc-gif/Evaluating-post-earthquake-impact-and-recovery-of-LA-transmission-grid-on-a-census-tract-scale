# 09 CAPACITY ROBUSTNESS

Validates closed SCE capacity outputs only; does not call the closure computation.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.
