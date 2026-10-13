# 08 FINAL STAGE7 TYPOLOGY

Validates the single final Stage 7 authority: Output_SOVI_Harmonized. No PCA/K-means rerun.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_08_stage7_typology.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/run_08_stage7_typology.py --resume
```
