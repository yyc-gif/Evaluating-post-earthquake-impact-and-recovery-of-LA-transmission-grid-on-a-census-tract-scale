# Reproducibility

Starting commit f539e3fe6015122d73e5656109e751770550bb70. Isolated branch diagnostics/pure-random-ga-parameter-consistency-20261011. Sources are read-only in sibling _gaf12 and _gri11 verified authority checkouts. Do not run setup/search phases on an existing completed package or inherit its cache; archived states permit exact replay without new physics.

Use C:\Users\yinch\anaconda3\python.exe and OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1. From isolated worktree:

```powershell
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py setup
# Commit registration before computation.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py engineering
python -m pytest results/diagnostics/pure_random_ga_parameter_consistency_20261011/test_audit.py -q
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py screen
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py select
# Original3-family confirmation.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py confirmation
# Post-screen amendment was committed before any confirmation results inspection.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/gain_confirmation.py register
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/gain_confirmation.py execute
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/gain_confirmation.py decision
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/analysis.py planning
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/analysis.py summary
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/qa.py numerical
# Seal and commit decision before existing validation outcomes are accessed.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/analysis.py mechanism
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/report.py memo
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/report.py figures
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/render_qa.py render
# Inspect each actual rendered PDF page before recording visual QA.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/render_qa.py record
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/qa.py integrity
```

Full per-search ZIP retains initial population, exact terminal RNG/checkpoint/cache, generation/selection diagnostics, budget checkpoints and strict improvement sequences. Source and output hashes, full92 final permutations, failed setup details, negative outcomes and the disclosed amendment are preserved. No physical sampler is called by these scripts. Four PDF diagnostics require actual Poppler visual inspection before release. Remote publication verification downloads actual LFS bytes, not only pointer hashes.
