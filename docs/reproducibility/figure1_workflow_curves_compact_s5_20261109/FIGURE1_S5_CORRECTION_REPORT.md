# Figure 1 Module 4 and Supplementary Figure S5

## Source Decision

Figure 1 Module 4 now uses the saved workflow-generated artwork at `results/figure_review_s6_main4_20261107/Main/Fig01.pdf`, reproduced byte-for-byte from commit `ea692f4dd6d1763a91b4b8f5c11e45ce6a8a1f15`. Its matching PNG and page preview are also reused from that same workflow output. The pinned source curve table is `provenance/legacy_outputs/stage6/recovery_curves_all_system.csv` (SHA256 `b4a0889e12ed855f1f681b73dbb429306f513585fd00afe058480e6aa5a43922`).

The saved generation record identifies 9,601 source rows and 2,001 plotted observations per series over 0-100 h. It confirms the population-weighted mean `2pc50` Unconstrained and Impact-first trajectories and records that the surrounding Figure 1 content was unchanged outside Module 4. The exact output PDF SHA256 is `cf71e10f4df852c8bf559ffd9b129a1a12fd3183506c90dd4b892f4acb1affbf`; the matching PNG SHA256 is `4ba55682666c4b2d857e8337956adb53706a09be971c9e56445b5d593d4ff0c2`.

The caption states the two execution modes and clarifies that constrained Impact-first execution uses finite crews, sampled repair durations and directed travel. It also states that completion events update station functionality and source-gated tract service. The displayed curves are saved model outputs, not observed outages or an averaged repair schedule. Source connectivity remains part of service evaluation, not a restoration priority.

## Supplementary Figure S5

S5 is 185 x 145 mm (7.28 x 5.71 in). It retains panels A-C, all four policies, the saved means, paired 5th-95th realization ranges, controls and comparison definitions. Its plot-data SHA256 is `bb409d2a8dc514eec2e5cb546d5357b2803882ea044e1f27d8a787fda67cad2d`.

Measured visible margins from the 600-dpi PNG are 21.29 mm left and 21.12 mm right, a 0.17 mm difference. The complete bounds include row labels, axes, titles and legends. The PDF contains embedded Arial regular/bold fonts; the minimum extracted text size is 7.0 pt. Visual review at native width found all three panels, legends, four strategy rows and whiskers legible, with no clipping or overlap. The compact height comes from reduced inter-panel whitespace and repositioned legends, not uniform scaling.

## Figure 1 Visual Review

The final Figure 1 preview is at `results/figure_review_s6_main4_20261107/Main/Fig01.png`. Stage 4 visibly contains the Unconstrained and Impact-first curves, execution-mode labels, time axis and availability axis. Modules 1-3 and 5, their arrows and the page dimensions are inherited from the hash-verified workflow output rather than redrawn.

The prior manual-process version is preserved in Git at starting commit `cb3272058c0d1f244bcaff8d567876a198072ab0`, path `results/figure_review_s6_main4_20261107/Page_Previews/Fig01.png`. The prior 185 x 210 mm S5 is preserved at the same commit and path `results/figure_review_s6_main4_20261107/Supplement/FigS05.png`.

## Preservation and Tests

Compared with the starting branch, exactly four numbered artwork files changed: Figure 1 PDF/PNG and S5 PDF/PNG. The other 28 numbered artwork files are byte-identical. Mirrored artwork hashes match the manifest. Main, Supplement and complete packets contain 8, 8 and 16 pages, respectively.

The S6 promotion integration tests passed (13 tests), and the targeted `build_current_suite_p2.py` workflow-artifact regression passed (1 test). The entire `tests/test_current_figure_suite_integration.py` module is not runnable in this isolated S6 worktree: it expects an unmaterialized `results/figure_review/` P2 suite and unrelated diagnostics. Its failure is a missing-path setup limitation, not a failure of the corrected builder; the new builder-specific regression passes independently.

The initial isolated worktree was at `cb3272058c0d1f244bcaff8d567876a198072ab0` on `review/fig1-moduleD-s5-final-20261109`, with no staged changes. A local `.remote-lfs-verify/` cache was already untracked and is preserved as-is. No source simulations, models, manuscripts or unrelated scientific results were changed.
