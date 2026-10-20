# Figure 7 Presentation Review — 2026-10-16

## Recommendation

Use **Layout C** (7.2 × 9.03 in; 182.88 × 229.31 mm) for the current 1021 figure suite. It shortens the page by 24.69 mm relative to Layout B while retaining the same map scale, geography, and panel-D color function. The A-panel ECDF axes and B-panel feature labels remain legible at 7.2-in width; the revised legend placement avoids overlap with the bivariate colorbar label. Layout B (7.2 × 10.0 in) remains in the review package as the larger-spacing reference.

## Palette

The selected palette is C1 `#3C9198` (muted lake teal), C2 `#52699E` (slate blue), and C3 `#C69EBA` (restrained mauve). It is applied consistently to the ECDF curves and medians, profile headers, map fills, and class legend. Panel B's independent zero-centered diverging scale is unchanged. Panel D retains its continuous blue–amber SOVI hue and service-deficit lightness function.

The tested darker C3 alternative, `#A87596`, is rejected: its grayscale C1–C3 CIE76 separation is approximately 0.23, so those classes nearly collapse to the same gray; the proposed mauve gives approximately 13.91. For the selected colors, C1–C2 grayscale separation is approximately 10.81. Pairwise distances and simulated swatches are in `PALETTE_PAIRWISE_DISTANCES.csv` and `PALETTE_COLOR_VISION_VALUES.csv`. Native, grayscale, protanopia, deuteranopia, and tritanopia previews are provided. Simulations are diagnostic approximations, not substitutes for user testing.

At full color the adjacent C1/C2 regions are distinguishable without internal boundary strokes, though their grayscale contrast is moderate. C3 is lighter than the other classes but remains distinct from N/A white; N/A tracts retain charcoal outlines. In grayscale, the Q4/P75 screen remains outlined but Panel D's two continuous dimensions cannot both be read: the hue dimension is necessarily lost. The aligned single-variable maps remain the accessibility alternative.

## Variable labels

The common display labels are:

| Fitted feature | Figure label |
|---|---|
| `Init_Supply` | Initial service availability |
| `Grid_Impact` | Spectral network impact |
| `Redundancy_HHI` | Dependency concentration (HHI) |
| `B_Unconstrained` | Unconstrained service deficit |
| `MeanDelta` | Mean additional service deficit (five policies) |
| `SOVI_SCORE` | Social vulnerability score |
| `log1p_Population` | Tract population |

Panel A intentionally shows six empirical distributions; Panel B shows standardized means for all seven fitted coordinates. Population is plotted in persons in A and enters the fit as `log1p(Population)` in B. The cohort-standardized profile values reproduce the saved class means with maximum absolute error below `1.2e-16`. No observations, class assignments, standardization values, or fitting weights changed.

## Layout and publisher sizing

Layout B is 7.2 × 10.0 in (182.88 × 254 mm). Layout C is 7.2 × 9.0278 in (182.88 × 229.31 mm). Both keep the map scale at 1.25; no proportional shrinking was used. Layout C moves the map region down to accommodate the three-row ECDF layout and repositions the two-dimensional legend and screening keys. The final PDF is vector-only (5,276 drawing objects; no page image objects) and embeds the used fonts. Figure text is at least 7.5 pt at native size, and all text spans are within the page bounds.

Elsevier's general artwork guidance recommends a finished printed size of 7 pt for normal lettering and lists 90 mm single-column, 140 mm 1.5-column, and 190 mm double-column target widths. It also directs authors to the selected journal's specific guide and does not state a universal maximum figure height. At 182.88 mm, the candidate is suitable only as a near-double-column/full-width figure. Resizing it to 140 mm would reduce 7.5-pt text to about 5.74 pt; at 90 mm it would be about 3.69 pt. Neither is suitable without a journal-specific alternative arrangement. The target journal is not confirmed, so journal compliance is not certified.

Official guidance checked 2026-10-16:

- https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing
- https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-formats-checklist

## Preservation and scope

The 2,299 eligible tracts, 1,235/428/636 K3 classes, 9,066,522 represented residents, 16 zero-population N/A tracts, 94 Q4/P75 screen tracts, and 350,799 residents in that screen were independently rechecked. The threshold is `38.38135467381475` equivalent service-deficit hours. Ordinary internal tract strokes remain absent; the same-fill vector overprint is 0.12 pt, N/A boundaries are 0.45 pt, and Q4/P75 outlines are 0.25 pt.

Only Figure 7 changes among the 16 numbered artwork pairs. Figures 1–6 and S01–S09 are byte-identical to the current 1021 baseline. Figure 7, the concise caption, current palette registry, manifest/index/gallery, page preview, and assembled figure packets are regenerated. No scientific tables, K3 memberships, recovery outputs, simulations, or manuscript files are changed.

The native-size review image is `LAYOUT_C_NATIVE_150DPI.png`; the B/C comparison is `FIG07_LAYOUT_COMPARISON.pdf`; enlarged maps are `FIG07_MAP_DETAILS_C_D.pdf`. High-resolution output and accessibility previews are in this directory.
