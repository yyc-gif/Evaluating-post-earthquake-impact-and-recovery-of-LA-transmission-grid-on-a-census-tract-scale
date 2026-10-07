# 10 FINAL RESULTS AND FIGURES

Validates the current complete Fig01–Fig07, combined FigS01 and FigS03–FigS13 set in `results/figures/` against the byte-identical author-review files. The complete figure-and-caption packet is `results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf`. S8 includes the supported-geography correction; there is no separate proposed S8B. The external revised suite remains historical scientific source provenance.

This stage is validation/reuse only under `run_all.py --resume`. Missing authority files cause fail-fast; no scientific fallback is permitted.

Entrypoint: `run_10_final_outputs.py`

Run this stage directly with:

```bash
python FINAL_REVISION_RUN_SEQUENCE/10_FINAL_RESULTS_AND_FIGURES/run_10_final_outputs.py --resume
```

S01 now combines damage severity with the former S02 initial-service maps. S06 validates the mapping support and service-assumption sensitivity figure; crew/duration scenario families remain in S12/S13.
