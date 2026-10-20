"""Figure-facing decision record; no paper text or scientific stage is edited."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

if __name__=='__main__':
    r=ROOT/'results/figure_review'
    memo='''# Figure suite update summary — 2026-10-12

Branch: `review/official-figure-suite-final-s05-20261012`.
Official-suite baseline: `c0a11ffb4df523111efe6c8e65cfe86eadffec3c`.
Approved S05 artwork: `34c49469036354453c7b1f7fcef9cd92d14e8a3d`.
Caption/integration review: `0d3d30cd3ce5a5503ff1711371a82c571eb85cef`.
The current user task authorizes S05 integration. The older approval plan's manuscript targets are explicitly outside this batch.

| Item | Decision/action | Current target |
|---|---|---|
| S05 | OFFICIALLY INTEGRATED into numbered paths on this branch. Approved PDF/600-dpi PNG copied without alteration; approved concise caption body copied exactly. The older three-panel S05 is historical. No formal strategy is replaced. | `Supplement/FigS05.pdf` / `.png` |
| Fig1 | RETAIN CURRENT ARTWORK; unresolved review comment documented below. No invented missing content. | `Main/Fig01.pdf` / `.png` |
| Fig4D | NOT APPLICABLE TO CURRENT FIG4. Current Fig4 has A/B recovery/outcome graphs and no D map. No map is invented or added. | `Main/Fig04.pdf` / `.png`, unchanged |
| Fig7C/D N/A | White fill and 0.45-pt dark-gray boundary on the exact existing 24 N/A tracts in each map; white bordered legend swatch. Study outline/Top-10 outlines retained. | `Main/Fig07.pdf` / `.png` |
| C4 | Replace slate #7b828f with muted indigo #8a83b8, synchronized across Fig7A/C and S9A/legends. Other four category colors unchanged. Formal five-class assignments, PCA and hotspot ranks unchanged. | `Main/Fig07`, `Supplement/FigS09`; `CURRENT_CLUSTER_PALETTE.json` |
| S10 | C remains tract population with its exact logarithmic range and scalar colorbar indices. Replace gray palette by truncated sequential YlGnBu (t=0.15..0.85). Stations, first-five priorities, geometry and text unchanged. A/B unchanged. | `Supplement/FigS10.pdf` / `.png` |
| S11 | REDUCED TO 2pc50, six fixed policies × four outcomes. Print the exact saved mean contrasts; common linear scale 0 to the saved maximum (9.46 h when rounded), no white divider and no signed-log transformation. | `Supplement/FigS11.pdf` / `.png` |
| S12/S13 | KEEP_SEPARATE. Crew availability and repair duration are different OFAT families with different controls; each shows four outcomes for all six selected policies. A merged eight-panel page would shrink axes or become too tall. Main Fig6 already juxtaposes the two contrast families. S12/S13 PDF/PNG bytes retained exactly. Fresh S13 rendering confirms that its legend, A-D titles and axis labels are complete; regenerated PNG/preview match the existing bytes. | `Supplement/FigS12.pdf`, `Supplement/FigS13.pdf`, unchanged |

## Figure 1 diagnosis

Actually inspected the official 185 × 220-mm PDF render, its current packet page, caption, `update_framework_figure.py`, and the pinned later presentation edits. All five framework stages are present. The input groups, damage-state/repair-duration labels, source-connected service chain, crew dispatch, policy recovery, community outcomes and tested conditions are labeled. Stages 1/2 now join before a single arrow into Stage3. The panel numbering/titles are aligned. No missing stage, detached connector, TODO or unfilled placeholder is evident.

The four Q1-Q4 bars are intentionally labeled “Schematic”; the caption already states that they are not estimated means or additional scientific results. They should not be filled with invented numbers. The current framework describes the original scheduled-policy analysis; final GA validation in S05 is separate and does not authorize a new framework or formal policy replacement.

Likely remaining concerns are whether the intentional schematic is being mistaken for an unfinished quantitative chart, whether the co-author viewed an older export, or a desired graphical detail not specified in the comment. None identifies a concrete missing scientific element. Figure1 is therefore retained, and an annotated location is needed before claiming the co-author's “not finished” comment is resolved.

## S11: retained and removed information

Retained the original 2pc50 means for Impact-first, Hospital-first, Degree-first, Vulnerability-first, Betweenness-first and Random relative to Unconstrained. Outcomes remain all-tract population-weighted service loss, Q4 population-weighted service loss, hospital-linked equal-tract mean service loss and population T80. These are the original 1,000-case comparisons, not the final GA's 2,000-case cohort. Saved uncertainty ranges remain in the source table and are not drawn in this mean heatmap.

Long Beach, San Fernando and Northridge are removed from numbered S11, not from the evidence. Their roughly 0.1–0.5-h effects were visually displaced by the 2pc50 scale in the shared four-panel design; the subsequent signed-log palette made even small positive differences conspicuously red. The cleaner one-scenario linear presentation serves the requested interpretation without nonlinear color spacing. S11 now makes fixed-policy increments explicit; Fig4 shows absolute outcomes and temporal recovery. The numerical source is reused, so this complement is not presented as an independent scientific result.

The prior four-scenario six-policy S11 PDF/PNG and caption are preserved in `provenance/figure_review_history/official_suite_update_20261012/`. Existing `Additional_Evidence/Cross_Hazard_Policy_Contrasts.pdf` is unchanged. S05 history is preserved in the same provenance snapshot and in its original review commits.

## Packaging and safeguards

Seven Main and twelve Supplement figures remain in the same numbered structure (S02 is already integrated into S01). PDF/PNG mirrors, manifest/index, page previews and the three packets are synchronized; figure pages retain native 185-mm width. Captions changed only for S05 and the requested S7/S10/S11 display details, plus the narrow Fig4/S12/S13 clarification that historical Direct-community coincidence does not describe the final GA. No broader paper prose, DOCX, manuscript PDF, formal candidate sequence, simulation, scheduling, trajectory, PCA, clustering or bootstrap output is changed.

Source/payload hashes, original 950-file and 862-staged-item checks, tests and actual visual rendering checks are recorded under `docs/reproducibility/official_figure_suite_review_20261012/`. Commit and remote verification are recorded there and reported on delivery. This isolated branch is not automatically merged into the revision branch.

## Remaining author clarification

1. Identify the specific unfinished location in the current Figure1, if it differs from the already corrected connector and intentional schematic.
2. Identify which map “Fig4D” refers to; current Figure4 has no such panel.

No new optimization or scientific rerun is needed for the completed figure changes.
'''
    u.write(r/'FIGURE_SUITE_UPDATE_SUMMARY_20261012.md',memo)
    u.write(r/'UPDATE_LOG.md','# Current figure update\n\nSee [the complete scoped summary](FIGURE_SUITE_UPDATE_SUMMARY_20261012.md) for S05 integration, current target paths, Fig1/Fig4D diagnosis, white N/A boundaries, synchronized C4, population S10, 2pc50 S11 and KEEP_SEPARATE for S12/S13.\n\nThe previous rounds remain in Git and immutable provenance. All unrelated artwork remains unchanged.\n')
    readme='''This is the single author-review source for the current submission figure set. Do not retrieve submission figures from older review folders.

# Current complete figure suite

This figure-only integration branch is `review/official-figure-suite-final-s05-20261012`, based on the latest verified revision artwork at c0a11ff. It has not been merged automatically into the revision branch.

- [Complete figures and captions](ALL_FIGURES_WITH_CAPTIONS.pdf): Main01-07, then S01/S03-13, each followed by its caption; the four existing complementary-evidence pages follow.
- [Main](Main/) and [Supplement](Supplement/): seven and twelve numbered PDF/600-dpi PNG pairs. S02 is already integrated into S01.
- [What changed and what remains unresolved](FIGURE_SUITE_UPDATE_SUMMARY_20261012.md).
- [Captions](MANUSCRIPT_FACING_CAPTIONS.md), [manifest](FIGURE_MANIFEST.csv), [palette authority](CURRENT_CLUSTER_PALETTE.json), and [native page previews](Page_Previews/).
- [Main packet](ALL_MAIN_FIGURES.pdf) and [Supplement packet](ALL_SUPPLEMENT_FIGURES.pdf).

The final approved four-panel S05 now occupies the official numbered targets. It displays twenty pure-random searches and validation of the frozen legacy sequence using the archived separate 2,000-case cohort. It does not add GA curves to the existing six-policy main/resource figures or replace protected formal strategies. Figure7/S9 retain the formal five clusters, with synchronized C4 color; no experimental four-cluster typology is substituted. S11 now displays 2pc50 only, while the complete historical cross-scenario evidence remains archived. S12 and S13 remain separate. All mirrors under results/figures are byte-identical, not alternative versions.

No manuscript or scientific stage is changed. S14/S15 remain internal evidence and S16 remains a review aid; none is added to the numbered set.
'''
    u.write(r/'README.md',readme)
    p=r/'Additional_Evidence/README.md'
    text=p.read_text(encoding='utf-8')
    text=text.replace('The numbered S11 displays all four scenarios for the six selected manuscript policies; the larger experimental record remains available here.',
        'The numbered S11 now displays the six selected fixed policies under 2pc50 only; the complete historical four-scenario experimental record remains available here.')
    text+='\nThe approved final S05 is integrated in Supplement/FigS05 on the current figure-update branch. Its exact producing/review commits and numerical source-manifest copy are recorded in docs/reproducibility/official_figure_suite_review_20261012; older GA optimization figures here remain historical evidence.\n'
    u.write(p,text)
    u.write(ROOT/'results/figures/README.md','# Synchronized current figure artwork\n\nThe single review entry is [results/figure_review](../figure_review/README.md), with the [complete packet](../figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf) and [scoped update summary](../figure_review/FIGURE_SUITE_UPDATE_SUMMARY_20261012.md). These nineteen PDF/PNG pairs are exact mirrors. The final approved S05 is integrated; no formal strategy, manuscript or scientific output is replaced.\n')
