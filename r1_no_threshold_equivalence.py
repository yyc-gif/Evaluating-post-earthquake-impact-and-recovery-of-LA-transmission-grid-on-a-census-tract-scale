"""Audit whether July92 positive functionality makes a zero-threshold gate degenerate.

Reads saved formal and equity-amendment f arrays. Does not re-evaluate a
scientific trajectory, schedule, or alternative scenario.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from r1_equity_amendment_execute import ROOT, FORMAL, AMEND
from r1_formal_dynamic_topology import _case_catalog
from r1_realization_scheduling import INITIAL_BY_DS


def audit_no_threshold_connectivity() -> dict:
    cases, original_index = _case_catalog(FORMAL)
    edges = pd.read_csv(ROOT / "Data" / "substation_graph_CEC_edges_expanded.csv",
                        dtype={"u": str, "v": str})
    graph = nx.from_pandas_edgelist(edges, "u", "v")
    sources_file = ROOT / "Data" / "source_nodes_core_expanded.csv"
    sources = set(pd.read_csv(sources_file, dtype={"ID": str}).query("level == 'Core'").ID)
    if len(graph) != 92 or graph.number_of_edges() != 318 or len(sources) != 14:
        raise ValueError("Frozen graph or source identities differ")
    components = list(nx.connected_components(graph))
    if any(not component & sources for component in components):
        raise ValueError("Full positive-functionality graph has a sourceless component")
    if any(float(INITIAL_BY_DS[d]) <= 0 for d in range(5)):
        raise ValueError("July DS residual functionality is not all positive")
    result = dict(status="FORMAL_EQUITY_AMENDMENT_EXPLANATORY_DIAGNOSTIC",
                  definition="C_positive uses all f>0 stations and active Core sources; e=f*C_positive",
                  original_trajectory_count=0,amendment_trajectory_count=0,
                  total_known_event_station_cells=0,minimum_known_f=1.0,
                  minimum_source_f=1.0,nonpositive_f_cells=0,missing_f_cells=0,
                  full_graph_station_count=len(graph),full_graph_edge_count=graph.number_of_edges(),
                  full_graph_component_count=len(components),
                  source_count=len(sources),
                  initial_functionality_by_DS={str(k):float(INITIAL_BY_DS[k]) for k in range(5)},
                  original_archive_index_sha256=hashlib.sha256(
                      (FORMAL/"FORMAL_TRAJECTORY_ARCHIVE_INDEX.json").read_bytes()).hexdigest(),
                  amendment_index_sha256=hashlib.sha256(
                      (AMEND/"VULNERABILITY_TRAJECTORY_INDEX.json").read_bytes()).hexdigest())
    for hazard,catalog in cases.items():
        for sample in range(1000):
            stem=f"{hazard}__evaluation_{sample:04d}.npz"
            paths=[FORMAL/"Formal_Trajectories"/hazard/resource/strategy/stem
                   for resource,strategy in catalog]
            paths += [AMEND/"T"/hazard/resource/stem for resource in
                      (["C57_D1","C29_D1","C86_D1","C114_D1","C57_D075","C57_D125","C57_D150"]
                       if hazard=="2pc50" else ["C57_D1"])]
            for i,path in enumerate(paths):
                with np.load(path,allow_pickle=False) as z:
                    ids=z["station_ids"].astype(str).tolist()
                    if len(ids)!=92 or set(ids)!=set(graph):
                        raise ValueError("Formal f station/graph domain changed")
                    f=z["f"]
                    source_indices=[ids.index(s) for s in sources]
                    if not np.isfinite(f).all():
                        result["missing_f_cells"]+=int((~np.isfinite(f)).sum())
                        raise ValueError("Formal f has missing/nonfinite cells")
                    result["total_known_event_station_cells"]+=int(f.size)
                    result["minimum_known_f"]=min(result["minimum_known_f"],float(f.min()))
                    result["minimum_source_f"]=min(result["minimum_source_f"],float(f[:,source_indices].min()))
                    result["nonpositive_f_cells"]+=int((f<=0).sum())
                result["original_trajectory_count" if i<len(catalog) else
                       "amendment_trajectory_count"]+=1
    if (result["original_trajectory_count"]!=84000 or
            result["amendment_trajectory_count"]!=10000 or
            result["nonpositive_f_cells"]!=0 or result["minimum_source_f"]<=0):
        raise ValueError("No-threshold equivalence conditions are not met")
    result["C_positive_all_known_states"]=True
    result["e_equals_f_on_all_known_states"]=True
    result["equivalent_existing_case"]="G0_NO_GATE"
    result["conclusion"]=("Under the retained DS residual states and full 92-node source-reachable "
                          "graph, removing the binary functionality threshold makes all "
                          "stations and 14 sources passable at every saved event; thus C_positive=1 "
                          "and e=f. This does not model continuous MW transfer capacity.")
    output=AMEND/"NO_THRESHOLD_CONNECTIVITY_EQUIVALENCE.json"
    if output.exists():raise ValueError("Refuse to overwrite no-threshold equivalence record")
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


if __name__=="__main__":
    print(json.dumps(audit_no_threshold_connectivity(),indent=2))
