"""Independent archive checks: no model imports or scientific resimulation."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

OUT=Path(__file__).resolve().parent


def lp(p):
    value=str(Path(p).resolve())
    return Path('\\\\?\\'+value) if sys.platform=='win32' and not value.startswith('\\\\?\\') else Path(value)


def digest(p):
    h=hashlib.sha256()
    with lp(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):
            h.update(b)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    args=parser.parse_args()
    root=args.source_root
    formal=root/'Formal_Experiment_20260923'
    f=pd.read_csv(lp(OUT/'TRACT_CANDIDATE_VALUES_2315.csv'),dtype={'tract_id':str}).set_index('tract_id')
    tracts=pd.read_csv(root/'Data/Tracts_Within_Expanded_Area.csv',dtype={'GEOID':str}).GEOID.str.zfill(11).tolist()
    m=pd.read_csv(root/'Data/JULY_UTILITY_CONSTRAINED_92.csv',dtype={'tract_id':str,'substation_id':str})
    m.tract_id=m.tract_id.str.zfill(11)
    samples=pd.read_csv(lp(formal/'Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv'))
    samples=samples[(samples.scenario=='2pc50')&(samples.split=='evaluation')].sort_values('realization_id')
    arrays={}
    for policy in ['direct-community','impact-first','unconstrained']:
        with np.load(lp(formal/f'Formal_Offline_Evaluation/2pc50__C57_D1__{policy}__INTEGRALS.npz')) as z:
            arrays[policy]=dict(L=z['G1_BASELINE_050__L_total'].copy(),
                                B=z['M1_UTILITY_003__normalized_burden_hr'].copy(),
                                physical=z['physical_hashes'].copy(),stations=z['station_ids'].copy())
    stations=arrays['direct-community']['stations'].tolist()
    wi={t:i for i,t in enumerate(tracts)}
    si={s:i for i,s in enumerate(stations)}
    w=csr_matrix((m.weight,([wi[t] for t in m.tract_id],[si[s] for s in m.substation_id])),shape=(2315,92))
    expected={k:(w@a['L'].mean(axis=0)) for k,a in arrays.items()}
    assert np.allclose(f.loc[tracts].B_480_hr,expected['impact-first'],atol=1e-10)
    assert np.allclose(f.loc[tracts].B_unconstrained,expected['unconstrained'],atol=1e-10)
    assert np.allclose(f.loc[tracts].Delta_B_logistics,expected['impact-first']-expected['unconstrained'],atol=1e-10)
    rules=json.loads(lp(formal/'Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50']
    selected=json.loads(lp(formal/'Stage 5 Output_expanded/FINAL_DIRECT_COMMUNITY_SEQUENCE.json').read_text())
    assert selected['ordered_station_ids']==rules['impact-first']
    trace=[]
    for i,row in enumerate(samples.itertuples()):
        identities={}
        npz_hashes={}
        for policy in arrays:
            folder=formal/f'Formal_Trajectories/2pc50/C57_D1/{policy}'
            meta=json.loads(lp(folder/(row.realization_id+'.json')).read_text())
            ident=meta['identity']
            identities[policy]=ident
            assert ident['physical_sample_hash']==row.physical_input_hash
            assert ident['DS_hash']==row.DS_hash and ident['duration_hash']==row.duration_hash
            assert ident['realization_id']==row.realization_id and ident['strategy']==policy
            path=folder/(row.realization_id+'.npz')
            npz_hashes[policy]=digest(path)
            assert npz_hashes[policy]==meta['npz_sha256']
            with np.load(lp(path)) as z:
                time,available=z['event_time_hr'],z['e']
                assert time[0]==0 and time[-1]==480 and np.all(np.diff(time)>0)
                assert np.array_equal(z['station_ids'].astype(str),stations)
                integral=np.einsum('ij,i->j',1-available[:-1],np.diff(time))
                assert np.allclose(integral,arrays[policy]['L'][i],rtol=0,atol=1e-10)
                assert np.isfinite(available).all() and np.min(np.diff(available,axis=0))>=-1e-12
        for k in ['DS_hash','duration_hash','physical_sample_hash','graph_hash','source_set_hash',
                  'mapping_method_id','event_horizon_hr','resource_scenario','directed_travel_hash','crew_roster_hash']:
            assert len({identities[p][k] for p in identities})==1
        assert npz_hashes['direct-community']==npz_hashes['impact-first']
        trace.append(dict(realization_id=row.realization_id,matched_physical_hash=row.physical_input_hash,
                          direct_npz_sha256=npz_hashes['direct-community'],impact_npz_sha256=npz_hashes['impact-first'],
                          unconstrained_npz_sha256=npz_hashes['unconstrained'],all_identity_fields_match=True))
    pd.DataFrame(trace).to_csv(lp(OUT/'INDEPENDENT_THREE_POLICY_ARCHIVE_VERIFICATION.csv'),index=False)
    p=pd.read_csv(lp(OUT/'PRIMARY_2291_PEARSON.csv'),index_col=0)
    residential=f[f.residential_member].loc[:,p.columns]
    assert np.allclose(residential.corr().to_numpy(),p.to_numpy(),atol=1e-12)
    diagnostics=pd.read_csv(lp(OUT/'CONDITIONAL_EXPLAINED_VARIANCE_AND_VIF.csv'))
    max_error=0.
    for row in diagnostics[diagnostics.block=='primary_three_RQ'].itertuples():
        x=residential[row.controls.split(';')].to_numpy()
        y=residential[row.target].to_numpy()
        x=(x-x.mean(axis=0))/x.std(axis=0)
        fitted=np.c_[np.ones(len(x)),x]@np.linalg.lstsq(np.c_[np.ones(len(x)),x],y,rcond=None)[0]
        value=1-np.sum((y-fitted)**2)/np.sum((y-y.mean())**2)
        max_error=max(max_error,abs(value-row.conditional_linear_R2))
    assert max_error<1e-10
    record=dict(status='PASS',archive_realizations=1000,policies=3,all3000_payload_hashes_pass=True,
                physical_DS_duration_graph_source_mapping_resource_travel_identities_match=True,
                original_sequences_equal=True,direct_impact_1000_event_payloads_bitwise_equal=True,
                independently_reproduced_integrals_and_pairwise_correlations=True,
                max_independent_linear_R2_error=max_error,no_scientific_runs=True)
    lp(OUT/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record),flush=True)


if __name__=='__main__':
    main()
