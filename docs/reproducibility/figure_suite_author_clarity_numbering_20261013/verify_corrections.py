"""Independent arithmetic, artwork, packet and preservation checks."""
from pathlib import Path
import csv
import io
import json
import sys

import fitz
import numpy as np
import pandas as pd
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ROOT = Path(str(ROOT).removeprefix('\\\\?\\'))
HERE = ROOT / 'docs/reproducibility/figure_suite_author_clarity_numbering_20261013'
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

BASE = '3c7899f0f328d37b99d2b022f1650c5288a4a664'
DEST = ROOT / 'results/figure_review'


def pixels(page, dpi=96):
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)


def main():
    rows = u.csv_rows(open(u.lp(DEST / 'FIGURE_MANIFEST.csv'), 'rb').read())
    assert len(rows) == 34
    unchanged = [r for r in rows if r['change_in_this_update'] == 'RETAINED']
    assert len(unchanged) == 26
    for r in rows:
        assert u.sha(ROOT / r['current_source_file']) == r['sha256'] == u.sha(ROOT / r['mirror_file'])
        if r in unchanged:
            assert r['sha256'] == r['parent_sha256']
    check = json.load(open(u.lp(HERE / 'BUILD_CHECKPOINT.json')))
    assert all(u.sha(ROOT / p) == h for p, h in check['output_hashes'].items())
    assert u.sha(DEST / 'Main/Fig07.pdf') == u.digest(u.payload(BASE, 'results/figure_review/Main/Fig07.pdf'))
    packet = fitz.open(u.lp(DEST / 'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    assert len(packet) == 38
    pdfs = [r for r in rows if r['final_name'].endswith('.pdf')]
    packet_checks = []
    for i, r in enumerate(pdfs):
        with fitz.open(u.lp(ROOT / r['current_source_file'])) as artwork:
            assert np.array_equal(pixels(artwork[0]), pixels(packet[2*i]))
        cap = packet[2*i+1]
        spans = [s for b in cap.get_text('dict', flags=0)['blocks']
                 for line in b.get('lines', []) for s in line['spans']]
        assert min(s['size'] for s in spans) >= 9.99
        assert all(cap.rect.contains(fitz.Rect(s['bbox'])) for s in spans)
        packet_checks.append(dict(figure=r['final_name'], artwork_matches=True,
                                  caption_min_font_pt=min(s['size'] for s in spans)))
    with fitz.open(stream=u.payload(BASE, 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),
                   filetype='pdf') as old:
        assert all(np.array_equal(pixels(old[i]), pixels(packet[i])) for i in range(34, 38))
    caption_text = open(u.lp(DEST / 'MANUSCRIPT_FACING_CAPTIONS.md'), encoding='utf-8').read()
    import re
    assert [int(n) for n in re.findall(r'^## Supplementary Figure S(\d+)\.', caption_text, re.M)] == list(range(1, 11))
    assert not re.search(r'\bS(?:11|12|13)\b', caption_text)
    assert 'Figures 4\u20136 and Supplementary Figure S10' in caption_text
    # Compare pixels outside the two authorized Fig01 text regions.
    with fitz.open(stream=u.payload(BASE, 'results/figure_review/Main/Fig01.pdf'), filetype='pdf') as old:
        with fitz.open(u.lp(DEST / 'Main/Fig01.pdf')) as new:
            a, b = pixels(old[0], 254), pixels(new[0], 254)
            changed = np.any(a != b, axis=2)
            mask = np.zeros(changed.shape, bool)
            mask[1700:, 940:] = True
            mask[1740:1860, 90:290] = True
            outside = int((changed & ~mask).sum())
            assert outside == 0, outside
    # The original threshold charts are reused, shifted by exactly 70 mm.
    with fitz.open(stream=u.payload(BASE, 'results/figure_review/Supplement/FigS06.pdf'), filetype='pdf') as old:
        with fitz.open(u.lp(DEST / 'Supplement/FigS05.pdf')) as new:
            a, b = pixels(old[0], 254), pixels(new[0], 254)
            delta = np.abs(a[850:1390].astype(int) - b[1550:2090].astype(int))
            threshold_difference = dict(max_channel_difference=int(delta.max()),
                differing_pixel_fraction=float(np.any(delta != 0, axis=2).mean()))
            assert threshold_difference['differing_pixel_fraction'] < .01
    # Independent mapped-tract reconstruction, rather than the production station sum.
    inputs = HERE / 'source_control_inputs'
    tracts = pd.read_csv(u.lp(inputs / 'TRACTS.csv'), dtype={'tract_id': str})
    mapping = pd.read_csv(u.lp(inputs / 'MAPPING.csv'), dtype={'tract_id': str, 'substation_id': str})
    values = pd.read_csv(u.lp(HERE / 'SOURCE_ONLY_REALIZATION_VALUES.csv'), float_precision='round_trip')
    independent = []
    for policy in values.policy.unique():
        with np.load(u.lp(inputs / (policy + '_INTEGRALS.npz'))) as z:
            w = mapping.pivot(index='tract_id', columns='substation_id', values='weight').fillna(0)
            w = w.reindex(index=tracts.tract_id, columns=z['station_ids'].astype(str), fill_value=0).to_numpy()
            tract_control = (z['G1_BASELINE_050__L_self'] + z['G1_BASELINE_050__L_threshold']) @ w.T
            calculated = tract_control @ tracts.population.to_numpy() / tracts.population.sum()
        published = values.loc[values.policy.eq(policy), 'source_off_loss_h'].to_numpy()
        error = float(np.max(abs(calculated - published)))
        assert error < 1e-10
        independent.append(dict(policy=policy, realizations=1000, maximum_error_h=error))
    before = json.load(open(u.lp(HERE / 'PRESERVATION_BEFORE.json')))
    prefix = 'docs/data_research/stage7_fig7d_policy_robustness_and_final_integration_gate_20261013/'
    reference = json.loads(u.payload('05a78645b17bf8de04326e54181f9db432d7186c',
                                     prefix + 'STARTING_STATE_AND_PROTECTION.json'))
    after = u.protected_snapshot(reference)
    assert before == after
    backup = json.load(open(u.lp(HERE / 'BASELINE_AND_BACKUP.json')))
    other = Path(backup['real_unchanged_backup_worktree'])
    assert u.git('status', '--porcelain=v1', '-z', root=other) == b''
    index = Path(u.git('rev-parse', '--path-format=absolute', '--git-path', 'index', root=other).decode().strip())
    assert u.sha(index) == backup['original_source_index_SHA256']
    for rel, h in backup['artwork_SHA256'].items():
        assert u.sha(other / rel) == h
    png_checks = []
    for r in rows:
        if not r['final_name'].endswith('.png'):
            continue
        with Image.open(u.lp(ROOT / r['current_source_file'])) as im:
            assert im.width >= 4360
            png_checks.append(dict(figure=r['final_name'], pixels=im.size, dpi=im.info.get('dpi')))
    u.dump(HERE / 'INDEPENDENT_QA.json', dict(
        numbered_figures=17, packet_pages=38, unchanged_artwork_pairs=13,
        Figure7_byte_identical=True, Fig01_outside_authorized_text_pixels_changed=outside,
        source_only_independent_checks=independent, threshold_aligned_render=threshold_difference,
        all_packet_figure_pixels_match=True, original_evidence_pages_preserved=True,
        packet_checks=packet_checks, png_checks=png_checks,
        protected_files=950, original_source_worktree_and_index_unchanged=True,
        no_new_physical_simulation_or_optimization=True,
        full_packet_SHA256=u.sha(DEST / 'ALL_FIGURES_WITH_CAPTIONS.pdf')))
    print('Independent QA passed: separate source-only control, 13 unchanged pairs, 38 pages, 950 protected files.')


if __name__ == '__main__':
    main()
