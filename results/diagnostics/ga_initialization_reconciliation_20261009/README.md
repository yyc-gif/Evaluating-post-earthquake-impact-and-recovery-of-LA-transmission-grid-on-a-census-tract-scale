# GA initialization and parameter evidence

Completed diagnostic evidence for the unchanged 64-realization planning model. The formal GA candidate and manuscript figures remain as before.

- [Decision and recommendations](GA_INITIALIZATION_AND_PARAMETER_DECISION_20261009.md)
- [Initialization effects and control limitations](INITIALIZATION_EVIDENCE_AND_LIMITATIONS.md)
- [Higher-budget parameter evidence](HIGHER_BUDGET_PARAMETER_EVIDENCE.md)
- [Diagnostic plot](GA_INITIALIZATION_AND_PARAMETER_EVIDENCE.pdf) and [caption](GA_INITIALIZATION_AND_PARAMETER_EVIDENCE_CAPTION.md)

The two cloud studies contribute 610 unique final-budget observations after representation deduplication. Thirty initialization seed identities include the twenty higher-budget identities; they are not fifty independent seeds. The bounded parameter follow-up contributes 180 new case/seed observations at 100k distinct queries, with completed baseline controls reused.

`cloud_artifacts/` contains all 50 exact downloaded archives. `CLOUD_ARTIFACT_MANIFEST.json`, `OBSERVATION_SOURCE_INDEX.csv` and `DUPLICATE_REPRESENTATION_AUDIT.csv` connect observations to artifact IDs, commits and immutable checksums. `MATCHED_20K_CHECKPOINT_AUDIT.csv` records prefix parity. The filename uses the source study's terminology; the plotted and reported uncertainty is across paired GA seeds.

`parameter_100k/<case>_s<seed>/` contains RUN.json, CHECKPOINTS.json, STRICT_IMPROVEMENTS.json and the complete compressed generation history. Every new run records configuration, counts, budget, actual generations, final chromosome, SHA-256 and CPU/attempt accounting. The cloud artifacts retain only chromosome identities, not full final sequences; this limitation is disclosed.

`PAIRED_INITIALIZATION_EFFECTS.csv` and `PAIRED_PARAMETER_EFFECTS.csv` report mean/median changes, paired 95% t/percentile-bootstrap intervals and comparison-family intervals. Numerical win rates have Wilson intervals and a 1e-10 h arithmetic-parity threshold, which is not a scientific tolerance. Repeated budget checkpoints are not independent replications. Tolerance-containment tables are descriptive; no equivalence margin was approved.

Reproduce the read-only analysis from the saved records with PYTHONPATH=src:

```text
python -m la_grid.diagnostics.ga_initialization_reconcile_20261009
python -m la_grid.diagnostics.ga_initialization_evidence_report_20261009 --initialization
python -m la_grid.diagnostics.ga_parameter_evidence_report_20261009 --plot
python -m pytest
```

These commands analyze existing records. They do not invoke the parameter search runner or any physical sampling/evaluation stage. The scoped preservation baseline, source parity and validation receipt accompany the evidence. No formal promotion was performed.
