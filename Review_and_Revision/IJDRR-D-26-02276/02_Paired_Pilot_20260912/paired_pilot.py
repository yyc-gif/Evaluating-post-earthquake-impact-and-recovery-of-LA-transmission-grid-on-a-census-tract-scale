"""Bounded revision experiment. Import legacy definitions without modifying them.

The scheduler receives an ex-ante priority list and the observed damaged task set.
The private event executor samples/uses realized service-action durations. No
priority or dispatch comparison can inspect future repair draws. Completion is
the sole local restoration event; source accessibility remains a separate gate.
All input and submission-era output files are read-only.
"""
from pathlib import Path
import os, sys
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
sys.dont_write_bytecode = True
import argparse, heapq, json, time, hashlib
import numpy as np
import pandas as pd
import networkx as nx
from scipy.special import ndtr, ndtri
from scipy.stats import norm, t as student_t
from threadpoolctl import threadpool_limits

OUT = Path(__file__).resolve().parent
BASE = OUT.parent.parent
ROOT = BASE / 'Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale'
AUDIT = BASE / '00_Project_Deliverables/Audit_IJDRR_20260912_01'
sys.path.insert(0, str(ROOT))
import C257H_Project_Main as legacy
H = 480.0
SEED = 20260912
POLICIES = ['Hospital-first', 'GA-Efficiency', 'Population-impact', 'GA-HospitalFirst']
NAMES = ['Hospital first', 'GA-Efficiency', 'Impact population first', 'GA-HospitalFirst']

def read_csv(path, **kwargs):
    return pd.read_csv('\\\\?\\' + str(path), **kwargs)

def load_inputs():
    cfg = legacy.Config()
    for key in ['DEVICES_CSV','PGA_CSV','MAP_TRACT_SUB_CSV','CEC_GRAPH_EDGES_CSV',
                'CEC_GRAPH_NODES_CSV','SOURCE_NODES_CSV','SVI_CSV']:
        setattr(cfg, key, '\\\\?\\' + str(getattr(cfg, key)))
    state = legacy.run_stage_0(cfg)
    ids = state['sub_index'].to_numpy(dtype=str)
    tids = state['tract_index'].to_numpy(dtype=str)
    W = np.asarray(state['W_mat'], dtype=float)
    joined = read_csv(AUDIT/'tract_population_vulnerability_join.csv', dtype={'tract_id':str}).set_index('tract_id').reindex(tids)
    pop = joined.population.to_numpy(float)
    assert np.isfinite(pop).all() and abs(pop.sum()-9066522) < 1e-6
    hospital = read_csv(ROOT/'Data/hospital_with_tract_expanded.csv')
    hids = set(hospital.GEOID.astype(str).str.replace(r'\.0$', '', regex=True).str.lstrip('0'))
    hosp = np.array([s.lstrip('0') in hids for s in tids], dtype=float)
    assert hosp.sum() > 0
    graph = legacy.build_base_graph(cfg, state['devices_merged'], state['sub_index'])
    sources = legacy.load_source_gate_nodes(cfg, state['sub_index'])
    graph = nx.relabel_nodes(graph, {s:i for i,s in enumerate(ids)})
    src = np.array([s in sources for s in ids], dtype=bool)
    schedules = read_csv(AUDIT/'schedules_normalized.csv', dtype={'substation_id':str})
    orders=[]
    for name in NAMES:
        q=schedules[(schedules.scenario=='2pc50')&(schedules.strategy==name)]
        # Audit concatenation preserved the original dispatch row order.
        order=np.array([np.flatnonzero(ids==x)[0] for x in q.substation_id],dtype=int)
        assert len(order)==len(ids) and len(set(order))==len(ids)
        orders.append(order)
    bm=read_csv(ROOT/'Stage 4 Output_expanded/travel_base_to_task.csv', index_col=0)
    tm=read_csv(ROOT/'Stage 4 Output_expanded/travel_task_to_task.csv', index_col=0)
    bm.index=bm.index.astype(str); bm.columns=bm.columns.astype(str)
    tm.index=tm.index.astype(str); tm.columns=tm.columns.astype(str)
    bm=bm.reindex(columns=ids); tm=tm.reindex(index=ids, columns=ids)
    assert np.isfinite(bm.to_numpy()).all() and np.isfinite(tm.to_numpy()).all()
    origins=read_csv(ROOT/'Data/stage45_C57_expanded_crew_origins.csv').travel_matrix_origin_key.astype(str).tolist()
    assert len(origins)==57
    return dict(cfg=cfg,state=state,ids=ids,tids=tids,W=W,pop=pop,hosp=hosp,
                joined=joined,graph=graph,sources=src,orders=orders,
                base_ids=list(bm.index),base=bm.to_numpy(),travel=tm.to_numpy(),origins=origins)

def original_negative_draws(x):
    """Recover raw negative draws only; do not re-evaluate old recovery curves."""
    raw_parts=[]; ds_parts=[]
    for worker, seed in enumerate(np.random.default_rng(42).integers(1,2**31,size=32)):
        rng=np.random.default_rng(seed); n=1000//32+int(worker<1000%32)
        ds=legacy.sample_damage_states(x['state']['devices_merged'].pga_2pc50,
                                      x['state']['devices_merged'],n,rng)
        raw=np.zeros(ds.shape)
        for k,(mu,sigma) in legacy.REPAIR_PARAM_NORMAL_HR.items():
            mask=ds==k; raw[mask]=rng.normal(mu,sigma,int(mask.sum()))
        ds_parts.append(ds); raw_parts.append(raw)
    raw=np.concatenate(raw_parts,axis=1); ds=np.concatenate(ds_parts,axis=1)
    rows=[]
    for k,(mu,sigma) in legacy.REPAIR_PARAM_NORMAL_HR.items():
        v=raw[ds==k]; negative=v[v<0]; p0=float(ndtr(-mu/sigma))
        mean_positive=mu+sigma*norm.pdf(mu/sigma)/(1-p0)
        mean_clipped=mu*(1-p0)+sigma*norm.pdf(mu/sigma)
        rows.append(dict(ds=k,draws=len(v),negative_count=len(negative),negative_rate=float((v<0).mean()),
                         negative_mean_h=float(negative.mean()) if len(negative) else None,
                         negative_min_h=float(negative.min()) if len(negative) else None,
                         negative_abs_sum_h=float(-negative.sum()),normal_mu=mu,normal_sigma=sigma,
                         theoretical_negative_rate=p0,clipped_expected_h=mean_clipped,
                         positive_expected_h=mean_positive))
    return rows

def physical_draw(x, realization):
    """Independent per-ID streams; invariant to workers, batch size and policy."""
    rng_d=np.random.default_rng(np.random.SeedSequence([SEED, realization, 1]))
    rng_r=np.random.default_rng(np.random.SeedSequence([SEED, realization, 2]))
    ds=legacy.sample_damage_states(x['state']['devices_merged'].pga_2pc50,
                                  x['state']['devices_merged'],1,rng_d)[:,0]
    u=rng_r.random(len(ds)); duration=np.zeros(len(ds)); unconditioned=np.zeros(len(ds))
    for k,(mu,sigma) in legacy.REPAIR_PARAM_NORMAL_HR.items():
        mask=ds==k; p0=ndtr(-mu/sigma)
        duration[mask]=mu+sigma*ndtri(p0+(1-p0)*u[mask])
        unconditioned[mask]=mu+sigma*ndtri(u[mask])
    assert np.all(duration[ds>0]>0) and np.all(duration[ds==0]==0)
    return ds,duration,u,unconditioned

def execute_queue(priority, damaged, hidden_duration, base, travel, origin_indices):
    """Static-list dispatch at observed release events, without duration foresight.

    heap is the simulator's future-event calendar, not an optimizer input.
    A policy only selects the next pending task once a crew actually becomes free.
    """
    n=len(damaged); starts=np.full(n,np.nan); finishes=np.zeros(n)
    crews=np.full(n,-1,int); previous=np.full(n,-1,int); travel_used=np.zeros(n)
    queue=[int(i) for i in priority if damaged[i]]
    events=[(0., c, -1) for c in range(len(origin_indices))]; heapq.heapify(events)
    dispatch_order=[]
    for task in queue:
        free,c,prev=heapq.heappop(events)
        move=base[origin_indices[c],task] if prev<0 else travel[prev,task]
        starts[task]=free+move
        finishes[task]=starts[task]+hidden_duration[task]
        crews[task]=c; previous[task]=prev; travel_used[task]=move
        dispatch_order.append(task)
        heapq.heappush(events,(finishes[task],c,task))
    assert np.allclose(finishes[damaged]-starts[damaged],hidden_duration[damaged])
    # Same crew may have gaps only for its explicitly recorded travel.
    for c in range(len(origin_indices)):
        tasks=[i for i in dispatch_order if crews[i]==c]
        last=0.
        for i in tasks:
            assert abs(starts[i]-last-travel_used[i])<1e-9
            last=finishes[i]
    return starts,finishes,crews,previous,travel_used

def gate_state(raw, graph, source_flags, threshold=.5):
    active=np.flatnonzero(raw>=threshold); gate=np.zeros(len(raw),bool)
    for component in nx.connected_components(graph.subgraph(active)):
        members=np.fromiter(component,dtype=int)
        if source_flags[members].any(): gate[members]=True
    return raw*gate,gate

def evaluate_events(x, ds, finishes, W=None):
    W=x['W'] if W is None else W
    raw0=np.array([legacy.INITIAL_FUNCTIONALITY_BY_DS[int(k)] for k in ds])
    times=np.unique(np.r_[0.,finishes[(ds>0)&(finishes<H)],H])
    eff=[]; gates=[]; triggers=[]
    for t in times:
        raw=raw0.copy(); raw[(ds>0)&(finishes<=t)]=1.
        e,g=gate_state(raw,x['graph'],x['sources'])
        eff.append(e); gates.append(g)
        done=np.flatnonzero((ds>0)&np.isclose(finishes,t,rtol=0,atol=1e-10))
        triggers.append(int(done[0]) if len(done)==1 else -1)
    eff=np.array(eff); gates=np.array(gates)
    assert np.all(np.diff(eff,axis=0)>=-1e-12) and np.allclose(eff[-1],1)
    dt=np.diff(times); station_b=(1-eff[:-1]).T@dt
    tract_b=W@station_b
    services=eff@W.T
    def first_cross(curve,level):
        ix=np.flatnonzero(curve>=level-1e-12)
        return float(times[ix[0]]) if len(ix) else np.nan
    tt=np.array([times[np.argmax(services>=p-1e-12,axis=0)] for p in [.5,.8,.9]])
    for k,p in enumerate([.5,.8,.9]): tt[k,services[-1]<p-1e-12]=np.nan
    popw=x['pop']/x['pop'].sum(); hw=x['hosp']/x['hosp'].sum()
    popcurve=eff@(W.T@popw); hospcurve=eff@(W.T@hw)
    # Independent aggregate check: event-curve integral equals tract aggregation.
    pop_b=float(popw@tract_b)
    assert abs(pop_b-np.dot(1-popcurve[:-1],dt))<1e-8
    t80idx=int(np.flatnonzero(popcurve>=.8-1e-12)[0])
    metrics={'makespan_h':float(finishes.max()),'population_T50_h':first_cross(popcurve,.5),
             'population_T80_h':first_cross(popcurve,.8),'population_T90_h':first_cross(popcurve,.9),
             'population_deficit_proxy_h':pop_b,'population_AUC':1-pop_b/H,
             'hospital_tract_deficit_proxy_h':float(hw@tract_b),
             'hospital_tract_T80_h':first_cross(hospcurve,.8),
             'T80_trigger_station_id':x['ids'][triggers[t80idx]] if triggers[t80idx]>=0 else '',
             'T80_event_population_service_jump':float(popcurve[t80idx]-(popcurve[t80idx-1] if t80idx else 0)),
             'T80_event_newly_source_connected_stations':int((gates[t80idx]&~gates[t80idx-1]).sum()) if t80idx else int(gates[0].sum()),
             'last_task_station_id':x['ids'][np.argmax(finishes)]}
    return dict(metrics=metrics,times=times,eff=eff,gates=gates,triggers=np.array(triggers),
                station_b=station_b,tract_b=tract_b,tract_times=tt,popcurve=popcurve,hospcurve=hospcurve,
                raw_station_b=(1-raw0)*finishes)

def mean_ci(v):
    v=np.asarray(v,dtype=float); v=v[np.isfinite(v)]; n=len(v)
    mean=float(v.mean()); se=float(v.std(ddof=1)/np.sqrt(n)) if n>1 else np.nan
    half=float(student_t.ppf(.975,n-1)*se) if n>1 else np.nan
    return dict(n=n,mean=mean,sd=float(v.std(ddof=1)) if n>1 else np.nan,
                ci95_low=mean-half,ci95_high=mean+half,positive_fraction=float((v>0).mean()))

def save_primary(x, results, draws, negative):
    records=[]; store={'station_ids':x['ids'],'tract_ids':x['tids'],'strategy_names':np.array(POLICIES),
                     'realization_ids':np.arange(len(draws)),'damage_state':np.array([z[0] for z in draws]),
                     'repair_duration_h':np.array([z[1] for z in draws]),'duration_uniform':np.array([z[2] for z in draws]),
                     'duration_unconditioned_h':np.array([z[3] for z in draws]),'population':x['pop'],
                     'cdc2022_RPL_THEMES':x['joined'].RPL_THEMES.to_numpy(float),
                     'legacy_NRI_SOVI_SCORE':x['joined'].SOVI_SCORE.to_numpy(float),
                     'source_flags':x['sources'],'W':x['W'],
                     'metadata_json':np.array(json.dumps({'seed':SEED,'horizon_h':H,'scenario':'2pc50',
                         'crew_count':57,'ordering':'retained ex-ante priority lists; remove observed DS0 tasks',
                         'negative_draw_summary':negative},ensure_ascii=False))}
    flat=[results[k][p] for k in range(len(draws)) for p in range(4)]
    max_events=max(len(z['times']) for z in flat)
    for key,field in [('event_times_h','times'),('event_population_service','popcurve'),('event_hospital_tract_service','hospcurve')]:
        arr=np.full((len(flat),max_events),np.nan)
        for j,z in enumerate(flat): arr[j,:len(z[field])]=z[field]
        store[key]=arr.reshape(len(draws),4,max_events)
    for key,field in [('event_station_service','eff'),('event_station_gate','gates')]:
        arr=np.full((len(flat),max_events,len(x['ids'])),np.nan)
        for j,z in enumerate(flat): arr[j,:len(z[field])]=z[field]
        store[key]=arr.reshape(len(draws),4,max_events,len(x['ids']))
    for key in ['starts','finishes','crews','previous','travel_used','station_b','raw_station_b','tract_b','tract_times']:
        store[key]=np.array([[z[key] for z in row] for row in results])
    for k,row in enumerate(results):
        sample_hash=hashlib.sha256(draws[k][0].tobytes()+draws[k][1].tobytes()).hexdigest()[:16]
        for p,z in enumerate(row):
            record=dict(realization_id=k,scenario='2pc50',crews=57,strategy=POLICIES[p],sample_key=sample_hash,
                        repair_task_count=int((draws[k][0]>0).sum()),total_sampled_repair_h=float(draws[k][1].sum()),
                        total_travel_h=float(z['travel_used'].sum()),**z['metrics'])
            for key in ['makespan_h','population_T50_h','population_T80_h','population_T90_h',
                        'population_deficit_proxy_h','hospital_tract_deficit_proxy_h']:
                record['delta_'+key+'_vs_Hospital_first']=z['metrics'][key]-row[0]['metrics'][key]
            records.append(record)
    table=pd.DataFrame(records); table.to_csv(OUT/'PAIRED_PILOT_RESULTS.csv',index=False)
    b=store['tract_b']; diff=b[:,0]-b[:,1]
    tt=store['tract_times']; td=tt[:,0,1,:]-tt[:,1,1,:]
    j=x['joined']; svi=j.RPL_THEMES.to_numpy(float); group=np.full(len(svi),'missing',dtype='U8')
    valid=np.isfinite(svi)&(svi>=0)
    group[valid]=pd.qcut(svi[valid],4,labels=['Q1','Q2','Q3','Q4']).astype(str)
    cols=dict(tract_id=np.char.zfill(x['tids'],11),population=x['pop'].astype(int),
              cdc2022_RPL_THEMES=svi,legacy_NRI_SOVI_SCORE=j.SOVI_SCORE.to_numpy(float),SVI_quartile=group,
              baseline_strategy='GA-Efficiency',baseline_burden_mean_proxy_h=b[:,1].mean(axis=0),
              Hospital_first_burden_mean_proxy_h=b[:,0].mean(axis=0),
              difference_Hospital_minus_baseline_proxy_h=diff.mean(axis=0),
              paired_difference_sd_h=diff.std(axis=0,ddof=1),
              improvement_probability=(diff < -1e-9).mean(axis=0),worsening_probability=(diff>1e-9).mean(axis=0),
              expected_improvement_magnitude_h=np.maximum(-diff,0).mean(axis=0),
              expected_worsening_magnitude_h=np.maximum(diff,0).mean(axis=0),
              paired_difference_p10_h=np.quantile(diff,.1,axis=0),paired_difference_p50_h=np.quantile(diff,.5,axis=0),
              paired_difference_p90_h=np.quantile(diff,.9,axis=0),
              baseline_tract_T80_mean_h=tt[:,1,1,:].mean(axis=0),
              Hospital_first_tract_T80_mean_h=tt[:,0,1,:].mean(axis=0),
              paired_tract_T80_difference_mean_h=td.mean(axis=0),n_realizations=len(draws))
    pd.DataFrame(cols).to_csv(OUT/'TRACT_DISTRIBUTIONAL_EFFECTS.csv',index=False)
    np.savez_compressed(OUT/'PAIRED_EVENT_DATA.npz',**store)
    summaries={}
    for p in range(1,4):
        rows=table[table.strategy==POLICIES[p]]
        summaries[POLICIES[p]]={c:mean_ci(rows[c]) for c in rows.columns if c.startswith('delta_')}
    print(json.dumps({'paired_summaries_strategy_minus_Hospital':summaries,'negative_draws':negative},indent=2),flush=True)

def pilot(n):
    tic=time.perf_counter(); x=load_inputs(); negative=original_negative_draws(x)
    origin_idx=np.array([x['base_ids'].index(s) for s in x['origins']])
    results=[]; draws=[]
    for k in range(n):
        d=physical_draw(x,k); draws.append(d); ds,duration,_,_=d; row=[]
        for p,order in enumerate(x['orders']):
            starts,finishes,crews,previous,move=execute_queue(order,ds>0,duration,x['base'],x['travel'],origin_idx)
            z=evaluate_events(x,ds,finishes)
            z.update(starts=starts,finishes=finishes,crews=crews,previous=previous,travel_used=move)
            row.append(z)
        assert all(np.array_equal(z['gates'][0],row[0]['gates'][0]) for z in row)
        results.append(row)
        if (k+1)%8==0: print('paired realizations',k+1,'elapsed_s',round(time.perf_counter()-tic,2),flush=True)
    save_primary(x,results,draws,negative)

def inspect_existing():
    """Analyze saved pilot only. No new physical draws, schedules, or GA runs."""
    from scipy.stats import spearmanr
    x=load_inputs()
    with np.load(OUT/'PAIRED_EVENT_DATA.npz',allow_pickle=False) as archive:
        data={k:archive[k] for k in archive.files}
    table=read_csv(OUT/'PAIRED_PILOT_RESULTS.csv')
    tract=read_csv(OUT/'TRACT_DISTRIBUTIONAL_EFFECTS.csv',dtype={'tract_id':str})
    pop=x['pop']; pw=pop/pop.sum(); b=data['tract_b']; delta=b[:,0]-b[:,1]
    def weighted_q(values,weights,quantile):
        order=np.argsort(values); v=np.asarray(values)[order]; w=np.asarray(weights)[order]
        return float(np.interp(quantile,np.cumsum(w)/w.sum(),v))
    # Compare identical estimands: mean of T80 AND T80 of the mean step curve.
    curve_summary={}; metrics={}; group_summary=[]
    for p,label in enumerate(POLICIES):
        rows=table[table.strategy==label]
        metrics[label]={col:mean_ci(rows[col]) for col in ['makespan_h','population_T50_h',
            'population_T80_h','population_T90_h','population_deficit_proxy_h','hospital_tract_deficit_proxy_h']}
        alltimes=data['event_times_h'][:,p].ravel(); grid=np.unique(alltimes[np.isfinite(alltimes)])
        curves=[]
        for k in range(len(b)):
            t=data['event_times_h'][k,p]; valid=np.isfinite(t); t=t[valid]
            v=data['event_population_service'][k,p,valid]
            curves.append(v[np.searchsorted(t,grid,side='right')-1])
        mc=np.mean(curves,axis=0)
        curve_summary[label]={f'T{int(q*100)}_of_mean_curve_h':float(grid[np.flatnonzero(mc>=q)[0]]) for q in [.5,.8,.9]}
        for group in ['Q1','Q2','Q3','Q4']:
            mask=tract.SVI_quartile.eq(group).to_numpy(); weights=pw[mask]/pw[mask].sum()
            paired=np.sum(delta[:,mask]*weights,axis=1)
            group_summary.append(dict(policy=label,group=group,population=int(pop[mask].sum()),
                mean_B_h=float(np.mean(b[:,p,mask]@weights)),
                mean_realization_weighted_P90_B_h=float(np.mean([weighted_q(v,pop[mask],.9) for v in b[:,p,mask]])),
                delta_Hospital_minus_GAEff=mean_ci(paired)))
    mean_delta=delta.mean(axis=0)
    distribution={'residents_mean_burden_improves':int(pop[mean_delta<-1e-9].sum()),
        'residents_mean_burden_worsens':int(pop[mean_delta>1e-9].sum()),
        'tracts_mean_improves':int((mean_delta<-1e-9).sum()),'tracts_mean_worsens':int((mean_delta>1e-9).sum()),
        'residents_improve_over_1_proxy_h':int(pop[mean_delta<-1].sum()),
        'residents_worsen_over_1_proxy_h':int(pop[mean_delta>1].sum()),
        'population_weighted_tract_mean_delta_quantiles':{str(q):weighted_q(mean_delta,pop,q) for q in [.05,.1,.25,.5,.75,.9,.95]},
        'gross_expected_improvement_h':float(np.mean(np.maximum(-delta,0)@pw)),
        'gross_expected_worsening_h':float(np.mean(np.maximum(delta,0)@pw)),
        'per_realization_population_improves':mean_ci((delta<-1e-9)@pop),
        'per_realization_population_worsens':mean_ci((delta>1e-9)@pop),
        'residents_Hospital_better_in_at_least_90pct':int(pop[(delta<-1e-9).mean(axis=0)>=.9].sum()),
        'residents_Hospital_worse_in_at_least_90pct':int(pop[(delta>1e-9).mean(axis=0)>=.9].sum())}
    baseline=tract.baseline_burden_mean_proxy_h.to_numpy()
    cutoff=weighted_q(baseline,pop,.9); tail=baseline>=cutoff
    distribution['baseline_high_burden_top_population_decile']={'cutoff_B_h':cutoff,
        'population':int(pop[tail].sum()),'tracts':int(tail.sum()),
        'mean_delta_h':float(np.average(mean_delta[tail],weights=pop[tail])),
        'population_worsens':int(pop[tail&(mean_delta>0)].sum())}
    distribution['baseline_burden_vs_delta_spearman']=float(spearmanr(baseline,mean_delta).statistic)
    svi=tract.cdc2022_RPL_THEMES.to_numpy(); good=(svi>=0)&np.isfinite(svi)
    distribution['SVI_vs_delta_spearman_descriptive']=float(spearmanr(svi[good],mean_delta[good]).statistic)
    # Exact linear accounting after gating; never claim an independent causal effect.
    station_pw=x['W'].T@pw
    station_delta=(data['station_b'][:,1]-data['station_b'][:,0]).mean(axis=0)
    raw_delta=(data['raw_station_b'][:,1]-data['raw_station_b'][:,0]).mean(axis=0)
    contribution=station_pw*station_delta
    # Convex bounds on existing candidate support. Not independent mapping validation.
    mean_hospital_minus_ga=-station_delta
    support=x['W']>0
    lower=np.where(support,mean_hospital_minus_ga[None,:],np.inf).min(axis=1)
    upper=np.where(support,mean_hospital_minus_ga[None,:],-np.inf).max(axis=1)
    sign=np.where(upper < -1e-9,'improves_for_all_existing_candidates',
         np.where(lower > 1e-9,'worsens_for_all_existing_candidates','weight_dependent_or_tie'))
    tract['existing_candidate_support_delta_lower_h']=lower
    tract['existing_candidate_support_delta_upper_h']=upper
    tract['existing_candidate_support_sign']=sign
    tract.to_csv(OUT/'TRACT_DISTRIBUTIONAL_EFFECTS.csv',index=False)
    support_summary={v:dict(tracts=int((sign==v).sum()),population=int(pop[sign==v].sum())) for v in np.unique(sign)}
    # If crews >= damaged tasks, each dispatch happens at t=0: only assigned-depot
    # travel changes. Uniform completion-time bounds propagate through monotone gate/W.
    abundant=legacy._scale_sensitivity_crew_origins(x['origins'],2.)
    possible_origin_ids=sorted(set(abundant[:len(x['ids'])]))
    possible_indices=[x['base_ids'].index(s) for s in possible_origin_ids]
    spread=np.ptp(x['base'][possible_indices],axis=0)
    resource_bound=dict(crews=len(abundant),max_tasks=len(x['ids']),max_dispatch_queue_delay_h=0,
        conservative_max_completion_or_service_threshold_difference_h=float(spread.max()),
        station_attaining_bound=x['ids'][np.argmax(spread)],
        type='algebraic bound from retained travel matrix, not a new crew-level simulation',
        crew29_minimum_queued_tasks_in_saved_realizations=int(np.min((data['damage_state']>0).sum(axis=1)-29)))
    names=x['state']['devices_merged']['NAME'].astype(str).to_numpy()
    mechanism={'raw_timing_contribution_h':float(station_pw@raw_delta),
        'gate_penalty_contribution_h':float(station_pw@(station_delta-raw_delta)),
        'top_station_terms':[], 'negative_station_terms':[], 'completion_tail':{},'T80_events':{}}
    for group,indices in [('top_station_terms',np.argsort(contribution)[-8:][::-1]),
                          ('negative_station_terms',np.argsort(contribution)[:5])]:
        for i in indices:
            mechanism[group].append(dict(station_id=x['ids'][i],name=names[i],mapped_population=float(station_pw[i]*pop.sum()),
                system_deficit_contribution_h=float(contribution[i]),
                start_Hospital_h=float(np.nanmean(data['starts'][:,0,i])),
                start_GAEff_h=float(np.nanmean(data['starts'][:,1,i])),
                completion_Hospital_h=float(data['finishes'][:,0,i].mean()),
                completion_GAEff_h=float(data['finishes'][:,1,i].mean())))
    for label in ['Hospital-first','GA-Efficiency']:
        rows=table[table.strategy==label]
        mechanism['completion_tail'][label]=rows.last_task_station_id.astype(str).value_counts().to_dict()
        mechanism['T80_events'][label]={'triggers':rows.T80_trigger_station_id.astype(str).value_counts().to_dict(),
            'mean_new_source_connected_stations':float(rows.T80_event_newly_source_connected_stations.mean()),
            'mean_service_jump':float(rows.T80_event_population_service_jump.mean())}
    # Representative observed pilot, selected nearest to the median paired T80 difference.
    de=(table[table.strategy=='GA-Efficiency'].population_T80_h.to_numpy()-
        table[table.strategy=='Hospital-first'].population_T80_h.to_numpy())
    dm=(table[table.strategy=='GA-Efficiency'].makespan_h.to_numpy()-
        table[table.strategy=='Hospital-first'].makespan_h.to_numpy())
    joint={'GA_faster_tasks_but_slower_population':int(((dm<0)&(de>0)).sum()),
           'Hospital_better_on_both':int(((dm>0)&(de>0)).sum()),
           'GA_better_on_both':int(((dm<0)&(de<0)).sum()),
           'Hospital_faster_tasks_but_slower_population':int(((dm>0)&(de<0)).sum())}
    mechanism['paired_quadrants']=joint
    candidates=np.flatnonzero((dm<0)&(de>0))
    if len(candidates):
        distance=abs(dm[candidates]-np.median(dm[candidates]))/max(np.std(dm[candidates]),1e-12)
        distance+=abs(de[candidates]-np.median(de[candidates]))/max(np.std(de[candidates]),1e-12)
        case=int(candidates[np.argmin(distance)])
        bottlenecks=[]
        for p in [0,1]:
            i=int(np.argmax(data['finishes'][case,p])); sid=x['ids'][i]
            bottlenecks.append(dict(policy=POLICIES[p],station_id=sid,name=names[i],
                mapped_population=float(station_pw[i]*pop.sum()),
                mapped_population_percentile=float((station_pw<=station_pw[i]).mean()),
                duration_h=float(data['repair_duration_h'][case,i]),
                start_Hospital_h=float(data['starts'][case,0,i]),start_GAEff_h=float(data['starts'][case,1,i]),
                finish_Hospital_h=float(data['finishes'][case,0,i]),finish_GAEff_h=float(data['finishes'][case,1,i])))
        mechanism['conditional_tradeoff_example']={'realization_id':case,'makespan_GA_minus_Hospital_h':float(dm[case]),
            'population_T80_GA_minus_Hospital_h':float(de[case]),'last_tasks':bottlenecks,
            'selection':'Within observed tradeoff quadrant, closest to its two marginal medians; descriptive only.'}
    duration_shift=data['repair_duration_h']-np.maximum(data['duration_unconditioned_h'],0)
    distribution['duration_distribution_change_only']={'mean_positive_minus_clipped_per_damaged_task_h':float(duration_shift[data['damage_state']>0].mean()),
        'mean_total_additional_work_per_realization_h':float(duration_shift.sum(axis=1).mean()),
        'max_single_task_shift_h':float(duration_shift.max()),
        'note':'paired inverse-CDF duration comparison only; not a service-outcome counterfactual'}
    k=int(np.argmin(abs(de-np.median(de)))); mechanism['representative_realization_id']=k
    mechanism['representative_T80_paths']={}
    for p in [0,1]:
        row=table[(table.realization_id==k)&(table.strategy==POLICIES[p])].iloc[0]
        t80=row.population_T80_h; t=data['event_times_h'][k,p]
        event=int(np.nanargmin(abs(t-t80)))
        active=np.flatnonzero(data['event_station_gate'][k,p,event]>.5)
        graph=x['graph'].subgraph(active)
        target=int(np.argmax((data['event_station_service'][k,p,event]-data['event_station_service'][k,p,event-1])*station_pw))
        paths=[nx.shortest_path(graph,s,target) for s in active if x['sources'][s] and nx.has_path(graph,s,target)]
        path=min(paths,key=len)
        mechanism['representative_T80_paths'][POLICIES[p]]={'T80_h':t80,
             'trigger':str(row.T80_trigger_station_id),'largest_jump_station':x['ids'][target],
             'one_active_source_path':[x['ids'][i] for i in path]}
    evidence=dict(metrics=metrics,mean_curve_metrics=curve_summary,groups=group_summary,
                  distribution=distribution,mechanism=mechanism,
                  mapping_support_bounds=support_summary,resource_bound=resource_bound)
    data['analysis_json']=np.array(json.dumps(evidence,ensure_ascii=False))
    metadata=json.loads(str(data['metadata_json']))
    metadata['legacy_source_sha256']=hashlib.sha256((ROOT/'C257H_Project_Main.py').read_bytes()).hexdigest()
    metadata['revision_driver_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    data['metadata_json']=np.array(json.dumps(metadata,ensure_ascii=False))
    np.savez_compressed(OUT/'PAIRED_EVENT_DATA.npz',**data)
    print(json.dumps(evidence,ensure_ascii=False,indent=2),flush=True)

def check_interface():
    """Independent small examples for the new interface, not legacy reproduction."""
    simple={'W':np.array([[0.,0.,1.]]),'pop':np.array([100.]),'hosp':np.array([1.]),
            'graph':nx.path_graph(3),'sources':np.array([True,False,False]),
            'ids':np.array(['source','bridge','load'])}
    ds=np.array([0,4,4]); completion=np.array([0.,10.,3.])
    e=evaluate_events(simple,ds,completion)
    assert e['metrics']['population_T80_h']==10.
    assert e['tract_b'][0]==10.
    assert not e['gates'][1,2] and e['gates'][2,2]
    z=evaluate_events(simple,np.zeros(3,int),np.zeros(3))
    assert z['tract_b'][0]==0 and z['metrics']['population_T80_h']==0
    travel=np.zeros((3,3)); base=np.zeros((1,3)); orders=np.arange(3)
    a=execute_queue(orders,np.ones(3,bool),np.array([10.,3.,1.]),base,travel,np.array([0,0]))
    c=execute_queue(orders,np.ones(3,bool),np.array([10.,3.,400.]),base,travel,np.array([0,0]))
    assert np.array_equal(a[0],np.array([0.,0.,3.])) and np.array_equal(a[0],c[0])
    assert np.array_equal(a[2],c[2])
    print('Interface checks passed: repair before source access; exact deficit integration; undamaged state; nonanticipative dispatch prefix.')

def plot_existing():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    table=read_csv(OUT/'PAIRED_PILOT_RESULTS.csv')
    tract=read_csv(OUT/'TRACT_DISTRIBUTIONAL_EFFECTS.csv')
    e=table[table.strategy=='GA-Efficiency']
    dx=e.delta_makespan_h_vs_Hospital_first.to_numpy()
    dy=e.delta_population_T80_h_vs_Hospital_first.to_numpy()
    cx=mean_ci(dx); cy=mean_ci(dy)
    fig,axes=plt.subplots(1,2,figsize=(12.5,4.7),layout='constrained')
    ax=axes[0]; ax.scatter(dx,dy,s=28,color='#217f8c',alpha=.75,label='32 paired realizations')
    ax.errorbar(cx['mean'],cy['mean'],xerr=cx['mean']-cx['ci95_low'],yerr=cy['mean']-cy['ci95_low'],
                fmt='D',color='#bd4e3b',capsize=4,label='Mean and marginal 95% CIs')
    ax.axvline(0,color='.4',lw=.8); ax.axhline(0,color='.4',lw=.8)
    ax.set_xlabel('GA-Efficiency minus Hospital-first makespan (h)')
    ax.set_ylabel('GA-Efficiency minus Hospital-first population T80 (h)')
    ax.set_title('A. Makespan advantage does not persist in this pilot',fontsize=11)
    ax.legend(fontsize=8,loc='upper left'); ax.grid(alpha=.15)
    ax=axes[1]
    colors=['#2c7bb6','#55a868','#dd9c28','#c95151']
    for group,color in zip(['Q1','Q2','Q3','Q4'],colors):
        d=tract[tract.SVI_quartile==group].sort_values('difference_Hospital_minus_baseline_proxy_h')
        cumulative=d.population.cumsum()/d.population.sum()
        ax.step(d.difference_Hospital_minus_baseline_proxy_h,cumulative,where='post',label=group,color=color)
    ax.axvline(0,color='.4',lw=.8); ax.set_ylim(0,1)
    ax.set_xlabel('Hospital-first minus GA-Efficiency mean tract deficit (proxy h)')
    ax.set_ylabel('Cumulative resident share within fixed SVI group')
    ax.set_title('B. Overall gain includes tracts with greater burden',fontsize=11)
    ax.legend(title='CDC 2022 SVI quartile',fontsize=8,title_fontsize=8,loc='lower right'); ax.grid(alpha=.15)
    fig.suptitle('Completion-event pilot: 2%-in-50-year scenario, 57 crews, fixed priority lists',fontsize=12)
    fig.savefig(OUT/'CORE_DIAGNOSTIC.png',dpi=200)
    plt.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--n',type=int,default=32)
    parser.add_argument('--analyze',action='store_true')
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--plot',action='store_true')
    args=parser.parse_args()
    if not 2<=args.n<=64: raise ValueError('Bounded pilot only: 2..64 realizations; no automatic expansion.')
    with threadpool_limits(limits=1):
        if args.check: check_interface()
        elif args.plot: plot_existing()
        elif args.analyze: inspect_existing()
        else: pilot(args.n)
