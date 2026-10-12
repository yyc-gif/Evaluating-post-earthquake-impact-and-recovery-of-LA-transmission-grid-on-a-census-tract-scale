# Targeted author-review package

Start with AUTHOR_REVIEW_FIGURES_AND_CAPTIONS.pdf: the recommended full figures at 185-mm native width, each followed by its proposed caption. NATIVE_BEFORE_AFTER_CONTACT_SHEETS.pdf shows the current and proposed artwork side by side, each full figure still 185 mm wide. Print at 100%; do not fit the wide comparison sheets to A4.

Recommended candidates: Fig01_Author_Review, Fig03_Low_End_Palette, Fig05_Q4_Context_Candidate, Fig07_Cluster_Color_Candidate and FigS09_Palette_Synchronization. Each has a vector PDF and a 600-dpi PNG. Fig04 remains byte-identical and is included in the review packet; see FIGURE4_ASSESSMENT.md.

Fig03E_Palette_Comparison.pdf shows the focused E-panel comparison at the native panel size. The alternatives directory contains full-size Fig5 individual-Q4-outline and Q1-Q4-locator prototypes and both full Fig7 categorical-color alternatives. The chosen Fig5 uses Q4-area outer boundaries to reduce central clutter; the chosen Fig7 uses slate-blue C4. Nothing here is promoted or replaces the numbered figure set.

The `before` directory contains exact copies of the current authoritative PDFs, not older historical candidates. Source hashes are checked against the actual 031d2c6 Git/LFS payloads. Current formal five-cluster identities and the six scheduled manuscript policies remain. Experimental CORE3/W1 labels are not used.

Reproduce in order, using Python with PyMuPDF, Matplotlib, GeoPandas, pandas, NumPy and Pillow:

1. inspect_baseline.py (read current baseline PDFs; render inspection previews).
2. preserve.py (snapshot original checkout without changing its index).
3. revise_artwork.py (base candidates and alternatives).
4. finish_candidates.py (final framework and less crowded Q4-area overlay).
5. build_review_package.py (captions, contact sheets and author-review packet).
6. pytest test_invariance.py; preserve.py --after; finalize.py.
7. Commit only this directory, push the isolated review branch, and run verify_remote_delivery.py.

No simulation, scheduling, GA, clustering, bootstrap or scientific-table producer is called. Geometry union is solely a display operation on frozen tract polygons. Quartile assignments are read, not recomputed. Degree-first's saved per-tract comparison identity is checked, not replaced.

The preservation record checks 950 scientific files, the original staged index and status. See SOURCE_HASHES.json, OUTPUT_HASHES.json, CANDIDATE_MANIFEST.csv, NUMERICAL_INVARIANCE_QA.json and REMOTE_DELIVERY_VERIFICATION.json for byte-level and remote checks.
