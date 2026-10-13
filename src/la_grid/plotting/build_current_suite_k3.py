"""Canonical, figure-only NCV14/H2/K3 suite layer over the approved 17-figure suite.

No models are fitted. Pinned source payloads are hash-checked before use. Historical
builders remain historical; this is the documented current-suite entrypoint.
"""
from pathlib import Path
import hashlib
import html
import io
import json
import os
import re
import sys

import fitz
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from PIL import Image

import consolidate_current_figure_suite as u

ROOT = u.ROOT
DEST = ROOT / 'results/figure_review'
QA = ROOT / 'docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013'
INPUTS = QA / 'inputs'
BASE = '59d9001edadef57c5ff1dc6af6ca8d7817fb4f94'
SCIENTIFIC = '49cc153c3f4d7a8c29cf94baf090dbfc0be4d068'
FROZEN = '0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
DECISION = '05a78645b17bf8de04326e54181f9db432d7186c'
ACCEPTED_SUITE = '8f2dcb3b9762137b9f2686609c34480334f5d44e'
S10_OLD_REFERENCE = 'Outcome comparisons appear in Figures 4-6 and Supplementary Figures S12/S13'
S10_CURRENT_REFERENCE = 'Outcome comparisons appear in Figures 4\u20136 and Supplementary Figure S11'
SP = 'docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/'
DP = 'docs/data_research/stage7_fig7d_policy_robustness_and_final_integration_gate_20261013/'
GENERATOR = 'src/la_grid/plotting/build_current_suite_k3.py'
ACTIVE = [f'Main/Fig{i:02d}' for i in range(1, 8)] + [f'Supplement/FigS{i:02d}' for i in [1, *range(3, 12)]]
CHANGED = ['Main/Fig01', 'Main/Fig07', 'Supplement/FigS09']
FEATURES = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained',
            'MeanDelta', 'SOVI_SCORE', 'log1p_Population', 'FEMA_NCV14_CA_v119']
BUDGETS = np.array([1/9, 1/9, 1/9, 1/6, 1/6, 1/6, 1/12, 1/12])
COLORS = ['#147f98', '#d07734', '#7a5899']
NA = '#e5e5e5'
SOURCES = {}
MM = 72 / 25.4


def source(commit, rel):
    key = commit + ':' + rel
    b = u.payload(commit, rel)
    pointer = u.git('show', key)
    m = re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)', pointer)
    SOURCES[key] = {'commit': commit, 'path': rel, 'sha256': u.digest(b), 'bytes': len(b),
                    'git_blob': u.git('rev-parse', key).decode().strip(),
                    'lfs_oid': m.group(1).decode() if m else None}
    if m:
        assert u.digest(b) == m.group(1).decode() and len(b) == int(m.group(2))
    return b


def frame(commit, rel):
    return pd.read_csv(io.BytesIO(source(commit, rel)), dtype={'tract_id': str}, float_precision='round_trip')


def table(name, df):
    u.write(INPUTS / name, df.to_csv(index=False, lineterminator='\n'))


def json_read(path):
    return json.load(open(u.lp(path), encoding='utf-8'))


def primary_source(stem):
    if stem == 'Main/Fig01':
        return BASE, 'results/figure_review/Main/Fig01.pdf'
    if stem == 'Main/Fig07':
        return FROZEN, SP + 'candidate/EIGHT_VARIABLE_FROZEN_TABLE.csv'
    if stem == 'Supplement/FigS09':
        return FROZEN, SP + 'inputs/EXISTING_K_EVIDENCE.csv'
    raise ValueError(stem)


def snapshot():
    if '--portable' in sys.argv:
        if not (QA / 'PRESERVATION_BEFORE.json').exists():
            raise FileNotFoundError('Portable replay requires the committed original preservation record')
        u.dump(QA / 'PORTABLE_REPLAY_PRESERVATION_NOTICE.json', {
            'original_worktree_reverified': False,
            'mode': 'Portable replay; historical preservation record retained, not reverified locally'})
        return json_read(QA / 'PRESERVATION_BEFORE.json')
    reference = json.loads(source(DECISION, DP + 'STARTING_STATE_AND_PROTECTION.json'))
    return u.protected_snapshot(reference)


def prepare_inputs():
    f = frame(FROZEN, SP + 'candidate/EIGHT_VARIABLE_FROZEN_TABLE.csv')
    member = frame(FROZEN, SP + 'candidate/K3_CLUSTER_MEMBERSHIP.csv')
    registry = frame(FROZEN, SP + 'candidate/CLASS_ID_REGISTRY.csv').query('k == 3').copy()
    all_tracts = frame(FROZEN, SP + 'candidate/FULL_2315_COHORT_STATUS.csv')
    weights = frame(FROZEN, SP + 'candidate/COHORT_STANDARDIZER_AND_WEIGHTS.csv')
    policy = frame(DECISION, DP + 'FROZEN_POLICY_TRACT_MEANS_2315.csv')
    k = frame(FROZEN, SP + 'inputs/EXISTING_K_EVIDENCE.csv')
    stability = frame(FROZEN, SP + 'inputs/EXISTING_STABILITY.csv').query('k == 3').copy()
    frozen = np.load(io.BytesIO(source(FROZEN, SP + 'candidate/FROZEN_PREPROCESSING_AND_LABELS.npz')))
    saved = np.load(io.BytesIO(source(FROZEN, SP + 'inputs/SAVED_LABELS_AND_SILHOUETTES.npz')))
    spec = json.loads(source(FROZEN, SP + 'candidate/FROZEN_CANDIDATE_SPECIFICATION.json'))
    # The registry fixes IDs; its companion pinned figure source fixes the palette.
    palette_source = source(FROZEN, SP + 'figures.py').decode()
    assert all(c in palette_source.lower() for c in COLORS), 'Pinned palette differs'
    assert spec['coordinates'] == FEATURES
    for d in [f, member, all_tracts, policy]:
        assert d.tract_id.str.fullmatch(r'\d{11}').all() and not d.tract_id.duplicated().any()
    assert len(f) == len(member) == 2299 and len(all_tracts) == len(policy) == 2315
    assert f.tract_id.equals(member.tract_id)
    assert np.array_equal(f.tract_id.to_numpy(), frozen['tract_ids'])
    np.testing.assert_array_equal(f[FEATURES].to_numpy(), frozen['raw'])
    np.testing.assert_allclose(weights.squared_distance_budget, BUDGETS, atol=1e-16, rtol=0)
    np.testing.assert_allclose(weights.Euclidean_multiplier, np.sqrt(BUDGETS), atol=1e-16, rtol=0)
    raw = f[FEATURES].to_numpy()
    np.testing.assert_allclose(raw.mean(0), weights.cohort_mean, atol=1e-12, rtol=1e-14)
    np.testing.assert_allclose(raw.std(0), weights.population_SD, atol=1e-12, rtol=1e-14)
    weighted = (raw - weights.cohort_mean.to_numpy()) / weights.population_SD.to_numpy() * np.sqrt(BUDGETS)
    np.testing.assert_allclose(weighted, frozen['weighted_matrix'], atol=1e-12, rtol=1e-13)
    np.testing.assert_array_equal(member.saved_model_class, frozen['K3_labels'])
    assert np.array_equal(member.candidate_display_cluster, member.saved_model_class + 1)
    assert list(registry.saved_model_class) == [0, 1, 2]
    np.testing.assert_allclose(np.log1p(f.Population), f.log1p_Population, atol=1e-14, rtol=0)
    f = f.drop(columns='review_status').merge(member[['tract_id', 'candidate_display_cluster']], validate='one_to_one')
    f = f.rename(columns={'candidate_display_cluster': 'K3_class'})
    p = policy.set_index('tract_id').loc[f.tract_id]
    np.testing.assert_array_equal(f.Population, p.Population)
    np.testing.assert_array_equal(f.frozen_SOVI_quartile, p.frozen_SOVI_quartile)
    np.testing.assert_allclose(f.B_Unconstrained, p.B_unconstrained, atol=1e-12, rtol=0)
    np.testing.assert_allclose(f.MeanDelta, p.MeanDelta5, atol=1e-12, rtol=0)
    scheduled = ['B_' + s for s in ['impact-first', 'hospital-first', 'degree-first', 'betweenness-first', 'vulnerability-first']]
    total = policy[scheduled].mean(axis=1)
    errors = total - (policy.B_unconstrained + policy.MeanDelta5)
    np.testing.assert_allclose(errors, 0, atol=1e-12, rtol=0)
    np.testing.assert_allclose(total, policy.MeanTotal5, atol=1e-12, rtol=0)
    f['MeanTotalDeficit_5'] = p.MeanTotal5.to_numpy()
    assert f.Population.sum() == 9066522 and (f.Population > 0).all()
    sizes = f.groupby('K3_class').size().tolist()
    pops = f.groupby('K3_class').Population.sum().tolist()
    assert sizes == [1242, 475, 582] and pops == [5101704, 1897838, 2066980]
    assert int(f.additional_zero_housing_positive_population.sum()) == 8
    assert all_tracts.Frozen_Formal_Population.gt(0).sum() == 2299
    assert all_tracts.Frozen_Formal_Population.eq(0).sum() == 16
    assert np.array_equal(all_tracts.loc[all_tracts.clustering_eligible, 'K3_candidate_cluster'].astype(int), f.K3_class)
    assert f.frozen_SOVI_quartile.eq('Q4').sum() == 579
    geobytes = source(FROZEN, SP + 'candidate/FULL_2315_GEOMETRY.gpkg')
    u.write(INPUTS / 'FULL_2315_GEOMETRY.gpkg', geobytes)
    g = gpd.read_file(u.lp(INPUTS / 'FULL_2315_GEOMETRY.gpkg'))
    assert len(g) == 2315 and g.crs is not None
    if 'tract_id' not in g:
        g = g.rename(columns={'GEOID': 'tract_id'})
    g['tract_id'] = g.tract_id.astype(str).str.zfill(11)
    assert set(g.tract_id) == set(all_tracts.tract_id)
    assert g.geometry.notna().all() and not g.geometry.is_empty.any()
    g = g[['tract_id', 'geometry']].to_crs(3310).merge(f, on='tract_id', how='left', validate='one_to_one')
    assert g.K3_class.notna().sum() == 2299
    assert not g.loc[g.K3_class.isna(), 'tract_id'].isin(f.tract_id).any()
    # Current plotting inputs explicitly exclude all K4 membership arrays and columns.
    all_tracts = all_tracts.drop(columns=['K4_candidate_cluster', 'review_status']).rename(columns={'K3_candidate_cluster': 'K3_class'})
    member = member.drop(columns=['review_status', 'candidate_role']).rename(columns={'candidate_display_cluster': 'K3_class'})
    registry = registry.drop(columns=['review_status', 'role'])
    registry['color'] = COLORS
    weights = weights.drop(columns='review_status')
    k = k.drop(columns='review_status')
    stability = stability.drop(columns='review_status')
    for name, d in [('EIGHT_VARIABLE_FROZEN_TABLE.csv', f), ('K3_CLUSTER_MEMBERSHIP.csv', member),
                    ('FULL_2315_COHORT_STATUS.csv', all_tracts), ('CLASS_ID_REGISTRY.csv', registry),
                    ('COHORT_STANDARDIZER_AND_WEIGHTS.csv', weights), ('K_DIAGNOSTICS.csv', k),
                    ('K3_STABILITY.csv', stability), ('FROZEN_POLICY_TRACT_MEANS_2315.csv', policy.drop(columns='review_status'))]:
        table(name, d)
    main_index = list(saved['keys']).index('NCV14__main__k3__s42')
    np.testing.assert_array_equal(saved['tract_ids'], f.tract_id.to_numpy())
    np.testing.assert_array_equal(saved['labels'][main_index], member.saved_model_class)
    chosen = np.array(['__k3__' in key for key in saved['keys']])
    out = io.BytesIO()
    np.savez_compressed(out, tract_ids=f.tract_id.to_numpy(dtype='U11'), feature_names=np.array(FEATURES),
                        raw=raw, weighted_matrix=weighted, budgets=BUDGETS, K3_labels=frozen['K3_labels'],
                        keys=saved['keys'][chosen], labels=saved['labels'][chosen], silhouette=saved['silhouette'][chosen])
    u.write(INPUTS / 'K3_FROZEN_ARRAYS.npz', out.getvalue())
    sil = saved['silhouette'][main_index]
    np.testing.assert_allclose(sil.mean(), k.loc[k.k.eq(3), 'mean_silhouette'].item(), atol=1e-12, rtol=0)
    metrics = {'cohort': 2299, 'study_domain': 2315, 'zero_population_unassigned': 16,
               'positive_population_zero_housing_classified': 8, 'represented_population': 9066522,
               'class_counts': sizes, 'class_population': pops, 'frozen_Q4_count': 579,
               'saved_K3_labels_exact': True, 'eight_features_exact': True,
               'H2_budgets': BUDGETS.tolist(), 'maximum_total_deficit_identity_error_h': float(abs(errors).max()),
               'D3_definition': 'MeanTotalDeficit_5 = B_Unconstrained + MeanDelta_5',
               'policy_set': [s.removeprefix('B_') for s in scheduled], 'random_included': False,
               'physical_trajectories_or_fits_recomputed': False, 'formal_Stage7_migrated': False,
               'projection': 'EPSG:3310', 'palette': COLORS}
    u.dump(QA / 'FIG07_K3_AND_D3_NUMERICAL_QA.json', metrics)
    silrows = []
    for c in [1, 2, 3]:
        v = sil[f.K3_class.eq(c)]
        silrows.append({'class': c, 'n': len(v), 'mean': float(v.mean()), 'median': float(np.median(v)),
                        'p10': float(np.quantile(v, .1)), 'p90': float(np.quantile(v, .9)),
                        'negative_fraction': float(np.mean(v < 0))})
    u.write_csv(QA / 'K3_PER_CLASS_SILHOUETTE.csv', silrows)
    u.dump(QA / 'FIGS09_K3_DIAGNOSTIC_QA.json', {'source_commit': FROZEN, 'k_range': list(range(1, 9)),
        'K3_mean_silhouette': float(sil.mean()), 'K3_is_silhouette_maximum': False,
        'curve_rows': k.to_dict('records'), 'per_class_silhouette': silrows,
        'classification_k': 3, 'K4_classification_displayed': False, 'kmeans_fit_or_k_search_run': False,
        'stability_k': [3], 'initialization_seeds': list(range(42, 47)),
        'minus_Init_reallocates_RQ1_remaining_budgets_from': 1/9, 'minus_Init_reallocates_to': 1/6})
    return f, g, k, stability, sil


def style():
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 8.5, 'axes.titlesize': 9,
        'axes.labelsize': 8.5, 'xtick.labelsize': 8, 'ytick.labelsize': 8,
        'legend.fontsize': 8, 'pdf.fonttype': 42, 'ps.fonttype': 42,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .65,
        'savefig.facecolor': 'white'})


def save_figure(fig, stem):
    b = io.BytesIO()
    fig.savefig(b, format='pdf', metadata={'CreationDate': None, 'ModDate': None,
                                         'Creator': GENERATOR, 'Subject': 'Author-approved figure-only frozen NCV14/H2/K3 sources'})
    u.write(DEST / (stem + '.pdf'), b.getvalue())
    plt.close(fig)
    export_png(stem)


def export_png(stem):
    # A fresh renderer avoids cross-document font-cache substitution.
    import subprocess
    code = ('import fitz,sys; from PIL import Image; d=fitz.open(sys.argv[1]); '
            'p=d[0].get_pixmap(dpi=600,alpha=False); '
            'Image.frombytes("RGB",[p.width,p.height],p.samples).save(sys.argv[2],dpi=(600,600)); '
            'd[0].get_pixmap(dpi=160,alpha=False).save(sys.argv[3])')
    subprocess.run([sys.executable, '-c', code, u.lp(DEST / (stem + '.pdf')),
                    u.lp(DEST / (stem + '.png')), u.lp(DEST / 'Page_Previews' / (Path(stem).name + '.png'))], check=True)


def draw_map(ax, g, mode):
    extent = g.total_bounds
    if mode == 'class':
        g.loc[g.K3_class.isna()].plot(ax=ax, facecolor=NA, edgecolor='#757575', linewidth=.23)
        for c, color in enumerate(COLORS, 1):
            g.loc[g.K3_class.eq(c)].plot(ax=ax, facecolor=color, edgecolor='white', linewidth=.055)
    else:
        g.loc[g.MeanTotalDeficit_5.isna()].plot(ax=ax, facecolor=NA, edgecolor='#757575', linewidth=.23)
        g.loc[g.MeanTotalDeficit_5.notna()].plot(ax=ax, column='MeanTotalDeficit_5', cmap='cividis',
            edgecolor='none', vmin=g.MeanTotalDeficit_5.min(), vmax=g.MeanTotalDeficit_5.max())
        # Boundaries of the frozen Q4 geographic union avoid overpainting every shared edge.
        q4 = g.loc[g.frozen_SOVI_quartile.eq('Q4')].geometry.union_all()
        gpd.GeoSeries([q4], crs=g.crs).boundary.plot(ax=ax, color='#ac3650', linewidth=.38)
    outline = g.geometry.union_all()
    gpd.GeoSeries([outline], crs=g.crs).boundary.plot(ax=ax, color='#747474', linewidth=.25)
    padx, pady = np.diff(extent[[0, 2]])[0] * .035, np.diff(extent[[1, 3]])[0] * .035
    ax.set_xlim(extent[0]-padx, extent[2]+padx)
    ax.set_ylim(extent[1]-pady, extent[3]+pady)
    ax.set_aspect('equal')
    ax.set_axis_off()


def figure7(f, g):
    fig = plt.figure(figsize=(185/25.4, 245/25.4))
    fig.text(.055, .975, 'A. Tract and resident representation', weight='bold', fontsize=10)
    ax = fig.add_axes([.10, .855, .85, .095])
    tract = f.groupby('K3_class').size().to_numpy()
    pop = f.groupby('K3_class').Population.sum().to_numpy()
    for c, (n, p, color) in enumerate(zip(tract, pop, COLORS)):
        ax.barh(2-c, n/2299*100, height=.25, color=color)
        ax.barh(2-c-.28, p/9066522*100, height=.25, facecolor='white', edgecolor=color, linewidth=1.1)
        ax.text(max(n/2299*100, p/9066522*100)+1.3, 2-c-.14, f'{n:,} tracts\n{p:,} residents', va='center', fontsize=8)
    ax.set_yticks([1.86,.86,-.14], ['C1','C2','C3'])
    ax.set_xlim(0, 84); ax.set_xticks([0,20,40,60]);ax.set_xlabel('Share of eligible tracts or represented residents (%)', labelpad=2)
    ax.legend(handles=[Patch(facecolor='#999999', label='Tracts'), Patch(facecolor='white', edgecolor='#777777', label='Residents')],
              loc='upper right', bbox_to_anchor=(1.02,1.18), frameon=False, ncol=2)
    fig.text(.055,.79,'B. Original-unit class means',weight='bold',fontsize=10)
    fields = ['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','Population','FEMA_NCV14_CA_v119']
    titles = ['RQ1: Initial service\nAvailability (%)','RQ1: Spectral grid impact\nUnitless','RQ1: Dependency HHI\nUnitless',
              'RQ2: Unconstrained deficit\nHours (0-480 h)','RQ2: Constraint increment\nHours (five-policy mean)',
              'RQ3: Social vulnerability\nSOVI score (0-100)','RQ3: Population\nPersons','RQ3: Natural-hazard screen\nNCV14 index']
    for j, (field, title) in enumerate(zip(fields, titles)):
        row, col = divmod(j, 4)
        a = fig.add_axes([.075+col*.238, .665-row*.135, .188, .075])
        means = f.groupby('K3_class')[field].mean().to_numpy()
        if field == 'Init_Supply': means = means*100
        for c, (value, color) in enumerate(zip(means, COLORS)):
            a.bar(c, value, color=color, width=.65)
        a.set_xticks([0,1,2], ['C1','C2','C3'])
        a.set_title(title, loc='left', fontsize=7.5, pad=5)
        a.set_ylim(0,max(means)*1.20)
        a.tick_params(axis='both', labelsize=7.5, pad=2)
        a.locator_params(axis='y', nbins=3)
        if field == 'Population': a.ticklabel_format(axis='y', style='plain')
    fig.text(.075,.48,'Population is shown in persons; log1p(Population) is used for fitting.',fontsize=8)
    fig.text(.055,.445,'C. Adopted K3 community typology',weight='bold',fontsize=10)
    fig.text(.53,.445,'D. Five-policy mean service deficit',weight='bold',fontsize=10)
    c = fig.add_axes([.045,.10,.445,.34]);d=fig.add_axes([.515,.10,.445,.34])
    draw_map(c,g,'class'); draw_map(d,g,'deficit')
    fig.legend(handles=[Patch(facecolor=color, label=f'C{i}') for i,color in enumerate(COLORS,1)]+[Patch(facecolor=NA,edgecolor='#757575',label='N/A (16)')],
               loc='lower left',bbox_to_anchor=(.065,.052),ncol=4,frameon=False,columnspacing=.9,handlelength=1.1)
    m=plt.cm.ScalarMappable(norm=matplotlib.colors.Normalize(g.MeanTotalDeficit_5.min(),g.MeanTotalDeficit_5.max()),cmap='cividis')
    cb=fig.colorbar(m,cax=fig.add_axes([.56,.095,.335,.012]),orientation='horizontal')
    cb.solids.set_rasterized(False)
    cb.set_label('Equivalent full-service-deficit hours (0-480 h)',fontsize=8,labelpad=2)
    cb.ax.tick_params(labelsize=8,pad=2)
    fig.legend(handles=[Line2D([0],[0],color='#ac3650',lw=.8,label='Frozen SOVI Q4 boundary'),
                        Patch(facecolor=NA,edgecolor='#757575',label='N/A (16)')],
               loc='lower left',bbox_to_anchor=(.54,.010),ncol=1,frameon=False,handlelength=1.5)
    fig.text(.06,.012,'2,299 positive-population tracts; 9,066,522 represented residents.',fontsize=8)
    save_figure(fig,'Main/Fig07')


def figure_s9(f, k, stability, sil):
    fig, axes = plt.subplots(2,2,figsize=(185/25.4,165/25.4))
    fig.subplots_adjust(left=.15,right=.975,bottom=.095,top=.94,hspace=.51,wspace=.37)
    for ax in axes.flat: ax.tick_params(labelsize=8)
    ax=axes[0,0];ax.plot(k.k,k.mean_WCSS,'o-',color='#536671',lw=1.3,ms=3.5)
    row=k.loc[k.k.eq(3)].iloc[0]
    ax.scatter([3],[row.mean_WCSS],s=36,color=COLORS[0],zorder=3)
    ax.set(title='A. Weighted-space inertia',xlabel='Number of clusters (K)',ylabel='WCSS (inertia)')
    ax.set_xticks(range(1,9));ax.set_ylim(0,2400)
    ax=axes[0,1];valid=k.k.ge(2)
    ax.plot(k.loc[valid,'k'],k.loc[valid,'mean_silhouette'],'o-',color='#536671',lw=1.3,ms=3.5)
    ax.fill_between(k.loc[valid,'k'],k.loc[valid,'sil_min'],k.loc[valid,'sil_max'],color='#b8c3c9',alpha=.4)
    ax.scatter([3],[row.mean_silhouette],s=36,color=COLORS[0],zorder=3)
    ax.set(title='B. Full-cohort silhouette',xlabel='Number of clusters (K)',ylabel='Mean silhouette coefficient')
    ax.set_xticks(range(2,9))
    ax.text(.02,.04,'K3 adopted for regional interpretation;\nnot the silhouette maximum.',transform=ax.transAxes,fontsize=8)
    ax=axes[1,0]
    groups=[('seed',None,'Initialization'),('geographic',None,'Geographic\nleave-block-out'),('policy','__cohort','Policy LOO\n(cohort scale)'),('policy','__fixed_main5','Policy LOO\n(fixed scale)')]
    for y,(test,suffix,label) in enumerate(groups):
        d=stability.loc[stability.test.eq(test)]
        if suffix: d=d.loc[d.condition.str.endswith(suffix)&~d.condition.str.contains('plus_random')]
        vals=d.ARI.to_numpy();ax.plot([vals.min(),vals.max()],[y,y],color='#70818a',lw=2)
        ax.scatter(vals,np.full(len(vals),y),s=20,color=COLORS[0],zorder=3)
    ax.set_yticks(range(4),[v[2] for v in groups],fontsize=8)
    ax.invert_yaxis();ax.set_xlim(.45,1.025);ax.set_xticks([.5,.75,1]);ax.set_xlabel('Adjusted Rand index (ARI)')
    ax.set_title('C. K3 partition stability',loc='left')
    ax=axes[1,1]
    values=[sil[f.K3_class.eq(c)] for c in [1,2,3]]
    boxes=ax.boxplot(values,patch_artist=True,showfliers=False,whis=(10,90),widths=.5,
        medianprops={'color':'black','lw':1},boxprops={'lw':.7},whiskerprops={'lw':.7},capprops={'lw':.7})
    for b,color in zip(boxes['boxes'],COLORS):b.set_facecolor(color)
    ax.axhline(0,color='#777777',lw=.7,ls='--');ax.set_xticks([1,2,3],['C1','C2','C3'])
    ax.set(title='D. K3 class silhouette distributions',ylabel='Tract silhouette coefficient')
    ax.set_ylim(-.18,.53)
    ax.text(.02,.97,'Boxes: P25-P75; whiskers: P10-P90',transform=ax.transAxes,va='top',fontsize=7.5)
    save_figure(fig,'Supplement/FigS09')


def figure1():
    b=source(BASE,'results/figure_review/Main/Fig01.pdf')
    old=fitz.open(stream=b,filetype='pdf');new=fitz.open(stream=b,filetype='pdf')
    spans=[s for block in new[0].get_text('dict')['blocks'] for line in block.get('lines',[]) for s in line['spans'] if s['text']=='Hotspot score']
    assert len(spans)==1
    rect=fitz.Rect(spans[0]['bbox']); rect=rect+(-.4,-.2,.4,.2)
    new[0].add_redact_annot(rect,fill=(1,1,1));new[0].apply_redactions(images=0,graphics=0,text=0)
    new[0].insert_font(fontname='ArialCurrent',fontfile='C:/Windows/Fonts/arial.ttf')
    # Two lines in the same spatial-outcome cell, without modifying the diagram.
    for text,y in [('Spatial service-deficit',600.1),('patterns',608.6)]:
        font=fitz.Font(fontfile='C:/Windows/Fonts/arial.ttf');size=7.0
        x=168*MM-font.text_length(text,fontsize=size)/2
        new[0].insert_text((x,y),text,fontname='ArialCurrent',fontsize=size,color=(0,0,0))
    u.write(DEST/'Main/Fig01.pdf',new.tobytes(garbage=4,deflate=True))
    a=old[0].get_pixmap(dpi=160,alpha=False);b=new[0].get_pixmap(dpi=160,alpha=False)
    av=np.frombuffer(a.samples,dtype=np.uint8).reshape(a.height,a.width,3)
    bv=np.frombuffer(b.samples,dtype=np.uint8).reshape(b.height,b.width,3)
    allow=fitz.Rect(440,591,511,611)
    mask=np.ones(av.shape[:2],bool)
    x0,y0,x1,y1=[int(v*160/72) for v in allow]
    mask[y0:y1+2,x0:x1+2]=False
    assert np.array_equal(av[mask],bv[mask]),'Figure 1 changed outside its label'
    u.dump(QA/'FIG01_LABEL_PIXEL_QA.json',{'outside_label_pixels_identical':True,
        'allowable_label_rect_pt':list(allow),'render_dpi':160,'old_text':'Hotspot score',
        'new_text':'Spatial service-deficit patterns','all_other_diagram_content_unchanged':True})
    old.close();new.close();export_png('Main/Fig01')


def correct_s10_reference(heading, body):
    if not heading.startswith('Supplementary Figure S10.'):
        return body
    if S10_CURRENT_REFERENCE in body:
        assert S10_OLD_REFERENCE not in body
        return body
    assert body.count(S10_OLD_REFERENCE) == 1, 'Unexpected S10 source caption; reconcile before editing'
    return body.replace(S10_OLD_REFERENCE, S10_CURRENT_REFERENCE)


def metadata(caps, manifest, index):
    updated={}
    for h in caps:
        if h.startswith('Figure 1.'):
            updated[h]=caps[h].replace('Community typology and hotspot scores describe spatial patterns rather than repair priorities.',
                'Community typology and spatial service-deficit patterns describe modeled community outcomes rather than repair priorities.')
        elif h.startswith('Figure 7.'):
            updated['Figure 7. Three-RQ community typology and modeled service-deficit geography']=(
                'The author-adopted NCV14/H2/K3 figure representation uses 2,299 positive-frozen-population tracts, including eight positive-population tracts without conventional housing units. '
                '(A) Tract and resident representation: C1 comprises 1,242 tracts and 5,101,704 residents; C2, 475 tracts and 1,897,838 residents; and C3, 582 tracts and 2,066,980 residents. The represented total is 9,066,522 residents. '
                '(B) Class means in original units for the eight fitted coordinates. RQ1 comprises initial modeled service availability, spectral grid impact and tract-substation dependency HHI. RQ2 comprises Unconstrained cumulative deficit and the mean additional deficit under five scheduled policies. RQ3 comprises FEMA NRI v1.19 SOVI_SCORE, population and FEMA_NCV14_CA_v119. Population is displayed in persons but fitted as log1p(Population); initial availability is displayed as a percentage. '
                'Each RQ receives one-third of the squared-distance budget: 1/9 each for RQ1; 1/6 each for RQ2; and 1/6, 1/12 and 1/12 for SOVI, log population and NCV14, respectively, after cohort standardization. '
                'NCV14 is a researcher-derived fourteen-hazard frequency-area screening index using FEMA March 2023 v1.19 inputs and California reference scaling, not FEMA RISK_SCORE or a calibrated probability of multi-hazard electricity failure. '
                '(C) Saved K3 memberships use the same three-class palette as A and B. Sixteen zero-population tracts in the 2,315-tract study domain are N/A, not a fourth class. '
                '(D) Continuous five-policy mean total modeled service deficit equals B_Unconstrained plus MeanDelta. The equally weighted finite comparison set is Impact-first, Hospital-first, Degree-first, Betweenness-first and Vulnerability-first; Random is excluded and Unconstrained is the baseline. This mean is not an implemented average repair schedule or an adoption-probability expectation. '
                'Deficits integrate one minus modeled service availability over 0-480 h under frozen 2pc50/C57_D1/M1_UTILITY_003/G1_BASELINE_050 inputs and 1,000 matched physical realizations, in equivalent full-service-deficit hours. Thin outlines show original frozen SOVI Q4 geography. D is descriptive burden geography, not a thresholded hotspot, spatial-significance result or validated repair-priority measure. '
                'Class profiles summarize fitting inputs and are not independent validation. The figure uses the approved frozen K3 authority; the archived formal Stage 7 pipeline and scientific products have not been migrated.')
        elif h.startswith('Supplementary Figure S9.'):
            updated['Supplementary Figure S9. NCV14/H2/K3 selection evidence and stability']=(
                'Saved diagnostics for the eight-variable NCV14/H2 representation of 2,299 positive-frozen-population tracts. '
                '(A) Weighted standardized Euclidean WCSS/inertia for K=1-8. (B) Full-cohort mean silhouette for K=2-8; shading spans registered seeds 42-46, which coincide to displayed precision. Silhouette is undefined for K=1. The curves are smooth and elbow interpretation depends on the evaluated endpoints. '
                'K3 is the sole adopted classification for regional scientific interpretation, not the silhouette maximum; K4 has the highest saved mean silhouette (0.2444 versus 0.2337 for K3), but no K4 classification is presented or adopted. '
                '(C) K3 initialization ARI, four geographic leave-block-out comparisons, and five policy leave-one-out comparisons under cohort-specific and fixed-reference scaling. These are sensitivity checks, not independent external geographic validation. '
                '(D) Saved K3 tract silhouette distributions: boxes P25-P75, median line, P10-P90 whiskers; negative values indicate boundary ambiguity. '
                'The saved K3 minus-Init_Supply ablation has ARI 0.6554 and also redistributes the remaining RQ1 coordinate budgets from 1/9 to 1/6. It is not an isolated feature-deletion effect. Initial service is zero-heavy and partly dependent on the frozen Core-source representation; a relatively nonzero initial state is not proof of resilient electrical delivery. '
                'All diagnostics use existing fitted results (K-means++, n_init=50, Lloyd, max_iter=500, tol=1e-4). No model was refitted for figure production and no alternative classification is promoted.')
        else: updated[h]=correct_s10_reference(h, caps[h])
    u.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md','# Manuscript-facing figure captions\n\n'+'\n\n'.join('## '+h+'\n\n'+b for h,b in updated.items())+'\n')
    palette={'figure_cluster_count':3,'adopted_K':3,'colors':{str(i):c for i,c in enumerate(COLORS,1)},
        'class_labels':['C1','C2','C3'],'NA_fill':NA,'NA_outline':'#757575','NA_count':16,
        'applies_to':['Fig07 A/B/C','FigS09 D'],'membership_commit':FROZEN,
        'membership_source':SP+'candidate/K3_CLUSTER_MEMBERSHIP.csv','formal_Stage7_pipeline_migrated':False}
    u.dump(DEST/'CURRENT_CLUSTER_PALETTE.json',palette)
    changes=[];records=[]
    for row in manifest:
        row=row.copy();stem,ext=row['final_name'].rsplit('.',1)
        prior=row['sha256'];is_changed=stem in CHANGED
        row['change_in_this_update']='UPDATED' if is_changed else 'RETAINED'
        if is_changed:
            input_commit,input_path=primary_source(stem)
            row.update(parent_source_file=row['current_source_file'],parent_source_commit=BASE,parent_sha256=prior,
                source_commit=input_commit, source_file=input_path,
                presentation_generator=GENERATOR,presentation_generator_sha256=u.sha(__file__))
            if stem=='Main/Fig07':
                old_mirror=ROOT/row['mirror_file']
                if old_mirror.exists():
                    existing=open(u.lp(old_mirror),'rb').read()
                    assert u.digest(existing)==prior or existing.startswith(b'version https://git-lfs')
                    # Exact baseline bytes remain in pinned Git/LFS history and the baseline ledger.
                    Path(u.lp(old_mirror)).unlink()
                row['mirror_file']='results/figures/Fig07_Community_Typology_and_Service_Deficit.'+ext
        sha=u.sha(ROOT/row['current_source_file']);row['sha256']=sha
        if not is_changed:assert sha==prior
        doc=fitz.open(u.lp(DEST/(stem+'.pdf')))
        spans=[s for b in doc[0].get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
        if is_changed:
            row['size_mm']=' x '.join(f'{v/MM:.3f}' for v in [doc[0].rect.width,doc[0].rect.height])
            row['min_font_pt']=f"{min(s['size'] for s in spans):.3f}"
            row['status']='AUTHOR_APPROVED_CURRENT_FIGURE_SUITE'
        u.write(ROOT/row['mirror_file'],open(u.lp(ROOT/row['current_source_file']),'rb').read())
        ix=next(x.copy() for x in index if x['source_path']==row['current_source_file'])
        ix['sha256_or_lfs_oid']=sha;ix['file']=Path(row['mirror_file']).name
        if is_changed:
            ix.update(generator=GENERATOR,source_authority=input_commit,
                notes='Author-approved figure-only NCV14/H2/K3 update; archived formal Stage 7 unchanged.',
                source_data_path=input_path,source_data_sha256=u.digest(source(input_commit,input_path)))
        if stem=='Main/Fig07':
            ix.update(scientific_question='How do the three RQ-defined tract types and modeled deficits vary geographically?',
                main_message='K3, 2299 positive-population tracts; D3 continuous five-policy deficit with frozen Q4 outlines.',
                scientific_content='Eight frozen NCV14/H2 coordinates, saved K3 memberships; no hotspot threshold or new model fit.')
        if stem=='Supplement/FigS09':
            ix.update(scientific_question='What saved selection and robustness evidence supports adopted K3?',
                main_message='Neutral K1-8 curves and K3-only stability/per-class silhouette.',
                scientific_content='No PCA, obsolete cohort, K4 classification or new clustering.')
        records.append(ix);changes.append({'figure':stem,'format':ext,'baseline_sha256':prior,'current_sha256':sha,
            'status':'CHANGED' if is_changed else 'BYTE_IDENTICAL','mirror_file':row['mirror_file']})
        doc.close()
    return updated, records, changes


def finalize_manifest(old_manifest, changes):
    rows=[]
    lookup={(r['figure'],r['format']):r for r in changes}
    for row in old_manifest:
        r=row.copy();stem,ext=r['final_name'].rsplit('.',1);c=lookup[(stem,ext)]
        r['change_in_this_update']='UPDATED' if stem in CHANGED else 'RETAINED'
        r['sha256']=c['current_sha256'];r['mirror_file']=c['mirror_file']
        if stem in CHANGED:
            input_commit,input_path=primary_source(stem)
            d=fitz.open(u.lp(DEST/(stem+'.pdf')));page=d[0]
            spans=[s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
            r.update(parent_source_file=r['current_source_file'],parent_source_commit=BASE,parent_sha256=c['baseline_sha256'],
                source_commit=input_commit, source_file=input_path,
                size_mm=' x '.join(f'{v/MM:.3f}' for v in [page.rect.width,page.rect.height]),
                min_font_pt=f"{min(s['size'] for s in spans):.3f}",status='AUTHOR_APPROVED_CURRENT_FIGURE_SUITE',
                presentation_generator=GENERATOR,presentation_generator_sha256=u.sha(__file__))
        rows.append(r)
    for r in rows:
        r['status']='AUTHOR_APPROVED_CURRENT_FIGURE_SUITE'
    u.write_csv(DEST/'FIGURE_MANIFEST.csv',rows)
    u.write_csv(QA/'FIGURE_CHANGE_MANIFEST.csv',changes)
    u.write_csv(QA/'UNCHANGED_FIGURE_HASH_COMPARISON.csv',[r for r in changes if r['status']=='BYTE_IDENTICAL'])
    return rows


def packets(caps):
    u.pdfmetrics.registerFont(u.TTFont('SuiteArial','C:/Windows/Fonts/arial.ttf'))
    u.pdfmetrics.registerFont(u.TTFont('SuiteBold','C:/Windows/Fonts/arialbd.ttf'))
    books=[fitz.open(),fitz.open(),fitz.open()]
    for stem,(heading,body) in zip(ACTIVE,caps.items()):
        with fitz.open(u.lp(DEST/(stem+'.pdf'))) as fig:
            books[0 if stem.startswith('Main/') else 1].insert_pdf(fig);books[2].insert_pdf(fig)
        cap=u.caption_pdf(heading,body);books[2].insert_pdf(cap);cap.close()
    old=fitz.open(stream=source(BASE,'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),filetype='pdf')
    assert len(old)==38
    books[2].insert_pdf(old,from_page=34,to_page=37)
    for name,book,count in zip(['ALL_MAIN_FIGURES','ALL_SUPPLEMENT_FIGURES','ALL_FIGURES_WITH_CAPTIONS'],books,[7,10,38]):
        assert len(book)==count;u.write(DEST/(name+'.pdf'),book.tobytes(garbage=4,deflate=True));book.close()


def gallery(index):
    u.write_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    cards=[]
    for r in index:
        if r['format'].lower()!='pdf':continue
        png=Path(r['file']).with_suffix('.png').name
        cards.append(f'<section><h2>{html.escape(r["figure_number"])}</h2><a href="{html.escape(r["file"])}"><img src="{html.escape(png)}" alt="{html.escape(r["figure_number"])}"></a><p>{html.escape(r["main_message"])}</p></section>')
    u.write(ROOT/'results/figures/FIGURE_REVIEW_GALLERY.html','<!doctype html><html lang="en"><meta charset="utf-8"><title>Current publication figures</title><style>body{font:16px Arial;margin:30px;color:#222}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:30px}section{border-bottom:1px solid #ddd}img{max-width:100%;max-height:780px}h2{font-size:20px}</style><h1>Current publication figure suite</h1><p>17 numbered figures. NCV14/H2/K3; Figure 7D continuous five-policy deficit. Archived formal Stage 7 unchanged.</p><main>'+''.join(cards)+'</main></html>')


def verify_suite(manifest, before):
    full=fitz.open(u.lp(DEST/'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    comparisons=[]
    for j,stem in enumerate(ACTIVE):
        d=fitz.open(u.lp(DEST/(stem+'.pdf')));p=d[0]
        assert abs(p.rect.width-185*MM)<.15
        assert full[2*j].get_text()==p.get_text() and full[2*j].rect==p.rect
        # Same renderer, actual assembled packet versus authoritative actual figure.
        a=p.get_pixmap(dpi=100,alpha=False);b=full[2*j].get_pixmap(dpi=100,alpha=False)
        assert a.samples==b.samples
        comparisons.append({'figure':stem,'actual_packet_pixels_identical':True,
            'width_mm':p.rect.width/MM,'images':len(p.get_images()),
            'vector_drawings':len(p.get_cdrawings()) if stem in CHANGED else 'Retained exact approved PDF bytes'})
        with Image.open(u.lp(DEST/(stem+'.png'))) as im:
            assert im.width>=4360 and abs(im.width/im.height-p.rect.width/p.rect.height)<.002
        print('Packet/mirror check:',stem,flush=True)
    old=fitz.open(stream=source(BASE,'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),filetype='pdf')
    for j in range(34,38):
        assert full[j].get_text()==old[j].get_text()
        assert full[j].get_pixmap(dpi=100).samples==old[j].get_pixmap(dpi=100).samples
    for r in manifest:
        assert u.sha(ROOT/r['current_source_file'])==u.sha(ROOT/r['mirror_file'])==r['sha256']
    for n in ['FigS02','FigS12','FigS13']:
        assert not (DEST/'Supplement'/(n+'.pdf')).exists()
    after=snapshot();assert before==after
    u.dump(QA/'PRESERVATION_AFTER.json',after)
    u.dump(QA/'COMPLETE_PACKET_AND_MIRROR_QA.json',{'numbered_figures':17,'numbered_pairs':17,
        'packet_pages':{'main':7,'supplement':10,'complete':38},'caption_pages':17,
        'complementary_evidence_pages_retained':4,'all_mirrors_actual_bytes_identical':True,
        'packet_checks':comparisons,'scientific_fits_or_evaluations_run':False})


def build_ncv14_artwork():
    checkpoint=QA/'BUILD_CHECKPOINT.json'
    if checkpoint.exists() and '--rebuild' not in sys.argv:
        q=json_read(checkpoint)
        if q['generator_sha256']==u.sha(__file__) and all(Path(u.lp(ROOT/rel)).exists() and u.sha(ROOT/rel)==h for rel,h in q['output_hashes'].items()):
            assert snapshot()==json_read(QA/'PRESERVATION_BEFORE.json')
            print('Current NCV14/H2/K3 suite already verified; idempotent byte-identical reuse.',flush=True)
            return
    before=snapshot()
    assert before['protected_count']==950
    u.dump(QA/'PRESERVATION_BEFORE.json',before)
    for name in ['THRESHOLD_DISPLAY_VALUES.csv', 'S11_FIG4_NUMERICAL_IDENTITY.csv']:
        rel='docs/reproducibility/author_suite_final_layout_20261012/'+name
        u.write(ROOT/rel,source(BASE,rel))
    manifest=u.csv_rows(source(BASE,'results/figure_review/FIGURE_MANIFEST.csv'))
    index=u.csv_rows(source(BASE,'results/figures/FIGURE_INDEX.csv'))
    caps=u.captions(source(BASE,'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    assert len(manifest)==34 and len(caps)==17
    u.dump(QA/'CURRENT_SUITE_BASELINE.json',{'branch':'review/official-figure-suite-final-s05-20261012','HEAD':BASE,
        'implementation_initial_status':u.git('status','--porcelain').decode(),
        'manifest_sha256':u.digest(source(BASE,'results/figure_review/FIGURE_MANIFEST.csv')),
        'artwork':{r['current_source_file']:r['sha256'] for r in manifest},
        'protected_S05_S11':{r['current_source_file']:r['sha256'] for r in manifest if re.search(r'FigS(?:05|11)\.',r['current_source_file'])}})
    for r in manifest:
        b=source(BASE,r['current_source_file']);assert u.digest(b)==r['sha256']
        u.write(ROOT/r['current_source_file'],b);u.write(ROOT/r['mirror_file'],b)
    for stem in ACTIVE:
        rel='results/figure_review/Page_Previews/'+Path(stem).name+'.png'
        u.write(ROOT/rel,source(BASE,rel))
    f,g,k,stability,sil=prepare_inputs()
    style();figure1();print('Fig01 label changed; all outside-label pixels identical.',flush=True)
    figure7(f,g);print('Fig07 NCV14/H2/K3 and D3 rendered from frozen inputs.',flush=True)
    figure_s9(f,k,stability,sil);print('FigS09 neutral K curves and K3-only evidence rendered.',flush=True)
    caps,index,changes=metadata(caps,manifest,index)
    manifest=finalize_manifest(manifest,changes)
    packets(caps);gallery(index)
    readme=('# Current publication figure suite\n\n17 numbered figures: Main Fig01-Fig07 and Supplement FigS01, FigS03-FigS11. FigS02 remains integrated into S01; S12/S13 remain consolidated into S11.\n\n'
        'The current figure representation is author-approved NCV14/H2/K3 on 2,299 positive-population tracts. Figure 7D displays continuous five-policy mean total service deficit with frozen SOVI Q4 outlines. No K4 classification, hotspot ranking or new model fit is published. Archived formal Stage 7 science and manuscript files are unchanged.\n\n'
        'Canonical build: `python src/la_grid/plotting/build_current_suite_k3.py`. Historical dated builders reproduce historical presentations and are not current entrypoints.\n\n'
        'Run `python -m pytest tests/test_current_figure_suite_integration.py`. Figure-only sources, hashes and checks are in `docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/`. Pinned Git commits and actual LFS payloads are required for a fresh rebuild; fetch instructions are in REPRODUCTION_COMMANDS.md.\n\n'
        'The PDF artwork is native 185 mm wide, with 600 dpi PNG mirrors and publication-size page previews. Complete packet: 38 pages, including 17 figure/caption pairs and four unchanged complementary-evidence pages. Manifest and figure index each contain 34 PDF/PNG rows.\n')
    u.write(DEST/'README.md',readme)
    u.write(ROOT/'results/figures/README.md',readme+'\nArtwork here mirrors the authoritative `results/figure_review/` bytes exactly. Open FIGURE_REVIEW_GALLERY.html for the current gallery.\n')
    oldlog=source(BASE,'results/figure_review/UPDATE_LOG.md').decode()
    u.write(DEST/'UPDATE_LOG.md',oldlog+'\n\n## 2026-10-13 — author-approved NCV14/H2/K3, Figure 7D D3\n\nChanged Fig01 spatial-outcome label, Fig07 and FigS09 only. Fourteen numbered figures including S05 and merged S11 remain byte-identical to 59d9001. Captions, palette, manifest, gallery, mirrors and 38-page packet synchronized. No archived formal Stage 7 science or manuscript modified; no K4 classification adopted. Current builder is build_current_suite_k3.py.\n')
    u.dump(QA/'SOURCE_AUTHORITY_AND_HASHES.json',{'suite_baseline':BASE,'scientific_review':SCIENTIFIC,
        'frozen_K3_authority':FROZEN,'D3_decision_authority':DECISION,'sources':SOURCES})
    verify_suite(manifest,before)
    outputs=[r['current_source_file'] for r in manifest]+[r['mirror_file'] for r in manifest]
    outputs += ['results/figure_review/'+n for n in ['FIGURE_MANIFEST.csv','MANUSCRIPT_FACING_CAPTIONS.md','CURRENT_CLUSTER_PALETTE.json','UPDATE_LOG.md','README.md','ALL_MAIN_FIGURES.pdf','ALL_SUPPLEMENT_FIGURES.pdf','ALL_FIGURES_WITH_CAPTIONS.pdf']]
    outputs += ['results/figures/'+n for n in ['FIGURE_INDEX.csv','FIGURE_REVIEW_GALLERY.html','README.md']]
    outputs += ['results/figure_review/Page_Previews/'+Path(s).name+'.png' for s in ACTIVE]
    u.dump(checkpoint,{'generator_sha256':u.sha(__file__),'output_hashes':{rel:u.sha(ROOT/rel) for rel in outputs}})
    print('17 numbered figures, 38 complete packet pages; 950 scientific files and original Git state preserved.',flush=True)


def main():
    """Replay accepted artwork, changing only the S10 caption and packet page.

    The original NCV14 artwork layer above is retained for historical provenance.
    Current replay never redraws accepted artwork when its generator hash changes.
    """
    checkpoint = QA / 'BUILD_CHECKPOINT.json'
    approved = json.loads(u.payload(ACCEPTED_SUITE, str(checkpoint.relative_to(ROOT)).replace('\\', '/')))
    mutable = {'results/figure_review/' + n for n in [
        'MANUSCRIPT_FACING_CAPTIONS.md', 'ALL_FIGURES_WITH_CAPTIONS.pdf', 'FIGURE_MANIFEST.csv', 'UPDATE_LOG.md']}
    for rel, expected in approved['output_hashes'].items():
        path = ROOT / rel
        if not Path(u.lp(path)).is_file() or open(u.lp(path), 'rb').read(44).startswith(b'version https://git-lfs'):
            data = u.payload(ACCEPTED_SUITE, rel)
            assert u.digest(data) == expected
            u.write(path, data)
        if rel not in mutable:
            assert u.sha(path) == expected, 'Unapproved artwork or metadata change: ' + rel
    caps_rel = 'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md'
    source_text = u.payload(ACCEPTED_SUITE, caps_rel).decode()
    source_caps = u.captions(source_text)
    revised = {h: correct_s10_reference(h, b) for h, b in source_caps.items()}
    assert len(revised) == 17
    current_text = source_text.replace(S10_OLD_REFERENCE, S10_CURRENT_REFERENCE)
    assert u.captions(current_text) == revised
    if checkpoint.exists() and '--rebuild' not in sys.argv:
        q = json_read(checkpoint)
        if (q['generator_sha256'] == u.sha(__file__)
                and all(u.sha(ROOT / p) == h for p, h in q['output_hashes'].items())
                and open(u.lp(ROOT / caps_rel), encoding='utf-8').read() == current_text):
            print('Current S10/S11 caption and accepted 17-figure suite: byte-identical idempotent reuse.', flush=True)
            return
    u.write(ROOT / caps_rel, current_text)
    u.pdfmetrics.registerFont(u.TTFont('SuiteArial', 'C:/Windows/Fonts/arial.ttf'))
    u.pdfmetrics.registerFont(u.TTFont('SuiteBold', 'C:/Windows/Fonts/arialbd.ttf'))
    heading = next(h for h in revised if h.startswith('Supplementary Figure S10.'))
    caption_page = 2 * list(revised).index(heading) + 1
    old = fitz.open(stream=u.payload(ACCEPTED_SUITE, 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'), filetype='pdf')
    assert len(old) == 38 and caption_page == 31
    full = fitz.open()
    full.insert_pdf(old, from_page=0, to_page=caption_page - 1)
    with u.caption_pdf(heading, revised[heading]) as caption:
        full.insert_pdf(caption)
    full.insert_pdf(old, from_page=caption_page + 1, to_page=37)
    assert len(full) == 38
    assert S10_CURRENT_REFERENCE in ' '.join(full[caption_page].get_text().split())
    u.write(DEST / 'ALL_FIGURES_WITH_CAPTIONS.pdf', full.tobytes(garbage=4, deflate=True, no_new_id=True))
    full.close(); old.close()
    manifest = u.csv_rows(u.payload(ACCEPTED_SUITE, 'results/figure_review/FIGURE_MANIFEST.csv'))
    for row in manifest:
        # Refresh generator identity, not artwork provenance or its prior change classification.
        if row['presentation_generator'] == GENERATOR:
            row['presentation_generator_sha256'] = u.sha(__file__)
        assert u.sha(ROOT / row['current_source_file']) == row['sha256'] == u.sha(ROOT / row['mirror_file'])
    u.write_csv(DEST / 'FIGURE_MANIFEST.csv', manifest)
    log = u.payload(ACCEPTED_SUITE, 'results/figure_review/UPDATE_LOG.md').decode()
    u.write(DEST / 'UPDATE_LOG.md', log + '\n\n## 2026-10-13 — S10 active cross-reference correction\n\n'
        'The S10 caption now points to Supplementary Figure S11, which contains the consolidated resource-condition outcomes. '
        'Only this caption and its page 32 in the complete packet changed. All 17 artwork PDF/PNG pairs, mirrors, '
        'other 16 caption pages, four evidence pages, figure-only packets, index, gallery and palette retain their approved bytes. '
        'The canonical builder replays accepted 8f2dcb3 artwork without redrawing; the original artwork layer remains available in source. '
        'Caption-only QA: docs/reproducibility/figure_suite_s10_crossref_fix_20261013/.\n')
    u.dump(checkpoint, {'generator_sha256': u.sha(__file__),
        'output_hashes': {rel: u.sha(ROOT / rel) for rel in approved['output_hashes']}})
    print('S10 reference corrected to S11; 38 pages, 17 accepted artwork pairs unchanged.', flush=True)


if __name__=='__main__':
    main()
