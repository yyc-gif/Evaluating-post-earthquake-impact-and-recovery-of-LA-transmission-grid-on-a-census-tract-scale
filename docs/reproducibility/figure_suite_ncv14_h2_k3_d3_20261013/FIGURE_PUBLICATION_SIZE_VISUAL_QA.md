# Native publication-size visual QA — PASS

Actual changed vector PDFs and the assembled packet were rendered and inspected, not merely the previous source candidates. The published width is 185 mm. Numbered PNGs are exported at 600 dpi; page previews and changed figure/caption packet pages are rendered at 160 dpi.

| Artifact | Inspection and result |
|---|---|
| Fig01 | Only the former Hotspot score text cell changes. The new two-line Spatial service-deficit patterns label fits; Community typology remains distinct. Pixel comparison at 160 dpi is identical outside the bounded label rectangle. The Arial PDF maps spaces/hyphens to nonbreaking-space/soft-hyphen codepoints in extraction; the semantic test normalizes those equivalent characters, without altering other diagram content. |
| Fig07 A | C1/C2/C3 tract shares and resident shares are visibly distinguished by solid/outline bars. Exact tract and resident counts fit alongside the bars and match the frozen table. |
| Fig07 B | Eight separate original-unit axes avoid mixed-unit normalization. Two-line titles prevent collision. Population is in persons for display, log1p for fitting. Availability is clearly a percentage; both deficit quantities are hours. |
| Fig07 C/D | Matching EPSG:3310 extent, complete study geography and distinct neutral N/A fill. Three muted class colors are fixed. Continuous cividis deficit shading is ordered; Q4 outlines, the hour colorbar and N/A have separate, non-overlapping legends. No threshold, Top-10 ranking, hotspot or intervention marker appears. |
| Fig07 PDF properties | Zero raster image objects after explicitly disabling Matplotlib's default colorbar rasterization; maps, graph marks, labels and colorbar are vector artwork. |
| FigS09 | Authentic neutral K curves with only K3 emphasized as adopted; no K4 class membership/profile/map. Geographic and policy labels fit the left margin. Per-class boxplot annotation clears the upper whisker. No PCA or old residential denominator. Zero raster image objects. |
| Packet | Changed figure pages 1/13/29 and caption pages 2/14/30 were inspected at native size. All text bounding boxes stay inside the page. Caption fonts are at least 10 pt. The full 38-page contact sheet confirms the ordered 17 figure/caption pairs and four unchanged complementary-evidence pages. |

All 17 actual figure pages were also compared pixel-for-pixel with their corresponding assembled packet pages. All mirrors match authoritative PDF/PNG bytes. The 14 unaffected numbered figure pairs, including S05 and merged S11, retain the approved baseline SHA256s.

Evidence: `FIG01_LABEL_PIXEL_QA.json`, `NATIVE_PDF_AND_PACKET_LAYOUT_QA.json`, `COMPLETE_PACKET_AND_MIRROR_QA.json`, `UNCHANGED_FIGURE_HASH_COMPARISON.csv`, and `Packet_Page_Previews/`. Analytical maps/graphs are Matplotlib/GeoPandas and native PDF edits; no AI-generated imagery is used.
