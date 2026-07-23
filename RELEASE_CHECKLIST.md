# Publication Release Checklist

Use this checklist to freeze a version-specific paper companion release. Do
not assign or advertise a DOI until an archive service has actually issued it.

## 1. Confirm a Clean Repository

```bash
git status
git log -1 --oneline
```

Confirm that all intended changes are committed and that no local data,
temporary figures, logs, credentials, or manuscript edits are pending.

## 2. Confirm Git LFS Availability

```bash
git lfs pull
git lfs ls-files
git lfs status
```

On a fresh clone, open representative CSV, PDF, PNG, shapefile, and GraphML
objects to confirm that they are real files rather than LFS pointer text.

## 3. Run Lightweight Checks

```bash
python -m compileall .
python run_pipeline.py --help
```

Do not run the full Monte Carlo and GA workflow solely for a release metadata
check. If scientific outputs have changed intentionally, perform the separate
full validation documented in `REPRODUCIBILITY.md`.

## 4. Check Frozen Paper Assets

- Confirm `Submission_Package/Figure_1.pdf` and Figures 2-7 open correctly.
- Confirm `Submission_Package/Supplementary_Material.pdf` opens correctly.
- Confirm automated scripts do not write into `Submission_Package/`.
- Compare generated `build/figures/` assets with the frozen files and document
  any expected rendering differences.
- Decide whether the editable manuscript should remain publicly tracked before
  the release is tagged.

## 5. Create an Annotated Tag

After the release commit has been reviewed:

```bash
git tag -a v1.0.0-manuscript -m "IJDRR manuscript companion release"
git push origin v1.0.0-manuscript
```

Use a new semantic version for later revisions rather than moving an existing
published tag.

## 6. Create a GitHub Release

Create a GitHub Release from the annotated tag. Include the manuscript title,
authors, scope statement, reproducibility entry point, known limitations, and
a concise inventory of paper assets. Confirm that Git LFS-backed release files
are accessible from a fresh clone.

## 7. Connect the Repository to Zenodo

Sign in to Zenodo, enable the GitHub repository integration, and confirm the
target repository. This step requires an authorized maintainer account and is
not performed automatically by this repository.

## 8. Archive the Release

Publish the GitHub Release only after the intended tag and assets are final.
Allow Zenodo to archive that specific release and verify the archived record's
title, creators, version, files, and license notes.

## 9. Obtain a Version-Specific DOI

Record the DOI issued by Zenodo for the archived version. Do not invent a DOI,
use a placeholder DOI in public metadata, or claim that Zenodo is connected
before the integration has been completed.

## 10. Update Citation Metadata

In a follow-up release, add the real DOI and final article metadata to:

- `CITATION.cff`
- `README.md`
- the manuscript Data Availability Statement

Check that the software-release DOI and the article DOI are identified
correctly and are not substituted for one another.
