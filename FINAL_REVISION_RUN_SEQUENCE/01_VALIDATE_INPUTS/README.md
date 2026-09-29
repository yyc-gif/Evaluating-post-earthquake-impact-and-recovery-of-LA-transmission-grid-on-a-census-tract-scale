# 01 VALIDATE INPUTS

Validates frozen matrix, input hashes, code and Git/LFS identities, and protected archive identity. No sampling.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_01_validate.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/01_VALIDATE_INPUTS/run_01_validate.py --resume
```
