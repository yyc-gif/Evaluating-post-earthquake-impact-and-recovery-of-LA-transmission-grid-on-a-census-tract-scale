# Sensitivity Output Index

Use only the files in this folder for the cleaned sensitivity-analysis deliverable. All sensitivity calculations are restricted to the 2%-in-50-year (`2pc50`) scenario.

Regenerate these outputs through `C257H_Project_Main.py` or directly with `build_sensitivity_outputs.py`. The clean PNGs are generated without figure-level caption-style titles; those titles belong in the manuscript caption or table caption.

## Main text

1. `Main/Fig_Sensitivity_T80_Response_2pc50.png`
2. Use the editable table in `Tables/Table_Sensitivity_Summary_2pc50.tex`, `Tables/Table_Sensitivity_Summary_2pc50.md`, or `Tables/Table_Sensitivity_Summary_2pc50.csv`.

`Main/Table_Sensitivity_Summary_2pc50.png` is a visual preview only; do not use the PNG as the manuscript table.

Suggested main-text framing:

The qualitative ranking of the leading restoration strategies is generally stable, whereas absolute recovery milestones are sensitive to crew availability and repair-duration assumptions. Mapping-related parameters alter spatial dependency concentration more than aggregate recovery timing.

## Supplementary

1. `Supplementary/Fig_Supp_IDW_Mapping_Diagnostics.png`
2. `Supplementary/Fig_Supp_Rank_Stability_T80.png`

Suggested captions:

Figure S1. Effect of the IDW dependency threshold theta_W on tract-dependency concentration. Increasing theta_W reduces the mean number of supplying substations per tract and increases the mean Herfindahl-Hirschman Index (HHI), indicating a shift from multi-source to more concentrated tract-level dependency. The blue axis shows mean supplying substations, and the red axis shows mean HHI.

Figure S2. Strategy-rank stability relative to the `2pc50` baseline configuration, measured using Spearman's rank correlation for population-weighted T80. Blank cells indicate parameter values not applicable to a sensitivity group. Average ranks are used for tied T80 values.

## Tables

1. `Tables/Table_Sensitivity_Summary_2pc50.csv`
2. `Tables/Table_Sensitivity_Summary_2pc50.md`
3. `Tables/Table_Sensitivity_Summary_2pc50.tex`
4. `Tables/Table_Sensitivity_Rank_Stability_2pc50.csv`

Table note: the column `Max within-strategy change in T80_pop (h)` reports the largest parameter-induced T80 change within any single strategy, not the cross-strategy spread.
