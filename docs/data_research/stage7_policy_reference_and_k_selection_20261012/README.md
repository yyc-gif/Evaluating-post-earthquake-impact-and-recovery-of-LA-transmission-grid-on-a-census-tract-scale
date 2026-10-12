# Stage 7 policy-reference and K-selection diagnostics
AUTHOR REVIEW - NOT FORMAL STAGE 7

Start: 66d16d61b13c05785f58795ef9d13ba82ece472e. Read FINAL_POLICY_AND_K_AUTHOR_DECISION.md first. This isolated package changes no formal scientific outputs.

Python 3.12; see requirements-diagnostics.txt. Set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS and MKL_NUM_THREADS to 1 for deterministic registered fits. Run from this package:

```powershell
python audit_policies.py
python fit_registered.py
python build_evidence.py
python write_reports.py
python make_figures.py
python verify_independent.py
python verify_package.py
```

audit_policies.py requires the original read-only manifest-bound Formal_Experiment_20260923 archive. Set LA_GRID_FROZEN_SOURCE_ROOT to its checkout path; the default only records the local reference location. The preceding audit's verified Sources reader resolves commit/LFS-bound files from that checkout, sibling audit worktrees or the common LFS object cache. It never imports/runs physical model stages. Clean-clone post-processing can instead begin from the committed VERIFIED_FIXED_FEATURES_2315.csv and POLICY_REFERENCE_TRACT_METRICS.csv (git lfs pull first); fit_registered.py additionally verifies the preceding rare-ID, label and geographic source tables. Supply a cache/checkout with those actual LFS bytes. Full preservation/source tests require the protected scientific archive.

REGISTERED_ANALYSIS.json predeclares settings; all 960 fit records, full labels and silhouettes, 672 spatial checks and scaler matrices are retained. Two scalers are not scientifically equivalent. No unregistered feature search or weight optimization is performed. Generated content is confined to this package. The package's default external path is an operational archive locator, not an input substitution; no formal data are modified.

pdf_review/ is an ignored rendering scratch area; figures/ contains vector PDFs and 600-dpi PNGs. VISUAL_QA.json records actual publication-size review. All preceding diagnostic packages and 950 protected scientific files are independently hash-checked. Git delivery is restricted to this package; no merge, release or formal Stage7 promotion is authorized.
