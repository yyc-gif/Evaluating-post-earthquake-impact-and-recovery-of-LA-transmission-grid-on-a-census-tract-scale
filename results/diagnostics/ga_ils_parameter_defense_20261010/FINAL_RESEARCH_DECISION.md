# Final Research Decision

## Completed Work

Reconciled historical inventory and original duplicate/overlap audits; executed the precommitted engineering and independent confirmation studies; ran five fixed-seed deterministic refinements and matched-total-budget GA continuations; independently verified 40 important new 92-station sequences through all 64 production realizations. Their exact permutations, hashes, objectives and influence are in IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json. All are diagnostic, not formal policy replacements.

The strongest new verified development candidate has objective 32.99552241352189 h and SHA-256 `288c37e1219d69d03734f21db615cdb4ecc1c1f95d235b7314d37ff1593bf673`. It improves 14/64 planning realizations but worsens 50/64. Its mean difference from the frozen GA is -0.00231836036083 h; excluding realization 15 reverses that difference to +0.03044145575588 h. The better planning minimum is therefore not evidence of robust physical generalization or grounds for formal promotion.

## GA Decision

| parameter             | classification                |
|:----------------------|:------------------------------|
| Representation        | SUPPORTED                     |
| Population            | DEFENSIBLE WITH QUALIFICATION |
| Crossover operator    | SUPPORTED                     |
| Crossover probability | DEFENSIBLE WITH QUALIFICATION |
| Mutation operator     | SUPPORTED                     |
| Mutation probability  | DEFENSIBLE WITH QUALIFICATION |
| Selection             | DEFENSIBLE WITH QUALIFICATION |
| Generational elitism  | DEFENSIBLE WITH QUALIFICATION |
| Initialization        | DEFENSIBLE WITH QUALIFICATION |
| Best-so-far retention | SUPPORTED                     |
| Adaptive mutation     | DEFENSIBLE WITH QUALIFICATION |
| Restart               | DEFENSIBLE WITH QUALIFICATION |
| Diversity replacement | DEFENSIBLE WITH QUALIFICATION |
| Budget/stopping       | SUPPORTED                     |

The formal fixed method remains scientifically defensible with these qualifications. The missing elite-count comparison was completed instead of deferred. Exact population, probabilities, tournament size, one-elite count and initializer allocation are not certified optima. Background-specific disabled adaptation/restart/crowding and alternative crossovers are documented limitations rather than claims all such mechanisms fail.

## ILS Decision

The requested neighborhoods, three stagnation thresholds, three perturbation cycles, best/current restart, no-perturbation accessibility and a focused operator/stagnation interaction were actually studied. Only screen-selected threshold/strength alternatives received full independent confirmation; the other alternatives retain engineering-screen status. Single-swap has a reduced neighborhood description; its contrast is mean -0.001762417 h; median -0.003275649; paired SD 0.003297369; simultaneous 95% interval [-0.004067700, +0.000542866]; wins/losses/ties 13/7/0 (n=20). Original multi-operator ILS plus optional refinement is not automatically simpler than GA.

The swap/2000 package improves the original mixed ILS under the prospective confirmation family: mean -0.002187538 h; median -0.001880154; paired SD 0.002682022; simultaneous 95% interval [-0.004062614, -0.000312461]; wins/losses/ties 16/4/0 (n=20). Direct comparison with GA, mean -0.002226523 h; median -0.001496724; paired SD 0.001995669; simultaneous 95% interval [-0.003312434, -0.001140612]; wins/losses/ties 20/0/0 (n=20), is a separate retrospective exploratory finding. It provides real conditional evidence for a competitive reduced-neighborhood optimizer, not grounds to continue claiming GA superiority against only weak alternatives. The interaction itself remains unresolved and does not establish synergy.

Recommend Scope A in the main manuscript and the complete parameter audit in supplement. Scope B can be presented as postvalidation methodological development, but requires an explicit editorial decision and cannot inherit untouched validation status. A lower planning minimum alone does not select a formal optimizer.

## Computation and Preservation

32,258,131 new distinct main-batch objective calls; 359,267,484 attempted main-batch queries; 327,009,353 duplicate lookups. Refinement adds 749,175 distinct calls, matched GA continuation adds 749,175, and 500,000 prefix scores are reused. Setup/parity/export full-64 equivalents: 12,287; total new full-64 calls: 33,768,768. Additional independent production checks: 2,560 single-realization calls, reported as a different unit. Main-batch incomplete controls: 40. First serializer-only QA failure and its repeated bounded parity work are disclosed and counted.

Screen wall 378.0s; confirmation wall 4814.3s; summed worker CPU 60420.1s. Concurrent worker-wall sums are not elapsed study time. GA cached-prefix replay time is included separately. EXECUTION_ACCOUNTING.json gives the complete ledger.

No physical samples were generated or changed; no completed validation outcomes were used. Before/after protected950-file and revision-index comparisons, formal configuration/sequence and validation artifact hashes are recorded. Source-content checks distinguish Git/LF identities from Windows CRLF working bytes. Publication includes actual remote HEAD and downloaded LFS object verification, not merely local commit success.

## Remaining Insufficient Evidence

No global optimum or exact hyperparameter optimum; no pure population intervention with all initializer and RNG composition held fixed; no powered final-swap comparison of every crossover/adaptive/restart/crowding option; no new untouched physical confirmation of postvalidation settings; no claim that every planning-state improvement is robust to influential-state omission. Five-seed deterministic refinement is a bounded consistency check, not exhaustive optimizer-family validation. All feasible missing targeted studies requested here were completed; these remaining broader questions do not justify an uncontrolled new grid.

## Existing Draft Claims to Qualify

Historical docs/reviewer/FIGURE_S04_S05_S06_INTERPRETATION_20261007.md, GA_SEARCH_BUDGET_SENSITIVITY_20261007.md and EXTENDED_GA_AND_SELECTED_STRATEGY_20261008.md describe older version-specific decisions. Do not transfer those decisions to the current frozen method without version labels. Older continuation's 'LNS untested' statement is superseded by completed LNS/actionable-delay packages. Prohibited current claims include globally optimal GA, universal optimizer superiority, all improvement produced after initialization, exact parameters independently validated, or ILS simpler merely because it stores one sequence. No existing manuscript was edited.

EXISTING_METHOD_CLAIM_AUDIT.csv identifies the relevant source lines and distinguishes valid historical statements from claims that would exceed the evidence if used as current Methods. The strongest new development candidates and their sample sensitivity are summarized in IMPORTANT_CANDIDATE_SUMMARY.csv, without promotion.

The proposed frozen-method paragraph in FINAL_GA_METHOD_AUDIT.md line 66 is already bounded: it discloses inherited initialization, finite budgets and no global-optimality proof. It need not be accused of claiming universal superiority. A real wording ambiguity is "Counts exclude generation-zero scoring" in GA_BUDGET_AND_REPLICATION_DECISION.md line 14: this must identify strict improvement counts, because the expensive-query budget does include the seven incumbent scores. Legacy July/inversion/generation-limited descriptions must not be copied into current frozen-method text. This is a source-bounded draft audit, not a claim that an uninspected current manuscript contains every prohibited assertion.

Stop this bounded audit after evidence publication and preservation/remote verification. Do not promote new settings or run the completed validation cohort again.
