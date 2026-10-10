# Prospective scheduling-aware LNS experiment on frozen LA 92-station planning objective

Parent: [GA consolidated research commit `409693a68a099e6c1ec2fee093b3bfd2ecf80dd6`](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/commit/409693a68a099e6c1ec2fee093b3bfd2ecf80dd6).

This design precedes execution of the newly selected LNS seeds. There are no newly sampled earthquakes, no modification of the original exact objective, physical damage states, directed travel, C57 depot roster, network, source gate, population mapping, formally selected restoration sequence, or untouched proposed 2,000-realization cohort.

## Why the experiment is warranted

Existing 500k GA tournament3 and tournament5 stop improving after 250k in ten seeds, whereas ILS improves in seven of ten seeds during 250k–500k. Full 64-sample ILS-refined minimum is lower than frozen GA but dominated by conditional source reconnection and high leverage of realization 15. Four-fold internal crossfit reveals ranking reversals. These facts do NOT prove GA inferiority, ILS superiority or global optimization.

A genuinely different candidate-generation mechanism may address delayed source connections. Standard local moves change one/two positions or short blocks; a route/connected-component gateway often requires *joint* changes to several tasks to preserve a path to a Core source. Network/schedule-aware LNS is untested, unlike existing neutral drifts, ILS, simple GA/local hybrid, and deterministic one-move neighborhoods.

## Algorithms, predeclared design and fixed seed blocks

Four methods, all exactly **100,000 distinct expensive evaluations per search** on the same **64 fixed planning realizations**:

- `ga_baseline`: existing P100, OX=.8, swap mutation=.1, tournament=3, elite=1, quality_mix initializer; exact original engine.
- `iterated_local`: original equal-budget ILS from the same inherited GA best with swap/insertion/inversion, cyclic 2/4/8 perturbations; exact original implementation.
- `lns_event_route`: original scheduler decodes current chromosome on 4 randomly selected frozen planning states. Event-reconnection gains under the original 0.5-Core-source eligibility gate generate actual source-to-gateway routes and newly connected restoration station bundles of up to 8. The bundle is removed from the 92-chromosome and reinserted as one block at an earlier/random valid insertion position. Candidate quality scored **only** by original exact mean service-loss kernel.
- `lns_random_bundle`: same LNS scoring, acceptance, restart, event refresh and bundle sizes, but select the same number of **damaged tasks from the same selected planning state uniformly** rather than select the source-restoration route. This control tests whether information-targeted bundles matter beyond large multi-station perturbations.

Both LNS variants:
- start with identical seven heuristic scores and exact inherited older warm-start sequence (`3bfeafdd1adf950749e63fdbbe3b7efc21b1efd04c3b3d64c28c3d118717bbed`) as GA and ILS;
- require strict objective gain (>1e-12) to accept beneficial candidates and use probability=.15 to traverse neutral plateaus (|\Delta J|\le1e-9);
- rebuild event-route proposal bank every 2,500 distinct candidates or after relevant accepted path changes, choosing 4 of the existing 64 planning states each time, never using a validation cohort;
- use cyclic 2/4/8 local perturbations after 1,200 attempted proposals without strict improvement; such perturbed candidates are **metered when scored**;
- count every distinct expensive objective evaluation, record repeated attempts, note unmetered event-proposal computation in actual elapsed wall time, save final complete 92-station chromosomes and hashes;
- do not use the heldout dataset or any final validation sample for tuning.

**Sanity screen:** four new seeds 800–803 × four methods × 20,000 expensive distinct queries (320,000 search scores). Used to verify program correctness, exact budget and source-path construction; no parameter selection from pilot.

**Primary comparison:** 20 additional new seeds 820–839 × four methods × 100,000 distinct queries (8,000,000 scores). Precommit fixed construction and settings *before* the screening results; 20/50/100k checkpoints are descriptive within each 100k run, **not separate seed replicates**. A common seed means paired comparison of algorithm RNG, **not identical random trajectories**.

Primary effects (lower is better): `lns_event_route - iterated_local` and `lns_event_route - ga_baseline` final 100k loss on the same seed. Secondary mechanistic contrast: `lns_event_route - lns_random_bundle`. Summarize mean and median paired differences, across-seed SD, 95% paired t intervals, 30,000 seed-resample bootstrap intervals, three-contrast Bonferroni simultaneous t intervals, empirical paired wins, best/worst seed, distinct/attempted evaluations and wall times. Interpret as optimizer RNG uncertainty conditional on the *same reused 64 physical realizations*. Do not treat non-significance as equivalence; no research-approved scientific negligibility margin exists.

Mechanistic diagnostic: report distribution of proposed bundle sizes, sampled reconnection events, accepted strict/neutral moves, and resulting schedule phenotypes for selected candidates. Re-score any novel best sequence independently using the production pandas/NetworkX path before trusting it, and compute per-realization influence/leave-one-out sensitivity against formally frozen candidate. A new best in mean J does not imply out-of-sample superiority.

## Validation and continuation boundaries

- All scenario files/model/evaluator remain immutable. New optimization runs use no 2,000 fresh validation states; no new sampling or formal strategy replacement.
- Source paths are *unweighted topological reachability witnesses*, not measured electrical flow or necessarily unique connection cut sets; event-informed proposals are heuristic and may be wrong. Their output nevertheless remains a feasible full permutation and is scored against the original objective.
- This predeclared LNS cannot claim superiority over all possible scheduling-aware methods. If it underperforms, examine whether bundles were used/accepted, whether the random control is comparable, and whether its event signals capture network behavior before discarding the approach.
- Do not select the method based on a single lowest planning loss, or inspect independent holdout to select a sequence. A robust mean advantage is necessary but is still conditional on training realizations; full independent validation requires separately frozen candidates and a one-time prospective test.
- If a method-specific result is dominated by realization 15, report the exact sensitivity. No outlier should be removed from the original J to make a newly found method look favorable.
- Completed historical cloud GA and ILS results can be cited for context but are not counted as new independent seeds in these precommitted 820–839 comparisons.
