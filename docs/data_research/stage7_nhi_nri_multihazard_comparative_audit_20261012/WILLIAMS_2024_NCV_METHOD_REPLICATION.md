> EXPLORATORY MULTI-HAZARD INDEX AUDIT — NOT FORMAL STAGE 7

# Published-method versus exact implementation

Both the official publisher's13-page PDF and EuropePMC accepted XML were acquired, hashed and read. Sections2.1-2.3 on publisher pages4-5 specify the hazard factor:

NCV_h = AFREQ_h * (EXP_AREA_h / AREA).

Then independently min-max each hazard, sum normalized hazards, and min-max the sum. Empirical analysis is county-level; the denominator definition also mentions Census tracts, but this does not validate tract aggregation. The individual earthquake map is Figure7. Published comparisons address susceptible-area fractions, individual hazard factors, histograms and maps, not our electricity-restoration typology.

Exact aggregate replication is NOT achieved: the Methods says nine combined hazards but Table1 lists all18 available NRI types, without an explicit aggregate-nine list. The original normalization universe/extrema, missing/not-applicable and zero-range rules and a reproducible county result workbook are not supplied in acquired materials. The published Data Availability text points to a local network-drive location rather than a usable public file. No supplementary numerical table or exact source-version snapshot was acquired. The paper's source access date is January2024, whereas our input remains frozen March2023 v1.19. Reference to CRSI's hazard set is not permission to guess the aggregate list.

The mathematical frequency-area operator is independently reproduced on actual frozen tract rows (WILLIAMS_FACTOR_REAL_SOURCE_EXAMPLES.csv), including ERQK, WFIR, RFLD and HWAV. These examples are real source calculations, not falsely attributed published county examples. The fourteen-hazard extension and California normalization are separately registered before fitting. Original exact-nine implementation stays FAIL_SOURCE_RECONSTRUCTION; the tract extension has a qualified full-cohort modeled-input gate.

- [Columbia NCDP official NHI v2.0](https://ncdp.columbia.edu/us-natural-hazards-index/)
- [Verified Columbia ArcGIS layer77](https://services2.arcgis.com/IsDCghZ73NgoYoz5/ArcGIS/rest/services/Hazards_Index_Sum/FeatureServer/77)
- [Census California 2010-to-2020 tract relationship](https://www2.census.gov/geo/docs/maps-data/data/rel2020/tract/tab20_tract20_tract10_st06.txt)
- [Matching FEMA March2023 v1.19 technical documentation, official Ohio mirror](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)
- [Williams, Summers and Harwell2024](https://doi.org/10.3390/su162310778)
- [Publisher's archived PDF](https://mdpi-res.com/d_attachment/sustainability/sustainability-16-10778/article_deploy/sustainability-16-10778.pdf)
