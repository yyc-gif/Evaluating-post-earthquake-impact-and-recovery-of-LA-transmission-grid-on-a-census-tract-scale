# Stage 7 manuscript integration preview

Start with MANUSCRIPT_INTEGRATION_REVIEW.md, STAGE7_PROFILE_TABLES.md and FIGURE_CAPTIONS.md. Open the three FIG_STAGE7 PDFs at their native 185-mm width.

Candidate: D, five equal domains, k=4, seed 42, exact saved full-cohort labels. Classified residential sample: 2,287. Master labels: 2,291 with four explicitly unclassified records. No promotion or new clustering.

Reproduce from the repository root with:

```
python docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010/build_preview.py --repo .
python docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010/render_preview.py --repo .
python docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010/write_drafts.py --repo .
python -m pytest docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010/test_preview.py
```

Arial is required for the PDF renderer; no font files are distributed. The source commits and exact bytes are recorded; SOURCE_HASH_VERIFICATION.csv explicitly distinguishes payload hashes from Git text normalization. Display identifiers map source 0-3 to C1-C4 with no reordering.
