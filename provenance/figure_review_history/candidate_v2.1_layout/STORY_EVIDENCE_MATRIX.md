# Story-evidence matrix — candidate v2.1

This matrix locates accepted evidence for author review. It is not a manuscript figure selection, does not promote candidates, and does not alter `results/figures/`. Candidate v2 remains untouched.

| Evidence topic | Current frozen authority | v2.1 review location | Evidence status / boundary |
|---|---|---|---|
| System representation | CEC GIS panels; 92-node/318-edge graph; 14 Core sources | Fig02 A–B | Direct system representation; reachability is not electrical adequacy. |
| Utility eligibility and revised tract dependency | Frozen 2,315-tract utility-domain and mapping-shift crosswalks | Fig02 C shows SCE/LADWP/other eligibility domains and domain counts; existing mapping-robustness evidence shows M0-to-revised weight shifts | **Closed for the eligibility representation:** the main candidate now directly shows which candidate pool applies spatially. Neither panel validates feeder or service-territory truth. |
| Public mapping evidence | Frozen 337 direct-site agreement summary; earlier 342-tract crosswalk | Fig02 D | Direct-site agreement shown on 337 comparable tracts; distinct 342 set is disclosed; not accuracy or feeder validation. |
| Four-hazard damage and initial service | Frozen four-hazard damage and tract initial-service tables | Fig03 A–B | Direct scenario context; historical/current fragility sets differ. |
| Local, threshold, source-path loss mechanism | Frozen `LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv`, Unconstrained rows | Fig03 C | **Closed:** a policy-independent Unconstrained decomposition exists for all four hazards and replaces the prior Hospital-first integral. It is an integrated component summary, not dynamic timing. |
| Unconstrained recovery baseline | Frozen C57_D1 Unconstrained summary and tract initial/T80 table | Fig03 D | Direct 2pc50 population T80 distribution and reached-tract T80 map; distinct estimands. |
| Full scheduled-policy recovery | Frozen recovery curves and 84k+10k summary authorities | Fig04 A–B | **Closed:** all eight distinct policies plus Unconstrained are shown; four explanatory strategies emphasized, remaining four retained. Curves display 0–120 h; burden/outcomes use 0–480 h. |
| Aggregate burden, T80 and hospital-linked burden | Frozen strategy summaries | Fig04 B | All policies retained with uniform 5th–95th realization ranges, not confidence intervals. Hospital-linked tract service is not hospital electricity or clinical capacity. |
| Q1–Q4 absolute burden | Frozen 2pc50 strategy/equity summaries | Fig05 A | Four policy contrasts shown; Q4 is highest and Q1 lowest social-vulnerability quartile. |
| Aggregate vs Q4 burden | Frozen strategy summaries | Fig05 B | Mean summary estimates only; no uncertainty encoded in this plane. The adjacent matched-effects panel carries paired-realization ranges. |
| Reference sensitivity, signed/absolute group separation and Gini | Frozen strategy/equity summaries | Fig05 C | Matched VF−Impact/Hospital/Degree contrasts shown; Gini is separately unitless and is not treated as a single equity verdict. |
| Spatial paired effects | Frozen tract-effects table contains VF−Impact and VF−Hospital | Fig05 D | **Closed:** map uses VF−Impact, 2pc50, all 2,315 tracts. Mean sign/magnitude is not significance or per-realization improved population. |
| Two-level crew contrast | Frozen C29_D1/C57_D1 outcomes | Fig06 | **Closed at the stated scope:** exact 29- vs 57-crew comparison; no continuous response language. |
| Full discrete crew cases | Frozen C29/C57/C86/C114 summaries, eight distinct scheduled policies, n=1,000 each | Candidate supplement: Crew Resource Contrasts | **Closed:** all tested discrete crew cases are visualized for four outcomes; no values between cases are inferred. |
| Repair-duration cases | Frozen C57_D0.75/D1/D1.25/D1.50 summaries, eight distinct scheduled policies, n=1,000 each | Candidate supplement: Repair Duration Contrasts | **Closed:** complete frozen D variants exist and are visualized for four outcomes; claims are limited to tested 2pc50 cases. |
| Cross-hazard policy contrasts | Frozen formal plus Vulnerability-first summary tables; all eight strategies, each n=1,000/hazard | Candidate supplement: Cross-Hazard Policy Robustness | **Closed for descriptive scenario contrasts:** all four hazards and eight policies have frozen results. Fragility vintage differs, so not a pure PGA sensitivity. |
| GA reproducibility | Five fixed-seed histories, incumbent summary, sequence identity | FigS05 A–C | **Closed:** candidate mean traces vary, best-so-far remains at Impact-first incumbent, no seed improves it. This is not proof of global optimality. |
| Stage 7 typology/hotspots | Harmonized Stage 7 labels/status/profiles/hotspot output | Fig07 A–C; FigS09 A–D | **Closed:** same Stage 7 cluster-ID palette in Fig07 map and FigS09 scatter. 2,291 typology members; 24 tracts remain explicitly outside typology. |
| Mapping/gate robustness | Existing frozen mapping, cutoff and gate sensitivity tables | Existing supporting authorities; not recomputed here | Evidence remains available in the prior collection; this v2.1 pass does not add a new sensitivity. |
| Source redundancy | Frozen station/dynamic connectivity diagnostics | Existing supporting authorities; not recomputed here | A connectivity diagnostic, not delivered MW or capacity. |
| Capacity sensitivity | Frozen SCE closure and supported-station output | Existing supporting authorities; not recomputed here | Limited supported subset; cannot establish full-system earthquake-time electrical adequacy. |

## STORY_EVIDENCE_GAP closure and remaining claim boundaries

**Closed by existing frozen evidence:** the loss-mechanism panel can be a general Unconstrained baseline because all four hazards have frozen Unconstrained decomposition rows; the resource/duration review no longer lacks its scenario coverage because all four crew cases and four duration cases have 1,000-realization summaries for the eight distinct scheduled policies; Vulnerability-first also has frozen summaries in all four hazards; the tract map can use the existing Vulnerability-first minus Impact-first tract-effect authority; and the GA plot has generation-mean candidate traces as well as incumbent history.

**Resolved by narrower claims rather than new evidence:** cross-hazard contrasts must be called scenario contrasts because historical hazards and 2pc50 use different adopted fragility parameter sets. Crew count and duration are separate discrete one-factor scenario families; the archive does not define a full crew-by-duration factorial, so no interaction or interpolated response claim is supported. Public-site comparison is candidate-site agreement on 337 comparable tracts, not accuracy, feeder validation, service-territory ground truth, or whole-model predictive validation. Capacity support is not full-network adequacy. Source reachability/redundancy is not delivered power. Stage 7 cluster/hotspot outputs are descriptive/screening products, not intervention priorities.

| Previously identified gap / claim risk | Status in v2.1 | Frozen evidence or claim boundary |
|---|---|---|
| Policy-independent loss-mechanism decomposition | CLOSED | Four-hazard Unconstrained rows in the accepted decomposition table; no restoration policy is used as a general baseline. |
| Utility candidate eligibility visible in the system figure | CLOSED for representation | Fig02-C maps the frozen 2,315-tract utility domains and candidate-pool rule. External public-site comparison remains support/agreement only. |
| Resource and duration robustness absent from review figures | CLOSED for tested cases | All four crew-count cases and all four duration-multiplier cases have 1,000 frozen realizations per distinct scheduled policy. They are separate discrete scenario families. |
| Cross-hazard policy evidence | CLOSED for descriptive contrasts; interpretation narrowed | All four hazards are represented. Differences across hazards are not pure PGA effects because adopted fragility parameter vintages differ. |
| GA candidate search hidden by coincident incumbent curves | CLOSED for execution evidence | Five frozen generation-mean candidate histories are shown against the retained incumbent. The finite search does not establish global optimality. |
| Full-network earthquake-time electrical adequacy | OPEN; claim must remain bounded | No compatible load-flow case supports calculation of delivered MW, overload, or adequacy. Source reachability is not electrical delivery. |
| Feeder/service-territory mapping truth | OPEN; claim must remain bounded | Public-site candidate agreement is not feeder ground truth or predictive mapping accuracy. |
| Crew-by-duration interaction / continuous response | OPEN; claim must remain bounded | No complete frozen factorial or continuous parameter support exists; do not interpolate between cases. |
| All 2,315 tracts in residential typology | OPEN by defined scope, explicitly represented | Only 2,291 tracts enter residential clustering; 24 are labeled outside/not applicable and are not assigned a cluster. |

## Three core research questions

| Core question | Direct v2.1 evidence | Status |
|---|---|---|
| 1. How do hazard and network dependency produce tract service disruption? | Fig02 B–D; Fig03 A–D; existing mapping-robustness evidence | Direct evidence for retained topology, utility eligibility, public-site agreement, hazard loss decomposition, and Unconstrained baseline. Earthquake-time electrical adequacy remains a claim-limited gap: no load-flow/capacity simulation is supported. |
| 2. Under logistics/resource constraints, how do priorities change overall and critical-service recovery? | Fig04 A–B; Fig06; crew and duration robustness candidates; FigS05 | Direct for displayed 2pc50 cases and frozen discrete scenario families. No continuous interpolation or crew-duration interaction. |
| 3. How are burdens redistributed across vulnerability groups and places? | Fig05 A–D; Fig06; crew/duration candidates; Fig07 descriptive community context | Direct for the displayed metrics; no single “fairest policy” claim. |
