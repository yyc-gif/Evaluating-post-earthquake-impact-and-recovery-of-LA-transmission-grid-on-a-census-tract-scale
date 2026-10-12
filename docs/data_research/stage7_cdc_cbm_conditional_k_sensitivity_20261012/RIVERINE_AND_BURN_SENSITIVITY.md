# Riverine, burned-area, heat and wildfire sensitivity
EXPLORATORY AUTHOR REVIEW — NOT FORMAL STAGE 7

Riverine contributes69.248% of local SPL covariance variance, heat12.215%, wildfire10.310%, coastal8.106%. These are local covariance shares, not declared policy weights or causal hazard shares. The binary riverine-support split explains 84.33% of official local CBM rank variance. Heat changes fine ordering substantially: removing heat retains only51.74% of top230, versus53.48% after riverine removal. Burn removal retains95.22%; wildfire-domain removal90.87%.

Bounded component fits use H1/H2 K3/4/5 and seeds42-46. Those Ks are the predeclared continuity range plus all main endpoint bends/silhouette maxima; no additional K is needed. Each counterfactual is standardized on the unchanged2,299 cohort; other coordinates are unchanged.

| specification   | alternative           |   k |   minimum_ARI |   mean_ARI |   maximum_ARI |   mean_reassigned_tracts |   mean_reassigned_population_share |
|:----------------|:----------------------|----:|--------------:|-----------:|--------------:|-------------------------:|-----------------------------------:|
| H1              | component_no_burn     |   3 |        0.9915 |     0.9932 |        0.9943 |                   4.8000 |                             0.0019 |
| H1              | component_no_burn     |   4 |        0.9820 |     0.9872 |        0.9903 |                  10.0000 |                             0.0047 |
| H1              | component_no_burn     |   5 |        0.9514 |     0.9578 |        0.9630 |                  42.4000 |                             0.0171 |
| H1              | component_no_heat     |   3 |        0.9547 |     0.9553 |        0.9576 |                  38.6000 |                             0.0181 |
| H1              | component_no_heat     |   4 |        0.9689 |     0.9705 |        0.9730 |                  23.6000 |                             0.0084 |
| H1              | component_no_heat     |   5 |        0.9162 |     0.9243 |        0.9321 |                  69.4000 |                             0.0310 |
| H1              | component_no_riverine |   3 |        0.9254 |     0.9260 |        0.9282 |                  56.6000 |                             0.0273 |
| H1              | component_no_riverine |   4 |        0.8818 |     0.8852 |        0.8959 |                  95.0000 |                             0.0436 |
| H1              | component_no_riverine |   5 |        0.8524 |     0.8552 |        0.8575 |                 135.4000 |                             0.0620 |
| H1              | component_no_wildfire |   3 |        0.9824 |     0.9844 |        0.9852 |                  11.6000 |                             0.0053 |
| H1              | component_no_wildfire |   4 |        0.9710 |     0.9746 |        0.9765 |                  20.0000 |                             0.0096 |
| H1              | component_no_wildfire |   5 |        0.9430 |     0.9461 |        0.9483 |                  56.4000 |                             0.0233 |
| H2              | component_no_burn     |   3 |        0.9900 |     0.9945 |        0.9956 |                   4.0000 |                             0.0015 |
| H2              | component_no_burn     |   4 |        0.9796 |     0.9867 |        0.9904 |                   9.6000 |                             0.0039 |
| H2              | component_no_burn     |   5 |        0.9830 |     0.9868 |        0.9898 |                  10.4000 |                             0.0041 |
| H2              | component_no_heat     |   3 |        0.9789 |     0.9817 |        0.9864 |                  13.8000 |                             0.0066 |
| H2              | component_no_heat     |   4 |        0.9894 |     0.9910 |        0.9921 |                   6.8000 |                             0.0041 |
| H2              | component_no_heat     |   5 |        0.9643 |     0.9686 |        0.9744 |                  27.2000 |                             0.0132 |
| H2              | component_no_riverine |   3 |        0.9262 |     0.9262 |        0.9262 |                  55.0000 |                             0.0264 |
| H2              | component_no_riverine |   4 |        0.9495 |     0.9507 |        0.9521 |                  40.0000 |                             0.0199 |
| H2              | component_no_riverine |   5 |        0.9120 |     0.9273 |        0.9388 |                  71.2000 |                             0.0306 |
| H2              | component_no_wildfire |   3 |        0.9808 |     0.9819 |        0.9821 |                  13.2000 |                             0.0050 |
| H2              | component_no_wildfire |   4 |        0.9699 |     0.9709 |        0.9725 |                  21.2000 |                             0.0085 |
| H2              | component_no_wildfire |   5 |        0.9066 |     0.9325 |        0.9635 |                  63.4000 |                             0.0247 |

Riverine removal has the largest membership effect, particularly H1/K5 (mean ARI0.855;6.20% of resident population reassigned). Nevertheless, K3–K5 retain broadly similar recovery/dependency contrasts rather than losing an exclusively flood-defined regional class. Burn removal gives ARI0.951–0.996 across these fits: the unresolved component is not driving the regional partition. This does not validate its zeros or restore the source-quality gate.

Heat/wildfire influence individual ranks and selected memberships but do not create stable stand-alone climate classes in the credible K3–K5 range. A modest clustering effect alongside a large top-rank change is expected when the climate coordinate provides only a small share of realized between-class separation. These are distance-geometry findings, not estimates of real multi-hazard outage consequences.
