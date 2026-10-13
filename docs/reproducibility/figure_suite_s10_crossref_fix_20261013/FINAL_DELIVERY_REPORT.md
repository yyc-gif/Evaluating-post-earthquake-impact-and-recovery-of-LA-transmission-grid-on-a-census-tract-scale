# S10 cross-reference correction

Starting authority: `review/official-figure-suite-ncv14-h2-k3-d3-20261013`, actual remote HEAD `8f2dcb3b9762137b9f2686609c34480334f5d44e`. Implemented separately on `review/figure-suite-s10-crossreference-fix-20261013`; no merge, reset of the source branch or history rewrite.

Exact corrected phrase: **Outcome comparisons appear in Figures 4–6 and Supplementary Figure S11**.

Only S10's cross-reference changed. Other 16 captions are text-identical. No other stale active citation was found; historical consolidation/source references are retained. The canonical builder now replays accepted artwork and applies the narrow correction to the pinned caption source, including a validated rule in the preserved original NCV14 generation layer. It never redraws accepted figures for this correction.

## Verification

- All 17 numbered artwork PDF/PNG pairs and mirrors are byte-identical to the starting authority. This includes Figure 1, NCV14/H2/K3 Figure 7 with D3, K3 Figure S09, approved S05 and merged S11.
- Seven-page main and ten-page supplementary figure-only packets, figure index, gallery, palette and all numbered previews retain their bytes. No new numbering or class result was introduced.
- The complete packet remains 38 pages: 17 immediately adjacent figure/caption pairs plus four retained evidence pages. Only caption page 32 changed. Every other page has identical text, dimensions and 100 dpi rendered pixels.
- Full-packet SHA256 before: `527a74223e5a2b24c65cd2148dbb1dc9038582ce5a48ee9fef269bf9dd0a612e`.
- Full-packet SHA256 after: `384c78d7437adc5d639bdd2d9bfa7f5de55673ba5daa84d39de5d5452a7371e9`.
- All 22 integration tests passed, including the original 19 unchanged test functions and three new regression tests. Compile checks passed.
- Two ordinary canonical replays and one forced caption rebuild preserve all production bytes, including the checkpoint. See `BUILD_IDEMPOTENCE_RESULTS.json`.
- The S10 caption page was visually inspected at native A4 size; body 10 pt, heading 11 pt, all bounds inside the page, no clipping or missing glyphs.
- All 950 original protected-file hashes, original author-worktree HEAD/status/index/staged-file state, and the clean approved figure source worktree are preserved. No manuscript, formal Stage 7 product or scientific input changed; no fit, simulation, scheduling, GA or scientific postprocessing was run.

The manifest's six canonical generator hashes and active build checkpoint were refreshed to match the changed code. Artwork provenance/hashes and prior artwork-change classifications remain intact; this follow-up's zero artwork changes are recorded in `UNCHANGED_ARTWORK_HASH_TABLE.csv`.

The source caption registry, complete packet and update log are synchronized. The remote delivery receipt records the publication commit, actual remote HEAD and fresh-cache downloads of every changed LFS payload; a subsequent receipt-only commit preserves those payload identities. The final HEAD is reported in the task closeout because a commit cannot contain its own SHA.

See `REPRODUCTION_COMMANDS.md`, `TEST_RESULTS.json`, `PACKET_AND_PRESERVATION_QA.json` and `REMOTE_DELIVERY_VERIFICATION.json` for machine-readable evidence and reproducibility boundaries.
