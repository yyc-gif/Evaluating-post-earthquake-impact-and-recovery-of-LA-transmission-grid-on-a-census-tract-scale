# Metric Direction and Count Definitions

All paired differences are revised GA minus the named reference. The reused statistical engine's generic fields `improved_count`, `worsened_count` and `ties_count` count differences below -1e-9, above +1e-9 and within that tolerance, respectively. These are algebraic sign counts; their inherited names must not imply that a lower value is scientifically preferable for every metric.

- Population loss, hospital-associated burden, absolute Q4-Q1 burden gap and burden Gini: a negative difference is lower burden/disparity/Gini.
- T80, completion time, travel, makespan and disconnected-dependency integral: a negative difference is earlier/shorter, or a smaller disconnected integral. These are distinct outcomes, not interchangeable recovery objectives.
- `signed_Q4_minus_Q1_hr`: sign describes which quartile has larger mean burden. Neither a more positive nor a more negative value is inherently more equitable. Only the corresponding absolute-gap endpoint measures this two-quartile disparity magnitude. The report's sign counts for this signed endpoint are not equity improvement/worsening counts.
- `effective_service_at_480`: a higher value indicates greater modeled availability. The generic negative-difference count is therefore not an improvement count for this metric. All three policies reach1 in this cohort, so there are2000 paired ties per contrast.
- Individual Q1-Q4 burdens: a negative difference indicates lower burden in that quartile; it does not by itself establish lower inequality between groups.
- The decomposition components are signed accounting terms. A smaller source-loss component does not alone prove better source connectivity, because its multiplier fF can change. See the separate native dependency-mass integral and component reconstruction.

All pointwise/simultaneous intervals, original-unit differences and counts are preserved unchanged. This codebook corrects interpretation of inherited generic column names, not statistics or the frozen analysis plan. No causal effect, noninferiority margin or equivalence criterion is introduced.
