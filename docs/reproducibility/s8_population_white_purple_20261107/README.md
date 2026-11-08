# Figure S8 population palette correction

Requested change: white-purple instead of teal for Panel C population fills and its colorbar. Stops: white, #E0D6E9, #B69ACB, #8B63AC, #613A80. The second stop matches the existing A/B purple.

The original truncated grayscale color ramp is mapped monotonically to the new color ramp. This is a display-only color reassignment: population values, log normalization, ticks, station priorities, map paths, and text remain unchanged. The colorbar retains its original raster support and resolution; tract geometry remains vector.

Source: pinned canonical S8 PDF at 0f67aa1f2758fcf1d35c112c36eb04e6d8a5dd68. Before-change current suite: e611e93cea95e5c7296c47bbe1dc0777fe97e31a. Exact payload hashes and geometric checks are recorded in QA.json. Archived suites and scientific records are not edited.

Reproduce this scoped change:

```powershell
python docs/reproducibility/s8_population_white_purple_20261107/refresh.py
python -m pytest tests/test_s8_white_purple_20261107.py -q
```

The canonical `build_current_suite_p2.py` uses the same `figure_presentation.priority_geography` renderer and white-purple caption. Inspection previews are local-only and excluded from Git. Only the final S8 artwork and dependent publication artifacts are delivered.

Visual inspection: full-page native-proportion render and enlarged Panel C render checked. Map and colorbar have matched ordered white-purple shading; station circles, priority labels, linework and legends remain legible. Full-page image confirms A/B remain unchanged. No new artwork or explanatory annotations were added. S8 is 185 x 264 mm; PNG export is 600 dpi.

Verification: 3 targeted tests passed; 9 active-suite tests passed (2 unrelated tests not selected: pre-existing missing change-manifest registry and all-preview rendering). The targeted test independently reproduces the PDF through the canonical population renderer. Renderer output was checked twice for exact deterministic bytes. Other 15 artwork PDF/PNG pairs and their mirrors match the current baseline manifest. Main-figure packet bytes are retained; supplementary and complete packets are rebuilt. The complete packet remains 16 pages.
