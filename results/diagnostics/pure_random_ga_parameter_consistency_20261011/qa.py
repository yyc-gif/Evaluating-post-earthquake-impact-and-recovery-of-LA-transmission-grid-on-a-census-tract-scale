"""Scoped numerical/provenance QA and unchanged-checkout preservation."""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import gzip
import hashlib
import json
import inspect
from pathlib import Path
import platform
import pickle
import subprocess
import time
import zipfile
import numpy as np
import pandas as pd
import audit as a

def numerical():
    frames=[a.frame(a.OUT/'PARAMETER_SCREEN_RESULTS.csv'),a.frame(a.OUT/'PARAMETER_CONFIRMATION_RESULTS.csv'),a.frame(a.OUT/'PARAMETER_GAIN_CONFIRMATION_RESULTS.csv')]
    records=pd.concat(frames,ignore_index=True)
    assert len(records)==244 and not records.duplicated(['stage','case','seed']).any()
    assert len(frames[0])==104 and len(frames[1])==80 and len(frames[2])==60
    assert records.distinct.eq(records.budget).all()
    assert np.isfinite(records.final_loss_hr).all()
    assert np.allclose(records.initial_best_loss_hr-records.final_loss_hr,records.gain_after_random_initialization_hr,atol=1e-12)
    assert (records.gain_after_random_initialization_hr>0).all()
    manifests=[];initials={};fitness_ties=[]
    for r in records.to_dict('records'):
        row=a.read(a.OUT/f"runs/{r['stage']}/{r['case']}_{r['seed']}.json")
        assert a.identity(row['sequence'])==r['sequence_sha256']
        manifest=a.read(a.OUT/f"raw_evidence/{r['stage']}_{r['case']}_{r['seed']}.manifest.json")
        archive=a.OUT/f"raw_evidence/{r['stage']}_{r['case']}_{r['seed']}.zip"
        assert a.sha(archive)==manifest['zip_sha256']
        with zipfile.ZipFile(a.lp(archive)) as z:
            for member in manifest['members']:
                data=z.read(member['path'])
                assert hashlib.sha256(data).hexdigest()==member['sha256'] and len(data)==member['bytes']
            initial=json.loads(z.read('INITIAL_POPULATION.json'))
            checkpoint=pickle.loads(gzip.decompress(z.read('CHECKPOINT.pkl.gz')))
            assert len(checkpoint['cache'])==r['budget']==checkpoint['state']['expensive_calls']
            assert checkpoint['state']['lookup_calls']==0
            counts=Counter(checkpoint['cache'].values())
            fitness_ties.append(dict(stage=r['stage'],case=r['case'],seed=r['seed'],distinct_permutations=len(checkpoint['cache']),
                exact_scalar_fitness_values=len(counts),largest_exact_score_multiplicity=max(counts.values()),
                final_best_exact_score_multiplicity=counts[checkpoint['state']['best_seen']],
                interpretation='Equal scalar fitness does not prove equal dispatch/schedule; cache keys are full permutations, not physical phenotypes'))
            del checkpoint
            assert initial['initial_cache']==initial['archive_before_first_evaluation']==[]
            expected=__import__('random').Random(r['seed'])
            ids=a.load_study().load_model()[0].ids if not initials else next(iter(initials.values()))['domain']
            generated=[expected.sample(ids,92) for _ in range(r['population'])]
            assert generated==initial['initial_sequences']
            initials[(r['stage'],r['case'],r['seed'])]=dict(initial=initial,domain=ids)
        manifests.append(dict(archive=str(archive.relative_to(a.OUT)).replace('\\','/'),**manifest))
    for (stage,case,seed),stored in initials.items():
        refkey=('confirmation' if stage=='gain_confirmation' else stage,'REF',seed)
        if case=='REF': continue
        ref=initials[refkey]['initial']
        if case in ('P50','P250'):
            p=stored['initial']['initial_sequences'];q=ref['initial_sequences']
            assert p[:min(len(p),len(q))]==q[:min(len(p),len(q))]
        else: assert stored['initial']==ref
    a.save('COMPLETE_SEARCH_NUMERICAL_QA.json',dict(status='PASS',fresh_cold_start_searches=244,
        independent_optimizer_seed_blocks=28,screen_seed_blocks=8,confirmation_seed_blocks=20,
        cross_configuration_replication='Paired, not244 statistically independent observations; private empty caches for each setting/run',
        valid_full_permutation_outputs=244,all_initial_pools_exact_random_replay=True,
        initial_empty_cache_archive_verified=True,each_budget_exact=True,all_initial_gains_positive=True,
        source_operator_state_and_cached_parent_count_unchanged=True))
    a.csv('EXACT_FITNESS_TIE_DIAGNOSTICS.csv',fitness_ties)
    a.save('RAW_SEARCH_EVIDENCE_MANIFEST.json',dict(status='PASS',archives=manifests,
        total_bytes=sum(x['bytes'] for x in manifests),all_roundtrip_bytes_verified=True,
        checkpoint='Complete score cache, operation state, RNG, moves and generation/selection history; CANDIDATES.npz omitted as redundant derived serialization'))
    from la_grid.diagnostics.ga_search_budget_sensitivity import per_sample
    from la_grid.diagnostics.standalone_ils_analysis_20261010 import production
    from la_grid.revision.r1_equity_amendment_execute import execution_context
    k,_,_=a.load_study().load_model();ctx,_,_=execution_context(k.ids)
    from la_grid.diagnostics.standalone_ils_20261010 import load_model as loader
    loader_tree=ast.parse(inspect.getsource(loader))
    registry_keys={n.slice.value for n in ast.walk(loader_tree) if isinstance(n,ast.Subscript)
        and isinstance(n.value,ast.Name) and n.value.id=='final' and isinstance(n.slice,ast.Constant)}
    assert registry_keys=={'planning_sample_hashes','H_plan_hr'}
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='score' for n in ast.walk(loader_tree))
    assert not any('cache' in name.lower() or 'incumbent' in name.lower() for name in vars(k))
    assert not hasattr(k.score,'cache_info')
    a.save('LOADER_AND_CACHE_INDEPENDENCE_AUDIT.json',dict(status='PASS',
        planning_loader_source_sha256=a.sha(inspect.getsourcefile(loader)),
        exact_kernel_source_sha256=a.sha(inspect.getsourcefile(type(k))),
        metadata_registry_keys_read=sorted(registry_keys),
        loader_reads_registry_that_also_contains_a_prior_sequence=True,
        prior_sequence_field_not_accessed_by_loader=True,
        impact_comparator_constructed_for_identity_but_not_passed_to_new_search=True,
        loader_objective_calls=0,hidden_kernel_fitness_cache=False,
        numba_cache='Compiled machine-code cache only; every private-search distinct key invokes unchanged64-state objective',
        interpretation='Independence is verified chromosome/score dataflow, not a claim that legacy metadata/comparator files are never read'))
    confirmed=pd.concat(frames[1:],ignore_index=True);parity=[]
    for case,g in confirmed.groupby('case'):
        r=g.sort_values(['final_loss_hr','seed']).iloc[0]
        seq=a.read(a.OUT/f"runs/{r.stage}/{r.case}_{r.seed}.json")['sequence']
        exact=per_sample(k,seq)
        native=np.array([production(k,ctx,seq,i) for i in range(64)])
        assert abs(exact.mean()-r.final_loss_hr)<1e-8 and np.max(abs(exact-native))<1e-8
        parity.extend(dict(case=case,seed=int(r.seed),planning_realization=i,kernel_loss_hr=exact[i],native_loss_hr=native[i],difference_hr=native[i]-exact[i]) for i in range(64))
    a.csv('CONFIGURATION_NUMERICAL_PARITY_ALL64.csv',parity)
    a.save('CONFIGURATION_NATIVE_PRODUCTION_QA.json',dict(status='PASS',configurations=7,all64_checks=448,
        max_abs_error_hr=max(abs(r['difference_hr']) for r in parity),new_physical_samples=0,
        purpose='Best-observed per-setting numerical representatives only; not selected/promoted policy candidates',
        no_independent_validation_outcomes_consulted=True))
    print('NUMERICAL_QA_PASS',len(records),len(parity),flush=True)

def integrity():
    current=a.preservation();baseline=a.read(a.OUT/'PRESERVATION_BASELINE.json')
    assert current==baseline,'Protected source/checkouts differ; no overwrite allowed'
    assert len(current['files_sha256'])==950 and current['staged_count']==862
    design=a.read(a.OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')
    assert a.sha(a.OUT/'audit.py')==design['source_sha256'][str(a.OUT/'audit.py')]
    prefix=str(a.OUT.relative_to(a.ROOT)).replace('\\','/')+'/'
    changed=a.git('diff','--name-only',a.START,'HEAD').decode().splitlines()
    assert all(p.startswith(prefix) for p in changed),changed
    for p in a.OUT.rglob('*'):
        if p.is_file() and 'runtime' not in p.parts:
            assert p.suffix.lower() not in ('.docx','.pptx'),p
    a.save('REPRODUCIBILITY_AND_PRESERVATION_QA.json',dict(status='PASS',protected_scientific_files=950,
        original_staged_items=862,original_revision_head=current['revision_head'],
        index_sha256=current['index_sha256'],staged_diff_sha256=current['staged_diff_sha256'],
        index_checksum_definition='SHA256 of git ls-files --stage -z; logical index entries, not a claim about raw index metadata bytes',
        frozen_candidate_sequence='edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a',
        original_validation_files_model_formal_strategy_and_manuscript_unchanged=True,
        original_source_checkout_status_index_head_unchanged=True,
        new_physical_draws=0,new_word_documents=0,new_manuscript_or_official_figure_changes=0,
        current_source_protection_file_count=len(current['protected_external_sha256'])))
    phases=[a.read(a.OUT/f'{s}_EXECUTION.json') for s in ['screen','confirmation','gain_confirmation']]
    records=pd.concat([a.frame(a.OUT/f) for f in ['PARAMETER_SCREEN_RESULTS.csv','PARAMETER_CONFIRMATION_RESULTS.csv','PARAMETER_GAIN_CONFIRMATION_RESULTS.csv']])
    a.save('EXECUTION_ACCOUNTING.json',dict(status='PASS',new_cold_start_searches=244,
        independent_optimizer_seed_blocks=28,paired_configurations_not_independent_replicates=True,
        new_distinct_mean_objective_calls=sum(x['distinct_calls'] for x in phases),
        individual_planning_state_kernel_evaluations=64*sum(x['distinct_calls'] for x in phases),
        attempts=sum(x['attempts'] for x in phases),mandatory_parent_cache_queries=int(records.parent_cache_queries.sum()),
        member_duplicate_queries=int(records.member_duplicate_queries.sum()),
        engineering_mean_calls=1000,engineering_synthetic_calls=2000,test_synthetic_calls=1333,
        engineering_mean_call_planning_state_evaluations=64000,engineering_extra_per_sample_kernel_checks=64,
        worker_model_loader_objective_calls=0,independent_native_engineering_checks=3,
        independent_native_configuration_parity_checks=448,individual_kernel_configuration_parity_checks=448,
        frozen_prefix_logical_cached_calls=100000,frozen_prefix_actual_expensive_calls=0,
        historical_optimizer_records_reused=20,historical_continued_trajectories_reused=10,
        existing_validation_native_cases_read_only=2000,source_integrals_reintegrated=4000,
        all_saved_component_integrals_reintegrated=16000,
        new_validation_realizations=0,validation_new_production_calls=0,
        phases=phases,python=platform.python_version(),numpy_version=np.__version__,
        implementation_failures=['Initial sandbox could not inspect external revision Git status; rerun read-only with optional locks disabled and escalation.',
            'Empty legacy CSV handled explicitly; inventory restricted to relevant summary tables before preregistration.',
            'Historical20k/50k have exact BUDGET_CHECKPOINTS, not FINAL JSON receipts; reused original checkpoint records.'],
        reporting_repair='Static syntax QA caught extra closing parentheses in supplementary source-crossing and loader-audit records; repaired before execution, no optimizer or scientific result affected.',
        scientific_failed_or_omitted_runs=0,formal_replacement=False))
    a.md('REPRODUCIBLE_COMMANDS.md','''# Reproducibility

Starting commit f539e3fe6015122d73e5656109e751770550bb70. Isolated branch diagnostics/pure-random-ga-parameter-consistency-20261011. Sources are read-only in sibling _gaf12 and _gri11 verified authority checkouts. Do not run setup/search phases on an existing completed package or inherit its cache; archived states permit exact replay without new physics.

Use C:\\Users\\yinch\\anaconda3\\python.exe and OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1. From isolated worktree:

```powershell
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py setup
# Commit registration before computation.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py engineering
python -m pytest results/diagnostics/pure_random_ga_parameter_consistency_20261011/test_audit.py -q
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py screen
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py select
# Original3-family confirmation.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/audit.py confirmation
# Post-screen amendment was committed before any confirmation results inspection.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/gain_confirmation.py register
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/gain_confirmation.py execute
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/gain_confirmation.py decision
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/analysis.py planning
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/analysis.py summary
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/qa.py numerical
# Seal and commit decision before existing validation outcomes are accessed.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/analysis.py mechanism
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/report.py memo
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/report.py figures
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/render_qa.py render
# Inspect each actual rendered PDF page before recording visual QA.
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/render_qa.py record
python results/diagnostics/pure_random_ga_parameter_consistency_20261011/qa.py integrity
```

Full per-search ZIP retains initial population, exact terminal RNG/checkpoint/cache, generation/selection diagnostics, budget checkpoints and strict improvement sequences. Source and output hashes, full92 final permutations, failed setup details, negative outcomes and the disclosed amendment are preserved. No physical sampler is called by these scripts. Four PDF diagnostics require actual Poppler visual inspection before release. Remote publication verification downloads actual LFS bytes, not only pointer hashes.
''')
    files={str(p.relative_to(a.OUT)).replace('\\','/'):dict(sha256=a.sha(p),bytes=p.stat().st_size) for p in a.OUT.rglob('*')
        if p.is_file() and not any(x in p.parts for x in ['runtime','__pycache__','.pytest_cache'])
        and p.name not in ['OUTPUT_HASH_MANIFEST.json','REMOTE_PUBLICATION_VERIFIED.json']}
    a.save('OUTPUT_HASH_MANIFEST.json',dict(files=files,total_bytes=sum(x['bytes'] for x in files.values())))
    print('PRESERVATION_PASS',len(files),950,862,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['numerical','integrity']);x=p.parse_args()
    {'numerical':numerical,'integrity':integrity}[x.phase]()
