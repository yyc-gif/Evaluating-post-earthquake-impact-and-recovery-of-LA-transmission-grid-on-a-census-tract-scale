# Reviewer 1 Comments 6–7 — GA Search and Objective Revision

## 1. July objective and algorithm

The retained July `run_stage_5()` remains available as legacy code. For each policy it normalized station population, hospital and SOVI importance, mixed those with weights `(1,3,1)`, `(1,20,1)` or `(1,1,1)`, then blended the service score with a source-role/voltage/line network score using `eta=0.20`. A decoded representative-duration schedule produced weighted early-completion benefit minus `W_MAKESPAN × makespan/Tmax`, with makespan weights 0.5, 0.1 and 2.0. The objective did not calculate source-gated tract service or tract burden.

July settings were a full task permutation, population 100, 100 generations, ordered crossover at 0.8, inversion mutation at 0.2, tournament selection of size 3 and a fixed generation budget. Two deterministic candidates were inserted. `eaSimple()` returned the final population and `selBest(pop,1)` selected only from that population. There was no Hall of Fame/best-so-far archive or saved generation history; therefore a known better incumbent or earlier individual could be lost.

## 2. Revised search mechanism

`r1_ga_revision.py` leaves the July function untouched and supplies the revised engine for future strategy freezing:

- validates every chromosome as one complete permutation;
- requires named deterministic incumbents and evaluates them under the identical objective/decoder;
- preserves the best incumbent and best candidate seen over the complete run;
- returns the incumbent explicitly if the finite-budget search does not improve it;
- records generation best, generation mean and best-so-far, plus best generation and candidate source;
- accepts explicit independent seeds and has a fixed generation stopping budget;
- uses a local reproducible RNG, ordered crossover, inversion mutation and tournament selection.

The synthetic two-seed check (seeds 7 and 8; population 8; five generations) retained the known incumbent at fitness 4.0, source `incumbent:fixed`, generation 0, with six history rows. Repeating seed 7 reproduced the sequence and history exactly. This diagnostic is not a formal GA run and is not publication evidence.

## 3. Explicit evaluators

### Legacy evaluator

`legacy_station_completion_objective()` exposes the submitted station-level early-completion surrogate under an unambiguous name. It uses expected/representative durations, station priority and makespan weight. Different policy objectives must not have their fitness values compared as though they were the same scale.

### Direct community evaluator

`evaluate_direct_population_burden()` and `direct_population_burden_objective()` execute:

`candidate permutation → realization-specific event schedule → completion-step raw functionality → supplied unchanged source gate → tract weight propagation → represented tract burden → population×resolved-mass weighted burden`.

The maximization fitness is the negative direct population burden. Makespan and task events are returned as diagnostics; no new makespan tradeoff coefficient is silently embedded.

In the fixed three-station diagnostic, A-first had direct population burden 1.0198019802 h and B-first 3.0 h, so the direct objective preferred A-first. A deliberately B-heavy legacy station-priority surrogate scored A-first 0.6081818182 and B-first 0.7718181818, preferring B-first. This demonstrates an objective-rank mismatch without tuning either evaluator.

## 4. Hospital-first versus old GA-HospFirst

Hospital-first is a deterministic ordering based on the hospital rule. The old GA-HospFirst maximized a station-level weighted-completion surrogate containing hospital weight 20, other service/network terms and a makespan penalty. Reported T80/AUC were calculated later from source-gated tract trajectories. Optimizing the surrogate therefore never guaranteed lower tract T80, AUC or burden. A simple Hospital-first rule could outperform the retained GA candidate on a reported metric because the rule and GA were judged by a metric that the GA did not directly optimize; that is objective mismatch, not by itself proof of search failure.

A possible future direct hospital evaluator is hospital-tract cumulative burden. No new 20× hospital coefficient or hospital GA was introduced here.

## 5. Verification and boundaries

`test_r1_ga_revision.py` verifies incumbent preservation, no best-so-far regression, exact same-seed repeatability, two independent seed records, complete generation history, actual invocation of a source-gate callback inside the direct evaluator, agreement between direct fitness and reported population burden, and a constructed legacy/direct ranking mismatch.

No formal GA, final evaluation sample, full pipeline, mapping change, crew sensitivity, typology analysis, manuscript edit or figure generation was run.

## 6. Decisions still open

The following remain for the later strategy-freeze design:

1. final GA strategy set;
2. whether a distinct direct hospital-burden GA is scientifically necessary;
3. whether makespan is a reported secondary metric, deterministic tie-break, explicit constraint or predeclared weighted term;
4. separation and size of planning versus final paired evaluation samples.
