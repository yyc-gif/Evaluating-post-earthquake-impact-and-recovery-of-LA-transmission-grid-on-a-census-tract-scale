# Interpretation Of The Completed Fixed Validation

All findings below refer to the completed 2,000-state cohort, not planning
samples or intermediate checkpoints. The numerical companion is
`INDEPENDENT_VALIDATION_RESULTS.md`. Original numerical exports and their
hashes are retained unchanged in `fixed_2000_20261010/`.

## Primary Finding

Frozen GA reduced mean normalized population-weighted service loss from
33.522649523125 h to 33.020747887680 h. Its paired difference from Impact-first
was -0.501901635445 h, with MCSE 0.011604801347 h and the prespecified 95%
paired-bootstrap interval [-0.524975128718, -0.479472230142] h.

The reduction is about 1.4972% of the reference mean. GA had lower loss in
1,810/2,000 states (90.5%), higher loss in 190, and no ties at the frozen
1e-9 h tolerance. The median difference was -0.387835427245 h. This supports
a repeatable mean benefit of the frozen sequence under new states of the
same model. It does not demonstrate empirical utility-restoration accuracy
or the necessity/superiority of evolutionary search over all alternatives.

The roughly 30.11 equivalent service-loss minutes must not be described as
every household regaining electricity 30 minutes earlier. Mean population
T80 changed by only -0.188486236263 h, approximately 11.31 minutes. The two
endpoints measure different aspects of recovery. All 26,000 T80 records
reached 80% by 480 h, so this cohort has no T80 censoring. That does not imply
all stations completed repairs or all service reached 100% by 480 h.

Sources: PRIMARY_PAIRED_EFFECT.csv, POLICY_OUTCOMES.csv, PAIRED_EFFECTS.csv,
T80_CENSORING.csv and PAIRED_DIFFERENCE_DISTRIBUTIONS.csv.

## Source Connectivity Accounts For The Net Benefit

Mean losses for Impact-first versus Frozen GA, respectively:

| Accounting component | Impact-first (h) | Frozen GA (h) | GA minus reference (h) |
|---|---:|---:|---:|
| Self | 28.456563791 | 28.660326188 | +0.203762398 |
| Threshold | 0.933484657 | 0.941304230 | +0.007819572 |
| Source connectivity | 4.132601075 | 3.419117470 | -0.713483606 |
| Total | 33.522649523 | 33.020747888 | -0.501901635 |

The reduction in the source-connectivity accounting component outweighs
increases in self and threshold losses. This is consistent with the frozen
source-gated objective rewarding restoration of useful connected paths.
It is not evidence that all stations finish sooner, nor a controlled causal
attribution to a particular station, edge or dispatch movement. Complete
event traces and scheduling records are archived if a separately authorized
causal mechanism study is required.

Source: MEAN_LOSS_COMPONENTS.csv and the exact event arrays in the capsule.

## Refined ILS Has A Different Benefit Distribution

The prespecified secondary ILS-minus-GA comparison has mean -0.024549091909 h
(approximately 1.473 minutes), MCSE 0.007338083738 h and descriptive pointwise
95% interval [-0.039332393533, -0.010473325774] h. This secondary interval
does not cross zero but is not an additional multiplicity-adjusted
confirmatory result.

ILS improved 608 states (30.4%) and worsened 1,392 (69.6%). Its median
difference was +0.046945216879 h, approximately 2.817 minutes against ILS.
Conditional mean changes were -0.292843886579 h among improved states and
+0.092637140245 h among worsened states. Less frequent, larger reductions
outweigh more frequent, smaller increases under the original mean-loss
objective. This is distributional evidence, not a reason to retrospectively
replace the objective with a median or win-rate objective.

The new cohort supports a small average advantage for this fixed ILS
sequence, while preserving the earlier concern about uneven realization
benefits. It does not prove that one old realization drives the fresh
result, and no validation-based chromosome reselection or formal GA
replacement has occurred. Optimizer-method comparisons still require the
separate matched-budget search evidence, not just these two selected orders.

Sources: PAIRED_EFFECTS.csv, PAIRED_DIFFERENCE_DISTRIBUTIONS.csv and
REALIZATION_OUTCOMES.csv. Conditional means can be reproduced after
completion, without sampling or changing any strategy:

```python
import pandas as pd
from la_grid.diagnostics import independent_validation_20261010 as v
path = v.OUT / 'authorized_validation/fixed_2000_20261010/REALIZATION_OUTCOMES.csv'
wide = pd.read_csv(v.long_path(path), float_precision='round_trip').pivot(
    index='realization_id', columns='strategy', values=v.PRIMARY)
d = wide[v.ILS] - wide[v.GA]
print(d[d < -1e-9].mean(), d[d > 1e-9].mean(), d.median())
```

## Efficiency Is Not Universal Equity Improvement

GA reduced the mean burden of both fixed SOVI groups: Q1 by 0.442223303540 h
and Q4 by 0.656640349523 h. Hospital-linked equal-tract burden decreased by
0.283895943586 h. These are descriptive secondary benefits.

However, Q4 already had lower mean loss than Q1 under Impact-first. The
signed Q4-minus-Q1 mean changed from -2.629434541345 h to -2.843851587328 h.
A more negative signed value is not automatically a smaller disparity.
The mean per-realization absolute Q4-Q1 gap increased by 0.158232892912 h
(pointwise interval [0.138352384318, 0.178127943814] h), and population-weighted
loss Gini increased by 0.008311508732 (pointwise interval
[0.007921456044, 0.008717886048]).

Thus the manuscript must not claim a simultaneous improvement in all
efficiency and inequality measures. Lower burden for a socially vulnerable
group and lower overall inter-tract inequality are distinct statements.
These patterns are associations within fixed modeled dependencies and
physical realizations, not causal effects of social vulnerability.

Important exporter terminology: `improved_count` in PAIRED_EFFECTS.csv means
candidate-minus-reference < -1e-9 for every metric. This correctly indicates
improvement for the primary loss but does not establish improvement for a
signed gap or an endpoint where higher is preferable, such as availability.
Interpret signs using each endpoint's definition. Frozen exports were not
rewritten to change that convention.

Sources: POLICY_OUTCOMES.csv and PAIRED_EFFECTS.csv.

## Disposition

The authorized validation is complete and suitable for scientific author
review. Preserve the original mean-loss primary endpoint, report its modest
relative magnitude and broad state-level benefit, and retain ILS and equity
trade-offs as secondary findings. No new samples, tuning, priority ranking,
method replacement, manuscript change or figure promotion is authorized by
completion of this batch.
