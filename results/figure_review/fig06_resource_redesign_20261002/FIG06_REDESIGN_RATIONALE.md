# Fig06 resource-policy contrast — review candidate

Review only. No promotion or author acceptance is implied. The remote baseline
verified before work was `734e830185b0ebf29a4f2ed91eb1f5bc51f48a29`.

The previous figure compares absolute outcomes at 29 and 57 crews. It exposes
the resource effect on the baseline but does not isolate the effect of choosing
one restoration priority over another. It omits two tested crew levels and all
duration levels. Its exact PDF is retained as `Fig06_Previous_Two_Level_Comparison.pdf`.

The preferred title is **Resource dependence of restoration-policy contrasts
under 2pc50**. Crew count and repair duration are two separate
one-factor-at-a-time scenario families, not a unified calibrated capacity
variable.

The preferred figure uses six panels, all at a native width of 185 mm. Gray
circles identify Hospital-first, orange squares Impact-first, and open green
triangles Degree-first. Every difference is **Vulnerability-first minus the
named reference**. Points are discrete tested cases, without connecting curves,
fits or interpolation. Each column shares its y scale across rows. A horizontal
zero line makes direction visible. Tick values retain actual hours.

| Panel | Conditions | Question | Source metric |
|---|---|---|---|
| A | Four tested crew-availability multipliers; duration 1.00× | How does the benefit to the highest-vulnerability group differ by crew constraint? | `burden_Q4_hr` |
| B | Same crew cases | Does that targeting improve or worsen aggregate loss relative to each reference? | `population_weighted_normalized_burden_hr` |
| C | Same crew cases | Does targeting narrow or widen absolute high–low group separation? | `absolute_Q4_minus_Q1_hr` |
| D | Duration 0.75×/1.00×/1.25×/1.50×; reference crew level | How does the Q4 targeting benefit change with tested repair workload? | `burden_Q4_hr` |
| E | Same duration cases | How does the aggregate policy contrast depend on repair workload and reference? | `population_weighted_normalized_burden_hr` |
| F | Same duration cases | How does absolute group separation change under those conditions? | `absolute_Q4_minus_Q1_hr` |

Inputs: `Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PAIRWISE_EFFECTS.csv`
(baseline) and `VULNERABILITY_RESOURCE_EFFECTS.csv` for the existing
Hospital-first/Impact-first contrasts; the two accepted realization-summary
parquets provide the paired Degree-first values. All rows are filtered to
2pc50, Vulnerability-first and the three displayed metrics. Point values are
`paired_mean_difference`; Hospital-first/Impact-first whiskers retain the saved
95% bootstrap confidence intervals in `bootstrap_ci_low`/`bootstrap_ci_high`.
Degree-first mean differences and 95% percentile-bootstrap intervals use the
same saved realization-level metric values and the established paired-bootstrap
routine. There are 63 distinct comparison/metric rows and 72 displayed points:
the reference C57_D1 condition appears in both one-factor scenario families.
`FIG06_PANEL_SOURCE_INDEX.csv` traces every displayed point. No physical
outcome, trajectory or source table is regenerated or modified.

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

“Policy contrasts were largest under the most crew-constrained tested case and
generally diminished at higher crew availability, while longer tested repair
durations amplified Q4 and Q4–Q1 separation contrasts. Together, these tested
cases indicate greater policy leverage when restoration capacity is more
constrained relative to workload.” This refers to these discrete scenario families and these
policy contrasts, not a universal monotonic law or a single equity verdict.

| Reference and condition | Q4 loss change (h) | Population loss change (h) | Absolute separation change (h) |
|---|---:|---:|---:|
| Hospital-first, 0.51× crew availability | −6.385 | +1.710 | +15.268 |
| Hospital-first, 1.00× crew availability | −1.595 | −0.049 | +2.501 |
| Impact-first, 0.51× crew availability | −2.727 | +3.809 | +13.963 |
| Impact-first, 1.00× crew availability | −0.710 | +0.664 | +2.540 |
| Hospital-first, duration 0.75 | −1.203 | −0.026 | +1.906 |
| Hospital-first, duration 1.50 | −2.377 | −0.094 | +3.691 |
| Impact-first, duration 0.75 | −0.534 | +0.508 | +1.932 |
| Impact-first, duration 1.50 | −1.060 | +0.976 | +3.757 |

At 86/114 crews the contrasts are near zero and not strictly monotonic; the
absolute-gap contrast at 86 crews is slightly negative. Aggregate direction is
reference-dependent: increasing duration does not create an aggregate penalty
relative to Hospital-first in these saved cases, whereas it does relative to
Impact-first. Thus **targeted benefit ≠ aggregate efficiency ≠ between-group
separation**. The figure preserves this disagreement. Between-group separation (group
disparity) is distinct from the population-weighted Gini coefficient, an
overall tract-burden inequality measure retained in Fig05 and the supplement.

Degree-first is included as a third named comparator so the reader can see
whether the vulnerability-targeting contrast depends on the choice of
population-oriented, hospital-oriented or degree-based reference. Hospital-first
and Impact-first remain the two formally designated references; Degree-first is
an additional comparison, not a newly declared primary policy. The three outcome
columns are sufficient for this focused figure because they separate the direct
Q4 outcome, the all-tract population-weighted outcome and the Q4–Q1 group gap.
They are not a complete display of all available metrics: T80, hospital-linked
tract loss and population-weighted Gini remain elsewhere in the figure set. The
gap is a between-group measure, while Gini summarizes overall tract-burden
inequality. No crew-by-duration interaction, untested-level response,
historical-hazard intensity inference or universal scarcity claim is made. No
metric definition or source table is modified.

`FIG06_SIDE_BY_SIDE_REVIEW.pdf` is one A3 landscape page placing both 185-mm
figures at native size. `RESOURCE_REVIEW_PACKET.pdf` supplies actual-size pages,
captions and the other isolated layout candidates. PNGs are 600-dpi previews.

At 185-mm native width, the C29 magnitude compresses the 86-/114-crew signs
against the zero line. The preferred figure retains its shared scales without
any broken axis. `Fig06_Separation_Detail_Review.pdf` is a separate review-only
local zoom of those same four saved points/intervals; no main scale or source
value changes. Duration-row direction and relative magnitude remain readable
on the main common scale.

Frozen model definitions, physical outcomes and trajectories changed = NO.
The displayed comparison set now includes the requested Degree-first reference,
with paired means and bootstrap intervals derived from saved outcomes.
Promotion = NO. Author review = PENDING.

## Author-feedback update — 2026-10-04

The three Fig06 outcomes are retained because they answer three distinct questions: whether Q4 loss changes, whether population-weighted loss changes, and whether the absolute Q4–Q1 burden gap changes. This is a focused policy-contrast figure, not a display of every outcome metric. Gini remains a separate overall inequality measure in Fig05; T80 and hospital-linked tract loss remain in the all-policy outcome figures. The Q4–Q1 gap is described as between-group separation, not Gini inequality.

Degree-first is shown as a third named comparator. Its mean matched differences and 95% percentile-bootstrap intervals are derived from saved realization-level summary values using the established paired bootstrap routine; physical outcomes, source tables and trajectories are unchanged. Crew availability is displayed only as multipliers relative to the reference level. The duration row states that the reference crew level is held constant, without repeating a crew count.

Fig07 uses FEMA National Risk Index v1.19 field `SOVI_SCORE`. FEMA's documentation calls this measure the Social Vulnerability Score; the figure uses that concise label. Cluster colors are brighter and keyed consistently across Fig07 and FigS09. Top-ten tract outlines appear only on the hotspot-score map, with a thin boundary stroke.

Presentation update only; no promotion. Frozen scientific inputs changed = 0.
