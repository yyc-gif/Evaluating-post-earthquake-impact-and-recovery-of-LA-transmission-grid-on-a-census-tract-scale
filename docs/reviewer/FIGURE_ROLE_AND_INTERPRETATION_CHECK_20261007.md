# Main-figure roles and interpretation check

Review basis: `revision/reviewer-driven-core-rebuild-v2`, commit `61aec61df6d3a1896764326b18d90152a617ca71`. Local and remote HEAD were checked against this commit. All seven current native PDFs in `results/figure_review/Main/` were rendered and opened for this check; their text and current captions were compared with the saved result tables. This is an interpretation review, not author acceptance of the artwork or a new submission-layout certification.

Scope: review the co-author's proposed figure explanations and the grouped-bar suggestion for Figure 4B. No figure, caption authority, scientific code or numerical result is changed by this document. The English descriptions below are proposed replacement text for discussion.

## The central correction

The description must distinguish a benefit to the targeted group from a reduction in overall inequality. Under the reference 2pc50 condition, Vulnerability-first reduces Q4 service loss relative to Hospital-first and Impact-first, but increases both the mean within-realization absolute Q4–Q1 difference and population-weighted Gini relative to those references. Its aggregate effect changes direction with the reference policy.

Q1 and Q4 are social-vulnerability quartiles, not income quartiles. Neither the figures nor these metrics establish which neighborhoods are richest or poorest.

### Direct numerical check: 2pc50, reference crew availability, duration multiplier 1.00

The following are saved mean distributional effects, Vulnerability-first minus the named reference, over 1,000 realizations. Values are rounded for explanation; no new simulation, scheduling or uncertainty estimation is performed.

| Outcome | Relative to Hospital-first | Relative to Impact-first |
|---|---:|---:|
| Population-weighted service loss, all tracts (h) | −0.049 | +0.664 |
| Population-weighted Q4 service loss (h) | −1.595 | −0.710 |
| Population-weighted Q1 service loss (h) | +1.269 | +2.162 |
| Mean within-realization absolute Q4–Q1 service-loss difference (h) | +2.501 | +2.540 |
| Population-weighted Gini coefficient | +0.00499 | +0.00585 |
| Equal-weight mean service loss in hospital-linked tracts (h) | +0.572 | +0.880 |
| Population-weighted T80 (h) | +0.466 | +1.186 |

Sources: `Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PAIRWISE_EFFECTS.csv` and `results/vulnerability/EFFICIENCY_DISTRIBUTION_TRADEOFF_2PC50.csv`. The pairwise table supplies the effects; the three-policy summary independently confirms the aggregate, Q4, absolute-difference and Gini means.

The Gini means are 0.188530 for Impact-first, 0.189391 for Hospital-first and 0.194381 for Vulnerability-first. Consequently, “Vulnerability-first structurally reduces systemic inequality” reverses the result for both primary references. Higher Gini means a more unequal distribution of modeled tract service loss; it does not by itself establish an ethical judgment about a policy.

## Figure-by-figure corrections

### Figure 1 — Analytical framework

The proposed role is appropriate. Preserve the distinction between modeled service availability and electricity delivery. The framework connects substation damage, station functionality, threshold eligibility and source connectivity to tract dependency, then combines restoration logistics and priorities with community outcomes.

**Proposed description:**

Figure 1 links earthquake-induced substation damage to modeled tract service through station functionality, source connectivity and utility-compatible tract dependencies. Restoration priorities and crew-dispatch constraints determine the recovery sequence. Community outcomes include population-weighted service loss, hospital-linked tract service loss, vulnerability-group outcomes and spatial recovery patterns; resource and model-assumption checks examine the limits of these comparisons.

### Figure 2 — System representation, dependency and external mapping support

Panel C restricts candidate tract–substation assignments by utility compatibility. It does not impose an independently tested rule that all repair operations remain inside rigid administrative borders. Other or uncertain utility assignments use the general candidate pool.

Panel D compares assignments with public SCE substation records. It does not compare modeled service with actual electricity-use records. The 97.6% value is 329/337 tracts with at least one positive-weight assigned substation in the public-record comparison set. It is not a top-1 rate or overall recovery-model accuracy.

| Assignment comparison | Distance-based baseline | Utility-compatible mapping |
|---|---:|---:|
| At least one match among all positive-weight assignments | 320/337 = 95.0% | 329/337 = 97.6% |
| Highest-weight assigned substation matches | 296/337 = 87.8% | 302/337 = 89.6% |
| At least one match among the three highest-weight assignments | 317/337 = 94.1% | 324/337 = 96.1% |

The 337 comparison tracts and the earlier 342-tract crosswalk are different sets. Their denominators cannot be pooled. Agreement with these public records supports candidate assignment, not feeder boundaries, service-territory ground truth, electricity delivery or prediction of recovery.

**Proposed description:**

Figure 2 shows the physical transmission network and derived substation connection paths, followed by the utility areas used to constrain tract–substation assignments. The external comparison uses public SCE records for 337 comparable tracts. Utility-compatible assignments have greater agreement than the distance-based baseline under all three assignment tests, providing external support for the dependency representation without establishing feeder-level ground truth.

### Figure 3 — Hazard context, loss mechanisms and the unconstrained baseline

The 2pc50 label concerns ground-motion exceedance probability: 2% in 50 years. It does not mean a 2% probability of an earthquake causing mean station damage at or above DS3. See the [USGS explanation of probability of exceedance](https://www.usgs.gov/programs/earthquake-hazards/science/earthquake-hazards-201-technical-qa).

Panel A summarizes station mean damage states across saved realizations, with a 5th–95th range across stations. Panel B is a distribution of tract mean initial modeled availability, not a probability curve for a universal observed blackout. A claimed percentage of blacked-out tracts needs an explicit availability threshold and aggregation definition; “over 85%” should not be inferred from the curve without those definitions.

Panel C is the **Unconstrained** decomposition over 0–480 h. Its source-path shares are 4.4%, 8.8%, 15.1% and 11.4% for Long Beach, San Fernando, Northridge and 2pc50, respectively. Source connectivity can be lost when damaged or threshold-ineligible stations interrupt graph paths. The production source-gate implementation does not independently sample transmission-line failures, so this component must not be described as measured loss from severed upstream transmission lines.

Panel D's displayed median is 43.3 h, verified against the saved Unconstrained population T80 values (median 43.327397 h). This is time to 80% population-weighted modeled tract service, not restoration of 80% of physical grid functionality. Panel E shows the mean of realization-specific tract T80 values conditional on that tract reaching T80. Its spatial pattern cannot be attributed to topology alone: hazard exposure, fragility, repair durations, tract dependencies and source connectivity also enter the model. Historical cases and 2pc50 have different fragility parameterizations.

**Proposed description:**

Figure 3 establishes the hazard-to-service baseline before scheduling constraints are introduced. Station damage and initial tract availability differ across the four modeled scenarios. Under Unconstrained recovery, service loss arises from substation damage, the functionality threshold and source-path unavailability; population-weighted T80 and conditional tract T80 then reveal recovery-time variability across realizations and locations. In 2pc50 the population-weighted T80 median is 43.3 h, while spatial heterogeneity persists even without crew competition.

### Figure 4 — All-policy recovery and outcome comparisons

The current Panel A is modeled population-weighted tract service, not recovered MW. The narrative that Closeness-first and Degree-first “take the lead” while Impact-first gives the fastest overall recovery conflates possible local curve crossings with whole-horizon outcomes. The saved mean aggregate service loss is lowest among the scheduled policies for Impact-first (33.594 h), compared with Hospital-first (34.306 h), Vulnerability-first (34.258 h) and Degree-first (35.708 h). Unconstrained is a separate reference at 31.338 h. A ranking must name its metric and reference condition; it is not automatically the same at every time or for every community group.

The current Panel B contains all-tract population-weighted loss, Q4 population-weighted loss, hospital-linked equal-weight mean tract loss and population-weighted T80. It no longer contains source-path loss. These are means with 5th–95th realization ranges, not confidence intervals. Q4 is the highest social-vulnerability quartile. Hospital-linked tract service is not hospital electricity delivery or clinical capacity.

**Proposed description:**

Figure 4 compares all eight scheduled restoration priorities with the Unconstrained reference under 2pc50 at the reference resource condition. Recovery curves show mean modeled service availability over the first 100 h; outcome comparisons show service-loss integrals over 0–480 h and time to 80% service. Different priorities produce different aggregate, Q4 and hospital-linked tract outcomes, so a policy's ranking depends on the outcome being considered.

### Figure 5 — Distributional consequences, not a predetermined fairness verdict

Panel A includes all eight scheduled policies and Unconstrained. Panel B shows the four emphasized policies across social-vulnerability quartiles. C and D show Vulnerability-first relative to Hospital-first, Impact-first and Degree-first; the reference must remain explicit. E contains two maps, relative to Hospital-first and Impact-first.

The claim that vulnerability targeting flattens the richest–poorest gap is unsupported and contradicted by the two primary-reference comparisons above. Q4 initially has lower mean service loss than Q1 for these policies; lowering Q4 further while raising Q1 can widen their absolute separation. The signed difference preserves direction, while the within-realization absolute difference measures distance. The mean absolute difference is not generally the absolute difference of group means.

The map colors encode changes in the integral of modeled service deficit. They are not directly maps of earlier T80, statistical significance or the mean population benefiting in each realization.

**Proposed description:**

Figure 5 examines how restoration priorities redistribute modeled service loss across social-vulnerability groups and locations. Vulnerability-first lowers Q4 service loss relative to Hospital-first and Impact-first, but its aggregate effect depends on the reference: a small decrease relative to Hospital-first and an increase relative to Impact-first. Both comparisons increase high–low group separation and population-weighted Gini, showing that targeted benefit, aggregate efficiency and inequality reduction are distinct outcomes. Spatial effect maps locate lower and higher mean tract service loss under the two primary-reference comparisons.

### Figure 6 — Resource dependence of policy contrasts

The pasted explanation describes absolute outcomes, whereas the current eight panels show **Vulnerability-first minus a named reference**. A/B concern aggregate loss changes, C/D Q4 loss changes, E/F high–low group-gap changes, and G/H hospital-linked loss changes. The left column varies crew availability and the right varies duration; they are separate one-factor scenario families. Hospital-first and Impact-first are primary references, while Degree-first supplies reference sensitivity.

These plots do not establish that manpower alone dictates overall efficiency, that prioritization matters only under scarcity, or that inadequate preparedness causally harms poor households. They do not estimate a continuous resource response or crew-by-duration interaction. The intervals are saved 95% percentile-bootstrap confidence intervals for mean effects, unlike Figure 4/5 realization ranges. Degree-first hospital-linked effects have means only where no saved interval exists.

**Proposed description:**

Figure 6 shows how Vulnerability-first's effects relative to the named policies vary across the tested crew-availability and repair-duration conditions. Policy contrasts are largest under the most crew-constrained tested case and generally diminish at higher crew availability; longer tested repair durations amplify Q4 and high–low group-separation contrasts. These cases indicate greater policy leverage when restoration capacity is more constrained relative to workload, with targeted-group gains, aggregate effects and hospital-linked outcomes evaluated separately.

### Figure 7 — Community typology and descriptive hotspots

Panels A/B display six selected descriptive features; these are not the complete eleven-feature clustering input. Cluster membership covers 2,291 eligible residential tracts; the other 24 study tracts are N/A. Cluster names must follow the actual profiles, rather than assuming income or affluence from housing age, building value or vulnerability score.

The social-vulnerability feature uses the documented NRI v1.19 SOVI_SCORE field derived from CDC/ATSDR SVI 2020. It is not simply an income measure. The ten outlined hotspots are highest on the constructed score, not ten independently validated optimal intervention sites. No intervention-response or cost model supports directing funding, reinforcement or response units by this ranking.

**Proposed description:**

Figure 7 describes recovery–vulnerability community typology through feature distributions, standardized cluster profiles and spatial membership. The hotspot map combines recovery and community information to identify locations warranting further examination. Clusters and hotspot scores provide descriptive spatial context, not validated repair or investment priorities.

## Figure 4B: assessment of the grouped-bar suggestion

The suggestion addresses a real reading problem: organizing by strategy would make the three community-group outcomes easier to compare. It is not necessary to change the scientific results to achieve this.

1. A possible grouping is one row per strategy, with three adjacent colors for all-tract population-weighted loss, Q4 population-weighted loss and hospital-linked mean tract loss. These colors would identify outcome groups, rather than the policy colors used in Panel A; the legend must explain that distinction.
2. Keep T80 in a separate axis. Although it is also measured in hours, a threshold-crossing time is not another community-group service-loss integral.
3. The weighting differs: the first two outcomes use population weights over their respective domains; the hospital-linked outcome is an equal-weight tract mean. Hospital-linked tracts can overlap Q4. The three values are neither mutually exclusive contributions nor quantities to add together.
4. Preserve mean and 5th–95th realization range. Grouped bars would require a zero origin and enough room for 27 bars plus intervals. Grouped dots with horizontal ranges could achieve the same grouping with less visual density. Neither choice is automatically better without an actual-size preview.
5. Absolute differences between groups alone do not identify the effect of changing policy. Compare each outcome across policies, and use Figure 5's reference effects for redistribution claims.

Recommendation: use the suggestion as a candidate presentation direction, not as authorization to redraw the current figure. Keep all eight scheduled policies and the independent Unconstrained reference. Do not introduce a new metric, stack overlapping groups, replace uncertainty with bars alone, or state that prioritizing Q4 necessarily delays the system.

## Shared language and statistical definitions

- **Modeled service availability:** the modeled tract service index, not delivered electricity, power or hospital clinical capacity.
- **Service loss (h):** the integral of one minus modeled availability over 0–480 h. For example, availability of 0.5 for 2 h contributes 1 equivalent unavailable-service hour. This is not necessarily the duration of a complete outage.
- **T80 (h):** first time modeled service reaches 80%; it differs from the service-loss integral.
- **Q1/Q4:** lowest/highest social-vulnerability quartile, not richest/poorest or income groups.
- **High–low group separation:** the absolute Q4–Q1 loss difference within a realization, subsequently summarized; it is distinct from signed group difference and from Gini.
- **Gini:** population-weighted inequality in modeled tract service loss; zero indicates equal loss. It is one distributional metric, not a complete definition of fairness.
- **Figures 4/5:** 5th–95th ranges of realization outcomes or realization-level differences, not confidence intervals.
- **Figure 6:** saved bootstrap confidence intervals for mean effects, with means-only exceptions explicitly identified.

## Traceability and scope check

Current figure and caption authority: `results/figure_review/Main/Fig01.pdf` through `Fig07.pdf`, and `results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md` at the review-basis commit.

Numerical authorities read:

- `Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet`; production rows filtered to `M1_UTILITY_003`, `G1_BASELINE_050`, `mapping_native_domain`, and the stated hazard/resource case.
- `Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PAIRWISE_EFFECTS.csv`; `2pc50`, `C57_D1`, `vulnerability-first`, and the explicitly named reference/metric.
- `results/vulnerability/EFFICIENCY_DISTRIBUTION_TRADEOFF_2PC50.csv`.
- Source-gate semantics checked in `src/la_grid/revision/r1_source_gate.py`.

Input SHA-256 values:

| Numerical authority | SHA-256 |
|---|---|
| Formal primary summary | `7f6d7bfd55883fb05b04088e65eea02da579c553064f40d992452cc92690cc4d` |
| Vulnerability policy-effect table | `ef5af1d32dc0184684f9d0c619b96a1dcab596818e1c01be8fe8de7d53cff982` |
| Efficiency/distribution summary | `5e6f50b68c26104de77fec2512991d7066e3fea52c0cf7d9947d8850c5d6e332` |

No artwork or scientific calculation is changed. This document proposes corrected explanations only.
