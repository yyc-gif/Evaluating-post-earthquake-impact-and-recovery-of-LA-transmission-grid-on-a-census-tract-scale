# Local noncontiguous connectivity LNS investigation

## Decision

Completed the archived-study audit, five-method 20-seed local comparison, engineering checks, bounded mechanism probes, independent all-64 production parity, sample-influence audit, and validation-readiness addendum. No formal policy, physics, planning sample, revision output or artwork was replaced.

The tested connectivity-targeted insertion beam is not a better optimizer. Source-wait importance does not imply removable dispatch delay. The exact negative results are retained; they do not prove that every connectivity-aware optimizer would fail.

## Authority and prospective design

- Starting remote branch: `diagnostics/scheduling-aware-lns-20261010`, commit `79ac982afeb09fdfb3b79d8579208f4cda4c0133`.
- Isolated standalone checkout and branch: `diagnostics/noncontiguous-connectivity-lns-local-20261010`.
- Confirmation algorithm/design committed at `6de7efa` before any 100k case; bounded adaptive failure probe committed at `e69d0c9` before its outcomes.
- Preserved original July92/318-edge/14-Core, C57_D1, 2pc50, 64 planning states, directed travel, realized repair durations, M1 population mapping, 0.5 gate and mean-loss objective.
- Original planning horizon: 2855.2540131100995 h. This normalized population-weighted service-loss integral is not wall-clock recovery time or T80.
- Shared older prior J=33.03813174326729 h plus seven rules, charged within every search budget. Frozen GA/refined ILS were not injected as priors.
- Seeds1200..1219, 100,000 distinct full-permutation exact evaluations per method. Full seed records and SHA-256 identities: `ALL_FINAL_PERMUTATIONS_100000.json` and `SEED_LEVEL_100000.csv`.
- First engineering invocation followed a failed Git commit due missing local author identity. The new-arm smoke invocation failed at bank serialization before LNS proposal construction; four reference smoke results completed and were retained. The collision was repaired, identity configured, and algorithm committed before successful new-arm smoke and all confirmation runs. No seed or algorithm-performance decision used these smoke outcomes.

## Archived evidence, not reruns

Official original runs: [LNS v1](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38033702030), [LNS v2](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38034064901), [160-outcome audit](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38065463263), [proposal transfer](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38065546076). Original ZIPs, GitHub artifact digests, extracted-member hashes and run commits are retained in `ORIGINAL_ACTIONS_MANIFEST.json`.

All160 full-budget observations pass original92-ID, 92-unique permutation, checksum, seed, exact100k budget and completion checks. Smoke/checkpoints are not additional independent optimizer observations. All8 transfer seeds pass, with2,048 arm-level observations /1,024 paired macros; no completed optimizer was rerun.

Existing three-primary-contrast family is distinguished from two secondary contrasts. `ORIGINAL_160_AUDIT.json` also gives family-five simultaneous intervals; this avoids describing all five old contrasts as a simultaneous family-three result.

| Parent | Old repair | Origin improved /512 | Mean64 improved /512 | Replayed first-wave origin changes | Earlier / later completions |
|---|---|---:|---:|---:|---:|
| prior_optimized_warm | lns_repair_route | 37 | 0 | 9.875 | 7.750 / 14.125 |
| prior_optimized_warm | lns_repair_random | 45 | 0 | 8.500 | 9.500 / 22.750 |
| frozen_formal_ga | lns_repair_route | 23 | 0 | 8.625 | 6.125 / 20.625 |
| frozen_formal_ga | lns_repair_random | 36 | 0 | 9.625 | 6.000 / 24.500 |

Replay covers macro0 for each8 seeds, each2 parents and2 arms, locating the archived best candidate by hash without any objective reevaluation. Raw crew-label changes are larger, but same-origin crews may be interchangeable. Origin, predecessor, travel and completion differences are retained separately. These whole-proposal comparisons do not isolate a causal effect of one moved station.

The old repaired witness is collected after reconnection and may include already-functional or non-bottleneck members. A rigid block alters other priorities, crew origins and downstream routes. Since most proposals fail their own originating state as well, negative cross-state transfer alone cannot explain the failure.

## New mechanism and correctness

All64 native schedules supply activation times. Minimax source paths account for alternative source routes; delayed path nodes plus queued predecessors form2-4-station bundles. Population dependency mass times source waiting is aggregated over64 states. A width-three beam relocates each member independently; every intermediate chromosome is a full92 permutation. Random-damaged and population-completion controls use the same size distribution, slots and repair effort. This random control inherits the size distribution from the connectivity bank, not its station identities.

The original gate constrains every fitness value; a truncated witness bundle does not guarantee a particular component reconnects earlier. Source-wait weights are proposal heuristics, not a changed objective or a proof of causal gateway leverage. DS1 target-credit weights are conservatively half credit.

Minimax reachability matches native graph components at 5,877 event points across all64 states. Four unit tests cover delayed sources, bypass routes, no sources, full-permutation repair and relative-order preservation. The static context audit verifies78 source-to-non-Core minimum internal vertex separators on a copied graph; cut-size counts are `{1: 8, 2: 14, 3: 6, 4: 4, 5: 7, 6: 9, 7: 8, 8: 4, 9: 1, 11: 15, 12: 2}`. These are one representative separator per target, not every cut or a time-dependent causal repair plan.

## Completed 100k comparison

| Method | Mean J (h) | SD (h) | Best J (h) | Mean attempts | Mean worker search wall (s) | Accepted current improvements | Archive improvements below prior |
|---|---:|---:|---:|---:|---:|---:|---:|
| connectivity_lns | 33.031680766 | 0.005099343 | 33.018110793 | 142836 | 197.07 | 938.85 | 11.05 |
| random_lns | 33.021690867 | 0.005656047 | 33.007326958 | 133846 | 196.16 | 1044.55 | 34.75 |
| scheduling_lns | 33.026049833 | 0.005442083 | 33.013013921 | 135981 | 199.56 | 1037.45 | 23.35 |
| ga_baseline | 33.000197932 | 0.001716231 | 32.998356671 | 821102 | 305.88 | not recorded | not recorded |
| iterated_local | 33.000735033 | 0.002654852 | 32.996287059 | 101023 | 193.91 | 1499.20 | 80.70 |

GA reference wrapper does not serialize its best-path/acceptance counters; these are unavailable, not zero. A population GA has no directly comparable single-current acceptance count. The unchanged reference was not rerun to invent missing history.

| Primary pair (connectivity minus reference) | Mean delta (h) | Family-four 95% simultaneous interval | Connectivity wins / losses / ties |
|---|---:|---:|---:|
| connectivity - random_lns | +0.009989900 | [+0.005793460, +0.014186339] | 2 / 18 / 0 |
| connectivity - scheduling_lns | +0.005630933 | [+0.000443636, +0.010818230] | 6 / 14 / 0 |
| connectivity - ga_baseline | +0.031482835 | [+0.028346246, +0.034619423] | 0 / 20 / 0 |
| connectivity - iterated_local | +0.030945733 | [+0.027526325, +0.034365142] | 0 / 20 / 0 |

Secondary GA-minus-ILS mean=-0.000537101 h, family-ten interval=[-0.002845295, +0.001771093]. All ten secondary paired comparisons and pointwise bootstrap intervals are supplied in `BUDGET_100000_SUMMARY.json`. Intervals concern optimizer seeds under this reused training model; an interval crossing zero is not equivalence or external robustness.

## Why this new repair still struggles

The all64 bank is not uniformly cross-state consensus: retained bundles have mean support 1.828/64; the weighted sample15 share is 3.353%, and top10 membership overlap without15 is 10/10. Thus sample15 does not dominate this initial proposal bank, while many exact bundle combinations remain state-specific.
- `300493,307693`: support=16/64, DS2+ first-wave fraction=1.0000, mean relaxed queue/travel-delay fraction=1.90888e-17.
- `300493,303620,307693`: support=14/64, DS2+ first-wave fraction=1.0000, mean relaxed queue/travel-delay fraction=2.11968e-17.
- `306768,307693`: support=7/64, DS2+ first-wave fraction=1.0000, mean relaxed queue/travel-delay fraction=0.001511.

The highest weighted witnesses largely have irreducible sampled repair durations and already-favorable first-wave origins. Moving them earlier in the priority list cannot remove those durations. The relaxed independent-origin benchmark is not a feasible schedule or a certified bound, especially when a later directed inter-task leg can be shorter.

Insertion repair still shifts intervening ranks even though its bundle is noncontiguous. Width-three pruning may also omit useful jointly harmful intermediate moves. Restarts generate many accepted improvements back toward the archived prior; accepted-current progress must not be confused with improving the global archive.

Thirty percent local *macros* is not thirty percent local objective queries: a bundle macro tests many candidates. The measured local-macro counts give an upper bound on local distinct calls; the bulk of the budget is allocated to beam repair. This is a concrete efficiency limitation relative to100k ILS neighborhoods, not a proof that network information is useless.

## Bounded rank-disruption probe

Registered during confirmation after its first outcomes; adaptive diagnosis, not another confirmatory optimizer trial. Seeds1400..1423, fixed shared-prior/frozen-GA/refined-ILS parents, four targeting/repair combinations, matched attempted proposal effort and full mean64 fitness. No parent was updated. All288 macros retained.

| Parent | Targeting | Repair | Improving /24 | Mean delta (h) | Mean changed first-wave origins |
|---|---|---|---:|---:|---:|
| shared_prior | connectivity | insertion_beam | 0 | +0.000000000 | 0.000 |
| shared_prior | connectivity | joint_slot_swaps | 8 | -0.001553767 | 0.887 |
| shared_prior | random | insertion_beam | 0 | +0.000000000 | 0.000 |
| shared_prior | random | joint_slot_swaps | 7 | -0.000639102 | 0.712 |
| frozen_ga | connectivity | insertion_beam | 0 | +0.000000000 | 0.000 |
| frozen_ga | connectivity | joint_slot_swaps | 0 | +0.000000000 | 0.000 |
| frozen_ga | random | insertion_beam | 0 | +0.000000000 | 0.000 |
| frozen_ga | random | joint_slot_swaps | 0 | +0.000000000 | 0.000 |
| refined_ils | connectivity | insertion_beam | 0 | +0.000000000 | 0.000 |
| refined_ils | connectivity | joint_slot_swaps | 0 | +0.000000000 | 0.000 |
| refined_ils | random | insertion_beam | 0 | +0.000000000 | 0.000 |
| refined_ils | random | joint_slot_swaps | 0 | +0.000000000 | 0.000 |

Joint swaps preserve other slots and improve the older prior in some probes; the tested probes do not improve the frozen GA or refined ILS. Different operator RNG streams and beams generate different candidate sets, so this is evidence of a repair/disruption mechanism, not an equal-search-space superiority claim. Zero loss changes can still have raw crew-label differences; operational origins/travel/predecessors are reported separately.

## Independent candidate verification and influence

Every method's best confirmation permutation plus frozen GA/refined ILS passed all64 original pandas/NetworkX production evaluations (448 sample calls; maximum absolute compiled/production discrepancy 3.49e-12 h). Full identities and92-station permutations are in `CANDIDATE_PRODUCTION_AND_INFLUENCE_100000.json`; per-state values and event-exact self/threshold/source decomposition are in companion CSV/JSON files.

| Best method candidate | Seed | Production J (h) | Delta vs frozen GA (h) | Improved / worsened states | Delta without15 (h) | Leave-one-out reversal count |
|---|---:|---:|---:|---:|---:|---:|
| connectivity_lns | 1212 | 33.018110793425 | +0.020270020 | 27 / 37 | +0.020061146 | 0 |
| random_lns | 1202 | 33.007326958137 | +0.009486184 | 9 / 55 | +0.042333085 | 0 |
| scheduling_lns | 1215 | 33.013013920585 | +0.015173147 | 27 / 37 | +0.014740538 | 0 |
| ga_baseline | 1205 | 32.998356670973 | +0.000515897 | 24 / 40 | -0.000444524 | 1 |
| iterated_local | 1202 | 32.996287058662 | -0.001553715 | 14 / 50 | +0.031606322 | 6 |

The new ILS best (seed1202) remains +0.000149693 h worse than the previously refined ILS. Against frozen GA it improves only14/64 states and worsens50; its median change is +0.043610062 h. Sample15 contributes -2.090636091 h, and excluding15 reverses the mean to +0.031606322 h. Six leave-one-out removals reverse its frozen-GA ranking. None of those removals is used in optimization.
Sample15's event-exact difference is self=+0.155072845, threshold=+0.005702034, source=-2.251410970, total=-2.090636091 h. The benefit is source reconnection, overcoming worse self-restoration and threshold contributions. This is exact accounting for the whole schedule comparison, not proof that one station move caused it.

Differences against refined ILS, medians, empirical quantiles, all leave-one-out changes, largest beneficial/adverse states and leave1/2/4/8-most-beneficial-out diagnostics are retained. Outcome-selected sample removals are sensitivity diagnostics, not a revised objective. All64 samples still determine every optimized mean.

Complete event trajectories compare candidate and frozen GA at sample15 and each candidate's strongest beneficial/adverse state. `L_total=L_self+L_threshold+L_source` is integrated on the union of native completion events over the original planning horizon. Affected station dependency mass and interval timing are descriptive, not station-level causal interventions.

## Computation and identities

Confirmation: 100 runs, 10,000,000 distinct search queries and 26,695,746 attempted calls. Elapsed parallel batch wall=1972.28 s at12 workers; aggregate worker wall including setup=21947.62 s. Worker timings are contention-dependent, not isolated serial speed benchmarks.
Completed smoke contributes10,000 search queries. Bounded probe contributes7,586 distinct/10,287 attempted mean calls, plus18,624 compiled single-state audit calls. Native-only reannotation adds36,864 decodes; final-phenotype audit adds6,336 decodes and zero objective queries.
Each successful worker loader also makes8 setup-parity mean calls outside its search budget and one final best-score verification;100 confirmation runs add800+100 such calls. Analysis loaders have the same8-call setup. Failed smoke initialization and cold compilation overhead were not fully instrumented and are explicitly additional, not counted as zero. Search-distinct means chromosome identity, not guaranteed unique scheduling behavior or globally distinct queries across methods.
Per-run checkpoints, archive trajectories, attempted-call overhead, acceptance/restart counters, weighted bundle support and complete candidate hashes are retained. The final-phenotype audit ignores interchangeable same-origin crew labels but preserves per-station origin, predecessor, travel, arrival and completion. It concerns final candidates, not an unobserved whole-search neutral fraction.

## Validation readiness, without generating states

Original freeze hashes pass. Addendum retains the original nine ordered policies and addsCentrality-first, Closeness-first and fixed refined ILS as secondary diagnostic:12 ordered+unconstrained=13 conditions. Original primary frozenGA-minus-Impact remains unchanged. The original protocol and formal strategies are not overwritten. Physical sampling function/source hashes, RNG namespace and bootstrap plan are recorded in `VALIDATION_COMPARATORS_ADDENDUM.json`.
Projected archive=1.387 GiB; reserve=4.162 GiB; checked free disk=81.16 GiB. These are scaled engineering estimates, not measured new-archive sizes. Physical DS/duration arrays alone require2,944,000 bytes; trajectories and metrics dominate storage.
No sampling functions were called. Keep SeedSequence([202610091,3,2,r]), shared physical states, overlap-abort against64 planning and1000 previously inspected states, fixed comparator hashes,20k whole-state paired bootstrap, no optional stopping/reselection, and explicit author approval. Validation0-480 h is distinct from H_plan. This addendum must itself be frozen and all fragility/PGA/config hashes rechecked immediately before an authorized executor.

## Remaining research decision

Prespecified500k trigger passed: **False**, triggering methods: `[]`. No unchanged underperforming LNS batch was extended just to repeat its plateau. This is a gate decision, not a claim that current GA parameters are optimal.
The executed evidence narrows the unresolved mechanism to removable scheduling leverage and rank-preserving repair, rather than generic source importance or merely sampling more optimizer seeds. Slot swaps help an older prior but currently give no evidence of beating the fixed high-quality comparators. GA versus ILS must be judged using the actual paired uncertainty and computation, not the failure of this LNS or one weak baseline. Generalization remains untested on untouched states; no new scientific policy is promoted.

Preservation passes for950 protected revision files plus exact revision HEAD/branch and staged binary-diff hash. The isolated checkout hydrated only8 verified LFS inputs. Their payload SHA-256 equals the original pointer OIDs; this is hydration, not a model modification. No source gate, scheduler, kernel, physical file or manuscript figure changed in the diagnostic commits.

## Reproduction

```powershell
$env:PYTHONPATH='src'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMBA_NUM_THREADS='1'
$env:NUMBA_CACHE_DIR=Join-Path $env:TEMP 'lns2-20261010-numba'
python -m unittest discover -s tests -p test_connectivity_lns_20261010.py -v
python -m la_grid.diagnostics.ga_connectivity_lns_local_20261010 --phase smoke --workers 2
python -m la_grid.diagnostics.ga_connectivity_lns_local_20261010 --phase confirmation --workers 12
python -m la_grid.diagnostics.ga_connectivity_lns_audit_20261010 --task mechanism
python -m la_grid.diagnostics.ga_connectivity_lns_audit_20261010 --task cutsets
python -m la_grid.diagnostics.ga_connectivity_lns_audit_20261010 --task readiness
python -m la_grid.diagnostics.ga_connectivity_lns_failure_probe_20261010
python -m la_grid.diagnostics.ga_connectivity_lns_candidate_20261010 --budget 100000
python -m la_grid.diagnostics.ga_connectivity_lns_report_20261010 --task reannotate
python -m la_grid.diagnostics.ga_connectivity_lns_report_20261010 --task phenotypes
python -m la_grid.diagnostics.ga_connectivity_lns_report_20261010 --task report
```

The optimizer command verifies and reuses completed per-case records. It does not resample physics. Frozen input hydration requires the checked original LFS objects; setup command and run IDs are recorded in the setup module. Publication uses only this research prefix, new diagnostic modules/tests and the dedicated review index.
