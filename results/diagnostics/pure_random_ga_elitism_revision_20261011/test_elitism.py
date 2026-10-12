"""Synthetic A-G tests; no physical sampling or objective calls."""
from dataclasses import replace
import random
import study as s

IDS=tuple(str(300000+i) for i in range(92))


def pool():
    rng=random.Random(123)
    return [tuple(rng.sample(IDS,92)) for _ in range(101)]


def objective(seq):
    return -sum((i+1)*(int(x)-300000) for i,x in enumerate(seq))


def run(folder,budget,mode='POST',cfg=s.CFG,**kwargs):
    return s.e.run_search(items=IDS,incumbents={},objective=objective,seed=2026121000,
        config=cfg,max_evaluations=budget,folder=s.a.lp(folder),
        elitism_mode=s.MODES[mode],checkpoints=(333,1000),**kwargs)


def test_A_last_best_survives():
    p=pool();children=p[:100];elite=p[100];values=[-33.0]*100
    values[0]=-34.2;values[-1]=-32.5
    action=s.e.post_evaluation_elitism(children,values,[(elite,-32.8)])[0]
    assert action['index']==0 and action['discarded_fitness']==-34.2
    assert children[-1]==p[99] and values[-1]==-32.5 and elite in children
    assert len(children)==100 and all(len(set(x))==92 for x in children)


def test_B_all_better_no_insertion():
    p=pool();children=p[:100];original=children.copy();values=[-32.5]*100
    actions=s.e.post_evaluation_elitism(children,values,[(p[100],-32.8)])
    assert actions[0]['reason']=='all_strictly_better' and children==original


def test_C_existing_elite_no_redundancy():
    p=pool();children=p[:100];original=children.copy()
    action=s.e.post_evaluation_elitism(children,[-33.0]*100,[(p[4],-32.8)])[0]
    assert action['reason']=='already_present' and children==original


def test_D_exact_ties_deterministic():
    p=pool();children=p[:100];values=[-32.0]*100;values[1]=values[3]=-32.8
    rng=random.Random(123);before=rng.getstate()
    action=s.e.post_evaluation_elitism(children,values,[(p[100],-32.8)])[0]
    assert action['index']==1 and values[1]==-32.8 and children[3]==p[3]
    assert rng.getstate()==before
    # The newly inserted exact chromosome prevents a second insertion.
    assert s.e.post_evaluation_elitism(children,values,[(p[100],-32.8)])[0]['reason']=='already_present'


def test_E_duplicate_cache_accounting(tmp_path):
    cfg=replace(s.CFG,crossover=0,mutation=0)
    r=run(tmp_path/'duplicate',500,cfg=cfg,max_generations=1)
    assert len(r['cache'])==r['state']['expensive_calls']==100
    assert r['state']['generated_offspring']==100 and r['state']['offspring_attempts']==100
    assert r['state']['offspring_new_distinct']==0 and r['state']['attempts']==300
    assert r['state']['completed_generations']==1 and len(set(r['state']['population']))<100


def test_F_partial_generation_and_boundary(tmp_path):
    r=run(tmp_path/'partial',101)
    st=r['state']
    assert len(r['cache'])==101 and st['phase']=='evaluate'
    assert st['next_index']<100 and not st['elitism_finalized']
    assert st['completed_generations']==st['elite_insertions']==0
    assert st['best_seen']==max(r['cache'].values())
    first=run(tmp_path/'complete_reference',1000,max_generations=1)
    boundary=len(first['cache'])
    r=run(tmp_path/'boundary',boundary)
    assert r['state']['completed_generations']==1 and r['state']['elitism_finalized']
    before=s.statefile(tmp_path/'boundary')
    run(tmp_path/'boundary',boundary)
    after=s.statefile(tmp_path/'boundary')
    assert before['rng']==after['rng'] and before['cache']==after['cache']
    for name in ('population','scores','phase','generation','next_index','elite_events','elite_insertions','completed_generations'):
        assert before['state'][name]==after['state'][name],name


def test_G_full_checkpoint_replay_and_pairing(tmp_path):
    final=[]
    for mode in ('LEGACY','POST'):
        whole=tmp_path/f'whole_{mode}';split=tmp_path/f'split_{mode}'
        run(whole,1000,mode)
        run(split,333,mode);run(split,1000,mode)
        a=s.statefile(whole);b=s.statefile(split)
        assert a['rng']==b['rng'] and a['cache']==b['cache'] and list(a['cache'])==list(b['cache'])
        for name in ('population','scores','phase','generation','next_index','elite_events',
                     'elite_insertions','elite_already_present','all_offspring_better','completed_generations',
                     'pending_elites','elitism_finalized','attempts','generated_offspring',
                     'offspring_attempts','offspring_new_distinct','best_seq','best_seen','archive_seq','archive_score'):
            assert a['state'][name]==b['state'][name],name
        final.append(a['state'])
    for name in ('initial_population','initial_rng_state','first_offspring_proposals','first_proposal_rng_state'):
        assert final[0][name]==final[1][name],name


def test_mode_switch_resume_rejected(tmp_path):
    folder=tmp_path/'mode';run(folder,101,'LEGACY')
    import pytest
    with pytest.raises(AssertionError):run(folder,333,'POST')
