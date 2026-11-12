# Scientific and publication review

Starting authority: `96367fe564e065933e828d82afd2b5a8909b84e5`, branch `review/fig1-moduleD-s5-final-20261109`. Active collection: `results/figure_review_s6_main4_20261107/`, eight main plus eight supplementary figures. Former S6 is main Figure 4; subsequent numbering is preserved. Every individual PDF-derived preview was inspected, not only a contact sheet.

## Scientific narrative and implemented decisions

| Figure | Scientific purpose and actual authority | Review decision |
|---|---|---|
| 1 | Mapping, sampled damage, event-based repair, source gating and community outcomes; scheduler, GA and gate implementations plus archived priority order and events | Replace arbitrary workers/station icon/tract tiles with three real archived states. Retain five crew histories and map. Link Crew 5's highlighted task end to delayed source connection. Concise shared caption; no recovery-result curves in Stage 4. |
| 2 | Abstract transmission graph and utility-compatible tract dependencies; CEC geometry and public SCE assignment comparison | Retain. Maps and comparison have distinct purposes; assignment agreement is not electrical validation. |
| 3 | Damage/initial service across hazards and Unconstrained loss/T80; frozen station means, gate components and recovery summaries | Retain artwork. Independently match all eight PDF whisker endpoints to the four frozen 92-station/1,000-realization archives: endpoints are observations within 5th-95th station-mean percentiles (maximum error below 0.000001 damage-state units). Correct caption statistical units; these are not realization intervals or 1.5-IQR whiskers. |
| 4 | Dynamic full-network versus fixed-path connectivity and conditional station diagnostics | Retain all four panels. Static conditional station probabilities are not dynamic service probabilities; caption explicitly separates them. Symbols, routes, and Core sources are traceable to retained graph and source-reliability tables. |
| 5 | Absolute restoration-strategy performance; frozen paired policy trajectories and outcomes | Retain. Different loss populations and T80 use separate axes; ranges describe realizations, not uncertainty in the mean. Unconstrained remains an idealized reference. |
| 6 | Vulnerability targeting, distributional trade-offs and paired tract differences | Remove redundant unanchored Vulnerability-first annotation in A; keep the strategy legend. Preserve signed and absolute gap rows separately. All non-text vectors, uncertainty bars, maps and data remain identical. |
| 7 | Resource dependence of paired Vulnerability-first effects | Label third-row quantity explicitly as absolute Q4-Q1 service-loss gap; center the complete composition by translation. Retain bootstrap intervals and means-only exception; these are not realization ranges. |
| 8 | Descriptive seven-variable community types and direct continuous burden/vulnerability geography | Retain artwork and all memberships. Caption identifies screen outlines in both C and D, ordinary cohort-z means, fitted log population and ECDF median markers. Remove internal P2 naming and unnecessary prevalence results from caption. Not external cluster validation or significant hotspot detection. |
| S1 | Detailed station-damage distributions and four-scenario initial-service maps | Retain. Means across simulations are continuous, so violin distributions of station means are not smoothed categorical damage states. Adds geography absent from main Figure 3B. |
| S2 | Crew origins and directed task-to-task travel inputs | Center the complete vector composition without scaling. Inputs are not damaged-road forecasts; matrix is an overview, not a station-name lookup table. |
| S3 | Time-dependent functional-network topology | Retain. Largest-component fraction and mean degree are not tract service. Similar curve shapes do not make this a delivered-electricity measure. |
| S4 | GA search and held-out simulation evaluation | Rename C to Held-out evaluation. Clarify within-model generalization, not independent empirical validation. Preserve every search point, realization result and component gap. |
| S5 | Mapping cutoff, source-only gating and functionality-threshold controls | Retain byte-identically, 185 x 145 mm, centered. Four matched strategies and paired realization ranges remain intact. |
| S6 | Provider facility planning loads and ceiling sensitivity in supported SCE geography | Retain artwork. Caption now identifies population-weighted means and paired 5th-95th realization bars from `review_sce_supported_geography.py`. This is not post-earthquake power flow. |
| S7 | Hospital, Q4 and population-based station-priority geography | Center the complete map/table/legend composition without scaling. Caption distinguishes binary hospital/Q4 layers from the population gradient and full priority order from damaged-task dispatch. Representative maps do not depict all strategies. |
| S8 | Absolute outcomes over resource conditions | Label absolute Q4-Q1 gap explicitly. Retain all strategies and ranges. Complements main Figure 7's paired effects, rather than serving as an independent experiment. |

Exact input commit/path/hash provenance is retained in the active `FIGURE_MANIFEST.csv`, `QA/SOURCE_IDENTITIES.json`, and the review's `EVENT_STATE_EXAMPLE.json`. `ARTWORK_METRICS.json` compares every PDF with the starting commit. Text-only corrections assert equality of every non-text vector signature before and after editing.

## The completion example

The first task of the first displayed crew is station 300558. At 18.154886173136717 h, raw functionality changes from 0.03 to 1.00 and Crew 5 starts its next dispatch. Source connectivity and effective availability remain zero. Source connectivity becomes available at 30.733697448399262 h. The example tract, 06037402301, is selected by maximum dependency weight then smallest GEOID; its station weight is exactly one. Its service therefore remains zero at repair completion, then becomes one at the later connection. These are archived scalar states, not fabricated map cells or a claim that this tract is typical. No source-gate, repair schedule or physical simulation is rerun.

## Manuscript alignment boundary

The locally available `Submission_Package/Manuscript_IJDRR.docx` is an older manuscript: it still discusses mean-duration scheduling, normal-CDF recovery, static percolation and the obsolete multifeature hotspot construct. Those statements contradict the current archived event-based methods and must not be used as authority for new artwork. It was read but not modified. The active suite's `MANUSCRIPT_INTEGRATION.md` establishes current Section 4.2/4.3 placement and simultaneous renumbering. A current author-controlled manuscript needs a coordinated text review before submission; artwork consistency alone cannot certify manuscript consistency.

Read-only manuscript identity: SHA256 `1863531334286c917a36b95075119fea0762e2edd07a7e06a2bccba4a0405107`, from the original project's `Submission_Package/Manuscript_IJDRR.docx` (not a newly tracked manuscript copy).

## Readiness

Artwork revisions are presentation-only. Existing simulations, GA results, cluster labels, quartiles, tract geometry and scientific arrays remain unchanged. Retained figures are not redesigned merely to impose identical layouts. The unresolved journal and manuscript gates are described separately; this review does not declare the entire submission compliant.

## Reproduction

```powershell
python src/la_grid/plotting/build_current_figures.py --portable
python src/la_grid/plotting/review_publication_suite.py
python -m pytest tests/test_s6_main4_promotion_20261107.py -q
```

`--historical-p2` explicitly selects the earlier seven-main/nine-supplement pathway. The direct workflow script no longer silently exports its historical card overview; that output requires `--legacy-card-overview`. Both production presentation paths share the current Stage 4 generator. Re-extracting the event example uses `review_publication_suite.py --extract-event` and requires the hash-bound original local archive; normal figure reproduction uses the committed, traceable excerpt and does not need to rerun or reconstruct the model.

The standalone Stage 4 renderer also reads its priority map from the same pinned, uncentered source commit as the canonical builder. It must not read the newly centered S7 publication output as a fixed-coordinate input crop. The integration test detected this feedback dependency; the default source was corrected, while the explicit production path and its plotted information remain unchanged.
