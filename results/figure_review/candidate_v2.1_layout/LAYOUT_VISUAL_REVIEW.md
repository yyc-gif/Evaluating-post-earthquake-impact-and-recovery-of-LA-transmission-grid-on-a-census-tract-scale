# Actual-output layout review

Scientific content changed = NO. This review concerns the isolated layout candidates, not promotion or manuscript figure selection.

All twelve exported figure previews were opened individually. The Fig03 and Fig05 journal-page previews were also opened at their native 185-mm placement. Each exported PDF was measured for physical size, actual embedded fonts, minimum text size and text outside the page.

| Candidate | Actual-output checks and visual adjustments |
|---|---|
| Fig01 | Diagram chain and box wording retained; long capacity note wrapped inside its box; caption explanations are outside the artwork. |
| Fig02 | Four panels retained; GIS geometry unchanged; top-row legends moved below maps; agreement labels moved away from the utility map; titles aligned. |
| Fig03 | Four-part baseline chain retained; decomposition has a shared exterior legend; T80 map and histogram share a row with independent readable areas; horizontal map colorbar is clear. |
| Fig04 | All eight scheduled policies and the reference remain visible; four explanatory policies have stronger strokes; shared legend is outside the data; four outcome columns retain their ranges and axes. |
| Fig05 | Height reduced from 218 to 208 mm; a single nine-policy key replaces repeated keys; axis labels no longer touch following panel titles; Gini ticks remain readable; tract-map physical dimensions are unchanged at 64.925 × 50.236 mm. |
| Fig06 | Crew categories and policy offsets unchanged across four panels; top shared legend separated from panel titles; long labels wrapped without reducing font sizes. |
| Fig07 | Category palette unchanged; map colorbar moved outside geography; profile colorbar label is visible; typology and hotspot titles aligned; non-membership display retained. |
| FigS05 | Five search traces, incumbent, seed points and retained-sequence identity remain visible; common text hierarchy applied. |
| FigS09 | Four diagnostic panels retained; existing cluster-ID palette unchanged; labels and legends readable. |
| Cross-hazard candidate | Four comparisons and every annotated value retained; lower whitespace reduced; colorbars and hazard labels fit. |
| Crew-resource candidate | All discrete cases and policies retained; labels wrapped; intervals, legends and panel spacing readable. |
| Repair-duration candidate | All discrete cases and policies retained; labels wrapped; no continuous interpolation added; panel spacing readable. |

Measurements: all figure PDFs are 185 mm wide; minimum extracted text is at least 7 pt; Arial and Arial Bold subsets are embedded; no extracted text extends outside any figure page. PNG exports are 600 dpi. The A4 page-preview packet places each native PDF at 1:1 scale, without shrinking artwork to fit.

The numerical source hashes, original candidate files and formal publication collection are unchanged. Caption science and statistical definitions are unchanged; current caption edits synchronize display terminology and the Fig05 D/E panel references. Plot-value/geometry/axis-limit signatures match before and after the layout adapter. See `LAYOUT_IDENTITY_VALIDATION.json` and `LAYOUT_ACTUAL_OUTPUT_QA.csv` for the recorded checks.

## Author-requested display corrections

- Fig02: `Simplified network topology` and `Modeled substations` replace the former display wording. Percentage labels receive an additional 3-pt horizontal gap from each point; values and points do not move in data coordinates.
- Fig03: Long Beach uses a stronger blue solid line; San Fernando uses a purple dashed line, also reflected in the damage boxes. Northridge uses a dash-dot line. The steep 2pc50 curve is drawn above the frame and the left frame is offset outward 3 pt; probability limits and every CDF coordinate remain unchanged. The bottom-left histogram explicitly identifies `2pc50 Unconstrained T80` and `2pc50 realizations (n)`.
- Fig04: the vertical label is `Mean population-weighted service availability`; the source series and averaging remain unchanged.
- Fig05: the existing Gini subplot is explicitly panel D, and the existing tract-effect map is E. Captions, panel crosswalk and review packet use the same letters; no subplot is added or removed.

Updated Fig02-Fig05 actual previews were opened after these corrections, including the separated CDF/frame and the Gini/map lettering. PDF measurement continues to require normal text at least 7 pt and no off-page text. These changes are confined to the layout review folder.
