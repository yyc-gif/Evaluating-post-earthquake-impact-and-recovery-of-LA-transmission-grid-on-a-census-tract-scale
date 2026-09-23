"""Regenerate mapping benchmark and cutoff diagnostics only; no scientific chain."""
from pathlib import Path
import pandas as pd,numpy as np,json,hashlib
from r1_mapping_gate_robustness import mapping_cases
from r1_mapping import generate_mapping,threshold_weights
root=Path.cwd();out=root/'Revision_Mapping_Gate';maps,c= mapping_cases();rows=[];cut=[]
for name in ['M0_JULY_003','M1_UTILITY_003']:
    w=maps[name].loc[c.index,c.columns];positive=w>0;top=np.argsort(-w.to_numpy(),axis=1,kind='stable')
    # top-k includes only retained positive candidates.
    hit=c.to_numpy() & positive.to_numpy()
    rows.append(dict(mapping=name,tracts=len(c),any_match=int(hit.any(axis=1).sum()),top1=int(hit[np.arange(len(c)),top[:,0]].sum()),top3=int(np.take_along_axis(hit,top[:,:3],axis=1).any(axis=1).sum())))
for constrained in [False,True]:
    _,raw=generate_mapping(utility_constrained=constrained);support=c.reindex(index=raw.index,columns=raw.columns,fill_value=False)
    for cutoff in [0.,.01,.03]:
        w=threshold_weights(raw,cutoff);deleted=(raw>0)&(w==0);supported=deleted&support
        cut.append(dict(mapping_family='utility' if constrained else 'July',cutoff=cutoff,deleted_candidate_relations=int(deleted.sum().sum()),deleted_SCE_supported_relations=int(supported.sum().sum()),deleted_SCE_supported_fraction_of_411=float(supported.sum().sum()/c.sum().sum()),fraction_deleted_relations_with_SCE_support=float(supported.sum().sum()/deleted.sum().sum()) if deleted.sum().sum() else 0.,LAX_RSN_weight=float(w.loc['06037980028','301637'])))
pd.DataFrame(rows).to_csv(out/'SCE_BENCHMARK_REPRODUCED.csv',index=False);pd.DataFrame(cut).to_csv(out/'CUTOFF_RELATION_EFFECTS.csv',index=False)
assert [(r['any_match'],r['top1'],r['top3']) for r in rows]==[(320,296,317),(329,302,324)]
status=maps['M3_SCE_SUPPORTED'].sum(axis=1).rename('represented_mass').reset_index();status['status']=np.where(status.represented_mass>0,'represented','unresolved_zero_July_overlap');status.to_csv(out/'SCE_SUPPORTED_SUBSET_STATUS.csv',index=False)
np.savez_compressed(out/'MAPPING_EVALUATION_MATRICES.npz',**{k:v.to_numpy() for k,v in maps.items()},station_ids=np.array(c.columns,dtype=str),full_tract_ids=np.array(maps['M0_JULY_003'].index,dtype=str),subset_tract_ids=np.array(c.index,dtype=str))
print(pd.DataFrame(rows).to_string(index=False));print(pd.DataFrame(cut).to_string(index=False));print(status.status.value_counts().to_dict())
