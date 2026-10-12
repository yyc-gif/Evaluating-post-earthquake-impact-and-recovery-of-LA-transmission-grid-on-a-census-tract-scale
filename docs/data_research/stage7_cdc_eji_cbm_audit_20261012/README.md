# Standalone CDC EJI2024 climate-burden audit
AUTHOR REVIEW - NOT FORMAL STAGE 7

Start `022f3f9a8a1fb3e454de05559311f1763a2ebb3b`. This package is isolated diagnostics, not formal Stage7. Read `FINAL_CBM_AUTHOR_DECISION.md` first. No new clustering fits: source-quality admission is unresolved.

Reproduction (Python3.12; repository dependencies plus requests/PyMuPDF/tabulate):
1. `python initialize.py` only at the starting authority in a clean isolated worktree; records hashes and source dirty state.
2. `python acquire.py --phase metadata`, `--phase discovery`, `--phase bulk`, `--phase query` (network only if archived snapshots absent).
3. `python audit_cdc.py`
4. `python information_audit.py`
5. `python reports.py`
6. `python figures.py`
7. `python verify_independent.py`

Run scripts from this package or pass their absolute path. Source resolver first uses clean-clone tracked files, then declared local frozen worktree fallbacks. Set LA_GRID_FROZEN_SOURCE_ROOT when full frozen local archives are needed. No formal-source outputs are overwritten. If a source is absent, resolution fails rather than inventing records. Git LFS pull is required for original ZIPs, tables and figures. Original source download failures/transfer-limit recoveries are documented. Review figure renders are for publication-size QA.

Policy/hazard/physical source inputs remain frozen:2pc50,C57_D1,M1_UTILITY_003,G1_BASELINE_050,480h,1,000 matched realizations; P2 MeanDelta is the equal descriptive mean of Impact/Hospital/Degree/Betweenness/Vulnerability-first increments, not a future-policy probability. Existing SOVI groups remain unchanged. Contacting CDC for missing flags is proposed, not performed.
