# Stage 7 Results - Path B replacement draft

The three saved P2 classes represent contrasting combinations rather than a hierarchy of resilience or total risk. C1 comprises 1,235 tracts and 5,184,036 residents; C2 comprises 428 tracts and 1,695,501 residents; C3 comprises 636 tracts and 2,186,985 residents. Display IDs are specific to P2 and are not the previous NCV14/H2 class memberships.

C1 has relatively high mean SOVI (78.92 versus cohort 66.51), low spectral impact and smaller additional constraint deficit (1.75 h). C2 combines relatively lower Unconstrained deficit (27.80 h) with the greatest mean added constraint burden (7.10 h). C3 has greater spectral impact and Unconstrained deficit (37.20 h), with intermediate additional burden (3.97 h). HHI distributions substantially overlap; not every retained construct separates every class. These profiles describe the frozen earthquake-conditioned network and policy design, not causal neighborhood characteristics or actual delivered electricity.

| class_id   |   Init_Supply |   Grid_Impact |   Redundancy_HHI |   B_Unconstrained |   MeanDelta |   SOVI_SCORE |   Population |
|:-----------|--------------:|--------------:|-----------------:|------------------:|------------:|-------------:|-------------:|
| C1         |        0.0003 |        0.0086 |           0.6456 |           30.0557 |      1.7542 |      78.9205 |    4197.6000 |
| C2         |        0.0023 |        0.1197 |           0.6250 |           27.7961 |      7.1031 |      48.3082 |    3961.4509 |
| C3         |        0.0001 |        0.3084 |           0.6391 |           37.2000 |      3.9693 |      54.6536 |    3438.6557 |

| class_id   |   tracts |   population |   hospital_linked_tracts |   Q1 |   Q2 |   Q3 |   Q4 |
|:-----------|---------:|-------------:|-------------------------:|-----:|-----:|-----:|-----:|
| C1         |     1235 |      5184036 |                       65 |   84 |  303 |  419 |  429 |
| C2         |      428 |      1695501 |                       13 |  220 |  105 |   53 |   50 |
| C3         |      636 |      2186985 |                       25 |  274 |  158 |  104 |  100 |

K3 mean silhouette is approximately 0.2487; K4 is approximately 0.2530 and K5 approximately 0.2633. The smooth endpoint-chord inertia diagnostic favors K3, but does not establish a unique optimum. K4 isolates a 37-tract source-proxy-conditioned class, while K5 can isolate twelve very-low-population tracts. K3 retains broad recovery/vulnerability contrasts without presenting the source-proxy state as a separate universal community type. K4 is nevertheless more geographically stable: median full-cohort leave-out ARI is 0.8613 versus 0.7610 for K3, and the minimum held-out ARI is 0.8057 versus 0.4189. The author accepts K3 conditionally for broad interpretation, with this K4 advantage retained in supplementary sensitivity evidence. These coarse geographic checks are not independent spatial validation. Removing initial availability also redistributes RQ1 weights and materially changes the partition.

The Figure 7D direct screen reproduces 94 Q4/high-deficit tracts and 350,799 represented residents at P75=38.38135467381475 h. The global tract-level high-deficit prevalence is lower in Q4 (16.23%) than non-Q4 (27.97%), not evidence of positive regional concentration. The pattern remains negative after removing Vulnerability-first, but is weaker and substantially reduced or reversed in geographic common-support descriptions. This conditional spatial result should not be promoted to a causal equity benefit. These numerical details belong in Results or supplemental analysis, not the short figure caption.
