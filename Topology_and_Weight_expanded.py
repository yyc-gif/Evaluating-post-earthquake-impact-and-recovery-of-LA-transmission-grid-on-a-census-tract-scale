"""Expanded-area counterpart for the topology + mapping builder."""

from pathlib import Path

import Topology_and_Weight as base


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "Data"


EXPANDED_PATHS = base.Paths(
    DEVICES_CSV=str(DATA_DIR / "working_area_substations_with_fragility.csv"),
    LA_TRACTS_SHP=str(DATA_DIR / "LA_Tracts_With_Population.shp"),
    TRANSMISSION_LINES_SHP=str(DATA_DIR / "TransmissionLine_CEC.shp"),
    CITY_TRACTS_LIST_CSV=str(DATA_DIR / "Tracts_Within_Expanded_Area.csv"),
    OUTPUT_MAPPING_CSV=str(DATA_DIR / "tract_to_substation_mapping_CEC_expanded.csv"),
    OUTPUT_GRAPH_EDGES_CSV=str(DATA_DIR / "substation_graph_CEC_edges_expanded.csv"),
    OUTPUT_GRAPH_NODES_CSV=str(DATA_DIR / "substation_graph_CEC_nodes_expanded.csv"),
    OUTPUT_PLOT_PNG=None,
    OUTPUT_INTERACTIVE_HTML=str(DATA_DIR / "topology_interactive_validation_expanded.html"),
    OUTPUT_SUPPRESSED_THRESHOLD_CSV=str(DATA_DIR / "substations_suppressed_by_threshold_expanded.csv"),
    OUTPUT_LINE_SPLIT_AUDIT_CSV=str(DATA_DIR / "transmission_line_substation_split_audit_expanded.csv"),
    OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_AUDIT_CSV=str(DATA_DIR / "direct_link_projection_anchor_audit_expanded.csv"),
    OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_DEBUG_CSV=str(DATA_DIR / "direct_link_projection_anchor_debug_expanded.csv"),
    LINE_SNAP_SECONDARY_TOLERANCE_M=375.0,
    LINE_SNAP_SECONDARY_OUTER_START_M=300.0,
    LINE_SNAP_SECONDARY_OUTER_MARGIN_M=300.0,
    LINE_SNAP_SECONDARY_OUTER_RATIO_MAX=0.55,
    MAX_SUBSTATION_TO_GRAPH_SNAP_DIST_M=250.0,
    ENABLE_PROTECTED_JUNCTION_CLUSTER_SNAP=True,
    LINE_SPLIT_TOLERANCE_M=10.0,
)


def main():
    """Run the topology-and-weight preprocessing workflow for the expanded study area."""
    base.main(EXPANDED_PATHS)


if __name__ == "__main__":
    main()
