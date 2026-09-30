# 09 CAPACITY ROBUSTNESS

Validates closed SCE capacity numerical outputs and audit only; does not call the closure computation. The publication-facing capacity panels are part of `results/figures/FigS08_Capacity_Sensitivity.*` and are validated in Stage 10 against frozen sources.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_09_capacity_robustness.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/09_CAPACITY_ROBUSTNESS/run_09_capacity_robustness.py --resume
```
