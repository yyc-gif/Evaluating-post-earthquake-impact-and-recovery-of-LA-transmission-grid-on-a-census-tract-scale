# Noncontiguous connectivity LNS: prospective local experiment

Starting authority: `79ac982afeb09fdfb3b79d8579208f4cda4c0133`. Diagnostic only.
This document and algorithm are committed before confirmation outcomes.
An initial engineering invocation started after a failed commit (missing local
Git author identity). It failed at bank-log serialization before a new LNS
proposal. The keyword collision was corrected; no algorithm choices, seeds,
budgets or comparisons changed. Any completed reference smoke records from
that invocation are retained and identified in the execution journal.

## Mechanism

The native earliest-free-crew scheduler decodes each of the original 64 samples.
At threshold 0.5, DS0/DS1 activate at time zero; DS2+ activate at completion.
A minimax path from the 14 Core sources gives each station's earliest source
connection and a witness path. A disconnected, already-functional target
contributes population dependency mass times its source-wait interval. Delayed
stations on its witness form a 2-4 station proposal, including a queued
gateway's immediate crew predecessor where present. These are scheduling
witnesses, not asserted causal or globally minimum cut sets. Alternate paths
are accounted for by the minimax search. Scores aggregate all 64 samples;
support, sample-15 share and leave-15 score are retained. No sample is omitted
from fitness. Credit for initially DS1 targets is conservative half credit.

Rebuild top-128 weighted bundles every 10,000 distinct fitness calls. Only
proposal construction uses these weights. The exact original mean population
loss, original directed travel, durations, source gate and full 92 permutation
remain authoritative. A witness may change after repair; every trial is scored.

Destroy/repair is independent station relocation with a width-three beam.
Each move tests its current slot, slot zero, a station-specific favorable
first-wave base/crew slot, a uniform random slot, and +/-8 or +/-20 slots.
All intermediate candidates are full 92 permutations. Joint moves can retain
temporarily harmful branches; no contiguous bundle requirement is imposed.
Thirty percent of macros use the unchanged equal swap/insertion/inversion
mixture. Strict acceptance tolerance 1e-9 h, neutral acceptance probability
0.15; stagnation 800 distinct calls triggers original ILS-style 2/4/8 kicks
of best-so-far. Archive preservation is distinguished from current acceptance.

Controls use identical beam/slots/acceptance and bundle-size distribution:
uniform random damaged stations; or population-times-native-completion
weighted damaged stations without connectivity identities. The common size
distribution is derived from the same all-64 bank. Thus the random control is
size-matched, not fully free of topology information. GA and ILS call existing
reference implementations unchanged. Every method receives the older common
33.03813174326729-h prior plus seven rules, scored within its own budget.
The frozen GA and refined ILS are comparators only, not initialization priors.

## Frozen execution and analysis

- Engineering seeds 1180,1181: 1,000 distinct calls per method. Correctness only.
- Confirmation seeds 1200..1219: 100,000 DISTINCT exact calls per method;
  five methods, 100 observations. Attempted calls, duplicates, accepted moves,
  archive improvements, checkpoints, wall time and complete final sequences
  retained. Completed original studies reused, never rerun.
- Four primary paired contrasts: connectivity minus random, scheduling, GA,
  ILS. Bonferroni t 95% simultaneous intervals (family four); pointwise paired
  bootstrap 20,000 resamples, RNG 2026101012. All ten pairwise contrasts are
  secondary with family-ten intervals. Paired by optimizer seed, conditional
  on fixed previously inspected training samples; not external validation.
- Larger-budget gate: any new method has mean loss below BOTH GA and ILS
  with >=12/20 wins against each, OR any new method finds a candidate more
  than 1e-6 h below the refined ILS 32.996137365-h benchmark. Then all five
  methods run 500,000 distinct calls on new seeds 1300..1309. No gate means
  no redundant unchanged 500k run; conduct proposal/repair failure diagnosis.
- Every method's best confirmation candidate, and any better-than-refined
  candidate, receives independent production-path evaluation of all 64
  states. Compare with frozen GA and refined ILS, sample-wise wins, quantiles,
  leave-one-out and leave-15, and largest adverse/improving states. Selection
  is diagnostic; do not replace formal GA or retrospectively change objective.
- Parallel worker wall is reported separately from serial-equivalent worker
  totals. Initialization parity and final verification calls are separately
  acknowledged outside distinct search counts. Native bank decodes are not
  objective calls. Code/protocol hashes and execution commit are retained.
- A fixed validation-readiness addendum adds Centrality-first, Closeness-first,
  and refined ILS secondary. NO 2,000 new physical samples are generated.

## Original negative mechanism

Prior v1/v2 proposals concatenate up to eight stations into one block; this
changes first-wave assignment to a deterministic 57-crew roster, directed
travel and queued predecessors even when bundle members are geographically
unrelated. Their witness is from a component *after* reconnection, so includes
already-functional and non-bottleneck nodes. Best of up to 36 such repairs
never beats either fixed parent in the 1,024 completed paired macros. This
rules out cross-realization transfer as the sole failure mechanism, but does
not establish station-specific causality. The new minimax timing witnesses
and independent repair directly test that structural proposal limitation.
