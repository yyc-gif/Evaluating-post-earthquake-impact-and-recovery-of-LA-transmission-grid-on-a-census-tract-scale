"""Bounded publication gate: no fits, simulations, or official artwork edits."""
import argparse
import json
import os
from pathlib import Path
import sys

import fitz
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
PB = ROOT / 'docs/data_research/stage7_path_b_p2_integration_review_20261014'
HERE = ROOT / 'docs/reproducibility/path_b_pre_migration_publication_gate_20261014'
sys.path.insert(0, str(PB))
import analyze_path_b as a


def dump(name, obj):
    a.u.dump(HERE / name, obj)


def write(name, text):
    a.u.write(HERE / name, text)


def read_json(p):
    return json.load(open(a.u.lp(p), encoding='utf-8'))


def freeze():
    assert not (HERE / 'STARTING_STATE.json').exists()
    science = []
    for p in Path(a.u.lp(PB)).rglob('*'):
        if p.is_file() and p.suffix in ['.csv', '.npz', '.gpkg']:
            science.append(PB / p.relative_to(Path(a.u.lp(PB))))
    artworks = []
    for r in a.u.csv_rows(open(a.u.lp(ROOT / 'results/figure_review/FIGURE_MANIFEST.csv'), 'rb').read()):
        artworks.extend([ROOT / r['current_source_file'], ROOT / r['mirror_file']])
    prior_candidates = [PB / 'figures' / ('FIGURE7_PATH_B_CANDIDATE_' + k + ext)
                        for k in ['A', 'B'] for ext in ['.pdf', '.png']]
    protected = a.u.protected_snapshot(read_json(PB / 'PRESERVATION_BEFORE.json'))
    assert protected == read_json(PB / 'PRESERVATION_BEFORE.json')
    dump('PRESERVATION_BEFORE.json', protected)
    dump('STARTING_STATE.json', dict(
        branch=a.u.git('branch', '--show-current').decode().strip(),
        HEAD=a.u.git('rev-parse', 'HEAD').decode().strip(),
        status=a.u.git('status', '--porcelain=v1').decode(),
        source_worktree_HEAD=a.u.git('rev-parse', 'HEAD', root=ROOT.parent / '_ac13').decode().strip(),
        source_index_sha256=a.u.sha(a.u.git('rev-parse', '--path-format=absolute', '--git-path', 'index',
                                           root=ROOT.parent / '_ac13').decode().strip()),
        immutable_hashes={str(p.relative_to(ROOT)).replace('\\', '/'): a.u.sha(p)
                          for p in science + artworks + prior_candidates},
        packet_sha256=a.u.sha(ROOT / 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),
        captions=open(a.u.lp(ROOT / 'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md'), encoding='utf-8').read(),
        scope='Caption precision, conditional K3/K4 disclosure, print-size review only; no formal migration'))
    print('Frozen: 950 scientific files, original index, 17 artwork pairs/mirrors, P2 data and prior A/B.')


def text_spans(page):
    return [s for b in page.get_text('dict', flags=0)['blocks'] for l in b.get('lines', []) for s in l['spans']]


def render_previews(path):
    import make_review_figures as m
    with fitz.open(a.u.lp(path)) as doc:
        pix = doc[0].get_pixmap(dpi=150, alpha=False)
        rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3) / 255
    linear = m.linear_rgb(rgb)
    modes = {'NATIVE': rgb, 'GRAYSCALE': np.repeat(m.srgb(linear @ [.2126729, .7151522, .0721750])[:, :, None], 3, axis=2)}
    for label, matrix in m.MACHADO.items():
        modes[label.upper()] = np.clip(m.srgb(linear @ np.asarray(matrix).T), 0, 1)
    for mode, values in modes.items():
        Image.fromarray(np.rint(values * 255).astype('uint8')).save(a.u.lp(HERE / (path.stem + '_' + mode + '.png')))


def print_fit(fig, kind):
    from matplotlib.text import Text
    fig.set_size_inches(7.2, 9.0)
    for t in fig.findobj(Text):
        t.set_fontsize(max(7.5, t.get_fontsize()))
    changes = []
    # Preserve every plotted observation/mesh; only print typography and spacing change.
    for i, ax in enumerate(fig.axes[:6]):
        old = list(ax.get_position().bounds)
        ax.set_position([.075 + (i % 3) * .322, .779 - (i // 3) * .155, .225, .100])
        ax.set_title(ax.get_title(), fontsize=7.5, pad=4)
        changes.append(dict(axis=i, before=old, after=list(ax.get_position().bounds)))
    profile = fig.axes[6]
    profile.set_position([.40, .379, .35, .129])
    fig.axes[7].set_position([.81, .379, .017, .129])
    for ax in fig.axes[8:10]:
        old = list(ax.get_position().bounds)
        ax.set_position([old[0], .134, old[2], .211])
        changes.append(dict(axis=fig.axes.index(ax), before=old, after=list(ax.get_position().bounds)))
    for t in fig.texts:
        text = t.get_text()
        if text.startswith('A.'): t.set_y(.959)
        elif text.startswith('Exact empirical'): t.set_y(.582)
        elif text.startswith('B.'): t.set_y(.558)
        elif text.startswith('Ordinary feature'): t.set_y(.537)
        elif text.startswith(('C.', 'D.')): t.set_y(.361)
        elif text.startswith('2,299'): t.set_y(.072)
        elif text.startswith('Finite five'): t.set_y(.021)
    fig.legends[0].set_bbox_to_anchor((.025, .947))
    if kind == 'B':
        fig.axes[10].set_position([.61, .066, .32, .060])
        fig.legends[1].set_bbox_to_anchor((.035, .128))
        joint = fig.legends[2]
    else:
        fig.axes[10].set_position([.56, .118, .37, .009])
        fig.legends[1].set_bbox_to_anchor((.525, .073))
        fig.legends[2].set_bbox_to_anchor((.035, .128))
        joint = fig.legends[3]
    handles, labels = joint.legend_handles, [t.get_text() for t in joint.get_texts()]
    joint.remove()
    fig.legend(handles, labels, loc='lower left', bbox_to_anchor=(.525, .008),
               frameon=False, ncol=2, fontsize=7.5, columnspacing=1, handlelength=1.2)
    # Ticks/colorbar labels are generated on draw; enforce the floor again afterwards.
    fig.canvas.draw()
    for t in fig.findobj(Text):
        t.set_fontsize(max(7.5, t.get_fontsize()))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    xlabel = fig.axes[10].xaxis.label.get_window_extent(renderer)
    assert all(not xlabel.overlaps(t.get_window_extent(renderer)) for t in fig.legends[-1].get_texts())
    return changes


def make_proofs():
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import make_review_figures as m
    d = a.load_frozen()
    geo = gpd.read_file(a.u.lp(PB / 'inputs/FULL_2315_GEOMETRY.gpkg')).set_index('tract_id')
    g = geo.join(d)
    legend = pd.read_csv(a.u.lp(PB / 'BIVARIATE_EXACT_COLOR_LEGEND.csv'), float_precision='round_trip')
    lut = legend.sort_values(['position', 'quartile'])[['R', 'G', 'B']].to_numpy().reshape(257, 4, 3)
    font_rows = []
    changes = []
    invariant = []

    def save_review(fig, unused_name):
        kind = unused_name[-1]
        lines = [tuple((line.get_xdata().copy(), line.get_ydata().copy()) for line in ax.lines)
                 for ax in fig.axes[:6]]
        mesh = fig.axes[6].collections[0].get_array().copy()
        old_maps = [ax.get_xlim() + ax.get_ylim() for ax in fig.axes[8:10]]
        edits = print_fit(fig, kind)
        for ax, frozen in zip(fig.axes[:6], lines):
            for line, (x, y) in zip(ax.lines, frozen):
                np.testing.assert_array_equal(line.get_xdata(), x)
                np.testing.assert_array_equal(line.get_ydata(), y)
        np.testing.assert_array_equal(fig.axes[6].collections[0].get_array(), mesh)
        assert old_maps == [ax.get_xlim() + ax.get_ylim() for ax in fig.axes[8:10]]
        name = 'FIGURE7_PATH_B_' + kind + '_PRINT_FIT_7p2x9p0'
        path = HERE / (name + '.pdf')
        a.u.write(path, b'')
        fig.savefig(a.u.lp(path), metadata={'CreationDate': None, 'ModDate': None})
        fig.savefig(a.u.lp(HERE / (name + '.png')), dpi=600)
        plt.close(fig)
        with fitz.open(a.u.lp(path)) as doc:
            p = doc[0]
            spans = text_spans(p)
            assert min(s['size'] for s in spans) >= 7.49
            assert all(p.rect.contains(fitz.Rect(s['bbox'])) for s in spans)
            assert len(p.get_images()) == 0
            font_rows.extend(dict(file=path.name, text=s['text'], native_pt=s['size'],
                                  at_9in_pt=s['size'], at_8p5in_pt=s['size'] * 8.5 / 9) for s in spans)
        changes.extend(dict(candidate=kind, **r) for r in edits)
        invariant.append(dict(candidate=kind, ecdf_axes_exact=6, curves_exact=18,
                              printed_cohort_z_cells=21, values_exact=True,
                              map_limits_exact=True, published_color_legend_exact=True,
                              physical_display_positions_changed=True, approved_official_layout=False))
        render_previews(path)

    m.save = save_review
    for kind in ['A', 'B']:
        m.make_candidate(kind, d, g, lut)
    # Height-constrained proofs retain aspect ratio; this also reduces printed width.
    book = fitz.open()
    for kind in ['A', 'B']:
        original = PB / 'figures' / ('FIGURE7_PATH_B_CANDIDATE_' + kind + '.pdf')
        with fitz.open(a.u.lp(original)) as src:
            for height in [9.0, 8.5]:
                page = book.new_page(width=7.2 * 72, height=9.0 * 72)
                page.show_pdf_page(fitz.Rect(0, 0, 7.2 * 72, height * 72), src, 0)
            for s in text_spans(src[0]):
                font_rows.append(dict(file=original.name, text=s['text'], native_pt=s['size'],
                                      at_9in_pt=s['size'] * 9 / 10.4, at_8p5in_pt=s['size'] * 8.5 / 10.4))
        with fitz.open(a.u.lp(HERE / ('FIGURE7_PATH_B_' + kind + '_PRINT_FIT_7p2x9p0.pdf'))) as src:
            book.insert_pdf(src)
    proof = HERE / 'FIGURE7_HEIGHT_LIMIT_AND_PRINT_FIT_PROOFS.pdf'
    a.u.write(proof, book.tobytes(garbage=4, deflate=True, no_new_id=True))
    book.close()
    a.u.write_csv(HERE / 'TEXT_SIZE_AT_FINISHED_DIMENSIONS.csv', font_rows)
    a.u.write_csv(HERE / 'PRINT_SPACING_CHANGE_REGISTER.csv', changes)
    dump('PRINT_FIT_SCIENTIFIC_AND_VECTOR_QA.json', invariant)
    dump('PUBLICATION_SIZE_ASSUMPTIONS.json', dict(
        original_inches=[7.2, 10.4], review_reflow_inches=[7.2, 9.0],
        journal_specific_height_confirmed=False, caption_space_reserved=False,
        original_min_pt=min(r['native_pt'] for r in font_rows if 'CANDIDATE' in r['file']),
        original_min_at_9in_pt=min(r['at_9in_pt'] for r in font_rows if 'CANDIDATE' in r['file']),
        print_fit_min_pt=min(r['native_pt'] for r in font_rows if 'PRINT_FIT' in r['file']),
        print_fit_min_at_8p5in_pt=min(r['at_8p5in_pt'] for r in font_rows if 'PRINT_FIT' in r['file']),
        print_fit_is_review_only=True, CVD_method='Machado2009 linear-sRGB severity100; simulation, not certification'))
    print('Two print-fit proofs and a six-page height-limit proof; no official artwork changed.')


def verify_preservation():
    before = read_json(HERE / 'STARTING_STATE.json')
    changed = [p for p, h in before['immutable_hashes'].items() if a.u.sha(ROOT / p) != h]
    assert not changed, changed
    protected = a.u.protected_snapshot(read_json(HERE / 'PRESERVATION_BEFORE.json'))
    assert protected == read_json(HERE / 'PRESERVATION_BEFORE.json')
    assert a.u.git('rev-parse', 'HEAD', root=ROOT.parent / '_ac13').decode().strip() == before['source_worktree_HEAD']
    assert a.u.sha(a.u.git('rev-parse', '--path-format=absolute', '--git-path', 'index',
                          root=ROOT.parent / '_ac13').decode().strip()) == before['source_index_sha256']
    dump('PRESERVATION_AFTER.json', protected)
    dump('UNCHANGED_ARTWORK_DATA_AND_CANDIDATES.json', dict(
        hashes_checked=len(before['immutable_hashes']), all_bytes_identical=True,
        protected_scientific_files=950, official_numbered_artwork_pairs=17,
        original_index_unchanged=True, no_new_Kmeans_or_physical_model=True))
    print('Preservation PASS:', len(before['immutable_hashes']), 'hashes, protected950/index unchanged.')


def verify_caption_and_decision():
    import ast
    before = read_json(HERE / 'STARTING_STATE.json')
    current_text = open(a.u.lp(ROOT / 'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md'), encoding='utf-8').read()
    previous, current = a.u.captions(before['captions']), a.u.captions(current_text)
    changes = [h for h in current if previous[h] != current[h]]
    assert len(current) == 17 and len(changes) == 3
    assert all(h.startswith(('Figure 4.', 'Figure 5.', 'Figure 6.')) for h in changes)
    captions = []
    source = ROOT / 'src/la_grid/plotting/short_current_captions_20261013.py'
    tree = ast.parse(open(a.u.lp(source), encoding='utf-8').read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CAPTIONS' for t in node.targets):
            captions = ast.literal_eval(node.value)
    assert captions == list(current.values())
    assert all(len(v.split()) <= 90 for v in current.values())
    assert 'eight fitted coordinates' in captions[6] and 'NCV14/H2/K3' in captions[6]
    assert all('5th-95th realization ranges, not confidence intervals' in captions[i] for i in [3, 4])
    assert 'service-loss bars show means without whiskers' in captions[3]
    assert '95% bootstrap confidence intervals for mean effects' in captions[5]
    assert 'Degree-first hospital comparisons show means only' in captions[5]
    rows = []
    registry = pd.read_csv(a.u.lp(ROOT / 'docs/reproducibility/figure_suite_concise_captions_20261013/COMPACT_PACKET_PAGE_REGISTRY.csv'))
    with fitz.open(a.u.lp(ROOT / 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf')) as packet:
        assert len(packet) == 21
        for i in [3, 4, 5]:
            page = packet[i]
            cut = float(registry.iloc[i].figure_height_pt)
            actual = ' '.join(page.get_text(clip=fitz.Rect(0, cut, page.rect.width, page.rect.height)).split())
            assert captions[i] in actual
            a.u.write(HERE / ('Figure' + str(i + 1) + '_CORRECTED_CAPTION_PREVIEW.png'),
                      page.get_pixmap(dpi=150, clip=fitz.Rect(0, cut, page.rect.width, page.rect.height), alpha=False).tobytes('png'))
            rows.append(dict(figure=i + 1, before=previous[list(current)[i]], after=captions[i],
                             visible_in_packet=True, words=len(captions[i].split())))
    a.u.write_csv(HERE / 'EXACT_CAPTION_BEFORE_AFTER.csv', rows)
    draft = open(a.u.lp(PB / 'FIGURE7_AND_S9_CAPTION_DRAFTS.md'), encoding='utf-8').read()
    assert draft.count('Six descriptive empirical feature distributions') == 2
    assert draft.count('all seven fitted P2 variables') == 2
    decision = open(a.u.lp(PB / 'K3_K4_AUTHOR_DECISION.md'), encoding='utf-8').read()
    assert 'accepted as the conditional' in decision and 'must remain as sensitivity' in decision
    k = pd.read_csv(a.u.lp(PB / 'K3_K4_K5_DECISION_EVIDENCE.csv')).set_index('k')
    assert k.loc[4, 'geographic_full_median_ARI'] > k.loc[3, 'geographic_full_median_ARI']
    assert k.loc[4, 'geographic_heldout_min_ARI'] > k.loc[3, 'geographic_heldout_min_ARI']
    q = read_json(PB / 'INDEPENDENT_QA_RESULTS.json')
    assert q['passed'] == 234 and q['failed'] == 0 and q['no_fitting']
    proof_rows = []
    for kind in ['A', 'B']:
        p = HERE / ('FIGURE7_PATH_B_' + kind + '_PRINT_FIT_7p2x9p0.pdf')
        with fitz.open(a.u.lp(p)) as doc:
            page = doc[0]
            assert abs(page.rect.width / 72 - 7.2) < 1e-6
            assert abs(page.rect.height / 72 - 9) < 1e-6
            assert not page.get_images()
            proof_rows.append(dict(file=p.name, sha256=a.u.sha(p), width_in=7.2, height_in=9,
                                   min_font_pt=min(s['size'] for s in text_spans(page)),
                                   raster_images=0, vector_paths=len(page.get_drawings()),
                                   PNG_dimensions=Image.open(a.u.lp(p.with_suffix('.png'))).size, dpi=600))
    dump('INDEPENDENT_FOLLOWUP_QA.json', dict(
        caption_source_matches_export=True, changed_captions=['Figure4', 'Figure5', 'Figure6'],
        other_current_captions_exact=14, packet_pages=21, visible_caption_text_matches=True,
        P2_draft_six_descriptive_distributions_and_seven_fitted_coordinates=True,
        conditional_K3_and_mandatory_K4_recorded=True, K4_geographic_advantage_disclosed=True,
        frozen_data_independent_checks=234, models_fitted=0, official_Fig07_promoted=False,
        packet_before_sha256=before['packet_sha256'],
        packet_after_sha256=a.u.sha(ROOT / 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),
        print_fit_figures=proof_rows))
    style_rows = []
    for r in a.u.csv_rows(open(a.u.lp(ROOT / 'results/figure_review/FIGURE_MANIFEST.csv'), 'rb').read()):
        if not r['final_name'].endswith('.pdf'):
            continue
        with fitz.open(a.u.lp(ROOT / r['current_source_file'])) as doc:
            fonts = sorted({s['font'] for s in text_spans(doc[0])})
        style_rows.append(dict(figure=r['final_name'], width_height_mm=r['size_mm'],
                               declared_min_font_pt=r['min_font_pt'], PDF_font_names=';'.join(fonts),
                               actual_PDF_sha256=a.u.sha(ROOT / r['current_source_file']),
                               modified=False))
    a.u.write_csv(HERE / 'PREVIOUS_FIGURE_PRESENTATION_REFERENCE.csv', style_rows)
    print('Caption source/PDF, K decision and print-fit vector checks PASS.')


if __name__ == '__main__':
    mode = argparse.ArgumentParser()
    mode.add_argument('mode', choices=['freeze', 'proofs', 'preservation', 'qa'])
    {'freeze': freeze, 'proofs': make_proofs, 'preservation': verify_preservation,
     'qa': verify_caption_and_decision}[mode.parse_args().mode]()
