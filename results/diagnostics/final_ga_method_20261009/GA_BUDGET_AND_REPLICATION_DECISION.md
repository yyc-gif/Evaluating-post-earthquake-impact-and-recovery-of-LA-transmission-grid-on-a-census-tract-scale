# Final computational budget and replication decision

Recommend **Stage A 20 seeds x100k + Stage B fixed seeds 42-46 continued to 500k total**, with the recommended unchanged parameter set. No further open-ended sweep. Stage B's seed rule is fixed before extension, not chosen using planning rank or evaluation effects. The nominal unique-query total is 4,000,000:20*100k+5*(500k-100k). Stage B adds2m to Stage A's2m;100k and 500k are unequal budgets.

## Five common extended streams at common checkpoints

|   distinct_evaluations |   seeds |      best_hr |    median_hr |      mean_hr |       sd_hr |   mean_wall_seconds |   mean_new_strict | mean_marginal_gain_hr   |
|-----------------------:|--------:|-------------:|-------------:|-------------:|------------:|--------------------:|------------------:|:------------------------|
|                  50000 |       5 | 32.998792492 | 32.999203252 | 32.999192306 | 0.000285667 |        87.317885140 |       0.000000000 | not applicable          |
|                 100000 |       5 | 32.997904329 | 32.999203252 | 32.998888541 | 0.000591759 |       173.384974840 |       2.000000000 | 0.00030376489158925326  |
|                 250000 |       5 | 32.997896622 | 32.999203252 | 32.998878311 | 0.000587553 |       459.449218120 |       0.800000000 | 1.0230431648494687e-05  |
|                 500000 |       5 | 32.997840774 | 32.999203252 | 32.998867141 | 0.000610946 |       928.081128980 |       0.200000000 | 1.1169568514901584e-05  |

FINAL_BUDGET_CHECKPOINTS.csv supplies best objectives, actual attempts/generations, completed-generation boundaries, initial/reference improvements, strict improvements and time per seed. Counts exclude generation-zero scoring. A strict tiny improvement is not automatically a practically meaningful scientific gain. No benefit threshold is invented.

Twenty-seed 100k result: mean 32.999625244 h, SD 0.001300140, median 32.999215517, best 32.997904329, worst 33.002987520. All 20 improve prior best. Seeds42-46 are common screening seeds;47-61 are 15 additional pseudorandom restarts. This replication assesses search stochasticity under the same 64 samples and selected configuration, not independent physical validation.

Mean100k-to 500k gain for the same five streams: **0.000021400 h**. Later gains are small relative to the approximately 0.58 h improvement over Impact-first. A bounded extension remains defensible for final selection; small late gains do not prove there is no remaining improvement.

## CPU, wall-clock and generation caveats

Historical process CPU time was **not recorded**. The saved objective_seconds uses perf_counter and is an objective wall timer, not CPU. Do not relabel it or invent a historical CPU estimate. New controlled comparisons record process CPU explicitly. Recorded per-run times include concurrent-host effects; their sum is aggregate run wall duration, not elapsed batch time or total CPU. The budget CSV records minimum/maximum actual generations and completed-generation boundaries; no common generation count is fabricated.

Continuation preserves RNG/state/cache. If a local checkpoint was removed after completing old runs, a from-scratch500k replay reproduces the algorithm but pays its 100k prefix again. Existing saved 500k source records are the reporting authority; future fresh execution should retain resume checkpoints. Count actual replay overhead separately from the nominal continuation budget. Warm-start discovery, screening and operator development are disclosed as earlier work, not free initialization. New evaluation cannot select extension seeds or chromosomes.
