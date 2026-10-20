# Figure 7 map-readability comparison

## Decision

Layout B is used for the current `1021` suite: 7.2 × 10.0 in, with C/D map paths enlarged 1.25× and centered in their original geographic extents. The continuous blue–amber D design is retained. An unnumbered two-page map enlargement and aligned single-variable maps are included as reading aids; they do not replace the numbered figure.

## Comparison

`FIG07_BOUNDARY_AND_LAYOUT_COMPARISON.pdf` compares the starting artwork, borderless Layout A, and enlarged Layout B at the same 7.2-in width. Layout A keeps the 7.2 × 9.0-in page and original map footprint. Layout B adds 25% to each linear map dimension, reducing the burden of reading small tract patterns without changing map centers, extent, coordinates, or numerical values. The page becomes 1 in taller; figure text was not reduced.

The source PDF diagnosis found explicit white 0.10-pt strokes on 2,303 positive-population tract path parts in both maps. These produced the regular light seams. The replacement uses vector fills and a 0.12-pt edge overprint in each polygon's own fill color. That suppresses antialias hairlines without adding a contrasting internal boundary. Source path coordinates and tract geometries are unchanged. White N/A polygons retain a separate 0.45-pt charcoal outline.

The Q4/high-burden screen is drawn separately at 0.25 pt. The 0.25/0.35/0.40-pt comparison shows that 0.25 pt keeps the selected polygons legible while reducing the dense black patches that obscure small tracts at 0.35 and 0.40 pt. The 94 selected GEOIDs and 350,799 residents are unchanged.

## Visual assessment

Layout B is clearer than the original and Layout A for tract-scale geography. N/A remains distinguishable from white exterior space because its boundary is charcoal. The 2D legend retains burden in equivalent hours and SOVI on its original 0–100 scale. At high burden, darkening reduces the apparent blue-versus-amber contrast; the aligned SOVI-only and burden-only maps provide a direct secondary reading. In grayscale the bivariate map cannot independently encode SOVI hue. This is an inherent limitation of the combined color mapping, not a numerical or source-data change.

The full map at native size supports regional pattern reading, but not confident identification of every tiny polygon. The unnumbered enlargement is supplied for that purpose. The gradient is descriptive; it does not imply observed outages, compound hazard simulation, or a statistically significant hotspot result.

## Source and preservation

Figure 7C retains the P2/K3 membership and class palette; Figure 7D retains the exact continuous SOVI and five-policy mean deficit values from the pinned experiment source. The eligibility rule, 2,299 GEOIDs, 16 N/A tracts, eight positive-population zero-housing tracts, frozen quartiles, and 94-tract outline set are checked by `verify_figure7_map_suite.py` and the figure-suite tests. No K-means or physical simulation was run.

Only `Main/Fig07.pdf` and `.png` differ among the 16 numbered artwork pairs. The other 15 pairs are byte-identical to starting HEAD `0f67aa1f2758fcf1d35c112c36eb04e6d8a5dd68`. The current suite remains 7 main and 9 supplementary figures; the combined packet remains 20 pages.
