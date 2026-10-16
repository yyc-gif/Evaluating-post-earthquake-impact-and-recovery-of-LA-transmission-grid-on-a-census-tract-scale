# Figure 7D: continuous bivariate review

**Recommendation for author approval: blue-amber continuous-continuous D for
full-color publication, accompanied by the aligned separate maps when independent
or grayscale reading is important. Do not promote it automatically.**

The current approved design remains intact. This review does not change K3,
the manuscript, the publication packet or the ongoing 1021 exploration.

## What improves, and what does not

The continuous design represents the actual SOVI score rather than four hue
classes. Nearby scores no longer acquire a large artificial color jump merely
because they straddle a quartile boundary. Darkness remains a common recovery-
burden coordinate. The new key is genuinely two-dimensional: moving horizontally
changes deficit hours; moving vertically changes continuous SOVI. It is not a
new composite score or an overlay of opaque maps.

In normal color the blue-amber version is quieter and makes broad low-/high-SOVI
geography easier to follow than the four-family original. It shows that greater
vulnerability and greater modeled recovery burden need not occupy the same
places. This is a qualitative visual-reading judgment, not a controlled observer
study or a new scientific result. Exact values still require the supplied table.

There are real trade-offs. The original makes the four quartile categories
immediately visible; the continuous version deliberately does not. Small score
differences within high-SOVI areas produce subtle, appropriately small color
differences. Tiny tracts cannot reliably support precise simultaneous reading
of both variables at this regional scale. The 94 inherited screening outlines
remain useful landmarks, but do not validate a hotspot or repair priority.

## Bounded palette comparison

Only two purposeful designs were tested:

- **Blue-amber:** a continuous blue-to-neutral-to-amber direction for increasing
  SOVI, with decreasing lightness for increasing recovery burden. This retained
  clearer SOVI differences in the red-green simulations than teal-wine and the
  original's four families, some of which merge under those simulations.
- **Teal-wine:** an alternative continuous chromatic direction. Its normal-color
  map is viable, but vulnerability differences weaken substantially in the
  protanopia/deuteranopia stress tests. It is retained in the comparison, not
  recommended as the primary alternative.

Both use CIELAB with a D65 reference white. The burden coordinate is normalized
linearly over the unchanged 23.688337196157214-53.63739206750921 h cohort range.
SOVI uses its original 0-100 scale, not a regional percentile stretch. At any
common burden, L*=91-49u is identical for every SOVI value. The numerical gamut
procedure reduces chroma, not lightness or scientific values. No tract color
uses RGB clipping and no new variable classes are introduced.

The gamut factor is common across the entire SOVI axis at a given burden and
interpolated continuously between 257 numerical knots. The PDF key is native
function-based continuous shading with 16-bit interpolated RGB samples, not a
3x3/4x4 classified color grid and not a raster image of geography.

## Accessibility and native size

Actual PDFs were inspected at the full figure's 7.2 x 9.0-inch publication size,
where D occupies the original footprint. The standalone D page is enlarged
twofold for detailed review; it is not the basis for the minimum-font claim.
All new text in native D is at least 7.5 pt. The separate-map reference keeps
each map at the same native size, extent, projection and boundary widths.

Normal, grayscale, protanopia, deuteranopia and tritanopia proofs are supplied.
The CVD previews use the published Machado severity 100 matrix implementation
on linear sRGB; clipping occurs only in the simulated display transformation.
They are stress tests, not clinical accessibility certification. CMYK press
proofing and a reader study have not been performed.

**Grayscale cannot retain both independent coordinates in these common-lightness
maps.** The original four-family version also loses quartile hue information
in grayscale. The continuous version is not a cure for that existing limitation.
If the final publication must communicate both values in grayscale, prefer the
two separate aligned maps rather than either combined encoding. Those maps
also make the opposing or overlapping spatial patterns easiest to read
independently, at the cost of additional page space.

At the unchanged map footprint, 2,017 eligible tracts occupy less than 1 mm2
and 700 less than 0.25 mm2; 93 of the 94 outlined tracts occupy less than 1 mm2.
These are polygon areas, not minimum-width guarantees. Fine boundaries and
screening outlines remain vector sharp, but individual dual-value reading is
limited by physical print size. The enlarged D proof must not be mistaken for
the native map size. The analytical color field is continuous; the PDF key's
interpolation differs by at most 0.12145 DeltaE76 in the registered 5,000-point
numerical check, which is not a human discriminability experiment.

## Scientific and approval boundary

Use the exact title "Recovery burden and social vulnerability" for D and
"Community recovery types and social vulnerability" for Figure 7. D uses direct
tract-level values, not K3 averages. The high-high rule remains original Q4 AND
burden >= 38.38135467381475 h: 94 tracts and 350,799 residents, with the exact same
GEOIDs and source outlines. It is not equivalent to SOVI_SCORE>=75.

A-C were imported from the approved PDF, not regenerated. Their rendered pixels
are unchanged at 150, 300 and 600 dpi. The source geography is replayed directly as
vectors, including white N/A fills and the existing outline widths. Any later
production substitution, caption update or packet regeneration requires a
separate author instruction. No current artifact has been replaced.

Independent output inspection verifies all 2,413 source polygon/boundary
paths with zero vertex-coordinate differences. MuPDF reports one tiny filled
quadrilateral as separate adjacent fill and stroke records; the verifier
reunites those actual records before comparison. This is parser normalization,
not a missing tract. The original PDF already has a 0.09021-pt bounding-envelope
difference between one screening outline (06037701801) and its raw GPKG polygon.
The archived outline is retained exactly rather than silently repaired.

## Method references

- [sRGB interpretation and conversion, W3C/ICC](https://www.w3.org/Graphics/Color/srgb).
- [Color conversion definitions and sample code, W3C](https://www.w3.org/TR/css-color-4/).
- [Machado, Oliveira and Fernandes 2009](https://doi.org/10.1109/TVCG.2009.113).
- [Severity-matrix implementation](https://raw.githubusercontent.com/njsmith/colorspacious/master/colorspacious/cvd.py).

Sources consulted on 2026-10-15. CIELAB here is explicitly referenced to D65;
it is not an unannounced use of the D50 CSS lab() default. Quantitative color
checks are recorded separately from visual judgments and do not establish
clinical discriminability or a new scientific interpretation.
