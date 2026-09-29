# 10 FINAL RESULTS AND FIGURES

Validates the external revised suite archive and the consolidated publication-facing collection in `results/figures/`. The collection inventory is `results/figures/FIGURE_INDEX.csv`; included files are checked against their indexed source authority by SHA-256/Git LFS OID.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_10_final_outputs.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/10_FINAL_RESULTS_AND_FIGURES/run_10_final_outputs.py --resume
```
