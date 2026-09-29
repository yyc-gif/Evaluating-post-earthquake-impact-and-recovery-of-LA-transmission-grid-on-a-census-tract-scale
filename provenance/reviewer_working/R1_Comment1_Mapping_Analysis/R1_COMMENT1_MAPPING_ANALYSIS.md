# Reviewer 1 Comment #1 — external candidate benchmark and fixed-decision mapping sensitivity

**Recommendation: hybrid presentation, not a production switch in this task.** Keep the 2,315-tract full-region question and label its output a modeled infrastructure/service-access **proxy**. Use the retained SCE circuit/substation relations as an external *candidate* benchmark, not the only study domain. M2 (utility-constrained, network-informed) is the most defensible candidate for a future full-region proxy because it improves the R1 reference's SCE top-1 and precision-like agreement without M1's broad candidate proliferation. Do not replace the production mapping until all intended strategy trajectories can be evaluated under a common domain and the same decision policies. The July 92-station mapping should remain a historical benchmark, not be interpreted as empirical customer assignment.

## Question and evidence boundary

Reviewer 1 #1 objects to a centroid/network-IDW/cutoff matrix without utility territory, feeder, or outage evidence; population recovery, hospital priority, and community interpretation inherit that assumption. The request is stronger external support where possible, robustness beyond cutoff-only variation, and a clearer proxy claim. The analysis changed no scientific function or frozen input. It read the July mapping, the retained **2026-09-14** SCE/CEC/LADWP snapshot from historical commit `87110da`, the frozen R1-310 static graph/matrix, and saved baseline trajectories. No current portal response replaced the retained snapshot.

The SCE [DRPEP circuit layer](https://drpep.sce.com/arcgis_server/rest/services/Hosted/Distribution_circuits/FeatureServer/0) exposes circuit IDs/names, `sub_name`, `sys_name`, voltage and line geometry. The [SCE substation layer](https://drpep.sce.com/arcgis_server/rest/services/Hosted/ICA_Layer/FeatureServer/18) supplies station-role/identity context. The [CEC load-serving-entity polygons](https://services3.arcgis.com/bWPjFyq029ChCGur/ArcGIS/rest/services/ElectricLoadServingEntities_IOU_POU/FeatureServer/0) constrain utility-level geography. See `EXTERNAL_DATA_PROVENANCE.csv` for retained date, fields, counts, raw/archive hashes, and limits. The archived raw-response ZIP is SHA-256 `8450c804063ba2af5fb2677332b27786fcbd250e36e1784695488293f295ba53`. It has 56 request records and their individual hashes. The public circuit geometry is **not** a household-to-feeder assignment, service share, or historical outage trace; this 2026 planning-data epoch is not backdated to any earthquake scenario.

The retained polygon classification has 817 strict SCE tracts, 848 strict LADWP tracts, and 650 mixed/other/ambiguous tracts. All 817 strict SCE tracts intersect published circuits; 794 have at least one circuit-derived candidate crosswalked to an R1 ID, and 23 have none. Among the 794, **350 also have unmatched official station candidates**. Thus even a top-1 match is candidate consistency, not full service allocation. For LADWP, retained public territory and system-role references do not contain comparable tract-to-customer feeder assignments; no relationship was invented.

## Predeclared alternatives and fair comparison

| Label | Definition | Role |
|---|---|---|
| M0_July_92 | Submitted expanded-area 2,315×92 network-distance IDW output, exponent 2, 0.03 cutoff | Historical baseline and SCE candidate benchmark only |
| M0_R1_310 | Already frozen 2,315×310 R1 closure `W` | Same-station reference for saved R1 outcomes; not July's 92-node result |
| M1_utility_spatial | Strict SCE/LADWP tracts restrict candidates to explicitly owned R1 stations of that utility; ambiguous tracts retain a general candidate pool. Polygon centroid-to-station EPSG:3310 Euclidean distance, exponent 2, 0.03 row cutoff and normalization. | Minimal utility-constrained spatial proxy |
| M2_utility_network | Same territory/ownership restriction; station must be registered in a source-containing frozen component. Select the nearest eligible access station, then use access distance plus shortest path over **frozen** R1 direct edges (1,040 retained edge rows), exponent 2, 0.03 cutoff. Unreachable candidates remain excluded. | Utility-constrained network-informed proxy |
| M3_SCE_evidence | Official intersecting circuit `sub_name/sys_name` candidate set, crosswalked where possible to R1; no inferred service shares. | External benchmark, not full-region mapping |

M1/M2 use July's exponent and cutoff **without fitting them to SCE overlap**. Their station universe is R1-310; `M0_July_92` versus M1/M2 also changes inventory, so the clean within-R1 mapping comparison is `M0_R1_310` versus M1/M2. No load/capacity weights, nearest fill for missing official candidates, topology rebuild, or dynamic source-gate rerun was used. Mixed tracts remain Tier 3 general proxy rather than being assigned to one utility from a small polygon sliver.

## External candidate benchmark

Denominator: the **794** strict SCE tracts with at least one official candidate matched to R1; 23 with only unmatched candidates remain visible but have no matched-R1 denominator. Any-match asks whether at least one positive proxy station is in that matched official set. Precision-like and recall-like values are unweighted candidate-set fractions, **not** conventional supervised accuracy. Top-3 uses the three largest weights. Spatial offset is the distance from proxy top-1 station to the nearest matched official R1 station, not customer distance or feeder error.

| Mapping | Any match | Mean precision-like | Mean recall-like | Top-1 | Top-3 | Mean candidates | Mean max weight | Mean HHI | Mean top-1 offset km |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M0_July_92 | 40.8% | 0.219 | 0.238 | 37.9% | 40.6% | 3.36 | 0.774 | 0.657 | 2.50 |
| M0_R1_310 | 86.8% | 0.504 | 0.602 | 69.1% | 85.0% | 2.53 | 0.831 | 0.744 | 0.63 |
| M1_utility_spatial | 99.0% | 0.426 | 0.921 | 73.0% | 96.0% | 4.82 | 0.528 | 0.407 | 0.55 |
| M2_utility_network | 89.8% | 0.544 | 0.636 | 73.4% | 88.5% | 2.51 | 0.847 | 0.761 | 0.55 |

`SCE_CANDIDATE_BENCHMARK.csv` also gives p90 offset and effective candidate count. M1's near-universal any-match is partly achieved by a **broader** candidate set: it improves recall but lowers precision-like fraction relative to M0_R1. M2 makes a smaller, more balanced improvement. Neither validates the weights or proves that an R1 station serves residents of an intersected tract. The large M0_July-to-R1 change cannot be attributed solely to the utility constraint because 92 became 310 stations.

The analysis-only tier table retains all **2,315 tracts**: 794 Tier 1 (a matched SCE public candidate exists, even if other official candidates are unmatched), 871 Tier 2 (utility and network proxy, including 23 SCE tracts without matched R1 candidate), 650 Tier 3 (mixed/other general proxy), zero algorithmically unsupported. “Supported” here means the formula returns a candidate; it does **not** mean empirical service assignment. `MAPPING_EVIDENCE_TIERS.csv` keeps the per-tract distinction.

## Fixed-decision offline outcome sensitivity

Only **GA-Balanced and GA-HospFirst**, each over the same 32 saved physical realizations, have complete per-run R1-310 effective-state trajectories in the retained `SCIENTIFIC_RUN_CHECKPOINTS.zip` baseline section. These are historical `87110da` candidates, not newly optimized Phase 3 sequences. The saved network deficit integrals were reproduced exactly from the event-step states. For each fixed run and mapping, unidentified R1 cells are excluded from resolved mass, never treated as failed state. Tract normalized burden is `Σ_i W_ri ∫(1−state_i)dt / Σ_identified_i W_ri`; the second population burden uses `Σ_r Pop_r × mass-burden_r / Σ_r Pop_r × resolved-mass_r`. Population T80 is the first saved event reaching 0.8 of total resolved, population-weighted candidate mass. Quartiles and hospital-tract flags are fixed from the retained 2,315-tract metadata. This is **offline evaluation of fixed decisions**, not policy redesign under a changed mapping.

| Mapping | Fully unresolved tracts / population | Balanced mean normalized burden h | HospFirst mean normalized burden h | Balanced−HospFirst burden h | Balanced−HospFirst T80 h | Balanced Q4−Q1 h |
|---|---:|---:|---:|---:|---:|---:|
| M0_R1_310 | 36 / 141,615 | 83.426 | 83.434 | −0.0079 | +0.0575 | −3.393 |
| M1_utility_spatial | 0 / 0 | 84.090 | 84.092 | −0.0019 | +0.0071 | −1.147 |
| M2_utility_network | 15 / 58,545 | 82.383 | 82.387 | −0.0034 | +0.0235 | +0.265 |

The mappings change both weights **and identified coverage**. On the 2,279-tract common resolved domain (8,924,907 residents), Balanced's population-normalized burden is 83.426, 83.582 and 82.046 h for M0_R1/M1/M2. This still shows a mapping-dependent absolute level, without denominator drift. The two-strategy mean difference remains small and negative under these three tested mappings, while the first-event T80 difference stays small and positive; neither is evidence of equivalence or a general four-strategy rank. The Q4−Q1 **sign changes** under M2, so the group-level interpretation is not stable.

Spatial attribution is more sensitive. Across saved tract–realization cells, M1 changes absolute normalized burden from M0_R1 by mean **10.64 h** and exceeds 1 h in **83.1%**; M2 changes it by mean **5.41 h** and exceeds 1 h in **31.8%**. The ±1 h practical Balanced-versus-HospFirst *32-run mean* classification changes from 35 improved / 9 worsened / 2,235 near-zero / 36 unresolved (M0_R1) to 19 / 3 / 2,293 / 0 (M1) and 37 / 9 / 2,254 / 15 (M2). This threshold is not statistical significance, and near-zero pairwise effects do not mean absolute tract burden is mapping-insensitive. See `MAPPING_TRACT_SHIFT_SUMMARY.csv`, `OFFLINE_TRACT_ATTRIBUTION_TWO_STRATEGIES.csv`, and `MAPPING_PAIRWISE_EFFECTS.csv`.

**Completeness limit:** saved HF and Efficiency results do not include full 310-station per-run trajectories. Their narrower 116-interface integrals cannot identify the contribution of every R1 station to M0_R1/M1/M2, and the July 92-station curves are already aggregated. Thus population T80, hospital/group effects, Gini, and winners/losers for **all four strategies under full-region M0/M1/M2** cannot be computed without additional upstream state storage or rerunning the scientific chain. This task ran neither. The table is a bounded two-strategy evaluation sensitivity, not a robustness certificate for the final strategy comparison. Rebuilding priorities or re-optimizing under M1/M2 would answer a different *policy-redesign* question and was not done.

## Recommendation and direct answers

1. **Q1 — Public support:** utility-level polygons and SCE circuit/station *candidate* relationships; the archived strict-SCE subset permits external candidate-consistency checks.
2. **Q2 — Unknown:** household feeder assignment, true customer/load shares, switching, outage records, and comparable LADWP tract-feeder links.
3. **Q3 — July weakness:** one centroid-selected access station, graph-IDW across utility boundaries, arbitrary cutoff/fallback, and no customer-level validation; the 92-station inventory further limits official-candidate overlap.
4. **Q4 — M1/M2 change:** M1 removes clear cross-utility candidates but spreads mass; M2 additionally uses the frozen eligible network and improves SCE candidate agreement more selectively. Neither establishes actual service.
5. **Q5 — SCE evidence:** M0_R1 is partly supported; M1/M2 improve different candidate-set metrics, with M2 the better balance. Evidence does not identify shares or prove a complete historical mapping.
6. **Q6 — Aggregate strategy stability:** in the **two archived strategies only**, the small paired burden direction is unchanged across tested maps, but T80 points the other way and no four-strategy conclusion is established.
7. **Q7 — Tract/community attribution:** not stable enough for unchanged local claims; absolute tract burden shifts are common and the Q4−Q1 sign changes in this bounded test.
8. **Q8 — Method or limitation:** recommend full-region **M2 proxy plus SCE external benchmark**, with M0_R1/M1 evaluation sensitivity and explicit evidence tiers, as the candidate future presentation. **Do not change production mapping now.** Before making four-strategy full-region claims, retain complete per-run R1 states for all strategies and rerun only the offline mapping/evaluation layer; if unavailable, label that result untested. No feeder-truth, actual-outage, or actual-electricity claim is warranted.

No mapping, damage, scheduler, source, GA, crew, typology, manuscript, or final scientific result file was modified. The only new code is this folder's read-only analysis script and the only new tables are analysis outputs.
