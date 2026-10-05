# SCE capacity geography review

Author authorized the S8 update on 4 October 2026. The original full-study figure and caption are preserved in provenance.

## Exact domains and estimand

- Primary: frozen utility_domain = SCE, and positive original mapping weight to at least one of the fixed 19 one-to-one SCE stations.
- Local binding: positive integrated OLINDA capacity increment in at least one of the 1,000 saved realizations of any of the four reported policies. Numerical tolerance is 1e-12 h. This set is recomputed, not imported from the old count; all four policies yield the same set.
- Diagnostic: any positive dependency on the 19 stations, irrespective of utility classification. Public-record overlaps use the exact 337-tract set, independently checked against strict-SCE tracts with represented direct candidates.
- Full 2,315-tract domain is provenance only; it is not the manuscript-facing SCE estimate.

For tract r and realization n, the increment is the 0–480 h left-rectangle event integral of the original weighted station-service difference. Domain means use sum(P_r × increment_r) / sum(P_r) over that domain. Original tract weights are neither renormalized nor reassigned. Unsupported station contributions remain identical and cancel. All station trajectories are identified in TRAJECTORY_SOURCE_HASHES.csv. The saved offline tract arrays are aligned by the historical GIS tract order before comparison with the original mapping CSV; this is an ID-order alignment, not a new mapping.

## Domain audit

|Domain|Tracts|Population|Overlap with 337|
|---|---:|---:|---:|
|strict_sce_supported|676|2,971,782|268|
|local_olinda_binding|25|117,102|8|
|any_supported_diagnostic|932|3,999,710|268|
|full_2315_provenance|2315|9,066,522|337|

## Population-weighted service loss

|Domain|Policy|Baseline (h)|Capacity-bounded (h)|Change (h)|
|---|---|---:|---:|---:|
|strict_sce_supported|hospital-first|29.951966|30.323826|0.371859|
|strict_sce_supported|impact-first|29.638510|30.009115|0.370605|
|strict_sce_supported|degree-first|30.047988|30.431092|0.383104|
|strict_sce_supported|vulnerability-first|31.163334|31.529765|0.366431|
|local_olinda_binding|hospital-first|35.575884|45.012830|9.436946|
|local_olinda_binding|impact-first|36.031208|45.436317|9.405109|
|local_olinda_binding|degree-first|33.736291|43.458597|9.722306|
|local_olinda_binding|vulnerability-first|40.783850|50.083023|9.299173|
|any_supported_diagnostic|hospital-first|31.153929|31.430220|0.276291|
|any_supported_diagnostic|impact-first|30.443673|30.719032|0.275359|
|any_supported_diagnostic|degree-first|30.916437|31.201083|0.284646|
|any_supported_diagnostic|vulnerability-first|32.206990|32.479247|0.272258|
|full_2315_provenance|hospital-first|34.306465|34.428352|0.121886|
|full_2315_provenance|impact-first|33.593686|33.715162|0.121475|
|full_2315_provenance|degree-first|35.707709|35.833281|0.125572|
|full_2315_provenance|vulnerability-first|34.257849|34.377956|0.120107|

## Policy contrasts relative to Hospital-first

|Domain|Policy|Baseline (h)|Capacity-bounded (h)|Change (h)|Sign flipped?|
|---|---|---:|---:|---:|---|
|strict_sce_supported|impact-first|-0.313456|-0.314710|-0.001255|False|
|strict_sce_supported|degree-first|+0.096022|+0.107266|+0.011245|False|
|strict_sce_supported|vulnerability-first|+1.211368|+1.205939|-0.005429|False|
|local_olinda_binding|impact-first|+0.455323|+0.423486|-0.031837|False|
|local_olinda_binding|degree-first|-1.839593|-1.554233|+0.285360|False|
|local_olinda_binding|vulnerability-first|+5.207966|+5.070192|-0.137773|False|
|any_supported_diagnostic|impact-first|-0.710256|-0.711188|-0.000932|False|
|any_supported_diagnostic|degree-first|-0.237492|-0.229137|+0.008355|False|
|any_supported_diagnostic|vulnerability-first|+1.053061|+1.049027|-0.004034|False|
|full_2315_provenance|impact-first|-0.712779|-0.713190|-0.000411|False|
|full_2315_provenance|degree-first|+1.401244|+1.404930|+0.003686|False|
|full_2315_provenance|vulnerability-first|-0.048616|-0.050395|-0.001779|False|

**The old about-0.12-h statement does not survive on the primary domain:** the four policies span 0.366431–0.383104 h.

The corrected S8B review candidate shows domain population-weighted mean increments (points) and 5th–95th realization ranges (lines), not confidence intervals. Both axes start at zero; their hour scales differ because the two domain averages have different magnitudes. Forecast planning ceilings are not earthquake-time flow observations or full-network electrical adequacy.

TRACT_LEVEL_CHANGES.csv gives each tract's mean increment, realization quantiles and positive-increment frequency. TRACT_CHANGE_DISTRIBUTIONS.csv gives unweighted quantiles of tract means; these are not realization ranges and are not population-weighted percentiles. POLICY_DOMAIN_REALIZATIONS.csv supplies all 1,000 domain results per policy for independent checking.

Only OLINDA 66/12 is binding-capable under the existing provider values. Its original forecast demand and planning limit are retained; other supported factors equal one. Existing numerical source files and trajectories are unchanged. Current S8 artwork and its caption were updated on author instruction; the previous versions are archived.
