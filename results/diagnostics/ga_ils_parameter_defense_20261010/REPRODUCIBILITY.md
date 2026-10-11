# Reproducibility and Evidence Access

## Frozen Authority

Repository: `yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale`.

Task starting commit: `e7d05e2649f3be2ccfbf9398d86e0612407dd5ea`.

Diagnostic branch: `diagnostics/ga-ils-reviewer-parameter-defense-20261010`.

Prospective commits: `196e09c` (initial design), `3766c1a` (observation-only JSON repair), `c4b765e` (independent confirmation and focused mechanism addendum). Individual raw records retain the actual execution commit, compute-source SHA, runtime, worker PID, CPU and wall time. Later report/packaging changes do not redefine the search implementation used by those records.

After all numerical searches finished, an administrative safety repair made the original 16-case engineering set explicit and prevented `setup` from overwriting an existing preservation/design authority. It changes no evaluator, search operator, stochastic trajectory or saved result. For exact execution-source provenance, use the pre-execution commits and raw recorded SHA; the published helper includes this postexecution setup guard.

All runs use the original 92-station, 64-realization `2pc50/C57_D1` planning authority. `MODEL_IDENTITY.json` gives physical sample, source-set, graph, directed-travel and input hashes. No earthquake samples are created, and no completed validation outcomes participate in diagnostic calculations.

## Evidence Without New Searches

Run `git lfs pull` on this diagnostic branch to retrieve the CSVs, figures and compressed raw evidence. The raw archive contains every screening and confirmation JSON, including exact 92-station final permutations, initial chromosome lists, initializer fingerprints, post-initializer RNG hashes, generation histories, strict improvements, checkpoint objectives, and incomplete-control records. It also contains the five deterministic refinement scans, accepted moves, planning-only per-state exports, cached GA prefixes and matched-budget continuation records.

The archive is `RAW_SEARCH_AND_REFINEMENT_EVIDENCE.zip`. `RAW_EVIDENCE_ARCHIVE_MANIFEST.json` records each member's length and SHA-256, and the archive's length/hash. It was reopened and all member payloads verified before publication. Raw directories are ignored in Git solely to avoid storing duplicate uncompressed histories. Nothing was deleted from the local scientific evidence.

To reanalyze without rerunning searches, verify the archive hash against its manifest, then extract its relative members into this results directory. Reject absolute paths or members containing `..`; all recorded members belong to `screen/`, `confirmation/`, `refinement/` or `prefixes/`. Existing historical evidence is already retained by the starting authority.

In PowerShell from the diagnostic worktree:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:NUMBA_NUM_THREADS = '1'
python -B -m la_grid.diagnostics.ga_ils_parameter_analysis_20261010 inventory
python -B -m la_grid.diagnostics.ga_ils_parameter_analysis_20261010 historical_statistics
python -B -m la_grid.diagnostics.ga_ils_parameter_analysis_20261010 analyze
python -B -m la_grid.diagnostics.ga_ils_parameter_analysis_20261010 accounting
python -B -m la_grid.diagnostics.ga_ils_parameter_report_20261010 reports
```

Those commands read retained observations; they do not generate samples or repeat optimizer batches. Candidate production QA is a separate calculation and its calls are accounted separately:

```powershell
python -B -m la_grid.diagnostics.ga_ils_parameter_analysis_20261010 candidate_qa
```

It verifies important candidates on the original 64 planning states through the original production evaluator, not the 2,000 validation cohort.

## Actual New Search Commands

These were executed only after committing the prospective design; they are costly and are not required merely to inspect or reanalyze evidence:

```powershell
python -B -m la_grid.diagnostics.ga_ils_parameter_defense_20261010 screen --workers 12
python -B -m la_grid.diagnostics.ga_ils_parameter_defense_20261010 select
python -B -m la_grid.diagnostics.ga_ils_parameter_defense_20261010 confirmation --workers 12
python -B -m la_grid.diagnostics.ga_ils_parameter_defense_20261010 refinement
```

The first five predeclared confirmation seeds were refined once their ILS results and GA prefixes were available; this sequential refinement process overlapped the still-running 12-worker confirmation batch. No seed was selected from a favorable result. Per-run CPU, wall time and concurrent batch wall times are distinct measurements. Local wall times should not be compared directly to historical GitHub Actions times as if hardware were identical.

Batch commands reuse an existing saved case rather than rerun it. For an independent search reproduction, use a separate worktree/output area, the archived prospective design, matching recorded execution source/commit and pinned scientific inputs. Do not overwrite the existing package or rerun setup on its preservation/design authority. Mixed-ILS observational parity, GA operator/initializer property tests and production parity bound numerical implementation drift. Floating-point/platform equivalence and wall-time equivalence are not claimed bitwise across arbitrary environments.

## Statistical Rules

Optimizer seeds are blocks. The confirmation range is `2026101200:2026101220`; screening is `2026101100:2026101108`; bootstrap seed `2026101300`, 20,000 replications. Seed-level paired final differences, pointwise t intervals, block-bootstrap intervals and predefined-family Bonferroni t intervals are all saved. Family sizes: elite 3, original/selected/mechanism ILS contrasts 9, warm/cold method/information contrasts 4, confirmation interaction 1, refinement 2. The two additional direct reduced-ILS-versus-GA contrasts form a retrospective exploratory family, not a prospective primary analysis. Engineering screens are explicitly exploratory, even when used to select a setting for independent confirmation. No numerical equivalence margin was inferred from observed differences.

Measured local timings include diagnostic instrumentation. GA retains per-generation population diversity/history whereas ILS tracks a current sequence. Objective scoring time is separate; remaining wall time includes algorithm bookkeeping, observation and runtime overhead. Do not interpret the instrumented wall ratio as an instrumentation-free universal speedup. Attempted queries and cached repeats are exact independently useful cost measures.

Distinct-evaluation budgets refer to uniqueness inside each fresh search cache, not global uniqueness across configurations or seeds. If two independently executed searches score the same reference or permutation, those are two actual expensive calls and are charged twice. The controlled GA continuation is the declared exception: its retained 100k prefix is replayed by lookup and is not charged as new physical scoring.

The cache key is the complete 92-station permutation, not a unique operational schedule or objective value. Different permutations can produce identical schedules or losses and still consume distinct expensive scores. Equal distinct budgets therefore match actual objective work, not guaranteed equal amounts of useful scheduling information. Existing neutral-plateau and actionable-delay studies are retained rather than conflating genotype duplication with scheduling equivalence.

Incomplete no-perturbation cases remain in records and descriptive accessibility comparisons but are not used as completed equal-budget evidence. Historical overlapping phases, duplicated artifacts, repeated checkpoints and continued prefixes are labeled rather than treated as new independent optimizer seeds. Historical cloud timings are not pooled with local CPU timings.

## Preservation and Publication

`PRESERVATION_BASELINE.json` and `PRESERVATION_VERIFIED.json` retain the protected revision checkout's HEAD, branch, staged binary-diff SHA and 950 scientific-file hashes. They also retain all formal-GA and completed-validation artifact hashes. Hashing validation evidence checks preservation only, not its scientific outcomes. No `git reset`, `git clean` or `git stash` is used against the original checkout.

`REPRODUCIBILITY_AND_PRESERVATION_QA.json` records numerical, permutation, scientific-input, source-content, test and visual checks. `REMOTE_PUBLICATION_VERIFIED.json` records the published data commit, remote branch equality and actual downloaded LFS object SHA-256 and lengths. Its verification receipt is committed/pushed separately, then final remote HEAD is checked again. This finite receipt chain does not claim a file can contain its own final commit hash.
