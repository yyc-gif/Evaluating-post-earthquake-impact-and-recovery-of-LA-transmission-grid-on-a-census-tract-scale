# Data Sources, Terms, and Redistribution Notes

The repository combines third-party source material with study-specific
derivatives. Inclusion in this repository does not transfer ownership or place
third-party material under the repository's MIT License. Provider pages and
terms may change; users are responsible for confirming the terms that apply to
their use and redistribution.

| Dataset/source name | Provider | Purpose in this study | Original URL | Repository content | License or terms note | Redistribution note |
|---|---|---|---|---|---|---|
| OpenStreetMap road network | OpenStreetMap contributors | Static pre-event driving network used to calculate crew-base-to-task and task-to-task travel times | <https://www.openstreetmap.org/> | A prepared study-area derivative is retained as `Data/la_drive.graphml`; the full original OSM database is not included | See the [OpenStreetMap copyright and license page](https://www.openstreetmap.org/copyright) and consult the current provider terms | Preserve required OpenStreetMap attribution and comply with the current database-license terms when redistributing derivatives |
| California electric transmission lines | California Energy Commission (CEC) | Physical transmission-line geometry used to construct the topology | <https://gis.data.ca.gov/datasets/CAEnergy::california-electric-transmission-lines-1/about> | A working input layer is retained as `Data/TransmissionLine_CEC.*`; reduced graph outputs are study derivatives | Users should consult the original provider's current terms of use | Do not assume that the repository MIT License applies to the CEC source layer; verify redistribution and attribution requirements with CEC |
| California electric substations | California Energy Commission (CEC) | Substation locations and attributes used in the study-area inventory and topology | <https://hub.arcgis.com/datasets/c2d4e65fe7b84c67a94e98ff9555c3ac_0> | Study-area and derived substation tables are retained; the repository does not present them as original project data | Users should consult the original provider's current terms of use | Cite the provider and review the current terms before redistributing source attributes |
| California Geological Survey Map Sheet 48 | California Geological Survey | Source for the 2%-in-50-year ground-motion scenario input | <https://www.conservation.ca.gov/cgs/publications/ms48> | The repository contains the scenario grid file used by the workflow under `Data/MS_048_CA_pt01_MMI_GM_datafiles/` | Users should consult the original provider's current terms of use | Redistribute only when permitted by the provider and retain source attribution |
| USGS ShakeMap | U.S. Geological Survey | Historical Northridge, San Fernando, and Long Beach PGA scenario fields | <https://earthquake.usgs.gov/data/shakemap/> | Scenario-specific CoverageJSON inputs are retained in `Data/` | Users should consult the original provider's current terms of use | Preserve USGS attribution and review the provider's current reuse guidance |
| National Risk Index | Federal Emergency Management Agency (FEMA) | Tract-level hazard and risk indicators used in the vulnerability analysis | <https://www.fema.gov/flood-maps/products-tools/national-risk-index> | A California tract table is retained as `Data/NRI_Table_CensusTracts_California.csv`; study outputs are derivatives | Users should consult the original provider's current terms of use | Do not treat the repository copy as project-owned data; cite FEMA and verify current redistribution terms |
| TIGER/Line census tract boundaries | U.S. Census Bureau | Census-tract geometry used for mapping and tract-level aggregation | <https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html> | Study-area tract geometry and derivatives are retained under `Data/` | Users should consult the original provider's current terms of use | Retain Census source attribution and verify any applicable notices for redistributed extracts |
| American Community Survey (ACS) | U.S. Census Bureau | Population and housing indicators, including the pre-1970 housing measure | <https://api.census.gov/data.html> | Selected tables and study-area derivatives are retained under `Data/` | Users should consult the original provider's current terms of use | Cite the ACS dataset and vintage used; do not imply that the repository created the source estimates |
| CDC/ATSDR Social Vulnerability Index | Centers for Disease Control and Prevention / Agency for Toxic Substances and Disease Registry | Tract-level social-vulnerability variables and composite scores | <https://www.atsdr.cdc.gov/place-health/php/svi/index.html> | Source-like state data and study-area derivatives are retained under `Data/` | Users should consult the original provider's current terms of use | Preserve CDC/ATSDR attribution and check current redistribution guidance |
| HIFLD electric substations | Homeland Infrastructure Foundation-Level Data / data.gov | Substation identifiers and source attributes retained in the working inventory | <https://catalog.data.gov/dataset/electric-substations> | HIFLD-derived attributes appear in study-area and derived substation tables | Users should consult the original provider's current terms of use | Review the catalog record and current HIFLD/data.gov terms before redistributing source attributes |
| City of Los Angeles GeoHub | City of Los Angeles | Municipal spatial context and source data used in study-area processing, including healthcare-related spatial association | <https://geohub.lacity.org/> | The repository retains study derivatives such as hospital-tract associations rather than claiming ownership of source layers | Users should consult the original provider's current terms of use | Cite the City of Los Angeles source and confirm current terms before redistributing source-layer content |

## Repository-Specific Notes

- `Data/README.md` identifies the source-like inputs, derived workflow inputs,
  and validation outputs used by the scripts.
- Some CEC/HIFLD-derived CSV files retain a `path` metadata field containing a
  historical local GIS source path. The workflow does not read this field; it
  is retained only as source-layer metadata and should not be interpreted as a
  required runtime path.
- Derived topology, tract-dependency, sensitivity, and recovery outputs remain
  subject to the terms of any third-party source data from which they were
  produced.
