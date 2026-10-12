# Multi-hazard RQ3 audit

AUTHOR REVIEW - NOT FORMAL STAGE 7

Starting authority `81c3452e29abc109f50564d39035c06225e3ea84`. Begin with [the decision](FINAL_MULTIHAZARD_AUTHOR_DECISION.md) and [coverage audit](TRACT_OVERLAY_AND_MISSINGNESS_QA.md).

No new clustering or physical simulations; no formal Stage7promotion. The approved2299positivepopulationIDs and all eight additionalzero-housingtracts are retained. LossfamiliesE/L are not substitutes for physicalfamilyH.

Reproduce numerical post-processing from retained new-package CSVs: `python information_audit.py`, `python reports.py`, `python figures.py`, `python verify_independent.py`. Run from this package directory or use its full script path. Source-stage reproduction uses `audit_fema.py`, `audit_physical.py --phase base` and `--phase flood`; it needs GitLFS-delivered frozen inputs/priorPGA extraction and the retained official geometry/heat snapshots. `common.py` resolves a fullclone first; local sparseworktrees use declared fallback sources.

`acquire_physical_sources.py --phase metadata|heat|geometry` is optional live reacquisition, not exact historicalsnapshot reconstruction. Providerlayers can change. Rawrequestchunkresponses are local-only caches; canonicalcombinedFeatureCollections, exactqueryIDQA, metadata and requesthashrecords are retained. CachedTIGER2020waterbytes are copied from prior officialacquisition; their sourceURL/hash and nofreshdownload limitation are explicit. No manifest-bound realizationarchive is required to reproduce this package's CSV-based informationaudit; the prior P2physical provenance remains in its original package.

Reviewplots are vectorPDFs plus600dpipreviews, rendered and checked at publication dimensions. They use Matplotlib/GeoPandas, not generatedimages or illustrativephysicalmechanisms. Source PDFs are copied official documents, not created finalplotdeliverables. Requirements used: Python3.12.3, NumPy,Pandas,SciPy,scikit-learn,GeoPandas,Shapely,Matplotlib,PyMuPDF,requests,tabulate; exact versions are recorded in INDEPENDENT_QA.json.
