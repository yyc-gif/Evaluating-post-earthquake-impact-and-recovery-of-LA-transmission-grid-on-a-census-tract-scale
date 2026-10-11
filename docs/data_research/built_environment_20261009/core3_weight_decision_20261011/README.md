# CORE3 final domain-weight decision

Start with CORE3_FINAL_WEIGHT_DECISION.md. It recommends W1 as the single reference convention and qualifies the four-class taxonomy. CORE3_SCIENTIFIC_INTERPRETATION.md supplies the numerical evidence, class-meaning changes and minority failure cases. The selected measurement set is unchanged.

Required tables cover the five vectors, same-seed changes, raw transitions, spatial stability, stock/ALR profiles, domain/feature sums of squares and the exact 34-member group. Full run_records preserve actual estimator centers, scalers, factors, labels/predictions and 11-digit GEOID order. CORE3_EXACT_INPUTS.npz retains exact floating-point input values; CORE3_MASTER_2291.csv retains the four unclassified records. Tables contain empirical summaries, not confidence intervals.

Reproduction: use the recorded Python 3.12.3/scikit-learn 1.5.1 environment. Run preregister.py once; fit_weights.py reuses complete hash-matching checkpoints; summarize_weights.py and meaning_audit.py derive tables without fitting; write_decision.py writes the decision from completed results; make_diagnostics.py and render_and_check_pdfs.py create/render the diagnostic figures. Tests recompute consequential numerical identities without new KMeans fits. Do not import the parent package's common.py, which writes to its own output directory.

Diagnostic figures are 185 mm wide with minimum 7.5 pt text, vector PDFs and 600 dpi PNGs, with actual-PDF render previews and captions. They are not manuscript replacements. W1's 40 original fits are reused; W2-W5 added 160 fits. No additional schemes, variables, k values, PCA or scientific simulation was executed. The 20 spatial cases represent 17 unique geographic deletion sets. All interpretation retains measurement-source and spatial-sample limitations.

The original 950 protected scientific files, 862 staged items, formal Stage7, manuscript, figures, trajectories, scheduling and GA outputs remain untouched. Only this isolated diagnostic package is committed on its research branch. No formal promotion is authorized.
