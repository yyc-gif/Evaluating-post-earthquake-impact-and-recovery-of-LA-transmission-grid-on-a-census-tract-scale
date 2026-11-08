# AUTHOR-DIRECTED CONTINUATION — Recover/produce GA validation inputs; complete GA-vs-Impact mechanism study

**Priority:** This supersedes the previous instruction to stop or substitute a different cohort when the exact held-out validation inputs are absent. The author explicitly instructs: obtain the validation data and continue; an absent local file is a recovery/reproducibility task, **not permission to stop**. This directive does not change any original frozen simulations, optimization selections, or published figures.

## Question that must be answered

Why is the unconstrained 2pc50 mean burden dominated by substation self-functionality loss (26.887247/31.337777 h = 85.8%) while the reported GA-minus-Impact-first benefit (-0.533 h total) is associated with an approximately -0.821 h source-path contribution, +0.277 h self contribution and +0.011 h threshold contribution? **What exact differences in GA and Impact-first repair completion times, network source reconnections, and affected community dependency masses generate that gain?**

The previous investigation successfully established DS2–DS4 external unlocking and local swaps under fixed rules, but never compared the actual GA and Impact-first execution histories. Its findings are retained and **do not close this question**.

## Source and frozen identity audit — do this, then calculate

1. Read the **actual source for the published Figure S4 GA result** and identify the exact order/sequence SHA, 2,000 realization sample identifiers, seeds, generation/scheduler version, and component totals. The review caption says 2,000 held-out validations; do not assume it uses the October 9 *proposed* archive. Distinguish GA selections by sequence SHA, not filename or display name. Check later manuscript/figure provenance, local research output directories, archival worktrees, adjacent branches, LFS objects and valid local caches first.
2. The repository **already contains an independently frozen 2,000-sample validation protocol**, under `results/diagnostics/final_ga_method_20261009/FINAL_VALIDATION_PROTOCOL.json` and `FINAL_INDEPENDENT_VALIDATION_PROTOCOL.md`. At creation (October 9), it explicitly recorded **NO PHYSICAL SAMPLES GENERATED YET** and selected GA order SHA `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`. **Do not identify this plan as the earlier S4 output without evidence of matching identities.** Its fixed plan was:
   - `N=2000`, `hazard=2pc50`, `resource=C57_D1`, `mapping=M1_UTILITY_003`, `G1_BASELINE_050`, horizon 480 h.
   - For `r=0..1999`, use `rng = numpy.random.default_rng(numpy.random.SeedSequence([202610091,3,2,r]))`.
   - In the original **ordered 92 station IDs**, call unchanged `la_grid.core.C257H_Project_Main.sample_damage_states(pga, devices_df, 1, rng)`; on the **same advanced RNG**, call `damage_to_functionality_and_repair(ds, rng, cfg)`. Preserve original fragility columns, clipping, DS0 duration0, DS-specific positive-normal repair times, input PGA and original station order. The production sampler itself is used in `run_stage_1_revision` (`src/la_grid/core/C257H_Project_Main.py` around lines 6225–6270).
   - Save `station_ids, DS, duration, realization_id, physical_hash, seed` and complete source code/file hashes to a **new namespaced immutable validation archive**. Never overwrite the 64 planning samples or 1,000 original evaluation samples.
   - Check all frozen input and sequence hashes, no overlap with 64 planning/1,000 evaluation physical hashes, and exact determinism by independent regeneration of selected samples, matching DS/duration bits.
3. **If the original 2,000 S4 samples are not recoverable, DO NOT STOP OR silently use only the older 1,000.** Generate the 2,000 samples now under the registered Oct 9 protocol, since the author explicitly authorizes recovery/reconstruction. This would be a new separately labeled independent-cohort validation, not proof of reproducing original Figure S4. If the S4 GA order differs from the Oct 9 pinned GA order, evaluate **both** identified fixed orders against Impact-first on the newly generated sample; report the order identity for each.
4. Execute exact C57 earliest-available-crew dispatch, actual directed travel, same source-connected G1 gate and M1 tract weights, on each common physical realization for Impact-first and every identified fixed GA order. Reuse the production numerical kernels; `src/la_grid/diagnostics/c1_mechanism_actionability.py` already has frozen graph/mapping/crew/travel loaders, exact decoder, source-gate tracing, physical hashes and event attribution scaffolding. Adapt/reuse rather than write a different service model.

## Mechanism analysis required, not another loss table

- Reproduce paired per-realization GA-minus-Impact values of `L_self, L_threshold, L_source, L_total`, and compute paired 95% bootstrap CI by resampling **entire realizations**. Compare to the claimed -0.821/+0.277/+0.011/-0.533 values **only if their cohort and sequence identity genuinely match**.
- Align actual completion time at each station between both schedules. For each repair completion, identify `f/F/C` changes, newly reachable **other** stations, mapped population-dependency mass, event timing and duration before disconnection clears. Attribute the difference in *integrated source deficit* by station/tract/time interval; reconcile attribution sums to total paired source delta within numerical tolerance. Do not subtract unmatched event rows or assign individual credit to arbitrary members of a simultaneous batch.
- Rank substantive GA-advanced or GA-delayed repairs, test when changes in source-path deficit arise, and show their self-loss offset. Explain positive and negative cases, not just selected successful examples.
- Carry forward yesterday's pre-registered 128-local-swap results only as *supporting mechanism evidence*. The requested answer must be about **actual GA-vs-Impact-first**.
- Do **not** change the optimization algorithm, retune using validation outcomes, relabel model availability as actual power delivered, or modify approved manuscript figures.

## Deliverables and non-stopping standard

Commit into this same research branch a reproducible validation-data recovery/generation script, archived physical-sample identity manifest (raw large tables may be retained locally with path and SHA256 documented), paired GA-vs-Impact numeric results, event-level component-attribution table, **one or two direct GA-vs-Impact figures**, and a concise `GA_VS_IMPACT_MECHANISM_CLOSURE.md` answering the question. Post a PR #5 update with the exact paths and results.

A missing file requires: recover from source OR regenerate using the prescribed deterministic algorithm OR fix the local environment to run that algorithm; report the **specific failed operation** and continue with the next recovery route. Do not request another authorization merely to execute these already defined simulations. If the registered protocol itself has a concrete incompatible physical input (rather than a missing file), document the exact technical obstruction and recover it from the frozen model, not by inventing a replacement input.

Do not spend time on PR merging or legacy CI/LFS cleanup. Work on the numerical scientific question until the paired GA mechanism is accounted for.
