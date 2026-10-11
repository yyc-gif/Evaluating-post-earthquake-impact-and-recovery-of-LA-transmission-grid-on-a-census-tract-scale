# Frozen random only GA independent validation

The frozen random-only GA candidate is validated on a new, authorized cohort of 2,000 damage/repair realizations conditional on the unchanged 2pc50 field and physical model. The exact 92-station sequence is seed 2026103108 at 100k distinct evaluations, SHA256 `edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a`. The 20-seed execution protocol and final selection were committed before this fresh cohort. No tuning, optimization or reselection occurred during validation.

## Population and source path mechanism

Mean normalized population-weighted service loss is 33.048229 h for GA and 33.580903 h for Impact-first. GA minus Impact-first is -0.532675 h; two-contrast simultaneous 95% interval [-0.563982, -0.502321] h. The mean reduction is 1.586% of the Impact-first mean. GA has lower population loss in 1741/2,000 (87.05%), higher loss in 259 and no ties. This is modeled efficiency, not observed outages or delivered energy.

The exact component difference is self +0.277475 h, threshold +0.010638 h, source-path -0.820788 h, summing to -0.532675 h. Less source-path loss offsets greater self and threshold loss. These are descriptive event-integral components, not evidence that a particular station movement caused the benefit.

## Hospital associated tracts

The 103 hospital-associated tracts have mean normalized burden 32.826021 h under GA versus 33.086725 h under Impact-first. The paired difference is -0.260704 h, pointwise 95% interval [-0.288579, -0.233509] h. This is an unweighted mean of normalized tract burdens, not hospital-load-weighted loss, hospital uptime, patient disruption, facility capacity or MWh. It is not a comparison with Hospital-first, which is outside this fresh three-policy cohort.

## Distributional tradeoff

GA lowers all four population-weighted SOVI-quartile mean burdens relative to Impact-first. Q1-Q4 GA means are 34.809529, 33.370729, 32.265592, 31.971272 h; corresponding Impact-first means are 35.283431, 33.705242, 32.792827, 32.748901 h. Q4 is the highest vulnerability group, but its baseline mean burden is lower than Q1 in this model. A larger Q4 reduction does not establish lower disparity.

Mean per-realization absolute Q4-Q1 separation increases from 2.952449 h to 3.185182 h; paired increase +0.232733 h, pointwise 95% interval [0.206896, 0.258975] h. Population-weighted tract burden Gini increases from 0.189654 to 0.199444; difference +0.009790, pointwise 95% interval [0.009298, 0.010293]. Thus absolute group outcomes improve while measured dispersion worsens. Do not describe this as an equity improvement.

The fixed labels are SOVI tract quartiles, not equal-population bins. Population weighting occurs within each group. Q1-Q4 populations are 2,072,860, 2,288,266, 2,305,690, 2,399,706; the full 2315-tract population is 9,066,522. Mean absolute gaps are means of realization-specific absolute differences, not absolute values of averaged signed differences. Gini is likewise averaged after per-realization computation.

## Legacy sequence traceability

The unchanged legacy formal GA has mean population loss 33.075265 h. New-minus-legacy is -0.027036 h, two-contrast simultaneous 95% interval [-0.042877, -0.012255] h. Yet the new candidate worsens 1363/2,000 (68.15%) realizations, with median difference +0.042645 h. A minority of larger benefits lowers the mean; this is not uniform dominance. The new candidate's hospital-associated mean is +0.018708 h higher than legacy, and both absolute-gap and Gini means increase. Retain these results as supplementary provenance. Do not present a second GA method or replace legacy results retrospectively.

## Uncertainty and interpretation

All policies share the same new physical draw per realization. Inference resamples complete paired realizations, not tracts or 6,000 trajectories. The 20,000-resample bootstrap uses seed 2026110400. Only the two population-loss contrasts have simultaneous 95% Bonferroni percentile intervals; hospital, quartile, gap, Gini and T80 intervals are descriptive pointwise. All 2,000 system T80 crossings occurred before 480 h for all three strategies. GA mean system T80 is 45.178976 h and Impact-first 45.273142 h; these are means of per-realization system crossings, not tract-mean T80 or the crossing of the mean curve.

This is a prospective stochastic model test, not empirical validation against measured electricity outages. The post-data method choice and failed 90% single-run planning-proximity criterion remain in the immutable method evidence. A fresh physical cohort does not turn those earlier choices into preregistered method development or imply reliable performance from every single optimization run.
