# Co-author map and legend corrections — 2026-10-08

Baseline: revision/reviewer-driven-core-rebuild-v2 at 515024e19d060d283d85f2a8b3d74072e03b1c32.

| Comment | Implemented display change |
|---|---|
| Fig07 feature medians | One dashed median per feature: the cluster with the largest median feature value. All five density curves remain; their native curve operators are preserved. This selects the rightmost median, not the tallest density peak. |
| Fig07 Top-10 boundaries | Black, 0.60-pt outlines on the hotspot panel only. |
| Fig07 N/A and regional border | The same 24 N/A tracts are white, with no hatch. The study-region outline is gray, 0.80 pt, slightly thicker than the hotspot outline. Membership, hotspot scores and the selected ten IDs are unchanged. |
| S04 B/C legend | The shared key uses Fig04A's infrastructure-based, community/equity-informed and baseline groups. The separate static-removal key is unchanged. No policy or curve is removed. |
| S03 travel matrix | Upper-triangle display cells are hidden; lower triangle and diagonal are preserved. The road matrix is directed: opposite travel directions are not assumed equal. The full original matrix remains unchanged and used by the model. |
| S06 threshold panel | Former C splits into C (0.05) and D (0.75), each compared with 0.50. Both use the same -0.17 to +0.05 h axis and zero line. Means and 5th–95th realization-range endpoints are copied literally from the existing display record. The cutoff panel remains native at its original size. |
| S07 A explanation | The caption states the early increase in full-network source connectivity, the 24/48-h differences from the fixed path, and later convergence. Exact source values are recorded in the accompanying JSON. No curve changes. |

All affected figures were opened as rendered actual PDFs/PNGs. They retain 185-mm width, Arial text at least 7 pt and 600-dpi PNG previews. The current publication copies are byte-identical to the review artwork. The complete packet contains 19 figures and their following captions, 38 pages.

Scientific operations: none. The 260 protected scientific file hashes are unchanged, including the registered physical inputs and numerical authorities. Trajectories, schedules, mapping, clustering, capacity and all numerical tables remain unchanged. Tests: 49 passed.

The full directed travel matrix has 8,324 non-diagonal entries that differ between directions; the maximum difference is 0.0743963 h. Showing the lower triangle is a display choice, not a declaration of symmetry.

The original 862 staged provenance changes remain separately staged and are excluded from this task's commits. Canonical resume status and LFS verification are recorded in COAUTHOR_MAP_LEGEND_VERIFICATION_20261008.json after validation.
