# Native-size diagnostic figure review

All three vector PDFs were rendered with PyMuPDF at 150 dpi at their actual
7.2-inch page width and inspected, not merely checked for bounding boxes.
PDF_STRUCTURE_QA.json reports one page each, zero raster image objects,
minimum text size 7 pt, vector paths and all text contained inside each page.
The higher-resolution PNG previews are 300 dpi; PDF-derived previews are in
pdf_previews/. No existing publication figure or packet was opened for writing.

- 01: Gap reference colors/legend, one-SE-rule error bars and the nonmonotone
  curves are readable; PS split bands and 0.8/0.9 guides do not imply confidence
  intervals. K1 is included only where defined. The silhouette and WCSS axes
  retain their actual scales; no artificial elbow or selected-K highlight.
- 02: bootstrap ranges show unstable classes rather than truncating low
  Jaccard values; matching markers/ranges use consistent colors. The quadrant
  panel retains all four points per K. Ward and seed curves use distinct
  line/marker styles. The rare-set projection comparison and its unredistributed
  budget are explicitly identified; its shaded region is min-max, not a CI.
- 03: ECDF steps preserve ties and overlap. The four selected coordinates have
  clear original units; K3 and K4 have separate model-specific legends and
  counts. At native size, 7-pt legends and 8-pt axes are readable, with no
  clipped labels, title overlap, map distortion or unsupported smoothing.

Class colors in 03 are diagnostic fit-local identifiers, not a modification
of official class IDs. These plots describe fitting inputs and must not be
presented as external validation. They are explicitly labeled exploratory and
not formal Stage 7. Scientific interpretation is in SCIENTIFIC_DECISION.md.
