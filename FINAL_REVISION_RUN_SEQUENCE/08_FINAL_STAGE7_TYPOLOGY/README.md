# 08 FINAL STAGE7 TYPOLOGY

Validates the single adopted Stage 7 authority: `results/stage7/P2_K3_2299/`, selected by `config/current_stage7.json`. Seven fitted variables; saved K3 primary and K4 sensitivity. No PCA/K-means rerun. The former harmonized five-class and eight-variable products remain archived, never the current authority.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_08_stage7_typology.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/run_08_stage7_typology.py --resume
```
