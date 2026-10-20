# S05 figure-text correction — 2026-10-12

The active isolated branch and remote HEAD were both f010a4b42ebb7b160ab78556405bdb5c8e8a3ef6 before authoring. The original protected Windows worktree was not edited. All inputs were read as actual bytes from that pinned commit and its existing LFS cache.

Only S05 display text, legend glyphs and its blank footer margin were changed. All original source-stream graphics bytes and all non-target text were retained. The four data regions were additionally compared by actual PDF rendering at 216 dpi; their pixels were identical. No source table, scientific evaluator, simulation, schedule, GA, clustering, bootstrap or manuscript was executed or changed.

The final display removes the B/D explanatory footnotes and global footer. Titles and keys use plain wording; an actual diamond identifies the selected run, and actual blue/red/charcoal swatches identify decrease/increase/net change. The signed values and comparison with Impact-first remain explicit. Necessary initialization, selection, finite-budget, confidence-interval and distributional qualifications remain in the caption. The caption uses service loss throughout.

The numbered vector PDF, 600-dpi PNG, mirror, native preview, manifest/index, Supplement packet and complete figure/caption packet were synchronized. The other eighteen numbered figure pairs and Main packet remain exact copies. The final native figure and actual caption page were visually inspected for clipping, spacing and readable keys.

An initial text-integrity check caught Arial Unicode aliases for spaces and hyphens in newly inserted PDF labels. Explicit ASCII ToUnicode mappings corrected searchable text without changing its rendered appearance. The completed checks pass: 9 tests in 25.59 seconds. The final four data-region and two packet comparisons pass.

PRESERVATION_BEFORE.json and PRESERVATION_AFTER.json agree byte-for-byte in their scientific hashes, original index hash, staged-file list and original worktree status: 950 protected files and 862 staged items. Prior artwork and qualification records remain available in the pinned source commits and prior immutable QA package.

Reproduce the edit using the existing Anaconda Python, with the bundled ReportLab dependency path appended and src/la_grid/plotting on sys.path. Run simplify_s05_figure_text_20261012.py, then verify_visual.py and tests/test_current_figure_suite_integration.py. verify_delivery.py checks remote HEAD, both numbered GitHub directories and actual remote LFS payload hashes after push.
