# Journal-neutral figure captions

## Figure 1. Analytical framework

Workflow from seismic damage through source-gated station functionality and tract dependencies to community recovery. Fixed rules or GA planning produce a station order for the same finite-crew scheduler. Stage 4 shows an Impact-first priority example and five of 57 crew histories from 2pc50/C57_D1 evaluation realization 0. Map numbers are full station priority ranks; damaged tasks (DS > 0) use saved directed travel and damage-state-specific repair intervals. At repair completion the crew is released and raw station functionality is restored. The recorded state inset shows why source connectivity and tract service need not increase immediately (all states 0-1). Map shading is log population. Unconstrained is a separate parallel-repair reference. T80 is time to 80% modeled service availability; service loss integrates its deficit. Strategy outcomes appear in Figure 5. PGA denotes peak ground acceleration; DS, damage state; GA, genetic algorithm.

## Figure 2. Transmission network and tract dependencies

Transmission network, tract-substation mapping, and comparison of candidate tract assignments with public SCE assignments. Assignment agreement does not validate feeder boundaries or recovery outcomes. CEC is the California Energy Commission; SCE, Southern California Edison; LADWP, the Los Angeles Department of Water and Power.

## Figure 3. Damage and Unconstrained recovery

A summarizes station-level mean damage states: boxes span the interquartile range, lines mark medians, and whiskers end at observations within the 5th-95th station percentiles, with outliers omitted. B shows tract initial-service distributions; C decomposes population-weighted Unconstrained deficit. D distributes system T80 across 1,000 2pc50 realizations; E maps tract-level mean T80. T80 is time to 80% modeled service availability. DS denotes damage state.

## Figure 4. Network-dependent source connectivity during recovery

For 2pc50. (A) Recovery of population-dependency-weighted joint functionality and source connection through the full network (solid) or a fixed precomputed path (dashed). (B) Their difference shows restoration-sequence-dependent alternative-route support. (C) Station source access conditional on station functionality; (D) additional conditional reliability beyond the fixed path. Triangles mark Core sources. A/B are dynamic recovery comparisons; C/D are fragility-based station diagnostics. These topological measures are not delivered electricity. Core sources are the prescribed source substations in the retained graph.

## Figure 5. Restoration-policy performance under 2pc50

For 2pc50/C57_D1. Recovery trajectories and outcomes for six scheduled strategies and the Unconstrained reference. A shows population-weighted service availability. B reports mean overall, Q4 and hospital-linked service loss and population T80; whiskers show 5th-95th realization ranges. T80 denotes time to 80% modeled service availability. Q4 is the highest frozen social-vulnerability quartile; hospital-linked denotes tract association, not hospital electricity demand.

## Figure 6. Vulnerability-targeted recovery and distributional effects

For 2pc50/C57_D1. A/B show overall and quartile service loss. C compares Vulnerability-first with Hospital-first, Impact-first, and Degree-first for overall loss, Q4 loss, signed Q4-Q1 gap, mean within-realization absolute |Q4-Q1| gap, and hospital-linked loss; D shows Gini change and E maps tract-level mean changes. B-D whiskers show 5th-95th realization ranges; negative map values favor Vulnerability-first. Q1/Q4 are the lowest/highest frozen social-vulnerability quartiles. Gini summarizes tract service-loss inequality.

## Figure 7. Resource dependence of policy contrasts under 2pc50

For 2pc50; resource multipliers are relative to C57_D1. Vulnerability-first minus each reference strategy across crew-availability and repair-duration scenarios. Whiskers are 95% bootstrap confidence intervals for mean effects, not realization ranges; Degree-first hospital-linked comparisons show means only. The third row is the change in mean within-realization absolute Q4-Q1 service-loss gap; other rows are deficit changes. Negative values favor Vulnerability-first for the named outcome. Q1/Q4 are the lowest/highest frozen social-vulnerability quartiles.

## Figure 8. Community recovery types and social vulnerability

For 2pc50/C57_D1. A shows six feature distributions; B shows standardized means for all seven fitted variables, grouped by research question; C shows three-class geography. D maps continuous SOVI and five-policy mean cumulative service deficit; outlines in C and D identify tracts that are in Federal Emergency Management Agency (FEMA) National Risk Index (NRI) v1.19 SOVI quartile Q4 (the highest social-vulnerability quartile) and have five-policy mean total service deficit at or above 38.38135467381475 equivalent full-service-deficit hours over 0-480 h (the positive-population cohort 75th percentile). Population is fitted as log1p population; profile cells are ordinary cohort z-score means, not weighted distances. ECDF markers locate class medians. This policy-conditioned screen is not a significance test or intervention-priority score. HHI is the Herfindahl-Hirschman index of tract dependency-weight concentration; RQ denotes research question. SOVI is the social-vulnerability score. The five-policy mean includes Impact-, Hospital-, Degree-, Betweenness-, and Vulnerability-first, excluding Random.

## Supplementary Figure S1. Damage and initial service

Station damage severity and corresponding initial modeled tract-service availability. Availability is a network proxy, not delivered electric power or observed customer outages.

## Supplementary Figure S2. Restoration logistics

Crew bases, station tasks, and task-to-task travel times used in restoration scheduling. These are pre-event scheduling inputs, not post-earthquake traffic forecasts. LADWP is the Los Angeles Department of Water and Power; SCE, Southern California Edison.

## Supplementary Figure S3. Functional-network recovery

For 2pc50/C57_D1. Recovery of the largest connected-component fraction and mean degree within that component among functional substations. The curves describe network topology, not power flow or delivered electricity.

## Supplementary Figure S4. Genetic-algorithm diagnostics

For 2pc50/C57_D1. A/B summarize 20 GA runs using 64 optimization realizations and 100 repair orders per run. C/D evaluate the selected order on 2,000 held-out simulation realizations; D decomposes the mean GA-minus-Impact-first loss gap. Negative values indicate lower deficit under GA; a global optimum is not established. This evaluates generalization within the same model, not independent observed outages. Paired component differences reflect restoration timing and gating, not different physical damage samples. GA denotes genetic algorithm.

## Supplementary Figure S5. Dependency and service-gate sensitivity

For 2pc50/C57_D1. (A) Change in population-weighted normalized service deficit when the tract-substation mapping cutoff is relaxed from 3% to 0% or 1%. (B) Change when source connectivity is removed while the 0.50 functionality threshold is retained. (C) Change under 0.05 or 0.75 functionality thresholds, with source connectivity reevaluated. Points are means of paired differences across 1,000 frozen physical realizations; bars show empirical 5th-95th percentile ranges, not confidence intervals. No damage samples or repair schedules were regenerated.

## Supplementary Figure S6. Facility planning limits

For 2pc50/C57_D1. Provider planning loads, reported limits, and modeled service-loss changes under capacity ceilings. Post-earthquake load flow and complete electrical-capacity adequacy are not assessed. Panel B points show population-weighted mean increases from the modeled ceiling; bars span the paired 5th-95th realization percentiles. SCE denotes Southern California Edison.

## Supplementary Figure S7. Restoration-priority geography

Repair-priority geography for Hospital-first, Vulnerability-first, and Impact-first strategies. A marks hospital-linked tracts, B marks frozen Q4 tracts, and C shows population on a logarithmic color scale; ranks are full station priority positions, not realization-specific dispatch positions; outcome comparisons appear in Figures 5-7 and Supplementary Figure S8. Q4 is the highest frozen social-vulnerability quartile.

## Supplementary Figure S8. Outcomes under resource variation

For 2pc50; resource multipliers are relative to C57_D1. Absolute modeled service losses under crew-availability and repair-duration variations, reported separately for overall, Q4, mean within-realization absolute Q4-Q1 gap, and hospital-linked outcomes. Whiskers show the 5th-95th realization range. Q1/Q4 are the lowest/highest frozen social-vulnerability quartiles.

