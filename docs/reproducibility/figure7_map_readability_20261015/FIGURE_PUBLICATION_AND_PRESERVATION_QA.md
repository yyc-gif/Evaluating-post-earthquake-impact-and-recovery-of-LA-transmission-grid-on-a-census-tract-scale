# Figure 7 Map Readability and Preservation QA

## Publication-size review

Figure 7 was rendered and inspected at 7.2-inch width. Layout A retains the 7.2 × 9.0-inch page and prior map footprint. Layout B is 7.2 × 10.0 inches; it enlarges each C/D map 1.25× linearly without changing tract coordinates, map extent, or center. The taller page recovers map area instead of shrinking text. The comparison PDF shows the starting artwork, borderless original-size layout, and enlarged layout. A two-page detail PDF provides larger C and D views.

The starting PDF contains explicit white 0.10-pt strokes across 2,303 positive-population path parts; these produced the light seams. The replacement uses vector fills with same-fill 0.12-pt edge overprint to suppress rasterizer hairlines without adding contrasting regular tract boundaries. N/A tracts use a separate white-fill, charcoal-outline layer (0.45 pt). The 94 Q4/P75 screening polygons use a separate 0.25-pt outline. The 0.25/0.35/0.40-pt comparison supports 0.25 pt as the least occlusive option that remains visible at native size.

The continuous blue-to-amber SOVI hue and burden-to-lightness mapping retains the pinned two-dimensional legend. In the darkest high-burden regions the SOVI hue distinction is muted; grayscale also cannot preserve SOVI as an independent channel. Aligned SOVI-only and burden-only maps are retained as an accessibility/reference view. The joint map supports regional pattern reading, while the separate maps are clearer for reading either variable independently and in grayscale.

## Scientific and file preservation

- The map contains 2,299 eligible tracts; 16 zero-population tracts remain N/A; eight positive-population zero-housing tracts remain classified.
- P2/K3 class counts are 1,235 / 428 / 636 in this `1021` authority.
- The high-high screen remains the exact frozen Q4 and burden ≥ 38.38135467381475 h rule: 94 tracts and 350,799 residents.
- Figure 7 PDF map content is vector-only. Its PNG is 4,320 × 6,000 px (600 dpi at 7.2 × 10 in).
- Fifteen of 16 numbered PDF/PNG pairs are byte-identical to the starting suite. Only Main/Fig07 PDF and PNG change; mirrors match exactly.
- Main, supplement, and combined packets contain 7, 9, and 20 pages. The combined packet is rebuilt from the current numbered art and captions.
- The changed-path allowlist contains Figure 7 presentation, directly dependent suite registries/packets, builder/test code, and this review package. No formal Stage 7 data, simulation, scheduling, or manuscript path is changed.
- The pre-existing 195 diagnostic blob identities and 17 Stage 7 authority blob identities still resolve to the original `1021` base. A prior repository inventory records 950 protected paths; it predates the current branch snapshot and includes files absent from this checkout, so this round verifies the current-base changed-path allowlist rather than comparing those stale per-file hashes to unavailable files.

See `COMPLETE_SUITE_QA.json`, `ARTWORK_HASH_COMPARISON.csv`, `PRESERVATION_AFTER.json`, and `TEST_RESULTS.json` for machine-readable checks.
