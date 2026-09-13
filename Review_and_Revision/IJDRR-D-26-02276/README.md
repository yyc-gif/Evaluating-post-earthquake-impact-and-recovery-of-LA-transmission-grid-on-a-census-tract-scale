# IJDRR-D-26-02276 Review and Substantive Revision

This directory is the Git-visible handoff for the post-review revision of:

> *Post-Earthquake Power Service Recovery in Los Angeles: Linking Substation Damage, Restoration Logistics, and Tract-Level Disparities*

Formal IJDRR outcome: **Reject with transfer offer**, not major revision.

## Start here

Read [CORE_REVISION_FINDINGS.md](02_Paired_Pilot_20260912/CORE_REVISION_FINDINGS.md) first. It records:

- the corrected repair-duration, completion-event, and information-set definitions;
- the 32-realization paired pilot design and limitations;
- the main numerical findings and stopping decision;
- tract distributional effects, GA checks, resource-regime bounds, and mapping priorities;
- what must be resolved before expanding the Monte Carlo study.

The decisive current finding is that Hospital-first retains a population-service advantage over GA-Efficiency, but the old average GA-Efficiency makespan advantage does **not** persist in the corrected pilot. This triggered the predeclared stop condition, so no larger Monte Carlo, additional crew scenarios, mapping variants, or new GA runs were launched.

## Directory contents

### 01_Reviewer_and_Decision

- `IJDRR-D-26-02276_editor_review_transfer_record.md`: editorial decision, reviewer reports, and transfer-page context.
- `Reviewer.docx`: source review document retained for provenance.

### 02_Paired_Pilot_20260912

- `CORE_REVISION_FINDINGS.md`: authoritative technical handoff and revision decision.
- `PAIRED_PILOT_RESULTS.csv`: 32 realization IDs × 4 fixed strategies. The paired columns are **strategy minus Hospital-first**.
- `TRACT_DISTRIBUTIONAL_EFFECTS.csv`: one row per tract. The principal difference is **Hospital-first minus GA-Efficiency**; negative values mean lower modeled cumulative service deficit under Hospital-first.
- `PAIRED_EVENT_DATA.npz`: compact realization-level damage, duration, dispatch, completion, gate, service trajectory, and tract result arrays needed to reproduce the paired analysis.
- `paired_pilot.py`: bounded revision driver. It imports the submission-era model without editing it.
- `CORE_DIAGNOSTIC.png`: the single retained diagnostic figure.

## Evidence boundaries

All reported service deficits are conditional **connectivity/service proxy hours**, not observed outage hours or delivered electricity. The model still has no capacity, power flow, generation-demand balance, line loading, voltage constraint, or load shedding.

The pilot uses fixed submission-era priority lists under a common information set and new shared damage/duration realizations. It does not prove the four repair-time parameter pairs are empirically calibrated, does not validate the tract-to-substation mapping, and does not establish GA convergence across seeds.

The prior broad audit remains in [docs/IJDRR_D_26_02276_TECHNICAL_AUDIT.md](../../docs/IJDRR_D_26_02276_TECHNICAL_AUDIT.md). Do not repeat it before acting on the focused next steps in the core report.
