# 06 SOURCE AND NETWORK DIAGNOSTICS

Validates retained dynamic topology and source/connectivity result archives. No diagnostics are recomputed.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_06_source_network_diagnostics.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/06_SOURCE_AND_NETWORK_DIAGNOSTICS/run_06_source_network_diagnostics.py --resume
```
