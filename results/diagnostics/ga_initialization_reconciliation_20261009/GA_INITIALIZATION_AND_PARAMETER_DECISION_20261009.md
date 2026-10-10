# GA initialization and parameter decision

The completed evidence supports retaining the existing population 100 / ordered crossover 0.80 / swap mutation 0.10 / tournament 3 / one-elite method as a reproducible reporting reference. It does not establish that these values or the 7/1/25/67 allocation are optimal. No formal candidate, model, physical samples, evaluation trajectories or manuscript figures were changed.

## Retrieved evidence

Both cloud runs are complete: 510 initialization observations at 20k (17 cases x 30 seeds), 100 at 100k (5 cases x 20 seeds). All 50 artifact digests were verified. Removing 1153 duplicate representations leaves 610 distinct final-budget observations. The 100 overlapping 20k prefixes agree within 2.274e-13 h and share initial-population hashes. The 20 higher-budget seeds are a subset of the 30, not 50 independent seeds. Full immutable archives and source identities are retained.

The inherited-information package has a finite-budget advantage: removing the prior chromosome and all local neighbors raises final mean loss by 0.007447 h at 20k (95% paired interval 0.005322 to 0.009572 h). At 100k this becomes 0.001609 h (pointwise 0.000111 to 0.003107 h; simultaneous-contrast interval -0.000365 to 0.003583 h). Neither the residual package effect nor equivalence is established after multiplicity. Exact-copy, heuristic-copy and neighbor-count comparisons cannot be interpreted as independent contributions: their replacements change composition and RNG use.

`heuristics_0` retains the scored heuristic archive and Impact-derived neighbors. `warm_copies_0` retains 13 prior-derived neighbors. `heuristics_only` removes both inherited information and all local neighbors, including Impact neighbors. No pure no-prior-information / no-archive control was run. At generation zero most of the warm-start advantage was inherited from earlier development, not created by this batch.

## Completed unresolved parameter tests

Nine one-factor variants x 20 fixed seeds at 100k distinct expensive evaluations: 180 new runs / 18 million search queries. Completed 100k baseline controls were reused. The design was committed before these results. Five historical controls also reproduce the cloud20k sequence identities from saved local fitness caches, with zero new objective evaluations. Current initial-population parity and evaluator/model source parity are recorded; the five cached checks are not claimed as exact local replays of every 100k control.

Negative change favors the variant. All intervals below concern GA randomness conditional on the same 64 planning realizations; they do not measure independent physical-validation uncertainty.

| case | mean_change_hr | t95_low_hr | t95_high_hr | bootstrap95_low_hr | bootstrap95_high_hr | bonferroni95_low_hr | bonferroni95_high_hr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| crossover060 | 0.000080 | -0.001015 | 0.001174 | -0.000913 | 0.001079 | -0.001555 | 0.001715 |
| crossover095 | -0.000075 | -0.001003 | 0.000854 | -0.000893 | 0.000794 | -0.001462 | 0.001312 |
| mutation005 | 0.000341 | -0.000666 | 0.001349 | -0.000572 | 0.001258 | -0.001164 | 0.001846 |
| mutation020 | -0.000225 | -0.001233 | 0.000782 | -0.001119 | 0.000712 | -0.001730 | 0.001279 |
| tournament2 | 0.026100 | 0.018448 | 0.033753 | 0.018731 | 0.032531 | 0.014669 | 0.037531 |
| tournament5 | -0.000517 | -0.001428 | 0.000395 | -0.001345 | 0.000330 | -0.001879 | 0.000845 |
| population50 | -0.000487 | -0.001472 | 0.000499 | -0.001360 | 0.000432 | -0.001959 | 0.000986 |
| population250 | 0.000165 | -0.000808 | 0.001139 | -0.000703 | 0.001067 | -0.001289 | 0.001619 |
| population500 | 0.000350 | -0.000681 | 0.001382 | -0.000586 | 0.001299 | -0.001190 | 0.001891 |

Tournament 2 is worse by 0.026100 h on average, simultaneous interval 0.014669 to 0.037531 h. Its median final loss is 33.035544 h versus the baseline median 33.000207 h. Three of twenty seeds numerically improve on their same-seed reference; occasional good searches do not rescue its average performance. This is a reproducible weak-selection failure at this budget, not proof of a universal tournament-size optimum.

Tournament 5 improves in15/20 seed pairs, but the mean change -0.000517 h has pointwise interval -0.001428 to 0.000395 h and simultaneous interval -0.001879 to 0.000845 h. Win frequency and mean effect are different estimands; its suggestive win pattern is not a demonstrated mean improvement after the planned comparison correction.

Population 500 is not intrinsically unsuccessful under the tuned configuration: its mean change is +0.000350 h with simultaneous interval -0.001190 to 0.001891 h. Earlier poor population 500 results cannot be generalized to this warm-start / swap / elite implementation. This study cannot isolate the causes of the earlier behavior or remove population-by-initialization/selection interactions.

## Recommended choices

| parameter | recommendation | reason |
| --- | --- | --- |
| Population | 100 | 50/250/500 conditional mixtures have unresolved mean differences from100 |
| Ordered crossover probability | 0.80 | 0.60 and0.95 do not show resolved superiority |
| Swap mutation probability | 0.10 | 0.05 and0.20 do not show resolved superiority |
| Tournament size | 3 | Size2 is reliably worse at100k; size5 mean advantage remains unresolved |
| Generational elites | 1 | Held fixed in this round; no new elitism claim |
| Initialization | 7/1/25/67 working recipe | Retain disclosed comparison allocation; exact counts/percentages are not established as optimal |

Retaining the reference settings is a stability choice in the absence of resolved superiority, not an assertion of equivalence or optimality. Do not combine separately low-mean settings into an untested supposedly tuned method. The lower mean of tournament 5 and population 50 remains unresolved. The population comparisons follow fixed 7 heuristics and 1 exact prior copy, floor(P/4) inversion neighbors, and random fill: P50 = 7/1/12/30, P100 = 7/1/25/67, P250 = 7/1/62/180, P500 = 7/1/125/367. Thus population size and composition percentages change together.

## Precision and remaining uncertainty

The expected half-width at 20 seeds from the five-seed pilot was 0.003740 h. The stated 0.004 h target was optimizer-estimation precision, not a scientifically approved negligibility margin. Eight final contrasts meet this target pointwise and simultaneously; tournament 2 does not (pointwise half-width 0.007652 h, simultaneous 0.011431 h). Its interval is nevertheless entirely above zero, enough to disfavor it here. Extra seeds were not added after observing a p-value.

All eight other simultaneous mean-effect intervals fall within +/-0.002 h. This is descriptive precision, not a prospective equivalence conclusion: no scientific tolerance was approved. At a +/-0.001 h margin the intervals still do not establish equivalence. A 0.002 h margin cannot be justified only because these intervals fit inside it; its scientific meaning would need to be defended independently of the observed results. Exact percentages and copies therefore remain indistinguishable or unresolved at the relevant unapproved tolerances. Thirty seeds do not certify reliability, tails or physical generalization.

Higher-budget initialization evidence covers only five cases. Warm-copy multiplicity and the full neighbor-source grid were not tested at 100k. True no-prior controls, initialization interactions, joint parameter changes and further-budget rankings remain untested. A valid independent physical validation is still required before a new scientific-performance claim; neither the proposed validation cohort nor the inspected 1000-realization cohort was used for tuning in this round.

The lowest retrieved initialization observation is 32.997722786 h, from `neighbors_0`. Its artifact saves the final sequence SHA-256 but not the chromosome itself. This limits immediate candidate recovery, not initialization-outcome analysis; no completed batch was rerun solely to regenerate the missing representation. Each of the 180 new parameter runs does save its complete best chromosome. Their best is 32.997747754 h (population 50, seed 113); it does not improve the retrieved initialization-study minimum. Neither single minimum establishes a preferable initialization or authorizes formal replacement.

## Cost and preservation

The new searches used 18, 000, 000 expensive evaluations plus 1440 setup-parity scores, 12.379 process-CPU hours and 8.028 objective-CPU hours. Batch wall time was 44.142 min. Per-run records contain actual generations/partial boundaries, attempted evaluations, duplicates, sequences and hashes. Cloud and local wall times are not compared as identical hardware. Controller job counts are not independent observations and are not added together.

The original 834 protected files, revision HEAD, main/July protected references and unrelated staging are preserved. No new physical sampling, no independent-cohort tuning, no formal strategy/candidate replacement and no manuscript-artwork update. Repository tests: 85 passed. The separate diagnostic branch carries the artifacts, uncertainty tables, source/cost audits and recommendations.
