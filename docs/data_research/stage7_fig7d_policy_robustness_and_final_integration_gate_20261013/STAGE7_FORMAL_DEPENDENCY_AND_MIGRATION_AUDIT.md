> AUTHOR REVIEW - NOT FORMAL STAGE 7

# Formal dependency audit: replacing one PDF is insufficient

Exact committed code/caption snapshots and line references are under evidence/ and FORMAL_DEPENDENCY_MATCHES.csv. FORMAL_PROMOTION_PATH_REGISTRY.csv gives planned paths/actions, separates new versioned authority from active readers/artwork and from immutable history. The new source schema is not compatible with the current production reader by merely copying a PDF.

Critical blockers for a future promotion:
1. The legacy verifier requires(2315,2291,24) and residential status. New version requires(2315,2299,16) and positive frozen population; the original verifier must remain valid for its historical authority.
2. The old core run_stage_7 loads housing, CDC population density, NRI risk/building value, constructs old hotspot/PCA coordinates and chooses clusters. Invoking it would not reproduce NCV14/H2/savedK3. A versioned saved-authority loader and explicit routing are required; no silent replacement of old fit behavior.
3. Project_Visualizer/composite and suite refreshers expect oldPC/loadings, six descriptive profile fields and SlowVulnerable_Hotspot_Score/Top10. D3 must read exact five-policy total deficit and frozen Q4, not invent compatibility score columns.
4. refine_policy_cluster_presentation.py has CLUSTER_OLD/NEW arrays of length5 and asserts all five colors were found. It would fail or mispaint a three-class figure. New registry colors are C1#147f98,C2#d07734,C3#7a5899; K4 sensitivity has a separate registry. Do not relabel old IDs as new IDs.
5. Stage08 resume manifests, code authority, figure manifests/indexes and assembled caption collections must update together afterapproval. Historical execution identities and archives must not be rewritten.
6. The current editable manuscript is not identifiable from the pinned repository: tracked DOCX files are older review/meeting/legacy documents; the previously mentioned Downloads path is absent. No arbitrary archived DOCX is chosen for futurewrite. Author must name the active manuscript andsupplementtargets.

The relevant current formal caption uses five classes/2291 residential tracts and PC5/eigenvalue rules. These statements must be replaced only in the active Stage 7 Methods/Results/F7/S9/supplement, not globally in historical audit reports. A new supplementary robustness figure should use the previous candidate package's existing saved maps; placement/numbering needs author approval. Its current candidate source is retained at the prior commit, not regenerated.
