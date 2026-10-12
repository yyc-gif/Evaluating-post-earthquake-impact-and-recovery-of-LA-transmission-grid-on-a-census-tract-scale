"""Clean-clone arithmetic reproduction from published frozen extracts only."""
from scipy import sparse
from common import *


def main():
    qa=json.loads(lp(OUT/'POLICY_ENSEMBLE_QA.json').read_text())
    assert sha(OUT/'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz')==qa['snapshot_sha256']
    z=np.load(lp(OUT/'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz'))
    w=sparse.csr_matrix((z['mapping_data'],z['mapping_indices'],z['mapping_indptr']),shape=z['mapping_shape'])
    mass=np.asarray(w.sum(1)).ravel(); order=pd.Index(z['tract_ids'])
    pi={p:i for i,p in enumerate(z['policies'])}
    burden=np.stack([(w@station.T).T/mass for station in z['station_loss']])
    u=burden[pi['unconstrained']]
    values=frame('MULTIPOLICY_RQ2_TRACT_VALUES.csv')
    maxerr=0
    for name,ps in SETS.items():
        selected=burden[[pi[p] for p in ps]]; delta=(selected-u).mean(1)
        expected={'B_Unconstrained':u.mean(0),'MeanDelta':delta.mean(0),'PolicySD':delta.std(0,ddof=0),
            'MeanTotalBurden':selected.mean((0,1)),'MeanWithinRealizationPolicySD':selected.std(0,ddof=0).mean(0)}
        actual=values.loc[values.policy_set.eq(name)].set_index('tract_id').reindex(order)
        for v,x in expected.items():
            err=np.max(np.abs(actual[v].to_numpy()-x));maxerr=max(maxerr,err)
            assert err<1e-10,(name,v,err)
    d=dataset(); assert len(d)==2299 and d.index.str.fullmatch(r'\d{11}').all()
    for sp in ['A','P2','P3']:
        x,_,_=matrix(d,sp)
        assert abs(((x-x.mean(0))**2).sum()-2299)<1e-8
    dump('CLEAN_CLONE_CORE_ARITHMETIC_QA.json',dict(status='PASS',raw_external_archives_used=False,
        policy_sets_verified=len(SETS),realizations=1000,study_tracts=2315,clustering_tracts=2299,max_error_hr=maxerr,
        limitation='Checks published frozen extracts and derived arithmetic; does not establish full original event/physical provenance without the manifest-bound local archive.'))
    print('Published snapshot core arithmetic PASS',flush=True)


if __name__=='__main__':main()
