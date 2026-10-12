# Frozen network/source explanation of the 34 tracts

**AUTHOR REVIEW - NOT FORMAL STAGE 7.**

## Direct answer

The group has a demonstrable **model-internal** explanation: every tract's highest-weight station and largest initial-service contributor is **308581, STATION Q (HARBOR)**, a LADWP 138-kV station retained as a **Core `in_basin_generation_proxy`**. Mean dependency weight on Q is 0.720127 (range 0.414532-1.000000). Q supplies 97.1891% of the sum of their mean initial service; this is a service-contribution ratio, not electrical capacity or a power-flow allocation. Other aggregate contributions are Wilmington 1.8514%, Harbor Gen 0.7773% and Dock 0.1822%.

The frozen rule is F=1[f>=0.5], C=source connectivity within the F-eligible subgraph, and e=f*F*C. Q is itself a retained Core source. For its 40 eligible samples the saved path certificate is zero-hop, not proof that a remote supply corridor survived. The rare advantage is therefore the interaction of Q's **frozen sampled damage frequency**, its **assumed Core role**, and tract mapping. Less frequent severe damage alone does not explain the result.

## Realization-level evidence

Q's DS counts in 1,000 existing samples are [9,31,78,510,372] for DS0-DS4. The authenticated formal initial lookup is [1,0.5,0.09,0.04,0.03]; no legacy alternative lookup is substituted. Q reaches 0.5 in 40/1,000 samples, remains connected in all 40, and mean e is (9+31*0.5)/1,000=0.0245. Its raw mean f is 0.06308. Dock has a slightly larger raw mean (0.06356) but only 2/37 eligible samples are source-connected, so mean e is 0.001. Wilmington has 3/25 eligible samples source-connected and mean e 0.002. This contrast shows why raw station survival alone is insufficient.

Each rare tract's realization median initial service is **zero**. Positive-service frequency ranges from 4.0% to 5.7% (mean 4.35%). Across the entire station system, only 114 of the 1,000 samples have any positive initial effective service. The group's mean tract availability of 0.018153 is a rare-event average; it does not mean every sample retains 1.8153% service, and is very low absolutely.

## Exact station and mapping audit

The 34 exact eleven-digit GEOIDs are in `THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv`. Their assigned positive-weight station count is 1-7 (median 3); average HHI is 0.581765 and average weighted spectral impact 0.028704. Mapping sums are one. Every tract-station weight and contribution is in `THIRTYFOUR_TRACT_STATION_DEPENDENCY.csv`; each contribution is W_ri * mean(e_i(0)). All 2,299 Init_Supply values reproject from saved station e(0) with maximum absolute error 2.985e-16.

The same mechanism is continuous outside the rare cluster. Higher initial service increases with weight on Q, with other Core stations also contributing to some tracts. It is not a unique binary physical class; the K-means boundary partitions this continuous mapping/source outcome. `STATION_CONTRIBUTIONS_RARE_AND_OTHER_TRACTS.csv` records cohort and outside-group contributions, rather than assuming only these 34 receive Q service.

Frozen mean B decomposition for the rare group is 22.5303 h own-functionality loss + 0.8038 h threshold loss + 0.2670 h source-disconnection loss = 23.6011 h. The cohort's mean source-disconnection component is 4.3185 h. This is consistent with the retained source role and lower cumulative loss, but shares the simulation inputs and is not independent causal validation. Delta B is 2.1437 h, close to cohort mean 2.2877 h; the group is not uniquely insensitive to logistics.

## Identity and geography

The exact same 34 occur in A and B at k4 and k5 for all five registered seeds. All 23 top-1%-Init observations are among them. None of the eight added zero-housing positive-population tracts joins the group. Their total population is 124,158 (1.3694% of cohort population), Q4 membership is 13/34, and mean/median SOVI is 67.99/85.04; they are not uniformly low-vulnerability communities.

Official internal points occupy latitude 33.710708-33.790275 and longitude -118.329404 to -118.254908; P90 radius from the median point is 4.82 km. Three of four existing geographic perturbations preserve the exact group. With the southwest quadrant removed from training, A/k4 predicts a larger 207-tract class containing all 34 plus 173 others (Jaccard 0.1643); B/k4 predicts 211. A/k5 and B/k5 similarly merge into 206/210 tracts. All members survive that matching, but **the exact class does not**. Saved IDs and added/lost sets are explicit in the identity CSV. No new geographic fits were performed.

## Limits

The frozen Core assignment is a supply proxy, not independently verified islanding/generation availability. No alternate Core assignment, fragility, new damage sample, source propagation or power-flow test was run. Positive saved reachability is checked with functional-path certificates; the audit does not rebuild all negative reachability states. These results establish a specific model mechanism, not customer outage, feeder adequacy, electricity capacity, or real-world resilience. Original population upstream Census vintage remains unresolved even though frozen values are authenticated. Official points support locations and coarse quadrants, not municipal/neighborhood identification or contiguous class areas.
