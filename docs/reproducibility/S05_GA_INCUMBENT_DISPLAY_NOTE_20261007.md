# S05: direct five-seed comparison with the planning incumbent

The author requested two panels in place of the generation-mean search panel and the mixed fixed-rule/final-result panel.

- **A:** best-so-far planning cumulative service loss across generations 0–100 for seeds 42–46. The black dashed line is Impact-first. The saved best-so-far archive includes the initial incumbent, and every seed's trace is constant at 33.57830255999965 h. Sparse, seed-specific symbols lie on the original trace values; neither axes nor data are jittered to separate coincident curves.
- **B:** final best planning service loss for each seed, with the same black dashed reference and the same real hour axis. Each final value equals its saved incumbent. Points do not encode standard deviations or confidence intervals.
- The seven fixed-rule scores remain in their original table. Their comparison is summarized in the caption, rather than taking over panel B.

The negative-fitness sign is converted to positive service loss for display. The separately saved direct incumbent score differs from the GA incumbent by less than 1e-12 h, consistent with the existing exact-objective equivalence record. The planning horizon is 2,855.2540131100995 h, as recorded before search; it is not the 480 h evaluation horizon. The 64 planning realizations and five search seeds are distinct from the evaluation realizations.

Only the saved GA histories, five-seed final summary, fixed-rule table and planning-horizon record are read. No objective, GA, scheduling or simulation entrypoint is called. Their hashes and exact displayed values are recorded in `S05_GA_INCUMBENT_DISPLAY_20261007.json`.

The native 185 × 90 mm PDF and rendered PNG were opened. Titles, units, seed symbols, shared scales and the black reference are legible; the actual PDF uses embedded Arial and a minimum 7.5 pt font. The PNG is a 600-dpi preview. The old S05 artwork is retained in `provenance/figure_review_history/ga_incumbent_before_20261007/`.

The author-review S05, its publication copy, caption, inventory and complete figure-and-caption packet are synchronized. Other numbered artwork is unchanged. The bounded search result does not establish global optimality.
