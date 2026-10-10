# Prospective parameter-defense study

Authority: e7d05e2649f3be2ccfbf9398d86e0612407dd5ea. Diagnostic only.
This specification must be committed before any new scientific search.

## Frozen boundary

Use the original 92-station, 64-realization 2pc50/C57_D1 planning
kernel, objective, scheduling, directed travel, mapping and Core-source gate.
No physical sampling. Never read realization-level independent-validation
outcomes for analysis or selection. Historical frozen validation aggregates
may be cited. No formal candidate, manuscript, artwork or Stage 7 changes.

## Evidence reuse

Reuse original records of completed GA initialization, parameter follow-up,
operator screens/confirmations, interaction confirmation, root-cause,
100k/500k alternatives, internal crossfit, LNS and actionable-delay studies.
Deduplicate mirrored artifact representations; retain same-seed budget
checkpoints as repeated measurements, not independent searches.
Existing 0/1 elite evidence does not cover fixed-config 2/3 elites.

## New experiments

Engineering screen: seeds 2026101100-2026101107, 20,000 distinct
evaluations per case, separate empty cache per case. GA: elites 0/1/2/3.
ILS: original equal mix; swap only; insertion only; inversion only;
stagnation 200/2000 versus 800; perturbation schedules 1/2/4 and 4/8/16
versus 2/4/8; current-sequence versus global-best restart; no perturbation;
focused swap/insertion x stagnation200 interactions. This interaction
design is fixed prospectively and is not a full factorial grid.

Independent confirmation: seeds 2026101200-2026101219, 100,000 distinct
evaluations. GA elites 0/1/2/3. ILS equal mix/swap/insertion/inversion,
current-sequence restart, no perturbation, one stagnation alternative
and one perturbation alternative. Select the two latter settings by
lowest screen mean within their respective pairs (exact ties: 200 and
1/2/4), irrespective of statistical significance. Selection is disclosed;
confirmation uses new seeds. No favorable-seed selection or seed extension.
Also run cold GA/ILS equal mix without the optimized prior or prior-derived
neighbors; both retain the same seven heuristic information sources.
Warm GA/ILS use the exact original 33.03813174326729 h prior, NOT the
formal GA or refined ILS candidate. Method-family contrasts share seeds.

No-perturbation search can exhaust a finite neighborhood before the nominal
distinct budget. Apply the same 60*budget attempt cap used by original ILS.
Report incomplete budget explicitly, not as an equal-100k comparison.
This control is intended to diagnose accessibility, not hide exhaustion.

Refinement: first five confirmation seeds, selected before outcomes;
refine baseline ILS 100k finals with the original deterministic four-family
neighbor enumerator, original 1e-9 improvement tolerance and a 150k
additional-distinct-call cap. Count all additional queries and setup
scores. Compare against GA continued from the same seed/RNG/population
state to each achieved joint logical budget (cached prefix replay, zero
new expensive prefix scores), not a fresh GA or uncounted refinement.
If a complete tested-neighborhood scan ends early, stop and report its
actual cost; no global-optimality claim.

## Instrumentation and QA

Record exact permutations/hashes, initial chromosomes and fingerprints,
post-initializer RNG state hash, attempts/cache hits/distinct calls,
generation or proposal counts, accepted moves, restarts, operator-specific
attempts/successes, checkpoints, objective and wall seconds, CPU and runtime.
Store compressed per-run objective caches for reproducible prefix replay.
Observe GA through unchanged engine; instrumentation must consume no RNG.
ILS baseline must reproduce the original implementation on toy and frozen
short-budget parity tests before main execution.
Verify all important new per-configuration minima through the independent
original pandas/NetworkX production path on all 64 planning states;
retain per-state differences, leave-one-out and leave-top-five influence.
New candidates remain postvalidation exploratory, not formal replacements.

## Statistics and decisions

Optimizer seed is the replication unit. Report paired mean/median/SD,
win/loss/tie counts (1e-10 h reporting tolerance), two-sided t intervals,
20,000 seed-block bootstrap intervals and Bonferroni t intervals within
predefined GA elite, ILS confirmation, method-comparison and interaction
families. Bootstrap RNG seed 2026101300. No equivalence margin or p-value
dependent stopping. Compare costs only within comparable local batches;
historical cloud hardware costs remain separately identified.
Reference retention does not imply equivalence or unique optimality.
All newly selected settings are postvalidation exploratory physical research,
even when a contrast is prospectively confirmatory within this diagnostic.

## Execution and preservation

Up to 12 one-thread local workers; do not interrupt unrelated computations.
Snapshot protected revision HEAD, staged binary diff and scientific hashes;
hash frozen validation files for preservation only. Preserve all other
worktrees. Commit and push only this new diagnostic package and scripts;
verify remote HEAD and actual LFS downloads. Stop after completed evidence,
controlled calculations, QA and publication-ready qualified decisions.
