# Fig06 resource-policy contrast — review candidate

Review only. No promotion or author acceptance is implied. The remote baseline
verified before work was `734e830185b0ebf29a4f2ed91eb1f5bc51f48a29`.

The previous figure compares absolute outcomes at 29 and 57 crews. It exposes
the resource effect on the baseline but does not isolate the effect of choosing
one restoration priority over another. It omits two tested crew levels and all
duration levels. Its exact PDF is retained as `Fig06_Previous_Two_Level_Comparison.pdf`.

The preferred figure uses six panels, all at a native width of 185 mm. Gray
circles identify the Hospital-first reference; orange squares identify the
Impact-first reference. Every difference is **Vulnerability-first minus the
named reference**. Points are discrete tested cases, without connecting curves,
fits or interpolation. Each column shares its y scale across rows. A horizontal
zero line makes direction visible. Tick values retain actual hours.

| Panel | Conditions | Question | Source metric |
|---|---|---|---|
| A | 29/57/86/114 crews, duration multiplier 1.00 | How does the benefit to the highest-vulnerability group differ by crew constraint? | `burden_Q4_hr` |
| B | Same crew cases | Does that targeting improve or worsen aggregate loss relative to each reference? | `population_weighted_normalized_burden_hr` |
| C | Same crew cases | Does targeting narrow or widen absolute high–low group separation? | `absolute_Q4_minus_Q1_hr` |
| D | Duration 0.75/1.00/1.25/1.50, 57 crews | How does the Q4 targeting benefit change with tested repair workload? | `burden_Q4_hr` |
| E | Same duration cases | How does the aggregate policy contrast depend on repair workload and reference? | `population_weighted_normalized_burden_hr` |
| F | Same duration cases | How does absolute group separation change under those conditions? | `absolute_Q4_minus_Q1_hr` |

Inputs: `Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PAIRWISE_EFFECTS.csv`
(baseline) and `VULNERABILITY_RESOURCE_EFFECTS.csv` (other cases), filtered to
2pc50, Vulnerability-first, Hospital-first/Impact-first and the three metrics.
Point values are `paired_mean_difference`; whiskers are the **saved 95%
bootstrap confidence interval** in `bootstrap_ci_low`/`bootstrap_ci_high`.
There are 42 distinct source rows and 48 displayed points because C57_D1 is
shared by the two scenario families. `FIG06_PANEL_SOURCE_INDEX.csv` traces every
displayed point. Mean parity against the two accepted realization-summary
parquets is checked without regenerating an interval or any physical outcome.

Cumulative service loss is the time-integrated modeled tract service deficit
over 0–480 h, in equivalent hours of complete loss. Population loss is
population-weighted across tracts; Q4 loss is population-weighted within the
highest social-vulnerability quartile. Absolute separation is the mean of the
**per-realization absolute Q4–Q1 difference**, not the absolute value of a mean
signed difference. The complete absolute-outcome companions also show the
equal-weight mean loss over hospital-linked tracts, not hospital power delivery
or clinical capacity. Their whiskers are **5th–95th realization ranges**, not
the confidence intervals used in the preferred figure.

## What the tested results support

“Under the tested 2pc50 cases, tighter restoration capacity relative to workload
increased the leverage and distributional consequences of restoration
prioritization.” This refers to these discrete scenario families and these
policy contrasts, not a universal monotonic law or a single equity verdict.

| Reference and condition | Q4 loss change (h) | Population loss change (h) | Absolute separation change (h) |
|---|---:|---:|---:|
| Hospital-first, 29 crews | −6.385 | +1.710 | +15.268 |
| Hospital-first, 57 crews | −1.595 | −0.049 | +2.501 |
| Impact-first, 29 crews | −2.727 | +3.809 | +13.963 |
| Impact-first, 57 crews | −0.710 | +0.664 | +2.540 |
| Hospital-first, duration 0.75 | −1.203 | −0.026 | +1.906 |
| Hospital-first, duration 1.50 | −2.377 | −0.094 | +3.691 |
| Impact-first, duration 0.75 | −0.534 | +0.508 | +1.932 |
| Impact-first, duration 1.50 | −1.060 | +0.976 | +3.757 |

At 86/114 crews the contrasts are near zero and not strictly monotonic; the
absolute-gap contrast at 86 crews is slightly negative. Aggregate direction is
reference-dependent: increasing duration does not create an aggregate penalty
relative to Hospital-first in these saved cases, whereas it does relative to
Impact-first. Thus **targeted benefit ≠ aggregate efficiency ≠ inequality
reduction**. The figure preserves this disagreement.

Degree-first is retained in the complete absolute-outcome comparisons, but is
not elevated to a main contrast reference here. T80, Gini and hospital-linked
outcomes remain in the complete metric review. No crew-by-duration interaction,
untested-level response, historical-hazard intensity inference or universal
scarcity claim is made. No metric definition or source table is modified.

`FIG06_SIDE_BY_SIDE_REVIEW.pdf` is one A3 landscape page placing both 185-mm
figures at native size. `RESOURCE_REVIEW_PACKET.pdf` supplies actual-size pages,
captions and the other isolated layout candidates. PNGs are 600-dpi previews.

Scientific content changed = NO. Promotion = NO. Author review = PENDING.
