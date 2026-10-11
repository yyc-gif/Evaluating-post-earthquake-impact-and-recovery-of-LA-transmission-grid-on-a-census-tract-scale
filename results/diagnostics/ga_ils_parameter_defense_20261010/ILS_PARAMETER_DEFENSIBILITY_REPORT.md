# ILS Parameter Defensibility Report

All new findings are postvalidation exploratory for the manuscript. Within this diagnostic study, the committed fixed contrasts and independent confirmation seeds are prospective; selecting two settings from the separate eight-seed engineering screen is explicitly recorded. No 2,000-realization outcomes were loaded for algorithm selection and no physical realizations were generated. The frozen formal GA configuration and sequence remain unchanged.

Negative paired differences favor the first-named method/setting. The replication unit is the optimizer seed, conditional on the same 64 planning states. Tables retain paired means, medians, SD, wins/losses/ties, pointwise t intervals, 20,000 seed-block bootstrap intervals and Bonferroni simultaneous intervals. These intervals concern optimizer variability, not physical population uncertainty. No equivalence margin was invented, and an interval containing zero is not evidence of equivalence.


## Actual Algorithm, Not Informal Shorthand

Warm ILS starts its current sequence at the same declared prior available to GA; seven reference evaluations are charged and eligible for best-so-far retention. Cold ILS starts at Impact; cold GA excludes the optimized prior and prior-derived neighbors but keeps Impact neighbors and random fill. They share allowed prior information, not identical candidate populations or RNG consumption. Initial chromosomes and fingerprints are retained.

For each local proposal, select swap, insertion or inclusive inversion uniformly; accept only fitness greater than current + 1e-12. Rejected proposals, including cache hits, increment stagnation. After 800 such attempts, perturb global best by 2, 4 or 8 sequential primitive moves cyclically and evaluate the final permutation. The perturbed current state may worsen; archive best cannot worsen. Those move counts are not kilometers, rank distance, counts of distinct changed stations or additional objective evaluations; mutations may cancel. Each search begins with an empty cache. No validation states participate.

The exact original-wrapper versus instrumented mixed-ILS short parity matches sequence, loss, attempts, accepted moves and restarts. Single-operator variants deliberately remove the random mixture-choice draw and therefore do not pretend to preserve identical later RNG streams.

## Completed Sensitivity, Including Negative Evidence

Engineering screen: 16 configurations x 8 independent seeds x 20k, all completed. All three stagnation values 200/800/2000 and perturbation cycles 1/2/4, 2/4/8 and 4/8/16 were screened. The lowest predeclared pair means selected 2000 and 4/8/16 for fresh confirmation. The additional swap x 2000 and swap/no-perturb mechanisms were committed before confirmation, after the separate screen. Confirmation has 16 cases x 20 seeds, with a target of 100k each. Accessible no-perturb controls that hit the 60x attempted-call safety cap are retained as incomplete, not equal-budget quality evidence.

| case                |   n |   mean_hr |    sd_hr |   best_hr |   mean_distinct |   mean_attempts |   mean_wall_seconds |   completed_budgets |
|:--------------------|----:|----------:|---------:|----------:|----------------:|----------------:|--------------------:|--------------------:|
| ga_cold             |  20 | 33.001096 | 0.002413 | 32.997723 |   100000.000000 |   797256.550000 |          220.944555 |                  20 |
| ga_elite0           |  20 | 33.000280 | 0.001832 | 32.998208 |   100000.000000 |   966554.050000 |          237.687048 |                  20 |
| ga_elite1           |  20 | 33.000143 | 0.001634 | 32.997748 |   100000.000000 |   792853.150000 |          221.440997 |                  20 |
| ga_elite2           |  20 | 33.000278 | 0.001582 | 32.998176 |   100000.000000 |   932731.350000 |          235.398278 |                  20 |
| ga_elite3           |  20 | 33.000296 | 0.001424 | 32.998656 |   100000.000000 |  1151412.000000 |          255.631158 |                  20 |
| ils_cold            |  20 | 33.000027 | 0.001643 | 32.996038 |   100000.000000 |   100956.700000 |          148.672636 |                  20 |
| ils_current         |  20 | 33.000619 | 0.002687 | 32.996004 |   100000.000000 |   101011.350000 |          148.749233 |                  20 |
| ils_insertion       |  20 | 33.016890 | 0.004183 | 33.006996 |   100000.000000 |   102196.650000 |          148.102243 |                  20 |
| ils_inversion       |  20 | 33.036169 | 0.003539 | 33.026511 |   100000.000000 |   103009.600000 |          148.396314 |                  20 |
| ils_large           |  20 | 33.000809 | 0.002383 | 32.996836 |   100000.000000 |   100909.100000 |          148.993836 |                  20 |
| ils_mix             |  20 | 33.000104 | 0.002390 | 32.996675 |   100000.000000 |   101006.200000 |          148.303662 |                  20 |
| ils_no_perturb      |  20 | 32.999409 | 0.000943 | 32.997937 |    60187.700000 |  6000000.000000 |          190.962531 |                   0 |
| ils_stag2000        |  20 | 32.999249 | 0.001607 | 32.995552 |   100000.000000 |   102378.200000 |          148.727290 |                  20 |
| ils_swap            |  20 | 32.998342 | 0.001303 | 32.996092 |   100000.000000 |   103788.350000 |          148.198685 |                  20 |
| ils_swap_no_perturb |  20 | 32.999500 | 0.001255 | 32.998469 |    24718.850000 |  6000000.000000 |          129.648529 |                   0 |
| ils_swap_stag2000   |  20 | 32.997917 | 0.001093 | 32.995689 |   100000.000000 |   109055.050000 |          147.701833 |                  20 |

- `ga_elite0 minus ga_elite1`: mean +0.000136686 h; median -0.000118375; paired SD 0.002778904; simultaneous 95% interval [-0.001494507, +0.001767879]; wins/losses/ties 10/9/1 (n=20). Scope: prospectively fixed confirmation.
- `ga_elite2 minus ga_elite1`: mean +0.000134608 h; median -0.000008199; paired SD 0.002115241; simultaneous 95% interval [-0.001107021, +0.001376236]; wins/losses/ties 10/10/0 (n=20). Scope: prospectively fixed confirmation.
- `ga_elite3 minus ga_elite1`: mean +0.000153063 h; median +0.000176518; paired SD 0.001893548; simultaneous 95% interval [-0.000958434, +0.001264559]; wins/losses/ties 8/12/0 (n=20). Scope: prospectively fixed confirmation.
- `ils_swap minus ils_mix`: mean -0.001762417 h; median -0.003275649; paired SD 0.003297369; simultaneous 95% interval [-0.004067700, +0.000542866]; wins/losses/ties 13/7/0 (n=20). Scope: prospectively fixed confirmation.
- `ils_insertion minus ils_mix`: mean +0.016785643 h; median +0.017647728; paired SD 0.004597687; simultaneous 95% interval [+0.013571272, +0.020000015]; wins/losses/ties 0/20/0 (n=20). Scope: prospectively fixed confirmation.
- `ils_inversion minus ils_mix`: mean +0.036065127 h; median +0.036304090; paired SD 0.004638876; simultaneous 95% interval [+0.032821959, +0.039308294]; wins/losses/ties 0/20/0 (n=20). Scope: prospectively fixed confirmation.
- `ils_current minus ils_mix`: mean +0.000514457 h; median +0.000176578; paired SD 0.002975752; simultaneous 95% interval [-0.001565975, +0.002594888]; wins/losses/ties 7/12/1 (n=20). Scope: prospectively fixed confirmation.
- `ils_no_perturb minus ils_mix`: mean -0.000695599 h; median -0.001582631; paired SD 0.002539758; simultaneous 95% interval [-0.002471215, +0.001080017]; wins/losses/ties 12/8/0 (n=20). Scope: prospectively fixed confirmation; unequal actual-budget accessibility control, NOT equal-budget quality.
- `ils_stag2000 minus ils_mix`: mean -0.000854844 h; median -0.000922925; paired SD 0.002777224; simultaneous 95% interval [-0.002796479, +0.001086791]; wins/losses/ties 13/7/0 (n=20). Scope: prospectively fixed confirmation; setting selected by independent screen.
- `ils_large minus ils_mix`: mean +0.000705137 h; median +0.001104269; paired SD 0.003823639; simultaneous 95% interval [-0.001968076, +0.003378350]; wins/losses/ties 8/12/0 (n=20). Scope: prospectively fixed confirmation; setting selected by independent screen.
- `ils_swap_stag2000 minus ils_mix`: mean -0.002187538 h; median -0.001880154; paired SD 0.002682022; simultaneous 95% interval [-0.004062614, -0.000312461]; wins/losses/ties 16/4/0 (n=20). Scope: prospectively fixed confirmation.
- `ils_swap_no_perturb minus ils_mix`: mean -0.000604486 h; median -0.000867473; paired SD 0.002527163; simultaneous 95% interval [-0.002371297, +0.001162324]; wins/losses/ties 12/8/0 (n=20). Scope: prospectively fixed confirmation; unequal actual-budget accessibility control, NOT equal-budget quality.
- `ils_mix minus ga_elite1`: mean -0.000038986 h; median +0.000449721; paired SD 0.002940574; simultaneous 95% interval [-0.001852845, +0.001774874]; wins/losses/ties 9/11/0 (n=20). Scope: prospectively fixed confirmation.
- `ils_cold minus ga_cold`: mean -0.001069415 h; median -0.001143809; paired SD 0.003192597; simultaneous 95% interval [-0.003038732, +0.000899902]; wins/losses/ties 11/9/0 (n=20). Scope: prospectively fixed confirmation.
- `ils_mix minus ils_cold`: mean +0.000077709 h; median +0.000235272; paired SD 0.002923840; simultaneous 95% interval [-0.001725829, +0.001881246]; wins/losses/ties 9/11/0 (n=20). Scope: prospectively fixed confirmation.
- `ga_elite1 minus ga_cold`: mean -0.000952721 h; median -0.000597997; paired SD 0.002774720; simultaneous 95% interval [-0.002664275, +0.000758833]; wins/losses/ties 12/8/0 (n=20). Scope: prospectively fixed confirmation.
- `ils_swap minus ga_elite1`: mean -0.001801402 h; median -0.001887167; paired SD 0.001699928; simultaneous 95% interval [-0.002726391, -0.000876414]; wins/losses/ties 17/3/0 (n=20). Scope: retrospective reduced-neighborhood method comparisons, not prospective primary family.
- `ils_swap_stag2000 minus ga_elite1`: mean -0.002226523 h; median -0.001496724; paired SD 0.001995669; simultaneous 95% interval [-0.003312434, -0.001140612]; wins/losses/ties 20/0/0 (n=20). Scope: retrospective reduced-neighborhood method comparisons, not prospective primary family.
- `swap x stagnation2000`: mean +0.000429723 h; median +0.001178066; paired SD 0.003908677; simultaneous 95% interval [-0.001399594, +0.002259040]; wins/losses/ties 8/12/0 (n=20). Scope: screen-motivated interaction; independent confirmation seeds; postvalidation exploratory.

Swap-minus-mix: mean -0.001762417 h; median -0.003275649; paired SD 0.003297369; simultaneous 95% interval [-0.004067700, +0.000542866]; wins/losses/ties 13/7/0 (n=20). Simultaneous support for lower swap mean in this confirmation is **False**. Regardless of significance, three operators are not automatically required. No additional two-operator mixture was launched: the predeclared individual-neighborhood screen already supported the more parsimonious single-swap check, and adding an unmotivated mixture grid would not answer a distinct mechanism.

The screen-selected settings are assessed on independent seeds, not evaluated with reused favorable screening seeds. Their precise values are not proven optimal. The focused difference-of-differences estimates whether operator performance changes with stagnation threshold; it does not generalize to untested perturbation schedules.

The completed equal-20k mixed-neighborhood no-perturbation screen gives mean -0.003948107 h; median -0.003899317; paired SD 0.005271264; simultaneous 95% interval [-0.010470001, +0.002573786]; wins/losses/ties 7/1/0 (n=8). This is an engineering-screen result, not an independent confirmatory contrast. At 100k, accessibility truncation prevents an equal-distinct-work quality claim for that control. Perturbation can enable further new-order scoring without being proved better by an unfair comparison to an incomplete local search.

## Deterministic Refinement Is a Separate Stage

Historical selected seed 304 stochastic ILS achieved 32.9971211516713 h. The additional deterministic neighborhood search used 132,545 distinct scores and seven accepted improvements to reach 32.99613736538884 h. Comparing that refined result to 100k GA without the extra cost would be unfair.

This study executed refinement from the first five prospectively fixed independent mixed-ILS 100k seeds, rather than selecting the best five. Original four-family scans and the 1e-9 improvement tolerance were retained, with a maximum of 150k additional distinct evaluations. For every seed the corresponding GA 100k search was continued to the same total distinct budget by deterministic prefix replay; its 100k prefix reused cached scores, not a repeated full-64 calculation. Replay overhead remains in wall time. The replayed 100k sequence hash, loss and initializer fingerprints are checked against the original prefix. The companion CSV includes complete base-plus-refinement and base-plus-GA-replay wall time.

|       seed |   base_loss_hr |   refined_loss_hr |   refinement_additional_distinct |   refinement_accepted_moves |   refinement_wall_seconds | scan_complete   |   joint_budget |   ga_joint_loss_hr |
|-----------:|---------------:|------------------:|---------------------------------:|----------------------------:|--------------------------:|:----------------|---------------:|-------------------:|
| 2026101200 |      33.000143 |         32.997117 |                           150000 |                          10 |                218.219519 | False           |         250000 |          32.998874 |
| 2026101201 |      33.002681 |         32.999467 |                           150000 |                           9 |                216.286050 | False           |         250000 |          33.001812 |
| 2026101202 |      32.997788 |         32.995571 |                           150000 |                           9 |                216.055003 | False           |         250000 |          32.999372 |
| 2026101203 |      32.996675 |         32.995522 |                           149175 |                           8 |                211.476851 | True            |         249175 |          32.999183 |
| 2026101204 |      33.002101 |         32.999708 |                           150000 |                           9 |                255.629195 | False           |         250000 |          32.999183 |

| contrast                                  |   mean_delta_hr |   simultaneous95_low_hr |   simultaneous95_high_hr |   wins |   losses |   ties |
|:------------------------------------------|----------------:|------------------------:|-------------------------:|-------:|---------:|-------:|
| refined ILS minus base ILS                |       -0.002401 |               -0.003672 |                -0.001129 |      5 |        0 |      0 |
| refined ILS minus matched-joint-budget GA |       -0.002208 |               -0.004953 |                 0.000537 |      4 |        1 |      0 |

A complete tested-neighborhood scan is a local certificate under those four neighborhoods and tolerance only. An incomplete budget-capped scan is not a certificate. Refinement is not part of base stochastic ILS and must be named and charged separately. The refined-versus-base gain is an incremental additional-work result, not an equal-budget causal advantage over simply continuing stochastic ILS. That latter five-seed intervention was not separately tested; the matched-total-budget GA comparison answers a different question.

## Simplicity and Presentation

ILS avoids population size, crossover and parent-selection settings. Original ILS nevertheless requires neighborhood set/weights, acceptance tolerance, stagnation unit/threshold, perturbation strengths/cycle, restart reference, initialization, archive, budget/safety cap and optional refinement policy. Single-swap removes neighborhood-mixture choices but retains perturbation and stopping settings. No-perturb is genuinely simpler but may repeatedly exhaust its finite accessible neighborhood before equal distinct work, and is not assumed equivalent because an interval crosses zero.

The parameter matrix provides adequate conditional study of the requested factors; it does not prove a universal ILS optimum. Main-paper Scope A remains the cleanest defensible presentation: diagnostic optimizer-family check with fixed original settings, matched budgets, inheritance and limitations. This new prospective diagnostic calibration can receive full supplemental treatment, but cannot be described as independently validated paper-method replacement. Scope B is feasible as a clearly postvalidation development appendix, not an authorized formal method promotion.
