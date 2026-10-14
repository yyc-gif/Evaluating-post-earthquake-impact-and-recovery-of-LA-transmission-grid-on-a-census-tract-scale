# Publication-size inspection

The four changed figures were inspected as actual PDF renders at their native
185-mm width and in publication-size previews. The final package is assembled
from the actual final PDFs; per-page pixel identity is independently tested.

- Figure 1: T80 is defined, quartile sequence and absolute gap are distinct,
  Stage 5 labels use 7.5-pt body type, and the redundant Schematic label is gone.
  No clipping or collisions were observed. Outside the authorized Stage 5 and
  small Stage 4 T80 text regions, changed pixels are exactly zero.
- Current S04 (former S05): sequence counts, 20-run endpoints and the independent
  validation set are distinguished. The mean-only annotation leaves the frozen
  ECDF readable. Damage/threshold/source components have explicit loss labels.
  The removed CI inset no longer obscures the story.
- Current S05 (former S06): mapping, source-only and threshold-only effects have
  separate panels. Source-off points are labeled with the correct hour gaps.
  The source-only panel uses means and realization percentiles, not confidence
  intervals. Existing threshold plots are translated without scaling; their
  aligned rendered data/axes region is pixel-identical at 254 dpi. The nested
  original PDF clipping was retained to avoid exposing hidden historical ticks.
- Current S09 (former S10): a muted blue population palette replaces the warm
  orange map. Geography, log scaling, colorbar indices, ranks and dark priority
  markers are preserved. The map and legend remain readable.

All 600-dpi numbered previews have at least 4,360 pixels of width. Caption pages
use minimum 10-pt text and pass page-bound checks. Current Figure 7, K3 data,
white N/A maps, D3 values and all other 13 unchanged artwork pairs retain their
source bytes. No AI imagery was generated or substituted.

Former S09 C/D and S11 are content-review questions, not silently redesigned
here. Their necessity is evaluated in `S09_S11_SCIENTIFIC_NECESSITY_REVIEW.md`.
