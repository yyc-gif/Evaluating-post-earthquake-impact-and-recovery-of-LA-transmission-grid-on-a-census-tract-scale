# Standalone ILS: Fixed Prospective Validation

## Decision

The prespecified modeled-benefit criterion against Impact-first is met. The frozen standalone ILS also has lower mean loss than the formal GA on this new cohort under the simultaneous two-contrast interval. **This does not authorize replacing the formal GA or imply that ILS dominates GA across realizations or outcomes.** No strategy is promoted.

ILS mean loss is 33.088299 h, versus 33.106569 h for GA and 33.607020 h for Impact-first. Relative mean reductions are 1.5435% versus Impact and 0.0552% versus GA. These are normalized cumulative service-deficit hours, not delivered MW or elapsed restoration-time savings. The GA comparison is a small mean effect with a positive paired median and a majority of unfavorable realizations.

## Prospective Authority and Integrity

- Parent research freeze: `740f941f3614e51b15bcf6c91b3aff3afec9f2ea` on `diagnostics/standalone-ils-final-method-decision-20261010`.
- The human author explicitly authorized exactly 2,000 new physical realizations and three fixed comparisons on 2026-10-11. `AUTHORIZATION.json` records the exact request.
- Execution/analysis code, seed rules, sequences, authorization and engineering checks were committed before drawing: `0dc10edf92e94e52f31fa5298424102606c483f6`. Its receipt records zero new physical draws.
- `EXECUTION_FREEZE.json` incorporates the parent's original prospective plan and original model/input/source hashes. Its embedded pre-execution status is historical, not a claim that this now-completed experiment remains unexecuted.
- Independent PCG64 per-realization entropy `[2026110100,r]`, r=0..1999; namespace `la-grid/standalone-ils/17705a83a7607862d05ec9d6b607d58e31ff644712ceb0d0652ce7e59642499f/prospective-v1`. These streams were not chosen after inspecting outcomes.
- All 2,000 DS/duration pairs were saved before policy evaluation. Each saved pair is shared by all three strategies; all 6,000 cases finish before final analysis. No interim effect-based stopping, expansion, tuning, optimizer call, candidate reselection, or exclusion.
- 2,000 distinct new physical-pair hashes; zero overlap against 3,064 prior identities (64 planning, 1,000 original 2pc50 evaluation and 2,000 earlier validation states). Earlier validation was read only for identity/entropy and byte-hash preservation, never its outcome tables or trajectories.

## Model and Endpoint

The original 92-station network, 318 graph edges, 14 Core sources, 57 C57_D1 crews, directed travel, original damage/repair samplers, 0.5 source gate and M1 population mapping of 2,315 tracts are retained. Priority lists are full 92-station permutations; realized damaged tasks are handled by the original production scheduler. The ILS name identifies the already-selected fixed order; no ILS search is executed on this cohort.

For normalized tract modeled service availability a_i(t), the endpoint is B_i = integral from 0 to 480 h of [1-a_i(t)] dt; B_pop = sum_i population_i B_i / sum_i population_i. The original evaluator's resolved-mass normalization is retained. The current M1 primary and dependency-mass-weighted component totals agree within 2.84e-14 h over all 6,000 records. Do not assume that equality for a different mapping.

The frozen horizon is 480 h, distinct from the longer planning bound of 2855.254013110 h. Exact completion-event left-rectangle integration is used, not trapezoids on a coarse grid. Task completion events after 480 h and censored T80 are preserved by design. In this actual cohort there are zero late task events and zero censored population T80 cases, and all three policies reach effective modeled service 1 by 480 h. This observation is not an assumption that arbitrary future samples have zero post-480 loss.

## Fixed Statistical Analysis

20,000 paired whole-realization percentile bootstrap resamples use seed 2026110200 and a shared resample bank. The unit of replication is the physical realization, not a tract, station, crew, policy row, or checkpoint. The primary two-sided pointwise 95% interval is the frozen decision rule versus Impact-first. Both population-loss contrasts additionally use Bonferroni 97.5% individual intervals for simultaneous 95% coverage of the two-contrast family. No other endpoint family is multiplicity-adjusted; all other intervals are descriptive pointwise. No equivalence or noninferiority margin was registered.

| Policy | Mean loss (h) | SD | MCSE | Median | P95 | P99 | Highest 5% mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| standalone-ILS | 33.088299 | 2.537138 | 0.056732 | 33.037075 | 37.432730 | 39.057956 | 38.436507 |
| formal-GA | 33.106569 | 2.558375 | 0.057207 | 33.023403 | 37.478494 | 39.188495 | 38.510392 |
| Impact-first | 33.607020 | 2.652096 | 0.059303 | 33.483507 | 38.113655 | 39.899911 | 39.224612 |

| Contrast | Mean difference (h) | MCSE | Pointwise 95% CI | Simultaneous 95% family CI | Favorable / unfavorable / tied |
|---|---:|---:|---|---|---|
| ILS minus Impact-first | -0.518721 | 0.013940 | [-0.546203, -0.492059] | [-0.550475, -0.488425] | 1704 / 296 / 0 |
| ILS minus formal-GA | -0.018270 | 0.006753 | [-0.031869, -0.005412] | [-0.033822, -0.003717] | 627 / 1373 / 0 |

All contrasts are ILS minus reference; negative population-loss differences favor ILS. MCSE is the paired-difference SD divided by sqrt(2,000), distinct from the bootstrap interval.

## Distribution: Mean Benefit Is Not Dominance

| Contrast | Paired median | P05 | P95 | P99 | Minimum | Maximum | Highest 5% difference mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| ILS minus Impact-first | -0.382775 | -1.670931 | 0.207501 | 0.747941 | -3.935229 | 2.435170 | 0.522579 |
| ILS minus formal-GA | 0.046136 | -0.453595 | 0.173394 | 0.385092 | -3.943383 | 1.276710 | 0.326285 |

Against Impact-first, 1704/2,000 (85.20%) improve and 296 worsen. Against GA, only 627/2,000 (31.35%) improve; 1373 (68.65%) worsen. The paired GA median is +0.046136 h despite mean -0.018270 h. Larger favorable differences offset more numerous small unfavorable differences. This is an asymmetric distribution, not evidence that a typical new realization benefits from ILS versus GA. `PAIRED_DISTRIBUTION_DESCRIPTION.csv` reports the conditional means and their contributions using the full cohort without removing samples or creating an alternative ranking.

The highest-5% policy-loss means above are each policy's own largest 100 losses, not paired differences for a shared subset. The highest-5% difference mean is the largest 100 ILS-minus-reference differences and describes unfavorable changes, not the same tail estimand. These tail summaries are descriptive, with no registered superiority test for quantiles or conditional tails.

## Exact Loss Decomposition

The original production gate partitions total loss into self, functionality threshold and source-connectivity losses. Population dependency mass weighting is retained.

| ILS minus reference | Self (h) | Threshold (h) | Source (h) | Sum / total (h) |
|---|---:|---:|---:|---:|
| Impact-first | +0.295584 | +0.011343 | -0.825648 | -0.518721 |
| formal-GA | +0.089029 | +0.003331 | -0.110630 | -0.018270 |

Against both references, lower mean source-connectivity loss offsets higher mean self and threshold losses. The GA source decrease is larger than the small final net mean decrease. This is a decomposition of the effects of each entire fixed scheduling policy under the same physical state, not proof that any single station move caused the gain. No station-level controlled counterfactual is performed here.

## Tradeoffs and Negative Results

| Endpoint | ILS minus Impact mean [pointwise 95% CI] | ILS minus GA mean [pointwise 95% CI] |
|---|---|---|
| Q1 population loss (h) | -0.481432 [-0.512530, -0.451070] | -0.038184 [-0.048659, -0.027779] |
| Q2 population loss (h) | -0.311896 [-0.337581, -0.286879] | +0.073235 [0.061150, 0.084887] |
| Q3 population loss (h) | -0.501550 [-0.529068, -0.474657] | +0.001735 [-0.012555, 0.015129] |
| Q4 population loss (h) | -0.764651 [-0.797803, -0.732388] | -0.107545 [-0.126953, -0.088929] |
| Mean hospital-linked tract loss (h) | -0.225644 [-0.254076, -0.198424] | +0.054158 [0.040755, 0.066859] |
| Absolute Q4-Q1 gap (h) | +0.221764 [0.196316, 0.246814] | +0.049559 [0.036155, 0.063177] |
| Signed Q4-Q1 gap (h) | -0.283219 [-0.308219, -0.258019] | -0.069360 [-0.083182, -0.056005] |
| Population-weighted tract-loss Gini | +0.009917 [0.009417, 0.010428] | +0.001851 [0.001568, 0.002148] |
| Population T80, restricted (h) | -0.116392 [-0.178312, -0.055702] | +0.086507 [0.065461, 0.108014] |
| Total directed crew travel (crew-h) | -6.083630 [-6.128026, -6.038978] | -0.357898 [-0.393033, -0.323253] |
| Last task completion (h) | -0.100517 [-0.279071, 0.075141] | -0.026602 [-0.085896, 0.031553] |

Quartiles are the original fixed social-vulnerability groupings, not Stage 7 community classes. Hospital loss is an unweighted mean of normalized modeled loss among hospital-linked tracts, not hospital downtime, patient outcomes, or electricity delivered to individual hospitals.

The GA comparison has worse mean Q2 loss, hospital-linked tract loss, T80, absolute Q4-Q1 gap and tract-loss Gini under ILS. Mean Q3 loss and makespan differences remain unresolved at pointwise 95%; an interval crossing zero is not equivalence. Q4 mean loss improves, but its paired median difference is positive. Against Impact-first, the absolute Q4-Q1 gap and Gini also increase despite lower overall and all-quartile mean losses. Signed gap reductions do not automatically mean improved equality: mean Q4-Q1 is already negative under every policy. No claim of uniform fairness improvement is warranted.

ILS total directed crew travel is lower on average than both references, but travel summed across simultaneous crews is crew-hours, not elapsed makespan. Mean makespan is not demonstrably shorter under either comparison's pointwise interval. Do not infer faster completion of the full restoration campaign from lower cumulative population loss or summed travel alone.

## Numerical and Execution QA

- 6,000 actual saved trajectory reintegrations passed; independent kernel maximum absolute disagreement: 4.263e-14 h.
- Eventwise self + threshold + source conservation maximum error: 0.000e+00.
- 850 independent summary-statistic/sign-count checks against final realization records passed. No bootstrap reselection/recalculation in reporting.
- No missing primary records, failed prospective cases, case deletions, or resumed completed prospective cases. Synthetic late-event/censoring handling and identical saved-state crash-resume were separately tested before drawing.
- Genuine damage sampler calls: 2,000; repair sampler calls: 2,000; production evaluations: 6,000; independent kernel checks: 6,000; optimizer calls: 0.
- Draw wall time: 13.353 s; eight-worker evaluation batch wall time: 35.001 s; sum of case evaluation wall times: 247.774 s; final analysis wall time: 27.567 s. These measure this fixed-policy evaluation only, not optimizer training cost or GA-versus-ILS search speed.
- Engineering used 16 successful original/synthetic production/kernel evaluations and one additional failed-cache-attempt production evaluation; zero new physical draws. An initial scenario-registry assertion was corrected before sampling. The Windows JIT cache path was shortened without scientific source changes.
- Seventeen guard/scheduler/source-gate tests passed before sampling. Exact runtime versions and source byte hashes are in `EXECUTION_FREEZE.json`; original sampler AST/constant agreement is in `SAMPLING_SOURCE_AUDIT.json`.
- The same 17 tests passed after execution using a checked workspace `--basetemp`. A preceding post-execution attempt had three sandbox TEMP atomic-rename permission failures and 14 passes; the three failures occurred before fixture sampling. Both JUnit records are retained (`POST_EXECUTION_TESTS.xml` and `POST_EXECUTION_TESTS_WORKSPACE.xml`). No source change, new physical generation or prospective rescoring was used to resolve the environment issue.

## Preservation and Evidence

`PRESERVATION_VERIFIED.json` confirms unchanged protected revision HEAD, branch, staged-diff hash and 950 protected files; 14095 old-validation files and 403 parent-source-package files are also byte-identical. No formal GA, model, manuscript, Stage 7 label, original trajectory or original sample is overwritten.

`FIXED2000_FULL_EVIDENCE.zip` contains 12,000 files (172,007,128 bytes): all physical draws and RNG receipts, all three policies' dispatch/completion records, exact event/state/tract-loss arrays and hash-completion receipts. Archive SHA256: `5a81123a3f2a32bd5bd5458fc3ce6b51dd451502734009b75abfc2faaea0fb77`. Every archive member passes SHA256 round-trip verification. Summary tables are outside the archive for direct review. `FIXED_STRATEGY_IDENTITIES.json` and `EXECUTION_FREEZE.json` retain every full permutation and sequence hash.

The diagnostic PNGs are generated only from these completed new-cohort records. The recovery curve display uses an hourly step summary; inference and loss integration use the archived exact event clock, not this displayed grid. The ECDF includes all differences, zero, paired mean and paired median without trimming the favorable tail. These are diagnostic artifacts only; no manuscript artwork is regenerated.

Commit/push and actual remote Git LFS payload verification are recorded in `REMOTE_PUBLICATION_VERIFIED.json` once completed. That receipt identifies the data commit; a later receipt-only commit leaves the data payload unchanged. `OUTPUT_HASHES.json` hashes this local report package excluding itself and later publication/visual-review receipts.

## Interpretation and Next Decision

This is independent simulated-physics generalization evidence for one previously selected standalone ILS sequence, under the unchanged 2pc50 model. It is not a fresh test of the optimizer's probability of discovering good solutions, an untouched test of every historical optimizer decision, real-world calibration, or validation against observed utility restoration. Shared fixed hazard/fragility/network/repair assumptions remain limitations.

The frozen primary benefit criterion succeeds. The secondary mean result also favors ILS, but its approximately 0.0552% mean gain over GA must be weighed against majority-case worsening, hospital/T80/equity tradeoffs and the asymmetric difference distribution. The experiment is complete at the authorized fixed sample size; it does not justify more tuning or another candidate search on these outcomes. The formal GA remains unchanged. Author review of these mean-versus-distribution and stakeholder tradeoffs is required before any separate promotion decision.

## Reproduction and Sources

`PROTOCOL_AND_COMMANDS.md` records original execution commands. For a new checkout of this committed package, hydrate only the frozen input payloads, retain the recorded runtime and do not run `execute` to invent a second validation cohort. The evidence ZIP can reconstruct the original `cohort/` tree; analysis/report phases read that saved tree without drawing or optimizing. The existing complete-cohort execution guard refuses a second execution.

```powershell
$env:PYTHONPATH='src'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:NUMBA_NUM_THREADS='1'
$env:NUMBA_CACHE_DIR=Join-Path $env:TEMP 'vils7-numba'
python -B -m la_grid.diagnostics.standalone_ils_validation_analysis_20261011 analyze
python -B -m la_grid.diagnostics.standalone_ils_validation_report_20261011 report
python -B -m la_grid.diagnostics.standalone_ils_validation_report_20261011 hashes
```

Numerical authority: the parent's `FUTURE_VALIDATION_FREEZE.json`; original `src/la_grid/revision/r1_realization_scheduling.py`, `r1_source_gate.py` and `formal/offline.py`; unchanged `src/la_grid/diagnostics/independent_validation_20261010.py`; archived new `DRAW.json`, `SUMMARY.csv`, `TASK_EXECUTION.csv` and `TRAJECTORIES.npz`. All source/version hashes are local recorded evidence, not inferred from file names.
