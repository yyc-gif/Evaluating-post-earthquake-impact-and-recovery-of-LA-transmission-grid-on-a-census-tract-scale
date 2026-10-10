# LFS integrity boundary

Publication verifies every new LFS pointer with git lfs pointer --check --strict, compares its OID and size with exact local data, and runs git lfs fsck --objects on the new commit range. Original PDF/source snapshots retain their exact bytes.

The baseline has one previously documented repository-wide pointer exception: results/capacity/SCE_CAPACITY_SUPPORTED_STATIONS.csv is an ordinary Git blob although the CSV attributes call for LFS. Blob 0c21a932ea6d4db2409100d860a4dd0f91fea3db is preserved. It is not converted by this audit, and a global pointer-compliance PASS is not claimed.

The new branch inherits unchanged feature-extraction commit e90186e62103b2dfe1d8bb7e09c07cae15476497 to retain the exact read-only physical-form correlation inputs. This audit's commit changes only nri_eal_redundancy_audit_20261009/. Original scientific baseline remains031d2c675f8e7d58035d27448be040b809ced086, original staged index is unchanged, and no formal result is promoted.
