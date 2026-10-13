# Reproduce the adopted figure presentation

This changes figure presentation only. Archived formal Stage 7 data and the manuscript have not been migrated. Do not call run_stage_7, a clustering fit, scheduling or recovery simulation to reproduce this suite.

## Sources

- Approved 17-figure presentation baseline: `59d9001edadef57c5ff1dc6af6ca8d7817fb4f94`, branch `review/official-figure-suite-final-s05-20261012`.
- Scientific source review: `49cc153c3f4d7a8c29cf94baf090dbfc0be4d068`.
- Frozen NCV14/H2/K3 features, standardizer and saved labels: `0c5365cc39e2717e0fab4aa3b5d05b445d427eb6`.
- D3 authority and frozen five-policy means: `05a78645b17bf8de04326e54181f9db432d7186c`.

The current figure-specific inputs are extracted under `inputs/`. K4 membership columns/arrays are deliberately excluded. The original full source files remain unchanged in their source branches. Source records include exact Git blob, LFS OID, actual byte count and SHA256.

## Commands

Use Python 3.12 with the repository scientific dependencies plus the figure-only dependencies below. Arial must be available (the verified environment uses Windows Arial). No installation of dependencies changes scientific source data.

```powershell
python -m pip install -r requirements.txt
python -m pip install -r docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/figure-requirements.txt
git fetch origin review/official-figure-suite-final-s05-20261012 review/stage7-natural-hazard-k3-k4-integration-20261012 review/stage7-fig7d-integration-gate-20261013
git lfs fetch origin 59d9001edadef57c5ff1dc6af6ca8d7817fb4f94 0c5365cc39e2717e0fab4aa3b5d05b445d427eb6 05a78645b17bf8de04326e54181f9db432d7186c --include="results/figure_review/Main/**,results/figure_review/Supplement/**,results/figure_review/Page_Previews/**,results/figure_review/FIGURE_MANIFEST.csv,results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf,results/figures/FIGURE_INDEX.csv,docs/reproducibility/author_suite_final_layout_20261012/*.csv,docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/candidate/**,docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/inputs/EXISTING_K_EVIDENCE.csv,docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/inputs/EXISTING_STABILITY.csv,docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/inputs/SAVED_LABELS_AND_SILHOUETTES.npz,docs/data_research/stage7_fig7d_policy_robustness_and_final_integration_gate_20261013/*.csv" --exclude=""
git lfs pull --include="results/figure_review/**,results/figures/**,docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/**" --exclude=""
python src/la_grid/plotting/build_current_suite_k3.py --portable
python -m pytest tests/test_current_figure_suite_integration.py
python src/la_grid/plotting/build_current_suite_k3.py --portable
```

The second build validates and reuses identical current bytes. If the generator or an output changes, the frozen baseline is reapplied before the accepted K3 layer. The four dated historical entrypoints now default to the current builder; `--historical` explicitly invokes their unchanged historical numerical/presentation routines. Use historical mode only in a separate historical worktree.

## Preservation and portable replay

In this author's workstation, a build compares the 950 protected scientific files and the original revision worktree's HEAD, status, staged names and binary index before/after. A clean clone without that unrelated original worktree cannot perform its local preservation check. Use `--portable` to replay the current frozen figure layer without claiming a check of an absent original worktree. Source hashes, numeric checks and the figure tests remain mandatory. No local simulation archive is required for these figures: all figure sources are commit/LFS-bound.

Outputs: `results/figure_review/` is authoritative; `results/figures/` mirrors its numbered artwork. The complete packet must have 38 pages and exactly 17 figure/caption pairs plus four unchanged evidence pages. Optional D2 evidence is unnumbered and is not inserted into the packet.

The workstation used Anaconda Python 3.12 with its NumPy 1.26.4/Matplotlib 3.9.2/GeoPandas 1.1.1 and bundled ReportLab appended after installed scientific packages. It did not mix the bundled NumPy 2 environment with the scientific environment.
