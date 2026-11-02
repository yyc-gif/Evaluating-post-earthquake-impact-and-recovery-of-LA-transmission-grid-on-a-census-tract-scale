# Final delivery report

## Scope completed

- Publication-facing `centrality-first` is displayed as **Spectral-connectivity-first** through one authoritative mapping. The internal ID, registered sequence digest, sorting procedure and tie-breakers remain unchanged.
- Active Supplementary Figure S3 now contains only the two time-dependent functional-network recovery panels. The retained plots use preserved vector regions from the pinned source artwork; no recovery values were recalculated. Historical static-percolation code and outputs were left intact.
- The canonical figure builder, current caption, manifest/index, gallery, previews, mirrors and packet outputs were synchronized. The active suite remains seven main and nine supplementary figures; the combined packet remains 20 pages.
- A July-manuscript Methods reference documents priority metrics and the event-based station-recovery state transition.

## Verification

- Starting branch and commit: `refs/heads/1021`, `382f50c385069c54d8970c443c50ee108ead13ab`.
- Canonical build: `python src/la_grid/plotting/build_current_figures.py --portable`; two runs were deterministic.
- Integration tests: 61 passed, 0 failed.
- Only Supplementary Figure S3 artwork changed. The other 15 numbered artwork pairs are hash-identical to the starting commit; Figure 7 is byte-identical. The 103-entry preservation check reports all registered scientific sources unchanged, all unrelated numbered artwork unchanged, and Figure 7 unchanged.
- The new S3 PDF is a 185 × 152.4 mm vector page, with embedded TrueType fonts and no raster images. The full combined packet has 20 pages.
- No manuscript, formal Stage 7 products, simulations, schedules, GA output, clustering results, or source data were changed.

## Source limitation

The raw archived sequence JSON is not available in this worktree. The frozen strategy ID and registered sequence digest are preserved and documented, but the full permutation was not independently replayed. The registered digest is evidence of continuity, not a substitute for raw-payload replay.

## Delivery state

The scoped implementation is committed locally on `refs/heads/1021`, without merging to another branch. Push was attempted, but GitHub rejected the LFS upload because the repository exceeded its LFS budget. The remote branch still points to the starting commit, so this local commit is not yet delivered. `REMOTE_DELIVERY_STATUS.json` records the attempted push, remote HEAD, and the ten pending LFS payloads. No LFS bypass was used.
