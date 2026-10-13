# Current author figure corrections — 2026-10-12

Branch: `review/official-figure-suite-final-s05-20261012`.
Starting local/remote HEAD: `37e71b3e15b0f4e1be3a651344e3f9e6475dc24b`.

| Figure | Actual change |
|---|---|
| Fig1 | Stage5 uses Service loss/T80; Q1-Q4 service loss/Quartile gap/Gini; Service-loss changes/Community typology/Hotspot score. Remove the selective all/hospital list, percent definition, policy-effect row mixed with metrics, and Tested conditions block. Resource/model comparisons remain in the caption and corresponding figures. Stages1–4 unchanged. |
| Fig5E | Color normalization clips at -20/+20 h. End ticks coincide exactly with the colorbar endpoints. All 6,945 polygon paints were checked against exact saved tract values and GEOID order; polygon geometry, all three references, Q4 outlines and A–D are preserved. |
| S02 | No current artwork, caption, index entry or placeholder. No search in another folder is required. |
| S6 | Remove the joint threshold/source-removal panel from the numbered sensitivity figure. Keep cutoff and the existing threshold 0.05/0.75 comparisons relative to 0.50; the source requirement and Core sources remain unchanged. The archive has no source-only control. Joint-removal values remain in the audit CSV; no isolated source effect is invented. S7 is the separate source-redundancy analysis and is unchanged. |
| S9 | Only K-means inertia and silhouette remain. Read the original diagnostic values, without fitting or changing the five-class solution. |
| S10 | C still plots tract population on its existing log scale and exact range. Warm YlOrBr colors replace blue; middle colors are softened. Dark first-five symbols/rank text and white number labels contrast with the map and are synchronized across A/B/C and keys. |
| S11 | The previous baseline heatmap's 24 means equal Fig4 policy means minus Unconstrained means (maximum error below 1.2e-14 h); retire this redundant separate display. New S11 combines all eight original S12/S13 panels by outcome row and resource column, with readable text and a shared six-policy/symbol key. Original marks, means and 5th–95th ranges are reused. |
| S12/S13 | Combined into S11; remove old numbered files, mirrors, previews, caption headings and index entries from the current set. Their exact source bytes remain at the starting commit. |

Seven Main plus ten Supplement figures remain in this one directory. Three packets, native previews, manifest/index and figure-facing captions are synchronized; the complete packet contains 38 pages. All eleven unrelated figure pairs, including S05, are byte-identical to the starting set.

Actual vector renders, assembled packet pages, source hashes, protected-file/index checks and tests are recorded under `docs/reproducibility/author_suite_final_layout_20261012/`. The only remaining missing experiment is a source-only removal control; this figure-only round neither creates nor implies one. No author decision is needed to locate the current artwork.

No manuscript or formal scientific output is changed. Original 950 protected files and 862 staged items are preserved. Earlier provenance packages remain unchanged, and this isolated figure branch is not automatically merged into the manuscript branch.
