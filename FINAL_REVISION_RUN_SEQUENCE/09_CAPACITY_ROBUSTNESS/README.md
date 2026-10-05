# 09 CAPACITY ROBUSTNESS

Validates the original capacity closure for provenance and the current evidence-supported geographic results in `results/capacity/SCE_SUPPORTED_GEOGRAPHY/`. It does not execute capacity post-processing. S8 is integrated into the complete figure set and validated at Stage 10. The primary domain is 676 strict-SCE supported tracts; the independently identified OLINDA-local domain is 25 tracts. The old full-study approximately 0.12 h value is not the current manuscript-facing result.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_09_capacity_robustness.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/09_CAPACITY_ROBUSTNESS/run_09_capacity_robustness.py --resume
```
