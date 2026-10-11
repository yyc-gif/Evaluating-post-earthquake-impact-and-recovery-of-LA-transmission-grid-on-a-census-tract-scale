# GA-ILS Method Choice Decision

## Formal Method Remains Frozen

Retain the already validated GA configuration and sequence. This is a preservation decision, not an assertion that it beats every newly calibrated algorithm. No new candidate was scored on the completed 2,000-realization validation cohort.

## Matched Comparisons

| contrast                          |   mean_delta_hr |   simultaneous95_low_hr |   simultaneous95_high_hr |   wins |   losses |   ties |   paired_mean_wall_ratio |
|:----------------------------------|----------------:|------------------------:|-------------------------:|-------:|---------:|-------:|-------------------------:|
| ils_mix minus ga_elite1           |       -0.000039 |               -0.001853 |                 0.001775 |      9 |       11 |      0 |                 0.670330 |
| ils_cold minus ga_cold            |       -0.001069 |               -0.003039 |                 0.000900 |     11 |        9 |      0 |                 0.673621 |
| ils_mix minus ils_cold            |        0.000078 |               -0.001726 |                 0.001881 |      9 |       11 |      0 |                 0.998614 |
| ga_elite1 minus ga_cold           |       -0.000953 |               -0.002664 |                 0.000759 |     12 |        8 |      0 |                 1.004518 |
| ils_swap minus ga_elite1          |       -0.001801 |               -0.002726 |                -0.000876 |     17 |        3 |      0 |                 0.669894 |
| ils_swap_stag2000 minus ga_elite1 |       -0.002227 |               -0.003312 |                -0.001141 |     20 |        0 |      0 |                 0.668437 |

The four original method/information contrasts form the prospectively declared family. The two reduced-neighborhood ILS-versus-GA contrasts are an additional retrospective exploratory family on the already planned 20 paired seeds, not a newly preregistered confirmatory result. They require no additional search runs and are not independent physical validation.

Shared warm comparisons give both methods the same optimized prior; cold comparisons exclude it and prior-derived neighbors. The initial candidate generation operations differ and are documented, so cold/warm effects include their composition and RNG changes. Equal distinct budgets do not imply equal attempted-query work, CPU or wall time. Local measured wall time includes diagnostic observation: GA records per-generation diversity/history, whereas ILS has no evolving-population history. Objective scoring time is retained separately; nonobjective time cannot be attributed wholly to intrinsic algorithm overhead. Attempted-query reduction is directly measured, but the wall ratio is an instrumented implementation comparison, not an instrumentation-free universal speedup.

Historical 100k mixed-ILS minus GA mean +0.001298265 h, simultaneous interval [-0.00013347, 0.00273000]; historical 500k -0.001101224 h, interval [-0.002591758, 0.000389309], with 7/10 wins. These are conditional empirical comparisons, not universal superiority. Tested simulated annealing and LNS configurations performed worse but do not invalidate all non-GA optimizers. Completed scheduling/actionable-delay evidence supersedes older notes saying LNS was untested.

New single-swap versus mixed: mean -0.001762417 h; median -0.003275649; paired SD 0.003297369; simultaneous 95% interval [-0.004067700, +0.000542866]; wins/losses/ties 13/7/0 (n=20). Base, refinement and continued-GA costs remain separate. The five-seed joint-budget table is MULTISEED_REFINEMENT_AND_MATCHED_GA.csv. Best-found quality, average quality, variability, duplicate overhead and per-state influence are different questions; a low selected minimum cannot settle method choice.

## Paper Scope

The stronger reduced-neighborhood findings must not be hidden behind the older unresolved mixed-ILS comparison. Single-swap ILS versus GA gives mean -0.001801402 h; median -0.001887167; paired SD 0.001699928; simultaneous 95% interval [-0.002726391, -0.000876414]; wins/losses/ties 17/3/0 (n=20); swap with stagnation 2000 versus GA gives mean -0.002226523 h; median -0.001496724; paired SD 0.001995669; simultaneous 95% interval [-0.003312434, -0.001140612]; wins/losses/ties 20/0/0 (n=20). These direct GA comparisons were added retrospectively on already planned cases and belong to their separate two-contrast exploratory family. Within the prospective nine-contrast ILS family, the swap/2000 package versus original mixed/800 gives mean -0.002187538 h; median -0.001880154; paired SD 0.002682022; simultaneous 95% interval [-0.004062614, -0.000312461]; wins/losses/ties 16/4/0 (n=20). The focused operator-by-stagnation interaction is mean +0.000429723 h; median +0.001178066; paired SD 0.003908677; simultaneous 95% interval [-0.001399594, +0.002259040]; wins/losses/ties 8/12/0 (n=20); an improved package is not proof of interaction synergy or a uniquely optimal threshold.

Recommend **Scope A**, diagnostic alternative in the main paper, with the complete calibration sensitivity preserved in Supplementary Information. Original ILS's several neighborhood/restart/refinement settings are not demonstrably trivial just because only one current sequence is stored. A single-swap implementation is a credible reduced-neighborhood diagnostic under the studied model, not a validated new policy. Scope B is supported as a calibrated conditional development comparison in Supplementary Information; its placement as a substantive main-paper extension requires an explicit author decision. The fresh twenty-seed algorithmic confirmation was completed here. Claims of physical generalization for the new settings would require appropriate independent evidence, not reuse of the old validation cohort as untouched confirmation.

The completed parameter evidence warrants substantive supplemental presentation of reduced-neighborhood ILS rather than only a weak untuned baseline. The main text should acknowledge that it achieved lower conditional development means and fewer attempted lookups. The simpler base method omits population/crossover/tournament choices and neighborhood-mixture weights, but still requires a stagnation threshold, perturbation cycle, restart reference, initializer, archive and budget. Scope A describes its paper role, not absence of a calibration audit; Scope B remains scientifically supportable as a clearly bounded postvalidation methods appendix, not independently validated formal-policy replacement.

## Validation and Physical-Sample Sensitivity

Previously frozen GA-minus-Impact validation mean -0.501901635445 h, 95% interval [-0.524975128718, -0.479472230142]; refined-ILS-minus-frozen-GA mean -0.024549091909 h while ILS worsened 69.6% of realizations. These aggregates were provided with the task; this study did not access their realization outcomes. They describe the frozen sequences, not parameter selection, calibration superiority, capacity or universal robustness.

Historical refined planning advantage is influential-state sensitive: 14/64 improvements and 50 worsening, with omission of realization 15 reversing the mean difference to +0.030758169262 h. Internal 48/16 crossfit produced 16/20 ranking reversals; folds already belonged to the development collection. New candidate production and leave-one-out evidence are retained, not used to redefine the mean objective or retroactively choose a different physical loss.

## Independently Checked New Candidates

The eight lowest verified development objectives are shown below. Negative deltas favor the diagnostic sequence over the frozen GA. Complete 92-station orders, hashes and origins are in IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json; this selected-minimum table is not an unbiased optimizer comparison. Omission diagnostics remove planning states only from the comparison, not from the authoritative objective or search.

| SHA256 prefix   |   Mean J (h) |   Delta vs frozen GA (h) |   Improved states |   Worsened states |   LOO reversals |   Omit 15 delta (h) |   Omit best five delta (h) |
|:----------------|-------------:|-------------------------:|------------------:|------------------:|----------------:|--------------------:|---------------------------:|
| 288c37e1219d    |    32.995522 |                -0.002318 |                14 |                50 |               5 |            0.030441 |                   0.061462 |
| df675f40dcbe    |    32.995552 |                -0.002289 |                15 |                49 |               5 |            0.030384 |                   0.061494 |
| 72cbb51b3027    |    32.995571 |                -0.002270 |                13 |                51 |               5 |            0.029994 |                   0.060327 |
| f7649b13a658    |    32.995689 |                -0.002152 |                15 |                49 |               5 |            0.030517 |                   0.061614 |
| 6488c47f53a4    |    32.996004 |                -0.001837 |                15 |                49 |               5 |            0.030822 |                   0.061790 |
| 8193ed7cb3a1    |    32.996038 |                -0.001803 |                15 |                49 |               5 |            0.030325 |                   0.061059 |
| 55fbac042427    |    32.996092 |                -0.001749 |                15 |                49 |               5 |            0.030870 |                   0.062058 |
| 9ffc5cca4082    |    32.996675 |                -0.001166 |                14 |                50 |               8 |            0.031584 |                   0.063039 |

Differences of 0.001 normalized service-loss hour correspond to 3.6 seconds of equivalent population-weighted deficit duration. They are not 0.001 person-hours, delivered electrical energy, or a promise that every household is restored sooner.
