# Author decision, not an implementation approval

**Recommendation for review: Candidate A's four-panel scientific logic.** No separate Candidate B was generated. A different line-profile or cosmetic arrangement was not shown to add scientific information beyond the restored distribution/profile functions, so a second decorative option would not be justified.

The recommendation is not approval. Current Figure 7, its canonical generator, every other figure, captions, mirrors, manifests and packets remain unchanged.

## Scientific story visible in Candidate A

| Saved type | Tracts / frozen residents | SOVI mean | Spectral impact mean | Baseline deficit mean (h) | Five-policy increment mean (h) | NCV14 mean |
|---|---|---:|---:|---:|---:|---:|
| C1 | 1,242 / 5,101,704 | 77.05 | 0.00620 | 30.33 | 1.61 | 0.6556 |
| C2 | 475 / 1,897,838 | 52.48 | 0.12016 | 27.65 | 6.96 | 0.5902 |
| C3 | 582 / 2,066,980 | 55.46 | 0.33195 | 37.58 | 4.15 | 0.6201 |

Values are rounded here only for reading; the QA CSV retains full precision. "Higher/lower" is relative to the full frozen cohort or the other saved classes, not a universal vulnerability or resilience threshold.

A's empirical distributions make within-type overlap and heterogeneity visible, including the nearly coincident HHI distributions. B makes the joint contrasts legible: C2 has lower baseline loss but a higher constraint increment; C3 has higher structural impact and baseline loss; C1 has higher social vulnerability and lower constraint increment. These do not imply that social vulnerability causes less loss or that climate/other hazards were simulated as electrical failures. NCV14 is a geographic frequency-area screen, not official FEMA risk, expected monetary loss, or an outage probability.

Init_Supply has 1,533 exact zeros (66.6812%) and a maximum of 0.0245. All three class medians are zero. Its class means are only about 0.0247%, 0.2142% and 0.00225% availability for C1-C3. The B z-score contrast is a relative initial-state signal, not evidence of strong absolute resilience. No smoothing, trimming, changed transformation or new fit was used.

## Decisions requiring the author

1. Restore A to distributions and B to a common-scale multivariable profile rather than representation bars/original-unit mean bars.
2. Accept the six proposed A coordinates: spectral impact, dependency HHI, Unconstrained deficit, MeanDelta, SOVI, NCV14. All eight stay visible in B; Init and log population are not removed from fitting.
3. Accept empirical CDFs instead of historical KDE, and the three median markers instead of one maximum-median line. This is a deliberately disclosed encoding proposal. It avoids unsupported smoothing of ties/zero-heavy measures; density modality is less directly visible.
4. Accept the frozen full-cohort, ordinary z-score means in B, not historical centroid-only normalization or square-root-weighted distance coordinates. H2 fitting is unchanged.
5. Accept the proposed 185 x 253-mm page, with the intact current C/D region translated down 8 mm and no resizing. It has exact aligned pixel and source-content-stream identity.
6. Make a separate decision on N/A gray versus restoring archived white fill with dark outlines. Candidate A retains current gray until that decision; the white alternative appears only in its isolated comparison.

## What a later approved update would need

These are dependency requirements, not instructions to execute promotion now:

- Update the Figure 7 presentation route in `src/la_grid/plotting/build_current_suite_k3.py` only after an exact layout is approved, preserving accepted data sources, D3 values and the existing separate S10 cross-reference correction at `7795638a73ac533d544971c20db13cf6662d13d3`.
- Replace `results/figure_review/Main/Fig07.pdf` and `.png`, its page preview, and the exact `results/figures/Fig07_Community_Typology_and_Service_Deficit.pdf/.png` mirrors.
- Update Figure 7's A/B caption in `MANUSCRIPT_FACING_CAPTIONS.md`, its generator/artwork provenance in `FIGURE_MANIFEST.csv` and `FIGURE_INDEX.csv`, the gallery description and update log. Keep all numerical identities and class colors.
- Rebuild the affected main/complete packets from final artwork and captions; the complete numbered suite must remain 17 figures/38 pages. Preserve every other artwork pair and the S10/S11 reference.
- Adapt presentation-specific assertions in `tests/test_current_figure_suite_integration.py` to approved distributions/profiles and retained count/source checks. Do not delete or weaken scientific membership/population/weight/D3 invariants.
- Update `CURRENT_CLUSTER_PALETTE.json` only if a separate N/A-style decision requires it; class colors/IDs do not need changing. Record new frozen artwork hashes and figure-specific visual/replay QA.

No change to S09, Figure 1, model data, the formal Stage 7 pipeline or manuscript is needed to implement a visual-only A/B restoration. No K4 classification is proposed. Formal manuscript/data migration requires its own scope and approval.

**STOP: author review is pending. No current-suite update or merge is authorized by this package.**
