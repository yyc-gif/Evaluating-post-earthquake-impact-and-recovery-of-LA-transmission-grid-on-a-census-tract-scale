# CDC EJI 2024 source and version QA
AUTHOR REVIEW - NOT FORMAL STAGE 7

Authority: `022f3f9a8a1fb3e454de05559311f1763a2ebb3b`. Official portal JavaScript and its geography JSON supplied the actual bulk filenames. Both national and California 2024 CSV ZIPs were downloaded successfully; no guessed third-party table substituted. Archives contain original CSV and matching CSV/XLSX dictionaries. National table: 85,188 rows; California: 9,109. Both have unique GEOIDs. California numeric values and both dictionaries match the national release exactly.

Original payload URLs, UTC retrieval timestamps, server last-modified labels and SHA256/byte counts are in `OFFICIAL_SOURCE_ACQUISITION.json`. Archive member hashes are separate. The environment's task date is recorded separately from actual client UTC time; neither is the data vintage. Original ZIPs are immutable. The dictionary CSV uses Windows-1252 encoding; its original bytes are retained.

Official raw and CBM map services were queried for all 2,495 LA county records. Map's first broad query was transfer-limited; a long object-ID URL returned HTTP404. Both are retained in acquisition evidence, not mistaken for complete data. Final short, ID-bound queries retrieved exactly all expected records. Raw/bulk/map CBM fields agree on all2,299 approved tract IDs.

Dictionary/header use `GEOID_2020`, rather than the technical changelog's `GEOID_20` shorthand. It equals GEOID for all matched LA records. Connecticut's 2022 county-code exception is not applicable. Boundaries are 2020 TIGER/Line. CDC `E_TOTPOP` is ACS2018-2022 and differs from frozen population for 2,294 study tracts. It is not substituted. One frozen-positive tract,06037980023 (47 frozen residents), has CDC population0 but valid climate rank; it remains eligible. All eight positive-population zero-housing tracts remain.

Published ranks exist for all2299; this is rank coverage, not proof of complete physical observation. Full source dictionaries expose six extreme-events flags, but no F_NEHD/F_SMOKE/F_BURN. Technical processing describes flags for all three; this upstream discrepancy remains unresolved.

The bulk raw NRI frequency fields numerically match the frozen v1.19 coastal/drought/riverine/wind frequencies to four-decimal export precision; hurricane source nulls match F=1. This is numerical association, not proof of an explicitly documented CDC NRI release identifier. Tornado uses CDC Tracking1986-2024 and does not match NRIv1.19; no substitution made.

The burned-area dictionary refers to the MTBS source archive (1984-2022), whereas technical processing uses 2013-2022 only and wildfire polygons over 1,000 acres. This is an archive-versus-analysis distinction, not a contradiction. Smaller fires and prescribed burns are not measured by this indicator. The drought technical text says event-weeks, whereas values match NRI event-days/year. Frozen FEMA v1.19 documentation p143 (printed 9-4) explicitly converts weeks to seven event-days. No values or published rank have been corrected by this audit. Indicator-level provider URLs and technical PDF page references are in the source register.
