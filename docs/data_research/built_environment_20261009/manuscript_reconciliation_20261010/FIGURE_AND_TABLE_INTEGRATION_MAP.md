# Figure And Table Integration Map

Authority: author-confirmed S19. This map distinguishes the actual six-figure manuscript, July legacy figures, and later planning identifiers. Review-copy numbering is local to this integration round and is not formal promotion. The final journal has not been confirmed.

## Actual Working Manuscript

| Existing item and exact caption | Information | Validity and decision | Review identifier and source | References affected |
| --- | --- | --- | --- | --- |
| Figure 1, S19 P0104: Modeled 2pc50 population availability trajectories under retained restoration sequences. Formal 1,000-realization output. | Recovery policy curves | KEEP; independent of Stage7 membership. Do not regenerate. | Figure1; original DOCX media payload and caption unchanged | Existing citations remain unchanged |
| Figure 2, P0106: Spatial variation in modeled tract T80 for the formal 2pc50 analysis. Values are service-availability proxy crossings. | Formal tract recovery | KEEP; no relabeling as new classes | Figure2; original payload/caption unchanged | Existing citations unchanged |
| Figure 3, P0108: Aggregate population burden versus Q4 absolute burden across hazards and selected strategies. | Population/Q4 policy tradeoff | KEEP; SOVI quartiles, not clusters | Figure3; original payload/caption unchanged | Existing citations unchanged |
| Figure 4, P0110: Q1-Q4 absolute modeled burden for 2pc50/C57 with paired-realization uncertainty. | Quartile burdens/uncertainty | KEEP; independent policy analysis | Figure4; original payload/caption unchanged | Existing citations unchanged |
| Figure 5, P0112: Paired-mean tract changes under vulnerability-first relative to hospital-first and impact-first. | Policy effects at fixed tract identities | KEEP; no new hotspot index | Figure5; original payload/caption unchanged | Existing citations unchanged |
| Figure 6, P0114: 2pc50 one-factor-at-a-time resource contrasts for population and Q4 burden. | Crew/duration sensitivity | KEEP; no Stage7 rerun | Figure6; original payload/caption unchanged | Existing citations unchanged |
| Table1, body block27, header Module / Revision baseline / Predeclared contrast / Interpretation | Formal experimental design | KEEP; no member-label dependency | Table1; original table XML unchanged | Section2.6 unchanged |
| Table2, hazard / self / threshold / source path / total / source share | Exact formal loss decomposition | KEEP | Table2; original XML unchanged | Formal mechanism Results unchanged |
| Table3, strategy / population burden / T80 / hospital / Q1 / Q4 / gap / Gini | Formal policy statistics | KEEP; cluster replacement does not change Q4 | Table3; original XML unchanged | Existing references unchanged |

The actual S19 contains no embedded Stage7 figure to replace. Thus two main figures are added at the end of its existing Figures section, retaining Figures1-6 and Tables1-3. Section3.4's Stage7 result paragraphs introduce Figures7-8 and Table4. No unrelated later numbering is shifted.

## New Main Figures And Table

**Figure7, spatial typology map.** Exact frozen source: `../manuscript_integration_preview_20261010/FIG_STAGE7_TYPOLOGY_MAP.pdf`. Review-only derivative: `FIG_STAGE7_TYPOLOGY_MAP_REVIEW.pdf` and its raster for Word. One inaccurate legend text operator is removed and replaced with 'Outside cohort (24 tracts)'. Geometry, class memberships, colors, all other text and vector paths are retained. The frozen preview remains unchanged. The original 'No residents' phrase is contradicted by 16,979 mapped residents outside the retained typology cohort; no eligibility rule or population estimate was changed to hide that conflict.

Caption: Four-class joint typology of 2,287 complete residential tracts under 2pc50, the reference 57-crew/unit-duration condition and direct-community recovery sequence. Five equal analytical domains define the classification; C1-C4 denote saved seed42 memberships, not a ranking. Four unresolved residential geometries are gray/unclassified and 24 outside-cohort tracts are white. Archived tract boundaries cover the exact 2,315-tract model domain in EPSG:3310; the study union is not a utility service boundary. This descriptive spatial classification is not a causal estimate or intervention priority.

**Figure8, joint cluster profile.** Exact unchanged PDF: `../manuscript_integration_preview_20261010/FIG_STAGE7_CLUSTER_PROFILE.pdf`; unchanged preview PNG embedded in Word.

Caption: Equal-tract mean coordinate z scores on the 2,287 classified tracts, grouped into five domains. These are unweighted visual coordinates, not the sqrt-domain-weighted fit coordinates. Color saturates outside +/-1.5, but actual annotations retain C2's initial-service value of +7.15. Building stock is log1p-transformed; standardized colors are not hours, fractions or dollars. Original-unit profiles and coverage are in Table4 and the companion profile files; T80 and population density are outside the primary coordinate space.

**Table4, panels A/B.** Source: frozen `STAGE7_CLUSTER_PROFILES.csv`; detailed companion `STAGE7_CLUSTER_PROFILES_LONG.csv`. Panel A gives counts, population totals, equal-tract mean B/T80 and initial availability percentages. Panel B gives SOVI/entropy/roof/observed-age means, building-stock medians in million2022USD, and ALR medians. No aggregation weight is silently changed. Display rounding and full precision are both checked. Replaces the old 11-feature description only conceptually; no existing S19 table is removed.

**Figure S_STAGE7, saved spatial robustness.** Exact unchanged source: `../manuscript_integration_preview_20261010/FIG_STAGE7_SPATIAL_ROBUSTNESS.pdf`. Supplementary placement. Caption and panel definitions are in REVISED_STAGE7_SUPPLEMENTARY.md. Main Section3.4 cites the temporary S_STAGE7 identifier explicitly. This temporary identifier avoids silently colliding with legacy S6/S7 or a plan's S09. The author must reconcile final supplementary numbers before submission.

## Legacy And Plan Dependencies

- S13 P0372 and equivalent S22 Figure6: five-class profiles/map and cluster-specific hotspot/centrality panels. REPLACE the typology/profile panels with the new map/profile if the July manuscript is ever reactivated; REMOVE obsolete hotspot-by-cluster panels pending separate revalidation. In current S19, Figure6 is a different resource figure and must not be replaced.
- S13 Table3 / Table4 extraction: old 11-coordinate schema, NRI_RISK_SCORE, ACS age/density and unweighted transforms. REPLACE schema with the frozen twelve-coordinate/five-domain definition. Do not treat old table numbers as S19's actual Table3.
- S13 P0291: old supplementary PCA/scree/elbow FiguresS10/S11. REMOVE their claimed role in the primary D partition; MOVE historically useful diagnostics to a clearly labeled old-model comparison only after supplementary reconciliation. No new PCA fit or primary PCA claim.
- S13 Figure1 workflow (P0367): REVISE only its Stage7/hotspot label if the legacy workflow is reused; not a request to regenerate independent recovery panels.
- S15 P0011 and P0013: two distinct FigureS6 captions. VERIFY separately; no automatic global renumbering. SVI-weighted curves are not SOVI class summaries.
- S35/S37 planned Fig07 and FigS09: plans, not authoritative installed figures. New review numbering7/8 is justified by S19's actual six figures, not by inheriting plan identities.
- Old five-class colors/names must not appear on new four-class membership. Main map uses saved C1 blue #0072B2, C2 amber #E69F00, C3 green #009E73, C4 vermilion #D55E00. Profile columns use these same identifiers without implying ordinal ranking. Spatial FigureC's blue/orange represent original/additional membership, with a distinct explicit legend.

## Actual Rendering Checks

All three original PDF pages were rendered with PDFium at 185-mm native width and 178-mm provisional two-column width. Actual page images were opened and inspected: no clipped axes/legends or overlapping profile/domain labels; C2 +7.15 remains legible. The review Word's existing usable width is172.72mm (6.8in); new figures are rendered inside that width and independently checked on actual exported pages. This is not a confirmed journal column specification. Original fonts and figure payloads are retained except the one review-only map text correction. Numeric/profile saturation and full-unit tables are mandatory together.

Figure rendering measurements, original hashes, manual notes, and document pagination are recorded in FIGURE_RENDER_QA.json, FIGURE_LEGEND_CORRECTION.json, DOCUMENT_RENDER_QA.json and DOCUMENT_STRUCTURE_QA.json. Script success and file existence are not substituted for visual review. Final supplementary numbering and target-journal dimensions remain editorial gates.
