# Figure 1 Stage 4 visual QA

The final Figure 1 PDF was rendered as a complete 185 x 220 mm page and its Stage 4 region was inspected separately at 600 dpi. The assembled figure-and-caption packet's first page was also rendered. The map's southern extent and all three rows are visible; labels, arrows and the bottom reference line remain inside the module.

| Operation | Displayed source | Meaning |
| --- | --- | --- |
| Priority rules | Figure S7C vector map, Impact-first first five repair targets | Numbered markers are repair rank; purple background represents tract population on a logarithmic scale. Network/community rules and GA provide alternative orders. |
| Repair scheduling | Archived `2pc50/C57_D1/impact-first` evaluation schedule, realization 0 | Two actual crew histories with station IDs. Gray segments are directed travel (<1 h here); teal segments are realized DS-specific repairs. The labels link each crew's first and second task. |
| Completion events | Same archived schedule | Crew 5 completes station 300558 at 18.15 h, becomes available for its next task, and the station's raw functionality becomes 1 before source-gated tract-service evaluation. |

The four plotted events, crew indices, station IDs, arrival and completion times are recorded in `FIGURE1_STAGE4_NUMERICAL_AND_PRESERVATION_QA.json`. Travel segments are thin because the Gantt uses actual time proportions, not exaggerated travel width. No recovery-result curve, T80 or cumulative-loss chart appears in Stage 4.

At 120 dpi the rendered pixels outside Stage 4 match the starting figure. Supplementary S5 PDF, PNG and preview are byte-identical. The complete packet remains 16 pages.

Rebuild: `python src/la_grid/plotting/build_s6_main4_review.py`.
Verify: `python docs/reproducibility/figure1_stage4_methods_correction_20261110/verify_correction.py`.
