# Supplement feedback validation

The eight revised native PDFs and their native-width page previews were opened and inspected. Width is 185 mm; the minimum text sizes are 7.0–7.5 pt. Actual PDFs contain embedded Arial/Arial Bold, without DejaVu fallback. Labels remain within each artwork page. S06's duplicate title objects were removed; S08's low-side voltage key contains all three classes. Map color scales remain linear and their numeric limits are unchanged.

- S01: all 368 station means remain plotted. The 13 San Fernando default boxplot fliers were duplicate symbols over the station scatter layer, not extra observations; only that duplicate layer was disabled.
- S02: four exact map clips and shared colorbar retained; the ECDF already in Main Fig03 is removed. A–D identify the four hazards.
- S03: origin coordinates/utility assignments come from the unchanged allocation table. Smaller equal-size origin symbols and nearby legend replace the overlapping display. The travel panel is an exact vector clip with axis wording corrected.
- S04: all saved static and dynamic curve ordinates are retained. B/C use the main policy identity and a shared nearby legend; the fraction denominator is explained in the caption, not placed in the y-axis label. The source-loss panel is removed from this copy at the author's request; its earlier review source and numeric table are retained.
- S06: the former C is removed only from this review artwork. Remaining values, including the 337-tract comparison and 246 tracts with greater-than-1-hour mapping changes, are unchanged. Former D is now C and identifies the mapping comparison in its axis/caption.
- S07: the same station probabilities are displayed on more visible sequential palettes, with the same zero-to-maximum linear normalization and Core-source triangles. Dynamic curves read the existing summary; captions distinguish dynamic joint connection from static conditional reliability.
- S08: all 34 facility loadings and four closed capacity increments are taken directly from the existing tables. The low-side voltage statement is a legend definition, not a title. B explains the capacity-bound comparison and its expanded scale; this is not a load-flow result.
- S13: only four repeated “57 crews” axis qualifiers are replaced with “reference crews”. No other S13 element is revised.

All Main artwork and S05/S09/S10/S11/S12 remain byte-identical. All 40 manifest artwork rows have matching source/copy SHA-256. The caption packet contains 40 pages in the existing Main-then-Supplement order. The 31 scientific authority guards and all 33 existing publication collection files have zero hash changes.

`python -m pytest`: **49 passed**.

`run_all.py --resume`: **Stages 01–09 PASS_VALIDATE/PASS_REUSE; Stage 10 FAIL_FAST**. The failure is an existing mismatch between `results/figures/FigS03_Crew_Bases_and_Directed_Travel.pdf` and the old source recorded in its index, `provenance/artwork_drafts/figure_fix_20260930/FigS03_Crew_Bases_and_Directed_Travel.pdf`. Neither file is changed by this round, and no index fallback or publication promotion is performed. Current and HEAD identities are recorded in `CANONICAL_STAGE10_EXISTING_CONFLICT.json`. This failure is reported rather than relabeled as PASS.

`git diff --check`: **PASS**. The protected July ref remains `182686868cffe962739804f6bc0ccecaed73d601`. Pre-existing staged changes are excluded from the scoped commits.
