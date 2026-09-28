# Final revised-paper workflow

Run the authoritative local validation/reuse path:

```bash
python FINAL_REVISION_RUN_SEQUENCE/run_all.py --resume
```

`--from-scratch = NOT YET CERTIFIED`.

`--resume` validates and reuses frozen formal archives and accepted post-freeze results. It does not sample, schedule, run GA, recompute Stage 7, or regenerate sensitivity results. `--from-scratch` is **NOT YET CERTIFIED**.

| Stage | Command | Purpose | Primary authority | Resume status |
|---|---|---|---|---|
| 01 Validate inputs | same | Verify frozen matrix, hashes, code and Git/LFS identities | parent matrix and dry validation | Validate |
| 02 Mapping and samples | same | Verify/reuse M1 and 4,000 evaluation + 64 planning samples | frozen Stage 1 inputs | Reuse |
| 03 GA and strategy freeze | same | Verify final eight sequences and GA provenance | GA identities and frozen sequences | Reuse |
| 04 Trajectories | same | Verify/reuse 84,000 formal + 10,000 Vulnerability-first trajectories | archive indexes | Reuse; local archive required |
| 05 Service and tract evaluation | same | Verify frozen offline shards and metrics | formal/equity indexes | Reuse; local shards required |
| 06 Source/network diagnostics | same | Verify retained diagnostics | dynamic/connectivity identities | Reuse; local diagnostic archive required |
| 07 Distributional/vulnerability | same | Verify final equity results | Equity Amendment result index | Reuse |
| 08 Stage 7 typology | same | Verify harmonized typology | `Stage 7 Output_SOVI_Harmonized` | Reuse |
| 09 Capacity robustness | same | Verify closed SCE capacity sensitivity | closure outputs | Reuse |
| 10 Results and figures | same | Verify final suite and every manifest row | `LA_Grid_Revised_Suite_20260925` | Reuse; sibling required |

Large archives are outside Git and are registered in `EXTERNAL_ARCHIVE_MANIFEST.json`. The suite defaults to `../LA_Grid_Revised_Suite_20260925`; set `LA_GRID_REVISED_SUITE_DIR` to override. Prior patches and identities are mapped in `LEGACY_AND_PROVENANCE_MAP.md`.
