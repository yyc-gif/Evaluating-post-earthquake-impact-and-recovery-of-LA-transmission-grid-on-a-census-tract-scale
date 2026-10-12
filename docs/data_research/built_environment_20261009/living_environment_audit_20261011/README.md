# Stage7 living-environment measurement audit

Start with LIVING_ENVIRONMENT_CONSTRUCT_DECISION.md, DATA_AVAILABILITY_AND_PROVENANCE.md and CANDIDATE_ADMISSION.csv. CORE3/W1 is an archived reference, not an approved final feature set.

Values are in LIVING_ENVIRONMENT_VALUES_2315.csv, LIVING_ENVIRONMENT_VALUES_RESIDENTIAL_2291.csv and LIVING_ENVIRONMENT_VALUES_REFERENCE_2287.csv. Fractions, original survey counts, uncertainty and continuous geometry/support flags are retained. Four unresolved geometry IDs remain in the residential master; no labels or missing physical variables are imputed.

Required coverage/distribution/uncertainty/redundancy tables are present with exact comparison GEOID sets. Figures are under figures/, with native185-mm vector PDFs,600-dpi page PNGs and rendered native-width previews. These are measurement diagnostics, not replacements for manuscript figures.

Reproduction using the recorded Python environment: verify_sources.py (checks/replays ledger only when requested), audit_values.py (reads original source byte identities and already acquired measurements), finish_measurement_checks.py (reuses cached land-mask bytes), write_reports.py, render_figures.py, then pytest test_measurements.py. No new source request is needed for cached reproduction. audit_values.py repeats only tract-level measurement/support arithmetic; it never reruns restoration, scheduling, mapping, GA or clustering. Original cached inputs are resolved by exact Git/LFS hashes; INPUT_HASHES.json records actual local byte locations. Source downloads are snapshot data, not promises that a live URL always returns identical bytes.

Run pytest with a workspace-local --basetemp. See TEST_RESULTS.txt, NUMERICAL_AND_RENDER_QA.json, PRESERVATION_BEFORE/AFTER.json and REMOTE_DELIVERY_VERIFICATION.json. Only this new package is committed; the original checkout/index,950 protected scientific files and prior audit packages remain unchanged.
