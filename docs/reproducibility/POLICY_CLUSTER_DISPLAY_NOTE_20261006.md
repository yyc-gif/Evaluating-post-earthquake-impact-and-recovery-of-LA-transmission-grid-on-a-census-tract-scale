# Author-requested policy and cluster display correction

- Fig05: filled Degree-first triangles; all four quartile-policy connectors solid; four emphasized scheduled policies plus Unconstrained in the first legend row; secondary policies in the second; panel titles centered.
- Fig06 and the capacity comparison use the same filled Degree-first marker. Parallel metric wording is also synchronized in Fig04, FigS11, FigS12 and FigS13.
- The reader-facing group metric is **High–low vulnerability service-loss gap**. Its definition remains the absolute Q4–Q1 group-mean service-loss difference within each realization, summarized across realizations. It is distinct from the signed difference and population-weighted Gini.
- Hospital-linked mean service loss remains an equal-weight tract mean; the population-wide and Q4 outcomes remain population weighted. Wording consistency does not imply identical weighting.
- Fig05E retains the two available spatial references: Hospital-first and Impact-first. `VULNERABILITY_TRACT_EFFECTS.parquet` contains those references only; Degree-first has summary comparisons but no saved tract-effect map. No missing map was calculated or fabricated.
- Fig07 and FigS09 share explicit cluster-ID colors from ColorBrewer Set2: C1 `#66c2a5`, C2 `#fc8d62`, C3 `#8da0cb`, C4 `#e78ac3`, C5 `#a6d854`. The numeric profile heatmap, hotspot scale, cluster membership, PCA values and map boundaries are unaltered. The choice is qualitative-category coding, not a new cluster calculation or a claim that every form of color-vision deficiency is resolved.

## Resource-variable scope

The existing complete resource evidence comprises separate one-factor families: crew availability C29/C57/C86/C114 at duration multiplier 1, and repair duration 0.75/1/1.25/1.50 at C57. Neither is a complete crew-by-duration factorial. Current Fig06 remains limited to these observed conditions. Mapping cutoff and functionality/source-gate thresholds are model-assumption checks, rather than additional restoration-resource capacity variables. Directed travel is a fixed logistics input in these families. No additional resource variable or scientific comparison is introduced.

## Visual references

- ColorBrewer qualitative cartographic palettes: https://colorbrewer2.org/
- Nature figure preparation guidance on readable labels and color separation: https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/

The correction changes native PDF text/paint and existing preview files only. Prior artwork is retained under `provenance/figure_review_history/policy_cluster_before_20261006/`. Current author files, publication copies, captions, indexes and the complete packet are synchronized.
