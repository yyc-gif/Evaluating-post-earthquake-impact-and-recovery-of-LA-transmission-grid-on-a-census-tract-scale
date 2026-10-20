# Final scientific and visual review of S05

## Decision

**READY_FOR_AUTHOR_APPROVAL** for the unchanged proposed figure and the concise accompanying caption. No graphical correction, split, rearrangement or numerical alteration is necessary. This is figure-readiness, not automatic promotion or a declaration that every manuscript paragraph is reconciled.

## Actual inspection

Inspected the actual candidate PDF and original 600-dpi PNG from the source review worktree, not Git LFS pointers. Verified the prior output manifest and all 86 archived immutable source payloads before review. The unchanged PDF SHA-256 is `58bc67206d0e418b1079a418ea2151fa75eca78e2e5365815b6d1c62db40432d`.

The PDF is 185.000 x 178.000 mm. Independently rendered at 200 dpi with **MuPDF 1.28.0** and **Poppler 26.07.0**; both complete-page renders and the original PNG were visually opened and inspected. Render dimensions preserve the native publication width, not a enlarged single-panel crop. The candidate uses embedded Arial/Arial Bold; saved technical QA reports a minimum 7.5-pt text size and vector artwork with no raster-image panels. These are supplemented by actual visual inspection, not treated as its substitute. Browser/display physical scaling cannot certify a printer or a monitor's ruler calibration; the PDF and approval-page embedding dimensions are the publication-size authority.

## Panel-by-panel observations

| Panel | Scientific check | Actual presentation observation | Decision |
|---|---|---|---|
| A | 20 archived best-observed step trajectories, 64 fixed planning states, 100k distinct queries per run; right-continuous median; no interpolated loss history | Dark median is distinct from pale paths; late paths genuinely overlap. Axis explicitly says thousands of distinct evaluations and absolute loss hours. Dashed Impact-first is labeled reference only. Legend and all title/axis text fit. | KEEP |
| B | All 20 initial/final pairs; selected seed 2026103108; same loss limits as A | Selected diamonds and seed annotation are legible. Final losses cluster together naturally; no jitter or magnified endpoint inset was added. The 10/20 and failed 90% criterion are visible below the axis. | KEEP |
| C | All 2,000 original candidate-specific validation cases, including unfavorable cases and both tails; saved Bonferroni simultaneous mean CI | Whole ECDF spans the actual -4.967486 to +1.139627 h range. Dotted red mean and dashed dark zero differ in both color and pattern. Mean CI has its own inset hour axis and explicit simultaneous-CI label, spatially clear of the rising ECDF. No quantile whisker is labeled a CI. | KEEP |
| D | Same cohort; exact component values retained in source CSV; self +0.277475453672, threshold +0.010637992790, source -0.820787986509, net -0.532674540047 h | Positive red and negative blue bars consistently mean increased/decreased loss. Neutral net bar is distinct. The tiny threshold bar is rightly tiny on the common hour scale; its +0.010638 annotation carries the value. Zero line, six-decimal labels and component names are readable, without collisions. | KEEP |

The source accounting closes within the previously verified `3.730349362740526e-14 h` per-case tolerance. Six-decimal displayed components sum to -0.532675 h; exact source values are not replaced by rounded artwork values. Existing statistical and production checks were read and hash-verified, **not rerun**.

## Coherence and duplication

A/B establish genuine finite-budget optimization from random initialization and seed reproducibility; C/D establish this frozen sequence's separate physical performance and accounting mechanism. This is a coherent supplementary argument, not four unrelated algorithm experiments. Keep all four panels together at 185 mm.

Inspected current main-figure packet pages 1-7 and caption text; no main figure displays these 20 seed histories or the fresh 2,000-case GA effect ECDF. Main Figure 3 also uses decomposition, but for unconstrained recovery across hazards, not the signed GA-minus-Impact effect in D. Main Figure 5 covers vulnerability-targeted policy contrasts in the original 1,000-case ensemble, not this GA validation. S7 addresses source reachability and alternate routes, not this component contrast. Similar concepts are complementary, not redundant evidence.

Original S05 remains an authentic historical figure, but is not the final pure-random-GA visualization. Its generation budgets, deterministic initialization and separate 1,000-case exploratory evaluations cannot accompany the proposed final caption.

## Remaining boundaries

- Single-run near-optimal reliability is not demonstrated. Endpoint overlap does not convert the failed 90% criterion into a success.
- The original simultaneous interval retains its original two-population-contrast family; changing the figure's number of panels does not alter that family.
- Mean loss reduction is not an equity benefit: absolute SOVI quartile disparity and tract Gini increase. No power-flow, MW or actual-customer claim is supported.
- The separate later post-evaluation-elitism cohort is not used for C/D. Engineering correction and selected-sequence performance are distinct.
- Manuscript promotion requires coordinated approved edits. The previously identified complete external working manuscript remains missing; the inspected backup is not restored or designated current.

## Review artifacts

The source candidate PDF/PNG and existing/proposed comparison remain unchanged in `../Final_Pure_Random_GA_S05_20261012/`. The two-page approval packet embeds that identical vector PDF at exactly 185 mm width on page 1 and puts the concise caption and author decisions on page 2. Render receipts and visual-review attestations accompany this review. No replacement figure files are generated merely to create another version.
