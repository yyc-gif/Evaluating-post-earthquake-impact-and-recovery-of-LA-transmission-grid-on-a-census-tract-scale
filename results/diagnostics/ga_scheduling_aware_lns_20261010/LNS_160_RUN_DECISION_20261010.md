# Full LNS 100k comparison — reconciled negative results and research next action

Evidence authority: [original LNS v1 24/24 successful GitHub Actions jobs](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38033702030) and [independent new-seed LNS v2 24/24 successful jobs](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38034064901). Both include 4 engineering smoke seeds plus 20 full 100k-budget seeds. All **160 full-budget case/seed records** were reconciled from their archived full 92-ID permutations by [offline audit 38065463263](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38065463263); its `ga-lns-160-run-negative-audit` artifact contains the full machine-readable cross-seed statistics and verification output. No optimizer run or physical sample was regenerated to construct this report.

## Primary 100k comparisons (lower modeled mean loss J is better)

| Method | v1, seeds 820–839: mean J (h) | v2, seeds 920–939: mean J (h) |
|---|---:|---:|
| Existing final GA | **32.999892304** | **32.999799415** |
| Existing ILS | 33.000315359 | 33.001203353 |
| Source-event route LNS | 33.038041659 | 33.037022548 |
| Random damaged-bundle control | 33.037878468 | 33.032375723 |

The **v2 event-route minus randomized-bundle** paired mean is **+0.004646825 h**, with three-comparison Bonferroni simultaneous 95% interval **[+0.002093024,+0.007200627] h**; route loses **18/20** pairs. The v1 equivalent contrast is +0.000163191 h with interval [-0.000341830,+0.000668212], unresolved. In both 20-seed blocks, event-route LNS is worse than final GA and ILS in **all 20 seed pairs**.

Both LNS implementations were fully executed (100,000 expensive distinct objective evaluations per method/seed); the poor performance is **not** evidence of a missing execution step or identical candidates only. A failed initial workflow with a syntax error was superseded by the successful v1 run; no failed or partial record enters this comparison.

## Why accepted moves do not imply optimizer improvement

| Diagnostic per v2 100k seed | Event-route LNS | Random-bundle LNS |
|---|---:|---:|
| Mean strictly accepted *current-state* repair moves | 233.4 | 220.7 |
| Mean truly improved **global best after inherited warm reference** | **1.5** | **12.7** |
| Runs with no globally improved warm best | **8/20** | **0/20** |
| Runs attaining lower loss than inherited older warm best | 12/20 | 20/20 |

For v1, event-route averaged 1711.95 strictly accepted current-state moves but only 0.25 new global-best improvements; 18/20 seeds never improved the older best. These are two different counters: accepted improvements after a stagnant/restored/perturbed *current sequence* can remain worse than the previously seen global best.

In v2, event-route and random-bundle arms both searched multiple repair insertions at the same budget and both retained 30% conventional local proposals. Thus route-conditioned targeting performed worse than non-informed bundle selection even within that repair framework.

### Mechanism (testable, not yet established)

The proposal bank is constructed from *four sampled planning realizations* and ranks single-realization source-gate reconnection events. The optimizer's actual J is the equally weighted mean across all **64** original planning realizations. Advancing a high-value source route within one realization might harm dispatch/crew/source timings in others. In addition, connectivity witnesses from an already functional source component may include already repaired or marginal stations; blindly moving that whole set earlier is not necessarily beneficial.

The negative effect therefore warrants a **proposal-level transfer diagnostic**, not another unchanged 100k LNS repetition. [The targeted fixed-start event-sample versus all64 proposal audit](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38065546076) was launched on eight fresh diagnostic seeds, comparing route-targeted versus random damaged bundles at both the inherited prior best and frozen formal GA sequence. It checks where a source-event proposal improves the generating realization but worsens the 64-sample mean. It is not a competing optimizer or physical-validation experiment.

## Scientific next actions

1. Reconcile the completed `ga-lns-160-run-negative-audit` machine report and the proposal-transfer diagnostics. If the expected single-realization-to-mean transfer failure appears, test a genuinely new **cross-realization consensus/reconnection-aware** proposal. Design the rule before new outcomes; compare against random bundle, GA and ILS with equal distinct objective budgets and recorded wall/attempted costs.
2. If the proposal diagnostic contradicts that mechanism, examine proposal size, order, refresh rate and terminal plateau connectivity. Do **not** assume network-aware LNS must win.
3. For paper claims, keep the formally frozen GA and verify meaningful policy behavior on a **separate untouched physical sample**. Internal 64-sample analyses and more optimization evaluations cannot establish unseen earthquake generalization. The proposed untouched cohort must be evaluated only after methods, candidate sequences and analysis are frozen; no tuning or reselection after observing it.
4. Preserve all negative outcomes; do not call LNS v1/v2 effective, infer GA universal superiority, or promote a lucky new planning-best sequence without full production and sensitivity audits.

All research outputs are diagnostics only. No change to original repair model, final GA, physical inputs, manuscript results or future independent-validation sample.
