# 1021: engineering and descriptive value follow-up

Read SCIENTIFIC_DECISION.md first. K3 has useful descriptive contrasts but is
not supported as a robust three-class taxonomy; it remains optional. Proposed
wording is in MANUSCRIPT_WORDING.md and has not been inserted into the paper.

## Reproduce without original simulations

Use the parent's requirements-validation.txt (Python 3.12 and recorded package
versions). Pull actual LFS bytes for results/stage7/2026-10-14 and the complete
results/diagnostics/1021 subtree. The earlier protocol/results remain unchanged.

```powershell
python -m pytest results/diagnostics/1021/engineering_value_20261015/test_followup.py -q
python results/diagnostics/1021/engineering_value_20261015/analyze.py
python results/diagnostics/1021/engineering_value_20261015/summarize_followup.py
```

The statistical analysis uses only committed tract outcomes and original frozen
feature matrices; no untracked trajectory archive is required for those commands.
It always performs all 100 repetitions at 70% and 85%, all K2/K3/K4 and all
registered benchmarks. Do not cherry-pick runs or replace the K3 source labels.

## Original-source extraction and preservation QA

```powershell
$env:LA_GRID_FROZEN_SOURCE_ROOT = "path/to/exact/registered/archive"
python results/diagnostics/1021/engineering_value_20261015/extract_outcomes.py
python results/diagnostics/1021/engineering_value_20261015/verify_followup.py
```

These two commands additionally require the manifest-bound local archive and
the original source worktree for preservation checks. They deliberately fail
when source bytes/identities are unavailable or differ. They must not be
interpreted as a promise that a clean Git clone contains all simulation archives.
The extractor reuses saved service states; it imports no physical-model stage,
does not schedule repairs and does not propagate station states anew.

The protocol was pushed as d64cc2dd3a3ed9f733414a0dd32149bf9343d9d9 before
class-outcome results were examined. Source hashes and exact denominator/units
are documented in SOURCE_AND_OUTCOME_QA.md, SOURCE_HASHES.csv and
EVENT_SOURCE_HASHES_AND_IDENTITIES.csv. The legacy T80 is the crossing time of
a MEAN curve, not the realization-median threshold time used here.

## Machine-readable evidence

- UNFITTED_TRACT_OUTCOMES.csv: 2,299 aligned tract rows. Unconstrained total
  burden is retained for reconciliation but EXCLUDED from outcome evaluation.
  OUTCOME_REGISTER.csv identifies primary, supporting and ancillary quantities.
  Impact total deficit is an ancillary identity descriptor, not an additional
  confirmatory endpoint. No conclusion relies on relabeling it as independent.
- T80_REALIZATION_VALUES.npz: exact post-processed times, with NaN reserved for
  unreached values. No unreached value was observed; zero censoring is not a
  discriminating outcome or evidence of perfect recovery prediction.
- REFERENCE_OUTCOME_PROFILES.csv: original units, counts, population, valid
  values and tract distribution summaries for each unchanged reference class.
- CROSS_K_MEMBERSHIP_OVERLAP.csv: every cell, conditional proportions, Jaccard
  and resident counts. Agreement uses ARI/NMI, not assumed nesting.
- SUBSAMPLING_ARRAYS.npz: all 200 training sets and 600 centroids/partitions.
  SUBSAMPLING_MEMBERSHIP.csv and CLASS_JACCARD_SUMMARY.csv retain both fractions.
- TRACT_MEMBERSHIP_CORE_FREQUENCIES.csv: every GEOID, full and held-out-only
  denominators/frequencies; cores never exclude a tract from the analysis.
  CORE_SOURCE_PROXY_OVERLAP.csv identifies the overlap with the historical 37-set.
- HELD_OUT_OUTCOME_SCORES.csv: all models/outcomes/repetitions, MAE/RMSE and
  test denominators. PAIRED_MAE_COMPARISONS.csv retains every paired contrast;
  the summary records the fraction reaching the preregistered notable margin.
- SIMPLE_BENCHMARK_CUTS.csv: training-only cuts, including any collapsed ties.
- SUBSAMPLING_RECOVERY_PROFILE_CHANGES.csv and the engineering contrast tables:
  all outcomes/classes/repetitions, not just favorable profile contrasts.

The original 50% prediction-strength, bootstrap and policy/geographic evidence
remain in the parent outputs/ directory. Their metrics/definitions differ from
the new ARI and core frequency; larger-sample ARI is not a refutation of them.

## Figures and interpretation

01: class means and between-tract P10-P90 for the excluded Random burden,
Impact-priority time to 80%, reduced crews and Northridge burden. Small numbers
are class indices within each K (one-based for display), NOT cross-K identities.
For K3 they correspond to the existing C1/C2/C3. A temporal point averages tract
realization medians, not a population threshold time. All remaining registered
contexts are retained in the tables, including LongBeach, SanFernando and C114.

02: benchmark MAE minus K3 MAE; positive favors K3. Points are means over 100
paired repeats, bars P10-P90 (not confidence intervals). Dashed lines are the
registered notable gain. Both fractions and all same-size simple groupings are
shown; K4 and every other outcome remain in machine-readable paired evidence.

03: overall membership ARI and per-class held-out-only stable-core fraction.
All classes, including zero-core cases, are shown. This is not a plot of
external scientific validation. PDFs are vector, 7.2 inches wide, with 300-dpi
previews and PDF-derived native-size inspection records.

## Scope and delivery

Only this new subdirectory changes after 3f10ff62. The frozen 2026-10-14 branch,
official manuscripts, figures, captions, trajectories, original Stage 7 and the
older 1021 package remain unchanged. No merge or promotion is performed.
Independent QA recalculates all 600 membership partitions and 20,400 held-out
cluster/outcome scores, 3,600 class Jaccards, core frequencies, threshold-time
quantiles, event identities and protected-file hashes. Remote delivery uses a
fresh empty LFS store, not pointer existence. The receipt names its payload
commit; a subsequent receipt-only commit is separately checked at final HEAD.
