"""Independent numerical, source-stream, publication and protection QA."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import sys

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE = Path(str(Path(__file__).resolve().parent).removeprefix('\\\\?\\'))
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import fitz
import numpy as np
import pandas as pd
from PIL import Image

MM = 72 / 25.4


def read(name):
    return json.load(open(u.lp(HERE / name), encoding='utf-8'))


def main():
    checks = []
    authority = read('SOURCE_AUTHORITY_AND_HASHES.json')
    for s in authority['sources']:
        assert u.sha(HERE / s['local']) == s['sha256'] == u.digest(u.payload(s['commit'], s['path']))
    checks.append('All pinned source payload identities and local source-copy bytes match')
    f = pd.read_csv(u.lp(HERE / 'inputs/EIGHT_VARIABLE_FROZEN_TABLE.csv'), dtype={'tract_id': str}, float_precision='round_trip')
    m = pd.read_csv(u.lp(HERE / 'inputs/K3_CLUSTER_MEMBERSHIP.csv'), dtype={'tract_id': str}, float_precision='round_trip')
    w = pd.read_csv(u.lp(HERE / 'inputs/COHORT_STANDARDIZER_AND_WEIGHTS.csv'), float_precision='round_trip').set_index('variable')
    plotted = pd.read_csv(u.lp(HERE / 'PLOTTED_FROZEN_VALUES.csv'), dtype={'tract_id': str}, float_precision='round_trip')
    summary = pd.read_csv(u.lp(HERE / 'FIGURE7_ORIGINAL_UNIT_AND_STANDARDIZED_DATA_QA.csv'), float_precision='round_trip')
    story = read('NUMERICAL_STORY_QA.json')
    assert plotted.tract_id.equals(f.tract_id) and plotted['class'].equals(m.candidate_display_cluster)
    assert len(f) == 2299 and f.Population.sum() == 9066522
    assert plotted.groupby('class').size().tolist() == [1242, 475, 582]
    assert plotted.additional_zero_housing_positive_population.sum() == 8
    assert len(summary) == 24 and summary.variable.nunique() == 8
    features = story['features']
    doc = fitz.open(u.lp(HERE / 'FIGURE7_CONSERVATIVE_RESTORATION.pdf'))
    errors = []
    for row in summary.to_dict('records'):
        c = int(row['class'][1:])
        j = features.index(row['variable'])
        values = f.loc[m.candidate_display_cluster.eq(c), row['variable']].to_numpy()
        assert len(values) == row['n']
        np.testing.assert_array_equal(plotted.loc[plotted['class'].eq(c), row['variable']], values)
        mean = math.fsum(values.tolist()) / len(values)
        assert abs(mean - row['raw_mean']) < 1e-11
        assert abs(np.median(values) - row['raw_median']) < 1e-12
        standardized = (mean - w.loc[row['variable'], 'cohort_mean']) / w.loc[row['variable'], 'population_SD']
        assert abs(standardized - row['ordinary_z_class_mean']) < 1e-12
        errors.append(abs(standardized - row['ordinary_z_class_mean']))
        cell = fitz.Rect((74 + (c - 1) * 22) * MM, (111 + j * 3.5) * MM,
                         (74 + c * 22) * MM, (111 + (j + 1) * 3.5) * MM)
        assert f'{standardized:+.2f}' in doc[0].get_textbox(cell)
    checks.append('Every original-unit mean/median and all 24 displayed z-score cells independently reconstructed')
    points = pd.read_csv(u.lp(HERE / 'A_EMPIRICAL_DISTRIBUTION_POINTS.csv'), float_precision='round_trip')
    for (feature, group), d in points.groupby(['variable', 'class'], sort=False):
        c = int(group[1:])
        values = f.loc[m.candidate_display_cluster.eq(c), feature].to_numpy()
        counter = Counter(values.tolist())
        actual = dict(zip(d.value, d.value_count))
        assert actual == counter and d.value_count.sum() == len(values)
        np.testing.assert_allclose(d.value_count.cumsum() / len(values), d.cumulative_fraction, atol=1e-15, rtol=0)
    assert points.variable.nunique() == 6
    checks.append('All 18 class/feature empirical distributions contain the exact source observations and ties')
    current = fitz.open(u.lp(HERE / 'inputs/CURRENT_FIGURE7.pdf'))
    source_stream = b''.join(current.xref_stream(x) for x in current[0].get_contents())
    source_digest = hashlib.sha256(source_stream).hexdigest()
    imported = [doc.xref_stream(x) for x in range(1, doc.xref_length())
                if doc.xref_is_stream(x) and doc.xref_get_key(x, 'Subtype')[1] == '/Form']
    assert source_digest in [hashlib.sha256(b).hexdigest() for b in imported]
    checks.append('The original current Fig07 content stream is embedded byte-identically behind the locked C/D clip')
    # Normalize both clipped regions to the same origin before comparing pixels.
    normalized = []
    for document, top in [(current, 132), (doc, 140)]:
        d = fitz.open()
        clip = fitz.Rect(0, top * MM, current[0].rect.width, (top - 132) * MM + current[0].rect.height)
        p = d.new_page(width=clip.width, height=clip.height)
        p.show_pdf_page(p.rect, document, 0, clip=clip, keep_proportion=False)
        pix = p.get_pixmap(dpi=160, alpha=False)
        normalized.append((np.frombuffer(pix.samples, dtype=np.uint8).copy(), pix.width, pix.height))
        d.close()
    assert normalized[0][1:] == normalized[1][1:]
    difference = abs(normalized[0][0].astype(int) - normalized[1][0].astype(int))
    # Source-stream identity is exact; any nested-form edge rounding is recorded, not hidden.
    map_pixels = {'exact_pixel_identity': bool(not difference.any()), 'maximum_channel_difference': int(difference.max()),
        'nonidentical_channel_fraction': float(np.mean(difference != 0)), 'normalized_render_dpi': 160,
        'source_content_stream_identical': True, 'only_proposed_translation_mm': [0, 8], 'no_geographic_rescaling': True}
    assert map_pixels['nonidentical_channel_fraction'] < .001 and map_pixels['maximum_channel_difference'] <= 16
    checks.append('Locked C/D vector identity and normalized publication rendering checked')
    names = ['FIGURE7_CONSERVATIVE_RESTORATION', 'FIGURE7_AB_PANEL_SIDE_BY_SIDE_REVIEW',
             'FIGURE7_OLD_CURRENT_CANDIDATE_NATIVE_COMPARISON', 'FIGURE7_NA_FILL_SEPARATE_APPROVAL_COMPARISON']
    pdfs = []
    for name in names:
        with fitz.open(u.lp(HERE / (name + '.pdf'))) as d:
            assert all('LAYOUT PROPOSAL' in ' '.join(p.get_text().split())
                       and 'NOT APPROVED FOR CURRENT SUITE' in ' '.join(p.get_text().split()) for p in d)
            pdfs.append({'file': name + '.pdf', 'pages': len(d), 'sha256': u.sha(HERE / (name + '.pdf')),
                'image_objects': [len(p.get_images()) for p in d], 'native_size_mm': [[p.rect.width / MM, p.rect.height / MM] for p in d]})
    assert len(doc[0].get_images()) == 0
    assert abs(doc[0].rect.width / MM - 185) < .01 and abs(doc[0].rect.height / MM - 253) < .01
    with Image.open(u.lp(HERE / 'FIGURE7_CONSERVATIVE_RESTORATION.png')) as im:
        assert im.width >= 4360 and abs(im.info['dpi'][0] - 600) < .1
    checks.append('Four marked vector review PDFs, native 185-mm candidate and 600-dpi candidate export verified')
    initial = read('INITIAL_OFFICIAL_SUITE_AND_WORKTREE_STATE.json')
    official = ROOT.parent / '_ok13'
    assert all(u.sha(official / p) == h for p, h in initial['official_tracked_file_hashes'].items())
    for root, expected in initial['worktrees'].items():
        root = Path(root)
        index = u.git('rev-parse', '--path-format=absolute', '--git-path', 'index', root=root).decode().strip()
        now = {'HEAD': u.git('rev-parse', 'HEAD', root=root).decode().strip(),
            'status_sha256': u.digest(u.git('status', '--porcelain=v1', '-z', root=root)), 'index_sha256': u.sha(index),
            'staged_names_sha256': u.digest(u.git('diff', '--cached', '--name-only', '-z', root=root))}
        assert now == expected
    before = read('PRESERVATION_BEFORE.json')
    after = u.protected_snapshot(before)
    assert before == after and after['protected_count'] == 950
    u.dump(HERE / 'PRESERVATION_AFTER.json', after)
    checks.append('950 actual protected hashes, original index/staged state and all three official/historical worktrees unchanged')
    changed = u.git('diff', '--name-only', authority['current_suite']).decode().splitlines()
    prefix = str(HERE.relative_to(ROOT)).replace('\\', '/') + '/'
    assert all(path.startswith(prefix) for path in changed), changed
    u.dump(HERE / 'REPRODUCIBILITY_AND_PROTECTION_QA.json', {'checks': checks, 'passed': len(checks), 'failures': 0,
        'all_17_official_artwork_pairs_unchanged': True, 'official_packet_captions_mirrors_and_generator_unchanged': True,
        'all_950_protected_scientific_files_unchanged': True, 'original_staged_count': after['staged_count'],
        'maximum_independent_z_mean_error': max(errors), 'locked_CD': map_pixels, 'PDFs': pdfs,
        'no_K4_proposal': True, 'new_candidate_B_generated': False, 'no_model_fit_or_physical_recovery_run': True})
    print('Independent review QA PASS:', len(checks), 'checks. Locked C/D pixel diagnostic:', map_pixels, flush=True)


if __name__ == '__main__':
    main()
