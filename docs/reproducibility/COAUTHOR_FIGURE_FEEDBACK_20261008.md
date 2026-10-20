# Co-author figure feedback — 2026-10-08

Baseline: `8b0b75397a1a6dc152fde95289696ae63d71087d`; local and live remote HEAD agreed before editing. Actual PDF pages were rendered and opened before and after the edits. Presentation checks do not imply author acceptance.

| Comment | Action | Scientific boundary |
|---|---|---|
| Fig04A: group the key by strategy mechanism | Infrastructure-based: Degree/Centrality/Betweenness/Closeness. Community/equity-informed: Impact/Hospital/Vulnerability. Baselines: Unconstrained/Random. Existing curves, colors and emphasis retained. | Random is not misclassified as a network or equity priority; Impact/Hospital are community-service priorities, not asserted inequality objectives. |
| Fig04B: grouped tract outcomes | Three side-by-side horizontal bars per policy: all-tract, Q4 and hospital-tract service loss. Metric colors, a zero-based hour axis and 5th–95th realization ranges are explicit. T80 retains a separate point/range axis. | Same nine policies, same 1,000 2pc50/C57_D1 outcomes and same weighting definitions. Ranges are not confidence intervals. |
| Fig05A: identify Vulnerability-first | Direct label and arrow to the existing diamond. | No point moved. B–E retained. |
| S03B: remove supposedly repeated upper triangle | Not applied: this is a directed road-travel matrix, not a symmetric distance matrix. | 8,324 directed entries differ from their reverse direction; maximum difference is 0.07439625 h (4.4638 min). Both triangles contain information. Matrix and figure remain unchanged. |
| S06B: remove repeated Fig02D benchmark | Removed. Native cutoff, gate and threshold graphics retain their size and values; reflowed as A/B/C. | 337-tract public-record comparison remains once in Fig02D. No mapping changed. |
| S09: larger legend circles and PC5 arrow | Cluster swatch diameter increased 50% inside A. B arrow identifies “Five PCs selected.” | Saved eigenvalues select five PCs by eigenvalue >1. No new PCA/elbow analysis; PC5 is not falsely labeled a statistically established elbow. |
| S11: compact 2pc50 view | One heatmap, eight policies × four outcome columns, with a common symmetric true-hour scale and contrast-aware numeric labels. | Exact prior four-scenario PDF retained at `Additional_Evidence/Cross_Hazard_Policy_Contrasts.pdf`; historical comparisons were not deleted. |

## Actual output checks

All edited pages remain 185 mm wide. Current heights: Fig04 205 mm; Fig05 250 mm; S06 152 mm; S09 174 mm; S11 113 mm. Native Arial text is embedded. Minimum text is at least 7 pt. Preview PNGs are 600 dpi. Every edited page was opened: no legend/data overlap, clipped labels, crossing annotation text, or stray labels from removed panels remained. The complete packet was regenerated, retaining nineteen numbered figures and their captions.

The service-loss bars intentionally share a zero baseline; small differences are not exaggerated by truncated bar axes. Fig05 and the full outcome evidence retain distributional comparisons at a more detailed scale. T80 is not presented as another tract-population integral.

## Read-only sources

- `Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet`
- `Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet`
- `Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/pca_stats_with_eigenvalues.csv`
- `provenance/figure_review_history/candidate_v2.1/CROSS_HAZARD_POLICY_EFFECTS.csv`
- `data/travel/travel_task_to_task.csv`

Exact identities, displayed values and original artwork hashes are recorded in `COAUTHOR_FIGURE_FEEDBACK_20261008.json`. Scientific definitions, formal policies, mappings and trajectories were not changed. The existing 862 unrelated staged provenance entries are excluded from this round's commits.

## Completed validation

- `python -m pytest -q`: 49 passed.
- Canonical `run_all.py --resume`: all ten stages PASS_VALIDATE/PASS_REUSE; overall `PASS_ALL_STAGES_REUSE_OR_VALIDATE`.
- Protected scientific files: 260 checked, 0 changed.
- 1,367 unaffected committed LFS identities preserved. The 27 figure/index LFS pointers in the artwork commit matched their materialized SHA-256 values.
- July archive and main refs unchanged; original 862 staged provenance entries excluded and preserved.
