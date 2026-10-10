# GA Research Continuation: Completed Evidence

Diagnostic branch: `diagnostics/ga-algorithm-interaction-and-alternatives-20261009`.
This note supersedes the earlier GA-only methodological preference, not the formal strategy or its protected outputs.

[Consolidated report](../../results/diagnostics/ga_deeper_research_20261009/continuation/GA_OPTIMIZATION_CONSOLIDATED_RESEARCH.md)
contains the experiment inventory, seed-level contrasts, source-connectivity mechanism,
cross-fitting, influence diagnostics, computation accounting and reproducible commands.

## Main Findings

- All outstanding Actions studies completed. Thirteen runs were reconciled, including one failed superseded parity attempt and the later successful refined-candidate audit. All 127 existing artifacts were retrieved and hash-checked. The six regular batches comprise 718 searches; cross-fitting adds 40 searches. Repeated artifact copies and checkpoints are not independent runs.
- Refined ILS has original-production mean planning loss **32.99613736538761 h**, with maximum per-realization production/compiled discrepancy **3.44e-12 h**. The unchanged formal GA candidate remains **32.997840773882714 h**. Refined sequence SHA-256: `75a1014c7f921c09b574eed4eebcaa412f86fcbc61487bf4a1277c4eb448ddbd`.
- At 500k distinct evaluations, ten-seed mean losses are GA tournament3 **32.999132080 h**, tournament5 **32.999825296 h**, and ILS **32.998030855 h**. ILS-minus-GA3 is **-0.001101224 h**, simultaneous 95% interval **[-0.002591758, +0.000389309] h**. ILS wins 7/10 paired seeds and uses about 65% of GA3 wall time and 11% of attempted calls. This supports competitiveness, not statistical proof of universal superiority.
- GA3/GA5 have zero improving seeds from 250k to 500k; ILS improves in 7/10. The short-budget tournament5 advantage does not establish a robust default at higher budgets.
- Refined ILS improves only 14/64 physical states and worsens 50/64. Omitting state15 reverses its mean advantage to **+0.030758169 h**. Four-fold internal cross-fitting has **16/20** optimizer-pair training/held-out ranking reversals. These are conditional development diagnostics, not untouched external validation.
- The first ILS state15 gain of **2.082523454 h** is source-reconnection driven: source loss decreases **2.279239845 h**, despite worse self and threshold loss and greater total crew travel. Three independently evaluated feasible priority interventions show that moving station301745 alone does not reproduce the gain. Joint restoration of source307373 and the surrounding path/order matters; no isolated station-level causal effect is asserted.
- Original GA archives could retain Impact-first after its chromosome disappeared from the population. Twenty exact native-history replays distinguish archive preservation, elitism, operator effects and useful search from simple diversity or parent-relative improvement.

## Decision and Boundaries

Retain the formal GA candidate. ILS plus deterministic multi-neighborhood refinement is a credible challenger; a tiny selected mean gain is not sufficient evidence of physical robustness or authorization to replace the strategy. Completed neutral, perturbation, local-refinement and prior hybrid evidence is analyzed, not converted into another list of unexecuted tests. A dedicated scheduling-aware LNS benchmark remains unperformed and is explicitly distinguished from completed experiments.

No physical samples, repair durations, objective, scheduler, network, source gate,
population mapping, manuscript figures or Stage7 results were changed. The proposed
2,000-state validation collection was not accessed. Revision-checkout HEAD, unrelated
staged changes and 950 protected files are checked in the preservation receipts.

Complete important permutations, canonical hashes, independent validation receipts and all
seed-level statistics are retained under the consolidated report's `continuation/` directory;
original Actions ZIPs and extracted members are under `actions_raw/`.
