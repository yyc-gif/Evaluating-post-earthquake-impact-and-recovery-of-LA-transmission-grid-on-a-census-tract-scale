"""Read retained event traces to expose the jointly required source-gate paths."""
from __future__ import annotations
import json
import networkx as nx
import pandas as pd

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_research_collect_20261009 import ROOT, long_path, save


def main():
    out = ROOT/"continuation"
    a = json.loads(long_path(out/"SAMPLE15_FirstILS_EVENTS.json").read_text())
    b = json.loads(long_path(out/"FrozenGA_move_301745_62_to_21_SAMPLE15_EVENTS.json").read_text())
    time = next(r["finish_hr"] for r in a["station_schedule"] if r["station"]=="301745")
    left = max((e for e in a["events"] if e["time_hr"]<=time), key=lambda e:e["time_hr"])
    right = max((e for e in b["events"] if e["time_hr"]<=time), key=lambda e:e["time_hr"])
    functional = set(sum((c["stations"] for c in left["components"]), []))
    controlled_functional = set(sum((c["stations"] for c in right["components"]), []))
    edges = pd.read_csv(REPO_ROOT/"Data/substation_graph_CEC_edges_expanded.csv", dtype={"u":str,"v":str})
    graph = nx.from_pandas_edgelist(edges,"u","v")
    assert len(graph)==92 and graph.number_of_edges()==318
    induced = graph.subgraph(functional)
    schedule = {s["station"]:s for s in b["station_schedule"]}
    rows = []
    for station in left["newly_source_connected_stations"]:
        paths = [nx.shortest_path(induced, station, source) for source in left["active_sources"]
                 if nx.has_path(induced, station, source)]
        path = min(paths, key=lambda p:(len(p),p))
        missing = [s for s in path if s not in controlled_functional]
        rows.append(dict(station=station, representative_ils_functional_path_to_source=path,
            inactive_path_stations_in_ga_early_intervention=missing,
            inactive_station_completions={s:schedule[s]["finish_hr"] for s in missing},
            source_connected_under_ils=station in left["source_connected_stations"],
            source_connected_under_ga_early_intervention=station in right["source_connected_stations"]))
    result = dict(time_hr=time, common_301745_completion_hr=next(s["finish_hr"] for s in b["station_schedule"] if s["station"]=="301745"),
        first_ils_connected_count=len(left["source_connected_stations"]),
        ga_early_intervention_connected_count=len(right["source_connected_stations"]),
        inactive_along_representative_paths=sorted(set(sum((r["inactive_path_stations_in_ga_early_intervention"] for r in rows),[]))),
        paths=rows, physical_source_gate_changed=False,
        interpretation="Representative shortest-hop active ILS paths; not unique electrical flows or proof all alternatives use these stations")
    save(out/"SAMPLE15_CONTROLLED_SOURCE_PATHS.json", result)
    print("JOINT_SOURCE_PATHS", result["inactive_along_representative_paths"],
          result["first_ils_connected_count"], result["ga_early_intervention_connected_count"])


if __name__ == "__main__":
    main()
