# Recovery patterns: decision for author review

**Recommendation: describe recovery continuously in the main engineering
analysis. A two-group trajectory summary and a two-group resource-sensitivity
description are useful optional summaries, not established universal community
types. Do not replace formal Stage 7 or strengthen the previous K3 claim.**

Protocol was pushed first at `bc7d7c0798588ac585426a59f98046f282df2383`.
Starting scientific branch: `5e6a950e2bf58fc72279991430dd0ed5731f6d3f`.
All 2,299 tracts and 9,066,522 residents remain represented, including the eight
positive-population zero-housing tracts. No physical simulations were rerun.

## 1. What the trajectories establish

A uses absolute mean availability in five exact event-integrated time windows,
with equal window budgets, not separate z-scores. Two unwhitened principal
components retain 99.875% of variance (PC1 90.921%); PCA and full-window K2
memberships are identical. Most differentiation concerns 6-72 hours. The
168-480-hour window is effectively constant in these frozen results.

A/K2 separates 1,058 and 1,241 tracts. Mean silhouettes across registered seeds
for K2..6 are 0.5581, 0.4759, 0.4977, 0.4622 and 0.4571. Random-subsample ARI
is 0.9940/0.9953 at 70%/85%; spatial leave-cell-out mean full-cohort ARI is
0.9886 (minimum 0.9587). Its largest window-profile change is 0.000764 under
random sampling and 0.001642 under spatial exclusion. These are reproducible
summaries, appreciably more stable than the previous mixed P2/K3 representation.

But reproducibility does not establish discrete physical regimes. K2 agrees
with two simple reference-burden quantiles at ARI 0.8399, and Ward at only 0.5214.
The mean curves mostly shift along a recovery-speed gradient. A/K3 has three
ordered curves, not a new demonstrated mechanism; its worst spatial withheld
ARI is 0.2031. K4-K6 add resolution, not a uniquely supported regime count.
Ward agreement improves at K5 (0.8834), illustrating criterion disagreement.
No new gap/null test was registered; K1/no uniquely meaningful partition is
not ruled out. These observations support a continuous interpretation, not a
proof that the distribution is mathematically unimodal.

## 2. Engineering information, including contradictory outcomes

The slower A/K2 group has 8.83 h more Random deficit, 9.93 h later Random median
T80, and 10.99 h more C29 deficit. These contrasts exceed registered thresholds
and persist in all random and spatial profile checks. However, differences in
the *change* caused by reduced crews are only 2.61 h, below the 5 h convention.
Much of the contrast is overall recovery severity, not different resource
response. Northridge and SanFernando retain higher burdens in this group;
LongBeach reverses the ordering (difference about -5.00 h, boundary-sensitive).

| Pooled held-out MAE, hours | A/K2 | A/K3 | Burden quantiles K2 | P2/K3 | Continuous A |
|---|---:|---:|---:|---:|---:|
| Random deficit | 5.438 | 5.688 | 5.567 | 5.087 | 4.620 |
| C29 deficit | 8.281 | 8.079 | 8.435 | 7.951 | 5.526 |
| C114 deficit | 2.513 | 2.214 | 2.483 | 2.680 | 0.809 |

The compact continuous models were prespecified, not tuned after observing
results. A/K2 adds no registered meaningful advantage over burden quantiles
on these endpoints; adding a third trajectory group does not resolve that.
Tables retain all ten outcomes, both sampling fractions and all K2..6.

For comparison, P2/K2, P2/K3 and P2/K4 have pooled Random-deficit MAE
5.351/5.087/4.901 h and C29-total MAE 8.424/7.951/7.584 h on these same draws.
Neither improved trajectory membership stability nor a higher silhouette
therefore establishes across-outcome superiority to the old mixed-variable space.

## 3. Mechanism representation: useful, but different and source-sensitive

B contains initial availability, Unconstrained burden and Impact-first extra
burden, each cohort-standardized with equal construct budgets. B does not use
the five-policy MeanDelta or any social/population feature. It identifies a
meaningful baseline-versus-resource-constraint distinction not captured by
ranking total reference burden alone.

B/K2 separates 2,066 tracts from 233 (901,443 residents, 9.94%). The 233-tract group
has lower baseline deficit (27.01 versus 32.13 h), but larger reference increment
(9.35 versus 1.49 h). With 29 crews its mean total deficit is 68.40 versus 42.45 h;
the reduced-crew increment is 32.04 versus 8.83 h. With 114 crews the smaller group
has *less* total deficit. Under Random it also has less burden (31.94 versus
40.44 h): priorities and resources alter rankings, not just levels.

Random resampling preserves the C29-increment contrast in every draw. B/K2
reduces that endpoint's held-out MAE by 2.72/2.74 h relative to two total-burden
quantiles, but its Random-deficit MAE is about 0.78 h worse. It improves C29-total
MAE by about 1.06 h on average, not in every draw. A continuous B model is better
still (C29 increment MAE 4.812 h versus 5.579 h for B/K2). This is a valuable
mechanism-focused descriptive result, not across-context classification dominance.

B/K2 has silhouette 0.6437 and Ward ARI 0.8890. Random membership ARI is
0.9761/0.9830; spatial mean is 0.9314 but one leave-out cell (8_-24) reduces
full ARI to 0.2456. Its C29 total contrast falls below 5 h in one of 15 spatial
refits, although the increment contrast remains meaningful. Northridge has the
opposite group ordering to LongBeach, whose contrast is below 5 h. No hazard-
independent or policy-independent recovery regime is established.

B/K3 adds a 34-tract group, all within the historical 37-tract Q-source-proxy
reference. Its mean initial availability is 0.018153 (1.815%, not strong absolute
service); 91.66% of its centroid distance comes from that coordinate. It is
random-sample stable but concentrated: 30/34 tracts occur in one 20-km cell.
Leaving cell 7_-24 out changes full B/K3 agreement to 0.2293. Removing Init only
from saved distances, without refitting/reweighting, expands that projected
centroid's catchment from 34 to 247 tracts (ARI 0.6274). Thus all 34 may remain
assigned to that projected centroid, but its rare-state specificity is lost.
This is not an executed minus-Init clustering or evidence of physical resilience.

B/K4 is highly random-stable and has better spatial full ARI (mean 0.9836),
but Ward agreement is 0.4555 and it still isolates 34 source-proxy tracts. B/K5
and K6 do not supply an invariant natural resolution either. Small size alone
is not the objection; model-source leverage and context dependence are.

This does not make the higher-resolution results useless. B/K4 distinguishes
964/1,125 tracts with higher/lower baseline burden, a 176-tract high-increment
group (11.41 h), and the 34-tract initial-state exception. It improves C29-total
MAE over four burden quantiles by 1.64 h, meeting the 1 h margin in all 60 draws.
Its Random-deficit gain is only 0.39 h, below that margin. B/K5 and K6 also improve
resource prediction, without a comparable general policy-outcome advantage.
These are meaningful resource-focused subdivisions, not evidence to suppress
because they contain a small class. They do not meet the preregistered broad
policy-and-resource advantage rule for a primary replacement typology.

No registered representation/K achieves the 1 h Random-deficit gain over its
same-K burden-quantile benchmark in 90% of draws. Continuous response models
remain preferable for preserving differences across the unused contexts.

## 4. Social context is not a recovery class

A/K2 slower/faster groups have mean SOVI 60.32/71.78, respectively, with Q4
counts 214/365. Both include every vulnerability quartile; their SOVI IQRs are
36.86-86.33 and 58.68-91.12. B/K2 groups have SOVI 67.55/57.29 with equally broad
overlap; hospital-linked incidence is 4.65%/3.00%, descriptive of locations only.
All eight zero-housing tracts remain classified. None belongs to B/K3's
34-tract exception; that group is not an isolated zero-housing-tract artifact.

Adding K2/K3 labels to continuous recovery features and a fixed geographic
basis improves random held-out SOVI MAE by at most 0.0432 points on average,
far below the registered 2-point convention; spatial gains can be negative.
Raw social differences are real descriptions, but do not supply a separate
classification association beyond these continuous/geographic predictors.
This is not a causal adjustment or proof that all geographic confounding is removed.

## 5. Answers and manuscript decision

1. **Discrete groups?** Stable subdivisions exist, particularly A/K2; no unique
   physical partition is established. Retain continuous variation as primary.
2. **Clearer than P2?** A clarifies recovery speed and is more membership-stable;
   B clarifies resource sensitivity. Neither supplies a universally better typology.
3. **Do A/B agree?** No. Their distinctions differ scientifically and in membership;
   B/K2 has ARI 0.0036 with total-burden quantiles and 0.1255 with P2/K3.
4. **What transfers?** Severity contrasts often persist, and B's reduced-crew
   increment is robust; policy/scenario rankings and some geographic fits do not.
5. **Beyond rankings?** A adds little; B adds resource-response interpretation,
   but continuous baseline/increment modeling retains more information.
6. **Social differences?** Yes descriptively, with large within-group overlap;
   no registered meaningful incremental SOVI prediction after continuous/context adjustment.
7. **Main manuscript?** Support continuous recovery/resource comparisons and
   a cautious secondary B/K2 mechanism description. Do not adopt a replacement
   clustering or claim the existing P2/K3 is independently validated.

All withheld checks remain inside the same frozen simulation framework. They
share network, mapping, source assumptions and damage-model architecture; other
earthquakes are not independent observed outage evidence. The 1,000 realizations
were not resampled as a new earthquake uncertainty experiment. Spatial blocks
are sensitivity checks, not independent replications or significance tests.
Any manuscript or Figure 7 change requires subsequent author approval.

Excluding population from fitted coordinates does not make the experiment
population-independent: the reference Impact-first priority is population-impact
oriented. Resource/hazard transfer here uses verified integral outcomes; no
transfer-scenario T80 or full-curve history was inferred from integral means. The
resampled profile contrasts describe changes in assigned groups over the common
cohort; held-out MAE tables separately test prediction on unused tracts.
