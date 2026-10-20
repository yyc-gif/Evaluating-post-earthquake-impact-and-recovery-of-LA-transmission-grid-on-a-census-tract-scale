"""Budget-controlled permutation GA variants and observation-only original replay.

Physical evaluators are injected unchanged. Archive-only/legacy/OX/inversion with
no extra mechanisms preserves the original random-number stream exactly.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import gzip, pickle, random, time, hashlib, json
import numpy as np
import pandas as pd
import psutil
from la_grid.revision.r1_ga_revision import _ordered_crossover, _mutate_inversion

@dataclass(frozen=True)
class Variant:
    population: int = 100
    crossover: float = .8
    mutation: float = .2
    tournament: int = 3
    elites: int = 0
    initialization: str = 'legacy'
    mutation_operator: str = 'inversion'
    crossover_operator: str = 'ordered'
    adaptive: bool = False
    restart: bool = False
    diversity_replacement: bool = False


def mutation(x, rng, operator):
    if operator == 'mixed': operator=rng.choice(['inversion','swap','insertion'])
    if operator == 'inversion': return _mutate_inversion(x,rng)
    a,b=rng.sample(range(len(x)),2);v=list(x)
    if operator == 'swap': v[a],v[b]=v[b],v[a]
    elif operator == 'insertion': v.insert(b,v.pop(a))
    else: raise ValueError(operator)
    return tuple(v)


def crossover(a,b,rng,operator):
    if operator=='ordered': return _ordered_crossover(a,b,rng)
    n=len(a)
    if operator=='cycle':
        i=rng.randrange(n);visited=set();lookup={v:j for j,v in enumerate(a)}
        while i not in visited:visited.add(i);i=lookup[b[i]]
        return tuple(a[j] if j in visited else b[j] for j in range(n)),tuple(b[j] if j in visited else a[j] for j in range(n))
    if operator=='pmx':
        lo,hi=sorted(rng.sample(range(n),2));hi+=1
        def child(p,q):
            out=list(q);out[lo:hi]=p[lo:hi];mapping={p[j]:q[j] for j in range(lo,hi)}
            for j in list(range(lo))+list(range(hi,n)):
                value=out[j]
                while value in mapping:value=mapping[value]
                out[j]=value
            return tuple(out)
        return child(a,b),child(b,a)
    raise ValueError(operator)


def diversity(population,lookup):
    a=np.array([[lookup[v] for v in row] for row in population],dtype=np.int16);n,p=a.shape
    pairs=[(i,(i*37+11)%n) for i in range(min(n,16))];pairs=[(i,j if j!=i else (i+1)%n) for i,j in pairs]
    h=float(np.mean([np.mean(a[i]!=a[j]) for i,j in pairs]))
    inverse=np.argsort(a,axis=1);r=float(np.mean([1-6*np.sum((inverse[i]-inverse[j])**2)/(p*(p*p-1)) for i,j in pairs]))
    edges=[set(zip(row[:-1],row[1:])) for row in a]
    overlap=float(np.mean([len(edges[i]&edges[j])/(p-1) for i,j in pairs]))
    sub=a[np.linspace(0,n-1,min(n,100),dtype=int)];entropy=[]
    for j in range(p):
        c=np.bincount(sub[:,j],minlength=p);q=c[c>0]/len(sub);entropy.append(float(-np.sum(q*np.log(q))/np.log(min(len(sub),p))))
    return dict(positional_hamming_fraction=h,mean_pair_rank_correlation=r,directed_adjacency_overlap=overlap,position_entropy=float(np.mean(entropy)))


def initialize(domain,inc,rng,config,quality):
    population=list(inc.values())
    if config.initialization=='quality_mix':
        population.append(tuple(quality));nlocal=max(1,config.population//4)
        for j in range(nlocal):
            parent=tuple(quality) if j%2==0 else tuple(inc['impact-first'])
            population.append(mutation(parent,rng,'inversion'))
    while len(population)<config.population:
        if config.initialization=='diverse':
            pool=[tuple(rng.sample(domain,len(domain))) for _ in range(4)]
            reference=population[:min(len(population),32)]
            x=max(pool,key=lambda q:min(sum(a!=b for a,b in zip(q,p)) for p in reference))
        else:x=tuple(rng.sample(domain,len(domain)))
        population.append(x)
    return population[:config.population]


def run_search(*,items,incumbents,objective,seed,config,max_evaluations,
               checkpoints=(50000,100000,250000,500000),folder=None,
               quality=None,max_generations=None,lookup_objective=None):
    domain=tuple(str(x) for x in items);index={v:i for i,v in enumerate(domain)}
    inc={str(k):tuple(str(v) for v in x) for k,x in incumbents.items()}
    assert all(len(x)==len(domain) and set(x)==set(domain) for x in inc.values())
    assert config.population>=len(inc) and config.elites<config.population
    rng=random.Random(int(seed));process=psutil.Process();start=time.perf_counter();state_path=None
    if folder is not None:
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);state_path=folder/'CHECKPOINT.pkl.gz'
    checkpoint_values=sorted(c for c in set(checkpoints) if 0<c<=max_evaluations)
    cache={};first={};samples={};history=[];budget_rows=[];moves=[];parent_rows=[]
    state=dict(phase='incumbents',generation=0,inc_index=0,population=None,scores=[],next_index=0,
               attempts=0,expensive_calls=0,lookup_calls=0,score_seconds=0.,elapsed_seconds=0.,
               archive_score=-np.inf,archive_seq=None,archive_generation=0,best_seen=-np.inf,best_seq=None,
               last_improvement_evaluations=0,last_improvement_seconds=0.,peak_rss_bytes=process.memory_info().rss,
               parents=None,flags=None,selection={},restart_count=0,last_restart_evaluations=0)
    if state_path is not None and state_path.exists():
        with gzip.open(state_path,'rb') as f:saved=pickle.load(f)
        assert saved['config']==asdict(config) and saved['seed']==seed
        state=saved['state'];cache=saved['cache'];first=saved['first'];history=saved['history'];budget_rows=saved['budget_rows'];moves=saved['moves'];parent_rows=saved['parent_rows'];rng.setstate(saved['rng'])
    offset=state['elapsed_seconds'];last_saved=len(cache)
    def key(seq):return bytes(index[v] for v in seq)
    def elapsed():return offset+time.perf_counter()-start
    def save():
        if state_path is None:return
        state['elapsed_seconds']=elapsed();record=dict(config=asdict(config),seed=seed,state=state,cache=cache,first=first,history=history,budget_rows=budget_rows,moves=moves,parent_rows=parent_rows,rng=rng.getstate())
        tmp=state_path.with_suffix('.tmp')
        with gzip.open(tmp,'wb',compresslevel=1) as f:pickle.dump(record,f,protocol=5)
        tmp.replace(state_path)
        pd.DataFrame(history).to_csv(folder/'GENERATION_DIAGNOSTICS.csv',index=False)
        pd.DataFrame(budget_rows).to_csv(folder/'BUDGET_CHECKPOINTS.csv',index=False)
    def budget_snapshot():
        budget_rows.append(dict(seed=seed,**asdict(config),distinct_evaluations=len(cache),total_attempts=state['attempts'],actual_expensive_calls=state['expensive_calls'],lookup_calls=state['lookup_calls'],generation=state['generation'],best_service_loss_hr=-state['best_seen'],archive_service_loss_hr=-state['archive_score'],elapsed_seconds=elapsed(),objective_seconds=state['score_seconds'],peak_rss_mb=state['peak_rss_bytes']/2**20,sequence_sha256=hashlib.sha256(('\n'.join(state['best_seq'])+'\n').encode()).hexdigest(),sequence=list(state['best_seq']),checkpoint_scope='Exact distinct-permutation boundary, possibly within a generation'))
    def score(seq):
        k=key(seq);state['attempts']+=1
        if k not in cache:
            tick=time.perf_counter()
            if lookup_objective is not None and k in lookup_objective:
                value=float(lookup_objective[k]);state['lookup_calls']+=1
            else:value=float(objective(seq));state['expensive_calls']+=1
            assert np.isfinite(value);state['score_seconds']+=time.perf_counter()-tick;cache[k]=value;first[k]=(state['generation'],state['attempts'],elapsed())
            if value>state['best_seen']:
                old=state['best_seen'];state['best_seen']=value;state['best_seq']=seq;state['last_improvement_evaluations']=len(cache);state['last_improvement_seconds']=elapsed()
                moves.append(dict(generation=state['generation'],distinct_evaluations=len(cache),elapsed_seconds=elapsed(),service_loss_hr=-value,improvement_hr=value-old if np.isfinite(old) else None,sequence=list(seq)))
            if len(cache)%250==0:state['peak_rss_bytes']=max(state['peak_rss_bytes'],process.memory_info().rss)
            if len(cache) in checkpoint_values:budget_snapshot()
        return cache[k]
    def observe():
        pop=state['population'];scored=state['scores'];idx=max(range(len(pop)),key=lambda i:(scored[i],tuple(pop[i])))
        if scored[idx]>state['archive_score']:
            state['archive_score']=scored[idx];state['archive_seq']=pop[idx];state['archive_generation']=state['generation']
        values=np.array(scored);row=dict(generation=state['generation'],generation_best=max(scored),generation_mean=float(np.mean(scored)),generation_median=float(np.median(scored)),best_so_far=state['archive_score'],population_best_service_loss_hr=-max(scored),population_mean_service_loss_hr=-values.mean(),population_median_service_loss_hr=-np.median(values),best_so_far_service_loss_hr=-state['archive_score'],best_observed_service_loss_hr=-state['best_seen'],unique_population=len(set(pop)),unique_candidates_evaluated=len(cache),total_attempts=state['attempts'],duplicate_objective_fraction=1-len(cache)/state['attempts'],evaluations_since_strict_improvement=len(cache)-state['last_improvement_evaluations'],seconds_since_strict_improvement=elapsed()-state['last_improvement_seconds'],elapsed_seconds=elapsed(),objective_seconds=state['score_seconds'],peak_rss_mb=state['peak_rss_bytes']/2**20,archive_copies_in_population=pop.count(state['archive_seq']),**diversity(pop,index),**state['selection'])
        for name,seq in inc.items():row['incumbent_copies_'+name]=pop.count(seq)
        row['deterministic_incumbents_remaining']=sum(pop.count(seq) for seq in set(inc.values()))
        if state['parents'] is not None:
            improvements=[];cross=[];mut=[];combined=[];cxchanged=0;mchanged=0
            for j,flag in enumerate(state['flags']):
                if flag['elite']:continue
                pv=state['parent_values'][j];success=scored[j]>max(pv);improvements.append(success)
                if flag['cross'] and flag['mutation']:combined.append(success)
                elif flag['cross']:cross.append(success)
                elif flag['mutation']:mut.append(success)
                cxchanged+=flag['cross_changed'];mchanged+=flag['mutation_changed']
            row.update(offspring_improving_parent_fraction=float(np.mean(improvements)) if improvements else 0,crossover_only_success_fraction=float(np.mean(cross)) if cross else np.nan,mutation_only_success_fraction=float(np.mean(mut)) if mut else np.nan,combined_success_fraction=float(np.mean(combined)) if combined else np.nan,crossover_changed_children=cxchanged,mutation_changed_children=mchanged,crossover_events=sum(f['cross'] for f in state['flags']),mutation_events=sum(f['mutation'] for f in state['flags']))
        history.append(row)
    while True:
        if state['phase']=='incumbents':
            names=list(inc)
            while state['inc_index']<len(names):
                if len(cache)>=max_evaluations:break
                score(inc[names[state['inc_index']]]);state['inc_index']+=1
            ranked=sorted([(cache[key(seq)],name,seq) for name,seq in inc.items()],key=lambda z:(-z[0],z[1],z[2]));best,name,seq=ranked[0];state['archive_score']=best;state['archive_seq']=seq
            state['population']=initialize(domain,inc,rng,config,quality);state['phase']='evaluate';state['scores']=[];state['next_index']=0
        if state['phase']=='evaluate':
            while state['next_index']<len(state['population']):
                seq=state['population'][state['next_index']]
                if len(cache)>=max_evaluations and key(seq) not in cache:break
                state['scores'].append(score(seq));state['next_index']+=1
                if len(cache)-last_saved>=25000:save();last_saved=len(cache)
            if state['next_index']<len(state['population']):break
            if config.diversity_replacement and state['generation']>0:
                # Deterministic crowding: each pair competes with its nearest
                # selected parental lineage, using already cached parent scores.
                pop=state['population'];values=state['scores'];parents=state['parents']
                for j in range(0,len(pop),2):
                    if j+1>=len(pop):break
                    a,b=parents[j],parents[j+1];x,y=pop[j],pop[j+1]
                    direct=sum(q!=v for q,v in zip(x,a))+sum(q!=v for q,v in zip(y,b))
                    reverse=sum(q!=v for q,v in zip(x,b))+sum(q!=v for q,v in zip(y,a))
                    pairs=[(a,state['parent_values'][j][0]),(b,state['parent_values'][j][1])]
                    if reverse<direct:pairs.reverse()
                    for k,(parent,parent_score) in enumerate(pairs):
                        if values[j+k]<parent_score:pop[j+k]=parent;values[j+k]=parent_score
            observe();state['phase']='reproduce'
            if max_generations is not None and state['generation']>=max_generations:break
            if len(cache)>=max_evaluations or state['attempts']>=50*max_evaluations:break
        if state['phase']=='reproduce':
            pop=state['population'];scored=[score(seq) for seq in pop];n=len(pop)
            selected=[];counts=np.zeros(n,dtype=int)
            for _ in range(n):
                ix=[rng.randrange(n) for _ in range(config.tournament)];j=max(ix,key=lambda j:scored[j]);selected.append(j);counts[j]+=1
            parent=[pop[j] for j in selected];values=np.array(scored);std=float(values.std());prob=counts[counts>0]/n
            pressure=(float(np.mean(values[selected]))-float(values.mean()))/std if std>0 else 0.
            rank=np.argsort(-values,kind='stable');sel=dict(parent_selection_intensity=pressure,parent_unique_count=int((counts>0).sum()),parent_effective_count=float(1/np.sum(prob**2)),top10_percent_parent_share=float(counts[rank[:max(1,n//10)]].sum()/n),best_parent_share=float(counts[rank[0]]/n),selected_parent_mean_service_loss_hr=float(-values[selected].mean()))
            for name,seq in inc.items():sel['parent_draws_'+name]=sum(counts[j] for j,x in enumerate(pop) if x==seq)
            parent_rows.append(dict(generation=state['generation']+1,selection_frequency_by_fitness_rank=counts[rank].copy(),parent_population_fitness_by_rank=values[rank].copy()))
            m=config.mutation
            if config.adaptive:m=min(.6,m*(1+(len(cache)-state['last_improvement_evaluations'])/10000))
            children=[];flags=[];pv=[]
            for j in range(0,n,2):
                a=parent[j];b=parent[(j+1)%n];original_a=a;original_b=b;did_cx=rng.random()<config.crossover
                if did_cx:a,b=crossover(a,b,rng,config.crossover_operator)
                before_a=a;before_b=b;ma=rng.random()<m
                if ma:a=mutation(a,rng,config.mutation_operator)
                mb=rng.random()<m
                if mb:b=mutation(b,rng,config.mutation_operator)
                children.extend([a,b]);pv.extend([(scored[selected[j]],scored[selected[(j+1)%n]])]*2)
                flags.extend([dict(cross=did_cx,mutation=ma,cross_changed=a!=original_a if not ma else before_a!=original_a,mutation_changed=a!=before_a,elite=False),dict(cross=did_cx,mutation=mb,cross_changed=b!=original_b if not mb else before_b!=original_b,mutation_changed=b!=before_b,elite=False)])
            children=children[:n];flags=flags[:n];pv=pv[:n]
            if config.elites:
                elite=[]
                for i in sorted(range(n),key=lambda i:(-scored[i],pop[i])):
                    if pop[i] not in elite:elite.append(pop[i])
                    if len(elite)==config.elites:break
                for j,x in enumerate(elite):children[n-len(elite)+j]=x;flags[n-len(elite)+j]=dict(cross=False,mutation=False,cross_changed=False,mutation_changed=False,elite=True)
            if config.restart and len(cache)-max(state['last_improvement_evaluations'],state['last_restart_evaluations'])>=10000:
                for j in range(max(config.elites,1),n//2):children[j]=tuple(rng.sample(domain,len(domain)));flags[j]=dict(cross=False,mutation=False,cross_changed=False,mutation_changed=False,elite=True)
                state['last_restart_evaluations']=len(cache);state['restart_count']+=1
            state.update(generation=state['generation']+1,population=children,scores=[],next_index=0,phase='evaluate',parents=parent,flags=flags,parent_values=pv,selection=sel)
    # A fixed expensive budget may end partway through a generation. Best-observed
    # then includes every evaluated valid chromosome; original completed archive
    # is retained separately, not falsely reported as having a generation update.
    state['peak_rss_bytes']=max(state['peak_rss_bytes'],process.memory_info().rss);save()
    if folder is not None:
        pd.DataFrame(history).to_csv(folder/'GENERATION_DIAGNOSTICS.csv',index=False)
        np.savez_compressed(folder/'PARENT_SELECTION.npz',generation=np.array([r['generation'] for r in parent_rows]),selection_frequency_by_fitness_rank=np.array([r['selection_frequency_by_fitness_rank'] for r in parent_rows]),parent_population_fitness_by_rank=np.array([r['parent_population_fitness_by_rank'] for r in parent_rows]))
        pd.DataFrame(budget_rows).to_csv(folder/'BUDGET_CHECKPOINTS.csv',index=False)
        (folder/'STRICT_IMPROVEMENTS.json').write_text(json.dumps(moves,indent=2)+'\n')
        keys=list(cache);np.savez_compressed(folder/'CANDIDATES.npz',station_ids=np.array(domain),orders=np.array([np.frombuffer(k,dtype=np.uint8) for k in keys]),fitness=np.array([cache[k] for k in keys]),first_generation=np.array([first[k][0] for k in keys]),first_attempt=np.array([first[k][1] for k in keys]),first_elapsed_seconds=np.array([first[k][2] for k in keys]))
    return dict(state=state,history=pd.DataFrame(history),budget_rows=budget_rows,best_sequence=state['best_seq'],best_fitness=state['best_seen'],archive_sequence=state['archive_seq'],archive_fitness=state['archive_score'],cache=cache,elapsed_seconds=elapsed())
