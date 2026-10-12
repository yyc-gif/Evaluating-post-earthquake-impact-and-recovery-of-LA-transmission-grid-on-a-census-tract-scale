"""Planning-only bounded GA audit; existing model and engine are read-only."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import pickle
import random
import subprocess
import sys
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = ROOT.parent / '_gaf12'
PRIOR = ROOT.parent / '_gri11'
START = 'f539e3fe6015122d73e5656109e751770550bb70'
BRANCH = 'diagnostics/pure-random-ga-parameter-consistency-20261011'
sys.path.insert(0, str(BASE / 'src'))
import numpy as np
import pandas as pd
from scipy import stats
from la_grid.diagnostics.ga_research_preserve_20261009 import snapshot
from la_grid.diagnostics.ga_variant_engine import Variant

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git','-c','filter.lfs.process=',
        '-c','filter.lfs.required=false',*args],cwd=cwd)

def lp(path):
    p = Path(path).resolve()
    return Path('\\\\?\\'+str(p)) if os.name == 'nt' and not str(p).startswith('\\\\?\\') else p

def sha(path):
    h=hashlib.sha256()
    with lp(path).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''): h.update(b)
    return h.hexdigest()

def payload(path):
    p=lp(path)
    with p.open('rb') as f: prefix=f.read(200)
    if not prefix.startswith(b'version https://git-lfs.github.com/spec/v1'):
        return p
    d=dict(x.split(' ',1) for x in prefix.decode().splitlines())
    oid=d['oid'][7:]
    common=Path(git('rev-parse','--git-common-dir',cwd=BASE).decode().strip())
    if not common.is_absolute(): common=BASE/common
    obj=lp(common/'lfs/objects'/oid[:2]/oid[2:4]/oid)
    assert obj.stat().st_size==int(d['size']) and sha(obj)==oid, str(path)
    return obj

def read(path): return json.loads(payload(path).read_text(encoding='utf-8-sig'))
def frame(path): return pd.read_csv(payload(path))
def clean(v):
    if isinstance(v,dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    if isinstance(v,np.generic): v=v.item()
    if isinstance(v,float) and not np.isfinite(v): return None
    return v
def save(name,v):
    p=lp(OUT/name);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def csv(name,data):
    p=lp(OUT/name);p.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(data).to_csv(p,index=False,lineterminator='\n',float_format='%.17g')
def md(name,text): lp(OUT/name).write_text(text.strip()+'\n',encoding='utf-8',newline='\n')
def identity(seq): return hashlib.sha256(('\n'.join(seq)+'\n').encode()).hexdigest()

def load_study():
    spec=importlib.util.spec_from_file_location('frozen_random_study',BASE/'results/diagnostics/ga_random_initialization_isolation_20261011/study.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m

REFERENCE=Variant(population=100,crossover=.8,mutation=.1,tournament=3,elites=1,
    initialization='paired_random_pool',mutation_operator='swap',crossover_operator='ordered',
    adaptive=False,restart=False,diversity_replacement=False)
CASES={'REF':{},'P50':{'population':50},'P250':{'population':250},
    'CX60':{'crossover':.60},'CX95':{'crossover':.95},
    'M05':{'mutation':.05},'M20':{'mutation':.20},
    'T2':{'tournament':2},'T5':{'tournament':5},
    'E0':{'elites':0},'E2':{'elites':2},
    'INVERSION':{'mutation_operator':'inversion'},'INSERTION':{'mutation_operator':'insertion'}}
SCREEN=list(range(2026120100,2026120108))
CONFIRM=list(range(2026120200,2026120220))
HIST_DIRS=['ga_initialization_reconciliation_20261009','ga_optimization_20261009',
    'ga_deeper_research_20261009/continuation','ga_ils_parameter_defense_20261010',
    'ga_random_initialization_isolation_20261011']

def engine(capture):
    s=load_study()
    m=s.engine('PURE_RANDOM_GA',None,capture)
    def initialize(domain,inc,rng,cfg,quality):
        assert not inc and quality is None
        pop=[tuple(rng.sample(domain,len(domain))) for _ in range(cfg.population)]
        assert all(len(x)==len(set(x))==92 and set(x)==set(domain) for x in pop)
        capture.update(initial_sequences=[list(x) for x in pop],
            initial_hashes=[identity(x) for x in pop],archive_before_first_evaluation=[],
            initial_cache=[],initialization='independent random.Random.sample full permutations',
            post_initializer_rng_sha256=hashlib.sha256(pickle.dumps(rng.getstate(),protocol=5)).hexdigest())
        return pop
    m.initialize=initialize
    return m

def preservation():
    f=read(BASE/'results/diagnostics/pure_random_ga_final_20261011/EXECUTION_FREEZE.json')
    revision=Path(f['protected_revision_checkout'])
    d=snapshot(revision)
    d.update(staged_count=len([x for x in git('diff','--cached','--name-only','-z',cwd=revision).split(b'\0') if x]),
        index_sha256=hashlib.sha256(git('ls-files','--stage','-z',cwd=revision)).hexdigest(),
        revision_status_sha256=hashlib.sha256(git('status','--porcelain=v1','-z',cwd=revision)).hexdigest())
    d['source_checkout_state']={str(p):dict(head=git('rev-parse','HEAD',cwd=p).decode().strip(),
        index=hashlib.sha256(git('ls-files','--stage','-z',cwd=p)).hexdigest(),
        status=hashlib.sha256(git('status','--porcelain=v1','-z',cwd=p)).hexdigest()) for p in (BASE,PRIOR)}
    protected={}
    for folder in ['results/diagnostics/pure_random_ga_final_20261011',
        'Review_and_Revision/Pure_Random_GA_20261011','results/diagnostics/final_ga_method_20261009']:
        for p in lp(BASE/folder).rglob('*'):
            if p.is_file() and not any(x in p.parts for x in ('runtime','cohort','__pycache__','.pytest_cache')):
                protected[str(p)]=sha(p)
    for name,h in {**f['input_sha256'],**f['code_sha256']}.items():
        assert sha(BASE/name)==h,name
        protected[str(BASE/name)]=h
    protected[str(BASE/'src/la_grid/diagnostics/ga_variant_engine.py')]=sha(BASE/'src/la_grid/diagnostics/ga_variant_engine.py')
    manuscript=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_manuscript_rebuild\LA_Grid_Manuscript_Resubmission_Rebuild.docx')
    protected[str(manuscript)]=sha(manuscript)
    d['protected_external_sha256']=protected
    return d

def historical_inventory():
    rows=[];seeds=set()
    for folder in HIST_DIRS:
        for p in lp(BASE/'results/diagnostics'/folder).glob('*.csv'):
            try:
                data=frame(p)
            except (AssertionError,FileNotFoundError) as e:
                rows.append(dict(path=str(p),status='LOCAL_PAYLOAD_UNAVAILABLE',error=str(e)));continue
            except pd.errors.EmptyDataError:
                rows.append(dict(path=str(p),status='EMPTY_HISTORICAL_TABLE',sha256=sha(payload(p)),rows=0));continue
            if 'seed' in data:
                seeds.update(pd.to_numeric(data.seed,errors='coerce').dropna().astype(int))
            rows.append(dict(path=str(p),sha256=sha(payload(p)),rows=len(data),
                columns='|'.join(data.columns),status='READ_PLANNING_ONLY',
                evidence_scope='PURE random fixed reference only' if 'ga_random_initialization' in folder else 'Background/conditional initialization; not transferable parameter optimum'))
    assert not seeds.intersection(SCREEN+CONFIRM+[2026120000,2026120001])
    csv('HISTORICAL_EVIDENCE_INVENTORY.csv',rows)
    return len(seeds),rows

def setup():
    assert not (OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json').exists()
    assert git('rev-parse','HEAD').decode().strip()==START
    assert git('branch','--show-current').decode().strip()==BRANCH
    current=preservation()
    if (OUT/'PRESERVATION_BASELINE.json').exists():
        assert current==read(OUT/'PRESERVATION_BASELINE.json')
    else: save('PRESERVATION_BASELINE.json',current)
    n,rows=historical_inventory()
    model=load_study().load_model()[2]
    design=dict(start=START,branch=BRANCH,model=model,reference=asdict(REFERENCE),
        screen_cases={k:asdict(replace(REFERENCE,**v)) for k,v in CASES.items()},
        screen_seeds=SCREEN,screen_budget=20000,confirmation_seeds=CONFIRM,confirmation_budget=100000,
        confirmation_rule='REF plus exactly three alternatives with largest absolute paired screen mean loss difference; exact ties case ID ascending. This prioritizes consequential improvements AND deterioration, not selected minima.',
        confirmation_count=3,extra_interactions='None: bounded one-factor design; unresolved interaction limits disclosed, no unplanned factorial',
        checkpoints=[20000,50000,100000],new_high_budget_continuation=False,
        selection_for_formal_strategy=False,original_candidate_unchanged=True,
        initializer='Independent uniform random.Random.sample permutations; paired seeds; common-prefix pools for P50/P100/P250; RNG diverges after different population initialization lengths.',
        pairing='Optimizer seed is replication unit. Same-sized populations share exact initial pool and post-initializer RNG; changes in operator rates alter subsequent RNG consumption, not enforced common variates.',
        budget='Actual distinct permutation objective calls, initial pool included; independent caches, zero lookup/prescoring; parent cache queries separated from offspring duplicate queries.',
        statistics=dict(bootstrap_replicates=20000,seed=2026120300,reporting_tie_hr=1e-10,
            screen_family=12,confirmation_family=3,interval='pointwise paired t and percentile bootstrap; Bonferroni simultaneous t within each predeclared final-endpoint family',
            practical_equivalence_margin=None,decision='A confirmed direction requires entire simultaneous95 interval below or above zero; no equivalence from zero crossing. Retain reproducible reference unless a consistent improvement is confirmed; changed algorithm would remain development-only, not replacement.'),
        workers=12,engineering_seed=2026120000,engineering_budgets=[333,1000],
        objective_read_only=True,new_physical_samples=0,validation_results_loaded=False,
        mechanism_gate='Freeze final parameter decision and its SHA256 before any validation outcome diagnostics.',
        historical_unique_seeds_checked=n,
        source_sha256={str(p):sha(p) for p in [Path(__file__),BASE/'src/la_grid/diagnostics/ga_variant_engine.py',BASE/'results/diagnostics/ga_random_initialization_isolation_20261011/study.py']})
    save('EXPERIMENT_DESIGN_AND_SEEDS.json',design)
    md('PARAMETER_EVIDENCE_INVENTORY.md','''# Pure-random parameter evidence admission

The five requested historical families were read as planning-only evidence; exact source hashes and table columns are in HISTORICAL_EVIDENCE_INVENTORY.csv. No validation outcome enters parameter selection.

| Choice | Purpose and prior rationale | Transfer to pure random | Required controlled evidence |
| --- | --- | --- | --- |
| Population100 | Parallel exploration bounded by distinct work | Earlier50/250 mixes changed heuristic/prior/neighbor counts; do not transfer | P50/P250 random-only; common-prefix initialization, fewer generations at larger N |
| OX0.80 | Copy a contiguous priority block, cyclically preserve other-parent order; valid permutation | Existing fixed implementation and working pure-reference receipts support feasibility, not rate optimality | 0.60/0.95 with all other choices fixed |
| Swap0.10 | Small permutation move, no repair operation needed | Prior operator/rate comparisons used quality initialization | 0.05/0.20; inversion/insertion at0.10 to resolve move-scale dependence |
| Tournament3 | With-replacement rank pressure without fitness rescaling | Earlier T2 deterioration and T5 interactions are background-specific | T2/T5 from same random pools |
| Elite1 | Preserve current-population best; distinct from passive output archive | Fixed0/1/2/3 studies retained inherited/heuristic information | E0/E2 random-only, all with identical passive retention |
| 100k/20seeds | Finite evaluation budget and independent optimizer replication | Direct20 pure-reference records and10 continued prefixes are admissible | Reuse20k/50k/100k/250k/500k; continuations are not new replicates |
| Adaptation/restart/crowding off | Keep one reproducible basic GA, no extra dynamics | Direct reference works; disabled mechanisms not a superiority claim | No new enabled search: not needed to defend a working simple reference |

Literature supports mechanisms, not these numerical optima. Blickle & Thiele, TIK Report11 revised Dec1995, describes tournament selection intensity/diversity: https://tik-old.ee.ethz.ch/file/6c0e384dceb283cd4301339a895b72b8/TIK-Report11.pdf . Eiben, Hinterding & Michalewicz1999 distinguish parameter tuning/control: https://cs.adelaide.edu.au/~zbyszek/Papers/self9.pdf , DOI10.1109/4235.771166. Vazquez & Whitley2000 compare order-based scheduling operators: https://www.cs.colostate.edu/~genitor/2000/ppsn2000.pdf . No paper is cited as proving P100/CX.8/M.1/T3/E1 optimal here. Source code, not a generic textbook description, defines this exact OX and tie rules.

The old93.06% inherited-gain fraction is excluded from claims of independent GA efficacy. Existing reference initialization and budget evidence is reused, not rerun. Twelve genuine unresolved one-factor alternatives enter the engineering screen; three consequential contrasts enter separately seeded confirmation by the precommitted absolute-effect rule. No alternative crossover or broad enabled-mechanism grid is scientifically necessary for this bounded audit.
''')
    print('REGISTERED',len(CASES),len(SCREEN),n,flush=True)

def engineering():
    d=read(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')
    assert sha(__file__)==d['source_sha256'][str(Path(__file__))]
    s=load_study();ids=tuple(str(300000+i) for i in range(92))
    obj=lambda seq:-sum((i+1)*int(x) for i,x in enumerate(seq))
    captures={};checks=[]
    for case in CASES:
        c=replace(REFERENCE,**CASES[case]);a={};m=engine(a)
        rr=random.Random(1234);pool=m.initialize(ids,{},rr,c,None)
        expected=random.Random(1234);assert pool==[tuple(expected.sample(ids,92)) for _ in range(c.population)]
        captures[case]=a
        for _ in range(500):
            pa,pb=rr.sample(pool,2)
            children=m.crossover(pa,pb,rr,'ordered')
            for child in children:
                assert len(child)==len(set(child))==92 and set(child)==set(ids)
            child=m.mutation(pa,rr,c.mutation_operator)
            assert len(child)==len(set(child))==92 and set(child)==set(ids)
        checks.append(dict(case=case,validity_checks=1500,all_valid=True))
    for case,a in captures.items():
        if case not in ('P50','P250'):
            assert a==captures['REF']
    assert captures['P50']['initial_sequences']==captures['REF']['initial_sequences'][:50]
    assert captures['REF']['initial_sequences']==captures['P250']['initial_sequences'][:100]
    folder=OUT/'runtime/engineering/resume';whole=OUT/'runtime/engineering/whole'
    eng=engine({})
    eng.run_search(items=ids,incumbents={},objective=obj,seed=2026120000,config=REFERENCE,max_evaluations=333,folder=lp(folder),checkpoints=(333,1000))
    resumed=eng.run_search(items=ids,incumbents={},objective=obj,seed=2026120000,config=REFERENCE,max_evaluations=1000,folder=lp(folder),checkpoints=(333,1000))
    engine({}).run_search(items=ids,incumbents={},objective=obj,seed=2026120000,config=REFERENCE,max_evaluations=1000,folder=lp(whole),checkpoints=(333,1000))
    with gzip.open(lp(folder/'CHECKPOINT.pkl.gz'),'rb') as f: a=pickle.load(f)
    with gzip.open(lp(whole/'CHECKPOINT.pkl.gz'),'rb') as f: b=pickle.load(f)
    assert a['rng']==b['rng'] and a['cache']==b['cache'] and list(a['cache'])==list(b['cache'])
    for key in ['population','scores','phase','generation','attempts','next_index','best_seq','best_seen','archive_seq']:
        assert a['state'][key]==b['state'][key],key
    assert len(a['cache'])==a['state']['expensive_calls']==1000 and a['state']['lookup_calls']==0
    k,_,model=s.load_model()
    cap={};r=engine(cap).run_search(items=k.ids,incumbents={},objective=k.score,seed=2026120001,
        config=REFERENCE,max_evaluations=1000,checkpoints=(100,1000))
    station_index={v:i for i,v in enumerate(k.ids)}
    assert list(r['cache'])[:100]==[bytes(station_index[v] for v in seq) for seq in cap['initial_sequences']]
    assert r['state']['expensive_calls']==1000 and r['state']['lookup_calls']==0
    from la_grid.diagnostics.ga_search_budget_sensitivity import per_sample
    from la_grid.diagnostics.standalone_ils_analysis_20261010 import production
    from la_grid.revision.r1_equity_amendment_execute import execution_context
    ctx,_,_=execution_context(k.ids)
    exact=per_sample(k,r['best_sequence'])
    errors=[abs(production(k,ctx,r['best_sequence'],i)-exact[i]) for i in (0,15,63)]
    assert max(errors)<1e-8
    save('PURE_RANDOM_GA_IMPLEMENTATION_QA.json',dict(status='PASS',
        original_engine_unchanged=True,zero_incumbent_guard='Existing frozen AST adapter, no source edit',
        uniform_initialization='Exact random.sample replay for every configuration; pseudorandom algorithm, not empirical proof of every92! probability',
        same_size_pools_rng_identical=True,population_common_prefix=True,operator_validity=checks,
        checkpoint_rng_cache_population_exact=True,initial_and_best_archive_empty=True,
        objective='unchanged negative64-state population loss',actual_distinct_budget=True,
        costly_initial_pool_included=True,parent_queries_are_cache_hits=True,
        actual_planning_engineering_calls=1000,independent_native_checks=3,max_native_error_hr=max(errors),
        caveats=['Raw ga_variant_engine.run_search with empty incumbents alone would fail at ranked[0]; authoritative frozen method uses recorded existing zero-incumbent AST guard.',
            'Passive best-observed archive retains first exact fitness tie; tournament samples with replacement and ties take first drawn index.',
            'Elitism preserves up to configured number of distinct chromosomes from current population, not reinjection of global archive.',
            'Search may end inside generation; every actually scored chromosome participates in best-observed output.']))
    print('ENGINEERING_PASS',max(errors),flush=True)

KERNEL=None
def worker_setup():
    global KERNEL
    KERNEL=load_study().load_model()[0]

def run_one(stage,case,seed,budget):
    tick=time.perf_counter();cpu=time.process_time();capture={}
    folder=OUT/'runtime'/stage/f'{case}_{seed}'
    cfg=replace(REFERENCE,**CASES[case]);m=engine(capture)
    assert not lp(folder/'CHECKPOINT.pkl.gz').exists(),'Fresh experiment may not inherit saved state'
    r=m.run_search(items=KERNEL.ids,incumbents={},objective=KERNEL.score,seed=seed,config=cfg,
        max_evaluations=budget,checkpoints=tuple(x for x in (20000,50000,100000) if x<=budget),folder=lp(folder),quality=None)
    state=r['state'];hist=r['history'];initial=hist.iloc[0]
    assert state['expensive_calls']==len(r['cache'])==budget and state['lookup_calls']==0
    assert len(r['best_sequence'])==92 and set(r['best_sequence'])==set(KERNEL.ids)
    assert state['restart_count']==0 and state['phase'] in ('evaluate','reproduce')
    save(str(folder.relative_to(OUT)/'INITIAL_POPULATION.json'),capture)
    parent=(state['generation'] if state['phase']=='evaluate' else state['generation'])*cfg.population
    # Every reproduce pass rescans exactly N cached parents, one pass per generated generation.
    assert state['attempts']>=len(r['cache'])+parent
    with gzip.open(lp(folder/'CHECKPOINT.pkl.gz'),'rb') as f: saved=pickle.load(f)
    assert all(len(b)==92 and len(set(b))==92 for b in saved['cache'])
    row=dict(stage=stage,case=case,seed=seed,budget=budget,**asdict(cfg),
        initial_best_loss_hr=float(initial.population_best_service_loss_hr),
        final_loss_hr=-r['best_fitness'],gain_after_random_initialization_hr=float(initial.population_best_service_loss_hr)+r['best_fitness'],
        distinct=len(r['cache']),attempts=state['attempts'],parent_cache_queries=parent,
        member_duplicate_queries=state['attempts']-len(r['cache'])-parent,
        cache_hit_fraction=1-len(r['cache'])/state['attempts'],
        completed_generations=int(hist.generation.max()),generated_generations=state['generation'],
        strict_improvements_after_initialization=sum(x['distinct_evaluations']>cfg.population for x in saved['moves']),
        last_improvement=state['last_improvement_evaluations'],objective_seconds=state['score_seconds'],
        wall_seconds=time.perf_counter()-tick,cpu_seconds=time.process_time()-cpu,
        final_position_entropy=float(hist.iloc[-1].position_entropy),
        final_unique_population=int(hist.iloc[-1].unique_population),
        mean_parent_intensity=float(hist.parent_selection_intensity.mean()),
        mean_parent_effective_count=float(hist.parent_effective_count.mean()),
        sequence_sha256=identity(r['best_sequence']),initial_pool_sha256=sha(folder/'INITIAL_POPULATION.json'),
        initialization_rng_sha256=capture['post_initializer_rng_sha256'],
        sequence=list(r['best_sequence']),completed=True)
    save(f'runs/{stage}/{case}_{seed}.json',row)
    # One complete checkpoint contains every score, operation state, strict improvement,
    # generation diagnostic, parent-selection frequencies and exact terminal RNG.
    archive=lp(OUT/f'raw_evidence/{stage}_{case}_{seed}.zip');archive.parent.mkdir(parents=True,exist_ok=True)
    names=['INITIAL_POPULATION.json','CHECKPOINT.pkl.gz','GENERATION_DIAGNOSTICS.csv','BUDGET_CHECKPOINTS.csv','STRICT_IMPROVEMENTS.json','PARENT_SELECTION.npz']
    members=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in names:
            data=lp(folder/name).read_bytes();z.writestr(name,data)
            members.append(dict(path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    with zipfile.ZipFile(archive) as z:
        assert all(hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256'] for x in members)
    save(f'raw_evidence/{stage}_{case}_{seed}.manifest.json',dict(zip_sha256=sha(archive),bytes=archive.stat().st_size,members=members,all_roundtrip_hashes_pass=True))
    return {k:v for k,v in row.items() if k!='sequence'}

def execute(stage):
    d=read(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json');assert read(OUT/'PURE_RANDOM_GA_IMPLEMENTATION_QA.json')['status']=='PASS'
    assert sha(__file__)==d['source_sha256'][str(Path(__file__))]
    if stage=='screen': cases,seeds,budget=list(CASES),SCREEN,20000
    else: cases,seeds,budget=read(OUT/'CONFIRMATION_FAMILY_FROZEN.json')['cases'],CONFIRM,100000
    assert not (OUT/f'{stage}_EXECUTION.json').exists()
    tick=time.perf_counter();rows=[]
    with ProcessPoolExecutor(max_workers=12,initializer=worker_setup) as pool:
        jobs={pool.submit(run_one,stage,c,s,budget):(c,s) for s in seeds for c in cases}
        for f in as_completed(jobs):
            row=f.result();rows.append(row);print('COMPLETE',stage,row['case'],row['seed'],round(row['final_loss_hr'],9),len(rows),len(jobs),flush=True)
    csv('PARAMETER_SCREEN_RESULTS.csv' if stage=='screen' else 'PARAMETER_CONFIRMATION_RESULTS.csv',sorted(rows,key=lambda x:(x['case'],x['seed'])))
    save(f'{stage}_EXECUTION.json',dict(status='PASS',cases=cases,seeds=seeds,budget=budget,
        distinct_calls=sum(x['distinct'] for x in rows),attempts=sum(x['attempts'] for x in rows),
        objective_seconds=sum(x['objective_seconds'] for x in rows),summed_run_wall_seconds=sum(x['wall_seconds'] for x in rows),batch_wall_seconds=time.perf_counter()-tick,new_physical_samples=0,validation_outcomes_loaded=False))

def paired(data,family,seed):
    x=np.asarray(data,float);n=len(x);se=x.std(ddof=1)/np.sqrt(n)
    rng=np.random.default_rng(seed);means=x[rng.integers(0,n,size=(20000,n))].mean(axis=1)
    return dict(n=n,mean_delta_hr=x.mean(),median_delta_hr=np.median(x),sd_delta_hr=x.std(ddof=1),
        pointwise95_low_hr=x.mean()-stats.t.ppf(.975,n-1)*se,pointwise95_high_hr=x.mean()+stats.t.ppf(.975,n-1)*se,
        simultaneous95_low_hr=x.mean()-stats.t.ppf(1-.025/family,n-1)*se,simultaneous95_high_hr=x.mean()+stats.t.ppf(1-.025/family,n-1)*se,
        bootstrap95_low_hr=np.quantile(means,.025),bootstrap95_high_hr=np.quantile(means,.975),
        wins=int((x<-1e-10).sum()),losses=int((x>1e-10).sum()),ties=int((np.abs(x)<=1e-10).sum()),family_size=family)

def effects(df,family):
    rows=[];ref=df[df.case=='REF'].set_index('seed')
    for i,c in enumerate(sorted(set(df.case)-{'REF'})):
        g=df[df.case==c].set_index('seed').loc[ref.index];delta=g.final_loss_hr-ref.final_loss_hr
        row=dict(stage=df.iloc[0].stage,case=c,reference='REF',**paired(delta,family,2026120300+i),
            alternative_mean_hr=g.final_loss_hr.mean(),reference_mean_hr=ref.final_loss_hr.mean(),
            median_wall_ratio=float(np.median(g.wall_seconds/ref.wall_seconds)),
            median_attempt_ratio=float(np.median(g.attempts/ref.attempts)))
        rows.append(row)
    return rows

def select_confirmation():
    assert not (OUT/'CONFIRMATION_FAMILY_FROZEN.json').exists()
    df=frame(OUT/'PARAMETER_SCREEN_RESULTS.csv');e=effects(df,12)
    selected=sorted(e,key=lambda x:(-abs(x['mean_delta_hr']),x['case']))[:3]
    save('CONFIRMATION_FAMILY_FROZEN.json',dict(cases=['REF']+[x['case'] for x in selected],
        rule=read(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')['confirmation_rule'],
        selected_screen_effects=selected,screen_results_sha256=sha(OUT/'PARAMETER_SCREEN_RESULTS.csv'),
        confirmation_seeds=CONFIRM,validation_outcomes_loaded=False,new_physical_samples=0))
    csv('PAIRED_PARAMETER_EFFECTS_SCREEN.csv',e)
    print('CONFIRMATION_FROZEN',[x['case'] for x in selected],flush=True)

def parameter_decision():
    screen=frame(OUT/'PARAMETER_SCREEN_RESULTS.csv');confirm=frame(OUT/'PARAMETER_CONFIRMATION_RESULTS.csv')
    rows=effects(screen,12)+effects(confirm,3);csv('PAIRED_PARAMETER_EFFECTS.csv',rows)
    confirmed=[x for x in rows if x['stage']=='confirmation']
    better=[x for x in confirmed if x['simultaneous95_high_hr']<0]
    recommended=min(better,key=lambda x:x['mean_delta_hr'])['case'] if better else 'REF'
    save('PARAMETER_DECISION_FROZEN.json',dict(recommended_development_configuration=recommended,
        config=asdict(replace(REFERENCE,**CASES[recommended])),frozen_validated_method_changed=False,
        evidence_source_sha256={n:sha(OUT/n) for n in ('PARAMETER_SCREEN_RESULTS.csv','PARAMETER_CONFIRMATION_RESULTS.csv','PAIRED_PARAMETER_EFFECTS.csv')},
        validation_outcomes_loaded=False,no_new_candidate_selection=True,better_confirmation=better))
    text='# Final pure-random GA parameter decision\n\n'
    text+=f'Recommended configuration: **{recommended}**; {asdict(replace(REFERENCE,**CASES[recommended]))}.\n\n'
    text+='The already validated REF sequence/configuration remains unchanged. A confirmed alternative is a development finding only and cannot inherit the old physical validation. No sequence is selected from these diagnostic searches.\n\n'
    for r in confirmed:
        text+=f"- {r['case']} minus REF: mean {r['mean_delta_hr']:.9f}h, median {r['median_delta_hr']:.9f}h; simultaneous95 [{r['simultaneous95_low_hr']:.9f}, {r['simultaneous95_high_hr']:.9f}]h; wins/losses/ties {r['wins']}/{r['losses']}/{r['ties']}; median wall ratio {r['median_wall_ratio']:.3f}.\n"
    text+='\nReplication unit is optimizer seed. Screen and confirmation use separate seeds, identical planning samples, unchanged fitness, independent empty caches and exactly equal distinct budgets. All negative results are retained. Bonferroni families are12 screen/3 confirmation; no equivalence margin, no equivalence claim from an interval crossing zero. Screen-only alternatives remain less certain. Same-size settings share initial chromosomes and initializer RNG; subsequent RNG paths diverge naturally. Populations50/100/250 share a common random-pool prefix, not identical starting minima or completed generations.\n\n'
    text+='The frozen reference is empirically executable, not a unique hyperparameter optimum. No broad operator comparison or new physical validation is requested. Adaptation/restart/diversity replacement remain disabled because no extra machinery is needed to establish basic independent search; their absence is not evidence they cannot help. Earlier90% automatic initialization adoption criterion failed and the final pure-random choice was post-data; this audit does not rewrite either fact. The20 historical reference seeds and10 continuation trajectories remain repeated measurements, not50 independent runs. The93.06% inherited-gain statistic is excluded.\n'
    md('FINAL_PURE_RANDOM_GA_PARAMETER_DECISION.md',text)
    print('PARAMETER_DECISION_FROZEN',recommended,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['setup','engineering','screen','select','confirmation','decision']);a=p.parse_args()
    {'setup':setup,'engineering':engineering,'screen':lambda:execute('screen'),'select':select_confirmation,
        'confirmation':lambda:execute('confirmation'),'decision':parameter_decision}[a.phase]()
