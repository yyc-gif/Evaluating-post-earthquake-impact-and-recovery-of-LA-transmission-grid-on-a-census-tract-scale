# Actual-output review, 2026-10-02

Baseline: local HEAD and `git ls-remote` both identified
`734e830185b0ebf29a4f2ed91eb1f5bc51f48a29`. Actual PDFs were loaded, measured,
and rendered; all 27 inspected PDF files match their pushed LFS content OIDs.
The current publication set and v2.1 layout set are **different collections**;
they must not be conflated. Measurements are in
`CURRENT_ACTUAL_PDF_MEASUREMENTS.csv`; individual rendered files are in
`actual_review/`. Every listed image was opened for review, not inferred from
its source code or an earlier PASS report.

## Fig01–Fig07

| Figure | Actual observation | This round's action / remaining qualification |
|---|---|---|
| Fig01, both sets | Exact July diagram remains visually detailed; some explanations are very small at native width. Minimum extracted text is 4.9 pt. | Preserve the author-requested exact July artwork. This remains an explicit readability exception, not submission approval. No unauthorized replacement diagram. |
| Fig02 publication | 293-mm vertical stack; three maps dominate the page; “Revised” and station-count display remain. | Do not promote automatically. The pushed v2.1 174-mm 2×2 already provides the direct utility-eligibility map and 337-tract public-site agreement; opened and rechecked. |
| Fig02 v2.1 | A/B geography intact; map sizes balanced; public-site values separate from markers; utility map key lies outside geography. All four panels are readable at 185-mm width. | No rerender needed this round. Public-site agreement remains support rather than feeder ground truth. |
| Fig03 publication | Compact T80 distribution/map lacks the complete baseline loss chain; map not mislabeled as a policy result. | Retain, do not silently promote another story. |
| Fig03 v2.1 | 216-mm four-part baseline chain is readable; Long Beach blue-solid and San Fernando purple-dashed are distinguishable; 2pc50 curve is separated from the frame. The T80 map has its own colorbar and adequate area. | No new rerender. Long labels and source-path percentages remain legible; 216-mm height is disclosed. |
| Fig04 publication | Nine-policy curves and three boxplots retain all results; the boxplot bands are visually dense and recovery display remains 120 h. | This is not declared accepted. The newer v2.1 comparison has uniform dot/range outcomes and a 100-h display. |
| Fig04 v2.1 | Four explanatory policies are visible; other fixed-rule marks/curves are too faint in the pushed draft. The outcome-column labels fit but are necessarily multiline. | Increase weaker-rule curve opacity from .40 to .68 and interval opacity from .50 to .75 in a separate review PDF. Retain all nine identities, axis units, means, percentiles and line styles. |
| Fig05 publication | Hospital-priority map/boxplot is readable; numbered circles are priority ranks of substations, not hospital IDs. This repeats one outcome from Fig04. | No promotion/deletion decision. Preserve policy-definition evidence and its source. |
| Fig05 v2.1 | Q1–Q4 whiskers overlap at identical category x positions; all-policy plane's secondary marks are pale; Gini change's reference is not explicit on its own axis. | Dodge category marks only, retaining all y values and endpoints; strengthen secondary plane marks; label Gini as Vulnerability-first minus reference. The map keeps its size and reference. C/D retain 5th–95th paired-realization ranges, not bootstrap CIs. |
| Fig06 publication | Old distributional composition has metric-specific effects without interpretable common tick axes. | Preserve as existing publication content but do not certify its scale design. The v2.1 Fig05 provides the real-hour and separate Gini axes; this round does not promote it. |
| Fig06 v2.1 | Two-level absolute resource comparison is visually readable but cannot isolate policy leverage and omits tested levels. | Retain exact comparison copy; replace only in the new review packet with the preferred six-panel resource-policy contrast. Full absolute companions retain all eight policies and levels. |
| Fig07 publication | Cluster colors differ from the newer common cluster-ID palette; top-10 boundaries are absent in this older copy. | Preserve publication files; the newer review composition already restores those boundaries and common colors. |
| Fig07 v2.1 | Six KDE panels, profile and maps are readable, but 268-mm page is too tall for a conventional native-width manuscript placement. | Review alternative is 229 mm high. Reflow existing vector plot boxes; every word/tick is preserved, and all text is restored at its original size. Map row remains native 185×75 mm. No KDE or cluster computation. |

## Major supplements

| Figure | Actual observation / action |
|---|---|
| Publication S01 damage | Readable box/jitter display; published hazard palette differs from the newer Fig03 palette. Retained without promotion or numerical alteration. A shared hazard-palette replacement would require author promotion of a consistent set, not an isolated silent overwrite. |
| Publication S02 initial service | Four full maps share a scale/extent; CDF legend inside the lower-right empty region does not cover data. The near-axis 2pc50 line and old hazard colors remain presentation consistency exceptions in this older set; newer Fig03 addresses its CDF. |
| Publication S03 input context | 229-mm input/map/heatmap composition is readable, but a “Retained station” label remains and title hierarchy is larger than other figures. New native-PDF label correction removes that word without regenerating inputs; large input-map typography remains visible in the review copy. |
| Publication S04 network | Curves and source-loss contrasts are readable, but the 244-mm stack is tall. Static percolation, dynamic topology, and source-loss contrast have distinct meanings. No acceptance or optimal-repair inference is implied. |
| v2.1 S05 GA | Search paths from five seeds are visible above the incumbent. Incumbent equality is shown separately; not merely five coincident flat lines. Source uses planning evidence; no optimization rerun. |
| Publication S06 mapping | 3% selected-cutoff annotation and 337-row agreement values are readable. “Revised minus July” in the mapping shift is a comparison identity, unlike treating public-site agreement as model accuracy. |
| Publication S07 source | Two dynamic panels and two maps are readable; exterior shared policy legend and Core-source marker key do not obscure paths. Very small static probabilities create intentionally pale maps; do not reinterpret them as delivered power. |
| Publication S08 capacity | Facility loading points and low-side marker key are readable; OLINDA 109.04% is separate from the planning-limit line. Remaining “retained”/“population burden” wording is replaced only in a separate review copy. Small 0.120–0.126-h effects retain a labeled expanded dot scale and values. |
| v2.1 S09 diagnostics | Numerical loading annotations solve the mid-color ambiguity; cluster points/key were too translucent. New review raises opacity without changing palette/PC coordinates or memberships. Category palette matches v2.1 Fig07. |
| v2.1 cross-hazard | Four heatmaps show every policy and named scenario; values distinguish small contextual cases from 2pc50. Their fragility parameterizations differ; not a pure intensity experiment. |
| v2.1 complete crew/duration | Four outcome panels retain all eight policies and all four levels. Intervals are dense at 86/114 crews because outcomes genuinely converge. No truncated bars, interpolation or invented Unconstrained sensitivity case. Exact copies supplied for this review. |

## Final inspection of new candidates

All new PDFs and native-width page previews were opened after rendering. The
preferred Fig06 has separated headers, reference key, zero lines, explicit ticks
and units; gray circles/orange squares remain distinct in grayscale. Whiskers
are narrow because the saved mean CIs are narrow; they are not enlarged or
substituted with realization variability. The sign of near-zero 86/114 effects
should be read with the source table/CI, not inferred from a large marker.

Fig05's dodged marks make individual intervals visible; map size is unchanged.
Fig07's shorter boxes preserve curves and geographic shapes; every extracted
word/tick matches the source after normalizing Arial's hyphen encoding. The
existing pale-blue cluster remains distinguishable by the explicit category
key and geographic boundaries, but no claim of perfect CVD separation is made.
The new S09 point/key opacity improves visibility without relabeling clusters.

Native-width exports embed Arial/Arial Bold, have no off-page text, and have
minimum text ≥7 pt (preferred Fig06 ≥7.5 pt). PNGs are rendered at 600 dpi.
The one-page side-by-side sheet is intentionally A3 landscape, with both
artworks at 185 mm. It is a review aid, not submission artwork.

**Author acceptance remains pending.** The unresolved July Fig01 small lettering
and the older publication-set inconsistencies are not converted into a PASS.
The checked and corrected review artifacts are not a promotion decision.


## Final Fig06 wording and native-size check

The title now reads “Resource dependence of restoration-policy contrasts under
2pc50.” Caption and rationale distinguish between-group separation/group
disparity from the separate overall Gini inequality measure. The stated finding
uses “generally diminished” and the tested-case scope, with crew and duration
identified as separate OFAT families, not one calibrated capacity variable.

The revised actual PDF and actual-size page were opened. At 185 x 166 mm,
minimum text is 7.5 pt with embedded Arial/Arial Bold; the longer title fits.
The main drawing paths, common axes, zero lines, markers and saved intervals
are exactly unchanged. Gray circles and orange squares still match Fig05.
C29 and the duration row retain readable relative magnitudes, but 86-/114-crew
separation signs sit against zero on the main scale. A separate review-only
local-detail PDF exposes those same four values and saved CIs without a broken
axis or changed main scale. Its actual PDF/preview was also opened; it shows
the Impact-first interval at 86 crews crossing zero. No universal monotonic
trend is inferred.

Fig04, Fig05, Fig07 and FigS09 actual PDFs were freshly rendered and opened.
No new obvious clipping, overlap or layout defect was found in these retained
versions. Their PDFs and all previews are byte-identical to the preceding
review. They are not declared author-approved or promoted.

The 31 guarded scientific files and 33 publication files remain byte-identical;
the saved effect rows, displayed-point source index and parity table also remain
byte-identical. No scientific stage or bootstrap interval was rerun.
