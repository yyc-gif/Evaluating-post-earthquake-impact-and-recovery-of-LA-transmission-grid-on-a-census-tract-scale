# Final elitism decision

**ADOPT POST-EVALUATION WORST-OFFSPRING ELITISM**

The source retains legacy as the backward-compatible default. Adoption, if recommended, applies to a future explicitly configured scientific workflow, not automatic replacement of its already validated sequence. Both modes remain independently executable.

## Empirical endpoint results

Negative POST-minus-LEGACY means lower loss. Replication is paired optimizer seed, not generations or budget checkpoints.

- 100,000 distinct: n=20; legacy mean/median/SD 33.000555071/33.000759988/0.003396706 h; POST 32.999251484/33.000229953/0.002560460 h. Paired mean delta -0.001303587 h; adjusted95% [-0.003400358,+0.000793184] h; wins/losses/ties 10/10/0. Median wall ratio 0.9825.
  Mean completed-generation delta -208.85; entropy delta +0.006228; unique-survivor delta +4.15; offspring-attempt delta -20904.95.
- 250,000 distinct: n=10; legacy mean/median/SD 33.001211232/33.000927143/0.002663508 h; POST 32.999830503/33.000035684/0.001868870 h. Paired mean delta -0.001380729 h; adjusted95% [-0.004580351,+0.001818893] h; wins/losses/ties 6/3/1. Median wall ratio 0.9637.
  Mean completed-generation delta -1296.70; entropy delta +0.003168; unique-survivor delta +6.70; offspring-attempt delta -129684.60.
- 500,000 distinct: n=10; legacy mean/median/SD 33.001211232/33.000927143/0.002663508 h; POST 32.999768633/33.000035684/0.001994487 h. Paired mean delta -0.001442599 h; adjusted95% [-0.004674689,+0.001789491] h; wins/losses/ties 6/3/1. Median wall ratio 0.9166.
  Mean completed-generation delta -4917.50; entropy delta +0.017172; unique-survivor delta +13.60; offspring-attempt delta -491754.30.

Primary 100k is one predeclared contrast. The 250k/500k family has two endpoints with Bonferroni simultaneous intervals; an all-three-endpoint conservative family is additionally provided. Paired bootstrap intervals and complete best/worst statistics are in the companion tables. A zero-crossing interval is not equivalence. All seeds and negative outcomes are retained.

The reasoned engineering choice is to remove blind, unscored deletion while retaining exactly the same scientific objective and distinct-evaluation ceiling. The observed mean differences favor POST, but none establishes empirical optimization superiority. This choice does not imply that every seed improves, that the algorithms are equivalent, or that the diagnostic sequence should replace the validated formal candidate.

### Within-trajectory marginal gains

- LEGACY, 100,000 to 250,000: 6/10 seeds improved; mean gain 0.000158230 h; 1,500,000 additional distinct calls; mean added objective time 198.23 s and checkpointed engine wall time 310.82 s.
- LEGACY, 250,000 to 500,000: 0/10 seeds improved; mean gain 0.000000000 h; 2,500,000 additional distinct calls; mean added objective time 341.60 s and checkpointed engine wall time 584.73 s.
- POST, 100,000 to 250,000: 4/10 seeds improved; mean gain 0.000337820 h; 1,500,000 additional distinct calls; mean added objective time 198.35 s and checkpointed engine wall time 291.98 s.
- POST, 250,000 to 500,000: 2/10 seeds improved; mean gain 0.000061870 h; 2,500,000 additional distinct calls; mean added objective time 340.96 s and checkpointed engine wall time 516.90 s.

These are repeated measurements of the reserved ten pairs. The 100k mean over all twenty seeds must not be directly compared with the higher-budget mean over ten different-sized cohorts as a marginal treatment effect.

## Mechanism and nine requested answers

1. At100k, legacy overwrote 93/78855 generated last children (0.1179%) that retrospective unchanged fitness shows were strictly better than the previous elite. 20151 were unscored at the moment of replacement. Complete versus terminal-partial events are separately recorded. These are events, not independent trials.
2. POST removes only a scored worst child no better than the previous elite: 0 stronger discarded children. At100k, insertion/presence/all-better counts are 27931/46728/0. The last-child opportunity is preserved; every valid observation still enters best-observed.
3. The matched algorithm comparison measures the aggregate later-search consequence; it does not identify any individual retained child as the cause. Selection and sequence trajectories may diverge after survival differs. Random-draw rules remain unchanged; the stream can remain matched at the same operator generation, while distinct-budget endpoints can stop at different generations/RNG states. Endpoint intervals determine evidence for advantage; engineering correctness alone cannot prove it.
4. Paired survivor uniqueness, normalized position entropy and positional Hamming are reported above and per seed. Metrics refer to the last completed population, never an unfinished proposal. Diversity is descriptive rather than proof of search quality.
5. Both consume exactly the same distinct objective budget, including100 initial chromosomes. Scoring the last child does not add expensive calls beyond that ceiling: it redistributes work and may reduce completed generations. Attempted/cache queries and wall/objective time are separate. Retrospective discard auditing added 54,423 separate fixed-planning calls (3,483,072 state kernels), excluded from all optimizer budgets. Median wall ratios above are operational observations from the same12-worker machine, not platform-independent speed claims.
6. Paired improvement frequencies and uncertainty above answer consistency. No assertion is made that every run improves or reaches the same sequence.
7. The first ten prospectively reserved states, not freshly restarted searches, supply higher-budget evidence when the registered gate allows continuation. Budget checkpoints share seeds and are not new replication. Marginal gains and incremental costs are recorded independently. No further favorable-result extension is permitted.
8. POST remains a simple permutation GA: the same100random initialization, OX.80, Swap.10, Tournament3 and one current-generation elite, with conditional deterministic survivor replacement and a passive output archive. No local search, adaptation, restarts or incumbent injection.
9. Decision follows the prospective rule: wholly adverse adjusted endpoint=False; all median wall ratios<=1.5=True. Engineering preference and empirical superiority are kept separate. This yields **ADOPT POST-EVALUATION WORST-OFFSPRING ELITISM**.

## Computation and failed-attempt accounting

There are 40 fresh searches (20 matched seed pairs), followed by 20 continued trajectories at each higher endpoint: 80 endpoint records, not 80 independent searches. Incremental search accounting totals 12,000,000 distinct objective evaluations and 768,000,000 fixed-planning-state kernels.

Two sandboxed post-search audit attempts terminated with exit code 1 and no traceback. The first lost its in-memory score map: it performed at least 27,100 and at most 49,861 additional fixed-planning calls; its exact total is unavailable. The second persisted completed scores and the successful host-resource retry reused them. Its calls are included once in the 54,423-call persistent audit ledger. No completed optimizer batch was rerun. The termination cause is unconfirmed. Preliminary unit-test path errors and the eventual eight-test pass are separately documented.

Wall ratios use accumulated engine elapsed time from checkpoints; they exclude final run export and evidence ZIP packaging. Incremental phase and whole-batch wall times include their respective export/startup work and are recorded separately. Objective-scoring time, attempted calls, cache hits and expensive distinct evaluations are not interchangeable. No aggregate wall-time figure is labeled CPU time.

Git LFS staging subsequently encountered insufficient disk space. After verifying all five members of each current runtime against its preserved archive, only the forty ignored run-directory copies were removed. All eighty raw endpoint archives remain intact and restore exact continuation state. Resolved-path checks and hashes are in REDUNDANT_RUNTIME_CLEANUP_QA.json; no original data, previous package or protected checkout was cleaned.

## Candidate boundary

Best POST development sequence: seed 2026121110, 100,000 distinct, native64-planning loss 32.995220412411 h, SHA256 `46732e49c3afa0827cdf37543882b3ec3f06ab0a3f600eedd92162733fa5ee82`. Full92-station order, state lineage and native per-realization results are archived. Old frozen legacy loss32.99552241352315 h and SHA edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a remain unchanged. Their prior2,000-sample validation is not transferred.

No physical sampling, old independent-validation outcome analysis, manuscript, official figure, Stage7, source-gate, scheduler, objective, travel/crew, mapping or repair-duration changes occurred. A proposed validation plan is readiness only and cannot be executed without authorization.
