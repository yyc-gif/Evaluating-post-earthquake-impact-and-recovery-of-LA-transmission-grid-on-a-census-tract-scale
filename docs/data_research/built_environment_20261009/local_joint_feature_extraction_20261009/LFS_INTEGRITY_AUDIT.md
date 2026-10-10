# LFS integrity audit

All 33 new LFS files have canonical pointers verified with git lfs pointer --check --strict. Each OID equals the SHA256 of its exact local data bytes, and each size matches. git lfs fsck --objects passes for the research commit. Raw source snapshots retain byte-identical contents in Git.

The combined repository-wide pointer/object check reports one inherited exception: results/capacity/SCE_CAPACITY_SUPPORTED_STATIONS.csv is an ordinary Git blob although the current CSV attribute calls for LFS. Its Git blob is 0c21a932ea6d4db2409100d860a4dd0f91fea3db in both baseline 031d2c675f8e7d58035d27448be040b809ced086 and the research tree. This task does not convert or alter that protected scientific file.

Thus new-output LFS object/hash/pointer integrity is verified; repository-wide pointer compliance has this explicit pre-existing exception. It is not reported as an unrestricted global PASS.
