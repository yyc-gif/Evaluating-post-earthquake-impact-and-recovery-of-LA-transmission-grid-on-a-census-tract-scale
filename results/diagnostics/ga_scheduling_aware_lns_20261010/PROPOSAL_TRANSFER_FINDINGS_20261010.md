# Why the tested source-aware LNS did not work: fixed-start proposal diagnosis

Completed [8-seed proposal transfer study](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38065546076), seeds 1000–1007. Two **fixed** existing chromosomes were tested independently: (i) earlier inherited best J=33.038131743 h and (ii) frozen formal GA best J=32.997840774 h. Each seed/parent combination samples 64 real source-reconnection events from previously frozen planning states; each proposal generates up to 12 insertion ranks × 3 internal orders, and its *best of these repairs* is evaluated under the unchanged 64-planning-realization population-weighted mean objective. The random-bundle control uses the **same** event sample and bundle size. There are **512 paired event proposals per starting chromosome** (8 seeds × 64 events), **1024 pairs total** and four scores per pair (individual-event and whole64 for each arm). No evolving optimizer or new physical samples were run.

The full per-seed `LNS_TRANSFER_SUMMARY` values are retained in `reconciliation/TRANSFER_8_SEED_LOG_SUMMARY.json` alongside the [run artifacts](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38065546076), which record the actual selected events, candidate counts, source mass, and scores.

| Start chromosome | Repair proposal | Mean loss change on event-generating single realization (h) | Mean loss change on original all64 aggregate (h) | Event sample improved | All64 aggregate improved |
|---|---|---:|---:|---:|---:|
| Previous optimized warm | Source-route repair | +0.026931 | +0.027937 | 7.23% | **0/512** |
| Previous optimized warm | Random-damaged-bundle repair | +0.107223 | +0.103017 | 8.79% | **0/512** |
| Formal frozen GA | Source-route repair | +0.034451 | +0.037126 | 4.49% | **0/512** |
| Formal frozen GA | Random-damaged-bundle repair | +0.108325 | +0.109764 | 7.03% | **0/512** |

Positive delta = **worse** service loss than the unchanged reference. These are best repaired proposals from each event macro, *not* a complete evolving search; the candidate sets are not distributions of independent physical draws.

**Key finding:** The poor LNS performance is not just a case of individual-event improvement failing to transfer to the 64-realization objective. Almost all candidate proposals fail even on the originating source-event realization. Moving a connected source-route bundle as one rigid block is an ineffective way to repair the priority permutation near either of the two reference solutions. Even when the generating sample improves, the all64 objective did not improve in this bounded test.

At these two fixed starts, route-aware moves actually cause **less average damage** than random repaired bundles, yet in the previous adaptive 20-seed LNS-v2 full search, the random-bundle algorithm improved the global best 12.7 times per seed on average versus 1.5 for the source-aware arm. Thus static proposal quality and adaptive search-basin exploration are different questions. The route arm can make smaller harmful moves but reach fewer globally improving alternative basins. Do not claim single-realization overfitting is the *sole* identified cause.

## Immediate next step

Do **not** run more seeds or increase budget for unchanged LNS-v1/v2. If there is a separately justified further optimizer method, change the **proposal construction principle**: jointly alter only completion-critical delayed cut/gateway/crew assignments identified across multiple original realizations, allow noncontiguous multi-insertion, and *prospectively* compare against randomized but equally strong destroy/reinsert controls. This is a potential new method, not warranted simply by tweaking the current bundles' percentages. Any new test uses only the 64 existing optimization samples.

More important to the paper is the existing, proposed **one-time 2,000-realization independent physical validation** of fixed policies and candidate sequences, whose protocol states explicitly that physical sampling requires author approval. Before such a run, resolve the missing centrality/closeness policy comparators, decide whether the refined ILS diagnostic challenger is a declared secondary comparison, freeze exact sequences and analysis rules, and obtain authorization. Keep validation outcomes out of method selection. Neither the LNS full experiments nor this proposal study accessed validation samples.
