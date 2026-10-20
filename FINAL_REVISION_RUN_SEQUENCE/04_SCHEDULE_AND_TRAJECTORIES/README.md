# 04 SCHEDULE AND TRAJECTORIES

Validates/reuses 84,000 formal and 10,000 Vulnerability-first trajectories. Does not schedule.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_04_trajectories.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/04_SCHEDULE_AND_TRAJECTORIES/run_04_trajectories.py --resume
```
