# 02 MAPPING AND PHYSICAL SAMPLES

Validates/reuses production M1, 4,000 evaluation samples and 64 independent planning samples. No generation in resume.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_02_mapping_and_physical.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/02_MAPPING_AND_PHYSICAL_SAMPLES/run_02_mapping_and_physical.py --resume
```
