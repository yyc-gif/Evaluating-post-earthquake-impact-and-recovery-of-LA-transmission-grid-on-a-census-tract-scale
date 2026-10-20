PATH B LOCAL FIGURE 7 & ELSEVIER PACKAGE — 14 OCT 2026

AUTHOR DECISION
Primary model: seven-variable P2; main classification saved P2/K3/seed42; mandatory P2/K4 sensitivity. NCV14 supplemental context only.

FILES
PART_V_Path_B_Seven_Variable_Figure_Structure.docx
  Revised PART V figure matrix in the layout of the supplied Markdown (main F1-F7; current supplement S1-S10). Author-review wording; F7 and S8 have not yet been installed in the formal suite.
Path_B_Elsevier_Figure_Captions.docx
  Separate Word captions for seven main and ten supplementary figures, preserving the approved realization-percentile / bootstrap-CI distinctions.
local_figure7_elsevier_preflight.py
  Runs INSIDE your Windows/local Git checkout using actual Git-LFS figure files. Audits page size, font embedding, raster/vector structure, line widths, banner, and expected hashes. With --export creates clean candidate PDF copies without the review banner in an isolated output folder. Never overwrites source PDFs.
LOCAL_CODEX_Path_B_Elsevier_Finalization.md
  Detailed local Codex task to complete color-accessibility and publication-size QA, preserve model and numbering, and stage the coordinated review. No remote integration authorization.

RUN IN LOCAL REPOSITORY
python local_figure7_elsevier_preflight.py --repo "C:/path/to/your/_pb13"
python local_figure7_elsevier_preflight.py --repo "C:/path/to/your/_pb13" --export

The preflight script needs the original LFS payloads materialized, PyMuPDF installed, and source PDFs still matching the reviewed snapshot. Neither this sandbox nor this package contains those LFS figure bytes. The figure sources were not redrawn or submitted from this container.

NEXT STEP
Copy the files to your isolated local worktree and give the LOCAL_CODEX prompt to the local coding agent. Review the resulting final-size visual proofs and identify the intended Elsevier journal before authorizing formal artwork/manuscript promotion.
