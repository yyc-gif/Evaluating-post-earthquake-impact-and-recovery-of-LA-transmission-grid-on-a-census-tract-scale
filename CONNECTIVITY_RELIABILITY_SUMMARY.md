# Substation-fragility source-connectivity reliability (read-only analysis)

## Scope and inputs

This calculation uses the unchanged July 92-station/318-edge abstracted graph,
14 retained Core sources, production threshold 0.5, station-specific fragility
and fixed hazard PGA. It does **not** use line or distribution-circuit
fragility, repair, crew scheduling, GA, or a revised service gate. The
expanded graph SHA-256 is
`1a3073240a6dca3e902e0bf5c2b975c67ff100892d85f007270e9855250bd225`;
the Core-source file SHA-256 is
`892f5ec3e9a260db138c7fb2454dea09fcb75a8989ef13695aefca417b8c2955`.

The formal functionality values for DS0–DS4 are 1, 0.50, 0.09, 0.04, and
0.03. Thus a station is functional precisely for DS≤1 and
`p_functional = 1 − P(DS≥2 | station PGA)`. The three historical hazards use
the original `_old` station fragility parameters, as in their formal physical
samples; 2pc50 uses the current parameters. For each hazard, 100,000
independent station-functional masks were sampled with fixed SeedSequence
`[20260926, hazard_index, 721]`. Full masks, gate states, source counts and
station-independent route counts are retained locally as
`Formal_Experiment_20260923/Formal_Reviewer_Results/CONNECTIVITY_RELIABILITY_STATES_<hazard>.npz`.
Here an independent route joins a functional non-source station to any active
source without sharing an intermediate station with another counted route;
several routes may terminate at the same source. A local active source is
recorded separately rather than counted as an upstream route.

`R_conn` is the probability that a station is both functional and connected
to an active Core source. `R_path` is the conditional probability of source
connectivity given that station is functional. For an active Core source,
`R_path=1` by definition, even if no functional instance of that rare source
appears in a finite Monte Carlo sample. A zero functional count in the formal
1,000-sample comparison is reported as an undefined *sample estimate*, not
zero. The tract measure is the requested linear dependency-weighted index
`Σ_s w_rs R_path_s`; it is not the joint probability of full tract power.
The companion `Σ_s w_rs R_conn_s` represents expected initially connected
station dependency mass. Neither is actual delivered power.

## Four-hazard results

| Hazard | Population-dependency-weighted R_path | Weighted R_conn | R_path, intact one-route stations | R_path, intact multiple-route stations | Multiple minus one route |
|---|---:|---:|---:|---:|---:|
| Northridge | 0.7680 | 0.4975 | 0.3955 | 0.8218 | +0.4263 |
| SanFernando | 0.9289 | 0.7207 | 0.6943 | 0.9585 | +0.2642 |
| LongBeach | 0.9592 | 0.6772 | 0.6902 | 0.9288 | +0.2386 |
| 2pc50 | 0.1421 | 0.000973 | 0.0000 | 0.00689 | +0.00689 |

The route-class columns above are unweighted station means among the eight
non-source stations with one route in the intact graph and the 70 non-source
stations with multiple routes. The population-dependency-weighted class
means, and each group's mean fragility-based functionality probability, are
in `CONNECTIVITY_ROUTE_RELIABILITY_CROSSWALK.csv`; they should be consulted
because hazard exposure and fragility also differ among route classes. Among
the 78 non-source stations, Spearman correlations between intact route count
and `R_path` are 0.793, 0.764, 0.475, and 0.524 in the hazard order above.
These are descriptive station associations, not independent-station causal
tests. In 2pc50 the system is so damaged at t=0 that both non-source route
classes rarely retain any source path, so intact redundancy offers little
initial connectivity despite the positive class difference.

Across all station/sample states, the population-dependency-weighted
unconditional probabilities of one-route versus multiple-route connection
are 0.0425 versus 0.3860 (Northridge), 0.1002 versus 0.5463
(SanFernando), 0.1038 versus 0.4673 (LongBeach), and 0.000069 versus
0.000006 (2pc50). The remaining mass includes disconnected/inactive states
and local active sources. These route counts do not assign different service
weights: both connected classes pass the unchanged binary gate.

## Convergence and exact formal-gate parity

All 4,000 frozen formal evaluation realizations were read at t=0 from the
existing hospital-first trajectories. For every station and realization,
recomputed `F=(DS≤1)` and source-connected `C` **exactly matched** the
saved formal `F` and `C`. Population-weighted `R_conn` from the 1,000 formal
realizations versus the independent 100,000-state topology sample is
0.4994/0.4975 (Northridge), 0.7185/0.7207 (SanFernando),
0.6774/0.6772 (LongBeach), and 0.000914/0.000973 (2pc50).
For 1, 1, 0, and 5 stations respectively, no functional state appeared in
the formal 1,000 draws; their empirical conditional `R_path` is undefined.
The 100,000-state route class partition and the identity
`R_conn = P(κ=1)+P(κ≥2)+P(local active source)` held to numerical precision
for every station and hazard.

## Component importance and low-reliability tracts

For each sampled mask and each station `j`, all other functional states were
held fixed and `j` was forced functional and then nonfunctional. The saved
matrix is `I_ij = P(C_i=1 | do(F_j=1)) − P(C_i=1 | do(F_j=0))`, where `C_i`
includes target `i`'s own functionality as in the production gate. The
importance table contains both direct `i=j` and downstream `i≠j` effects;
the following population-weighted values exclude the direct term:

| Hazard | Leading downstream bottleneck | Importance as fraction of represented population dependency |
|---|---|---:|
| Northridge | EAGLE ROCK (301558) | 0.0132 |
| SanFernando | STATION K (OLYMPIC) (301105) | 0.0748 |
| LongBeach | TARZANA/STATION U (303620) | 0.0247 |
| 2pc50 | HARBORGEN (304450) | 0.00215 |

The next highest stations and the full 92×92 intervention matrix for each
hazard are in `CONNECTIVITY_COMPONENT_IMPORTANCE.csv`. A low importance in
2pc50 does not mean a station is intrinsically unimportant; with nearly all
stations nonfunctional at t=0, changing one station often cannot restore a
complete path. These are model-topology intervention effects, not observed
grid engineering criticality.

`TRACT_CONNECTIVITY_RELIABILITY.csv` gives continuous values for all 2,315
tracts per hazard. Examples of lowest positive-population tract `R_path`
are 06037115202 (Northridge, 0 sampled), 06037109100
(SanFernando, 0.1217), 06037572301 (LongBeach, 0.1121), and
06037264306 (2pc50, 0 sampled). At or below 0.1 are 382 tracts
(1.342 million represented population) in Northridge and 1,838 tracts
(7.167 million) in 2pc50; none in the other two hazards. Exact sampled
zeros should not be read as physical impossibility.

## Interpretation boundary

The formal t=0 source-connected state is identical to this analysis's `C`,
so the existing physical Monte Carlo already propagates route redundancy
into the **probability of remaining connected**. The binary gate does not
distinguish one route from several once connection survives. The large
historical-hazard class differences show that topology matters to
connectivity reliability; they do not by themselves establish a quantitative
MW/service penalty for one-route states. No result here justifies changing
the production service formula without an independently supported
damage-to-capacity or operational relation. The gate remains unchanged for
author review.
