# Data Directory

Large files in this directory are managed with Git LFS. Run `git lfs pull`
after cloning the repository.

## Source Inputs

- `LA_Tracts_With_Population.*`: census-tract geometry and population data.
- `TransmissionLine_CEC.*`: California Energy Commission transmission lines.
- `working_area_substations_with_fragility.csv`: final study-area substations
  and fragility parameters.
- `Northridge_PGA.covjson`, `SanFernando_PGA.covjson`, and
  `LongBeach_PGA.covjson`: historical earthquake PGA fields.
- `MS_048_CA_pt01_MMI_GM_datafiles/CA_pt01_GM_maps.csv`: 2%-in-50-year PGA
  field used by the manuscript workflow.
- `la_drive.graphml`: prepared OpenStreetMap driving network.
- `California.csv`, `NRI_Table_CensusTracts_California.csv`,
  `ACSDT5Y2022.B25034-Data.csv`, and
  `LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv`: tract vulnerability,
  risk, housing, and social-vulnerability inputs.
- `hospital_with_tract_expanded.csv`: processed hospital-tract associations.
- `stage45_depot_inputs_final_origin_proxy.csv`: active crew-yard inputs.

## Derived Workflow Inputs

- `Substations_PGA_IDW_CEC_expanded.csv`: interpolated substation PGA values.
- `substation_graph_CEC_nodes_expanded.csv` and
  `substation_graph_CEC_edges_expanded.csv`: reduced substation topology.
- `tract_to_substation_mapping_CEC_expanded.csv`: final tract-substation
  dependency weights.
- `tract_to_substation_mapping_CEC_expanded_unthresholded.csv`: source mapping
  used by the IDW-threshold sensitivity analysis.
- `source_nodes_core_expanded.csv`: active-source identifiers.
- `Tracts_Within_Expanded_Area.csv`: accepted study-area tract list.

## Validation Outputs

- `topology_final_validation_expanded.png`: static topology validation figure.
- `topology_interactive_validation_expanded.html`: interactive topology map.
- `sensitivity_summary_2pc50.csv` and
  `sensitivity_mapping_diagnostics.csv`: sensitivity-analysis source tables.

The repository intentionally excludes unused alternate hazard layers, old
city-only outputs, audit packages, and files that can be regenerated directly
from the official workflow.
