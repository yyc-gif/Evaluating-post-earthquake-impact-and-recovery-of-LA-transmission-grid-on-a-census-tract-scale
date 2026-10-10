# Execution Record

Run date: 2026-10-09. Starting branch/HEAD: `revision/reviewer-driven-core-rebuild-v2`, `dab976173dcb5da7fdbd4a2c91d879317a797331`. No restoration, GA, PCA, K-means, hotspot or plotting entry point was invoked. All computations used existing labels and source inputs read-only.

## Completed Phases

| Phase | Command / record | Actual outcome |
| --- | --- | --- |
| Preservation baseline | `validate.py --repo <checkout> --phase baseline` | All 212 protected hashes match original baseline; original research files and existing staged digest recorded |
| Source acquisition | `acquire.py --phase sources`; `ACQUISITION_LOG.json` | Original California B25024/B25034 Census VRE ZIPs, state average weight and official documentation retained |
| ACS extraction | `validate.py --repo <checkout> --phase acs` | 2,315 matched; 2,291 residential ratios defined; 50,930 original source cells match; saved age ratios reproduced; 211 >10-pp MOEs, not the earlier approximate 868 |
| Official raster-access probes | `probe.py`; `NLCD_PROBE_LOG.json` | Four WCS2 time variants returned XML startTime-null exceptions, not TIFFs; WCS1 rejected its version |
| Numeric raster pilot | `nlcd.py --repo <checkout> --phase mirror` | 2022 C1.0 FIS/land-cover catalog rasters locked; native numeric bands retained; Esri item beta/version warning separately recorded |
| Raster geographic/aggregation QA | `nlcd.py --repo <checkout> --phase aggregate` | All 2,315 valid means, 0 unmatched, 0 m2 NoData; water explicitly excluded; independent 16-tract intersections agree within 1.321e-10; full repeat identical |
| Fresh download QA | `nlcd.py --repo <checkout> --phase repeat` | Independent 128x128 request matched pixels and transform; request/hash in `NLCD_REPEAT_DOWNLOAD.json` |
| Cluster/redudancy comparisons | `validate.py --repo <checkout> --phase compare` | Existing five groups summarized; replicate and approximate screens kept distinct; precision/composition/effect/correlation/conditional-information tables generated |
| Independent source checks | `qa.py --repo <checkout>` | Raw ZIP count/ratio/variance checks on six selected boundary/nonboundary tracts; summaries/coverage/input hashes pass |
| Offline reference route self-test | `nlcd.py --phase reference` using retained pilot clips and declared build `PILOT_SELF_TEST_NOT_AUTHORITATIVE` | 2,315 reference-minus-pilot means exactly zero; fresh-directory/native-window route works; **not** a comparison against an original USGS file |
| Independent offline reproduction | `reproduce.py --repo <checkout> --out <new-directory>` | Four successful phases, no network, input hashes unchanged; **18 result files byte-identical**; `REPRODUCTION_CHECK.json` |
| Pre-publication preservation | `validate.py --repo <checkout> --phase verify` | 212 hashes unchanged; all original audit bytes unchanged; original staged digest unchanged |

The numeric phase is complete. Publication admission is READY for aggregate ACS configuration descriptions, CONDITIONAL for the NLCD pilot and EXCLUDE for SCAG entropy in this round. Raw source availability is not a precision or mapping-accuracy test.

## Reproducibility and Processing Decisions

`requirements.txt` pins the runtime used. Additional raster packages were installed in an isolated scratch `vendor/` directory; that environment/cache is excluded from Git. Retained public source ZIPs, rasters, metadata, XML error responses and documentation make the numeric calculation independent of live-service availability. `package.py` selects only declared deliverables/sources and records their SHA-256 hashes; LA-wide VRE CSVs and temporary raster/replicate arrays are regenerated, not committed.

The original broad NLCD collection recommendation was revised to the build actually delivered by the selected catalog (C1.0). HTTP 200 alone was not accepted as raster success. Runtime/acquisition errors were resolved by isolated raster dependencies and the version-pinned numeric mirror; the authoritative USGS provenance limitation was **not** treated as resolved. No email-delivery request or requester-pays charge was initiated.

The actual Git checkout differs from the older IDE directory. All new work is exported only into `docs/data_research/built_environment_20261009/validation/`. The commit must be path-only so pre-existing staged changes remain staged and outside this research commit. Post-commit protected/staged verification and remote/LFS verification are performed separately; this pre-commit record does not pretend to contain its own final commit ID.

## Remaining Gates

- Authoritative NLCD 2022 release/build, original raster and mapping-error assessment. The offline reference path supports this follow-up, but its self-test is not independent provenance evidence.
- SCAG compatible historical geometry, area coverage, non-overlapping categories/STACK treatment and entropy quality; no entropy values were produced.
- The exact upstream shapefile release edition remains unverified; the existing polygons and 2020-based IDs are hashed and matched, not relabeled as a newly authenticated TIGER download.
- Manuscript insertion/figure edits and any revised clustering need separate review/authorization. This package does not declare the existing Stage 7 scientifically final.
