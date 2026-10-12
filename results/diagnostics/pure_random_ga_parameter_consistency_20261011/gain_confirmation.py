"""Disclosed post-screen amendment: confirm promising, not only harmful, contrasts."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import audit as a

def register():
    assert not (a.OUT/'GAIN_CONFIRMATION_DESIGN.json').exists()
    assert not (a.OUT/'PARAMETER_DECISION_FROZEN.json').exists()
    rows=a.effects(a.frame(a.OUT/'PARAMETER_SCREEN_RESULTS.csv'),12)
    candidates=sorted([r for r in rows if r['simultaneous95_high_hr']<0],key=lambda r:(r['mean_delta_hr'],r['case']))[:3]
    assert [x['case'] for x in candidates]==['P50','CX60','T5']
    a.save('GAIN_CONFIRMATION_DESIGN.json',dict(
        amendment='Post-screen, before inspecting any100k confirmation outcomes or physical-validation outcomes. Original largest-absolute-effect family remains intact.',
        scientific_reason='Original rule selected only slower settings. Three family-adjusted screen improvements leave a consequential untested100k question; independently confirm these without broadening to a factorial or high-budget continuation.',
        cases=[x['case'] for x in candidates],seeds=a.CONFIRM,budget=100000,
        stage='gain_confirmation',reference='Exact already-running REF on the same20 seeds; reused once, not another independent reference cohort',
        seed_independence='Seeds are independent of the8 engineering-screen seeds, shared with the original confirmation family for paired comparisons.',
        family='All six100k contrasts receive Bonferroni simultaneous95 paired-t intervals; separate original3-family results retained as registered historical inference.',
        screen_selection=candidates,screen_sha256=a.sha(a.OUT/'PARAMETER_SCREEN_RESULTS.csv'),
        inspected_confirmation_results=False,validation_outcomes_loaded=False,
        no_candidate_selection_or_promotion=True,no_physical_sampling=True,
        code_sha256=a.sha(__file__)))
    print('POST_SCREEN_GAIN_DESIGN_REGISTERED',[x['case'] for x in candidates],flush=True)

def execute():
    d=a.read(a.OUT/'GAIN_CONFIRMATION_DESIGN.json');assert d['code_sha256']==a.sha(__file__)
    assert (a.OUT/'confirmation_EXECUTION.json').exists(),'Do not oversubscribe existing12-worker batch'
    assert not (a.OUT/'gain_confirmation_EXECUTION.json').exists()
    rows=[];tick=time.perf_counter()
    with ProcessPoolExecutor(max_workers=12,initializer=a.worker_setup) as pool:
        futures={pool.submit(a.run_one,'gain_confirmation',case,seed,100000):(case,seed) for seed in d['seeds'] for case in d['cases']}
        for future in as_completed(futures):
            row=future.result();rows.append(row);print('COMPLETE gain_confirmation',row['case'],row['seed'],round(row['final_loss_hr'],9),len(rows),len(futures),flush=True)
    a.csv('PARAMETER_GAIN_CONFIRMATION_RESULTS.csv',sorted(rows,key=lambda r:(r['case'],r['seed'])))
    a.save('gain_confirmation_EXECUTION.json',dict(status='PASS',cases=d['cases'],seeds=d['seeds'],budget=100000,
        distinct_calls=sum(x['distinct'] for x in rows),attempts=sum(x['attempts'] for x in rows),
        objective_seconds=sum(x['objective_seconds'] for x in rows),summed_run_wall_seconds=sum(x['wall_seconds'] for x in rows),
        batch_wall_seconds=time.perf_counter()-tick,new_physical_samples=0,validation_outcomes_loaded=False))

def decision():
    assert not (a.OUT/'PARAMETER_DECISION_FROZEN.json').exists()
    original=a.frame(a.OUT/'PARAMETER_CONFIRMATION_RESULTS.csv')
    gains=a.frame(a.OUT/'PARAMETER_GAIN_CONFIRMATION_RESULTS.csv')
    combined=a.pd.concat([original,gains],ignore_index=True)
    combined['stage']='confirmation_six_contrast'
    effects=a.effects(combined,6)
    original_effects=a.effects(original,3)
    rows=a.effects(a.frame(a.OUT/'PARAMETER_SCREEN_RESULTS.csv'),12)+original_effects+effects
    a.csv('PAIRED_PARAMETER_EFFECTS.csv',rows)
    better=[x for x in effects if x['simultaneous95_high_hr']<0]
    case=min(better,key=lambda r:(r['mean_delta_hr'],r['case']))['case'] if better else 'REF'
    a.save('PARAMETER_DECISION_FROZEN.json',dict(recommended_development_configuration=case,
        config=a.asdict(a.replace(a.REFERENCE,**a.CASES[case])),frozen_validated_method_changed=False,
        evidence_source_sha256={p:a.sha(a.OUT/p) for p in ['PARAMETER_SCREEN_RESULTS.csv','PARAMETER_CONFIRMATION_RESULTS.csv','PARAMETER_GAIN_CONFIRMATION_RESULTS.csv','PAIRED_PARAMETER_EFFECTS.csv','GAIN_CONFIRMATION_DESIGN.json']},
        validation_outcomes_loaded=False,no_new_candidate_selection=True,better_confirmation=better,
        original_three_contrast_family_preserved=True,post_screen_amendment_disclosed=True,simultaneous_family_size=6))
    text='# Final pure-random GA parameter decision\n\n'
    text+=f'Preferred development configuration: **{case}**, {a.asdict(a.replace(a.REFERENCE,**a.CASES[case]))}. The already validated reference and its frozen seed2026103108 sequence remain unchanged. No diagnostic final sequence is promoted or selected.\n\n'
    text+='The original preregistration selected the3 largest absolute screen effects. It selected only slower settings. A disclosed post-screen amendment, before inspecting100k confirmation or physical-validation outcomes, separately registered the3 screen alternatives whose12-family simultaneous interval was entirely negative. REF was reused once across the same20 independent confirmation seeds. All6 final-endpoint contrasts are adjusted together; the original3-family intervals remain in the CSV, not overwritten.\n\n'
    for r in effects:
        text+=f"- {r['case']} minus REF: mean {r['mean_delta_hr']:+.9f}h, median {r['median_delta_hr']:+.9f}h; simultaneous95 [{r['simultaneous95_low_hr']:+.9f}, {r['simultaneous95_high_hr']:+.9f}]h; wins/losses/ties {r['wins']}/{r['losses']}/{r['ties']}; median wall ratio {r['median_wall_ratio']:.3f}, attempt ratio {r['median_attempt_ratio']:.3f}.\n"
    text+='\nOptimizer seed is the replication unit; genomes/generations/checkpoints are not replicates. Screen and confirmation seeds do not overlap. Same-size settings share initial pools/RNG, followed by naturally diverging operator streams. P50/P100/P250 share random-pool prefixes; changes also affect initial minima, RNG length, duplicate rates and completed generations. No equivalence margin or unique numerical optimum is claimed. Parameter interactions were not estimated here; one-factor contrasts are conditional on the reference background.\n\n'
    text+='Any gain confirmed here is a separate planning-development finding, not a replacement for the already validated algorithm/candidate or a transfer of its physical validation. Enabled adaptation/restart/crowding and alternative crossovers were not needed for this bounded test; disabled status does not prove they are inferior. The original90% adoption rule failed; pure random was a disclosed post-data method choice. Historical100k strict proximity10/20, ten continued prefixes and their250k/500k plateau are retained, not reinterpreted as robust repeated-block success or global optimality. No new physical realization or high-budget continuation was generated.\n'
    a.md('FINAL_PURE_RANDOM_GA_PARAMETER_DECISION.md',text)
    print('FINAL_PARAMETER_DECISION_FROZEN',case,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['register','execute','decision']);x=p.parse_args()
    {'register':register,'execute':execute,'decision':decision}[x.phase]()
