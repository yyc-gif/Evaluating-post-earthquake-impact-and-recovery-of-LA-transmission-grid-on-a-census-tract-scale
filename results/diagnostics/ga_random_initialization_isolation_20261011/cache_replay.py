"""Replay two prespecified main prefixes using saved scores, with zero physical calls."""
import time
import study as s


def main():
    rows=[];tick=time.perf_counter()
    for mode in s.MODES:
        source=s.OUT/'runs'/f'{mode}_{s.MAIN[0]}'
        receipt=s.read(source/'FINAL_100000.json')
        with s.gzip.open(s.lp(source/'STATE_100000.pkl.gz'),'rb') as f: saved=s.pickle.load(f)
        init=s.read(source/'INITIAL_POPULATION.json')
        import numpy as np
        with np.load(s.lp(source/'CANDIDATES.npz')) as z: ids=z['station_ids'].astype(str).tolist()
        lookup={x:i for i,x in enumerate(ids)}
        if mode==s.MODES[1]: impact=tuple(init['initial_sequences'][0])
        else:
            other=s.read(s.OUT/'runs'/f'{s.MODES[1]}_{s.MAIN[0]}'/'INITIAL_POPULATION.json')
            impact=tuple(other['initial_sequences'][0])
        reads=0
        def cached(seq):
            nonlocal reads
            reads+=1
            return saved['cache'][bytes(lookup[x] for x in seq)]
        target=s.OUT/'runtime'/'cached_replay'/mode
        # First partial prefix tests a physical-size interruption, then exact continuation.
        s.run_engine(mode,s.MAIN[0],20000,target,cached,ids,impact)
        result=s.run_engine(mode,s.MAIN[0],100000,target,cached,ids,impact)
        actual=s.read_state(target)
        assert reads==100000
        assert actual['rng']==saved['rng']
        assert list(actual['cache'])==list(saved['cache']) and actual['cache']==saved['cache']
        for field in ['population','scores','next_index','phase','generation','attempts',
                      'best_seq','best_seen','archive_seq','archive_score']:
            assert actual['state'][field]==saved['state'][field],field
        fields=['distinct_evaluations','total_attempts','generation','best_service_loss_hr',
                'archive_service_loss_hr','sequence_sha256','sequence']
        assert [{k:r[k] for k in fields} for r in actual['budget_rows']]==[
            {k:r[k] for k in fields} for r in saved['budget_rows']]
        rows.append(dict(mode=mode,seed=s.MAIN[0],cached_distinct_reads=reads,
            logical_state_and_rng_exact=True,ordered_cache_and_checkpoints_exact=True,
            original_receipt_sha256=s.digest(source/'FINAL_100000.json')))
        print('MAIN100K_CACHED_REPLAY_PASS',mode,flush=True)
    s.save(s.OUT/'MAIN_PREFIX_REPLAY_QA.json',dict(status='PASS',rows=rows,
        physical_objective_calls=0,new_search_replicates=0,wall_seconds=time.perf_counter()-tick,
        timing_bytes_excluded_from_semantic_comparison=True))


if __name__=='__main__':main()
