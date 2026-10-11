"""Predefined paired analysis and publication of the fixed standalone ILS cohort."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
from unittest.mock import patch
import zipfile

import numpy as np
import pandas as pd
import requests

from la_grid.diagnostics import standalone_ils_validation_20261011 as q

v, R, OUT = q.v, q.R, q.OUT
MODULE = 'src/la_grid/diagnostics/standalone_ils_validation_analysis_20261011.py'


def markdown(name, content):
    (OUT / name).write_text(content.strip() + '\n', encoding='utf-8', newline='\n')


def engineering():
    freeze = q.verify()
    model = v.load_model()
    assert not (q.ARCHIVE / 'physical').exists()
    root, original = OUT / 'engineering', q.ARCHIVE
    q.ARCHIVE = root
    calls, tick = 0, time.perf_counter()
    try:
        with patch.object(v.core, 'sample_damage_states', side_effect=AssertionError('No engineering draws')), \
             patch.object(v.core, 'damage_to_functionality_and_repair', side_effect=AssertionError('No engineering draws')):
            for r in (0, 15, 63, 900001):
                ds = model['banks']['planning'][0][15 if r == 900001 else r]
                duration = model['banks']['planning'][1][15 if r == 900001 else r]
                if r == 900001:
                    duration = np.where(ds > 0, 10000., 0.)
                v.write(root / 'physical' / f'{r:04d}' / 'DRAW.json', dict(station_ids=model['ids'],
                        damage_state=ds.tolist(), duration_hr=duration.tolist(),
                        physical_sha256=v.physical_hash(model['ids'], ds, duration)))
                result = q.evaluate_case(model, freeze['strategies'], root / 'cases' / f'{r:04d}', r)
                calls += result['production_calls']
                resumed = q.evaluate_case(model, freeze['strategies'], root / 'cases' / f'{r:04d}', r)
                assert resumed['production_calls'] == 0
            try:
                q.evaluate_case(model, freeze['strategies'], root / 'resumed', 15, interrupt_after=0)
            except InterruptedError:
                calls += 1
            else:
                raise AssertionError('Expected engineering interruption')
            calls += q.evaluate_case(model, freeze['strategies'], root / 'resumed', 15)['production_calls']
            a, b = v.read(root / 'resumed/COMPLETE.json'), v.read(root / 'cases/0015/COMPLETE.json')
            assert a['files_sha256'] == b['files_sha256']
            late = pd.read_csv(root / 'cases/900001/SUMMARY.csv')
            assert late.T80_censored.eq(1).all() and late.T80_restricted_hr.eq(480).all()
            assert late.population_T80_hr.isna().all() and (late.tasks_completed_after_480 > 0).all()
    finally:
        q.ARCHIVE = original
    v.write(OUT / 'ENGINEERING_QA.json', dict(status='PASS', genuine_sampling_calls=0,
              old_planning_case_ids=[0,15,63], synthetic_late_case=True,
              production_calls=calls, independent_kernel_calls=calls,
              complete_resume_no_scoring=True, same_saved_state_crash_resume_identical_bytes=True,
              censored_T80_and_late_events_preserved=True, wall_seconds=time.perf_counter()-tick,
              analysis_source_sha256=v.sha(R / MODULE), execution_freeze_sha256=v.sha(OUT / 'EXECUTION_FREEZE.json'),
              previous_engineering_failures=['Initial registry included all scenarios; fixed to the declared 2pc50 identities before any draw.',
                    'First planning0 ILS production call completed, but independent JIT cache write failed on Windows path length; rerun using short TEMP cache.'],
              extra_failed_attempt_production_calls=1, extra_failed_attempt_completed_kernel_calls=0,
              validation_outcomes_read=False))
    print('ENGINEERING_QA_PASS; no new physical draws; production calls', calls, flush=True)


def paired_analysis(frame):
    names = [q.ILS, q.GA, q.IMPACT]
    n = frame.realization_id.nunique()
    assert n == q.N and len(frame) == 3*n and not frame.duplicated(['realization_id','strategy']).any()
    metrics = list(v.METRICS)
    ids = sorted(frame.realization_id.unique())
    y = np.stack([frame.pivot(index='realization_id', columns='strategy', values=m).loc[ids,names].to_numpy(float)
                  for m in metrics], axis=2)
    assert np.isfinite(y).all()
    rng = np.random.default_rng(q.BOOT_SEED)
    boot = np.empty((q.BOOT, 3, len(metrics)))
    for start in range(0, q.BOOT, 100):
        count = min(100, q.BOOT-start)
        indices = rng.integers(0, n, size=(count,n))
        weights = np.stack([np.bincount(row, minlength=n)/n for row in indices])
        boot[start:start+count] = (weights @ y.reshape(n,-1)).reshape(count,3,-1)
    effects, levels = [], []
    for j, name in enumerate(names):
        for k, metric in enumerate(metrics):
            x = y[:,j,k]
            lo, hi = np.quantile(boot[:,j,k], [.025,.975])
            levels.append(dict(strategy=name, metric=metric, n=n, mean=x.mean(), sd=x.std(ddof=1),
                mcse=x.std(ddof=1)/np.sqrt(n), median=np.median(x), p05=np.quantile(x,.05),
                p95=np.quantile(x,.95), p99=np.quantile(x,.99), worst5pct_mean=np.sort(x)[-math.ceil(.05*n):].mean(),
                ci95_low=lo, ci95_high=hi, inference='descriptive pointwise'))
    for reference in (q.IMPACT, q.GA):
        j, ref = names.index(q.ILS), names.index(reference)
        for k, metric in enumerate(metrics):
            x, b = y[:,j,k]-y[:,ref,k], boot[:,j,k]-boot[:,ref,k]
            lo, hi = np.quantile(b,[.025,.975])
            slo, shi = np.quantile(b,[.0125,.9875])
            effects.append(dict(candidate=q.ILS, reference=reference, metric=metric, n=n,
                mean_difference=x.mean(), sd_difference=x.std(ddof=1), mcse=x.std(ddof=1)/np.sqrt(n),
                ci95_low=lo, ci95_high=hi, simultaneous95_low=slo if metric==v.PRIMARY else None,
                simultaneous95_high=shi if metric==v.PRIMARY else None,
                median_difference=np.median(x), p05=np.quantile(x,.05), p95=np.quantile(x,.95),
                p99=np.quantile(x,.99), worst5pct_mean=np.sort(x)[-math.ceil(.05*n):].mean(),
                min_difference=x.min(), max_difference=x.max(),
                improved_count=int((x < -1e-9).sum()), worsened_count=int((x > 1e-9).sum()), ties_count=int((abs(x)<=1e-9).sum()),
                inference='prespecified primary' if reference==q.IMPACT and metric==v.PRIMARY else
                          'prespecified secondary two-contrast family' if metric==v.PRIMARY else 'descriptive pointwise',
                simultaneous_family='two population-loss contrasts only' if metric==v.PRIMARY else 'not adjusted'))
    primary_index = metrics.index(v.PRIMARY)
    differences = pd.DataFrame(dict(realization_id=ids))
    for reference in (q.IMPACT, q.GA):
        for k, metric in enumerate(metrics):
            differences[metric+'_ILS_minus_'+reference] = y[:,0,k]-y[:,names.index(reference),k]
    return pd.DataFrame(effects), pd.DataFrame(levels), differences


def analyze():
    freeze = q.verify()
    assert v.sha(R / MODULE) == v.read(OUT / 'ENGINEERING_QA.json')['analysis_source_sha256']
    assert v.read(OUT / 'COHORT_COMPLETED.json')['sample_count'] == q.N
    model, frames, records, tick = v.load_model(), [], [], time.perf_counter()
    prior = set(v.read(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json').values())
    physical_hashes, curves = set(), {p['strategy']: np.zeros((481,3)) for p in freeze['strategies']}
    pop = model['mapping'].population
    mass = model['mapping'].weight.T @ pop
    qmass = np.array([model['mapping'].weight.T @ (pop*(model['mapping'].quartile==c)) for c in ('Q1','Q4')])
    max_error, max_conservation, late_tasks = 0., 0., 0
    for r in range(q.N):
        folder = q.ARCHIVE / 'cases' / f'{r:04d}'
        done = v.read(folder / 'COMPLETE.json')
        for name, h in done['files_sha256'].items():
            assert v.sha(folder / name) == h
        physical = v.read(q.ARCHIVE / 'physical' / f'{r:04d}' / 'DRAW.json')
        assert physical['entropy'] == [q.SAMPLE_SEED,r] and physical['namespace'] == freeze['sampling_namespace']
        ds, duration = np.array(physical['damage_state'],np.int64),np.array(physical['duration_hr'],float)
        h = v.physical_hash(model['ids'],ds,duration)
        assert h == physical['physical_sha256'] and h not in prior and h not in physical_hashes
        physical_hashes.add(h)
        frame = pd.read_csv(folder / 'SUMMARY.csv',float_precision='round_trip')
        assert len(frame)==3 and set(frame.strategy)==set(curves) and frame.physical_sha256.eq(h).all()
        assert done['identity']['freeze_sha256']==v.sha(OUT / 'EXECUTION_FREEZE.json')
        frames.append(frame)
        max_error = max(max_error,float(frame.independent_kernel_abs_error_hr.max()))
        late_tasks += int(frame.tasks_completed_after_480.sum())
        with np.load(folder / 'TRAJECTORIES.npz',allow_pickle=False) as z:
            start=0
            assert z['station_ids'].astype(str).tolist()==model['ids']
            for strategy,length in zip(z['policies'],z['event_lengths']):
                clock, e = z['event_time_hr'][start:start+length],z['e'][start:start+length]
                assert clock[0]==0 and clock[-1]==480 and np.all(np.diff(clock)>0)
                expected = float(np.diff(clock) @ (1-e[:-1] @ mass/mass.sum()))
                observed = float(frame.loc[frame.strategy.eq(str(strategy)),v.PRIMARY].iloc[0])
                assert abs(expected-observed)<1e-8
                ix = np.searchsorted(clock,np.arange(481.),side='right')-1
                curves[str(strategy)][:,0] += e[ix] @ mass/mass.sum()
                curves[str(strategy)][:,1:] += e[ix] @ qmass.T/qmass.sum(axis=1)
                total = z['L_self'][start:start+length]+z['L_threshold'][start:start+length]+z['L_source'][start:start+length]
                error = np.max(abs(total-z['L_total'][start:start+length]))
                max_conservation = max(max_conservation,float(error))
                assert error < 1e-10
                start += length
        records.append(dict(r=r, physical_sha256=h, damage_sha256=physical['damage_sha256'],
                duration_sha256=physical['duration_sha256'], ds0=int((ds==0).sum()),
                ds1=int((ds==1).sum()), ds2=int((ds==2).sum()),ds3=int((ds==3).sum()),ds4=int((ds==4).sum()),
                duration_mean_hr=duration.mean(),duration_max_hr=duration.max()))
    frame = pd.concat(frames,ignore_index=True)
    effects, levels, differences = paired_analysis(frame)
    v.csv(OUT / 'REALIZATION_OUTCOMES.csv',frame)
    v.csv(OUT / 'PAIRED_EFFECTS.csv',effects)
    v.csv(OUT / 'POLICY_OUTCOMES.csv',levels)
    v.csv(OUT / 'PAIRED_REALIZATION_DIFFERENCES.csv',differences)
    v.csv(OUT / 'PHYSICAL_COHORT_IDENTITY.csv',pd.DataFrame(records))
    t80 = frame.groupby('strategy').agg(n=('realization_id','size'), reached_count=('population_T80_hr','count'),
            censored_count=('T80_censored','sum'),restricted_mean_hr=('T80_restricted_hr','mean'),
            reached_only_conditional_mean_hr=('population_T80_hr','mean')).reset_index()
    v.csv(OUT / 'T80_CENSORING.csv',t80)
    curve_frames=[]
    for name,a in curves.items():
        a /= q.N
        curve_frames.append(pd.DataFrame(dict(strategy=name,time_hr=np.arange(481.),population_availability=a[:,0],
                Q1_availability=a[:,1],Q4_availability=a[:,2],Q4_minus_Q1_availability=a[:,2]-a[:,1])))
    v.csv(OUT / 'RECOVERY_CURVES.csv',pd.concat(curve_frames,ignore_index=True))
    primary = effects[(effects.reference==q.IMPACT)&(effects.metric==v.PRIMARY)].iloc[0]
    secondary = effects[(effects.reference==q.GA)&(effects.metric==v.PRIMARY)].iloc[0]
    v.write(OUT / 'VALIDATION_CONCLUSION.json',v.clean(dict(status='FIXED2000_VALIDATION_COMPLETE',
        candidate_sha256=freeze['strategies'][0]['sequence_sha256'], sample_count=q.N,
        modeled_benefit_vs_Impact=bool(primary.ci95_high<0),
        comparison_vs_GA='lower mean loss supported' if secondary.simultaneous95_high<0 else
                         'higher mean loss supported' if secondary.simultaneous95_low>0 else 'mean ranking unresolved',
        primary=primary.to_dict(),secondary=secondary.to_dict(),formal_strategy_promoted=False,
        independent_of_prior_physical_cohort=True, model_empirical_accuracy_tested=False)))
    v.write(OUT / 'NUMERICAL_AND_COHORT_QA.json',dict(status='PASS',sample_count=2000,
        policy_records=6000,distinct_physical_hashes=len(physical_hashes),prior_overlap_count=0,
        independent_kernel_max_abs_error_hr=max_error,component_conservation_max_abs_error=max_conservation,
        exact_trajectory_reintegration_checks=6000,late_task_events=late_tasks,
        primary_missing=0,complete_case_deletions=0,bootstrap_resamples=q.BOOT,
        bootstrap_seed=q.BOOT_SEED,analysis_wall_seconds=time.perf_counter()-tick,
        new_physical_draws_in_analysis=0,new_production_evaluations_in_analysis=0,
        no_policy_reselection=True,no_tuning=True))
    print('ANALYSIS_COMPLETE',json.dumps(v.clean(dict(primary=primary.to_dict(),secondary=secondary.to_dict()))),flush=True)


def package():
    freeze = q.verify()
    assert v.read(OUT / 'NUMERICAL_AND_COHORT_QA.json')['status']=='PASS'
    current = q.protected_state(freeze['protected_revision_checkout'],freeze['old_validation_checkout'],freeze['source_checkout'])
    assert current == v.read(OUT / 'PRESERVATION_BASELINE.json')
    v.write(OUT / 'PRESERVATION_VERIFIED.json',dict(status='PASS',protected_revision_file_count=len(current['files_sha256']),
        old_validation_file_count=len(current['old_validation_sha256']),
        frozen_source_file_count=len(current['frozen_source_package_sha256']),
        revision_head=current['revision_head'],revision_branch=current['revision_branch'],
        staged_diff_sha256=current['staged_diff_sha256'],baseline_sha256=v.sha(OUT / 'PRESERVATION_BASELINE.json')))
    records, target = [], OUT / 'FIXED2000_FULL_EVIDENCE.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p in sorted(q.ARCHIVE.rglob('*')):
            if p.is_file():
                name=str(p.relative_to(q.ARCHIVE)).replace('\\','/')
                records.append(dict(path=name,bytes=p.stat().st_size,sha256=v.sha(p)))
                z.write(p,name)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None and len(z.namelist())==len(records)
        for record in records:
            assert hashlib.sha256(z.read(record['path'])).hexdigest()==record['sha256']
    v.write(OUT / 'FULL_EVIDENCE_MANIFEST.json',dict(archive_sha256=v.sha(target),archive_bytes=target.stat().st_size,
            member_count=len(records),members=records,round_trip_all_members_verified=True))
    print('FULL_EVIDENCE_VERIFIED',len(records),target.stat().st_size,flush=True)


def transport_env():
    credential=subprocess.run(['git','credential','fill'],cwd=Path.cwd().parent,
            input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True)
    fields=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    encoded=base64.b64encode((fields['username']+':'+fields['password']).encode()).decode()
    env=os.environ.copy();env.update(GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
            GIT_CONFIG_VALUE_0='Authorization: Basic '+encoded,GIT_CONFIG_KEY_1='credential.helper',
            GIT_CONFIG_VALUE_1='',GIT_TERMINAL_PROMPT='0')
    return env,fields


def publish(receipt_only=False):
    q.verify()
    prefix='results/diagnostics/standalone_ils_prospective_validation_20261011/'
    allowed=(prefix,'src/la_grid/diagnostics/standalone_ils_validation_', 'tests/test_standalone_ils_validation_')
    changed=v.git(q.REPO_ROOT,'diff','--name-only',q.PARENT,'HEAD').decode().splitlines()
    assert changed and all(name.startswith(allowed) for name in changed)
    status=v.git(q.REPO_ROOT,'status','--porcelain').decode().splitlines()
    assert not [s for s in status if s[3:].strip('"').startswith(allowed)],status
    assert v.read(OUT / 'PRESERVATION_VERIFIED.json')['status']=='PASS'
    env,fields=transport_env()
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+q.BRANCH],cwd=q.REPO_ROOT,env=env,check=True)
    head=v.git(q.REPO_ROOT,'rev-parse','HEAD').decode().strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+q.BRANCH],cwd=q.REPO_ROOT,env=env,text=True).split()[0]
    assert remote==head
    if receipt_only:
        print('FINAL_REMOTE_HEAD_VERIFIED',head,flush=True);return
    objects={}
    names=v.git(q.REPO_ROOT,'ls-tree','-r','--name-only','HEAD',prefix).decode().splitlines()
    for name in names:
        blob=v.git(q.REPO_ROOT,'show','HEAD:'+name)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            row=dict(s.split(' ',1) for s in blob.decode().splitlines())
            oid,size=row['oid'][7:],int(row['size'])
            assert v.sha(R / name)==oid
            objects[oid]=dict(bytes=size,paths=objects.get(oid,{}).get('paths',[])+[name])
    endpoint='https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git/info/lfs/objects/batch'
    response=requests.post(endpoint,auth=(fields['username'],fields['password']),timeout=90,
        headers={'Accept':'application/vnd.git-lfs+json','Content-Type':'application/vnd.git-lfs+json'},
        json=dict(operation='download',transfers=['basic'],ref=dict(name='refs/heads/'+q.BRANCH),
                  objects=[dict(oid=o,size=r['bytes']) for o,r in objects.items()]))
    response.raise_for_status();received=response.json()['objects']
    assert {o['oid'] for o in received}==set(objects)
    for obj in received:
        assert 'error' not in obj
        action,h,size=obj['actions']['download'],hashlib.sha256(),0
        with requests.get(action['href'],headers=action.get('header',{}),stream=True,timeout=180) as download:
            download.raise_for_status()
            for block in download.iter_content(2**20):
                h.update(block);size+=len(block)
        assert h.hexdigest()==obj['oid'] and size==objects[obj['oid']]['bytes']
        objects[obj['oid']]['downloaded_sha256']=h.hexdigest()
        print('REMOTE_LFS_DOWNLOADED_VERIFIED',obj['oid'],size,flush=True)
    freeze=q.verify()
    assert q.protected_state(freeze['protected_revision_checkout'],freeze['old_validation_checkout'],freeze['source_checkout'])==v.read(OUT / 'PRESERVATION_BASELINE.json')
    v.write(OUT / 'REMOTE_PUBLICATION_VERIFIED.json',dict(status='PASS',data_commit=head,branch=q.BRANCH,
             remote_head_verified=True,remote_lfs_payloads=objects,downloaded_bytes=sum(x['bytes'] for x in objects.values()),
             protected_files_and_staging_preserved=True))
    print('REMOTE_HEAD_VERIFIED',head,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['engineering','analyze','package','publish','receipt-push'])
    a=p.parse_args()
    if a.phase=='engineering':engineering()
    elif a.phase=='analyze':analyze()
    elif a.phase=='package':package()
    else:publish(a.phase=='receipt-push')
