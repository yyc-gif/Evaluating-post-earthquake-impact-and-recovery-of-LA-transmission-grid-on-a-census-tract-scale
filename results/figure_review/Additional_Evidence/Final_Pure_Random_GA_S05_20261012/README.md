# Final pure-random GA methodology and proposed S05

Author-review package only. Base: verified remote manuscript branch `c0a11ffb4df523111efe6c8e65cfe86eadffec3c`. Isolated branch: `review/final-pure-random-ga-figs05-20261012`.

## Main Review Files

- `FigS05_GA_Final_Candidate.pdf`: four-panel vector candidate, 185x178 mm.
- `FigS05_GA_Final_Candidate.png`: 600-dpi preview.
- `S05_Existing_vs_Proposed_REVIEW.pdf`: both vector figures at 185 mm on a comparison sheet.
- `PROPOSED_MANUSCRIPT_CAPTION.md`: complete caption including post-data choice, failed 90% single-run rule and negative equity consequences.
- `FINAL_GA_METHOD.md` and `FINAL_GA_CONFIGURATION_AND_CANDIDATE.json`: frozen algorithm, full 92-ID sequence and original provenance.
- `EXISTING_VS_PROPOSED_S05_AUDIT.md`: historical inconsistencies and retained development evidence.
- `NUMERICAL_AND_VISUAL_QA_REPORT.md`, `NUMERICAL_QA.json`, `PDF_TECHNICAL_QA.json`, `VISUAL_QA_REVIEW.json`: numerical, technical and actual-render review.
- `SOURCE_DATA_PROVENANCE_MANIFEST.json` and `SOURCE_EVIDENCE.zip`: 86 original source payloads, versions, URLs and SHA-256 identities.
- Five plotting/source-summary CSVs and `PANEL_A_MEDIAN_ARCHIVE.csv`: reusable figure data and saved inferential outputs.
- `PRESERVATION_BASELINE.json` / `PRESERVATION_VERIFIED.json`: 950 protected files and 862 staged items; no original checkout or figure edits.
- `OUTPUT_HASH_MANIFEST.json`, `REMOTE_PUBLICATION_VERIFIED.json`, `FINAL_REMOTE_HEAD_VERIFIED.json`: output integrity and actual remote payload checks, recorded after publication.

## Reproduction Without New Numerical Experiments

Use `C:\Users\yinch\anaconda3\python.exe` with NumPy/pandas/Matplotlib/PyMuPDF installed. The bundled runtime was inspected; its Python lacked Matplotlib, so the established Anaconda scientific runtime is used. Poppler rendering uses the bundled `dependencies/native/poppler/Library/bin/pdftoppm.exe`. Scripts read archived results only; never execute any search or physical sampling entrypoint stored in the source archive.

From the isolated worktree:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:GIT_OPTIONAL_LOCKS = '0'
$env:MPLCONFIGDIR = '\\?\' + (Join-Path (Get-Location) 'results/figure_review/Additional_Evidence/Final_Pure_Random_GA_S05_20261012/runtime/mpl')
& C:\Users\yinch\anaconda3\python.exe results/figure_review/Additional_Evidence/Final_Pure_Random_GA_S05_20261012/study.py render
& C:\Users\yinch\anaconda3\python.exe results/figure_review/Additional_Evidence/Final_Pure_Random_GA_S05_20261012/study.py qa
& C:\Users\yinch\anaconda3\python.exe results/figure_review/Additional_Evidence/Final_Pure_Random_GA_S05_20261012/test_archived_s05.py
```

The `prepare` phase additionally reassembles evidence from four diagnostic worktrees and the verified manuscript-base commit, asserting their branch/HEAD identities and read-only preservation baseline. It is intended for the initial isolated worktree at the recorded base commit, not as a reason to reset a completed branch. Normal figure regeneration/tests need only committed archive/CSVs and never use a physical evaluator. The `preservation` phase requires the original local protected/source checkouts; `remote` uses the existing actual-download verifier and writes only this package's receipt/runtime files.

No new searches, simulations, bootstrap or selection. No manuscript prose, formal results, official figures or Stage 7 files changed. The later engineering correction and its candidate must not be presented as sharing this prior candidate's validation evidence.
