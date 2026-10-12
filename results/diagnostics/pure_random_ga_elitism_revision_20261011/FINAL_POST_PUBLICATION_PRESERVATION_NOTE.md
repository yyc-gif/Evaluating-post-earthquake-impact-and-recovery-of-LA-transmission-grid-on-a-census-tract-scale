# Late external manuscript path exception

The strict preservation comparison in `REPRODUCIBILITY_AND_PRESERVATION_QA.json` passed after the experiments, native production checks and raw-archive verification. Following remote publication, the additional final recheck encountered a missing external manuscript directory. The earlier PASS is a real earlier observation, not proof that this path remains available now.

The original path is:

`C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/LA_grid_manuscript_rebuild/LA_Grid_Manuscript_Resubmission_Rebuild.docx`

Its recorded SHA-256 is `a61472ed6918f505dfd0c26b88ce24f9d184f6dca076194b5032014142acd253`. A read-only filename search found two backup copies. The copy under `Local_Recovery_Snapshot_20260925/Private_Backup_Small/private-la-grid-research/manuscripts/` has exactly these baseline bytes; the similarly named `Private_Backup_Staging` copy does not match and is not substituted.

No manuscript was restored, copied, edited or designated as a new authoritative version. The external disappearance cause is unknown. The only cleanup performed by this task resolved and checked forty directories inside `_ger14/results/diagnostics/pure_random_ga_elitism_revision_20261011/runtime/`, after matching all archived members. It did not target the external manuscript directory.

`post_publication_check.py` separately verifies all 950 scientific hashes, the original 862 staged items and staged-diff/index/status/branch/HEAD identities, prior scientific source checkouts, prior parameter payloads and the complete diagnostic payload manifest. The resulting receipt records this one external-path exception explicitly rather than masking it or declaring an unqualified full-preservation PASS. Author confirmation of the current manuscript location remains outside this algorithm-development task.

The completed elitism calculations, paired analysis, engineering recommendation and candidate non-promotion remain unchanged. Remote payload-byte verification at commit `549ca6b7e7f91dba44cc1544e73245d79cbc321b` passed; later commits add only ordinary-text verification records and this preservation exception.
