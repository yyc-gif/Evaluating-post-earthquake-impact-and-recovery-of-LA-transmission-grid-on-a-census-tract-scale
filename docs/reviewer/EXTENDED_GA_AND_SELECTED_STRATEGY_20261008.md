# Extended GA search and selected-policy evidence

Formal strategies and original scientific outputs are not replaced. New numerical results are confined to this explicitly authorized optimization/evaluation diagnostic. The manuscript display set is six scheduled policies (Degree, Betweenness, Impact, Hospital, Vulnerability-first and fixed Random), with Unconstrained as the idealized reference. Centrality/Closeness original experiments remain intact. The protected July reference is unchanged.

## Objective and incumbent interpretation

Let m_i = sum_r P_r W_ri, F_bi(t)=I[f_bi(t)>=0.5], C_bi(t) indicate connection to an active Core source, and e_bi=f_bi F_bi C_bi. The existing objective is

$$J(\pi)=\frac{1}{64}\sum_{b=1}^{64}\frac{\sum_i m_i\int_0^{H_{plan}}[1-e_{bi}^\pi(t)]dt}{\sum_i m_i},\qquad \text{fitness}(\pi)=-J(\pi).$$

Impact-first is one of seven deterministic incumbents, not the fitness function. Each chromosome is a full permutation over the 92 stations, giving 92! possible orders. The seven fixed sequences enter generation zero; the best incumbent initializes an independent archive. Only `scored[idx] > archive_score` replaces it. Thus the original five coincident archives show no strict improvement within that budget, not independent stochastic rediscovery of Impact-first. All original crossover/mutation/tournament operations and random-number streams are preserved. Exact baseline history parity is verified; checkpoint/resume parity is also tested. Parallel processes execute independent seeds only.

H_plan = 2855.254013110100 h. An order-independent list-scheduling bound of 134.332550 h is below 480 h in every planning sample. Every intact component contains a Core source; consequently loss is zero afterward. The objective ranking is therefore identical at 480 h and H_plan for every permutation on these planning samples. Numerical checks of the earlier 25 generated candidates differ by less than 3e-12 h; the optimization objective itself is not changed. The calculation and proof are in `audit_planning_horizon_20261008.py` and `PLANNING_HORIZON_AUDIT.json`.

## Completed budgets

The earlier study contains five original-budget replays and twenty population-100, 250-generation restarts. This round adds 60 runs:

| population | generations | seeds | strict_improvements | lowest_planning_loss_hr | unique_candidates_sum |
|---|---|---|---|---|---|
| 100.000000 | 500.000000 | 20.000000 | 20.000000 | 33.082764 | 530573.000000 |
| 100.000000 | 1000.000000 | 20.000000 | 20.000000 | 33.043518 | 875044.000000 |
| 100.000000 | 2000.000000 | 5.000000 | 5.000000 | 33.038132 | 419843.000000 |
| 250.000000 | 500.000000 | 5.000000 | 1.000000 | 33.125886 | 499801.000000 |
| 500.000000 | 500.000000 | 5.000000 | 0.000000 | 33.578303 | 1045799.000000 |
| 500.000000 | 1000.000000 | 5.000000 | 0.000000 | 33.578303 | 2088837.000000 |

Unique-candidate sums count a permutation separately if it occurs in multiple runs; cross-run memoization and per-run caching avoid redundant exact scores. Run timings are wall-clock intervals and parallel-worker runtimes are not added as elapsed study time. The population-500, 500-generation seed-42 timing covers only its resumed segment after generation 200; its earlier segment was not separately timed, so no complete-run runtime or speedup claim is made for that run. Each run records candidate permutations, objective values, first generation, archives, best generated non-incumbent, sequence identity and all 64 realization differences. Exact ties exclude all deterministic sequences; cumulative near-tie thresholds are 1e-6, 1e-4, 1e-3 and 1e-2 h. Full details are in `SEARCH_SUMMARY.csv` and `p*_g*_s*/RUN.json`, `HISTORY.csv`, `CANDIDATES.npz`, and `PLANNING_DIFFERENCES.csv`.

Lowest completed planning loss: **33.038131743 h**, versus Impact-first **33.578302560 h**; improvement **0.540170817 h (1.608690%)**. Configuration: population 100, generations 2000, seed 46. The retained order displaces 86 stations, has rank correlation 0.722223 and top-ten overlap 2/10 relative to Impact-first. Improvement under some budgets does not imply improvement under every larger population: the archive is preserved, but the original GA does not force it into each offspring generation. Neither finite search nor these metrics certify a global optimum.

## Independent exploratory evaluation

Two distinct orders were selected solely by lowest planning loss and identified before any evaluation, in `independent_evaluation/CANDIDATE_SELECTION.json`. They use the original separate 1,000 2pc50/C57_D1 physical realizations, existing exact scheduling, source gate, mapping and 480-h event integration. Three Impact-first replay samples reproduce existing formal metrics within 1e-8. No evaluation score was used to select or reselect the two orders.

| candidate | reference | metric | mean_change | median_change | p05 | p95 |
|---|---|---|---|---|---|---|
| ga-exploratory-01 | impact-first | All-tract service loss (h) | -0.466060 | -0.359184 | -1.487492 | 0.197630 |
| ga-exploratory-01 | impact-first | Hospital-tract service loss (h) | -0.322944 | -0.212792 | -1.423854 | 0.341058 |
| ga-exploratory-01 | impact-first | Population-weighted Gini | 0.007626 | 0.006225 | -0.004937 | 0.025371 |
| ga-exploratory-01 | impact-first | High-low vulnerability service-loss gap (h) | 0.236719 | 0.239708 | -0.550425 | 1.036950 |
| ga-exploratory-01 | impact-first | Q4 tract service loss (h) | -0.627512 | -0.499301 | -1.774240 | 0.040993 |
| ga-exploratory-01 | hospital-first | All-tract service loss (h) | -1.178838 | -1.076242 | -2.297828 | -0.517827 |
| ga-exploratory-01 | hospital-first | Hospital-tract service loss (h) | -0.630305 | -0.475005 | -1.778883 | 0.021485 |
| ga-exploratory-01 | hospital-first | Population-weighted Gini | 0.006764 | 0.005425 | -0.010663 | 0.029043 |
| ga-exploratory-01 | hospital-first | High-low vulnerability service-loss gap (h) | 0.197726 | 0.264002 | -0.798753 | 1.037013 |
| ga-exploratory-01 | hospital-first | Q4 tract service loss (h) | -1.512673 | -1.463984 | -2.667238 | -0.613135 |
| ga-exploratory-02 | impact-first | All-tract service loss (h) | -0.491469 | -0.386260 | -1.502763 | 0.104774 |
| ga-exploratory-02 | impact-first | Hospital-tract service loss (h) | -0.253909 | -0.137134 | -1.300677 | 0.379027 |
| ga-exploratory-02 | impact-first | Population-weighted Gini | 0.007572 | 0.005950 | -0.004073 | 0.025580 |
| ga-exploratory-02 | impact-first | High-low vulnerability service-loss gap (h) | 0.245194 | 0.248101 | -0.532498 | 1.058667 |
| ga-exploratory-02 | impact-first | Q4 tract service loss (h) | -0.685504 | -0.552699 | -1.811556 | -0.059505 |
| ga-exploratory-02 | hospital-first | All-tract service loss (h) | -1.204248 | -1.095721 | -2.293748 | -0.548831 |
| ga-exploratory-02 | hospital-first | Hospital-tract service loss (h) | -0.561270 | -0.419274 | -1.684372 | 0.066806 |
| ga-exploratory-02 | hospital-first | Population-weighted Gini | 0.006710 | 0.005306 | -0.010801 | 0.029167 |
| ga-exploratory-02 | hospital-first | High-low vulnerability service-loss gap (h) | 0.206201 | 0.272911 | -0.786361 | 0.990654 |
| ga-exploratory-02 | hospital-first | Q4 tract service loss (h) | -1.570665 | -1.493682 | -2.748779 | -0.674882 |

Changes are candidate less named reference on the same physical sample; p05/p95 are realization-difference ranges, not confidence intervals. Planning and evaluation samples are separate. Quartile, signed/absolute group difference, population-weighted Gini, hospital-linked, T80, component and logistics results remain available in the new summaries. Event arrays and task execution are retained by batch. These results assess transfer of planning improvement; they do not promote a new formal strategy.

## Landscape and station interpretation

The planning family includes samples with all stations damaged. A joint signature containing such a sample cannot collapse two different full permutations merely through DS>0 filtering. Near-equivalent objective values are not proof of identical effective task orders or a broad exact plateau. The original 100-generation result was a finite-budget limitation, as improvements at longer budgets demonstrate. No global-optimality claim is made.

`STATION_PRIORITY_AND_EXPLORATORY_EXECUTION.csv` distinguishes fixed full rank from damage-filtered task dispatch and mean repair completion. It links saved degree/betweenness, population/Q4/hospital dependencies and directed travel. Differences are descriptive strategy outcomes, not a causal station-by-station early-repair benefit. Actual 92-station electrical MW capacity and power-flow outcomes are not available; S8 remains the restricted SCE planning-ceiling sensitivity.

## Reference purposes and new mechanism evidence

Hospital-first is the predeclared critical-service reference. Impact-first is the population-loss-oriented incumbent. Random is one fixed random order. Unconstrained removes crew competition and is not an operational policy. Degree and Betweenness are compared with both Hospital and Impact; complete absolute outcomes and named-reference effects cover every existing selected-policy scenario.

The new network/station/community candidate reads saved f/F/e trajectories, not recalculated dynamics. Under 2pc50/C57_D1, Degree-first relative to Hospital-first changes source-path loss by -1.646692 h and all-tract loss by +1.401244 h: substation-damage loss increases 2.944702 h and threshold loss 0.103234 h. The components account for the opposite directions. This is modeled service loss, not delivered MW. The Degree/Betweenness maps and histograms read existing station metrics; July's top-ten map used network lambda2 impact instead.

S4 remains static node-removal criticality plus dynamic functional LCC structure; S7 instead measures Core-source connectivity/redundancy. S6 is dependency and service-model assumptions: mapping cutoff, source-connectivity gate and functionality threshold, with the public-record mapping agreement shown in Fig2.

## Preservation boundary

Original physical samples, mapping, source gate, 64 planning inputs, formal sequences, original schedules/evaluation trajectories, Stage7 membership, equity and capacity results remain unchanged. The new exploratory schedules and evaluations are in a separate namespace and were explicitly requested by the author. Only presentation files/captions/indexes, diagnostic results and validation identities are updated. Author selection of a replacement formal policy is still pending.
