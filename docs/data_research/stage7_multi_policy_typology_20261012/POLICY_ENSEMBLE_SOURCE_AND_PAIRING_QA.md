# Frozen ensemble source and pairing QA

AUTHOR REVIEW — NOT FORMAL STAGE 7


Status: PASS. Starting authority `739420417412228f9302051d154f11ba3d5cde84`. Rechecked 7,000 event payloads (seven policies times 1,000 physical IDs), their JSON and actual NPZ SHA256, station order, physical/damage/duration hashes, graph/source/crew/directed-travel identities, mapping and horizon. The frozen physical inputs are `(92 stations, 1000 samples)`; canonical hashes combine ordered station IDs, DS and repair-duration bytes, not filenames. All initial effective station states match the existing source-gate archive.

| Check | Maximum error / evidence |
|---|---|
| Exact B = U + paired Delta | 2.02e-14 h |
| Archived tract projection | 4.26e-14 h |
| Event integration vs station integrals | 0 h |
| Population-weighted summary over full study | 1.85e-13 h |
| Independent ensemble arithmetic | 2.13e-14 h |
| Independent SciPy full-cohort silhouettes | 7.73e-15 |

Sources: original policies and Unconstrained in `Formal_Experiment_20260923/Formal_Offline_Evaluation/` and `Formal_Trajectories/2pc50/C57_D1/`; Vulnerability-first in `Equity_Amendment/Offline/` and `Equity_Amendment/T/2pc50/C57_D1/`. Its executable commit differs, but the common physical and configuration identities are independently matched. `POLICY_ENSEMBLE_QA.json` preserves exact source identities and integral/summary hashes; `FROZEN_EVENT_VERIFICATION.csv` records all individual archive hashes. `SOURCE_HASH_VERIFICATION.csv` binds tracked inputs to actual Git/LFS bytes and external files to their manifests.

The NPZ tract arrays do not carry GEOIDs. Their order is the original frozen `Data/Tracts_Within_Expanded_Area.csv` order, explicitly recovered and independently checked by W projection; fits subsequently sort exact eleven-digit IDs. All population values are byte-source verified and unchanged. The upstream frozen Census download vintage is not newly established by this analysis.

`FROZEN_STATION_INTEGRALS_AND_MAPPING.npz` is a compact byte-exact extraction of existing station integral arrays, physical IDs/hashes and W, not new recovery simulation. It enables clean-clone reproduction of the new ensemble calculations without the large raw event archive. Rechecking ALL original event files and their physical authority still requires the manifest-bound local archive absent from a clean Git clone. No aggregate-to-tract outcomes were fabricated.

950 protected scientific files and 278 files in the four preceding packages remain hash-identical. The unrelated source Git status is unchanged. This package alone is committed. No physical schedules, trajectories, formal memberships, quartiles or numbered figures were modified.
