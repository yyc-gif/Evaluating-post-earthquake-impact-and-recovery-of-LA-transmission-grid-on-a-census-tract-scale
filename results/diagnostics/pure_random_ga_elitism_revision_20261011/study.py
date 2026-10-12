"""Two-mode elitism development; unchanged fixed planning physics, no validation reads."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import pickle
import random
import subprocess
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
PRIOR=ROOT.parent/'_gpc13'
BASE=ROOT.parent/'_gaf12'
START='3da06ca6b9d5bb55d179ff1ff7bdcae583b2f231'
BRANCH='diagnostics/pure-random-ga-worst-offspring-elitism-20261011'
SOURCE=ROOT/'src/la_grid/diagnostics/ga_variant_engine.py'
sys.path.insert(0,str(BASE/'src'))


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
    return m


a=module('elitism_prior_utilities',PRIOR/'results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py')
import numpy as np
import pandas as pd
e=module('elitism_development_engine',SOURCE)
MODES={'LEGACY':e.LEGACY_LAST_POSITION_ELITISM,'POST':e.POST_EVALUATION_WORST_OFFSPRING_ELITISM}
SEEDS=list(range(2026121100,2026121120))
EXTEND=SEEDS[:10]
POINTS=(100,1000,5000,10000,20000,50000,100000,250000,500000)
CFG=a.REFERENCE


def save(name,value):
    p=a.lp(OUT/name);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(a.clean(value),indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def csv(name,rows):
    p=a.lp(OUT/name);p.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(p,index=False,lineterminator='\n',float_format='%.17g')


def md(name,text):
    p=a.lp(OUT/name);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text.strip()+'\n',encoding='utf-8',newline='\n')


def git(*args):return a.git(*args,cwd=ROOT)


def engineering():
    # Short temporary prefix avoids the Windows MAX_PATH limit in pytest fixtures.
    command=[sys.executable,'-m','pytest',str(OUT/'test_elitism.py'),'-q',
             '--basetemp='+str(ROOT/'_elitism_tmp')]
    result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    md('ALGORITHM_UNIT_TEST_LOG.txt',result.stdout+'\n'+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    assert '8 passed' in result.stdout
    save('ALGORITHM_UNIT_TEST_RESULTS.json',dict(status='PASS',tests_passed=8,
        cases=['A_last_child_best','B_all_children_better','C_elite_present',
               'D_deterministic_ties','E_duplicate_cache','F_budget_boundary',
               'G_exact_checkpoint_replay','mode_switch_rejected'],command=command,
        python=sys.version,engine_sha256=a.sha(SOURCE),tests_sha256=a.sha(OUT/'test_elitism.py'),
        new_physical_samples=0,real_planning_objective_calls=0,
        initial_setup_errors='Two preliminary pytest invocations passed A-D but failed E-G fixture creation from Windows long paths. No algorithm assertion failed; rerunning with the short temporary prefix passed all eight tests.'))


def preservation():
    data=a.preservation()
    data['parameter_evidence_head']=a.git('rev-parse','HEAD',cwd=PRIOR).decode().strip()
    data['parameter_evidence_index']=hashlib.sha256(a.git('ls-files','--stage','-z',cwd=PRIOR)).hexdigest()
    data['parameter_evidence_status']=hashlib.sha256(a.git('status','--porcelain=v1','-z',cwd=PRIOR)).hexdigest()
    assert data['parameter_evidence_head']==START
    old=a.read(PRIOR/'results/diagnostics/pure_random_ga_parameter_consistency_20261011/OUTPUT_HASH_MANIFEST.json')
    for name,row in old['files'].items():
        assert a.sha(PRIOR/'results/diagnostics/pure_random_ga_parameter_consistency_20261011'/name)==row['sha256']
    data['parameter_evidence_hash_manifest']=a.sha(PRIOR/'results/diagnostics/pure_random_ga_parameter_consistency_20261011/OUTPUT_HASH_MANIFEST.json')
    return data


def setup():
    assert not a.lp(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json').exists()
    assert git('rev-parse','HEAD').decode().strip()==START
    assert git('branch','--show-current').decode().strip()==BRANCH
    save('PRESERVATION_BASELINE.json',preservation())
    # Planning metadata only; loader does not score or use a prior sequence.
    kernel,_,model=a.load_study().load_model()
    historical=set(a.frame(PRIOR/'results/diagnostics/pure_random_ga_parameter_consistency_20261011/BUDGET_AND_DUPLICATE_ACCOUNTING.csv').seed.astype(int))
    assert not historical.intersection(SEEDS)
    design=dict(start=START,branch=BRANCH,modes=MODES,configuration=asdict(CFG),
        main_seeds=SEEDS,main_budget=100000,reserved_continuation_seeds=EXTEND,
        continuation_budgets=[250000,500000],checkpoints=list(POINTS),workers=12,
        engineering_seed=2026121000,model=model,replication_unit='Paired independent optimizer seed; checkpoints are repeated observations',
        continuation_rule='Continue the first ten paired states to both250k and500k if the primary100k paired95% interval is not wholly adverse to POST (lower<=0). This resolves budget-dependent benefit/plateau ambiguity, not a search for favorable seeds. No continuation if clearly adverse at100k.',
        primary_statistics='Paired t95 and20k paired bootstrap, one prespecified100k contrast; extension250k/500k family size2 and conservative all-three-budget family size3 also reported. No practical equivalence margin.',
        bootstrap_seed=2026121200,tie_reporting_tolerance_hr=1e-10,
        decision_rule='ADOPT POST as engineering design if no tested endpoint has a multiplicity-adjusted interval wholly adverse and median paired wall ratio is <=1.5 at every tested endpoint; otherwise RETAIN LEGACY. The1.5 cap is a prospective operational-cost safeguard, not physical equivalence. Statistical superiority requires an adjusted interval entirely below zero; unresolved intervals do not prove equivalence.',
        candidate_rule='Record best and median-loss seed per mode/budget with loss, then seed ascending ties. A single POST development candidate is the lowest actual within-budget planning loss over eligible completed runs, then smaller budget/seed; shadow discard scores are excluded. No formal promotion.',
        shadow_audit='Only after searches finish, score unique legacy discarded children absent from the terminal cache. These separate audit calls never enter optimizer cache, selection, archive or100k budget. Record known-at-proposal and eventual-cache observations separately.',
        new_physical_samples=0,independent_validation_outcomes_loaded=False,
        source_hashes={str(SOURCE):a.sha(SOURCE),str(Path(__file__)):a.sha(__file__),
                       str(BASE/'src/la_grid/diagnostics/ga_variant_engine.py'):a.sha(BASE/'src/la_grid/diagnostics/ga_variant_engine.py')})
    save('EXPERIMENT_DESIGN_AND_SEEDS.json',design)
    md('ELITISM_IMPLEMENTATION_DIFF.md',f'''# Actual execution path and change

The frozen pure-random path is the original ga_variant_engine.run_search plus the zero-incumbent guard/100-random initializer in ga_random_initialization_isolation_20261011/study.py. This isolated source makes the same empty-incumbent guard directly executable; paired_random_pool already uses the exact random.sample initializer. r1_ga_revision.py is imported only for unchanged OX/inversion helpers and is not edited.

Prior elite: unique current-generation chromosomes ranked by negative loss descending, then chromosome lexicographically ascending. Legacy overwrites child index99 BEFORE evaluation regardless of fitness; it only knows that child's score if the run-local cache already contains it. Passive best_seen retains every actually evaluated strict improvement, with first exact score tie retained. The completed-generation archive is separately observed and never inserted as an additional prior.

Default remains LEGACY_LAST_POSITION_ELITISM. New explicit keyword elitism_mode=POST_EVALUATION_WORST_OFFSPRING_ELITISM evaluates the complete proposal before survival. Parent selection, OX, swap, ranking, maximization objective, random draws, independent caches and100k distinct stopping remain unchanged. Initial pool/RNG and first unmodified proposal are recorded and paired. A top-of-loop guard makes repeating a fully completed budget idempotent without changing uninterrupted baseline search.

Checkpoints retain mode, previous elite, full/partial score prefix, next_index, finalization flag, counters, elite event keys, complete private cache, exact RNG and trace history. A mode mismatch cannot resume. Older checkpoints without a mode identify legacy. Cached trailing children may finish a generation at the budget, but no additional unique child is scored. Conditional survival and generation observation occur once, only on complete scoring.

Original source SHA256: {a.sha(BASE/'src/la_grid/diagnostics/ga_variant_engine.py')}. Authorized development source SHA256: {a.sha(SOURCE)}. No scientific evaluator or physical file changes.
''')
    md('POST_EVALUATION_ELITISM_SPECIFICATION.md','''# Post-evaluation survival specification

Generate exactly100 children with unchanged parent selection/OX/swap. Evaluate them in index order through the private cache. Count all new distinct scores including the last child. Update global best-observed at every actual new score, before any survival replacement.

Previous elite is selected by the unchanged current-generation rank; its chromosome/fitness is stored across interrupted evaluations. If its exact chromosome appears among children, skip insertion. Otherwise choose minimum fitness, breaking worst-score ties by lowest child index. Insert only if elite fitness >= worst fitness; equal-fitness distinct chromosomes therefore replace the first worst. If all offspring are strictly better, skip. No tie-related RNG draw. Population size and permutation validity stay unchanged.

If the distinct budget ends at an unseen child, preserve the scored prefix and unfinalized pending elite. Do not count a complete generation or insertion. After all children are scored, finalize once even when the final unique score consumes the budget. Repeating that budget is idempotent; extending it resumes the exact next operation.

Legacy discarded children are measured separately after search, not fed back into either algorithm. Generated, attempted, distinct, cached, generation, insertion/presence/all-better and strict-improvement counts remain distinct. Conditional elite survival is not global-archive injection.
''')
    print('REGISTERED',len(kernel.ids),len(SEEDS),flush=True)


def statefile(folder):
    with gzip.open(a.lp(folder/'CHECKPOINT.pkl.gz'),'rb') as f:return pickle.load(f)


def baseline():
    path=BASE/'results/diagnostics/pure_random_ga_final_20261011/candidate_lineage/STATE_100000.pkl.gz'
    with gzip.open(a.payload(path),'rb') as f:original=pickle.load(f)
    kernel,_,_=a.load_study().load_model();ids=kernel.ids;calls=[0];index={x:i for i,x in enumerate(ids)}
    def lookup(seq):
        calls[0]+=1;return original['cache'][bytes(index[x] for x in seq)]
    folder=OUT/'runtime/legacy_reproduction'
    assert not a.lp(folder/'CHECKPOINT.pkl.gz').exists()
    r=e.run_search(items=ids,incumbents={},objective=lookup,seed=2026103108,config=CFG,
        max_evaluations=100000,folder=a.lp(folder),elitism_mode=MODES['LEGACY'])
    replay=statefile(folder)
    assert replay['rng']==original['rng'] and r['cache']==original['cache']
    assert list(r['cache'])==list(original['cache'])
    fields=['population','scores','next_index','phase','generation','attempts','best_seq','best_seen','archive_seq','archive_score','flags','parents','parent_values']
    for field in fields:assert r['state'][field]==original['state'][field],field
    assert abs(-r['best_fitness']-32.99552241352315)<1e-12
    assert a.identity(r['best_sequence'])=='edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a'
    # First proposal parity before scoring/survival, with the original evaluator untouched.
    other=e.run_search(items=ids,incumbents={},objective=lookup,seed=2026103108,config=CFG,
        max_evaluations=100,elitism_mode=MODES['POST'])
    assert other['state']['initial_population']==r['state']['initial_population']
    assert other['state']['initial_rng_state']==r['state']['initial_rng_state']
    initial_rng=random.Random();initial_rng.setstate(other['state']['initial_rng_state'])
    save('LEGACY_REPRODUCTION_PARITY.json',dict(status='PASS',seed=2026103108,budget=100000,
        loss_hr=-r['best_fitness'],sequence=list(r['best_sequence']),sequence_sha256=a.identity(r['best_sequence']),
        all_cache_values_order_rng_and_core_operator_state_exact=True,
        original_checkpoint_sha256=a.sha(a.payload(path)),lookup_calls=calls[0],new_physical_objective_calls=0,
        initial_pool_rng_match=True,first_proposal_parity='Verified explicitly in engineering tests and every paired experiment',
        source_sha256=a.sha(SOURCE)))
    print('LEGACY_FULL_REPLAY_PASS',flush=True)


def worker_setup():
    global KERNEL
    KERNEL=a.load_study().load_model()[0]


def run_one(mode,seed,budget):
    tick=time.perf_counter();folder=OUT/'runtime'/f'{mode}_{seed}'
    existed=a.lp(folder/'CHECKPOINT.pkl.gz').exists()
    assert existed==(budget>100000),'Fresh100k search cannot inherit a checkpoint'
    before=statefile(folder) if existed else None
    r=e.run_search(items=KERNEL.ids,incumbents={},objective=KERNEL.score,seed=seed,config=CFG,
        max_evaluations=budget,checkpoints=POINTS,folder=a.lp(folder),elitism_mode=MODES[mode])
    s=r['state'];h=r['history'];snapshot=statefile(folder)
    assert len(r['cache'])==s['expensive_calls']==budget and s['lookup_calls']==0
    assert len(r['best_sequence'])==len(set(r['best_sequence']))==92
    assert all(len(k)==len(set(k))==92 for k in r['cache'])
    row=dict(mode=mode,seed=seed,budget=budget,final_loss_hr=-r['best_fitness'],
        initial_best_loss_hr=float(h.iloc[0].population_best_service_loss_hr),
        sequence=list(r['best_sequence']),sequence_sha256=a.identity(r['best_sequence']),
        distinct=budget,generated_offspring=s['generated_offspring'],attempts=s['attempts'],
        cache_hits=s['attempts']-budget,offspring_attempts=s['offspring_attempts'],
        offspring_distinct=s['offspring_new_distinct'],offspring_cache_hits=s['offspring_attempts']-s['offspring_new_distinct'],
        parent_cache_queries=s['generation']*100,completed_generations=s['completed_generations'],
        generated_generations=s['generation'],elite_insertions=s['elite_insertions'],
        elite_already_present=s['elite_already_present'],all_offspring_better=s['all_offspring_better'],
        strict_improvements=sum(x['distinct_evaluations']>100 for x in snapshot['moves']),
        objective_seconds=s['score_seconds'],wall_seconds=s['elapsed_seconds'],
        incremental_wall_seconds=time.perf_counter()-tick,
        incremental_distinct=budget-(len(before['cache']) if before else 0),
        final_unique_population=int(h.iloc[-1].unique_population),final_position_entropy=float(h.iloc[-1].position_entropy),
        final_hamming=float(h.iloc[-1].positional_hamming_fraction),
        initial_pool_sha256=hashlib.sha256(pickle.dumps(s['initial_population'],protocol=5)).hexdigest(),
        initial_rng_sha256=hashlib.sha256(pickle.dumps(s['initial_rng_state'],protocol=5)).hexdigest(),
        first_proposal_sha256=hashlib.sha256(pickle.dumps(s['first_offspring_proposals'],protocol=5)).hexdigest(),
        first_proposal_rng_sha256=hashlib.sha256(pickle.dumps(s['first_proposal_rng_state'],protocol=5)).hexdigest())
    save(f'runs/{mode}_{seed}_{budget}.json',row)
    archive=a.lp(OUT/f'raw_evidence/{mode}_{seed}_{budget}.zip');archive.parent.mkdir(parents=True,exist_ok=True)
    members=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in ['CHECKPOINT.pkl.gz','GENERATION_DIAGNOSTICS.csv','BUDGET_CHECKPOINTS.csv','STRICT_IMPROVEMENTS.json','PARENT_SELECTION.npz']:
            data=a.lp(folder/name).read_bytes();z.writestr(name,data)
            members.append(dict(path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    with zipfile.ZipFile(archive) as z:
        for m in members:assert hashlib.sha256(z.read(m['path'])).hexdigest()==m['sha256']
    save(f'raw_evidence/{mode}_{seed}_{budget}.manifest.json',dict(zip_sha256=a.sha(archive),bytes=archive.stat().st_size,members=members,status='PASS'))
    return {k:v for k,v in row.items() if k!='sequence'}


def execute(budget):
    design=a.read(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')
    for path,digest in design['source_hashes'].items():assert a.sha(path)==digest
    assert a.read(OUT/'ALGORITHM_UNIT_TEST_RESULTS.json')['status']=='PASS'
    assert a.read(OUT/'LEGACY_REPRODUCTION_PARITY.json')['status']=='PASS'
    if budget>100000:assert a.read(OUT/'CONTINUATION_DECISION.json')['execute']
    seeds=SEEDS if budget==100000 else EXTEND
    tick=time.perf_counter();rows=[]
    with ProcessPoolExecutor(max_workers=12,initializer=worker_setup) as pool:
        jobs=[pool.submit(run_one,m,s,budget) for s in seeds for m in MODES]
        for f in as_completed(jobs):
            row=f.result();rows.append(row)
            print('COMPLETE',budget,row['mode'],row['seed'],round(row['final_loss_hr'],9),len(rows),len(jobs),flush=True)
    rows=sorted(rows,key=lambda r:(r['seed'],r['mode']))
    df=pd.DataFrame(rows)
    for seed,g in df.groupby('seed'):
        for field in ('initial_pool_sha256','initial_rng_sha256','first_proposal_sha256','first_proposal_rng_sha256'):
            assert g[field].nunique()==1,(seed,field)
    csv(f'RUN_RESULTS_{budget}.csv',rows)
    save(f'EXECUTION_{budget}.json',dict(status='PASS',seeds=seeds,budget=budget,new_distinct_calls=sum(r['incremental_distinct'] for r in rows),
        paired_initialization_rng_and_first_proposals_exact=True,batch_wall_seconds=time.perf_counter()-tick,
        new_physical_samples=0,validation_outcomes_loaded=False))


def continuation():
    d=a.frame(OUT/'RUN_RESULTS_100000.csv').pivot(index='seed',columns='mode',values='final_loss_hr')
    effect=a.paired(d.POST-d.LEGACY,1,2026121200)
    save('CONTINUATION_DECISION.json',dict(execute=effect['pointwise95_low_hr']<=0,
        rule=a.read(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')['continuation_rule'],primary_effect=effect,
        seeds=EXTEND,budgets=[250000,500000],no_new_seeds_or_parameter_changes=True))
    print('CONTINUATION',effect,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['engineering','setup','baseline','main','continuation','250k','500k']);args=p.parse_args()
    {'engineering':engineering,'setup':setup,'baseline':baseline,'main':lambda:execute(100000),'continuation':continuation,
     '250k':lambda:execute(250000),'500k':lambda:execute(500000)}[args.phase]()
