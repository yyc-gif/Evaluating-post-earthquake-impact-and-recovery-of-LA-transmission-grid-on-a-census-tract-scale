# Concise caption delivery

Baseline: `5fbdf5a33cb8cee4790f81e896776b8b6fb4f9ae`.

The 17 captions now explain the panels, definitions and necessary units rather than restating Results or Discussion. Text decreases from 4,219 to 856 words. Each native-size figure is followed immediately by its short 10-point caption on the same PDF page. Four previously retained evidence pages follow: 21 pages total, instead of 38. Figure dimensions are not reduced.

All 17 numbered PDF/PNG artwork pairs, all mirrors and both artwork-only packets retain baseline bytes. The current Figure 7 remains the previous eight-variable artwork until a separate Path B figure decision; no caption silently relabels it as seven-variable P2.

Verification: 30 figure-suite tests pass, including pixel comparison of every embedded figure, matching caption streams, figure/mirror hashes, scientific invariants and the four retained evidence pages. Visual inspection of packet pages 1, 7, 11, 12 and 16 found readable caption text without clipping. PDF text extraction can expose invisible legacy Form text outside clipped artwork; caption checks therefore verify the actual inserted caption stream and font sizes, not invisible source-object text.

Reproduce: `python src/la_grid/plotting/build_current_suite_k3.py --portable`. Use `--rebuild` for immutable-source recomposition. Historical author-clarity and earlier suite modes remain available. The new default never redraws science.

The original 950-file scientific snapshot and dirty index/staged state are compared before/after. This change is isolated from the source worktree and is not merged.
