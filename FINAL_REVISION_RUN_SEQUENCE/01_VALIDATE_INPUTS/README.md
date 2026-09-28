# 01 VALIDATE INPUTS

Validates frozen matrix, input hashes, code and Git/LFS identities, and protected archive identity. No sampling.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.
