# Repository cleanup decisions (recorded before deletion)

Scope: `revision/reviewer-driven-core-rebuild-v2` only. July submission archive is excluded. A complete pre-cleanup reviewer-worktree snapshot and file tree exist at `C:\2025-2026 Fall\Local_Recovery_Snapshot_20260925`. Git history also retains tracked deletions. Do not clean the worktree globally.

| Path | Category | Size | Git state | Decision | Reason | Replaced by |
| --- | --- | ---: | --- | --- | --- | --- |
| `Revised_Entry_Trial_20260922/Event_Archives/` | three-realization trial event outputs | included in 114,562,077-byte trial directory | tracked | DELETE | Diagnostic-only trial, not formal evidence or a supplement dependency | `Formal_Experiment_20260923/Formal_Trajectories/` and formal tables |
| `Revised_Entry_Trial_20260922/Offline_Mapping_Gate/` | trial offline outputs | included above | tracked | DELETE | Superseded by 1,000-realization formal offline evaluation | `Formal_Experiment_20260923/Formal_Offline_Evaluation/` and `Formal_Reviewer_Results/` |
| `Revised_Entry_Trial_20260922/Stage 1 Output_expanded/` through `Stage 7 Output_expanded/`, and `TRIAL_RESULTS/` | trial generated CSV/plots/intermediates | included above | tracked | DELETE | Trial scale cannot support final supplement claims | formal Stage 1–7 and Equity Amendment |
| `Revised_Entry_Trial_20260922/*.log` | development/failure run logs | small | untracked/ignored | IGNORE | Retain local failure logs rather than deleting untracked research evidence during branch cleanup | formal checkpoint and reports |
| `Revised_Entry_Trial_20260922/` identity, reports, and small diagnostic records | trial provenance | included above | tracked | KEEP | Retain concise audit trail; do not cite trial as final science | not applicable |
| `Formal_Experiment_20260923/Failed_Offline_Attempt_c341e27/` | failed intermediate attempt | 32,893,255 bytes, five files | tracked | DELETE NPZ/parquet/duplicate JSON payloads; KEEP `FAILURE_RECORD.txt` | Failed payload is not a final analysis input; failure provenance remains visible | successful `Formal_Offline_Evaluation/` |
| `Formal_Experiment_20260923/Formal_Trajectories/` | frozen formal trajectories | 1,669,251,984 bytes, 252,000 files | untracked local | KEEP | Needed for reproducibility and further plotting; never treat as trial | not applicable |
| `Formal_Experiment_20260923/Formal_Reviewer_Results/`, `Formal_Results/`, `Formal_Offline_Evaluation/`, Stage 1–7 formal outputs, `Equity_Amendment/` | final scientific results | varied | tracked and untracked | KEEP | Frozen result authority for manuscript and supplement | not applicable |
| `External_Validation_Data/`, `July92_Provenance/`, `R1_Comment1_2_External_Evidence_20260922/` | retained source data and evidence | varied | mixed | KEEP | Provenance and official external evidence | not applicable |
| `Submission_Package/`, `Manuscript_Figures/`, root `Stage * Output_expanded/` | submitted July artifacts | varied | tracked | KEEP | Historical submission/reference content; deletion from revision branch is unnecessary and may break crosswalk | not applicable |
| `.pytest_cache/`, `__pycache__/` | local cache | varied | untracked/ignored | IGNORE | No manuscript relevance; deletion not needed for a safe tracked cleanup | not applicable |

Potential duplicate or old figures outside these two deletion targets remain **KEEP** unless a byte-identical duplicate and lack of final references are both verified. There is no blanket file-name-based deletion. Untracked large formal archives are recommended for a separately verified off-repository backup before any move; no move is authorized by this log.
