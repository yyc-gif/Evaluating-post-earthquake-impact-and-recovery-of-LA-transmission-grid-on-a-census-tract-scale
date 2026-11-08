# GA versus Impact-first: Paired Source-Connectivity Mechanism

## Result

On the exact saved, paired 2,000-realization 2pc50/C57_D1 cohort, the frozen GA final-method candidate changed total modeled burden by -0.501902 h versus Impact-first (paired bootstrap 95% CI -0.524975 to -0.479472 h).
The component changes were self +0.203762 h, threshold +0.007820 h, and source path -0.713484 h. These add to the total within 9.99e-16 h.
The paired source-path difference decomposes exactly into -12.943337 h from each repaired station's own source-loss state change and +12.229853 h from other already-functional stations whose source connection changed at completion events. Their sum is -0.713484 h.
On the saved 1-hour descriptive curve, the mean paired source-path deficit difference reaches -0.03233 at hour 17 and is effectively zero by 72 h; the 480-hour effect above is integrated exactly from the original event times, not from this hourly display.

## Paired Effects

Effect is GA minus Impact-first; negative values favor GA. All are population-weighted normalized service-deficit hours over 0-480 h.

| Component | Mean (h) | Paired MCSE (h) | Paired bootstrap 95% interval (h) |
|---|---:|---:|---:|
| Self functionality | +0.203762 | 0.001776 | [+0.200334, +0.207271] |
| Functionality threshold | +0.007820 | 0.000115 | [+0.007598, +0.008049] |
| Source path | -0.713484 | 0.011742 | [-0.736862, -0.690814] |
| Total | -0.501902 | 0.011605 | [-0.524975, -0.479472] |

| Strategy | Self (h) | Threshold (h) | Source path (h) | Total (h) |
|---|---:|---:|---:|---:|
| impact-first | 28.456564 | 0.933485 | 4.132601 | 33.522650 |
| ga-final-method-candidate | 28.660326 | 0.941304 | 3.419117 | 33.020748 |

At each completion event the source-path loss state is `f_s * F_s * (1 - C_s)`: `f` is modeled station functionality, `F` is the 0.5 functionality gate, and `C` is connection to a frozen Core-source proxy. The direct event term is the changed mapped source loss on stations repaired at that event; the external term is the changed source loss on all other stations. Each is integrated over remaining time to 480 h and normalized by total mapped population.


## What Produces the Source-Path Improvement?

The GA-minus-Impact source-path difference is **-12.943337 h** at the repaired stations' own mapped source-loss states, but **+12.229853 h** across other stations whose source connection changes at completion events. The latter offsets 94.5% of the own-station source-path benefit, leaving the net -0.713484 h gain. So the result is not produced by GA unlocking more external dependency overall.
Instead, the fixed GA order moves selected stations earlier while delaying others. Across 183,387 paired damaged-station repairs, its mean completion shift was -0.0951 h per repair (55.9% earlier; 34.2% later); crew assignments differed in 99.2% of paired station-repair cases. The matched repair durations were identical; average task travel changed -0.0624 h per repair.

| External-unlock quantity (GA minus Impact-first) | Mean per realization | Paired bootstrap 95% interval |
|---|---:|---:|
| Completion events with >=1 other-station unlock | -0.7580 | [-0.8205, -0.6935] |
| Other-station connectivity transitions | -1.5825 | [-1.6975, -1.4700] |
| M1 mapped person-equivalent dependency mass | -254040.0779 | [-265953.9967, -242448.3338] |

External-unlock mass is the sum of population-weighted M1 station dependencies newly connected at each completion, averaged across realizations. It is not a count of distinct residents; tract population is fractionally mapped across substations.

Event-trigger contrasts below are GA minus Impact-first in the other-station source-loss integral; negative means that event's external loss contribution is lower under GA. Completion is the mean scheduled completion time for that station across cases where it required repair.

| Completion trigger | Source-register label / role | External contribution (h) | Mean repair rank GA vs Impact | Mean completion GA vs Impact (h) |
|---|---|---:|---:|---:|
| 301614 | station label unavailable in source register (not in source-only register) | -1.464885 | 41.9 vs 79.7 | -18.45 |
| 308581 | STATION Q (HARBOR) (Core, in_basin_generation_proxy) | -1.435771 | 35.9 vs 39.9 | -0.03 |
| 307373 | HAYNES (Core, in_basin_generation_proxy) | -1.263166 | 73.8 vs 82.7 | -5.86 |
| 308206 | NICHOLS CANYON (Transit, transit_hub_not_source) | -1.046869 | 14.0 vs 32.9 | -0.00 |
| 306768 | station label unavailable in source register (not in source-only register) | -0.641129 | 16.9 vs 81.7 | -19.83 |
| 306844 | LA FRESA (Transit, transit_hub_not_source) | -0.612306 | 23.9 vs 55.8 | +0.12 |
| 310504 | station label unavailable in source register (not in source-only register) | -0.409666 | 12.0 vs 22.0 | -0.34 |
| 303371 | station label unavailable in source register (not in source-only register) | -0.340566 | 52.8 vs 23.9 | -0.23 |

### Downstream stations newly connected at those completion events

These rows identify the other station whose binary source-connection state changed at a completion. Contributions are integrated step-trajectory accounting, not causal task effects.

| Trigger completion | Newly connected station | Source role | GA−Impact contribution (h) | Unlock transitions per 2,000 cases (GA / Impact) |
|---|---|---|---:|---:|
| 301614 | 310504 (label unavailable) | not in source-only register | -0.284054 | 121 / 53 |
| 301614 | 306369 (label unavailable) | not in source-only register | -0.107615 | 51 / 19 |
| 308581 | 310179 (WILMINGTON (STATION C)) | Transit, transit_hub_not_source | -0.125983 | 151 / 72 |
| 308581 | 303169 (LIGHTPIPE) | Transit, transit_hub_not_source | -0.113181 | 40 / 21 |
| 307373 | 304073 (STATION B (CENTURY)) | Transit, transit_hub_not_source | -0.172816 | 65 / 35 |
| 307373 | 309042 (label unavailable) | not in source-only register | -0.074925 | 19 / 6 |
| 308206 | 303899 (label unavailable) | not in source-only register | -0.636637 | 181 / 75 |
| 308206 | 303099 (STATION D (FAIRFAX)) | Transit, transit_hub_not_source | -0.282868 | 99 / 44 |
| 306768 | 308206 (NICHOLS CANYON) | Transit, transit_hub_not_source | -0.283722 | 419 / 330 |
| 306768 | 303899 (label unavailable) | not in source-only register | -0.242388 | 202 / 163 |
| 306844 | 308786 (LA CIENEGA) | Transit, transit_hub_not_source | -0.091123 | 134 / 29 |
| 306844 | 301105 (STATION K (OLYMPIC)) | Transit, transit_hub_not_source | -0.087604 | 41 / 17 |
| 310504 | 308907 (NEWMARK) | Transit, transit_hub_not_source | -0.075650 | 34 / 8 |
| 310504 | 300648 (label unavailable) | not in source-only register | -0.063370 | 13 / 1 |
| 303371 | 300558 (label unavailable) | not in source-only register | -0.131938 | 100 / 81 |
| 303371 | 300648 (label unavailable) | not in source-only register | -0.036688 | 30 / 23 |

### Own-station source-loss changes on repaired stations

Negative values mean lower own-station source-path deficit under GA. This table separates direct station restoration from downstream source reconnection.

| Repaired station | Source role | GA−Impact own-station contribution (h) | Mean completion GA vs Impact (h) | GA completes earlier |
|---|---|---:|---:|---:|
| 305885 (305885) | not in source-only register | -1.174408 | +11.04 | 0.0% |
| 306694 (306694) | not in source-only register | -1.013779 | +12.69 | 0.0% |
| 301156 (301156) | not in source-only register | -0.983641 | +10.27 | 0.0% |
| 303899 (303899) | not in source-only register | -0.879818 | +0.10 | 0.0% |
| 304040 (304040) | not in source-only register | -0.832154 | +12.09 | 0.0% |
| 309663 (309663) | not in source-only register | -0.781710 | +8.08 | 0.0% |

Largest offsetting event groups (positive means higher external source-path deficit under GA):

| Completion trigger | External contribution (h) | GA unlock events / Impact unlock events |
|---|---:|---:|
| 301105 | +3.776762 | 1029 / 1074 |
| 310179 | +1.487345 | 491 / 604 |
| 301100 | +1.453145 | 77 / 185 |
| 303099 | +1.113430 | 453 / 481 |
| 306060 | +1.090048 | 185 / 278 |

The full station-level rank, crew, travel, arrival, completion, realized-duration and own-station contribution comparison is in `GA_IMPACT_STATION_EVENT_ATTRIBUTION.json`. Negative rank/completion differences indicate GA earlier than Impact-first.
The source-path component favored GA in 1,948/2,000 cases; it was worse in 52. Total burden favored GA in 1,810/2,000 and favored Impact-first in 190.

## Provenance and Reconciliation

- Physical cohort: 2000 paired unique physical hashes; all 2,000 cases passed embedded payload hashes.
- Independent sample identity QA: PASS; 2,000 registered seed records, 2,000 unique draws, zero overlap with 1,064 original hashes; bitwise sampler checks at r=0, 1, 1000, 1999.
- GA sequence SHA-256: `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`; Impact-first sequence SHA-256: `d75ee1dc0fed0671b40d7f539d1e456ea42402105554cb1eb41ab3ec41bc9168`.
- GA candidate provenance: seed 43, source commit `73ef343f21e998eb9c9ccf7797d1aa0119d15c04`, candidate planning loss 32.997841 h, selection uses evaluation = `False`; source `results/diagnostics/ga_optimization_20261009/budget_extension/operator_swap_s43/RUN.json` (SHA-256 `c1787c887719bc92b9ae170fb0ff393d3d7abc6c096a90937fd7944388ae6a70`).
- LFS archive SHA-256: `74d83734549c83b7bcb57270a07db3ab4c696d4384c5a851461184cfcb28947d`; validation freeze: `45d157c0a3b9460d7c29e389b649afef0f0e6bc568bfba8eb773f9b5b974ae15`.
- The Oct 9 sequence JSON is the exact `ga-final-method-candidate` sequence in the completed Oct 10 independent validation manifest. The execution accounting records one completed 2,000-sample run, not merely a protocol plan.
- The latest PR comment's approximate (-0.533 h total; -0.821, +0.277, +0.011 h components) does not match the exact paired component table in this archive. The active checkout's current FigS04 is network recovery; its GA diagnostic is FigS05 and describes a different 1,000-realization exploratory comparison. No artifact-level proof was found tying the comment's tuple to the exact frozen 2,000-case GA sequence.

## Interpretation Limits

The event split is an exact decomposition of saved completion-step source-loss curves. It quantifies own-station versus other-station source-path changes at each completion, but it is not a causal intervention on an individual bridge station: event order, crew assignment and travel jointly determine the state at each repair. The modeled source gate is a binary Core-source proxy, not power flow or observed service.
The independent 2,000-realization cohort is conditional Monte Carlo validation of the frozen model, not observed-outage validation. No new cohort, repair schedule, or GA optimization was generated here; four archived samples were independently regenerated solely to verify their registered identity.

## Reproduction

Run the script with the archived materialized LFS object and the original input files:

```powershell
python src/la_grid/diagnostics/ga_impact_event_mechanism_20261106.py `
  --archive results/diagnostics/independent_validation_ready_20261010/authorized_validation/FIXED_2000_FULL_ARCHIVE.zip `
  --validation-dir results/diagnostics/independent_validation_ready_20261010/authorized_validation `
  --selected-sequence results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json `
  --mapping Data/JULY_UTILITY_CONSTRAINED_92.csv `
  --graph Data/substation_graph_CEC_edges_expanded.csv `
  --sources Data/source_nodes_core_expanded.csv `
  --output results/research_contribution1_20261105/GA_IMPACT_EVENT_FOLLOWUP_20261106
```
