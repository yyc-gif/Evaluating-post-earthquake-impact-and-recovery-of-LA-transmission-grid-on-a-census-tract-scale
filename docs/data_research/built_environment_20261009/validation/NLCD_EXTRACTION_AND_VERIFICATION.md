# NLCD Numeric Extraction and Release Gate

## Product Actually Used

**Annual NLCD 2022, Collection 1.0**, USGS product generation released in 2024; retrieved 2026-10-09 from the **Esri public numeric mirror**, not directly from a USGS original GeoTIFF. Both catalog objects identify `_2022_CU_C1V0`, OBJECTID 38. Land-cover metadata misspells 'Collection' as 'Collction'; the filename and version number agree. The broader item description refers to v1.1 whereas these specific 2022 objects identify v1.0. This discrepancy is retained, not silently relabeled. [USGS product access](https://www.usgs.gov/centers/eros/science/annual-nlcd-data-access), [official C1.0 guide](https://www.mrlc.gov/sites/default/files/docs/LSDS-2103%20Annual%20National%20Land%20Cover%20Database%20%28NLCD%29%20Collection%201%20Science%20Product%20User%20Guide%20-v1.0%202024_10_15.pdf).

Authoritative definition: fractional constructed, water-impermeable surface in each 30-m cell, encoded 0-100 percent; background/NoData=250. It includes roads, parking, pavement, roofs and other artificial substrates, **not building footprint area, building seismic capacity or additional earthquake exposure**. Map year 2022 is compatible with ACS 2018-2022 but is a single-year land-cover observation, not the same temporal average.

Actual delivery: one uint8 band, **AEA_WGS84** equal-area CRS with central meridian -96, origin latitude 23, standard parallels 29.5/45.5, WGS84 ellipsoid. This is **not NAD83 EPSG:5070**; the latter belongs to the failed WCS service. Clips are 2,934 x 2,484, 30 x 30 m, identical FIS/land-cover grids. Tract geometry is the existing EPSG:4269 shapefile, transformed to the actual raster CRS. The export uses native extent/resolution/grid, nearest-neighbor, raster function `None`, and locks the catalog raster rather than using the default/latest mosaic or colors. [Esri numeric export API](https://developers.arcgis.com/rest/services-reference/enterprise/export-image/).

## Formula and Coverage

For each tract, `I = sum_j(a_j * FIS_j/100) / sum_j(a_j)`, where `a_j` is exact tract/cell intersection area for valid **non-water** cells. Land-cover class 11 is excluded as open water; wetlands remain land. Valid zero-impervious land stays in the denominator. Joint invalid FIS/land-cover cells are missing, not zero. Whole-tract valid-area means are also retained as a different estimand. Census AWATER is not a spatial mask and was not used to remove pixel areas. Classified water need not equal legal Census water area.

`exactextract` computes fractional boundary-cell coverage on this equal-area grid; 900 m2 per cell converts its sums/counts to area. No vector-to-raster center approximation or deliberate raster reprojection is used for the primary result. [Algorithm documentation](https://isciences.github.io/exactextract/).

- **2,315/2,315 geometry/GEOID matches; zero unmatched**, including **2,291/2,291 residential members**.
- All study tracts have a defined valid-land mean. NoData intersection area is **0 m2**. Minimum valid-area coverage is **99.99999985%**, within floating-point area tolerance of complete coverage; all pass the 99% audit threshold.
- Explicitly excluded mapped open water: **83.528 km2** across the full domain. Smallest tract has **51.016** valid-land cell equivalents. This establishes numeric coverage, not mapping accuracy for every tract.
- Residential impervious mean medians/IQR: overall median **65.14%**, IQR **57.95-71.87%**. C1-C5 mean values: **67.72, 64.83, 66.23, 51.76, 64.29%**; medians **67.53, 66.13, 65.38, 54.23, 67.45%**. These are **pilot mirror-derived results** until the release gate closes.

## Aggregation and Reproducibility Checks

Independent Shapely polygon/cell intersections for 16 tracts (eight smallest, eight seeded random) agree with the primary fraction means to **1.321e-10** maximum absolute difference. Repeating the full zonal extraction is bitwise equal; independently downloading a 128x128 subwindow reproduces every pixel and the geotransform. Both numeric clips and the subwindow are archived with SHA-256; remote export links are temporary, while request URLs/catalog metadata reproduce the query.

Across all 2,315 tracts, center-cell means differ from exact aggregation by at most **0.2915 pp**, p95 **0.0946 pp**; all-touched means by at most **2.5724 pp**, p95 **1.1723 pp**. These test aggregation choices, not land-cover classification error. Removing water changes means by as much as **55.69 pp**: tract **06037576602** is 89.34% mapped water, and its mean is **62.34% over valid land versus 6.65% over the whole tract**. Whole-tract and land-normalized values must not be interchanged.

No tract-level impervious accuracy confidence interval is invented. Spatial resolution, classified water boundaries and remote-sensing estimation errors remain distinct from ACS sampling MOEs. The statistical tables hold labels fixed; no existing figure is regenerated.

## Exact Blockers and How to Close Them

The official Annual WCS advertises a numeric coverage/time domain, but four WCS2 time variants return HTTP 200 **XML exceptions**, including `Cannot invoke "Object.getClass()" because "startTime" is null`; WCS1 returns `Could not understand version:1.0.0`. A TIFF header/content validation prevents these errors being treated as rasters. `NLCD_PROBE_LOG.json` records URLs, status and response; capability/description snapshots are retained. Public USGS S3 was requester-pays in the official guide; an earlier unauthenticated listing returned 403, which is not evidence that every data-acquisition route is unavailable.

The successful mirror item **6df535f263dd44f489365eed49461a38**, publisher `esri_environment`, explicitly states beta/not recommended for production, and its item-level version description disagrees with the selected 2022 catalog build. [Publisher item metadata](https://www.arcgis.com/sharing/rest/content/items/6df535f263dd44f489365eed49461a38?f=pjson). Thus extraction/geometry/numeric reproducibility pass, but the **authoritative production-source gate remains open**. NLCD is CONDITIONAL, not READY. No comparison to an original USGS file or to Collection 1.2 was completed.

Acquisition route: use the [official MRLC Viewer](https://www.mrlc.gov/viewer/) with a single-part polygon containing the study extent, select year 2022 and both fractional impervious/land cover, obtain the delivered GeoTIFFs and product metadata; alternatively obtain USGS tiles/COGs via EarthExplorer or authorized requester-pays S3. Do not assume an old bundle and current release are identical. Record release/build, exact input hashes, no-data codes and CRS; use the actual raster grid.

`nlcd.py --repo <checkout> --phase reference --fis-raster <file> --lc-raster <file> --reference-out <new-directory> --reference-build <documented-build>` provides the offline authoritative-file path. It clips even a large local CONUS raster on its native grid, performs the same aggregation/geographic QA in a **new output directory**, and compares it with this pilot. The declared build remains user-supplied until original source/metadata review; the script cannot automatically certify provenance. An intentional newer-build choice needs the corresponding guide and reported change distribution, not pixel equality to C1.0. Only after that source gate passes can Option A's impervious descriptor be adopted.

The exact upstream TIGER boundary-release year was not independently recovered from the shapefile's sidecars. This audit uses the same hashed study polygons and 2020-based IDs as existing Stage 7 maps, with 2,315 exact matches; it does not claim to have authenticated a specific TIGER download edition. Retain this distinction in eventual source metadata.
