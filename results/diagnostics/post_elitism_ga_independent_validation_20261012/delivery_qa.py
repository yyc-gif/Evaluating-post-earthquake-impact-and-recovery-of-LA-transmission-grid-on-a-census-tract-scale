"""Independent reconstruction of published statistics; no physical evaluation."""
import hashlib
import study as s
import numpy as np
import pandas as pd


def main():
    s.configure();s.verify()
    v,OUT=s.v,s.OUT
    frame=pd.read_csv(OUT/'REALIZATION_LEVEL_POLICY_RESULTS.csv',float_precision='round_trip')
    effects=pd.read_csv(OUT/'ALL_PAIRED_METRIC_RESULTS.csv',float_precision='round_trip')
    assert len(frame)==6000 and frame.realization_id.nunique()==2000
    assert not frame.duplicated(['realization_id','strategy']).any()
    metrics=effects.metric.drop_duplicates().tolist()
    rid=sorted(frame.realization_id.unique())
    delta=[];keys=[]
    for ref in (s.IMPACT,s.PREVIOUS):
        for metric in metrics:
            p=frame.pivot(index='realization_id',columns='strategy',values=metric).loc[rid]
            delta.append((p[s.CANDIDATE]-p[ref]).to_numpy());keys.append((ref,metric))
    delta=np.stack(delta,axis=1)
    assert np.isfinite(delta).all()
    # Reconstruct directly from paired differences, not differences of policy means.
    rng=np.random.default_rng(s.BOOT_SEED);before=rng.bit_generator.state
    boot=np.empty((20000,len(keys)));index_hash=hashlib.sha256()
    for start in range(0,20000,100):
        indices=rng.integers(0,2000,size=(100,2000))
        index_hash.update(indices.astype('<i8').tobytes())
        weights=np.stack([np.bincount(row,minlength=2000)/2000 for row in indices])
        boot[start:start+100]=weights@delta
    maximum=0.
    for j,(ref,metric) in enumerate(keys):
        row=effects[(effects.reference==ref)&(effects.metric==metric)].iloc[0]
        x=delta[:,j]
        lo,hi=np.quantile(boot[:,j],[.025,.975])
        maximum=max(maximum,abs(lo-row.ci95_low),abs(hi-row.ci95_high),abs(x.mean()-row.mean_difference))
        assert abs(np.median(x)-row.median_difference)<1e-10
        assert abs(x.std(ddof=1)/np.sqrt(2000)-row.mcse)<1e-10
        assert (x<-1e-9).sum()==row.improved_count and (x>1e-9).sum()==row.worsened_count
        assert (abs(x)<=1e-9).sum()==row.ties_count
        if metric==v.PRIMARY:
            slo,shi=np.quantile(boot[:,j],[.0125,.9875])
            maximum=max(maximum,abs(slo-row.simultaneous95_low),abs(shi-row.simultaneous95_high))
    assert maximum<1e-10
    manifest=v.read(OUT/'OUTPUT_HASH_MANIFEST.json')['files']
    for name,row in manifest.items():assert v.sha(OUT/name)==row['sha256']
    tracked=set(s.git(s.ROOT,'ls-files',s.REL).decode().splitlines())
    missing=[n for n in manifest if s.REL+'/'+n not in tracked]
    assert not missing,missing
    prereg=v.read(OUT/'PREREGISTRATION_COMMIT.json')['commit']
    for name in ('AUTHORIZATION_AND_EXECUTION_FREEZE.json','EXECUTION_FREEZE.json','FIXED_STRATEGY_IDENTITIES.json','study.py','analyze.py','publish.py'):
        blob=s.git(s.ROOT,'show',prereg+':'+s.REL+'/'+name)
        assert hashlib.sha256(blob).hexdigest()==v.sha(OUT/name),name
    assert s.preserved()==v.read(OUT/'PRESERVATION_BASELINE.json')
    v.write(OUT/'STATISTICAL_RECONSTRUCTION_AND_DELIVERY_QA.json',dict(status='PASS',
        reconstructed_contrast_metrics=len(keys),same_registered_bootstrap_replayed=True,
        bootstrap_seed=s.BOOT_SEED,bootstrap_resamples=20000,bootstrap_index_sha256=index_hash.hexdigest(),
        rng_before=before,rng_after=rng.bit_generator.state,max_statistical_error=maximum,
        preregistered_source_and_protocol_byte_identical=True,manifest_payloads_checked=len(manifest),
        all_manifest_payloads_in_index=True,physical_sampler_calls=0,production_evaluations=0,optimizer_calls=0,
        source_sha256=v.sha(OUT/'delivery_qa.py')))
    print('STATISTICAL_RECONSTRUCTION_PASS',maximum,'MANIFEST_PAYLOADS',len(manifest),flush=True)


if __name__=='__main__':main()
