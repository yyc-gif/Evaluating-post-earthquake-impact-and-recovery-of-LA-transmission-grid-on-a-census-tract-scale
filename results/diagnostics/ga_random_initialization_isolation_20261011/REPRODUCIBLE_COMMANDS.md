# Reproduction And Evidence

Run in the isolated checkout `diagnostics/ga-random-initialization-isolation-20261011`, starting at f9734afa09bd0a0e59b2b1d81d43599062d4c258. The authority contains the three requested historical packages. Selective LFS hydration checks exact object hashes. On a new machine, obtain only the planning input and source LFS objects identified in EXPERIMENT_DESIGN_AND_SEEDS.json; do not fetch or analyze independent-validation cohorts.

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMBA_NUM_THREADS='1'
$env:NUMBA_CACHE_DIR=Join-Path (Get-Location) 'results\diagnostics\ga_random_initialization_isolation_20261011\runtime'
$python='C:\Users\yinch\anaconda3\python.exe'
$dir='results/diagnostics/ga_random_initialization_isolation_20261011'
& $python -B "$dir/study.py" setup
& $python -B "$dir/study.py" smoke
& $python -B -m pytest "$dir/test_isolation.py" -q --basetemp="$dir/runtime/pytest"
git add -- $dir
git commit -m "Preregister paired GA initialization study"
& $python -B "$dir/study.py" register
& $python -B "$dir/study.py" main
& $python -B "$dir/analyze.py" summary
# Only if EXTENSION_DECISION.json says extend=true:
& $python -B "$dir/study.py" extension
& $python -B "$dir/analyze.py" final
& $python -B "$dir/study.py" verify
& $python -B "$dir/publish.py" package
& $python -B "$dir/final_quality.py"
# Refresh the manifest after the QA receipt is created:
& $python -B "$dir/publish.py" manifest
```

The completed package is not to be rerun in place. Setup refuses to overwrite a registered study. Main/continuation reuse completed receipts; an interrupted trajectory resumes from CHECKPOINT.pkl.gz and must retain its matching initializer receipt. All runs use fresh per-run caches, never shared historical objective lookups. Twelve single-threaded workers bound local resource use. The extension adds 400k evaluations to each of the first 10 paired searches; 250k and 500k states are continuations, not additional random seeds.

Binary raw evidence is stored losslessly in 40 per-run ZIP bundles. Each includes CANDIDATES.npz, PARENT_SELECTION.npz and exact saved checkpoints at all executed terminal budgets. SHA-identical final/current checkpoint copies are stored once within a bundle with a complete path-to-object manifest. Initial populations, per-budget receipts, strict improvements, generation diagnostics and budget rows remain directly readable in `runs/`. No observation has been discarded. Engineering data remain directly versioned, including the split/uninterrupted counterparts.

To restore a particular run, read its ZIP's PATH_HASH_MANIFEST.json and extract each named `objects/<sha256>` payload to the indicated logical filename. Check size and SHA256 before unpickling. Pickle is a trusted-repository execution format; do not load untrusted substitute states. To continue, place the matching checkpoint and directly saved initializer under the same run directory and use the registered mode/seed/mechanics. A new physical sample is not needed.

Counts distinguish independent optimizer replicates from repeated checkpoints. `attempts` includes unchanged-engine parent re-queries; the convergence CSV additionally reports mandatory parent cache queries and population-member duplicates. Distinct evaluations count unique 92-station permutations per search. Identical schedules/objective values can still arise from different permutations; they are not automatically cache duplicates. Timing includes diagnostic observation/checkpoint overhead. It is not solely an intrinsic GA cost estimate.

Production QA uses the original pandas/NetworkX scheduler and source gate on all 64 planning states for the prespecified important candidates. Those checks are separate from search budgets. No completed old study is rerun and no validation outcomes are used to choose chromosomes. All recommendations are diagnostic only.

Final report/figure wording can be regenerated from the already verified CSV tables without re-evaluating any objective:

```powershell
& $python -B -c "import sys; from pathlib import Path; import pandas as pd; p=Path('$dir'); sys.path.insert(0,str(p)); import analyze as a; df=pd.concat([pd.read_csv(p/(m+'_SEED_RESULTS.csv')) for m in a.s.MODES]); cp=pd.read_csv(p/'PAIRED_INITIALIZATION_COMPARISON.csv'); a.final_reports(df,cp); a.figure(df,cp)"
```

The final recommendation explicitly departs from the immutable automatic adoption fallback. Read FINAL_GA_INITIALIZATION_DECISION.md and FINAL_DECISION_MACHINE_READABLE.json before using proposed Methods text. No prospectively passed adoption or 90% proximity gate is claimed.

After a scoped commit and push, `publish.py remote` downloads actual bytes for every unique LFS object in the diagnostic package and verifies its SHA256 and size against the committed pointer. The subsequent receipt-only commit records that check; verify its remote HEAD separately. Only this new diagnostic directory is staged, never the original revision checkout.
