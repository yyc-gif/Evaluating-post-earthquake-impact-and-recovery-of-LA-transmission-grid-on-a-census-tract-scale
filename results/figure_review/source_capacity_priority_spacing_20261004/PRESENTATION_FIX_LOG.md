# Author-requested source, capacity, priority and spacing fixes

Scientific calculations and numerical outputs changed: **NO**. No simulation, scheduling, GA, clustering, bootstrap or capacity calculation was run. These are author-review updates; `results/figures/` has not been promoted or changed.

## Changes

- S07: retain all eight scheduled policies; strengthen Impact/Hospital/Degree/Vulnerability curves and fade secondary curves. Curve legends now contain matching line swatches, with no unplotted squares or triangles. Separate the legend from C/D; restore visible 318-edge connections, darker blue/orange station colors, and small distinguishable Core triangles.
- S08: separate B from A tick labels. B explicitly shows the extra modeled population-weighted service loss caused by the OLINDA planning bound, relative to the same model without this bound. OLINDA is the only bound-supported station with limit/demand below one; the existing four increments remain 0.120–0.126 h. This is a limited planning-data sensitivity, not earthquake-time load flow.
- S10: retain the full-size Hospital-first map and add Vulnerability-first and Impact-first construction maps from the already saved fixed station sequences. Name the first five stations using leaders. Impact-first uses the accepted population-impact scoring; it is not relabeled as a simple mapped-population sort.
- S12/S13: replace vague separation wording with absolute Q4–Q1 service-loss gap. This is abs(Q4 group loss − Q1 group loss) within each realization, then averaged; it indicates the magnitude of the group difference, not its direction, and is not Gini. Preserve all points and 5th–95th realization ranges.
- Fig04/Fig07/S03/S04: remove only verified empty horizontal strips; retain native plot/map/text sizes and contents.

## All-set native PDF visual review and measured internal spacing

All 20 current PDFs were opened as native-resolution renders. Each of the nine corrected PDFs was also opened after export; Arial embeddings and on-page text were checked. Preview-only viewing is not author acceptance.

Measurements below are the largest internal horizontal blank band at 144 dpi, excluding outer margins. Bands within a framework or natural-aspect map do not alone imply a defective layout. Only empty full-width strips were removed; plotted coordinates, maps and font sizes were not scaled.

| Figure | Before blank band (mm) | After (mm) | Action |
|---|---:|---:|---|
| Fig01 | 8.47 | 8.47 | Visually inspected; no artwork change |
| Fig02 | 5.12 | 5.12 | Visually inspected; no artwork change |
| Fig03 | 5.82 | 5.82 | Visually inspected; no artwork change |
| Fig04 | 14.29 | 7.76 | Corrected and visually inspected |
| Fig05 | 8.64 | 8.64 | Visually inspected; no artwork change |
| Fig06 | 10.23 | 10.23 | Visually inspected; no artwork change |
| Fig07 | 13.58 | 8.64 | Corrected and visually inspected |
| FigS01 | 0.00 | 0.00 | Visually inspected; no artwork change |
| FigS02 | 0.00 | 0.00 | Visually inspected; no artwork change |
| FigS03 | 10.58 | 7.58 | Corrected and visually inspected |
| FigS04 | 14.82 | 8.82 | Corrected and visually inspected |
| FigS05 | 6.00 | 6.00 | Visually inspected; no artwork change |
| FigS06 | 9.00 | 9.00 | Visually inspected; no artwork change |
| FigS07 | 10.05 | 8.47 | Corrected and visually inspected |
| FigS08 | 5.64 | 9.17 | Corrected and visually inspected |
| FigS09 | 7.94 | 7.94 | Visually inspected; no artwork change |
| FigS10 | 10.76 | 13.41 | Corrected and visually inspected |
| FigS11 | 8.11 | 8.11 | Visually inspected; no artwork change |
| FigS12 | 14.99 | 6.00 | Corrected and visually inspected |
| FigS13 | 14.99 | 6.00 | Corrected and visually inspected |

S12/S13 row separation is now 6.00 mm, versus 14.99 mm. S07 has clear separation between the shared policy keys and map titles. S10 preserves the original large hospital map; its remaining natural map-to-row space separates two different priority constructions and contains no overlapping labels.

## Verification

- 31 scientific-source hashes and 33 existing publication-file hashes unchanged.
- Every one of the 40 bundled artwork files matches its registered source hash.
- Nine corrected PDFs: native width 185 mm; minimum text 7.0 pt (S08) / 7.5 pt (other corrected files); Arial fonts embedded; no off-page text.
- `python -m pytest -q`: 49 passed.
- `git diff --check`: passed.
- The pre-existing 881 staged changes are preserved and excluded from these commits.
- Canonical resume is not claimed as passing: the previously existing Stage 10 S03 publication/source identity mismatch remains outside this author-review edit. No scientific stage was executed to resolve it.
- Protected July ref remains `182686868cffe962739804f6bc0ccecaed73d601`.
