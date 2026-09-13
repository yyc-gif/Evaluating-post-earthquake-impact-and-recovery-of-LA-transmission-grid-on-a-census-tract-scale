# IJDRR-D-26-02276 Review and Substantive Revision

This directory is the Git-visible handoff for the post-review revision of:

> *Post-Earthquake Power Service Recovery in Los Angeles: Linking Substation Damage, Restoration Logistics, and Tract-Level Disparities*

Formal IJDRR outcome: **Reject with transfer offer**, not major revision.

## Start here

Read [PROVENANCE_DECISION.md](04_Provenance_Decision_20260913/PROVENANCE_DECISION.md) first. The targeted historical search is complete: the hour-scale parameters have no recovered empirical basis, and the historical 486-to-92 selection rule was not recovered. The replacement selection rule produces **310 facilities, with 83 retained from the old 92, 227 additions, and nine exclusions**. Its list is compared in `STATION_SELECTION_COMPARISON.csv`.

**Latest decision: keep recovery-simulation STOP.** Work durations may be used only as explicit, uncalibrated action-duration scenarios; the station change requires rebuilding topology, dependency, and downstream inputs/results. The next recommended computation is a topology/dependency dry build, with no recovery sampling or optimization. This round performed only source checks and list comparison.

The previous [BLOCKER_RESOLUTION.md](03_Blocker_Resolution_20260913/BLOCKER_RESOLUTION.md) contains the frozen fixed-sample checks: Hospital-first retains a population-service advantage under that model, with no identifiable systematic makespan difference. Its two alternative mappings retain the aggregate advantage but change some tract-level winners and losers. Those results do not automatically transfer to a 310-facility model.

**Previous blocker-stage decision: STOP expansion.** Positive-conditioned and clipped-normal implementations were compared as candidates, not promoted as empirically validated corrections. The latest provenance report resolves how to proceed without claiming those missing empirical/selection records were recovered.

The frozen previous-round [CORE_REVISION_FINDINGS.md](02_Paired_Pilot_20260912/CORE_REVISION_FINDINGS.md) records:

- the candidate repair-duration, completion-event, and information-set definitions;
- the 32-realization paired pilot design and limitations;
- the main numerical findings and stopping decision;
- tract distributional effects, GA checks, resource-regime bounds, and mapping priorities;
- what must be resolved before expanding the Monte Carlo study.

That previous pilot triggered the predeclared stop condition. The new blocker round uses the same 32 realization IDs and four fixed strategies; its mapping checks only postprocess saved station trajectories. No additional crew scenarios, Monte Carlo expansion, or new GA runs have been launched.

## Directory contents

### 04_Provenance_Decision_20260913 — latest

- `PROVENANCE_DECISION.md`: first parameter appearances, action-scope/travel evidence, QGIS/Git selection gaps, replacement R1 rule, decisions, and minimum next-computation gates. Includes executable list-verification code.
- `STATION_SELECTION_COMPARISON.csv`: 487 comparison-relevant records with raw fields and explicit eligibility, old/new membership, city-filter exception, source, and key-station flags. No model output is included.

### 03_Blocker_Resolution_20260913

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
