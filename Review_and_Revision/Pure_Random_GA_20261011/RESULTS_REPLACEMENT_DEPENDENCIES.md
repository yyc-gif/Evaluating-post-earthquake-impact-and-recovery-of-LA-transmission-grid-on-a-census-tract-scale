# Candidate-specific manuscript result reconciliation

The paper's main text should describe one GA: the frozen random-only repeated-run method. The legacy GA is retained for independent-study provenance and, if useful, supplementary paired comparison, not as a second optimization method in the main narrative. Internal optimizer trials are not a manuscript contribution.

| Manuscript item | Replacement source | Completed review status |
| --- | --- | --- |
| GA method and final chromosome | FINAL_GA_EXECUTION_PROTOCOL.json; FINAL_RANDOM_GA_CANDIDATE.json | Ready for author review |
| Planning objective | Reused original 64-realization native evaluation for the selected sequence | Verified; 32.99552241352315 h compiled, 32.99552241352189 h native |
| Recovery curves | RECOVERY_CURVES.csv; FIG_GA_RECOVERY | New 2,000-draw mean curves replace Figure 1 only in the review copy |
| Population service loss | POLICY_OUTCOMES.csv; PAIRED_EFFECTS.csv; FIG_GA_POPULATION_LOSS | GA-minus-Impact -0.532675 h; simultaneous 95% [-0.563982, -0.502321] h |
| Hospital-associated service loss | Same new-cohort tables; FIG_GA_HOSPITAL_LOSS | Difference -0.260704 h; unweighted normalized burden over 103 associated tracts, not actual hospital load |
| Fairness | Frozen SOVI tract-quartile burdens; absolute gap and Gini; FIG_GA_EQUITY | Mean absolute gap increases 0.232733 h and Gini 0.009790; Figure 4 reports the unfavorable disparity result |
| System T80 | New-cohort population-weighted system 80% crossings | 45.178976 h GA, 45.273142 h Impact; all 2,000 crossings before 480 h, not mean tract T80 |
| Abstract, conclusions, captions and numerical strategy comparisons | MANUSCRIPT_PARAGRAPH_CHANGE_LEDGER.csv; Table GA1 | Updated in a clean separate review copy, not fabricated tracked changes |
| Stage 7 recovery-dependent inputs/labels and hotspot priorities | Separate dependency reconciliation if their saved B/Init/T80 inputs came from the legacy sequence | Not authorized to refit or silently relabel in this task |

Preserve old validation and its strategy hashes. Changing Methods alone does not update any scientific results. Do not assert empirical physical accuracy from a successful stochastic model validation. If the new candidate does not outperform a comparator on a particular endpoint, retain that finding without reselection or another search.

The original manuscript, formal outputs, legacy final sequence, network, sources, travel, mapping and physical samples remain unchanged. This directory contains controlled review material, not an automatic promotion or submission.

The review-copy parent is the previously authorized Stage 7 review copy, SHA-256 `3f90a76593b24abbb4a175766ba9f2f7f683919781c475f4e7f4320f0e58acc4`, derived from the confirmed working manuscript. Only document text and the Figure 1/Figure 4 PNG parts change. All other package parts remain byte-identical. Figure 2 and Stage 7 retain their historical Impact-first recovery source, with explicit provenance rather than silently becoming new-GA results.
