"""CLI for existing event-state NPZ archives. Never executes the physical pipeline."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,networkx as nx
from r1_mapping import ROOT
from r1_topology_robustness import characterize_topology,dynamic_redundancy,source_loss_contributions
from r1_mapping_gate_robustness import mapping_cases,evaluate_saved_trajectory,paired_effects,paired_assumption_effects,tract_effects

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--index',required=True,help='CSV: realization_id,strategy_id,npz_file; paths relative to index');parser.add_argument('--output',required=True);parser.add_argument('--reference-strategy',required=True);args=parser.parse_args()
    index_path=Path(args.index).resolve();index=pd.read_csv(index_path,dtype=str)
    if index.duplicated(['realization_id','strategy_id']).any():raise ValueError('Duplicate archive keys')
    sets=index.groupby('realization_id').strategy_id.agg(lambda x:tuple(sorted(x)))
    if len(set(sets))!=1:raise ValueError('Incomplete paired strategy archive')
    output=Path(args.output);output.mkdir(exist_ok=False,parents=True)
    edges=pd.read_csv(ROOT/'Data/substation_graph_CEC_edges_expanded.csv',dtype={'u':str,'v':str});g=nx.from_pandas_edgelist(edges,'u','v')
    source=pd.read_csv(ROOT/'Data/source_nodes_core_expanded.csv',dtype={'ID':str});sources=source.loc[source.level.eq('Core'),'ID'].tolist()
    meta=pd.read_csv(ROOT/'R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv',dtype={'tract_id':str}).set_index('tract_id')
    maps,_=mapping_cases();summary=[];tract=[]
    topology=characterize_topology(g,sources);topology.to_csv(output/'STATIC_TOPOLOGY.csv')
    for row in index.itertuples():
        with np.load(index_path.parent/row.npz_file,allow_pickle=False) as z:
            raw=pd.DataFrame(z['f'],index=z['event_time_hr'],columns=z['station_ids'].astype(str))
            md=json.loads(str(z['metadata_json']))
            if str(md['realization_id'])!=row.realization_id or str(md['strategy_id'])!=row.strategy_id:raise ValueError('Archive identity mismatch')
        a,b,traces=evaluate_saved_trajectory(raw,g,sources,maps,meta.population,meta.SOVI_quartile,set(meta.index[meta.hospital_tract]),realization_id=row.realization_id,strategy_id=row.strategy_id)
        summary.append(a);tract.append(b)
        baseline_trace=traces['G1_BASELINE_050']
        dynamic_redundancy(baseline_trace,g).to_parquet(output/(row.realization_id+'__'+row.strategy_id+'__DYNAMIC_TOPOLOGY.parquet'),index=False)
        contributions=[]
        for gate,trace in traces.items():
            if gate=='G0_NO_GATE':continue
            for mapping,w in maps.items():
                z=source_loss_contributions(trace,w,meta.population,topology).rename_axis('station_id').reset_index()
                contributions.append(z.assign(mapping=mapping,gate=gate,realization_id=row.realization_id,strategy_id=row.strategy_id))
        pd.concat(contributions,ignore_index=True).to_parquet(output/(row.realization_id+'__'+row.strategy_id+'__SOURCE_CONTRIBUTIONS.parquet'),index=False)
        arrays={k+'__'+field:getattr(v,field).to_numpy() for k,v in traces.items() for field in ['F','C','e','L_self','L_threshold','L_source']}
        arrays.update(f=raw.to_numpy(),event_time_hr=np.asarray(raw.index),station_ids=np.array(raw.columns,dtype=str))
        np.savez_compressed(output/(row.realization_id+'__'+row.strategy_id+'.npz'),**arrays)
    a=pd.concat(summary,ignore_index=True);b=pd.concat(tract,ignore_index=True)
    a.to_csv(output/'SUMMARY.csv',index=False);b.to_parquet(output/'TRACT_BURDEN.parquet',index=False)
    tract_effects(b,meta.population,meta.SOVI_quartile,reference_strategy=args.reference_strategy).to_parquet(output/'TRACT_EFFECTS.parquet',index=False)
    metrics=[c for c in a if c.endswith('_hr') or c=='burden_gini']
    pd.concat([paired_effects(a,m,reference_strategy=args.reference_strategy).assign(metric=m) for m in metrics]).to_csv(output/'PAIRED_STRATEGY_EFFECTS.csv',index=False)
    pd.concat([paired_assumption_effects(a,m) for m in metrics]).to_csv(output/'PAIRED_ASSUMPTION_EFFECTS.csv',index=False)
if __name__=='__main__':main()
