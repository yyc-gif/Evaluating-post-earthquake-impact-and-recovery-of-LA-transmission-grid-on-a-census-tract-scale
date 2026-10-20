# Controlled S05 publication integration plan

**Status: proposal only; author approval required.** Figure readiness is `READY_FOR_AUTHOR_APPROVAL`. Current figure/caption suite is pinned to revision remote `c0a11ffb4df523111efe6c8e65cfe86eadffec3c`; the source candidate is pinned to review `34c49469036354453c7b1f7fcef9cd92d14e8a3d`. Reverify both branches before an authorized promotion. No merge, official overwrite or formal-candidate replacement occurs in this package.

## Exact promotion targets

All paths in this table are repository-relative. Root for the untouched protected revision checkout is `C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision`; use a separate clean worktree for any subsequently authorized integration rather than writing over its staged work.

| Proposed target | Approved change needed | Source / guard |
|---|---|---|
| `results/figure_review/Supplement/FigS05.pdf` | Replace historical three-panel PDF with reviewed, unchanged four-panel candidate | `Additional_Evidence/Final_Pure_Random_GA_S05_20261012/FigS05_GA_Final_Candidate.pdf`; SHA-256 `58bc67206d0e418b1079a418ea2151fa75eca78e2e5365815b6d1c62db40432d`; 185 x 178 mm |
| `results/figure_review/Supplement/FigS05.png` | Replace preview with exact existing 600-dpi candidate | Corresponding `FigS05_GA_Final_Candidate.png`; use its recorded manifest hash; 4370 x 4204 pixels |
| `results/figures/FigS05_GA_Reproducibility.pdf` and `.png` | Synchronize byte-identical publication mirrors | Same approved source payloads, not a second renderer output |
| `results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md` | Replace S05 heading/body; qualify the old Direct-community identity sentences in Figure 4/S11/S12/S13 | New 312-word caption; audit C01-C12; keep all other numerical captions |
| `results/figure_review/FIGURE_MANIFEST.csv` | Update only two S05 PDF/PNG rows: source commit, actual payload hash, 185 x 178 mm dimensions, font metrics, renderer provenance and action | Retain prior record in history; use actual artifact-producing source rather than citing historical extended-GA renderer |
| `results/figures/FIGURE_INDEX.csv` | Update only S05's two rows: scientific question/message, source and generator, source data references and hashes | Match all 20 final100k receipts and old pure-random candidate's 2,000-case validation, not the POST cohort |
| `results/figure_review/Page_Previews/FigS05.png` | Refresh publication-size page preview | Render approved PDF at established preview settings; separate from 600-dpi source PNG |
| `results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf` | Replace supplementary page 4 only | Current 12 pages; keep S01,S03,S04,S06-S13 artwork payloads unchanged |
| `results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf` | Replace artwork p21 and caption p22; synchronize affected caption pages p8,p34,p36,p38 | Current 42 pages, with four existing complementary-evidence pages at end; retain all unrelated artwork and caption content |
| `results/figure_review/README.md` and `UPDATE_LOG.md` | Replace historical S05 description, record approved scoped promotion and separate cohorts | Do not claim GA is in the existing six-policy main plots |
| `results/figures/README.md` and `FIGURE_REVIEW_GALLERY.html` | Synchronize current-figure description/link/preview if needed | Keep 19 numbered figures and existing order; gallery source path does not change |
| `results/figure_review/Additional_Evidence/README.md` | Add final-method review/provenance link and retain historical experiment links | Do not mark this pending review approved before authorization |
| New scoped integration script and QA under `docs/reproducibility/` | Freeze actual approved source hashes, complete packet/native-size QA and preservation | Do not overwrite historical `figure_suite_integration_20261011` receipts as if they proved the new integration |
| Accessible authoritative working manuscript, GA Methods/Results/Discussion, Abstract, Conclusion, summary-table cells and reproducibility references | Apply only approved proposed GA edits and correct S05 A-D references | Full path/paragraph identity must be reconfirmed; inspected backup p4,p21,p25,p43,p47,p49/Table1r7 locations remain provisional |
| `docs/meeting/LA_Grid_Part_II_Methodology_Modifications_Meeting_Summary.docx` | If still distributed as current Methods, reconcile p50 and S05 references | Author-approved text-only revision; not the authority for the complete paper |

The full manuscript cannot presently be specified as an executable update target: the previously confirmed external working path is missing. Its known backup is an audit reference only, not a recovery source. Do not restore, overwrite or designate it current in this integration task. No journal-specific renumbering or bibliography overhaul is presumed.

## Scientific compatibility with the rest of the suite

- **Main Figures 1-7:** retain artwork. Figure 4 caption needs the historical Direct-community identity qualified, not an Impact-first-to-GA relabel. Figures 3/5 use decomposition/equity concepts but different policy questions and the original ensemble; they do not duplicate the seed evidence or fresh GA ECDF. No other current main figure contains a final GA curve.
- **S04/S06/S07/S08:** keep original network, assumption, source-route and capacity results. They do not validate the final GA across assumptions, prove delivered power, or identify D's station-level causal mechanism.
- **S11/S12/S13:** retain all fixed-rule values/artwork. Replace the three stale Direct-community-equals-Impact clauses; explicitly state that final GA was not evaluated in these displayed four-hazard/resource families. Do not infer GA performance at untested conditions.
- **Figure7/S09 and all Stage7:** unaffected and protected. Their separate typology revision status is not resolved by S05.
- **S05:** preserve original number, so other figure/table numbering need not change. Cross-references that formerly named A-C historical budgets now need A/B search and C/D fixed-candidate validation/accounting. Main-text prose should introduce a separate candidate-validation subsection, not change every original sample denominator to 2,000.
- **Historical S05:** retain existing files through Git and an explicitly historical provenance snapshot at promotion; retain deterministic-incumbent reports and original experiment records unmodified.

## Suggested promotion sequence, only after approval

1. Author approves unchanged candidate, concise caption, negative disclosures and narrow GA text changes; supply/reconfirm accessible complete manuscript.
2. Freeze source review/official heads, candidate permutation hash, original cohort identity, original payload hashes and preservation baseline. Do not evaluate anything anew.
3. In a clean authorized integration worktree, copy exact approved PDF/PNG payloads and update only caption/index/manifest/preview targets. Use a new scoped integration script so historical renderers cannot silently revert S05.
4. Rebuild only packets and current presentation metadata from already archived artwork/caption pages; no numerical analysis, plot fitting, optimizer or sampler is run.
5. Apply narrow text amendments to a separate author-review manuscript copy if approved; verify its actual source identity first. No backup recovery, global reformatting or unrelated section rewrite.
6. Visually inspect both packets at native 185-mm figure width; verify numbering, references, legends, text fonts, candidate/cohort hashes, unchanged other artwork and the 950-file/862-staged-item preservation guards. Commit/push scoped integration and verify actual LFS bytes and remote HEAD.

## Remaining author decisions

Approve this figure and caption; approve coordinated manuscript wording; provide or confirm the accessible current full manuscript. None requires another optimization study, fresh physical validation or bootstrap. No fairness claim, global-optimum claim, actual electricity-delivery claim or formal strategy promotion is warranted by S05 alone.
