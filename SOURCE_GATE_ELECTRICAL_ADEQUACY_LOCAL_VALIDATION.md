# Source-gate electrical-adequacy local validation

## Direct findings

The retained project already contains more electrical evidence than a directory-only review suggested. Thirty-nine of the 92 retained stations have a conservative exact/strong named-facility identity match: 33 SCE stations in the GNA planning table and six LADWP stations in named public project/event records. Twenty-eight retained SCE stations have at least one 2026 voltage-level row with simultaneous provider fields for cumulative demand, facility load limit, facility loading and capacity margin. Those 28 stations contribute 34 Level-A facility rows. RS-Q adds one Level-B benchmark row because the provider project document explicitly identifies its existing capacity and congestion/capacity limitation, although it supplies no simultaneous demand. The resulting benchmark has 35 rows across 29 stations. Adelanto-Rinaldi supplies a meaningful line rating but no flow. No Core source has a verified time-specific generation/import availability bound.

One Level-A case is **topologically source-connected yet documented above its provider planning limit**: retained station 306279 OLINDA, facility `OLINDA 66/12`, planning year 2026. Its SCE GNA row reports `CUMULATIVE_DEMAND=28.45`, `FAC_LOAD_LIMIT=26.09`, `FACILITY_LOADING=109.04`, `DEFICIENCY=2.36`, and `SUBST_CAPACITY=-2.3600`. The project-calculated dimensionless ratio is 28.45/26.09 = 1.090456, consistent with 109.04% after provider rounding. RS-Q provides a separate Level-B case: the official project document says existing 160 MVA Rack B faces circuit-congestion and capacity limitations in supporting future Port load growth. Both show that binary reachability and electrical adequacy are different concepts. Neither is evidence of post-earthquake overload.

The result supports a bounded response to Reviewer 1 Comment 2: the production gate is a source-connected service-availability proxy. It screens out stations with no surviving modeled source path, but it does not verify power balance, equipment capacity, line loading, generation/import sufficiency, voltage feasibility or load shedding. The local evidence directly demonstrates that a facility can be reachable in the intact abstract topology while its provider planning row identifies loading above its facility limit.

A real earthquake-time adequacy calculation still requires a compatible case containing bus topology, branch endpoints, reactance/base and ratings, bus loads, generator/import bounds, operating status, and slack/boundary treatment. Those fields cannot be assembled defensibly by joining unrelated CEC, SCE, LADWP and EIA sources.

## SCE GNA verification

The retained raw acquisition is SCE ArcGIS FeatureServer service item `67ebc52767594428b808f44f8809355f`, table 5, `Substation Level Planning Assumptions`. It was retrieved 2026-09-23 from `https://drpep.sce.com/arcgis_server/rest/services/Hosted/GNA_Layer/FeatureServer/5`; the retained source date is 2026-08-27. The table contains 8,040 records. Its native fields include:

- `CUMULATIVE_DEMAND`
- `FAC_LOAD_LIMIT`
- `FACILITY_LOADING`
- `DEFICIENCY`
- `SUBST_CAPACITY`
- `FACILITY`, `SUBSTATION_NAME`, `YEAR_VALUE`, `GNA_ID`, `OBJECTID`

The layer metadata supplies field names and numeric/string types but no absolute unit aliases or data dictionary definitions. Therefore the crosswalk does not label 28.45 or 26.09 as MW or MVA. Their ratio is valid because the provider reports both for the same facility row and gives the corresponding percentage. `SUBST_CAPACITY` equals limit minus cumulative demand for OLINDA; `DEFICIENCY` is the positive shortfall. The record identifies a GNA planning assumption, not observed loading. The layer does not state whether `FAC_LOAD_LIMIT` is a base-condition, N-1, transformer-bank or another detailed constraint basis, so the benchmark retains the neutral phrase “provider-defined facility planning limit.”

The previously recorded counts reproduce from the actual table and matching file:

| Check | Reproduced value |
|---|---:|
| Matched July station names | 33 |
| Named voltage-level facilities in 2026 | 44 |
| 2026 rows with consistent demand, limit, loading and margin | 34 |
| Retained stations represented by those 34 rows | 28 |
| Provider-consistent rows above documented limit | 1 |

Seven of the remaining 2026 rows are absent/redacted for the required fields. Three more rows (COLORADO, GANESHA and REPETTO facilities) fail the retained numerical consistency tolerance between demand/limit and provider loading and are not promoted to Level A. The screening does not invent a threshold such as 80% or 90%; it uses only provider-defined within/above-limit status.

## Evidence levels

### Level A — same-facility demand and limit

The 34 SCE GNA rows in `CONNECTED_VS_ELECTRICAL_CONSTRAINT_BENCHMARK.csv` have the same named voltage-level facility, 2026 planning year, provider demand, facility limit, loading percentage and margin fields. They support a direct planning-condition comparison with intact-model source reachability. They do not calibrate post-earthquake service.

### Level B — rating without simultaneous demand

**RS-Q / Harbor.** The ZEPEO MND identifies RS-Q as a receiving station at Harbor Generating Station. Existing Rack B is described as 160 MVA and as facing limitations due to circuit congestion and capacity constraints; proposed Rack D is separately 160 MVA. The same project estimates an additional 200 MVA for Port electrification. The 200 MVA is an incremental project need, not an RS-Q present load or retained-node rating. Existing and proposed racks are not summed as current capacity. The explicit provider constraint statement supports a Level-B benchmark row, but the absence of simultaneous RS-Q demand prevents a loading ratio.

**Adelanto–Rinaldi.** The retained MND gives the existing Adelanto–Rinaldi 500 kV Line 1 rating as 1,593 A and proposed ratings as 1,680 A continuous and 1,965 A emergency. The evidence is a named line terminating at Rinaldi, not a station transformer limit. No contemporaneous line flow is provided. Amps are not converted to MW because a defensible conversion would require provider-defined voltage basis, power factor/phase convention and actual flow.

### Level C — context only

SCE ICA hosting/interconnection fields, LADWP 34.5 kV segment capacity bands and named project relationships are useful context. They are not earthquake-time deliverable MW, branch thermal limits, or station adequacy checks. Segment capacity is not summed into station capacity.

## Production-gate connection

The intact 92-node model marks every functional retained station source-connected. For the benchmark facilities this makes the network-side production gate equal to one whenever the station is functional. OLINDA demonstrates that this binary result can coexist with a provider planning row above its facility limit; RS-Q shows the same conceptual distinction through an explicit provider constraint statement without a calculable loading ratio. The attached `r_i`, `R_path_full` and `R_conn_full` columns describe 2pc50 fragility/connectivity reliability only. They are not multiplied by planning loading or interpreted as capacity.

The benchmark therefore validates an interpretation boundary rather than an earthquake operating result:

> Source reachability is a necessary topological availability condition in the model, not evidence of unconstrained electrical delivery. Public same-facility planning data include a retained, source-reachable facility with documented loading above its provider-defined limit.

## LADWP and DC-case status

The public LADWP files support strong named identities and isolated physical ratings. They do not provide simultaneous station loads, source P limits, a complete bus/branch case, or actual line flows. The Cheng et al. paper confirms that a utility-provided 432-bus/545-branch case with the required electrical quantities existed for the published analysis, but the retained paper, NSF record and author/publication pages do not provide its input tables or anonymized case.

The current determination is **facility-only electrical adequacy benchmark feasible**. The next highest-value acquisition is an anonymized Cheng/LADWP case or reduced validation subset. CAISO/WECC and FERC Form 715 are real access routes but require restricted-access approval and may not contain sufficient LADWP internal detail.

## Reproducibility and boundaries

`build_source_gate_electrical_benchmark.py` creates the 92-row crosswalk, the 34-row benchmark and coverage summary from retained files. It asserts the 92-station and 14-Core-source identities and does not read or write any damage, repair, schedule, GA, mapping or formal trajectory state. The July archive and production source gate are unchanged.

The separately supplied archive `source_gate_electrical_adequacy_research_partial_20260926(1).zip` was not present in the repository, Downloads folder or searched project roots. This is recorded as an unavailable input, not interpreted as evidence that the underlying sources do not exist. The retained external-data package already contains the Cheng paper, CAISO NDA instructions, WECC policy/catalog, FERC CEII forms and the SCE/LADWP raw evidence used here.
