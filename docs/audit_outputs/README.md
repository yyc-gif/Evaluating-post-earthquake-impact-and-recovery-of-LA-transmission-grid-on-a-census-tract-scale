# IJDRR-D-26-02276 audit outputs

These files support the technical audit in `../IJDRR_D_26_02276_TECHNICAL_AUDIT.md`.

- `ISSUE_MATRIX.csv` records each reviewer concern, manuscript statement, code/output evidence, consequence, and A-E disposition.
- `cross_scenario_policy_comparison.csv`, `crew_rankings.csv`, `same_fitness_comparison.csv`, and `policy_group_burdens_CDC2022.csv` contain the main comparative results.
- `beneficiaries_and_delays.csv` reports tract and resident counts for conditional model improvements or delays.
- `full_curve_reproduction_check.csv` and `sample_reconstruction_check.csv` document the bounded reconstruction checks.
- `topology_diagnostic_summary.json` and `proposed_line_check.json` document the bounded topology checks.

The audit did not run the full pipeline or re-optimize the GA. It reconstructed one scenario with four retained schedules. Raw reviewer files, manuscript copies, Monte Carlo arrays, and full local audit intermediates are intentionally excluded from this public repository.
