> EXPLORATORY MULTI-HAZARD INDEX AUDIT — NOT FORMAL STAGE 7

# Verified Columbia NHI v2.0

The actual provider dataset was retrieved, not inferred from a historical endpoint. The official NCDP page links Experience app fda2d684cd3f4ed5b802818a298d1b1a; archived app data links webmap1ddc2479ea4b4fe491fd776843c73cf6, whose layer resolves to FeatureServer/77, item ecdfbee171bb4224b7c47862c6e484a5. Layer description specifies 2010 Census tracts. Ancillary POP2020 is not a geometry-vintage declaration.

The OID inventory has2343 LA features. Twenty-four100-OID GeoJSON requests reproduce exactly that inventory without result-offset pagination, simplified geometry or silent duplicate removal.400-ID query failures are preserved as failed responses, not data. All fourteen raw indicator values, category numbers, textual labels, original geometry and hazsum5 are archived. Published sum equals sum of available categories, with NULL contributing zero only to reconstruct provider arithmetic: maximum absolute error0.

Ratings represent1-5 ordinal severity bins, with explicit0 tsunami footprint values. No-data and no-hazard both affect the provider sum as zero; these conditions cannot be inferred separately from a NULL rating. Original records remain unmodified. Sources/years are preserved in the official app documentation tables1/2. Earthquake categories are saturated:2341 of2343 source tracts are5, two are4. Local winter class is constant1; drought is5 in2307 source tracts. Locally varying heat, flood, landslide and wildfire categories account for much of the summed variation; precise signed covariance shares are in CANDIDATE_LOCAL_COMPONENT_ATTRIBUTION.csv, not a declaration of independent hazard importance.

Wildfire RPS combines burn probability with a generic response of a hypothetical structure, not actual house counts, income or monetary building value. Nevertheless this is not a pure physical-intensity coordinate. See archived USFS source. The broader NHI omits social/resilience/value adjustment but retains heterogeneous classification and generic response assumptions.

- [Columbia NCDP official NHI v2.0](https://ncdp.columbia.edu/us-natural-hazards-index/)
- [Verified Columbia ArcGIS layer77](https://services2.arcgis.com/IsDCghZ73NgoYoz5/ArcGIS/rest/services/Hazards_Index_Sum/FeatureServer/77)
- [Census California 2010-to-2020 tract relationship](https://www2.census.gov/geo/docs/maps-data/data/rel2020/tract/tab20_tract20_tract10_st06.txt)
- [Matching FEMA March2023 v1.19 technical documentation, official Ohio mirror](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)
- [Williams, Summers and Harwell2024](https://doi.org/10.3390/su162310778)
- [Publisher's archived PDF](https://mdpi-res.com/d_attachment/sustainability/sustainability-16-10778/article_deploy/sustainability-16-10778.pdf)
