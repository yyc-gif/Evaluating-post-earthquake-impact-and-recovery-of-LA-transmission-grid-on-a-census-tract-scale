# Reviewer 1 #1 — July mapping baseline

Reviewer 1 identified the tract-centroid, network-distance and IDW dependency matrix as an assumed service mapping. The reviewer asked for utility/feeder/outage support where possible, robustness beyond changing only the cutoff, and a clear proxy interpretation. This note records the submitted algorithm before any alternative is judged.

## Submitted expanded-area chain

The submitted full-region file is `Data/tract_to_substation_mapping_CEC_expanded.csv`: **2,315 tracts, 92 station IDs, 7,791 positive tract–station rows**; SHA-256 `04b3f83a7be7a0a60fbfb6968b5bcee5a6e722722155f351712508f2c438fd93`. `Topology_and_Weight_expanded.py` passes the expanded input and output paths into `Topology_and_Weight.main`; it uses the same `topology_outputs.build_W_matrix`, `apply_min_weight_threshold`, and `export_mapping_from_W` functions. The non-expanded `Data/tract_to_substation_mapping_CEC.csv` is a different 1,108-tract/29-station output and is **not** the submitted full-region matrix.

1. The retained tract polygon is projected to EPSG:3310 and its **polygon centroid** becomes the tract access point.
2. The station geographically nearest that centroid is selected as the *single* access station using straight-line EPSG:3310 distance. There is no utility territory or ownership eligibility test in this choice.
3. A candidate station receives distance `d = tract-centroid-to-access-station Euclidean distance + shortest path from access station to candidate on the abstracted station/line graph`. Every station with a finite graph path can be a candidate; there is no fixed top-k candidate count. The shortest path uses graph edge distance, not road travel. This is a static network-distance proxy, not a feeder/customer connection or the dynamic source gate.
4. Raw weight is proportional to `1/max(d, 0.001 km)^2`, normalized within tract. If no network candidate is reachable, the code assigns weight 1 to the Euclidean-nearest station.
5. Weights below **0.03** are removed and each row is renormalized. If the threshold removes all candidates, the highest pre-threshold candidate becomes one-hot.
6. Export emits positive weights above `1e-6`. Its separate “smart injection” path may add a station judged missing from the export chain to the nearest tract, with a voltage-dependent proxy weight, then renormalize. A station merely suppressed by the 0.03 threshold is not reinjected.

Relevant implementation: `Topology_and_Weight.py` configuration and main call; `Topology_and_Weight_expanded.py` expanded paths; `topology_outputs.py:build_W_matrix`, `apply_min_weight_threshold`, and `export_mapping_from_W`. The separate `IDW.py` interpolates **hazard PGA** onto stations and is not the tract dependency weighting algorithm.

## Scientific interpretation

The July matrix gives a normalized **tract–station dependency proxy**. Its single nearest access station, unconstrained cross-utility candidate pool, graph reachability, 0.03 cutoff, and occasional export injection are assumptions. A row sum of 1 does not validate load share, customer assignment, outage propagation, or actual delivered electricity. Changing only the cutoff cannot test the more consequential utility-eligibility and access-path assumptions.

The later retained R1-310 closure matrix is a separate **2,315×310** static reference, not the July 92-station result. It is labelled `M0_R1_310` in the accompanying benchmark so that mapping alternatives can be compared on the same saved 310-station upstream trajectories. Comparing `M0_July_92` directly with those trajectories would confound mapping with station inventory and is therefore not used for outcome remapping.
