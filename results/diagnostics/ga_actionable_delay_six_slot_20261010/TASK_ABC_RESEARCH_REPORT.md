# Actionable-delay and exact six-slot audit

## Decision

Completed Task A-C with original92 stations,64 physical planning states and unchanged C57_D1 scheduler, source gate, M1 population mass and mean-loss objective. No formal GA replacement and no new physical/validation states.

The complete chosen restricted neighborhoods are tested; this is not a global optimality proof. Group minima and overlapping sets are not independent physical samples or optimizer-seed replications.

## Prospective Registration

Starting remote commit `39d64133b75f7ef528725bfb3bdc7161303c4ed9`. Diagnostic design/code/tests committed at `12fd25a`; all120 exact slot sets and their timing evidence committed at `af13c73` before observing neighborhood minima. Set-file SHA256: `08383d26b83a43ccf8e4c8254dd5df40c93b5ec9531740141187b745c1f26146`.

The helper mentioned in the brief was not supplied. The specified graph construction was implemented and independently passed six tests, including12000 exhaustively enumerated synthetic schedules. Initial setup hit two Windows path-format errors, repaired before the prospective design commit and scientific evaluation. The CRLF byte-preserving evidence attributes initially made Git whitespace checks report CR characters; corrected with cr-at-eol without rewriting any numeric evidence.

## Task A: Lower Relaxation

For damaged tasks S={i:DS_i>0}, dummy-start edges have cost min over actual active origins b[o,i], and directed j-to-i edges have cost p_j+t[j,i], j!=i. Dijkstra gives a_i; c_i_lower=a_i+p_i. DS0 nodes cannot be waypoints. Any actual crew route to i is a path in this graph with the same preceding repair times and directed travel, plus nonnegative idle time. Therefore shortest arrival is no later than actual arrival. Independent routes relax resource competition and generally cannot coexist in one feasible schedule.

Direct depot arrival is an upper candidate for shortest relaxed arrival, not a general lower bound. First-wave tasks can retain origin-assignment improvement room. Nonnegative finite duration/travel and a completion-only monotone model are verified assumptions. All crew origins are drawn from the actual active roster, not every potential depot.

All17598 reference task/state completion inequalities pass at1e-8h. Original source-gate evaluation checks64 route envelopes and64 duration-only envelopes. Maximum diagnostic/authoritative value discrepancy=2.867e-12h. Ordinary doubles with disclosed tolerances, not outward-rounded interval-certified decimals.

Earlier completions weakly increase raw functionality, threshold-active nodes and source-connected components. Nonnegative dependency mass then weakly increases effective service and decreases the original loss. This establishes analytical admissibility of the simultaneous envelope but not a feasible policy. It is never inserted into formal strategy results.

The minimax source-connectivity time C_i gives an independent formula check: DS0 loss=C_i; DS1 loss=0.5 C_i+0.5 max(C_i,c_i); DS2+ loss=C_i, since C_i>=c_i. Terms are horizon-clipped and population weighted. This formula is diagnostic only and independently checked against the original functionality/NetworkX gate.

Duration-only unlimited-crew zero-travel loss=31.360999855947h. Independent-route loss=31.514846689664h; tightening=0.153846833717h.

| Parent | Feasible mean J (h) | Incumbent minus route relaxation (h) | First-wave task/state observations with headroom |
|---|---:|---:|---:|
| shared_prior | 33.038131743267 | 1.523285053604 | 2806 |
| frozen_ga | 32.997840773883 | 1.482994084219 | 2454 |
| refined_ils | 32.996137365389 | 1.481290675725 | 2404 |

A remaining1.48h relaxation gap is not a promise that a single shared priority order or57 finite crews can realize it. No maximum-direct-travel substitute or horizon change was used.

## Task B: Actionable Opportunities

STATION_STATE_ACTIONABLE_DELAY.csv retains all three parents x64 states x92 stations: repair, arrival, release, predecessor, active-origin index, travel, dispatch, first-wave status, relaxed completion, headroom and exact single-station optimistic service screen. ACTIVE_ORIGIN_LOOKUP.json resolves numeric base-row indexes to origin names and the original57-crew roster; only actual active origins are admissible.

ACTIONABLE_DELAY_STATE_MAP.png shows the top25 station/state diagnostic screens per parent, marking state15. Screens are infeasible interventions: changing one completion while holding all others fixed need not be schedulable, is not a causal feasible effect, and gains must not be summed. Slot sets may include zero-headroom donors/enablers.

Old dominant warm-start bundles300493/307693 and300493/303620/307693 have zero headroom in every damaged observation under the admissible route construction. Bundle306768/307693 has mean0.0345414h and max0.0690828h headroom. This supports irreducible-duration diagnosis for those specific bundles without declaring all first-wave tasks unchangeable.

| Parent | Highest single-screen station | Mean optimistic gain (h) | Supporting states | State15 fraction |
|---|---|---:|---:|---:|
| shared_prior | 306489 | 0.072610720 | 64 | 0.0111 |
| frozen_ga | 306489 | 0.070279951 | 64 | 0.0115 |
| refined_ils | 306489 | 0.072459062 | 64 | 0.0125 |

All64 and without15 rankings/headroom/support are retained. State15 is never excluded from feasible fitness. Interacting opportunities include queue predecessors, co-witness gateway activation, and first-wave origin donors; high mass/source waiting alone is not actionable-delay evidence.

## Task C: Complete Restricted Enumeration

Top20 all64 optimistic-screen centers per parent, weighted predecessor/donor/co-witness inclusion, deterministic ranking fill/diversity, and20 uniform random six-position controls per parent were pinned prospectively. Random controls match the target count in three priority-rank bands, not voltage/degree/repair severity. Cases with no causal donor are filled by opportunity rank. Same six occupied positions and remaining86 fixed positions are checked for all720 permutations. No beam or intermediate-score pruning.

| Parent | Arm | Improving sets /20 | Mean gain (h) | Maximum gain (h) | Best conditional J (h) |
|---|---|---:|---:|---:|---:|
| shared_prior | targeted | 7 /20 | 0.000428433078 | 0.006168417875 | 33.031963325392 |
| shared_prior | random_control | 2 /20 | 0.000035418853 | 0.000584103999 | 33.037547639269 |
| frozen_ga | targeted | 0 /20 | 0.000000000000 | 0.000000000000 | 32.997840773883 |
| frozen_ga | random_control | 0 /20 | 0.000000000000 | 0.000000000000 | 32.997840773883 |
| refined_ils | targeted | 0 /20 | 0.000000000000 | 0.000000000000 | 32.996137365389 |
| refined_ils | random_control | 0 /20 | 0.000000000000 | 0.000000000000 | 32.996137365389 |

Each archive retains720 full92-ID assignments and exact original-kernel scores. Every parent is included. Certificates apply only to the120 pinned slot sets and1e-9h arithmetic improvement tolerance; no claim about arbitrary six-slot sets, every neighborhood or global optimality. Numerical ties retain the parent for auditing.

## Production Parity And Influence

All11 unique restricted optima passed original production evaluator across64 states (704 sample calls). Maximum compiled/production discrepancy=3.432e-12h.

Complete sequences and SHA256 identities: CANDIDATE_PRODUCTION_INFLUENCE.json. Per-state values: CANDIDATE_PER_STATE_PARITY.csv. Every candidate has comparison to shared prior, frozen GA and refined ILS, full leave-one-out reversals, removal of1/2/4/8 most beneficial states and without15 sensitivity. Those removals are diagnostic, never a changed objective. Candidate schedules retain origin/predecessor/travel/completion/source timing; event decompositions are descriptive accounting of whole schedules, not causal claims about one station.

Best restricted optimum J=32.996137365387h, SHA256 `75a1014c7f921c09b574eed4eebcaa412f86fcbc61487bf4a1277c4eb448ddbd`.
Compared withfrozen_ga: delta=-0.001703408495h; improves14/64, worsens50/64; without15 delta=+0.030758169261h; LOO reversals=[4, 13, 15, 39, 40, 55, 57].
Compared withrefined_ils: delta=-0.000000000001h; improves0/64, worsens0/64; without15 delta=-0.000000000001h; LOO reversals=[].

### Best Warm-Start Counterexample

Targeted set11 reaches33.031963325391h, improving the older warm start by0.006168417876h. SHA256 `b14f54cb83464d711ec8739e55e740e6f4687fb863de219c27c178edab76c511`. It improves55/64 states, worsens9/64, median delta=-0.003115868359h. State15 actually worsens by+0.001716197256h; excluding it yields-0.006293570498h. No leave-one-out reversal, and removing the eight most beneficial states still yields-0.004009372055h.

This remains+0.034122551508h worse than frozen GA and+0.035825960002h worse than refined ILS. Thus the7/20 versus2/20 targeted/control result is limited to recovering a weak-parent deficit, not evidence of superior optimization of current incumbents.

Exact all64 whole-schedule decomposition versus prior: self=-0.002599277340h, threshold=-0.000085823440h, source=-0.003483317095h; sum=-0.006168417875h. Mean directed crew travel change=-0.152448541604h; mean earlier/later station completions=2.875/0.469. BEST_PRIOR_MECHANISM.json retains all64 event accounts, changed occupied positions, individual headroom, source timing and candidate influence. This is attribution of the entire feasible schedule difference, not causal identification of a single donor/gateway.


## Computation Accounting

Task A-B wall=6.119s (analysis phase only). Task C wall=131.408s;86400 assignment observations;84964 new exact64-state mean calls;1436 reused assignment observations. Imported original checkpoint cache has132545 entries, SHA256 `d56ac7ac367ceede066d16e805a0eae30f1c373c701a3ade56a49c8e1c09b2e4`. No refined-ILS single-move scan was repeated.

Candidate parity/annotation phase wall=11.212s. Each load() performs8 fixed-rule/prior mean parity calls outside neighborhood accounting. Audit,select,exact,candidates,mechanism each invoke it once:40 setup means. Audit also checks3 parent means and192 compiled reference sample calls. Candidate verification makes704 compiled sample calls as well as the same number of original production sample calls; it also performs192 reference sample calls. Best-prior mechanism adds128 native component event evaluations and128 decodes, zero feasible fitness calls. Candidate/event summary decoding includes120 x128=15,360 per-set native decodes, plus annotated improving candidates and event comparisons. Analysis/report source-minimax/native-only decodes and17,598 single-completion screens are not feasible-chromosome fitness calls. Cold imports and failed engineering setup are additional overhead. Original cached132,545 objective calls are historical, not new computation.

No stochastic optimizer campaign,500k extension, physical resampling, external validation or candidate promotion performed. Exact conditional coverage is a diagnostic budget, not independent-run statistical power.

## Next Decision

No tested six-slot assignment improves frozen GA or refined ILS. Retain those restricted certificates and the nonzero global relaxation gap. Do not expand the failed unchanged LNS to500k or launch a weight-only retuning campaign. Any later expansion needs evidence that a larger coordinated slot/origin reassignment can access actual residual scheduling delay, with prospective controls. A relaxation gap alone does not establish that such feasible opportunity exists.

## Preservation And Reproduction

950 protected revision file hashes, revision branch/HEAD/staged binary-diff and all original kernel input hashes are checked again before publication.13-condition validation-readiness addendum remains identical. Diagnostic plots reside only here; manuscript/formal strategy output remains untouched.

```powershell
$env:PYTHONPATH='src'
$env:NUMBA_CACHE_DIR=Join-Path $env:TEMP 'delay3-20261010-numba'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMBA_NUM_THREADS='1'
python -m unittest discover -s tests -p test_actionable_delay_20261010.py -v
python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task audit
python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task select
# Pin and commit the selection file before executing exact.
python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task exact
python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task candidates
python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task mechanism
python -m la_grid.diagnostics.ga_actionable_delay_report_20261010
python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task preservation
```

The exact command resumes and reuses cached completed sets. Preserve pinned files when reproducing; do not overwrite them after seeing minima. Setup hydration needs the original checkpoint LFS/blob object and protected revision path recorded in SETUP.json.
