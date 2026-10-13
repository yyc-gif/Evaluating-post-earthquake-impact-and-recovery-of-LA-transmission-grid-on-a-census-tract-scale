"""Isolated Figure 7 layout proposals; no fitting, maps or trajectories computed."""
from pathlib import Path
import io
import json
import re
import sys

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from PIL import Image

INPUTS = HERE / 'inputs'
MM = 72 / 25.4
WARNING = 'LAYOUT PROPOSAL \u2014 NOT APPROVED FOR CURRENT SUITE'
FEATURES = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained',
            'MeanDelta', 'SOVI_SCORE', 'log1p_Population', 'FEMA_NCV14_CA_v119']
A_FEATURES = ['Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained', 'MeanDelta', 'SOVI_SCORE', 'FEMA_NCV14_CA_v119']
COLORS = ['#147f98', '#d07734', '#7a5899']
STYLES = ['-', '--', ':']
CD_CLIP = fitz.Rect(0, 132 * MM, 185 * MM, 245 * MM)


def frame(name):
    return pd.read_csv(u.lp(INPUTS / name), dtype={'tract_id': str}, float_precision='round_trip')


def data():
    f = frame('EIGHT_VARIABLE_FROZEN_TABLE.csv')
    member = frame('K3_CLUSTER_MEMBERSHIP.csv')
    weights = frame('COHORT_STANDARDIZER_AND_WEIGHTS.csv').set_index('variable').loc[FEATURES]
    assert len(f) == len(member) == 2299 and f.tract_id.equals(member.tract_id)
    assert f.tract_id.str.fullmatch(r'\d{11}').all() and f.tract_id.is_unique
    np.testing.assert_array_equal(f.Population, member.Population)
    np.testing.assert_array_equal(f.frozen_SOVI_quartile, member.frozen_SOVI_quartile)
    f['class'] = member.candidate_display_cluster
    assert f.groupby('class').size().tolist() == [1242, 475, 582]
    assert f.groupby('class').Population.sum().tolist() == [5101704, 1897838, 2066980]
    assert f.Population.sum() == 9066522 and (f.Population > 0).all()
    assert f.additional_zero_housing_positive_population.sum() == 8
    full = frame('FULL_2315_COHORT_STATUS.csv')
    assert len(full) == 2315 and full.Frozen_Formal_Population.eq(0).sum() == 16
    palette = json.load(open(u.lp(INPUTS / 'CURRENT_CLUSTER_PALETTE.json'), encoding='utf-8'))
    assert [palette['colors'][str(i)] for i in [1, 2, 3]] == COLORS
    raw = f[FEATURES].to_numpy()
    z = (raw - weights.cohort_mean.to_numpy()) / weights.population_SD.to_numpy()
    saved = np.load(u.lp(INPUTS / 'FROZEN_PREPROCESSING_AND_LABELS.npz'))
    np.testing.assert_array_equal(raw, saved['raw'])
    np.testing.assert_array_equal(f.tract_id.to_numpy(), saved['tract_ids'])
    np.testing.assert_array_equal(member.saved_model_class, saved['K3_labels'])
    np.testing.assert_allclose(raw.mean(0), weights.cohort_mean, atol=1e-12, rtol=1e-14)
    np.testing.assert_allclose(raw.std(0), weights.population_SD, atol=1e-12, rtol=1e-14)
    np.testing.assert_allclose(z * np.sqrt(weights.squared_distance_budget.to_numpy()), saved['weighted_matrix'], atol=1e-12, rtol=1e-13)
    policies = frame('FROZEN_POLICY_TRACT_MEANS_2315.csv').set_index('tract_id').loc[f.tract_id]
    scheduled = ['B_' + name for name in ['impact-first', 'hospital-first', 'degree-first', 'betweenness-first', 'vulnerability-first']]
    np.testing.assert_allclose(f.B_Unconstrained, policies.B_unconstrained, atol=1e-12, rtol=0)
    np.testing.assert_allclose(f.MeanDelta, policies.MeanDelta5, atol=1e-12, rtol=0)
    total = f.B_Unconstrained + f.MeanDelta
    np.testing.assert_allclose(total, policies[scheduled].mean(axis=1), atol=1e-12, rtol=0)
    np.testing.assert_array_equal(f.frozen_SOVI_quartile, policies.frozen_SOVI_quartile)
    means = np.vstack([z[f['class'].eq(c)].mean(0) for c in [1, 2, 3]])
    counts = f.groupby('class').size().to_numpy()
    budget = weights.squared_distance_budget.to_numpy()
    between = budget * (counts[:, None] * means ** 2).sum(0)
    rows = []
    for c in [1, 2, 3]:
        take = f['class'].eq(c)
        for j, feature in enumerate(FEATURES):
            v = f.loc[take, feature].to_numpy()
            rows.append({'class': 'C' + str(c), 'variable': feature, 'domain': weights.loc[feature, 'domain'],
                'n': int(take.sum()), 'class_population': int(f.loc[take, 'Population'].sum()),
                'raw_mean': float(v.mean()), 'raw_median': float(np.median(v)),
                'p10': float(np.quantile(v, .1)), 'p90': float(np.quantile(v, .9)),
                'minimum': float(v.min()), 'maximum': float(v.max()), 'exact_zero_count': int((v == 0).sum()),
                'positive_count': int((v > 0).sum()), 'cohort_mean': float(weights.loc[feature, 'cohort_mean']),
                'cohort_population_SD': float(weights.loc[feature, 'population_SD']),
                'ordinary_z_class_mean': float(means[c - 1, j]),
                'sqrt_budget_weighted_class_mean': float(means[c - 1, j] * np.sqrt(budget[j])),
                'squared_distance_budget': float(budget[j]),
                'weighted_between_SS_coordinate': float(between[j]),
                'between_SS_share_pct': float(100 * between[j] / between.sum()),
                'A_distribution': feature in A_FEATURES,
                'Population_original_unit_mean_persons': float(f.loc[take, 'Population'].mean()) if feature == 'log1p_Population' else ''})
    u.write_csv(HERE / 'FIGURE7_ORIGINAL_UNIT_AND_STANDARDIZED_DATA_QA.csv', rows)
    plot = f[['tract_id', 'class', 'Population', 'frozen_SOVI_quartile',
              'additional_zero_housing_positive_population', *FEATURES]].copy()
    plot['MeanTotalDeficit_5'] = total
    for j, feature in enumerate(FEATURES):
        plot['z_' + feature] = z[:, j]
    u.write(HERE / 'PLOTTED_FROZEN_VALUES.csv', plot.to_csv(index=False, lineterminator='\n'))
    u.dump(HERE / 'NUMERICAL_STORY_QA.json', {'tracts': 2299, 'study_domain': 2315, 'N_A_zero_population': 16,
        'class_counts': counts.tolist(), 'class_population': f.groupby('class').Population.sum().tolist(),
        'represented_population': int(f.Population.sum()), 'positive_population_zero_housing_included': 8,
        'ordinary_z_class_means': means.tolist(), 'features': FEATURES, 'A_features': A_FEATURES,
        'Init_exact_zero_count': int(f.Init_Supply.eq(0).sum()), 'Init_exact_zero_fraction': float(f.Init_Supply.eq(0).mean()),
        'Init_maximum': float(f.Init_Supply.max()), 'Init_class_medians': f.groupby('class').Init_Supply.median().tolist(),
        'class_feature_means': f.groupby('class')[FEATURES].mean().to_dict(),
        'weighted_between_SS_coordinate': between.tolist(), 'total_weighted_between_SS': float(between.sum()),
        'original_Q4_count': int(f.frozen_SOVI_quartile.eq('Q4').sum()),
        'maximum_D3_identity_error_h': float(abs(total.to_numpy() - policies[scheduled].mean(axis=1).to_numpy()).max()),
        'classification_recomputed': False, 'physical_recovery_recomputed': False})
    return f, means


def text(doc, x, y, value, size=8, bold=False):
    page = doc[0]
    name = 'LayoutBold' if bold else 'LayoutArial'
    font = 'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf'
    page.insert_font(fontname=name, fontfile=font)
    page.insert_text((x * MM, y * MM), value, fontsize=size, fontname=name)


def export(doc, name, dpi=160):
    u.write(HERE / (name + '.pdf'), doc.tobytes(garbage=4, deflate=True, no_new_id=True))
    for i, page in enumerate(doc):
        suffix = '' if len(doc) == 1 else '_PAGE' + str(i + 1)
        page.get_pixmap(dpi=dpi, alpha=False).save(u.lp(HERE / (name + suffix + '.png')))


def candidate(f, means):
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 8, 'axes.labelsize': 8,
        'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5, 'axes.spines.top': False,
        'axes.spines.right': False, 'pdf.fonttype': 42, 'axes.linewidth': .6})
    width, height = 185, 253
    fig = plt.figure(figsize=(width / 25.4, height / 25.4))
    ft = lambda x, y, s, **kw: fig.text(x / width, 1 - y / height, s, **kw)
    ft(5, 4.8, WARNING, fontsize=7.5, color='#595959')
    ft(5, 11, 'A. Feature distributions across the saved K3 classes', fontsize=9.5, weight='bold')
    handles = [Line2D([0], [0], color=color, ls=style, lw=1.3,
                     label=f'C{c} (n={n:,})') for c, n, color, style in zip([1, 2, 3], [1242, 475, 582], COLORS, STYLES)]
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(5 / width, 1 - 14 / height),
               ncol=3, frameon=False, fontsize=8, columnspacing=2.4, handlelength=2.0, borderaxespad=0)
    titles = ['RQ1: Spectral grid impact', 'RQ1: Dependency concentration',
              'RQ2: Unconstrained deficit', 'RQ2: Constraint increment',
              'RQ3: Social vulnerability', 'RQ3: Natural-hazard screen']
    labels = ['Grid impact (unitless)', 'HHI (unitless)',
              'Equivalent deficit hours', 'Five-policy mean increment (h)',
              'SOVI score (0-100)', 'NCV14 screening index (unitless)']
    limits = [(0, 1), (0, 1), (19, 44), (0, 20), (0, 100), (.3, 1)]
    ecdf_rows = []
    for j, feature in enumerate(A_FEATURES):
        row, col = divmod(j, 3)
        x, top, w, h = 17 + col * 59, 28 + row * 37, 42, 23
        ax = fig.add_axes([x / width, 1 - (top + h) / height, w / width, h / height])
        lo, hi = limits[j]
        for c, color, line in zip([1, 2, 3], COLORS, STYLES):
            values = f.loc[f['class'].eq(c), feature].to_numpy()
            assert values.min() >= lo - 1e-12 and values.max() <= hi + 1e-12, (feature, values.min(), values.max())
            unique, n = np.unique(values, return_counts=True)
            cumulative = np.cumsum(n) / len(values)
            ecdf_rows.extend({'variable': feature, 'class': 'C' + str(c), 'class_n': len(values),
                'value': float(v), 'value_count': int(count), 'cumulative_fraction': float(cf)}
                for v, count, cf in zip(unique, n, cumulative))
            ax.step(np.r_[lo, unique, hi], np.r_[0, cumulative, 1], where='post',
                    color=color, ls=line, lw=1.1)
            ax.plot(np.median(values), .5, 'o', color=color, ms=3)
        ax.axhline(.5, color='#a9a9a9', lw=.5, zorder=0)
        ax.set_xlim(lo, hi); ax.set_ylim(0, 1.03)
        ax.set_yticks([0, .5, 1]); ax.locator_params(axis='x', nbins=3)
        ax.set_title(titles[j], fontsize=8.5, pad=3)
        ax.set_xlabel(labels[j], fontsize=7.5, labelpad=2)
        if col == 0:
            ax.set_ylabel('Cumulative fraction', fontsize=7.5, labelpad=2)
        ax.tick_params(length=2.2, pad=1.5)
    ft(5, 97, 'Exact empirical CDFs; dots locate class medians on the 50% guide. No smoothing or trimming.', fontsize=7.5)
    ft(5, 103, 'B. Standardized eight-coordinate class profiles', fontsize=9.5, weight='bold')
    ft(5, 108, 'Unweighted z means; zero = 2,299-tract mean.', fontsize=7.5)
    ax = fig.add_axes([74 / width, 1 - 139 / height, 66 / width, 28 / height])
    maximum = np.ceil(abs(means).max() * 10) / 10
    im = ax.pcolormesh(np.arange(4) - .5, np.arange(9) - .5, means.T,
                      cmap='RdBu_r', vmin=-maximum, vmax=maximum, shading='flat', rasterized=False)
    ax.set_xlim(-.5, 2.5); ax.set_ylim(7.5, -.5)
    ax.set_xticks([0, 1, 2], ['C1', 'C2', 'C3']); ax.xaxis.tick_top()
    for label, color in zip(ax.get_xticklabels(), COLORS):
        label.set_color(color); label.set_weight('bold'); label.set_fontsize(8)
    display = ['Initial service', 'Spectral grid impact', 'Dependency HHI', 'Unconstrained deficit',
               'Constraint increment', 'SOVI score', 'log1p(Population)', 'NCV14 screening index']
    ax.set_yticks(range(8), display); ax.tick_params(axis='y', labelsize=7.5, length=0, pad=4)
    ax.tick_params(axis='x', length=0, pad=2)
    for split in [2.5, 4.5]:
        ax.axhline(split, color='white', lw=1.0)
    for j in range(8):
        for c in range(3):
            ax.text(c, j, f'{means[c, j]:+.2f}', ha='center', va='center', fontsize=7.5,
                    color='white' if abs(means[c, j]) > .8 * maximum else '#202020')
    for top, bottom, label in [(111, 121.5, 'RQ1'), (121.5, 128.5, 'RQ2'), (128.5, 139, 'RQ3')]:
        ft(7, (top + bottom) / 2 + .8, label, fontsize=8, weight='bold')
    cb = fig.colorbar(im, cax=fig.add_axes([151 / width, 1 - 139 / height, 3 / width, 28 / height]))
    cb.solids.set_rasterized(False)
    cb.set_ticks([-1, 0, 1]); cb.ax.tick_params(labelsize=7.5, length=2, pad=2)
    cb.set_label('Class-mean z-score', fontsize=7.5, labelpad=3)
    out = io.BytesIO()
    fig.savefig(out, format='pdf', metadata={'CreationDate': None, 'ModDate': None,
        'Subject': WARNING, 'Creator': 'Isolated Figure 7 layout review; frozen data, no fits'})
    plt.close(fig)
    doc = fitz.open(stream=out.getvalue(), filetype='pdf')
    with fitz.open(u.lp(INPUTS / 'CURRENT_FIGURE7.pdf')) as current:
        locked_clip = fitz.Rect(0, 132 * MM, current[0].rect.width, current[0].rect.height)
        target = locked_clip + (0, 8 * MM, 0, 8 * MM)
        doc[0].show_pdf_page(target, current, 0, clip=locked_clip, keep_proportion=False)
    export(doc, 'FIGURE7_CONSERVATIVE_RESTORATION', dpi=600)
    doc[0].get_pixmap(dpi=160, alpha=False).save(u.lp(HERE / 'FIGURE7_CONSERVATIVE_RESTORATION_NATIVE_PREVIEW.png'))
    doc.close()
    u.write_csv(HERE / 'A_EMPIRICAL_DISTRIBUTION_POINTS.csv', ecdf_rows)


def comparisons():
    paths = ['HISTORICAL_FIGURE7.pdf', 'CURRENT_FIGURE7.pdf']
    documents = [fitz.open(u.lp(INPUTS / n)) for n in paths]
    documents.append(fitz.open(u.lp(HERE / 'FIGURE7_CONSERVATIVE_RESTORATION.pdf')))
    labels = ['Historical 59d9001: reference only', 'Current 8f2dcb3: reference only', 'Candidate A: conservative restoration']
    full = fitz.open(); page = full.new_page(width=575 * MM, height=275 * MM)
    text(full, 5, 5, WARNING, 9, True)
    for j, (d, label) in enumerate(zip(documents, labels)):
        x = 5 + j * 190
        text(full, x, 12, label, 9, True)
        target = fitz.Rect(x * MM, 18 * MM, (x + 185) * MM, (18 + d[0].rect.height / MM) * MM)
        page.show_pdf_page(target, d, 0, keep_proportion=False)
    export(full, 'FIGURE7_OLD_CURRENT_CANDIDATE_NATIVE_COMPARISON')
    full.close()
    comparison = fitz.open()
    clips = [[(0, 96), (0, 47), (0, 99)], [(96, 166), (47, 131), (99, 140)]]
    for label, row in zip(['A: within-class distributions versus representation only', 'B: common-scale profiles versus independently scaled means'], clips):
        scale = 240 / 185
        page = comparison.new_page(width=740 * MM, height=158 * MM)
        page.insert_font(fontname='LayoutBold', fontfile='C:/Windows/Fonts/arialbd.ttf')
        page.insert_text((5 * MM, 5 * MM), WARNING, fontname='LayoutBold', fontsize=9)
        page.insert_text((5 * MM, 11 * MM), label, fontname='LayoutBold', fontsize=9)
        page.insert_text((5 * MM, 16 * MM), 'All crops enlarged equally to 240 mm (1.297 times native width).', fontname='LayoutBold', fontsize=8)
        for j, (d, lab, (top, bottom)) in enumerate(zip(documents, labels, row)):
            x = 5 + 245 * j
            page.insert_text((x * MM, 23 * MM), lab, fontname='LayoutBold', fontsize=9)
            page.show_pdf_page(fitz.Rect(x * MM, 28 * MM, (x + 240) * MM, (28 + (bottom - top) * scale) * MM),
                               d, 0, clip=fitz.Rect(0, top * MM, 185 * MM, bottom * MM), keep_proportion=False)
    export(comparison, 'FIGURE7_AB_PANEL_SIDE_BY_SIDE_REVIEW')
    comparison.close()
    for d in documents:
        d.close()


def na_comparison():
    original = fitz.open(u.lp(INPUTS / 'CURRENT_FIGURE7.pdf'))
    alternate = fitz.open(u.lp(INPUTS / 'CURRENT_FIGURE7.pdf'))
    rgb = re.compile(rb'([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s+rg\b')
    gray = re.compile(rb'([-+0-9.]+)\s+g\b')
    count = 0
    xrefs = set(alternate[0].get_contents())
    xrefs |= {x for x in range(1, alternate.xref_length()) if alternate.xref_is_stream(x) and alternate.xref_get_key(x, 'Subtype')[1] == '/Form'}
    for xref in xrefs:
        def replace(m):
            nonlocal count
            values = [float(m[i]) for i in [1, 2, 3]]
            if max(abs(v - 229 / 255) for v in values) < 1e-7:
                count += 1
                return b'1 1 1 rg'
            return m.group(0)
        stream = alternate.xref_stream(xref)
        revised = rgb.sub(replace, stream)
        def replace_gray(m):
            nonlocal count
            if abs(float(m[1]) - 229 / 255) < 1e-7:
                count += 1
                return b'1 g'
            return m.group(0)
        revised = gray.sub(replace_gray, revised)
        if stream != revised:
            alternate.update_stream(xref, revised)
    assert count > 0
    old, new = original[0].get_cdrawings(), alternate[0].get_cdrawings()
    assert len(old) == len(new)
    changed = 0
    for a, b in zip(old, new):
        if a != b:
            # MuPDF converts DeviceGray to RGB with a small color-management offset.
            assert a.get('fill') is not None and max(abs(v - 229 / 255) for v in a['fill']) < 2e-4
            assert b['fill'] == (1, 1, 1)
            a = {**a, 'fill': b['fill']}
            assert a == b
            changed += 1
    doc = fitz.open(); page = doc.new_page(width=385 * MM, height=137 * MM)
    text(doc, 5, 5, WARNING, 9, True)
    text(doc, 5, 12, 'Separate N/A-only comparison; not applied to Candidate A or official maps', 9)
    for j, (d, lab) in enumerate([(original, 'Current gray N/A; retained in Candidate A'), (alternate, 'White N/A alternative; existing dark outlines retained')]):
        x = 5 + j * 190
        text(doc, x, 20, lab, 9, True)
        page.show_pdf_page(fitz.Rect(x * MM, 23 * MM, (x + 185) * MM, 136 * MM), d, 0, clip=CD_CLIP, keep_proportion=False)
    export(doc, 'FIGURE7_NA_FILL_SEPARATE_APPROVAL_COMPARISON')
    u.dump(HERE / 'NA_FILL_COMPARISON_QA.json', {'fill_only_comparison': True, 'official_or_candidate_changed': False,
        'gray_rgb': [229 / 255] * 3, 'white_rgb': [1, 1, 1], 'changed_paint_operators': count,
        'changed_vector_drawings': changed, 'all_other_vector_properties_identical': True,
        'no_membership_geometry_or_Q4_change': True})
    original.close(); alternate.close(); doc.close()


if __name__ == '__main__':
    f, means = data()
    candidate(f, means)
    comparisons()
    na_comparison()
    print('Four isolated review PDFs created. Candidate B not generated; official suite untouched.', flush=True)
