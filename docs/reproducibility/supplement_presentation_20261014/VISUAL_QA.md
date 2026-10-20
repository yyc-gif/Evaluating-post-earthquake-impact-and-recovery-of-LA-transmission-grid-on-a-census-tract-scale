# Native-size visual review

Changed artwork was rendered from the actual vector PDFs at 110-150 dpi for native-width inspection; production PNGs are 600 dpi. Main figures 2, 3 and 7 and supplementary figures 1-8 were inspected, with enlarged S03/S04/S05 and priority-map reviews. The actual combined-packet pages were also inspected, not just standalone PNGs.

- Headings use Arial Bold, centered on their own panels. A single point size is used within each figure; existing dense eight-panel resource figures retain their approved smaller heading size.
- S02: the travel title is clear and contains no Directed qualifier. Insets, axes, hours and legends remain legible.
- S03: static removal and time-dependent recovery are clearly distinguished. B/C have matching column headers and matched title-to-axis offsets. Gaps above the next row title are controlled separately. No duplicated or displaced legend fragments remain.
- S04: the paired endpoints are unambiguously initial and final best orders **per run**, not 100 orders versus 20 runs as two comparable samples. All original curves and validation/component values remain.
- S05: three panel headings have identical 9.5-pt type. Two threshold comparisons share one axis and legend, separated from the source-connectivity control. No bottom explanation, superposed historical title or overlapping legend remains. Canvas is 185 x 210 mm; blank bottom space is trimmed without scaling any data axis.
- New S08 (previous S09): all three titles identify substation repair priorities. The population map and its log-scale colorbar use consistent ordered grays. The other map fills, station symbols, ranks and geometry are preserved.
- Figure 7: the six distributions, seven-coordinate profile, class geography and burden/vulnerability map remain unchanged apart from centered headings. No process-only title or review banner is present.
- Figure 3's long rotated damage-state label is protected with rectangle-specific heading clipping. An independent 144-dpi crop comparison requires zero changed pixels in that label; full-width heading strips are not used there.

All new heading faces and even unused legacy Base-14 resources carried by the clipped S05 source are explicitly embedded. PDF text extraction and centering are regression-tested in addition to visual inspection. Font checks caught and resolved an intermediate CID/subset problem before delivery.

The current packet has 16 numbered figure/short-caption pages and the same four complementary-evidence pages. The retired clustering artwork is absent, rather than hidden under a different supplementary number. Numerical tests, source preservation and repeat-build hashes are recorded in the adjacent QA files.
