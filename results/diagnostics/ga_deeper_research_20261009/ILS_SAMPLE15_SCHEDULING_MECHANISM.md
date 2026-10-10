# Scheduling mechanism behind the influential planning realization 15

The original formal earliest-free-crew decoder was applied to every one of the previously saved 64 planning samples with the exact frozen GA and new ILS 92-station sequences. [Completed Actions run 38025630104](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025630104) contains `ILS_SCHEDULE_INFLUENCE_MECHANISM.json`, including every sample's objective/travel/completion diagnostics and the detailed station changes for realizations 15, 55, 13, 58, 50. **No new physical samples or scientific-model changes.**

In realization 15, ILS decreases modeled cumulative population-weighted loss **2.082523454063 h**, yet among 90 damaged stations it alters 44 completion times: **22 earlier and 22 later**. There is no uniform faster completion:

| Characteristic | New ILS minus frozen GA |
|---|---:|
| Cumulative loss | −2.082523454063 h |
| Total directed crew travel | **+1.142998168232 h** |
| Mean damaged-station completion time | +0.050290139 h |
| Population-dependency-mass-weighted mean completion time | +0.202259229 h |
| Maximum absolute single-station completion change | 13.114913569 h |

Examples of advanced station completion: `307373` (−13.114914 h; DS3), `301745` (−7.600147 h; DS3), `301637` (−7.085225 h; DS3), `309703` (−3.192681 h; DS4). Examples delayed: `308806` (+11.025751 h; DS3), `300627` (+7.217655 h; DS3), `310204` (+5.408404 h; DS4), `303303` (+5.177906 h; DS3).

This rules out a simplistic explanation in terms of lower total crew travel or earlier average station completion. **A nonlinear connectivity/source-threshold mechanism is plausible but is not established merely by these completion times.** A separate exact event-time `L_self + L_threshold + L_source = L_total` decomposition has been coded and launched to test the mechanism directly. Station times and network states are jointly schedule dependent; single-station completion changes are descriptive, not independently identified causal effects. The full 64-realization production loss audit and influence sensitivity are recorded in `ILS_NEW_BEST_INFLUENCE_AUDIT.md`.
