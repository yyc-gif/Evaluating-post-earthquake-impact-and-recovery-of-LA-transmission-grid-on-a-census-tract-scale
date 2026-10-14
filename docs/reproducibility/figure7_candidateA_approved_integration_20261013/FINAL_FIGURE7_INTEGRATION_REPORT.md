# Approved Figure 7 Candidate A integrated

## Authority and scope

Implementation branch: `review/official-figure7-candidateA-approved-20261013`.
Baseline: `review/official-figure-suite-ncv14-h2-k3-d3-20261013` at
`8f2dcb3b9762137b9f2686609c34480334f5d44e`, independently matched to the remote.
Approved Candidate A: `aa55131cc5455aca9e1a6dead98e8f0eb8944217`.
Frozen science and D3 are pinned to `0c5365c` and `05a7864`, respectively; full
commit identities and actual payload hashes are in the source authority record.

Only Figure 7 artwork and directly dependent production/presentation files were
updated. The separate approved S10-to-S11 caption fix at `7795638` was not in
the starting branch; it is explicitly carried forward here, not silently merged.
All other 15 captions retain their exact approved text. No numbered figures,
manuscript documents, Stage 7 scientific files or historical review packages
were repurposed or removed.

## Approved implementation

1. A: Grid_Impact, Redundancy_HHI, B_Unconstrained, MeanDelta, SOVI_SCORE and
   FEMA_NCV14_CA_v119 ECDFs. Eighteen class/feature curves preserve every frozen
   observation and repeated value; medians and the 50% guide are retained.
2. B: ordinary class-mean cohort z-scores for all eight fitted coordinates using
   the exact frozen cohort mean and population SD. Twenty-four cells are
   independently reconstructed. H2 fitting budgets and K3 labels are unchanged.
3. C/D: locked original vector maps translated down 8 mm with no scaling. Only
   N/A fill and stroke were changed: white, dark gray `#777777`, 0.45 pt, on the
   32 map polygons and two legend swatches. Geometry, Q4 outlines, class fills,
   numerical deficit values, colorbar and all other paint remain unchanged.
4. Final Figure 7 is 185 x 253 mm, vector PDF with 600-dpi PNG and native preview.

## Scientific invariants

The exact 2,299 positive-population tracts represent 9,066,522 residents. Counts
remain C1 1,242 (5,101,704 residents), C2 475 (1,897,838), C3 582 (2,066,980).
All eight positive-population zero-housing tracts remain classified; only the
16 zero-population tracts are N/A. Original frozen Q4 membership is unchanged.
Initial service has 1,533 exact zeros; the caption cautions that standardized
separation does not imply large absolute initial electricity service.

D3 remains `B_Unconstrained + MeanDelta_5`, matched to the existing five-policy
mean within floating-point tolerance. No trajectory, schedule, model fit, K4
classification, P75 selection or hotspot score was produced. The canonical
builder does not invoke `run_stage_7` or any scientific simulation.

## Suite synchronization

Seventeen numbered figures remain: Main Fig01-Fig07 and Supplement FigS01,
FigS03-FigS11. The other 16 PDF/PNG pairs retain exact baseline SHA256, including
Fig01, S05, S09 and merged S11. All authoritative/mirror bytes match. Figure 7
caption, palette, manifest, index, gallery, README and log are synchronized.
The Main packet has seven pages; the unchanged Supplement packet has ten.
The complete packet has 38 pages: 17 actual figure/caption pairs followed by
the four unchanged complementary-evidence pages.

The new canonical layer reproduces approved ECDF/profile artwork from frozen
data; it does not merely copy the review PDF. The old NCV14 presentation layer
remains explicitly historical. Default replay checks both code modules and all
canonical outputs. Two forced builds reproduce exact bytes.

## Verification and preservation

The 19 original suite tests retain their scientific invariance assertions; only
approved display routing changed. Three S10 regression checks are carried
forward and adapted to the newly authorized Figure 7 change. Four additional
tests check the 18 ECDFs, 24 cohort-z cells, N/A/vector layout and independent
preservation/packet QA. The complete current suite has 26 tests.

Independent QA checks source matrices, profile/median values, exact GEOIDs,
vector paths and paint, aligned pixels, actual packet pages and mirror hashes.
Before/after records retain all 950 protected scientific files, 862 staged files,
the original author Git index, and all three source worktree states unchanged.
The active build checkpoint is refreshed; old numerical source/QA files are
not overwritten. Git LFS delivery verification must use an empty independent
cache and actual downloaded payload bytes, not pointers or the shared cache.

See `TEST_RESULTS.json`, `BUILD_IDEMPOTENCE_QA.json`, `INDEPENDENT_QA.json`,
`CD_VECTOR_AND_ALIGNED_PIXEL_QA.json`, and the remote delivery record for the
actual execution results. No source or implementation branch is merged or
force-pushed.
