# Figure 1 Stage 4 delivery

Stage 4 now reads priority rules -> repair scheduling -> completion events. The Impact-first map is a labeled example of an archived priority order. A two-crew Gantt uses four actual task events from evaluation realization 0, with directed travel and DS-specific repair time distinguished. The first mapped rank-5 task, station 300558, completes at 18.15 h; the completion releases its crew, restores raw station functionality and passes the updated state to source-gated service evaluation. Unconstrained parallel repair remains a separate reference.

Final artwork: `results/figure_review_s6_main4_20261107/Main/Fig01.pdf` and `Fig01.png`. The whole-page and Stage 4 before/after comparisons are `FIG01_BEFORE_AFTER.pdf` and `FIG01_STAGE4_DETAIL_BEFORE_AFTER.pdf` in this directory. Source hashes, four plotted events, preservation checks and packet counts are in `FIGURE1_STAGE4_NUMERICAL_AND_PRESERVATION_QA.json`.

The Stage 4 source is `src/la_grid/plotting/make_methodology_workflow_figure.py`; both `build_s6_main4_review.py` and `build_current_suite_p2.py` call it through `figure_presentation.py`. No physical realization, schedule or GA search was rerun. Figure 1 outside Stage 4 and all Supplementary S5 artwork remain unchanged.
