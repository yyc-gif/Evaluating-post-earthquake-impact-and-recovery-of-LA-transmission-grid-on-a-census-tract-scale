# Repository physical reorganization — Phase A dry plan

**Status: inventory and dependency audit only. No paths were moved, no code/imports were edited, no caches were deleted, and no scientific outputs were regenerated.** This plan is for `revision/reviewer-driven-core-rebuild-v2` at `cfeadcdcb7d7b0d1d70a9b854440c6f0360c72b5`.

The July archive ref was read-only verified at `archive/ijdrr-submission-20260722` = `182686868cffe962739804f6bc0ccecaed73d601`. No command wrote to that branch or archive.

## Root inventory and proposed scale

The baseline scan counted **172 root entries** before creating the requested audit files: 24 directories, 147 ordinary files, and Git's `.git` metadata entry. Git reports 147 tracked files directly at root. The requested CSV is now the only new root entry; this plan will be the second, so the temporary Phase A root count is 174. Both audit files are intended to move under `docs/reproducibility/` during Phase B.

The machine-readable map has one row for every baseline root entry. It records Git tracked/mixed/local-only status, role and authority, literal Python path/import and manifest references, canonical resume validation references, and proposed action/path. The reference scan was checked against `FINAL_REVISION_RUN_SEQUENCE/run_all.py`, canonical JSON registries, and explicit `rg` path/import searches for high-risk paths. `used_by_final_workflow` distinguishes data/output paths validated by `--resume` from code whose identity is registered but which `--resume` does not execute.

| Proposed action | Root entries |
|---|---:|
| `KEEP_AT_ROOT` | 7 |
| `MOVE_TO_SRC` | 65 |
| `MOVE_TO_TESTS` | 19 |
| `MOVE_TO_CONFIG` | 2 |
| `MOVE_TO_DATA` | 3 |
| `MOVE_TO_RESULTS` | 32 |
| `MOVE_TO_DOCS` | 27 |
| `MOVE_TO_PROVENANCE` | 15 |
| `DELETE_CACHE` | 2 |
| **Total inventoried** | **172** |

The retained root is expected to contain 14 visible project entries: `README.md`, `requirements.txt`, `.gitignore`, `.gitattributes`, `.github/`, `FINAL_REVISION_RUN_SEQUENCE/`, `src/`, `config/`, `data/`, `results/`, `docs/`, `tests/`, `provenance/`, and a small `pyproject.toml` for the `src/la_grid` package and test discovery. Git metadata is not counted as a user-facing project entry. The two Phase A audit files will live under `docs/reproducibility/` after physical moves.

## Actual authorities and path dependencies found

The canonical `run_all.py --resume` is validation/reuse only. It does not import and execute the scientific modules. It reads canonical registries and checks identities, tracked/materialized files, external archive inventories and hashes. The code authority registry lists implementation modules for provenance; those listed modules are not silently run by `--resume`.

The following current root paths are directly named by canonical validation/manifests and therefore need explicit path migration before any move:

- `Data/`, including `Data/JULY_UTILITY_CONSTRAINED_92.csv`, is hash-checked by Stages 01–02 and referenced by many legacy/revision scripts.
- `FINAL_EXPERIMENT_MATRIX.json` is the parent frozen-design input whose content SHA must remain unchanged. Its current path is read by the validator and several historical helpers.
- `Formal_Experiment_20260923/` supplies formal execution identities, planning/sample inputs, GA/sequence provenance, trajectories, offline shards, Stage 7 authority, and accepted reviewer additions across Stages 01–09. It is a **mixed tracked + local-only** tree.
- `Stage 4 Output_expanded/travel_base_to_task.csv` and `travel_task_to_task.csv` are frozen directed-travel inputs explicitly hash-checked by Stage 01. This is a real final-workflow dependency inside a directory that otherwise contains legacy Stage 4 products. The two CSVs must move to `data/travel/`; the rest of that stage directory can move to legacy provenance.
- `Manuscript_Figures/` contains capacity-closure figure files whose hashes are checked by Stage 09.
- Root capacity outputs (`SCE_CAPACITY_*`, `SCE_CAPACITY_SUPPORTED_STATIONS.csv`) and retained source/connectivity summary CSVs are hash-checked by Stages 06/09.
- `FINAL_REVISION_RUN_SEQUENCE/` is the sole workflow authority and stays at root.

A further dependency is **outside the repo root**: Stage 10 validates the sibling `../LA_Grid_Revised_Suite_20260925/`. The frozen registry expects 575 files / 299,030,125 bytes and checks its suite manifest and every listed output hash. Phase B should move that one suite intact under `results/` (recommended `results/revised_suite/LA_Grid_Revised_Suite_20260925/`) and update the registry, rather than leave the canonical workflow tied to a sibling directory. This is a physical relocation only; the suite's internal manifest and file hashes must remain byte-identical.

Consequently, **yes: at least one final input was in a directory that could have been mistaken for a legacy output**—the two Stage 4 travel matrices. `Stage 1–3, 5–7 Output_expanded/` at root are not the canonical formal authorities; the Stage 7 authority is `Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/`. The old root `Stage 7 Output_expanded/` is provenance only. Root `Manuscript_Figures/`, despite being a separate figure folder, remains a Stage 09 validation dependency.

The seven existing external-archive registry entries and expected inventories are:

| Artifact | Current registered path | Files | Bytes |
|---|---|---:|---:|
| Formal trajectories | `Formal_Experiment_20260923/Formal_Trajectories` | 252,000 | 1,669,251,984 |
| Vulnerability-first trajectories | `Formal_Experiment_20260923/Equity_Amendment/T` | 30,000 | 204,630,868 |
| Formal offline shards | `Formal_Experiment_20260923/Formal_Offline_Evaluation` | 255 | 2,145,840,075 |
| Dynamic topology archive | `Formal_Experiment_20260923/Formal_Dynamic_Topology` | 8,002 | 193,720,502 |
| Equity offline shards | `Formal_Experiment_20260923/Equity_Amendment/Offline` | 31 | 232,639,654 |
| Connectivity state cache | `Formal_Experiment_20260923/Formal_Reviewer_Results` | 5 | 100,073,170 |
| Revised suite | sibling `../LA_Grid_Revised_Suite_20260925` | 575 | 299,030,125 |

These are read-only authorities during reorganization. Directory moves must preserve contents, per-artifact file counts, sizes, index hashes, and archive-chain hashes. The `Equity_Amendment` subtree should be physically relocated to `results/vulnerability/Equity_Amendment/` while retaining its internal layout; frozen vulnerability trajectories then become a named Stage 04 source and the distributional outputs a Stage 07 source, not an external patch. The harmonized Stage 7 subtree should move intact to `results/stage7/`.

## Proposed target tree and mapping logic

```text
repo/
├── README.md  requirements.txt  .gitignore  .gitattributes  pyproject.toml
├── .github/
├── FINAL_REVISION_RUN_SEQUENCE/
├── src/la_grid/
│   ├── core/  revision/  diagnostics/  plotting/  utilities/
├── config/parent_frozen_design/
├── data/model/  mapping/  travel/  external_validation/
├── results/formal/  vulnerability/  stage7/  capacity/
│   diagnostics/  manuscript/  supplement/  revised_suite/
├── docs/methodology/  reviewer/  audits/  data_research/
│   reproducibility/  meeting/
├── tests/
└── provenance/july92/  reviewer_working/  amendments/
    legacy_outputs/  failed_attempts/
```

This is a content plan, not an instruction to split frozen archives blindly. `Formal_Experiment_20260923/` should first move as a whole to `results/formal/` so its internal relative archive structure stays intact; then move only the accepted `Equity_Amendment/` and harmonized Stage 7 subtrees to their semantic result categories. Move `Failed_Offline_Attempt_c341e27/` to `provenance/failed_attempts/`. The July archive branch remains untouched.

The original `Data/` tree has 73 tracked descendants (67 currently LFS-managed); its nested files must be inventoried before splitting model inputs and mappings. Preserve file bytes and the frozen mapping SHA while moving inputs to `data/model/` and `data/mapping/`. `External_Validation_Data/` is local-only/untracked and should move to `data/external_validation/` without adding raw payloads to Git. Move Stage 4's two validated travel CSVs to `data/travel/`, then move only its remaining products to `provenance/legacy_outputs/Stage 4 Output_expanded/`.

Scientific Python files map to `src/la_grid/` without algorithm copies: original model/topology/travel implementation to `core`; reviewer implementation to `revision`; connectivity/fragility/path/electrical diagnostics to `diagnostics`; visualizers/builders to `plotting`; small preparation/index utilities to `utilities`. Nineteen `test_*.py` files map to `tests/`. Reviewer working directories and obsolete July stage products map to `provenance/`; no provenance is deleted. Reports, request drafts, meeting files and source notes map to the relevant `docs/` category. Tables/figures map by role to `results/`.

## Expected code and manifest work in Phase B

There are 84 tracked root Python files in the map (65 implementation/plotting/utilities plus 19 tests) and 92 direct cross-module import lines were found in the current tracked Python corpus. The imports include expanded wrappers loading base modules, model code importing `strategy_names` and scheduling utilities, the `r1_*` dependency graph, plotting modules loading the July visualizer, and tests importing root modules. Phase B should place the files in a real `src/la_grid` package, add package initializers and packaging/test discovery metadata, and update these imports to package-qualified names. It should add one explicit repository-root/path helper and update only path construction. It must not add the repository root wholesale to `sys.path`; numerical function bodies and constants remain unchanged.

Canonical path registries that will need path-only updates include `run_all.py`, `CODE_AUTHORITY.json`, `EXTERNAL_ARCHIVE_MANIFEST.json`, `FINAL_REVISION_RUN_MATRIX.json`, the affected stage validation manifests, Stage 8/9 output-hash records, and the generated `FINAL_RUN_MANIFEST.json`. Update stage READMEs and provenance crosswalks to the moved authorities. Preserve the parent frozen matrix bytes/SHA and every scientific result file SHA. Update `.gitattributes` path-specific LFS rules for moved formal parquet files and the trial parquet provenance; the extension-wide rules for CSV, PDF, PNG, shapefile components, and other listed types continue to apply after a move. There are currently **472 Git LFS-tracked files**. Run `git lfs ls-files` and verify pointer/materialization state before and after moves.

Tracked repositioning in Phase B must use `git mv`. Mixed/local-only archive payloads move only after before/after inventory snapshots; do not stage them just because they now reside under `results/`. Add an explicit root `.gitignore` entry for `.pytest_cache/`: `__pycache__/` is explicitly ignored today, while `.pytest_cache` is currently hidden by its own nested ignore file rather than the root policy. No cache was removed in Phase A.

## Path-risk classification and sequencing

**Low-risk once import/path edits are prepared:** tracked docs, reviewer reports, tables, figures, tests, and legacy stage products; use `git mv`, then update code/docs references. Preserve Git LFS rules and keep duplicated content until the map identifies its authority.

**Grouped move with identity checks required:** `Data/`, `Formal_Experiment_20260923/`, the `Equity_Amendment/` and harmonized Stage 7 subtrees, the two Stage 4 travel matrices, `Manuscript_Figures/`, and the sibling Revised Suite. The directory names are part of current path registries, but the frozen identity is also content/hash based. For each, snapshot current file count/bytes and all registered hashes; move without editing payload; update canonical path registries; rerun hash/inventory validation. Archive-chain calculations must still use the same internal relative paths. Do not claim a move safe until its resulting registry passes.

**High path-churn code:** old `*_expanded.py` paths, scripts that resolve `ROOT = Path(__file__).parent`, scripts with literal `Data/`, Stage-output or Formal paths, all `from r1_*` imports, and `CODE_AUTHORITY.json`. Retain source/history and update path/import locations only. If an old entrypoint cannot be preserved as a thin compatibility wrapper without duplication, label it legacy and provide the package invocation; do not copy the algorithm.

Phase B should proceed in this order: create target package/folders; take path/hash snapshots; `git mv` tracked trees/files (and move local-only payloads separately without staging); split the two travel files, Equity Amendment, final Stage 7, and failed-attempt records; update imports/path helpers and canonical registries; update `.gitattributes`/`.gitignore` and README; run tests and `FINAL_REVISION_RUN_SEQUENCE/run_all.py --resume`; compare all frozen hashes and verify the protected July ref; then review the rename-heavy diff. No scientific sampling, scheduling, GA, clustering, or sensitivity run is part of this plan.

## Phase A result

`REPO_REORGANIZATION_MAP.csv` is the 172-row root inventory and proposed action map. No final scientific result is untraceable to an authority: formal results are registered under the Formal archive, vulnerability-first under the accepted Equity Amendment archive, Stage 7 under the SOVI-harmonized subtree, Stage 09 under its closure hashes, source/connectivity diagnostics under the Stage 06 hashes, and the figure suite under its external suite manifest. However, current path authority is distributed across those registries and direct root paths; Phase B must update all of them together. The main newly identified path split is that the root Stage 4 directory contains two mandatory travel inputs alongside legacy outputs.

This completes Phase A only. No physical reorganization is authorized or performed by these documents alone; pause here for review before Phase B.


## Phase B execution outcome

Physical organization is complete with two explicit root exceptions. `Data/` remains at root because frozen formal identities and historical paths refer to it; the two active travel matrices are tracked under `data/travel/` (which Windows materializes beneath the case-insensitive `Data/` directory). `Formal_Experiment_20260923/` remains at root because placing it under `results/formal/` made ordinary Python inventory enumeration miss 8,000 deeply nested task-event paths on this Windows host. Returning it to its original path restored the registered 252,000-file inventory and every Stage 01–09 hash. The canonical external archive registry now names the root path explicitly.

The Revised Suite is physically at `results/revised_suite/LA_Grid_Revised_Suite_20260925/`. Windows long-path-aware validation is used for its 575 files and 558 manifest entries. It remains locally maintained and Git-ignored. `External_Validation_Data/` is now local-only `Data/external_validation/` and Git-ignored. `Manuscript_Figures/` is at `results/manuscript/figures/`; old stage outputs, sensitivity products, and the old submission package are preserved under `provenance/legacy_outputs/`.

Tracked code/tests/docs/config were moved into `src/la_grid/`, `tests/`, `docs/`, and `config/`. Python imports use the `la_grid` package and `pyproject.toml` configures the src layout. No scientific functions were rewritten.

Final root inventory: 15 project entries excluding `.git`; `Data/` and `Formal_Experiment_20260923/` are the only root data/archive exceptions. The two Git-ignored local collections (`Data/external_validation/` and `results/revised_suite/`) remain physically in their logical result/data locations.
