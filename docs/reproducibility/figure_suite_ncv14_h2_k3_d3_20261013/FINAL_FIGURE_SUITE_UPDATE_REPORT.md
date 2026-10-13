# Official figure suite updated — NCV14/H2/K3, Figure 7D D3

## Authority and scope

Implementation branch: `review/official-figure-suite-ncv14-h2-k3-d3-20261013`.

Actual approved starting figure branch: `review/official-figure-suite-final-s05-20261012`, local and remote HEAD `59d9001edadef57c5ff1dc6af6ca8d7817fb4f94`. The source branch remains clean. This is a separate worktree; no reset, merge or force-push is used.

Scientific review `49cc153c3f4d7a8c29cf94baf090dbfc0be4d068`, frozen eight-variable/K3 authority `0c5365cc39e2717e0fab4aa3b5d05b445d427eb6`, and D3 authority `05a78645b17bf8de04326e54181f9db432d7186c` are pinned. `SOURCE_AUTHORITY_AND_HASHES.json` records actual source bytes, SHA256, Git blobs and LFS OIDs. Source files are not modified.

## Implemented figures

- Fig01: replaces only Hotspot score with Spatial service-deficit patterns. All pixels outside that label region match the approved baseline.
- Fig07 A: C1 has 1,242 tracts / 5,101,704 residents; C2, 475 / 1,897,838; C3, 582 / 2,066,980. Total 2,299 / 9,066,522. Tract and resident representation are distinct.
- Fig07 B: original-unit means for the exact eight NCV14/H2 coordinates. Population is displayed as persons and fitted as log1p. The NCV14 label identifies a researcher-derived fourteen-hazard frequency-area screening index with FEMA v1.19 inputs and California scaling, not official FEMA risk or electric failure probability.
- Fig07 C: exact saved K3 labels and palette C1 `#147f98`, C2 `#d07734`, C3 `#7a5899`. Only 16 zero-population tracts are N/A; eight positive-population zero-housing tracts remain classified.
- Fig07 D: continuous saved five-policy mean total deficit = B_Unconstrained + MeanDelta_5. The finite, equally weighted policies are Impact/Hospital/Degree/Betweenness/Vulnerability-first. Random is excluded. Frozen SOVI Q4 geography is outlined, not reranked. Hours are equivalent full-service-deficit hours over 0-480 h, not a simulated average schedule, spatial hotspot inference or intervention priority.
- FigS09: neutral authentic K1-8 weighted-space inertia and K2-8 full-cohort silhouette; K3 initialization, geography and policy-set stability; K3 per-class silhouettes. K3 is not the silhouette maximum, which is disclosed. No K4 classification/profile/map, PCA or 2,291-residential denominator is published. The saved K3 Init ablation ARI and RQ1 weight redistribution are described accurately.

Exactly three numbered figures change. Fourteen numbered figure pairs, including approved S05, fixed-color Fig05 and merged eight-panel S11, remain byte-identical to the starting suite. `FIGURE_CHANGE_MANIFEST.csv` records all 34 artifact comparisons.

## Complete production synchronization

Current palette, captions, manifest, index, gallery, READMEs, update log, page previews, artwork mirrors and all three packets are synchronized. The misleading Hotspots mirror basename is replaced by `Fig07_Community_Typology_and_Service_Deficit`; exact old bytes remain pinned in Git/LFS history. The dated October 12 update summary is explicitly marked historical, not a competing current specification.

The suite contains 7 Main + 10 Supplement = 17 numbered PDF/PNG pairs. S02 is integrated into S01; S12/S13 are not restored. Packets contain 7 Main pages, 10 Supplement pages and 38 complete pages (17 actual figure/caption pairs + 4 unchanged evidence pages). Optional D2 evidence and the exact 94 saved GEOIDs are unnumbered and excluded from these packets.

Canonical command: `python src/la_grid/plotting/build_current_suite_k3.py`. Rerunning it was verified as byte-identical reuse. The four dated presentation entrypoints default to this current builder; `--historical` preserves explicit historical reproduction. Clean-clone replay uses `--portable`, disclosing that an absent unrelated original worktree cannot be checked locally. Narrow Git LFS fetch commands and figure dependencies are documented in `REPRODUCTION_COMMANDS.md`.

## Verification and boundaries

- All 18 figure-suite tests pass, including existing scientific display checks rather than removed/bypassed assertions.
- Independent script verifies exact raw coordinates, saved K3 labels, original population/quartile identities, D2 GEOIDs, native page bounds and the test report.
- Current Fig07 and S09 are vector PDFs with zero raster image objects and native 185-mm widths; PNGs are 600 dpi. Actual native pages and assembled caption pages were visually inspected.
- All 17 packet figure pages match actual authoritative figure renders. All mirrored PDF/PNG bytes match their authoritative files. Four complementary-evidence pages match the baseline.
- The 950 protected scientific files, original HEAD/status, all 862 staged names and the binary Git index are identical before/after. No manuscript, archived formal Stage 7, physical sample, restoration trajectory, strategy/GA result or vulnerability quartile is modified.
- The protection authority is the original revision worktree. Twenty-one explicitly authorized current presentation paths share logical names with its older protection register, but their original bytes remain intact. `AUTHORIZED_PRESENTATION_PATH_OVERLAP_QA.json` documents these exceptions and proves zero protected nonpresentation scientific-path changes. Scoped LF rules keep figure registries and the current generator's byte checks stable across clones.
- No K-means fit, Monte Carlo, scheduling, source propagation or full pipeline is run. This is adoption of a frozen figure authority, not formal scientific Stage 7 pipeline migration.

Remote delivery is recorded separately after push in `REMOTE_DELIVERY_VERIFICATION.json`, with actual isolated-cache downloads and payload SHA256s rather than pointer-only checks. No final commit SHA is embedded self-referentially here; the publication commit and verification commit are identified by Git history and the delivery record.
