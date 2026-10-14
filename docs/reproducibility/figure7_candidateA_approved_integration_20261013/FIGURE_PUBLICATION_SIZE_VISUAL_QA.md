# Publication-size visual review

## Actual outputs inspected

The actual final PDF was rendered at 160 dpi at its native 185 x 253 mm size.
The final 600-dpi PNG is an export of that PDF, not a separately redrawn figure.
The actual complete-packet Figure 7 page and its caption were rendered and checked;
the carried-forward S10 caption page was also visually inspected.

- A: six empirical small multiples, with solid/dashed/dotted class lines, original
  units, a 50% guide, and colored median markers. No smoothing, clipping or
  population-weighted substitution. Tied observations remain visible as steps.
- B: all eight coordinates, 24 signed cells, one zero-centered diverging scale,
  colored C1/C2/C3 headers and RQ separators. The note explicitly identifies
  ordinary unweighted cohort-z means rather than fitted distance coordinates.
- C/D: original geographic sizing and extent retained. Titles, cluster legend,
  deficit-hour colorbar, Q4 boundary key and N/A keys are legible and unchanged
  except for the specifically approved white/dark N/A paint.
- All final figure text is at least 7.5 pt; caption body is 10 pt. No title, legend,
  colorbar or profile label is clipped. The approved tight A-note placement is
  retained; no extra layout or font redesign was applied.
- The A/B scientific story is directly visible: C1 greater SOVI and smaller
  constraint increment; C2 lower baseline deficit and greater increment; C3
  greater spectral impact and baseline deficit. These are descriptive contrasts.

## Exact visual preservation

At 254 dpi, A/B pixels match the approved Candidate A PDF outside the removed
review-warning band. C/D were compared at the same new-page origin without
resampling; this avoids float32 MediaBox raster rounding between differently
tall pages. Across 2,090,500 map-region pixels, changes are confined to the
authorized N/A path/stroke/antialias masks. Zero pixels outside those masks
changed. The independently extracted 5,035 map/legend vector objects preserve
all geometry and non-N/A paint. Original content-stream bytes are recovered
exactly after removing only the 34 local graphics-state overrides.

The copied vector Form retains clipped, nonrendered source A/B content as PDF
provenance. Generic text extraction may report it despite the visible C/D clip;
it is not displayed. Actual visible A/B pixels were therefore verified against
Candidate A rather than relying on clipping-unaware text extraction.

The native PDF has no raster image objects; ECDF paths, heatmap cells and maps
are vector content. Sixteen other numbered PDF/PNG pairs, all their previews,
the Supplement-only packet and four retained evidence pages are unchanged.
No visual claim of resilient electrical delivery, compound-hazard simulation,
statistical hotspot or intervention priority was introduced.
