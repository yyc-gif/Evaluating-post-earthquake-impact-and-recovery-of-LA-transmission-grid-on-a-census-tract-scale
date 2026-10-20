"""Exact rational arithmetic for the monotone unlimited-crew relaxation."""
from fractions import Fraction as F
import json,math
import numpy as np,networkx as nx
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,load
from la_grid.revision.r1_realization_scheduling import INITIAL_BY_DS


def main():
    k,_,_=load();g=nx.Graph();g.add_nodes_from(range(92))
    for i in range(92):g.add_edges_from((i,int(j)) for j in k.neighbors[k.neighbor_offset[i]:k.neighbor_offset[i+1]])
    weights=[F.from_float(float(v)) for v in k.station_mass];total=F.from_float(float(k.total_mass));horizon=F.from_float(float(k.horizon));results=[]
    for b in range(64):
        times=sorted(set([F(0),horizon]+[F.from_float(float(k.duration[b,j])) for j in range(92) if k.damage[b,j]>0]));value=F(0)
        for left,right in zip(times[:-1],times[1:]):
            raw=[F(1) if k.damage[b,j]==0 or F.from_float(float(k.duration[b,j]))<=left else F.from_float(float(INITIAL_BY_DS[int(k.damage[b,j])])) for j in range(92)];active=[j for j,v in enumerate(raw) if v>=F(1,2)];connected=set()
            for cc in nx.connected_components(g.subgraph(active)):
                if any(k.source_flag[j] for j in cc):connected.update(cc)
            lost=total-sum(weights[j]*(raw[j] if j in connected else F(0)) for j in range(92));value+=lost*(right-left)/total
        results.append(value)
    exact=sum(results)/64;scale=10**9;down=(exact.numerator*scale//exact.denominator)/scale;assert F.from_float(down)<=exact
    record=dict(bound_hr_exact_rational_numerator=str(exact.numerator),bound_hr_exact_rational_denominator=str(exact.denominator),lower_bound_hr_rounded_down_1e_minus_9=down,double_approximation=float(exact),uses_exact_encoded_float_inputs=True,normalization='Exact encoded original kernel total_mass, with original total_mass minus available-mass integrand',scope='Mathematical fixed-input objective; original evaluator still uses ordinary double arithmetic',algorithm='Exact event integration, unlimited crews, zero travel, native threshold/source gate semantics; rational arithmetic only in this diagnostic',original_numerical_files_modified=False)
    (OUT/'RATIONAL_RELAXATION_BOUND.json').write_text(json.dumps(record,indent=2)+'\n');print('RATIONAL DOWNWARD BOUND',down)
if __name__=='__main__':main()
