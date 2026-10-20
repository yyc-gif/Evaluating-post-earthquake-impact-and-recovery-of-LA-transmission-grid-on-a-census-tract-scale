# Reproduction

Python 3.12; recorded versions are in `TEST_RESULTS.json`. In addition to the
repository's scientific dependencies, this figure production path uses
PyMuPDF 1.28.0, ReportLab 4.4.9 and pytest 7.4.4. Windows Arial/Arial Bold fonts
are required by the retained artwork-editing code. No platform-independent
font substitution is certified here.

```powershell
git lfs pull
git lfs fetch --include="results/figure_review/**,results/figure_review/*" origin 3c7899f0f328d37b99d2b022f1650c5288a4a664
python src/la_grid/plotting/source_only_frozen_control_20261013.py
python src/la_grid/plotting/build_current_suite_k3.py --portable
python -m pytest tests/test_current_figure_suite_integration.py -q
```

`--rebuild` forces deterministic frozen-source rendering. Otherwise the builder
verifies the source-code and output hashes before allowing a byte-identical
replay. Rerunning the canonical command preserves continuous S01-S10 numbering,
the corrected wording, source-only control and cool population palette.

The previous `--historical-ncv14` and `--historical-candidate-a` modes are retained
for historical reproduction, not for writing the current active suite. Run
those modes only in a separate historical worktree.

`source_only_frozen_control_20261013.py --acquire` is an optional authority-refresh
operation requiring the original local frozen offline archive. It was executed
once in this round. Normal reproduction uses the committed compact inputs and
does not need that archive. It does not run damage, schedules, GA or trajectories.

The independent preservation script `verify_corrections.py` also checks the
original research checkout and untouched source-figure worktree. Those local
checks require the original paths. Portable users can run the pytest arithmetic,
manifest, mirror, packet and frozen-source tests without those local checkouts.
If the original checkout is absent, portable rebuilding retains the historical
preservation record and explicitly reports that it was not reverified locally.

The actual local environment used Anaconda Python and appended the bundled
ReportLab site-packages directory; it did not replace Anaconda's NumPy with the
bundled NumPy version. Input/output hashes and the replay result are recorded
in the adjacent JSON records.
