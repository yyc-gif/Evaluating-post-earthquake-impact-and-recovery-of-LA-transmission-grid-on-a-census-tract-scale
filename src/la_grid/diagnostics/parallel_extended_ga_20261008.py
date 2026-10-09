"""Parallel independent seeds, identical checkpointed original GA."""
import json
from concurrent.futures import ProcessPoolExecutor,as_completed
import pandas as pd
from la_grid.diagnostics import extended_ga_search_20261008 as search
from la_grid.diagnostics import ga_search_budget_sensitivity as old

def initialize():
    global KERNEL,INC,CACHE
    KERNEL,INC,inputs=old.load_inputs();assert json.loads((search.OUT/'INPUT_IDENTITY.json').read_text())==inputs
    CACHE={}

def task(config):return search.run(KERNEL,INC,CACHE,*config)

def main():
    configs=[(p,g,s) for p,g,seeds in [(100,500,range(42,62)),(100,1000,range(42,62)),(250,500,range(42,47)),(500,500,range(42,47)),(500,1000,range(42,47)),(100,2000,range(42,47))] for s in seeds]
    rows=[];todo=[]
    for p,g,s in configs:
        file=search.OUT/f'p{p}_g{g}_s{s}/RUN.json'
        if file.exists():
            data=json.loads(file.read_text());assert data['status']=='COMPLETE'
            for name,h in data['artifacts_sha256'].items():assert old.digest(file.parent/name)==h
            rows.append(data['summary'])
        else:todo.append((p,g,s))
    print('Previously complete',len(rows),'remaining',len(todo),flush=True)
    with ProcessPoolExecutor(max_workers=3,initializer=initialize) as pool:
        futures={pool.submit(task,config):config for config in todo}
        for future in as_completed(futures):
            rows.append(future.result());pd.DataFrame(rows).sort_values(['population','generations','seed']).to_csv(search.OUT/'SEARCH_SUMMARY.csv',index=False)
    assert len(rows)==60
    best=min(rows,key=lambda r:r['retained_service_loss_hr'])
    (search.OUT/'SEARCH_DECISION.json').write_text(json.dumps({'completed_runs':len(rows),'best':best,'formal_strategy_replaced':False,'global_optimality_proven':False,'independent_evaluation_started':False,'execution':'Three independent worker processes; unchanged RNG/operator sequence per seed; completed checkpoints resumed.'},indent=2)+'\n')
if __name__=='__main__':main()
