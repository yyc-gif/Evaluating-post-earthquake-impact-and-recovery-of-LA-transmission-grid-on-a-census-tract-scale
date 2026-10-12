# Targeted author-review changes

Authority: current numbered artwork, captions and manifest at 031d2c675f8e7d58035d27448be040b809ced086, verified against the remote revision branch. This package proposes display changes only. The current numbered set and formal figures are not overwritten.

| Figure | Exact display change | Recommendation |
|---|---|---|
|1|Scale 12 existing marker Forms and 246 inline circles to 75% of their original linear dimensions, including stroke widths; retain their centers, original path bytes, node identities and invocations. Replace only the Stage 5 distribution illustration with four labeled schematic bars and a gap bracket. Replace the recovery wording with Cumulative service loss / All tracts and / hospital-linked tracts / T80: time to 80%.|Review the candidate. Stage boundaries, arrows, all five stages, Spatial Patterns and Tested Conditions remain.|
|3E|Actual source palette is YlGnBu. Lift only its lowest normalized quarter from t to 0.12 + 0.52t. Middle and high colors stay exact; recolor the indexed colorbar lookup consistently.|Use the proposed darker low end, which is easier to distinguish against white. Same tract paths, scalar colorbar pixels, numerical range, conditional estimand, missingness and ticks.|
|4|No artwork change.|FIGURE 4: RETAIN CURRENT DESIGN. No duplication of Figure 5 gap metrics.|
|5E|Add a transparent 0.24-pt, 75%-opaque dark outline of the exact frozen Q4 polygon union to each of the three maps; omit internal boundaries between adjoining Q4 tracts. Add an 8-pt explanation above the maps.|Recommend union outlines at the original 185 x 250-mm size. Effect fills, colorbar, original map sizes and A-D stay exact.|
|5E alternatives|Individual-tract outlines and a separate Q1-Q4 locator were rendered. The locator preserves all existing maps at native size, increasing total height to 310 mm.|Individual outlines clutter central areas. The locator gives clearer standalone quartile context, but adds 60 mm; retain it as a review alternative.|
|7A/C|C4, originally #68a9b5, is the cyan category with 545 formal members and broad mapped coverage. Alternative A is #648890 muted teal; alternative B is #7b828f slate blue. Change C4 paint only, including its curves, median if present, map fill and keys.|Recommend B: it is less saturated and more distinct from the unchanged green C3 and blue C1. Other four categorical colors, N/A gray, Panel B and the continuous hotspot colors stay exact.|
|S9A|Synchronize C4 scatter and legend paint to #7b828f.|PCA scores, axes, loadings, explained variance and clustering support diagnostics remain exact.|

No labels were shrunk. Existing minimum fonts remain 7 pt in Fig1/S9 and 7.5 pt in the other retained figures; new main geographic context and locator text are 8 pt or larger. Compact framework labels are 7.5 pt within the established card. These baseline small-font facts are reported rather than claiming an 8-pt minimum for the entire suite.

All recommended figures retain 185-mm native width and their original height. The nonrecommended locator is the only extended-height prototype. New plots and overlays are vector; existing source colorbar images are retained as existing colorbar images, not whole-figure rasterizations. Each modified figure and prototype has a 600-dpi PNG.

Caption changes are limited to disclosing the Fig1 schematic and Fig5 Q4 context and targeting mechanism. Figure 3's conditional realization-specific T80 explanation and all previous scientific qualifications remain intact. No mapped mean is described as a significance result.

See ARTWORK_EDIT_RECORDS.json for exact transformations, SOURCE_HASHES.json for baseline bytes, QUARTILE_AND_DEGREE_PROVENANCE.json for formal quartile and Degree-first checks, and NUMERICAL_INVARIANCE_QA.json for tests and preservation.
