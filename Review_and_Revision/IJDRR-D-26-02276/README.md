# IJDRR-D-26-02276 Review and Substantive Revision

This directory is the Git-visible handoff for the post-review revision of:

> *Post-Earthquake Power Service Recovery in Los Angeles: Linking Substation Damage, Restoration Logistics, and Tract-Level Disparities*

Formal IJDRR outcome: **Reject with transfer offer**, not major revision.

## Start here

Read [BLOCKER_RESOLUTION.md](03_Blocker_Resolution_20260913/BLOCKER_RESOLUTION.md) first. The latest fixed-sample checks retain Hospital-first's population-service advantage, with no identifiable systematic makespan difference. Two alternative mappings retain the aggregate advantage but change some tract-level winners and losers.

**Current decision: STOP expansion; do not run revised 29 crews yet.** The hour-scale repair parameters and the reasons for selecting 92 facilities from the recovered 486-candidate inventory remain unresolved. Positive-conditioned and clipped-normal implementations are compared as candidates, not promoted as empirically validated corrections.

The frozen previous-round [CORE_REVISION_FINDINGS.md](02_Paired_Pilot_20260912/CORE_REVISION_FINDINGS.md) records:

- the candidate repair-duration, completion-event, and information-set definitions;
- the 32-realization paired pilot design and limitations;
- the main numerical findings and stopping decision;
- tract distributional effects, GA checks, resource-regime bounds, and mapping priorities;
- what must be resolved before expanding the Monte Carlo study.

That previous pilot triggered the predeclared stop condition. The new blocker round uses the same 32 realization IDs and four fixed strategies; its mapping checks only postprocess saved station trajectories. No additional crew scenarios, Monte Carlo expansion, or new GA runs have been launched.

## Directory contents

### 03_Blocker_Resolution_20260913 — latest

- `BLOCKER_RESOLUTION.md`: repair-time source evidence, explicit MODEL_EVENT_DEFINITION, network selection provenance, before/after findings, manuscript revision notes, and Go/Stop decision.
- `CORRECTED_PAIRED_RESULTS.csv`: 256 rows, two distribution candidates × 32 realizations × four strategies; explicit candidate status and duration coupling.
- `BEFORE_AFTER_COMPARISON.csv`: paired strategy differences and community count changes; aggregate mean-tract classification rows are clearly labeled.
- `MAPPING_SENSITIVITY_SUMMARY.csv`: two alternative mappings evaluated on frozen station trajectories.
- `BLOCKER_PAIRED_EVENT_DATA.npz`: paired event/tract arrays, mapping matrices, and compact analysis metadata.
- `blocker_fixed32.py`: repository-portable bounded driver; no new sampling or GA calls. The archived driver and outputs remain unchanged.

### 01_Reviewer_and_Decision

- `IJDRR-D-26-02276_editor_review_transfer_record.md`: editorial decision, reviewer reports, and transfer-page context.
- `Reviewer.docx`: source review document retained for provenance.

### 02_Paired_Pilot_20260912

- `CORE_REVISION_FINDINGS.md`: frozen previous-round technical findings; use the blocker report for the latest decision.
- `PAIRED_PILOT_RESULTS.csv`: 32 realization IDs × 4 fixed strategies. The paired columns are **strategy minus Hospital-first**.
- `TRACT_DISTRIBUTIONAL_EFFECTS.csv`: one row per tract. The principal difference is **Hospital-first minus GA-Efficiency**; negative values mean lower modeled cumulative service deficit under Hospital-first.
- `PAIRED_EVENT_DATA.npz`: compact realization-level damage, duration, dispatch, completion, gate, service trajectory, and tract result arrays needed to reproduce the paired analysis.
- `paired_pilot.py`: bounded revision driver. It imports the submission-era model without editing it.
- `CORE_DIAGNOSTIC.png`: the single retained diagnostic figure.

## Evidence boundaries

All reported service deficits are conditional **connectivity/service proxy hours**, not observed outage hours or delivered electricity. The model still has no capacity, power flow, generation-demand balance, line loading, voltage constraint, or load shedding.

The pilot uses fixed submission-era priority lists under a common information set and new shared damage/duration realizations. It does not prove the four repair-time parameter pairs are empirically calibrated, does not validate the tract-to-substation mapping, and does not establish GA convergence across seeds.

The prior broad audit remains in [docs/IJDRR_D_26_02276_TECHNICAL_AUDIT.md](../../docs/IJDRR_D_26_02276_TECHNICAL_AUDIT.md). Do not repeat it before acting on the focused next steps in the core report.
