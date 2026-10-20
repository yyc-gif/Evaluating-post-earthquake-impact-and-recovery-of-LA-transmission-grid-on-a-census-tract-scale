# Figure presentation corrections - 2026-10-14

Baseline: `96297fb12fceb8e61137b456648d2655a5909b6b`, branch `2026-10-14`.

- Panel headings are centered on their own panels, with a common size within each figure.
- S02: Task-to-task travel, without the Directed qualifier.
- S03: static percolation is distinguished from time-dependent component/degree recovery; corresponding row gaps are controlled separately from title-to-plot spacing.
- S04: initial and final best repair orders are both identified per GA run. No new optimization is run.
- S05: mapping, source connectivity, and a combined threshold comparison form three panels. The saved alternative thresholds are **0.05 and 0.75**, not 0.50 and 0.75; 0.50 is the reference. All nine mean/range records are reused without recomputation. No explanatory footer is embedded.
- Previous S08 clustering artwork is removed from the active suite; numerical clustering evidence and historical artwork remain preserved. Previous S09/S10 become S08/S09.
- New S08 identifies substation repair priorities explicitly. Its population context and colorbar use an ordered neutral gray scale, without changing values, geometry, station priorities or other map fills.

The active registry contains 16 numbered figures (Main 1-7; Supplement 1-9).
The combined PDF contains 16 native-size figure/short-caption pages and four retained evidence pages: 20 pages total.

## Verification

`BEFORE.json` records source artwork and all 17 current scientific-authority files before edits. Artwork retired from active paths is backed up locally under ignored `build/retired_artwork_20261014/` and remains in Git/LFS history. `ARTWORK_COMPARISON.csv` uses explicit old/new paths for renumbered figures.

`PRESENTATION_QA.json` records transformations, saved threshold values, and the neutral-palette geometry check. Tests independently check the actual nine error-bar endpoints in the exported vector PDF against the saved CSV, rather than trusting this record alone. Scientific assertions for GEOIDs, populations, all seven features, weights, memberships and quartiles remain in the suite tests.

```powershell
python src/la_grid/plotting/build_current_figures.py --portable
python docs/reproducibility/supplement_presentation_20261014/verify_update.py
python -m pytest tests/test_current_figure_suite_integration.py -q
python docs/reproducibility/p2_final_adoption_20261014/finalize_workflow.py
```

The builder reads pinned artwork and existing numerical results. It does not run physical simulations, scheduling, GA, source propagation or clustering. Inspect changed native-size previews and their pages in the actual combined packet. Remote delivery is verified using a fresh LFS store and SHA256 of downloaded payloads, not Git pointers.
