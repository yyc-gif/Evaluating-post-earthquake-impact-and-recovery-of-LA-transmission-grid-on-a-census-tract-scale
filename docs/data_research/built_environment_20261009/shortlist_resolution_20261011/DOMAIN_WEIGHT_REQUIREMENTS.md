# Domain-weight decision required after measurement selection

Preferred physical variables: EMC2022 occupancy, ACS5+ residential configuration, SCAG2020 classified-parcel composition. These are three constructs and have different populations/support. They must not be called interchangeable density indicators. Age is not a preferred primary construct with the current sources.

Retained coordinates: B_480_hr and Init_Supply; unchanged grid degree/impact/betweenness/HHI; SOVI; log building stock; unadjusted multi-hazard ALR. Stock measures amount of monetary assets, ALR measures loss propensity after exposure normalization and component aggregation. Neither is pure hazard or interchangeable with physical coverage.

The unresolved decisions are:
1. Whether the three physical constructs intentionally share one parent-domain budget or receive distinct construct budgets.
2. Whether monetary stock and expected-loss propensity intentionally share a parent budget or have separate exposure/loss budgets.
3. The declared total budgets for recovery/initial service, grid dependence and mandatory social vulnerability relative to those domains.
4. If a separately justified hardening/height extension is considered later, whether its budget is taken from physical form or is additional at the expense of explicitly named domains. It must not gain weight merely by adding columns.

This round used only an equal-five-parent benchmark: 0.2 each for recovery/service,grid,physical,social,stock/loss. Within each, standardized coordinates share squared-distance weight. CORE2 receives 0.1 per physical coordinate, CORE3 receives 0.0666666667, CORE4/age/optional four-coordinate variants 0.05. B and Init receive 0.1 each, grid 0.05 each, SOVI 0.2, stock and ALR0.1 each. Standardized values are multiplied by the square root of these weights. DOMAIN_COORDINATE_CONTRIBUTIONS.csv reports actual coefficients and observed separation contributions separately.

The added-variable comparisons therefore combine a new measurement with a declared redistribution of the unchanged physical budget. They are not zero-cost incremental additions and not pure feature effects at fixed individual-coordinate weights. No second weight scheme, interpolation, optimization, PCA or k sweep was executed. Five historical domains each 20% are not selected as the final scientific hierarchy.

The next study must preregister hierarchy/budgets from the intended representation, keep this measurement set and common GEOIDs fixed, and distinguish content from weighting. Do not tune budgets for silhouette, old-label agreement, preserving the 34-member class or making four groups look clean. This package gives a measurement selection now; it does not leave the candidate pool open indefinitely.
