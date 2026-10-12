"""Read frozen evidence and write diagnostics here, never model outputs.

Example: python audit.py --source-root PATH --cache-root PATH [--cache-root PATH]
All main sources must match the fixed Git commit or its recorded LFS payload.
The heating package is separately pinned to its diagnostic commit.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from scipy import sparse, stats
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.preprocessing import SplineTransformer, StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SPEC = json.loads((OUT / 'AUDIT_SPECIFICATION.json').read_text())
BE = 'docs/data_research/built_environment_20261009/'
FORMAL = 'Formal_Experiment_20260923/'
GRID = ['Grid_Impact', 'Grid_Degree', 'Grid_Betweenness', 'Redundancy_HHI']
PRIMARY = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_480_hr',
           'Delta_B_logistics', 'SOVI_SCORE', 'log1p_Population']
DIAGNOSTIC = ['T80', 'B_unconstrained', 'Grid_Degree', 'Grid_Betweenness',
              'Population', 'log1p_Pop_Density', 'CDC2022_RPL_THEMES',
              'CDC2022_local_theme_mean', 'electric_heating_share',
              'housing_5plus_share', 'hospital_tract']


def longpath(path):
    p = str(Path(path).resolve())
    return Path('\\\\?\\' + p) if sys.platform == 'win32' and not p.startswith('\\\\?\\') else Path(p)


def sha(path):
    h = hashlib.sha256()
    with longpath(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def dump(name, value):
    longpath(OUT / name).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n', encoding='utf-8')


def save(name, frame, index=False):
    pd.DataFrame(frame).to_csv(longpath(OUT / name), index=index, float_format='%.17g', lineterminator='\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def idhash(ids):
    return hashlib.sha256(('\n'.join(map(str, ids)) + '\n').encode()).hexdigest()


def read_index(path, key='tract_id', columns=None):
    frame = pd.read_csv(longpath(path), dtype={key: str}, usecols=columns)
    ids = frame[key].str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(11)
    if not ids.str.fullmatch(r'\d{11}').all() or not ids.is_unique:
        raise ValueError(f'Invalid/duplicate GEOIDs: {path}')
    frame[key] = ids
    return frame.set_index(key)


class Sources:
    def __init__(self, source_root, caches):
        self.original = Path(source_root)
        self.roots = [self.original, ROOT, *map(Path, caches)]
        self.records = []
        self.resolved = {}

    def source(self, rel, commit=None):
        commit = commit or SPEC['baseline_commit']
        key = (commit, rel)
        if key in self.resolved:
            return self.resolved[key]
        blob = git('show', f'{commit}:{rel}')
        is_lfs = blob.startswith(b'version https://git-lfs.github.com/spec/v1')
        if is_lfs:
            expected = blob.decode().split('oid sha256:')[1].splitlines()[0]
        else:
            expected = hashlib.sha256(blob).hexdigest()
        common = Path(git('rev-parse', '--git-common-dir').decode().strip())
        objects = common / 'lfs/objects' / expected[:2] / expected[2:4] / expected
        for p in [*(r / rel for r in self.roots), objects]:
            q = longpath(p)
            actual = sha(q) if q.is_file() else None
            eol_equivalent = (actual is not None and not is_lfs and
                              q.suffix.lower() in {'.py','.json','.md','.txt','.yaml'} and
                              q.read_bytes().replace(b'\r\n',b'\n') == blob)
            if actual == expected or eol_equivalent:
                self.records.append(dict(source_file=rel, commit=git('rev-parse', commit).decode().strip(),
                                         sha256=actual, committed_sha256=expected, bytes=q.stat().st_size,
                                         verification='GIT_TEXT_EQUIVALENT_CRLF_ONLY' if actual != expected else
                                         'ACTUAL_BYTES_MATCH_COMMITTED_SOURCE'))
                self.resolved[key] = q
                return q
        raise FileNotFoundError(f'No actual verified source bytes: {commit}:{rel}')

    def frame(self, rel, key='tract_id', columns=None, commit=None):
        return read_index(self.source(rel, commit), key, columns)

    def archive(self, rel, expected=None):
        p = longpath(self.original / rel)
        actual = sha(p)
        if expected is not None:
            assert actual == expected
        self.records.append(dict(source_file=rel, commit='', sha256=actual,
                                 bytes=p.stat().st_size,
                                 verification='FROZEN_LOCAL_ARCHIVE_MANIFEST_MATCH' if expected else
                                 'LOCAL_ARCHIVE_METADATA_RECORDED_NOT_GIT_TRACKED'))
        return p

    def snapshot(self):
        # Observe the same protected universe as the preceding independent audit.
        old = json.loads(self.source(BE + 'shortlist_resolution_review_20261011/PRESERVATION_BEFORE.json').read_text())
        records = {rel: sha(self.original / rel) for rel in old['protected_files']}
        return dict(protected_count=len(records), protected_files=records,
                    source_worktree_git_head=longpath(self.original / '.git').read_text().strip())


def equal_quartiles(s):
    valid = s.dropna().sort_index()
    order = pd.DataFrame({'score': valid.to_numpy(), 'tract_id': valid.index.to_numpy()}).sort_values(['score', 'tract_id'], kind='stable')
    out = pd.Series(index=s.index, dtype=object)
    out.loc[order.tract_id] = [f'Q{x}' for x in np.arange(len(order)) * 4 // len(order) + 1]
    return out


def svi_comparison(frame, frozen, previous):
    measures = ['SOVI_SCORE', 'CDC2022_RPL_THEMES', 'CDC2022_local_theme_mean']
    groups = {c: equal_quartiles(frame[c]) for c in measures}
    groups['frozen_Q'] = frozen
    rows = []
    for a, b in [*itertools.combinations(measures, 2), *[('frozen_Q', c) for c in measures]]:
        ok = groups[a].notna() & groups[b].notna()
        q_a = ok & groups[a].eq('Q4')
        q_b = ok & groups[b].eq('Q4')
        common = q_a & q_b
        union = q_a | q_b
        rankdiff = (frame.loc[ok, a].rank(pct=True) - frame.loc[ok, b].rank(pct=True)).abs() if a != 'frozen_Q' else pd.Series(dtype=float)
        row = dict(measure_a=a, measure_b=b, n=int(ok.sum()),
                   pearson=frame.loc[ok, a].corr(frame.loc[ok, b]) if a != 'frozen_Q' else np.nan,
                   spearman=frame.loc[ok, a].corr(frame.loc[ok, b], method='spearman') if a != 'frozen_Q' else np.nan,
                   median_rank_displacement=rankdiff.median(), p95_rank_displacement=rankdiff.quantile(.95),
                   q4_a_count=int(q_a.sum()), q4_b_count=int(q_b.sum()), q4_overlap=int(common.sum()),
                   q4_jaccard=common.sum() / union.sum(),
                   population_weighted_overlap=frame.loc[common, 'Population'].sum() / frame.loc[union, 'Population'].sum(),
                   entering_Q4=int((q_b & ~q_a).sum()), leaving_Q4=int((q_a & ~q_b).sum()))
        old_a = {'SOVI_SCORE': 'NRI_SOVI_SCORE', 'CDC2022_RPL_THEMES': 'CDC_RPL_THEMES',
                 'CDC2022_local_theme_mean': 'STAGE7_THEME_MEAN', 'frozen_Q': 'FROZEN_SOVI_Q'}[a]
        old_b = {'SOVI_SCORE': 'NRI_SOVI_SCORE', 'CDC2022_RPL_THEMES': 'CDC_RPL_THEMES',
                 'CDC2022_local_theme_mean': 'STAGE7_THEME_MEAN'}[b]
        prior = previous[(previous.measure_a == old_a) & (previous.measure_b == old_b)]
        assert len(prior) == 1
        for new, old in [('n', 'common_valid_tracts'), ('q4_overlap', 'q4_overlap_count'),
                         ('q4_jaccard', 'q4_jaccard'), ('entering_Q4', 'into_b_q4_tracts'),
                         ('leaving_Q4', 'out_of_a_q4_tracts')]:
            assert np.isclose(row[new], prior.iloc[0][old], atol=1e-12)
        row['previous_source_reproduced'] = True
        rows.append(row)
    save('SVI_COMPOSITE_SOURCE_COMPARISON.csv', rows)


def verify_recovery(sources, frame, tract_order, mapping, stations):
    prefix = FORMAL + 'Formal_Offline_Evaluation/2pc50__C57_D1__'
    data, identity = {}, {}
    for policy in ['direct-community', 'impact-first', 'unconstrained']:
        meta = json.loads(sources.archive(prefix + policy + '__EVALUATION.json').read_text())
        path = sources.archive(prefix + policy + '__INTEGRALS.npz',meta['integral_sha256'])
        assert sha(path) == meta['integral_sha256']
        identity[policy] = meta['identity']
        with np.load(path, allow_pickle=False) as z:
            assert np.array_equal(z['station_ids'].astype(str), stations)
            data[policy] = {k: z[k].copy() for k in ['physical_hashes', 'M1_UTILITY_003__normalized_burden_hr', 'G1_BASELINE_050__L_total']}
        assert meta['realization_count'] == 1000
        assert identity[policy]['H_eval_hr'] == 480 and identity[policy]['hazard'] == '2pc50'
    names = ['direct-community', 'impact-first', 'unconstrained']
    for k in ['physical_hashes_sha256', 'matrix_sha256', 'mapping_cases', 'gate_cases', 'resource_case']:
        assert all(identity[n][k] == identity[names[0]][k] for n in names)
    physical = pd.read_csv(sources.source(FORMAL + 'Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv'))
    selected = physical[(physical.scenario == '2pc50') & (physical.split == 'evaluation')].sort_values('realization_id')
    assert len(selected) == 1000
    w = sparse.csr_matrix((mapping.weight, ([tract_order.index(t) for t in mapping.tract_id],
                                          [list(stations).index(s) for s in mapping.substation_id])), shape=(2315, 92))
    mass = np.asarray(w.sum(axis=1)).ravel()
    assert np.allclose(mass, 1)
    errors = {}
    for policy in names:
        assert np.array_equal(data[policy]['physical_hashes'], selected.physical_input_hash.to_numpy())
        b = data[policy]['M1_UTILITY_003__normalized_burden_hr']
        assert b.shape == (1000, 2315) and np.isfinite(b).all() and b.min() >= 0 and b.max() <= 480
        errors[policy] = float(np.max(np.abs(b - (w @ data[policy]['G1_BASELINE_050__L_total'].T).T / mass)))
        assert errors[policy] < 1e-10
    direct = data['direct-community']['M1_UTILITY_003__normalized_burden_hr']
    impact = data['impact-first']['M1_UTILITY_003__normalized_burden_hr']
    uncon = data['unconstrained']['M1_UTILITY_003__normalized_burden_hr']
    assert np.array_equal(direct, impact)
    for col, values in [('B_480_hr', impact.mean(axis=0)), ('B_unconstrained', uncon.mean(axis=0)),
                        ('Delta_B_logistics', (impact - uncon).mean(axis=0))]:
        frame[col] = pd.Series(values, index=tract_order).reindex(frame.index)
    assert np.allclose(frame.B_480_hr, frame.B_unconstrained + frame.Delta_B_logistics, atol=1e-12)
    previous = sources.frame(BE + 'local_joint_feature_extraction_20261009/RECOVERY_B_T80_INIT_COMPARISON.csv')
    assert np.allclose(frame.B_480_hr, previous.B_480_hr.reindex(frame.index), atol=1e-10)
    chain = hashlib.sha256()
    initial = np.zeros(92)
    events, changes, rows, terminal = [], [], [], []
    # Read existing event records only. This is an exact metric reconstruction,
    # not resimulation or a new source-gate application.
    for i, physical_row in enumerate(selected.itertuples()):
        stem = physical_row.realization_id
        folder = sources.original / FORMAL / 'Formal_Trajectories/2pc50/C57_D1/direct-community'
        manifest_path = longpath(folder / (stem + '.json'))
        manifest_bytes = manifest_path.read_bytes()
        meta = json.loads(manifest_bytes)
        chain.update(hashlib.sha256(manifest_bytes).digest())
        ident = meta['identity']
        assert ident['physical_sample_hash'] == physical_row.physical_input_hash
        assert ident['realization_id'] == stem and ident['event_horizon_hr'] == 480
        assert ident['DS_hash'] == physical_row.DS_hash and ident['duration_hash'] == physical_row.duration_hash
        assert ident['mapping_method_id'] == SPEC['mapping']
        p = longpath(folder / (stem + '.npz'))
        actual_hash = sha(p)
        assert actual_hash == meta['npz_sha256']
        with np.load(p, allow_pickle=False) as z:
            t, e = z['event_time_hr'].copy(), z['e'].copy()
            assert np.array_equal(stations, z['station_ids'].astype(str))
        assert t[0] == 0 and t[-1] == 480 and (np.diff(t) > 0).all()
        assert np.isfinite(e).all() and e.min() >= 0 and e.max() <= 1 + 1e-12
        d = np.diff(e, axis=0)
        assert d.min() >= -1e-12
        initial += e[0]
        changed = (d != 0).any(axis=1)
        events.append(t[1:][changed])
        changes.append(d[changed])
        terminal.append(e[-1])
        error = np.abs(np.sum((1 - e[:-1]) * np.diff(t)[:, None], axis=0) - data['direct-community']['G1_BASELINE_050__L_total'][i]).max()
        assert error < 1e-10
        rows.append(dict(realization_id=stem, physical_hash=physical_row.physical_input_hash,
                         manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(), npz_sha256=actual_hash,
                         integration_error_hr=error, relative_file=f'{FORMAL}Formal_Trajectories/2pc50/C57_D1/direct-community/{stem}.npz'))
        if i % 250 == 0:
            print('verified frozen event records', i, flush=True)
    saved_identity = json.loads(sources.source(FORMAL + 'FORMAL_STAGE7_INPUT_IDENTITY.json').read_text())
    assert chain.hexdigest() == saved_identity['source_manifest_chain_sha256']
    init = w @ (initial / 1000)
    mean = init.copy()
    crossing = np.where(init >= .8, 0., np.nan)
    time, delta = np.concatenate(events), np.concatenate(changes)
    order = np.argsort(time, kind='stable')
    time, delta = time[order], delta[order]
    csc = w.tocsc()
    start = 0
    while start < len(time):
        stop = int(np.searchsorted(time, time[start], side='right'))
        increment = delta[start:stop].sum(axis=0) / 1000
        for station in np.flatnonzero(increment):
            lo, hi = csc.indptr[station:station+2]
            mean[csc.indices[lo:hi]] += csc.data[lo:hi] * increment[station]
        hit = np.isnan(crossing) & (mean >= .8)
        crossing[hit] = time[start]
        start = stop
    expected = frame.reindex(tract_order)
    assert np.allclose(init, expected.Init_Supply, atol=1e-12)
    assert np.allclose(crossing, expected.T80, atol=1e-8, equal_nan=True)
    terminals = (w @ np.array(terminal).T).T / mass
    frame['T80_unreached'] = pd.Series(np.isnan(crossing), index=tract_order)
    frame['realization_terminal_below80_fraction'] = pd.Series((terminals < .8).mean(axis=0), index=tract_order)
    save('FROZEN_REALIZATION_VERIFICATION.csv', rows)
    save('T80_CENSORING_AND_ENDPOINTS.csv', frame[['T80', 'T80_unreached', 'realization_terminal_below80_fraction']].reset_index())
    dump('RECOVERY_PAIRING_QA.json', dict(identities=identity, normalized_integral_max_errors_hr=errors,
         direct_impact_integrals_bitwise_equal=True,
         direct_impact_integral_files_identical=sha(sources.archive(prefix+'direct-community__INTEGRALS.npz')) == sha(sources.archive(prefix+'impact-first__INTEGRALS.npz')),
         T80_mean_trajectory_unreached=int(np.isnan(crossing).sum()),
         realization_tract_terminal_unreached=int((terminals < .8).sum()),
         all_mean_curves_reach_before480=bool((crossing < 480).all()),
         delta_min_all_paired_realizations_hr=float((impact-uncon).min()),
         initial_max_error=float(np.abs(init - expected.Init_Supply.to_numpy()).max()),
         T80_max_error=float(np.nanmax(np.abs(crossing - expected.T80.to_numpy()))),
         manifest_chain_sha256=chain.hexdigest()))


def information_audit(frame, cohort, label):
    f = frame.loc[cohort].astype(float)
    assert np.isfinite(f).all().all()
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    pearson, spearman = f.corr(), f.corr(method='spearman')
    save(f'{label}_PEARSON.csv', pearson, True)
    save(f'{label}_SPEARMAN.csv', spearman, True)
    rows = []
    for a, b in itertools.combinations(f.columns, 2):
        if f[a].std() == 0 or f[b].std() == 0:
            continue
        def spline_r2(x, y):
            estimator = make_pipeline(SplineTransformer(n_knots=5, degree=3, include_bias=False), LinearRegression())
            return r2_score(y, cross_val_predict(estimator, x, y, cv=cv))
        rows.append(dict(cohort=label, n=len(f), GEOID_order_sha256=idhash(f.index),
                         variable_a=a, variable_b=b, pearson_r=pearson.loc[a,b], spearman_rho=spearman.loc[a,b],
                         mutual_information_a_to_b_nats=mutual_info_regression(f[[a]],f[b],n_neighbors=5,random_state=42)[0],
                         mutual_information_b_to_a_nats=mutual_info_regression(f[[b]],f[a],n_neighbors=5,random_state=42)[0],
                         spline_cv_R2_b_given_a=spline_r2(f[[a]], f[b]),
                         spline_cv_R2_a_given_b=spline_r2(f[[b]], f[a])))
    return pd.DataFrame(rows)


def conditional(frame, columns, block, cohort):
    f = frame.loc[cohort, columns].astype(float)
    assert np.isfinite(f).all().all()
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    rows=[]
    for target in columns:
        x = f.drop(columns=target)
        y = f[target]
        model = make_pipeline(StandardScaler(), LinearRegression())
        fitted = model.fit(x,y).predict(x)
        r2 = r2_score(y, fitted)
        estimator = make_pipeline(SplineTransformer(n_knots=5,degree=3,include_bias=False),LinearRegression())
        rows.append(dict(block=block, target=target, controls=';'.join(x.columns), n=len(f),
                         GEOID_order_sha256=idhash(f.index), conditional_linear_R2=r2,
                         conditional_linear_unexplained_fraction=max(0,1-r2),
                         VIF=np.inf if 1-r2<1e-12 else 1/(1-r2),
                         full_linear_design_rank=np.linalg.matrix_rank(np.c_[np.ones(len(f)),f]),
                         coordinate_count=len(columns),
                         linear_cv_R2=r2_score(y,cross_val_predict(model,x,y,cv=cv)),
                         additive_spline_cv_R2=r2_score(y,cross_val_predict(estimator,x,y,cv=cv))))
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--cache-root', type=Path, action='append', default=[])
    parser.add_argument('--comments', type=Path)
    args=parser.parse_args()
    sources=Sources(args.source_root,args.cache_root)
    dump('PRESERVATION_BEFORE.json', sources.snapshot())
    cols=['B_480_hr','T80','Init_Supply','SOVI_SCORE','formal_population','Pop_Density',*GRID,'housing_total','housing_5plus_share','acs_residential_pre1970_share']
    master=sources.frame(BE+'candidate_admission_rebuild_20261010/CANDIDATE_VALUES_2315.csv',columns=['tract_id',*cols])
    status=sources.frame(FORMAL+'Stage 7 Output_SOVI_Harmonized/stage7_full_domain_tract_status.csv',columns=['tract_id','T80','Init_Supply','formal_population','Housing_Units_Total','typology_status'])
    meta=sources.frame('provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv')
    tracts=sources.frame('Data/Tracts_Within_Expanded_Area.csv',key='GEOID',columns=['GEOID','population'])
    assert set(master.index)==set(status.index)==set(meta.index)==set(tracts.index) and len(master)==2315
    f=master.sort_index().copy()
    f['Population']=tracts.population.reindex(f.index)
    assert np.array_equal(f.Population,meta.population.reindex(f.index))
    assert np.array_equal(f.Population,f.formal_population)
    f['log1p_Population']=np.log1p(f.Population)
    f['log1p_Pop_Density']=np.log1p(f.Pop_Density)
    f['hospital_tract']=meta.hospital_tract.reindex(f.index).astype(float)
    residential=f.index[(f.Population>0)&(f.housing_total>0)]
    assert len(residential)==2291
    old=json.loads(sources.source(BE+'shortlist_resolution_review_20261011/CONTROLLED_SHORTLIST_SPECIFICATION.json').read_text())
    core=pd.Index(old['primary_GEOID_order']).intersection(residential)
    assert len(core)==2287
    mapping=pd.read_csv(sources.source('Data/JULY_UTILITY_CONSTRAINED_92.csv'),dtype={'tract_id':str,'substation_id':str})
    mapping.tract_id=mapping.tract_id.str.zfill(11)
    central=pd.read_csv(sources.source(FORMAL+'Stage 2 Output_expanded/impact_centrality_substations.csv'),dtype={'substation_id':str})
    m=mapping.merge(central,on='substation_id',validate='many_to_one')
    m['p']=m.weight/m.groupby('tract_id').weight.transform('sum')
    checks={}
    for src,dst in [('degree','Grid_Degree'),('impact_centrality','Grid_Impact'),('betweenness_centrality','Grid_Betweenness')]:
        reconstructed=(m.p*m[src]).groupby(m.tract_id).sum().reindex(f.index)
        checks[dst]=float((reconstructed-f[dst]).abs().max())
        assert np.allclose(reconstructed,f[dst],atol=1e-10)
    hhi=(m.p**2).groupby(m.tract_id).sum().reindex(f.index)
    assert np.allclose(hhi,f.Redundancy_HHI,atol=1e-12)
    checks['Redundancy_HHI']=float((hhi-f.Redundancy_HHI).abs().max())
    dump('GRID_DEFINITION_QA.json',checks)
    with np.load(sources.source(FORMAL+'Stage 1 Output_expanded/physical_inputs_2pc50.npz')) as z:
        stations=z['station_ids'].astype(str)
    verify_recovery(sources,f,tracts.index.tolist(),mapping,stations)
    nri=sources.frame('Data/NRI_Table_CensusTracts_California.csv',key='TRACTFIPS',columns=['TRACTFIPS','NRI_VER','SOVI_SCORE','SOVI_SPCTL','POPULATION'])
    helper=sources.frame('Data/LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv',key='TRACTFIPS',columns=['TRACTFIPS','SOVI_SCORE'])
    assert nri.loc[f.index].NRI_VER.eq('Mar-23').all()
    assert np.allclose(f.SOVI_SCORE,nri.loc[f.index].SOVI_SCORE,atol=1e-10)
    assert np.allclose(f.SOVI_SCORE,helper.loc[f.index].SOVI_SCORE,atol=1e-5)
    cdc=sources.frame('Data/California.csv',key='FIPS',columns=['FIPS','RPL_THEMES','E_TOTPOP','AREA_SQMI',*[f'RPL_THEME{i}' for i in range(1,5)]])
    cdc=cdc.reindex(f.index).replace(-999,np.nan)
    density=cdc.E_TOTPOP/cdc.AREA_SQMI
    assert np.allclose(f.Pop_Density,density,atol=1e-8)
    dump('POPULATION_AND_DENSITY_SOURCE_QA.json',dict(
         frozen_population_matches_all_formal_rows=True,frozen_count=len(f),
         nri_population_exact_matches=int(f.Population.eq(nri.POPULATION.reindex(f.index)).sum()),
         frozen_population_replaced=False,
         frozen_population_documented_vintage='2020-based per existing harmonization decision; upstream Census release/batch not independently authenticated',
         direct_upstream_population_release_resolved=False,
         stored_density_definition='CDC2022 E_TOTPOP / AREA_SQMI; persons per square mile',
         density_source_max_error=float((f.Pop_Density-density).abs().max())))
    f['CDC2022_RPL_THEMES']=cdc.RPL_THEMES
    themes=[f'RPL_THEME{i}' for i in range(1,5)]
    f['CDC2022_local_theme_mean']=cdc[themes].mean(axis=1).where(cdc[themes].notna().all(axis=1))
    historical=sources.frame(FORMAL+'Stage 7 Output_expanded/clusters_labels_final.csv',columns=['tract_id','SVI_Composite'])
    assert np.allclose(f.loc[historical.index,'CDC2022_local_theme_mean'],historical.SVI_Composite,atol=1e-10)
    previous=pd.read_csv(sources.source('results/vulnerability/SOCIAL_VULNERABILITY_MEASURE_COMPARISON.csv'))
    svi_comparison(f,meta.SOVI_quartile.reindex(f.index),previous)
    living=sources.frame(BE+'living_environment_audit_20261011/LIVING_ENVIRONMENT_VALUES_2315.csv',commit=SPEC['external_diagnostic_commit'])
    for c in ['electric_heating_share','electric_heating_share_moe90','electric_heating_occupied_units','electric_heating_denominator_CI90_includes_zero','electric_heating_units','SVI2020_CA_EP_MUNIT']:
        f[c]=living[c].reindex(f.index)
    f['residential_member']=f.index.isin(residential)
    f['historical_CORE3_member']=f.index.isin(core)
    f['frozen_SOVI_quartile']=meta.SOVI_quartile.reindex(f.index)
    cohort=pd.DataFrame(index=f.index)
    cohort['study_member']=True
    cohort['residential_member']=f.residential_member
    cohort['historical_CORE3_member']=f.historical_CORE3_member
    cohort['proposed_primary_member']=f.residential_member & f[PRIMARY].notna().all(axis=1)
    cohort['formal_population']=f.Population
    cohort['housing_units']=f.housing_total
    cohort['old_geometry_exclusion_not_inherited']=f.residential_member & ~f.historical_CORE3_member
    cohort['residential_exclusion_reason']=np.select([f.housing_total.eq(0), f.Population.eq(0)],['zero housing units: prior residential-cohort definition','zero frozen population'],default='')
    cohort['primary_missing_variables']=f[PRIMARY].isna().apply(lambda row:';'.join(row.index[row]),axis=1)
    cohort['diagnostic_missing_variables']=f[DIAGNOSTIC].isna().apply(lambda row:';'.join(row.index[row]),axis=1)
    cohort['full_domain_eligibility_note']='No geometry-based exclusion required for proposed RQ variables; full-domain inclusion is an author scope decision.'
    save('TRACT_COHORT_AND_MISSINGNESS.csv',cohort.reset_index())
    save('TRACT_CANDIDATE_VALUES_2315.csv',f.reset_index())
    primary_pairs=information_audit(f[PRIMARY],residential,'PRIMARY_2291')
    allcols=PRIMARY+DIAGNOSTIC
    complete=f.loc[residential,allcols].dropna().index
    all_pairs=information_audit(f[allcols],complete,'EXTENDED_COMMON')
    gridpairs=information_audit(f[['Init_Supply',*GRID]],residential,'RQ1_2291')
    recpairs=information_audit(f[['B_480_hr','T80','Delta_B_logistics','B_unconstrained']],residential,'RQ2_2291')
    save('RQ1_GRID_METRIC_REDUNDANCY.csv',gridpairs)
    save('RQ2_RECOVERY_METRIC_REDUNDANCY.csv',recpairs)
    save('CROSS_DOMAIN_INFORMATION_AUDIT.csv',pd.concat([primary_pairs,all_pairs],ignore_index=True))
    cond=[]
    for columns,block,cohort_ids in [(PRIMARY,'primary_three_RQ',residential),(['Init_Supply',*GRID],'RQ1_all',residential),
          (['B_480_hr','T80','Delta_B_logistics'],'RQ2_candidate_not_arithmetic_triplet',residential),
          (['B_480_hr','B_unconstrained','Delta_B_logistics'],'RQ2_forbidden_identity_diagnostic_only',residential),
          (allcols,'extended_includes_identity_and_alternatives_DIAGNOSTIC_ONLY',complete),
          (['SOVI_SCORE','log1p_Population','electric_heating_share','housing_5plus_share','log1p_Pop_Density'],'RQ3_heating_context',complete)]:
        cond.extend(conditional(f,columns,block,cohort_ids))
    save('CONDITIONAL_EXPLAINED_VARIANCE_AND_VIF.csv',cond)
    invalid=[]
    for c in allcols:
        for key in f.index[f[c].isna()]:
            invalid.append(dict(tract_id=key,variable=c,reason='source NA or documented undefined denominator; no zero fill',residential_member=key in residential))
    save('MISSING_VALUE_LEDGER.csv',invalid)
    save('PRIMARY_COHORT_GEOIDS.csv',pd.DataFrame({'tract_id':residential}))
    save('EXTENDED_DIAGNOSTIC_COHORT_GEOIDS.csv',pd.DataFrame({'tract_id':complete}))
    dump('COHORT_QA.json',dict(study_n=len(f),residential_n=len(residential),core3_n=len(core),primary_n=int(cohort.proposed_primary_member.sum()),
         primary_GEOID_sha256=idhash(residential),extended_common_n=len(complete),extended_GEOID_sha256=idhash(complete),
         regained_residential_GEOIDs=cohort.index[cohort.old_geometry_exclusion_not_inherited].tolist(),
         full_domain_primary_missing=int(f[PRIMARY].isna().any(axis=1).sum()),no_zero_filling=True,no_cluster_labels_read=True))
    if args.comments:
        raw=longpath(args.comments).read_bytes()
        with zipfile.ZipFile(longpath(args.comments)) as z:
            ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in ET.fromstring(z.read('word/document.xml')).findall('.//w:p',ns)]
            has_comments_xml='word/comments.xml' in z.namelist()
        svi_text_hits=[p for p in paragraphs if re.search(r'\bSVI\b|social.vulnerab',p,re.I)]
        assert not has_comments_xml and not svi_text_hits
        quote=next(t for t in paragraphs if 'which are the variables for the k-means' in t)
        dump('ORIGINAL_COMMENT_SOURCE_RECORD.json',dict(filename=args.comments.name,sha256=hashlib.sha256(raw).hexdigest(),
             source_location='local research archive/00_Project_Deliverables/Manuscript_Working_Files',original_comment=quote,
             main_document_paragraph_index=paragraphs.index(quote),comments_xml_present=has_comments_xml,
             readable_SVI_specific_paragraphs=svi_text_hits,
             explicit_SVI_theme_aggregation_recommendation_found=False,
             limitation='Readable main-document text inspected, no comments XML present; embedded equation images not interpreted as new recommendations.'))
    # Verify static station provenance by original CGS bytes and saved check,
    # without regenerating or replacing any PGA values.
    gridpath=sources.source('Data/MS_048_CA_pt01_MMI_GM_datafiles/CA_pt01_GM_maps.csv')
    grid=pd.read_csv(gridpath,skipinitialspace=True)
    grid.columns=grid.columns.str.strip()
    check=pd.read_csv(sources.source(BE+'local_joint_feature_extraction_20261009/FROZEN_STATION_PGA_SOURCE_CHECK.csv'),dtype={'station_id':str})
    stationpga=pd.read_csv(sources.source('Data/Substations_PGA_IDW_CEC_expanded.csv'),dtype={'ID':str})
    aligned=check.merge(stationpga[['ID','PGA_2pc50']],left_on='station_id',right_on='ID',validate='one_to_one')
    assert len(aligned)==92 and set(aligned.station_id)==set(stations)
    assert np.allclose(aligned.frozen_PGA_g,aligned.PGA_2pc50,atol=1e-12)
    assert aligned.error_g.abs().max()<1e-12
    source_qa=json.loads(sources.source(BE+'local_joint_feature_extraction_20261009/TRACT_SEISMIC_HAZARD_QA.json').read_text())
    assert source_qa['source_sha256']==sha(gridpath)
    dump('HAZARD_SOURCE_QA.json',dict(source_sha256=sha(gridpath),rows=len(grid),columns=grid.columns.tolist(),
         units='g',vintage=source_qa['vintage'],official_byte_identity_previously_verified=source_qa['official_download_exact_byte_match'],
         frozen_station_n=92,station_min_g=float(aligned.PGA_2pc50.min()),station_median_g=float(aligned.PGA_2pc50.median()),station_max_g=float(aligned.PGA_2pc50.max()),
         frozen_check_max_error_g=float(aligned.error_g.abs().max()),mean_return_interval_yr=-50/np.log(.98),
         substantive_hazard_source_mismatch=False,interpretation_mismatch_if_called_BSE_2E=True,
         no_PGA_regenerated=True))
    save('FROZEN_STATION_PGA_VERIFICATION.csv',aligned)
    for rel in [BE+'living_environment_audit_20261011/SOURCE_URLS_AND_CHECKSUMS.csv',BE+'living_environment_audit_20261011/ACS_NUMERICAL_QA.json',
                BE+'living_environment_audit_20261011/SVI_COMPONENT_SCOPE_QA.json',
                BE+'living_environment_audit_20261011/sources/B25040_06.csv.zip',
                BE+'living_environment_audit_20261011/sources/ACS_VRE_DOCUMENTATION.pdf']:
        sources.source(rel,SPEC['external_diagnostic_commit'])
    for rel in ['docs/methodology/STAGE7_SVI_HARMONIZATION_DECISION.md','docs/reviewer/SOCIAL_VULNERABILITY_MEASURE_REVIEW.md',
                'src/la_grid/core/C257H_Project_Main.py','src/la_grid/revision/formal/stage7.py',
                'config/parent_frozen_design/FINAL_EXPERIMENT_MATRIX.json',
                'provenance/figure_review_history/candidate_v2.1_layout/STORY_EVIDENCE_MATRIX.md',
                'results/figure_review/Main/Fig01.pdf',BE+'local_joint_feature_extraction_20261009/ACQUISITION_LOG.json']:
        sources.source(rel)
    design=json.loads(sources.source('config/parent_frozen_design/FINAL_EXPERIMENT_MATRIX.json').read_text())
    assert design['production']['mapping_case']==SPEC['mapping']
    assert design['production']['functional_threshold']==SPEC['gate_threshold']
    assert design['physical_samples']['N_EVAL_per_hazard']==SPEC['realization_count']
    assert design['domain']==dict(stations=92,edges=318,tracts=2315)
    dump('FROZEN_DESIGN_REFERENCE_QA.json',dict(matrix_id=design['matrix_id'],
         declared_production=design['production'],declared_physical_samples=design['physical_samples'],
         selected_resource=SPEC['resources'],selected_mapping=SPEC['mapping'],selected_gate=SPEC['gate'],
         configuration_checked_not_executed=True))
    save('SOURCE_HASH_VERIFICATION.csv',sources.records)
    after=sources.snapshot()
    before=json.loads((OUT/'PRESERVATION_BEFORE.json').read_text())
    dump('PRESERVATION_AFTER.json',after)
    assert before==after
    dump('EXECUTION_QA.json',dict(status='COMPLETE_NUMERICAL_AUDIT',protected_files_unchanged=before==after,
         no_Kmeans_or_PCA_fits=True,no_weighted_matrix=True,no_new_PGA_damage_MC_schedules=True,
         software=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__),
         source_baseline=git('rev-parse',SPEC['baseline_commit']).decode().strip()))
    print('AUDIT_COMPLETE',len(f),len(residential),len(complete),flush=True)


if __name__=='__main__':
    main()
