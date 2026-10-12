# Supplement follow-up for author review

Start with COMBINED_TARGETED_AUTHOR_REVIEW.pdf. It contains the preceding Main-figure review and these five supplement candidates, with each figure followed by its proposed caption. NATIVE_SUPPLEMENT_BEFORE_AFTER.pdf keeps both sides at 185-mm figure width; print at 100%, rather than fitting the wide sheet to A4.

S03 removes station IDs from the travel display and adds point transparency. S06 makes the joint removal explicit; separate removal controls are absent from the saved design. S07 separates four focal policies and other selected policies in both dynamic rows, with Unconstrained repeated as the same reference. S10 uses neutral population shading. S11 uses one disclosed signed-log color scale to retain the large effects while revealing the smaller ones.

Each candidate has a vector PDF and 600-dpi PNG. The current numbered figures, formal results and prior review candidates are preserved. This package is not promotion.

Reproduce: inspect_inputs.py; revise.py; package.py; pytest test_review.py; verify_package.py. All numerical sources are read-only. The S06 per-policy offline shards are local saved files whose exact hashes are registered by the committed display record; they are not individually tracked Git blobs. No missing removal control is generated or inferred.
