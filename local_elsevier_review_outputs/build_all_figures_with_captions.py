"""Local Path B packet from checked captions and frozen P2 results; no fits."""
import io
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

os.environ['MPLBACKEND'] = 'Agg'
import fitz
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from sklearn.metrics import silhouette_samples

import build_local_review as local

a = local.a
u = a.u
OUT = local.OUT
ROOT = local.ROOT
PB = local.PB
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import short_current_captions_20261013 as short

PACKET = OUT / 'ALL_FIGURES_WITH_CAPTIONS.pdf'
S8 = OUT / 'FigS08_P2_K3_K4_Saved_Diagnostics.pdf'
DOCX = OUT / 'Path_B_Figure_Captions_Checked.docx'
OFFICIAL = ROOT / 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'


def captions():
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(u.lp(DOCX)) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    paragraphs = [''.join(p.itertext()).strip() for p in root.findall('.//w:p', ns)]
    entries = []
    for i, title in enumerate(paragraphs):
        match = re.match(r'^(Figure ([1-7])|Supplementary Figure S(\d+))\.', title)
        if match:
            key = ('Fig' + match[2].zfill(2)) if match[2] else ('FigS' + match[3].zfill(2))
            body = paragraphs[i + 1]
            assert body and not body.startswith('Figure ')
            entries.append((key, title, body))
    assert [x[0] for x in entries] == [f'Fig{i:02d}' for i in range(1, 8)] + [f'FigS{i:02d}' for i in range(1, 11)]
    return entries


def saved_diagnostics():
    registry = pd.read_csv(u.lp(PB / 'SOURCE_PAYLOAD_HASHES.csv'))
    for name in ['REGISTERED_FIT_ARRAYS.npz', 'VERIFIED_WEIGHTED_MATRICES.npz']:
        row = registry.loc[registry.archived_path.eq('inputs/' + name)].iloc[0]
        assert u.sha(PB / 'inputs' / name) == row.sha256
    z = np.load(u.lp(PB / 'inputs/REGISTERED_FIT_ARRAYS.npz'))
    w = np.load(u.lp(PB / 'inputs/VERIFIED_WEIGHTED_MATRICES.npz'))
    eligible = a.load_frozen().query('Population > 0')
    ids = z['tract_ids'].astype(str)
    assert all(len(x) == 11 for x in ids)
    assert np.array_equal(ids, eligible.index.to_numpy())
    assert np.array_equal(ids, w['tract_ids'].astype(str))
    index = list(z['keys']).index('P2__main5__cohort__k3__s42')
    labels = z['labels'][index]
    sil = z['silhouette'][index]
    np.testing.assert_array_equal(labels + 1, eligible.P2_K3_class.to_numpy())
    np.testing.assert_allclose(silhouette_samples(w['P2__main5__cohort'], labels), sil, atol=2e-12, rtol=0)
    evidence = pd.read_csv(u.lp(PB / 'P2_REGISTERED_K_EVIDENCE.csv'))
    seed42 = evidence.query('k == 3 and seed == 42').iloc[0]
    np.testing.assert_allclose(sil.mean(), seed42.mean_silhouette, atol=2e-12, rtol=0)
    assert len(eligible) == 2299 and eligible.Population.sum() == 9066522
    assert eligible.P2_K3_class.value_counts().sort_index().tolist() == [1235, 428, 636]
    stability = {
        'Initialization': pd.read_csv(u.lp(PB / 'P2_SEED_STABILITY.csv')),
        'Geographic leave-out': pd.read_csv(u.lp(PB / 'P2_SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv')),
        'Policy leave-one-out': pd.read_csv(u.lp(PB / 'P2_POLICY_SET_CLUSTER_STABILITY.csv')),
    }
    qa = dict(cohort_tracts=2299, population=9066522, K3_counts=[1235, 428, 636],
              frozen_label_identity=True, full_cohort_silhouette_recomputed=True,
              silhouette_mean=float(sil.mean()), no_fitting=True,
              feature_space='P2 seven-variable weighted standardized Euclidean',
              input_hashes={name: u.sha(PB / name) for name in [
                  'inputs/REGISTERED_FIT_ARRAYS.npz', 'inputs/VERIFIED_WEIGHTED_MATRICES.npz',
                  'P2_REGISTERED_K_EVIDENCE.csv', 'P2_SEED_STABILITY.csv',
                  'P2_SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv', 'P2_POLICY_SET_CLUSTER_STABILITY.csv']})
    return eligible, labels, sil, evidence, stability, qa


def make_s8():
    eligible, labels, sil, evidence, stability, qa = saved_diagnostics()
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 8.5, 'axes.labelsize': 8.5,
                         'axes.titlesize': 9, 'xtick.labelsize': 8, 'ytick.labelsize': 8,
                         'legend.fontsize': 7.5, 'pdf.fonttype': 42, 'ps.fonttype': 42,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.2))
    fig.subplots_adjust(left=.085, right=.97, bottom=.105, top=.92, wspace=.32, hspace=.55)
    summary = evidence.groupby('k').agg(inertia=('WCSS', 'mean'),
                                      silhouette=('mean_silhouette', 'mean'))
    for ax, col, title, ylabel in [
        (axes[0, 0], 'inertia', 'A  Within-cluster variation', 'Weighted-space inertia'),
        (axes[0, 1], 'silhouette', 'B  Cluster separation', 'Full-cohort mean silhouette')]:
        part = summary if col == 'inertia' else summary.loc[2:]
        for seed, group in evidence.groupby('seed'):
            group = group if col == 'inertia' else group.query('k >= 2')
            ax.plot(group.k, group.WCSS if col == 'inertia' else group.mean_silhouette,
                    color='#b4b4b4', lw=.65, alpha=.7)
        ax.plot(part.index, part[col], color='#404040', marker='o', ms=3.5, lw=1)
        ax.scatter([3], [part.loc[3, col]], color=a.COLORS[0], s=32, zorder=4, label='K3 primary')
        ax.scatter([4], [part.loc[4, col]], facecolor='white', edgecolor='#444444', s=32,
                   zorder=4, label='K4 sensitivity')
        ax.set(title=title, xlabel='Number of classes (K)', ylabel=ylabel)
        ax.set_xticks(part.index)
        ax.grid(axis='y', alpha=.15)
    axes[0, 0].legend(frameon=False, loc='upper right')
    axes[0, 1].text(.03, .04, 'Thin curves: saved seeds 42-46', transform=axes[0, 1].transAxes, fontsize=7.5)

    ax = axes[1, 0]
    values_for_qa = []
    for ki, (k, color, marker) in enumerate([(3, a.COLORS[0], 'o'), (4, '#555555', 's')]):
        for j, (name, frame) in enumerate(stability.items()):
            subset = frame.loc[frame.k.eq(k)]
            if name == 'Geographic leave-out':
                values = subset.held_out_ARI.to_numpy()
            elif name == 'Policy leave-one-out':
                subset = subset.loc[subset.scaling.eq('cohort') & subset.seed.eq(42)
                                    & subset.policy_set.str.startswith('without_')]
                values = subset.ARI.to_numpy()
            else:
                values = subset.ARI.to_numpy()
            assert len(values) == {'Initialization': 10, 'Geographic leave-out': 4,
                                   'Policy leave-one-out': 5}[name]
            pos = j + (-.12 if k == 3 else .12)
            ax.plot([pos, pos], [values.min(), values.max()], color=color, lw=1.6)
            ax.scatter(np.full(len(values), pos) + np.linspace(-.035, .035, len(values)),
                       values, color=color, s=12, marker=marker,
                       label=f'K{k}' if j == 0 else None, zorder=3)
            values_for_qa.append(dict(k=k, check=name, values=values.tolist()))
    ax.set(title='C  Saved partition agreement', ylabel='Adjusted Rand index', ylim=(.3, 1.025))
    ax.set_xticks([0, 1, 2], ['Seeds', 'Geographic\nheld-out tracts', 'Policy-set\nleave-one-out'])
    ax.grid(axis='y', alpha=.15)
    ax.legend(frameon=False, loc='lower left')
    ax = axes[1, 1]
    for c, color in enumerate(a.COLORS):
        values = np.sort(sil[labels == c])
        ax.step(values, np.arange(1, len(values) + 1) / len(values), where='post',
                color=color, lw=1.2, label=f'C{c + 1}')
    ax.axvline(0, color='#777777', lw=.65, ls='--')
    ax.set(title='D  K3 within-class separation', xlabel='Tract silhouette',
           ylabel='Empirical cumulative fraction', ylim=(0, 1))
    ax.legend(frameon=False, loc='upper left')
    fig.suptitle('P2 seven-variable typology: saved selection and sensitivity evidence',
                 fontsize=10, x=.52, y=.98)
    fig.text(.085, .025, 'Agreement comparisons are descriptive internal diagnostics, not independent physical validation.',
             fontsize=7.5)
    buffer = io.BytesIO()
    fig.savefig(buffer, format='pdf', metadata={'CreationDate': None, 'ModDate': None,
                                               'Creator': 'Frozen P2 local review packet'})
    u.write(S8, buffer.getvalue())
    fig.savefig(u.lp(S8.with_suffix('.png')), dpi=600)
    plt.close(fig)
    qa['stability_values'] = values_for_qa
    qa['K4_is_sensitivity_only'] = True
    qa['no_NCV14_coordinate'] = True
    local.dump('PACKET_P2_S8_NUMERICAL_QA.json', qa)


def make_packet():
    u.pdfmetrics.registerFont(u.TTFont('SuiteArial', 'C:/Windows/Fonts/arial.ttf'))
    u.pdfmetrics.registerFont(u.TTFont('SuiteBold', 'C:/Windows/Fonts/arialbd.ttf'))
    entries = captions()
    book = fitz.open()
    rows = []
    for index, (key, title, body) in enumerate(entries):
        if key == 'Fig07':
            path = OUT / 'FIG07_P2_K3_B_COLOR_NO_REVIEW_BANNER.pdf'
        elif key == 'FigS08':
            path = S8
        else:
            folder = 'Supplement' if key.startswith('FigS') else 'Main'
            path = ROOT / 'results/figure_review' / folder / (key + '.pdf')
        with fitz.open(u.lp(path)) as art:
            assert len(art) == 1
            width, height = art[0].rect.width, art[0].rect.height
            with short.brief_caption_page(title, body, width) as cap:
                page = book.new_page(width=width, height=height + cap[0].rect.height)
                page.show_pdf_page(fitz.Rect(0, 0, width, height), art, 0)
                page.show_pdf_page(fitz.Rect(0, height, width, page.rect.height), cap, 0)
            rows.append(dict(page=index + 1, figure=key, artwork=str(path),
                             artwork_sha256=u.sha(path), artwork_height_pt=height,
                             title=title, caption=body, caption_words=len(body.split()),
                             local_replacement=key in ['Fig07', 'FigS08']))
    with fitz.open(u.lp(OFFICIAL)) as previous:
        assert len(previous) == 21
        book.insert_pdf(previous, from_page=17, to_page=20)
    assert len(book) == 21
    book.set_metadata({'title': 'Path B local figures with concise captions',
                       'subject': 'Local review only; P2/K3 primary, K4 sensitivity; no formal promotion',
                       'creator': 'build_all_figures_with_captions.py'})
    u.write(PACKET, book.tobytes(garbage=4, deflate=True, no_new_id=True))
    book.close()
    u.write_csv(OUT / 'ALL_FIGURES_LOCAL_PAGE_REGISTRY.csv', rows)
    return rows


def verify_packet(rows):
    results = []
    with fitz.open(u.lp(PACKET)) as book, fitz.open(u.lp(OFFICIAL)) as old:
        assert len(book) == 21
        for i, row in enumerate(rows):
            with fitz.open(u.lp(row['artwork'])) as art:
                p = book[i]
                rect = art[0].rect
                source = art[0].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
                packed = p.get_pixmap(matrix=fitz.Matrix(1, 1), clip=rect, alpha=False)
                assert source.samples == packed.samples, row['figure']
                caprect = fitz.Rect(0, rect.height, p.rect.width, p.rect.height)
                text = p.get_text(clip=caprect)
                normalize = lambda s: re.sub(r'\s+', '', s)
                assert normalize(row['title']) in normalize(text), row['figure']
                assert normalize(row['caption']) in normalize(text), row['figure']
                spans = [s for b in p.get_text('dict', clip=caprect)['blocks'] if 'lines' in b
                         for line in b['lines'] for s in line['spans']]
                assert min(s['size'] for s in spans) >= 9.99
                assert all(fitz.Rect(s['bbox']).y1 <= p.rect.height for s in spans)
                results.append(dict(figure=row['figure'], embedded_artwork_pixel_identity=True,
                                    checked_docx_caption_identity=True, caption_min_font_pt=10))
        for i in range(17, 21):
            assert book[i].get_pixmap().samples == old[i].get_pixmap().samples
        for i in [6, 14]:
            book[i].get_pixmap(dpi=150).save(u.lp(OUT / f'packet_previews/Page_{i+1:02d}.png'))
        thumbs = []
        for i, page in enumerate(book):
            pix = page.get_pixmap(dpi=45)
            im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            im.thumbnail((245, 330))
            tile = Image.new('RGB', (265, 360), 'white')
            tile.paste(im, ((265-im.width)//2, 22))
            ImageDraw.Draw(tile).text((8, 4), f'Page {i+1}', fill='black')
            thumbs.append(tile)
        contact = Image.new('RGB', (7*265, 3*360), '#dddddd')
        for i, im in enumerate(thumbs):
            contact.paste(im, ((i % 7)*265, (i // 7)*360))
        contact.save(u.lp(OUT / 'packet_previews/ALL_21_PAGES.png'))
    with fitz.open(u.lp(S8)) as s8:
        assert not s8[0].get_images()
        fonts = s8[0].get_fonts()
        assert all(len(s8.extract_font(f[0])[3]) > 0 for f in fonts)
        minfont = min(s['size'] for b in s8[0].get_text('dict')['blocks'] if 'lines' in b
                      for line in b['lines'] for s in line['spans'])
        assert minfont >= 7.49
    local.dump('ALL_FIGURES_PACKET_QA.json', dict(
        scope='Local Elsevier review packet only; official tracked suite untouched',
        numbered_figures=17, total_pages=21, complementary_evidence_pages=4,
        concise_caption_pages_combined_with_artwork=True,
        local_replacement_figures=['Fig07', 'FigS08'], unaffected_artworks=15,
        original_official_packet_sha256=u.sha(OFFICIAL), output_packet_sha256=u.sha(PACKET),
        caption_docx_sha256=u.sha(DOCX), P2_S8_sha256=u.sha(S8),
        four_evidence_pages_render_identical=True, figure_and_caption_checks=results,
        S8_vector_only=True, S8_all_fonts_embedded=True, S8_min_font_pt=float(minfont)))


def main():
    previous = {str(p.relative_to(OUT)): u.sha(p) for p in [PACKET, S8, S8.with_suffix('.png')]
                if Path(u.lp(p)).is_file()}
    for folder in ['packet_previews']:
        Path(u.lp(OUT / folder)).mkdir(exist_ok=True)
    make_s8()
    rows = make_packet()
    verify_packet(rows)
    if previous:
        after = {name: u.sha(OUT / name) for name in previous}
        assert previous == after, 'Packet rebuild changed bytes without a source change'
        local.dump('ALL_FIGURES_BUILD_IDEMPOTENCE.json', dict(
            rebuilt_from_sources=True, all_pdf_and_png_bytes_identical=True, before=previous, after=after))
    print(json.dumps({'packet': str(PACKET), 'pages': 21, 'figures': 17,
                      'sha256': u.sha(PACKET), 'official_packet_untouched': True}))


if __name__ == '__main__':
    main()
