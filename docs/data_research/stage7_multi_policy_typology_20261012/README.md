# Stage7 multi-policy diagnostic package

AUTHOR REVIEW — NOT FORMAL STAGE 7


Starting authority: `739420417412228f9302051d154f11ba3d5cde84`. This is an isolated controlled diagnostic, not formal Stage7. Main decision: `FINAL_P2_P3_AUTHOR_DECISION.md`. Numerical evidence: `K_SCIENTIFIC_EVIDENCE_MATRIX.csv`, ensemble values, policy-set sensitivities, all fitted labels and source records.

Reproduce in Python 3.12 using the repository environment (NumPy 1.26.4, pandas 2.2.2, SciPy 1.11.4, scikit-learn 1.5.1, Matplotlib 3.9.2, PyMuPDF 1.28.0). Limit BLAS/OpenMP to one thread as in the recorded run. Run these scripts in order from this directory:

```text
python audit_ensemble.py          # requires manifest-bound local frozen archives
python audit_information.py
python fit_registered.py
python verify_independent.py      # full source checks and exact registered spatial replays
python build_evidence.py
python write_reports.py
python make_figures.py
python verify_package.py
```

Set `LA_GRID_FROZEN_SOURCE_ROOT` only to the authoritative archive root if it differs from the archived default. No script executes physical simulation. For a clean Git clone, `git lfs pull` retrieves this package's verified compact station-integral/W snapshot and frozen descriptor table. `reproduce_from_snapshot.py` verifies the core ensemble quantities without needing all raw event files. Full event/source re-audit still needs the external archive and is not claimed clean-clone complete.

Review figures01-07 are data-only Matplotlib vector PDFs with 600 dpi previews. The profile PDF has four pages. Official geographic support is tract internal points, not verified neighborhood polygons. K5 profiles are seed42 illustrations only; competing seeds are retained and disclosed. All classes/IDs are diagnostic and model-specific. No method, input, quartile, formal result, manuscript or numbered figure is promoted or overwritten.

Sources, derived SHA256, independent numerical QA, visual QA and remote LFS delivery proofs are included. `REMOTE_DELIVERY_VERIFICATION.json` binds scientific payload bytes to the first delivery commit; the following provenance-only commit records that proof. Neither modifies formal science.
