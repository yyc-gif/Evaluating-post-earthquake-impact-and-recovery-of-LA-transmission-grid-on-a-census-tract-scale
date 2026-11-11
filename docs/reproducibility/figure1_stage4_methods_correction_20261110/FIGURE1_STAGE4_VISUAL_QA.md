# Figure 1 Stage 4 visual QA

Final page size is 185 x 220 mm. At native publication dimensions, Stage 4 remains a three-part method flow and fits inside the original module area. The Figure 1 preview and 600-dpi Stage 4 panel were inspected. The Impact-first map's full southern extent is present; the 1-5 rank markers retain their saved locations, with 7 pt numerals and slightly enlarged circles. The explanatory text, crew labels, station IDs, time ticks, and event descriptions are 7 pt.

| Step | What the reader sees |
| --- | --- |
| Priority rules | Impact-first map: purple is log tract population and numbered stations are ranks 1-5. Network/community rules and GA set station orders; Unconstrained is identified separately as parallel repair. |
| Repair scheduling | Actual archived 2pc50 / C57_D1 evaluation realization 0, showing crews 5 and 9 (2 of the modeled 57). DS>0 tasks are assigned to the earliest-free crew. Each row identifies its two station tasks; gray marks directed travel and teal shows realized DS-specific repair duration. The elapsed-time axis has 0, 15, 30 and 45 h ticks. |
| Completion events | Station 300558 completes at 18.15 h, releasing crew 5. Raw station functionality becomes 1, then the updated state passes to the source gate and tract-service evaluation. |

The final crew-9 task completes at 42.9368228474 h and appears before the 45 h axis limit. Event rows, the source NPZ SHA256, and scheduler/resource-code identities are in `FIGURE1_STAGE4_NUMERICAL_AND_PRESERVATION_QA.json`. The four events were read from the archived schedule; no schedule or simulation was rerun.

Rendered full-page review: `FIG01_COMPLETE_PAGE_FINAL_150DPI.png`. The packet's Figure 1 and caption page was inspected. Every rendered pixel outside the Stage 4 replacement region is identical to starting commit `9119bbc5290215f422426037b5cb7f9051adeabd`. Supplementary S5 PDF, PNG and page preview remain byte-identical. The combined packet remains 16 pages.

Rebuild: `python src/la_grid/plotting/build_s6_main4_review.py`.
Verify: `python docs/reproducibility/figure1_stage4_methods_correction_20261110/verify_correction.py`.
