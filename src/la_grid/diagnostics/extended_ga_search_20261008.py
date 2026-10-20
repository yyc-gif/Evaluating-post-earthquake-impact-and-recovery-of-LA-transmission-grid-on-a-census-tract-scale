"""Checkpointed unchanged-GA budget extensions; formal results are read-only."""
from pathlib import Path
import gzip,inspect,json,pickle,time
import numpy as np
import pandas as pd
from la_grid.paths import REPO_ROOT
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision import r1_ga_revision as ga
ROOT=REPO_ROOT
OUT=ROOT/'results/diagnostics/extended_ga_20261008'

def instrumented(state_path,record):
    source=inspect.getsource(ga.run_revised_permutation_ga)
    source=source.replace('    update(0,population)', '''    if resume is not None:
        population=resume['population'];score_cache=resume['score_cache']
        archive_score=resume['archive_score'];archive_seq=resume['archive_seq']
        archive_source=resume['archive_source'];archive_generation=resume['archive_generation']
        history=resume['history'];rng.setstate(resume['rng']);start=resume['generation']+1
    else:
        update(0,population);start=1''')
    source=source.replace('range(1,config.generations+1)','range(start,config.generations+1)')
    source=source.replace('population=offspring[:config.population_size];update(generation,population)', '''population=offspring[:config.population_size];update(generation,population)
        if generation % 100 == 0 or generation == config.generations:
            checkpoint(dict(generation=generation,population=population,score_cache=score_cache,
                archive_score=archive_score,archive_seq=archive_seq,archive_source=archive_source,
                archive_generation=archive_generation,history=history,rng=rng.getstate()))''')
    resume=None
    if state_path.exists():
        with gzip.open(state_path,'rb') as f:resume=pickle.load(f)
        record.update(resume.pop('records'))
    def checkpoint(state):
        state['records']=record;tmp=state_path.with_suffix('.tmp')
        with gzip.open(tmp,'wb',compresslevel=1) as f:pickle.dump(state,f,protocol=5)
        tmp.replace(state_path)
        print('CHECKPOINT',state_path.parent.name,state['generation'],len(record),flush=True)
    env=dict(vars(ga),resume=resume,checkpoint=checkpoint)
    exec(compile(source,'<unchanged-ga-with-checkpoints>','exec'),env)
    return env['run_revised_permutation_ga']

def run(kernel,inc,cache,pop,generations,seed):
    folder=OUT/f'p{pop}_g{generations}_s{seed}';folder.mkdir(parents=True,exist_ok=True)
    path=folder/'RUN.json'
    if path.exists():
        data=json.loads(path.read_text());assert data['status']=='COMPLETE'
        assert data['config']==ga.RevisedGAConfig(pop,generations,.8,.2,3).__dict__ and data['summary']['seed']==seed
        for name,sha in data['artifacts_sha256'].items():assert old.digest(folder/name)==sha
        with np.load(folder/'CANDIDATES.npz') as z:
            for order,value in zip(z['orders'],z['fitness']):cache[order.tobytes()]=float(value)
        return data['summary']
    records={};checkpoint=folder/'SEARCH_CHECKPOINT.pkl.gz';runner=instrumented(checkpoint,records)
    cache.update({k:v[0] for k,v in records.items()});started=time.perf_counter()
    def objective(sequence):
        frame=inspect.currentframe().f_back;generation=0
        while frame is not None:
            if frame.f_code.co_name=='update':generation=frame.f_locals['generation'];break
            frame=frame.f_back
        key=bytes(kernel.index[x] for x in sequence)
        if key not in cache:cache[key]=kernel.score(sequence)
        records.setdefault(key,(cache[key],generation));return cache[key]
    config=ga.RevisedGAConfig(pop,generations,.8,.2,3)
    result=runner(items=kernel.ids,objective=objective,incumbents=inc,seed=seed,config=config)
    inc_keys={bytes(kernel.index[x] for x in sequence) for sequence in inc.values()}
    keys=list(records);orders=np.array([np.frombuffer(k,dtype=np.uint8) for k in keys]);fitness=np.array([records[k][0] for k in keys]);first=np.array([records[k][1] for k in keys])
    non=np.array([k not in inc_keys for k in keys]);idx=np.flatnonzero(non)[np.argmax(fitness[non])]
    generated=tuple(kernel.ids[j] for j in orders[idx]);impact=inc['impact-first'];reference=kernel.score(impact)
    history=result.history.copy();history['non_incumbent_best_so_far']=[fitness[non&(first<=g)].max() for g in history.generation]
    history.to_csv(folder/'HISTORY.csv',index=False)
    np.savez_compressed(folder/'CANDIDATES.npz',station_ids=np.array(kernel.ids),orders=orders,fitness=fitness,first_generation=first,non_incumbent=non)
    values=old.per_sample(kernel,result.best_sequence);base=old.per_sample(kernel,impact)
    pd.DataFrame({'realization_id':[f'2pc50__planning_{i:04}' for i in range(64)],'impact_service_loss_hr':base,'candidate_service_loss_hr':values,'change_hr':values-base}).to_csv(folder/'PLANNING_DIFFERENCES.csv',index=False)
    positions=np.array([result.best_sequence.index(x) for x in impact])
    summary=dict(seed=seed,population=pop,generations=generations,unique_candidates_evaluated=len(keys),unique_non_incumbent_candidates=int(non.sum()),retained_service_loss_hr=-result.best_fitness,best_non_incumbent_service_loss_hr=-float(fitness[idx]),impact_service_loss_hr=-reference,delta_J_hr=-result.best_fitness+reference,improvement_hr=result.best_fitness-reference,improvement_percent=100*(result.best_fitness-reference)/(-reference),strict_improvement=bool(result.search_improved_incumbent),sequence_sha256=old.identity(result.best_sequence),generation_found=result.best_generation,displaced_stations=int(np.sum(positions!=np.arange(92))),rank_correlation=float(np.corrcoef(positions,np.arange(92))[0,1]),top10_overlap=len(set(result.best_sequence[:10])&set(impact[:10])),elapsed_seconds=time.perf_counter()-started,exact_tie_candidate_count=int(np.sum(non&(fitness==reference))))
    for threshold in old.THRESHOLDS:summary[f'near_tie_abs_gap_lt_{threshold:g}_hr']=int(np.sum(non&(np.abs(fitness-reference)<threshold)))
    data=dict(status='COMPLETE',diagnostic_only=True,formal_strategy_replaced=False,config=config.__dict__,summary=summary,station_ids=list(kernel.ids),retained_sequence=list(result.best_sequence),best_non_incumbent_sequence=list(generated),artifacts_sha256={f.name:old.digest(f) for f in folder.iterdir() if f.suffix in ['.csv','.npz']})
    path.write_text(json.dumps(data,indent=2)+'\n');checkpoint.unlink(missing_ok=True)
    print('COMPLETE',json.dumps(summary),flush=True);return summary

def main():
    OUT.mkdir(parents=True,exist_ok=True);kernel,inc,inputs=old.load_inputs()
    identity=OUT/'INPUT_IDENTITY.json'
    if identity.exists():assert json.loads(identity.read_text())==inputs
    else:identity.write_text(json.dumps(inputs,indent=2)+'\n')
    cache={}
    for folder in sorted(old.OUT.glob('p*_g*_s*')):
        with np.load(folder/'CANDIDATES.npz') as z:
            for order,value in zip(z['orders'],z['fitness']):cache[order.tobytes()]=float(value)
    folder=OUT/'parity';folder.mkdir(exist_ok=True);records={}
    replay=instrumented(folder/'SEARCH_CHECKPOINT.pkl.gz',records)
    result=replay(items=kernel.ids,objective=kernel.score,incumbents=inc,seed=42,config=ga.RevisedGAConfig(100,100,.8,.2,3))
    expected=pd.read_csv(old.OUT/'p100_g100_s42/HISTORY.csv')
    error=float(np.max(np.abs(result.history[['generation_best','generation_mean','best_so_far']].to_numpy()-expected[['generation_best','generation_mean','best_so_far']].to_numpy())))
    assert error<1e-9
    (folder/'SEARCH_CHECKPOINT.pkl.gz').unlink(missing_ok=True)
    (folder/'PARITY.json').write_text(json.dumps({'history_max_abs_error':error,'original_ga_sha256':old.digest(ROOT/'src/la_grid/revision/r1_ga_revision.py')},indent=2))
    schedule=[(100,500,range(42,62)),(100,1000,range(42,62)),(250,500,range(42,47)),(500,500,range(42,47)),(500,1000,range(42,47)),(100,2000,range(42,47))]
    rows=[]
    for p,g,seeds in schedule:
        for seed in seeds:
            rows.append(run(kernel,inc,cache,p,g,seed));pd.DataFrame(rows).to_csv(OUT/'SEARCH_SUMMARY.csv',index=False)
    best=min(rows,key=lambda r:r['retained_service_loss_hr'])
    (OUT/'SEARCH_DECISION.json').write_text(json.dumps({'completed_runs':len(rows),'best':best,'formal_strategy_replaced':False,'global_optimality_proven':False,'independent_evaluation_started':False},indent=2)+'\n')
if __name__=='__main__':main()
