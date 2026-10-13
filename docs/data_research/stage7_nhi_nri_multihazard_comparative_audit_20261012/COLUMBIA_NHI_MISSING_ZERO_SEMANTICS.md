> EXPLORATORY MULTI-HAZARD INDEX AUDIT — NOT FORMAL STAGE 7

# Columbia missingness and geographic gate

NULL is retained in all source fields. Provider arithmetic uses zero for unknown or absent hazard, but a summed numerical score is not full fourteen-hazard observation. None of2299 target tracts has fourteen non-null source components. Volcano and hurricane are NULL in every LA source tract; hail, tornado and damaging-wind records are mostly NULL. Tsunami has explicit raw/category0 outside its modeled footprint; it indicates the layer's geographic exclusion, not proof of physically impossible tsunami. Text label NaN on those numeric zeros is retained separately.

Official TIGER2010 has2346 LA tracts, whereas the NHI service has2343. Missing donors06037990100,06037990200,06037990300 have zero land in the archived2010 TIGER edition. The Census2020 relationship's updated2010 geography assigns small land parts to these codes; the two editions must not be treated as geometrically identical. Eleven targets lack some official donor land, representing46,455 residents. Lowest supported land fraction is0.955864. These eleven are retained and flagged, not dropped or filled. The ordinal land-average estimate is unavailable on inadequately covered targets; dominant donor values remain explicitly estimates.

Exact identifier matches:1887/2299. Relationship types:

| relationship   |   tracts |
|:---------------|---------:|
| one_to_one     |     1434 |
| one_to_many    |      471 |
| many_to_many   |      387 |
| many_to_one    |        7 |

All polygon intersections use equal-area EPSG3310; invalid polygons alone use make_valid, not buffer or arbitrary clipping. Geometric total-area overlaps, union coverage and partition excess are reported separately from the official LAND-area relationship used for transfer. Identical identifiers do not imply identical boundaries. Dominant-land-source categories and fractional class compositions are screening transfers, not reconstructed2020 physical hazard intensity. Area-averaged ordinal values are researcher diagnostics only.

Admission: EXPLORATORY_ONLY for original14 score. Do not fit this vector to the primary cohort or repair NULL by assumed zero. A missingness-aware sum of seven commonly complete layers would change the declared index and still inherit source/projection uncertainty; no replacement index is promoted here.
