"""Observable July source gate. No schedule, sampling, mapping or capacity logic."""
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np
import pandas as pd
import networkx as nx

@dataclass(frozen=True)
class GateTrace:
    f: pd.DataFrame
    F: pd.DataFrame
    C: pd.DataFrame
    e: pd.DataFrame
    L_self: pd.DataFrame
    L_threshold: pd.DataFrame
    L_source: pd.DataFrame
    L_total: pd.DataFrame
    threshold: float
    source_ids: tuple
    mode: str


def evaluate_source_gate(raw, graph, source_ids, *, threshold=.5, mode='source_gate'):
    """C=0 for threshold-ineligible nodes; NA for unknown raw state.

    Unknown states are unavailable to graph traversal, not numeric zero evidence.
    This yields conditional reachability given the known-functional subgraph.
    """
    if mode not in {'source_gate','no_gate'} or not 0 < threshold <= 1:
        raise ValueError('Invalid gate mode/threshold')
    if raw.empty or raw.index.has_duplicates or raw.columns.has_duplicates:
        raise ValueError('Explicit unique event and station identities required')
    if not all(isinstance(x,str) and x for x in raw.columns) or set(raw.columns)!=set(graph):
        raise ValueError('Exact graph/trajectory station identity required')
    times=np.asarray(raw.index,float)
    if not np.isfinite(times).all() or np.any(np.diff(times)<=0):
        raise ValueError('Strictly increasing finite event times required')
    sources=tuple(sorted(set(source_ids)))
    if not sources or not set(sources).issubset(graph):
        raise ValueError('Explicit valid source set required; no ungated fallback')
    x=raw.to_numpy(float,copy=True); known=~np.isnan(x)
    if np.isinf(x).any() or np.any((x[known]<0)|(x[known]>1)):
        raise ValueError('Raw state outside [0,1]')
    if np.any(known != known[0]):
        raise ValueError('Identified station domain must be static within trajectory')
    F=known & (x>=threshold); C=np.zeros_like(F); cache={}
    for i in range(len(x)):
        key=F[i].tobytes()
        if key not in cache:
            nodes=set(raw.columns[F[i]]); active=set(sources)&nodes; keep=set()
            for component in nx.connected_components(graph.subgraph(nodes)):
                if component & active: keep.update(component)
            cache[key]=np.array([s in keep for s in raw.columns])
        C[i]=cache[key]
    if mode=='no_gate':
        # Identity-gate accounting, not a claim of physical connectivity.
        F=known.copy(); C=known.copy()
    e=x*F*C
    arrays={'f':x,'F':F.astype(float),'C':C.astype(float),'e':e,
            'L_self':1-x,'L_threshold':x*(1-F),'L_source':x*F*(1-C),'L_total':1-e}
    for value in arrays.values():value[~known]=np.nan
    np.testing.assert_allclose(arrays['L_self']+arrays['L_threshold']+arrays['L_source'],arrays['L_total'],rtol=0,atol=1e-12,equal_nan=True)
    frames={k:pd.DataFrame(v,index=raw.index.copy(),columns=raw.columns.copy()) for k,v in arrays.items()}
    return GateTrace(**frames,threshold=float(threshold),source_ids=sources,mode=mode)


def gate_callback(graph, source_ids, *, threshold=.5):
    """Callback accepted by the revised paired scheduler; retains f/F/C/e."""
    return lambda raw:evaluate_source_gate(raw,graph,source_ids,threshold=threshold)


def save_gate_trace(trace, path, *, realization_id, strategy_id):
    payload={k:getattr(trace,k).to_numpy() for k in ['f','F','C','e','L_self','L_threshold','L_source','L_total']}
    payload.update(station_ids=np.array(trace.f.columns,dtype=str),event_time_hr=np.array(trace.f.index,float),
        metadata_json=np.array(json.dumps(dict(realization_id=str(realization_id),strategy_id=str(strategy_id),threshold=trace.threshold,source_ids=trace.source_ids,mode=trace.mode))))
    np.savez_compressed(Path(path),**payload)
