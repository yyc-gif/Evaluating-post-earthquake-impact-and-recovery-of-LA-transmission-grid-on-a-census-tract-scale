# Figure 7D continuous bivariate review, 2026-10-15

Branch: `review/fig7d-continuous-bivariate-20261015`.
Publication authority: `b307e6deafc054864787a3db63ad95218be91659`.
Read `VISUAL_ASSESSMENT_AND_RECOMMENDATION.md` first. Nothing is promoted.

## Review artifacts

- `FIGURE7D_CONTINUOUS.pdf` and 600-dpi PNG: primary blue-amber D, enlarged for
  detailed inspection. Both variables affect the color continuously.
- `FIGURE7_CONTINUOUS_REVIEW.pdf` and 600-dpi PNG: experimental complete figure;
  A-C are the unchanged approved regions, with only D and its key replaced.
- `ORIGINAL_VS_CONTINUOUS_COMPARISON.pdf`: page 1 compares complete figures at
  identical 7.2-inch widths; page 2 compares original, blue-amber and teal-wine D
  at the identical native map size. 300-dpi PNGs accompany both pages.
- `CONTINUOUS_2D_LEGENDS.pdf`: enlarged blue-amber and teal-wine continuous keys,
  with 600-dpi PNGs. These use the same color functions as the tract fills.
- `ALIGNED_SEPARATE_MAPS.pdf` and 600-dpi PNG: separate continuous SOVI and burden
  maps, preserving the native map dimensions. This is the grayscale/independent-
  reading reference, not an unapproved rearrangement of the complete figure.
- `ACCESSIBILITY_COMPARISON.png` and `previews/`: actual-PDF native-size,
  grayscale and three CVD simulation comparisons.
- `PROPOSED_CAPTION.md`: proposed wording only, separate from official captions.

## Scientific and technical records

`SOURCE_HASHES.csv` binds delivered inputs to their exact publication-commit
payloads. `DATA_AND_GEOMETRY_QA.json`, `HIGH_HIGH_94_GEOIDS.csv` and
`VERIFIED_TRACT_DISPLAY_VALUES.csv` retain all scientific definitions and counts.
The original 94-tract list is included for an independent equality check.

`COLOR_MAPPING_SPECIFICATION.json`, `TRACT_DISPLAY_COLORS.csv`,
`PALETTE_CORNER_COLORS.csv` and `PERCEPTUAL_ACCESSIBILITY_DIAGNOSTICS.csv`
define the continuous mapping, exact gamut rules and numerical stress tests.
They do not certify human visual performance.

`ABC_PIXEL_PRESERVATION.csv`, `SOURCE_VECTOR_TO_GEOID_QA.csv`,
`INDEPENDENT_OUTPUT_VECTOR_QA.csv`, `PDF_PUBLICATION_QA.csv` and
`TRACT_NATIVE_DISPLAY_SUPPORT.csv` separate source-path provenance, rendered
invariance, font/vector checks and small-tract display support.

`PRESERVATION_BEFORE.json` and `PRESERVATION_AFTER.json` bind the original
publication/1021 worktree status, index hashes and relevant payloads.
`PROTECTED_950_HASHES.json` retains the protected scientific-file authority.
`INDEPENDENT_QA.json`, `TEST_RESULTS.json`, `tests.xml`, `PACKAGE_HASHES.json`
and `REMOTE_DELIVERY_VERIFICATION.json` record completed QA and delivery.

## Reproduction

All scientific inputs needed to render the alternatives are under `inputs/`;
no restoration event archive, clustering fit or simulation is needed. Fetch
actual Git LFS payloads before running. Python 3.12, NumPy, pandas, PyMuPDF,
Pillow and Arial fonts are required; GeoPandas is used for source/geometry QA.

```powershell
$D = 'results/diagnostics/fig7d_continuous_bivariate_20261015'
python "$D/build_review.py"
python "$D/verify_review.py"
python -m pytest "$D/test_bivariate_review.py" -q
python "$D/verify_rebuild.py"
```

`prepare_sources.py` is the initial baseline-bound acquisition/preservation
record, not a command to overwrite that record after committing. The renderer
is self-contained. The preservation portion of verification additionally
requires the original neighboring publication/1021 worktrees and the local
protected-file archive. Those original index/status comparisons are machine-
local preservation checks, not a claim of cross-machine clean-clone testing.

Only this directory may be committed. The source Figure 7, manuscript, captions,
other numbered figures, publication packet and 1021 experiment remain unchanged.
